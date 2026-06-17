# Code Improvement Workorder - 2026-06-17

## 목적

- Postclose 자동화가 생성한 `code_improvement_order`를 Codex 실행용 작업지시서로 변환한다.
- 입력은 scalping pattern lab automation, swing lifecycle improvement automation, swing pattern lab automation을 함께 포함할 수 있다.
- 이 문서는 repo/runtime을 직접 변경하지 않는다. 사용자가 이 문서를 Codex 세션에 넣고 구현을 요청하는 지점만 사람 개입으로 남긴다.
- 구현 후 자동화체인 재투입은 다음 postclose report, threshold calibration, daily EV report가 담당한다.

## Source

- pattern_lab_automation: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-06-17.json`
- swing_improvement_automation: `/home/ubuntu/KORStockScan/data/report/swing_improvement_automation/swing_improvement_automation_2026-06-17.json`
- swing_pattern_lab_automation: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-06-17.json`
- swing_strategy_discovery_ev: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-06-17.json`
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-06-17.json`
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-06-17.json`
- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-17.json`
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-06-17.json`
- threshold_cycle_calibration: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_calibration/threshold_cycle_calibration_2026-06-17_postclose.json`
- pipeline_event_verbosity: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-06-17.json`
- observation_source_quality_audit: `/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-17.json`
- codebase_performance_workorder: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-06-17.json`
- pattern_lab_currentness_audit: `/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-06-17.json`
- pattern_lab_ai_review: `/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-06-17.json`
- producer_gap_discovery: `/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-06-17.json`
- stage_hook_workorder_discovery: `/home/ubuntu/KORStockScan/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_2026-06-17.json`
- stage_hook_runtime_scaffold: `/home/ubuntu/KORStockScan/data/report/stage_hook_runtime_scaffold/stage_hook_runtime_scaffold_2026-06-17.json`
- buy_funnel_sentinel: `/home/ubuntu/KORStockScan/data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-06-17.json`
- generated_at: `2026-06-17T19:07:44+09:00`
- generation_id: `2026-06-17-5a2bb3b52d66`
- source_hash: `5a2bb3b52d66071354ee3b3b49cb4d7fb50d00824d7f80fe92d3905479f3a0e2`

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
- previous_generation_id: `2026-06-17-510e92f2689c`
- previous_source_hash: `510e92f2689c2bc32bbb0abf0a8295b1e2f266e7b7b2a0042407985c9e933c15`
- new_order_ids: `[]`
- removed_order_ids: `['order_pattern_lab_ai_review_lifecycle_bucket_discovery_contract_drift', 'order_pattern_lab_ai_review_missing_code_improvement_workorder', 'order_pattern_lab_ai_review_missing_threshold_cycle_ev', 'order_pattern_lab_ai_review_swing_lifecycle_bucket_discovery_code_patch_required', 'order_pattern_lab_ai_review_swing_strategy_discovery_pending_quotes']`
- decision_changed_order_ids: `[]`

## Summary

- source_order_count: `152`
- scalping_source_order_count: `10`
- swing_source_order_count: `8`
- swing_entry_bottleneck_primary: `SWING_ENTRY_BOTTLENECK_OBSERVE`
- swing_entry_bottleneck_selected: `False`
- swing_lab_source_order_count: `3`
- swing_strategy_discovery_source_order_count: `2`
- swing_lifecycle_matrix_source_order_count: `25`
- swing_lifecycle_bucket_discovery_source_order_count: `61`
- pattern_lab_currentness_source_order_count: `0`
- pattern_lab_ai_review_source_order_count: `0`
- threshold_ev_source_order_count: `20`
- lifecycle_submit_bucket_source_order_count: `0`
- lifecycle_holding_exit_bucket_source_order_count: `20`
- pipeline_event_verbosity_source_order_count: `0`
- observation_source_quality_source_order_count: `0`
- codebase_performance_source_order_count: `12`
- buy_funnel_sentinel_source_order_count: `6`
- entry_submit_drought_selected: `True`
- entry_submit_drought_handoff_missing: `False`
- panic_lifecycle_source_order_count: `2`
- selected_order_count: `117`
- non_selected_order_count: `35`
- source_decision_counts: `{'implement_now': 1, 'attach_existing_family': 135, 'design_family_candidate': 5, 'defer_evidence': 8, 'reject': 3}`
- selected_decision_counts: `{'implement_now': 1, 'attach_existing_family': 116}`
- selected_route_counts: `{'repeat_unresolved_structural_blocker': 1, 'existing_family': 114, 'positive_source_only_review': 1, 'source_dimension_rollup': 1}`
- selected_implement_now_route_count: `1`
- selected_runtime_effect_false_count: `117`
- selected_unimplemented_runtime_effect_false_count: `1`
- selected_unimplemented_route_counts: `{'repeat_unresolved_structural_blocker': 1}`
- selected_terminal_non_implement_runtime_effect_false_count: `3`
- selected_terminal_non_implement_route_counts: `{'existing_family': 1, 'positive_source_only_review': 1, 'source_dimension_rollup': 1}`
- selected_implement_now_existing_implementation_count: `0`
- selected_implement_now_existing_implementation_order_ids: `[]`
- selected_implement_now_new_runtime_effect_false_count: `1`
- selected_implement_now_new_runtime_effect_false_order_ids: `['order_swing_ofi_qi_stale_or_missing_context']`
- repeat_unresolved_escalation_count: `0`
- repeat_unresolved_escalated_order_ids: `[]`
- repeat_unresolved_structural_blocker_count: `1`
- repeat_unresolved_structural_blocker_order_ids: `['order_swing_ofi_qi_stale_or_missing_context']`
- root_cause_closure_status_counts: `{'handoff_closed_root_cause_open': 20, 'implementation_done': 1, 'needs_followup_workorder': 1, 'root_cause_closed': 92}`
- implementation_done_count: `1`
- artifact_regeneration_required_count: `0`
- handoff_closed_root_cause_open_count: `20`
- root_cause_closed_count: `92`
- needs_followup_workorder_count: `1`
- root_cause_open_top: `[{'order_id': 'order_conversion_lane_key_lineage_active_arm_0c383886ae3c8de3', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_arm_78c1ca03d11c256b', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_arm_7bc3260124b31b77', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_arm_d09163dbcf8e6037', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_arm_da294c8705564eaf', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_seed_0629ba2d0f4dd524', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_seed_06fce89fd3a136e6', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_seed_07677c2e78c144df', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_seed_0a9736d86332c717', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_seed_0cae3a2115d07d28', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}]`
- selected_terminal_non_implement_longstanding_count: `3`
- selected_terminal_non_implement_longstanding_order_ids: `['order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_overnight_sell_today_rule_scalp_sim_overnight_sell_tod_ff77f4c9', 'order_lifecycle_quiet_gap_positive_source_only_rollup', 'order_lifecycle_source_dimension_gap_rollup']`
- non_selected_decision_counts: `{'attach_existing_family': 19, 'design_family_candidate': 5, 'defer_evidence': 8, 'reject': 3}`
- gemini_fresh: `False`
- claude_fresh: `True`
- swing_lifecycle_audit_available: `True`
- swing_pattern_lab_automation_available: `True`
- swing_pattern_lab_fresh: `True`
- pattern_lab_currentness_status: `pass`
- pattern_lab_currentness_fail_count: `0`
- pattern_lab_ai_review_status: `pass`
- pattern_lab_ai_review_workorder_count: `0`
- swing_threshold_ai_status: `parsed`
- daily_ev_available: `True`

### Duplicate Order Collisions
- `duplicate_order_id=order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manufacture_of_ele source=swing_lifecycle_decision_matrix stage=selection`
- `duplicate_order_id=order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_real_estate_activi source=swing_lifecycle_decision_matrix stage=selection`
- `duplicate_order_id=order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_other_financial_in source=swing_lifecycle_decision_matrix stage=selection`
- `duplicate_order_id=order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_other_financial_in source=swing_lifecycle_decision_matrix stage=selection`
- `duplicate_order_id=order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manufacture_of_bas source=swing_lifecycle_decision_matrix stage=selection`
- `duplicate_order_id=order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_other_financial_in source=swing_lifecycle_decision_matrix stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_risk_cap source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_risk_cap source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_risk_cap source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_risk_cap source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_risk_cap source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_risk_cap source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_pullback_limit_entry_risk_cappe source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_pullback_limit_entry_risk_cappe source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_pullback_limit_entry_risk_cappe source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_risk_cap source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_risk_cap source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_risk_cap source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_risk_cap source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_pullback_limit_entry_risk_cappe source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped source=swing_lifecycle_bucket_discovery stage=selection`

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

### 1. `order_swing_ofi_qi_stale_or_missing_context`

- title: swing OFI/QI stale or missing context
- decision: `implement_now`
- decision_reason: longstanding non-implement finding remained unresolved across 8 workorder days; promote it as a structural blocker instead of leaving it as passive evidence
- source_report_type: `swing_improvement_automation`
- lifecycle_stage: `entry`
- target_subsystem: `swing_orderbook_micro_context`
- route: `repeat_unresolved_structural_blocker`
- mapped_family: `swing_entry_ofi_qi_execution_quality`
- threshold_family: `swing_entry_ofi_qi_execution_quality`
- improvement_type: `instrumentation`
- confidence: `consensus`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: stale_missing_ratio decreases while submitted/simulated entry quality remains attributable.
- evidence: `stale_missing_count=12670`, `stale_missing_ratio=0.1407`, `stale_missing_unique_record_count=13`, `stale_missing_reason_counts={'micro_missing': 12670, 'micro_not_ready': 12312, 'state_insufficient': 12312, 'observer_unhealthy': 4}`, `stale_missing_reason_combination_counts={'micro_missing+micro_not_ready+state_insufficient': 12308, 'micro_missing': 358, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 4}`, `stale_missing_reason_combination_unique_record_counts={'micro_missing+micro_not_ready+state_insufficient': 13, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`, `observer_unhealthy_overlap={'observer_unhealthy_total': 4, 'observer_unhealthy_with_other_reason': 4, 'observer_unhealthy_only': 0}`, `scale_in_source_quality={'group': 'scale_in', 'sample_count': 76, 'valid_micro_context_count': 69, 'invalid_micro_context_count': 7, 'invalid_micro_context_unique_record_count': 1, 'invalid_reason_combination_counts': {'micro_missing+micro_not_ready+state_insufficient': 12308, 'micro_missing': 358, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 4}, 'invalid_reason_combination_unique_record_counts': {'micro_missing+micro_not_ready+state_insufficient': 13, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}, 'observer_unhealthy_overlap': {'observer_unhealthy_total': 4, 'observer_unhealthy_with_other_reason': 4, 'observer_unhealthy_only': 0}, 'source_quality_blockers': ['scale_in_ofi_qi_invalid_micro_context']}`, `entry_source_quality={'group': 'entry', 'sample_count': 89572, 'valid_micro_context_count': 77278, 'invalid_micro_context_count': 12294, 'invalid_micro_context_unique_record_count': 13, 'invalid_reason_combination_counts': {'micro_missing+micro_not_ready+state_insufficient': 12308, 'micro_missing': 358, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 4}, 'invalid_reason_combination_unique_record_counts': {'micro_missing+micro_not_ready+state_insufficient': 13, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}, 'observer_unhealthy_overlap': {'observer_unhealthy_total': 4, 'observer_unhealthy_with_other_reason': 4, 'observer_unhealthy_only': 0}, 'source_quality_blockers': ['entry_ofi_qi_invalid_micro_context']}`
- parity_contract: -
- next_postclose_metric: stale_missing_ratio decreases while submitted/simulated entry quality remains attributable.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/orderbook_stability.py`, `src/engine/swing_lifecycle_audit.py`
- acceptance_tests: `pytest orderbook stability tests`, `pytest swing lifecycle audit tests`
- implementation_status: `repeat_unresolved_structural_blocker`
- root_cause_closure_status: `needs_followup_workorder`
- implementation_provenance: `{"structural_blocker_escalation": {"escalation_reason": "source_quality_ratio_not_improving_after_handoff", "history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "terminal_existing_family_evidence", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_swing_ofi_qi_stale_or_missing_context", "repeat_signature": "sig:swing_improvement_automation|swing_orderbook_micro_context|entry|instrumentation|swing_entry_ofi_qi_execution_quality|swing_ofi_qi_stale_or_missing_context", "required_next_route": "implement_now"}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "terminal_existing_family_evidence", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_swing_ofi_qi_stale_or_missing_context", "repeat_signature": "sig:swing_improvement_automation|swing_orderbook_micro_context|entry|instrumentation|swing_entry_ofi_qi_execution_quality|swing_ofi_qi_stale_or_missing_context", "review_disposition": "repeat_unresolved_structural_blocker"}`
- structural_blocker_escalation: `{"escalation_reason": "source_quality_ratio_not_improving_after_handoff", "history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "terminal_existing_family_evidence", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_swing_ofi_qi_stale_or_missing_context", "repeat_signature": "sig:swing_improvement_automation|swing_orderbook_micro_context|entry|instrumentation|swing_entry_ofi_qi_execution_quality|swing_ofi_qi_stale_or_missing_context", "required_next_route": "implement_now"}`
- automation_reentry: After implementation, regenerate the source report, code improvement workorder, threshold EV/runtime summary, and postclose verifier; runtime/order/provider/bot state must remain unchanged.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 2. `order_entry_submit_drought_auto_resolution`

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
- evidence: `ai_confirmed_unique=333`, `budget_pass_unique=78`, `latency_pass_unique=36`, `submitted_unique=5`, `submitted_to_ai_pct=1.5`, `submitted_to_budget_pct=6.4`, `blocker:latency_block:latency_state_danger=45315`, `blocker:blocked_gatekeeper_reject:눌림 대기=8308`, `blocker:blocked_strength_momentum:insufficient_history=5460`, `upstream:blocked_ai_score:score_62.0=1075`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=614`, `upstream:first_ai_wait:-=563`, `latency:latency_block:latency_state_danger=45315`
- parity_contract: -
- next_postclose_metric: SUBMIT_DROUGHT_CRITICAL must produce a selected implement_now workorder and the next postclose LDM/runtime summary must show submit blocker attribution.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/threshold_cycle_ev_report.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "artifact_regeneration_required": false, "broker_order_submit_allowed": false, "forbidden_uses": ["intraday_threshold_mutation", "broker_guard_bypass", "provider_route_change", "bot_restart_trigger", "telegram_pre_submit_buy_alert"], "implementation_type": "source_only_report_provenance_handoff", "ldm_quote_freshness_attribution_present": true, "quote_freshness_attribution_inconsistent": false, "quote_freshness_latency_pass_recovered_count": 21, "quote_freshness_refresh_applied_count": 66, "quote_freshness_refresh_attempted_count": 77, "required_downstream": ["code_improvement_workorder", "lifecycle_decision_matrix.submit_bucket_attribution", "threshold_cycle_ev_report", "runtime_approval_summary", "postclose_verifier"], "root_cause_closure_status_hint": "root_cause_closed", "root_cause_counts": {"observer_unhealthy": 26493, "order_rtt_guard": 12309, "quote_stale": 83017, "spread_or_slippage_guard": 15212}, "root_cause_signal": "SUBMIT_DROUGHT_CRITICAL", "runtime_effect": false, "source_report_type": "buy_funnel_sentinel", "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
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
- evidence: `ai_confirmed_unique=333`, `budget_pass_unique=78`, `latency_pass_unique=36`, `submitted_unique=5`, `submitted_to_ai_pct=1.5`, `submitted_to_budget_pct=6.4`, `blocker:latency_block:latency_state_danger=45315`, `blocker:blocked_gatekeeper_reject:눌림 대기=8308`, `blocker:blocked_strength_momentum:insufficient_history=5460`, `upstream:blocked_ai_score:score_62.0=1075`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=614`, `upstream:first_ai_wait:-=563`, `latency:latency_block:latency_state_danger=45315`, `weak_contract_gap=broker_receipt_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_submit_contract_verified`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "broker_receipt_contract_gap", "implementation_type": "submit_contract_report_provenance_verified", "missing_broker_order_key_count": 0, "post_submit_provenance_join_resolution": "no_gap_broker_order_key_present_or_no_missing_rows", "real_submitted_row_count": 5, "runtime_effect": false, "sample_status": "ldm_submit_contract_verified", "source_report_type": "buy_funnel_sentinel", "submit_rows": 213, "taxonomy_leakage_labels": [], "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_submit_contract_verified", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_entry_broker_receipt_contract_gap_review", "repeat_signature": "sig:buy_funnel_sentinel|runtime_instrumentation|entry_submit||lifecycle_decision_matrix_runtime|entry_broker_receipt_contract_gap_review", "review_disposition": "review_required"}`
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
- evidence: `ai_confirmed_unique=333`, `budget_pass_unique=78`, `latency_pass_unique=36`, `submitted_unique=5`, `submitted_to_ai_pct=1.5`, `submitted_to_budget_pct=6.4`, `blocker:latency_block:latency_state_danger=45315`, `blocker:blocked_gatekeeper_reject:눌림 대기=8308`, `blocker:blocked_strength_momentum:insufficient_history=5460`, `upstream:blocked_ai_score:score_62.0=1075`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=614`, `upstream:first_ai_wait:-=563`, `latency:latency_block:latency_state_danger=45315`, `weak_contract_gap=fill_quality_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_submit_contract_verified`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "fill_quality_contract_gap", "implementation_type": "submit_contract_report_provenance_verified", "missing_broker_order_key_count": 0, "post_submit_provenance_join_resolution": "no_gap_broker_order_key_present_or_no_missing_rows", "real_submitted_row_count": 5, "runtime_effect": false, "sample_status": "ldm_submit_contract_verified", "source_report_type": "buy_funnel_sentinel", "submit_rows": 213, "taxonomy_leakage_labels": [], "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_submit_contract_verified", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_entry_fill_quality_contract_gap_review", "repeat_signature": "sig:buy_funnel_sentinel|runtime_instrumentation|entry_submit||lifecycle_decision_matrix_runtime|entry_fill_quality_contract_gap_review", "review_disposition": "review_required"}`
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
- evidence: `ai_confirmed_unique=333`, `budget_pass_unique=78`, `latency_pass_unique=36`, `submitted_unique=5`, `submitted_to_ai_pct=1.5`, `submitted_to_budget_pct=6.4`, `blocker:latency_block:latency_state_danger=45315`, `blocker:blocked_gatekeeper_reject:눌림 대기=8308`, `blocker:blocked_strength_momentum:insufficient_history=5460`, `upstream:blocked_ai_score:score_62.0=1075`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=614`, `upstream:first_ai_wait:-=563`, `latency:latency_block:latency_state_danger=45315`, `weak_contract_gap=post_submit_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_submit_contract_verified`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "post_submit_contract_gap", "implementation_type": "submit_contract_report_provenance_verified", "missing_broker_order_key_count": 0, "post_submit_provenance_join_resolution": "no_gap_broker_order_key_present_or_no_missing_rows", "real_submitted_row_count": 5, "runtime_effect": false, "sample_status": "ldm_submit_contract_verified", "source_report_type": "buy_funnel_sentinel", "submit_rows": 213, "taxonomy_leakage_labels": [], "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_submit_contract_verified", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_entry_post_submit_contract_gap_review", "repeat_signature": "sig:buy_funnel_sentinel|runtime_instrumentation|entry_submit||lifecycle_decision_matrix_runtime|entry_post_submit_contract_gap_review", "review_disposition": "review_required"}`
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
- evidence: `ai_confirmed_unique=333`, `budget_pass_unique=78`, `latency_pass_unique=36`, `submitted_unique=5`, `submitted_to_ai_pct=1.5`, `submitted_to_budget_pct=6.4`, `blocker:latency_block:latency_state_danger=45315`, `blocker:blocked_gatekeeper_reject:눌림 대기=8308`, `blocker:blocked_strength_momentum:insufficient_history=5460`, `upstream:blocked_ai_score:score_62.0=1075`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=614`, `upstream:first_ai_wait:-=563`, `latency:latency_block:latency_state_danger=45315`, `weak_contract_gap=source_taxonomy_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`, `taxonomy_leakage_labels=[]`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_submit_contract_verified`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "source_taxonomy_contract_gap", "implementation_type": "submit_contract_report_provenance_verified", "missing_broker_order_key_count": 0, "post_submit_provenance_join_resolution": "no_gap_broker_order_key_present_or_no_missing_rows", "real_submitted_row_count": 5, "runtime_effect": false, "sample_status": "ldm_submit_contract_verified", "source_report_type": "buy_funnel_sentinel", "submit_rows": 213, "taxonomy_leakage_labels": [], "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_submit_contract_verified", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_entry_source_taxonomy_contract_gap_review", "repeat_signature": "sig:buy_funnel_sentinel|runtime_instrumentation|entry_submit||lifecycle_decision_matrix_runtime|entry_source_taxonomy_contract_gap_review", "review_disposition": "review_required"}`
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
- evidence: `ai_confirmed_unique=333`, `budget_pass_unique=78`, `latency_pass_unique=36`, `submitted_unique=5`, `submitted_to_ai_pct=1.5`, `submitted_to_budget_pct=6.4`, `blocker:latency_block:latency_state_danger=45315`, `blocker:blocked_gatekeeper_reject:눌림 대기=8308`, `blocker:blocked_strength_momentum:insufficient_history=5460`, `upstream:blocked_ai_score:score_62.0=1075`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=614`, `upstream:first_ai_wait:-=563`, `latency:latency_block:latency_state_danger=45315`, `weak_contract_gap=telegram_post_submit_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_submit_contract_verified`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "telegram_post_submit_contract_gap", "implementation_type": "submit_contract_report_provenance_verified", "missing_broker_order_key_count": 0, "post_submit_provenance_join_resolution": "no_gap_broker_order_key_present_or_no_missing_rows", "real_submitted_row_count": 5, "runtime_effect": false, "sample_status": "ldm_submit_contract_verified", "source_report_type": "buy_funnel_sentinel", "submit_rows": 213, "taxonomy_leakage_labels": [], "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_submit_contract_verified", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_entry_telegram_post_submit_contract_gap_review", "repeat_signature": "sig:buy_funnel_sentinel|runtime_instrumentation|entry_submit||lifecycle_decision_matrix_runtime|entry_telegram_post_submit_contract_gap_review", "review_disposition": "review_required"}`
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
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_latency_canary_tag_완화_1축_canary_승인", "repeat_signature": "sig:scalping_pattern_lab_automation|runtime_instrumentation||latency_canary_tag_완화_1축_canary_승인||latency_canary_tag_완화_1축_canary_승인", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_but_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 9. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_10_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_15cc1740`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_10`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 10. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_11_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_15cc1740`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_11`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 11. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_12_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_90f8527b`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:85dd6827b8
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_12`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:85dd6827b8`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 12. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_13_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_15cc1740`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_13`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 13. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_14_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_15cc1740`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_14`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 14. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_15_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_15cc1740`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_15`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 15. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_16_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_15cc1740`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_16`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 16. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_17_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:70a865069d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_17`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:70a865069d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 17. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_18_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:70a865069d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_18`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:70a865069d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 18. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_19_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:70a865069d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_19`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:70a865069d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 19. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_1_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_15cc1740`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_1`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 20. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_20_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:70a865069d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_20`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:70a865069d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 21. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_2_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_15cc1740`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_2`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 22. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_3_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_15cc1740`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_3`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 23. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_4_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_15cc1740`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_4`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 24. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_5_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_15cc1740`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_5`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 25. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_6_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_15cc1740`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_6`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 26. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_7_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_15cc1740`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_7`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 27. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_8_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_15cc1740`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_8`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 28. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_9_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_15cc1740`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_9`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 29. `order_stage_hook_workorder_discovery_stage_hook_holding_flow_runner_debounce_guard`

- title: Implement stage hook: holding_flow_runner_debounce_guard
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `stage_hook_workorder_discovery`
- lifecycle_stage: `holding`
- target_subsystem: `holding`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `holding_flow_runner_debounce_guard`
- confidence: `high`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: none_direct_until_separate_runtime_apply_candidate
- evidence: `strict_match_count=736`, `ambiguous_match_count=0`, `top_symbols=000150,000270,000500,000650,000660,001740,001820,002220`, `estimated_uplift_pct_sum=3471.2700`, `gap=sim-only early stop/loss followed by later runner is not isolated as a dedicated producer`, `required_microstructure_features=ws_orderbook_churn,ofi_qi_persistence,large_trade_absorption,spread_flicker,top_depth_replenishment,holding_flow_cache_freshness`, `required_producer=runner_regime_counterfactual_producer`, `readiness_tier=implementation_workorder_ready`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/stage_hook/holding/holding_flow_runner_debounce_guard.py`, `config/stage_hook/holding_flow_runner_debounce_guard.yaml`, `tests/unit/test_holding_flow_runner_debounce_guard.py`, `tests/integration/test_hook_lifecycle.py`
- acceptance_tests: `Validate hook_input_output_contract_test passes`, `Verify forbidden_use_authority_test blocks all prohibited actions`, `Confirm disabled_initial_runtime_state_test prevents early activation`, `Test post_apply_attribution_breach_guard triggers on policy violation`, `Validate rollback guards preserve safety vetoes`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "hook_name": "holding_flow_runner_debounce_guard", "implementation_files": ["src/engine/automation/stage_hook_runtime_scaffold.py"], "initial_runtime_state": "disabled", "requires_separate_runtime_apply_candidate": true, "runtime_effect": false, "source_report_type": "stage_hook_runtime_scaffold"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_stage_hook_workorder_discovery_stage_hook_holding_flow_runner_debounce_guard", "repeat_signature": "sig:stage_hook_workorder_discovery|holding|holding|holding_flow_runner_debounce_guard||implement_stage_hook_holding_flow_runner_debounce_guard", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

Stage hook candidate:

- hook_name: `holding_flow_runner_debounce_guard`
- hook_class: `runtime_arbitration_hook`
- stage: `holding`
- initial_authority: `source_only_proposal`
- readiness_tier: `implementation_workorder_ready`
- evidence_score: `100.0`
- action_namespace: `EXIT_CONFIRM`, `HOLD_REVIEW`, `TRIM`
- action_namespace_scope: `review_only_labels_not_runtime_actions`
- required_source_artifacts: `runner_regime_counterfactual_producer`
- required_mapping_tests: `hook_input_output_contract_test`, `forbidden_use_authority_test`, `disabled_initial_runtime_state_test`
- rollback_guard_requirements: `hard_safety_veto_preserved`, `broker_account_order_quantity_cooldown_veto_preserved`, `post_apply_attribution_breach_guard_defined`
- forbidden_uses: `account guard bypass`, `bot restart`, `broker guard bypass`, `broker order submit`, `cooldown guard bypass`, `emergency stop override`, `entry decision override`, `exit decision override`, `hard stop override`, `order guard bypass`, `position cap release`, `protect stop override`, `provider change`, `quantity guard bypass`, `real order enablement`, `threshold mutation`, `real_1share_as_preapply_primary_ev`, `real_one_share_as_preapply_primary_ev`, `merge_real_pnl_with_sim_probe_ev`, `runtime_change_from_preapply_real_sample`

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 30. `order_stage_hook_workorder_discovery_stage_hook_plateau_breakdown_exit_arbitration_probe`

- title: Implement stage hook: plateau_breakdown_exit_arbitration_probe
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `stage_hook_workorder_discovery`
- lifecycle_stage: `exit`
- target_subsystem: `exit`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `plateau_breakdown_exit_arbitration_probe`
- confidence: `high`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: none_direct_until_separate_runtime_apply_candidate
- evidence: `strict_match_count=859`, `ambiguous_match_count=0`, `top_symbols=000150,000240,000370,000500,000660,000990,001440,001740`, `estimated_giveback_pct_sum=4190.7200`, `gap=sim-only prior modest win followed by late stop/giveback is not isolated as a dedicated producer`, `required_producer=plateau_breakdown_exit_counterfactual_producer`, `readiness_tier=implementation_workorder_ready`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/stage_hook/exit/plateau_breakdown_exit_arbitration_probe.py`, `config/stage_hook/plateau_breakdown_exit_arbitration_probe.yaml`, `tests/unit/test_plateau_breakdown_exit_arbitration_probe.py`, `tests/integration/test_hook_lifecycle.py`
- acceptance_tests: `Validate hook_input_output_contract_test passes`, `Verify forbidden_use_authority_test blocks all prohibited actions`, `Confirm disabled_initial_runtime_state_test prevents early activation`, `Test post_apply_attribution_breach_guard triggers on policy violation`, `Validate rollback guards preserve safety vetoes`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "hook_name": "plateau_breakdown_exit_arbitration_probe", "implementation_files": ["src/engine/automation/stage_hook_runtime_scaffold.py"], "initial_runtime_state": "disabled", "requires_separate_runtime_apply_candidate": true, "runtime_effect": false, "source_report_type": "stage_hook_runtime_scaffold"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_stage_hook_workorder_discovery_stage_hook_plateau_breakdown_exit_arbitration_probe", "repeat_signature": "sig:stage_hook_workorder_discovery|exit|exit|plateau_breakdown_exit_arbitration_probe||implement_stage_hook_plateau_breakdown_exit_arbitration_probe", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

Stage hook candidate:

- hook_name: `plateau_breakdown_exit_arbitration_probe`
- hook_class: `runtime_arbitration_hook`
- stage: `exit`
- initial_authority: `source_only_proposal`
- readiness_tier: `implementation_workorder_ready`
- evidence_score: `100.0`
- action_namespace: `EXIT_CONFIRM`, `TAKE_PROFIT_ON_PLATEAU`, `HOLD_REVIEW`
- action_namespace_scope: `review_only_labels_not_runtime_actions`
- required_source_artifacts: `plateau_breakdown_exit_counterfactual_producer`
- required_mapping_tests: `hook_input_output_contract_test`, `forbidden_use_authority_test`, `disabled_initial_runtime_state_test`
- rollback_guard_requirements: `hard_safety_veto_preserved`, `broker_account_order_quantity_cooldown_veto_preserved`, `post_apply_attribution_breach_guard_defined`
- forbidden_uses: `account guard bypass`, `bot restart`, `broker guard bypass`, `broker order submit`, `cooldown guard bypass`, `emergency stop override`, `entry decision override`, `exit decision override`, `hard stop override`, `order guard bypass`, `position cap release`, `protect stop override`, `provider change`, `quantity guard bypass`, `real order enablement`, `threshold mutation`, `real_1share_as_preapply_primary_ev`, `real_one_share_as_preapply_primary_ev`, `merge_real_pnl_with_sim_probe_ev`, `runtime_change_from_preapply_real_sample`

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
- evidence: `workorder_id=entry_bucket_source_quality_6`, `bucket_type=exit_rule`, `bucket_key=exit_unknown`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "entry_label_not_applicable", "source_field_coverage": {"exit_rule": {"coverage_rate": 0.0, "present_count": 0, "sample_count": 1529, "source_fields": ["labels.exit_rule"]}}, "unknown_reason_counts": {"entry_label_not_applicable": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_lifecycle_entry_bucket_exit_rule_exit_unknown", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|runtime_instrumentation|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_exit_rule_exit_unknown", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 32. `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_overnight_sell_today_rule_scalp_sim_overnight_sell_tod_ff77f4c9`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010
- decision: `attach_existing_family`
- decision_reason: source coverage is present and the remaining bucket is an explicit not_applicable evidence classification
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
- evidence: `workorder_id=exit_bucket_source_quality_8`, `bucket_type=combo_exit_result`, `bucket_key=source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=source_quality_workorder`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `terminal_not_applicable_evidence`
- root_cause_closure_status: `-`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "source_quality_workorder", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "mark_not_applicable_explicitly", "source_field_coverage": {"outcome": {"coverage_rate": 1.0, "present_count": 8, "sample_count": 8, "source_fields": ["source_stage", "labels.exit_rule", "runtime_features.chosen_action", "labels.sim_post_sell_outcome", "labels.outcome", "labels.profit_rate"]}}, "unknown_reason_counts": {"not_applicable": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "terminal_not_applicable_evidence", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_scalp_sim_over", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_scalp_sim_over", "review_disposition": "keep_visible_by_design"}`
- structural_blocker_escalation: `-`
- automation_reentry: Keep the item out of the canonical implement_now queue; regenerated postclose reports and runner terminal dispositions must preserve the non-implement decision.

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
- evidence: `workorder_id=exit_bucket_source_quality_6`, `bucket_type=combo_exit_result`, `bucket_key=source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_823fe278", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_scalp_sim_part", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 34. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_good_e_d8c33947`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070
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
- evidence: `workorder_id=exit_bucket_source_quality_2`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_good_e_d8c33947", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 35. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_missed_30bb5c8f`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070
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
- evidence: `workorder_id=exit_bucket_source_quality_3`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_missed_30bb5c8f", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 36. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_neutra_d5168c3c`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070
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
- evidence: `workorder_id=exit_bucket_source_quality_10`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 37. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_e_71b132b9`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070
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
- evidence: `workorder_id=exit_bucket_source_quality_4`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_e_71b132b9", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 38. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_missed_bb293be8`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070
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
- evidence: `workorder_id=exit_bucket_source_quality_5`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_missed_bb293be8", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 39. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutra_d73738ba`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070
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
- evidence: `workorder_id=exit_bucket_source_quality_1`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutra_d73738ba", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 40. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_17b509a7`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300
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
- evidence: `workorder_id=exit_bucket_source_quality_7`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_recovery_or_relax", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 41. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_eb03513e`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150
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
- evidence: `workorder_id=exit_bucket_source_quality_9`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_recovery_or_relax", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 42. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_not_applicable_a_50644c4a`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_holding_bucket_attribution`
- lifecycle_stage: `holding`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `holding_bucket_source_quality_child_evidence`
- confidence: `daily_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep holding stage buckets visible as child evidence while parent lifecycle flow owns promotion EV.
- evidence: `workorder_id=holding_bucket_source_quality_10`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_recovery_or_relax", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 43. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_not_applicable_a_828a0f68`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_holding_bucket_attribution`
- lifecycle_stage: `holding`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `holding_bucket_source_quality_child_evidence`
- confidence: `daily_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep holding stage buckets visible as child evidence while parent lifecycle flow owns promotion EV.
- evidence: `workorder_id=holding_bucket_source_quality_6`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_recovery_or_relax", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 44. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_not_applicable_a_9af5260c`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_holding_bucket_attribution`
- lifecycle_stage: `holding`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `holding_bucket_source_quality_child_evidence`
- confidence: `daily_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep holding stage buckets visible as child evidence while parent lifecycle flow owns promotion EV.
- evidence: `workorder_id=holding_bucket_source_quality_9`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 45. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_not_applicable_a_f7731cc4`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_holding_bucket_attribution`
- lifecycle_stage: `holding`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `holding_bucket_source_quality_child_evidence`
- confidence: `daily_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep holding stage buckets visible as child evidence while parent lifecycle flow owns promotion EV.
- evidence: `workorder_id=holding_bucket_source_quality_4`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_recovery_or_relax", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 46. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_not_applicable_a_fc555278`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_holding_bucket_attribution`
- lifecycle_stage: `holding`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `holding_bucket_source_quality_child_evidence`
- confidence: `daily_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep holding stage buckets visible as child evidence while parent lifecycle flow owns promotion EV.
- evidence: `workorder_id=holding_bucket_source_quality_2`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_not_applicable_a_fc555278", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 47. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_lt_neg070_he_ed505a3f`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_holding_bucket_attribution`
- lifecycle_stage: `holding`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `holding_bucket_source_quality_child_evidence`
- confidence: `daily_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep holding stage buckets visible as child evidence while parent lifecycle flow owns promotion EV.
- evidence: `workorder_id=holding_bucket_source_quality_1`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_lt_neg070_he_ed505a3f", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 48. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_neg070_neg01_7ffc2d26`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_holding_bucket_attribution`
- lifecycle_stage: `holding`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `holding_bucket_source_quality_child_evidence`
- confidence: `daily_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep holding stage buckets visible as child evidence while parent lifecycle flow owns promotion EV.
- evidence: `workorder_id=holding_bucket_source_quality_8`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 49. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_pos080_pos15_aaaecaaf`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_holding_bucket_attribution`
- lifecycle_stage: `holding`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `holding_bucket_source_quality_child_evidence`
- confidence: `daily_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep holding stage buckets visible as child evidence while parent lifecycle flow owns promotion EV.
- evidence: `workorder_id=holding_bucket_source_quality_3`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_recovery_or_relax", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 50. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_pos150_pos30_562da131`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_holding_bucket_attribution`
- lifecycle_stage: `holding`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `holding_bucket_source_quality_child_evidence`
- confidence: `daily_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep holding stage buckets visible as child evidence while parent lifecycle flow owns promotion EV.
- evidence: `workorder_id=holding_bucket_source_quality_7`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_recovery_or_relax", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 51. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_pos150_pos30_6f3188b0`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_holding_bucket_attribution`
- lifecycle_stage: `holding`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `holding_bucket_source_quality_child_evidence`
- confidence: `daily_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep holding stage buckets visible as child evidence while parent lifecycle flow owns promotion EV.
- evidence: `workorder_id=holding_bucket_source_quality_5`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_recovery_or_relax", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 52. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_banking_and_saving`

- title: Swing LDM source field follow-up: breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Banking and Savings Institutions|은행|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_decision_matrix`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_ldm_bucket_instrumentation_gap`
- confidence: `postclose_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close Swing LDM bucket source-quality gaps while preserving sim-only authority.
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Banking and Savings Institutions|은행|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 14, "total_count": 14}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 14, "total_count": 14}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 14, "total_count": 14}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 14, "total_count": 14}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 14, "total_count": 14}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 53. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_building_construct`

- title: Swing LDM source field follow-up: breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Building Construction|건설_국내주택,건설_해외건설|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_decision_matrix`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_ldm_bucket_instrumentation_gap`
- confidence: `postclose_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close Swing LDM bucket source-quality gaps while preserving sim-only authority.
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Building Construction|건설_국내주택,건설_해외건설|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 10, "total_count": 10}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 10, "total_count": 10}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 10, "total_count": 10}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 10, "total_count": 10}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 10, "total_count": 10}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 54. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_building_of_ships_`

- title: Swing LDM source field follow-up: breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Building of Ships and Boats|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_decision_matrix`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_ldm_bucket_instrumentation_gap`
- confidence: `postclose_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close Swing LDM bucket source-quality gaps while preserving sim-only authority.
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Building of Ships and Boats|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 11, "total_count": 11}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 11, "total_count": 11}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 11, "total_count": 11}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 11, "total_count": 11}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 11, "total_count": 11}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 55. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_insurance_보험_손해보험_`

- title: Swing LDM source field follow-up: breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Insurance|보험_손해보험|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_decision_matrix`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_ldm_bucket_instrumentation_gap`
- confidence: `postclose_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close Swing LDM bucket source-quality gaps while preserving sim-only authority.
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Insurance|보험_손해보험|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 11, "total_count": 11}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 11, "total_count": 11}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 11, "total_count": 11}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 11, "total_count": 11}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 11, "total_count": 11}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 56. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manufacture_of_bas`

- title: Swing LDM source field follow-up: breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Basic Chemicals|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_decision_matrix`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_ldm_bucket_instrumentation_gap`
- confidence: `postclose_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close Swing LDM bucket source-quality gaps while preserving sim-only authority.
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Basic Chemicals|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 14, "total_count": 14}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 14, "total_count": 14}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 14, "total_count": 14}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 14, "total_count": 14}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 14, "total_count": 14}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 57. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manufacture_of_ele`

- title: Swing LDM source field follow-up: breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_decision_matrix`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_ldm_bucket_instrumentation_gap`
- confidence: `postclose_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close Swing LDM bucket source-quality gaps while preserving sim-only authority.
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 30, "total_count": 30}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 30, "total_count": 30}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 30, "total_count": 30}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 30, "total_count": 30}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 30, "total_count": 30}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 58. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manufacture_of_gen`

- title: Swing LDM source field follow-up: breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of General Purpose Machinery|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_decision_matrix`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_ldm_bucket_instrumentation_gap`
- confidence: `postclose_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close Swing LDM bucket source-quality gaps while preserving sim-only authority.
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of General Purpose Machinery|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 15, "total_count": 15}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 15, "total_count": 15}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 15, "total_count": 15}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 15, "total_count": 15}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 15, "total_count": 15}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 59. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manufacture_of_par`

- title: Swing LDM source field follow-up: breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_decision_matrix`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_ldm_bucket_instrumentation_gap`
- confidence: `postclose_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close Swing LDM bucket source-quality gaps while preserving sim-only authority.
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 11, "total_count": 11}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 11, "total_count": 11}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 11, "total_count": 11}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 11, "total_count": 11}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 11, "total_count": 11}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 60. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_other_financial_in`

- title: Swing LDM source field follow-up: breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Other Financial Intermediation|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_decision_matrix`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_ldm_bucket_instrumentation_gap`
- confidence: `postclose_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close Swing LDM bucket source-quality gaps while preserving sim-only authority.
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Other Financial Intermediation|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 44, "total_count": 44}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 44, "total_count": 44}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 44, "total_count": 44}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 44, "total_count": 44}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 44, "total_count": 44}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 61. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_passenger_air_tran`

- title: Swing LDM source field follow-up: breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Passenger Air Transport|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_decision_matrix`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_ldm_bucket_instrumentation_gap`
- confidence: `postclose_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close Swing LDM bucket source-quality gaps while preserving sim-only authority.
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Passenger Air Transport|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 13, "total_count": 13}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 13, "total_count": 13}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 13, "total_count": 13}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 13, "total_count": 13}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 13, "total_count": 13}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 62. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_real_estate_activi`

- title: Swing LDM source field follow-up: breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Real Estate Activities with Own or Leased Property|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_decision_matrix`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_ldm_bucket_instrumentation_gap`
- confidence: `postclose_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close Swing LDM bucket source-quality gaps while preserving sim-only authority.
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Real Estate Activities with Own or Leased Property|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 29, "total_count": 29}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 29, "total_count": 29}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 29, "total_count": 29}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 29, "total_count": 29}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 29, "total_count": 29}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_real_estate_activi", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 63. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_sea_and_coastal_wa`

- title: Swing LDM source field follow-up: breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Sea and Coastal Water Transport|운송_해운|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_decision_matrix`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_ldm_bucket_instrumentation_gap`
- confidence: `postclose_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close Swing LDM bucket source-quality gaps while preserving sim-only authority.
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Sea and Coastal Water Transport|운송_해운|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 20, "total_count": 20}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 20, "total_count": 20}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 20, "total_count": 20}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 20, "total_count": 20}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 20, "total_count": 20}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 64. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_trust_and_collecti`

- title: Swing LDM source field follow-up: breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Trust and collective Investment Businesses|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_decision_matrix`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_ldm_bucket_instrumentation_gap`
- confidence: `postclose_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close Swing LDM bucket source-quality gaps while preserving sim-only authority.
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Trust and collective Investment Businesses|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 11, "total_count": 11}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 11, "total_count": 11}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 11, "total_count": 11}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 11, "total_count": 11}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 11, "total_count": 11}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 65. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_banking_and_savings_instit`

- title: Swing LDM source field follow-up: breakout_confirm_entry|risk_capped|mae_stop_time_stop|Banking and Savings Institutions|은행|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_decision_matrix`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_ldm_bucket_instrumentation_gap`
- confidence: `postclose_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close Swing LDM bucket source-quality gaps while preserving sim-only authority.
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|risk_capped|mae_stop_time_stop|Banking and Savings Institutions|은행|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 14, "total_count": 14}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 14, "total_count": 14}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 14, "total_count": 14}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 14, "total_count": 14}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 14, "total_count": 14}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_risk_capped_mae_stop_tim", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_risk_capped_mae_stop_tim", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 66. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_of_electronic_`

- title: Swing LDM source field follow-up: breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Electronic Components|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_decision_matrix`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_ldm_bucket_instrumentation_gap`
- confidence: `postclose_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close Swing LDM bucket source-quality gaps while preserving sim-only authority.
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Electronic Components|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 28, "total_count": 28}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 28, "total_count": 28}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 28, "total_count": 28}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 28, "total_count": 28}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 28, "total_count": 28}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_risk_capped_mae_stop_tim", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_risk_capped_mae_stop_tim", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 67. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_other_financial_intermedia`

- title: Swing LDM source field follow-up: breakout_confirm_entry|risk_capped|mae_stop_time_stop|Other Financial Intermediation|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_decision_matrix`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_ldm_bucket_instrumentation_gap`
- confidence: `postclose_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close Swing LDM bucket source-quality gaps while preserving sim-only authority.
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|risk_capped|mae_stop_time_stop|Other Financial Intermediation|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 34, "total_count": 34}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 34, "total_count": 34}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 34, "total_count": 34}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 34, "total_count": 34}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 34, "total_count": 34}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_risk_capped_mae_stop_tim", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_risk_capped_mae_stop_tim", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 68. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_real_estate_activities_wit`

- title: Swing LDM source field follow-up: breakout_confirm_entry|risk_capped|mae_stop_time_stop|Real Estate Activities with Own or Leased Property|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_decision_matrix`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_ldm_bucket_instrumentation_gap`
- confidence: `postclose_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close Swing LDM bucket source-quality gaps while preserving sim-only authority.
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|risk_capped|mae_stop_time_stop|Real Estate Activities with Own or Leased Property|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 31, "total_count": 31}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 31, "total_count": 31}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 31, "total_count": 31}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 31, "total_count": 31}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 31, "total_count": 31}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_real_estate_activities_wit", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_risk_capped_mae_stop_tim", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 69. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_sea_and_coastal_water_tran`

- title: Swing LDM source field follow-up: breakout_confirm_entry|risk_capped|mae_stop_time_stop|Sea and Coastal Water Transport|운송_해운|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_decision_matrix`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_ldm_bucket_instrumentation_gap`
- confidence: `postclose_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close Swing LDM bucket source-quality gaps while preserving sim-only authority.
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|risk_capped|mae_stop_time_stop|Sea and Coastal Water Transport|운송_해운|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 24, "total_count": 24}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 24, "total_count": 24}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 24, "total_count": 24}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 24, "total_count": 24}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 24, "total_count": 24}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_risk_capped_mae_stop_tim", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_risk_capped_mae_stop_tim", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 70. `order_swing_ldm_selection_discovery_arm_attribution_pullback_limit_entry_risk_capped_mae_stop_time_stop_real_estate_activities_with_`

- title: Swing LDM source field follow-up: pullback_limit_entry|risk_capped|mae_stop_time_stop|Real Estate Activities with Own or Leased Property|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_decision_matrix`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_ldm_bucket_instrumentation_gap`
- confidence: `postclose_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close Swing LDM bucket source-quality gaps while preserving sim-only authority.
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=pullback_limit_entry|risk_capped|mae_stop_time_stop|Real Estate Activities with Own or Leased Property|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 31, "total_count": 31}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 31, "total_count": 31}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 31, "total_count": 31}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 31, "total_count": 31}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 31, "total_count": 31}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_pullback_limit_entry_risk_capped_mae_stop_time_", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_pullback_limit_entry_risk_capped_mae_stop_time_", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 71. `order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden`

- title: Swing lifecycle bucket discovery handoff follow-up: swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_b99781db765f
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_bucket_discovery`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_bucket_discovery`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_bucket_handoff_or_contract_gap`
- confidence: `postclose_bucket_discovery_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep Swing bucket discovery handoff explicit without allowing sim-only output to mutate real runtime.
- evidence: `bucket_id=swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_b99781db765f`, `canonical_bucket=-`, `legacy_raw_bucket_key=-`, `ai_tier2_taxonomy_decision=-`, `ai_tier2_selected_source=-`, `classification_state=code_patch_required`, `reason=swing_ldm_bucket_contract_or_source_quality_gap`, `source_workorder_id=-`, `parent_bucket_id=swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_b99781db765f`, `decision_authority=swing_ldm_bucket_discovery_sim_auto`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Swing bucket discovery candidates and workorders should be visible in EV, runtime summary, workorder, and verifier.
- files_likely_touched: `src/engine/swing_lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_ev_report.py`, `src/engine/runtime_approval_summary.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 14, "total_count": 14}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 14, "total_count": 14}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 14, "total_count": 14}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 14, "total_count": 14}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 14, "total_count": 14}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 4, "repeat_key": "order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden", "repeat_signature": "sig:swing_lifecycle_bucket_discovery|swing_lifecycle_bucket_discovery|selection|swing_bucket_handoff_or_contract_gap||swing_lifecycle_bucket_discovery_handoff_follow_up_swing_bucket_selection_discov", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 72. `order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_risk_cap`

- title: Swing lifecycle bucket discovery handoff follow-up: swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_o_d1ec8c1ded70
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_bucket_discovery`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_bucket_discovery`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_bucket_handoff_or_contract_gap`
- confidence: `postclose_bucket_discovery_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep Swing bucket discovery handoff explicit without allowing sim-only output to mutate real runtime.
- evidence: `bucket_id=swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_o_d1ec8c1ded70`, `canonical_bucket=-`, `legacy_raw_bucket_key=-`, `ai_tier2_taxonomy_decision=-`, `ai_tier2_selected_source=-`, `classification_state=code_patch_required`, `reason=swing_ldm_bucket_contract_or_source_quality_gap`, `source_workorder_id=-`, `parent_bucket_id=swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_o_d1ec8c1ded70`, `decision_authority=swing_ldm_bucket_discovery_sim_auto`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Swing bucket discovery candidates and workorders should be visible in EV, runtime summary, workorder, and verifier.
- files_likely_touched: `src/engine/swing_lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_ev_report.py`, `src/engine/runtime_approval_summary.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 28, "total_count": 28}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 28, "total_count": 28}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 28, "total_count": 28}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 28, "total_count": 28}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 28, "total_count": 28}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 4, "repeat_key": "order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_risk_cap", "repeat_signature": "sig:swing_lifecycle_bucket_discovery|swing_lifecycle_bucket_discovery|selection|swing_bucket_handoff_or_contract_gap||swing_lifecycle_bucket_discovery_handoff_follow_up_swing_bucket_selection_discov", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 73. `order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_pullback_limit_entry_risk_cappe`

- title: Swing lifecycle bucket discovery handoff follow-up: swing_bucket_selection_discovery_arm_attribution_pullback_limit_entry_risk_capped_mae_stop_time_stop_real_estate_act_6b163bac0453
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_bucket_discovery`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_bucket_discovery`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_bucket_handoff_or_contract_gap`
- confidence: `postclose_bucket_discovery_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep Swing bucket discovery handoff explicit without allowing sim-only output to mutate real runtime.
- evidence: `bucket_id=swing_bucket_selection_discovery_arm_attribution_pullback_limit_entry_risk_capped_mae_stop_time_stop_real_estate_act_6b163bac0453`, `canonical_bucket=-`, `legacy_raw_bucket_key=-`, `ai_tier2_taxonomy_decision=-`, `ai_tier2_selected_source=-`, `classification_state=code_patch_required`, `reason=swing_ldm_bucket_contract_or_source_quality_gap`, `source_workorder_id=-`, `parent_bucket_id=swing_bucket_selection_discovery_arm_attribution_pullback_limit_entry_risk_capped_mae_stop_time_stop_real_estate_act_6b163bac0453`, `decision_authority=swing_ldm_bucket_discovery_sim_auto`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Swing bucket discovery candidates and workorders should be visible in EV, runtime summary, workorder, and verifier.
- files_likely_touched: `src/engine/swing_lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_ev_report.py`, `src/engine/runtime_approval_summary.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 31, "total_count": 31}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 31, "total_count": 31}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 31, "total_count": 31}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 31, "total_count": 31}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 31, "total_count": 31}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 4, "repeat_key": "order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_pullback_limit_entry_risk_cappe", "repeat_signature": "sig:swing_lifecycle_bucket_discovery|swing_lifecycle_bucket_discovery|selection|swing_bucket_handoff_or_contract_gap||swing_lifecycle_bucket_discovery_handoff_follow_up_swing_bucket_selection_discov", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 74. `order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_`

- title: Swing lifecycle bucket discovery handoff follow-up: swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manufacture_of_bas
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_bucket_discovery`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_bucket_handoff_or_contract_gap`
- confidence: `postclose_bucket_discovery_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep Swing bucket discovery handoff explicit without allowing sim-only output to mutate real runtime.
- evidence: `bucket_id=swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manufacture_of_bas`, `canonical_bucket=-`, `legacy_raw_bucket_key=-`, `ai_tier2_taxonomy_decision=-`, `ai_tier2_selected_source=-`, `classification_state=None`, `reason=source_quality_or_instrumentation_gap`, `source_workorder_id=swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manufacture_of_bas`, `parent_bucket_id=-`, `decision_authority=swing_ldm_bucket_discovery_sim_auto`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Swing bucket discovery candidates and workorders should be visible in EV, runtime summary, workorder, and verifier.
- files_likely_touched: `src/engine/swing_lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_ev_report.py`, `src/engine/runtime_approval_summary.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 14, "total_count": 14}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 14, "total_count": 14}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 14, "total_count": 14}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 14, "total_count": 14}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 14, "total_count": 14}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 4, "repeat_key": "order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_", "repeat_signature": "sig:swing_lifecycle_bucket_discovery|swing_lifecycle_decision_matrix|selection|swing_bucket_handoff_or_contract_gap||swing_lifecycle_bucket_discovery_handoff_follow_up_swing_ldm_selection_discovery", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 75. `order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped`

- title: Swing lifecycle bucket discovery handoff follow-up: swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_of_electronic_
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_bucket_discovery`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_bucket_handoff_or_contract_gap`
- confidence: `postclose_bucket_discovery_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep Swing bucket discovery handoff explicit without allowing sim-only output to mutate real runtime.
- evidence: `bucket_id=swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_of_electronic_`, `canonical_bucket=-`, `legacy_raw_bucket_key=-`, `ai_tier2_taxonomy_decision=-`, `ai_tier2_selected_source=-`, `classification_state=None`, `reason=source_quality_or_instrumentation_gap`, `source_workorder_id=swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_of_electronic_`, `parent_bucket_id=-`, `decision_authority=swing_ldm_bucket_discovery_sim_auto`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Swing bucket discovery candidates and workorders should be visible in EV, runtime summary, workorder, and verifier.
- files_likely_touched: `src/engine/swing_lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_ev_report.py`, `src/engine/runtime_approval_summary.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 28, "total_count": 28}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 28, "total_count": 28}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 28, "total_count": 28}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 28, "total_count": 28}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 28, "total_count": 28}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 4, "repeat_key": "order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped", "repeat_signature": "sig:swing_lifecycle_bucket_discovery|swing_lifecycle_decision_matrix|selection|swing_bucket_handoff_or_contract_gap||swing_lifecycle_bucket_discovery_handoff_follow_up_swing_ldm_selection_discovery", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 76. `order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_pullback_limit_entry_risk_capped_m`

- title: Swing lifecycle bucket discovery handoff follow-up: swing_ldm_selection_discovery_arm_attribution_pullback_limit_entry_risk_capped_mae_stop_time_stop_real_estate_activities_with_
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_bucket_discovery`
- lifecycle_stage: `selection`
- target_subsystem: `swing_lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_bucket_handoff_or_contract_gap`
- confidence: `postclose_bucket_discovery_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep Swing bucket discovery handoff explicit without allowing sim-only output to mutate real runtime.
- evidence: `bucket_id=swing_ldm_selection_discovery_arm_attribution_pullback_limit_entry_risk_capped_mae_stop_time_stop_real_estate_activities_with_`, `canonical_bucket=-`, `legacy_raw_bucket_key=-`, `ai_tier2_taxonomy_decision=-`, `ai_tier2_selected_source=-`, `classification_state=None`, `reason=source_quality_or_instrumentation_gap`, `source_workorder_id=swing_ldm_selection_discovery_arm_attribution_pullback_limit_entry_risk_capped_mae_stop_time_stop_real_estate_activities_with_`, `parent_bucket_id=-`, `decision_authority=swing_ldm_bucket_discovery_sim_auto`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Swing bucket discovery candidates and workorders should be visible in EV, runtime summary, workorder, and verifier.
- files_likely_touched: `src/engine/swing_lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_ev_report.py`, `src/engine/runtime_approval_summary.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 31, "total_count": 31}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 31, "total_count": 31}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 31, "total_count": 31}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 31, "total_count": 31}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 31, "total_count": 31}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 4, "repeat_key": "order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_pullback_limit_entry_risk_capped_m", "repeat_signature": "sig:swing_lifecycle_bucket_discovery|swing_lifecycle_decision_matrix|selection|swing_bucket_handoff_or_contract_gap||swing_lifecycle_bucket_discovery_handoff_follow_up_swing_ldm_selection_discovery", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 77. `order_lifecycle_quiet_gap_parent_conflict_rollup`

- title: Lifecycle quiet gap parent conflict/exclusion review
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_bucket_discovery_quiet_gap_rollup`
- lifecycle_stage: `multi_stage`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `existing_family`
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
- evidence: `quiet_gap_count=429`, `rollup_required_count=429`, `sim_live_connected_quiet_gap_count=14`, `quiet_gap_type_counts={'parent_conflict_child': 87, 'exclusion_dimension_candidate': 34, 'positive_source_only_keep_collecting': 393, 'absorbed_into_parent_policy': 10}`, `ai_review_coverage={'status': 'partial', 'shard_count': 5, 'parsed_shard_count': 3, 'reviewed_candidate_count': 3, 'low_coverage': False}`, `runtime_effect=false`, `allowed_runtime_apply=false`, `parent_conflict_resolution_count=8`, `resolution_states={'resolution_blocked_source_quality': 2, 'resolution_complete': 3, 'resolution_blocked_thin_sample': 3}`, `sim_eligible_after_resolution=0`
- parity_contract: -
- next_postclose_metric: quiet_gap_summary rollup counts remain visible until explicitly resolved.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_lifecycle_quiet_gap_parent_conflict_rollup", "repeat_signature": "sig:lifecycle_bucket_discovery_quiet_gap_rollup|lifecycle_bucket_discovery_taxonomy_provenance|multi_stage|quiet_gap_rollup_evidence|lifecycle_bucket_discovery|lifecycle_quiet_gap_parent_conflict_exclusion_review", "review_disposition": "keep_visible_by_design"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 78. `order_lifecycle_quiet_gap_positive_source_only_rollup`

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
- evidence: `quiet_gap_count=429`, `rollup_required_count=429`, `sim_live_connected_quiet_gap_count=14`, `quiet_gap_type_counts={'parent_conflict_child': 87, 'exclusion_dimension_candidate': 34, 'positive_source_only_keep_collecting': 393, 'absorbed_into_parent_policy': 10}`, `ai_review_coverage={'status': 'partial', 'shard_count': 5, 'parsed_shard_count': 3, 'reviewed_candidate_count': 3, 'low_coverage': False}`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: quiet_gap_summary rollup counts remain visible until explicitly resolved.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `terminal_existing_family_evidence`
- root_cause_closure_status: `-`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "terminal_existing_family_evidence", "previous_route": "positive_source_only_review", "repeat_count": 8, "repeat_key": "order_lifecycle_quiet_gap_positive_source_only_rollup", "repeat_signature": "sig:lifecycle_bucket_discovery_quiet_gap_rollup|lifecycle_bucket_discovery_taxonomy_provenance|multi_stage|quiet_gap_rollup_evidence|lifecycle_bucket_discovery|lifecycle_quiet_gap_positive_source_only_review", "review_disposition": "keep_visible_by_design"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose checklist/workorder should keep quiet_gap_summary visible until the gap is implemented, covered by parent policy, deferred for more sample, or explicitly rejected.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 79. `order_lifecycle_source_dimension_gap_rollup`

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
- evidence: `rollup_only_gap_count=61`, `unknown_source_dimensions=9`, `recommended_resolution_counts={'explicit_lifecycle_flow_source_only_blocker': 52, 'entry_label_not_applicable': 1, 'mark_not_applicable_explicitly': 4, 'join_labels_before_bucket_decision': 4}`, `missing_dimension_key_counts={'entry': 34, 'exit': 78, 'holding': 72, 'submit': 82}`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: source_dimension_gap_summary rollup/actionable counts remain visible.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `terminal_existing_family_evidence`
- root_cause_closure_status: `-`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "terminal_existing_family_evidence", "previous_route": "source_dimension_rollup", "repeat_count": 8, "repeat_key": "order_lifecycle_source_dimension_gap_rollup", "repeat_signature": "sig:lifecycle_bucket_discovery_source_dimension_rollup|lifecycle_bucket_discovery_taxonomy_provenance|multi_stage|source_dimension_gap_rollup_evidence|lifecycle_bucket_discovery|unknown", "review_disposition": "keep_visible_by_design"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose checklist/workorder should keep source_dimension_gap_summary visible until actionable gaps are resolved or explicitly marked not applicable.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 80. `order_lifecycle_overnight_bucket_confidence_band_confidence_070p`

- title: LDM overnight bucket attribution follow-up: confidence_band=confidence_070p
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_overnight_bucket_attribution`
- lifecycle_stage: `overnight`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `scalp_sim_overnight_ai_carry`
- threshold_family: `scalp_sim_overnight_ai_carry`
- improvement_type: `overnight_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep SELL_TODAY/HOLD_OVERNIGHT bucket attribution and next-day carry labels connected as source-only evidence for threshold-cycle rolling confirmation.
- evidence: `workorder_id=overnight_bucket_source_quality_1`, `bucket_type=confidence_band`, `bucket_key=confidence_070p`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.overnight_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/scalp_sim_overnight.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM overnight bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": null, "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_lifecycle_overnight_bucket_confidence_band_confidence_070p", "repeat_signature": "sig:lifecycle_decision_matrix_overnight_bucket_attribution|lifecycle_decision_matrix|overnight|overnight_bucket_source_quality_attribution|scalp_sim_overnight_ai_carry|ldm_overnight_bucket_attribution_follow_up_confidence_band_confidence_070p", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 81. `order_lifecycle_overnight_bucket_held_bucket_held_600_1800s_plus`

- title: LDM overnight bucket attribution follow-up: held_bucket=held_600_1800s_plus
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_overnight_bucket_attribution`
- lifecycle_stage: `overnight`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `scalp_sim_overnight_ai_carry`
- threshold_family: `scalp_sim_overnight_ai_carry`
- improvement_type: `overnight_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep SELL_TODAY/HOLD_OVERNIGHT bucket attribution and next-day carry labels connected as source-only evidence for threshold-cycle rolling confirmation.
- evidence: `workorder_id=overnight_bucket_source_quality_2`, `bucket_type=held_bucket`, `bucket_key=held_600_1800s_plus`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.overnight_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/scalp_sim_overnight.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM overnight bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": null, "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_lifecycle_overnight_bucket_held_bucket_held_600_1800s_plus", "repeat_signature": "sig:lifecycle_decision_matrix_overnight_bucket_attribution|lifecycle_decision_matrix|overnight|overnight_bucket_source_quality_attribution|scalp_sim_overnight_ai_carry|ldm_overnight_bucket_attribution_follow_up_held_bucket_held_600_1800s_plus", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 82. `order_lifecycle_overnight_bucket_overnight_action_sell_today`

- title: LDM overnight bucket attribution follow-up: overnight_action=SELL_TODAY
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_overnight_bucket_attribution`
- lifecycle_stage: `overnight`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `scalp_sim_overnight_ai_carry`
- threshold_family: `scalp_sim_overnight_ai_carry`
- improvement_type: `overnight_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep SELL_TODAY/HOLD_OVERNIGHT bucket attribution and next-day carry labels connected as source-only evidence for threshold-cycle rolling confirmation.
- evidence: `workorder_id=overnight_bucket_source_quality_3`, `bucket_type=overnight_action`, `bucket_key=SELL_TODAY`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.overnight_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/scalp_sim_overnight.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM overnight bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": null, "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_lifecycle_overnight_bucket_overnight_action_sell_today", "repeat_signature": "sig:lifecycle_decision_matrix_overnight_bucket_attribution|lifecycle_decision_matrix|overnight|overnight_bucket_source_quality_attribution|scalp_sim_overnight_ai_carry|ldm_overnight_bucket_attribution_follow_up_overnight_action_sell_today", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 83. `order_lifecycle_overnight_bucket_overnight_status_sell_today`

- title: LDM overnight bucket attribution follow-up: overnight_status=SELL_TODAY
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_overnight_bucket_attribution`
- lifecycle_stage: `overnight`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `scalp_sim_overnight_ai_carry`
- threshold_family: `scalp_sim_overnight_ai_carry`
- improvement_type: `overnight_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep SELL_TODAY/HOLD_OVERNIGHT bucket attribution and next-day carry labels connected as source-only evidence for threshold-cycle rolling confirmation.
- evidence: `workorder_id=overnight_bucket_source_quality_4`, `bucket_type=overnight_status`, `bucket_key=SELL_TODAY`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.overnight_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/scalp_sim_overnight.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM overnight bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": null, "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_lifecycle_overnight_bucket_overnight_status_sell_today", "repeat_signature": "sig:lifecycle_decision_matrix_overnight_bucket_attribution|lifecycle_decision_matrix|overnight|overnight_bucket_source_quality_attribution|scalp_sim_overnight_ai_carry|ldm_overnight_bucket_attribution_follow_up_overnight_status_sell_today", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 84. `order_lifecycle_overnight_bucket_peak_profit_band_peak_lt_zero`

- title: LDM overnight bucket attribution follow-up: peak_profit_band=peak_lt_zero
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_overnight_bucket_attribution`
- lifecycle_stage: `overnight`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `scalp_sim_overnight_ai_carry`
- threshold_family: `scalp_sim_overnight_ai_carry`
- improvement_type: `overnight_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep SELL_TODAY/HOLD_OVERNIGHT bucket attribution and next-day carry labels connected as source-only evidence for threshold-cycle rolling confirmation.
- evidence: `workorder_id=overnight_bucket_source_quality_5`, `bucket_type=peak_profit_band`, `bucket_key=peak_lt_zero`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.overnight_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/scalp_sim_overnight.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM overnight bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": null, "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_lifecycle_overnight_bucket_peak_profit_band_peak_lt_zero", "repeat_signature": "sig:lifecycle_decision_matrix_overnight_bucket_attribution|lifecycle_decision_matrix|overnight|overnight_bucket_source_quality_attribution|scalp_sim_overnight_ai_carry|ldm_overnight_bucket_attribution_follow_up_peak_profit_band_peak_lt_zero", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 85. `order_lifecycle_overnight_bucket_price_source_holding_price_samples_last`

- title: LDM overnight bucket attribution follow-up: price_source=holding_price_samples_last
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_overnight_bucket_attribution`
- lifecycle_stage: `overnight`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `scalp_sim_overnight_ai_carry`
- threshold_family: `scalp_sim_overnight_ai_carry`
- improvement_type: `overnight_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep SELL_TODAY/HOLD_OVERNIGHT bucket attribution and next-day carry labels connected as source-only evidence for threshold-cycle rolling confirmation.
- evidence: `workorder_id=overnight_bucket_source_quality_6`, `bucket_type=price_source`, `bucket_key=holding_price_samples_last`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.overnight_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/scalp_sim_overnight.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM overnight bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": null, "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_lifecycle_overnight_bucket_price_source_holding_price_samples_last", "repeat_signature": "sig:lifecycle_decision_matrix_overnight_bucket_attribution|lifecycle_decision_matrix|overnight|overnight_bucket_source_quality_attribution|scalp_sim_overnight_ai_carry|ldm_overnight_bucket_attribution_follow_up_price_source_holding_price_samples_la", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 86. `order_lifecycle_overnight_bucket_source_quality_gate_overnight_decision_coverage`

- title: LDM overnight bucket attribution follow-up: source_quality_gate=overnight_decision_coverage
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_overnight_bucket_attribution`
- lifecycle_stage: `overnight`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `scalp_sim_overnight_ai_carry`
- threshold_family: `scalp_sim_overnight_ai_carry`
- improvement_type: `overnight_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep SELL_TODAY/HOLD_OVERNIGHT bucket attribution and next-day carry labels connected as source-only evidence for threshold-cycle rolling confirmation.
- evidence: `workorder_id=overnight_bucket_source_quality_7`, `bucket_type=source_quality_gate`, `bucket_key=overnight_decision_coverage`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.overnight_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/scalp_sim_overnight.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM overnight bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": null, "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 4, "repeat_key": "order_lifecycle_overnight_bucket_source_quality_gate_overnight_decision_coverage", "repeat_signature": "sig:lifecycle_decision_matrix_overnight_bucket_attribution|lifecycle_decision_matrix|overnight|overnight_bucket_source_quality_attribution|scalp_sim_overnight_ai_carry|ldm_overnight_bucket_attribution_follow_up_source_quality_gate_overnight_decisio", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 87. `order_lifecycle_overnight_bucket_source_stage_scalp_sim_overnight_sell_today`

- title: LDM overnight bucket attribution follow-up: source_stage=scalp_sim_overnight_sell_today
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_overnight_bucket_attribution`
- lifecycle_stage: `overnight`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `scalp_sim_overnight_ai_carry`
- threshold_family: `scalp_sim_overnight_ai_carry`
- improvement_type: `overnight_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep SELL_TODAY/HOLD_OVERNIGHT bucket attribution and next-day carry labels connected as source-only evidence for threshold-cycle rolling confirmation.
- evidence: `workorder_id=overnight_bucket_source_quality_8`, `bucket_type=source_stage`, `bucket_key=scalp_sim_overnight_sell_today`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.overnight_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/scalp_sim_overnight.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM overnight bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": null, "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_lifecycle_overnight_bucket_source_stage_scalp_sim_overnight_sell_today", "repeat_signature": "sig:lifecycle_decision_matrix_overnight_bucket_attribution|lifecycle_decision_matrix|overnight|overnight_bucket_source_quality_attribution|scalp_sim_overnight_ai_carry|ldm_overnight_bucket_attribution_follow_up_source_stage_scalp_sim_overnight_sell", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 88. `order_lifecycle_overnight_bucket_stage_exit`

- title: LDM overnight bucket attribution follow-up: stage=exit
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_overnight_bucket_attribution`
- lifecycle_stage: `overnight`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `scalp_sim_overnight_ai_carry`
- threshold_family: `scalp_sim_overnight_ai_carry`
- improvement_type: `overnight_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep SELL_TODAY/HOLD_OVERNIGHT bucket attribution and next-day carry labels connected as source-only evidence for threshold-cycle rolling confirmation.
- evidence: `workorder_id=overnight_bucket_source_quality_9`, `bucket_type=stage`, `bucket_key=exit`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.overnight_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/scalp_sim_overnight.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM overnight bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": null, "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 89. `order_lifecycle_entry_bucket_chosen_action_wait_requote`

- title: LDM entry bucket attribution follow-up: chosen_action=WAIT_REQUOTE
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
- evidence: `workorder_id=entry_bucket_source_quality_1`, `bucket_type=chosen_action`, `bucket_key=WAIT_REQUOTE`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_lifecycle_entry_bucket_chosen_action_wait_requote", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|lifecycle_decision_matrix|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_chosen_action_wait_requote", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 90. `order_lifecycle_entry_bucket_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale_fresh_liquid`

- title: LDM entry bucket attribution follow-up: combo_entry_spot=score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000
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
- evidence: `workorder_id=entry_bucket_source_quality_4`, `bucket_type=combo_entry_spot`, `bucket_key=score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_lifecycle_entry_bucket_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale_fresh_liquid", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|lifecycle_decision_matrix|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_combo_entry_spot_score_score_60_62_source", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 91. `order_lifecycle_entry_bucket_combo_entry_spot_score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_l`

- title: LDM entry bucket attribution follow-up: combo_entry_spot=score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200
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
- evidence: `workorder_id=entry_bucket_source_quality_5`, `bucket_type=combo_entry_spot`, `bucket_key=score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 4, "repeat_key": "order_lifecycle_entry_bucket_combo_entry_spot_score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_l", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|lifecycle_decision_matrix|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_combo_entry_spot_score_score_63_65_source", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 92. `order_lifecycle_entry_bucket_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_l`

- title: LDM entry bucket attribution follow-up: combo_entry_spot=score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200
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
- evidence: `workorder_id=entry_bucket_source_quality_2`, `bucket_type=combo_entry_spot`, `bucket_key=score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_lifecycle_entry_bucket_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_l", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|lifecycle_decision_matrix|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_combo_entry_spot_score_score_66_69_source", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 93. `order_lifecycle_entry_bucket_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liq`

- title: LDM entry bucket attribution follow-up: combo_entry_spot=score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200
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
- evidence: `workorder_id=entry_bucket_source_quality_3`, `bucket_type=combo_entry_spot`, `bucket_key=score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_lifecycle_entry_bucket_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liq", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|lifecycle_decision_matrix|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_combo_entry_spot_score_score_70p_source_w", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 94. `order_lifecycle_entry_bucket_liquidity_bucket_liquidity_high`

- title: LDM entry bucket attribution follow-up: liquidity_bucket=liquidity_high
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
- evidence: `workorder_id=entry_bucket_source_quality_7`, `bucket_type=liquidity_bucket`, `bucket_key=liquidity_high`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_lifecycle_entry_bucket_liquidity_bucket_liquidity_high", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|lifecycle_decision_matrix|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_liquidity_bucket_liquidity_high", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 95. `order_lifecycle_entry_bucket_overbought_bucket_overbought_normal`

- title: LDM entry bucket attribution follow-up: overbought_bucket=overbought_normal
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
- evidence: `workorder_id=entry_bucket_source_quality_8`, `bucket_type=overbought_bucket`, `bucket_key=overbought_normal`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 96. `order_lifecycle_entry_bucket_score_band_score_66_69`

- title: LDM entry bucket attribution follow-up: score_band=score_66_69
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
- evidence: `workorder_id=entry_bucket_source_quality_9`, `bucket_type=score_band`, `bucket_key=score_66_69`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_lifecycle_entry_bucket_score_band_score_66_69", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|lifecycle_decision_matrix|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_score_band_score_66_69", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 97. `order_lifecycle_entry_bucket_score_band_score_70p`

- title: LDM entry bucket attribution follow-up: score_band=score_70p
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
- evidence: `workorder_id=entry_bucket_source_quality_10`, `bucket_type=score_band`, `bucket_key=score_70p`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 98. `order_conversion_lane_key_lineage_active_arm_0c383886ae3c8de3`

- title: Conversion lane blocker follow-up: key_lineage active_arm_0c383886ae3c8de3
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_key_lineage_blocker`
- confidence: `-`
- priority: `25`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_0c383886ae3c8de3`, `blocker_class=key_lineage`, `conversion_impact_rank=25`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_arm_0c383886ae3c8de3", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_0c383886ae3c8de3", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 99. `order_conversion_lane_key_lineage_active_arm_78c1ca03d11c256b`

- title: Conversion lane blocker follow-up: key_lineage active_arm_78c1ca03d11c256b
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_key_lineage_blocker`
- confidence: `-`
- priority: `26`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_78c1ca03d11c256b`, `blocker_class=key_lineage`, `conversion_impact_rank=26`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_conversion_lane_key_lineage_active_arm_78c1ca03d11c256b", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_78c1ca03d11c256b", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 100. `order_conversion_lane_key_lineage_active_arm_7bc3260124b31b77`

- title: Conversion lane blocker follow-up: key_lineage active_arm_7bc3260124b31b77
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_key_lineage_blocker`
- confidence: `-`
- priority: `27`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_7bc3260124b31b77`, `blocker_class=key_lineage`, `conversion_impact_rank=27`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_arm_7bc3260124b31b77", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_7bc3260124b31b77", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 101. `order_conversion_lane_key_lineage_active_arm_d09163dbcf8e6037`

- title: Conversion lane blocker follow-up: key_lineage active_arm_d09163dbcf8e6037
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_key_lineage_blocker`
- confidence: `-`
- priority: `28`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_d09163dbcf8e6037`, `blocker_class=key_lineage`, `conversion_impact_rank=28`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 102. `order_conversion_lane_key_lineage_active_arm_da294c8705564eaf`

- title: Conversion lane blocker follow-up: key_lineage active_arm_da294c8705564eaf
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_key_lineage_blocker`
- confidence: `-`
- priority: `29`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_da294c8705564eaf`, `blocker_class=key_lineage`, `conversion_impact_rank=29`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_arm_da294c8705564eaf", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_da294c8705564eaf", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 103. `order_conversion_lane_key_lineage_active_seed_0629ba2d0f4dd524`

- title: Conversion lane blocker follow-up: key_lineage active_seed_0629ba2d0f4dd524
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_key_lineage_blocker`
- confidence: `-`
- priority: `30`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_0629ba2d0f4dd524`, `blocker_class=key_lineage`, `conversion_impact_rank=30`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_conversion_lane_key_lineage_active_seed_0629ba2d0f4dd524", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_seed_0629ba2d0f4dd524", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 104. `order_conversion_lane_key_lineage_active_seed_06fce89fd3a136e6`

- title: Conversion lane blocker follow-up: key_lineage active_seed_06fce89fd3a136e6
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_key_lineage_blocker`
- confidence: `-`
- priority: `31`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_06fce89fd3a136e6`, `blocker_class=key_lineage`, `conversion_impact_rank=31`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_conversion_lane_key_lineage_active_seed_06fce89fd3a136e6", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_seed_06fce89fd3a136e6", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 105. `order_conversion_lane_key_lineage_active_seed_07677c2e78c144df`

- title: Conversion lane blocker follow-up: key_lineage active_seed_07677c2e78c144df
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_key_lineage_blocker`
- confidence: `-`
- priority: `32`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_07677c2e78c144df`, `blocker_class=key_lineage`, `conversion_impact_rank=32`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_conversion_lane_key_lineage_active_seed_07677c2e78c144df", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_seed_07677c2e78c144df", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 106. `order_conversion_lane_key_lineage_active_seed_0a9736d86332c717`

- title: Conversion lane blocker follow-up: key_lineage active_seed_0a9736d86332c717
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_key_lineage_blocker`
- confidence: `-`
- priority: `33`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_0a9736d86332c717`, `blocker_class=key_lineage`, `conversion_impact_rank=33`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_seed_0a9736d86332c717", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_seed_0a9736d86332c717", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 107. `order_conversion_lane_key_lineage_active_seed_0cae3a2115d07d28`

- title: Conversion lane blocker follow-up: key_lineage active_seed_0cae3a2115d07d28
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_key_lineage_blocker`
- confidence: `-`
- priority: `34`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_0cae3a2115d07d28`, `blocker_class=key_lineage`, `conversion_impact_rank=34`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_seed_0cae3a2115d07d28", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_seed_0cae3a2115d07d28", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 108. `order_conversion_lane_key_lineage_active_seed_102cfe8a5ee6ec9b`

- title: Conversion lane blocker follow-up: key_lineage active_seed_102cfe8a5ee6ec9b
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_key_lineage_blocker`
- confidence: `-`
- priority: `35`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_102cfe8a5ee6ec9b`, `blocker_class=key_lineage`, `conversion_impact_rank=35`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 4, "repeat_key": "order_conversion_lane_key_lineage_active_seed_102cfe8a5ee6ec9b", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_seed_102cfe8a5ee6ec9b", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 109. `order_conversion_lane_key_lineage_active_seed_1096e7d8ada1ee8a`

- title: Conversion lane blocker follow-up: key_lineage active_seed_1096e7d8ada1ee8a
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_key_lineage_blocker`
- confidence: `-`
- priority: `36`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_1096e7d8ada1ee8a`, `blocker_class=key_lineage`, `conversion_impact_rank=36`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_seed_1096e7d8ada1ee8a", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_seed_1096e7d8ada1ee8a", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 110. `order_conversion_lane_key_lineage_active_seed_109a6ab7807c9624`

- title: Conversion lane blocker follow-up: key_lineage active_seed_109a6ab7807c9624
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_key_lineage_blocker`
- confidence: `-`
- priority: `37`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_109a6ab7807c9624`, `blocker_class=key_lineage`, `conversion_impact_rank=37`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_seed_109a6ab7807c9624", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_seed_109a6ab7807c9624", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 111. `order_conversion_lane_key_lineage_active_seed_117652d76d63ff34`

- title: Conversion lane blocker follow-up: key_lineage active_seed_117652d76d63ff34
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_key_lineage_blocker`
- confidence: `-`
- priority: `38`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_117652d76d63ff34`, `blocker_class=key_lineage`, `conversion_impact_rank=38`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_conversion_lane_key_lineage_active_seed_117652d76d63ff34", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_seed_117652d76d63ff34", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 112. `order_conversion_lane_key_lineage_active_seed_120deebc97eec625`

- title: Conversion lane blocker follow-up: key_lineage active_seed_120deebc97eec625
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_key_lineage_blocker`
- confidence: `-`
- priority: `39`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_120deebc97eec625`, `blocker_class=key_lineage`, `conversion_impact_rank=39`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_conversion_lane_key_lineage_active_seed_120deebc97eec625", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_seed_120deebc97eec625", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 113. `order_conversion_lane_key_lineage_active_seed_1307cd5fa2e96df9`

- title: Conversion lane blocker follow-up: key_lineage active_seed_1307cd5fa2e96df9
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_key_lineage_blocker`
- confidence: `-`
- priority: `40`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_1307cd5fa2e96df9`, `blocker_class=key_lineage`, `conversion_impact_rank=40`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_seed_1307cd5fa2e96df9", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_seed_1307cd5fa2e96df9", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 114. `order_conversion_lane_key_lineage_active_seed_1c230a4bff6aa0e4`

- title: Conversion lane blocker follow-up: key_lineage active_seed_1c230a4bff6aa0e4
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_key_lineage_blocker`
- confidence: `-`
- priority: `41`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_1c230a4bff6aa0e4`, `blocker_class=key_lineage`, `conversion_impact_rank=41`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_conversion_lane_key_lineage_active_seed_1c230a4bff6aa0e4", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_seed_1c230a4bff6aa0e4", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 115. `order_conversion_lane_key_lineage_active_seed_1c60438d887840e3`

- title: Conversion lane blocker follow-up: key_lineage active_seed_1c60438d887840e3
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_key_lineage_blocker`
- confidence: `-`
- priority: `42`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_1c60438d887840e3`, `blocker_class=key_lineage`, `conversion_impact_rank=42`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 116. `order_conversion_lane_key_lineage_active_seed_1fc6245cf630af1c`

- title: Conversion lane blocker follow-up: key_lineage active_seed_1fc6245cf630af1c
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_key_lineage_blocker`
- confidence: `-`
- priority: `43`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_1fc6245cf630af1c`, `blocker_class=key_lineage`, `conversion_impact_rank=43`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 117. `order_conversion_lane_key_lineage_active_seed_24a139dfb60cb311`

- title: Conversion lane blocker follow-up: key_lineage active_seed_24a139dfb60cb311
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_key_lineage_blocker`
- confidence: `-`
- priority: `44`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_24a139dfb60cb311`, `blocker_class=key_lineage`, `conversion_impact_rank=44`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_conversion_lane_key_lineage_active_seed_24a139dfb60cb311", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_seed_24a139dfb60cb311", "review_disposition": "review_required"}`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

## Non-Selected Source Orders

아래 항목은 source order로 분류됐지만 selected implementation order에는 포함되지 않았다. 재작업 지시 시 `decision`, `decision_reason`, `runtime_effect`를 먼저 재판정한다.

### N1. `order_perf_buy_funnel_json_scan`

- title: BUY funnel sentinel field scan without repeated json.dumps
- decision: `attach_existing_family`
- decision_reason: report-only performance implementation is already present in code; keep the order as provenance and validate through regenerated reports/tests instead of re-implementing
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `buy_funnel_sentinel`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`
- acceptance_tests: `pytest src/tests/test_buy_funnel_sentinel.py`, `BUY Sentinel classification parity on same raw/cache input`

### N2. `order_latency_guard_miss_ev_recovery`

- title: latency guard miss EV recovery
- decision: `attach_existing_family`
- decision_reason: instrumentation/provenance contract is already implemented; keep as report source for the existing family
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `runtime_instrumentation`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_but_waiting_sample`
- files_likely_touched: `src/engine/sniper_performance_tuning_report.py`, `src/engine/daily_threshold_cycle_report.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N3. `order_perf_daily_report_bulk_history`

- title: Daily report market snapshot bulk history query
- decision: `attach_existing_family`
- decision_reason: report-only performance implementation is already present in code; keep the order as provenance and validate through regenerated reports/tests instead of re-implementing
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `daily_report`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- files_likely_touched: `src/engine/daily_report_service.py`
- acceptance_tests: `pytest src/tests/test_daily_report_service.py src/tests/test_daily_report.py`, `daily report output parity on injected DB/model fixture`

### N4. `order_perf_daily_report_engine_singleton`

- title: Daily report SQLAlchemy engine singleton
- decision: `attach_existing_family`
- decision_reason: report-only performance implementation is already present in code; keep the order as provenance and validate through regenerated reports/tests instead of re-implementing
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `daily_report`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- files_likely_touched: `src/engine/daily_report_service.py`
- acceptance_tests: `pytest src/tests/test_daily_report_service.py src/tests/test_daily_report.py`, `engine creation count regression test`

### N5. `order_swing_gatekeeper_reject_threshold_review`

- title: swing gatekeeper reject threshold review
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `swing_improvement_automation`
- lifecycle_stage: `entry`
- target_subsystem: `swing_entry`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_existing_family_evidence`
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/swing_lifecycle_audit.py`
- acceptance_tests: `pytest swing lifecycle audit tests`, `pytest state handler fast signatures`

### N6. `order_swing_pattern_lab_deepseek_scale_in_events_observed`

- title: Scale-in events observed for swing positions
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `swing_pattern_lab_automation`
- lifecycle_stage: `scale_in`
- target_subsystem: `swing_scale_in`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_existing_family_evidence`
- files_likely_touched: `src/engine/swing_lifecycle_audit.py`, `src/engine/swing_selection_funnel_report.py`, `src/model/common_v2.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_model_selection_funnel_repair.py`, `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_deepseek_swing_pattern_lab.py`

### N7. `order_perf_recommend_update_vectorization`

- title: Recommendation and update_kospi vectorized membership checks
- decision: `attach_existing_family`
- decision_reason: report-only performance implementation is already present in code; keep the order as provenance and validate through regenerated reports/tests instead of re-implementing
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `swing_daily_recommendation`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- files_likely_touched: `src/model/recommend_daily_v2.py`, `src/utils/update_kospi.py`
- acceptance_tests: `pytest src/tests/test_swing_retrain_automation.py src/tests/test_swing_feature_ssot.py`, `recommendation CSV and diagnostics parity`

### N8. `order_swing_holding_exit_contract_gap_review`

- title: swing holding/exit contract gap review
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_improvement_automation`
- lifecycle_stage: `holding_exit`
- target_subsystem: `swing_holding_exit`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- files_likely_touched: `src/engine/swing_lifecycle_audit.py`, `src/engine/ai_prompt_contracts.py`, `src/engine/ai_engine_openai.py`
- acceptance_tests: `pytest swing lifecycle audit tests`

### N9. `order_swing_scale_in_contract_gap_review`

- title: swing scale-in contract gap review
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_improvement_automation`
- lifecycle_stage: `scale_in`
- target_subsystem: `swing_scale_in`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- files_likely_touched: `src/engine/swing_lifecycle_audit.py`, `src/engine/sniper_scale_in.py`
- acceptance_tests: `pytest swing lifecycle audit tests`

### N10. `order_perf_swing_simulation_iteration`

- title: Swing simulation iteration and quote grouping
- decision: `attach_existing_family`
- decision_reason: report-only performance implementation is already present in code; keep the order as provenance and validate through regenerated reports/tests instead of re-implementing
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `swing_daily_simulation`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- files_likely_touched: `src/engine/swing_daily_simulation_report.py`
- acceptance_tests: `pytest src/tests/test_swing_model_selection_funnel_repair.py`, `swing simulation JSON parity on injected sources`

### N11. `order_swing_discovery_label_contract_gap_review`

- title: swing discovery label contract gap review
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_improvement_automation`
- lifecycle_stage: `selection`
- target_subsystem: `swing_strategy_discovery`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- files_likely_touched: `src/engine/swing_strategy_discovery_label_builder.py`, `src/engine/swing_strategy_discovery_ev_report.py`
- acceptance_tests: `pytest swing lifecycle audit tests`

### N12. `order_swing_scale_in_ofi_qi_bearish_risk_review`

- title: swing scale-in OFI/QI bearish risk review
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `swing_improvement_automation`
- lifecycle_stage: `scale_in`
- target_subsystem: `swing_scale_in`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_existing_family_evidence`
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/swing_lifecycle_audit.py`
- acceptance_tests: `pytest sniper scale-in tests`, `pytest swing lifecycle audit tests`

### N13. `order_panic_sell_defense_lifecycle_transition_pack`

- title: panic sell defense lifecycle transition pack
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `threshold_cycle_calibration_source_bundle`
- lifecycle_stage: `holding_exit`
- target_subsystem: `panic_sell_defense`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_but_waiting_sample`
- files_likely_touched: `src/engine/panic_sell_defense_report.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/plan-korStockScanPerformanceOptimization.rebase.md`
- acceptance_tests: `pytest panic sell defense/report lifecycle tests`, `pytest src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py`

### N14. `order_perf_monitor_snapshot_stream_tail`

- title: Monitor snapshot runtime streaming tail read
- decision: `attach_existing_family`
- decision_reason: report-only performance implementation is already present in code; keep the order as provenance and validate through regenerated reports/tests instead of re-implementing
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `monitor_snapshot`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- files_likely_touched: `src/engine/monitor_snapshot_runtime.py`
- acceptance_tests: `pytest src/tests/test_log_archive_service.py`, `last valid JSON line parity`

### N15. `order_swing_exit_ofi_qi_smoothing_distribution`

- title: swing exit OFI/QI smoothing distribution
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `swing_improvement_automation`
- lifecycle_stage: `holding_exit`
- target_subsystem: `swing_holding_exit`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_existing_family_evidence`
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/swing_lifecycle_audit.py`
- acceptance_tests: `pytest OFI smoothing tests`, `pytest swing lifecycle audit tests`

### N16. `order_swing_strategy_discovery_source_quality_followup`

- title: swing strategy discovery label/source quality follow-up
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_strategy_discovery_ev`
- lifecycle_stage: `source_quality`
- target_subsystem: `swing_strategy_discovery_sim`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- files_likely_touched: `src/engine/swing_strategy_discovery_label_builder.py`, `src/engine/swing_strategy_discovery_ev_report.py`, `src/engine/swing_sector_theme_source.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_strategy_discovery_label_builder.py src/tests/test_swing_strategy_discovery_ev_report.py src/tests/test_swing_sector_theme_source.py`

### N17. `order_panic_buying_source_quality_market_breadth_micro_coverage`

- title: panic buying source-quality market breadth and micro coverage
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `threshold_cycle_calibration_source_bundle`
- lifecycle_stage: `source_quality`
- target_subsystem: `panic_buying`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- files_likely_touched: `src/engine/panic_buying_report.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/plan-korStockScanPerformanceOptimization.rebase.md`, `docs/code-improvement-workorders/panic_buying_regime_mode_v2_2026-05-14.md`
- acceptance_tests: `pytest src/tests/test_panic_buying_report.py`, `pytest src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py`

### N18. `order_perf_final_ensemble_records`

- title: Final ensemble scanner records conversion without iterrows
- decision: `attach_existing_family`
- decision_reason: report-only performance implementation is already present in code; keep the order as provenance and validate through regenerated reports/tests instead of re-implementing
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `final_ensemble_scanner`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- files_likely_touched: `src/scanners/final_ensemble_scanner.py`
- acceptance_tests: `pytest src/tests/test_swing_model_selection_funnel_repair.py`, `V2 CSV pick list parity`

### N19. `order_swing_strategy_discovery_avoid_bucket_review`

- title: swing strategy discovery avoid bucket report enrichment
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_strategy_discovery_ev`
- lifecycle_stage: `selection`
- target_subsystem: `swing_strategy_discovery_sim`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- files_likely_touched: `src/engine/swing_strategy_discovery_ev_report.py`, `docs/swing-strategy-discovery-sim-v1.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_strategy_discovery_ev_report.py src/tests/test_build_code_improvement_workorder.py`

### N20. `order_swing_pattern_lab_deepseek_entry_no_submissions`

- title: All selected candidates failed to reach order submission
- decision: `design_family_candidate`
- decision_reason: pattern lab can only propose source-only family design input; LDM/discovery/runtime bridge contracts must close before any auto_bounded_live consideration
- source_report_type: `swing_pattern_lab_automation`
- lifecycle_stage: `entry`
- target_subsystem: `swing_entry_funnel`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_design_family_candidate`
- files_likely_touched: `src/engine/swing_lifecycle_audit.py`, `src/engine/swing_selection_funnel_report.py`, `src/model/common_v2.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_model_selection_funnel_repair.py`, `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_deepseek_swing_pattern_lab.py`

### N21. `order_no_acute_observability_alert`

- title: No acute observability alert
- decision: `design_family_candidate`
- decision_reason: pattern lab can only propose source-only family design input; LDM/discovery/runtime bridge contracts must close before any auto_bounded_live consideration
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `scalping_logic`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_design_family_candidate`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N22. `order_liquidity_gate_miss_ev_recovery`

- title: liquidity gate miss EV recovery
- decision: `design_family_candidate`
- decision_reason: pattern lab can only propose source-only family design input; LDM/discovery/runtime bridge contracts must close before any auto_bounded_live consideration
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `entry_filter_quality`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_design_family_candidate`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N23. `order_swing_ai_contract_structured_output_eval`

- title: swing AI contract structured output eval
- decision: `design_family_candidate`
- decision_reason: finding needs family design; allowed_runtime_apply remains false until metadata/tests/guards are closed
- source_report_type: `swing_improvement_automation`
- lifecycle_stage: `ai_contract`
- target_subsystem: `swing_ai_contract`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_design_family_candidate`
- files_likely_touched: `src/engine/ai_prompt_contracts.py`, `src/engine/ai_engine_openai.py`, `src/engine/ai_response_contracts.py`
- acceptance_tests: `pytest OpenAI transport/schema tests`, `pytest swing lifecycle audit tests`

### N24. `order_overbought_gate_miss_ev_recovery`

- title: overbought gate miss EV recovery
- decision: `design_family_candidate`
- decision_reason: pattern lab can only propose source-only family design input; LDM/discovery/runtime bridge contracts must close before any auto_bounded_live consideration
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `entry_filter_quality`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_design_family_candidate`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N25. `order_ai_threshold_miss_ev_recovery`

- title: AI threshold miss EV recovery
- decision: `defer_evidence`
- decision_reason: single-lab finding; keep as low-confidence backlog until repeated by fresh lab or EV report
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `entry_funnel`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_deferred_evidence`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_missed_entry_counterfactual.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N26. `order_swing_pattern_lab_deepseek_ofi_qi_smoothing_review`

- title: OFI/QI exit smoothing action distribution
- decision: `defer_evidence`
- decision_reason: single-lab finding; keep as low-confidence backlog until repeated by fresh lab or EV report
- source_report_type: `swing_pattern_lab_automation`
- lifecycle_stage: `ofi_qi`
- target_subsystem: `swing_micro_context`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_deferred_evidence`
- files_likely_touched: `src/engine/swing_lifecycle_audit.py`, `src/engine/swing_selection_funnel_report.py`, `src/model/common_v2.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_model_selection_funnel_repair.py`, `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_deepseek_swing_pattern_lab.py`

### N27. `order_partial_only_표류_전용_timeout_report_only`

- title: partial-only 표류 전용 timeout report-only
- decision: `defer_evidence`
- decision_reason: single-lab finding; keep as low-confidence backlog until repeated by fresh lab or EV report
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `holding_exit`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_deferred_evidence`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N28. `order_split_entry_rebase_수량_정합성_report_only_감사`

- title: split-entry rebase 수량 정합성 report-only 감사
- decision: `defer_evidence`
- decision_reason: single-lab finding; keep as low-confidence backlog until repeated by fresh lab or EV report
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `holding_exit`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_deferred_evidence`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N29. `order_동일_종목_split_entry_soft_stop_재진입_cooldown_report_only`

- title: 동일 종목 split-entry soft-stop 재진입 cooldown report-only
- decision: `defer_evidence`
- decision_reason: single-lab finding; keep as low-confidence backlog until repeated by fresh lab or EV report
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `holding_exit`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_deferred_evidence`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N30. `order_perf_kiwoom_orders_http_session_review`

- title: Kiwoom orders HTTP session reuse manual review
- decision: `defer_evidence`
- decision_reason: broker request lifecycle may change; requires manual review before implementation
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `broker_transport`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_deferred_evidence`
- files_likely_touched: `src/engine/kiwoom_orders.py`
- acceptance_tests: `pytest src/tests/test_kiwoom_orders.py src/tests/test_sniper_scale_in.py`

### N31. `order_perf_config_cache_scope_review`

- title: Config cache scope review
- decision: `defer_evidence`
- decision_reason: runtime config reload semantics are not yet bounded
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `config_loading`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_deferred_evidence`
- files_likely_touched: `src/utils/constants.py`, `src/utils/kiwoom_utils.py`
- acceptance_tests: `pytest config/import smoke tests`

### N32. `order_perf_dashboard_db_pool_review`

- title: Legacy dashboard DB connection pool review
- decision: `defer_evidence`
- decision_reason: legacy DB write is opt-in and pool lifetime risk needs separate review
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `dashboard_legacy_db`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_deferred_evidence`
- files_likely_touched: `src/engine/dashboard_data_repository.py`
- acceptance_tests: `pytest src/tests/test_dashboard_data_repository.py`

### N33. `order_partial_fallback_확대_직후_즉시_재평가_report_only`

- title: partial → fallback 확대 직후 즉시 재평가 report-only
- decision: `reject`
- decision_reason: fallback revival or shadow reintroduction conflicts with current Plan Rebase policy
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `holding_exit`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_rejected`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N34. `order_perf_kiwoom_ws_tick_parse_fastpath`

- title: Kiwoom websocket tick parsing fast path
- decision: `reject`
- decision_reason: quote/data-quality semantics can change; requires separate data-quality approval owner
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `quote_data_quality`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_rejected`
- files_likely_touched: `src/engine/kiwoom_websocket.py`
- acceptance_tests: `pytest websocket parsing/data-quality tests`

### N35. `order_perf_raw_event_suppression_out_of_scope`

- title: Raw pipeline event suppression out of scope
- decision: `reject`
- decision_reason: raw suppression is governed by pipeline event V2 suppress guard
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `pipeline_event_storage`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_rejected`
- files_likely_touched: `src/utils/pipeline_event_logger.py`
- acceptance_tests: `pytest pipeline event verbosity tests`

## 자동화체인 재투입

- 구현 결과는 `2026-06-18` 이후 postclose `threshold_cycle`, `scalping_pattern_lab_automation`, `threshold_cycle_ev`가 자동으로 다시 읽는다.
- 구현자가 수동으로 threshold 값을 바꾸는 것이 아니라, source/report/provenance를 닫아 다음 calibration이 판단하게 한다.
- 다음 Codex 세션 입력 문구: `none_for_bucket_discovery_classification`

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
