# Code Improvement Workorder - 2026-07-08

## 목적

- Postclose 자동화가 생성한 `code_improvement_order`를 Codex 실행용 작업지시서로 변환한다.
- 입력은 scalping pattern lab automation, swing lifecycle improvement automation, swing pattern lab automation을 함께 포함할 수 있다.
- 이 문서는 repo/runtime을 직접 변경하지 않는다. 사용자가 이 문서를 Codex 세션에 넣고 구현을 요청하는 지점만 사람 개입으로 남긴다.
- 구현 후 자동화체인 재투입은 다음 postclose report, threshold calibration, daily EV report가 담당한다.

## Source

- pattern_lab_automation: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-07-08.json`
- swing_improvement_automation: `/home/ubuntu/KORStockScan/data/report/swing_improvement_automation/swing_improvement_automation_2026-07-08.json`
- swing_pattern_lab_automation: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-07-08.json`
- swing_strategy_discovery_ev: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-07-08.json`
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-07-08.json`
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-07-08.json`
- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-08.json`
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-07-08.json`
- threshold_cycle_calibration: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_calibration/threshold_cycle_calibration_2026-07-08_postclose.json`
- pipeline_event_verbosity: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-07-08.json`
- observation_source_quality_audit: `/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-08.json`
- ai_watching_score_smoothing_diagnostic: `/home/ubuntu/KORStockScan/data/report/ai_watching_score_smoothing_diagnostic/ai_watching_score_smoothing_diagnostic_2026-07-08.json`
- codebase_performance_workorder: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-07-08.json`
- pattern_lab_currentness_audit: `/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-07-08.json`
- pattern_lab_ai_review: `/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-07-08.json`
- producer_gap_discovery: `/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-07-08.json`
- stage_hook_workorder_discovery: `/home/ubuntu/KORStockScan/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_2026-07-08.json`
- stage_hook_runtime_scaffold: `/home/ubuntu/KORStockScan/data/report/stage_hook_runtime_scaffold/stage_hook_runtime_scaffold_2026-07-08.json`
- buy_funnel_sentinel: `/home/ubuntu/KORStockScan/data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-07-08.json`
- generated_at: `2026-07-08T22:20:22+09:00`
- generation_id: `2026-07-08-d4803754427d`
- source_hash: `d4803754427d4760e1eec658b685f57c1d145a0a60638722a2739d25cfa5acb6`

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
- previous_generation_id: `2026-07-08-11b40b57410a`
- previous_source_hash: `11b40b57410aa0b549fcf1883810072010de343ef782f27c6f788f16ab623a4c`
- new_order_ids: `[]`
- removed_order_ids: `['order_active_seed_or_ldm_match_missing_contract_gap']`
- decision_changed_order_ids: `[]`

## Summary

- source_order_count: `146`
- scalping_source_order_count: `10`
- swing_source_order_count: `8`
- swing_entry_bottleneck_primary: `SWING_ENTRY_BOTTLENECK_OBSERVE`
- swing_entry_bottleneck_selected: `False`
- swing_lab_source_order_count: `3`
- swing_strategy_discovery_source_order_count: `2`
- swing_lifecycle_matrix_source_order_count: `25`
- swing_lifecycle_bucket_discovery_source_order_count: `62`
- pattern_lab_currentness_source_order_count: `0`
- pattern_lab_ai_review_source_order_count: `0`
- threshold_ev_source_order_count: `20`
- entry_hurdle_backtest_source_order_count: `0`
- lifecycle_submit_bucket_source_order_count: `0`
- lifecycle_holding_exit_bucket_source_order_count: `17`
- pipeline_event_verbosity_source_order_count: `0`
- observation_source_quality_source_order_count: `0`
- codebase_performance_source_order_count: `12`
- buy_funnel_sentinel_source_order_count: `6`
- entry_submit_drought_selected: `True`
- entry_submit_drought_handoff_missing: `False`
- panic_lifecycle_source_order_count: `2`
- selected_order_count: `105`
- non_selected_order_count: `41`
- source_decision_counts: `{'attach_existing_family': 134, 'design_family_candidate': 3, 'defer_evidence': 6, 'reject': 3}`
- selected_decision_counts: `{'attach_existing_family': 103, 'defer_evidence': 2}`
- selected_route_counts: `{'existing_family': 99, 'ai_review_coverage_review': 1, 'positive_source_only_review': 1, 'source_dimension_rollup': 1, 'join_gap_enrichment': 1, 'instrumentation_order': 2}`
- selected_implement_now_route_count: `0`
- selected_runtime_effect_false_count: `105`
- selected_unimplemented_runtime_effect_false_count: `0`
- selected_unimplemented_route_counts: `{}`
- selected_terminal_non_implement_runtime_effect_false_count: `8`
- selected_terminal_non_implement_route_counts: `{'existing_family': 2, 'ai_review_coverage_review': 1, 'positive_source_only_review': 1, 'source_dimension_rollup': 1, 'join_gap_enrichment': 1, 'instrumentation_order': 2}`
- selected_implement_now_existing_implementation_count: `0`
- selected_implement_now_existing_implementation_order_ids: `[]`
- selected_implement_now_new_runtime_effect_false_count: `0`
- selected_implement_now_new_runtime_effect_false_order_ids: `[]`
- repeat_unresolved_escalation_count: `0`
- repeat_unresolved_escalated_order_ids: `[]`
- repeat_unresolved_structural_blocker_count: `0`
- repeat_unresolved_structural_blocker_order_ids: `[]`
- root_cause_closure_status_counts: `{'handoff_closed_root_cause_open': 20, 'implementation_done': 1, 'root_cause_closed': 76}`
- implementation_done_count: `1`
- artifact_regeneration_required_count: `0`
- handoff_closed_root_cause_open_count: `20`
- root_cause_closed_count: `76`
- needs_followup_workorder_count: `0`
- root_cause_open_top: `[{'order_id': 'order_conversion_lane_key_lineage_active_arm_1661ca30f0d594fd', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_arm_167e2213662b0147', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_arm_2c44a9b1dd392eb3', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_arm_2d256010e69684c1', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_arm_400bb07e38eb1ab2', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_arm_431cb98e1d4adfce', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_arm_518e85a70ac730e3', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_arm_52e8c1f2d0e05882', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_arm_5ed5448f4e3ccb60', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_arm_665f8e1098e38541', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}]`
- selected_terminal_non_implement_longstanding_count: `7`
- selected_terminal_non_implement_longstanding_order_ids: `['order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_overnight_sell_today_rule_scalp_sim_overnight_sell_tod_3355d7a3', 'order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_overnight_sell_today_rule_scalp_sim_overnight_sell_tod_7b698c08', 'order_lifecycle_quiet_gap_ai_review_coverage_rollup', 'order_lifecycle_quiet_gap_positive_source_only_rollup', 'order_lifecycle_source_dimension_gap_rollup', 'order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_euphoria_context_noop_rule_exit_rule_unknown_outcome_o_5f592cef', 'order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_panic_context_warning_rule_exit_rule_unknown_outcome_o_58a13326']`
- selected_longstanding_non_implement_disposition_counts: `{'keep_visible_by_design': 5, 'review_required': 2}`
- selected_longstanding_non_implement_action_required_order_ids: `[]`
- non_selected_decision_counts: `{'attach_existing_family': 31, 'design_family_candidate': 3, 'defer_evidence': 4, 'reject': 3}`
- non_selected_longstanding_non_implement_disposition_counts: `{'implemented_with_provenance': 29, 'review_required': 7}`
- non_selected_longstanding_non_implement_action_required_order_ids: `[]`
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
- `duplicate_order_id=order_swing_ldm_selection_discovery_arm_attribution_next_open_entry_volatility_adjusted_fixed_10d_manufacture_of_parts_and_accessori source=swing_lifecycle_decision_matrix stage=selection`
- `duplicate_order_id=order_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_electric_lamps_and_bulbs_ source=swing_lifecycle_decision_matrix stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_volatility_adju source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_volatility_adju source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_volatility_adju source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_volatility_adju source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_volatility_adju source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_volatility_adju source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_volatility_adju source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_volatility_adju source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_next_open_entry_volatility_adjuste source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_next_open_entry_volatility_adjuste source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_next_open_entry_volatility_adjuste source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fix source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fix source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fix source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fix source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_next_open_entry_volatility_adjuste source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fix source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fix source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fix source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_next_open_entry_volatility_adjuste source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fix source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fix source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_ source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fix source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fix source=swing_lifecycle_bucket_discovery stage=selection`
- `duplicate_order_id=order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fix source=swing_lifecycle_bucket_discovery stage=selection`

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
- evidence: `ai_confirmed_unique=71`, `budget_pass_unique=17`, `latency_pass_unique=9`, `submitted_unique=9`, `submitted_to_ai_pct=12.7`, `submitted_to_budget_pct=52.9`, `blocker:blocked_strength_momentum:below_strength_base=302`, `blocker:blocked_strength_momentum:below_window_buy_value=268`, `blocker:blocked_vpw:-=256`, `upstream:first_ai_wait:-=134`, `upstream:blocked_ai_score:score_62.0=84`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=76`, `latency:latency_block:latency_state_danger=151`
- parity_contract: -
- next_postclose_metric: SUBMIT_DROUGHT_CRITICAL must produce a selected implement_now workorder and the next postclose LDM/runtime summary must show submit blocker attribution.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/threshold_cycle_ev_report.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "artifact_regeneration_required": false, "broker_order_submit_allowed": false, "forbidden_uses": ["intraday_threshold_mutation", "broker_guard_bypass", "provider_route_change", "bot_restart_trigger", "telegram_pre_submit_buy_alert"], "implementation_type": "source_only_report_provenance_handoff", "ldm_quote_freshness_attribution_present": true, "observation_axis_status": {"BROKER_RECEIPT": "observed", "BUDGET_PASS_COLLAPSE": "observed", "LATENCY_PRE_SUBMIT": "observed", "SIM_REAL_AUTHORITY": "observed", "SOURCE_TAXONOMY_LEAKAGE": "no_current_signal", "UPSTREAM_GATE": "observed"}, "observation_breakdown": {"allowed_runtime_apply": false, "axes": {"BROKER_RECEIPT": {"evidence": {"latency_pass_unique": 9, "order_bundle_submitted_unique": 9, "submitted_to_budget_unique_pct": 52.9}, "next_repair_action": "join post-submit broker receipt and fill provenance when submitted samples exist", "observed_count": 0, "status": "observed"}, "BUDGET_PASS_COLLAPSE": {"evidence": {"ai_confirmed_unique": 71, "budget_pass_unique": 17, "budget_to_ai_unique_pct": 23.9}, "next_repair_action": "preserve budget pass collapse as source attribution before EV approval", "observed_count": 54, "status": "observed"}, "LATENCY_PRE_SUBMIT": {"evidence": {"latency_blocker_top": [{"count": 151, "label": "latency_block:latency_state_danger"}], "latency_root_cause_counts": {"observer_unhealthy": 3, "order_rtt_guard": 111, "quote_stale": 14, "spread_microstructure_guard": 151, "spread_or_slippage_guard": 37}, "quote_freshness_attribution": {"decision_authority": "submit_drought_quote_freshness_attribution_only", "forbidden_uses": ["broker_order_submit", "adm_ldm_training_input", "general_threshold_ev_input", "live_auto_promotion"], "latency_pass_recovered_count": 5, "latency_pass_recovered_downstream_counts": {"budget_pass_no_submit_event": 1, "order_bundle_submitted": 1, "price_guard_or_revalidation": 3}, "latency_pass_recovered_downstream_stage_counts": {"budget_pass": 1, "order_bundle_submitted": 1, "pre_submit_entry_ai_authority_guard_block": 1, "pre_submit_price_guard_block": 2}, "order_bundle_submitted_after_refresh_count": 1, "post_restart_window_policy": "event_provenance_only", "refresh_applied_count": 14, "refresh_attempted_count": 15, "refresh_block_subreason_counts": {"observer_quote_refresh_failed_stale": 2, "ws_snapshot_refresh_failed_invalid": 1, "ws_snapshot_refresh_failed_missing": 2, "ws_snapshot_refresh_failed_stale": 2}, "refresh_subreason_counts": {"observer_quote_refresh_failed_stale": 2, "ws_snapshot_refresh_failed_invalid": 1, "ws_snapshot_refresh_failed_missing": 2, "ws_snapshot_refresh_failed_stale": 2}, "runtime_effect": false, "still_latency_blocked_after_refresh_count": 4}, "unknown_latency_reason_count": 0, "unknown_latency_workorder_required": false}, "next_repair_action": "close unknown latency labels or route quote freshness gaps to LDM attribution", "observed_count": 151, "status": "observed"}, "SIM_REAL_AUTHORITY": {"evidence": {"actual_order_submitted_authority": "not_granted_by_report", "broker_order_submit_allowed": false}, "next_repair_action": "keep attribution source-only until explicit runtime approval artifact exists", "observed_count": 1, "status": "observed"}, "SOURCE_TAXONOMY_LEAKAGE": {"evidence": {"blocker_top": [{"count": 302, "label": "blocked_strength_momentum:below_strength_base"}, {"count": 268, "label": "blocked_strength_momentum:below_window_buy_value"}, {"count": 256, "label": "blocked_vpw:-"}, {"count": 151, "label": "latency_block:latency_state_danger"}, {"count": 134, "label": "first_ai_wait:-"}, {"count": 125, "label": "blocked_liquidity:-"}, {"count": 104, "label": "blocked_strength_momentum:below_buy_ratio"}, {"count": 84, "label": "blocked_ai_score:score_62.0"}, {"count": 76, "label": "blocked_ai_score:ai_score_50_buy_hold_override"}, {"count": 37, "label": "blocked_ai_score:score_0.0"}], "taxonomy_leakage_labels": []}, "next_repair_action": "separate swing/source taxonomy from entry-submit blocker labels", "observed_count": 0, "status": "no_current_signal"}, "UPSTREAM_GATE": {"evidence": {"budget_to_ai_unique_pct": 23.9, "upstream_blocker_top": [{"count": 134, "label": "first_ai_wait:-"}, {"count": 84, "label": "blocked_ai_score:score_62.0"}, {"count": 76, "label": "blocked_ai_score:ai_score_50_buy_hold_override"}, {"count": 37, "label": "blocked_ai_score:score_0.0"}, {"count": 21, "label": "blocked_ai_score:score_58.0"}, {"count": 4, "label": "blocked_ai_score:score_64.0"}, {"count": 2, "label": "wait65_79_ev_candidate:score_74.0"}, {"count": 2, "label": "blocked_ai_score:score_56.0"}, {"count": 1, "label": "blocked_ai_score:score_22.0"}, {"count": 1, "label": "blocked_ai_score:score_53.0"}]}, "next_repair_action": "split upstream AI terminal and score gate reasons before threshold interpretation", "observed_count": 362, "status": "observed"}}, "axis_order": ["UPSTREAM_GATE", "BUDGET_PASS_COLLAPSE", "LATENCY_PRE_SUBMIT", "BROKER_RECEIPT", "SIM_REAL_AUTHORITY", "SOURCE_TAXONOMY_LEAKAGE"], "broker_order_submit_allowed": false, "decision_authority": "submit_drought_attribution_only", "forbidden_uses": ["broker_order_submit", "runtime_apply_candidate", "intraday_threshold_mutation", "provider_route_change", "bot_restart_trigger", "live_auto_promotion"], "runtime_effect": false}, "quote_freshness_attribution_inconsistent": false, "quote_freshness_latency_pass_recovered_count": 5, "quote_freshness_refresh_applied_count": 14, "quote_freshness_refresh_attempted_count": 15, "required_downstream": ["code_improvement_workorder", "lifecycle_decision_matrix.submit_bucket_attribution", "threshold_cycle_ev_report", "runtime_approval_summary", "postclose_verifier"], "root_cause_closure_status_hint": "root_cause_closed", "root_cause_counts": {"observer_unhealthy": 3, "order_rtt_guard": 111, "quote_stale": 14, "spread_microstructure_guard": 151, "spread_or_slippage_guard": 37}, "root_cause_signal": "SUBMIT_DROUGHT_CRITICAL", "runtime_effect": false, "source_report_type": "buy_funnel_sentinel", "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 2. `order_entry_broker_receipt_contract_gap_review`

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
- evidence: `ai_confirmed_unique=71`, `budget_pass_unique=17`, `latency_pass_unique=9`, `submitted_unique=9`, `submitted_to_ai_pct=12.7`, `submitted_to_budget_pct=52.9`, `blocker:blocked_strength_momentum:below_strength_base=302`, `blocker:blocked_strength_momentum:below_window_buy_value=268`, `blocker:blocked_vpw:-=256`, `upstream:first_ai_wait:-=134`, `upstream:blocked_ai_score:score_62.0=84`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=76`, `latency:latency_block:latency_state_danger=151`, `weak_contract_gap=broker_receipt_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_submit_contract_verified`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "broker_receipt_contract_gap", "implementation_type": "submit_contract_report_provenance_verified", "missing_broker_order_key_count": 0, "post_submit_provenance_join_resolution": "no_gap_broker_order_key_present_or_no_missing_rows", "real_submitted_row_count": 24, "runtime_effect": false, "sample_status": "ldm_submit_contract_verified", "source_report_type": "buy_funnel_sentinel", "submit_rows": 101, "taxonomy_leakage_labels": [], "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_submit_contract_verified and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 3. `order_entry_fill_quality_contract_gap_review`

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
- evidence: `ai_confirmed_unique=71`, `budget_pass_unique=17`, `latency_pass_unique=9`, `submitted_unique=9`, `submitted_to_ai_pct=12.7`, `submitted_to_budget_pct=52.9`, `blocker:blocked_strength_momentum:below_strength_base=302`, `blocker:blocked_strength_momentum:below_window_buy_value=268`, `blocker:blocked_vpw:-=256`, `upstream:first_ai_wait:-=134`, `upstream:blocked_ai_score:score_62.0=84`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=76`, `latency:latency_block:latency_state_danger=151`, `weak_contract_gap=fill_quality_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_submit_contract_verified`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "fill_quality_contract_gap", "implementation_type": "submit_contract_report_provenance_verified", "missing_broker_order_key_count": 0, "post_submit_provenance_join_resolution": "no_gap_broker_order_key_present_or_no_missing_rows", "real_submitted_row_count": 24, "runtime_effect": false, "sample_status": "ldm_submit_contract_verified", "source_report_type": "buy_funnel_sentinel", "submit_rows": 101, "taxonomy_leakage_labels": [], "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_submit_contract_verified and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 4. `order_entry_post_submit_contract_gap_review`

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
- evidence: `ai_confirmed_unique=71`, `budget_pass_unique=17`, `latency_pass_unique=9`, `submitted_unique=9`, `submitted_to_ai_pct=12.7`, `submitted_to_budget_pct=52.9`, `blocker:blocked_strength_momentum:below_strength_base=302`, `blocker:blocked_strength_momentum:below_window_buy_value=268`, `blocker:blocked_vpw:-=256`, `upstream:first_ai_wait:-=134`, `upstream:blocked_ai_score:score_62.0=84`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=76`, `latency:latency_block:latency_state_danger=151`, `weak_contract_gap=post_submit_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_submit_contract_verified`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "post_submit_contract_gap", "implementation_type": "submit_contract_report_provenance_verified", "missing_broker_order_key_count": 0, "post_submit_provenance_join_resolution": "no_gap_broker_order_key_present_or_no_missing_rows", "real_submitted_row_count": 24, "runtime_effect": false, "sample_status": "ldm_submit_contract_verified", "source_report_type": "buy_funnel_sentinel", "submit_rows": 101, "taxonomy_leakage_labels": [], "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_submit_contract_verified and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 5. `order_entry_source_taxonomy_contract_gap_review`

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
- evidence: `ai_confirmed_unique=71`, `budget_pass_unique=17`, `latency_pass_unique=9`, `submitted_unique=9`, `submitted_to_ai_pct=12.7`, `submitted_to_budget_pct=52.9`, `blocker:blocked_strength_momentum:below_strength_base=302`, `blocker:blocked_strength_momentum:below_window_buy_value=268`, `blocker:blocked_vpw:-=256`, `upstream:first_ai_wait:-=134`, `upstream:blocked_ai_score:score_62.0=84`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=76`, `latency:latency_block:latency_state_danger=151`, `weak_contract_gap=source_taxonomy_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`, `taxonomy_leakage_labels=[]`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_submit_contract_verified`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "source_taxonomy_contract_gap", "implementation_type": "submit_contract_report_provenance_verified", "missing_broker_order_key_count": 0, "post_submit_provenance_join_resolution": "no_gap_broker_order_key_present_or_no_missing_rows", "real_submitted_row_count": 24, "runtime_effect": false, "sample_status": "ldm_submit_contract_verified", "source_report_type": "buy_funnel_sentinel", "submit_rows": 101, "taxonomy_leakage_labels": [], "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_submit_contract_verified and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 6. `order_entry_telegram_post_submit_contract_gap_review`

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
- evidence: `ai_confirmed_unique=71`, `budget_pass_unique=17`, `latency_pass_unique=9`, `submitted_unique=9`, `submitted_to_ai_pct=12.7`, `submitted_to_budget_pct=52.9`, `blocker:blocked_strength_momentum:below_strength_base=302`, `blocker:blocked_strength_momentum:below_window_buy_value=268`, `blocker:blocked_vpw:-=256`, `upstream:first_ai_wait:-=134`, `upstream:blocked_ai_score:score_62.0=84`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=76`, `latency:latency_block:latency_state_danger=151`, `weak_contract_gap=telegram_post_submit_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_submit_contract_verified`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "telegram_post_submit_contract_gap", "implementation_type": "submit_contract_report_provenance_verified", "missing_broker_order_key_count": 0, "post_submit_provenance_join_resolution": "no_gap_broker_order_key_present_or_no_missing_rows", "real_submitted_row_count": 24, "runtime_effect": false, "sample_status": "ldm_submit_contract_verified", "source_report_type": "buy_funnel_sentinel", "submit_rows": 101, "taxonomy_leakage_labels": [], "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_submit_contract_verified and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 7. `order_latency_canary_tag_완화_1축_canary_승인`

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
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_latency_canary_tag_완화_1축_canary_승인", "repeat_signature": "sig:scalping_pattern_lab_automation|runtime_instrumentation||latency_canary_tag_완화_1축_canary_승인||latency_canary_tag_완화_1축_canary_승인", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_but_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 8. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_10_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_0cf08fc8`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:96c1793987
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_10`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:96c1793987`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 9. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_11_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_25002a6e`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:fef5ae20be
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_11`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:fef5ae20be`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 10. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_12_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_7508c15e`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:cbddc5ff25
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_12`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:cbddc5ff25`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 11. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_13_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_25002a6e`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:fef5ae20be
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_13`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:fef5ae20be`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 12. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_14_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_a8c4fc32`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3f826a3664
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_14`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3f826a3664`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 13. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_15_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_15`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:70a865069d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 14. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_16_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_77a92b6c`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:7b1e064efb
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_16`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:7b1e064efb`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 15. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_17_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_65b143ae`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:f2f2f3d14e
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_17`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:f2f2f3d14e`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 16. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_18_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_25533295`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:1e86336b12
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_18`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:1e86336b12`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 17. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_19_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_90fa3482`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:71e9b92bc5
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_19`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:71e9b92bc5`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 18. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_1_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_9cb11ea2`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a4de6797c9
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_1`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a4de6797c9`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 19. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_20_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42`

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
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 20. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_2_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_2`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:70a865069d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 21. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_3_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_9cb11ea2`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a4de6797c9
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_3`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a4de6797c9`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 22. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_4_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_af0aef43`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:df02034b40
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_4`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:df02034b40`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 23. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_5_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_9cb11ea2`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a4de6797c9
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_5`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a4de6797c9`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 24. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_6_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_f12338ed`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6f0786a34b
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_6`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6f0786a34b`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 25. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_7_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_7508c15e`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:cbddc5ff25
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_7`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:cbddc5ff25`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 26. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_8_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c0394ca1`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:075ce13c92
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_8`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:075ce13c92`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 27. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_9_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_25002a6e`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:fef5ae20be
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_9`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:fef5ae20be`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 28. `order_stage_hook_workorder_discovery_stage_hook_holding_flow_runner_debounce_guard`

- title: Implement stage hook: holding_flow_runner_debounce_guard
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `stage_hook_workorder_discovery`
- lifecycle_stage: `holding`
- target_subsystem: `holding-flow runtime arbitration`
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
- evidence: `strict_match_count=808`, `ambiguous_match_count=0`, `top_symbols=000150,000270,000500,000650,000660,001740,001820,002220`, `estimated_uplift_pct_sum=3837.1900`, `gap=sim-only early stop/loss followed by later runner is not isolated as a dedicated producer`, `required_microstructure_features=ws_orderbook_churn,ofi_qi_persistence,large_trade_absorption,spread_flicker,top_depth_replenishment,holding_flow_cache_freshness`, `required_producer=runner_regime_counterfactual_producer`, `readiness_tier=implementation_workorder_ready`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `data/report/producer_gap_discovery/producer_gap_discovery_2026-07-08.json`, `stage_hooks/holding_flow_runner_debounce_guard.yaml`, `tests/test_holding_flow_runner_debounce_guard_contract.py`, `tests/test_runner_regime_counterfactual_producer.py`
- acceptance_tests: `hook_input_output_contract_test`, `forbidden_use_authority_test`, `disabled_initial_runtime_state_test`, `runner_regime_counterfactual_producer_presence_test`, `microstructure_feature_contract_test`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "hook_name": "holding_flow_runner_debounce_guard", "implementation_files": ["src/engine/automation/stage_hook_runtime_scaffold.py"], "initial_runtime_state": "disabled", "requires_separate_runtime_apply_candidate": true, "runtime_effect": false, "source_report_type": "stage_hook_runtime_scaffold"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_stage_hook_workorder_discovery_stage_hook_holding_flow_runner_debounce_guard", "repeat_signature": "sig:stage_hook_workorder_discovery|holding-flow runtime arbitration|holding|holding_flow_runner_debounce_guard||implement_stage_hook_holding_flow_runner_debounce_guard", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
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

### 29. `order_stage_hook_workorder_discovery_stage_hook_plateau_breakdown_exit_arbitration_probe`

- title: Implement stage hook: plateau_breakdown_exit_arbitration_probe
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `stage_hook_workorder_discovery`
- lifecycle_stage: `exit`
- target_subsystem: `exit arbitration / plateau breakdown handling`
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
- evidence: `strict_match_count=958`, `ambiguous_match_count=0`, `top_symbols=000150,000240,000370,000500,000660,000990,001440,001740`, `estimated_giveback_pct_sum=4738.5800`, `gap=sim-only prior modest win followed by late stop/giveback is not isolated as a dedicated producer`, `required_producer=plateau_breakdown_exit_counterfactual_producer`, `readiness_tier=implementation_workorder_ready`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `data/report/producer_gap_discovery/producer_gap_discovery_2026-07-08.json`, `stage_hooks/plateau_breakdown_exit_arbitration_probe.yaml`, `tests/test_plateau_breakdown_exit_arbitration_probe_contract.py`
- acceptance_tests: `hook_input_output_contract_test`, `forbidden_use_authority_test`, `disabled_initial_runtime_state_test`, `plateau_breakdown_exit_counterfactual_producer_presence_test`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "hook_name": "plateau_breakdown_exit_arbitration_probe", "implementation_files": ["src/engine/automation/stage_hook_runtime_scaffold.py"], "initial_runtime_state": "disabled", "requires_separate_runtime_apply_candidate": true, "runtime_effect": false, "source_report_type": "stage_hook_runtime_scaffold"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_stage_hook_workorder_discovery_stage_hook_plateau_breakdown_exit_arbitration_probe", "repeat_signature": "sig:stage_hook_workorder_discovery|exit arbitration / plateau breakdown handling|exit|plateau_breakdown_exit_arbitration_probe||implement_stage_hook_plateau_breakdown_exit_arbitration_probe", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
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

### 30. `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_overnight_sell_today_rule_scalp_sim_overnight_sell_tod_3355d7a3`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150
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
- evidence: `workorder_id=exit_bucket_source_quality_7`, `bucket_type=combo_exit_result`, `bucket_key=source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=source_quality_workorder`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `terminal_not_applicable_evidence`
- root_cause_closure_status: `-`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "source_quality_workorder", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "hold_sample"}, "recommended_resolution": "mark_not_applicable_explicitly", "source_field_coverage": {"outcome": {"coverage_rate": 1.0, "present_count": 1, "sample_count": 1, "source_fields": ["source_stage", "labels.exit_rule", "runtime_features.chosen_action", "labels.sim_post_sell_outcome", "labels.outcome", "labels.profit_rate"]}}, "unknown_reason_counts": {"not_applicable": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "terminal_not_applicable_evidence", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_scalp_sim_over", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_scalp_sim_over", "review_disposition": "keep_visible_by_design"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Keep the item out of the canonical implement_now queue; regenerated postclose reports and runner terminal dispositions must preserve the non-implement decision.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 31. `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_overnight_sell_today_rule_scalp_sim_overnight_sell_tod_7b698c08`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080
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
- evidence: `workorder_id=exit_bucket_source_quality_5`, `bucket_type=combo_exit_result`, `bucket_key=source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=source_quality_workorder`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `terminal_not_applicable_evidence`
- root_cause_closure_status: `-`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "source_quality_workorder", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "mark_not_applicable_explicitly", "source_field_coverage": {"outcome": {"coverage_rate": 1.0, "present_count": 3, "sample_count": 3, "source_fields": ["source_stage", "labels.exit_rule", "runtime_features.chosen_action", "labels.sim_post_sell_outcome", "labels.outcome", "labels.profit_rate"]}}, "unknown_reason_counts": {"not_applicable": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "terminal_not_applicable_evidence", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_scalp_sim_over", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_scalp_sim_over", "review_disposition": "keep_visible_by_design"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Keep the item out of the canonical implement_now queue; regenerated postclose reports and runner terminal dispositions must preserve the non-implement decision.

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
- evidence: `workorder_id=exit_bucket_source_quality_4`, `bucket_type=combo_exit_result`, `bucket_key=source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_73281913", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_scalp_sim_part", "review_disposition": "implemented_with_provenance"}`
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
- evidence: `workorder_id=exit_bucket_source_quality_1`, `bucket_type=combo_exit_result`, `bucket_key=source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_823fe278", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_scalp_sim_part", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 34. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_e_71b132b9`

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
- evidence: `workorder_id=exit_bucket_source_quality_2`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 35. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_missed_bb293be8`

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
- evidence: `workorder_id=exit_bucket_source_quality_3`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 36. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutra_d73738ba`

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
- evidence: `workorder_id=exit_bucket_source_quality_6`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 37. `order_lifecycle_exit_bucket_exit_outcome_outcome_not_applicable_partial_exit_92629206`

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
- evidence: `workorder_id=exit_bucket_source_quality_10`, `bucket_type=exit_outcome`, `bucket_key=outcome_not_applicable_partial_exit`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "outcome_not_applicable_partial_exit", "bucket_type": "exit_outcome", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_lifecycle_exit_bucket_exit_outcome_outcome_not_applicable_partial_exit_92629206", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_exit_outcome_outcome_not_applicable_par", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 38. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_lt_neg070_he_ed505a3f`

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
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_lt_neg070_he_ed505a3f", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 39. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_pos150_pos30_6f3188b0`

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
- evidence: `workorder_id=holding_bucket_source_quality_2`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 40. `order_lifecycle_holding_bucket_held_bucket_held_not_applicable_at_start_508784a3`

- title: LDM holding bucket source-quality follow-up: held_bucket=held_not_applicable_at_start
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
- evidence: `workorder_id=holding_bucket_source_quality_3`, `bucket_type=held_bucket`, `bucket_key=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "held_not_applicable_at_start", "bucket_type": "held_bucket", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_lifecycle_holding_bucket_held_bucket_held_not_applicable_at_start_508784a3", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_held_bucket_held_not_applicable_at_s", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 41. `order_lifecycle_holding_bucket_holding_action_wait_c26d74df`

- title: LDM holding bucket source-quality follow-up: holding_action=WAIT
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
- evidence: `workorder_id=holding_bucket_source_quality_4`, `bucket_type=holding_action`, `bucket_key=WAIT`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "WAIT", "bucket_type": "holding_action", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_lifecycle_holding_bucket_holding_action_wait_c26d74df", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_holding_action_wait", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 42. `order_lifecycle_holding_bucket_holding_source_stage_scalp_sim_holding_started_78913f30`

- title: LDM holding bucket source-quality follow-up: holding_source_stage=scalp_sim_holding_started
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
- evidence: `workorder_id=holding_bucket_source_quality_5`, `bucket_type=holding_source_stage`, `bucket_key=scalp_sim_holding_started`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "scalp_sim_holding_started", "bucket_type": "holding_source_stage", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_lifecycle_holding_bucket_holding_source_stage_scalp_sim_holding_started_78913f30", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_holding_source_stage_scalp_sim_holdi", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 43. `order_lifecycle_holding_bucket_profit_band_profit_lt_neg070_711f1b3f`

- title: LDM holding bucket source-quality follow-up: profit_band=profit_lt_neg070
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
- evidence: `workorder_id=holding_bucket_source_quality_6`, `bucket_type=profit_band`, `bucket_key=profit_lt_neg070`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "profit_lt_neg070", "bucket_type": "profit_band", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_lifecycle_holding_bucket_profit_band_profit_lt_neg070_711f1b3f", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_profit_band_profit_lt_neg070", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 44. `order_lifecycle_holding_bucket_profit_band_profit_pos150_pos300_0904c33e`

- title: LDM holding bucket source-quality follow-up: profit_band=profit_pos150_pos300
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
- evidence: `workorder_id=holding_bucket_source_quality_7`, `bucket_type=profit_band`, `bucket_key=profit_pos150_pos300`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "profit_pos150_pos300", "bucket_type": "profit_band", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_lifecycle_holding_bucket_profit_band_profit_pos150_pos300_0904c33e", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_profit_band_profit_pos150_pos300", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 45. `order_swing_ldm_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_manufacture_of_other_che`

- title: Swing LDM source field follow-up: bottom_rebound_next_open_entry|equal_notional|fixed_10d|Manufacture of Other Chemical Products|-|RUNNER
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=bottom_rebound_next_open_entry|equal_notional|fixed_10d|Manufacture of Other Chemical Products|-|RUNNER`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 32, "total_count": 32}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 32, "total_count": 32}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 32, "total_count": 32}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 32, "total_count": 32}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 32, "total_count": 32}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_bottom_rebound_next_open_entry_equal_notional_f", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_bottom_rebound_next_open_entry_equal_notional_f", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 46. `order_swing_ldm_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_manufacture_of_structura`

- title: Swing LDM source field follow-up: bottom_rebound_next_open_entry|equal_notional|fixed_10d|Manufacture of Structural Metal Products, Tanks, Reservoirs and Steam Generators|-|RUNNER
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=bottom_rebound_next_open_entry|equal_notional|fixed_10d|Manufacture of Structural Metal Products, Tanks, Reservoirs and Steam Generators|-|RUNNER`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 10, "total_count": 10}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 10, "total_count": 10}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 10, "total_count": 10}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 10, "total_count": 10}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 10, "total_count": 10}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_swing_ldm_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_manufacture_of_structura", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_bottom_rebound_next_open_entry_equal_notional_f", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 47. `order_swing_ldm_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_manufacture_of_telecommu`

- title: Swing LDM source field follow-up: bottom_rebound_next_open_entry|equal_notional|fixed_10d|Manufacture of Telecommunication and Broadcasting Apparatuses|-|RUNNER
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=bottom_rebound_next_open_entry|equal_notional|fixed_10d|Manufacture of Telecommunication and Broadcasting Apparatuses|-|RUNNER`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 16, "total_count": 16}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 16, "total_count": 16}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 16, "total_count": 16}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 16, "total_count": 16}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 16, "total_count": 16}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_bottom_rebound_next_open_entry_equal_notional_f", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_bottom_rebound_next_open_entry_equal_notional_f", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 48. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manufacture_of_ins`

- title: Swing LDM source field follow-up: breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Instruments and Appliances for Measuring, Checking, Testing, Navigating, controlling and Other Purposes, Except Optical Instruments|-|DIAGNOSTIC
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Instruments and Appliances for Measuring, Checking, Testing, Navigating, controlling and Other Purposes, Except Optical Instruments|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 20, "total_count": 20}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 20, "total_count": 20}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 20, "total_count": 20}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 20, "total_count": 20}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 20, "total_count": 20}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 49. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manufacture_of_rub`

- title: Swing LDM source field follow-up: breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Rubber Products|타이어|DIAGNOSTIC
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Rubber Products|타이어|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 14, "total_count": 14}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 14, "total_count": 14}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 14, "total_count": 14}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 14, "total_count": 14}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 14, "total_count": 14}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_breakout_confirm_entry_confidence_weighted_trai", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 50. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_of_parts_and_a`

- title: Swing LDM source field follow-up: breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|-|DIAGNOSTIC
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 26, "total_count": 26}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 26, "total_count": 26}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 26, "total_count": 26}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 26, "total_count": 26}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 26, "total_count": 26}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 51. `order_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_audio_publishing_and_original_master_rec`

- title: Swing LDM source field follow-up: next_open_entry|equal_notional|fixed_5d|Audio Publishing and Original Master Recordings|-|DIAGNOSTIC
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=next_open_entry|equal_notional|fixed_5d|Audio Publishing and Original Master Recordings|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 11, "total_count": 11}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 11, "total_count": 11}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 11, "total_count": 11}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 11, "total_count": 11}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 11, "total_count": 11}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_audio_publishing_and_original_master_rec", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_next_open_entry_equal_notional_fixed_5d_audio_p", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 52. `order_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_computer_programming_system_integration_`

- title: Swing LDM source field follow-up: next_open_entry|equal_notional|fixed_5d|Computer programming, System Integration and Management Services|-|DIAGNOSTIC
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=next_open_entry|equal_notional|fixed_5d|Computer programming, System Integration and Management Services|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 22, "total_count": 22}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 22, "total_count": 22}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 22, "total_count": 22}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 22, "total_count": 22}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 22, "total_count": 22}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_computer_programming_system_integration_", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_next_open_entry_equal_notional_fixed_5d_compute", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 53. `order_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_data_processing_hosting_and_related_acti`

- title: Swing LDM source field follow-up: next_open_entry|equal_notional|fixed_5d|Data Processing, Hosting and Related activities; Web Portals|SNS(Social Network Service),게임_모바일|DIAGNOSTIC
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=next_open_entry|equal_notional|fixed_5d|Data Processing, Hosting and Related activities; Web Portals|SNS(Social Network Service),게임_모바일|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 16, "total_count": 16}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 16, "total_count": 16}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 16, "total_count": 16}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 16, "total_count": 16}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 16, "total_count": 16}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_data_processing_hosting_and_related_acti", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_next_open_entry_equal_notional_fixed_5d_data_pr", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 54. `order_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_basic_chemicals_2차전지_소재_양`

- title: Swing LDM source field follow-up: next_open_entry|equal_notional|fixed_5d|Manufacture of Basic Chemicals|2차전지_소재(양극화물질등),온실가스배출저감|DIAGNOSTIC
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=next_open_entry|equal_notional|fixed_5d|Manufacture of Basic Chemicals|2차전지_소재(양극화물질등),온실가스배출저감|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 17, "total_count": 17}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 17, "total_count": 17}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 17, "total_count": 17}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 17, "total_count": 17}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 17, "total_count": 17}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_next_open_entry_equal_notional_fixed_5d_manufac", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_next_open_entry_equal_notional_fixed_5d_manufac", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 55. `order_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_basic_precious_and_non_fe`

- title: Swing LDM source field follow-up: next_open_entry|equal_notional|fixed_5d|Manufacture of Basic Precious and Non-ferrous Metals|-|DIAGNOSTIC
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=next_open_entry|equal_notional|fixed_5d|Manufacture of Basic Precious and Non-ferrous Metals|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 13, "total_count": 13}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 13, "total_count": 13}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 13, "total_count": 13}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 13, "total_count": 13}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 13, "total_count": 13}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_next_open_entry_equal_notional_fixed_5d_manufac", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_next_open_entry_equal_notional_fixed_5d_manufac", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 56. `order_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_electric_lamps_and_bulbs_`

- title: Swing LDM source field follow-up: next_open_entry|equal_notional|fixed_5d|Manufacture of Electric Lamps and Bulbs|-|DIAGNOSTIC
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=next_open_entry|equal_notional|fixed_5d|Manufacture of Electric Lamps and Bulbs|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 15, "total_count": 15}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 15, "total_count": 15}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 15, "total_count": 15}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 15, "total_count": 15}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 15, "total_count": 15}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_next_open_entry_equal_notional_fixed_5d_manufac", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_next_open_entry_equal_notional_fixed_5d_manufac", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 57. `order_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_instruments_and_appliance`

- title: Swing LDM source field follow-up: next_open_entry|equal_notional|fixed_5d|Manufacture of Instruments and Appliances for Measuring, Checking, Testing, Navigating, controlling and Other Purposes, Except Optical Instruments|-|DIAGNOSTIC
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=next_open_entry|equal_notional|fixed_5d|Manufacture of Instruments and Appliances for Measuring, Checking, Testing, Navigating, controlling and Other Purposes, Except Optical Instruments|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 22, "total_count": 22}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 22, "total_count": 22}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 22, "total_count": 22}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 22, "total_count": 22}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 22, "total_count": 22}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_next_open_entry_equal_notional_fixed_5d_manufac", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_next_open_entry_equal_notional_fixed_5d_manufac", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 58. `order_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_motor_vehicles_and_engine`

- title: Swing LDM source field follow-up: next_open_entry|equal_notional|fixed_5d|Manufacture of Motor Vehicles and Engines for Motor Vehicles|그린카_하이브리드카/전기차|DIAGNOSTIC
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=next_open_entry|equal_notional|fixed_5d|Manufacture of Motor Vehicles and Engines for Motor Vehicles|그린카_하이브리드카/전기차|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 15, "total_count": 15}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 15, "total_count": 15}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 15, "total_count": 15}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 15, "total_count": 15}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 15, "total_count": 15}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_next_open_entry_equal_notional_fixed_5d_manufac", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_next_open_entry_equal_notional_fixed_5d_manufac", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 59. `order_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_other_chemical_products_2`

- title: Swing LDM source field follow-up: next_open_entry|equal_notional|fixed_5d|Manufacture of Other Chemical Products|2차전지_소재(양극화물질등)|DIAGNOSTIC
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=next_open_entry|equal_notional|fixed_5d|Manufacture of Other Chemical Products|2차전지_소재(양극화물질등)|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 24, "total_count": 24}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 24, "total_count": 24}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 24, "total_count": 24}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 24, "total_count": 24}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 24, "total_count": 24}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_other_chemical_products_2", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_next_open_entry_equal_notional_fixed_5d_manufac", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 60. `order_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_parts_and_accessories_for`

- title: Swing LDM source field follow-up: next_open_entry|equal_notional|fixed_5d|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|-|DIAGNOSTIC
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=next_open_entry|equal_notional|fixed_5d|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 34, "total_count": 34}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 34, "total_count": 34}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 34, "total_count": 34}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 34, "total_count": 34}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 34, "total_count": 34}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_parts_and_accessories_for", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_next_open_entry_equal_notional_fixed_5d_manufac", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 61. `order_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_semiconductor_diagnostic`

- title: Swing LDM source field follow-up: next_open_entry|equal_notional|fixed_5d|Manufacture of Semiconductor|-|DIAGNOSTIC
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=next_open_entry|equal_notional|fixed_5d|Manufacture of Semiconductor|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 13, "total_count": 13}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 13, "total_count": 13}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 13, "total_count": 13}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 13, "total_count": 13}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 13, "total_count": 13}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_next_open_entry_equal_notional_fixed_5d_manufac", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_next_open_entry_equal_notional_fixed_5d_manufac", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 62. `order_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_other_financial_intermediation_태양광_폴리실리콘`

- title: Swing LDM source field follow-up: next_open_entry|equal_notional|fixed_5d|Other Financial Intermediation|태양광_폴리실리콘|DIAGNOSTIC
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=next_open_entry|equal_notional|fixed_5d|Other Financial Intermediation|태양광_폴리실리콘|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 10, "total_count": 10}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 10, "total_count": 10}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 10, "total_count": 10}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 10, "total_count": 10}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 10, "total_count": 10}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 63. `order_swing_ldm_selection_discovery_arm_attribution_next_open_entry_volatility_adjusted_fixed_10d_building_construction_건설_국내주택_건설_해`

- title: Swing LDM source field follow-up: next_open_entry|volatility_adjusted|fixed_10d|Building Construction|건설_국내주택,건설_해외건설|DIAGNOSTIC
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=next_open_entry|volatility_adjusted|fixed_10d|Building Construction|건설_국내주택,건설_해외건설|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 12, "total_count": 12}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 12, "total_count": 12}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 12, "total_count": 12}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 12, "total_count": 12}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 12, "total_count": 12}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 64. `order_swing_ldm_selection_discovery_arm_attribution_next_open_entry_volatility_adjusted_fixed_10d_computer_programming_system_integr`

- title: Swing LDM source field follow-up: next_open_entry|volatility_adjusted|fixed_10d|Computer programming, System Integration and Management Services|-|DIAGNOSTIC
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=next_open_entry|volatility_adjusted|fixed_10d|Computer programming, System Integration and Management Services|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 14, "total_count": 14}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 14, "total_count": 14}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 14, "total_count": 14}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 14, "total_count": 14}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 14, "total_count": 14}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 65. `order_swing_ldm_selection_discovery_arm_attribution_next_open_entry_volatility_adjusted_fixed_10d_data_processing_hosting_and_relate`

- title: Swing LDM source field follow-up: next_open_entry|volatility_adjusted|fixed_10d|Data Processing, Hosting and Related activities; Web Portals|SNS(Social Network Service),게임_모바일|DIAGNOSTIC
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=next_open_entry|volatility_adjusted|fixed_10d|Data Processing, Hosting and Related activities; Web Portals|SNS(Social Network Service),게임_모바일|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 12, "total_count": 12}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 12, "total_count": 12}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 12, "total_count": 12}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 12, "total_count": 12}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 12, "total_count": 12}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 66. `order_swing_ldm_selection_discovery_arm_attribution_next_open_entry_volatility_adjusted_fixed_10d_manufacture_of_parts_and_accessori`

- title: Swing LDM source field follow-up: next_open_entry|volatility_adjusted|fixed_10d|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|그린카_하이브리드카/전기차,자동차_전장화 수혜,자동차_차량용 반도체|DIAGNOSTIC
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=next_open_entry|volatility_adjusted|fixed_10d|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|그린카_하이브리드카/전기차,자동차_전장화 수혜,자동차_차량용 반도체|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 13, "total_count": 13}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 13, "total_count": 13}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 13, "total_count": 13}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 13, "total_count": 13}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 13, "total_count": 13}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 4, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_next_open_entry_volatility_adjusted_fixed_10d_m", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_next_open_entry_volatility_adjusted_fixed_10d_m", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 67. `order_swing_ldm_selection_discovery_arm_attribution_next_open_entry_volatility_adjusted_fixed_10d_manufacture_of_plastic_products_di`

- title: Swing LDM source field follow-up: next_open_entry|volatility_adjusted|fixed_10d|Manufacture of Plastic Products|-|DIAGNOSTIC
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=next_open_entry|volatility_adjusted|fixed_10d|Manufacture of Plastic Products|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_available`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 14, "total_count": 14}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 14, "total_count": 14}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 14, "total_count": 14}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 14, "total_count": 14}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 14, "total_count": 14}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 4, "repeat_key": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_next_open_entry_volatility_adjusted_fixed_10d_m", "repeat_signature": "sig:swing_lifecycle_decision_matrix|swing_lifecycle_decision_matrix|selection|swing_ldm_bucket_instrumentation_gap||swing_ldm_source_field_follow_up_next_open_entry_volatility_adjusted_fixed_10d_m", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 68. `order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_`

- title: Swing lifecycle bucket discovery handoff follow-up: swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_manufacture_fa09ac98bf0d
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
- evidence: `bucket_id=swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_manufacture_fa09ac98bf0d`, `canonical_bucket=-`, `legacy_raw_bucket_key=-`, `ai_tier2_taxonomy_decision=-`, `ai_tier2_selected_source=-`, `classification_state=code_patch_required`, `reason=swing_ldm_bucket_contract_or_source_quality_gap`, `source_workorder_id=-`, `parent_bucket_id=swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_manufacture_fa09ac98bf0d`, `decision_authority=swing_ldm_bucket_discovery_sim_auto`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Swing bucket discovery candidates and workorders should be visible in EV, runtime summary, workorder, and verifier.
- files_likely_touched: `src/engine/swing_lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_ev_report.py`, `src/engine/runtime_approval_summary.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 10, "total_count": 10}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 10, "total_count": 10}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 10, "total_count": 10}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 10, "total_count": 10}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 10, "total_count": 10}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:swing_lifecycle_bucket_discovery|swing_lifecycle_bucket_discovery|selection|swing_bucket_handoff_or_contract_gap||swing_lifecycle_bucket_discovery_handoff_follow_up_swing_bucket_selection_discov", "repeat_signature": "sig:swing_lifecycle_bucket_discovery|swing_lifecycle_bucket_discovery|selection|swing_bucket_handoff_or_contract_gap||swing_lifecycle_bucket_discovery_handoff_follow_up_swing_bucket_selection_discov", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 69. `order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_bottom_rebound_signal_close_ret`

- title: Swing lifecycle bucket discovery handoff follow-up: swing_bucket_selection_discovery_arm_attribution_bottom_rebound_signal_close_retest_limit_entry_risk_capped_fixed_10_9dae191c3a78
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
- evidence: `bucket_id=swing_bucket_selection_discovery_arm_attribution_bottom_rebound_signal_close_retest_limit_entry_risk_capped_fixed_10_9dae191c3a78`, `canonical_bucket=-`, `legacy_raw_bucket_key=-`, `ai_tier2_taxonomy_decision=-`, `ai_tier2_selected_source=-`, `classification_state=code_patch_required`, `reason=swing_ldm_bucket_contract_or_source_quality_gap`, `source_workorder_id=-`, `parent_bucket_id=swing_bucket_selection_discovery_arm_attribution_bottom_rebound_signal_close_retest_limit_entry_risk_capped_fixed_10_9dae191c3a78`, `decision_authority=swing_ldm_bucket_discovery_sim_auto`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Swing bucket discovery candidates and workorders should be visible in EV, runtime summary, workorder, and verifier.
- files_likely_touched: `src/engine/swing_lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_ev_report.py`, `src/engine/runtime_approval_summary.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 30, "total_count": 30}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 30, "total_count": 30}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 30, "total_count": 30}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 30, "total_count": 30}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 30, "total_count": 30}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:swing_lifecycle_bucket_discovery|swing_lifecycle_bucket_discovery|selection|swing_bucket_handoff_or_contract_gap||swing_lifecycle_bucket_discovery_handoff_follow_up_swing_bucket_selection_discov", "repeat_signature": "sig:swing_lifecycle_bucket_discovery|swing_lifecycle_bucket_discovery|selection|swing_bucket_handoff_or_contract_gap||swing_lifecycle_bucket_discovery_handoff_follow_up_swing_bucket_selection_discov", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 70. `order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden`

- title: Swing lifecycle bucket discovery handoff follow-up: swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_229b6ae1d64e
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
- evidence: `bucket_id=swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_229b6ae1d64e`, `canonical_bucket=-`, `legacy_raw_bucket_key=-`, `ai_tier2_taxonomy_decision=-`, `ai_tier2_selected_source=-`, `classification_state=code_patch_required`, `reason=swing_ldm_bucket_contract_or_source_quality_gap`, `source_workorder_id=-`, `parent_bucket_id=swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_229b6ae1d64e`, `decision_authority=swing_ldm_bucket_discovery_sim_auto`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Swing bucket discovery candidates and workorders should be visible in EV, runtime summary, workorder, and verifier.
- files_likely_touched: `src/engine/swing_lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_ev_report.py`, `src/engine/runtime_approval_summary.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 14, "total_count": 14}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 14, "total_count": 14}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 14, "total_count": 14}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 14, "total_count": 14}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 14, "total_count": 14}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden", "repeat_signature": "sig:swing_lifecycle_bucket_discovery|swing_lifecycle_bucket_discovery|selection|swing_bucket_handoff_or_contract_gap||swing_lifecycle_bucket_discovery_handoff_follow_up_swing_bucket_selection_discov", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 71. `order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_risk_cap`

- title: Swing lifecycle bucket discovery handoff follow-up: swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_o_044b6c899b11
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
- evidence: `bucket_id=swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_o_044b6c899b11`, `canonical_bucket=-`, `legacy_raw_bucket_key=-`, `ai_tier2_taxonomy_decision=-`, `ai_tier2_selected_source=-`, `classification_state=code_patch_required`, `reason=swing_ldm_bucket_contract_or_source_quality_gap`, `source_workorder_id=-`, `parent_bucket_id=swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_o_044b6c899b11`, `decision_authority=swing_ldm_bucket_discovery_sim_auto`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Swing bucket discovery candidates and workorders should be visible in EV, runtime summary, workorder, and verifier.
- files_likely_touched: `src/engine/swing_lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_ev_report.py`, `src/engine/runtime_approval_summary.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 26, "total_count": 26}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 26, "total_count": 26}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 26, "total_count": 26}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 26, "total_count": 26}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 26, "total_count": 26}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:swing_lifecycle_bucket_discovery|swing_lifecycle_bucket_discovery|selection|swing_bucket_handoff_or_contract_gap||swing_lifecycle_bucket_discovery_handoff_follow_up_swing_bucket_selection_discov", "repeat_signature": "sig:swing_lifecycle_bucket_discovery|swing_lifecycle_bucket_discovery|selection|swing_bucket_handoff_or_contract_gap||swing_lifecycle_bucket_discovery_handoff_follow_up_swing_bucket_selection_discov", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 72. `order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_`

- title: Swing lifecycle bucket discovery handoff follow-up: swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_electric_lam_672a0f93e4b0
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
- evidence: `bucket_id=swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_electric_lam_672a0f93e4b0`, `canonical_bucket=-`, `legacy_raw_bucket_key=-`, `ai_tier2_taxonomy_decision=-`, `ai_tier2_selected_source=-`, `classification_state=code_patch_required`, `reason=swing_ldm_bucket_contract_or_source_quality_gap`, `source_workorder_id=-`, `parent_bucket_id=swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_electric_lam_672a0f93e4b0`, `decision_authority=swing_ldm_bucket_discovery_sim_auto`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Swing bucket discovery candidates and workorders should be visible in EV, runtime summary, workorder, and verifier.
- files_likely_touched: `src/engine/swing_lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_ev_report.py`, `src/engine/runtime_approval_summary.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 15, "total_count": 15}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 15, "total_count": 15}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 15, "total_count": 15}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 15, "total_count": 15}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 15, "total_count": 15}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_", "repeat_signature": "sig:swing_lifecycle_bucket_discovery|swing_lifecycle_bucket_discovery|selection|swing_bucket_handoff_or_contract_gap||swing_lifecycle_bucket_discovery_handoff_follow_up_swing_bucket_selection_discov", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 73. `order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_next_open_entry_volatility_adju`

- title: Swing lifecycle bucket discovery handoff follow-up: swing_bucket_selection_discovery_arm_attribution_next_open_entry_volatility_adjusted_fixed_10d_manufacture_of_parts_00ad0a10c05e
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
- evidence: `bucket_id=swing_bucket_selection_discovery_arm_attribution_next_open_entry_volatility_adjusted_fixed_10d_manufacture_of_parts_00ad0a10c05e`, `canonical_bucket=-`, `legacy_raw_bucket_key=-`, `ai_tier2_taxonomy_decision=-`, `ai_tier2_selected_source=-`, `classification_state=code_patch_required`, `reason=swing_ldm_bucket_contract_or_source_quality_gap`, `source_workorder_id=-`, `parent_bucket_id=swing_bucket_selection_discovery_arm_attribution_next_open_entry_volatility_adjusted_fixed_10d_manufacture_of_parts_00ad0a10c05e`, `decision_authority=swing_ldm_bucket_discovery_sim_auto`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Swing bucket discovery candidates and workorders should be visible in EV, runtime summary, workorder, and verifier.
- files_likely_touched: `src/engine/swing_lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_ev_report.py`, `src/engine/runtime_approval_summary.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 13, "total_count": 13}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 13, "total_count": 13}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 13, "total_count": 13}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 13, "total_count": 13}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 13, "total_count": 13}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:swing_lifecycle_bucket_discovery|swing_lifecycle_bucket_discovery|selection|swing_bucket_handoff_or_contract_gap||swing_lifecycle_bucket_discovery_handoff_follow_up_swing_bucket_selection_discov", "repeat_signature": "sig:swing_lifecycle_bucket_discovery|swing_lifecycle_bucket_discovery|selection|swing_bucket_handoff_or_contract_gap||swing_lifecycle_bucket_discovery_handoff_follow_up_swing_bucket_selection_discov", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 74. `order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equ`

- title: Swing lifecycle bucket discovery handoff follow-up: swing_ldm_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_manufacture_of_structura
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
- evidence: `bucket_id=swing_ldm_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_manufacture_of_structura`, `canonical_bucket=-`, `legacy_raw_bucket_key=-`, `ai_tier2_taxonomy_decision=-`, `ai_tier2_selected_source=-`, `classification_state=None`, `reason=source_quality_or_instrumentation_gap`, `source_workorder_id=swing_ldm_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_manufacture_of_structura`, `parent_bucket_id=-`, `decision_authority=swing_ldm_bucket_discovery_sim_auto`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Swing bucket discovery candidates and workorders should be visible in EV, runtime summary, workorder, and verifier.
- files_likely_touched: `src/engine/swing_lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_ev_report.py`, `src/engine/runtime_approval_summary.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 10, "total_count": 10}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 10, "total_count": 10}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 10, "total_count": 10}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 10, "total_count": 10}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 10, "total_count": 10}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:swing_lifecycle_bucket_discovery|swing_lifecycle_decision_matrix|selection|swing_bucket_handoff_or_contract_gap||swing_lifecycle_bucket_discovery_handoff_follow_up_swing_ldm_selection_discovery", "repeat_signature": "sig:swing_lifecycle_bucket_discovery|swing_lifecycle_decision_matrix|selection|swing_bucket_handoff_or_contract_gap||swing_lifecycle_bucket_discovery_handoff_follow_up_swing_ldm_selection_discovery", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 75. `order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_`

- title: Swing lifecycle bucket discovery handoff follow-up: swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manufacture_of_rub
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
- evidence: `bucket_id=swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manufacture_of_rub`, `canonical_bucket=-`, `legacy_raw_bucket_key=-`, `ai_tier2_taxonomy_decision=-`, `ai_tier2_selected_source=-`, `classification_state=None`, `reason=source_quality_or_instrumentation_gap`, `source_workorder_id=swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manufacture_of_rub`, `parent_bucket_id=-`, `decision_authority=swing_ldm_bucket_discovery_sim_auto`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Swing bucket discovery candidates and workorders should be visible in EV, runtime summary, workorder, and verifier.
- files_likely_touched: `src/engine/swing_lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_ev_report.py`, `src/engine/runtime_approval_summary.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 14, "total_count": 14}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 14, "total_count": 14}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 14, "total_count": 14}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 14, "total_count": 14}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 14, "total_count": 14}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_", "repeat_signature": "sig:swing_lifecycle_bucket_discovery|swing_lifecycle_decision_matrix|selection|swing_bucket_handoff_or_contract_gap||swing_lifecycle_bucket_discovery_handoff_follow_up_swing_ldm_selection_discovery", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 76. `order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped`

- title: Swing lifecycle bucket discovery handoff follow-up: swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_of_parts_and_a
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
- evidence: `bucket_id=swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_of_parts_and_a`, `canonical_bucket=-`, `legacy_raw_bucket_key=-`, `ai_tier2_taxonomy_decision=-`, `ai_tier2_selected_source=-`, `classification_state=None`, `reason=source_quality_or_instrumentation_gap`, `source_workorder_id=swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_of_parts_and_a`, `parent_bucket_id=-`, `decision_authority=swing_ldm_bucket_discovery_sim_auto`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Swing bucket discovery candidates and workorders should be visible in EV, runtime summary, workorder, and verifier.
- files_likely_touched: `src/engine/swing_lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_ev_report.py`, `src/engine/runtime_approval_summary.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 26, "total_count": 26}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 26, "total_count": 26}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 26, "total_count": 26}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 26, "total_count": 26}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 26, "total_count": 26}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:swing_lifecycle_bucket_discovery|swing_lifecycle_decision_matrix|selection|swing_bucket_handoff_or_contract_gap||swing_lifecycle_bucket_discovery_handoff_follow_up_swing_ldm_selection_discovery", "repeat_signature": "sig:swing_lifecycle_bucket_discovery|swing_lifecycle_decision_matrix|selection|swing_bucket_handoff_or_contract_gap||swing_lifecycle_bucket_discovery_handoff_follow_up_swing_ldm_selection_discovery", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 77. `order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fix`

- title: Swing lifecycle bucket discovery handoff follow-up: swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_electric_lamps_and_bulbs_
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
- evidence: `bucket_id=swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_electric_lamps_and_bulbs_`, `canonical_bucket=-`, `legacy_raw_bucket_key=-`, `ai_tier2_taxonomy_decision=-`, `ai_tier2_selected_source=-`, `classification_state=None`, `reason=source_quality_or_instrumentation_gap`, `source_workorder_id=swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_electric_lamps_and_bulbs_`, `parent_bucket_id=-`, `decision_authority=swing_ldm_bucket_discovery_sim_auto`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Swing bucket discovery candidates and workorders should be visible in EV, runtime summary, workorder, and verifier.
- files_likely_touched: `src/engine/swing_lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_ev_report.py`, `src/engine/runtime_approval_summary.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 15, "total_count": 15}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 15, "total_count": 15}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 15, "total_count": 15}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 15, "total_count": 15}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 15, "total_count": 15}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_next_open_entry_equal_notional_fix", "repeat_signature": "sig:swing_lifecycle_bucket_discovery|swing_lifecycle_decision_matrix|selection|swing_bucket_handoff_or_contract_gap||swing_lifecycle_bucket_discovery_handoff_follow_up_swing_ldm_selection_discovery", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 78. `order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_next_open_entry_volatility_adjuste`

- title: Swing lifecycle bucket discovery handoff follow-up: swing_ldm_selection_discovery_arm_attribution_next_open_entry_volatility_adjusted_fixed_10d_manufacture_of_parts_and_accessori
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
- evidence: `bucket_id=swing_ldm_selection_discovery_arm_attribution_next_open_entry_volatility_adjusted_fixed_10d_manufacture_of_parts_and_accessori`, `canonical_bucket=-`, `legacy_raw_bucket_key=-`, `ai_tier2_taxonomy_decision=-`, `ai_tier2_selected_source=-`, `classification_state=None`, `reason=source_quality_or_instrumentation_gap`, `source_workorder_id=swing_ldm_selection_discovery_arm_attribution_next_open_entry_volatility_adjusted_fixed_10d_manufacture_of_parts_and_accessori`, `parent_bucket_id=-`, `decision_authority=swing_ldm_bucket_discovery_sim_auto`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Swing bucket discovery candidates and workorders should be visible in EV, runtime summary, workorder, and verifier.
- files_likely_touched: `src/engine/swing_lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_ev_report.py`, `src/engine/runtime_approval_summary.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 13, "total_count": 13}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 13, "total_count": 13}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 13, "total_count": 13}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 13, "total_count": 13}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 13, "total_count": 13}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:swing_lifecycle_bucket_discovery|swing_lifecycle_decision_matrix|selection|swing_bucket_handoff_or_contract_gap||swing_lifecycle_bucket_discovery_handoff_follow_up_swing_ldm_selection_discovery", "repeat_signature": "sig:swing_lifecycle_bucket_discovery|swing_lifecycle_decision_matrix|selection|swing_bucket_handoff_or_contract_gap||swing_lifecycle_bucket_discovery_handoff_follow_up_swing_ldm_selection_discovery", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 79. `order_lifecycle_quiet_gap_ai_review_coverage_rollup`

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
- evidence: `quiet_gap_count=419`, `rollup_required_count=419`, `sim_live_connected_quiet_gap_count=2`, `quiet_gap_type_counts={'positive_source_only_keep_collecting': 416, 'parent_conflict_child': 7, 'exclusion_dimension_candidate': 3, 'ai_review_parsed_low_coverage': 1}`, `ai_review_coverage={'status': 'parsed', 'shard_count': 5, 'parsed_shard_count': 4, 'reviewed_candidate_count': 4, 'low_coverage': True}`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: quiet_gap_summary rollup counts remain visible until explicitly resolved.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `terminal_existing_family_evidence`
- root_cause_closure_status: `-`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "terminal_existing_family_evidence", "previous_route": "ai_review_coverage_review", "repeat_count": 8, "repeat_key": "order_lifecycle_quiet_gap_ai_review_coverage_rollup", "repeat_signature": "sig:lifecycle_bucket_discovery_quiet_gap_rollup|lifecycle_bucket_discovery_taxonomy_provenance|multi_stage|quiet_gap_rollup_evidence|lifecycle_bucket_discovery|lifecycle_quiet_gap_ai_review_coverage_review", "review_disposition": "keep_visible_by_design"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose checklist/workorder should keep quiet_gap_summary visible until the gap is implemented, covered by parent policy, deferred for more sample, or explicitly rejected.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 80. `order_lifecycle_quiet_gap_parent_conflict_rollup`

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
- evidence: `quiet_gap_count=419`, `rollup_required_count=419`, `sim_live_connected_quiet_gap_count=2`, `quiet_gap_type_counts={'positive_source_only_keep_collecting': 416, 'parent_conflict_child': 7, 'exclusion_dimension_candidate': 3, 'ai_review_parsed_low_coverage': 1}`, `ai_review_coverage={'status': 'parsed', 'shard_count': 5, 'parsed_shard_count': 4, 'reviewed_candidate_count': 4, 'low_coverage': True}`, `runtime_effect=false`, `allowed_runtime_apply=false`, `parent_conflict_resolution_count=2`, `resolution_states={'resolution_blocked_thin_sample': 2}`, `sim_eligible_after_resolution=0`
- parity_contract: -
- next_postclose_metric: quiet_gap_summary rollup counts remain visible until explicitly resolved.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_lifecycle_quiet_gap_parent_conflict_rollup", "repeat_signature": "sig:lifecycle_bucket_discovery_quiet_gap_rollup|lifecycle_bucket_discovery_taxonomy_provenance|multi_stage|quiet_gap_rollup_evidence|lifecycle_bucket_discovery|lifecycle_quiet_gap_parent_conflict_exclusion_review", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 81. `order_lifecycle_quiet_gap_positive_source_only_rollup`

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
- evidence: `quiet_gap_count=419`, `rollup_required_count=419`, `sim_live_connected_quiet_gap_count=2`, `quiet_gap_type_counts={'positive_source_only_keep_collecting': 416, 'parent_conflict_child': 7, 'exclusion_dimension_candidate': 3, 'ai_review_parsed_low_coverage': 1}`, `ai_review_coverage={'status': 'parsed', 'shard_count': 5, 'parsed_shard_count': 4, 'reviewed_candidate_count': 4, 'low_coverage': True}`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: quiet_gap_summary rollup counts remain visible until explicitly resolved.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `terminal_existing_family_evidence`
- root_cause_closure_status: `-`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "terminal_existing_family_evidence", "previous_route": "positive_source_only_review", "repeat_count": 8, "repeat_key": "order_lifecycle_quiet_gap_positive_source_only_rollup", "repeat_signature": "sig:lifecycle_bucket_discovery_quiet_gap_rollup|lifecycle_bucket_discovery_taxonomy_provenance|multi_stage|quiet_gap_rollup_evidence|lifecycle_bucket_discovery|lifecycle_quiet_gap_positive_source_only_review", "review_disposition": "keep_visible_by_design"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose checklist/workorder should keep quiet_gap_summary visible until the gap is implemented, covered by parent policy, deferred for more sample, or explicitly rejected.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 82. `order_lifecycle_source_dimension_gap_rollup`

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
- evidence: `rollup_only_gap_count=65`, `unknown_source_dimensions=7`, `recommended_resolution_counts={'explicit_lifecycle_flow_source_only_blocker': 57, 'entry_label_not_applicable': 1, 'mark_not_applicable_explicitly': 2, 'join_labels_before_bucket_decision': 4, 'source_quality_blocked_missing_runtime_features_ai_score': 1}`, `missing_dimension_key_counts={'entry': 30, 'exit': 96, 'holding': 76, 'submit': 60}`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: source_dimension_gap_summary rollup/actionable counts remain visible.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `terminal_existing_family_evidence`
- root_cause_closure_status: `-`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "terminal_existing_family_evidence", "previous_route": "source_dimension_rollup", "repeat_count": 8, "repeat_key": "order_lifecycle_source_dimension_gap_rollup", "repeat_signature": "sig:lifecycle_bucket_discovery_source_dimension_rollup|lifecycle_bucket_discovery_taxonomy_provenance|multi_stage|source_dimension_gap_rollup_evidence|lifecycle_bucket_discovery|unknown", "review_disposition": "keep_visible_by_design"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose checklist/workorder should keep source_dimension_gap_summary visible until actionable gaps are resolved or explicitly marked not applicable.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 83. `order_lifecycle_source_dimension_join_gap_enrichment`

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
- evidence: `join_gap_candidate_count=4`, `join_gap_stage_counts={'exit': 4}`, `join_gap_bucket_type_counts={'combo_exit_result': 2, 'exit_rule': 1, 'profit_band': 1}`, `join_gap_recommended_resolution_counts={'join_labels_before_bucket_decision': 4}`, `join_gap_missing_dimension_key_counts={}`, `recommended_next_action=enrich_bucket_label_or_join_key_before_bucket_decision`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: source_dimension_gap_summary.join_gap_enrichment candidate_count is tracked until explicitly closed.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `terminal_existing_family_evidence`
- root_cause_closure_status: `-`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose checklist/workorder should keep source_dimension_gap_summary visible until actionable gaps are resolved or explicitly marked not applicable.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 84. `order_conversion_lane_key_lineage_active_arm_1661ca30f0d594fd`

- title: Conversion lane blocker follow-up: key_lineage active_arm_1661ca30f0d594fd
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
- priority: `57`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_1661ca30f0d594fd`, `blocker_class=key_lineage`, `conversion_impact_rank=57`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_arm_1661ca30f0d594fd", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_1661ca30f0d594fd", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 85. `order_conversion_lane_key_lineage_active_arm_167e2213662b0147`

- title: Conversion lane blocker follow-up: key_lineage active_arm_167e2213662b0147
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
- priority: `58`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_167e2213662b0147`, `blocker_class=key_lineage`, `conversion_impact_rank=58`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_arm_167e2213662b0147", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_167e2213662b0147", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 86. `order_conversion_lane_key_lineage_active_arm_2c44a9b1dd392eb3`

- title: Conversion lane blocker follow-up: key_lineage active_arm_2c44a9b1dd392eb3
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
- priority: `59`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_2c44a9b1dd392eb3`, `blocker_class=key_lineage`, `conversion_impact_rank=59`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_arm_2c44a9b1dd392eb3", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_2c44a9b1dd392eb3", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 87. `order_conversion_lane_key_lineage_active_arm_2d256010e69684c1`

- title: Conversion lane blocker follow-up: key_lineage active_arm_2d256010e69684c1
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
- priority: `60`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_2d256010e69684c1`, `blocker_class=key_lineage`, `conversion_impact_rank=60`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_arm_2d256010e69684c1", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_2d256010e69684c1", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 88. `order_conversion_lane_key_lineage_active_arm_400bb07e38eb1ab2`

- title: Conversion lane blocker follow-up: key_lineage active_arm_400bb07e38eb1ab2
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
- priority: `61`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_400bb07e38eb1ab2`, `blocker_class=key_lineage`, `conversion_impact_rank=61`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_arm_400bb07e38eb1ab2", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_400bb07e38eb1ab2", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 89. `order_conversion_lane_key_lineage_active_arm_431cb98e1d4adfce`

- title: Conversion lane blocker follow-up: key_lineage active_arm_431cb98e1d4adfce
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
- priority: `62`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_431cb98e1d4adfce`, `blocker_class=key_lineage`, `conversion_impact_rank=62`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_arm_431cb98e1d4adfce", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_431cb98e1d4adfce", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 90. `order_conversion_lane_key_lineage_active_arm_518e85a70ac730e3`

- title: Conversion lane blocker follow-up: key_lineage active_arm_518e85a70ac730e3
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
- priority: `63`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_518e85a70ac730e3`, `blocker_class=key_lineage`, `conversion_impact_rank=63`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_arm_518e85a70ac730e3", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_518e85a70ac730e3", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 91. `order_conversion_lane_key_lineage_active_arm_52e8c1f2d0e05882`

- title: Conversion lane blocker follow-up: key_lineage active_arm_52e8c1f2d0e05882
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
- priority: `64`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_52e8c1f2d0e05882`, `blocker_class=key_lineage`, `conversion_impact_rank=64`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_arm_52e8c1f2d0e05882", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_52e8c1f2d0e05882", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 92. `order_conversion_lane_key_lineage_active_arm_5ed5448f4e3ccb60`

- title: Conversion lane blocker follow-up: key_lineage active_arm_5ed5448f4e3ccb60
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
- priority: `65`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_5ed5448f4e3ccb60`, `blocker_class=key_lineage`, `conversion_impact_rank=65`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_arm_5ed5448f4e3ccb60", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_5ed5448f4e3ccb60", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 93. `order_conversion_lane_key_lineage_active_arm_665f8e1098e38541`

- title: Conversion lane blocker follow-up: key_lineage active_arm_665f8e1098e38541
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
- priority: `66`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_665f8e1098e38541`, `blocker_class=key_lineage`, `conversion_impact_rank=66`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_arm_665f8e1098e38541", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_665f8e1098e38541", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 94. `order_conversion_lane_key_lineage_active_arm_82f4bc68bb168a83`

- title: Conversion lane blocker follow-up: key_lineage active_arm_82f4bc68bb168a83
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
- priority: `67`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_82f4bc68bb168a83`, `blocker_class=key_lineage`, `conversion_impact_rank=67`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_conversion_lane_key_lineage_active_arm_82f4bc68bb168a83", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_82f4bc68bb168a83", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 95. `order_conversion_lane_key_lineage_active_arm_888ade47545aacbc`

- title: Conversion lane blocker follow-up: key_lineage active_arm_888ade47545aacbc
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
- priority: `68`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_888ade47545aacbc`, `blocker_class=key_lineage`, `conversion_impact_rank=68`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_conversion_lane_key_lineage_active_arm_888ade47545aacbc", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_888ade47545aacbc", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 96. `order_conversion_lane_key_lineage_active_arm_89383c15a79e92ee`

- title: Conversion lane blocker follow-up: key_lineage active_arm_89383c15a79e92ee
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
- priority: `69`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_89383c15a79e92ee`, `blocker_class=key_lineage`, `conversion_impact_rank=69`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_conversion_lane_key_lineage_active_arm_89383c15a79e92ee", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_89383c15a79e92ee", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 97. `order_conversion_lane_key_lineage_active_arm_8ca13269eecf5f8e`

- title: Conversion lane blocker follow-up: key_lineage active_arm_8ca13269eecf5f8e
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
- priority: `70`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_8ca13269eecf5f8e`, `blocker_class=key_lineage`, `conversion_impact_rank=70`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_conversion_lane_key_lineage_active_arm_8ca13269eecf5f8e", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_8ca13269eecf5f8e", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 98. `order_conversion_lane_key_lineage_active_arm_8eb6698f81674caf`

- title: Conversion lane blocker follow-up: key_lineage active_arm_8eb6698f81674caf
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
- priority: `71`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_8eb6698f81674caf`, `blocker_class=key_lineage`, `conversion_impact_rank=71`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_conversion_lane_key_lineage_active_arm_8eb6698f81674caf", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_8eb6698f81674caf", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 99. `order_conversion_lane_key_lineage_active_arm_a0d18f8d00f97208`

- title: Conversion lane blocker follow-up: key_lineage active_arm_a0d18f8d00f97208
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
- priority: `72`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_a0d18f8d00f97208`, `blocker_class=key_lineage`, `conversion_impact_rank=72`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 4, "repeat_key": "order_conversion_lane_key_lineage_active_arm_a0d18f8d00f97208", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_a0d18f8d00f97208", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 100. `order_conversion_lane_key_lineage_active_arm_af0dff677e6a12e4`

- title: Conversion lane blocker follow-up: key_lineage active_arm_af0dff677e6a12e4
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
- priority: `73`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_af0dff677e6a12e4`, `blocker_class=key_lineage`, `conversion_impact_rank=73`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_conversion_lane_key_lineage_active_arm_af0dff677e6a12e4", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_af0dff677e6a12e4", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 101. `order_conversion_lane_key_lineage_active_arm_b460665611c8fde0`

- title: Conversion lane blocker follow-up: key_lineage active_arm_b460665611c8fde0
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
- priority: `74`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_b460665611c8fde0`, `blocker_class=key_lineage`, `conversion_impact_rank=74`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_conversion_lane_key_lineage_active_arm_b460665611c8fde0", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_b460665611c8fde0", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 102. `order_conversion_lane_key_lineage_active_arm_ba238963f55dedbe`

- title: Conversion lane blocker follow-up: key_lineage active_arm_ba238963f55dedbe
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
- priority: `75`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_ba238963f55dedbe`, `blocker_class=key_lineage`, `conversion_impact_rank=75`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 103. `order_conversion_lane_key_lineage_active_arm_c86557302f4681f3`

- title: Conversion lane blocker follow-up: key_lineage active_arm_c86557302f4681f3
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
- priority: `76`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_c86557302f4681f3`, `blocker_class=key_lineage`, `conversion_impact_rank=76`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 104. `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_euphoria_context_noop_rule_exit_rule_unknown_outcome_o_5f592cef`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown
- decision: `defer_evidence`
- decision_reason: not code-actionable in this cycle: no files_likely_touched and no runnable acceptance tests
- source_report_type: `lifecycle_decision_matrix_exit_bucket_attribution`
- lifecycle_stage: `exit`
- target_subsystem: `lifecycle_decision_matrix`
- route: `instrumentation_order`
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
- evidence: `workorder_id=exit_bucket_source_quality_8`, `bucket_type=combo_exit_result`, `bucket_key=source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=source_quality_workorder`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `terminal_deferred_evidence`
- root_cause_closure_status: `-`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "source_quality_workorder", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "hold_sample"}, "recommended_resolution": "join_labels_before_bucket_decision", "source_field_coverage": {"outcome": {"coverage_rate": 1.0, "present_count": 55, "sample_count": 55, "source_fields": ["source_stage", "labels.exit_rule", "runtime_features.chosen_action", "labels.sim_post_sell_outcome", "labels.outcome", "labels.profit_rate"]}, "profit": {"coverage_rate": 1.0, "present_count": 55, "sample_count": 55, "source_fields": ["source_stage", "labels.exit_rule", "runtime_features.chosen_action", "labels.sim_post_sell_outcome", "labels.outcome", "labels.profit_rate"]}, "rule": {"coverage_rate": 1.0, "present_count": 55, "sample_count": 55, "source_fields": ["source_stage", "labels.exit_rule", "runtime_features.chosen_action", "labels.sim_post_sell_outcome", "labels.outcome", "labels.profit_rate"]}}, "unknown_reason_counts": {"join_gap": 3}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "defer_evidence", "previous_implementation_status": "terminal_deferred_evidence", "previous_route": "instrumentation_order", "repeat_count": 8, "repeat_key": "order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_euphoria_context_noop_rule_exit_rule_unknown_outcome_o_5f592cef", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_scalp_sim_euph", "review_disposition": "review_required"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Keep the item out of the canonical implement_now queue; regenerated postclose reports and runner terminal dispositions must preserve the non-implement decision.

실행 기준:

- 구현하지 말고 부족한 evidence와 다음 확인 artifact를 명시한다.
- 필요한 경우 report warning 또는 다음 pattern lab 재평가 항목으로만 남긴다.

### 105. `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_panic_context_warning_rule_exit_rule_unknown_outcome_o_58a13326`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown
- decision: `defer_evidence`
- decision_reason: not code-actionable in this cycle: no files_likely_touched and no runnable acceptance tests
- source_report_type: `lifecycle_decision_matrix_exit_bucket_attribution`
- lifecycle_stage: `exit`
- target_subsystem: `lifecycle_decision_matrix`
- route: `instrumentation_order`
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
- evidence: `workorder_id=exit_bucket_source_quality_9`, `bucket_type=combo_exit_result`, `bucket_key=source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=source_quality_workorder`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `terminal_deferred_evidence`
- root_cause_closure_status: `-`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "source_quality_workorder", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "hold_sample"}, "recommended_resolution": "join_labels_before_bucket_decision", "source_field_coverage": {"outcome": {"coverage_rate": 1.0, "present_count": 1609, "sample_count": 1609, "source_fields": ["source_stage", "labels.exit_rule", "runtime_features.chosen_action", "labels.sim_post_sell_outcome", "labels.outcome", "labels.profit_rate"]}, "profit": {"coverage_rate": 1.0, "present_count": 1609, "sample_count": 1609, "source_fields": ["source_stage", "labels.exit_rule", "runtime_features.chosen_action", "labels.sim_post_sell_outcome", "labels.outcome", "labels.profit_rate"]}, "rule": {"coverage_rate": 1.0, "present_count": 1609, "sample_count": 1609, "source_fields": ["source_stage", "labels.exit_rule", "runtime_features.chosen_action", "labels.sim_post_sell_outcome", "labels.outcome", "labels.profit_rate"]}}, "unknown_reason_counts": {"join_gap": 3}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "defer_evidence", "previous_implementation_status": "terminal_deferred_evidence", "previous_route": "instrumentation_order", "repeat_count": 8, "repeat_key": "order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_panic_context_warning_rule_exit_rule_unknown_outcome_o_58a13326", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_scalp_sim_pani", "review_disposition": "review_required"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Keep the item out of the canonical implement_now queue; regenerated postclose reports and runner terminal dispositions must preserve the non-implement decision.

실행 기준:

- 구현하지 말고 부족한 evidence와 다음 확인 artifact를 명시한다.
- 필요한 경우 report warning 또는 다음 pattern lab 재평가 항목으로만 남긴다.

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
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "performance_optimization_order", "repeat_count": 8, "repeat_key": "order_perf_buy_funnel_json_scan", "repeat_signature": "sig:codebase_performance_workorder|buy_funnel_sentinel|ops_performance|||buy_funnel_sentinel_field_scan_without_repeated_json_dumps", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`
- acceptance_tests: `pytest src/tests/test_buy_funnel_sentinel.py`, `BUY Sentinel classification parity on same raw/cache input`

### N2. `order_swing_pattern_lab_deepseek_selection_low_candidate_count`

- title: Low swing candidate count per day
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_pattern_lab_automation`
- lifecycle_stage: `selection`
- target_subsystem: `swing_model_selection`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_source_quality_contract_available`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_swing_pattern_lab_deepseek_selection_low_candidate_count", "repeat_signature": "sig:swing_pattern_lab_automation|swing_model_selection|selection|pattern_lab_observation|swing_selection_top_k|low_swing_candidate_count_per_day", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/swing_lifecycle_audit.py`, `src/engine/swing_selection_funnel_report.py`, `src/model/common_v2.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_model_selection_funnel_repair.py`, `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_deepseek_swing_pattern_lab.py`

### N3. `order_latency_guard_miss_ev_recovery`

- title: latency guard miss EV recovery
- decision: `attach_existing_family`
- decision_reason: instrumentation/provenance contract is already implemented; keep as report source for the existing family
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `runtime_instrumentation`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_but_waiting_sample`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_latency_guard_miss_ev_recovery", "repeat_signature": "sig:scalping_pattern_lab_automation|runtime_instrumentation||latency_guard_miss_ev_recovery||latency_guard_miss_ev_recovery", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/sniper_performance_tuning_report.py`, `src/engine/daily_threshold_cycle_report.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N4. `order_perf_daily_report_bulk_history`

- title: Daily report market snapshot bulk history query
- decision: `attach_existing_family`
- decision_reason: report-only performance implementation is already present in code; keep the order as provenance and validate through regenerated reports/tests instead of re-implementing
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `daily_report`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "performance_optimization_order", "repeat_count": 8, "repeat_key": "order_perf_daily_report_bulk_history", "repeat_signature": "sig:codebase_performance_workorder|daily_report|ops_performance|||daily_report_market_snapshot_bulk_history_query", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_report_service.py`
- acceptance_tests: `pytest src/tests/test_daily_report_service.py src/tests/test_daily_report.py`, `daily report output parity on injected DB/model fixture`

### N5. `order_rising_missed_classifier_prior_feedback_bridge`

- title: rising missed cumulative classifier prior bridge
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `rising_missed_scout_workorder`
- lifecycle_stage: `entry`
- target_subsystem: `rising_missed_entry_classifier`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 4, "repeat_key": "order_rising_missed_classifier_prior_feedback_bridge", "repeat_signature": "sig:rising_missed_scout_workorder|rising_missed_entry_classifier|entry|source_only_classifier_prior_workorder|rising_missed_classifier_prior_feedback_bridge|rising_missed_cumulative_classifier_prior_bridge", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/monitoring/rising_missed_classifier_prior.py`, `src/engine/monitoring/rising_missed_scout_workorder.py`, `src/engine/scalping/rising_missed_one_share_entry.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_classifier_prior.py src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py`, `prior bridge remains source-only and cannot mutate one-share allow/block, runtime thresholds, broker/order guards, provider route, or bot state`

### N6. `order_rising_missed_scout_loss_filter`

- title: rising missed scout loss filter before any expansion
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `rising_missed_scout_workorder`
- lifecycle_stage: `entry`
- target_subsystem: `entry_risk_filter`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_rising_missed_scout_loss_filter", "repeat_signature": "sig:rising_missed_scout_workorder|entry_risk_filter|entry|source_only_operational_workorder|rising_missed_scout_loss_filter|rising_missed_scout_loss_filter_before_any_expansion", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/monitoring/rising_missed_scout_workorder.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py`, `loss filter is source-only and does not relax stops or broker/order guards`

### N7. `order_rising_missed_scout_post_sell_bridge`

- title: rising missed scout post-sell bridge for normal-entry recheck
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `rising_missed_scout_workorder`
- lifecycle_stage: `entry`
- target_subsystem: `entry_freshness`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_rising_missed_scout_post_sell_bridge", "repeat_signature": "sig:rising_missed_scout_workorder|entry_freshness|entry|source_only_operational_workorder|rising_missed_scout_post_sell_bridge|rising_missed_scout_post_sell_bridge_for_normal_entry_recheck", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/monitoring/rising_missed_scout_workorder.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py`, `forced scout remains excluded from normal BUY/submit/fill success counts`, `runtime_effect remains false until a separate approved runtime family exists`

### N8. `order_rising_missed_scout_take_profit_capture_review`

- title: rising missed scout take-profit capture review
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `rising_missed_scout_workorder`
- lifecycle_stage: `holding_exit`
- target_subsystem: `take_profit_and_trailing_capture`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/monitoring/rising_missed_scout_workorder.py`, `src/engine/holding_exit_observation_report.py`, `src/engine/daily_threshold_cycle_report.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py`, `take-profit capture review remains source-only and cannot widen TP/trailing or force holding extension`

### N9. `order_swing_pattern_lab_deepseek_entry_no_submissions`

- title: All selected candidates failed to reach order submission
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_pattern_lab_automation`
- lifecycle_stage: `entry`
- target_subsystem: `swing_entry_funnel`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_swing_pattern_lab_deepseek_entry_no_submissions", "repeat_signature": "sig:swing_pattern_lab_automation|swing_entry_funnel|entry|pattern_lab_observation||all_selected_candidates_failed_to_reach_order_submission", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/swing_lifecycle_audit.py`, `src/engine/swing_selection_funnel_report.py`, `src/model/common_v2.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_model_selection_funnel_repair.py`, `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_deepseek_swing_pattern_lab.py`

### N10. `order_ai_threshold_miss_ev_recovery`

- title: AI threshold miss EV recovery
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `entry_funnel`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_ai_threshold_miss_ev_recovery", "repeat_signature": "sig:scalping_pattern_lab_automation|entry_funnel||threshold_family_input||ai_threshold_miss_ev_recovery", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_missed_entry_counterfactual.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N11. `order_perf_daily_report_engine_singleton`

- title: Daily report SQLAlchemy engine singleton
- decision: `attach_existing_family`
- decision_reason: report-only performance implementation is already present in code; keep the order as provenance and validate through regenerated reports/tests instead of re-implementing
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `daily_report`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "performance_optimization_order", "repeat_count": 8, "repeat_key": "order_perf_daily_report_engine_singleton", "repeat_signature": "sig:codebase_performance_workorder|daily_report|ops_performance|||daily_report_sqlalchemy_engine_singleton", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_report_service.py`
- acceptance_tests: `pytest src/tests/test_daily_report_service.py src/tests/test_daily_report.py`, `engine creation count regression test`

### N12. `order_rising_missed_classifier_prior_bridge`

- title: Attach cumulative ADM/LDM prior lookup to rising-missed classifier reports
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `rising_missed_classifier_prior`
- lifecycle_stage: `entry`
- target_subsystem: `rising_missed_entry_classifier`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 4, "repeat_key": "order_rising_missed_classifier_prior_bridge", "repeat_signature": "sig:rising_missed_classifier_prior|rising_missed_entry_classifier|entry||rising_missed_classifier_prior_bridge|attach_cumulative_adm_ldm_prior_lookup_to_rising_missed_classifier_reports", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: -
- acceptance_tests: -

### N13. `order_perf_recommend_update_vectorization`

- title: Recommendation and update_kospi vectorized membership checks
- decision: `attach_existing_family`
- decision_reason: report-only performance implementation is already present in code; keep the order as provenance and validate through regenerated reports/tests instead of re-implementing
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `swing_daily_recommendation`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "performance_optimization_order", "repeat_count": 8, "repeat_key": "order_perf_recommend_update_vectorization", "repeat_signature": "sig:codebase_performance_workorder|swing_daily_recommendation|ops_performance|||recommendation_and_update_kospi_vectorized_membership_checks", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/model/recommend_daily_v2.py`, `src/utils/update_kospi.py`
- acceptance_tests: `pytest src/tests/test_swing_retrain_automation.py src/tests/test_swing_feature_ssot.py`, `recommendation CSV and diagnostics parity`

### N14. `order_swing_holding_exit_contract_gap_review`

- title: swing holding/exit contract gap review
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_improvement_automation`
- lifecycle_stage: `holding_exit`
- target_subsystem: `swing_holding_exit`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_swing_holding_exit_contract_gap_review", "repeat_signature": "sig:swing_improvement_automation|swing_holding_exit|holding_exit|lifecycle_contract_gap|swing_exit_ofi_qi_smoothing|swing_holding_exit_contract_gap_review", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/swing_lifecycle_audit.py`, `src/engine/ai_prompt_contracts.py`, `src/engine/ai_engine_openai.py`
- acceptance_tests: `pytest swing lifecycle audit tests`

### N15. `order_swing_ofi_qi_stale_or_missing_context`

- title: swing OFI/QI stale or missing context
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_improvement_automation`
- lifecycle_stage: `entry`
- target_subsystem: `swing_orderbook_micro_context`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/orderbook_stability.py`, `src/engine/swing_lifecycle_audit.py`
- acceptance_tests: `pytest orderbook stability tests`, `pytest swing lifecycle audit tests`

### N16. `order_swing_scale_in_contract_gap_review`

- title: swing scale-in contract gap review
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_improvement_automation`
- lifecycle_stage: `scale_in`
- target_subsystem: `swing_scale_in`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_swing_scale_in_contract_gap_review", "repeat_signature": "sig:swing_improvement_automation|swing_scale_in|scale_in|lifecycle_contract_gap|swing_scale_in_ofi_qi_confirmation|swing_scale_in_contract_gap_review", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/swing_lifecycle_audit.py`, `src/engine/sniper_scale_in.py`
- acceptance_tests: `pytest swing lifecycle audit tests`

### N17. `order_perf_swing_simulation_iteration`

- title: Swing simulation iteration and quote grouping
- decision: `attach_existing_family`
- decision_reason: report-only performance implementation is already present in code; keep the order as provenance and validate through regenerated reports/tests instead of re-implementing
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `swing_daily_simulation`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "performance_optimization_order", "repeat_count": 8, "repeat_key": "order_perf_swing_simulation_iteration", "repeat_signature": "sig:codebase_performance_workorder|swing_daily_simulation|ops_performance|||swing_simulation_iteration_and_quote_grouping", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/swing_daily_simulation_report.py`
- acceptance_tests: `pytest src/tests/test_swing_model_selection_funnel_repair.py`, `swing simulation JSON parity on injected sources`

### N18. `order_swing_ai_contract_structured_output_eval`

- title: swing AI contract structured output eval
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_improvement_automation`
- lifecycle_stage: `ai_contract`
- target_subsystem: `swing_ai_contract`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_waiting_sample", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_swing_ai_contract_structured_output_eval", "repeat_signature": "sig:swing_improvement_automation|swing_ai_contract|ai_contract|ai_contract_eval|swing_ai_contract_structured_output_eval|swing_ai_contract_structured_output_eval", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/ai_prompt_contracts.py`, `src/engine/ai_engine_openai.py`, `src/engine/ai_response_contracts.py`
- acceptance_tests: `pytest OpenAI transport/schema tests`, `pytest swing lifecycle audit tests`

### N19. `order_swing_discovery_label_contract_gap_review`

- title: swing discovery label contract gap review
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_improvement_automation`
- lifecycle_stage: `selection`
- target_subsystem: `swing_strategy_discovery`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_swing_discovery_label_contract_gap_review", "repeat_signature": "sig:swing_improvement_automation|swing_strategy_discovery|selection|lifecycle_contract_gap||swing_discovery_label_contract_gap_review", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/swing_strategy_discovery_label_builder.py`, `src/engine/swing_strategy_discovery_ev_report.py`
- acceptance_tests: `pytest swing lifecycle audit tests`

### N20. `order_swing_pattern_lab_deepseek_ofi_qi_smoothing_review`

- title: OFI/QI exit smoothing action distribution
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_pattern_lab_automation`
- lifecycle_stage: `ofi_qi`
- target_subsystem: `swing_micro_context`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_swing_pattern_lab_deepseek_ofi_qi_smoothing_review", "repeat_signature": "sig:swing_pattern_lab_automation|swing_micro_context|ofi_qi|pattern_lab_observation|swing_exit_ofi_qi_smoothing|ofi_qi_exit_smoothing_action_distribution", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/swing_lifecycle_audit.py`, `src/engine/swing_selection_funnel_report.py`, `src/model/common_v2.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_model_selection_funnel_repair.py`, `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_deepseek_swing_pattern_lab.py`

### N21. `order_panic_sell_defense_lifecycle_transition_pack`

- title: panic sell defense lifecycle transition pack
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `threshold_cycle_calibration_source_bundle`
- lifecycle_stage: `holding_exit`
- target_subsystem: `panic_sell_defense`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_but_waiting_sample`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_panic_sell_defense_lifecycle_transition_pack", "repeat_signature": "sig:threshold_cycle_calibration_source_bundle|panic_sell_defense|holding_exit|runtime_transition_design|panic_sell_defense|panic_sell_defense_lifecycle_transition_pack", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/panic_sell_defense_report.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/plan-korStockScanPerformanceOptimization.rebase.md`
- acceptance_tests: `pytest panic sell defense/report lifecycle tests`, `pytest src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py`

### N22. `order_perf_monitor_snapshot_stream_tail`

- title: Monitor snapshot runtime streaming tail read
- decision: `attach_existing_family`
- decision_reason: report-only performance implementation is already present in code; keep the order as provenance and validate through regenerated reports/tests instead of re-implementing
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `monitor_snapshot`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "performance_optimization_order", "repeat_count": 8, "repeat_key": "order_perf_monitor_snapshot_stream_tail", "repeat_signature": "sig:codebase_performance_workorder|monitor_snapshot|ops_performance|||monitor_snapshot_runtime_streaming_tail_read", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/monitor_snapshot_runtime.py`
- acceptance_tests: `pytest src/tests/test_log_archive_service.py`, `last valid JSON line parity`

### N23. `order_swing_exit_ofi_qi_smoothing_distribution`

- title: swing exit OFI/QI smoothing distribution
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_improvement_automation`
- lifecycle_stage: `holding_exit`
- target_subsystem: `swing_holding_exit`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_swing_exit_ofi_qi_smoothing_distribution", "repeat_signature": "sig:swing_improvement_automation|swing_holding_exit|holding_exit|threshold_family_input|swing_exit_ofi_qi_smoothing|swing_exit_ofi_qi_smoothing_distribution", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/swing_lifecycle_audit.py`
- acceptance_tests: `pytest OFI smoothing tests`, `pytest swing lifecycle audit tests`

### N24. `order_swing_scale_in_avg_down_pyramid_observation`

- title: swing scale-in AVG_DOWN/PYRAMID observation
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_improvement_automation`
- lifecycle_stage: `scale_in`
- target_subsystem: `swing_scale_in`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_waiting_sample", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_swing_scale_in_avg_down_pyramid_observation", "repeat_signature": "sig:swing_improvement_automation|swing_scale_in|scale_in|lifecycle_logic_observation||swing_scale_in_avg_down_pyramid_observation", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/sniper_scale_in.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest sniper scale-in tests`, `pytest swing lifecycle audit tests`

### N25. `order_swing_strategy_discovery_source_quality_followup`

- title: swing strategy discovery label/source quality follow-up
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_strategy_discovery_ev`
- lifecycle_stage: `source_quality`
- target_subsystem: `swing_strategy_discovery_sim`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_swing_strategy_discovery_source_quality_followup", "repeat_signature": "sig:swing_strategy_discovery_ev|swing_strategy_discovery_sim|source_quality|source_quality_instrumentation||swing_strategy_discovery_label_source_quality_follow_up", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/swing_strategy_discovery_label_builder.py`, `src/engine/swing_strategy_discovery_ev_report.py`, `src/engine/swing_sector_theme_source.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_strategy_discovery_label_builder.py src/tests/test_swing_strategy_discovery_ev_report.py src/tests/test_swing_sector_theme_source.py`

### N26. `order_panic_buying_source_quality_market_breadth_micro_coverage`

- title: panic buying source-quality market breadth and micro coverage
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `threshold_cycle_calibration_source_bundle`
- lifecycle_stage: `source_quality`
- target_subsystem: `panic_buying`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_waiting_sample", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_panic_buying_source_quality_market_breadth_micro_coverage", "repeat_signature": "sig:threshold_cycle_calibration_source_bundle|panic_buying|source_quality|source_quality_instrumentation||panic_buying_source_quality_market_breadth_and_micro_coverage", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/panic_buying_report.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/plan-korStockScanPerformanceOptimization.rebase.md`, `docs/code-improvement-workorders/panic_buying_regime_mode_v2_2026-05-14.md`
- acceptance_tests: `pytest src/tests/test_panic_buying_report.py`, `pytest src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py`

### N27. `order_perf_final_ensemble_records`

- title: Final ensemble scanner records conversion without iterrows
- decision: `attach_existing_family`
- decision_reason: report-only performance implementation is already present in code; keep the order as provenance and validate through regenerated reports/tests instead of re-implementing
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `final_ensemble_scanner`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "performance_optimization_order", "repeat_count": 8, "repeat_key": "order_perf_final_ensemble_records", "repeat_signature": "sig:codebase_performance_workorder|final_ensemble_scanner|ops_performance|||final_ensemble_scanner_records_conversion_without_iterrows", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/scanners/final_ensemble_scanner.py`
- acceptance_tests: `pytest src/tests/test_swing_model_selection_funnel_repair.py`, `V2 CSV pick list parity`

### N28. `order_swing_strategy_discovery_avoid_bucket_review`

- title: swing strategy discovery avoid bucket report enrichment
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_strategy_discovery_ev`
- lifecycle_stage: `selection`
- target_subsystem: `swing_strategy_discovery_sim`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_swing_strategy_discovery_avoid_bucket_review", "repeat_signature": "sig:swing_strategy_discovery_ev|swing_strategy_discovery_sim|selection|analysis_report_provenance||swing_strategy_discovery_avoid_bucket_report_enrichment", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/swing_strategy_discovery_ev_report.py`, `docs/swing-strategy-discovery-sim-v1.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_strategy_discovery_ev_report.py src/tests/test_build_code_improvement_workorder.py`

### N29. `order_partial_only_표류_전용_timeout_report_only`

- title: partial-only 표류 전용 timeout report-only
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `holding_exit`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_but_waiting_sample`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_partial_only_표류_전용_timeout_report_only", "repeat_signature": "sig:scalping_pattern_lab_automation|holding_exit||threshold_family_input||partial_only_표류_전용_timeout_report_only", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N30. `order_split_entry_rebase_수량_정합성_report_only_감사`

- title: split-entry rebase 수량 정합성 report-only 감사
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `holding_exit`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_but_waiting_sample`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_split_entry_rebase_수량_정합성_report_only_감사", "repeat_signature": "sig:scalping_pattern_lab_automation|holding_exit||threshold_family_input||split_entry_rebase_수량_정합성_report_only_감사", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N31. `order_동일_종목_split_entry_soft_stop_재진입_cooldown_report_only`

- title: 동일 종목 split-entry soft-stop 재진입 cooldown report-only
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `holding_exit`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_but_waiting_sample`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_동일_종목_split_entry_soft_stop_재진입_cooldown_report_only", "repeat_signature": "sig:scalping_pattern_lab_automation|holding_exit||threshold_family_input||동일_종목_split_entry_soft_stop_재진입_cooldown_report_only", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N32. `order_no_acute_observability_alert`

- title: No acute observability alert
- decision: `design_family_candidate`
- decision_reason: pattern lab can only propose source-only family design input; LDM/discovery/runtime bridge contracts must close before any auto_bounded_live consideration
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `scalping_logic`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_design_family_candidate`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "design_family_candidate", "previous_implementation_status": "terminal_design_family_candidate", "previous_route": "auto_family_candidate", "repeat_count": 8, "repeat_key": "order_no_acute_observability_alert", "repeat_signature": "sig:scalping_pattern_lab_automation|scalping_logic||no_acute_observability_alert||no_acute_observability_alert", "review_disposition": "review_required"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N33. `order_liquidity_gate_miss_ev_recovery`

- title: liquidity gate miss EV recovery
- decision: `design_family_candidate`
- decision_reason: pattern lab can only propose source-only family design input; LDM/discovery/runtime bridge contracts must close before any auto_bounded_live consideration
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `entry_filter_quality`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_design_family_candidate`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "design_family_candidate", "previous_implementation_status": "terminal_design_family_candidate", "previous_route": "auto_family_candidate", "repeat_count": 8, "repeat_key": "order_liquidity_gate_miss_ev_recovery", "repeat_signature": "sig:scalping_pattern_lab_automation|entry_filter_quality||liquidity_gate_miss_ev_recovery||liquidity_gate_miss_ev_recovery", "review_disposition": "review_required"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N34. `order_overbought_gate_miss_ev_recovery`

- title: overbought gate miss EV recovery
- decision: `design_family_candidate`
- decision_reason: pattern lab can only propose source-only family design input; LDM/discovery/runtime bridge contracts must close before any auto_bounded_live consideration
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `entry_filter_quality`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_design_family_candidate`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "design_family_candidate", "previous_implementation_status": "terminal_design_family_candidate", "previous_route": "auto_family_candidate", "repeat_count": 8, "repeat_key": "order_overbought_gate_miss_ev_recovery", "repeat_signature": "sig:scalping_pattern_lab_automation|entry_filter_quality||overbought_gate_miss_ev_recovery||overbought_gate_miss_ev_recovery", "review_disposition": "review_required"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N35. `order_swing_lifecycle_observation_coverage`

- title: swing lifecycle observation coverage
- decision: `defer_evidence`
- decision_reason: not code-actionable in this cycle: acceptance contract is review text only, not an executable validation
- source_report_type: `swing_improvement_automation`
- lifecycle_stage: `full_lifecycle`
- target_subsystem: `runtime_instrumentation`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_deferred_evidence`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "defer_evidence", "previous_implementation_status": "terminal_deferred_evidence", "previous_route": "instrumentation_order", "repeat_count": 4, "repeat_key": "order_swing_lifecycle_observation_coverage", "repeat_signature": "sig:swing_improvement_automation|runtime_instrumentation|full_lifecycle|instrumentation||swing_lifecycle_observation_coverage", "review_disposition": "review_required"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/swing_lifecycle_audit.py`, `src/engine/sniper_state_handlers.py`, `src/engine/sniper_scale_in.py`
- acceptance_tests: `pytest swing lifecycle audit tests`, `pipeline event field coverage smoke`

### N36. `order_perf_kiwoom_orders_http_session_review`

- title: Kiwoom orders HTTP session reuse manual review
- decision: `defer_evidence`
- decision_reason: broker request lifecycle may change; requires manual review before implementation
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `broker_transport`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_deferred_evidence`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "defer_evidence", "previous_implementation_status": "terminal_deferred_evidence", "previous_route": "performance_optimization_order", "repeat_count": 8, "repeat_key": "order_perf_kiwoom_orders_http_session_review", "repeat_signature": "sig:codebase_performance_workorder|broker_transport|ops_performance|||kiwoom_orders_http_session_reuse_manual_review", "review_disposition": "review_required"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/kiwoom_orders.py`
- acceptance_tests: `pytest src/tests/test_kiwoom_orders.py src/tests/test_sniper_scale_in.py`

### N37. `order_perf_config_cache_scope_review`

- title: Config cache scope review
- decision: `defer_evidence`
- decision_reason: runtime config reload semantics are not yet bounded
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `config_loading`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_deferred_evidence`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "defer_evidence", "previous_implementation_status": "terminal_deferred_evidence", "previous_route": "performance_optimization_order", "repeat_count": 8, "repeat_key": "order_perf_config_cache_scope_review", "repeat_signature": "sig:codebase_performance_workorder|config_loading|ops_performance|||config_cache_scope_review", "review_disposition": "review_required"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/utils/constants.py`, `src/utils/kiwoom_utils.py`
- acceptance_tests: `pytest config/import smoke tests`

### N38. `order_perf_sentinel_event_cache_incremental_review`

- title: Sentinel event cache incremental parse review
- decision: `defer_evidence`
- decision_reason: incremental cache semantics require a dedicated parity harness before implementation
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `sentinel_event_cache`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_deferred_evidence`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "defer_evidence", "previous_implementation_status": "terminal_deferred_evidence", "previous_route": "performance_optimization_order", "repeat_count": 3, "repeat_key": "order_perf_sentinel_event_cache_incremental_review", "repeat_signature": "sig:codebase_performance_workorder|sentinel_event_cache|ops_performance|||sentinel_event_cache_incremental_parse_review", "review_disposition": "review_required"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/sentinel_event_cache.py`
- acceptance_tests: `pytest src/tests/test_buy_funnel_sentinel.py src/tests/test_holding_exit_sentinel.py`, `sentinel event cache parity on malformed, unchanged, and appended JSONL inputs`

### N39. `order_partial_fallback_확대_직후_즉시_재평가_report_only`

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

### N40. `order_perf_kiwoom_ws_tick_parse_fastpath`

- title: Kiwoom websocket tick parsing fast path
- decision: `reject`
- decision_reason: quote/data-quality semantics can change; requires separate data-quality approval owner
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `quote_data_quality`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_rejected`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/kiwoom_websocket.py`
- acceptance_tests: `pytest websocket parsing/data-quality tests`

### N41. `order_perf_raw_event_suppression_out_of_scope`

- title: Raw pipeline event suppression out of scope
- decision: `reject`
- decision_reason: raw suppression is governed by pipeline event V2 suppress guard
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `pipeline_event_storage`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_rejected`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/utils/pipeline_event_logger.py`
- acceptance_tests: `pytest pipeline event verbosity tests`

## 자동화체인 재투입

- 구현 결과는 `2026-07-09` 이후 postclose `threshold_cycle`, `scalping_pattern_lab_automation`, `threshold_cycle_ev`가 자동으로 다시 읽는다.
- 구현자가 수동으로 threshold 값을 바꾸는 것이 아니라, source/report/provenance를 닫아 다음 calibration이 판단하게 한다.
- 다음 Codex 세션 입력 문구: `none_for_bucket_discovery_classification`

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
