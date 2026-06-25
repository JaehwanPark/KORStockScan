# Code Improvement Workorder - 2026-06-25

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
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-06-25.json`
- threshold_cycle_calibration: `-`
- pipeline_event_verbosity: `-`
- observation_source_quality_audit: `/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-25.json`
- ai_watching_score_smoothing_diagnostic: `-`
- codebase_performance_workorder: `-`
- pattern_lab_currentness_audit: `-`
- pattern_lab_ai_review: `-`
- producer_gap_discovery: `-`
- stage_hook_workorder_discovery: `-`
- stage_hook_runtime_scaffold: `-`
- buy_funnel_sentinel: `/home/ubuntu/KORStockScan/data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-06-25.json`
- generated_at: `2026-06-25T20:19:05+09:00`
- generation_id: `2026-06-25-0cfd8429982c`
- source_hash: `0cfd8429982c49d5de9b46e51f11628781313d3348cf3c907ddb0fb852872896`

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
- new_order_ids: `['order_entry_broker_receipt_contract_gap_review', 'order_entry_fill_quality_contract_gap_review', 'order_entry_post_submit_contract_gap_review', 'order_entry_source_taxonomy_contract_gap_review', 'order_entry_submit_drought_auto_resolution', 'order_entry_telegram_post_submit_contract_gap_review', 'order_lifecycle_entry_bucket_chosen_action_no_buy_ai', 'order_lifecycle_entry_bucket_chosen_action_wait_requote', 'order_lifecycle_entry_bucket_exit_rule_exit_unknown', 'order_lifecycle_entry_bucket_exit_rule_scalp_soft_stop_pct', 'order_lifecycle_entry_bucket_liquidity_bucket_liquidity_high', 'order_lifecycle_entry_bucket_overbought_bucket_overbought_normal', 'order_lifecycle_entry_bucket_overbought_bucket_overbought_watch', 'order_lifecycle_entry_bucket_score_band_score_60_62', 'order_lifecycle_entry_bucket_score_band_score_66_69', 'order_lifecycle_entry_bucket_score_band_score_70p', 'order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_overnight_sell_today_rule_scalp_sim_overnight_sell_tod_d982edbd', 'order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_73281913', 'order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_823fe278', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_daily_limit_up_immediate_exit_outc_960ea129', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_good_e_d8c33947', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_missed_30bb5c8f', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_neutra_d5168c3c', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_e_71b132b9', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_missed_bb293be8', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutra_d73738ba', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_10_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_fabcf0d3', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_11_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_12_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c0394ca1', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_13_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_14_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_25002a6e', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_15_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c0394ca1', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_16_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_17_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c0394ca1', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_18_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_e48e520c', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_19_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_1_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_20_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c0394ca1', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_2_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_3_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_5e11e397', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_4_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c0394ca1', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_5_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c0394ca1', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_6_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c0394ca1', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_7_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_8_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_cd847d1b', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_9_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_fabcf0d3', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_not_applicable_a_fc555278', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_lt_neg070_he_ed505a3f', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_neg070_neg01_7ffc2d26', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_pos080_pos15_aaaecaaf', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_pos150_pos30_6f3188b0', 'order_lifecycle_holding_bucket_held_bucket_held_not_applicable_at_start_508784a3', 'order_lifecycle_holding_bucket_holding_action_holding_action_not_applicable_at_start_c20ec935', 'order_lifecycle_holding_bucket_holding_action_wait_c26d74df', 'order_lifecycle_holding_bucket_holding_source_stage_scalp_sim_holding_started_78913f30', 'order_lifecycle_holding_bucket_profit_band_profit_lt_neg070_711f1b3f', 'order_lifecycle_quiet_gap_ai_review_coverage_rollup', 'order_lifecycle_quiet_gap_parent_conflict_rollup', 'order_lifecycle_quiet_gap_positive_source_only_rollup', 'order_lifecycle_source_dimension_gap_rollup']`
- removed_order_ids: `[]`
- decision_changed_order_ids: `[]`

## Summary

- source_order_count: `60`
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
- lifecycle_holding_exit_bucket_source_order_count: `20`
- pipeline_event_verbosity_source_order_count: `0`
- observation_source_quality_source_order_count: `0`
- codebase_performance_source_order_count: `0`
- buy_funnel_sentinel_source_order_count: `6`
- entry_submit_drought_selected: `True`
- entry_submit_drought_handoff_missing: `False`
- panic_lifecycle_source_order_count: `0`
- selected_order_count: `60`
- non_selected_order_count: `0`
- source_decision_counts: `{'implement_now': 1, 'attach_existing_family': 59}`
- selected_decision_counts: `{'implement_now': 1, 'attach_existing_family': 59}`
- selected_route_counts: `{'repeat_unresolved_structural_blocker': 1, 'existing_family': 56, 'ai_review_coverage_review': 1, 'positive_source_only_review': 1, 'source_dimension_rollup': 1}`
- selected_implement_now_route_count: `1`
- selected_runtime_effect_false_count: `60`
- selected_unimplemented_runtime_effect_false_count: `0`
- selected_unimplemented_route_counts: `{}`
- selected_terminal_non_implement_runtime_effect_false_count: `4`
- selected_terminal_non_implement_route_counts: `{'existing_family': 1, 'ai_review_coverage_review': 1, 'positive_source_only_review': 1, 'source_dimension_rollup': 1}`
- selected_implement_now_existing_implementation_count: `1`
- selected_implement_now_existing_implementation_order_ids: `['order_entry_submit_drought_auto_resolution']`
- selected_implement_now_new_runtime_effect_false_count: `0`
- selected_implement_now_new_runtime_effect_false_order_ids: `[]`
- repeat_unresolved_escalation_count: `0`
- repeat_unresolved_escalated_order_ids: `[]`
- repeat_unresolved_structural_blocker_count: `1`
- repeat_unresolved_structural_blocker_order_ids: `['order_entry_submit_drought_auto_resolution']`
- root_cause_closure_status_counts: `{'handoff_closed_root_cause_open': 1, 'root_cause_closed': 55}`
- implementation_done_count: `0`
- artifact_regeneration_required_count: `0`
- handoff_closed_root_cause_open_count: `1`
- root_cause_closed_count: `55`
- needs_followup_workorder_count: `0`
- root_cause_open_top: `[{'order_id': 'order_entry_submit_drought_auto_resolution', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'buy_funnel_sentinel', 'threshold_family': 'lifecycle_decision_matrix_runtime', 'implementation_status': 'repeat_unresolved_structural_blocker', 'root_cause_signal': 'SUBMIT_DROUGHT_CRITICAL'}]`
- selected_terminal_non_implement_longstanding_count: `4`
- selected_terminal_non_implement_longstanding_order_ids: `['order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_overnight_sell_today_rule_scalp_sim_overnight_sell_tod_d982edbd', 'order_lifecycle_quiet_gap_ai_review_coverage_rollup', 'order_lifecycle_quiet_gap_positive_source_only_rollup', 'order_lifecycle_source_dimension_gap_rollup']`
- selected_longstanding_non_implement_disposition_counts: `{'keep_visible_by_design': 4}`
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

### 1. `order_entry_submit_drought_auto_resolution`

- title: Entry submit drought automatic resolution handoff
- decision: `implement_now`
- decision_reason: longstanding non-implement finding remained unresolved across 8 workorder days; promote it as a structural blocker instead of leaving it as passive evidence
- source_report_type: `buy_funnel_sentinel`
- lifecycle_stage: `entry_submit`
- target_subsystem: `runtime_instrumentation`
- route: `repeat_unresolved_structural_blocker`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `-`
- confidence: `repeat_unresolved_structural_blocker`
- priority: `0`
- runtime_effect: `False`
- strategy_effect: `True`
- data_quality_effect: `True`
- tuning_axis_effect: `True`
- expected_ev_effect: restore submitted coverage before evaluating EV edge
- evidence: `ai_confirmed_unique=60`, `budget_pass_unique=14`, `latency_pass_unique=6`, `submitted_unique=3`, `submitted_to_ai_pct=5.0`, `submitted_to_budget_pct=21.4`, `blocker:blocked_strength_momentum:insufficient_history=421`, `blocker:blocked_strength_momentum:below_strength_base=339`, `blocker:blocked_liquidity:-=262`, `upstream:first_ai_wait:-=235`, `upstream:blocked_ai_score:score_62.0=198`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=179`, `latency:latency_block:latency_state_danger=15`
- parity_contract: -
- next_postclose_metric: SUBMIT_DROUGHT_CRITICAL must produce a selected implement_now workorder and the next postclose LDM/runtime summary must show submit blocker attribution.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/threshold_cycle_ev_report.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py`
- implementation_status: `repeat_unresolved_structural_blocker`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "artifact_regeneration_required": false, "broker_order_submit_allowed": false, "forbidden_uses": ["intraday_threshold_mutation", "broker_guard_bypass", "provider_route_change", "bot_restart_trigger", "telegram_pre_submit_buy_alert"], "implementation_type": "source_only_report_provenance_handoff", "ldm_quote_freshness_attribution_present": false, "quote_freshness_attribution_inconsistent": false, "quote_freshness_latency_pass_recovered_count": 6, "quote_freshness_refresh_applied_count": 12, "quote_freshness_refresh_attempted_count": 14, "required_downstream": ["code_improvement_workorder", "lifecycle_decision_matrix.submit_bucket_attribution", "threshold_cycle_ev_report", "runtime_approval_summary", "postclose_verifier"], "root_cause_closure_status_hint": "handoff_closed_root_cause_open", "root_cause_counts": {"observer_unhealthy": 2, "order_rtt_guard": 8, "quote_stale": 19, "spread_or_slippage_guard": 2, "unknown_latency_reason": 4}, "root_cause_signal": "SUBMIT_DROUGHT_CRITICAL", "runtime_effect": false, "source_report_type": "buy_funnel_sentinel", "structural_blocker_escalation": {"escalation_reason": "submit_drought_handoff_still_requires_actionable_workorder", "history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_entry_submit_drought_auto_resolution", "repeat_signature": "sig:buy_funnel_sentinel|runtime_instrumentation|entry_submit||lifecycle_decision_matrix_runtime|entry_submit_drought_automatic_resolution_handoff", "required_next_route": "implement_now"}, "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_entry_submit_drought_auto_resolution", "repeat_signature": "sig:buy_funnel_sentinel|runtime_instrumentation|entry_submit||lifecycle_decision_matrix_runtime|entry_submit_drought_automatic_resolution_handoff", "review_disposition": "repeat_unresolved_structural_blocker"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `{"escalation_reason": "submit_drought_handoff_still_requires_actionable_workorder", "history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_entry_submit_drought_auto_resolution", "repeat_signature": "sig:buy_funnel_sentinel|runtime_instrumentation|entry_submit||lifecycle_decision_matrix_runtime|entry_submit_drought_automatic_resolution_handoff", "required_next_route": "implement_now"}`
- automation_reentry: After implementation, regenerate the source report, code improvement workorder, threshold EV/runtime summary, and postclose verifier; runtime/order/provider/bot state must remain unchanged.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

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
- evidence: `ai_confirmed_unique=60`, `budget_pass_unique=14`, `latency_pass_unique=6`, `submitted_unique=3`, `submitted_to_ai_pct=5.0`, `submitted_to_budget_pct=21.4`, `blocker:blocked_strength_momentum:insufficient_history=421`, `blocker:blocked_strength_momentum:below_strength_base=339`, `blocker:blocked_liquidity:-=262`, `upstream:first_ai_wait:-=235`, `upstream:blocked_ai_score:score_62.0=198`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=179`, `latency:latency_block:latency_state_danger=15`, `weak_contract_gap=broker_receipt_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_submit_contract_verified`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "broker_receipt_contract_gap", "implementation_type": "submit_contract_report_provenance_verified", "missing_broker_order_key_count": 0, "post_submit_provenance_join_resolution": "no_gap_broker_order_key_present_or_no_missing_rows", "real_submitted_row_count": 5, "runtime_effect": false, "sample_status": "ldm_submit_contract_verified", "source_report_type": "buy_funnel_sentinel", "submit_rows": 90, "taxonomy_leakage_labels": [], "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_submit_contract_verified", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "order_entry_broker_receipt_contract_gap_review", "repeat_signature": "sig:buy_funnel_sentinel|runtime_instrumentation|entry_submit||lifecycle_decision_matrix_runtime|entry_broker_receipt_contract_gap_review", "review_disposition": "implemented_with_provenance"}`
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
- evidence: `ai_confirmed_unique=60`, `budget_pass_unique=14`, `latency_pass_unique=6`, `submitted_unique=3`, `submitted_to_ai_pct=5.0`, `submitted_to_budget_pct=21.4`, `blocker:blocked_strength_momentum:insufficient_history=421`, `blocker:blocked_strength_momentum:below_strength_base=339`, `blocker:blocked_liquidity:-=262`, `upstream:first_ai_wait:-=235`, `upstream:blocked_ai_score:score_62.0=198`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=179`, `latency:latency_block:latency_state_danger=15`, `weak_contract_gap=fill_quality_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_submit_contract_verified`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "fill_quality_contract_gap", "implementation_type": "submit_contract_report_provenance_verified", "missing_broker_order_key_count": 0, "post_submit_provenance_join_resolution": "no_gap_broker_order_key_present_or_no_missing_rows", "real_submitted_row_count": 5, "runtime_effect": false, "sample_status": "ldm_submit_contract_verified", "source_report_type": "buy_funnel_sentinel", "submit_rows": 90, "taxonomy_leakage_labels": [], "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_submit_contract_verified", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "order_entry_fill_quality_contract_gap_review", "repeat_signature": "sig:buy_funnel_sentinel|runtime_instrumentation|entry_submit||lifecycle_decision_matrix_runtime|entry_fill_quality_contract_gap_review", "review_disposition": "implemented_with_provenance"}`
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
- evidence: `ai_confirmed_unique=60`, `budget_pass_unique=14`, `latency_pass_unique=6`, `submitted_unique=3`, `submitted_to_ai_pct=5.0`, `submitted_to_budget_pct=21.4`, `blocker:blocked_strength_momentum:insufficient_history=421`, `blocker:blocked_strength_momentum:below_strength_base=339`, `blocker:blocked_liquidity:-=262`, `upstream:first_ai_wait:-=235`, `upstream:blocked_ai_score:score_62.0=198`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=179`, `latency:latency_block:latency_state_danger=15`, `weak_contract_gap=post_submit_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_submit_contract_verified`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "post_submit_contract_gap", "implementation_type": "submit_contract_report_provenance_verified", "missing_broker_order_key_count": 0, "post_submit_provenance_join_resolution": "no_gap_broker_order_key_present_or_no_missing_rows", "real_submitted_row_count": 5, "runtime_effect": false, "sample_status": "ldm_submit_contract_verified", "source_report_type": "buy_funnel_sentinel", "submit_rows": 90, "taxonomy_leakage_labels": [], "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_submit_contract_verified", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "order_entry_post_submit_contract_gap_review", "repeat_signature": "sig:buy_funnel_sentinel|runtime_instrumentation|entry_submit||lifecycle_decision_matrix_runtime|entry_post_submit_contract_gap_review", "review_disposition": "implemented_with_provenance"}`
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
- evidence: `ai_confirmed_unique=60`, `budget_pass_unique=14`, `latency_pass_unique=6`, `submitted_unique=3`, `submitted_to_ai_pct=5.0`, `submitted_to_budget_pct=21.4`, `blocker:blocked_strength_momentum:insufficient_history=421`, `blocker:blocked_strength_momentum:below_strength_base=339`, `blocker:blocked_liquidity:-=262`, `upstream:first_ai_wait:-=235`, `upstream:blocked_ai_score:score_62.0=198`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=179`, `latency:latency_block:latency_state_danger=15`, `weak_contract_gap=source_taxonomy_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`, `taxonomy_leakage_labels=[]`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_submit_contract_verified`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "source_taxonomy_contract_gap", "implementation_type": "submit_contract_report_provenance_verified", "missing_broker_order_key_count": 0, "post_submit_provenance_join_resolution": "no_gap_broker_order_key_present_or_no_missing_rows", "real_submitted_row_count": 5, "runtime_effect": false, "sample_status": "ldm_submit_contract_verified", "source_report_type": "buy_funnel_sentinel", "submit_rows": 90, "taxonomy_leakage_labels": [], "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_submit_contract_verified", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "order_entry_source_taxonomy_contract_gap_review", "repeat_signature": "sig:buy_funnel_sentinel|runtime_instrumentation|entry_submit||lifecycle_decision_matrix_runtime|entry_source_taxonomy_contract_gap_review", "review_disposition": "implemented_with_provenance"}`
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
- evidence: `ai_confirmed_unique=60`, `budget_pass_unique=14`, `latency_pass_unique=6`, `submitted_unique=3`, `submitted_to_ai_pct=5.0`, `submitted_to_budget_pct=21.4`, `blocker:blocked_strength_momentum:insufficient_history=421`, `blocker:blocked_strength_momentum:below_strength_base=339`, `blocker:blocked_liquidity:-=262`, `upstream:first_ai_wait:-=235`, `upstream:blocked_ai_score:score_62.0=198`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=179`, `latency:latency_block:latency_state_danger=15`, `weak_contract_gap=telegram_post_submit_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_submit_contract_verified`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "telegram_post_submit_contract_gap", "implementation_type": "submit_contract_report_provenance_verified", "missing_broker_order_key_count": 0, "post_submit_provenance_join_resolution": "no_gap_broker_order_key_present_or_no_missing_rows", "real_submitted_row_count": 5, "runtime_effect": false, "sample_status": "ldm_submit_contract_verified", "source_report_type": "buy_funnel_sentinel", "submit_rows": 90, "taxonomy_leakage_labels": [], "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_submit_contract_verified", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "order_entry_telegram_post_submit_contract_gap_review", "repeat_signature": "sig:buy_funnel_sentinel|runtime_instrumentation|entry_submit||lifecycle_decision_matrix_runtime|entry_telegram_post_submit_contract_gap_review", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_submit_contract_verified and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 7. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_10_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_fabcf0d3`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:0e304b8817
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_10`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:0e304b8817`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 8. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_11_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_11`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:70a865069d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 9. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_12_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c0394ca1`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_12`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:075ce13c92`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 10. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_13_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_13`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:70a865069d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 11. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_14_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_25002a6e`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_14`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:fef5ae20be`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 12. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_15_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c0394ca1`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_15`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:075ce13c92`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 13. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_16_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42`

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
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 14. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_17_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c0394ca1`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_17`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:075ce13c92`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 15. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_18_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_e48e520c`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:04fe106012
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_18`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:04fe106012`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 16. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_19_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42`

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
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 17. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_1_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_1`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:70a865069d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 18. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_20_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c0394ca1`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_20`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:075ce13c92`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 19. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_2_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42`

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
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 20. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_3_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_5e11e397`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:b846e1412a
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_3`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:b846e1412a`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 21. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_4_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c0394ca1`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_4`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:075ce13c92`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 22. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_5_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c0394ca1`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_5`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:075ce13c92`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 23. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_6_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c0394ca1`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_6`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:075ce13c92`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 24. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_7_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_7`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:70a865069d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 25. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_8_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_cd847d1b`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:5811e241d0
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_8`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:5811e241d0`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 26. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_9_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_fabcf0d3`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:0e304b8817
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_9`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:0e304b8817`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 27. `order_lifecycle_entry_bucket_exit_rule_exit_unknown`

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
- evidence: `workorder_id=entry_bucket_source_quality_3`, `bucket_type=exit_rule`, `bucket_key=exit_unknown`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "entry_label_not_applicable", "source_field_coverage": {"exit_rule": {"coverage_rate": 0.0, "present_count": 0, "sample_count": 596, "source_fields": ["labels.exit_rule"]}}, "unknown_reason_counts": {"entry_label_not_applicable": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "order_lifecycle_entry_bucket_exit_rule_exit_unknown", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|runtime_instrumentation|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_exit_rule_exit_unknown", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 28. `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_overnight_sell_today_rule_scalp_sim_overnight_sell_tod_d982edbd`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070
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
- evidence: `workorder_id=exit_bucket_source_quality_10`, `bucket_type=combo_exit_result`, `bucket_key=source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=source_quality_workorder`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `terminal_not_applicable_evidence`
- root_cause_closure_status: `-`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "source_quality_workorder", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "hold_sample"}, "recommended_resolution": "mark_not_applicable_explicitly", "source_field_coverage": {"outcome": {"coverage_rate": 1.0, "present_count": 2, "sample_count": 2, "source_fields": ["source_stage", "labels.exit_rule", "runtime_features.chosen_action", "labels.sim_post_sell_outcome", "labels.outcome", "labels.profit_rate"]}}, "unknown_reason_counts": {"not_applicable": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "terminal_not_applicable_evidence", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_scalp_sim_over", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_scalp_sim_over", "review_disposition": "keep_visible_by_design"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Keep the item out of the canonical implement_now queue; regenerated postclose reports and runner terminal dispositions must preserve the non-implement decision.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 29. `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_73281913`

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
- evidence: `workorder_id=exit_bucket_source_quality_3`, `bucket_type=combo_exit_result`, `bucket_key=source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_scalp_sim_part", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_scalp_sim_part", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 30. `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_823fe278`

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
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_823fe278", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_scalp_sim_part", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 31. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_daily_limit_up_immediate_exit_outc_960ea129`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_neg070_neg010
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
- evidence: `workorder_id=exit_bucket_source_quality_9`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_neg070_neg010`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_neg070_neg010", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 32. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_good_e_d8c33947`

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
- evidence: `workorder_id=exit_bucket_source_quality_5`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_good_e_d8c33947", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 33. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_missed_30bb5c8f`

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
- evidence: `workorder_id=exit_bucket_source_quality_7`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_missed_30bb5c8f", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 34. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_neutra_d5168c3c`

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
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 35. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_e_71b132b9`

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
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_e_71b132b9", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 36. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_missed_bb293be8`

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
- evidence: `workorder_id=exit_bucket_source_quality_6`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 37. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutra_d73738ba`

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
- evidence: `workorder_id=exit_bucket_source_quality_4`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutra_d73738ba", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_combo_exit_result_source_sim_post_sell_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 38. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_not_applicable_a_fc555278`

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
- evidence: `workorder_id=holding_bucket_source_quality_4`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 39. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_lt_neg070_he_ed505a3f`

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
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_lt_neg070_he_ed505a3f", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 40. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_neg070_neg01_7ffc2d26`

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
- evidence: `workorder_id=holding_bucket_source_quality_2`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 41. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_pos080_pos15_aaaecaaf`

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
- evidence: `workorder_id=holding_bucket_source_quality_5`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 42. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_pos150_pos30_6f3188b0`

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
- evidence: `workorder_id=holding_bucket_source_quality_3`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_recovery_or_relax", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_combo_holding_flow_source_scalp_sim_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 43. `order_lifecycle_holding_bucket_held_bucket_held_not_applicable_at_start_508784a3`

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
- evidence: `workorder_id=holding_bucket_source_quality_6`, `bucket_type=held_bucket`, `bucket_key=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "held_not_applicable_at_start", "bucket_type": "held_bucket", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_lifecycle_holding_bucket_held_bucket_held_not_applicable_at_start_508784a3", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_held_bucket_held_not_applicable_at_s", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 44. `order_lifecycle_holding_bucket_holding_action_holding_action_not_applicable_at_start_c20ec935`

- title: LDM holding bucket source-quality follow-up: holding_action=holding_action_not_applicable_at_start
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
- evidence: `workorder_id=holding_bucket_source_quality_8`, `bucket_type=holding_action`, `bucket_key=holding_action_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "holding_action_not_applicable_at_start", "bucket_type": "holding_action", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_lifecycle_holding_bucket_holding_action_holding_action_not_applicable_at_start_c20ec935", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_holding_action_holding_action_not_ap", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 45. `order_lifecycle_holding_bucket_holding_action_wait_c26d74df`

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
- evidence: `workorder_id=holding_bucket_source_quality_7`, `bucket_type=holding_action`, `bucket_key=WAIT`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "WAIT", "bucket_type": "holding_action", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_lifecycle_holding_bucket_holding_action_wait_c26d74df", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_holding_action_wait", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 46. `order_lifecycle_holding_bucket_holding_source_stage_scalp_sim_holding_started_78913f30`

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
- evidence: `workorder_id=holding_bucket_source_quality_9`, `bucket_type=holding_source_stage`, `bucket_key=scalp_sim_holding_started`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "scalp_sim_holding_started", "bucket_type": "holding_source_stage", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 4, "repeat_key": "order_lifecycle_holding_bucket_holding_source_stage_scalp_sim_holding_started_78913f30", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_holding_source_stage_scalp_sim_holdi", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 47. `order_lifecycle_holding_bucket_profit_band_profit_lt_neg070_711f1b3f`

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
- evidence: `workorder_id=holding_bucket_source_quality_10`, `bucket_type=profit_band`, `bucket_key=profit_lt_neg070`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "profit_lt_neg070", "bucket_type": "profit_band", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_lifecycle_holding_bucket_profit_band_profit_lt_neg070_711f1b3f", "repeat_signature": "sig:lifecycle_decision_matrix_holding_bucket_attribution|lifecycle_decision_matrix|holding|holding_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_holding_bucket_source_quality_follow_up_profit_band_profit_lt_neg070", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 48. `order_lifecycle_quiet_gap_ai_review_coverage_rollup`

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
- evidence: `quiet_gap_count=411`, `rollup_required_count=411`, `sim_live_connected_quiet_gap_count=3`, `quiet_gap_type_counts={'parent_conflict_child': 11, 'positive_source_only_keep_collecting': 407, 'exclusion_dimension_candidate': 3, 'ai_review_parsed_low_coverage': 1}`, `ai_review_coverage={'status': 'parsed', 'shard_count': 5, 'parsed_shard_count': 4, 'reviewed_candidate_count': 4, 'low_coverage': True}`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 49. `order_lifecycle_quiet_gap_parent_conflict_rollup`

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
- evidence: `quiet_gap_count=411`, `rollup_required_count=411`, `sim_live_connected_quiet_gap_count=3`, `quiet_gap_type_counts={'parent_conflict_child': 11, 'positive_source_only_keep_collecting': 407, 'exclusion_dimension_candidate': 3, 'ai_review_parsed_low_coverage': 1}`, `ai_review_coverage={'status': 'parsed', 'shard_count': 5, 'parsed_shard_count': 4, 'reviewed_candidate_count': 4, 'low_coverage': True}`, `runtime_effect=false`, `allowed_runtime_apply=false`, `parent_conflict_resolution_count=2`, `resolution_states={'resolution_blocked_thin_sample': 2}`, `sim_eligible_after_resolution=0`
- parity_contract: -
- next_postclose_metric: quiet_gap_summary rollup counts remain visible until explicitly resolved.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "order_lifecycle_quiet_gap_parent_conflict_rollup", "repeat_signature": "sig:lifecycle_bucket_discovery_quiet_gap_rollup|lifecycle_bucket_discovery_taxonomy_provenance|multi_stage|quiet_gap_rollup_evidence|lifecycle_bucket_discovery|lifecycle_quiet_gap_parent_conflict_exclusion_review", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 50. `order_lifecycle_quiet_gap_positive_source_only_rollup`

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
- evidence: `quiet_gap_count=411`, `rollup_required_count=411`, `sim_live_connected_quiet_gap_count=3`, `quiet_gap_type_counts={'parent_conflict_child': 11, 'positive_source_only_keep_collecting': 407, 'exclusion_dimension_candidate': 3, 'ai_review_parsed_low_coverage': 1}`, `ai_review_coverage={'status': 'parsed', 'shard_count': 5, 'parsed_shard_count': 4, 'reviewed_candidate_count': 4, 'low_coverage': True}`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: quiet_gap_summary rollup counts remain visible until explicitly resolved.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `terminal_existing_family_evidence`
- root_cause_closure_status: `-`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "terminal_existing_family_evidence", "previous_route": "positive_source_only_review", "repeat_count": 9, "repeat_key": "order_lifecycle_quiet_gap_positive_source_only_rollup", "repeat_signature": "sig:lifecycle_bucket_discovery_quiet_gap_rollup|lifecycle_bucket_discovery_taxonomy_provenance|multi_stage|quiet_gap_rollup_evidence|lifecycle_bucket_discovery|lifecycle_quiet_gap_positive_source_only_review", "review_disposition": "keep_visible_by_design"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose checklist/workorder should keep quiet_gap_summary visible until the gap is implemented, covered by parent policy, deferred for more sample, or explicitly rejected.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 51. `order_lifecycle_source_dimension_gap_rollup`

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
- evidence: `rollup_only_gap_count=50`, `unknown_source_dimensions=7`, `recommended_resolution_counts={'explicit_lifecycle_flow_source_only_blocker': 43, 'entry_label_not_applicable': 1, 'mark_not_applicable_explicitly': 2, 'join_labels_before_bucket_decision': 4}`, `missing_dimension_key_counts={'entry': 24, 'exit': 66, 'holding': 70, 'submit': 74}`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: source_dimension_gap_summary rollup/actionable counts remain visible.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `terminal_existing_family_evidence`
- root_cause_closure_status: `-`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "terminal_existing_family_evidence", "previous_route": "source_dimension_rollup", "repeat_count": 9, "repeat_key": "order_lifecycle_source_dimension_gap_rollup", "repeat_signature": "sig:lifecycle_bucket_discovery_source_dimension_rollup|lifecycle_bucket_discovery_taxonomy_provenance|multi_stage|source_dimension_gap_rollup_evidence|lifecycle_bucket_discovery|unknown", "review_disposition": "keep_visible_by_design"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose checklist/workorder should keep source_dimension_gap_summary visible until actionable gaps are resolved or explicitly marked not applicable.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 52. `order_lifecycle_entry_bucket_chosen_action_no_buy_ai`

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
- evidence: `workorder_id=entry_bucket_source_quality_2`, `bucket_type=chosen_action`, `bucket_key=NO_BUY_AI`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 4, "repeat_key": "order_lifecycle_entry_bucket_chosen_action_no_buy_ai", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|lifecycle_decision_matrix|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_chosen_action_no_buy_ai", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 53. `order_lifecycle_entry_bucket_chosen_action_wait_requote`

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
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 9, "repeat_key": "order_lifecycle_entry_bucket_chosen_action_wait_requote", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|lifecycle_decision_matrix|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_chosen_action_wait_requote", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 54. `order_lifecycle_entry_bucket_exit_rule_scalp_soft_stop_pct`

- title: LDM entry bucket attribution follow-up: exit_rule=scalp_soft_stop_pct
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
- evidence: `workorder_id=entry_bucket_source_quality_4`, `bucket_type=exit_rule`, `bucket_key=scalp_soft_stop_pct`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 55. `order_lifecycle_entry_bucket_liquidity_bucket_liquidity_high`

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
- evidence: `workorder_id=entry_bucket_source_quality_5`, `bucket_type=liquidity_bucket`, `bucket_key=liquidity_high`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_lifecycle_entry_bucket_liquidity_bucket_liquidity_high", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|lifecycle_decision_matrix|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_liquidity_bucket_liquidity_high", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 56. `order_lifecycle_entry_bucket_overbought_bucket_overbought_normal`

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
- evidence: `workorder_id=entry_bucket_source_quality_6`, `bucket_type=overbought_bucket`, `bucket_key=overbought_normal`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_lifecycle_entry_bucket_overbought_bucket_overbought_normal", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|lifecycle_decision_matrix|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_overbought_bucket_overbought_normal", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 57. `order_lifecycle_entry_bucket_overbought_bucket_overbought_watch`

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
- evidence: `workorder_id=entry_bucket_source_quality_7`, `bucket_type=overbought_bucket`, `bucket_key=overbought_watch`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 58. `order_lifecycle_entry_bucket_score_band_score_60_62`

- title: LDM entry bucket attribution follow-up: score_band=score_60_62
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
- evidence: `workorder_id=entry_bucket_source_quality_9`, `bucket_type=score_band`, `bucket_key=score_60_62`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_lifecycle_entry_bucket_score_band_score_60_62", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|lifecycle_decision_matrix|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_score_band_score_60_62", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 59. `order_lifecycle_entry_bucket_score_band_score_66_69`

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
- evidence: `workorder_id=entry_bucket_source_quality_10`, `bucket_type=score_band`, `bucket_key=score_66_69`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_lifecycle_entry_bucket_score_band_score_66_69", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|lifecycle_decision_matrix|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_score_band_score_66_69", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 60. `order_lifecycle_entry_bucket_score_band_score_70p`

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
- evidence: `workorder_id=entry_bucket_source_quality_8`, `bucket_type=score_band`, `bucket_key=score_70p`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_lifecycle_entry_bucket_score_band_score_70p", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|lifecycle_decision_matrix|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_score_band_score_70p", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

## 자동화체인 재투입

- 구현 결과는 `2026-06-26` 이후 postclose `threshold_cycle`, `scalping_pattern_lab_automation`, `threshold_cycle_ev`가 자동으로 다시 읽는다.
- 구현자가 수동으로 threshold 값을 바꾸는 것이 아니라, source/report/provenance를 닫아 다음 calibration이 판단하게 한다.
- 다음 Codex 세션 입력 문구: `none_for_bucket_discovery_classification`

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
