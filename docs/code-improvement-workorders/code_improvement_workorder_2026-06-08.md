# Code Improvement Workorder - 2026-06-08

## 목적

- Postclose 자동화가 생성한 `code_improvement_order`를 Codex 실행용 작업지시서로 변환한다.
- 입력은 scalping pattern lab automation, swing lifecycle improvement automation, swing pattern lab automation을 함께 포함할 수 있다.
- 이 문서는 repo/runtime을 직접 변경하지 않는다. 사용자가 이 문서를 Codex 세션에 넣고 구현을 요청하는 지점만 사람 개입으로 남긴다.
- 구현 후 자동화체인 재투입은 다음 postclose report, threshold calibration, daily EV report가 담당한다.

## Source

- pattern_lab_automation: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-06-08.json`
- swing_improvement_automation: `/home/ubuntu/KORStockScan/data/report/swing_improvement_automation/swing_improvement_automation_2026-06-08.json`
- swing_pattern_lab_automation: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-06-08.json`
- swing_strategy_discovery_ev: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-06-08.json`
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-06-08.json`
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-06-08.json`
- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-08.json`
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-06-08.json`
- threshold_cycle_calibration: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_calibration/threshold_cycle_calibration_2026-06-08_postclose.json`
- pipeline_event_verbosity: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-06-08.json`
- observation_source_quality_audit: `/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-08.json`
- codebase_performance_workorder: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-06-08.json`
- pattern_lab_currentness_audit: `/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-06-08.json`
- pattern_lab_ai_review: `/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-06-08.json`
- producer_gap_discovery: `/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-06-08.json`
- stage_hook_workorder_discovery: `/home/ubuntu/KORStockScan/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_2026-06-08.json`
- stage_hook_runtime_scaffold: `/home/ubuntu/KORStockScan/data/report/stage_hook_runtime_scaffold/stage_hook_runtime_scaffold_2026-06-08.json`
- buy_funnel_sentinel: `/home/ubuntu/KORStockScan/data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-06-08.json`
- generated_at: `2026-06-08T18:11:28+09:00`
- generation_id: `2026-06-08-bc3e1680b38e`
- source_hash: `bc3e1680b38e01855fc41e072d75ba08b55a7846a080e528aefe311a76902451`

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
- previous_generation_id: `2026-06-08-721cbb6963c2`
- previous_source_hash: `721cbb6963c2c2a135e1d4546c1ac3c85badbc0e7c0d8fb88faf2e54222cfeb9`
- new_order_ids: `[]`
- removed_order_ids: `[]`
- decision_changed_order_ids: `[]`

## Summary

- source_order_count: `141`
- scalping_source_order_count: `7`
- swing_source_order_count: `9`
- swing_entry_bottleneck_primary: `SWING_ENTRY_BOTTLENECK_OBSERVE`
- swing_entry_bottleneck_selected: `False`
- swing_lab_source_order_count: `4`
- swing_strategy_discovery_source_order_count: `2`
- swing_lifecycle_matrix_source_order_count: `5`
- swing_lifecycle_bucket_discovery_source_order_count: `0`
- pattern_lab_currentness_source_order_count: `0`
- pattern_lab_ai_review_source_order_count: `6`
- threshold_ev_source_order_count: `14`
- lifecycle_submit_bucket_source_order_count: `0`
- lifecycle_holding_exit_bucket_source_order_count: `20`
- pipeline_event_verbosity_source_order_count: `0`
- observation_source_quality_source_order_count: `0`
- codebase_performance_source_order_count: `12`
- buy_funnel_sentinel_source_order_count: `0`
- entry_submit_drought_selected: `False`
- entry_submit_drought_handoff_missing: `False`
- panic_lifecycle_source_order_count: `2`
- selected_order_count: `106`
- non_selected_order_count: `35`
- source_decision_counts: `{'attach_existing_family': 127, 'design_family_candidate': 5, 'defer_evidence': 7, 'reject': 2}`
- selected_decision_counts: `{'attach_existing_family': 105, 'defer_evidence': 1}`
- selected_route_counts: `{'existing_family': 97, 'ai_review_coverage_review': 1, 'parent_conflict_exclusion_review': 1, 'positive_source_only_review': 1, 'source_dimension_rollup': 1, 'pattern_lab_ai_review_handoff_evidence': 4, 'pattern_lab_ai_review_followup_evidence': 1}`
- selected_implement_now_route_count: `0`
- selected_runtime_effect_false_count: `106`
- selected_unimplemented_runtime_effect_false_count: `1`
- selected_unimplemented_route_counts: `{'pattern_lab_ai_review_followup_evidence': 1}`
- selected_implement_now_existing_implementation_count: `0`
- selected_implement_now_existing_implementation_order_ids: `[]`
- selected_implement_now_new_runtime_effect_false_count: `0`
- selected_implement_now_new_runtime_effect_false_order_ids: `[]`
- repeat_unresolved_escalation_count: `0`
- repeat_unresolved_escalated_order_ids: `[]`
- non_selected_decision_counts: `{'attach_existing_family': 22, 'design_family_candidate': 5, 'defer_evidence': 6, 'reject': 2}`
- gemini_fresh: `False`
- claude_fresh: `True`
- swing_lifecycle_audit_available: `True`
- swing_pattern_lab_automation_available: `True`
- swing_pattern_lab_fresh: `True`
- pattern_lab_currentness_status: `pass`
- pattern_lab_currentness_fail_count: `0`
- pattern_lab_ai_review_status: `warning`
- pattern_lab_ai_review_workorder_count: `6`
- swing_threshold_ai_status: `parsed`
- daily_ev_available: `True`

### Duplicate Order Collisions
- `duplicate_order_id=order_lifecycle_entry_bucket_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale_fresh_liquid source=lifecycle_decision_matrix_entry_bucket_attribution stage=entry`
- `duplicate_order_id=order_lifecycle_entry_bucket_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale_fresh_liquid source=lifecycle_decision_matrix_entry_bucket_attribution stage=entry`
- `duplicate_order_id=order_lifecycle_entry_bucket_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale_fresh_liquid source=lifecycle_decision_matrix_entry_bucket_attribution stage=entry`
- `duplicate_order_id=order_lifecycle_entry_bucket_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale_fresh_liquid source=lifecycle_decision_matrix_entry_bucket_attribution stage=entry`

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

### 1. `order_latency_canary_tag_완화_1축_canary_승인`

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
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "pattern_lab_analysis_workorder_source_only", "finding_id": "latency_canary_tag_완화_1축_canary_승인", "implementation_type": "pattern_lab_report_only_instrumentation", "runtime_effect": false, "source_report_type": "scalping_pattern_lab_automation", "target_subsystem": "runtime_instrumentation"}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_but_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 2. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_10_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_a680eadf`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_10`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- implementation_provenance: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 3. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_11_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_a680eadf`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_11`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- implementation_provenance: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 4. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_12_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_a680eadf`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_12`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- implementation_provenance: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 5. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_13_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_a680eadf`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_13`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- implementation_provenance: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 6. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_14_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_c976c968`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4391b87c03
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_14`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4391b87c03`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'postclose_exit_without_entry']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- implementation_provenance: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 7. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_15_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42`

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
- implementation_provenance: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 8. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_16_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_16`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:70a865069d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- implementation_provenance: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 9. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_17_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_ddadf37b`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:8c9bd92dae
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_17`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:8c9bd92dae`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'postclose_exit_without_entry']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- implementation_provenance: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 10. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_18_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_79db100a`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:496a0a2877
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_18`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:496a0a2877`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- implementation_provenance: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 11. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_19_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42`

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
- implementation_provenance: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 12. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_1_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_a680eadf`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_1`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- implementation_provenance: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 13. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_20_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42`

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
- implementation_provenance: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 14. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_2_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_a680eadf`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_2`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- implementation_provenance: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 15. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_3_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_a680eadf`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_3`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- implementation_provenance: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 16. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_4_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_a680eadf`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_4`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- implementation_provenance: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 17. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_5_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_a680eadf`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_5`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- implementation_provenance: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 18. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_6_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_a680eadf`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_6`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- implementation_provenance: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 19. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_7_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_a680eadf`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_7`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- implementation_provenance: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 20. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_8_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_a680eadf`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_8`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- implementation_provenance: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 21. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_9_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_a680eadf`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_9`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:91326fb12f`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- implementation_provenance: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 22. `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_73281913`

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
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 23. `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_823fe278`

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
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 24. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_good_e_d8c33947`

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
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 25. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_missed_30bb5c8f`

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
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 26. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_neutra_d5168c3c`

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
- evidence: `workorder_id=exit_bucket_source_quality_8`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 27. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_e_71b132b9`

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
- evidence: `workorder_id=exit_bucket_source_quality_6`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 28. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_missed_bb293be8`

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
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 29. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutra_d73738ba`

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
- evidence: `workorder_id=exit_bucket_source_quality_7`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 30. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_9ba77f3e`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300
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
- evidence: `workorder_id=exit_bucket_source_quality_10`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_recovery_or_relax", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 31. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_b3ffe955`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150
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
- evidence: `workorder_id=exit_bucket_source_quality_9`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 32. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_buy_profit_profit_lt_neg070_hel_575c586d`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start
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
- evidence: `workorder_id=holding_bucket_source_quality_2`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 33. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_buy_profit_profit_pos150_pos300_498d531b`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start
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
- evidence: `workorder_id=holding_bucket_source_quality_8`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_recovery_or_relax", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 34. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_not_applicable_a_50644c4a`

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
- evidence: `workorder_id=holding_bucket_source_quality_6`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_recovery_or_relax", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 35. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_not_applicable_a_d19d801a`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start
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
- evidence: `workorder_id=holding_bucket_source_quality_3`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_recovery_or_relax", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 36. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_not_applicable_a_f7731cc4`

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
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_recovery_or_relax", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 37. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_not_applicable_a_fc555278`

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
- evidence: `workorder_id=holding_bucket_source_quality_1`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
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
- evidence: `workorder_id=holding_bucket_source_quality_5`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 39. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_neg010_pos08_1ef35f1d`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start
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
- evidence: `workorder_id=holding_bucket_source_quality_9`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_recovery_or_relax", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 40. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_pos080_pos15_aaaecaaf`

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
- evidence: `workorder_id=holding_bucket_source_quality_7`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_recovery_or_relax", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 41. `order_lifecycle_holding_bucket_held_bucket_held_not_applicable_at_start_508784a3`

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
- evidence: `workorder_id=holding_bucket_source_quality_10`, `bucket_type=held_bucket`, `bucket_key=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "held_not_applicable_at_start", "bucket_type": "held_bucket", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 42. `order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_low_missing_30m_2h_kospi_trailing_start_take_profit`

- title: Swing LDM source field follow-up: mfe_low|missing|30m_2h|kospi_trailing_start_take_profit|-|-|-|-|-
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_decision_matrix`
- lifecycle_stage: `holding_exit`
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
- evidence: `section=holding_exit_bucket_attribution`, `bucket_type=holding_exit_bucket_attribution`, `bucket_key=mfe_low|missing|30m_2h|kospi_trailing_start_take_profit|-|-|-|-|-`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": ["mae_bucket", "selection_arm", "sector", "theme"], "runtime_effect": false, "sample_status": "waiting_source_field_sample", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 3, "total_count": 3}, "exit_rule": {"coverage_ratio": 1.0, "paths": ["label_fields.exit_reason"], "present_count": 3, "total_count": 3}, "held_bucket": {"coverage_ratio": 1.0, "paths": ["label_fields.held_sec"], "present_count": 3, "total_count": 3}, "mae_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.mae_pct"], "present_count": 0, "total_count": 3}, "market_regime": {"coverage_ratio": 1.0, "paths": ["runtime_features.panic_context", "runtime_features.market_regime"], "present_count": 3, "total_count": 3}, "mfe_bucket": {"coverage_ratio": 1.0, "paths": ["label_fields.mfe_pct"], "present_count": 3, "total_count": 3}, "sector": {"coverage_ratio": 0.0, "paths": ["runtime_features.sector"], "present_count": 0, "total_count": 3}, "selection_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.entry_policy"], "present_count": 0, "total_count": 3}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 3, "total_count": 3}, "theme": {"coverage_ratio": 0.0, "paths": ["runtime_features.theme_tags"], "present_count": 0, "total_count": 3}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 5, "bucket_value_missing": 1, "source_field_missing:mae_bucket": 1, "source_field_missing:sector": 1, "source_field_missing:selection_arm": 1, "source_field_missing:theme": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 43. `order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_low_missing_held_missing_kospi_trailing_start_take_profit`

- title: Swing LDM source field follow-up: mfe_low|missing|held_missing|kospi_trailing_start_take_profit|-|-|-|-|-
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_decision_matrix`
- lifecycle_stage: `holding_exit`
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
- evidence: `section=holding_exit_bucket_attribution`, `bucket_type=holding_exit_bucket_attribution`, `bucket_key=mfe_low|missing|held_missing|kospi_trailing_start_take_profit|-|-|-|-|-`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": ["mae_bucket", "held_bucket", "selection_arm", "sector", "theme"], "runtime_effect": false, "sample_status": "waiting_source_field_sample", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 3, "total_count": 3}, "exit_rule": {"coverage_ratio": 1.0, "paths": ["label_fields.exit_reason"], "present_count": 3, "total_count": 3}, "held_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.held_sec"], "present_count": 0, "total_count": 3}, "mae_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.mae_pct"], "present_count": 0, "total_count": 3}, "market_regime": {"coverage_ratio": 1.0, "paths": ["runtime_features.panic_context", "runtime_features.market_regime"], "present_count": 3, "total_count": 3}, "mfe_bucket": {"coverage_ratio": 1.0, "paths": ["label_fields.mfe_pct"], "present_count": 3, "total_count": 3}, "sector": {"coverage_ratio": 0.0, "paths": ["runtime_features.sector"], "present_count": 0, "total_count": 3}, "selection_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.entry_policy"], "present_count": 0, "total_count": 3}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 3, "total_count": 3}, "theme": {"coverage_ratio": 0.0, "paths": ["runtime_features.theme_tags"], "present_count": 0, "total_count": 3}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 5, "bucket_value_held_missing": 1, "bucket_value_missing": 1, "source_field_missing:held_bucket": 1, "source_field_missing:mae_bucket": 1, "source_field_missing:sector": 1, "source_field_missing:selection_arm": 1, "source_field_missing:theme": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 44. `order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_neg_missing_ge_1d_kospi_regime_stop_loss`

- title: Swing LDM source field follow-up: mfe_neg|missing|ge_1d|kospi_regime_stop_loss|-|-|-|-|-
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_decision_matrix`
- lifecycle_stage: `holding_exit`
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
- evidence: `section=holding_exit_bucket_attribution`, `bucket_type=holding_exit_bucket_attribution`, `bucket_key=mfe_neg|missing|ge_1d|kospi_regime_stop_loss|-|-|-|-|-`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": ["mae_bucket", "selection_arm", "sector", "theme"], "runtime_effect": false, "sample_status": "waiting_source_field_sample", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 4, "total_count": 4}, "exit_rule": {"coverage_ratio": 1.0, "paths": ["label_fields.exit_reason"], "present_count": 4, "total_count": 4}, "held_bucket": {"coverage_ratio": 1.0, "paths": ["label_fields.held_sec"], "present_count": 4, "total_count": 4}, "mae_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.mae_pct"], "present_count": 0, "total_count": 4}, "market_regime": {"coverage_ratio": 1.0, "paths": ["runtime_features.panic_context", "runtime_features.market_regime"], "present_count": 4, "total_count": 4}, "mfe_bucket": {"coverage_ratio": 1.0, "paths": ["label_fields.mfe_pct"], "present_count": 4, "total_count": 4}, "sector": {"coverage_ratio": 0.0, "paths": ["runtime_features.sector"], "present_count": 0, "total_count": 4}, "selection_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.entry_policy"], "present_count": 0, "total_count": 4}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 4, "total_count": 4}, "theme": {"coverage_ratio": 0.0, "paths": ["runtime_features.theme_tags"], "present_count": 0, "total_count": 4}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 5, "bucket_value_missing": 1, "source_field_missing:mae_bucket": 1, "source_field_missing:sector": 1, "source_field_missing:selection_arm": 1, "source_field_missing:theme": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 45. `order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_neg_missing_held_missing_kospi_regime_stop_loss`

- title: Swing LDM source field follow-up: mfe_neg|missing|held_missing|kospi_regime_stop_loss|-|-|-|-|-
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_decision_matrix`
- lifecycle_stage: `holding_exit`
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
- evidence: `section=holding_exit_bucket_attribution`, `bucket_type=holding_exit_bucket_attribution`, `bucket_key=mfe_neg|missing|held_missing|kospi_regime_stop_loss|-|-|-|-|-`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": ["mae_bucket", "held_bucket", "selection_arm", "sector", "theme"], "runtime_effect": false, "sample_status": "waiting_source_field_sample", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 7, "total_count": 7}, "exit_rule": {"coverage_ratio": 1.0, "paths": ["label_fields.exit_reason"], "present_count": 7, "total_count": 7}, "held_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.held_sec"], "present_count": 0, "total_count": 7}, "mae_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.mae_pct"], "present_count": 0, "total_count": 7}, "market_regime": {"coverage_ratio": 1.0, "paths": ["runtime_features.panic_context", "runtime_features.market_regime"], "present_count": 7, "total_count": 7}, "mfe_bucket": {"coverage_ratio": 1.0, "paths": ["label_fields.mfe_pct"], "present_count": 7, "total_count": 7}, "sector": {"coverage_ratio": 0.0, "paths": ["runtime_features.sector"], "present_count": 0, "total_count": 7}, "selection_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.entry_policy"], "present_count": 0, "total_count": 7}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 7, "total_count": 7}, "theme": {"coverage_ratio": 0.0, "paths": ["runtime_features.theme_tags"], "present_count": 0, "total_count": 7}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 5, "bucket_value_held_missing": 1, "bucket_value_missing": 1, "source_field_missing:held_bucket": 1, "source_field_missing:mae_bucket": 1, "source_field_missing:sector": 1, "source_field_missing:selection_arm": 1, "source_field_missing:theme": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 46. `order_swing_ldm_holding_exit_holding_exit_bucket_attribution_missing_missing_held_missing_kospi_trailing_start_take_profit`

- title: Swing LDM source field follow-up: missing|missing|held_missing|kospi_trailing_start_take_profit|-|-|-|-|-
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_lifecycle_decision_matrix`
- lifecycle_stage: `holding_exit`
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
- evidence: `section=holding_exit_bucket_attribution`, `bucket_type=holding_exit_bucket_attribution`, `bucket_key=missing|missing|held_missing|kospi_trailing_start_take_profit|-|-|-|-|-`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": ["mfe_bucket", "mae_bucket", "held_bucket", "selection_arm", "sector", "theme"], "runtime_effect": false, "sample_status": "waiting_source_field_sample", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 8, "total_count": 8}, "exit_rule": {"coverage_ratio": 1.0, "paths": ["label_fields.exit_reason"], "present_count": 8, "total_count": 8}, "held_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.held_sec"], "present_count": 0, "total_count": 8}, "mae_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.mae_pct"], "present_count": 0, "total_count": 8}, "market_regime": {"coverage_ratio": 1.0, "paths": ["runtime_features.panic_context", "runtime_features.market_regime"], "present_count": 8, "total_count": 8}, "mfe_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.mfe_pct"], "present_count": 0, "total_count": 8}, "sector": {"coverage_ratio": 0.0, "paths": ["runtime_features.sector"], "present_count": 0, "total_count": 8}, "selection_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.entry_policy"], "present_count": 0, "total_count": 8}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 8, "total_count": 8}, "theme": {"coverage_ratio": 0.0, "paths": ["runtime_features.theme_tags"], "present_count": 0, "total_count": 8}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 5, "bucket_value_held_missing": 1, "bucket_value_missing": 2, "source_field_missing:held_bucket": 1, "source_field_missing:mae_bucket": 1, "source_field_missing:mfe_bucket": 1, "source_field_missing:sector": 1, "source_field_missing:selection_arm": 1, "source_field_missing:theme": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 47. `order_lifecycle_quiet_gap_ai_review_coverage_rollup`

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
- evidence: `quiet_gap_count=255`, `rollup_required_count=255`, `sim_live_connected_quiet_gap_count=4`, `quiet_gap_type_counts={'positive_source_only_keep_collecting': 239, 'absorbed_into_parent_policy': 15, 'parent_conflict_child': 47, 'exclusion_dimension_candidate': 16, 'ai_review_parsed_low_coverage': 1}`, `ai_review_coverage={'status': 'parsed', 'shard_count': 5, 'parsed_shard_count': 2, 'reviewed_candidate_count': 2, 'low_coverage': True}`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: quiet_gap_summary rollup counts remain visible until explicitly resolved.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: Next postclose checklist/workorder should keep quiet_gap_summary visible until the gap is implemented, covered by parent policy, deferred for more sample, or explicitly rejected.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 48. `order_lifecycle_quiet_gap_parent_conflict_rollup`

- title: Lifecycle quiet gap parent conflict/exclusion review
- decision: `attach_existing_family`
- decision_reason: quiet gap rollup is visibility evidence for parent conflict/source-only/AI coverage review; it does not authorize a runtime patch by itself
- source_report_type: `lifecycle_bucket_discovery_quiet_gap_rollup`
- lifecycle_stage: `multi_stage`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `parent_conflict_exclusion_review`
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
- evidence: `quiet_gap_count=255`, `rollup_required_count=255`, `sim_live_connected_quiet_gap_count=4`, `quiet_gap_type_counts={'positive_source_only_keep_collecting': 239, 'absorbed_into_parent_policy': 15, 'parent_conflict_child': 47, 'exclusion_dimension_candidate': 16, 'ai_review_parsed_low_coverage': 1}`, `ai_review_coverage={'status': 'parsed', 'shard_count': 5, 'parsed_shard_count': 2, 'reviewed_candidate_count': 2, 'low_coverage': True}`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: quiet_gap_summary rollup counts remain visible until explicitly resolved.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: Next postclose checklist/workorder should keep quiet_gap_summary visible until the gap is implemented, covered by parent policy, deferred for more sample, or explicitly rejected.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 49. `order_lifecycle_quiet_gap_positive_source_only_rollup`

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
- evidence: `quiet_gap_count=255`, `rollup_required_count=255`, `sim_live_connected_quiet_gap_count=4`, `quiet_gap_type_counts={'positive_source_only_keep_collecting': 239, 'absorbed_into_parent_policy': 15, 'parent_conflict_child': 47, 'exclusion_dimension_candidate': 16, 'ai_review_parsed_low_coverage': 1}`, `ai_review_coverage={'status': 'parsed', 'shard_count': 5, 'parsed_shard_count': 2, 'reviewed_candidate_count': 2, 'low_coverage': True}`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: quiet_gap_summary rollup counts remain visible until explicitly resolved.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: Next postclose checklist/workorder should keep quiet_gap_summary visible until the gap is implemented, covered by parent policy, deferred for more sample, or explicitly rejected.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 50. `order_lifecycle_source_dimension_gap_rollup`

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
- evidence: `rollup_only_gap_count=54`, `unknown_source_dimensions=10`, `recommended_resolution_counts={'explicit_lifecycle_flow_source_only_blocker': 44, 'entry_label_not_applicable': 1, 'mark_not_applicable_explicitly': 5, 'join_labels_before_bucket_decision': 4}`, `missing_dimension_key_counts={'entry': 50, 'exit': 46, 'holding': 52, 'submit': 62}`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: source_dimension_gap_summary rollup/actionable counts remain visible.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: Next postclose checklist/workorder should keep source_dimension_gap_summary visible until actionable gaps are resolved or explicitly marked not applicable.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 51. `order_lifecycle_overnight_bucket_confidence_band_confidence_070p`

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
- evidence: `workorder_id=overnight_bucket_source_quality_1`, `bucket_type=confidence_band`, `bucket_key=confidence_070p`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.overnight_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/scalp_sim_overnight.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM overnight bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": null, "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 52. `order_lifecycle_overnight_bucket_overnight_action_sell_today`

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
- evidence: `workorder_id=overnight_bucket_source_quality_2`, `bucket_type=overnight_action`, `bucket_key=SELL_TODAY`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.overnight_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/scalp_sim_overnight.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM overnight bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": null, "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 53. `order_lifecycle_overnight_bucket_overnight_status_sell_today`

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
- evidence: `workorder_id=overnight_bucket_source_quality_3`, `bucket_type=overnight_status`, `bucket_key=SELL_TODAY`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.overnight_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/scalp_sim_overnight.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM overnight bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": null, "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 54. `order_lifecycle_overnight_bucket_peak_profit_band_peak_lt_zero`

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
- evidence: `workorder_id=overnight_bucket_source_quality_4`, `bucket_type=peak_profit_band`, `bucket_key=peak_lt_zero`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.overnight_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/scalp_sim_overnight.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM overnight bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": null, "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 55. `order_lifecycle_overnight_bucket_price_source_holding_price_samples_last`

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
- evidence: `workorder_id=overnight_bucket_source_quality_5`, `bucket_type=price_source`, `bucket_key=holding_price_samples_last`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.overnight_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/scalp_sim_overnight.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM overnight bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": null, "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 56. `order_lifecycle_overnight_bucket_source_quality_gate_overnight_decision_coverage`

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
- evidence: `workorder_id=overnight_bucket_source_quality_6`, `bucket_type=source_quality_gate`, `bucket_key=overnight_decision_coverage`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.overnight_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/scalp_sim_overnight.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM overnight bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": null, "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 57. `order_lifecycle_overnight_bucket_source_stage_scalp_sim_overnight_sell_today`

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
- evidence: `workorder_id=overnight_bucket_source_quality_7`, `bucket_type=source_stage`, `bucket_key=scalp_sim_overnight_sell_today`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.overnight_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/scalp_sim_overnight.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM overnight bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": null, "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 58. `order_lifecycle_overnight_bucket_stage_exit`

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
- evidence: `workorder_id=overnight_bucket_source_quality_8`, `bucket_type=stage`, `bucket_key=exit`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.overnight_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/scalp_sim_overnight.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM overnight bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": null, "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 59. `order_lifecycle_scale_in_bucket_ai_score_band_score_60_62`

- title: LDM scale-in bucket attribution follow-up: ai_score_band=score_60_62
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_scale_in_bucket_attribution`
- lifecycle_stage: `scale_in`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `scale_in_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Separate AVG_DOWN/PYRAMID attribution and keep scale-in threshold/cap candidates as source-only evidence until rolling confirmation and approval artifact.
- evidence: `workorder_id=scale_in_bucket_source_quality_2`, `bucket_type=ai_score_band`, `bucket_key=score_60_62`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.scale_in_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM scale-in bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 60. `order_lifecycle_scale_in_bucket_ai_score_band_score_63_65`

- title: LDM scale-in bucket attribution follow-up: ai_score_band=score_63_65
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_scale_in_bucket_attribution`
- lifecycle_stage: `scale_in`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `scale_in_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Separate AVG_DOWN/PYRAMID attribution and keep scale-in threshold/cap candidates as source-only evidence until rolling confirmation and approval artifact.
- evidence: `workorder_id=scale_in_bucket_source_quality_3`, `bucket_type=ai_score_band`, `bucket_key=score_63_65`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.scale_in_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM scale-in bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 61. `order_lifecycle_scale_in_bucket_ai_score_band_score_70p`

- title: LDM scale-in bucket attribution follow-up: ai_score_band=score_70p
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_scale_in_bucket_attribution`
- lifecycle_stage: `scale_in`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `scale_in_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Separate AVG_DOWN/PYRAMID attribution and keep scale-in threshold/cap candidates as source-only evidence until rolling confirmation and approval artifact.
- evidence: `workorder_id=scale_in_bucket_source_quality_1`, `bucket_type=ai_score_band`, `bucket_key=score_70p`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.scale_in_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM scale-in bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 62. `order_lifecycle_scale_in_bucket_ai_score_band_score_lt60`

- title: LDM scale-in bucket attribution follow-up: ai_score_band=score_lt60
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_scale_in_bucket_attribution`
- lifecycle_stage: `scale_in`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `scale_in_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Separate AVG_DOWN/PYRAMID attribution and keep scale-in threshold/cap candidates as source-only evidence until rolling confirmation and approval artifact.
- evidence: `workorder_id=scale_in_bucket_source_quality_4`, `bucket_type=ai_score_band`, `bucket_key=score_lt60`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.scale_in_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM scale-in bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 63. `order_lifecycle_scale_in_bucket_ai_score_source_score_field_backfilled`

- title: LDM scale-in bucket attribution follow-up: ai_score_source=score_field_backfilled
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_scale_in_bucket_attribution`
- lifecycle_stage: `scale_in`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `scale_in_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Separate AVG_DOWN/PYRAMID attribution and keep scale-in threshold/cap candidates as source-only evidence until rolling confirmation and approval artifact.
- evidence: `workorder_id=scale_in_bucket_source_quality_5`, `bucket_type=ai_score_source`, `bucket_key=score_field_backfilled`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.scale_in_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM scale-in bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 64. `order_lifecycle_scale_in_bucket_arm_avg_down`

- title: LDM scale-in bucket attribution follow-up: arm=AVG_DOWN
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_scale_in_bucket_attribution`
- lifecycle_stage: `scale_in`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `scale_in_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Separate AVG_DOWN/PYRAMID attribution and keep scale-in threshold/cap candidates as source-only evidence until rolling confirmation and approval artifact.
- evidence: `workorder_id=scale_in_bucket_source_quality_6`, `bucket_type=arm`, `bucket_key=AVG_DOWN`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.scale_in_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM scale-in bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 65. `order_lifecycle_scale_in_bucket_arm_pyramid`

- title: LDM scale-in bucket attribution follow-up: arm=PYRAMID
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_scale_in_bucket_attribution`
- lifecycle_stage: `scale_in`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `scale_in_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Separate AVG_DOWN/PYRAMID attribution and keep scale-in threshold/cap candidates as source-only evidence until rolling confirmation and approval artifact.
- evidence: `workorder_id=scale_in_bucket_source_quality_7`, `bucket_type=arm`, `bucket_key=PYRAMID`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.scale_in_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM scale-in bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 66. `order_lifecycle_scale_in_bucket_blocker_namespace_avg_down`

- title: LDM scale-in bucket attribution follow-up: blocker_namespace=AVG_DOWN
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_scale_in_bucket_attribution`
- lifecycle_stage: `scale_in`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `scale_in_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Separate AVG_DOWN/PYRAMID attribution and keep scale-in threshold/cap candidates as source-only evidence until rolling confirmation and approval artifact.
- evidence: `workorder_id=scale_in_bucket_source_quality_8`, `bucket_type=blocker_namespace`, `bucket_key=AVG_DOWN`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.scale_in_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM scale-in bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 67. `order_lifecycle_scale_in_bucket_blocker_namespace_avg_down_only`

- title: LDM scale-in bucket attribution follow-up: blocker_namespace=AVG_DOWN_ONLY
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_scale_in_bucket_attribution`
- lifecycle_stage: `scale_in`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `scale_in_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Separate AVG_DOWN/PYRAMID attribution and keep scale-in threshold/cap candidates as source-only evidence until rolling confirmation and approval artifact.
- evidence: `workorder_id=scale_in_bucket_source_quality_10`, `bucket_type=blocker_namespace`, `bucket_key=AVG_DOWN_ONLY`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.scale_in_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM scale-in bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 68. `order_lifecycle_scale_in_bucket_blocker_namespace_pyramid`

- title: LDM scale-in bucket attribution follow-up: blocker_namespace=PYRAMID
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_scale_in_bucket_attribution`
- lifecycle_stage: `scale_in`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `scale_in_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Separate AVG_DOWN/PYRAMID attribution and keep scale-in threshold/cap candidates as source-only evidence until rolling confirmation and approval artifact.
- evidence: `workorder_id=scale_in_bucket_source_quality_9`, `bucket_type=blocker_namespace`, `bucket_key=PYRAMID`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.scale_in_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM scale-in bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 69. `order_conversion_lane_key_lineage_active_arm_0c383886ae3c8de3`

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
- priority: `5`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_0c383886ae3c8de3`, `blocker_class=key_lineage`, `conversion_impact_rank=5`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 70. `order_lifecycle_entry_bucket_chosen_action_buy_now`

- title: LDM entry bucket attribution follow-up: chosen_action=BUY_NOW
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
- evidence: `workorder_id=entry_bucket_unknown_source_quality_2`, `bucket_type=chosen_action`, `bucket_key=BUY_NOW`, `reason=unknown_bucket_source_quality_blocker`, `recommended_route=source_quality_workorder`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_dimension_counts": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 71. `order_lifecycle_entry_bucket_chosen_action_no_buy_ai`

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
- evidence: `workorder_id=entry_bucket_unknown_source_quality_1`, `bucket_type=chosen_action`, `bucket_key=NO_BUY_AI`, `reason=unknown_bucket_source_quality_blocker`, `recommended_route=source_quality_workorder`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_dimension_counts": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 72. `order_lifecycle_entry_bucket_chosen_action_wait_requote`

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
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 73. `order_lifecycle_entry_bucket_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale_fresh_liquid`

- title: LDM entry bucket attribution follow-up: combo_entry_spot=score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000
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
- evidence: `workorder_id=entry_bucket_unknown_source_quality_3`, `bucket_type=combo_entry_spot`, `bucket_key=score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000`, `reason=unknown_bucket_source_quality_blocker`, `recommended_route=source_quality_workorder`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_dimension_counts": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 74. `order_lifecycle_entry_bucket_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale_stale_watch_`

- title: LDM entry bucket attribution follow-up: combo_entry_spot=score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000
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
- evidence: `workorder_id=entry_bucket_unknown_source_quality_7`, `bucket_type=combo_entry_spot`, `bucket_key=score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000`, `reason=unknown_bucket_source_quality_blocker`, `recommended_route=source_quality_workorder`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_dimension_counts": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 75. `order_lifecycle_entry_bucket_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_fresh_liquidit`

- title: LDM entry bucket attribution follow-up: combo_entry_spot=score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000
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
- evidence: `workorder_id=entry_bucket_unknown_source_quality_8`, `bucket_type=combo_entry_spot`, `bucket_key=score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000`, `reason=unknown_bucket_source_quality_blocker`, `recommended_route=source_quality_workorder`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_dimension_counts": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 76. `order_lifecycle_entry_bucket_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_fresh_liquidi`

- title: LDM entry bucket attribution follow-up: combo_entry_spot=score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000
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
- evidence: `workorder_id=entry_bucket_unknown_source_quality_10`, `bucket_type=combo_entry_spot`, `bucket_key=score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000`, `reason=unknown_bucket_source_quality_blocker`, `recommended_route=source_quality_workorder`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_dimension_counts": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 77. `order_lifecycle_entry_bucket_liquidity_bucket_liquidity_high`

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
- evidence: `workorder_id=entry_bucket_source_quality_2`, `bucket_type=liquidity_bucket`, `bucket_key=liquidity_high`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 78. `order_lifecycle_entry_bucket_overbought_bucket_overbought_watch`

- title: LDM entry bucket attribution follow-up: overbought_bucket=overbought_watch
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
- evidence: `workorder_id=entry_bucket_source_quality_3`, `bucket_type=overbought_bucket`, `bucket_key=overbought_watch`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 79. `order_lifecycle_entry_bucket_source_stage_wait6579_ev_cohort`

- title: LDM entry bucket attribution follow-up: source_stage=wait6579_ev_cohort
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
- evidence: `workorder_id=entry_bucket_source_quality_4`, `bucket_type=source_stage`, `bucket_key=wait6579_ev_cohort`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 80. `order_lifecycle_entry_bucket_stale_bucket_fresh_or_unflagged`

- title: LDM entry bucket attribution follow-up: stale_bucket=fresh_or_unflagged
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
- evidence: `workorder_id=entry_bucket_source_quality_5`, `bucket_type=stale_bucket`, `bucket_key=fresh_or_unflagged`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 81. `order_lifecycle_entry_bucket_strength_bucket_strong_strength_momentum`

- title: LDM entry bucket attribution follow-up: strength_bucket=strong_strength_momentum
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
- evidence: `workorder_id=entry_bucket_source_quality_6`, `bucket_type=strength_bucket`, `bucket_key=strong_strength_momentum`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 82. `order_conversion_lane_key_lineage_active_arm_342af4565cfdbf29`

- title: Conversion lane blocker follow-up: key_lineage active_arm_342af4565cfdbf29
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
- priority: `6`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_342af4565cfdbf29`, `blocker_class=key_lineage`, `conversion_impact_rank=6`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 83. `order_conversion_lane_key_lineage_active_arm_790e3894639690bd`

- title: Conversion lane blocker follow-up: key_lineage active_arm_790e3894639690bd
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
- priority: `7`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_790e3894639690bd`, `blocker_class=key_lineage`, `conversion_impact_rank=7`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 84. `order_conversion_lane_key_lineage_active_arm_7bc3260124b31b77`

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
- priority: `8`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_7bc3260124b31b77`, `blocker_class=key_lineage`, `conversion_impact_rank=8`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 85. `order_conversion_lane_key_lineage_active_arm_83b3cc10ef194674`

- title: Conversion lane blocker follow-up: key_lineage active_arm_83b3cc10ef194674
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
- priority: `9`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_83b3cc10ef194674`, `blocker_class=key_lineage`, `conversion_impact_rank=9`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 86. `order_conversion_lane_key_lineage_active_arm_d105ea417d1883a6`

- title: Conversion lane blocker follow-up: key_lineage active_arm_d105ea417d1883a6
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
- priority: `10`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_d105ea417d1883a6`, `blocker_class=key_lineage`, `conversion_impact_rank=10`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 87. `order_pattern_lab_ai_review_code_improvement_workorder_duplicate_orders`

- title: Pattern Lab AI review follow-up: code_improvement_workorder_duplicate_orders
- decision: `attach_existing_family`
- decision_reason: Pattern Lab AI review automation_handoff_gap is coverage evidence for the currentness handoff workorders; do not create duplicate implement_now items from the reviewer layer
- source_report_type: `pattern_lab_ai_review`
- lifecycle_stage: `pattern_lab_ai_review`
- target_subsystem: `pattern_lab`
- route: `pattern_lab_ai_review_handoff_evidence`
- mapped_family: `pattern_lab_feedback_handoff`
- threshold_family: `pattern_lab_feedback_handoff`
- improvement_type: `automation_handoff_gap`
- confidence: `ai_two_pass_review`
- priority: `10`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `True`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve pattern lab feedback quality without runtime mutation.
- evidence: `review_id=code_improvement_workorder_duplicate_orders`, `domain=cross_domain`, `final_state=automation_handoff_gap`, `final_decision=block_runtime_use`, `auditor_pass=False`, `explicit_gap_type=automation_handoff_gap`, `source_paths=['/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-06-08.json']`
- parity_contract: -
- next_postclose_metric: pattern_lab_ai_review.code_improvement_workorder_duplicate_orders
- files_likely_touched: `src/engine/pattern_lab_ai_review.py`, `src/engine/pattern_lab_currentness_audit.py`, `analysis/gemini_scalping_pattern_lab`, `analysis/claude_scalping_pattern_lab`, `analysis/deepseek_swing_pattern_lab`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_ai_review.py src/tests/test_pattern_lab_currentness_audit.py`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: Keep as source-quality blocker evidence until pattern_lab_currentness_audit handoff orders close and the regenerated AI review parses sufficient context.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 88. `order_pattern_lab_ai_review_lifecycle_bucket_discovery_source_contract_drift`

- title: Pattern Lab AI review follow-up: lifecycle_bucket_discovery_source_contract_drift
- decision: `attach_existing_family`
- decision_reason: Pattern Lab AI review automation_handoff_gap is coverage evidence for the currentness handoff workorders; do not create duplicate implement_now items from the reviewer layer
- source_report_type: `pattern_lab_ai_review`
- lifecycle_stage: `pattern_lab_ai_review`
- target_subsystem: `pattern_lab`
- route: `pattern_lab_ai_review_handoff_evidence`
- mapped_family: `pattern_lab_feedback_handoff`
- threshold_family: `pattern_lab_feedback_handoff`
- improvement_type: `automation_handoff_gap`
- confidence: `ai_two_pass_review`
- priority: `10`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `True`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve pattern lab feedback quality without runtime mutation.
- evidence: `review_id=lifecycle_bucket_discovery_source_contract_drift`, `domain=cross_domain`, `final_state=automation_handoff_gap`, `final_decision=block_runtime_use`, `auditor_pass=False`, `explicit_gap_type=automation_handoff_gap`, `source_paths=['/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-06-08.json']`
- parity_contract: -
- next_postclose_metric: pattern_lab_ai_review.lifecycle_bucket_discovery_source_contract_drift
- files_likely_touched: `src/engine/pattern_lab_ai_review.py`, `src/engine/pattern_lab_currentness_audit.py`, `analysis/gemini_scalping_pattern_lab`, `analysis/claude_scalping_pattern_lab`, `analysis/deepseek_swing_pattern_lab`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_ai_review.py src/tests/test_pattern_lab_currentness_audit.py`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: Keep as source-quality blocker evidence until pattern_lab_currentness_audit handoff orders close and the regenerated AI review parses sufficient context.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 89. `order_pattern_lab_ai_review_swing_lifecycle_decision_matrix_pending_quotes`

- title: Pattern Lab AI review follow-up: swing_lifecycle_decision_matrix_pending_quotes
- decision: `attach_existing_family`
- decision_reason: Pattern Lab AI review automation_handoff_gap is coverage evidence for the currentness handoff workorders; do not create duplicate implement_now items from the reviewer layer
- source_report_type: `pattern_lab_ai_review`
- lifecycle_stage: `pattern_lab_ai_review`
- target_subsystem: `pattern_lab`
- route: `pattern_lab_ai_review_handoff_evidence`
- mapped_family: `pattern_lab_feedback_handoff`
- threshold_family: `pattern_lab_feedback_handoff`
- improvement_type: `automation_handoff_gap`
- confidence: `ai_two_pass_review`
- priority: `10`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `True`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve pattern lab feedback quality without runtime mutation.
- evidence: `review_id=swing_lifecycle_decision_matrix_pending_quotes`, `domain=swing`, `final_state=automation_handoff_gap`, `final_decision=block_runtime_use`, `auditor_pass=False`, `explicit_gap_type=automation_handoff_gap`, `source_paths=['/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-06-08.json']`
- parity_contract: -
- next_postclose_metric: pattern_lab_ai_review.swing_lifecycle_decision_matrix_pending_quotes
- files_likely_touched: `src/engine/pattern_lab_ai_review.py`, `src/engine/pattern_lab_currentness_audit.py`, `analysis/gemini_scalping_pattern_lab`, `analysis/claude_scalping_pattern_lab`, `analysis/deepseek_swing_pattern_lab`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_ai_review.py src/tests/test_pattern_lab_currentness_audit.py`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: Keep as source-quality blocker evidence until pattern_lab_currentness_audit handoff orders close and the regenerated AI review parses sufficient context.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 90. `order_pattern_lab_ai_review_swing_pattern_lab_automation_source_quality`

- title: Pattern Lab AI review follow-up: swing_pattern_lab_automation_source_quality
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
- evidence: `review_id=swing_pattern_lab_automation_source_quality`, `domain=swing`, `final_state=source_quality_gap`, `final_decision=block_runtime_use`, `auditor_pass=False`, `explicit_gap_type=source_quality_gap`, `source_paths=['/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-06-08.json']`
- parity_contract: -
- next_postclose_metric: pattern_lab_ai_review.swing_pattern_lab_automation_source_quality
- files_likely_touched: `src/engine/pattern_lab_ai_review.py`, `src/engine/pattern_lab_currentness_audit.py`, `analysis/gemini_scalping_pattern_lab`, `analysis/claude_scalping_pattern_lab`, `analysis/deepseek_swing_pattern_lab`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_ai_review.py src/tests/test_pattern_lab_currentness_audit.py`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocked_families": [{"family": "swing_entry_ofi_qi_execution_quality", "invalid_micro_context_unique_record_count": 22, "runtime_effect": false, "source_quality_blockers": ["entry_ofi_qi_invalid_micro_context"], "stage": "entry"}, {"family": "swing_scale_in_ofi_qi_confirmation", "invalid_micro_context_unique_record_count": 2, "runtime_effect": false, "source_quality_blockers": ["scale_in_ofi_qi_invalid_micro_context"], "stage": "scale_in"}], "blocked_family_count": 2, "decision_authority": "swing_pattern_lab_analysis_workorder_source_only", "implementation_type": "source_quality_report_provenance", "ofi_qi_reason_counts": {"micro_missing": 16275, "micro_not_ready": 16249, "micro_stale": 0, "observer_unhealthy": 3563, "state_insufficient": 16249}, "runtime_effect": false, "source_report_type": "swing_pattern_lab_automation"}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 91. `order_pattern_lab_ai_review_threshold_cycle_ev_missing_feedback`

- title: Pattern Lab AI review follow-up: threshold_cycle_ev_missing_feedback
- decision: `attach_existing_family`
- decision_reason: Pattern Lab AI review automation_handoff_gap is coverage evidence for the currentness handoff workorders; do not create duplicate implement_now items from the reviewer layer
- source_report_type: `pattern_lab_ai_review`
- lifecycle_stage: `pattern_lab_ai_review`
- target_subsystem: `pattern_lab`
- route: `pattern_lab_ai_review_handoff_evidence`
- mapped_family: `pattern_lab_feedback_handoff`
- threshold_family: `pattern_lab_feedback_handoff`
- improvement_type: `automation_handoff_gap`
- confidence: `ai_two_pass_review`
- priority: `10`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `True`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve pattern lab feedback quality without runtime mutation.
- evidence: `review_id=threshold_cycle_ev_missing_feedback`, `domain=cross_domain`, `final_state=automation_handoff_gap`, `final_decision=block_runtime_use`, `auditor_pass=False`, `explicit_gap_type=automation_handoff_gap`, `source_paths=['/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-06-08.json', '/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-06-08.json']`
- parity_contract: -
- next_postclose_metric: pattern_lab_ai_review.threshold_cycle_ev_missing_feedback
- files_likely_touched: `src/engine/pattern_lab_ai_review.py`, `src/engine/pattern_lab_currentness_audit.py`, `analysis/gemini_scalping_pattern_lab`, `analysis/claude_scalping_pattern_lab`, `analysis/deepseek_swing_pattern_lab`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_ai_review.py src/tests/test_pattern_lab_currentness_audit.py`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: Keep as source-quality blocker evidence until pattern_lab_currentness_audit handoff orders close and the regenerated AI review parses sufficient context.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 92. `order_conversion_lane_key_lineage_active_arm_d7bb9da5df1a251d`

- title: Conversion lane blocker follow-up: key_lineage active_arm_d7bb9da5df1a251d
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
- priority: `11`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_d7bb9da5df1a251d`, `blocker_class=key_lineage`, `conversion_impact_rank=11`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 93. `order_conversion_lane_key_lineage_active_arm_da294c8705564eaf`

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
- priority: `12`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_da294c8705564eaf`, `blocker_class=key_lineage`, `conversion_impact_rank=12`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 94. `order_conversion_lane_key_lineage_active_seed_0a9736d86332c717`

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
- priority: `13`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_0a9736d86332c717`, `blocker_class=key_lineage`, `conversion_impact_rank=13`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 95. `order_conversion_lane_key_lineage_active_seed_0cae3a2115d07d28`

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
- priority: `14`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_0cae3a2115d07d28`, `blocker_class=key_lineage`, `conversion_impact_rank=14`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 96. `order_conversion_lane_key_lineage_active_seed_1096e7d8ada1ee8a`

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
- priority: `15`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_1096e7d8ada1ee8a`, `blocker_class=key_lineage`, `conversion_impact_rank=15`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 97. `order_conversion_lane_key_lineage_active_seed_109a6ab7807c9624`

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
- priority: `16`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_109a6ab7807c9624`, `blocker_class=key_lineage`, `conversion_impact_rank=16`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 98. `order_conversion_lane_key_lineage_active_seed_1307cd5fa2e96df9`

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
- priority: `17`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_1307cd5fa2e96df9`, `blocker_class=key_lineage`, `conversion_impact_rank=17`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 99. `order_conversion_lane_key_lineage_active_seed_24a139dfb60cb311`

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
- priority: `18`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_24a139dfb60cb311`, `blocker_class=key_lineage`, `conversion_impact_rank=18`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 100. `order_conversion_lane_key_lineage_active_seed_46465cc508b01988`

- title: Conversion lane blocker follow-up: key_lineage active_seed_46465cc508b01988
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
- priority: `19`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_46465cc508b01988`, `blocker_class=key_lineage`, `conversion_impact_rank=19`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 101. `order_conversion_lane_key_lineage_active_seed_760c98186c8de610`

- title: Conversion lane blocker follow-up: key_lineage active_seed_760c98186c8de610
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
- priority: `20`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_760c98186c8de610`, `blocker_class=key_lineage`, `conversion_impact_rank=20`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 102. `order_conversion_lane_key_lineage_active_seed_7cf1c198fc1e5246`

- title: Conversion lane blocker follow-up: key_lineage active_seed_7cf1c198fc1e5246
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
- priority: `21`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_7cf1c198fc1e5246`, `blocker_class=key_lineage`, `conversion_impact_rank=21`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 103. `order_conversion_lane_key_lineage_active_seed_afa0c4f1bdf63001`

- title: Conversion lane blocker follow-up: key_lineage active_seed_afa0c4f1bdf63001
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
- priority: `22`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_afa0c4f1bdf63001`, `blocker_class=key_lineage`, `conversion_impact_rank=22`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 104. `order_conversion_lane_key_lineage_active_seed_bef67812d7545625`

- title: Conversion lane blocker follow-up: key_lineage active_seed_bef67812d7545625
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
- priority: `23`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_bef67812d7545625`, `blocker_class=key_lineage`, `conversion_impact_rank=23`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 105. `order_conversion_lane_key_lineage_active_seed_c332627f82811a7c`

- title: Conversion lane blocker follow-up: key_lineage active_seed_c332627f82811a7c
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
- priority: `24`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_seed_c332627f82811a7c`, `blocker_class=key_lineage`, `conversion_impact_rank=24`, `next_repair_action=key_lineage_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 106. `order_pattern_lab_ai_review_ai_review_followup_2026_06_08`

- title: Resolve Pattern Lab AI review follow-up
- decision: `defer_evidence`
- decision_reason: Pattern Lab generic ai_review_followup is reviewer evidence for concrete source-quality or handoff orders; do not duplicate it as a Codex implement_now item
- source_report_type: `pattern_lab_ai_review`
- lifecycle_stage: `-`
- target_subsystem: `pattern_lab_ai_review`
- route: `pattern_lab_ai_review_followup_evidence`
- mapped_family: `pattern_lab_feedback_handoff`
- threshold_family: `pattern_lab_feedback_handoff`
- improvement_type: `ai_review_followup`
- confidence: `parsed_ai_review_followup`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `True`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve Pattern Lab feedback/source-quality handling without runtime mutation.
- evidence: `ai_review_followup_reason=audit_status_correction_required`, `audit_status=correction_required`, `audit_issues=['Missing second-pass audit results from pattern_lab_ai_review. First-pass interpretation exists but final conclusions with re-ranking against LDM/threshold feedback are not present in inputs.']`, `forbidden_use_violations=[]`
- parity_contract: -
- next_postclose_metric: pattern_lab_ai_review.ai_review_followup
- files_likely_touched: `src/engine/pattern_lab_ai_review.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_ai_review.py src/tests/test_build_code_improvement_workorder.py`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: Keep as terminal review evidence until the concrete source-quality/handoff orders and regenerated Pattern Lab AI review close the audit.

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
- implementation_status: `-`
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
- implementation_status: `-`
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

### N9. `order_swing_market_regime_sensitivity_review`

- title: swing market regime sensitivity review
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `swing_improvement_automation`
- lifecycle_stage: `entry`
- target_subsystem: `swing_entry`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `-`
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/swing_lifecycle_audit.py`
- acceptance_tests: `pytest swing lifecycle audit tests`

### N10. `order_swing_ofi_qi_stale_or_missing_context`

- title: swing OFI/QI stale or missing context
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `swing_improvement_automation`
- lifecycle_stage: `entry`
- target_subsystem: `swing_orderbook_micro_context`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `-`
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/orderbook_stability.py`, `src/engine/swing_lifecycle_audit.py`
- acceptance_tests: `pytest orderbook stability tests`, `pytest swing lifecycle audit tests`

### N11. `order_swing_pattern_lab_deepseek_ofi_qi_stale_missing`

- title: OFI/QI stale/missing quality review
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_pattern_lab_automation`
- lifecycle_stage: `ofi_qi`
- target_subsystem: `swing_micro_context`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented`
- files_likely_touched: `src/engine/swing_lifecycle_audit.py`, `src/engine/swing_selection_funnel_report.py`, `src/model/common_v2.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_model_selection_funnel_repair.py`, `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_deepseek_swing_pattern_lab.py`

### N12. `order_swing_scale_in_contract_gap_review`

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

### N13. `order_perf_swing_simulation_iteration`

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

### N14. `order_swing_discovery_label_contract_gap_review`

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

### N15. `order_swing_scale_in_ofi_qi_bearish_risk_review`

- title: swing scale-in OFI/QI bearish risk review
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `swing_improvement_automation`
- lifecycle_stage: `scale_in`
- target_subsystem: `swing_scale_in`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `-`
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/swing_lifecycle_audit.py`
- acceptance_tests: `pytest sniper scale-in tests`, `pytest swing lifecycle audit tests`

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
- files_likely_touched: `src/engine/panic_sell_defense_report.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/plan-korStockScanPerformanceOptimization.rebase.md`
- acceptance_tests: `pytest panic sell defense/report lifecycle tests`, `pytest src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py`

### N17. `order_perf_monitor_snapshot_stream_tail`

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

### N18. `order_swing_exit_ofi_qi_smoothing_distribution`

- title: swing exit OFI/QI smoothing distribution
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `swing_improvement_automation`
- lifecycle_stage: `holding_exit`
- target_subsystem: `swing_holding_exit`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `-`
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/swing_lifecycle_audit.py`
- acceptance_tests: `pytest OFI smoothing tests`, `pytest swing lifecycle audit tests`

### N19. `order_swing_strategy_discovery_source_quality_followup`

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

### N20. `order_panic_buying_source_quality_market_breadth_micro_coverage`

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

### N21. `order_perf_final_ensemble_records`

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

### N22. `order_swing_strategy_discovery_avoid_bucket_review`

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

### N23. `order_swing_pattern_lab_deepseek_entry_no_submissions`

- title: All selected candidates failed to reach order submission
- decision: `design_family_candidate`
- decision_reason: pattern lab can only propose source-only family design input; LDM/discovery/runtime bridge contracts must close before any auto_bounded_live consideration
- source_report_type: `swing_pattern_lab_automation`
- lifecycle_stage: `entry`
- target_subsystem: `swing_entry_funnel`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `-`
- files_likely_touched: `src/engine/swing_lifecycle_audit.py`, `src/engine/swing_selection_funnel_report.py`, `src/model/common_v2.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_model_selection_funnel_repair.py`, `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_deepseek_swing_pattern_lab.py`

### N24. `order_no_acute_observability_alert`

- title: No acute observability alert
- decision: `design_family_candidate`
- decision_reason: pattern lab can only propose source-only family design input; LDM/discovery/runtime bridge contracts must close before any auto_bounded_live consideration
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `scalping_logic`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N25. `order_liquidity_gate_miss_ev_recovery`

- title: liquidity gate miss EV recovery
- decision: `design_family_candidate`
- decision_reason: pattern lab can only propose source-only family design input; LDM/discovery/runtime bridge contracts must close before any auto_bounded_live consideration
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `entry_filter_quality`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N26. `order_swing_ai_contract_structured_output_eval`

- title: swing AI contract structured output eval
- decision: `design_family_candidate`
- decision_reason: finding needs family design; allowed_runtime_apply remains false until metadata/tests/guards are closed
- source_report_type: `swing_improvement_automation`
- lifecycle_stage: `ai_contract`
- target_subsystem: `swing_ai_contract`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `-`
- files_likely_touched: `src/engine/ai_prompt_contracts.py`, `src/engine/ai_engine_openai.py`, `src/engine/ai_response_contracts.py`
- acceptance_tests: `pytest OpenAI transport/schema tests`, `pytest swing lifecycle audit tests`

### N27. `order_overbought_gate_miss_ev_recovery`

- title: overbought gate miss EV recovery
- decision: `design_family_candidate`
- decision_reason: pattern lab can only propose source-only family design input; LDM/discovery/runtime bridge contracts must close before any auto_bounded_live consideration
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `entry_filter_quality`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N28. `order_ai_threshold_miss_ev_recovery`

- title: AI threshold miss EV recovery
- decision: `defer_evidence`
- decision_reason: single-lab finding; keep as low-confidence backlog until repeated by fresh lab or EV report
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `entry_funnel`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_missed_entry_counterfactual.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N29. `order_swing_pattern_lab_deepseek_ofi_qi_smoothing_review`

- title: OFI/QI exit smoothing action distribution
- decision: `defer_evidence`
- decision_reason: single-lab finding; keep as low-confidence backlog until repeated by fresh lab or EV report
- source_report_type: `swing_pattern_lab_automation`
- lifecycle_stage: `ofi_qi`
- target_subsystem: `swing_micro_context`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `-`
- files_likely_touched: `src/engine/swing_lifecycle_audit.py`, `src/engine/swing_selection_funnel_report.py`, `src/model/common_v2.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_model_selection_funnel_repair.py`, `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_deepseek_swing_pattern_lab.py`

### N30. `order_동일_종목_split_entry_soft_stop_재진입_cooldown_report_only`

- title: 동일 종목 split-entry soft-stop 재진입 cooldown report-only
- decision: `defer_evidence`
- decision_reason: single-lab finding; keep as low-confidence backlog until repeated by fresh lab or EV report
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `holding_exit`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N31. `order_perf_kiwoom_orders_http_session_review`

- title: Kiwoom orders HTTP session reuse manual review
- decision: `defer_evidence`
- decision_reason: broker request lifecycle may change; requires manual review before implementation
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `broker_transport`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `-`
- files_likely_touched: `src/engine/kiwoom_orders.py`
- acceptance_tests: `pytest src/tests/test_kiwoom_orders.py src/tests/test_sniper_scale_in.py`

### N32. `order_perf_config_cache_scope_review`

- title: Config cache scope review
- decision: `defer_evidence`
- decision_reason: runtime config reload semantics are not yet bounded
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `config_loading`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `-`
- files_likely_touched: `src/utils/constants.py`, `src/utils/kiwoom_utils.py`
- acceptance_tests: `pytest config/import smoke tests`

### N33. `order_perf_dashboard_db_pool_review`

- title: Legacy dashboard DB connection pool review
- decision: `defer_evidence`
- decision_reason: legacy DB write is opt-in and pool lifetime risk needs separate review
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `dashboard_legacy_db`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `-`
- files_likely_touched: `src/engine/dashboard_data_repository.py`
- acceptance_tests: `pytest src/tests/test_dashboard_data_repository.py`

### N34. `order_perf_kiwoom_ws_tick_parse_fastpath`

- title: Kiwoom websocket tick parsing fast path
- decision: `reject`
- decision_reason: quote/data-quality semantics can change; requires separate data-quality approval owner
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `quote_data_quality`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `-`
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
- implementation_status: `-`
- files_likely_touched: `src/utils/pipeline_event_logger.py`
- acceptance_tests: `pytest pipeline event verbosity tests`

## 자동화체인 재투입

- 구현 결과는 `2026-06-09` 이후 postclose `threshold_cycle`, `scalping_pattern_lab_automation`, `threshold_cycle_ev`가 자동으로 다시 읽는다.
- 구현자가 수동으로 threshold 값을 바꾸는 것이 아니라, source/report/provenance를 닫아 다음 calibration이 판단하게 한다.
- 다음 Codex 세션 입력 문구: `none_for_bucket_discovery_classification`

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
