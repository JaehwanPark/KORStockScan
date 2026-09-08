# Code Improvement Workorder - 2026-09-07

## 목적

- Postclose 자동화가 생성한 `code_improvement_order`를 Codex 실행용 작업지시서로 변환한다.
- 입력은 scalping pattern lab automation, swing lifecycle improvement automation, swing pattern lab automation을 함께 포함할 수 있다.
- 이 문서는 repo/runtime을 직접 변경하지 않는다. 사용자가 이 문서를 Codex 세션에 넣고 구현을 요청하는 지점만 사람 개입으로 남긴다.
- 구현 후 자동화체인 재투입은 다음 postclose report, threshold calibration, daily EV report가 담당한다.

## Source

- pattern_lab_automation: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-09-07.json`
- swing_improvement_automation: `-`
- swing_pattern_lab_automation: `-`
- swing_strategy_discovery_ev: `-`
- swing_lifecycle_decision_matrix: `-`
- swing_lifecycle_bucket_discovery: `-`
- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-07.json`
- lifecycle_decision_matrix: `-`
- threshold_cycle_calibration: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_calibration/threshold_cycle_calibration_2026-09-07_postclose.json`
- pipeline_event_verbosity: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-09-07.json`
- observation_source_quality_audit: `/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-07.json`
- ai_decision_action_outcome_calibration: `/home/ubuntu/KORStockScan/data/report/ai_decision_action_outcome_calibration/ai_decision_action_outcome_calibration_2026-09-07.json`
- codebase_performance_workorder: `-`
- pattern_lab_currentness_audit: `/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-09-07.json`
- pattern_lab_ai_review: `/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-09-07.json`
- producer_gap_discovery: `-`
- stage_hook_workorder_discovery: `-`
- stage_hook_runtime_scaffold: `-`
- buy_funnel_sentinel: `/home/ubuntu/KORStockScan/data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-09-07.json`
- microstructure_reaction_context: `/home/ubuntu/KORStockScan/data/report/microstructure_reaction_context/microstructure_reaction_context_2026-09-07.json`
- generated_at: `2026-09-08T00:17:14+09:00`
- generation_id: `2026-09-07-77beaaeed6e7`
- generation_hash: `77beaaeed6e7c6886ce6022ec6fe13b5d4e5daccaeabfc66934478c7508ace7e`
- source_hash: `e1aa25fde5c1711ccd8311309e45d733f5c07d39c081709d184d918cce0cee72`
- producer_contract_version: `code_improvement_workorder_producer_v5`

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
- previous_generation_id: `2026-09-07-18b622a64a1e`
- previous_source_hash: `0980ca27f51b41092474751aaae34ffc230d819900d584cc4e55ae4671d1325e`
- new_order_ids: `[]`
- removed_order_ids: `[]`
- decision_changed_order_ids: `[]`

## Summary

- source_order_count: `37`
- scalping_source_order_count: `10`
- swing_source_order_count: `0`
- swing_entry_bottleneck_primary: `None`
- swing_entry_bottleneck_selected: `False`
- swing_lab_source_order_count: `0`
- swing_strategy_discovery_source_order_count: `0`
- swing_lifecycle_matrix_source_order_count: `0`
- swing_lifecycle_bucket_discovery_source_order_count: `0`
- pattern_lab_currentness_source_order_count: `0`
- pattern_lab_ai_review_source_order_count: `2`
- threshold_ev_source_order_count: `9`
- entry_hurdle_backtest_source_order_count: `0`
- microstructure_reaction_context_source_order_count: `2`
- lifecycle_submit_bucket_source_order_count: `0`
- lifecycle_holding_exit_bucket_source_order_count: `0`
- pipeline_event_verbosity_source_order_count: `0`
- observation_source_quality_source_order_count: `2`
- codebase_performance_source_order_count: `0`
- buy_funnel_sentinel_source_order_count: `6`
- entry_submit_drought_selected: `True`
- entry_submit_drought_handoff_missing: `False`
- panic_lifecycle_source_order_count: `1`
- selected_order_count: `15`
- non_selected_order_count: `22`
- operator_workload_summary: `{'implementation_required_count': 9, 'existing_family_attribution_count': 5, 'visibility_only_count': 1, 'other_selected_count': 0, 'root_cause_open_count': 13, 'selected_total_count': 15, 'category_count_reconciled': True, 'runtime_effect_true_count': 0}`
- source_decision_counts: `{'implement_now': 9, 'attach_existing_family': 25, 'design_family_candidate': 2, 'reject': 1}`
- selected_decision_counts: `{'implement_now': 9, 'attach_existing_family': 6}`
- selected_route_counts: `{'instrumentation_order': 7, 'source_quality_warning_producer_fix': 1, 'implement_now': 1, 'existing_family': 5, 'source_quality_raw_row_exclusion_revalidated_closed': 1}`
- selected_implement_now_route_count: `9`
- selected_runtime_effect_false_count: `15`
- selected_unimplemented_runtime_effect_false_count: `9`
- selected_unimplemented_route_counts: `{'instrumentation_order': 7, 'source_quality_warning_producer_fix': 1, 'implement_now': 1}`
- selected_terminal_non_implement_runtime_effect_false_count: `1`
- selected_terminal_non_implement_route_counts: `{'source_quality_raw_row_exclusion_revalidated_closed': 1}`
- selected_implement_now_existing_implementation_count: `0`
- selected_implement_now_existing_implementation_order_ids: `[]`
- selected_implement_now_new_runtime_effect_false_count: `9`
- selected_implement_now_new_runtime_effect_false_order_ids: `['order_entry_broker_receipt_contract_gap_review', 'order_entry_fill_quality_contract_gap_review', 'order_entry_post_submit_contract_gap_review', 'order_entry_source_taxonomy_contract_gap_review', 'order_entry_telegram_post_submit_contract_gap_review', 'order_microstructure_v3_evaluation_venue_missing_or_conflicting', 'order_microstructure_v3_required_holding_payload_missing', 'order_observation_source_quality_unknown_token_provenance_gap', 'order_pattern_lab_ai_review_ai_review_gap']`
- repeat_unresolved_escalation_count: `0`
- repeat_unresolved_escalated_order_ids: `[]`
- repeat_unresolved_structural_blocker_count: `0`
- repeat_unresolved_structural_blocker_order_ids: `[]`
- root_cause_closure_status_counts: `{'handoff_closed_root_cause_open': 3, 'needs_followup_workorder': 9, 'root_cause_closed': 1, 'source_quality_blocked': 1}`
- implementation_done_count: `0`
- artifact_regeneration_required_count: `0`
- source_quality_blocked_count: `1`
- handoff_closed_root_cause_open_count: `3`
- root_cause_closed_count: `1`
- needs_followup_workorder_count: `9`
- root_cause_followup_contract_required_count: `13`
- root_cause_followup_contract_complete_count: `13`
- root_cause_followup_contract_missing_order_ids: `[]`
- root_cause_open_top: `[{'order_id': 'order_conversion_lane_submit_drought_submit_drought_entry_ai_authority_revalidation', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': 'conversion_lane:submit_drought:ENTRY_AI_AUTHORITY_REVALIDATION:open', 'acceptance_test': 'entry-AI-authority blocks preserve canonical reason and exact payload lineage through consumer validation; repair leaves AI semantics and submit guards unchanged and does not depend on positive EV samples', 'next_repair_action': 'join exact AI authority reason, executable BBO, and target/adverse first-hit outcomes before proposing a bounded one-share probe'}, {'order_id': 'order_conversion_lane_submit_drought_submit_drought_latency_pre_submit', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': 'conversion_lane:submit_drought:LATENCY_PRE_SUBMIT:open', 'acceptance_test': 'the same attempt joins budget to latency block/pass and terminal; an earlier-stage retry is not recovery and DANGER safety is unchanged', 'next_repair_action': 'close_submit_drought_latency_pre_submit_quote_freshness'}, {'order_id': 'order_conversion_lane_submit_drought_submit_drought_upstream_gate', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': 'conversion_lane:submit_drought:UPSTREAM_GATE:open', 'acceptance_test': 'exact attempts preserve canonical upstream terminal reasons and retry boundaries; raw/cache/consumer counts reconcile without unknown loss; repair does not require economic replay or grant runtime authority', 'next_repair_action': 'join upstream action/reason cohorts to executable BBO and first-hit outcomes; AI semantic tuning remains separately owned'}, {'order_id': 'order_entry_broker_receipt_contract_gap_review', 'status': 'needs_followup_workorder', 'source_report_type': 'buy_funnel_sentinel', 'threshold_family': 'entry_submit_drought_attribution', 'implementation_status': 'pending_exact_post_submit_verification', 'root_cause_signal': 'buy_funnel_sentinel:unknown_gap:open', 'acceptance_test': 'PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py', 'next_repair_action': 'collect new evidence for buy_funnel_sentinel:unknown_gap:open and re-run the owning verifier'}, {'order_id': 'order_entry_fill_quality_contract_gap_review', 'status': 'needs_followup_workorder', 'source_report_type': 'buy_funnel_sentinel', 'threshold_family': 'entry_submit_drought_attribution', 'implementation_status': 'pending_exact_post_submit_verification', 'root_cause_signal': 'buy_funnel_sentinel:unknown_gap:open', 'acceptance_test': 'PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py', 'next_repair_action': 'collect new evidence for buy_funnel_sentinel:unknown_gap:open and re-run the owning verifier'}, {'order_id': 'order_entry_post_submit_contract_gap_review', 'status': 'needs_followup_workorder', 'source_report_type': 'buy_funnel_sentinel', 'threshold_family': 'entry_submit_drought_attribution', 'implementation_status': 'pending_exact_post_submit_verification', 'root_cause_signal': 'buy_funnel_sentinel:unknown_gap:open', 'acceptance_test': 'PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py', 'next_repair_action': 'collect new evidence for buy_funnel_sentinel:unknown_gap:open and re-run the owning verifier'}, {'order_id': 'order_entry_source_taxonomy_contract_gap_review', 'status': 'needs_followup_workorder', 'source_report_type': 'buy_funnel_sentinel', 'threshold_family': 'entry_submit_drought_attribution', 'implementation_status': 'pending_exact_source_taxonomy_verification', 'root_cause_signal': 'buy_funnel_sentinel:unknown_gap:open', 'acceptance_test': 'PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py', 'next_repair_action': 'collect new evidence for buy_funnel_sentinel:unknown_gap:open and re-run the owning verifier'}, {'order_id': 'order_entry_telegram_post_submit_contract_gap_review', 'status': 'needs_followup_workorder', 'source_report_type': 'buy_funnel_sentinel', 'threshold_family': 'entry_submit_drought_attribution', 'implementation_status': 'pending_exact_post_submit_verification', 'root_cause_signal': 'buy_funnel_sentinel:unknown_gap:open', 'acceptance_test': 'PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py', 'next_repair_action': 'collect new evidence for buy_funnel_sentinel:unknown_gap:open and re-run the owning verifier'}, {'order_id': 'order_microstructure_v3_evaluation_venue_missing_or_conflicting', 'status': 'needs_followup_workorder', 'source_report_type': 'microstructure_reaction_context', 'threshold_family': 'microstructure_reaction_context', 'implementation_status': None, 'root_cause_signal': 'microstructure_reaction_context:source_quality_contract_gap:open', 'acceptance_test': 'PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_microstructure_reaction_context_report.py src/tests/test_market_data_enrichment.py src/tests/test_pipeline_event_logger.py src/tests/test_build_code_improvement_workorder.py', 'next_repair_action': 'collect new evidence for microstructure_reaction_context:source_quality_contract_gap:open and re-run the owning verifier'}, {'order_id': 'order_microstructure_v3_required_holding_payload_missing', 'status': 'needs_followup_workorder', 'source_report_type': 'microstructure_reaction_context', 'threshold_family': 'microstructure_reaction_context', 'implementation_status': None, 'root_cause_signal': 'microstructure_reaction_context:source_quality_contract_gap:open', 'acceptance_test': 'PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_microstructure_reaction_context_report.py src/tests/test_market_data_enrichment.py src/tests/test_pipeline_event_logger.py src/tests/test_build_code_improvement_workorder.py', 'next_repair_action': 'collect new evidence for microstructure_reaction_context:source_quality_contract_gap:open and re-run the owning verifier'}]`
- selected_terminal_non_implement_longstanding_count: `1`
- selected_terminal_non_implement_longstanding_order_ids: `['order_observation_source_quality_raw_row_exclusion_producer_gap']`
- selected_longstanding_non_implement_disposition_counts: `{'review_required': 1}`
- selected_longstanding_non_implement_action_required_order_ids: `[]`
- non_selected_decision_counts: `{'attach_existing_family': 19, 'design_family_candidate': 2, 'reject': 1}`
- non_selected_longstanding_non_implement_disposition_counts: `{'implemented_with_provenance': 15, 'review_required': 2}`
- non_selected_longstanding_non_implement_action_required_order_ids: `[]`
- gemini_fresh: `False`
- claude_fresh: `True`
- swing_lifecycle_audit_available: `False`
- swing_pattern_lab_automation_available: `False`
- swing_pattern_lab_fresh: `None`
- pattern_lab_currentness_status: `pass`
- pattern_lab_currentness_fail_count: `0`
- pattern_lab_ai_review_status: `warning`
- pattern_lab_ai_review_workorder_count: `2`
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

### 1. `order_entry_broker_receipt_contract_gap_review`

- title: Entry broker receipt contract gap review
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `buy_funnel_sentinel`
- lifecycle_stage: `entry_submit`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
- mapped_family: `entry_submit_drought_attribution`
- threshold_family: `entry_submit_drought_attribution`
- improvement_type: `-`
- confidence: `-`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `True`
- data_quality_effect: `True`
- tuning_axis_effect: `True`
- expected_ev_effect: none_direct_source_quality_only
- evidence: `scope_key=NXT|NXT_AFTERMARKET`, `ai_confirmed_unique=56`, `budget_pass_unique=67`, `latency_pass_unique=10`, `submitted_unique=2`, `submitted_to_ai_pct=3.6`, `submitted_to_budget_pct=3.0`, `blocker:blocked_strength_momentum:insufficient_history=160`, `blocker:blocked_strength_momentum:below_window_buy_value=123`, `blocker:blocked_overbought:-=57`, `upstream:blocked_strength_momentum:insufficient_history=160`, `upstream:blocked_strength_momentum:below_window_buy_value=123`, `upstream:blocked_overbought:-=57`, `latency:latency_block:latency_state_danger=53`, `weak_contract_gap=broker_receipt_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/scalping/main_lifecycle_paired.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `pending_exact_post_submit_verification`
- root_cause_closure_status: `needs_followup_workorder`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "code_improvement_workorder", "gap_confirmation": "not_established_by_submit_count", "gap_type": "broker_receipt_contract_gap", "implementation_type": "post_submit_provenance_join_gap", "runtime_effect": false, "sample_status": "submitted_sample_requires_exact_join_verification", "source_report_type": "buy_funnel_sentinel", "submitted_unique": 2, "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "ECONOMIC_PARTICIPATION", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 2. `order_entry_fill_quality_contract_gap_review`

- title: Entry fill quality contract gap review
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `buy_funnel_sentinel`
- lifecycle_stage: `entry_submit`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
- mapped_family: `entry_submit_drought_attribution`
- threshold_family: `entry_submit_drought_attribution`
- improvement_type: `-`
- confidence: `-`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `True`
- data_quality_effect: `True`
- tuning_axis_effect: `True`
- expected_ev_effect: none_direct_source_quality_only
- evidence: `scope_key=NXT|NXT_AFTERMARKET`, `ai_confirmed_unique=56`, `budget_pass_unique=67`, `latency_pass_unique=10`, `submitted_unique=2`, `submitted_to_ai_pct=3.6`, `submitted_to_budget_pct=3.0`, `blocker:blocked_strength_momentum:insufficient_history=160`, `blocker:blocked_strength_momentum:below_window_buy_value=123`, `blocker:blocked_overbought:-=57`, `upstream:blocked_strength_momentum:insufficient_history=160`, `upstream:blocked_strength_momentum:below_window_buy_value=123`, `upstream:blocked_overbought:-=57`, `latency:latency_block:latency_state_danger=53`, `weak_contract_gap=fill_quality_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/scalping/main_lifecycle_paired.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `pending_exact_post_submit_verification`
- root_cause_closure_status: `needs_followup_workorder`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "code_improvement_workorder", "gap_confirmation": "not_established_by_submit_count", "gap_type": "fill_quality_contract_gap", "implementation_type": "post_submit_provenance_join_gap", "runtime_effect": false, "sample_status": "submitted_sample_requires_exact_join_verification", "source_report_type": "buy_funnel_sentinel", "submitted_unique": 2, "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "ECONOMIC_PARTICIPATION", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 3. `order_entry_post_submit_contract_gap_review`

- title: Entry post-submit contract gap review
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `buy_funnel_sentinel`
- lifecycle_stage: `entry_submit`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
- mapped_family: `entry_submit_drought_attribution`
- threshold_family: `entry_submit_drought_attribution`
- improvement_type: `-`
- confidence: `-`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `True`
- data_quality_effect: `True`
- tuning_axis_effect: `True`
- expected_ev_effect: none_direct_source_quality_only
- evidence: `scope_key=NXT|NXT_AFTERMARKET`, `ai_confirmed_unique=56`, `budget_pass_unique=67`, `latency_pass_unique=10`, `submitted_unique=2`, `submitted_to_ai_pct=3.6`, `submitted_to_budget_pct=3.0`, `blocker:blocked_strength_momentum:insufficient_history=160`, `blocker:blocked_strength_momentum:below_window_buy_value=123`, `blocker:blocked_overbought:-=57`, `upstream:blocked_strength_momentum:insufficient_history=160`, `upstream:blocked_strength_momentum:below_window_buy_value=123`, `upstream:blocked_overbought:-=57`, `latency:latency_block:latency_state_danger=53`, `weak_contract_gap=post_submit_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/scalping/main_lifecycle_paired.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `pending_exact_post_submit_verification`
- root_cause_closure_status: `needs_followup_workorder`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "code_improvement_workorder", "gap_confirmation": "not_established_by_submit_count", "gap_type": "post_submit_contract_gap", "implementation_type": "post_submit_provenance_join_gap", "runtime_effect": false, "sample_status": "submitted_sample_requires_exact_join_verification", "source_report_type": "buy_funnel_sentinel", "submitted_unique": 2, "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "ECONOMIC_PARTICIPATION", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 4. `order_entry_source_taxonomy_contract_gap_review`

- title: Entry source taxonomy contract gap review
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `buy_funnel_sentinel`
- lifecycle_stage: `entry_submit`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
- mapped_family: `entry_submit_drought_attribution`
- threshold_family: `entry_submit_drought_attribution`
- improvement_type: `-`
- confidence: `-`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `True`
- data_quality_effect: `True`
- tuning_axis_effect: `True`
- expected_ev_effect: none_direct_source_quality_only
- evidence: `scope_key=NXT|NXT_AFTERMARKET`, `ai_confirmed_unique=56`, `budget_pass_unique=67`, `latency_pass_unique=10`, `submitted_unique=2`, `submitted_to_ai_pct=3.6`, `submitted_to_budget_pct=3.0`, `blocker:blocked_strength_momentum:insufficient_history=160`, `blocker:blocked_strength_momentum:below_window_buy_value=123`, `blocker:blocked_overbought:-=57`, `upstream:blocked_strength_momentum:insufficient_history=160`, `upstream:blocked_strength_momentum:below_window_buy_value=123`, `upstream:blocked_overbought:-=57`, `latency:latency_block:latency_state_danger=53`, `weak_contract_gap=source_taxonomy_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`, `taxonomy_leakage_labels=[]`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/scalping/main_lifecycle_paired.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `pending_exact_source_taxonomy_verification`
- root_cause_closure_status: `needs_followup_workorder`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "code_improvement_workorder", "gap_confirmation": "not_established_by_submit_count", "gap_type": "source_taxonomy_contract_gap", "implementation_type": "source_taxonomy_provenance_gap", "runtime_effect": false, "sample_status": "submitted_sample_requires_exact_taxonomy_verification", "source_report_type": "buy_funnel_sentinel", "submitted_unique": 2, "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "ECONOMIC_PARTICIPATION", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 5. `order_entry_telegram_post_submit_contract_gap_review`

- title: Entry Telegram post-submit contract gap review
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `buy_funnel_sentinel`
- lifecycle_stage: `entry_submit`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
- mapped_family: `entry_submit_drought_attribution`
- threshold_family: `entry_submit_drought_attribution`
- improvement_type: `-`
- confidence: `-`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `True`
- data_quality_effect: `True`
- tuning_axis_effect: `True`
- expected_ev_effect: none_direct_source_quality_only
- evidence: `scope_key=NXT|NXT_AFTERMARKET`, `ai_confirmed_unique=56`, `budget_pass_unique=67`, `latency_pass_unique=10`, `submitted_unique=2`, `submitted_to_ai_pct=3.6`, `submitted_to_budget_pct=3.0`, `blocker:blocked_strength_momentum:insufficient_history=160`, `blocker:blocked_strength_momentum:below_window_buy_value=123`, `blocker:blocked_overbought:-=57`, `upstream:blocked_strength_momentum:insufficient_history=160`, `upstream:blocked_strength_momentum:below_window_buy_value=123`, `upstream:blocked_overbought:-=57`, `latency:latency_block:latency_state_danger=53`, `weak_contract_gap=telegram_post_submit_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/scalping/main_lifecycle_paired.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `pending_exact_post_submit_verification`
- root_cause_closure_status: `needs_followup_workorder`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "code_improvement_workorder", "gap_confirmation": "not_established_by_submit_count", "gap_type": "telegram_post_submit_contract_gap", "implementation_type": "post_submit_provenance_join_gap", "runtime_effect": false, "sample_status": "submitted_sample_requires_exact_join_verification", "source_report_type": "buy_funnel_sentinel", "submitted_unique": 2, "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "ECONOMIC_PARTICIPATION", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 6. `order_observation_source_quality_unknown_token_provenance_gap`

- title: Observation source-quality unknown-token provenance gap
- decision: `implement_now`
- decision_reason: unknown-token source-quality warnings are not tuning hard blocks, but they must be traced to producer provenance or replaced with explicit not_available/insufficient_sample labels
- source_report_type: `observation_source_quality_audit`
- lifecycle_stage: `source_quality_gate`
- target_subsystem: `runtime_instrumentation`
- route: `source_quality_warning_producer_fix`
- mapped_family: `observation_source_quality_audit`
- threshold_family: `observation_source_quality_audit`
- improvement_type: `source_quality_unknown_token_provenance_gap`
- confidence: `audit`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: none_direct_source_quality_attribution_only
- evidence: `status=warning`, `event_count=329378`, `warning_stage_count=0`, `warning_stages=`, `high_volume_no_source_field_stage_count=0`, `unknown_token_stage_count=2`, `review_warning_count=2`, `decision_authority=source_quality_only`, `runtime_effect=false`, `unknown_token_policy=warning_only_not_tuning_hard_block`, `required_action=producer_provenance_fix_or_explicit_reviewed_not_available_label`, `forbidden_uses=ignore_unknown_token_warning/silent_tuning_promotion_without_review`, `unknown:stage=stat_action_decision_snapshot event_count=1529 fields=score_prior_band:104:0.068`, `unknown:stage=avg_down_route_arbitration_observed event_count=3 fields=runtime_previous_min_buy_pressure:3:1.0,holding_pipeline_stable_block_signature:3:1.0`, `top_unknown_fields=score_prior_band,runtime_previous_min_buy_pressure,holding_pipeline_stable_block_signature`
- parity_contract: -
- next_postclose_metric: observation_source_quality_audit.warning_stage_count and high_volume_no_source_field_stage_count
- files_likely_touched: `src/engine/observation_source_quality_audit.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_sim_overnight.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_observation_source_quality_audit.py src/tests/test_build_code_improvement_workorder.py`
- implementation_status: `-`
- root_cause_closure_status: `needs_followup_workorder`
- implementation_provenance: `{"current_raw_contains_pre_fix_rows": false, "fixed_unknown_fields": ["broker_receipt_status", "effective_venue", "entry_adm_bucket_token", "entry_adm_cache_token", "entry_adm_price_resolution_bucket", "entry_order_flow_status", "entry_recheck_excluded_reason", "entry_score_excluded_reason", "entry_score_source", "fill_quality", "holding_exit_matrix_decision_alignment", "lifecycle_bucket_bucket_id", "lifecycle_bucket_entry_bucket_id", "lifecycle_bucket_entry_bucket_key", "market_session_bucket", "opening_rotation_no_pullback_continuation_effective_venue", "overbought_guard_reason", "pre_submit_liquidity_value", "pre_submit_overbought_reason", "scanner_promotion_reanchor_effective_venue", "scanner_stale_backoff_canonical_effective_venue", "score_prior_band", "score_prior_confidence", "sell_order_exchange_resolution_reason", "sim_pre_submit_overbought_reason", "soft_stop_dynamic_grace_score_prior_band", "swing_micro_ws_quote_stale", "tier_reason", "venue"], "producer_fix_status": "open_unknown_field_producer_fix_required"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: After implementation, rerun observation_source_quality_audit and code improvement workorder; unknown_token_stage_count should fall or remaining unknowns must carry explicit reviewed provenance.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 7. `order_microstructure_v3_evaluation_venue_missing_or_conflicting`

- title: Microstructure diagnostic contract: evaluation_venue_missing_or_conflicting
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `microstructure_reaction_context`
- lifecycle_stage: `entry_source_quality`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
- mapped_family: `microstructure_reaction_context`
- threshold_family: `microstructure_reaction_context`
- improvement_type: `source_quality_contract_gap`
- confidence: `-`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Correct existing AI input diagnostics without creating a runtime family.
- evidence: `cause=evaluation_venue_missing_or_conflicting`, `unique_affected_count=99`, `feature_version=microstructure_reaction_context_v2`, `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/scalping/microstructure_reaction_context.py`, `src/engine/scalping/market_data_enrichment.py`, `src/utils/pipeline_event_logger.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_microstructure_reaction_context_report.py src/tests/test_market_data_enrichment.py src/tests/test_pipeline_event_logger.py src/tests/test_build_code_improvement_workorder.py`, `regenerated microstructure_reaction_context keeps runtime_effect=false and allowed_runtime_apply=false`, `postclose code_improvement_workorder includes or explicitly closes this source-only order`
- implementation_status: `-`
- root_cause_closure_status: `needs_followup_workorder`
- implementation_provenance: `{"actual_order_submitted": false, "allowed_runtime_apply": false, "broker_order_forbidden": true, "implementation_type": "microstructure_source_quality_workorder_handoff", "requires_separate_runtime_apply_candidate": false, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 8. `order_microstructure_v3_required_holding_payload_missing`

- title: Microstructure diagnostic contract: required_holding_payload_missing
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `microstructure_reaction_context`
- lifecycle_stage: `entry_source_quality`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
- mapped_family: `microstructure_reaction_context`
- threshold_family: `microstructure_reaction_context`
- improvement_type: `source_quality_contract_gap`
- confidence: `-`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Correct existing AI input diagnostics without creating a runtime family.
- evidence: `cause=required_holding_payload_missing`, `unique_affected_count=324`, `feature_version=microstructure_reaction_context_v2`, `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/scalping/microstructure_reaction_context.py`, `src/engine/scalping/market_data_enrichment.py`, `src/utils/pipeline_event_logger.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_microstructure_reaction_context_report.py src/tests/test_market_data_enrichment.py src/tests/test_pipeline_event_logger.py src/tests/test_build_code_improvement_workorder.py`, `regenerated microstructure_reaction_context keeps runtime_effect=false and allowed_runtime_apply=false`, `postclose code_improvement_workorder includes or explicitly closes this source-only order`
- implementation_status: `-`
- root_cause_closure_status: `needs_followup_workorder`
- implementation_provenance: `{"actual_order_submitted": false, "allowed_runtime_apply": false, "broker_order_forbidden": true, "implementation_type": "microstructure_source_quality_workorder_handoff", "requires_separate_runtime_apply_candidate": false, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 9. `order_pattern_lab_ai_review_ai_review_gap`

- title: Pattern Lab AI review follow-up: ai_review_gap
- decision: `implement_now`
- decision_reason: pattern lab audit/review/observability order is report/source-quality instrumentation only and must remain runtime_effect=false
- source_report_type: `pattern_lab_ai_review`
- lifecycle_stage: `pattern_lab_ai_review`
- target_subsystem: `pattern_lab`
- route: `implement_now`
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
- evidence: `review_id=ai_review_gap`, `domain=scalping`, `final_state=source_quality_gap`, `final_decision=block_runtime_use`, `auditor_pass=False`, `explicit_gap_type=source_quality_gap`, `source_paths=['/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-09-07.json', '/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-09-07.json', '/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-07.json']`
- parity_contract: -
- next_postclose_metric: pattern_lab_ai_review.ai_review_gap
- files_likely_touched: `src/engine/pattern_lab_ai_review.py`, `src/engine/pattern_lab_currentness_audit.py`, `analysis/gemini_scalping_pattern_lab`, `analysis/claude_scalping_pattern_lab`, `analysis/deepseek_swing_pattern_lab`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_ai_review.py src/tests/test_pattern_lab_currentness_audit.py`
- implementation_status: `-`
- root_cause_closure_status: `needs_followup_workorder`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: After implementation, rerun pattern labs, currentness audit, workorder, EV, and propagation audit.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 10. `order_entry_submit_drought_auto_resolution`

- title: Entry submit drought automatic resolution handoff
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_gap_open; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `buy_funnel_sentinel`
- lifecycle_stage: `entry_submit`
- target_subsystem: `runtime_instrumentation`
- route: `existing_family`
- mapped_family: `entry_submit_drought_attribution`
- threshold_family: `entry_submit_drought_attribution`
- improvement_type: `-`
- confidence: `-`
- priority: `0`
- runtime_effect: `False`
- strategy_effect: `True`
- data_quality_effect: `True`
- tuning_axis_effect: `True`
- expected_ev_effect: restore submitted coverage before evaluating EV edge
- evidence: `scope_key=NXT|NXT_AFTERMARKET`, `ai_confirmed_unique=56`, `budget_pass_unique=67`, `latency_pass_unique=10`, `submitted_unique=2`, `submitted_to_ai_pct=3.6`, `submitted_to_budget_pct=3.0`, `blocker:blocked_strength_momentum:insufficient_history=160`, `blocker:blocked_strength_momentum:below_window_buy_value=123`, `blocker:blocked_overbought:-=57`, `upstream:blocked_strength_momentum:insufficient_history=160`, `upstream:blocked_strength_momentum:below_window_buy_value=123`, `upstream:blocked_overbought:-=57`, `latency:latency_block:latency_state_danger=53`
- parity_contract: -
- next_postclose_metric: SUBMIT_DROUGHT_CRITICAL must produce a selected implement_now workorder and the next postclose Sentinel/runtime summary must show submit blocker attribution.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/threshold_cycle_ev_report.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py`
- implementation_status: `implemented_source_quality_gap_open`
- root_cause_closure_status: `source_quality_blocked`
- implementation_provenance: `{"allowed_runtime_apply": false, "artifact_regeneration_required": false, "broker_order_submit_allowed": false, "core_handoff_axes": ["UPSTREAM_GATE", "LATENCY_PRE_SUBMIT", "ENTRY_AI_AUTHORITY_REVALIDATION", "PRICE_REVALIDATION", "BROKER_RECEIPT"], "exact_attempt_contract": {"allowed_runtime_apply": false, "attempt_count": 119, "attempt_ledger": [{"attempt_key": "id:40475:cycle:1", "last_event_at": "2026-09-07T17:32:59.492268", "last_stage": "blocked_liquidity", "producer_attempt_id": "SCANPROM-382900-1788765285499", "record_id": "40475", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:14:52.228031", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_liquidity"}, {"attempt_key": "id:40475:cycle:2", "last_event_at": "2026-09-07T19:03:04.849588", "last_stage": "blocked_liquidity", "producer_attempt_id": "SCANPROM-382900-1788769926045", "record_id": "40475", "stages": ["ai_confirmed"], "started_at": "2026-09-07T17:33:02.648184", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_liquidity"}, {"attempt_key": "id:40475:cycle:3", "last_event_at": "2026-09-07T19:03:07.829972", "last_stage": "blocked_ai_score", "producer_attempt_id": "SCANPROM-382900-1788775288740", "record_id": "40475", "stages": ["ai_confirmed"], "started_at": "2026-09-07T19:03:07.821746", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_ai_score"}, {"attempt_key": "id:40485:cycle:1", "last_event_at": "2026-09-07T16:23:51.939184", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40485", "stages": ["budget_pass"], "started_at": "2026-09-07T16:23:51.919524", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40485:cycle:2", "last_event_at": "2026-09-07T16:23:54.451677", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40485", "stages": ["budget_pass"], "started_at": "2026-09-07T16:23:54.432679", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40486:cycle:1", "last_event_at": "2026-09-07T19:12:22.851976", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-271940-1788767543088", "record_id": "40486", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:21:05.116845", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40487:cycle:1", "last_event_at": "2026-09-07T16:13:57.903388", "last_stage": "blocked_ai_score", "producer_attempt_id": "SCANPROM-437730-1788765159189", "record_id": "40487", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:10:49.272155", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_ai_score"}, {"attempt_key": "id:40490:cycle:1", "last_event_at": "2026-09-07T17:40:31.187167", "last_stage": "budget_pass", "producer_attempt_id": "", "record_id": "40490", "stages": ["budget_pass"], "started_at": "2026-09-07T16:37:21.574271", "state": "pending", "terminal_axis": "", "terminal_stage": ""}, {"attempt_key": "id:40499:cycle:1", "last_event_at": "2026-09-07T16:15:39.348456", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-131970-1788764655944", "record_id": "40499", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:05:31.339640", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40499:cycle:2", "last_event_at": "2026-09-07T16:42:08.430768", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-131970-1788765285499", "record_id": "40499", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:15:42.186729", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40499:cycle:3", "last_event_at": "2026-09-07T17:05:38.367334", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-131970-1788766891311", "record_id": "40499", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:42:11.814540", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40499:cycle:4", "last_event_at": "2026-09-07T17:47:01.948881", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-131970-1788768240345", "record_id": "40499", "stages": ["ai_confirmed"], "started_at": "2026-09-07T17:05:42.943336", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40499:cycle:5", "last_event_at": "2026-09-07T18:28:43.355304", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-131970-1788770625665", "record_id": "40499", "stages": ["ai_confirmed"], "started_at": "2026-09-07T17:47:05.099170", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40499:cycle:6", "last_event_at": "2026-09-07T19:19:47.927644", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-131970-1788773003459", "record_id": "40499", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:28:45.453690", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40500:cycle:1", "last_event_at": "2026-09-07T18:27:41.387683", "last_stage": "blocked_liquidity", "producer_attempt_id": "SCANPROM-031980-1788765159189", "record_id": "40500", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:12:44.534190", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_liquidity"}, {"attempt_key": "id:40500:cycle:2", "last_event_at": "2026-09-07T18:55:02.646441", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-031980-1788773239991", "record_id": "40500", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:27:45.403604", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40501:cycle:1", "last_event_at": "2026-09-07T17:10:01.689304", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "", "record_id": "40501", "stages": [], "started_at": "2026-09-07T17:10:01.689304", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40505:cycle:1", "last_event_at": "2026-09-07T16:58:28.589380", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-000660-1788767678832", "record_id": "40505", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:00:21.253246", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40505:cycle:2", "last_event_at": "2026-09-07T17:02:07.514217", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-000660-1788767824852", "record_id": "40505", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:58:31.739462", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40505:cycle:3", "last_event_at": "2026-09-07T18:49:27.678045", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-000660-1788769686566", "record_id": "40505", "stages": ["ai_confirmed"], "started_at": "2026-09-07T17:28:17.348771", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40505:cycle:4", "last_event_at": "2026-09-07T18:52:34.174270", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-000660-1788774564366", "record_id": "40505", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:49:31.047291", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40505:cycle:5", "last_event_at": "2026-09-07T19:17:45.740709", "last_stage": "blocked_ai_score", "producer_attempt_id": "SCANPROM-000660-1788774684527", "record_id": "40505", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:52:37.147084", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_ai_score"}, {"attempt_key": "id:40508:cycle:1", "last_event_at": "2026-09-07T17:08:33.965994", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40508", "stages": ["budget_pass"], "started_at": "2026-09-07T17:08:33.954414", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40513:cycle:1", "last_event_at": "2026-09-07T18:59:47.120972", "last_stage": "blocked_ai_score", "producer_attempt_id": "", "record_id": "40513", "stages": [], "started_at": "2026-09-07T16:00:24.631264", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_ai_score"}, {"attempt_key": "id:40518:cycle:1", "last_event_at": "2026-09-07T16:10:49.249232", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40518", "stages": ["budget_pass"], "started_at": "2026-09-07T16:10:49.239163", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40518:cycle:2", "last_event_at": "2026-09-07T16:11:52.080854", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40518", "stages": ["budget_pass"], "started_at": "2026-09-07T16:11:52.062462", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40518:cycle:3", "last_event_at": "2026-09-07T16:13:13.219916", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40518", "stages": ["budget_pass"], "started_at": "2026-09-07T16:13:13.194598", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40518:cycle:4", "last_event_at": "2026-09-07T17:31:20.887481", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40518", "stages": ["budget_pass"], "started_at": "2026-09-07T17:31:20.882229", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40518:cycle:5", "last_event_at": "2026-09-07T17:31:59.133547", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40518", "stages": ["budget_pass"], "started_at": "2026-09-07T17:31:23.295985", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40518:cycle:6", "last_event_at": "2026-09-07T17:32:59.405139", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40518", "stages": ["budget_pass"], "started_at": "2026-09-07T17:32:59.384356", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40518:cycle:7", "last_event_at": "2026-09-07T17:49:40.536171", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40518", "stages": ["budget_pass"], "started_at": "2026-09-07T17:48:33.080271", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40518:cycle:8", "last_event_at": "2026-09-07T18:42:25.297955", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40518", "stages": ["budget_pass"], "started_at": "2026-09-07T18:42:25.050381", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40518:cycle:9", "last_event_at": "2026-09-07T18:42:28.784171", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40518", "stages": ["budget_pass"], "started_at": "2026-09-07T18:42:28.742002", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40518:cycle:10", "last_event_at": "2026-09-07T18:43:34.448107", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40518", "stages": ["budget_pass"], "started_at": "2026-09-07T18:43:34.375210", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40522:cycle:1", "last_event_at": "2026-09-07T19:07:46.339774", "last_stage": "blocked_overbought", "producer_attempt_id": "", "record_id": "40522", "stages": [], "started_at": "2026-09-07T16:14:22.064110", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_overbought"}, {"attempt_key": "id:40535:cycle:1", "last_event_at": "2026-09-07T18:10:22.927054", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40535", "stages": ["budget_pass"], "started_at": "2026-09-07T18:10:22.899523", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40535:cycle:2", "last_event_at": "2026-09-07T18:37:23.998996", "last_stage": "budget_pass", "producer_attempt_id": "", "record_id": "40535", "stages": ["budget_pass"], "started_at": "2026-09-07T18:37:23.998996", "state": "pending", "terminal_axis": "", "terminal_stage": ""}, {"attempt_key": "id:40555:cycle:1", "last_event_at": "2026-09-07T18:58:14.124258", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "", "record_id": "40555", "stages": [], "started_at": "2026-09-07T16:06:31.767808", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40558:cycle:1", "last_event_at": "2026-09-07T18:00:05.567939", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-000150-1788764417259", "record_id": "40558", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:00:48.023220", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40558:cycle:2", "last_event_at": "2026-09-07T18:55:53.233318", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-000150-1788771562510", "record_id": "40558", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:00:39.400328", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40558:cycle:3", "last_event_at": "2026-09-07T19:06:27.537612", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-000150-1788774924094", "record_id": "40558", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:55:54.133918", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40612:cycle:1", "last_event_at": "2026-09-07T16:08:41.757490", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40612", "stages": ["budget_pass"], "started_at": "2026-09-07T16:08:41.637775", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40612:cycle:2", "last_event_at": "2026-09-07T16:09:43.239900", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40612", "stages": ["budget_pass"], "started_at": "2026-09-07T16:09:43.234324", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40612:cycle:3", "last_event_at": "2026-09-07T16:10:45.341251", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40612", "stages": ["budget_pass"], "started_at": "2026-09-07T16:10:45.316717", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40612:cycle:4", "last_event_at": "2026-09-07T17:27:26.514227", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40612", "stages": ["budget_pass"], "started_at": "2026-09-07T17:27:22.150772", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40612:cycle:5", "last_event_at": "2026-09-07T17:28:43.917206", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40612", "stages": ["budget_pass"], "started_at": "2026-09-07T17:28:28.207774", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40612:cycle:6", "last_event_at": "2026-09-07T17:48:50.642552", "last_stage": "pre_submit_entry_ai_authority_guard_block", "producer_attempt_id": "SCANPROM-083650-1788770862225", "record_id": "40612", "stages": ["budget_pass", "latency_pass", "ai_confirmed"], "started_at": "2026-09-07T17:48:45.507947", "state": "blocked", "terminal_axis": "ENTRY_AI_AUTHORITY_REVALIDATION", "terminal_stage": "pre_submit_entry_ai_authority_guard_block"}, {"attempt_key": "id:40612:cycle:7", "last_event_at": "2026-09-07T17:49:28.312547", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40612", "stages": ["budget_pass", "latency_pass"], "started_at": "2026-09-07T17:48:54.277647", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40612:cycle:8", "last_event_at": "2026-09-07T18:34:32.427874", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40612", "stages": ["budget_pass"], "started_at": "2026-09-07T18:34:25.550098", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40612:cycle:9", "last_event_at": "2026-09-07T18:35:51.073655", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40612", "stages": ["budget_pass"], "started_at": "2026-09-07T18:35:51.017257", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40614:cycle:1", "last_event_at": "2026-09-07T19:19:18.420053", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "", "record_id": "40614", "stages": [], "started_at": "2026-09-07T16:51:14.762749", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40624:cycle:1", "last_event_at": "2026-09-07T16:27:15.458366", "last_stage": "blocked_vpw", "producer_attempt_id": "SCANPROM-052690-1788764417259", "record_id": "40624", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:00:24.607074", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_vpw"}, {"attempt_key": "id:40624:cycle:2", "last_event_at": "2026-09-07T16:52:51.890194", "last_stage": "blocked_vpw", "producer_attempt_id": "SCANPROM-052690-1788766014569", "record_id": "40624", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:27:18.458932", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_vpw"}, {"attempt_key": "id:40624:cycle:3", "last_event_at": "2026-09-07T17:02:00.426499", "last_stage": "blocked_vpw", "producer_attempt_id": "SCANPROM-052690-1788767543088", "record_id": "40624", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:52:55.147651", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_vpw"}, {"attempt_key": "id:40624:cycle:4", "last_event_at": "2026-09-07T17:30:56.278643", "last_stage": "blocked_vpw", "producer_attempt_id": "SCANPROM-052690-1788768002394", "record_id": "40624", "stages": ["ai_confirmed"], "started_at": "2026-09-07T17:02:06.425839", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_vpw"}, {"attempt_key": "id:40624:cycle:5", "last_event_at": "2026-09-07T17:55:52.593278", "last_stage": "blocked_vpw", "producer_attempt_id": "SCANPROM-052690-1788769805189", "record_id": "40624", "stages": ["ai_confirmed"], "started_at": "2026-09-07T17:30:59.862510", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_vpw"}, {"attempt_key": "id:40624:cycle:6", "last_event_at": "2026-09-07T18:21:32.849348", "last_stage": "blocked_vpw", "producer_attempt_id": "SCANPROM-052690-1788771329119", "record_id": "40624", "stages": ["ai_confirmed"], "started_at": "2026-09-07T17:55:55.917996", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_vpw"}, {"attempt_key": "id:40624:cycle:7", "last_event_at": "2026-09-07T18:48:09.557360", "last_stage": "blocked_vpw", "producer_attempt_id": "SCANPROM-052690-1788772883151", "record_id": "40624", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:21:35.858481", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_vpw"}, {"attempt_key": "id:40624:cycle:8", "last_event_at": "2026-09-07T19:01:55.207863", "last_stage": "blocked_vpw", "producer_attempt_id": "SCANPROM-052690-1788774450515", "record_id": "40624", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:48:11.265229", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_vpw"}, {"attempt_key": "id:40624:cycle:9", "last_event_at": "2026-09-07T19:02:02.157337", "last_stage": "blocked_ai_score", "producer_attempt_id": "SCANPROM-052690-1788775288740", "record_id": "40624", "stages": ["ai_confirmed"], "started_at": "2026-09-07T19:01:59.206260", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_ai_score"}, {"attempt_key": "id:40650:cycle:1", "last_event_at": "2026-09-07T16:26:47.376487", "last_stage": "latency_pass", "producer_attempt_id": "SCANPROM-190510-1788765766513", "record_id": "40650", "stages": ["ai_confirmed", "budget_pass", "latency_pass"], "started_at": "2026-09-07T16:04:19.775860", "state": "pending", "terminal_axis": "", "terminal_stage": ""}, {"attempt_key": "id:40650:cycle:2", "last_event_at": "2026-09-07T16:50:51.860060", "last_stage": "blocked_liquidity", "producer_attempt_id": "SCANPROM-190510-1788765891559", "record_id": "40650", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:26:50.414548", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_liquidity"}, {"attempt_key": "id:40650:cycle:3", "last_event_at": "2026-09-07T17:34:30.214268", "last_stage": "blocked_liquidity", "producer_attempt_id": "SCANPROM-190510-1788767423126", "record_id": "40650", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:50:54.837200", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_liquidity"}, {"attempt_key": "id:40650:cycle:4", "last_event_at": "2026-09-07T18:01:25.093056", "last_stage": "blocked_liquidity", "producer_attempt_id": "SCANPROM-190510-1788770045737", "record_id": "40650", "stages": ["ai_confirmed"], "started_at": "2026-09-07T17:34:31.216378", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_liquidity"}, {"attempt_key": "id:40650:cycle:5", "last_event_at": "2026-09-07T18:18:04.135569", "last_stage": "blocked_liquidity", "producer_attempt_id": "SCANPROM-190510-1788771675494", "record_id": "40650", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:01:28.725210", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_liquidity"}, {"attempt_key": "id:40650:cycle:6", "last_event_at": "2026-09-07T18:50:24.038160", "last_stage": "blocked_liquidity", "producer_attempt_id": "SCANPROM-190510-1788772644934", "record_id": "40650", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:18:09.004445", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_liquidity"}, {"attempt_key": "id:40650:cycle:7", "last_event_at": "2026-09-07T19:16:20.956915", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-190510-1788774564366", "record_id": "40650", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:50:27.827892", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40777:cycle:1", "last_event_at": "2026-09-07T16:33:28.728692", "last_stage": "budget_pass", "producer_attempt_id": "", "record_id": "40777", "stages": ["budget_pass"], "started_at": "2026-09-07T16:33:28.728692", "state": "pending", "terminal_axis": "", "terminal_stage": ""}, {"attempt_key": "id:40784:cycle:1", "last_event_at": "2026-09-07T17:43:55.526225", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-298040-1788769086363", "record_id": "40784", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:10:50.528926", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40784:cycle:2", "last_event_at": "2026-09-07T18:09:48.972033", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-298040-1788770625665", "record_id": "40784", "stages": ["ai_confirmed"], "started_at": "2026-09-07T17:43:58.942786", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40784:cycle:3", "last_event_at": "2026-09-07T18:39:59.828945", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-298040-1788772151519", "record_id": "40784", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:09:52.575546", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40784:cycle:4", "last_event_at": "2026-09-07T19:07:09.124098", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-298040-1788773959534", "record_id": "40784", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:40:03.688061", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40795:cycle:1", "last_event_at": "2026-09-07T17:59:44.417692", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40795", "stages": ["budget_pass"], "started_at": "2026-09-07T17:58:40.049624", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40851:cycle:1", "last_event_at": "2026-09-07T16:22:10.877880", "last_stage": "blocked_liquidity", "producer_attempt_id": "SCANPROM-053610-1788765285499", "record_id": "40851", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:16:22.937726", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_liquidity"}, {"attempt_key": "id:40851:cycle:2", "last_event_at": "2026-09-07T18:35:37.055058", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-053610-1788765644484", "record_id": "40851", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:22:12.378552", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40854:cycle:1", "last_event_at": "2026-09-07T17:37:51.219380", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T17:37:51.200266", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:2", "last_event_at": "2026-09-07T17:37:53.413247", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T17:37:53.360022", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:3", "last_event_at": "2026-09-07T17:52:19.188059", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T17:52:19.164068", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:4", "last_event_at": "2026-09-07T17:53:33.168958", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T17:53:32.917913", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:5", "last_event_at": "2026-09-07T17:54:34.912872", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T17:54:34.887681", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:6", "last_event_at": "2026-09-07T17:55:43.629484", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T17:55:43.598712", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:7", "last_event_at": "2026-09-07T18:01:20.860754", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:01:20.438984", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:8", "last_event_at": "2026-09-07T18:02:20.825453", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:02:20.787554", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:9", "last_event_at": "2026-09-07T18:02:23.236888", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:02:23.218066", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:10", "last_event_at": "2026-09-07T18:03:38.611835", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:03:38.575944", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:11", "last_event_at": "2026-09-07T18:29:04.250521", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:29:04.229264", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:12", "last_event_at": "2026-09-07T18:30:08.913721", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:30:08.844689", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:13", "last_event_at": "2026-09-07T18:31:10.980777", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:31:10.779059", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:14", "last_event_at": "2026-09-07T18:32:19.527261", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:32:19.463788", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:15", "last_event_at": "2026-09-07T18:33:25.634975", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:33:25.510460", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:16", "last_event_at": "2026-09-07T18:34:24.736330", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:34:24.704971", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:17", "last_event_at": "2026-09-07T18:35:25.859075", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:35:25.851804", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:18", "last_event_at": "2026-09-07T18:36:27.236229", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:36:27.211533", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:19", "last_event_at": "2026-09-07T18:36:29.332549", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:36:29.317089", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:20", "last_event_at": "2026-09-07T19:02:26.104235", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T19:02:26.093240", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:21", "last_event_at": "2026-09-07T19:03:44.095194", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T19:03:44.084023", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:22", "last_event_at": "2026-09-07T19:04:47.317973", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T19:04:47.297598", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:23", "last_event_at": "2026-09-07T19:05:50.342632", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T19:05:50.292732", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40880:cycle:1", "last_event_at": "2026-09-07T19:18:30.913234", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40880", "stages": ["budget_pass"], "started_at": "2026-09-07T19:18:30.905360", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40885:cycle:1", "last_event_at": "2026-09-07T17:43:38.697327", "last_stage": "blocked_liquidity", "producer_attempt_id": "SCANPROM-126340-1788767543088", "record_id": "40885", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:12:46.464184", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_liquidity"}, {"attempt_key": "id:40885:cycle:2", "last_event_at": "2026-09-07T19:10:34.528807", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-126340-1788770510624", "record_id": "40885", "stages": ["ai_confirmed"], "started_at": "2026-09-07T17:43:42.862669", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40889:cycle:1", "last_event_at": "2026-09-07T16:06:25.746674", "last_stage": "pre_submit_entry_ai_authority_guard_block", "producer_attempt_id": "SCANPROM-066970-1788764417259", "record_id": "40889", "stages": ["budget_pass", "latency_pass", "ai_confirmed"], "started_at": "2026-09-07T16:05:25.457862", "state": "blocked", "terminal_axis": "ENTRY_AI_AUTHORITY_REVALIDATION", "terminal_stage": "pre_submit_entry_ai_authority_guard_block"}, {"attempt_key": "id:40889:cycle:2", "last_event_at": "2026-09-07T16:15:29.185418", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40889", "stages": ["budget_pass"], "started_at": "2026-09-07T16:15:29.160703", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40894:cycle:1", "last_event_at": "2026-09-07T16:05:54.573396", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40894", "stages": ["budget_pass"], "started_at": "2026-09-07T16:05:54.388742", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40894:cycle:2", "last_event_at": "2026-09-07T16:39:46.000036", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40894", "stages": ["budget_pass"], "started_at": "2026-09-07T16:39:26.843699", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40894:cycle:3", "last_event_at": "2026-09-07T16:39:47.786565", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40894", "stages": ["budget_pass"], "started_at": "2026-09-07T16:39:47.765102", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40894:cycle:4", "last_event_at": "2026-09-07T18:21:39.823712", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40894", "stages": ["budget_pass"], "started_at": "2026-09-07T18:21:39.750465", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40904:cycle:1", "last_event_at": "2026-09-07T16:01:49.813918", "last_stage": "pre_submit_entry_ai_authority_guard_block", "producer_attempt_id": "SCANPROM-304100-1788764417259", "record_id": "40904", "stages": ["budget_pass", "latency_pass", "ai_confirmed"], "started_at": "2026-09-07T16:01:43.899718", "state": "blocked", "terminal_axis": "ENTRY_AI_AUTHORITY_REVALIDATION", "terminal_stage": "pre_submit_entry_ai_authority_guard_block"}, {"attempt_key": "id:40904:cycle:2", "last_event_at": "2026-09-07T16:32:01.690061", "last_stage": "order_bundle_submitted", "producer_attempt_id": "SCANPROM-304100-1788766259214", "record_id": "40904", "stages": ["budget_pass", "latency_pass", "ai_confirmed", "order_bundle_submitted"], "started_at": "2026-09-07T16:31:45.720639", "state": "submitted", "terminal_axis": "", "terminal_stage": ""}, {"attempt_key": "id:40907:cycle:1", "last_event_at": "2026-09-07T18:43:28.144658", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-402340-1788772644934", "record_id": "40907", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:04:30.448961", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40907:cycle:2", "last_event_at": "2026-09-07T19:17:52.877643", "last_stage": "blocked_ai_score", "producer_attempt_id": "SCANPROM-402340-1788774204084", "record_id": "40907", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:43:32.099685", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_ai_score"}, {"attempt_key": "id:40916:cycle:1", "last_event_at": "2026-09-07T19:04:34.086452", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-131290-1788765159189", "record_id": "40916", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:13:25.299713", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40924:cycle:1", "last_event_at": "2026-09-07T16:34:25.856540", "last_stage": "budget_pass", "producer_attempt_id": "", "record_id": "40924", "stages": ["budget_pass"], "started_at": "2026-09-07T16:34:25.856540", "state": "pending", "terminal_axis": "", "terminal_stage": ""}, {"attempt_key": "id:40942:cycle:1", "last_event_at": "2026-09-07T16:35:37.270044", "last_stage": "order_bundle_submitted", "producer_attempt_id": "SCANPROM-249420-1788766498453", "record_id": "40942", "stages": ["budget_pass", "latency_pass", "ai_confirmed", "order_bundle_submitted"], "started_at": "2026-09-07T16:35:08.240985", "state": "submitted", "terminal_axis": "", "terminal_stage": ""}, {"attempt_key": "id:40958:cycle:1", "last_event_at": "2026-09-07T18:35:33.936334", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40958", "stages": ["budget_pass"], "started_at": "2026-09-07T18:35:33.884590", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40958:cycle:2", "last_event_at": "2026-09-07T18:37:08.359375", "last_stage": "budget_pass", "producer_attempt_id": "", "record_id": "40958", "stages": ["budget_pass"], "started_at": "2026-09-07T18:35:38.327017", "state": "pending", "terminal_axis": "", "terminal_stage": ""}, {"attempt_key": "id:40987:cycle:1", "last_event_at": "2026-09-07T17:59:30.166587", "last_stage": "pre_submit_entry_ai_authority_guard_block", "producer_attempt_id": "SCANPROM-249420-1788771441948", "record_id": "40987", "stages": ["budget_pass", "latency_pass", "ai_confirmed"], "started_at": "2026-09-07T17:59:22.788289", "state": "blocked", "terminal_axis": "ENTRY_AI_AUTHORITY_REVALIDATION", "terminal_stage": "pre_submit_entry_ai_authority_guard_block"}, {"attempt_key": "id:40987:cycle:2", "last_event_at": "2026-09-07T18:03:32.406968", "last_stage": "pre_submit_entry_ai_authority_guard_block", "producer_attempt_id": "SCANPROM-249420-1788771795726", "record_id": "40987", "stages": ["budget_pass", "latency_pass", "ai_confirmed"], "started_at": "2026-09-07T18:03:24.481605", "state": "blocked", "terminal_axis": "ENTRY_AI_AUTHORITY_REVALIDATION", "terminal_stage": "pre_submit_entry_ai_authority_guard_block"}, {"attempt_key": "id:40987:cycle:3", "last_event_at": "2026-09-07T18:34:19.714873", "last_stage": "pre_submit_entry_ai_authority_guard_block", "producer_attempt_id": "SCANPROM-249420-1788773598141", "record_id": "40987", "stages": ["budget_pass", "latency_pass", "ai_confirmed"], "started_at": "2026-09-07T18:34:13.320269", "state": "blocked", "terminal_axis": "ENTRY_AI_AUTHORITY_REVALIDATION", "terminal_stage": "pre_submit_entry_ai_authority_guard_block"}], "attempt_partition_policy": "record_explicit_attempt_or_ordered_retry_v2", "axis_event_counts": {"BROKER_RECEIPT": 0, "ENTRY_AI_AUTHORITY_REVALIDATION": 8, "LATENCY_PRE_SUBMIT": 53, "PRICE_REVALIDATION": 0, "UPSTREAM_GATE": 509}, "axis_exact_attempt_event_counts": {"BROKER_RECEIPT": 0, "ENTRY_AI_AUTHORITY_REVALIDATION": 8, "LATENCY_PRE_SUBMIT": 53, "PRICE_REVALIDATION": 0, "UPSTREAM_GATE": 53}, "axis_later_progress_attempt_counts": {"BROKER_RECEIPT": 0, "ENTRY_AI_AUTHORITY_REVALIDATION": 0, "LATENCY_PRE_SUBMIT": 0, "PRICE_REVALIDATION": 0, "UPSTREAM_GATE": 1}, "axis_missing_exact_attempt_key_events": {"BROKER_RECEIPT": 0, "ENTRY_AI_AUTHORITY_REVALIDATION": 0, "LATENCY_PRE_SUBMIT": 0, "PRICE_REVALIDATION": 0, "UPSTREAM_GATE": 0}, "axis_stage_order_violation_events": {"BROKER_RECEIPT": 0, "ENTRY_AI_AUTHORITY_REVALIDATION": 1, "LATENCY_PRE_SUBMIT": 0, "PRICE_REVALIDATION": 0, "UPSTREAM_GATE": 0}, "axis_superseded_attempt_counts": {"BROKER_RECEIPT": 0, "ENTRY_AI_AUTHORITY_REVALIDATION": 1, "LATENCY_PRE_SUBMIT": 0, "PRICE_REVALIDATION": 0, "UPSTREAM_GATE": 0}, "axis_terminal_causal_attempt_counts": {"BROKER_RECEIPT": 0, "ENTRY_AI_AUTHORITY_REVALIDATION": 6, "LATENCY_PRE_SUBMIT": 53, "PRICE_REVALIDATION": 0, "UPSTREAM_GATE": 52}, "core_handoff_axes": ["UPSTREAM_GATE", "LATENCY_PRE_SUBMIT", "ENTRY_AI_AUTHORITY_REVALIDATION", "PRICE_REVALIDATION", "BROKER_RECEIPT"], "decision_authority": "submit_drought_attribution_only", "denominator_exact_attempt_counts": {"ai_confirmed": 56, "budget_pass": 67, "latency_pass": 10, "order_bundle_submitted": 2}, "denominator_missing_exact_attempt_key_events": {"ai_confirmed": 0, "budget_pass": 0, "latency_pass": 0, "order_bundle_submitted": 0}, "denominator_stage_order_violation_events": {"ai_confirmed": 0, "budget_pass": 0, "latency_pass": 0, "order_bundle_submitted": 0}, "denominator_stages": ["ai_confirmed", "budget_pass", "latency_pass", "order_bundle_submitted"], "exclusion_applied": true, "forbidden_uses": ["standalone_runtime_apply", "broker_order_submit", "guard_relaxation", "provider_change", "bot_restart", "standalone_ev_approval"], "identity_fallback_allowed": false, "identity_field": "record_id", "metric_role": "funnel_count", "missing_exact_attempt_key_event_count": 0, "pending_attempt_count": 6, "primary_decision_metric": "terminal_causal_attempt_count", "retry_attempt_count": 83, "runtime_effect": false, "sample_floor": "one_valid_record_attempt_per_causal_axis", "schema_version": 2, "source_quality_gate": "exact_record_identity_ordered_stages_excluded_invalid_rows", "stage_order_violation_event_count": 1, "status": "source_quality_gap_excluded", "submitted_attempt_count": 2, "summary_terminal_identity_gap_events": 0, "terminal_causal_attempt_count": 111, "terminal_causal_partition_disjoint": true, "unclassified_terminal_attempt_count": 0, "window_policy": "same_day_venue_session_ordered_attempt_cycles"}, "exact_attempt_contract_invalid": false, "exact_attempt_source_quality_open": true, "forbidden_uses": ["intraday_threshold_mutation", "broker_guard_bypass", "provider_route_change", "bot_restart_trigger", "telegram_pre_submit_buy_alert"], "implementation_type": "source_only_report_provenance_handoff", "ldm_quote_freshness_attribution_present": true, "observation_axis_status": {"BROKER_RECEIPT": "no_current_signal", "BUDGET_PASS_COLLAPSE": "observation_only", "ECONOMIC_PARTICIPATION": "observed", "ENTRY_AI_AUTHORITY_REVALIDATION": "observed", "LATENCY_PRE_SUBMIT": "observed", "PRICE_REVALIDATION": "no_current_signal", "SIM_REAL_AUTHORITY": "observed", "SOURCE_TAXONOMY_LEAKAGE": "no_current_signal", "UPSTREAM_GATE": "observed"}, "observation_breakdown": {"allowed_runtime_apply": false, "axes": {"BROKER_RECEIPT": {"evidence": {"broker_submit_failure_unique": 0, "latency_pass_unique": 10, "order_bundle_submitted_unique": 2, "submitted_to_budget_unique_pct": 3.0}, "exact_attempt_event_count": 0, "exact_join_valid": false, "identity_fallback_allowed": false, "identity_field": "record_id", "later_progress_attempt_count": 0, "missing_exact_attempt_key_events": 0, "next_repair_action": "join post-submit broker receipt and fill provenance only when a broker submission or explicit submit failure exists", "observed_count": 0, "source_quality_status": "pass", "stage_order_violation_events": 0, "status": "no_current_signal"}, "BUDGET_PASS_COLLAPSE": {"evidence": {"ai_confirmed_unique": 56, "budget_ai_lineage": {"ai_attempt_result_unavailable_parent_not_expected_event_count": 3, "ai_trace_count": 68, "ai_trace_source_stage_counts": {"ai_confirmed": 56, "early_accel_strong_bundle_recheck_failed": 12}, "allowed_runtime_apply": false, "budget_or_block_event_count": 90, "exact_parent_trace_unresolved_event_count": 0, "lineage_contract_coverage_pct": 100.0, "lineage_contract_event_count": 90, "lineage_contract_missing_event_count": 0, "lineage_exact_trusted_count": 0, "lineage_field_present_count": 0, "lineage_join_coverage_denominator": "events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_attempt_result_unavailable", "lineage_join_coverage_pct": 0.0, "lineage_join_eligible_event_count": 0, "lineage_joined_event_count": 0, "lineage_untrusted_or_stale_event_count": 0, "lineage_untrusted_or_stale_reason_counts": {}, "linked_budget_block_trace_count": 0, "linked_budget_pass_trace_count": 0, "linked_stage_counts": {}, "parent_attempt_without_trusted_result_event_count": 3, "parent_trace_missing_when_expected_event_count": 0, "parent_trace_missing_without_attempt_event_count": 0, "pipeline_stage_order_contract": "latest_watching_ai_to_budget_precheck_to_final_authority_revalidation", "pre_ai_parent_not_expected_event_count": 87, "raw_ai_budget_census_is_causal": false, "raw_event_lineage_join_coverage_pct": 0.0, "runtime_effect": false, "status": "no_trusted_ai_result_parent_not_expected"}, "budget_pass_unique": 67, "budget_to_ai_unique_pct": 119.6, "legacy_stage_census_gap": 0, "legacy_stage_census_gap_is_causal": false}, "next_repair_action": "treat pre-AI budget events as expected no-parent observations; repair only missing lineage contracts or stale/untrusted post-AI parents, and keep causal EV attribution limited to exact joins", "observed_count": 0, "status": "observation_only"}, "ECONOMIC_PARTICIPATION": {"evidence": {"allowed_runtime_apply": false, "bundle_count": 2, "by_venue": {"NXT": {"bundle_count": 2, "full_submitted_bundle_count": 0, "partial_residual_bundle_count": 0, "probe_only_bundle_count": 2, "requested_notional_krw": 554170, "requested_qty": 35, "submitted_notional_krw": 31690, "submitted_notional_to_requested_notional_pct": 5.7, "submitted_qty": 2, "submitted_qty_to_requested_qty_pct": 5.7}}, "decision_authority": "submit_drought_attribution_only", "forbidden_uses": ["broker_order_submit", "intraday_threshold_mutation", "quantity_cap_release", "live_auto_promotion", "bot_restart_trigger"], "full_submitted_bundle_count": 0, "metric_role": "funnel_count", "observed_bundle_count": 2, "partial_residual_bundle_count": 0, "primary_decision_metric": "submitted_notional_to_requested_notional_pct", "probe_only_bundle_count": 2, "requested_notional_krw": 554170, "requested_qty": 35, "rows": [{"attempt_key": "attempt:SCANPROM-304100-1788766259214", "bundle_state": "probe_only", "effective_venue": "NXT", "probe_submission_source": "split_probe_lifecycle", "requested_notional_krw": 276250, "requested_qty": 17, "residual_submitted_qty": 0, "source_quality_valid": true, "stock_code": "304100", "submitted_notional_krw": 16250, "submitted_qty": 1, "venue_source_quality": "pass"}, {"attempt_key": "attempt:SCANPROM-249420-1788766498453", "bundle_state": "probe_only", "effective_venue": "NXT", "probe_submission_source": "split_probe_lifecycle", "requested_notional_krw": 277920, "requested_qty": 18, "residual_submitted_qty": 0, "source_quality_valid": true, "stock_code": "249420", "submitted_notional_krw": 15440, "submitted_qty": 1, "venue_source_quality": "pass"}], "runtime_effect": false, "sample_floor": "1_explicit_venue_split_probe_or_bounded_single_share_order_bundle", "source_quality_blocked_bundle_count": 0, "source_quality_gate": "explicit_conflict_free_venue_and_positive_requested_submitted_qty_price", "source_quality_valid_bundle_count": 2, "submitted_notional_krw": 31690, "submitted_notional_to_requested_notional_pct": 5.7, "submitted_qty": 2, "submitted_qty_to_requested_qty_pct": 5.7, "window_policy": "same_session_split_probe_or_bounded_single_share_lifecycle"}, "next_repair_action": "join venue-proven submitted probe receipts to fill and terminal outcomes; submission participation alone is not execution EV", "observed_count": 2, "status": "observed"}, "ENTRY_AI_AUTHORITY_REVALIDATION": {"evidence": {"entry_ai_authority_guard_events": 8, "entry_ai_authority_guard_top": [{"count": 6, "label": "pre_submit_entry_ai_authority_guard_block:fresh_ai_drop_real_buy_veto"}, {"count": 2, "label": "pre_submit_entry_ai_authority_guard_block:entry_ai_result_stale_or_untrusted"}], "entry_ai_authority_guard_unique": 6, "latency_pass_unique": 10, "order_bundle_submitted_unique": 2}, "exact_attempt_event_count": 8, "exact_join_valid": true, "identity_fallback_allowed": false, "identity_field": "record_id", "later_progress_attempt_count": 0, "missing_exact_attempt_key_events": 0, "next_repair_action": "join exact AI authority reason, executable BBO, and target/adverse first-hit outcomes before proposing a bounded one-share probe", "observed_count": 6, "source_quality_status": "source_quality_gap_excluded", "stage_order_violation_events": 1, "status": "observed"}, "LATENCY_PRE_SUBMIT": {"evidence": {"budget_pass_missing_exact_attempt_key_events": 0, "latency_blocked_budget_events": 53, "latency_blocked_budget_unique": 11, "latency_blocker_top": [{"count": 53, "label": "latency_block:latency_state_danger"}], "latency_danger_missing_exact_attempt_key_events": 0, "latency_root_cause_counts": {"quote_freshness_input_snapshot_noop": 8, "quote_stale": 13, "spread_microstructure_guard": 53, "spread_or_slippage_guard": 41}, "latency_state_danger_events": 53, "latency_state_danger_unique": 11, "latency_terminal_causal_unique": 53, "quote_freshness_attribution": {"decision_authority": "submit_drought_quote_freshness_attribution_only", "forbidden_uses": ["broker_order_submit", "adm_ldm_training_input", "general_threshold_ev_input", "live_auto_promotion"], "latency_pass_recovered_count": 5, "latency_pass_recovered_downstream_counts": {"entry_ai_authority_revalidation": 4, "order_bundle_submitted": 1}, "latency_pass_recovered_downstream_stage_counts": {"order_bundle_submitted": 1, "pre_submit_entry_ai_authority_guard_block": 4}, "order_bundle_submitted_after_refresh_count": 1, "post_restart_window_policy": "event_provenance_only", "refresh_applied_count": 15, "refresh_attempted_count": 15, "refresh_block_subreason_counts": {"ws_snapshot_refresh_failed_input_snapshot_fresh": 8}, "refresh_subreason_counts": {"ws_snapshot_refresh_failed_input_snapshot_fresh": 8}, "runtime_effect": false, "still_latency_blocked_after_refresh_count": 5}, "unknown_latency_reason_count": 0, "unknown_latency_workorder_required": false}, "exact_attempt_event_count": 53, "exact_join_valid": true, "identity_fallback_allowed": false, "identity_field": "record_id", "later_progress_attempt_count": 0, "missing_exact_attempt_key_events": 0, "next_repair_action": "close unknown latency labels or route quote freshness gaps to Sentinel attribution", "observed_count": 53, "source_quality_status": "pass", "stage_order_violation_events": 0, "status": "observed"}, "PRICE_REVALIDATION": {"evidence": {"latency_pass_unique": 10, "order_bundle_submitted_unique": 2, "price_guard_events": 0, "price_guard_top": [], "price_guard_unique": 0}, "exact_attempt_event_count": 0, "exact_join_valid": false, "identity_fallback_allowed": false, "identity_field": "record_id", "later_progress_attempt_count": 0, "missing_exact_attempt_key_events": 0, "next_repair_action": "join executable BBO and target/adverse first-hit outcomes to price revalidation blocks before proposing bounded exploration", "observed_count": 0, "source_quality_status": "pass", "stage_order_violation_events": 0, "status": "no_current_signal"}, "SIM_REAL_AUTHORITY": {"evidence": {"actual_order_submitted_authority": "not_granted_by_report", "broker_order_submit_allowed": false}, "next_repair_action": "keep attribution source-only until explicit runtime approval artifact exists", "observed_count": 1, "status": "observed"}, "SOURCE_TAXONOMY_LEAKAGE": {"evidence": {"blocker_top": [{"count": 160, "label": "blocked_strength_momentum:insufficient_history"}, {"count": 123, "label": "blocked_strength_momentum:below_window_buy_value"}, {"count": 57, "label": "blocked_overbought:-"}, {"count": 53, "label": "latency_block:latency_state_danger"}, {"count": 36, "label": "blocked_ai_score:ai_score_50_buy_hold_override"}, {"count": 34, "label": "blocked_vpw:-"}, {"count": 33, "label": "blocked_strength_momentum:below_strength_base"}, {"count": 20, "label": "blocked_liquidity:-"}, {"count": 11, "label": "first_ai_wait:-"}, {"count": 8, "label": "blocked_strength_momentum:below_buy_ratio"}], "taxonomy_leakage_labels": []}, "next_repair_action": "separate swing/source taxonomy from entry-submit blocker labels", "observed_count": 0, "status": "no_current_signal"}, "UPSTREAM_GATE": {"evidence": {"ai_action_event_counts": {"DROP": 28, "WAIT": 28}, "ai_action_unique_counts": {"DROP": 14, "WAIT": 14}, "ai_terminal_reason_top": [{"count": 22, "label": "ai_terminal:entry_policy_no_buy_score_prior"}, {"count": 11, "label": "ai_terminal:first_ai_wait_big_bite_not_confirmed"}], "budget_to_ai_unique_pct": 119.6, "upstream_blocker_top": [{"count": 160, "label": "blocked_strength_momentum:insufficient_history"}, {"count": 123, "label": "blocked_strength_momentum:below_window_buy_value"}, {"count": 57, "label": "blocked_overbought:-"}, {"count": 36, "label": "blocked_ai_score:ai_score_50_buy_hold_override"}, {"count": 34, "label": "blocked_vpw:-"}, {"count": 33, "label": "blocked_strength_momentum:below_strength_base"}, {"count": 20, "label": "blocked_liquidity:-"}, {"count": 11, "label": "first_ai_wait:-"}, {"count": 8, "label": "blocked_strength_momentum:below_buy_ratio"}, {"count": 5, "label": "blocked_ai_score:score_64.0"}]}, "exact_attempt_event_count": 53, "exact_join_valid": true, "identity_fallback_allowed": false, "identity_field": "record_id", "later_progress_attempt_count": 1, "missing_exact_attempt_key_events": 0, "next_repair_action": "join upstream action/reason cohorts to executable BBO and first-hit outcomes; AI semantic tuning remains separately owned", "observed_count": 52, "source_quality_status": "pass", "stage_order_violation_events": 0, "status": "observed"}}, "axis_order": ["UPSTREAM_GATE", "LATENCY_PRE_SUBMIT", "ENTRY_AI_AUTHORITY_REVALIDATION", "PRICE_REVALIDATION", "BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "ECONOMIC_PARTICIPATION", "SIM_REAL_AUTHORITY", "SOURCE_TAXONOMY_LEAKAGE"], "broker_order_submit_allowed": false, "causal_bottleneck_axes": ["UPSTREAM_GATE", "LATENCY_PRE_SUBMIT", "ENTRY_AI_AUTHORITY_REVALIDATION"], "core_handoff_axes": ["UPSTREAM_GATE", "LATENCY_PRE_SUBMIT", "ENTRY_AI_AUTHORITY_REVALIDATION", "PRICE_REVALIDATION", "BROKER_RECEIPT"], "decision_authority": "submit_drought_attribution_only", "exact_attempt_contract": {"allowed_runtime_apply": false, "attempt_count": 119, "attempt_ledger": [{"attempt_key": "id:40475:cycle:1", "last_event_at": "2026-09-07T17:32:59.492268", "last_stage": "blocked_liquidity", "producer_attempt_id": "SCANPROM-382900-1788765285499", "record_id": "40475", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:14:52.228031", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_liquidity"}, {"attempt_key": "id:40475:cycle:2", "last_event_at": "2026-09-07T19:03:04.849588", "last_stage": "blocked_liquidity", "producer_attempt_id": "SCANPROM-382900-1788769926045", "record_id": "40475", "stages": ["ai_confirmed"], "started_at": "2026-09-07T17:33:02.648184", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_liquidity"}, {"attempt_key": "id:40475:cycle:3", "last_event_at": "2026-09-07T19:03:07.829972", "last_stage": "blocked_ai_score", "producer_attempt_id": "SCANPROM-382900-1788775288740", "record_id": "40475", "stages": ["ai_confirmed"], "started_at": "2026-09-07T19:03:07.821746", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_ai_score"}, {"attempt_key": "id:40485:cycle:1", "last_event_at": "2026-09-07T16:23:51.939184", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40485", "stages": ["budget_pass"], "started_at": "2026-09-07T16:23:51.919524", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40485:cycle:2", "last_event_at": "2026-09-07T16:23:54.451677", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40485", "stages": ["budget_pass"], "started_at": "2026-09-07T16:23:54.432679", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40486:cycle:1", "last_event_at": "2026-09-07T19:12:22.851976", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-271940-1788767543088", "record_id": "40486", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:21:05.116845", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40487:cycle:1", "last_event_at": "2026-09-07T16:13:57.903388", "last_stage": "blocked_ai_score", "producer_attempt_id": "SCANPROM-437730-1788765159189", "record_id": "40487", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:10:49.272155", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_ai_score"}, {"attempt_key": "id:40490:cycle:1", "last_event_at": "2026-09-07T17:40:31.187167", "last_stage": "budget_pass", "producer_attempt_id": "", "record_id": "40490", "stages": ["budget_pass"], "started_at": "2026-09-07T16:37:21.574271", "state": "pending", "terminal_axis": "", "terminal_stage": ""}, {"attempt_key": "id:40499:cycle:1", "last_event_at": "2026-09-07T16:15:39.348456", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-131970-1788764655944", "record_id": "40499", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:05:31.339640", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40499:cycle:2", "last_event_at": "2026-09-07T16:42:08.430768", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-131970-1788765285499", "record_id": "40499", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:15:42.186729", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40499:cycle:3", "last_event_at": "2026-09-07T17:05:38.367334", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-131970-1788766891311", "record_id": "40499", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:42:11.814540", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40499:cycle:4", "last_event_at": "2026-09-07T17:47:01.948881", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-131970-1788768240345", "record_id": "40499", "stages": ["ai_confirmed"], "started_at": "2026-09-07T17:05:42.943336", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40499:cycle:5", "last_event_at": "2026-09-07T18:28:43.355304", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-131970-1788770625665", "record_id": "40499", "stages": ["ai_confirmed"], "started_at": "2026-09-07T17:47:05.099170", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40499:cycle:6", "last_event_at": "2026-09-07T19:19:47.927644", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-131970-1788773003459", "record_id": "40499", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:28:45.453690", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40500:cycle:1", "last_event_at": "2026-09-07T18:27:41.387683", "last_stage": "blocked_liquidity", "producer_attempt_id": "SCANPROM-031980-1788765159189", "record_id": "40500", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:12:44.534190", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_liquidity"}, {"attempt_key": "id:40500:cycle:2", "last_event_at": "2026-09-07T18:55:02.646441", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-031980-1788773239991", "record_id": "40500", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:27:45.403604", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40501:cycle:1", "last_event_at": "2026-09-07T17:10:01.689304", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "", "record_id": "40501", "stages": [], "started_at": "2026-09-07T17:10:01.689304", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40505:cycle:1", "last_event_at": "2026-09-07T16:58:28.589380", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-000660-1788767678832", "record_id": "40505", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:00:21.253246", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40505:cycle:2", "last_event_at": "2026-09-07T17:02:07.514217", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-000660-1788767824852", "record_id": "40505", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:58:31.739462", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40505:cycle:3", "last_event_at": "2026-09-07T18:49:27.678045", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-000660-1788769686566", "record_id": "40505", "stages": ["ai_confirmed"], "started_at": "2026-09-07T17:28:17.348771", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40505:cycle:4", "last_event_at": "2026-09-07T18:52:34.174270", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-000660-1788774564366", "record_id": "40505", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:49:31.047291", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40505:cycle:5", "last_event_at": "2026-09-07T19:17:45.740709", "last_stage": "blocked_ai_score", "producer_attempt_id": "SCANPROM-000660-1788774684527", "record_id": "40505", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:52:37.147084", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_ai_score"}, {"attempt_key": "id:40508:cycle:1", "last_event_at": "2026-09-07T17:08:33.965994", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40508", "stages": ["budget_pass"], "started_at": "2026-09-07T17:08:33.954414", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40513:cycle:1", "last_event_at": "2026-09-07T18:59:47.120972", "last_stage": "blocked_ai_score", "producer_attempt_id": "", "record_id": "40513", "stages": [], "started_at": "2026-09-07T16:00:24.631264", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_ai_score"}, {"attempt_key": "id:40518:cycle:1", "last_event_at": "2026-09-07T16:10:49.249232", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40518", "stages": ["budget_pass"], "started_at": "2026-09-07T16:10:49.239163", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40518:cycle:2", "last_event_at": "2026-09-07T16:11:52.080854", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40518", "stages": ["budget_pass"], "started_at": "2026-09-07T16:11:52.062462", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40518:cycle:3", "last_event_at": "2026-09-07T16:13:13.219916", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40518", "stages": ["budget_pass"], "started_at": "2026-09-07T16:13:13.194598", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40518:cycle:4", "last_event_at": "2026-09-07T17:31:20.887481", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40518", "stages": ["budget_pass"], "started_at": "2026-09-07T17:31:20.882229", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40518:cycle:5", "last_event_at": "2026-09-07T17:31:59.133547", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40518", "stages": ["budget_pass"], "started_at": "2026-09-07T17:31:23.295985", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40518:cycle:6", "last_event_at": "2026-09-07T17:32:59.405139", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40518", "stages": ["budget_pass"], "started_at": "2026-09-07T17:32:59.384356", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40518:cycle:7", "last_event_at": "2026-09-07T17:49:40.536171", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40518", "stages": ["budget_pass"], "started_at": "2026-09-07T17:48:33.080271", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40518:cycle:8", "last_event_at": "2026-09-07T18:42:25.297955", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40518", "stages": ["budget_pass"], "started_at": "2026-09-07T18:42:25.050381", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40518:cycle:9", "last_event_at": "2026-09-07T18:42:28.784171", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40518", "stages": ["budget_pass"], "started_at": "2026-09-07T18:42:28.742002", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40518:cycle:10", "last_event_at": "2026-09-07T18:43:34.448107", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40518", "stages": ["budget_pass"], "started_at": "2026-09-07T18:43:34.375210", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40522:cycle:1", "last_event_at": "2026-09-07T19:07:46.339774", "last_stage": "blocked_overbought", "producer_attempt_id": "", "record_id": "40522", "stages": [], "started_at": "2026-09-07T16:14:22.064110", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_overbought"}, {"attempt_key": "id:40535:cycle:1", "last_event_at": "2026-09-07T18:10:22.927054", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40535", "stages": ["budget_pass"], "started_at": "2026-09-07T18:10:22.899523", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40535:cycle:2", "last_event_at": "2026-09-07T18:37:23.998996", "last_stage": "budget_pass", "producer_attempt_id": "", "record_id": "40535", "stages": ["budget_pass"], "started_at": "2026-09-07T18:37:23.998996", "state": "pending", "terminal_axis": "", "terminal_stage": ""}, {"attempt_key": "id:40555:cycle:1", "last_event_at": "2026-09-07T18:58:14.124258", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "", "record_id": "40555", "stages": [], "started_at": "2026-09-07T16:06:31.767808", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40558:cycle:1", "last_event_at": "2026-09-07T18:00:05.567939", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-000150-1788764417259", "record_id": "40558", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:00:48.023220", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40558:cycle:2", "last_event_at": "2026-09-07T18:55:53.233318", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-000150-1788771562510", "record_id": "40558", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:00:39.400328", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40558:cycle:3", "last_event_at": "2026-09-07T19:06:27.537612", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-000150-1788774924094", "record_id": "40558", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:55:54.133918", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40612:cycle:1", "last_event_at": "2026-09-07T16:08:41.757490", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40612", "stages": ["budget_pass"], "started_at": "2026-09-07T16:08:41.637775", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40612:cycle:2", "last_event_at": "2026-09-07T16:09:43.239900", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40612", "stages": ["budget_pass"], "started_at": "2026-09-07T16:09:43.234324", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40612:cycle:3", "last_event_at": "2026-09-07T16:10:45.341251", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40612", "stages": ["budget_pass"], "started_at": "2026-09-07T16:10:45.316717", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40612:cycle:4", "last_event_at": "2026-09-07T17:27:26.514227", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40612", "stages": ["budget_pass"], "started_at": "2026-09-07T17:27:22.150772", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40612:cycle:5", "last_event_at": "2026-09-07T17:28:43.917206", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40612", "stages": ["budget_pass"], "started_at": "2026-09-07T17:28:28.207774", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40612:cycle:6", "last_event_at": "2026-09-07T17:48:50.642552", "last_stage": "pre_submit_entry_ai_authority_guard_block", "producer_attempt_id": "SCANPROM-083650-1788770862225", "record_id": "40612", "stages": ["budget_pass", "latency_pass", "ai_confirmed"], "started_at": "2026-09-07T17:48:45.507947", "state": "blocked", "terminal_axis": "ENTRY_AI_AUTHORITY_REVALIDATION", "terminal_stage": "pre_submit_entry_ai_authority_guard_block"}, {"attempt_key": "id:40612:cycle:7", "last_event_at": "2026-09-07T17:49:28.312547", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40612", "stages": ["budget_pass", "latency_pass"], "started_at": "2026-09-07T17:48:54.277647", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40612:cycle:8", "last_event_at": "2026-09-07T18:34:32.427874", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40612", "stages": ["budget_pass"], "started_at": "2026-09-07T18:34:25.550098", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40612:cycle:9", "last_event_at": "2026-09-07T18:35:51.073655", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40612", "stages": ["budget_pass"], "started_at": "2026-09-07T18:35:51.017257", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40614:cycle:1", "last_event_at": "2026-09-07T19:19:18.420053", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "", "record_id": "40614", "stages": [], "started_at": "2026-09-07T16:51:14.762749", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40624:cycle:1", "last_event_at": "2026-09-07T16:27:15.458366", "last_stage": "blocked_vpw", "producer_attempt_id": "SCANPROM-052690-1788764417259", "record_id": "40624", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:00:24.607074", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_vpw"}, {"attempt_key": "id:40624:cycle:2", "last_event_at": "2026-09-07T16:52:51.890194", "last_stage": "blocked_vpw", "producer_attempt_id": "SCANPROM-052690-1788766014569", "record_id": "40624", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:27:18.458932", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_vpw"}, {"attempt_key": "id:40624:cycle:3", "last_event_at": "2026-09-07T17:02:00.426499", "last_stage": "blocked_vpw", "producer_attempt_id": "SCANPROM-052690-1788767543088", "record_id": "40624", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:52:55.147651", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_vpw"}, {"attempt_key": "id:40624:cycle:4", "last_event_at": "2026-09-07T17:30:56.278643", "last_stage": "blocked_vpw", "producer_attempt_id": "SCANPROM-052690-1788768002394", "record_id": "40624", "stages": ["ai_confirmed"], "started_at": "2026-09-07T17:02:06.425839", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_vpw"}, {"attempt_key": "id:40624:cycle:5", "last_event_at": "2026-09-07T17:55:52.593278", "last_stage": "blocked_vpw", "producer_attempt_id": "SCANPROM-052690-1788769805189", "record_id": "40624", "stages": ["ai_confirmed"], "started_at": "2026-09-07T17:30:59.862510", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_vpw"}, {"attempt_key": "id:40624:cycle:6", "last_event_at": "2026-09-07T18:21:32.849348", "last_stage": "blocked_vpw", "producer_attempt_id": "SCANPROM-052690-1788771329119", "record_id": "40624", "stages": ["ai_confirmed"], "started_at": "2026-09-07T17:55:55.917996", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_vpw"}, {"attempt_key": "id:40624:cycle:7", "last_event_at": "2026-09-07T18:48:09.557360", "last_stage": "blocked_vpw", "producer_attempt_id": "SCANPROM-052690-1788772883151", "record_id": "40624", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:21:35.858481", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_vpw"}, {"attempt_key": "id:40624:cycle:8", "last_event_at": "2026-09-07T19:01:55.207863", "last_stage": "blocked_vpw", "producer_attempt_id": "SCANPROM-052690-1788774450515", "record_id": "40624", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:48:11.265229", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_vpw"}, {"attempt_key": "id:40624:cycle:9", "last_event_at": "2026-09-07T19:02:02.157337", "last_stage": "blocked_ai_score", "producer_attempt_id": "SCANPROM-052690-1788775288740", "record_id": "40624", "stages": ["ai_confirmed"], "started_at": "2026-09-07T19:01:59.206260", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_ai_score"}, {"attempt_key": "id:40650:cycle:1", "last_event_at": "2026-09-07T16:26:47.376487", "last_stage": "latency_pass", "producer_attempt_id": "SCANPROM-190510-1788765766513", "record_id": "40650", "stages": ["ai_confirmed", "budget_pass", "latency_pass"], "started_at": "2026-09-07T16:04:19.775860", "state": "pending", "terminal_axis": "", "terminal_stage": ""}, {"attempt_key": "id:40650:cycle:2", "last_event_at": "2026-09-07T16:50:51.860060", "last_stage": "blocked_liquidity", "producer_attempt_id": "SCANPROM-190510-1788765891559", "record_id": "40650", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:26:50.414548", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_liquidity"}, {"attempt_key": "id:40650:cycle:3", "last_event_at": "2026-09-07T17:34:30.214268", "last_stage": "blocked_liquidity", "producer_attempt_id": "SCANPROM-190510-1788767423126", "record_id": "40650", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:50:54.837200", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_liquidity"}, {"attempt_key": "id:40650:cycle:4", "last_event_at": "2026-09-07T18:01:25.093056", "last_stage": "blocked_liquidity", "producer_attempt_id": "SCANPROM-190510-1788770045737", "record_id": "40650", "stages": ["ai_confirmed"], "started_at": "2026-09-07T17:34:31.216378", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_liquidity"}, {"attempt_key": "id:40650:cycle:5", "last_event_at": "2026-09-07T18:18:04.135569", "last_stage": "blocked_liquidity", "producer_attempt_id": "SCANPROM-190510-1788771675494", "record_id": "40650", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:01:28.725210", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_liquidity"}, {"attempt_key": "id:40650:cycle:6", "last_event_at": "2026-09-07T18:50:24.038160", "last_stage": "blocked_liquidity", "producer_attempt_id": "SCANPROM-190510-1788772644934", "record_id": "40650", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:18:09.004445", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_liquidity"}, {"attempt_key": "id:40650:cycle:7", "last_event_at": "2026-09-07T19:16:20.956915", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-190510-1788774564366", "record_id": "40650", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:50:27.827892", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40777:cycle:1", "last_event_at": "2026-09-07T16:33:28.728692", "last_stage": "budget_pass", "producer_attempt_id": "", "record_id": "40777", "stages": ["budget_pass"], "started_at": "2026-09-07T16:33:28.728692", "state": "pending", "terminal_axis": "", "terminal_stage": ""}, {"attempt_key": "id:40784:cycle:1", "last_event_at": "2026-09-07T17:43:55.526225", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-298040-1788769086363", "record_id": "40784", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:10:50.528926", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40784:cycle:2", "last_event_at": "2026-09-07T18:09:48.972033", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-298040-1788770625665", "record_id": "40784", "stages": ["ai_confirmed"], "started_at": "2026-09-07T17:43:58.942786", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40784:cycle:3", "last_event_at": "2026-09-07T18:39:59.828945", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-298040-1788772151519", "record_id": "40784", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:09:52.575546", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40784:cycle:4", "last_event_at": "2026-09-07T19:07:09.124098", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-298040-1788773959534", "record_id": "40784", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:40:03.688061", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40795:cycle:1", "last_event_at": "2026-09-07T17:59:44.417692", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40795", "stages": ["budget_pass"], "started_at": "2026-09-07T17:58:40.049624", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40851:cycle:1", "last_event_at": "2026-09-07T16:22:10.877880", "last_stage": "blocked_liquidity", "producer_attempt_id": "SCANPROM-053610-1788765285499", "record_id": "40851", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:16:22.937726", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_liquidity"}, {"attempt_key": "id:40851:cycle:2", "last_event_at": "2026-09-07T18:35:37.055058", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-053610-1788765644484", "record_id": "40851", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:22:12.378552", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40854:cycle:1", "last_event_at": "2026-09-07T17:37:51.219380", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T17:37:51.200266", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:2", "last_event_at": "2026-09-07T17:37:53.413247", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T17:37:53.360022", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:3", "last_event_at": "2026-09-07T17:52:19.188059", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T17:52:19.164068", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:4", "last_event_at": "2026-09-07T17:53:33.168958", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T17:53:32.917913", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:5", "last_event_at": "2026-09-07T17:54:34.912872", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T17:54:34.887681", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:6", "last_event_at": "2026-09-07T17:55:43.629484", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T17:55:43.598712", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:7", "last_event_at": "2026-09-07T18:01:20.860754", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:01:20.438984", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:8", "last_event_at": "2026-09-07T18:02:20.825453", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:02:20.787554", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:9", "last_event_at": "2026-09-07T18:02:23.236888", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:02:23.218066", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:10", "last_event_at": "2026-09-07T18:03:38.611835", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:03:38.575944", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:11", "last_event_at": "2026-09-07T18:29:04.250521", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:29:04.229264", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:12", "last_event_at": "2026-09-07T18:30:08.913721", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:30:08.844689", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:13", "last_event_at": "2026-09-07T18:31:10.980777", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:31:10.779059", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:14", "last_event_at": "2026-09-07T18:32:19.527261", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:32:19.463788", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:15", "last_event_at": "2026-09-07T18:33:25.634975", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:33:25.510460", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:16", "last_event_at": "2026-09-07T18:34:24.736330", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:34:24.704971", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:17", "last_event_at": "2026-09-07T18:35:25.859075", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:35:25.851804", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:18", "last_event_at": "2026-09-07T18:36:27.236229", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:36:27.211533", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:19", "last_event_at": "2026-09-07T18:36:29.332549", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T18:36:29.317089", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:20", "last_event_at": "2026-09-07T19:02:26.104235", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T19:02:26.093240", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:21", "last_event_at": "2026-09-07T19:03:44.095194", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T19:03:44.084023", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:22", "last_event_at": "2026-09-07T19:04:47.317973", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T19:04:47.297598", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40854:cycle:23", "last_event_at": "2026-09-07T19:05:50.342632", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40854", "stages": ["budget_pass"], "started_at": "2026-09-07T19:05:50.292732", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40880:cycle:1", "last_event_at": "2026-09-07T19:18:30.913234", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40880", "stages": ["budget_pass"], "started_at": "2026-09-07T19:18:30.905360", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40885:cycle:1", "last_event_at": "2026-09-07T17:43:38.697327", "last_stage": "blocked_liquidity", "producer_attempt_id": "SCANPROM-126340-1788767543088", "record_id": "40885", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:12:46.464184", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_liquidity"}, {"attempt_key": "id:40885:cycle:2", "last_event_at": "2026-09-07T19:10:34.528807", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-126340-1788770510624", "record_id": "40885", "stages": ["ai_confirmed"], "started_at": "2026-09-07T17:43:42.862669", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40889:cycle:1", "last_event_at": "2026-09-07T16:06:25.746674", "last_stage": "pre_submit_entry_ai_authority_guard_block", "producer_attempt_id": "SCANPROM-066970-1788764417259", "record_id": "40889", "stages": ["budget_pass", "latency_pass", "ai_confirmed"], "started_at": "2026-09-07T16:05:25.457862", "state": "blocked", "terminal_axis": "ENTRY_AI_AUTHORITY_REVALIDATION", "terminal_stage": "pre_submit_entry_ai_authority_guard_block"}, {"attempt_key": "id:40889:cycle:2", "last_event_at": "2026-09-07T16:15:29.185418", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40889", "stages": ["budget_pass"], "started_at": "2026-09-07T16:15:29.160703", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40894:cycle:1", "last_event_at": "2026-09-07T16:05:54.573396", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40894", "stages": ["budget_pass"], "started_at": "2026-09-07T16:05:54.388742", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40894:cycle:2", "last_event_at": "2026-09-07T16:39:46.000036", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40894", "stages": ["budget_pass"], "started_at": "2026-09-07T16:39:26.843699", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40894:cycle:3", "last_event_at": "2026-09-07T16:39:47.786565", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40894", "stages": ["budget_pass"], "started_at": "2026-09-07T16:39:47.765102", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40894:cycle:4", "last_event_at": "2026-09-07T18:21:39.823712", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40894", "stages": ["budget_pass"], "started_at": "2026-09-07T18:21:39.750465", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40904:cycle:1", "last_event_at": "2026-09-07T16:01:49.813918", "last_stage": "pre_submit_entry_ai_authority_guard_block", "producer_attempt_id": "SCANPROM-304100-1788764417259", "record_id": "40904", "stages": ["budget_pass", "latency_pass", "ai_confirmed"], "started_at": "2026-09-07T16:01:43.899718", "state": "blocked", "terminal_axis": "ENTRY_AI_AUTHORITY_REVALIDATION", "terminal_stage": "pre_submit_entry_ai_authority_guard_block"}, {"attempt_key": "id:40904:cycle:2", "last_event_at": "2026-09-07T16:32:01.690061", "last_stage": "order_bundle_submitted", "producer_attempt_id": "SCANPROM-304100-1788766259214", "record_id": "40904", "stages": ["budget_pass", "latency_pass", "ai_confirmed", "order_bundle_submitted"], "started_at": "2026-09-07T16:31:45.720639", "state": "submitted", "terminal_axis": "", "terminal_stage": ""}, {"attempt_key": "id:40907:cycle:1", "last_event_at": "2026-09-07T18:43:28.144658", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-402340-1788772644934", "record_id": "40907", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:04:30.448961", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40907:cycle:2", "last_event_at": "2026-09-07T19:17:52.877643", "last_stage": "blocked_ai_score", "producer_attempt_id": "SCANPROM-402340-1788774204084", "record_id": "40907", "stages": ["ai_confirmed"], "started_at": "2026-09-07T18:43:32.099685", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_ai_score"}, {"attempt_key": "id:40916:cycle:1", "last_event_at": "2026-09-07T19:04:34.086452", "last_stage": "blocked_strength_momentum", "producer_attempt_id": "SCANPROM-131290-1788765159189", "record_id": "40916", "stages": ["ai_confirmed"], "started_at": "2026-09-07T16:13:25.299713", "state": "blocked", "terminal_axis": "UPSTREAM_GATE", "terminal_stage": "blocked_strength_momentum"}, {"attempt_key": "id:40924:cycle:1", "last_event_at": "2026-09-07T16:34:25.856540", "last_stage": "budget_pass", "producer_attempt_id": "", "record_id": "40924", "stages": ["budget_pass"], "started_at": "2026-09-07T16:34:25.856540", "state": "pending", "terminal_axis": "", "terminal_stage": ""}, {"attempt_key": "id:40942:cycle:1", "last_event_at": "2026-09-07T16:35:37.270044", "last_stage": "order_bundle_submitted", "producer_attempt_id": "SCANPROM-249420-1788766498453", "record_id": "40942", "stages": ["budget_pass", "latency_pass", "ai_confirmed", "order_bundle_submitted"], "started_at": "2026-09-07T16:35:08.240985", "state": "submitted", "terminal_axis": "", "terminal_stage": ""}, {"attempt_key": "id:40958:cycle:1", "last_event_at": "2026-09-07T18:35:33.936334", "last_stage": "latency_block", "producer_attempt_id": "", "record_id": "40958", "stages": ["budget_pass"], "started_at": "2026-09-07T18:35:33.884590", "state": "blocked", "terminal_axis": "LATENCY_PRE_SUBMIT", "terminal_stage": "latency_block"}, {"attempt_key": "id:40958:cycle:2", "last_event_at": "2026-09-07T18:37:08.359375", "last_stage": "budget_pass", "producer_attempt_id": "", "record_id": "40958", "stages": ["budget_pass"], "started_at": "2026-09-07T18:35:38.327017", "state": "pending", "terminal_axis": "", "terminal_stage": ""}, {"attempt_key": "id:40987:cycle:1", "last_event_at": "2026-09-07T17:59:30.166587", "last_stage": "pre_submit_entry_ai_authority_guard_block", "producer_attempt_id": "SCANPROM-249420-1788771441948", "record_id": "40987", "stages": ["budget_pass", "latency_pass", "ai_confirmed"], "started_at": "2026-09-07T17:59:22.788289", "state": "blocked", "terminal_axis": "ENTRY_AI_AUTHORITY_REVALIDATION", "terminal_stage": "pre_submit_entry_ai_authority_guard_block"}, {"attempt_key": "id:40987:cycle:2", "last_event_at": "2026-09-07T18:03:32.406968", "last_stage": "pre_submit_entry_ai_authority_guard_block", "producer_attempt_id": "SCANPROM-249420-1788771795726", "record_id": "40987", "stages": ["budget_pass", "latency_pass", "ai_confirmed"], "started_at": "2026-09-07T18:03:24.481605", "state": "blocked", "terminal_axis": "ENTRY_AI_AUTHORITY_REVALIDATION", "terminal_stage": "pre_submit_entry_ai_authority_guard_block"}, {"attempt_key": "id:40987:cycle:3", "last_event_at": "2026-09-07T18:34:19.714873", "last_stage": "pre_submit_entry_ai_authority_guard_block", "producer_attempt_id": "SCANPROM-249420-1788773598141", "record_id": "40987", "stages": ["budget_pass", "latency_pass", "ai_confirmed"], "started_at": "2026-09-07T18:34:13.320269", "state": "blocked", "terminal_axis": "ENTRY_AI_AUTHORITY_REVALIDATION", "terminal_stage": "pre_submit_entry_ai_authority_guard_block"}], "attempt_partition_policy": "record_explicit_attempt_or_ordered_retry_v2", "axis_event_counts": {"BROKER_RECEIPT": 0, "ENTRY_AI_AUTHORITY_REVALIDATION": 8, "LATENCY_PRE_SUBMIT": 53, "PRICE_REVALIDATION": 0, "UPSTREAM_GATE": 509}, "axis_exact_attempt_event_counts": {"BROKER_RECEIPT": 0, "ENTRY_AI_AUTHORITY_REVALIDATION": 8, "LATENCY_PRE_SUBMIT": 53, "PRICE_REVALIDATION": 0, "UPSTREAM_GATE": 53}, "axis_later_progress_attempt_counts": {"BROKER_RECEIPT": 0, "ENTRY_AI_AUTHORITY_REVALIDATION": 0, "LATENCY_PRE_SUBMIT": 0, "PRICE_REVALIDATION": 0, "UPSTREAM_GATE": 1}, "axis_missing_exact_attempt_key_events": {"BROKER_RECEIPT": 0, "ENTRY_AI_AUTHORITY_REVALIDATION": 0, "LATENCY_PRE_SUBMIT": 0, "PRICE_REVALIDATION": 0, "UPSTREAM_GATE": 0}, "axis_stage_order_violation_events": {"BROKER_RECEIPT": 0, "ENTRY_AI_AUTHORITY_REVALIDATION": 1, "LATENCY_PRE_SUBMIT": 0, "PRICE_REVALIDATION": 0, "UPSTREAM_GATE": 0}, "axis_superseded_attempt_counts": {"BROKER_RECEIPT": 0, "ENTRY_AI_AUTHORITY_REVALIDATION": 1, "LATENCY_PRE_SUBMIT": 0, "PRICE_REVALIDATION": 0, "UPSTREAM_GATE": 0}, "axis_terminal_causal_attempt_counts": {"BROKER_RECEIPT": 0, "ENTRY_AI_AUTHORITY_REVALIDATION": 6, "LATENCY_PRE_SUBMIT": 53, "PRICE_REVALIDATION": 0, "UPSTREAM_GATE": 52}, "core_handoff_axes": ["UPSTREAM_GATE", "LATENCY_PRE_SUBMIT", "ENTRY_AI_AUTHORITY_REVALIDATION", "PRICE_REVALIDATION", "BROKER_RECEIPT"], "decision_authority": "submit_drought_attribution_only", "denominator_exact_attempt_counts": {"ai_confirmed": 56, "budget_pass": 67, "latency_pass": 10, "order_bundle_submitted": 2}, "denominator_missing_exact_attempt_key_events": {"ai_confirmed": 0, "budget_pass": 0, "latency_pass": 0, "order_bundle_submitted": 0}, "denominator_stage_order_violation_events": {"ai_confirmed": 0, "budget_pass": 0, "latency_pass": 0, "order_bundle_submitted": 0}, "denominator_stages": ["ai_confirmed", "budget_pass", "latency_pass", "order_bundle_submitted"], "exclusion_applied": true, "forbidden_uses": ["standalone_runtime_apply", "broker_order_submit", "guard_relaxation", "provider_change", "bot_restart", "standalone_ev_approval"], "identity_fallback_allowed": false, "identity_field": "record_id", "metric_role": "funnel_count", "missing_exact_attempt_key_event_count": 0, "pending_attempt_count": 6, "primary_decision_metric": "terminal_causal_attempt_count", "retry_attempt_count": 83, "runtime_effect": false, "sample_floor": "one_valid_record_attempt_per_causal_axis", "schema_version": 2, "source_quality_gate": "exact_record_identity_ordered_stages_excluded_invalid_rows", "stage_order_violation_event_count": 1, "status": "source_quality_gap_excluded", "submitted_attempt_count": 2, "summary_terminal_identity_gap_events": 0, "terminal_causal_attempt_count": 111, "terminal_causal_partition_disjoint": true, "unclassified_terminal_attempt_count": 0, "window_policy": "same_day_venue_session_ordered_attempt_cycles"}, "forbidden_uses": ["broker_order_submit", "runtime_apply_candidate", "intraday_threshold_mutation", "provider_route_change", "bot_restart_trigger", "live_auto_promotion"], "metric_role": "funnel_count", "no_current_signal_axes": ["PRICE_REVALIDATION", "BROKER_RECEIPT", "SOURCE_TAXONOMY_LEAKAGE"], "observation_only_axes": ["BUDGET_PASS_COLLAPSE", "ECONOMIC_PARTICIPATION", "SIM_REAL_AUTHORITY"], "primary_decision_metric": "causal_bottleneck_axis_observed_count", "runtime_effect": false, "sample_floor": "one_explicit_attempt_per_axis", "source_quality_gate": "lossless_attempt_key_and_explicit_stage_provenance", "supporting_diagnostic_axes": ["BUDGET_PASS_COLLAPSE", "ECONOMIC_PARTICIPATION", "SIM_REAL_AUTHORITY", "SOURCE_TAXONOMY_LEAKAGE"], "window_policy": "same_session_unique_attempt_submit_funnel"}, "quote_freshness_attribution_inconsistent": false, "quote_freshness_latency_pass_recovered_count": 5, "quote_freshness_refresh_applied_count": 15, "quote_freshness_refresh_attempted_count": 15, "required_downstream": ["code_improvement_workorder", "threshold_cycle_ev_report", "runtime_approval_summary", "postclose_verifier"], "root_cause_closure_status_hint": "source_quality_blocked", "root_cause_counts": {"quote_freshness_input_snapshot_noop": 8, "quote_stale": 13, "spread_microstructure_guard": 53, "spread_or_slippage_guard": 41}, "root_cause_signal": "SUBMIT_DROUGHT_CRITICAL", "runtime_effect": false, "source_report_type": "buy_funnel_sentinel", "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "ECONOMIC_PARTICIPATION", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_gap_open and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 11. `order_observation_source_quality_raw_row_exclusion_producer_gap`

- title: Observation source-quality raw row exclusion revalidation closed
- decision: `attach_existing_family`
- decision_reason: the preserved exclusion manifest is audit evidence from the first scan; the current scan has no hard-blocking excluded rows and final revalidation passed
- source_report_type: `observation_source_quality_audit`
- lifecycle_stage: `source_quality_gate`
- target_subsystem: `runtime_instrumentation`
- route: `source_quality_raw_row_exclusion_revalidated_closed`
- mapped_family: `observation_source_quality_audit`
- threshold_family: `observation_source_quality_audit`
- improvement_type: `source_quality_raw_row_exclusion_revalidated_closed`
- confidence: `audit`
- priority: `0`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: none_direct_source_quality_attribution_only
- evidence: `status=warning`, `event_count=329378`, `warning_stage_count=0`, `warning_stages=`, `high_volume_no_source_field_stage_count=0`, `unknown_token_stage_count=2`, `review_warning_count=2`, `decision_authority=source_quality_only`, `runtime_effect=false`, `raw_row_exclusion_manifest=/home/ubuntu/KORStockScan/data/source_quality/raw_row_exclusion/2026-09-07_20260907T202828679987+0900/manifest.json`, `excluded_row_count=3`, `stage_counts={"pyramid_blocked_reason": 1, "scalp_entry_action_decision_snapshot": 2}`, `field_gap_counts={"invalid_fields:minute_candle_window_fresh_contract": 2, "missing_fields:max_micro_vwap_bps": 1, "missing_fields:min_ai_score": 1, "missing_fields:min_buy_pressure": 1, "missing_fields:min_profit_pct": 1, "missing_fields:min_tick_accel": 1}`, `exclusion_reasons={"invalid_label": 2, "not_evaluated_context": 3, "provenance_missing": 1, "required_field_missing": 1, "unknown_token": 3}`, `first_timestamp=2026-09-07T13:10:13.789505`, `last_timestamp=2026-09-07T19:40:41.056615`, `forbidden_uses=EV/rolling/MTD/cumulative tuning/live-auto promotion/runtime approval for excluded rows`, `required_action=fix producer provenance/source-quality cause or mark reviewed_not_available/waiting_sample_only explicitly`, `current_scan_hard_blocking_excluded_row_count=0`, `post_exclusion_hard_blocking_excluded_row_count=0`, `raw_row_exclusion_revalidation_required=false`, `revalidation_disposition=closed_preserved_manifest_audit_evidence`, `producer_hint:stage=scalp_entry_action_decision_snapshot count=2 pipeline=ENTRY_PIPELINE subsystem=scalping_entry_or_sim_producer top_reasons=invalid_label,not_evaluated_context,unknown_token`, `producer_hint:stage=pyramid_blocked_reason count=1 pipeline=HOLDING_PIPELINE subsystem=runtime_instrumentation_producer top_reasons=not_evaluated_context,provenance_missing,required_field_missing,unknown_token`, `sample_row:line_no=118238 stage=scalp_entry_action_decision_snapshot record_id=40581 reasons=invalid_label,not_evaluated_context,unknown_token gap_fields={"invalid_fields": ["minute_candle_window_fresh_contract"]}`, `sample_row:line_no=118243 stage=scalp_entry_action_decision_snapshot record_id=40581 reasons=invalid_label,not_evaluated_context,unknown_token gap_fields={"invalid_fields": ["minute_candle_window_fresh_contract"]}`, `sample_row:line_no=321606 stage=pyramid_blocked_reason record_id=40904 reasons=not_evaluated_context,provenance_missing,required_field_missing,unknown_token gap_fields={"missing_fields": ["min_profit_pct", "min_ai_score", "min_buy_pressure", "min_tick_accel", "max_micro_vwap_bps"]}`
- parity_contract: -
- next_postclose_metric: observation_source_quality_audit.warning_stage_count and high_volume_no_source_field_stage_count
- files_likely_touched: `src/engine/observation_source_quality_audit.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_observation_source_quality_audit.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `terminal_existing_family_evidence`
- root_cause_closure_status: `-`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "terminal_existing_family_evidence", "previous_route": "source_quality_raw_row_exclusion_revalidated_closed", "repeat_count": 4, "repeat_key": "order_observation_source_quality_raw_row_exclusion_producer_gap", "repeat_signature": "sig:observation_source_quality_audit|runtime_instrumentation|source_quality_gate|source_quality_raw_row_exclusion_revalidated_closed|observation_source_quality_audit|observation_source_quality_raw_row_exclusion_revalidation_closed", "review_disposition": "review_required"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Keep the manifest as audit provenance. Reopen a producer-fix implement_now only if a later current scan again finds hard-blocking rows or raw-row exclusion revalidation fails.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 12. `order_conversion_lane_submit_drought_submit_drought_latency_pre_submit`

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
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=submit_drought:LATENCY_PRE_SUBMIT`, `blocker_class=submit_drought`, `conversion_impact_rank=1`, `next_repair_action=close_submit_drought_latency_pre_submit_quote_freshness`, `acceptance_test=the same attempt joins budget to latency block/pass and terminal; an earlier-stage retry is not recovery and DANGER safety is unchanged`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "LATENCY_PRE_SUBMIT", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "root_cause_acceptance_test": "the same attempt joins budget to latency block/pass and terminal; an earlier-stage retry is not recovery and DANGER safety is unchanged", "root_cause_next_repair_action": "close_submit_drought_latency_pre_submit_quote_freshness", "root_cause_signal": "conversion_lane:submit_drought:LATENCY_PRE_SUBMIT:open", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_conversion_lane_submit_drought_submit_drought_latency_pre_submit", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_submit_drought_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_submit_drought_submit_drought_latency_pre_subm", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 13. `order_conversion_lane_submit_drought_submit_drought_upstream_gate`

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
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=submit_drought:UPSTREAM_GATE`, `blocker_class=submit_drought`, `conversion_impact_rank=2`, `next_repair_action=join upstream action/reason cohorts to executable BBO and first-hit outcomes; AI semantic tuning remains separately owned`, `acceptance_test=exact attempts preserve canonical upstream terminal reasons and retry boundaries; raw/cache/consumer counts reconcile without unknown loss; repair does not require economic replay or grant runtime authority`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "UPSTREAM_GATE", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "root_cause_acceptance_test": "exact attempts preserve canonical upstream terminal reasons and retry boundaries; raw/cache/consumer counts reconcile without unknown loss; repair does not require economic replay or grant runtime authority", "root_cause_next_repair_action": "join upstream action/reason cohorts to executable BBO and first-hit outcomes; AI semantic tuning remains separately owned", "root_cause_signal": "conversion_lane:submit_drought:UPSTREAM_GATE:open", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_conversion_lane_submit_drought_submit_drought_upstream_gate", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_submit_drought_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_submit_drought_submit_drought_upstream_gate", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 14. `order_conversion_lane_submit_drought_submit_drought_entry_ai_authority_revalidation`

- title: Conversion lane blocker follow-up: submit_drought submit_drought:ENTRY_AI_AUTHORITY_REVALIDATION
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
- evidence: `conversion_candidate_id=submit_drought:ENTRY_AI_AUTHORITY_REVALIDATION`, `blocker_class=submit_drought`, `conversion_impact_rank=3`, `next_repair_action=join exact AI authority reason, executable BBO, and target/adverse first-hit outcomes before proposing a bounded one-share probe`, `acceptance_test=entry-AI-authority blocks preserve canonical reason and exact payload lineage through consumer validation; repair leaves AI semantics and submit guards unchanged and does not depend on positive EV samples`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "ENTRY_AI_AUTHORITY_REVALIDATION", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "root_cause_acceptance_test": "entry-AI-authority blocks preserve canonical reason and exact payload lineage through consumer validation; repair leaves AI semantics and submit guards unchanged and does not depend on positive EV samples", "root_cause_next_repair_action": "join exact AI authority reason, executable BBO, and target/adverse first-hit outcomes before proposing a bounded one-share probe", "root_cause_signal": "conversion_lane:submit_drought:ENTRY_AI_AUTHORITY_REVALIDATION:open", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_conversion_lane_submit_drought_submit_drought_entry_ai_authority_revalidation", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_submit_drought_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_submit_drought_submit_drought_entry_ai_authori", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 15. `order_pattern_lab_ai_review_source_quality_gap`

- title: Pattern Lab AI review follow-up: source_quality_gap
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `review_id=source_quality_gap`, `domain=scalping`, `final_state=source_quality_gap`, `final_decision=block_runtime_use`, `auditor_pass=False`, `explicit_gap_type=source_quality_gap`, `source_paths=['/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-09-07.json', '/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-09-07.json', '/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-07.json']`
- parity_contract: -
- next_postclose_metric: pattern_lab_ai_review.source_quality_gap
- files_likely_touched: `src/engine/pattern_lab_ai_review.py`, `src/engine/pattern_lab_currentness_audit.py`, `analysis/gemini_scalping_pattern_lab`, `analysis/claude_scalping_pattern_lab`, `analysis/deepseek_swing_pattern_lab`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_ai_review.py src/tests/test_pattern_lab_currentness_audit.py`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"actual_order_submitted": false, "allowed_runtime_apply": false, "auditor_pass": false, "broker_order_forbidden": true, "decision_authority": "pattern_lab_ai_review_source_only", "explicit_gap_type": "source_quality_gap", "final_decision": "block_runtime_use", "final_state": "source_quality_gap", "forbidden_uses": ["threshold mutation", "order guard mutation", "provider change", "bot restart", "broker order submit", "runtime env apply", "real order enable"], "implementation_type": "pattern_lab_ai_review_source_quality_followup_provenance", "implemented_scope": "Pattern Lab AI review source-quality follow-up now carries review_id, source paths, final decision, gap type, and source-only runtime prohibitions into the workorder surface.", "normalized_review_id": "source_quality_gap", "requires_separate_runtime_apply_candidate": true, "review_id": "source_quality_gap", "root_cause_closure_status_hint": "root_cause_closed", "runtime_effect": false, "runtime_mutation_allowed": false, "source_paths": ["/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-09-07.json", "/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-09-07.json", "/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-07.json"], "source_report_type": "pattern_lab_ai_review"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

## Non-Selected Source Orders

아래 항목은 source order로 분류됐지만 selected implementation order에는 포함되지 않았다. 재작업 지시 시 `decision`, `decision_reason`, `runtime_effect`를 먼저 재판정한다.

### N1. `order_latency_canary_tag_완화_1축_canary_승인`

- title: latency canary tag 완화 1축 canary 승인
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `runtime_instrumentation`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_but_waiting_sample`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_latency_canary_tag_완화_1축_canary_승인", "repeat_signature": "sig:scalping_pattern_lab_automation|runtime_instrumentation||latency_canary_tag_완화_1축_canary_승인||latency_canary_tag_완화_1축_canary_승인", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/sniper_performance_tuning_report.py`, `src/engine/daily_threshold_cycle_report.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N2. `order_rising_missed_entry_turn_bbo_coverage`

- title: rising missed entry-turn executable BBO coverage closure
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `rising_missed_scout_workorder`
- lifecycle_stage: `entry`
- target_subsystem: `scanner_existing_ws_bbo_observation`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 4, "repeat_key": "order_rising_missed_entry_turn_bbo_coverage", "repeat_signature": "sig:rising_missed_scout_workorder|scanner_existing_ws_bbo_observation|entry|source_only_existing_ws_bbo_coverage_workorder|rising_missed_entry_turn_point_replay|rising_missed_entry_turn_executable_bbo_coverage_closure", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/kiwoom_sniper_v2.py`, `src/engine/monitoring/entry_turn_point_replay.py`, `src/engine/monitoring/rising_missed_intraday_feedback.py`
- acceptance_tests: `exact_ws_bbo_join_coverage_pct>=95`, `pre_anchor_bbo_coverage_pct>=95`, `paired_coverage_pct>=95`, `primary_right_censored_pct<=20`, `primary_resolved_outcome_count>=20`, `source_quality_adjusted_ev_pct remains null until every floor passes`, `runtime_effect=false, allowed_runtime_apply=false, actual_order_submitted=false, broker_order_forbidden=true`

### N3. `order_scanner_eligible_no_heavy_closed_loop`

- title: Scanner eligible-to-heavy evaluation loss closure
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `intraday_ws_freshness_monitor`
- lifecycle_stage: `entry`
- target_subsystem: `scanner_runtime_freshness_funnel`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_but_waiting_sample`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_scanner_eligible_no_heavy_closed_loop", "repeat_signature": "sig:intraday_ws_freshness_monitor|scanner_runtime_freshness_funnel|entry|scanner_funnel_source_quality_followup|scanner_runtime_freshness_funnel|scanner_eligible_to_heavy_evaluation_loss_closure", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/monitoring/intraday_ws_freshness_monitor.py`, `src/engine/scalping/scanner_scheduler_replay.py`, `src/tests/test_intraday_ws_freshness_monitor.py`
- acceptance_tests: `pipeline_threshold_mirror_events_are_deduplicated`, `every_unique_promotion_has_one_final_outcome_or_active_right_censored`, `missing_executable_bbo_remains_source_quality_blocked_not_zero_ev`

### N4. `order_ws_decision_stage_stale_backoff_attribution`

- title: WS decision-stage stale backoff attribution
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `intraday_ws_freshness_monitor`
- lifecycle_stage: `entry`
- target_subsystem: `scanner_runtime_freshness_funnel`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_waiting_sample", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_ws_decision_stage_stale_backoff_attribution", "repeat_signature": "sig:intraday_ws_freshness_monitor|scanner_runtime_freshness_funnel|entry|scanner_funnel_source_quality_followup|scanner_runtime_freshness_funnel|ws_decision_stage_stale_backoff_attribution", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/kiwoom_websocket.py`, `src/engine/sniper_state_handlers.py`, `src/engine/monitoring/intraday_ws_freshness_monitor.py`, `src/tests/test_intraday_ws_freshness_monitor.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_kiwoom_websocket.py src/tests/test_intraday_ws_freshness_monitor.py`

### N5. `order_ws_total_stale_escalation`

- title: WS total stale escalation
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `intraday_ws_freshness_monitor`
- lifecycle_stage: `entry`
- target_subsystem: `scanner_runtime_freshness_funnel`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_waiting_sample", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_ws_total_stale_escalation", "repeat_signature": "sig:intraday_ws_freshness_monitor|scanner_runtime_freshness_funnel|entry|scanner_funnel_source_quality_followup|scanner_runtime_freshness_funnel|ws_total_stale_escalation", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/kiwoom_websocket.py`, `src/engine/monitoring/quote_stale_frequency_report.py`, `src/engine/monitoring/intraday_ws_freshness_monitor.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_kiwoom_websocket.py src/tests/test_intraday_ws_freshness_monitor.py`

### N6. `order_latency_guard_miss_ev_recovery`

- title: latency guard miss EV recovery
- decision: `attach_existing_family`
- decision_reason: Independent latency calibration and aggregate join-gap inference are retired; retain existing BUY Funnel diagnostics only.
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `runtime_instrumentation`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_but_waiting_sample`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_latency_guard_miss_ev_recovery", "repeat_signature": "sig:scalping_pattern_lab_automation|runtime_instrumentation||latency_guard_miss_ev_recovery||latency_guard_miss_ev_recovery", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/sniper_performance_tuning_report.py`, `src/engine/daily_threshold_cycle_report.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N7. `order_one_share_threshold_ai_score_near_buy_entry_hook_review`

- title: one-share threshold opportunity existing-family evidence: ai_score_near_buy
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `one_share_threshold_opportunity`
- lifecycle_stage: `entry`
- target_subsystem: `scalping_entry_ai_score_recheck`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `source_evidence_candidate`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- files_likely_touched: -
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_one_share_threshold_opportunity.py src/tests/test_build_code_improvement_workorder.py`, `A separate source-gap/root-cause order is required before any implementation decision`, `source-only audit must not mutate intraday runtime thresholds, broker/order guards, provider route, bot state, quantity, or caps`

### N8. `order_one_share_threshold_strength_momentum_vpw_entry_hook_review`

- title: one-share threshold opportunity existing-family evidence: strength_momentum_vpw
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `one_share_threshold_opportunity`
- lifecycle_stage: `entry`
- target_subsystem: `entry_strength_momentum_history_recheck`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `source_evidence_candidate`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- files_likely_touched: -
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_one_share_threshold_opportunity.py src/tests/test_build_code_improvement_workorder.py`, `A separate source-gap/root-cause order is required before any implementation decision`, `source-only audit must not mutate intraday runtime thresholds, broker/order guards, provider route, bot state, quantity, or caps`

### N9. `order_rising_missed_classifier_prior_feedback_bridge`

- title: rising missed cumulative classifier prior bridge
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `rising_missed_scout_workorder`
- lifecycle_stage: `entry`
- target_subsystem: `rising_missed_entry_classifier`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_rising_missed_classifier_prior_feedback_bridge", "repeat_signature": "sig:rising_missed_scout_workorder|rising_missed_entry_classifier|entry|source_only_classifier_prior_workorder|rising_missed_classifier_prior_feedback_bridge|rising_missed_cumulative_classifier_prior_bridge", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/monitoring/rising_missed_classifier_prior.py`, `src/engine/monitoring/rising_missed_scout_workorder.py`, `src/engine/scalping/rising_missed_one_share_entry.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_classifier_prior.py src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py`, `prior bridge remains source-only and cannot mutate one-share allow/block, runtime thresholds, broker/order guards, provider route, or bot state`

### N10. `order_rising_missed_scout_scale_in_qty_evidence_split`

- title: rising missed scout scale-in quantity and evidence blocker split
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `rising_missed_scout_workorder`
- lifecycle_stage: `scale_in`
- target_subsystem: `scale_in_quantity_and_evidence`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/monitoring/rising_missed_scout_workorder.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py`, `qty/evidence split remains source-only and does not release position cap or quantity guard`

### N11. `order_scanner_funnel_executable_bbo_join`

- title: Scanner funnel executable-BBO economic attribution
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `intraday_ws_freshness_monitor`
- lifecycle_stage: `entry`
- target_subsystem: `scanner_runtime_freshness_funnel`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_but_waiting_sample`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_scanner_funnel_executable_bbo_join", "repeat_signature": "sig:intraday_ws_freshness_monitor|scanner_runtime_freshness_funnel|entry|scanner_funnel_source_quality_followup|scanner_runtime_freshness_funnel|scanner_funnel_executable_bbo_economic_attribution", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/monitoring/pruned_candidate_bbo_collector.py`, `src/scanners/scalping_scanner.py`, `src/engine/monitoring/intraday_ws_freshness_monitor.py`, `src/tests/test_pruned_candidate_bbo_collector.py`, `src/tests/test_intraday_ws_freshness_monitor.py`
- acceptance_tests: `source_capture_preserves_active_owner_targets_and_adds_zero_ws_registrations`, `ka10004_requests_remain_within_process_daily_and_interval_budget`, `bounded_observer_selected_episode_bbo_join_coverage_pct>=95`, `each_selected_prune_cohort_venue_session_resolved_outcome_count>=20`, `each_selected_prune_cohort_venue_session_right_censored_pct<=20`, `full_prune_population_ev_extrapolation_allowed=false`, `missing_bbo_is_source_quality_blocked_not_zero_profit`, `KRX_PREMARKET_KRX_LIKE_NXT_results_are_separate`, `fixed_cost_contract_effective_date_and_source_hash_match`, `official_common_stock_master_exact_date_hash_and_lookup_pass`

### N12. `order_ws_trade_tick_quiet_low_liquidity_classification`

- title: WS trade tick quiet low-liquidity classification
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `intraday_ws_freshness_monitor`
- lifecycle_stage: `entry`
- target_subsystem: `scanner_runtime_freshness_funnel`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_waiting_sample", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_ws_trade_tick_quiet_low_liquidity_classification", "repeat_signature": "sig:intraday_ws_freshness_monitor|scanner_runtime_freshness_funnel|entry|scanner_funnel_source_quality_followup|scanner_runtime_freshness_funnel|ws_trade_tick_quiet_low_liquidity_classification", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/kiwoom_websocket.py`, `src/engine/sniper_state_handlers.py`, `src/engine/monitoring/intraday_ws_freshness_monitor.py`, `src/tests/test_state_handler_fast_signatures.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_state_handler_fast_signatures.py src/tests/test_intraday_ws_freshness_monitor.py`

### N13. `order_ai_threshold_dominance`

- title: AI threshold dominance
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `entry_funnel`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_missed_entry_counterfactual.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N14. `order_rising_missed_classifier_prior_bridge`

- title: Attach cumulative source-lineage prior lookup to rising-missed classifier reports
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `rising_missed_classifier_prior`
- lifecycle_stage: `entry`
- target_subsystem: `rising_missed_entry_classifier`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_rising_missed_classifier_prior_bridge", "repeat_signature": "sig:rising_missed_classifier_prior|rising_missed_entry_classifier|entry||rising_missed_classifier_prior_bridge|attach_cumulative_source_lineage_prior_lookup_to_rising_missed_classifier_report", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: -
- acceptance_tests: -

### N15. `order_ai_threshold_miss_ev_recovery`

- title: AI threshold miss EV recovery
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `entry_funnel`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_ai_threshold_miss_ev_recovery", "repeat_signature": "sig:scalping_pattern_lab_automation|entry_funnel||threshold_family_input||ai_threshold_miss_ev_recovery", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_missed_entry_counterfactual.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N16. `order_panic_sell_defense_lifecycle_transition_pack`

- title: panic sell defense lifecycle transition pack
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `threshold_cycle_calibration_source_bundle`
- lifecycle_stage: `holding_exit`
- target_subsystem: `panic_sell_defense`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_but_waiting_sample`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_panic_sell_defense_lifecycle_transition_pack", "repeat_signature": "sig:threshold_cycle_calibration_source_bundle|panic_sell_defense|holding_exit|runtime_transition_design|panic_sell_defense|panic_sell_defense_lifecycle_transition_pack", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/panic_sell_defense_report.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/plan-korStockScanPerformanceOptimization.rebase.md`
- acceptance_tests: `pytest panic sell defense/report lifecycle tests`, `pytest src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py`

### N17. `order_partial_only_표류_전용_timeout_report_only`

- title: partial-only 표류 전용 timeout report-only
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `holding_exit`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_but_waiting_sample`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_partial_only_표류_전용_timeout_report_only", "repeat_signature": "sig:scalping_pattern_lab_automation|holding_exit||threshold_family_input||partial_only_표류_전용_timeout_report_only", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N18. `order_split_entry_rebase_수량_정합성_report_only_감사`

- title: split-entry rebase 수량 정합성 report-only 감사
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `holding_exit`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_but_waiting_sample`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_split_entry_rebase_수량_정합성_report_only_감사", "repeat_signature": "sig:scalping_pattern_lab_automation|holding_exit||threshold_family_input||split_entry_rebase_수량_정합성_report_only_감사", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N19. `order_동일_종목_split_entry_soft_stop_재진입_cooldown_report_only`

- title: 동일 종목 split-entry soft-stop 재진입 cooldown report-only
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `holding_exit`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_but_waiting_sample`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_동일_종목_split_entry_soft_stop_재진입_cooldown_report_only", "repeat_signature": "sig:scalping_pattern_lab_automation|holding_exit||threshold_family_input||동일_종목_split_entry_soft_stop_재진입_cooldown_report_only", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N20. `order_liquidity_gate_miss_ev_recovery`

- title: liquidity gate miss EV recovery
- decision: `design_family_candidate`
- decision_reason: pattern lab can only propose source-only family design input; LDM/discovery/runtime bridge contracts must close before any auto_bounded_live consideration
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `entry_filter_quality`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_design_family_candidate`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "design_family_candidate", "previous_implementation_status": "terminal_design_family_candidate", "previous_route": "auto_family_candidate", "repeat_count": 7, "repeat_key": "order_liquidity_gate_miss_ev_recovery", "repeat_signature": "sig:scalping_pattern_lab_automation|entry_filter_quality||liquidity_gate_miss_ev_recovery||liquidity_gate_miss_ev_recovery", "review_disposition": "review_required"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N21. `order_overbought_gate_miss_ev_recovery`

- title: overbought gate miss EV recovery
- decision: `design_family_candidate`
- decision_reason: pattern lab can only propose source-only family design input; LDM/discovery/runtime bridge contracts must close before any auto_bounded_live consideration
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `entry_filter_quality`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_design_family_candidate`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "design_family_candidate", "previous_implementation_status": "terminal_design_family_candidate", "previous_route": "auto_family_candidate", "repeat_count": 7, "repeat_key": "order_overbought_gate_miss_ev_recovery", "repeat_signature": "sig:scalping_pattern_lab_automation|entry_filter_quality||overbought_gate_miss_ev_recovery||overbought_gate_miss_ev_recovery", "review_disposition": "review_required"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N22. `order_partial_fallback_확대_직후_즉시_재평가_report_only`

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

- 구현 결과는 `2026-09-08` 이후 postclose `threshold_cycle`, `scalping_pattern_lab_automation`, `threshold_cycle_ev`가 자동으로 다시 읽는다.
- 구현자가 수동으로 threshold 값을 바꾸는 것이 아니라, source/report/provenance를 닫아 다음 calibration이 판단하게 한다.
- 다음 Codex 세션 입력 문구: `none_for_bucket_discovery_classification`

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
