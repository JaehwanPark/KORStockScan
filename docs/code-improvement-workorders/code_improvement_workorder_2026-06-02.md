# Code Improvement Workorder - 2026-06-02

## 목적

- Postclose 자동화가 생성한 `code_improvement_order`를 Codex 실행용 작업지시서로 변환한다.
- 입력은 scalping pattern lab automation, swing lifecycle improvement automation, swing pattern lab automation을 함께 포함할 수 있다.
- 이 문서는 repo/runtime을 직접 변경하지 않는다. 사용자가 이 문서를 Codex 세션에 넣고 구현을 요청하는 지점만 사람 개입으로 남긴다.
- 구현 후 자동화체인 재투입은 다음 postclose report, threshold calibration, daily EV report가 담당한다.

## Source

- pattern_lab_automation: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-06-02.json`
- swing_improvement_automation: `/home/ubuntu/KORStockScan/data/report/swing_improvement_automation/swing_improvement_automation_2026-06-02.json`
- swing_pattern_lab_automation: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-06-02.json`
- swing_strategy_discovery_ev: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-06-02.json`
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-06-02.json`
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-06-02.json`
- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-02.json`
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-06-02.json`
- threshold_cycle_calibration: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_calibration/threshold_cycle_calibration_2026-06-02_postclose.json`
- pipeline_event_verbosity: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-06-02.json`
- observation_source_quality_audit: `/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-02.json`
- codebase_performance_workorder: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-06-02.json`
- pattern_lab_currentness_audit: `/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-06-02.json`
- pattern_lab_ai_review: `/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-06-02.json`
- producer_gap_discovery: `/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-06-02.json`
- stage_hook_workorder_discovery: `/home/ubuntu/KORStockScan/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_2026-06-02.json`
- stage_hook_runtime_scaffold: `/home/ubuntu/KORStockScan/data/report/stage_hook_runtime_scaffold/stage_hook_runtime_scaffold_2026-06-02.json`
- buy_funnel_sentinel: `/home/ubuntu/KORStockScan/data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-06-02.json`
- generated_at: `2026-06-02T19:51:41+09:00`
- generation_id: `2026-06-02-459190fbee4c`
- source_hash: `459190fbee4c4dcfab3dd4c2c4653737df1a322d206f6f8cd14edd51ef75e494`

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
- previous_generation_id: `2026-06-02-f3d07a3d5e38`
- previous_source_hash: `f3d07a3d5e38ac21dfaee1b31db9d9e218de8dab1dac80980fd9f29d6e83fdbc`
- new_order_ids: `[]`
- removed_order_ids: `[]`
- decision_changed_order_ids: `[]`

## Summary

- source_order_count: `140`
- scalping_source_order_count: `11`
- swing_source_order_count: `8`
- swing_entry_bottleneck_primary: `SWING_ENTRY_BOTTLENECK_OBSERVE`
- swing_entry_bottleneck_selected: `False`
- swing_lab_source_order_count: `3`
- swing_strategy_discovery_source_order_count: `2`
- swing_lifecycle_matrix_source_order_count: `30`
- swing_lifecycle_bucket_discovery_source_order_count: `0`
- pattern_lab_currentness_source_order_count: `0`
- pattern_lab_ai_review_source_order_count: `0`
- threshold_ev_source_order_count: `21`
- lifecycle_submit_bucket_source_order_count: `0`
- lifecycle_holding_exit_bucket_source_order_count: `20`
- pipeline_event_verbosity_source_order_count: `0`
- observation_source_quality_source_order_count: `1`
- codebase_performance_source_order_count: `12`
- buy_funnel_sentinel_source_order_count: `6`
- entry_submit_drought_selected: `True`
- entry_submit_drought_handoff_missing: `False`
- panic_lifecycle_source_order_count: `2`
- selected_order_count: `102`
- non_selected_order_count: `38`
- source_decision_counts: `{'attach_existing_family': 125, 'design_family_candidate': 5, 'defer_evidence': 7, 'reject': 3}`
- selected_decision_counts: `{'attach_existing_family': 102}`
- selected_route_counts: `{'existing_family': 98, 'ai_review_coverage_review': 1, 'parent_conflict_exclusion_review': 1, 'positive_source_only_review': 1, 'source_dimension_rollup': 1}`
- selected_implement_now_route_count: `0`
- selected_runtime_effect_false_count: `102`
- selected_unimplemented_runtime_effect_false_count: `0`
- selected_unimplemented_route_counts: `{}`
- selected_implement_now_existing_implementation_count: `0`
- selected_implement_now_existing_implementation_order_ids: `[]`
- selected_implement_now_new_runtime_effect_false_count: `0`
- selected_implement_now_new_runtime_effect_false_order_ids: `[]`
- repeat_unresolved_escalation_count: `0`
- repeat_unresolved_escalated_order_ids: `[]`
- non_selected_decision_counts: `{'attach_existing_family': 23, 'design_family_candidate': 5, 'defer_evidence': 7, 'reject': 3}`
- gemini_fresh: `True`
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
- `duplicate_order_id=order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manufacture_of_ele source=swing_lifecycle_decision_matrix stage=selection`
- `duplicate_order_id=order_swing_ldm_selection_discovery_arm_attribution_bottom_rebound_atr_pullback_limit_entry_volatility_adjusted_mae_stop_time_stop_m source=swing_lifecycle_decision_matrix stage=selection`
- `duplicate_order_id=order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_of_electronic_ source=swing_lifecycle_decision_matrix stage=selection`
- `duplicate_order_id=order_lifecycle_entry_bucket_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liq source=lifecycle_decision_matrix_entry_bucket_attribution stage=entry`

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
- evidence: `ai_confirmed_unique=147`, `budget_pass_unique=86`, `latency_pass_unique=40`, `submitted_unique=20`, `submitted_to_ai_pct=13.6`, `submitted_to_budget_pct=23.3`, `blocker:latency_block:latency_state_danger=23889`, `blocker:blocked_swing_score_vpw:-=15188`, `blocker:blocked_overbought:-=10705`, `upstream:blocked_ai_score:score_62.0=1012`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=449`, `upstream:first_ai_wait:-=181`, `latency:latency_block:latency_state_danger=23889`
- parity_contract: -
- next_postclose_metric: SUBMIT_DROUGHT_CRITICAL must produce a selected implement_now workorder and the next postclose LDM/runtime summary must show submit blocker attribution.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/threshold_cycle_ev_report.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "broker_order_submit_allowed": false, "forbidden_uses": ["intraday_threshold_mutation", "broker_guard_bypass", "provider_route_change", "bot_restart_trigger", "telegram_pre_submit_buy_alert"], "implementation_type": "source_only_report_provenance_handoff", "required_downstream": ["code_improvement_workorder", "lifecycle_decision_matrix.submit_bucket_attribution", "threshold_cycle_ev_report", "runtime_approval_summary", "postclose_verifier"], "runtime_effect": false, "source_report_type": "buy_funnel_sentinel", "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "SOURCE_TAXONOMY_LEAKAGE", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 2. `order_ai_threshold_dominance`

- title: AI threshold dominance
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `entry_funnel`
- route: `existing_family`
- mapped_family: `score65_74_recovery_probe`
- threshold_family: `score65_74_recovery_probe`
- improvement_type: `threshold_family_input`
- confidence: `consensus`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve EV attribution and prepare bounded calibration input.
- evidence: `{'judgment': '경고', 'why': '`blocked_ai_score_share=80.4%`로 WAIT/BLOCK 비중이 높아 BUY drought 해석을 지지한다.'}`, `{'judgment': '경고', 'why': '`blocked_ai_score_share=80.4%`로 WAIT/BLOCK 비중이 높아 BUY drought 해석을 지지한다.'}`
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

### 3. `order_entry_broker_receipt_contract_gap_review`

- title: Entry broker receipt contract gap review
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `ai_confirmed_unique=147`, `budget_pass_unique=86`, `latency_pass_unique=40`, `submitted_unique=20`, `submitted_to_ai_pct=13.6`, `submitted_to_budget_pct=23.3`, `blocker:latency_block:latency_state_danger=23889`, `blocker:blocked_swing_score_vpw:-=15188`, `blocker:blocked_overbought:-=10705`, `upstream:blocked_ai_score:score_62.0=1012`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=449`, `upstream:first_ai_wait:-=181`, `latency:latency_block:latency_state_danger=23889`, `weak_contract_gap=broker_receipt_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_but_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "broker_receipt_contract_gap", "implementation_type": "entry_submit_source_contract_waiting_real_sample", "runtime_effect": false, "sample_status": "waiting_real_broker_or_fill_sample", "source_report_type": "buy_funnel_sentinel", "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "SOURCE_TAXONOMY_LEAKAGE", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_but_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 4. `order_entry_fill_quality_contract_gap_review`

- title: Entry fill quality contract gap review
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `ai_confirmed_unique=147`, `budget_pass_unique=86`, `latency_pass_unique=40`, `submitted_unique=20`, `submitted_to_ai_pct=13.6`, `submitted_to_budget_pct=23.3`, `blocker:latency_block:latency_state_danger=23889`, `blocker:blocked_swing_score_vpw:-=15188`, `blocker:blocked_overbought:-=10705`, `upstream:blocked_ai_score:score_62.0=1012`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=449`, `upstream:first_ai_wait:-=181`, `latency:latency_block:latency_state_danger=23889`, `weak_contract_gap=fill_quality_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_but_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "fill_quality_contract_gap", "implementation_type": "entry_submit_source_contract_waiting_real_sample", "runtime_effect": false, "sample_status": "waiting_real_broker_or_fill_sample", "source_report_type": "buy_funnel_sentinel", "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "SOURCE_TAXONOMY_LEAKAGE", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_but_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 5. `order_entry_post_submit_contract_gap_review`

- title: Entry post-submit contract gap review
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `ai_confirmed_unique=147`, `budget_pass_unique=86`, `latency_pass_unique=40`, `submitted_unique=20`, `submitted_to_ai_pct=13.6`, `submitted_to_budget_pct=23.3`, `blocker:latency_block:latency_state_danger=23889`, `blocker:blocked_swing_score_vpw:-=15188`, `blocker:blocked_overbought:-=10705`, `upstream:blocked_ai_score:score_62.0=1012`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=449`, `upstream:first_ai_wait:-=181`, `latency:latency_block:latency_state_danger=23889`, `weak_contract_gap=post_submit_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_but_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "post_submit_contract_gap", "implementation_type": "entry_submit_source_contract_waiting_real_sample", "runtime_effect": false, "sample_status": "waiting_real_broker_or_fill_sample", "source_report_type": "buy_funnel_sentinel", "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "SOURCE_TAXONOMY_LEAKAGE", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_but_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 6. `order_entry_source_taxonomy_contract_gap_review`

- title: Entry source taxonomy contract gap review
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `ai_confirmed_unique=147`, `budget_pass_unique=86`, `latency_pass_unique=40`, `submitted_unique=20`, `submitted_to_ai_pct=13.6`, `submitted_to_budget_pct=23.3`, `blocker:latency_block:latency_state_danger=23889`, `blocker:blocked_swing_score_vpw:-=15188`, `blocker:blocked_overbought:-=10705`, `upstream:blocked_ai_score:score_62.0=1012`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=449`, `upstream:first_ai_wait:-=181`, `latency:latency_block:latency_state_danger=23889`, `weak_contract_gap=source_taxonomy_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`, `taxonomy_leakage_labels=['blocked_swing_score_vpw:-']`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_but_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "source_taxonomy_contract_gap", "implementation_type": "entry_submit_source_contract_waiting_real_sample", "runtime_effect": false, "sample_status": "waiting_real_broker_or_fill_sample", "source_report_type": "buy_funnel_sentinel", "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "SOURCE_TAXONOMY_LEAKAGE", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_but_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 7. `order_entry_telegram_post_submit_contract_gap_review`

- title: Entry Telegram post-submit contract gap review
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `ai_confirmed_unique=147`, `budget_pass_unique=86`, `latency_pass_unique=40`, `submitted_unique=20`, `submitted_to_ai_pct=13.6`, `submitted_to_budget_pct=23.3`, `blocker:latency_block:latency_state_danger=23889`, `blocker:blocked_swing_score_vpw:-=15188`, `blocker:blocked_overbought:-=10705`, `upstream:blocked_ai_score:score_62.0=1012`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=449`, `upstream:first_ai_wait:-=181`, `latency:latency_block:latency_state_danger=23889`, `weak_contract_gap=telegram_post_submit_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_but_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "telegram_post_submit_contract_gap", "implementation_type": "entry_submit_source_contract_waiting_real_sample", "runtime_effect": false, "sample_status": "waiting_real_broker_or_fill_sample", "source_report_type": "buy_funnel_sentinel", "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "SOURCE_TAXONOMY_LEAKAGE", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_but_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 8. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_10_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_46a14fe6`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:9395e4b251
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_10`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:9395e4b251`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 9. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_11_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_46a14fe6`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:9395e4b251
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_11`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:9395e4b251`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 10. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_12_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_567137d8`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:ef1a1e11a9
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_12`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:ef1a1e11a9`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 11. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_13_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2ad7fdfe`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:53da8da968
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_13`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:53da8da968`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 12. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_14_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:fcd588ff6c
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_14`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:fcd588ff6c`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 13. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_15_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_586eb85f`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:8a4cc381a9
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_15`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:8a4cc381a9`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'postclose_exit_without_entry']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 14. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_16_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:fcd588ff6c
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_16`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:fcd588ff6c`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 15. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_17_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_ffbb2a48`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bfc859574f
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_17`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bfc859574f`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 16. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_18_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_ffbb2a48`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bfc859574f
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_18`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bfc859574f`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 17. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_19_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_ffbb2a48`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bfc859574f
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_19`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bfc859574f`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 18. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_1_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_264969e0`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:d4ae6b4cbc
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_1`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:d4ae6b4cbc`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 19. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_20_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_a599fff9`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:0dca29af56
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_20`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:0dca29af56`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'postclose_exit_without_entry']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 20. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_2_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_264969e0`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:d4ae6b4cbc
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_2`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:d4ae6b4cbc`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 21. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_3_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_264969e0`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:d4ae6b4cbc
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_3`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:d4ae6b4cbc`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 22. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_4_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_264969e0`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:d4ae6b4cbc
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_4`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:d4ae6b4cbc`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 23. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_5_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_6d30a10b`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:fdddb9a443
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_5`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:fdddb9a443`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 24. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_6_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_264969e0`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:d4ae6b4cbc
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_6`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:d4ae6b4cbc`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_entry', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 25. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_7_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:fcd588ff6c
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_7`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:fcd588ff6c`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 26. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_8_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_e2a4ad43`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:bab6e6899b
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_8`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:bab6e6899b`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 27. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_9_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_97a5021a`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:37be685a1a
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_9`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:37be685a1a`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 28. `order_lifecycle_entry_bucket_exit_rule_exit_unknown`

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
- evidence: `workorder_id=entry_bucket_source_quality_5`, `bucket_type=exit_rule`, `bucket_key=exit_unknown`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "entry_label_not_applicable", "source_field_coverage": {"exit_rule": {"coverage_rate": 0.0, "present_count": 0, "sample_count": 749, "source_fields": ["labels.exit_rule"]}}, "unknown_reason_counts": {"entry_label_not_applicable": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

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
- evidence: `workorder_id=exit_bucket_source_quality_2`, `bucket_type=combo_exit_result`, `bucket_key=source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
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
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 31. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_good_e_d8c33947`

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
- evidence: `workorder_id=exit_bucket_source_quality_3`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
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

### 32. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_missed_30bb5c8f`

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
- evidence: `workorder_id=exit_bucket_source_quality_4`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
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

### 33. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_neutra_d5168c3c`

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

### 37. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_0b5e3447`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080
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
- evidence: `workorder_id=exit_bucket_source_quality_10`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_recovery_or_relax", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 38. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_b3ffe955`

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

### 39. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_buy_profit_profit_lt_neg070_hel_575c586d`

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
- evidence: `workorder_id=holding_bucket_source_quality_7`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
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

### 40. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_not_applicable_a_50644c4a`

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
- evidence: `workorder_id=holding_bucket_source_quality_9`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
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

### 41. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_not_applicable_a_828a0f68`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start
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
- evidence: `workorder_id=holding_bucket_source_quality_4`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_recovery_or_relax", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 42. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_not_applicable_a_f7731cc4`

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
- evidence: `workorder_id=holding_bucket_source_quality_5`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
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

### 43. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_not_applicable_a_fc555278`

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
- evidence: `workorder_id=holding_bucket_source_quality_2`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
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

### 44. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_lt_neg070_he_ed505a3f`

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
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 45. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_neg070_neg01_7ffc2d26`

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
- evidence: `workorder_id=holding_bucket_source_quality_8`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 46. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_pos150_pos30_562da131`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start
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
- evidence: `workorder_id=holding_bucket_source_quality_6`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_recovery_or_relax", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 47. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_pos150_pos30_6f3188b0`

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
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_recovery_or_relax", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 48. `order_lifecycle_holding_bucket_held_bucket_held_not_applicable_at_start_508784a3`

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

### 49. `order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_low_missing_held_missing_kospi_regime_stop_loss`

- title: Swing LDM source field follow-up: mfe_low|missing|held_missing|kospi_regime_stop_loss|-|-|-|-|-
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
- evidence: `section=holding_exit_bucket_attribution`, `bucket_type=holding_exit_bucket_attribution`, `bucket_key=mfe_low|missing|held_missing|kospi_regime_stop_loss|-|-|-|-|-`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
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

### 50. `order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_low_missing_held_missing_kospi_trailing_start_take_profit`

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

### 51. `order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_neg_missing_2h_1d_kospi_regime_stop_loss`

- title: Swing LDM source field follow-up: mfe_neg|missing|2h_1d|kospi_regime_stop_loss|-|-|-|-|-
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
- evidence: `section=holding_exit_bucket_attribution`, `bucket_type=holding_exit_bucket_attribution`, `bucket_key=mfe_neg|missing|2h_1d|kospi_regime_stop_loss|-|-|-|-|-`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
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

### 52. `order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_neg_missing_held_missing_kospi_regime_stop_loss`

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
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": ["mae_bucket", "held_bucket", "selection_arm", "sector", "theme"], "runtime_effect": false, "sample_status": "waiting_source_field_sample", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 9, "total_count": 9}, "exit_rule": {"coverage_ratio": 1.0, "paths": ["label_fields.exit_reason"], "present_count": 9, "total_count": 9}, "held_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.held_sec"], "present_count": 0, "total_count": 9}, "mae_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.mae_pct"], "present_count": 0, "total_count": 9}, "market_regime": {"coverage_ratio": 1.0, "paths": ["runtime_features.panic_context", "runtime_features.market_regime"], "present_count": 9, "total_count": 9}, "mfe_bucket": {"coverage_ratio": 1.0, "paths": ["label_fields.mfe_pct"], "present_count": 9, "total_count": 9}, "sector": {"coverage_ratio": 0.0, "paths": ["runtime_features.sector"], "present_count": 0, "total_count": 9}, "selection_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.entry_policy"], "present_count": 0, "total_count": 9}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 9, "total_count": 9}, "theme": {"coverage_ratio": 0.0, "paths": ["runtime_features.theme_tags"], "present_count": 0, "total_count": 9}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 5, "bucket_value_held_missing": 1, "bucket_value_missing": 1, "source_field_missing:held_bucket": 1, "source_field_missing:mae_bucket": 1, "source_field_missing:sector": 1, "source_field_missing:selection_arm": 1, "source_field_missing:theme": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 53. `order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_neg_missing_lt_30m_kospi_regime_stop_loss`

- title: Swing LDM source field follow-up: mfe_neg|missing|lt_30m|kospi_regime_stop_loss|-|-|-|-|-
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
- evidence: `section=holding_exit_bucket_attribution`, `bucket_type=holding_exit_bucket_attribution`, `bucket_key=mfe_neg|missing|lt_30m|kospi_regime_stop_loss|-|-|-|-|-`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": ["mae_bucket", "selection_arm", "sector", "theme"], "runtime_effect": false, "sample_status": "waiting_source_field_sample", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 5, "total_count": 5}, "exit_rule": {"coverage_ratio": 1.0, "paths": ["label_fields.exit_reason"], "present_count": 5, "total_count": 5}, "held_bucket": {"coverage_ratio": 1.0, "paths": ["label_fields.held_sec"], "present_count": 5, "total_count": 5}, "mae_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.mae_pct"], "present_count": 0, "total_count": 5}, "market_regime": {"coverage_ratio": 1.0, "paths": ["runtime_features.panic_context", "runtime_features.market_regime"], "present_count": 5, "total_count": 5}, "mfe_bucket": {"coverage_ratio": 1.0, "paths": ["label_fields.mfe_pct"], "present_count": 5, "total_count": 5}, "sector": {"coverage_ratio": 0.0, "paths": ["runtime_features.sector"], "present_count": 0, "total_count": 5}, "selection_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.entry_policy"], "present_count": 0, "total_count": 5}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 5, "total_count": 5}, "theme": {"coverage_ratio": 0.0, "paths": ["runtime_features.theme_tags"], "present_count": 0, "total_count": 5}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 5, "bucket_value_missing": 1, "source_field_missing:mae_bucket": 1, "source_field_missing:sector": 1, "source_field_missing:selection_arm": 1, "source_field_missing:theme": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 54. `order_swing_ldm_selection_discovery_arm_attribution_bottom_rebound_atr_pullback_limit_entry_volatility_adjusted_mae_stop_time_stop_m`

- title: Swing LDM source field follow-up: bottom_rebound_atr_pullback_limit_entry|volatility_adjusted|mae_stop_time_stop|Manufacture of Medicaments|-|RUNNER
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=bottom_rebound_atr_pullback_limit_entry|volatility_adjusted|mae_stop_time_stop|Manufacture of Medicaments|-|RUNNER`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 20, "total_count": 20}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 20, "total_count": 20}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 20, "total_count": 20}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 20, "total_count": 20}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 20, "total_count": 20}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 55. `order_swing_ldm_selection_discovery_arm_attribution_bottom_rebound_atr_pullback_limit_entry_volatility_adjusted_mae_stop_time_stop_r`

- title: Swing LDM source field follow-up: bottom_rebound_atr_pullback_limit_entry|volatility_adjusted|mae_stop_time_stop|Road Freight Transport|-|RUNNER
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=bottom_rebound_atr_pullback_limit_entry|volatility_adjusted|mae_stop_time_stop|Road Freight Transport|-|RUNNER`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 10, "total_count": 10}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 10, "total_count": 10}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 10, "total_count": 10}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 10, "total_count": 10}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 10, "total_count": 10}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 56. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_computer_programmi`

- title: Swing LDM source field follow-up: breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Computer programming, System Integration and Management Services|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Computer programming, System Integration and Management Services|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 24, "total_count": 24}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 24, "total_count": 24}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 24, "total_count": 24}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 24, "total_count": 24}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 24, "total_count": 24}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 57. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_diagnostic`

- title: Swing LDM source field follow-up: breakout_confirm_entry|confidence_weighted|trailing_after_mfe|-|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|confidence_weighted|trailing_after_mfe|-|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 28, "total_count": 28}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 28, "total_count": 28}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 28, "total_count": 28}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 28, "total_count": 28}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 28, "total_count": 28}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 2}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 58. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_insurance_보험_생명보험_`

- title: Swing LDM source field follow-up: breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Insurance|보험_생명보험|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Insurance|보험_생명보험|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 15, "total_count": 15}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 15, "total_count": 15}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 15, "total_count": 15}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 15, "total_count": 15}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 15, "total_count": 15}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 59. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manufacture_of_ele`

- title: Swing LDM source field follow-up: breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 39, "total_count": 39}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 39, "total_count": 39}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 39, "total_count": 39}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 39, "total_count": 39}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 39, "total_count": 39}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 60. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manufacture_of_tel`

- title: Swing LDM source field follow-up: breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Telecommunication and Broadcasting Apparatuses|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Telecommunication and Broadcasting Apparatuses|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 17, "total_count": 17}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 17, "total_count": 17}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 17, "total_count": 17}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 17, "total_count": 17}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 17, "total_count": 17}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 61. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_telecommunications`

- title: Swing LDM source field follow-up: breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Telecommunications|클라우드 컴퓨팅|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Telecommunications|클라우드 컴퓨팅|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 21, "total_count": 21}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 21, "total_count": 21}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 21, "total_count": 21}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 21, "total_count": 21}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 21, "total_count": 21}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 62. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_diagnostic`

- title: Swing LDM source field follow-up: breakout_confirm_entry|risk_capped|mae_stop_time_stop|-|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|risk_capped|mae_stop_time_stop|-|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 20, "total_count": 20}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 20, "total_count": 20}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 20, "total_count": 20}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 20, "total_count": 20}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 20, "total_count": 20}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 2}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 63. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_insurance_보험_생명보험_diagnost`

- title: Swing LDM source field follow-up: breakout_confirm_entry|risk_capped|mae_stop_time_stop|Insurance|보험_생명보험|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|risk_capped|mae_stop_time_stop|Insurance|보험_생명보험|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 15, "total_count": 15}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 15, "total_count": 15}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 15, "total_count": 15}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 15, "total_count": 15}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 15, "total_count": 15}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 64. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_of_electric_mo`

- title: Swing LDM source field follow-up: breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Electric Motors, Generators and Transforming, Distributing and Controlling Apparatus of Electricity|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Electric Motors, Generators and Transforming, Distributing and Controlling Apparatus of Electricity|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 11, "total_count": 11}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 11, "total_count": 11}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 11, "total_count": 11}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 11, "total_count": 11}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 11, "total_count": 11}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 65. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_of_electronic_`

- title: Swing LDM source field follow-up: breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Electronic Components|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Electronic Components|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 35, "total_count": 35}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 35, "total_count": 35}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 35, "total_count": 35}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 35, "total_count": 35}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 35, "total_count": 35}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 66. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_of_other_chemi`

- title: Swing LDM source field follow-up: breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Other Chemical Products|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Other Chemical Products|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 21, "total_count": 21}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 21, "total_count": 21}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 21, "total_count": 21}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 21, "total_count": 21}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 21, "total_count": 21}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 67. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_other_financial_intermedia`

- title: Swing LDM source field follow-up: breakout_confirm_entry|risk_capped|mae_stop_time_stop|Other Financial Intermediation|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|risk_capped|mae_stop_time_stop|Other Financial Intermediation|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 39, "total_count": 39}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 39, "total_count": 39}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 39, "total_count": 39}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 39, "total_count": 39}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 39, "total_count": 39}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 68. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_telecommunications_클라우드_컴퓨`

- title: Swing LDM source field follow-up: breakout_confirm_entry|risk_capped|mae_stop_time_stop|Telecommunications|클라우드 컴퓨팅|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|risk_capped|mae_stop_time_stop|Telecommunications|클라우드 컴퓨팅|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 21, "total_count": 21}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 21, "total_count": 21}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 21, "total_count": 21}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 21, "total_count": 21}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 21, "total_count": 21}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 69. `order_swing_ldm_selection_discovery_arm_attribution_pullback_limit_entry_risk_capped_mae_stop_time_stop_building_of_ships_and_boats_`

- title: Swing LDM source field follow-up: pullback_limit_entry|risk_capped|mae_stop_time_stop|Building of Ships and Boats|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=pullback_limit_entry|risk_capped|mae_stop_time_stop|Building of Ships and Boats|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 13, "total_count": 13}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 13, "total_count": 13}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 13, "total_count": 13}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 13, "total_count": 13}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 13, "total_count": 13}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 70. `order_swing_ldm_selection_discovery_arm_attribution_pullback_limit_entry_risk_capped_mae_stop_time_stop_manufacture_of_basic_chemica`

- title: Swing LDM source field follow-up: pullback_limit_entry|risk_capped|mae_stop_time_stop|Manufacture of Basic Chemicals|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=pullback_limit_entry|risk_capped|mae_stop_time_stop|Manufacture of Basic Chemicals|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 22, "total_count": 22}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 22, "total_count": 22}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 22, "total_count": 22}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 22, "total_count": 22}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 22, "total_count": 22}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 71. `order_swing_ldm_selection_discovery_arm_attribution_pullback_limit_entry_risk_capped_mae_stop_time_stop_manufacture_of_medicaments_d`

- title: Swing LDM source field follow-up: pullback_limit_entry|risk_capped|mae_stop_time_stop|Manufacture of Medicaments|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=pullback_limit_entry|risk_capped|mae_stop_time_stop|Manufacture of Medicaments|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 31, "total_count": 31}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 31, "total_count": 31}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 31, "total_count": 31}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 31, "total_count": 31}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 31, "total_count": 31}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 72. `order_swing_ldm_selection_discovery_arm_attribution_pullback_limit_entry_risk_capped_mae_stop_time_stop_manufacture_of_other_chemica`

- title: Swing LDM source field follow-up: pullback_limit_entry|risk_capped|mae_stop_time_stop|Manufacture of Other Chemical Products|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=pullback_limit_entry|risk_capped|mae_stop_time_stop|Manufacture of Other Chemical Products|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 21, "total_count": 21}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 21, "total_count": 21}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 21, "total_count": 21}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 21, "total_count": 21}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 21, "total_count": 21}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 73. `order_swing_ldm_selection_discovery_arm_attribution_pullback_limit_entry_risk_capped_mae_stop_time_stop_manufacture_of_plastic_produ`

- title: Swing LDM source field follow-up: pullback_limit_entry|risk_capped|mae_stop_time_stop|Manufacture of Plastic Products|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=pullback_limit_entry|risk_capped|mae_stop_time_stop|Manufacture of Plastic Products|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 11, "total_count": 11}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 11, "total_count": 11}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 11, "total_count": 11}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 11, "total_count": 11}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 11, "total_count": 11}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 74. `order_swing_ldm_selection_discovery_arm_attribution_pullback_limit_entry_risk_capped_mae_stop_time_stop_manufacture_of_semiconductor`

- title: Swing LDM source field follow-up: pullback_limit_entry|risk_capped|mae_stop_time_stop|Manufacture of Semiconductor|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=pullback_limit_entry|risk_capped|mae_stop_time_stop|Manufacture of Semiconductor|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 17, "total_count": 17}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 17, "total_count": 17}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 17, "total_count": 17}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 17, "total_count": 17}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 17, "total_count": 17}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 75. `order_swing_ldm_selection_discovery_arm_attribution_pullback_limit_entry_risk_capped_mae_stop_time_stop_real_estate_activities_with_`

- title: Swing LDM source field follow-up: pullback_limit_entry|risk_capped|mae_stop_time_stop|Real Estate Activities with Own or Leased Property|-|DIAGNOSTIC
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=pullback_limit_entry|risk_capped|mae_stop_time_stop|Real Estate Activities with Own or Leased Property|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 36, "total_count": 36}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 36, "total_count": 36}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 36, "total_count": 36}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 36, "total_count": 36}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 36, "total_count": 36}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 76. `order_lifecycle_quiet_gap_ai_review_coverage_rollup`

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
- evidence: `quiet_gap_count=306`, `rollup_required_count=306`, `sim_live_connected_quiet_gap_count=7`, `quiet_gap_type_counts={'parent_conflict_child': 46, 'exclusion_dimension_candidate': 12, 'positive_source_only_keep_collecting': 294, 'absorbed_into_parent_policy': 6, 'ai_review_parsed_low_coverage': 1}`, `ai_review_coverage={'status': 'parsed', 'shard_count': 5, 'parsed_shard_count': 2, 'reviewed_candidate_count': 2, 'low_coverage': True}`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 77. `order_lifecycle_quiet_gap_parent_conflict_rollup`

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
- evidence: `quiet_gap_count=306`, `rollup_required_count=306`, `sim_live_connected_quiet_gap_count=7`, `quiet_gap_type_counts={'parent_conflict_child': 46, 'exclusion_dimension_candidate': 12, 'positive_source_only_keep_collecting': 294, 'absorbed_into_parent_policy': 6, 'ai_review_parsed_low_coverage': 1}`, `ai_review_coverage={'status': 'parsed', 'shard_count': 5, 'parsed_shard_count': 2, 'reviewed_candidate_count': 2, 'low_coverage': True}`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 78. `order_lifecycle_quiet_gap_positive_source_only_rollup`

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
- evidence: `quiet_gap_count=306`, `rollup_required_count=306`, `sim_live_connected_quiet_gap_count=7`, `quiet_gap_type_counts={'parent_conflict_child': 46, 'exclusion_dimension_candidate': 12, 'positive_source_only_keep_collecting': 294, 'absorbed_into_parent_policy': 6, 'ai_review_parsed_low_coverage': 1}`, `ai_review_coverage={'status': 'parsed', 'shard_count': 5, 'parsed_shard_count': 2, 'reviewed_candidate_count': 2, 'low_coverage': True}`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 79. `order_lifecycle_source_dimension_gap_rollup`

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
- evidence: `rollup_only_gap_count=150`, `unknown_source_dimensions=100`, `recommended_resolution_counts={'explicit_lifecycle_flow_source_only_blocker': 50, 'entry_label_not_applicable': 1, 'mark_not_applicable_explicitly': 24, 'join_labels_before_bucket_decision': 75}`, `missing_dimension_key_counts={'entry': 50, 'exit': 62, 'holding': 54, 'submit': 64}`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 80. `order_lifecycle_overnight_bucket_combo_overnight_decision_action_sell_today_status_sell_today_confidence_confidence_070p_profit_profit_lt_`

- title: LDM overnight bucket attribution follow-up: combo_overnight_decision=action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070
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
- evidence: `workorder_id=overnight_bucket_source_quality_2`, `bucket_type=combo_overnight_decision`, `bucket_key=action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 81. `order_lifecycle_overnight_bucket_combo_overnight_decision_action_sell_today_status_sell_today_confidence_confidence_070p_profit_profit_neg`

- title: LDM overnight bucket attribution follow-up: combo_overnight_decision=action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010
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
- evidence: `workorder_id=overnight_bucket_source_quality_1`, `bucket_type=combo_overnight_decision`, `bucket_key=action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 82. `order_lifecycle_overnight_bucket_peak_profit_band_peak_lt_zero`

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
- evidence: `workorder_id=overnight_bucket_source_quality_3`, `bucket_type=peak_profit_band`, `bucket_key=peak_lt_zero`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 83. `order_lifecycle_overnight_bucket_profit_band_profit_lt_neg070`

- title: LDM overnight bucket attribution follow-up: profit_band=profit_lt_neg070
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
- evidence: `workorder_id=overnight_bucket_source_quality_5`, `bucket_type=profit_band`, `bucket_key=profit_lt_neg070`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 84. `order_lifecycle_overnight_bucket_profit_band_profit_neg070_neg010`

- title: LDM overnight bucket attribution follow-up: profit_band=profit_neg070_neg010
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
- evidence: `workorder_id=overnight_bucket_source_quality_4`, `bucket_type=profit_band`, `bucket_key=profit_neg070_neg010`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 85. `order_lifecycle_scale_in_bucket_ai_score_band_score_60_62`

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
- evidence: `workorder_id=scale_in_bucket_source_quality_3`, `bucket_type=ai_score_band`, `bucket_key=score_60_62`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 86. `order_lifecycle_scale_in_bucket_ai_score_band_score_63_65`

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
- evidence: `workorder_id=scale_in_bucket_source_quality_5`, `bucket_type=ai_score_band`, `bucket_key=score_63_65`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 87. `order_lifecycle_scale_in_bucket_ai_score_band_score_66_69`

- title: LDM scale-in bucket attribution follow-up: ai_score_band=score_66_69
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
- evidence: `workorder_id=scale_in_bucket_source_quality_2`, `bucket_type=ai_score_band`, `bucket_key=score_66_69`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 88. `order_lifecycle_scale_in_bucket_ai_score_band_score_70p`

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

### 89. `order_lifecycle_scale_in_bucket_ai_score_band_score_lt60`

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

### 90. `order_lifecycle_scale_in_bucket_ai_score_source_score_field_backfilled`

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
- evidence: `workorder_id=scale_in_bucket_source_quality_6`, `bucket_type=ai_score_source`, `bucket_key=score_field_backfilled`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 91. `order_lifecycle_scale_in_bucket_arm_avg_down`

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
- evidence: `workorder_id=scale_in_bucket_source_quality_7`, `bucket_type=arm`, `bucket_key=AVG_DOWN`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 92. `order_lifecycle_scale_in_bucket_arm_pyramid`

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
- evidence: `workorder_id=scale_in_bucket_source_quality_8`, `bucket_type=arm`, `bucket_key=PYRAMID`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 93. `order_lifecycle_scale_in_bucket_blocker_namespace_avg_down`

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
- evidence: `workorder_id=scale_in_bucket_source_quality_9`, `bucket_type=blocker_namespace`, `bucket_key=AVG_DOWN`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 94. `order_lifecycle_scale_in_bucket_blocker_namespace_avg_down_only`

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

### 95. `order_lifecycle_entry_bucket_chosen_action_wait_requote`

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

### 96. `order_lifecycle_entry_bucket_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_l`

- title: LDM entry bucket attribution follow-up: combo_entry_spot=score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1200_1400
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
- evidence: `workorder_id=entry_bucket_source_quality_2`, `bucket_type=combo_entry_spot`, `bucket_key=score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1200_1400`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 97. `order_lifecycle_entry_bucket_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liq`

- title: LDM entry bucket attribution follow-up: combo_entry_spot=score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1000_1200
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
- evidence: `workorder_id=entry_bucket_source_quality_3`, `bucket_type=combo_entry_spot`, `bucket_key=score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1000_1200`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 98. `order_lifecycle_entry_bucket_exit_rule_scalp_hard_stop_pct`

- title: LDM entry bucket attribution follow-up: exit_rule=scalp_hard_stop_pct
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
- evidence: `workorder_id=entry_bucket_source_quality_7`, `bucket_type=exit_rule`, `bucket_key=scalp_hard_stop_pct`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 99. `order_lifecycle_entry_bucket_exit_rule_scalp_trailing_take_profit`

- title: LDM entry bucket attribution follow-up: exit_rule=scalp_trailing_take_profit
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
- evidence: `workorder_id=entry_bucket_source_quality_6`, `bucket_type=exit_rule`, `bucket_key=scalp_trailing_take_profit`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 100. `order_lifecycle_entry_bucket_liquidity_bucket_liquidity_high`

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
- evidence: `workorder_id=entry_bucket_source_quality_8`, `bucket_type=liquidity_bucket`, `bucket_key=liquidity_high`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 101. `order_lifecycle_entry_bucket_overbought_bucket_overbought_proxy_normal`

- title: LDM entry bucket attribution follow-up: overbought_bucket=overbought_proxy_normal
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
- evidence: `workorder_id=entry_bucket_source_quality_9`, `bucket_type=overbought_bucket`, `bucket_key=overbought_proxy_normal`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 102. `order_lifecycle_entry_bucket_overbought_bucket_overbought_proxy_watch`

- title: LDM entry bucket attribution follow-up: overbought_bucket=overbought_proxy_watch
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
- evidence: `workorder_id=entry_bucket_source_quality_10`, `bucket_type=overbought_bucket`, `bucket_key=overbought_proxy_watch`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### N2. `order_ai_threshold_miss_ev_recovery`

- title: AI threshold miss EV recovery
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `entry_funnel`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_missed_entry_counterfactual.py`
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

### N4. `order_latency_guard_miss_ev_recovery`

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

### N5. `order_observation_source_quality_warning_rollup`

- title: Observation source-quality warning rollup
- decision: `attach_existing_family`
- decision_reason: observation source-quality warning rollup is evidence-only visibility for warnings outside the immediate implementation allowlist
- source_report_type: `observation_source_quality_audit`
- lifecycle_stage: `source_quality_gate`
- target_subsystem: `runtime_instrumentation`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `-`
- files_likely_touched: `src/engine/observation_source_quality_audit.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_observation_source_quality_audit.py src/tests/test_build_code_improvement_workorder.py`

### N6. `order_perf_daily_report_engine_singleton`

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

### N7. `order_swing_gatekeeper_reject_threshold_review`

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

### N8. `order_swing_pattern_lab_deepseek_scale_in_events_observed`

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

### N9. `order_perf_recommend_update_vectorization`

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

### N10. `order_swing_holding_exit_contract_gap_review`

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

### N11. `order_swing_market_regime_sensitivity_review`

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

### N12. `order_swing_ofi_qi_stale_or_missing_context`

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

### N13. `order_swing_scale_in_contract_gap_review`

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

### N14. `order_perf_swing_simulation_iteration`

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

### N15. `order_swing_discovery_label_contract_gap_review`

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

### N16. `order_latency_canary_tag_완화_1축_canary_승인`

- title: latency canary tag 완화 1축 canary 승인
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `runtime_instrumentation`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_but_waiting_sample`
- files_likely_touched: `src/engine/sniper_performance_tuning_report.py`, `src/engine/daily_threshold_cycle_report.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N17. `order_panic_sell_defense_lifecycle_transition_pack`

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

### N18. `order_perf_monitor_snapshot_stream_tail`

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

### N19. `order_swing_exit_ofi_qi_smoothing_distribution`

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

### N20. `order_swing_strategy_discovery_source_quality_followup`

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

### N21. `order_panic_buying_source_quality_market_breadth_micro_coverage`

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

### N22. `order_perf_final_ensemble_records`

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

### N23. `order_swing_strategy_discovery_avoid_bucket_review`

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

### N24. `order_swing_pattern_lab_deepseek_entry_no_submissions`

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

### N26. `order_overbought_gate_miss_ev_recovery`

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

### N27. `order_swing_ai_contract_structured_output_eval`

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

### N28. `order_overbought_gate_miss_ev_회수_조건_점검`

- title: overbought gate miss EV 회수 조건 점검
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

### N30. `order_ai_threshold_miss_ev_회수_조건_점검`

- title: AI threshold miss EV 회수 조건 점검
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

### N31. `order_split_entry_rebase_수량_정합성_report_only_감사`

- title: split-entry rebase 수량 정합성 report-only 감사
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

### N32. `order_동일_종목_split_entry_soft_stop_재진입_cooldown_report_only`

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

### N33. `order_perf_kiwoom_orders_http_session_review`

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

### N34. `order_perf_config_cache_scope_review`

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

### N35. `order_perf_dashboard_db_pool_review`

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

### N36. `order_partial_fallback_확대_직후_즉시_재평가_report_only`

- title: partial → fallback 확대 직후 즉시 재평가 report-only
- decision: `reject`
- decision_reason: fallback revival or shadow reintroduction conflicts with current Plan Rebase policy
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `holding_exit`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N37. `order_perf_kiwoom_ws_tick_parse_fastpath`

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

### N38. `order_perf_raw_event_suppression_out_of_scope`

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

- 구현 결과는 `2026-06-03` 이후 postclose `threshold_cycle`, `scalping_pattern_lab_automation`, `threshold_cycle_ev`가 자동으로 다시 읽는다.
- 구현자가 수동으로 threshold 값을 바꾸는 것이 아니라, source/report/provenance를 닫아 다음 calibration이 판단하게 한다.
- 다음 Codex 세션 입력 문구: `none_for_bucket_discovery_classification`

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
