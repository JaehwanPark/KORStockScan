# Code Improvement Workorder - 2026-07-03

## 목적

- Postclose 자동화가 생성한 `code_improvement_order`를 Codex 실행용 작업지시서로 변환한다.
- 입력은 scalping pattern lab automation, swing lifecycle improvement automation, swing pattern lab automation을 함께 포함할 수 있다.
- 이 문서는 repo/runtime을 직접 변경하지 않는다. 사용자가 이 문서를 Codex 세션에 넣고 구현을 요청하는 지점만 사람 개입으로 남긴다.
- 구현 후 자동화체인 재투입은 다음 postclose report, threshold calibration, daily EV report가 담당한다.

## Source

- pattern_lab_automation: `None`
- swing_improvement_automation: `-`
- swing_pattern_lab_automation: `-`
- swing_strategy_discovery_ev: `-`
- swing_lifecycle_decision_matrix: `-`
- swing_lifecycle_bucket_discovery: `-`
- threshold_cycle_ev: `-`
- lifecycle_decision_matrix: `-`
- threshold_cycle_calibration: `-`
- pipeline_event_verbosity: `-`
- observation_source_quality_audit: `/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-03.json`
- ai_watching_score_smoothing_diagnostic: `-`
- codebase_performance_workorder: `-`
- pattern_lab_currentness_audit: `-`
- pattern_lab_ai_review: `-`
- producer_gap_discovery: `-`
- stage_hook_workorder_discovery: `-`
- stage_hook_runtime_scaffold: `-`
- buy_funnel_sentinel: `/home/ubuntu/KORStockScan/data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-07-03.json`
- generated_at: `2026-07-03T14:27:44+09:00`
- generation_id: `2026-07-03-e6ef0056a643`
- source_hash: `e6ef0056a64396dc41d036fe122dca9d987b69f7af39214901372f9c09d7186e`

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
- new_order_ids: `['order_intraday_entry_blocker_rising_missed_freshness_recovery_bounded_rising_candidate_fresh_74f6fd40', 'order_observation_source_quality_raw_row_exclusion_producer_gap', 'order_one_share_threshold_latency_or_freshness_entry_hook_review', 'order_one_share_threshold_strength_momentum_vpw_entry_hook_review', 'order_rising_missed_initial_quality_feedback_loop', 'order_rising_missed_scout_loss_filter', 'order_rising_missed_scout_post_sell_bridge']`
- removed_order_ids: `[]`
- decision_changed_order_ids: `[]`

## Summary

- source_order_count: `7`
- scalping_source_order_count: `0`
- swing_source_order_count: `0`
- swing_entry_bottleneck_primary: `None`
- swing_entry_bottleneck_selected: `False`
- swing_lab_source_order_count: `0`
- swing_strategy_discovery_source_order_count: `0`
- swing_lifecycle_matrix_source_order_count: `0`
- swing_lifecycle_bucket_discovery_source_order_count: `0`
- pattern_lab_currentness_source_order_count: `0`
- pattern_lab_ai_review_source_order_count: `0`
- threshold_ev_source_order_count: `1`
- entry_hurdle_backtest_source_order_count: `0`
- lifecycle_submit_bucket_source_order_count: `0`
- lifecycle_holding_exit_bucket_source_order_count: `0`
- pipeline_event_verbosity_source_order_count: `0`
- observation_source_quality_source_order_count: `1`
- codebase_performance_source_order_count: `0`
- buy_funnel_sentinel_source_order_count: `0`
- entry_submit_drought_selected: `False`
- entry_submit_drought_handoff_missing: `False`
- panic_lifecycle_source_order_count: `0`
- selected_order_count: `7`
- non_selected_order_count: `0`
- source_decision_counts: `{'implement_now': 1, 'attach_existing_family': 6}`
- selected_decision_counts: `{'implement_now': 1, 'attach_existing_family': 6}`
- selected_route_counts: `{'source_quality_raw_row_exclusion_producer_fix': 1, 'existing_family': 6}`
- selected_implement_now_route_count: `1`
- selected_runtime_effect_false_count: `7`
- selected_unimplemented_runtime_effect_false_count: `1`
- selected_unimplemented_route_counts: `{'source_quality_raw_row_exclusion_producer_fix': 1}`
- selected_terminal_non_implement_runtime_effect_false_count: `0`
- selected_terminal_non_implement_route_counts: `{}`
- selected_implement_now_existing_implementation_count: `0`
- selected_implement_now_existing_implementation_order_ids: `[]`
- selected_implement_now_new_runtime_effect_false_count: `1`
- selected_implement_now_new_runtime_effect_false_order_ids: `['order_observation_source_quality_raw_row_exclusion_producer_gap']`
- repeat_unresolved_escalation_count: `0`
- repeat_unresolved_escalated_order_ids: `[]`
- repeat_unresolved_structural_blocker_count: `0`
- repeat_unresolved_structural_blocker_order_ids: `[]`
- root_cause_closure_status_counts: `{'implementation_done': 4, 'needs_followup_workorder': 1, 'root_cause_closed': 2}`
- implementation_done_count: `4`
- artifact_regeneration_required_count: `0`
- handoff_closed_root_cause_open_count: `0`
- root_cause_closed_count: `2`
- needs_followup_workorder_count: `1`
- root_cause_open_top: `[{'order_id': 'order_observation_source_quality_raw_row_exclusion_producer_gap', 'status': 'needs_followup_workorder', 'source_report_type': 'observation_source_quality_audit', 'threshold_family': 'observation_source_quality_audit', 'implementation_status': None, 'root_cause_signal': None}]`
- selected_terminal_non_implement_longstanding_count: `0`
- selected_terminal_non_implement_longstanding_order_ids: `[]`
- selected_longstanding_non_implement_disposition_counts: `{}`
- selected_longstanding_non_implement_action_required_order_ids: `[]`
- non_selected_decision_counts: `{}`
- non_selected_longstanding_non_implement_disposition_counts: `{}`
- non_selected_longstanding_non_implement_action_required_order_ids: `[]`
- gemini_fresh: `None`
- claude_fresh: `None`
- swing_lifecycle_audit_available: `False`
- swing_pattern_lab_automation_available: `False`
- swing_pattern_lab_fresh: `None`
- pattern_lab_currentness_status: `None`
- pattern_lab_currentness_fail_count: `None`
- pattern_lab_ai_review_status: `None`
- pattern_lab_ai_review_workorder_count: `None`
- swing_threshold_ai_status: `None`
- daily_ev_available: `False`

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

### 1. `order_observation_source_quality_raw_row_exclusion_producer_gap`

- title: Observation source-quality raw row exclusion producer gap
- decision: `implement_now`
- decision_reason: raw row exclusion protected tuning inputs, but the producer/source-quality cause must be fixed or explicitly classified so future rows are not repeatedly excluded
- source_report_type: `observation_source_quality_audit`
- lifecycle_stage: `source_quality_gate`
- target_subsystem: `runtime_instrumentation`
- route: `source_quality_raw_row_exclusion_producer_fix`
- mapped_family: `observation_source_quality_audit`
- threshold_family: `observation_source_quality_audit`
- improvement_type: `source_quality_raw_row_exclusion_producer_gap`
- confidence: `audit`
- priority: `0`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: none_direct_source_quality_attribution_only
- evidence: `status=pass`, `event_count=75534`, `warning_stage_count=0`, `warning_stages=`, `high_volume_no_source_field_stage_count=0`, `unknown_token_stage_count=0`, `review_warning_count=0`, `decision_authority=source_quality_only`, `runtime_effect=false`, `raw_row_exclusion_manifest=/home/ubuntu/KORStockScan/data/source_quality/raw_row_exclusion/2026-07-03_20260703T142019383320+0900/manifest.json`, `excluded_row_count=89`, `stage_counts={"scalp_entry_action_decision_snapshot": 89}`, `field_gap_counts={"missing_fields:buy_pressure_10t": 89, "missing_fields:curr_vs_ma5_bp": 89, "missing_fields:curr_vs_micro_vwap_bp": 89, "missing_fields:prev_5tick_seconds": 89, "missing_fields:recent_5tick_seconds": 89, "missing_fields:tick_accel_effective_recent_5tick_seconds": 89, "missing_fields:tick_acceleration_ratio": 89, "missing_fields:tick_acceleration_ratio_raw": 89}`, `exclusion_reasons={"insufficient_history": 34, "not_evaluated_context": 89, "provenance_missing": 89, "required_field_missing": 89, "source_quality_blocker": 24, "unknown_token": 14}`, `first_timestamp=2026-07-03T12:01:22.740498`, `last_timestamp=2026-07-03T14:10:39.345594`, `forbidden_uses=EV/rolling/MTD/cumulative tuning/live-auto promotion/runtime approval for excluded rows`, `required_action=fix producer provenance/source-quality cause or mark reviewed_not_available/waiting_sample_only explicitly`, `producer_hint:stage=scalp_entry_action_decision_snapshot count=89 pipeline=ENTRY_PIPELINE subsystem=scalping_entry_or_sim_producer top_reasons=not_evaluated_context,provenance_missing,required_field_missing,insufficient_history,source_quality_blocker`, `sample_row:line_no=54460 stage=scalp_entry_action_decision_snapshot record_id=15242 reasons=insufficient_history,not_evaluated_context,provenance_missing,required_field_missing gap_fields={"missing_fields": ["tick_acceleration_ratio", "tick_acceleration_ratio_raw", "recent_5tick_seconds", "prev_5tick_seconds", "tick_accel_effective_recent_5tick_seconds", "buy_pressure_10t", "curr_vs_micro_vwap_bp", "curr_vs_ma5_bp"]}`, `sample_row:line_no=54656 stage=scalp_entry_action_decision_snapshot record_id=15241 reasons=insufficient_history,not_evaluated_context,provenance_missing,required_field_missing gap_fields={"missing_fields": ["tick_acceleration_ratio", "tick_acceleration_ratio_raw", "recent_5tick_seconds", "prev_5tick_seconds", "tick_accel_effective_recent_5tick_seconds", "buy_pressure_10t", "curr_vs_micro_vwap_bp", "curr_vs_ma5_bp"]}`, `sample_row:line_no=54663 stage=scalp_entry_action_decision_snapshot record_id=15261 reasons=insufficient_history,not_evaluated_context,provenance_missing,required_field_missing gap_fields={"missing_fields": ["tick_acceleration_ratio", "tick_acceleration_ratio_raw", "recent_5tick_seconds", "prev_5tick_seconds", "tick_accel_effective_recent_5tick_seconds", "buy_pressure_10t", "curr_vs_micro_vwap_bp", "curr_vs_ma5_bp"]}`, `sample_row:line_no=54743 stage=scalp_entry_action_decision_snapshot record_id=15242 reasons=insufficient_history,not_evaluated_context,provenance_missing,required_field_missing gap_fields={"missing_fields": ["tick_acceleration_ratio", "tick_acceleration_ratio_raw", "recent_5tick_seconds", "prev_5tick_seconds", "tick_accel_effective_recent_5tick_seconds", "buy_pressure_10t", "curr_vs_micro_vwap_bp", "curr_vs_ma5_bp"]}`, `sample_row:line_no=54834 stage=scalp_entry_action_decision_snapshot record_id=15241 reasons=not_evaluated_context,provenance_missing,required_field_missing gap_fields={"missing_fields": ["tick_acceleration_ratio", "tick_acceleration_ratio_raw", "recent_5tick_seconds", "prev_5tick_seconds", "tick_accel_effective_recent_5tick_seconds", "buy_pressure_10t", "curr_vs_micro_vwap_bp", "curr_vs_ma5_bp"]}`, `sample_row:line_no=54948 stage=scalp_entry_action_decision_snapshot record_id=15241 reasons=not_evaluated_context,provenance_missing,required_field_missing,source_quality_blocker gap_fields={"missing_fields": ["tick_acceleration_ratio", "tick_acceleration_ratio_raw", "recent_5tick_seconds", "prev_5tick_seconds", "tick_accel_effective_recent_5tick_seconds", "buy_pressure_10t", "curr_vs_micro_vwap_bp", "curr_vs_ma5_bp"]}`, `sample_row:line_no=54954 stage=scalp_entry_action_decision_snapshot record_id=15241 reasons=not_evaluated_context,provenance_missing,required_field_missing,source_quality_blocker,unknown_token gap_fields={"missing_fields": ["tick_acceleration_ratio", "tick_acceleration_ratio_raw", "recent_5tick_seconds", "prev_5tick_seconds", "tick_accel_effective_recent_5tick_seconds", "buy_pressure_10t", "curr_vs_micro_vwap_bp", "curr_vs_ma5_bp"]}`, `sample_row:line_no=55030 stage=scalp_entry_action_decision_snapshot record_id=15242 reasons=not_evaluated_context,provenance_missing,required_field_missing gap_fields={"missing_fields": ["tick_acceleration_ratio", "tick_acceleration_ratio_raw", "recent_5tick_seconds", "prev_5tick_seconds", "tick_accel_effective_recent_5tick_seconds", "buy_pressure_10t", "curr_vs_micro_vwap_bp", "curr_vs_ma5_bp"]}`
- parity_contract: -
- next_postclose_metric: observation_source_quality_audit.warning_stage_count and high_volume_no_source_field_stage_count
- files_likely_touched: `src/engine/observation_source_quality_audit.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_observation_source_quality_audit.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `-`
- root_cause_closure_status: `needs_followup_workorder`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: After implementation, rerun observation_source_quality_audit and code improvement workorder; raw_row_exclusion.excluded_row_count should fall or remaining exclusions must carry reviewed not_available/waiting_sample-only provenance.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 2. `order_rising_missed_initial_quality_feedback_loop`

- title: rising missed initial quality feedback loop
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `rising_missed_scout_workorder`
- lifecycle_stage: `entry`
- target_subsystem: `rising_missed_entry_classifier`
- route: `existing_family`
- mapped_family: `rising_missed_initial_quality_feedback_loop`
- threshold_family: `rising_missed_initial_quality_feedback_loop`
- improvement_type: `source_only_intraday_feedback_workorder`
- confidence: `same_day_source_only`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Feed same-day rising-missed entries that required at least two average-down attempts back into the rising-missed classifier as initial-quality fail/review labels before expansion.
- evidence: `rising_missed_avg_down_ge2_count=4`, `initial_quality_fail_count=3`, `feedback_label_counts=rising_missed_initial_quality_fail=3,rising_missed_scale_in_rescue_warning=1`, `runtime_effect=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/monitoring/rising_missed_intraday_feedback.py`, `src/engine/scalping/rising_missed_one_share_entry.py`, `src/engine/monitoring/intraday_entry_blocker_diagnostics.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_intraday_feedback.py src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py`, `feedback remains source-only and cannot mutate intraday runtime thresholds, broker/order guards, provider route, bot state, or scale-in quantity/caps`
- implementation_status: `implemented`
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "source_only_intraday_feedback_no_runtime_mutation", "implementation_type": "rising_missed_avg_down_ge2_intraday_feedback_bridge", "initial_quality_fail_count": 3, "rising_missed_avg_down_ge2_count": 4, "root_cause_closure_status_hint": "implementation_done", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 3. `order_intraday_entry_blocker_rising_missed_freshness_recovery_bounded_rising_candidate_fresh_74f6fd40`

- title: bounded rising candidate freshness recheck: multi_symbol
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `intraday_entry_blocker_diagnostics`
- lifecycle_stage: `entry`
- target_subsystem: `entry_freshness`
- route: `existing_family`
- mapped_family: `bounded_freshness_recheck`
- threshold_family: `bounded_freshness_recheck`
- improvement_type: `source_quality_freshness_repair`
- confidence: `intraday_diagnostic`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve source-quality handoff for rising missed candidates before any BUY/submit threshold judgment; no broker/order/provider/runtime authority.
- evidence: `workorder_type=bounded_rising_candidate_freshness_recheck`, `stock_code=multi_symbol`, `stock_name=5 rising candidates`, `event_count=69`, `latest_reason=stale_or_history_gap`, `diagnostic_quote_age_stale=47`, `pre_ai_stale_or_history_gap=22`, `latest_stage=aggregate`, `source_symbol_count=5`, `top_symbols=095500,010140,376900,441270,222800`
- parity_contract: -
- next_postclose_metric: intraday_entry_blocker_diagnostics source_quality_workorders should shrink or carry explicit reviewed not-applicable provenance after regenerated diagnostics.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/monitoring/intraday_entry_blocker_diagnostics.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_intraday_entry_blocker_diagnostics.py src/tests/test_build_code_improvement_workorder.py`, `runtime_effect remains false; stale submit, broker, order, provider, bot, and threshold guards remain unchanged`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "source_quality_only", "implementation_type": "bounded_freshness_recheck_aggregate_source_quality_provenance", "metric_role": "source_quality_gate", "root_cause_closure_status_hint": "implementation_done", "runtime_effect": false, "source_implementation_statuses": ["implemented_source_quality_contract_available"], "source_symbol_count": 5}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_source_quality_contract_available", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_intraday_entry_blocker_rising_missed_freshness_recovery_bounded_rising_candidate_fresh_74f6fd40", "repeat_signature": "sig:intraday_entry_blocker_diagnostics|entry_freshness|entry|source_quality_freshness_repair|bounded_freshness_recheck|bounded_rising_candidate_freshness_recheck_multi_symbol", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 4. `order_one_share_threshold_latency_or_freshness_entry_hook_review`

- title: one-share threshold opportunity entry hook review: latency_or_freshness
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `one_share_threshold_opportunity`
- lifecycle_stage: `entry`
- target_subsystem: `entry_latency_freshness_recheck`
- route: `existing_family`
- mapped_family: `latency_classifier_runtime_profile`
- threshold_family: `latency_classifier_runtime_profile`
- improvement_type: `source_only_entry_hook_workorder`
- confidence: `rolling_source_only`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Use one-share forced-entry post-sell outcomes to improve bounded entry hook selection without treating one-share PnL as standalone real-order approval evidence.
- evidence: `threshold_group=latency_or_freshness`, `sample=14`, `valid_profit_sample=14`, `profitable_count=11`, `loss_or_flat_count=3`, `equal_weight_avg_profit_pct=0.172857`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/monitoring/one_share_threshold_opportunity.py`, `src/engine/scalping/entry_opportunity_recheck.py`, `src/engine/sniper_state_handlers.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_one_share_threshold_opportunity.py src/tests/test_entry_opportunity_recheck.py src/tests/test_build_code_improvement_workorder.py`, `source-only audit must not mutate intraday runtime thresholds, broker/order guards, provider route, bot state, quantity, or caps`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"actual_order_submitted": false, "allowed_runtime_apply": false, "broker_order_forbidden": true, "decision_authority": "source_only_threshold_opportunity_audit", "equal_weight_avg_profit_pct": 0.172857, "forbidden_uses": ["runtime_threshold_mutation", "buy_score_threshold_relaxation_without_preopen_apply", "stale_submit_bypass", "broker_guard_bypass", "order_guard_relaxation", "provider_route_change", "bot_restart", "forced_one_share_success_counting", "real_execution_quality_approval"], "implementation_type": "one_share_threshold_opportunity_audit", "implemented_scope": "source-only threshold group audit and code-improvement order provenance", "mapped_family": "latency_classifier_runtime_profile", "primary_decision_metric": "equal_weight_avg_profit_pct", "requires_separate_runtime_apply_candidate": true, "runtime_effect": false, "runtime_mutation_allowed": false, "sample": 14, "source_quality_gate": "record_id_joined_forced_one_share_event_to_post_sell_outcome", "threshold_group": "latency_or_freshness", "valid_profit_sample": 14}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 5. `order_one_share_threshold_strength_momentum_vpw_entry_hook_review`

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
- evidence: `threshold_group=strength_momentum_vpw`, `sample=14`, `valid_profit_sample=14`, `profitable_count=11`, `loss_or_flat_count=3`, `equal_weight_avg_profit_pct=0.172857`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/monitoring/one_share_threshold_opportunity.py`, `src/engine/scalping/entry_opportunity_recheck.py`, `src/engine/sniper_state_handlers.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_one_share_threshold_opportunity.py src/tests/test_entry_opportunity_recheck.py src/tests/test_build_code_improvement_workorder.py`, `source-only audit must not mutate intraday runtime thresholds, broker/order guards, provider route, bot state, quantity, or caps`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"actual_order_submitted": false, "allowed_runtime_apply": false, "broker_order_forbidden": true, "decision_authority": "source_only_threshold_opportunity_audit", "equal_weight_avg_profit_pct": 0.172857, "forbidden_uses": ["runtime_threshold_mutation", "buy_score_threshold_relaxation_without_preopen_apply", "stale_submit_bypass", "broker_guard_bypass", "order_guard_relaxation", "provider_route_change", "bot_restart", "forced_one_share_success_counting", "real_execution_quality_approval"], "implementation_type": "one_share_threshold_opportunity_audit", "implemented_scope": "source-only threshold group audit and code-improvement order provenance", "mapped_family": "entry_strength_momentum_recheck", "primary_decision_metric": "equal_weight_avg_profit_pct", "requires_separate_runtime_apply_candidate": true, "runtime_effect": false, "runtime_mutation_allowed": false, "sample": 14, "source_quality_gate": "record_id_joined_forced_one_share_event_to_post_sell_outcome", "threshold_group": "strength_momentum_vpw", "valid_profit_sample": 14}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 6. `order_rising_missed_scout_loss_filter`

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
- evidence: `loser_count=3`, `loser_avg_profit_rate=-4.5967`, `losers_also_had_latency_pass=True`, `losers_also_had_order_bundle_submitted=True`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/monitoring/rising_missed_scout_workorder.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py`, `loss filter is source-only and does not relax stops or broker/order guards`
- implementation_status: `implemented`
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "source_only_operational_workorder", "implementation_type": "forced_scout_loss_filter_source_split", "joined_post_sell_loser_count": 3, "root_cause_closure_status_hint": "implementation_done", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_rising_missed_scout_loss_filter", "repeat_signature": "sig:rising_missed_scout_workorder|entry_risk_filter|entry|source_only_operational_workorder|rising_missed_scout_loss_filter|rising_missed_scout_loss_filter_before_any_expansion", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 7. `order_rising_missed_scout_post_sell_bridge`

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
- evidence: `winner_count=11`, `loser_count=3`, `winner_avg_profit_rate=1.4736`, `current_missed_count=5`, `current_missed_eligible_count=0`, `all_winner_rows_had_latency_pass=True`, `all_winner_rows_had_order_bundle_submitted=True`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/monitoring/rising_missed_scout_workorder.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py`, `forced scout remains excluded from normal BUY/submit/fill success counts`, `runtime_effect remains false until a separate approved runtime family exists`
- implementation_status: `implemented`
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "source_only_operational_workorder", "implementation_type": "forced_scout_post_sell_source_bridge", "joined_post_sell_loser_count": 3, "joined_post_sell_winner_count": 11, "root_cause_closure_status_hint": "implementation_done", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_rising_missed_scout_post_sell_bridge", "repeat_signature": "sig:rising_missed_scout_workorder|entry_freshness|entry|source_only_operational_workorder|rising_missed_scout_post_sell_bridge|rising_missed_scout_post_sell_bridge_for_normal_entry_recheck", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

## 자동화체인 재투입

- 구현 결과는 `2026-07-04` 이후 postclose `threshold_cycle`, `scalping_pattern_lab_automation`, `threshold_cycle_ev`가 자동으로 다시 읽는다.
- 구현자가 수동으로 threshold 값을 바꾸는 것이 아니라, source/report/provenance를 닫아 다음 calibration이 판단하게 한다.
- 다음 Codex 세션 입력 문구: `none_for_bucket_discovery_classification`

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
