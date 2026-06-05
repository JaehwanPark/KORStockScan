# Code Improvement Workorder - 2026-06-05

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
- observation_source_quality_audit: `/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-05.json`
- codebase_performance_workorder: `-`
- pattern_lab_currentness_audit: `-`
- pattern_lab_ai_review: `-`
- producer_gap_discovery: `-`
- stage_hook_workorder_discovery: `-`
- stage_hook_runtime_scaffold: `-`
- buy_funnel_sentinel: `/home/ubuntu/KORStockScan/data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-06-05.json`
- generated_at: `2026-06-05T12:14:38+09:00`
- generation_id: `2026-06-05-ed839fa290b6`
- source_hash: `ed839fa290b6cb17960be69d4372123a8a052234c4fa3422250ccf9b36e11235`

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
- previous_generation_id: `2026-06-05-a5774af0d2b5`
- previous_source_hash: `a5774af0d2b54d9db92b851fba260f6b4e09497d4dcb226daa44752a8f2cb7a7`
- new_order_ids: `[]`
- removed_order_ids: `[]`
- decision_changed_order_ids: `['order_observation_source_quality_raw_row_exclusion_producer_gap']`

## Summary

- source_order_count: `8`
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
- threshold_ev_source_order_count: `8`
- lifecycle_submit_bucket_source_order_count: `0`
- lifecycle_holding_exit_bucket_source_order_count: `0`
- pipeline_event_verbosity_source_order_count: `0`
- observation_source_quality_source_order_count: `2`
- codebase_performance_source_order_count: `0`
- buy_funnel_sentinel_source_order_count: `6`
- entry_submit_drought_selected: `True`
- entry_submit_drought_handoff_missing: `False`
- panic_lifecycle_source_order_count: `0`
- selected_order_count: `8`
- non_selected_order_count: `0`
- source_decision_counts: `{'implement_now': 1, 'attach_existing_family': 7}`
- selected_decision_counts: `{'implement_now': 1, 'attach_existing_family': 7}`
- selected_route_counts: `{'source_quality_warning_producer_fix': 1, 'existing_family': 6, 'review_required_limit_up_locked_context': 1}`
- selected_implement_now_route_count: `1`
- selected_runtime_effect_false_count: `8`
- selected_unimplemented_runtime_effect_false_count: `1`
- selected_unimplemented_route_counts: `{'source_quality_warning_producer_fix': 1}`
- selected_implement_now_existing_implementation_count: `0`
- selected_implement_now_existing_implementation_order_ids: `[]`
- selected_implement_now_new_runtime_effect_false_count: `1`
- selected_implement_now_new_runtime_effect_false_order_ids: `['order_observation_source_quality_unknown_token_provenance_gap']`
- repeat_unresolved_escalation_count: `0`
- repeat_unresolved_escalated_order_ids: `[]`
- non_selected_decision_counts: `{}`
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

### 1. `order_observation_source_quality_unknown_token_provenance_gap`

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
- evidence: `status=warning`, `event_count=122702`, `warning_stage_count=0`, `warning_stages=`, `high_volume_no_source_field_stage_count=0`, `unknown_token_stage_count=4`, `review_warning_count=4`, `decision_authority=source_quality_only`, `runtime_effect=false`, `unknown_token_policy=warning_only_not_tuning_hard_block`, `required_action=producer_provenance_fix_or_explicit_reviewed_not_available_label`, `forbidden_uses=ignore_unknown_token_warning/silent_tuning_promotion_without_review`, `unknown:stage=scalp_entry_action_decision_snapshot event_count=3917 fields=risk_regime_context:3:0.0008`, `unknown:stage=order_leg_request event_count=11 fields=risk_regime_context:4:0.3636`, `unknown:stage=swing_sim_buy_order_assumed_filled event_count=11 fields=risk_regime_context:4:0.3636`, `unknown:stage=swing_sim_order_bundle_assumed_filled event_count=11 fields=risk_regime_context:4:0.3636`, `top_unknown_fields=risk_regime_context,risk_regime_context,risk_regime_context,risk_regime_context`
- parity_contract: -
- next_postclose_metric: observation_source_quality_audit.warning_stage_count and high_volume_no_source_field_stage_count
- files_likely_touched: `src/engine/observation_source_quality_audit.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_sim_overnight.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_observation_source_quality_audit.py src/tests/test_build_code_improvement_workorder.py`
- implementation_status: `-`
- implementation_provenance: `{"current_raw_contains_pre_fix_rows": false, "fixed_unknown_fields": ["broker_receipt_status", "fill_quality", "holding_exit_matrix_decision_alignment", "lifecycle_bucket_bucket_id", "lifecycle_bucket_entry_bucket_id", "lifecycle_bucket_entry_bucket_key", "overbought_guard_reason", "pre_submit_liquidity_value", "pre_submit_overbought_reason", "sim_pre_submit_overbought_reason", "swing_micro_ws_quote_stale"], "producer_fix_status": "open_unknown_field_producer_fix_required"}`
- automation_reentry: After implementation, rerun observation_source_quality_audit and code improvement workorder; unknown_token_stage_count should fall or remaining unknowns must carry explicit reviewed provenance.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 2. `order_entry_submit_drought_auto_resolution`

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
- evidence: `ai_confirmed_unique=94`, `budget_pass_unique=14`, `latency_pass_unique=6`, `submitted_unique=0`, `submitted_to_ai_pct=0.0`, `submitted_to_budget_pct=0.0`, `blocker:latency_block:latency_state_danger=13524`, `blocker:blocked_swing_score_vpw:-=11690`, `blocker:blocked_strength_momentum:below_strength_base=3105`, `upstream:blocked_ai_score:score_60.0=293`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=260`, `upstream:blocked_ai_score:score_62.0=186`, `latency:latency_block:latency_state_danger=13524`
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

### 3. `order_observation_source_quality_raw_row_exclusion_producer_gap`

- title: Observation source-quality raw row exclusion limit-up locked context
- decision: `attach_existing_family`
- decision_reason: raw row exclusion is concentrated in a limit-up locked context; keep it as reviewed source-quality evidence and do not create an automatic producer-fix implementation
- source_report_type: `observation_source_quality_audit`
- lifecycle_stage: `source_quality_gate`
- target_subsystem: `runtime_instrumentation`
- route: `review_required_limit_up_locked_context`
- mapped_family: `observation_source_quality_audit`
- threshold_family: `observation_source_quality_audit`
- improvement_type: `source_quality_raw_row_exclusion_limit_up_locked_context`
- confidence: `audit`
- priority: `0`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: none_direct_source_quality_attribution_only
- evidence: `status=warning`, `event_count=122702`, `warning_stage_count=0`, `warning_stages=`, `high_volume_no_source_field_stage_count=0`, `unknown_token_stage_count=4`, `review_warning_count=4`, `decision_authority=source_quality_only`, `runtime_effect=false`, `raw_row_exclusion_manifest=/home/ubuntu/KORStockScan/data/source_quality/raw_row_exclusion/2026-06-05_20260605T114859516975+0900/manifest.json`, `excluded_row_count=1602`, `stage_counts={"blocked_overbought": 779, "blocked_strength_momentum": 823}`, `field_gap_counts={"zero_fields:intraday_range_pct": 1602}`, `exclusion_reasons={"insufficient_history": 557, "not_evaluated_context": 779, "source_quality_blocker": 1602, "zero_context_sensitive": 1602}`, `first_timestamp=2026-06-05T10:54:42.721884`, `last_timestamp=2026-06-05T11:48:35.782208`, `forbidden_uses=EV/rolling/MTD/cumulative tuning/live-auto promotion/runtime approval for excluded rows`, `required_action=fix producer provenance/source-quality cause or mark reviewed_not_available/waiting_sample_only explicitly`, `producer_hint:stage=blocked_strength_momentum count=823 pipeline=ENTRY_PIPELINE subsystem=scalping_entry_or_sim_producer top_reasons=source_quality_blocker,zero_context_sensitive,insufficient_history`, `producer_hint:stage=blocked_overbought count=779 pipeline=ENTRY_PIPELINE subsystem=scalping_entry_or_sim_producer top_reasons=not_evaluated_context,source_quality_blocker,zero_context_sensitive`, `sample_row:line_no=71127 stage=blocked_overbought record_id=9276 reasons=not_evaluated_context,source_quality_blocker,zero_context_sensitive gap_fields={"zero_fields": ["intraday_range_pct"]}`, `sample_row:line_no=71129 stage=blocked_strength_momentum record_id=9276 reasons=insufficient_history,source_quality_blocker,zero_context_sensitive gap_fields={"zero_fields": ["intraday_range_pct"]}`, `sample_row:line_no=71169 stage=blocked_overbought record_id=9276 reasons=not_evaluated_context,source_quality_blocker,zero_context_sensitive gap_fields={"zero_fields": ["intraday_range_pct"]}`, `sample_row:line_no=71171 stage=blocked_strength_momentum record_id=9276 reasons=insufficient_history,source_quality_blocker,zero_context_sensitive gap_fields={"zero_fields": ["intraday_range_pct"]}`, `sample_row:line_no=71214 stage=blocked_overbought record_id=9276 reasons=not_evaluated_context,source_quality_blocker,zero_context_sensitive gap_fields={"zero_fields": ["intraday_range_pct"]}`, `sample_row:line_no=71216 stage=blocked_strength_momentum record_id=9276 reasons=insufficient_history,source_quality_blocker,zero_context_sensitive gap_fields={"zero_fields": ["intraday_range_pct"]}`, `sample_row:line_no=71254 stage=blocked_overbought record_id=9276 reasons=not_evaluated_context,source_quality_blocker,zero_context_sensitive gap_fields={"zero_fields": ["intraday_range_pct"]}`, `sample_row:line_no=71256 stage=blocked_strength_momentum record_id=9276 reasons=insufficient_history,source_quality_blocker,zero_context_sensitive gap_fields={"zero_fields": ["intraday_range_pct"]}`, `context_classification=limit_up_locked_context`, `context_evidence={"classification": "limit_up_locked_context", "excluded_row_count": 1602, "manifest_limit_up_row_count": 748, "manifest_row_count": 1602, "manifest_zero_range_row_count": 1602, "relevant_stage_count": 1602, "required_followup": "review_only_until_non_limit_up_zero_range_repeats_or_high_low_candle_source_loss_is_proven", "stages_seen": ["blocked_overbought", "blocked_strength_momentum"], "stock_codes_sample": ["003220", "005500", "092220", "109740", "126730", "128940", "160980", "183300"], "top_identity": "003220:9276", "top_identity_count": 1496, "zero_intraday_range_count": 1602}`, `required_action=review postclose only; do not auto-implement unless non-limit-up rows repeat the same zero intraday range gap or independent high/low/candle source loss is proven`
- parity_contract: -
- next_postclose_metric: observation_source_quality_audit.warning_stage_count and high_volume_no_source_field_stage_count
- files_likely_touched: `src/engine/observation_source_quality_audit.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_observation_source_quality_audit.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: Next postclose source-quality audit should reclassify only if the same intraday_range_pct=0 gap repeats in non-limit-up rows or independent high/low/candle source loss is proven.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 4. `order_entry_broker_receipt_contract_gap_review`

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
- evidence: `ai_confirmed_unique=94`, `budget_pass_unique=14`, `latency_pass_unique=6`, `submitted_unique=0`, `submitted_to_ai_pct=0.0`, `submitted_to_budget_pct=0.0`, `blocker:latency_block:latency_state_danger=13524`, `blocker:blocked_swing_score_vpw:-=11690`, `blocker:blocked_strength_momentum:below_strength_base=3105`, `upstream:blocked_ai_score:score_60.0=293`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=260`, `upstream:blocked_ai_score:score_62.0=186`, `latency:latency_block:latency_state_danger=13524`, `weak_contract_gap=broker_receipt_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 5. `order_entry_fill_quality_contract_gap_review`

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
- evidence: `ai_confirmed_unique=94`, `budget_pass_unique=14`, `latency_pass_unique=6`, `submitted_unique=0`, `submitted_to_ai_pct=0.0`, `submitted_to_budget_pct=0.0`, `blocker:latency_block:latency_state_danger=13524`, `blocker:blocked_swing_score_vpw:-=11690`, `blocker:blocked_strength_momentum:below_strength_base=3105`, `upstream:blocked_ai_score:score_60.0=293`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=260`, `upstream:blocked_ai_score:score_62.0=186`, `latency:latency_block:latency_state_danger=13524`, `weak_contract_gap=fill_quality_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 6. `order_entry_post_submit_contract_gap_review`

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
- evidence: `ai_confirmed_unique=94`, `budget_pass_unique=14`, `latency_pass_unique=6`, `submitted_unique=0`, `submitted_to_ai_pct=0.0`, `submitted_to_budget_pct=0.0`, `blocker:latency_block:latency_state_danger=13524`, `blocker:blocked_swing_score_vpw:-=11690`, `blocker:blocked_strength_momentum:below_strength_base=3105`, `upstream:blocked_ai_score:score_60.0=293`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=260`, `upstream:blocked_ai_score:score_62.0=186`, `latency:latency_block:latency_state_danger=13524`, `weak_contract_gap=post_submit_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 7. `order_entry_source_taxonomy_contract_gap_review`

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
- evidence: `ai_confirmed_unique=94`, `budget_pass_unique=14`, `latency_pass_unique=6`, `submitted_unique=0`, `submitted_to_ai_pct=0.0`, `submitted_to_budget_pct=0.0`, `blocker:latency_block:latency_state_danger=13524`, `blocker:blocked_swing_score_vpw:-=11690`, `blocker:blocked_strength_momentum:below_strength_base=3105`, `upstream:blocked_ai_score:score_60.0=293`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=260`, `upstream:blocked_ai_score:score_62.0=186`, `latency:latency_block:latency_state_danger=13524`, `weak_contract_gap=source_taxonomy_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`, `taxonomy_leakage_labels=['blocked_swing_score_vpw:-', 'blocked_swing_gap:-']`
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

### 8. `order_entry_telegram_post_submit_contract_gap_review`

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
- evidence: `ai_confirmed_unique=94`, `budget_pass_unique=14`, `latency_pass_unique=6`, `submitted_unique=0`, `submitted_to_ai_pct=0.0`, `submitted_to_budget_pct=0.0`, `blocker:latency_block:latency_state_danger=13524`, `blocker:blocked_swing_score_vpw:-=11690`, `blocker:blocked_strength_momentum:below_strength_base=3105`, `upstream:blocked_ai_score:score_60.0=293`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=260`, `upstream:blocked_ai_score:score_62.0=186`, `latency:latency_block:latency_state_danger=13524`, `weak_contract_gap=telegram_post_submit_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

## 자동화체인 재투입

- 구현 결과는 `2026-06-06` 이후 postclose `threshold_cycle`, `scalping_pattern_lab_automation`, `threshold_cycle_ev`가 자동으로 다시 읽는다.
- 구현자가 수동으로 threshold 값을 바꾸는 것이 아니라, source/report/provenance를 닫아 다음 calibration이 판단하게 한다.
- 다음 Codex 세션 입력 문구: `none_for_bucket_discovery_classification`

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
