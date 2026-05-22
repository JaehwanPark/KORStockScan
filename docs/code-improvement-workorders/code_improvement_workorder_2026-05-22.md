# Code Improvement Workorder - 2026-05-22

## 목적

- Postclose 자동화가 생성한 `code_improvement_order`를 Codex 실행용 작업지시서로 변환한다.
- 입력은 scalping pattern lab automation, swing lifecycle improvement automation, swing pattern lab automation을 함께 포함할 수 있다.
- 이 문서는 repo/runtime을 직접 변경하지 않는다. 사용자가 이 문서를 Codex 세션에 넣고 구현을 요청하는 지점만 사람 개입으로 남긴다.
- 구현 후 자동화체인 재투입은 다음 postclose report, threshold calibration, daily EV report가 담당한다.

## Source

- pattern_lab_automation: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-22.json`
- swing_improvement_automation: `-`
- swing_pattern_lab_automation: `-`
- swing_strategy_discovery_ev: `-`
- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-22.json`
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-22.json`
- threshold_cycle_calibration: `-`
- pipeline_event_verbosity: `-`
- observation_source_quality_audit: `-`
- codebase_performance_workorder: `-`
- pattern_lab_currentness_audit: `-`
- generated_at: `2026-05-22T11:24:31+09:00`
- generation_id: `2026-05-22-a233add9704b`
- source_hash: `a233add9704bfd96f810631e601209d7a877b36add58e6e0f3a75cb354d5172f`

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

- previous_exists: `False`
- previous_generation_id: `-`
- previous_source_hash: `-`
- new_order_ids: `['order_lifecycle_ai_context_attribution_feedback', 'order_lifecycle_bucket_discovery_entry_entry_chosen_action_action_unknown', 'order_lifecycle_bucket_discovery_entry_entry_exit_rule_exit_unknown', 'order_lifecycle_bucket_discovery_entry_entry_liquidity_bucket_liquidity_unknown', 'order_lifecycle_bucket_discovery_entry_entry_overbought_bucket_overbought_unknown', 'order_lifecycle_bucket_discovery_entry_entry_strength_bucket_strength_unknown', 'order_lifecycle_bucket_discovery_entry_entry_time_bucket_time_unknown', 'order_lifecycle_bucket_discovery_scale_in_scale_in_ai_score_source_ai_source_unknown', 'order_lifecycle_bucket_discovery_scale_in_scale_in_arm_arm_unknown', 'order_lifecycle_bucket_discovery_scale_in_scale_in_blocker_namespace_blocker_namespace_unknown', 'order_lifecycle_bucket_discovery_scale_in_scale_in_blocker_reason_blocker_reason_unknown', 'order_lifecycle_entry_bucket_chosen_action_action_unknown', 'order_lifecycle_entry_bucket_exit_rule_exit_unknown', 'order_lifecycle_entry_bucket_liquidity_bucket_liquidity_unknown', 'order_lifecycle_entry_bucket_overbought_bucket_overbought_unknown', 'order_lifecycle_entry_bucket_source_stage_wait6579_ev_cohort', 'order_lifecycle_entry_bucket_stale_bucket_fresh_or_unflagged', 'order_lifecycle_entry_bucket_strength_bucket_strength_unknown', 'order_lifecycle_entry_bucket_time_bucket_time_unknown', 'order_lifecycle_scale_in_bucket_arm_avg_down', 'order_lifecycle_scale_in_bucket_arm_pyramid', 'order_lifecycle_scale_in_bucket_blocker_namespace_avg_down', 'order_lifecycle_scale_in_bucket_blocker_namespace_pyramid', 'order_lifecycle_scale_in_bucket_blocker_reason_low_broken', 'order_lifecycle_scale_in_bucket_blocker_reason_pnl_out_of_range_0_76', 'order_lifecycle_scale_in_bucket_blocker_reason_pnl_out_of_range_0_82', 'order_lifecycle_scale_in_bucket_blocker_reason_pnl_out_of_range_0_90', 'order_lifecycle_scale_in_bucket_blocker_reason_pnl_out_of_range_0_96', 'order_lifecycle_scale_in_bucket_blocker_reason_profit_not_enough', 'order_scalp_entry_adm_daily_tuning_coverage']`
- removed_order_ids: `[]`
- decision_changed_order_ids: `[]`

## Summary

- source_order_count: `30`
- scalping_source_order_count: `0`
- swing_source_order_count: `0`
- swing_lab_source_order_count: `0`
- swing_strategy_discovery_source_order_count: `0`
- pattern_lab_currentness_source_order_count: `0`
- threshold_ev_source_order_count: `2`
- pipeline_event_verbosity_source_order_count: `0`
- observation_source_quality_source_order_count: `0`
- codebase_performance_source_order_count: `0`
- panic_lifecycle_source_order_count: `0`
- selected_order_count: `30`
- decision_counts: `{'implement_now': 18, 'attach_existing_family': 12}`
- gemini_fresh: `None`
- claude_fresh: `None`
- swing_lifecycle_audit_available: `False`
- swing_pattern_lab_automation_available: `False`
- swing_pattern_lab_fresh: `None`
- pattern_lab_currentness_status: `None`
- pattern_lab_currentness_fail_count: `None`
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

### 1. `order_lifecycle_entry_bucket_chosen_action_action_unknown`

- title: LDM entry bucket attribution follow-up: chosen_action=action_unknown
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `lifecycle_decision_matrix_entry_bucket_attribution`
- lifecycle_stage: `entry`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
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
- evidence: `workorder_id=entry_bucket_source_quality_1`, `bucket_type=chosen_action`, `bucket_key=action_unknown`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 2. `order_lifecycle_entry_bucket_exit_rule_exit_unknown`

- title: LDM entry bucket attribution follow-up: exit_rule=exit_unknown
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `lifecycle_decision_matrix_entry_bucket_attribution`
- lifecycle_stage: `entry`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
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
- evidence: `workorder_id=entry_bucket_source_quality_2`, `bucket_type=exit_rule`, `bucket_key=exit_unknown`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 3. `order_lifecycle_entry_bucket_liquidity_bucket_liquidity_unknown`

- title: LDM entry bucket attribution follow-up: liquidity_bucket=liquidity_unknown
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `lifecycle_decision_matrix_entry_bucket_attribution`
- lifecycle_stage: `entry`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
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
- evidence: `workorder_id=entry_bucket_source_quality_3`, `bucket_type=liquidity_bucket`, `bucket_key=liquidity_unknown`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 4. `order_lifecycle_entry_bucket_overbought_bucket_overbought_unknown`

- title: LDM entry bucket attribution follow-up: overbought_bucket=overbought_unknown
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `lifecycle_decision_matrix_entry_bucket_attribution`
- lifecycle_stage: `entry`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
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
- evidence: `workorder_id=entry_bucket_source_quality_4`, `bucket_type=overbought_bucket`, `bucket_key=overbought_unknown`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 5. `order_lifecycle_entry_bucket_strength_bucket_strength_unknown`

- title: LDM entry bucket attribution follow-up: strength_bucket=strength_unknown
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `lifecycle_decision_matrix_entry_bucket_attribution`
- lifecycle_stage: `entry`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
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
- evidence: `workorder_id=entry_bucket_source_quality_7`, `bucket_type=strength_bucket`, `bucket_key=strength_unknown`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 6. `order_lifecycle_entry_bucket_time_bucket_time_unknown`

- title: LDM entry bucket attribution follow-up: time_bucket=time_unknown
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `lifecycle_decision_matrix_entry_bucket_attribution`
- lifecycle_stage: `entry`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
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
- evidence: `workorder_id=entry_bucket_source_quality_8`, `bucket_type=time_bucket`, `bucket_key=time_unknown`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 7. `order_scalp_entry_adm_daily_tuning_coverage`

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
- evidence: `status=missing`, `joined_sample=0`, `sample_floor=20`, `prompt_applied_count=0`
- parity_contract: -
- next_postclose_metric: scalp_entry_action_decision_matrix should meet sample_floor, include all action buckets, show prompt_applied_count, and expose entry_adm_runtime_effect/forced_action evidence when runtime bias env is enabled.
- files_likely_touched: `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/sniper_state_handlers.py`, `src/engine/scalp_entry_adm_runtime.py`, `src/engine/threshold_cycle_ev_report.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_scalp_entry_action_decision_matrix.py src/tests/test_build_code_improvement_workorder.py`, `runtime_effect remains false and broker submit safety guards remain owner`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 8. `order_lifecycle_ai_context_attribution_feedback`

- title: lifecycle AI context attribution feedback coverage
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `threshold_cycle_ev`
- lifecycle_stage: `lifecycle`
- target_subsystem: `lifecycle_decision_matrix`
- route: `instrumentation_order`
- mapped_family: `lifecycle_ai_context`
- threshold_family: `lifecycle_ai_context`
- improvement_type: `instrumentation_report_provenance`
- confidence: `consensus`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep lifecycle AI context contribution visible as bounded auxiliary ADM/LDM feedback without creating real order gates or standalone threshold families.
- evidence: `context_available=False`, `prompt_stage_count=0`, `context_applied_count=0`, `replay_budget=None`
- parity_contract: -
- next_postclose_metric: lifecycle_ai_context_attribution should show context_applied_count, stage attribution, and bounded auxiliary weights that LDM policy entries can consume.
- files_likely_touched: `src/engine/lifecycle_ai_context.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/ai_engine_openai.py`, `src/engine/threshold_cycle_ev_report.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_lifecycle_ai_context.py src/tests/test_threshold_cycle_ev_report.py`, `runtime_effect remains false and context is not used as real order gate`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 9. `order_lifecycle_scale_in_bucket_arm_avg_down`

- title: LDM scale-in bucket attribution follow-up: arm=AVG_DOWN
- decision: `implement_now`
- decision_reason: LDM scale-in bucket workorder is source-only attribution/handoff instrumentation; runtime scale-in changes still require a separate approval artifact
- source_report_type: `lifecycle_decision_matrix_scale_in_bucket_attribution`
- lifecycle_stage: `scale_in`
- target_subsystem: `lifecycle_decision_matrix`
- route: `source_quality_or_bounded_tunable_candidate`
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
- evidence: `workorder_id=scale_in_bucket_source_quality_1`, `bucket_type=arm`, `bucket_key=AVG_DOWN`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.scale_in_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM scale-in bucket candidates/workorders are not propagated`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: Next postclose LDM, threshold EV, runtime approval summary, and verifier must preserve scale-in bucket candidates/workorders without runtime mutation.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 10. `order_lifecycle_scale_in_bucket_arm_pyramid`

- title: LDM scale-in bucket attribution follow-up: arm=PYRAMID
- decision: `implement_now`
- decision_reason: LDM scale-in bucket workorder is source-only attribution/handoff instrumentation; runtime scale-in changes still require a separate approval artifact
- source_report_type: `lifecycle_decision_matrix_scale_in_bucket_attribution`
- lifecycle_stage: `scale_in`
- target_subsystem: `lifecycle_decision_matrix`
- route: `source_quality_or_bounded_tunable_candidate`
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
- evidence: `workorder_id=scale_in_bucket_source_quality_2`, `bucket_type=arm`, `bucket_key=PYRAMID`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.scale_in_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM scale-in bucket candidates/workorders are not propagated`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: Next postclose LDM, threshold EV, runtime approval summary, and verifier must preserve scale-in bucket candidates/workorders without runtime mutation.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 11. `order_lifecycle_scale_in_bucket_blocker_namespace_avg_down`

- title: LDM scale-in bucket attribution follow-up: blocker_namespace=AVG_DOWN
- decision: `implement_now`
- decision_reason: LDM scale-in bucket workorder is source-only attribution/handoff instrumentation; runtime scale-in changes still require a separate approval artifact
- source_report_type: `lifecycle_decision_matrix_scale_in_bucket_attribution`
- lifecycle_stage: `scale_in`
- target_subsystem: `lifecycle_decision_matrix`
- route: `source_quality_or_bounded_tunable_candidate`
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
- evidence: `workorder_id=scale_in_bucket_source_quality_3`, `bucket_type=blocker_namespace`, `bucket_key=AVG_DOWN`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.scale_in_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM scale-in bucket candidates/workorders are not propagated`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: Next postclose LDM, threshold EV, runtime approval summary, and verifier must preserve scale-in bucket candidates/workorders without runtime mutation.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 12. `order_lifecycle_scale_in_bucket_blocker_namespace_pyramid`

- title: LDM scale-in bucket attribution follow-up: blocker_namespace=PYRAMID
- decision: `implement_now`
- decision_reason: LDM scale-in bucket workorder is source-only attribution/handoff instrumentation; runtime scale-in changes still require a separate approval artifact
- source_report_type: `lifecycle_decision_matrix_scale_in_bucket_attribution`
- lifecycle_stage: `scale_in`
- target_subsystem: `lifecycle_decision_matrix`
- route: `source_quality_or_bounded_tunable_candidate`
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
- evidence: `workorder_id=scale_in_bucket_source_quality_4`, `bucket_type=blocker_namespace`, `bucket_key=PYRAMID`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.scale_in_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM scale-in bucket candidates/workorders are not propagated`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: Next postclose LDM, threshold EV, runtime approval summary, and verifier must preserve scale-in bucket candidates/workorders without runtime mutation.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 13. `order_lifecycle_scale_in_bucket_blocker_reason_low_broken`

- title: LDM scale-in bucket attribution follow-up: blocker_reason=low_broken
- decision: `implement_now`
- decision_reason: LDM scale-in bucket workorder is source-only attribution/handoff instrumentation; runtime scale-in changes still require a separate approval artifact
- source_report_type: `lifecycle_decision_matrix_scale_in_bucket_attribution`
- lifecycle_stage: `scale_in`
- target_subsystem: `lifecycle_decision_matrix`
- route: `source_quality_or_bounded_tunable_candidate`
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
- evidence: `workorder_id=scale_in_bucket_source_quality_6`, `bucket_type=blocker_reason`, `bucket_key=low_broken`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.scale_in_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM scale-in bucket candidates/workorders are not propagated`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: Next postclose LDM, threshold EV, runtime approval summary, and verifier must preserve scale-in bucket candidates/workorders without runtime mutation.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 14. `order_lifecycle_scale_in_bucket_blocker_reason_pnl_out_of_range_0_76`

- title: LDM scale-in bucket attribution follow-up: blocker_reason=pnl_out_of_range(-0.76)
- decision: `implement_now`
- decision_reason: LDM scale-in bucket workorder is source-only attribution/handoff instrumentation; runtime scale-in changes still require a separate approval artifact
- source_report_type: `lifecycle_decision_matrix_scale_in_bucket_attribution`
- lifecycle_stage: `scale_in`
- target_subsystem: `lifecycle_decision_matrix`
- route: `source_quality_or_bounded_tunable_candidate`
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
- evidence: `workorder_id=scale_in_bucket_source_quality_9`, `bucket_type=blocker_reason`, `bucket_key=pnl_out_of_range(-0.76)`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.scale_in_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM scale-in bucket candidates/workorders are not propagated`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: Next postclose LDM, threshold EV, runtime approval summary, and verifier must preserve scale-in bucket candidates/workorders without runtime mutation.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 15. `order_lifecycle_scale_in_bucket_blocker_reason_pnl_out_of_range_0_82`

- title: LDM scale-in bucket attribution follow-up: blocker_reason=pnl_out_of_range(-0.82)
- decision: `implement_now`
- decision_reason: LDM scale-in bucket workorder is source-only attribution/handoff instrumentation; runtime scale-in changes still require a separate approval artifact
- source_report_type: `lifecycle_decision_matrix_scale_in_bucket_attribution`
- lifecycle_stage: `scale_in`
- target_subsystem: `lifecycle_decision_matrix`
- route: `source_quality_or_bounded_tunable_candidate`
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
- evidence: `workorder_id=scale_in_bucket_source_quality_7`, `bucket_type=blocker_reason`, `bucket_key=pnl_out_of_range(-0.82)`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.scale_in_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM scale-in bucket candidates/workorders are not propagated`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: Next postclose LDM, threshold EV, runtime approval summary, and verifier must preserve scale-in bucket candidates/workorders without runtime mutation.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 16. `order_lifecycle_scale_in_bucket_blocker_reason_pnl_out_of_range_0_90`

- title: LDM scale-in bucket attribution follow-up: blocker_reason=pnl_out_of_range(-0.90)
- decision: `implement_now`
- decision_reason: LDM scale-in bucket workorder is source-only attribution/handoff instrumentation; runtime scale-in changes still require a separate approval artifact
- source_report_type: `lifecycle_decision_matrix_scale_in_bucket_attribution`
- lifecycle_stage: `scale_in`
- target_subsystem: `lifecycle_decision_matrix`
- route: `source_quality_or_bounded_tunable_candidate`
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
- evidence: `workorder_id=scale_in_bucket_source_quality_10`, `bucket_type=blocker_reason`, `bucket_key=pnl_out_of_range(-0.90)`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.scale_in_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM scale-in bucket candidates/workorders are not propagated`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: Next postclose LDM, threshold EV, runtime approval summary, and verifier must preserve scale-in bucket candidates/workorders without runtime mutation.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 17. `order_lifecycle_scale_in_bucket_blocker_reason_pnl_out_of_range_0_96`

- title: LDM scale-in bucket attribution follow-up: blocker_reason=pnl_out_of_range(-0.96)
- decision: `implement_now`
- decision_reason: LDM scale-in bucket workorder is source-only attribution/handoff instrumentation; runtime scale-in changes still require a separate approval artifact
- source_report_type: `lifecycle_decision_matrix_scale_in_bucket_attribution`
- lifecycle_stage: `scale_in`
- target_subsystem: `lifecycle_decision_matrix`
- route: `source_quality_or_bounded_tunable_candidate`
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
- evidence: `workorder_id=scale_in_bucket_source_quality_8`, `bucket_type=blocker_reason`, `bucket_key=pnl_out_of_range(-0.96)`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.scale_in_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM scale-in bucket candidates/workorders are not propagated`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: Next postclose LDM, threshold EV, runtime approval summary, and verifier must preserve scale-in bucket candidates/workorders without runtime mutation.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 18. `order_lifecycle_scale_in_bucket_blocker_reason_profit_not_enough`

- title: LDM scale-in bucket attribution follow-up: blocker_reason=profit_not_enough
- decision: `implement_now`
- decision_reason: LDM scale-in bucket workorder is source-only attribution/handoff instrumentation; runtime scale-in changes still require a separate approval artifact
- source_report_type: `lifecycle_decision_matrix_scale_in_bucket_attribution`
- lifecycle_stage: `scale_in`
- target_subsystem: `lifecycle_decision_matrix`
- route: `source_quality_or_bounded_tunable_candidate`
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
- evidence: `workorder_id=scale_in_bucket_source_quality_5`, `bucket_type=blocker_reason`, `bucket_key=profit_not_enough`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.scale_in_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM scale-in bucket candidates/workorders are not propagated`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: Next postclose LDM, threshold EV, runtime approval summary, and verifier must preserve scale-in bucket candidates/workorders without runtime mutation.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 19. `order_lifecycle_bucket_discovery_entry_entry_chosen_action_action_unknown`

- title: Lifecycle bucket discovery follow-up: entry:chosen_action:action_unknown
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `entry`
- target_subsystem: `lifecycle_bucket_discovery_runtime_hook`
- route: `auto_patch_required`
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
- evidence: `bucket_id=entry:chosen_action:action_unknown`, `stage=entry`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=relax_or_recover`, `source_quality_adjusted_ev_pct=3.4568`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, intraday/postclose calibration should include the updated family input.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 20. `order_lifecycle_bucket_discovery_entry_entry_exit_rule_exit_unknown`

- title: Lifecycle bucket discovery follow-up: entry:exit_rule:exit_unknown
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `entry`
- target_subsystem: `lifecycle_bucket_discovery_runtime_hook`
- route: `auto_patch_required`
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
- evidence: `bucket_id=entry:exit_rule:exit_unknown`, `stage=entry`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=relax_or_recover`, `source_quality_adjusted_ev_pct=3.4568`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, intraday/postclose calibration should include the updated family input.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 21. `order_lifecycle_bucket_discovery_entry_entry_liquidity_bucket_liquidity_unknown`

- title: Lifecycle bucket discovery follow-up: entry:liquidity_bucket:liquidity_unknown
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `entry`
- target_subsystem: `lifecycle_bucket_discovery_runtime_hook`
- route: `auto_patch_required`
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
- evidence: `bucket_id=entry:liquidity_bucket:liquidity_unknown`, `stage=entry`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=relax_or_recover`, `source_quality_adjusted_ev_pct=3.4568`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, intraday/postclose calibration should include the updated family input.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 22. `order_lifecycle_bucket_discovery_entry_entry_overbought_bucket_overbought_unknown`

- title: Lifecycle bucket discovery follow-up: entry:overbought_bucket:overbought_unknown
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `entry`
- target_subsystem: `lifecycle_bucket_discovery_runtime_hook`
- route: `auto_patch_required`
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
- evidence: `bucket_id=entry:overbought_bucket:overbought_unknown`, `stage=entry`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=relax_or_recover`, `source_quality_adjusted_ev_pct=3.4568`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, intraday/postclose calibration should include the updated family input.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 23. `order_lifecycle_bucket_discovery_entry_entry_strength_bucket_strength_unknown`

- title: Lifecycle bucket discovery follow-up: entry:strength_bucket:strength_unknown
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `entry`
- target_subsystem: `lifecycle_bucket_discovery_runtime_hook`
- route: `auto_patch_required`
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
- evidence: `bucket_id=entry:strength_bucket:strength_unknown`, `stage=entry`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=relax_or_recover`, `source_quality_adjusted_ev_pct=3.4568`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, intraday/postclose calibration should include the updated family input.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 24. `order_lifecycle_bucket_discovery_entry_entry_time_bucket_time_unknown`

- title: Lifecycle bucket discovery follow-up: entry:time_bucket:time_unknown
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `entry`
- target_subsystem: `lifecycle_bucket_discovery_runtime_hook`
- route: `auto_patch_required`
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
- evidence: `bucket_id=entry:time_bucket:time_unknown`, `stage=entry`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=relax_or_recover`, `source_quality_adjusted_ev_pct=3.4568`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, intraday/postclose calibration should include the updated family input.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 25. `order_lifecycle_bucket_discovery_scale_in_scale_in_ai_score_source_ai_source_unknown`

- title: Lifecycle bucket discovery follow-up: scale_in:ai_score_source:ai_source_unknown
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `scale_in`
- target_subsystem: `lifecycle_bucket_discovery_runtime_hook`
- route: `auto_patch_required`
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
- evidence: `bucket_id=scale_in:ai_score_source:ai_source_unknown`, `stage=scale_in`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=hold_no_edge`, `source_quality_adjusted_ev_pct=-0.142`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, intraday/postclose calibration should include the updated family input.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 26. `order_lifecycle_bucket_discovery_scale_in_scale_in_arm_arm_unknown`

- title: Lifecycle bucket discovery follow-up: scale_in:arm:arm_unknown
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `scale_in`
- target_subsystem: `lifecycle_bucket_discovery_runtime_hook`
- route: `auto_patch_required`
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
- evidence: `bucket_id=scale_in:arm:arm_unknown`, `stage=scale_in`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=hold_no_edge`, `source_quality_adjusted_ev_pct=-0.0833`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, intraday/postclose calibration should include the updated family input.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 27. `order_lifecycle_bucket_discovery_scale_in_scale_in_blocker_namespace_blocker_namespace_unknown`

- title: Lifecycle bucket discovery follow-up: scale_in:blocker_namespace:blocker_namespace_unknown
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `scale_in`
- target_subsystem: `lifecycle_bucket_discovery_runtime_hook`
- route: `auto_patch_required`
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
- evidence: `bucket_id=scale_in:blocker_namespace:blocker_namespace_unknown`, `stage=scale_in`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=hold_no_edge`, `source_quality_adjusted_ev_pct=-0.0833`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, intraday/postclose calibration should include the updated family input.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 28. `order_lifecycle_bucket_discovery_scale_in_scale_in_blocker_reason_blocker_reason_unknown`

- title: Lifecycle bucket discovery follow-up: scale_in:blocker_reason:blocker_reason_unknown
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `scale_in`
- target_subsystem: `lifecycle_bucket_discovery_runtime_hook`
- route: `auto_patch_required`
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
- evidence: `bucket_id=scale_in:blocker_reason:blocker_reason_unknown`, `stage=scale_in`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=hold_no_edge`, `source_quality_adjusted_ev_pct=-0.0833`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, intraday/postclose calibration should include the updated family input.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 29. `order_lifecycle_entry_bucket_source_stage_wait6579_ev_cohort`

- title: LDM entry bucket attribution follow-up: source_stage=wait6579_ev_cohort
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
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
- evidence: `workorder_id=entry_bucket_source_quality_5`, `bucket_type=source_stage`, `bucket_key=wait6579_ev_cohort`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, intraday/postclose calibration should include the updated family input.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 30. `order_lifecycle_entry_bucket_stale_bucket_fresh_or_unflagged`

- title: LDM entry bucket attribution follow-up: stale_bucket=fresh_or_unflagged
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
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
- evidence: `workorder_id=entry_bucket_source_quality_6`, `bucket_type=stale_bucket`, `bucket_key=fresh_or_unflagged`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, intraday/postclose calibration should include the updated family input.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

## 자동화체인 재투입

- 구현 결과는 `2026-05-23` 이후 postclose `threshold_cycle`, `scalping_pattern_lab_automation`, `threshold_cycle_ev`가 자동으로 다시 읽는다.
- 구현자가 수동으로 threshold 값을 바꾸는 것이 아니라, source/report/provenance를 닫아 다음 calibration이 판단하게 한다.
- 다음 Codex 세션 입력 문구: `none_for_bucket_discovery_classification`

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
