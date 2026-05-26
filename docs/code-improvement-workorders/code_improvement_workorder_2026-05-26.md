# Code Improvement Workorder - 2026-05-26

## 목적

- Postclose 자동화가 생성한 `code_improvement_order`를 Codex 실행용 작업지시서로 변환한다.
- 입력은 scalping pattern lab automation, swing lifecycle improvement automation, swing pattern lab automation을 함께 포함할 수 있다.
- 이 문서는 repo/runtime을 직접 변경하지 않는다. 사용자가 이 문서를 Codex 세션에 넣고 구현을 요청하는 지점만 사람 개입으로 남긴다.
- 구현 후 자동화체인 재투입은 다음 postclose report, threshold calibration, daily EV report가 담당한다.

## Source

- pattern_lab_automation: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-26.json`
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
- codebase_performance_workorder: `-`
- pattern_lab_currentness_audit: `-`
- pattern_lab_ai_review: `-`
- producer_gap_discovery: `/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-05-26.json`
- buy_funnel_sentinel: `/home/ubuntu/KORStockScan/data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-05-26.json`
- generated_at: `2026-05-26T15:57:37+09:00`
- generation_id: `2026-05-26-50884f69a2c9`
- source_hash: `50884f69a2c9a224ac94236ed524d60c159ff2b9517d393eb1124faf35948c5d`

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
- previous_generation_id: `2026-05-26-50884f69a2c9`
- previous_source_hash: `50884f69a2c9a224ac94236ed524d60c159ff2b9517d393eb1124faf35948c5d`
- new_order_ids: `[]`
- removed_order_ids: `[]`
- decision_changed_order_ids: `[]`

## Summary

- source_order_count: `12`
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
- threshold_ev_source_order_count: `6`
- lifecycle_submit_bucket_source_order_count: `0`
- pipeline_event_verbosity_source_order_count: `0`
- observation_source_quality_source_order_count: `0`
- codebase_performance_source_order_count: `0`
- buy_funnel_sentinel_source_order_count: `6`
- entry_submit_drought_selected: `True`
- entry_submit_drought_handoff_missing: `False`
- panic_lifecycle_source_order_count: `0`
- selected_order_count: `12`
- decision_counts: `{'implement_now': 12}`
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

### 1. `order_entry_submit_drought_auto_resolution`

- title: Entry submit drought automatic resolution handoff
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `buy_funnel_sentinel`
- lifecycle_stage: `entry_submit`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
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
- evidence: `ai_confirmed_unique=169`, `budget_pass_unique=81`, `latency_pass_unique=37`, `submitted_unique=20`, `submitted_to_ai_pct=11.8`, `submitted_to_budget_pct=24.7`, `blocker:blocked_swing_score_vpw:-=138819`, `blocker:blocked_overbought:-=20849`, `blocker:blocked_strength_momentum:below_strength_base=11868`, `upstream:blocked_ai_score:score_62.0=1247`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=738`, `upstream:first_ai_wait:-=344`, `latency:latency_block:latency_state_danger=2382`
- parity_contract: -
- next_postclose_metric: SUBMIT_DROUGHT_CRITICAL must produce a selected implement_now workorder and the next postclose LDM/runtime summary must show submit blocker attribution.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/threshold_cycle_ev_report.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 2. `order_entry_broker_receipt_contract_gap_review`

- title: Entry broker receipt contract gap review
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `buy_funnel_sentinel`
- lifecycle_stage: `entry_submit`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
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
- evidence: `ai_confirmed_unique=169`, `budget_pass_unique=81`, `latency_pass_unique=37`, `submitted_unique=20`, `submitted_to_ai_pct=11.8`, `submitted_to_budget_pct=24.7`, `blocker:blocked_swing_score_vpw:-=138819`, `blocker:blocked_overbought:-=20849`, `blocker:blocked_strength_momentum:below_strength_base=11868`, `upstream:blocked_ai_score:score_62.0=1247`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=738`, `upstream:first_ai_wait:-=344`, `latency:latency_block:latency_state_danger=2382`, `weak_contract_gap=broker_receipt_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 3. `order_entry_fill_quality_contract_gap_review`

- title: Entry fill quality contract gap review
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `buy_funnel_sentinel`
- lifecycle_stage: `entry_submit`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
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
- evidence: `ai_confirmed_unique=169`, `budget_pass_unique=81`, `latency_pass_unique=37`, `submitted_unique=20`, `submitted_to_ai_pct=11.8`, `submitted_to_budget_pct=24.7`, `blocker:blocked_swing_score_vpw:-=138819`, `blocker:blocked_overbought:-=20849`, `blocker:blocked_strength_momentum:below_strength_base=11868`, `upstream:blocked_ai_score:score_62.0=1247`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=738`, `upstream:first_ai_wait:-=344`, `latency:latency_block:latency_state_danger=2382`, `weak_contract_gap=fill_quality_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 4. `order_entry_post_submit_contract_gap_review`

- title: Entry post-submit contract gap review
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `buy_funnel_sentinel`
- lifecycle_stage: `entry_submit`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
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
- evidence: `ai_confirmed_unique=169`, `budget_pass_unique=81`, `latency_pass_unique=37`, `submitted_unique=20`, `submitted_to_ai_pct=11.8`, `submitted_to_budget_pct=24.7`, `blocker:blocked_swing_score_vpw:-=138819`, `blocker:blocked_overbought:-=20849`, `blocker:blocked_strength_momentum:below_strength_base=11868`, `upstream:blocked_ai_score:score_62.0=1247`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=738`, `upstream:first_ai_wait:-=344`, `latency:latency_block:latency_state_danger=2382`, `weak_contract_gap=post_submit_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 5. `order_entry_source_taxonomy_contract_gap_review`

- title: Entry source taxonomy contract gap review
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `buy_funnel_sentinel`
- lifecycle_stage: `entry_submit`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
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
- evidence: `ai_confirmed_unique=169`, `budget_pass_unique=81`, `latency_pass_unique=37`, `submitted_unique=20`, `submitted_to_ai_pct=11.8`, `submitted_to_budget_pct=24.7`, `blocker:blocked_swing_score_vpw:-=138819`, `blocker:blocked_overbought:-=20849`, `blocker:blocked_strength_momentum:below_strength_base=11868`, `upstream:blocked_ai_score:score_62.0=1247`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=738`, `upstream:first_ai_wait:-=344`, `latency:latency_block:latency_state_danger=2382`, `weak_contract_gap=source_taxonomy_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`, `taxonomy_leakage_labels=['blocked_swing_score_vpw:-', 'blocked_swing_gap:-']`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 6. `order_entry_telegram_post_submit_contract_gap_review`

- title: Entry Telegram post-submit contract gap review
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `buy_funnel_sentinel`
- lifecycle_stage: `entry_submit`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
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
- evidence: `ai_confirmed_unique=169`, `budget_pass_unique=81`, `latency_pass_unique=37`, `submitted_unique=20`, `submitted_to_ai_pct=11.8`, `submitted_to_budget_pct=24.7`, `blocker:blocked_swing_score_vpw:-=138819`, `blocker:blocked_overbought:-=20849`, `blocker:blocked_strength_momentum:below_strength_base=11868`, `upstream:blocked_ai_score:score_62.0=1247`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=738`, `upstream:first_ai_wait:-=344`, `latency:latency_block:latency_state_danger=2382`, `weak_contract_gap=telegram_post_submit_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 7. `order_producer_gap_discovery_producer_gap_sim_stop_recovery_gap_missing`

- title: Implement missing producer: sim_stop_recovery_gap_missing
- decision: `implement_now`
- decision_reason: producer gap discovery high-priority order is source-only missing producer work; implementation still requires Codex implement_now and cannot mutate runtime/order/provider/bot state
- source_report_type: `producer_gap_discovery`
- lifecycle_stage: `exit`
- target_subsystem: `post_sell.counterfactual.sim_stop_recovery_counterfactual_producer`
- route: `implement_now`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `sim_stop_recovery_gap_missing`
- confidence: `high`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve source-quality adjusted EV attribution by making the missing producer observable.
- evidence: `sim_stop_or_loss_rows=597`, `gap=sim stop/recovery variants need a sim-first source producer independent of real exits`, `required_producer=sim_stop_recovery_counterfactual_producer`, `ai_priority=critical`, `ai_route=implement_now`
- parity_contract: -
- next_postclose_metric: producer_gap_discovery.producer_gap_sim_stop_recovery_gap_missing
- files_likely_touched: `src/producers/post_sell/sim_stop_recovery_counterfactual_producer.py`, `src/features/post_sell/stop_recovery_features.py`, `src/reports/post_sell/rolling_stop_recovery_report.py`
- acceptance_tests: `The producer emits stop-recovery rows for the 597 sim stop/loss cases with recovery metrics and join-quality fields.`, `Hard/protect/emergency stop cases are labeled observational baselines rather than override candidates.`, `Incomplete candidate-only days are flagged and excluded from completed-evaluation aggregates.`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun producer_gap_discovery, code improvement workorder, threshold EV, runtime summary, and postclose verifier.

Runtime hook candidate:

- hook_name: `stop_recovery_review_probe`
- stage: `exit`
- initial_authority: `source_only_proposal`
- apply_boundary: `postclose_artifact_to_next_preopen_candidate_only`
- action_namespace: `EXIT_CONFIRM`, `HOLD_REVIEW`
- eligible_after: `dedicated_source_only_producer_implemented`, `rolling_completed_sim_ev_positive`, `source_quality_pass`, `runtime_hook_mapping_test_passed`, `rollback_guard_defined`
- safety_vetoes: `hard_stop`, `protect_stop`, `emergency_stop`, `broker_guard`, `account_guard`, `order_guard`, `quantity_guard`, `cooldown_guard`, `stale_quote_guard`
- rollback_guards: `max_defer_seconds_exceeded`, `max_review_ticks_exceeded`, `deferred_exit_loss_worsen_breach`, `ws_or_ofi_source_stale`, `stable_bearish_ofi_confirm`, `post_apply_attribution_breach`
- required_source_artifacts: `sim_stop_recovery_counterfactual_producer`
- required_ev_evidence: `completed_sim_equal_weight_avg_profit_pct_positive`, `source_quality_adjusted_ev_pct_positive`, `strict_chronology_sample_floor_pass`
- forbidden_uses: `account guard bypass`, `bot restart`, `broker guard bypass`, `broker order submit`, `cooldown guard bypass`, `emergency stop override`, `entry decision override`, `exit decision override`, `hard stop override`, `position cap release`, `protect stop override`, `provider change`, `quantity guard bypass`, `real order enablement`, `threshold mutation`

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 8. `order_producer_gap_discovery_producer_gap_limit_up_plateau_breakdown_exit_missing`

- title: Implement missing producer: limit_up_plateau_breakdown_exit_missing
- decision: `implement_now`
- decision_reason: producer gap discovery high-priority order is source-only missing producer work; implementation still requires Codex implement_now and cannot mutate runtime/order/provider/bot state
- source_report_type: `producer_gap_discovery`
- lifecycle_stage: `exit`
- target_subsystem: `post_sell.counterfactual.plateau_breakdown_exit_counterfactual_producer`
- route: `implement_now`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `limit_up_plateau_breakdown_exit_missing`
- confidence: `medium`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve source-quality adjusted EV attribution by making the missing producer observable.
- evidence: `matched_long_hold_plateau_to_stop_loss_rows=1`, `gap=limit-up or fixed-price plateau breakdown lacks a dedicated source-only exit regime producer`, `required_comparison=current_stop_exit_vs_plateau_take_profit_vs_breakdown_exit`, `required_features=plateau_duration,near_upper_limit_price_stickiness,top_depth_ratio,buy_pressure_decay,holding_flow_recovery_defer,hard_stop_after_plateau`, `forbidden_runtime_action=do_not_override_hard_stop_or_create_exit_rule_without_separate_approval`, `036010:아비코전자:real_profit=-2.69:real_peak=0.96:held_sec=12674:best_same_parent_reentry_profit=0.76:worst_same_parent_stop=-2.68`, `ai_priority=high`, `ai_route=implement_now`
- parity_contract: -
- next_postclose_metric: producer_gap_discovery.producer_gap_limit_up_plateau_breakdown_exit_missing
- files_likely_touched: `src/producers/post_sell/plateau_breakdown_exit_counterfactual_producer.py`, `src/features/post_sell/plateau_regime_features.py`, `src/reports/post_sell/plateau_breakdown_report.py`
- acceptance_tests: `Produce a row for 036010 with current_stop_exit, plateau_take_profit, breakdown_exit, and plateau classification fields.`, `Limit-up or fixed-price plateaus are separated from ordinary non-plateau exits.`, `Artifacts contain benchmark comparisons only and no exit instruction fields.`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun producer_gap_discovery, code improvement workorder, threshold EV, runtime summary, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 9. `order_producer_gap_discovery_producer_gap_sim_entry_selection_gap_missing`

- title: Implement missing producer: sim_entry_selection_gap_missing
- decision: `implement_now`
- decision_reason: producer gap discovery high-priority order is source-only missing producer work; implementation still requires Codex implement_now and cannot mutate runtime/order/provider/bot state
- source_report_type: `producer_gap_discovery`
- lifecycle_stage: `entry`
- target_subsystem: `sim_post_sell.entry_provenance_and_bucketization`
- route: `block_source_quality`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `sim_entry_selection_gap_missing`
- confidence: `high`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve source-quality adjusted EV attribution by making the missing producer observable.
- evidence: `sim_rows=789`, `entry_time_field_rate=0.0000`, `gap=sim entry/selection rows are present but entry provenance is insufficient for bucket producer coverage`, `required_producer=sim_entry_selection_bucket_producer`, `ai_priority=high`, `ai_route=block_source_quality`
- parity_contract: -
- next_postclose_metric: producer_gap_discovery.producer_gap_sim_entry_selection_gap_missing
- files_likely_touched: `src/pipelines/post_sell/sim_post_sell_candidate_writer.py`, `src/schemas/post_sell/sim_post_sell_candidate.schema.json`, `src/producers/post_sell/sim_entry_selection_bucket_producer.py`
- acceptance_tests: `New strict-chronology sim rows include non-null entry_time and provenance identifiers.`, `Bucketization can group completed sim rows without falling back to null entry provenance.`, `Candidate-only incomplete days are flagged incomplete rather than merged into completed-evaluation cohorts.`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun producer_gap_discovery, code improvement workorder, threshold EV, runtime summary, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 10. `order_producer_gap_discovery_producer_gap_sim_exit_plateau_breakdown_gap_missing`

- title: Implement missing producer: sim_exit_plateau_breakdown_gap_missing
- decision: `implement_now`
- decision_reason: producer gap discovery high-priority order is source-only missing producer work; implementation still requires Codex implement_now and cannot mutate runtime/order/provider/bot state
- source_report_type: `producer_gap_discovery`
- lifecycle_stage: `exit`
- target_subsystem: `post_sell.counterfactual.plateau_breakdown_exit_counterfactual_producer`
- route: `implement_now`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `sim_exit_plateau_breakdown_gap_missing`
- confidence: `high`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve source-quality adjusted EV attribution by making the missing producer observable.
- evidence: `strict_match_count=56`, `ambiguous_match_count=0`, `top_symbols=000990,001820,005680,017900,027360,031330,036010,043260`, `estimated_giveback_pct_sum=258.6200`, `gap=sim-only prior modest win followed by late stop/giveback is not isolated as a dedicated producer`, `required_producer=plateau_breakdown_exit_counterfactual_producer`, `ai_priority=high`, `ai_route=implement_now`
- parity_contract: -
- next_postclose_metric: producer_gap_discovery.producer_gap_sim_exit_plateau_breakdown_gap_missing
- files_likely_touched: `src/producers/post_sell/plateau_breakdown_exit_counterfactual_producer.py`, `src/features/post_sell/plateau_regime_features.py`, `src/reports/post_sell/rolling_plateau_breakdown_report.py`
- acceptance_tests: `The strict cohort reproduces the 56 strict plateau matches with giveback metrics.`, `Plateau detection separates limit-up or fixed-price regimes from non-plateau exits.`, `Output contains observational comparison fields only and no runtime exit instructions.`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun producer_gap_discovery, code improvement workorder, threshold EV, runtime summary, and postclose verifier.

Runtime hook candidate:

- hook_name: `plateau_breakdown_exit_arbitration_probe`
- stage: `exit`
- initial_authority: `source_only_proposal`
- apply_boundary: `postclose_artifact_to_next_preopen_candidate_only`
- action_namespace: `EXIT_CONFIRM`, `TAKE_PROFIT_ON_PLATEAU`, `HOLD_REVIEW`
- eligible_after: `dedicated_source_only_producer_implemented`, `rolling_completed_sim_ev_positive`, `source_quality_pass`, `runtime_hook_mapping_test_passed`, `rollback_guard_defined`
- safety_vetoes: `hard_stop`, `protect_stop`, `emergency_stop`, `broker_guard`, `account_guard`, `order_guard`, `quantity_guard`, `cooldown_guard`, `stale_quote_guard`
- rollback_guards: `max_defer_seconds_exceeded`, `max_review_ticks_exceeded`, `deferred_exit_loss_worsen_breach`, `ws_or_ofi_source_stale`, `stable_bearish_ofi_confirm`, `post_apply_attribution_breach`
- required_source_artifacts: `plateau_breakdown_exit_counterfactual_producer`
- required_ev_evidence: `completed_sim_equal_weight_avg_profit_pct_positive`, `source_quality_adjusted_ev_pct_positive`, `strict_chronology_sample_floor_pass`
- forbidden_uses: `account guard bypass`, `bot restart`, `broker guard bypass`, `broker order submit`, `cooldown guard bypass`, `emergency stop override`, `entry decision override`, `exit decision override`, `hard stop override`, `position cap release`, `protect stop override`, `provider change`, `quantity guard bypass`, `real order enablement`, `threshold mutation`

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 11. `order_producer_gap_discovery_producer_gap_sim_holding_runner_gap_missing`

- title: Implement missing producer: sim_holding_runner_gap_missing
- decision: `implement_now`
- decision_reason: producer gap discovery high-priority order is source-only missing producer work; implementation still requires Codex implement_now and cannot mutate runtime/order/provider/bot state
- source_report_type: `producer_gap_discovery`
- lifecycle_stage: `holding`
- target_subsystem: `post_sell.counterfactual.runner_regime_counterfactual_producer`
- route: `implement_now`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `sim_holding_runner_gap_missing`
- confidence: `high`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve source-quality adjusted EV attribution by making the missing producer observable.
- evidence: `strict_match_count=61`, `ambiguous_match_count=0`, `top_symbols=001740,001820,005680,005950,009150,009470,019180,025560`, `estimated_uplift_pct_sum=272.8800`, `gap=sim-only early stop/loss followed by later runner is not isolated as a dedicated producer`, `required_microstructure_features=ws_orderbook_churn,ofi_qi_persistence,large_trade_absorption,spread_flicker,top_depth_replenishment,holding_flow_cache_freshness`, `required_producer=runner_regime_counterfactual_producer`, `ai_priority=high`, `ai_route=implement_now`
- parity_contract: -
- next_postclose_metric: producer_gap_discovery.producer_gap_sim_holding_runner_gap_missing
- files_likely_touched: `src/producers/post_sell/runner_regime_counterfactual_producer.py`, `src/features/post_sell/runner_regime_features.py`, `src/reports/post_sell/rolling_runner_regime_report.py`
- acceptance_tests: `The strict cohort reproduces the 61 strict runner matches and keeps ambiguous paths separate.`, `Output rows include actual_exit_profit, runner_counterfactual_profit, uplift, and join-quality/freshness fields.`, `Artifacts contain no executable hook, broker, or exit-override fields.`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun producer_gap_discovery, code improvement workorder, threshold EV, runtime summary, and postclose verifier.

Runtime hook candidate:

- hook_name: `holding_flow_runner_debounce_guard`
- stage: `holding_exit`
- initial_authority: `source_only_proposal`
- apply_boundary: `postclose_artifact_to_next_preopen_candidate_only`
- action_namespace: `EXIT_CONFIRM`, `HOLD_REVIEW`, `TRIM`
- eligible_after: `dedicated_source_only_producer_implemented`, `rolling_completed_sim_ev_positive`, `source_quality_pass`, `runtime_hook_mapping_test_passed`, `rollback_guard_defined`
- safety_vetoes: `hard_stop`, `protect_stop`, `emergency_stop`, `broker_guard`, `account_guard`, `order_guard`, `quantity_guard`, `cooldown_guard`, `stale_quote_guard`
- rollback_guards: `max_defer_seconds_exceeded`, `max_review_ticks_exceeded`, `deferred_exit_loss_worsen_breach`, `ws_or_ofi_source_stale`, `stable_bearish_ofi_confirm`, `post_apply_attribution_breach`
- required_source_artifacts: `runner_regime_counterfactual_producer`
- required_ev_evidence: `completed_sim_equal_weight_avg_profit_pct_positive`, `source_quality_adjusted_ev_pct_positive`, `strict_chronology_sample_floor_pass`
- forbidden_uses: `account guard bypass`, `bot restart`, `broker guard bypass`, `broker order submit`, `cooldown guard bypass`, `emergency stop override`, `entry decision override`, `exit decision override`, `hard stop override`, `position cap release`, `protect stop override`, `provider change`, `quantity guard bypass`, `real order enablement`, `threshold mutation`

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 12. `order_producer_gap_discovery_producer_gap_volatile_runner_exit_counterfactual_missing`

- title: Implement missing producer: volatile_runner_exit_counterfactual_missing
- decision: `implement_now`
- decision_reason: producer gap discovery high-priority order is source-only missing producer work; implementation still requires Codex implement_now and cannot mutate runtime/order/provider/bot state
- source_report_type: `producer_gap_discovery`
- lifecycle_stage: `exit`
- target_subsystem: `post_sell.counterfactual.runner_regime_counterfactual_producer`
- route: `implement_now`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `volatile_runner_exit_counterfactual_missing`
- confidence: `medium`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve source-quality adjusted EV attribution by making the missing producer observable.
- evidence: `matched_real_small_take_profit_vs_sim_runner_rows=1`, `gap=volatile bullish continuation after trailing exit lacks a dedicated source-only producer`, `required_comparison=real_exit_profit_vs_same_parent_sim_runner_profit`, `required_features=peak_drawdown,holding_flow_override_state,ofi_qi_smoothing,large_sell_print,top_depth_ratio,post_exit_mfe`, `forbidden_runtime_action=do_not_override_exit_or_trailing_without_separate_approval`, `003720:삼영:real_profit=0.73:real_peak=2.72:sim_profit=6.33:uplift=5.60`, `ai_priority=high`, `ai_route=implement_now`
- parity_contract: -
- next_postclose_metric: producer_gap_discovery.producer_gap_volatile_runner_exit_counterfactual_missing
- files_likely_touched: `src/producers/post_sell/runner_regime_counterfactual_producer.py`, `src/producers/post_sell/real_sim_parent_join.py`, `src/reports/post_sell/runner_counterfactual_report.py`
- acceptance_tests: `Produce a counterfactual row for 003720 with real_exit_profit, same_parent_sim_runner_profit, uplift, and continuation_vs_reversal labeling.`, `Ambiguous or stale real-to-sim joins are excluded from the strict cohort and reported separately.`, `Output artifacts contain observational fields only and no runtime action fields.`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun producer_gap_discovery, code improvement workorder, threshold EV, runtime summary, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

## 자동화체인 재투입

- 구현 결과는 `2026-05-27` 이후 postclose `threshold_cycle`, `scalping_pattern_lab_automation`, `threshold_cycle_ev`가 자동으로 다시 읽는다.
- 구현자가 수동으로 threshold 값을 바꾸는 것이 아니라, source/report/provenance를 닫아 다음 calibration이 판단하게 한다.
- 다음 Codex 세션 입력 문구: `none_for_bucket_discovery_classification`

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
