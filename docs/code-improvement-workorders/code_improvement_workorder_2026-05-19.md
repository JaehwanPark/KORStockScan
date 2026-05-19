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
- generated_at: `2026-05-19T18:33:57+09:00`
- generation_id: `2026-05-19-1b4bfff04bbb`
- source_hash: `1b4bfff04bbb6d6877c24a1b8d8162a947d874bbd891d9cbf79529d41a9a3c77`

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

- previous_exists: `True`
- previous_generation_id: `2026-05-19-1b4bfff04bbb`
- previous_source_hash: `1b4bfff04bbb6d6877c24a1b8d8162a947d874bbd891d9cbf79529d41a9a3c77`
- new_order_ids: `[]`
- removed_order_ids: `[]`
- decision_changed_order_ids: `[]`

## Summary

- source_order_count: `35`
- scalping_source_order_count: `13`
- swing_source_order_count: `4`
- swing_lab_source_order_count: `4`
- pattern_lab_currentness_source_order_count: `0`
- threshold_ev_source_order_count: `14`
- pipeline_event_verbosity_source_order_count: `0`
- observation_source_quality_source_order_count: `0`
- codebase_performance_source_order_count: `12`
- panic_lifecycle_source_order_count: `2`
- selected_order_count: `12`
- decision_counts: `{'attach_existing_family': 15, 'design_family_candidate': 6, 'defer_evidence': 11, 'reject': 3}`
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

### 1. `order_ai_threshold_dominance`

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
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, intraday/postclose calibration should include the updated family input.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 2. `order_perf_buy_funnel_json_scan`

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
- implementation_status: `implemented`
- implementation_provenance: `-`
- automation_reentry: Next postclose codebase performance source report must keep implementation_status=implemented and parity tests green.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 3. `order_ai_threshold_miss_ev_recovery`

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
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, intraday/postclose calibration should include the updated family input.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 4. `order_perf_daily_report_bulk_history`

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
- implementation_status: `implemented`
- implementation_provenance: `-`
- automation_reentry: Next postclose codebase performance source report must keep implementation_status=implemented and parity tests green.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 5. `order_perf_daily_report_engine_singleton`

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
- implementation_status: `implemented`
- implementation_provenance: `-`
- automation_reentry: Next postclose codebase performance source report must keep implementation_status=implemented and parity tests green.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 6. `order_swing_gatekeeper_reject_threshold_review`

- title: swing gatekeeper reject threshold review
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `swing_improvement_automation`
- lifecycle_stage: `entry`
- target_subsystem: `swing_entry`
- route: `existing_family`
- mapped_family: `swing_gatekeeper_accept_reject`
- threshold_family: `swing_gatekeeper_accept_reject`
- improvement_type: `threshold_family_input`
- confidence: `consensus`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: gatekeeper reject/pass, submitted/simulated, and post-entry outcomes are attributable by family.
- evidence: `blocked_gatekeeper_reject_unique=8`
- parity_contract: -
- next_postclose_metric: gatekeeper reject/pass, submitted/simulated, and post-entry outcomes are attributable by family.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/swing_lifecycle_audit.py`
- acceptance_tests: `pytest swing lifecycle audit tests`, `pytest state handler fast signatures`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, intraday/postclose calibration should include the updated family input.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 7. `order_swing_pattern_lab_deepseek_scale_in_events_observed`

- title: Scale-in events observed for swing positions
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `swing_pattern_lab_automation`
- lifecycle_stage: `scale_in`
- target_subsystem: `swing_scale_in`
- route: `attach_existing_family`
- mapped_family: `swing_scale_in_ofi_qi_confirmation`
- threshold_family: `swing_scale_in_ofi_qi_confirmation`
- improvement_type: `pattern_lab_observation`
- confidence: `consensus`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Evaluate PYRAMID/AVG_DOWN outcome quality with OFI/QI confirmation.
- evidence: `{'scale_in_events': 11}`
- parity_contract: -
- next_postclose_metric: swing_scale_in_quality_score
- files_likely_touched: `src/engine/swing_lifecycle_audit.py`, `src/engine/swing_selection_funnel_report.py`, `src/model/common_v2.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_model_selection_funnel_repair.py`, `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_deepseek_swing_pattern_lab.py`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, intraday/postclose calibration should include the updated family input.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 8. `order_latency_guard_miss_ev_recovery`

- title: latency guard miss EV recovery
- decision: `attach_existing_family`
- decision_reason: instrumentation/provenance contract is already implemented; keep as report source for the existing family
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `runtime_instrumentation`
- route: `existing_family`
- mapped_family: `pre_submit_price_guard`
- threshold_family: `pre_submit_price_guard`
- improvement_type: `-`
- confidence: `consensus`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve EV attribution and prepare bounded calibration input.
- evidence: `{'total_blocked': 61199, 'block_ratio': 99.5, 'days': 25}`, `{'total_blocked': 52330, 'block_ratio': 99.5, 'days': 26}`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/sniper_performance_tuning_report.py`, `src/engine/daily_threshold_cycle_report.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: Next postclose calibration consumes the implemented report/provenance fields; no runtime mutation.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 9. `order_perf_recommend_update_vectorization`

- title: Recommendation and update_kospi vectorized membership checks
- decision: `attach_existing_family`
- decision_reason: report-only performance implementation is already present in code; keep the order as provenance and validate through regenerated reports/tests instead of re-implementing
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `swing_daily_recommendation`
- route: `performance_optimization_order`
- mapped_family: `ops_performance_report_only_implemented`
- threshold_family: `ops_performance_report_only_implemented`
- improvement_type: `-`
- confidence: `consensus`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: none_direct_ops_cpu_io_reduction_only
- evidence: `source_doc_hash=6bc37e5b3d13f356392d83e4ec1ecdcd2f57a05a0f9bc58f6329a1ea20fbed88`, `candidate_state=accepted`, `implementation_status=implemented`, `risk_tier=low`, `runtime_effect=false`, `strategy_effect=false`, `data_quality_effect=false`, `tuning_axis_effect=false`, `parity_contract=selected keys, diagnostics rows, CSV row order, and update_kospi inserted-row set exact match`
- parity_contract: selected keys, diagnostics rows, CSV row order, and update_kospi inserted-row set exact match
- next_postclose_metric: same report/output parity with lower runtime or CPU/IO overhead
- files_likely_touched: `src/model/recommend_daily_v2.py`, `src/utils/update_kospi.py`
- acceptance_tests: `pytest src/tests/test_swing_retrain_automation.py src/tests/test_swing_feature_ssot.py`, `recommendation CSV and diagnostics parity`
- implementation_status: `implemented`
- implementation_provenance: `-`
- automation_reentry: Next postclose codebase performance source report must keep implementation_status=implemented and parity tests green.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 10. `order_swing_ofi_qi_stale_or_missing_context`

- title: swing OFI/QI stale or missing context
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `swing_improvement_automation`
- lifecycle_stage: `entry`
- target_subsystem: `swing_orderbook_micro_context`
- route: `existing_family`
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
- evidence: `stale_missing_count=470`, `stale_missing_ratio=0.9216`, `stale_missing_unique_record_count=5`, `stale_missing_reason_counts={'micro_missing': 470, 'micro_not_ready': 24, 'state_insufficient': 24, 'observer_unhealthy': 1}`, `stale_missing_reason_combination_counts={'micro_missing': 446, 'micro_missing+micro_not_ready+state_insufficient': 23, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`, `stale_missing_reason_combination_unique_record_counts={'micro_missing+micro_not_ready+state_insufficient': 4, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`, `observer_unhealthy_overlap={'observer_unhealthy_total': 1, 'observer_unhealthy_with_other_reason': 1, 'observer_unhealthy_only': 0}`, `scale_in_source_quality={'group': 'scale_in', 'sample_count': 33, 'valid_micro_context_count': 30, 'invalid_micro_context_count': 3, 'invalid_micro_context_unique_record_count': 1, 'invalid_reason_combination_counts': {'micro_missing': 446, 'micro_missing+micro_not_ready+state_insufficient': 23, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}, 'invalid_reason_combination_unique_record_counts': {'micro_missing+micro_not_ready+state_insufficient': 4, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}, 'observer_unhealthy_overlap': {'observer_unhealthy_total': 1, 'observer_unhealthy_with_other_reason': 1, 'observer_unhealthy_only': 0}, 'source_quality_blockers': ['scale_in_ofi_qi_invalid_micro_context']}`, `entry_source_quality={'group': 'entry', 'sample_count': 0, 'valid_micro_context_count': 0, 'invalid_micro_context_count': 0, 'invalid_micro_context_unique_record_count': 0, 'invalid_reason_combination_counts': {'micro_missing': 446, 'micro_missing+micro_not_ready+state_insufficient': 23, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}, 'invalid_reason_combination_unique_record_counts': {'micro_missing+micro_not_ready+state_insufficient': 4, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}, 'observer_unhealthy_overlap': {'observer_unhealthy_total': 1, 'observer_unhealthy_with_other_reason': 1, 'observer_unhealthy_only': 0}, 'source_quality_blockers': []}`
- parity_contract: -
- next_postclose_metric: stale_missing_ratio decreases while submitted/simulated entry quality remains attributable.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/orderbook_stability.py`, `src/engine/swing_lifecycle_audit.py`
- acceptance_tests: `pytest orderbook stability tests`, `pytest swing lifecycle audit tests`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, intraday/postclose calibration should include the updated family input.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 11. `order_swing_pattern_lab_deepseek_ofi_qi_stale_missing`

- title: OFI/QI stale/missing quality review
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation is already present; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `swing_pattern_lab_automation`
- lifecycle_stage: `ofi_qi`
- target_subsystem: `swing_micro_context`
- route: `existing_family`
- mapped_family: `swing_entry_ofi_qi_execution_quality`
- threshold_family: `swing_entry_ofi_qi_execution_quality`
- improvement_type: `pattern_lab_observation`
- confidence: `consensus`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: If stale ratio > 0.3, consider instrumentation/observer enhancement.
- evidence: `{'total_samples': 510, 'stale_missing_count': 470, 'stale_missing_ratio': 0.9216, 'stale_missing_reason_counts': {'micro_missing': 470, 'micro_stale': 0, 'observer_unhealthy': 1, 'micro_not_ready': 24, 'state_insufficient': 24}, 'stale_missing_reason_ratios': {'micro_missing': 0.9216, 'micro_stale': 0.0, 'observer_unhealthy': 0.002, 'micro_not_ready': 0.0471, 'state_insufficient': 0.0471}, 'stale_missing_reason_combination_counts': {'micro_missing': 446, 'micro_missing+micro_not_ready+state_insufficient': 23, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}, 'stale_missing_reason_combination_unique_record_counts': {'micro_missing': 0, 'micro_missing+micro_not_ready+state_insufficient': 4, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}, 'stale_missing_group_counts': {'holding': 463, 'exit': 4, 'scale_in': 3}, 'stale_missing_group_unique_record_counts': {'exit': 4, 'holding': 0, 'scale_in': 1}, 'stale_missing_unique_record_count': 5, 'observer_unhealthy_overlap': {'observer_unhealthy_total': 1, 'observer_unhealthy_with_other_reason': 1, 'observer_unhealthy_only': 0}, 'advice_distribution': {'WAIT_FOR_PULLBACK': 36, 'MISSING': 7, 'SUPPORT_ENTRY': 3, 'RISK_BEARISH': 1}, 'state_distribution': {'neutral': 433, 'bearish': 45, 'insufficient': 24, 'bullish': 8}, 'group_distribution': {'holding': 463, 'scale_in': 33, 'exit': 14}, 'runtime_effect_true_count': 0}`
- parity_contract: -
- next_postclose_metric: swing_ofi_qi_quality_score
- files_likely_touched: `src/engine/swing_lifecycle_audit.py`, `src/engine/swing_selection_funnel_report.py`, `src/model/common_v2.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_model_selection_funnel_repair.py`, `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_deepseek_swing_pattern_lab.py`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "source_quality_only", "implemented_scope": "instrumentation_report_provenance_only", "next_postclose_metric": "swing_ofi_qi_quality_score", "owner": "swing_pattern_lab_automation", "runtime_effect": false, "source_quality_blocked_families": [{"automation_input": true, "family": "swing_scale_in_ofi_qi_confirmation", "invalid_micro_context_unique_record_count": 1, "invalid_reason_combination_unique_record_counts": {"micro_missing+micro_not_ready+state_insufficient": 4, "micro_missing+observer_unhealthy+micro_not_ready+state_insufficient": 1}, "runtime_effect": false, "source_quality_blockers": ["scale_in_ofi_qi_invalid_micro_context"], "stage": "scale_in"}]}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 12. `order_perf_swing_simulation_iteration`

- title: Swing simulation iteration and quote grouping
- decision: `attach_existing_family`
- decision_reason: report-only performance implementation is already present in code; keep the order as provenance and validate through regenerated reports/tests instead of re-implementing
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `swing_daily_simulation`
- route: `performance_optimization_order`
- mapped_family: `ops_performance_report_only_implemented`
- threshold_family: `ops_performance_report_only_implemented`
- improvement_type: `-`
- confidence: `consensus`
- priority: `5`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: none_direct_ops_cpu_io_reduction_only
- evidence: `source_doc_hash=6bc37e5b3d13f356392d83e4ec1ecdcd2f57a05a0f9bc58f6329a1ea20fbed88`, `candidate_state=accepted`, `implementation_status=implemented`, `risk_tier=medium`, `runtime_effect=false`, `strategy_effect=false`, `data_quality_effect=false`, `tuning_axis_effect=false`, `parity_contract=selection funnel, lifecycle arms, gate counterfactuals, and runtime funnel summary exact match`
- parity_contract: selection funnel, lifecycle arms, gate counterfactuals, and runtime funnel summary exact match
- next_postclose_metric: same report/output parity with lower runtime or CPU/IO overhead
- files_likely_touched: `src/engine/swing_daily_simulation_report.py`
- acceptance_tests: `pytest src/tests/test_swing_model_selection_funnel_repair.py`, `swing simulation JSON parity on injected sources`
- implementation_status: `implemented`
- implementation_provenance: `-`
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
