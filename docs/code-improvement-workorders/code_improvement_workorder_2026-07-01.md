# Code Improvement Workorder - 2026-07-01

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
- observation_source_quality_audit: `-`
- ai_watching_score_smoothing_diagnostic: `-`
- codebase_performance_workorder: `-`
- pattern_lab_currentness_audit: `-`
- pattern_lab_ai_review: `-`
- producer_gap_discovery: `-`
- stage_hook_workorder_discovery: `-`
- stage_hook_runtime_scaffold: `-`
- buy_funnel_sentinel: `/home/ubuntu/KORStockScan/data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-07-01.json`
- generated_at: `2026-07-01T13:32:58+09:00`
- generation_id: `2026-07-01-3dbf407101b9`
- source_hash: `3dbf407101b96919a1f1f5be385493f58f9b71b0b796e093d1361cdd6640f567`

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
- previous_generation_id: `2026-07-01-500c09b2e38f`
- previous_source_hash: `500c09b2e38fef1f4be7d7d5dcf554b2663e64c7b19e403bf76de272d77a5ded`
- new_order_ids: `['order_intraday_entry_blocker_repeated_zero_strength_history_scanner_strength_momentum_histor_86ed8c1c', 'order_rising_missed_scout_scale_in_price_guard_split', 'order_rising_missed_scout_scale_in_qty_evidence_split']`
- removed_order_ids: `[]`
- decision_changed_order_ids: `[]`

## Summary

- source_order_count: `6`
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
- threshold_ev_source_order_count: `0`
- lifecycle_submit_bucket_source_order_count: `0`
- lifecycle_holding_exit_bucket_source_order_count: `0`
- pipeline_event_verbosity_source_order_count: `0`
- observation_source_quality_source_order_count: `0`
- codebase_performance_source_order_count: `0`
- buy_funnel_sentinel_source_order_count: `0`
- entry_submit_drought_selected: `False`
- entry_submit_drought_handoff_missing: `False`
- panic_lifecycle_source_order_count: `0`
- selected_order_count: `6`
- non_selected_order_count: `0`
- source_decision_counts: `{'implement_now': 6}`
- selected_decision_counts: `{'implement_now': 6}`
- selected_route_counts: `{'instrumentation_order': 6}`
- selected_implement_now_route_count: `6`
- selected_runtime_effect_false_count: `6`
- selected_unimplemented_runtime_effect_false_count: `6`
- selected_unimplemented_route_counts: `{'instrumentation_order': 6}`
- selected_terminal_non_implement_runtime_effect_false_count: `0`
- selected_terminal_non_implement_route_counts: `{}`
- selected_implement_now_existing_implementation_count: `0`
- selected_implement_now_existing_implementation_order_ids: `[]`
- selected_implement_now_new_runtime_effect_false_count: `6`
- selected_implement_now_new_runtime_effect_false_order_ids: `['order_intraday_entry_blocker_repeated_zero_strength_history_scanner_strength_momentum_histor_86ed8c1c', 'order_intraday_entry_blocker_rising_missed_freshness_recovery_bounded_rising_candidate_fresh_74f6fd40', 'order_rising_missed_scout_loss_filter', 'order_rising_missed_scout_post_sell_bridge', 'order_rising_missed_scout_scale_in_price_guard_split', 'order_rising_missed_scout_scale_in_qty_evidence_split']`
- repeat_unresolved_escalation_count: `0`
- repeat_unresolved_escalated_order_ids: `[]`
- repeat_unresolved_structural_blocker_count: `0`
- repeat_unresolved_structural_blocker_order_ids: `[]`
- root_cause_closure_status_counts: `{'needs_followup_workorder': 6}`
- implementation_done_count: `0`
- artifact_regeneration_required_count: `0`
- handoff_closed_root_cause_open_count: `0`
- root_cause_closed_count: `0`
- needs_followup_workorder_count: `6`
- root_cause_open_top: `[{'order_id': 'order_intraday_entry_blocker_repeated_zero_strength_history_scanner_strength_momentum_histor_86ed8c1c', 'status': 'needs_followup_workorder', 'source_report_type': 'intraday_entry_blocker_diagnostics', 'threshold_family': 'scanner_strength_history_missing', 'implementation_status': None, 'root_cause_signal': None}, {'order_id': 'order_intraday_entry_blocker_rising_missed_freshness_recovery_bounded_rising_candidate_fresh_74f6fd40', 'status': 'needs_followup_workorder', 'source_report_type': 'intraday_entry_blocker_diagnostics', 'threshold_family': 'bounded_freshness_recheck', 'implementation_status': None, 'root_cause_signal': None}, {'order_id': 'order_rising_missed_scout_loss_filter', 'status': 'needs_followup_workorder', 'source_report_type': 'rising_missed_scout_workorder', 'threshold_family': 'rising_missed_scout_loss_filter', 'implementation_status': None, 'root_cause_signal': None}, {'order_id': 'order_rising_missed_scout_post_sell_bridge', 'status': 'needs_followup_workorder', 'source_report_type': 'rising_missed_scout_workorder', 'threshold_family': 'rising_missed_scout_post_sell_bridge', 'implementation_status': None, 'root_cause_signal': None}, {'order_id': 'order_rising_missed_scout_scale_in_price_guard_split', 'status': 'needs_followup_workorder', 'source_report_type': 'rising_missed_scout_workorder', 'threshold_family': 'rising_missed_scout_scale_in_price_guard_split', 'implementation_status': None, 'root_cause_signal': None}, {'order_id': 'order_rising_missed_scout_scale_in_qty_evidence_split', 'status': 'needs_followup_workorder', 'source_report_type': 'rising_missed_scout_workorder', 'threshold_family': 'rising_missed_scout_scale_in_qty_evidence_split', 'implementation_status': None, 'root_cause_signal': None}]`
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

### 1. `order_intraday_entry_blocker_repeated_zero_strength_history_scanner_strength_momentum_histor_86ed8c1c`

- title: scanner strength momentum history missing: 007860
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `intraday_entry_blocker_diagnostics`
- lifecycle_stage: `entry`
- target_subsystem: `entry_freshness`
- route: `instrumentation_order`
- mapped_family: `scanner_strength_history_missing`
- threshold_family: `scanner_strength_history_missing`
- improvement_type: `source_quality_history_repair`
- confidence: `intraday_diagnostic`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve source-quality handoff for rising missed candidates before any BUY/submit threshold judgment; no broker/order/provider/runtime authority.
- evidence: `workorder_type=scanner_strength_momentum_history_missing`, `stock_code=007860`, `stock_name=서연`, `event_count=3`, `latest_stage=scalping_scanner_fast_precheck`
- parity_contract: -
- next_postclose_metric: intraday_entry_blocker_diagnostics source_quality_workorders should shrink or carry explicit reviewed not-applicable provenance after regenerated diagnostics.
- files_likely_touched: `src/engine/kiwoom_websocket.py`, `src/engine/sniper_state_handlers.py`, `src/engine/monitoring/intraday_entry_blocker_diagnostics.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_intraday_entry_blocker_diagnostics.py src/tests/test_build_code_improvement_workorder.py`, `runtime_effect remains false; stale submit, broker, order, provider, bot, and threshold guards remain unchanged`
- implementation_status: `-`
- root_cause_closure_status: `needs_followup_workorder`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 2. `order_intraday_entry_blocker_rising_missed_freshness_recovery_bounded_rising_candidate_fresh_74f6fd40`

- title: bounded rising candidate freshness recheck: multi_symbol
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `intraday_entry_blocker_diagnostics`
- lifecycle_stage: `entry`
- target_subsystem: `entry_freshness`
- route: `instrumentation_order`
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
- evidence: `workorder_type=bounded_rising_candidate_freshness_recheck`, `stock_code=multi_symbol`, `stock_name=13 rising candidates`, `event_count=195`, `latest_reason=stale_or_history_gap`, `diagnostic_quote_age_stale=188`, `pre_ai_stale_or_history_gap=7`, `latest_stage=aggregate`, `source_symbol_count=13`, `top_symbols=045100,347700,006340,038500,000500,073240,006360,037350`
- parity_contract: -
- next_postclose_metric: intraday_entry_blocker_diagnostics source_quality_workorders should shrink or carry explicit reviewed not-applicable provenance after regenerated diagnostics.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/monitoring/intraday_entry_blocker_diagnostics.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_intraday_entry_blocker_diagnostics.py src/tests/test_build_code_improvement_workorder.py`, `runtime_effect remains false; stale submit, broker, order, provider, bot, and threshold guards remain unchanged`
- implementation_status: `-`
- root_cause_closure_status: `needs_followup_workorder`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 3. `order_rising_missed_scout_loss_filter`

- title: rising missed scout loss filter before any expansion
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `rising_missed_scout_workorder`
- lifecycle_stage: `entry`
- target_subsystem: `entry_risk_filter`
- route: `instrumentation_order`
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
- evidence: `loser_count=6`, `loser_avg_profit_rate=-3.365`, `losers_also_had_latency_pass=True`, `losers_also_had_order_bundle_submitted=True`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/monitoring/rising_missed_scout_workorder.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py`, `loss filter is source-only and does not relax stops or broker/order guards`
- implementation_status: `-`
- root_cause_closure_status: `needs_followup_workorder`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 4. `order_rising_missed_scout_post_sell_bridge`

- title: rising missed scout post-sell bridge for normal-entry recheck
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `rising_missed_scout_workorder`
- lifecycle_stage: `entry`
- target_subsystem: `entry_freshness`
- route: `instrumentation_order`
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
- evidence: `winner_count=17`, `loser_count=6`, `winner_avg_profit_rate=2.0112`, `current_missed_count=14`, `current_missed_eligible_count=0`, `all_winner_rows_had_latency_pass=True`, `all_winner_rows_had_order_bundle_submitted=True`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/monitoring/rising_missed_scout_workorder.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py`, `forced scout remains excluded from normal BUY/submit/fill success counts`, `runtime_effect remains false until a separate approved runtime family exists`
- implementation_status: `-`
- root_cause_closure_status: `needs_followup_workorder`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 5. `order_rising_missed_scout_scale_in_price_guard_split`

- title: rising missed scout profitable scale-in price guard split
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `rising_missed_scout_workorder`
- lifecycle_stage: `scale_in`
- target_subsystem: `scale_in_price_guard`
- route: `instrumentation_order`
- mapped_family: `rising_missed_scout_scale_in_price_guard_split`
- threshold_family: `rising_missed_scout_scale_in_price_guard_split`
- improvement_type: `source_only_scale_in_bottleneck_workorder`
- confidence: `same_day_source_only`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Split profitable forced-scout PYRAMID candidates that reached scale-in price guard into micro-vwap and quote-stale repair buckets before any scale-in guard or quantity change.
- evidence: `profitable_forced_scout_count=17`, `record_with_scale_in_event_count=17`, `pyramid_ok_record_count=17`, `price_guard_block_record_count=16`, `scale_in_executed_record_count=4`, `price_guard_reason_counts=micro_vwap_bp>60.0=25,quote_stale=19`, `pyramid_reason_counts=profit_not_enough=170,scalping_pyramid_ok=57,trend_not_strong=7,scale_in_cooldown=2`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/monitoring/rising_missed_scout_workorder.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py`, `price guard split remains source-only and does not bypass stale quote, broker, or order guards`
- implementation_status: `-`
- root_cause_closure_status: `needs_followup_workorder`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 6. `order_rising_missed_scout_scale_in_qty_evidence_split`

- title: rising missed scout scale-in quantity and evidence blocker split
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `rising_missed_scout_workorder`
- lifecycle_stage: `scale_in`
- target_subsystem: `scale_in_quantity_and_evidence`
- route: `instrumentation_order`
- mapped_family: `rising_missed_scout_scale_in_qty_evidence_split`
- threshold_family: `rising_missed_scout_scale_in_qty_evidence_split`
- improvement_type: `source_only_scale_in_bottleneck_workorder`
- confidence: `same_day_source_only`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Separate exposure-cap blocks from pyramid evidence-insufficient blocks for profitable forced-scout scale-in candidates; no position cap release or real scale-in approval.
- evidence: `profitable_forced_scout_count=17`, `qty_block_record_count=4`, `scale_in_executed_record_count=4`, `qty_block_reason_counts=pyramid_exposure_cap=5,pyramid_evidence_insufficient:ai_score_ok,buy_pressure_ok=2,pyramid_evidence_insufficient:tick_accel_ok=2,pyramid_evidence_insufficient:buy_pressure_ok,tick_accel_ok=1`, `price_guard_block_record_count=16`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/monitoring/rising_missed_scout_workorder.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py`, `qty/evidence split remains source-only and does not release position cap or quantity guard`
- implementation_status: `-`
- root_cause_closure_status: `needs_followup_workorder`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

## 자동화체인 재투입

- 구현 결과는 `2026-07-02` 이후 postclose `threshold_cycle`, `scalping_pattern_lab_automation`, `threshold_cycle_ev`가 자동으로 다시 읽는다.
- 구현자가 수동으로 threshold 값을 바꾸는 것이 아니라, source/report/provenance를 닫아 다음 calibration이 판단하게 한다.
- 다음 Codex 세션 입력 문구: `none_for_bucket_discovery_classification`

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
