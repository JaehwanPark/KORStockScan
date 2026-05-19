# Code Improvement Workorder - 2026-05-19

## 목적

- Postclose 자동화가 생성한 `code_improvement_order`를 Codex 실행용 작업지시서로 변환한다.
- 입력은 scalping pattern lab automation, swing lifecycle improvement automation, swing pattern lab automation을 함께 포함할 수 있다.
- 이 문서는 repo/runtime을 직접 변경하지 않는다. 사용자가 이 문서를 Codex 세션에 넣고 구현을 요청하는 지점만 사람 개입으로 남긴다.
- 구현 후 자동화체인 재투입은 다음 postclose report, threshold calibration, daily EV report가 담당한다.

## Source

- pattern_lab_automation: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-19.json`
- swing_improvement_automation: `/home/ubuntu/KORStockScan/data/report/swing_improvement_automation/swing_improvement_automation_2026-05-19.json`
- swing_pattern_lab_automation: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-05-19.json`
- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-19.json`
- threshold_cycle_calibration: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_calibration/threshold_cycle_calibration_2026-05-19_postclose.json`
- pipeline_event_verbosity: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-05-19.json`
- observation_source_quality_audit: `/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-05-19.json`
- codebase_performance_workorder: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-05-19.json`
- pattern_lab_currentness_audit: `/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-05-19.json`
- generated_at: `2026-05-19T16:20:50+09:00`
- generation_id: `2026-05-19-d75780954c2f`
- source_hash: `d75780954c2f778960709d50ecdd713f72050442828f00c877b4be727ec61f8d`

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
- 권장 지시문: `implement_now를 2-pass로 처리: Pass1 instrumentation/report/provenance 구현, 관련 리포트 재생성 후 workorder diff 확인, 신규 runtime_effect=false 항목만 Pass2 구현, 마지막에 generation_id/source_hash 기준으로 final freeze 보고`

## Snapshot Lineage

- previous_exists: `False`
- previous_generation_id: `-`
- previous_source_hash: `-`
- new_order_ids: `['order_ai_source_quality_not_evaluated_provenance', 'order_ai_threshold_dominance', 'order_ai_threshold_miss_ev_recovery', 'order_high_volume_diagnostic_stage_contract_labels', 'order_holding_exit_decision_matrix_edge_counterfactual', 'order_perf_buy_funnel_json_scan', 'order_perf_daily_report_bulk_history', 'order_perf_daily_report_engine_singleton', 'order_pipeline_event_compaction_v2_shadow', 'order_scalp_entry_adm_daily_tuning_coverage', 'order_swing_source_quality_micro_context_provenance', 'order_threshold_window_policy_source_snapshot_alignment']`
- removed_order_ids: `[]`
- decision_changed_order_ids: `[]`

## Summary

- source_order_count: `42`
- scalping_source_order_count: `13`
- swing_source_order_count: `4`
- swing_lab_source_order_count: `4`
- pattern_lab_currentness_source_order_count: `0`
- threshold_ev_source_order_count: `21`
- pipeline_event_verbosity_source_order_count: `1`
- observation_source_quality_source_order_count: `3`
- codebase_performance_source_order_count: `12`
- panic_lifecycle_source_order_count: `2`
- selected_order_count: `12`
- decision_counts: `{'implement_now': 7, 'attach_existing_family': 15, 'design_family_candidate': 6, 'defer_evidence': 11, 'reject': 3}`
- gemini_fresh: `True`
- claude_fresh: `True`
- swing_lifecycle_audit_available: `True`
- swing_pattern_lab_automation_available: `True`
- swing_pattern_lab_fresh: `True`
- pattern_lab_currentness_status: `pass`
- pattern_lab_currentness_fail_count: `0`
- swing_threshold_ai_status: `parsed`
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

### 1. `order_ai_source_quality_not_evaluated_provenance`

- title: AI source-quality not-evaluated provenance for cooldown and score50 paths
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `observation_source_quality_audit`
- lifecycle_stage: `source_quality_gate`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `-`
- confidence: `audit`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: none_direct_source_quality_attribution_only
- evidence: `status=warning`, `event_count=477812`, `warning_stage_count=5`, `warning_stages=ai_confirmed,blocked_strength_momentum,blocked_overbought,scale_in_price_resolved,scale_in_price_p2_observe`, `high_volume_no_source_field_stage_count=4`, `decision_authority=source_quality_only`, `runtime_effect=false`
- parity_contract: -
- next_postclose_metric: observation_source_quality_audit.warning_stage_count and high_volume_no_source_field_stage_count
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/observation_source_quality_audit.py`
- acceptance_tests: `pytest src/tests/test_observation_source_quality_audit.py src/tests/test_state_handler_fast_signatures.py`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 2. `order_pipeline_event_compaction_v2_shadow`

- title: Pipeline event compaction V2 shadow producer summary
- decision: `implement_now`
- decision_reason: pipeline event compaction V2 is report-only instrumentation; shadow means producer-summary observe mode, not trading shadow
- source_report_type: `pipeline_event_verbosity`
- lifecycle_stage: `ops_volume_diagnostic`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `-`
- confidence: `consensus`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: none_direct_ops_cpu_io_reduction_only
- evidence: `state=v2_shadow_parity_fail`, `recommended_workorder_state=block_suppress_and_fix_shadow`, `raw_size_bytes=832300287`, `high_volume_line_count=388488`, `high_volume_byte_share_pct=68.03`, `producer_summary_exists=True`, `parity_ok=False`, `raw_derived_event_count=388524`, `producer_event_count=388473`
- parity_contract: -
- next_postclose_metric: pipeline_event_verbosity.parity.ok
- files_likely_touched: `src/utils/pipeline_event_logger.py`, `src/engine/pipeline_event_summary.py`, `src/engine/pipeline_event_verbosity_report.py`
- acceptance_tests: `pytest src/tests/test_pipeline_event_logger.py src/tests/test_pipeline_event_verbosity_report.py`
- automation_reentry: Next postclose pipeline_event_verbosity report must show producer summary freshness and parity status.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 3. `order_high_volume_diagnostic_stage_contract_labels`

- title: High-volume diagnostic stage metric contract labels
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `observation_source_quality_audit`
- lifecycle_stage: `source_quality_gate`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `-`
- confidence: `audit`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: none_direct_source_quality_attribution_only
- evidence: `status=warning`, `event_count=477812`, `warning_stage_count=5`, `warning_stages=ai_confirmed,blocked_strength_momentum,blocked_overbought,scale_in_price_resolved,scale_in_price_p2_observe`, `high_volume_no_source_field_stage_count=4`, `decision_authority=source_quality_only`, `runtime_effect=false`, `gap_stages=loss_fallback_probe,soft_stop_whipsaw_confirmation,entry_armed,entry_armed_expired_after_wait`
- parity_contract: -
- next_postclose_metric: observation_source_quality_audit.warning_stage_count and high_volume_no_source_field_stage_count
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/observation_source_quality_audit.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `pytest src/tests/test_observation_source_quality_audit.py src/tests/test_build_code_improvement_workorder.py`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 4. `order_swing_source_quality_micro_context_provenance`

- title: Swing source-quality micro context provenance
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `observation_source_quality_audit`
- lifecycle_stage: `source_quality_gate`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `-`
- confidence: `audit`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: none_direct_source_quality_attribution_only
- evidence: `status=warning`, `event_count=477812`, `warning_stage_count=5`, `warning_stages=ai_confirmed,blocked_strength_momentum,blocked_overbought,scale_in_price_resolved,scale_in_price_p2_observe`, `high_volume_no_source_field_stage_count=4`, `decision_authority=source_quality_only`, `runtime_effect=false`, `swing_warning_stages=scale_in_price_resolved,scale_in_price_p2_observe`, `scale_in_price_resolved:sample_count=19 missing_fields=orderbook_micro_snapshot_age_ms`, `scale_in_price_p2_observe:sample_count=19 missing_fields=orderbook_micro_snapshot_age_ms`
- parity_contract: -
- next_postclose_metric: observation_source_quality_audit.warning_stage_count and high_volume_no_source_field_stage_count
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/observation_source_quality_audit.py`, `src/engine/build_code_improvement_workorder.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `pytest src/tests/test_observation_source_quality_audit.py src/tests/test_swing_model_selection_funnel_repair.py src/tests/test_build_code_improvement_workorder.py`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 5. `order_scalp_entry_adm_daily_tuning_coverage`

- title: scalp entry ADM daily tuning coverage
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `threshold_cycle_ev`
- lifecycle_stage: `entry`
- target_subsystem: `entry_funnel`
- route: `instrumentation_order`
- mapped_family: `scalp_entry_action_decision_matrix_advisory`
- threshold_family: `scalp_entry_action_decision_matrix_advisory`
- improvement_type: `instrumentation_report_provenance`
- confidence: `consensus`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep BUY_NOW/WAIT_REQUOTE/SKIP_STALE/BUY_DEFENSIVE/NO_BUY_AI/SKIP_SOURCE_QUALITY/SKIP_PRE_SUBMIT_SAFETY action buckets joined to post-sell outcomes and runtime forced_action provenance for daily entry policy tuning.
- evidence: `status=warning`, `joined_sample=72`, `sample_floor=20`, `prompt_applied_count=506`, `missing_actions=WAIT_REQUOTE,SKIP_STALE,BUY_DEFENSIVE`
- parity_contract: -
- next_postclose_metric: scalp_entry_action_decision_matrix should meet sample_floor, include all action buckets, show prompt_applied_count, and expose entry_adm_runtime_effect/forced_action evidence when runtime bias env is enabled.
- files_likely_touched: `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/sniper_state_handlers.py`, `src/engine/scalp_entry_adm_runtime.py`, `src/engine/threshold_cycle_ev_report.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_scalp_entry_action_decision_matrix.py src/tests/test_build_code_improvement_workorder.py`, `runtime_effect remains false and broker submit safety guards remain owner`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 6. `order_threshold_window_policy_source_snapshot_alignment`

- title: threshold window policy source snapshot alignment
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `threshold_cycle_calibration`
- lifecycle_stage: `threshold_cycle`
- target_subsystem: `threshold_cycle_report`
- route: `instrumentation_order`
- mapped_family: `-`
- threshold_family: `window_policy_registry`
- improvement_type: `source_quality_alignment`
- confidence: `consensus`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Prevent daily-only or snapshot-only calibration blind spots by aligning rolling/cumulative source metrics, snapshot denominators, AI correction context, and EV/workorder rendering.
- evidence: `issue_counts={"daily_only_leak_blocked": 1}`, `affected_families=lifecycle_decision_matrix_runtime`, `family=lifecycle_decision_matrix_runtime primary=latest_report state=hold_sample primary_sample=0 snapshot_sample=None source_sample=0 issues=daily_only_leak_blocked`
- parity_contract: -
- next_postclose_metric: window_policy_audit should have no daily_only_leak or rolling_consumer_gap; rolling_source_snapshot_mismatch must be explained as rendering-only or eliminated.
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/threshold_cycle_ev_report.py`, `src/engine/build_code_improvement_workorder.py`, `data/threshold_cycle/README.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_daily_threshold_cycle_report.py src/tests/test_build_code_improvement_workorder.py`, `threshold_cycle_YYYY-MM-DD.json includes window_policy_audit and calibration_source_bundle_by_window lineage`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 7. `order_holding_exit_decision_matrix_edge_counterfactual`

- title: holding exit decision matrix edge counterfactual coverage
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `threshold_cycle_ev`
- lifecycle_stage: `holding_exit`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
- mapped_family: `holding_exit_decision_matrix_advisory`
- threshold_family: `holding_exit_decision_matrix_advisory`
- improvement_type: `instrumentation`
- confidence: `consensus`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Break hold_no_edge by separating exit_only/hold_defer/avg_down/pyramid counterfactual outcomes.
- evidence: `calibration_state=hold_no_edge`, `sample_count=0`, `sample_floor=1`, `counterfactual_gap_count=0`, `eligible_snapshot_count=0`, `eligible_joined_candidates=0`, `proxy_missing_actions=hold_defer,exit_only,avg_down_wait,pyramid_wait`
- parity_contract: -
- next_postclose_metric: holding_exit_decision_matrix_advisory should report per-action edge buckets, non_no_clear_edge_count, and counterfactual coverage.
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/holding_exit_decision_matrix.py`, `src/engine/statistical_action_weight.py`
- acceptance_tests: `pytest holding exit decision matrix/report tests`, `threshold EV report includes per-action counterfactual coverage`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 8. `order_ai_threshold_dominance`

- title: AI threshold dominance
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `entry_funnel`
- route: `existing_family`
- mapped_family: `score65_74_recovery_probe`
- threshold_family: `score65_74_recovery_probe`
- improvement_type: `-`
- confidence: `consensus`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve EV attribution and prepare bounded calibration input.
- evidence: `{'judgment': '경고', 'why': '`blocked_ai_score_share=78.3%`로 WAIT/BLOCK 비중이 높아 BUY drought 해석을 지지한다.'}`, `{'judgment': '경고', 'why': '`blocked_ai_score_share=78.3%`로 WAIT/BLOCK 비중이 높아 BUY drought 해석을 지지한다.'}`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_missed_entry_counterfactual.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`
- automation_reentry: After implementation, intraday/postclose calibration should include the updated family input.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 9. `order_perf_buy_funnel_json_scan`

- title: BUY funnel sentinel field scan without repeated json.dumps
- decision: `attach_existing_family`
- decision_reason: report-only performance implementation is already present in code; keep the order as provenance and validate through regenerated reports/tests instead of re-implementing
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `buy_funnel_sentinel`
- route: `performance_optimization_order`
- mapped_family: `ops_performance_report_only_implemented`
- threshold_family: `ops_performance_report_only_implemented`
- improvement_type: `-`
- confidence: `consensus`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: none_direct_ops_cpu_io_reduction_only
- evidence: `source_doc_hash=6bc37e5b3d13f356392d83e4ec1ecdcd2f57a05a0f9bc58f6329a1ea20fbed88`, `candidate_state=accepted`, `implementation_status=implemented`, `risk_tier=low`, `runtime_effect=false`, `strategy_effect=false`, `data_quality_effect=false`, `tuning_axis_effect=false`, `parity_contract=classification, blocker counts, unique submitted count, actual_order_submitted split, source-quality/provenance fields exact match`
- parity_contract: classification, blocker counts, unique submitted count, actual_order_submitted split, source-quality/provenance fields exact match
- next_postclose_metric: same report/output parity with lower runtime or CPU/IO overhead
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`
- acceptance_tests: `pytest src/tests/test_buy_funnel_sentinel.py`, `BUY Sentinel classification parity on same raw/cache input`
- automation_reentry: Next postclose codebase performance source report must keep implementation_status=implemented and parity tests green.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 10. `order_ai_threshold_miss_ev_recovery`

- title: AI threshold miss EV recovery
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `entry_funnel`
- route: `existing_family`
- mapped_family: `score65_74_recovery_probe`
- threshold_family: `score65_74_recovery_probe`
- improvement_type: `-`
- confidence: `consensus`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve EV attribution and prepare bounded calibration input.
- evidence: `{'total_blocked': 4465075, 'block_ratio': 100.0, 'days': 25}`, `{'total_blocked': 5360351, 'block_ratio': 100.0, 'days': 26}`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_missed_entry_counterfactual.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`
- automation_reentry: After implementation, intraday/postclose calibration should include the updated family input.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 11. `order_perf_daily_report_bulk_history`

- title: Daily report market snapshot bulk history query
- decision: `attach_existing_family`
- decision_reason: report-only performance implementation is already present in code; keep the order as provenance and validate through regenerated reports/tests instead of re-implementing
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `daily_report`
- route: `performance_optimization_order`
- mapped_family: `ops_performance_report_only_implemented`
- threshold_family: `ops_performance_report_only_implemented`
- improvement_type: `-`
- confidence: `consensus`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: none_direct_ops_cpu_io_reduction_only
- evidence: `source_doc_hash=6bc37e5b3d13f356392d83e4ec1ecdcd2f57a05a0f9bc58f6329a1ea20fbed88`, `candidate_state=accepted`, `implementation_status=implemented`, `risk_tier=medium`, `runtime_effect=false`, `strategy_effect=false`, `data_quality_effect=false`, `tuning_axis_effect=false`, `parity_contract=per-stock history window, feature columns, model input row count, and report JSON exact match`
- parity_contract: per-stock history window, feature columns, model input row count, and report JSON exact match
- next_postclose_metric: same report/output parity with lower runtime or CPU/IO overhead
- files_likely_touched: `src/engine/daily_report_service.py`
- acceptance_tests: `pytest src/tests/test_daily_report_service.py src/tests/test_daily_report.py`, `daily report output parity on injected DB/model fixture`
- automation_reentry: Next postclose codebase performance source report must keep implementation_status=implemented and parity tests green.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 12. `order_perf_daily_report_engine_singleton`

- title: Daily report SQLAlchemy engine singleton
- decision: `attach_existing_family`
- decision_reason: report-only performance implementation is already present in code; keep the order as provenance and validate through regenerated reports/tests instead of re-implementing
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `daily_report`
- route: `performance_optimization_order`
- mapped_family: `ops_performance_report_only_implemented`
- threshold_family: `ops_performance_report_only_implemented`
- improvement_type: `-`
- confidence: `consensus`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: none_direct_ops_cpu_io_reduction_only
- evidence: `source_doc_hash=6bc37e5b3d13f356392d83e4ec1ecdcd2f57a05a0f9bc58f6329a1ea20fbed88`, `candidate_state=accepted`, `implementation_status=implemented`, `risk_tier=low`, `runtime_effect=false`, `strategy_effect=false`, `data_quality_effect=false`, `tuning_axis_effect=false`, `parity_contract=query result and rendered daily report exact match`
- parity_contract: query result and rendered daily report exact match
- next_postclose_metric: same report/output parity with lower runtime or CPU/IO overhead
- files_likely_touched: `src/engine/daily_report_service.py`
- acceptance_tests: `pytest src/tests/test_daily_report_service.py src/tests/test_daily_report.py`, `engine creation count regression test`
- automation_reentry: Next postclose codebase performance source report must keep implementation_status=implemented and parity tests green.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

## 자동화체인 재투입

- 구현 결과는 `2026-05-20` 이후 postclose `threshold_cycle`, `scalping_pattern_lab_automation`, `threshold_cycle_ev`가 자동으로 다시 읽는다.
- 구현자가 수동으로 threshold 값을 바꾸는 것이 아니라, source/report/provenance를 닫아 다음 calibration이 판단하게 한다.
- 다음 Codex 세션 입력 문구: `paste generated markdown into a Codex session and request implementation`

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
