# Code Improvement Workorder - 2026-07-29

## 목적

- Postclose 자동화가 생성한 `code_improvement_order`를 Codex 실행용 작업지시서로 변환한다.
- 입력은 scalping pattern lab automation, swing lifecycle improvement automation, swing pattern lab automation을 함께 포함할 수 있다.
- 이 문서는 repo/runtime을 직접 변경하지 않는다. 사용자가 이 문서를 Codex 세션에 넣고 구현을 요청하는 지점만 사람 개입으로 남긴다.
- 구현 후 자동화체인 재투입은 다음 postclose report, threshold calibration, daily EV report가 담당한다.

## Source

- pattern_lab_automation: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-07-29.json`
- swing_improvement_automation: `-`
- swing_pattern_lab_automation: `-`
- swing_strategy_discovery_ev: `-`
- swing_lifecycle_decision_matrix: `-`
- swing_lifecycle_bucket_discovery: `-`
- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-29.json`
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-07-29.json`
- threshold_cycle_calibration: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_calibration/threshold_cycle_calibration_2026-07-29_postclose.json`
- pipeline_event_verbosity: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-07-29.json`
- observation_source_quality_audit: `/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-29.json`
- ai_watching_score_smoothing_diagnostic: `/home/ubuntu/KORStockScan/data/report/ai_watching_score_smoothing_diagnostic/ai_watching_score_smoothing_diagnostic_2026-07-29.json`
- codebase_performance_workorder: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-07-29.json`
- pattern_lab_currentness_audit: `/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-07-29.json`
- pattern_lab_ai_review: `/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-07-29.json`
- producer_gap_discovery: `/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-07-29.json`
- stage_hook_workorder_discovery: `/home/ubuntu/KORStockScan/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_2026-07-29.json`
- stage_hook_runtime_scaffold: `/home/ubuntu/KORStockScan/data/report/stage_hook_runtime_scaffold/stage_hook_runtime_scaffold_2026-07-29.json`
- buy_funnel_sentinel: `/home/ubuntu/KORStockScan/data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-07-29.json`
- microstructure_reaction_context: `/home/ubuntu/KORStockScan/data/report/microstructure_reaction_context/microstructure_reaction_context_2026-07-29.json`
- generated_at: `2026-07-29T22:49:41+09:00`
- generation_id: `2026-07-29-b59da43d5b3f`
- source_hash: `b59da43d5b3f5a9bbd0d66e6d7efce9077f70e682675372c7ef231db50a53896`

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
- previous_generation_id: `2026-07-29-72601dca64a3`
- previous_source_hash: `72601dca64a3f134c9099f1d145ac144d9b9d1a5fd239ded400296b527327c7b`
- new_order_ids: `['order_ai_threshold_miss_ev_recovery', 'order_latency_guard_miss_ev_recovery', 'order_panic_sell_defense_lifecycle_transition_pack', 'order_partial_only_표류_전용_timeout_report_only', 'order_perf_buy_funnel_json_scan', 'order_perf_daily_report_bulk_history', 'order_perf_daily_report_engine_singleton', 'order_perf_final_ensemble_records', 'order_perf_monitor_snapshot_stream_tail', 'order_perf_sentinel_event_cache_incremental_review', 'order_rising_missed_classifier_prior_bridge', 'order_rising_missed_classifier_prior_feedback_bridge', 'order_rising_missed_scout_loss_filter', 'order_rising_missed_scout_post_sell_bridge', 'order_rising_missed_scout_scale_in_qty_evidence_split', 'order_split_entry_rebase_수량_정합성_report_only_감사', 'order_동일_종목_split_entry_soft_stop_재진입_cooldown_report_only']`
- removed_order_ids: `['order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_entry_6d966faa56', 'order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_institutional_flow_context_5ffac855c5', 'order_lifecycle_entry_bucket_chosen_action_skip_pre_submit_safety', 'order_lifecycle_entry_bucket_combo_entry_spot_score_score_unknown_source_scalp_sim_entry_ai_price_skip_order_stale_stale_not_a', 'order_lifecycle_entry_bucket_exit_rule_exit_unknown', 'order_lifecycle_entry_bucket_exit_rule_scalp_preset_hard_stop_pct', 'order_lifecycle_entry_bucket_exit_rule_scalp_trailing_take_profit', 'order_lifecycle_entry_bucket_liquidity_bucket_liquidity_not_available', 'order_lifecycle_entry_bucket_overbought_bucket_overbought_not_available', 'order_lifecycle_entry_bucket_score_band_score_unknown', 'order_lifecycle_entry_bucket_source_stage_scalp_sim_entry_ai_price_skip_order', 'order_lifecycle_source_dimension_gap_entry_combo_entry_spot_entry_combo_entry_spot_score_score_unknown_source_scalp_sim_entry_ai_pr_3694e586', 'order_lifecycle_source_dimension_gap_entry_score_band_entry_score_band_score_unknown_2083bdb1d0', 'order_observation_source_quality_unknown_token_provenance_gap']`
- decision_changed_order_ids: `[]`

## Summary

- source_order_count: `92`
- scalping_source_order_count: `10`
- swing_source_order_count: `0`
- swing_entry_bottleneck_primary: `None`
- swing_entry_bottleneck_selected: `False`
- swing_lab_source_order_count: `0`
- swing_strategy_discovery_source_order_count: `0`
- swing_lifecycle_matrix_source_order_count: `0`
- swing_lifecycle_bucket_discovery_source_order_count: `0`
- pattern_lab_currentness_source_order_count: `0`
- pattern_lab_ai_review_source_order_count: `1`
- threshold_ev_source_order_count: `14`
- entry_hurdle_backtest_source_order_count: `0`
- microstructure_reaction_context_source_order_count: `0`
- lifecycle_submit_bucket_source_order_count: `0`
- lifecycle_holding_exit_bucket_source_order_count: `8`
- pipeline_event_verbosity_source_order_count: `0`
- observation_source_quality_source_order_count: `0`
- codebase_performance_source_order_count: `12`
- buy_funnel_sentinel_source_order_count: `0`
- entry_submit_drought_selected: `False`
- entry_submit_drought_handoff_missing: `False`
- panic_lifecycle_source_order_count: `1`
- selected_order_count: `83`
- non_selected_order_count: `9`
- source_decision_counts: `{'attach_existing_family': 83, 'design_family_candidate': 3, 'defer_evidence': 3, 'reject': 3}`
- selected_decision_counts: `{'attach_existing_family': 83}`
- selected_route_counts: `{'existing_family': 72, 'performance_optimization_order': 6, 'ai_review_coverage_review': 1, 'positive_source_only_review': 1, 'source_dimension_rollup': 1, 'join_gap_enrichment': 1, 'pattern_lab_ai_review_handoff_evidence': 1}`
- selected_implement_now_route_count: `0`
- selected_runtime_effect_false_count: `83`
- selected_unimplemented_runtime_effect_false_count: `0`
- selected_unimplemented_route_counts: `{}`
- selected_terminal_non_implement_runtime_effect_false_count: `5`
- selected_terminal_non_implement_route_counts: `{'ai_review_coverage_review': 1, 'positive_source_only_review': 1, 'source_dimension_rollup': 1, 'join_gap_enrichment': 1, 'pattern_lab_ai_review_handoff_evidence': 1}`
- selected_implement_now_existing_implementation_count: `0`
- selected_implement_now_existing_implementation_order_ids: `[]`
- selected_implement_now_new_runtime_effect_false_count: `0`
- selected_implement_now_new_runtime_effect_false_order_ids: `[]`
- repeat_unresolved_escalation_count: `0`
- repeat_unresolved_escalated_order_ids: `[]`
- repeat_unresolved_structural_blocker_count: `0`
- repeat_unresolved_structural_blocker_order_ids: `[]`
- root_cause_closure_status_counts: `{'handoff_closed_root_cause_open': 20, 'implementation_done': 11, 'root_cause_closed': 47}`
- implementation_done_count: `11`
- artifact_regeneration_required_count: `0`
- handoff_closed_root_cause_open_count: `20`
- root_cause_closed_count: `47`
- needs_followup_workorder_count: `0`
- root_cause_open_top: `[{'order_id': 'order_conversion_lane_key_lineage_active_arm_07b7bc397f7a9d64', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_arm_0e6d07fa10a5b582', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_arm_0fcffe09b9b7096c', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_arm_15f74aa27eef743d', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_arm_1661ca30f0d594fd', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_arm_292c648e73675368', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_arm_2c44a9b1dd392eb3', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_arm_2d256010e69684c1', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_arm_3034ae45da8fefbc', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}, {'order_id': 'order_conversion_lane_key_lineage_active_arm_368b41a18c7e3a5e', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': None}]`
- selected_terminal_non_implement_longstanding_count: `4`
- selected_terminal_non_implement_longstanding_order_ids: `['order_lifecycle_quiet_gap_ai_review_coverage_rollup', 'order_lifecycle_quiet_gap_positive_source_only_rollup', 'order_lifecycle_source_dimension_gap_rollup', 'order_lifecycle_source_dimension_join_gap_enrichment']`
- selected_longstanding_non_implement_disposition_counts: `{'keep_visible_by_design': 4}`
- selected_longstanding_non_implement_action_required_order_ids: `[]`
- non_selected_decision_counts: `{'design_family_candidate': 3, 'defer_evidence': 3, 'reject': 3}`
- non_selected_longstanding_non_implement_disposition_counts: `{'review_required': 6}`
- non_selected_longstanding_non_implement_action_required_order_ids: `[]`
- gemini_fresh: `False`
- claude_fresh: `True`
- swing_lifecycle_audit_available: `False`
- swing_pattern_lab_automation_available: `False`
- swing_pattern_lab_fresh: `None`
- pattern_lab_currentness_status: `pass`
- pattern_lab_currentness_fail_count: `0`
- pattern_lab_ai_review_status: `warning`
- pattern_lab_ai_review_workorder_count: `1`
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

### 1. `order_conversion_lane_key_lineage_active_arm_07b7bc397f7a9d64`

- title: Conversion lane blocker follow-up: key_lineage active_arm_07b7bc397f7a9d64
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
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_07b7bc397f7a9d64`, `blocker_class=key_lineage`, `conversion_impact_rank=1`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 4, "repeat_key": "order_conversion_lane_key_lineage_active_arm_07b7bc397f7a9d64", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_07b7bc397f7a9d64", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 2. `order_latency_canary_tag_완화_1축_canary_승인`

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
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "pattern_lab_analysis_workorder_source_only", "finding_id": "latency_canary_tag_완화_1축_canary_승인", "implementation_type": "pattern_lab_report_only_instrumentation", "runtime_effect": false, "source_report_type": "scalping_pattern_lab_automation", "target_subsystem": "runtime_instrumentation"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_latency_canary_tag_완화_1축_canary_승인", "repeat_signature": "sig:scalping_pattern_lab_automation|runtime_instrumentation||latency_canary_tag_완화_1축_canary_승인||latency_canary_tag_완화_1축_canary_승인", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_but_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 3. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_10_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2ad7fdfe`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_10`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:53da8da968`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 4. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_11_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_de357c1b`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:81a1a398fd
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_11`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:81a1a398fd`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 5. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_12_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_41b4208c`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:07390fbd3e
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_12`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:07390fbd3e`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 6. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_13_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2ad7fdfe`

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
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 7. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_14_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2754550e`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:43870ece59
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_14`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:43870ece59`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 8. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_15_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2ad7fdfe`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_15`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:53da8da968`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 9. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_16_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c051278f`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:306834dafc
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_16`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:306834dafc`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 10. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_17_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_f12338ed`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6f0786a34b
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_17`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6f0786a34b`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 11. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_18_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_f12338ed`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6f0786a34b
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_18`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6f0786a34b`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 12. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_19_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_f12338ed`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6f0786a34b
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_19`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6f0786a34b`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 13. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_1_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2754550e`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:43870ece59
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_1`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:43870ece59`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 14. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_20_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_f12338ed`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6f0786a34b
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_20`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6f0786a34b`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 15. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_2_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2ad7fdfe`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_2`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:53da8da968`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 16. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_3_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_de357c1b`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:81a1a398fd
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_3`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:81a1a398fd`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 17. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_4_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_516dda63`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:661dd5007a
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_4`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:661dd5007a`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 18. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_5_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2ad7fdfe`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_5`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:53da8da968`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 19. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_6_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_fdb6ea3b`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5fc5abcf3e
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_6`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5fc5abcf3e`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 20. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_7_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2ad7fdfe`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_7`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:53da8da968`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 21. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_8_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_a59dd223`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:2ee469a4fb
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_8`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:2ee469a4fb`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 22. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_9_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_fdb6ea3b`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5fc5abcf3e
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_9`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5fc5abcf3e`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 23. `order_perf_buy_funnel_json_scan`

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
- evidence: `source_doc_hash=ffb2c2b9d6b8bf251d4f5665f1ea4ead0f680864428241fdcd6119d57f20722f`, `candidate_state=accepted`, `implementation_status=implemented`, `risk_tier=low`, `runtime_effect=false`, `strategy_effect=false`, `data_quality_effect=false`, `tuning_axis_effect=false`, `parity_contract=classification, blocker counts, unique submitted count, actual_order_submitted split, source-quality/provenance fields exact match`
- parity_contract: classification, blocker counts, unique submitted count, actual_order_submitted split, source-quality/provenance fields exact match
- next_postclose_metric: same report/output parity with lower runtime or CPU/IO overhead
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`
- acceptance_tests: `pytest src/tests/test_buy_funnel_sentinel.py`, `BUY Sentinel classification parity on same raw/cache input`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "performance_optimization_order", "repeat_count": 8, "repeat_key": "order_perf_buy_funnel_json_scan", "repeat_signature": "sig:codebase_performance_workorder|buy_funnel_sentinel|ops_performance|||buy_funnel_sentinel_field_scan_without_repeated_json_dumps", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose codebase performance source report must keep implementation_status=implemented and parity tests green.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 24. `order_stage_hook_workorder_discovery_stage_hook_holding_flow_runner_debounce_guard`

- title: Implement stage hook: holding_flow_runner_debounce_guard
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `stage_hook_workorder_discovery`
- lifecycle_stage: `holding`
- target_subsystem: `holding`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `holding_flow_runner_debounce_guard`
- confidence: `high`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: none_direct_until_separate_runtime_apply_candidate
- evidence: `strict_match_count=809`, `ambiguous_match_count=0`, `top_symbols=000150,000270,000500,000650,000660,001740,001820,002220`, `estimated_uplift_pct_sum=3842.7500`, `gap=sim-only early stop/loss followed by later runner is not isolated as a dedicated producer`, `required_microstructure_features=ws_orderbook_churn,ofi_qi_persistence,large_trade_absorption,spread_flicker,top_depth_replenishment,holding_flow_cache_freshness`, `required_producer=runner_regime_counterfactual_producer`, `readiness_tier=implementation_workorder_ready`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/stage_hook/holding/holding_flow_runner_debounce_guard.py`, `tests/stage_hook/holding/test_holding_flow_runner_debounce_guard.py`, `config/buckets/stage_hook_holding.yaml`
- acceptance_tests: `hook_input_output_contract_test: must pass`, `forbidden_use_authority_test: must confirm no runtime authority`, `disabled_initial_runtime_state_test: must verify runtime_effect=false`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "hook_name": "holding_flow_runner_debounce_guard", "implementation_files": ["src/engine/automation/stage_hook_runtime_scaffold.py"], "initial_runtime_state": "disabled", "requires_separate_runtime_apply_candidate": true, "runtime_effect": false, "source_report_type": "stage_hook_runtime_scaffold"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_stage_hook_workorder_discovery_stage_hook_holding_flow_runner_debounce_guard", "repeat_signature": "sig:stage_hook_workorder_discovery|holding|holding|holding_flow_runner_debounce_guard||implement_stage_hook_holding_flow_runner_debounce_guard", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

Stage hook candidate:

- hook_name: `holding_flow_runner_debounce_guard`
- hook_class: `runtime_arbitration_hook`
- stage: `holding`
- initial_authority: `source_only_proposal`
- readiness_tier: `implementation_workorder_ready`
- evidence_score: `100.0`
- action_namespace: `EXIT_CONFIRM`, `HOLD_REVIEW`, `TRIM`
- action_namespace_scope: `review_only_labels_not_runtime_actions`
- required_source_artifacts: `runner_regime_counterfactual_producer`
- required_mapping_tests: `hook_input_output_contract_test`, `forbidden_use_authority_test`, `disabled_initial_runtime_state_test`
- rollback_guard_requirements: `hard_safety_veto_preserved`, `broker_account_order_quantity_cooldown_veto_preserved`, `post_apply_attribution_breach_guard_defined`
- forbidden_uses: `account guard bypass`, `bot restart`, `broker guard bypass`, `broker order submit`, `cooldown guard bypass`, `emergency stop override`, `entry decision override`, `exit decision override`, `hard stop override`, `order guard bypass`, `position cap release`, `protect stop override`, `provider change`, `quantity guard bypass`, `real order enablement`, `threshold mutation`, `real_1share_as_preapply_primary_ev`, `real_one_share_as_preapply_primary_ev`, `merge_real_pnl_with_sim_probe_ev`, `runtime_change_from_preapply_real_sample`

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 25. `order_stage_hook_workorder_discovery_stage_hook_plateau_breakdown_exit_arbitration_probe`

- title: Implement stage hook: plateau_breakdown_exit_arbitration_probe
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `stage_hook_workorder_discovery`
- lifecycle_stage: `exit`
- target_subsystem: `exit`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `plateau_breakdown_exit_arbitration_probe`
- confidence: `high`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: none_direct_until_separate_runtime_apply_candidate
- evidence: `strict_match_count=959`, `ambiguous_match_count=0`, `top_symbols=000150,000240,000370,000500,000660,000990,001440,001740`, `estimated_giveback_pct_sum=4744.0100`, `gap=sim-only prior modest win followed by late stop/giveback is not isolated as a dedicated producer`, `required_producer=plateau_breakdown_exit_counterfactual_producer`, `readiness_tier=implementation_workorder_ready`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/stage_hook/exit/plateau_breakdown_exit_arbitration_probe.py`, `tests/stage_hook/exit/test_plateau_breakdown_exit_arbitration_probe.py`, `config/buckets/stage_hook_exit.yaml`
- acceptance_tests: `hook_input_output_contract_test: must pass`, `forbidden_use_authority_test: must confirm no runtime authority`, `disabled_initial_runtime_state_test: must verify runtime_effect=false`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "hook_name": "plateau_breakdown_exit_arbitration_probe", "implementation_files": ["src/engine/automation/stage_hook_runtime_scaffold.py"], "initial_runtime_state": "disabled", "requires_separate_runtime_apply_candidate": true, "runtime_effect": false, "source_report_type": "stage_hook_runtime_scaffold"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_stage_hook_workorder_discovery_stage_hook_plateau_breakdown_exit_arbitration_probe", "repeat_signature": "sig:stage_hook_workorder_discovery|exit|exit|plateau_breakdown_exit_arbitration_probe||implement_stage_hook_plateau_breakdown_exit_arbitration_probe", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

Stage hook candidate:

- hook_name: `plateau_breakdown_exit_arbitration_probe`
- hook_class: `runtime_arbitration_hook`
- stage: `exit`
- initial_authority: `source_only_proposal`
- readiness_tier: `implementation_workorder_ready`
- evidence_score: `100.0`
- action_namespace: `EXIT_CONFIRM`, `TAKE_PROFIT_ON_PLATEAU`, `HOLD_REVIEW`
- action_namespace_scope: `review_only_labels_not_runtime_actions`
- required_source_artifacts: `plateau_breakdown_exit_counterfactual_producer`
- required_mapping_tests: `hook_input_output_contract_test`, `forbidden_use_authority_test`, `disabled_initial_runtime_state_test`
- rollback_guard_requirements: `hard_safety_veto_preserved`, `broker_account_order_quantity_cooldown_veto_preserved`, `post_apply_attribution_breach_guard_defined`
- forbidden_uses: `account guard bypass`, `bot restart`, `broker guard bypass`, `broker order submit`, `cooldown guard bypass`, `emergency stop override`, `entry decision override`, `exit decision override`, `hard stop override`, `order guard bypass`, `position cap release`, `protect stop override`, `provider change`, `quantity guard bypass`, `real order enablement`, `threshold mutation`, `real_1share_as_preapply_primary_ev`, `real_one_share_as_preapply_primary_ev`, `merge_real_pnl_with_sim_probe_ev`, `runtime_change_from_preapply_real_sample`

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 26. `order_conversion_lane_key_lineage_active_arm_0e6d07fa10a5b582`

- title: Conversion lane blocker follow-up: key_lineage active_arm_0e6d07fa10a5b582
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
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_0e6d07fa10a5b582`, `blocker_class=key_lineage`, `conversion_impact_rank=2`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_conversion_lane_key_lineage_active_arm_0e6d07fa10a5b582", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_0e6d07fa10a5b582", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 27. `order_latency_guard_miss_ev_recovery`

- title: latency guard miss EV recovery
- decision: `attach_existing_family`
- decision_reason: instrumentation/provenance contract is already implemented; keep as report source for the existing family
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `runtime_instrumentation`
- route: `existing_family`
- mapped_family: `dynamic_entry_price_resolver`
- threshold_family: `dynamic_entry_price_resolver`
- improvement_type: `latency_guard_miss_ev_recovery`
- confidence: `solo`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve EV attribution and prepare bounded calibration input.
- evidence: `{'total_blocked': 142075, 'block_ratio': 99.6, 'days': 41}`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/sniper_performance_tuning_report.py`, `src/engine/daily_threshold_cycle_report.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`
- implementation_status: `implemented_but_waiting_sample`
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "pattern_lab_analysis_workorder_source_only", "finding_id": "latency_guard_miss_ev_recovery", "implementation_type": "pattern_lab_report_only_instrumentation", "runtime_effect": false, "source_report_type": "scalping_pattern_lab_automation", "target_subsystem": "runtime_instrumentation"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_latency_guard_miss_ev_recovery", "repeat_signature": "sig:scalping_pattern_lab_automation|runtime_instrumentation||latency_guard_miss_ev_recovery||latency_guard_miss_ev_recovery", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose calibration consumes the implemented report/provenance fields; no runtime mutation.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 28. `order_lifecycle_exit_bucket_exit_outcome_outcome_not_applicable_partial_exit`

- title: LDM exit bucket source-quality follow-up: exit_outcome=outcome_not_applicable_partial_exit
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
- evidence: `workorder_id=exit_bucket_source_quality_1`, `bucket_type=exit_outcome`, `bucket_key=outcome_not_applicable_partial_exit`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "outcome_not_applicable_partial_exit", "bucket_type": "exit_outcome", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 4, "repeat_key": "order_lifecycle_exit_bucket_exit_outcome_outcome_not_applicable_partial_exit", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_exit_outcome_outcome_not_applicable_par", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 29. `order_lifecycle_exit_bucket_exit_rule_scalp_sim_panic_lifecycle_partial_exit`

- title: LDM exit bucket source-quality follow-up: exit_rule=scalp_sim_panic_lifecycle_partial_exit
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
- evidence: `workorder_id=exit_bucket_source_quality_2`, `bucket_type=exit_rule`, `bucket_key=scalp_sim_panic_lifecycle_partial_exit`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "scalp_sim_panic_lifecycle_partial_exit", "bucket_type": "exit_rule", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 4, "repeat_key": "order_lifecycle_exit_bucket_exit_rule_scalp_sim_panic_lifecycle_partial_exit", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_exit_rule_scalp_sim_panic_lifecycle_par", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 30. `order_lifecycle_exit_bucket_exit_source_stage_scalp_sim_partial_sell_order_assumed_filled`

- title: LDM exit bucket source-quality follow-up: exit_source_stage=scalp_sim_partial_sell_order_assumed_filled
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
- evidence: `workorder_id=exit_bucket_source_quality_3`, `bucket_type=exit_source_stage`, `bucket_key=scalp_sim_partial_sell_order_assumed_filled`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "scalp_sim_partial_sell_order_assumed_filled", "bucket_type": "exit_source_stage", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 4, "repeat_key": "order_lifecycle_exit_bucket_exit_source_stage_scalp_sim_partial_sell_order_assumed_filled", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_exit_source_stage_scalp_sim_partial_sel", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 31. `order_lifecycle_exit_bucket_exit_source_stage_sim_post_sell_evaluation`

- title: LDM exit bucket source-quality follow-up: exit_source_stage=sim_post_sell_evaluation
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
- evidence: `workorder_id=exit_bucket_source_quality_4`, `bucket_type=exit_source_stage`, `bucket_key=sim_post_sell_evaluation`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "sim_post_sell_evaluation", "bucket_type": "exit_source_stage", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 32. `order_lifecycle_exit_bucket_profit_band_profit_lt_neg070`

- title: LDM exit bucket source-quality follow-up: profit_band=profit_lt_neg070
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
- evidence: `workorder_id=exit_bucket_source_quality_5`, `bucket_type=profit_band`, `bucket_key=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "profit_lt_neg070", "bucket_type": "profit_band", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 4, "repeat_key": "order_lifecycle_exit_bucket_profit_band_profit_lt_neg070", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_profit_band_profit_lt_neg070", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 33. `order_lifecycle_holding_bucket_held_bucket_held_not_applicable_at_start`

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
- evidence: `workorder_id=holding_bucket_source_quality_1`, `bucket_type=held_bucket`, `bucket_key=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "held_not_applicable_at_start", "bucket_type": "held_bucket", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 34. `order_lifecycle_holding_bucket_holding_action_wait`

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
- evidence: `workorder_id=holding_bucket_source_quality_2`, `bucket_type=holding_action`, `bucket_key=WAIT`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "WAIT", "bucket_type": "holding_action", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 35. `order_lifecycle_holding_bucket_holding_source_stage_scalp_sim_holding_started`

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
- evidence: `workorder_id=holding_bucket_source_quality_3`, `bucket_type=holding_source_stage`, `bucket_key=scalp_sim_holding_started`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "scalp_sim_holding_started", "bucket_type": "holding_source_stage", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 36. `order_perf_daily_report_bulk_history`

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
- evidence: `source_doc_hash=ffb2c2b9d6b8bf251d4f5665f1ea4ead0f680864428241fdcd6119d57f20722f`, `candidate_state=accepted`, `implementation_status=implemented`, `risk_tier=medium`, `runtime_effect=false`, `strategy_effect=false`, `data_quality_effect=false`, `tuning_axis_effect=false`, `parity_contract=per-stock history window, feature columns, model input row count, and report JSON exact match`
- parity_contract: per-stock history window, feature columns, model input row count, and report JSON exact match
- next_postclose_metric: same report/output parity with lower runtime or CPU/IO overhead
- files_likely_touched: `src/engine/daily_report_service.py`
- acceptance_tests: `pytest src/tests/test_daily_report_service.py src/tests/test_daily_report.py`, `daily report output parity on injected DB/model fixture`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "performance_optimization_order", "repeat_count": 8, "repeat_key": "order_perf_daily_report_bulk_history", "repeat_signature": "sig:codebase_performance_workorder|daily_report|ops_performance|||daily_report_market_snapshot_bulk_history_query", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose codebase performance source report must keep implementation_status=implemented and parity tests green.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 37. `order_rising_missed_classifier_prior_feedback_bridge`

- title: rising missed cumulative classifier prior bridge
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `rising_missed_scout_workorder`
- lifecycle_stage: `entry`
- target_subsystem: `rising_missed_entry_classifier`
- route: `existing_family`
- mapped_family: `rising_missed_classifier_prior_feedback_bridge`
- threshold_family: `rising_missed_classifier_prior_feedback_bridge`
- improvement_type: `source_only_classifier_prior_workorder`
- confidence: `cumulative_source_only`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Feed cumulative ADM/LDM prior recommendations back into the rising-missed scout loop as source-only classifier evidence.
- evidence: `prior_count=37`, `recommendation_counts={"hold_sample": 26, "loss_filter": 6, "positive_prior": 1, "source_quality_blocked": 4}`, `runtime_effect=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/monitoring/rising_missed_classifier_prior.py`, `src/engine/monitoring/rising_missed_scout_workorder.py`, `src/engine/scalping/rising_missed_one_share_entry.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_classifier_prior.py src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py`, `prior bridge remains source-only and cannot mutate one-share allow/block, runtime thresholds, broker/order guards, provider route, or bot state`
- implementation_status: `implemented`
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "source_only_classifier_prior_no_runtime_mutation", "implementation_type": "rising_missed_classifier_prior_feedback_bridge", "prior_count": 37, "recommendation_counts": {"hold_sample": 26, "loss_filter": 6, "positive_prior": 1, "source_quality_blocked": 4}, "root_cause_closure_status_hint": "implementation_done", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_rising_missed_classifier_prior_feedback_bridge", "repeat_signature": "sig:rising_missed_scout_workorder|rising_missed_entry_classifier|entry|source_only_classifier_prior_workorder|rising_missed_classifier_prior_feedback_bridge|rising_missed_cumulative_classifier_prior_bridge", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 38. `order_rising_missed_scout_loss_filter`

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
- evidence: `loser_count=2`, `loser_avg_profit_rate=-1.95`, `loser_avg_peak_profit=0.395`, `shared_source_signature_count=0`, `losers_also_had_latency_pass=True`, `losers_also_had_order_bundle_submitted=True`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/monitoring/rising_missed_scout_workorder.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py`, `loss filter is source-only and does not relax stops or broker/order guards`
- implementation_status: `implemented`
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "source_only_operational_workorder", "implementation_type": "forced_scout_loss_filter_source_split", "joined_post_sell_loser_count": 2, "root_cause_closure_status_hint": "implementation_done", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_rising_missed_scout_loss_filter", "repeat_signature": "sig:rising_missed_scout_workorder|entry_risk_filter|entry|source_only_operational_workorder|rising_missed_scout_loss_filter|rising_missed_scout_loss_filter_before_any_expansion", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 39. `order_rising_missed_scout_post_sell_bridge`

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
- evidence: `winner_count=3`, `loser_count=2`, `winner_avg_profit_rate=0.3133`, `shared_source_signature_count=0`, `runner_review_candidate_count=0`, `current_missed_count=0`, `current_missed_eligible_count=0`, `all_winner_rows_had_latency_pass=True`, `all_winner_rows_had_order_bundle_submitted=True`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/monitoring/rising_missed_scout_workorder.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py`, `forced scout remains excluded from normal BUY/submit/fill success counts`, `runtime_effect remains false until a separate approved runtime family exists`
- implementation_status: `implemented`
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "source_only_operational_workorder", "implementation_type": "forced_scout_post_sell_source_bridge", "joined_post_sell_loser_count": 2, "joined_post_sell_winner_count": 3, "root_cause_closure_status_hint": "implementation_done", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_rising_missed_scout_post_sell_bridge", "repeat_signature": "sig:rising_missed_scout_workorder|entry_freshness|entry|source_only_operational_workorder|rising_missed_scout_post_sell_bridge|rising_missed_scout_post_sell_bridge_for_normal_entry_recheck", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 40. `order_rising_missed_scout_scale_in_qty_evidence_split`

- title: rising missed scout scale-in quantity and evidence blocker split
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `rising_missed_scout_workorder`
- lifecycle_stage: `scale_in`
- target_subsystem: `scale_in_quantity_and_evidence`
- route: `existing_family`
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
- evidence: `profitable_forced_scout_count=3`, `qty_block_record_count=1`, `scale_in_executed_record_count=0`, `qty_block_reason_counts=position_cap_or_budget=2`, `price_guard_block_record_count=0`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/monitoring/rising_missed_scout_workorder.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py`, `qty/evidence split remains source-only and does not release position cap or quantity guard`
- implementation_status: `implemented`
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "source_only_scale_in_bottleneck_analysis", "implementation_type": "forced_scout_scale_in_qty_evidence_source_split", "qty_block_record_count": 1, "root_cause_closure_status_hint": "implementation_done", "runtime_effect": false, "scale_in_executed_record_count": 0}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_rising_missed_scout_scale_in_qty_evidence_split", "repeat_signature": "sig:rising_missed_scout_workorder|scale_in_quantity_and_evidence|scale_in|source_only_scale_in_bottleneck_workorder|rising_missed_scout_scale_in_qty_evidence_split|rising_missed_scout_scale_in_quantity_and_evidence_blocker_split", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 41. `order_ai_threshold_miss_ev_recovery`

- title: AI threshold miss EV recovery
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `entry_funnel`
- route: `existing_family`
- mapped_family: `score65_74_recovery_probe`
- threshold_family: `score65_74_recovery_probe`
- improvement_type: `threshold_family_input`
- confidence: `solo`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve EV attribution and prepare bounded calibration input.
- evidence: `{'total_blocked': 293589, 'block_ratio': 99.8, 'days': 41}`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_missed_entry_counterfactual.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "pattern_lab_analysis_workorder_source_only", "implementation_type": "pattern_lab_existing_family_source_metric", "implemented_scope": "score65_74_recovery_probe_source_metric_provenance", "runtime_effect": false, "source_contract": "scalping_ai_threshold_miss_source_metric_v1", "source_fields": ["total_blocked", "block_ratio", "days"], "source_metric_snapshot": {"block_ratio": 99.8, "days": 41, "mapped_family": "score65_74_recovery_probe", "total_blocked": 293589}, "source_report_type": "scalping_pattern_lab_automation"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_ai_threshold_miss_ev_recovery", "repeat_signature": "sig:scalping_pattern_lab_automation|entry_funnel||threshold_family_input||ai_threshold_miss_ev_recovery", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 42. `order_conversion_lane_key_lineage_active_arm_0fcffe09b9b7096c`

- title: Conversion lane blocker follow-up: key_lineage active_arm_0fcffe09b9b7096c
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
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_0fcffe09b9b7096c`, `blocker_class=key_lineage`, `conversion_impact_rank=3`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 43. `order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_lifecycle_ai_context_attribution_8b12f01b14`

- title: Lifecycle bucket discovery follow-up: source_contract:source_added:lifecycle_ai_context_attribution:source_key_lifecycle_ai_context_attribution
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `source_contract`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `existing_family`
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
- evidence: `bucket_id=source_contract:source_added:lifecycle_ai_context_attribution:source_key_lifecycle_ai_context_attribution`, `source_bucket_id=source_contract:source_added:lifecycle_ai_context_attribution:8b12f01b14`, `canonical_bucket=source_contract:source_added:lifecycle_ai_context_attribution`, `legacy_raw_bucket_key=lifecycle_ai_context_attribution`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=keep_existing_bucket`, `ai_tier2_taxonomy_decision=keep_bucket`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=source_only_observation`, `stage=source_contract`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=update_source_contract_or_taxonomy`, `recommended_resolution=update_source_contract_or_taxonomy`, `source_dimension_gap=`, `missing_dimension_keys=[]`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"actual_order_submitted": false, "ai_tier2_taxonomy_decision": "keep_bucket", "allowed_runtime_apply": false, "broker_order_forbidden": true, "decision_authority": "source_contract_drift_detection", "evidence_grade": "source_only", "implementation_type": "lifecycle_source_contract_drift_source_only_provenance", "root_cause_closure_status_hint": "root_cause_closed", "runtime_effect": false, "source_bucket_kind": "source_only_observation", "source_contract_change_count": 12, "source_contract_status": "warning", "transition_target": "source_only_keep_collecting"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 44. `order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_scale_in_attribution_792528d29e`

- title: Lifecycle bucket discovery follow-up: source_contract:source_added:scale_in_attribution:source_key_scale_in_attribution
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `source_contract`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `existing_family`
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
- evidence: `bucket_id=source_contract:source_added:scale_in_attribution:source_key_scale_in_attribution`, `source_bucket_id=source_contract:source_added:scale_in_attribution:792528d29e`, `canonical_bucket=source_contract:source_added:scale_in_attribution`, `legacy_raw_bucket_key=scale_in_attribution`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=keep_existing_bucket`, `ai_tier2_taxonomy_decision=keep_bucket`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=source_only_observation`, `stage=source_contract`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=update_source_contract_or_taxonomy`, `recommended_resolution=update_source_contract_or_taxonomy`, `source_dimension_gap=`, `missing_dimension_keys=[]`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"actual_order_submitted": false, "ai_tier2_taxonomy_decision": "keep_bucket", "allowed_runtime_apply": false, "broker_order_forbidden": true, "decision_authority": "source_contract_drift_detection", "evidence_grade": "source_only", "implementation_type": "lifecycle_source_contract_drift_source_only_provenance", "root_cause_closure_status_hint": "root_cause_closed", "runtime_effect": false, "source_bucket_kind": "source_only_observation", "source_contract_change_count": 12, "source_contract_status": "warning", "transition_target": "source_only_keep_collecting"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 45. `order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_scale_in_counterfactual_enrichment_24ee1298bf`

- title: Lifecycle bucket discovery follow-up: source_contract:source_added:scale_in_counterfactual_enrichment:source_key_scale_in_counterfactual_enrichment
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `source_contract`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `existing_family`
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
- evidence: `bucket_id=source_contract:source_added:scale_in_counterfactual_enrichment:source_key_scale_in_counterfactual_enrichment`, `source_bucket_id=source_contract:source_added:scale_in_counterfactual_enrichment:24ee1298bf`, `canonical_bucket=source_contract:source_added:scale_in_counterfactual_enrichment`, `legacy_raw_bucket_key=scale_in_counterfactual_enrichment`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=keep_existing_bucket`, `ai_tier2_taxonomy_decision=keep_bucket`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=source_only_observation`, `stage=source_contract`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=update_source_contract_or_taxonomy`, `recommended_resolution=update_source_contract_or_taxonomy`, `source_dimension_gap=`, `missing_dimension_keys=[]`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"actual_order_submitted": false, "ai_tier2_taxonomy_decision": "keep_bucket", "allowed_runtime_apply": false, "broker_order_forbidden": true, "decision_authority": "source_contract_drift_detection", "evidence_grade": "source_only", "implementation_type": "lifecycle_source_contract_drift_source_only_provenance", "root_cause_closure_status_hint": "root_cause_closed", "runtime_effect": false, "source_bucket_kind": "source_only_observation", "source_contract_change_count": 12, "source_contract_status": "warning", "transition_target": "source_only_keep_collecting"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 46. `order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_scalp_sim_holding_1fe719177c`

- title: Lifecycle bucket discovery follow-up: source_contract:source_added:scalp_sim_holding:source_key_scalp_sim_holding
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `source_contract`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `existing_family`
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
- evidence: `bucket_id=source_contract:source_added:scalp_sim_holding:source_key_scalp_sim_holding`, `source_bucket_id=source_contract:source_added:scalp_sim_holding:1fe719177c`, `canonical_bucket=source_contract:source_added:scalp_sim_holding`, `legacy_raw_bucket_key=scalp_sim_holding`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=keep_existing_bucket`, `ai_tier2_taxonomy_decision=keep_bucket`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=source_only_observation`, `stage=source_contract`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=update_source_contract_or_taxonomy`, `recommended_resolution=update_source_contract_or_taxonomy`, `source_dimension_gap=`, `missing_dimension_keys=[]`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"actual_order_submitted": false, "ai_tier2_taxonomy_decision": "keep_bucket", "allowed_runtime_apply": false, "broker_order_forbidden": true, "decision_authority": "source_contract_drift_detection", "evidence_grade": "source_only", "implementation_type": "lifecycle_source_contract_drift_source_only_provenance", "root_cause_closure_status_hint": "root_cause_closed", "runtime_effect": false, "source_bucket_kind": "source_only_observation", "source_contract_change_count": 12, "source_contract_status": "warning", "transition_target": "source_only_keep_collecting"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 47. `order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_scalp_sim_overnight_bbc5c8073f`

- title: Lifecycle bucket discovery follow-up: source_contract:source_added:scalp_sim_overnight:source_key_scalp_sim_overnight
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `source_contract`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `existing_family`
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
- evidence: `bucket_id=source_contract:source_added:scalp_sim_overnight:source_key_scalp_sim_overnight`, `source_bucket_id=source_contract:source_added:scalp_sim_overnight:bbc5c8073f`, `canonical_bucket=source_contract:source_added:scalp_sim_overnight`, `legacy_raw_bucket_key=scalp_sim_overnight`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=keep_existing_bucket`, `ai_tier2_taxonomy_decision=keep_bucket`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=source_only_observation`, `stage=source_contract`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=update_source_contract_or_taxonomy`, `recommended_resolution=update_source_contract_or_taxonomy`, `source_dimension_gap=`, `missing_dimension_keys=[]`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"actual_order_submitted": false, "ai_tier2_taxonomy_decision": "keep_bucket", "allowed_runtime_apply": false, "broker_order_forbidden": true, "decision_authority": "source_contract_drift_detection", "evidence_grade": "source_only", "implementation_type": "lifecycle_source_contract_drift_source_only_provenance", "root_cause_closure_status_hint": "root_cause_closed", "runtime_effect": false, "source_bucket_kind": "source_only_observation", "source_contract_change_count": 12, "source_contract_status": "warning", "transition_target": "source_only_keep_collecting"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 48. `order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_scalp_sim_panic_2d758895e8`

- title: Lifecycle bucket discovery follow-up: source_contract:source_added:scalp_sim_panic:source_key_scalp_sim_panic
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `source_contract`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `existing_family`
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
- evidence: `bucket_id=source_contract:source_added:scalp_sim_panic:source_key_scalp_sim_panic`, `source_bucket_id=source_contract:source_added:scalp_sim_panic:2d758895e8`, `canonical_bucket=source_contract:source_added:scalp_sim_panic`, `legacy_raw_bucket_key=scalp_sim_panic`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=keep_existing_bucket`, `ai_tier2_taxonomy_decision=keep_bucket`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=source_only_observation`, `stage=source_contract`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=update_source_contract_or_taxonomy`, `recommended_resolution=update_source_contract_or_taxonomy`, `source_dimension_gap=`, `missing_dimension_keys=[]`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"actual_order_submitted": false, "ai_tier2_taxonomy_decision": "keep_bucket", "allowed_runtime_apply": false, "broker_order_forbidden": true, "decision_authority": "source_contract_drift_detection", "evidence_grade": "source_only", "implementation_type": "lifecycle_source_contract_drift_source_only_provenance", "root_cause_closure_status_hint": "root_cause_closed", "runtime_effect": false, "source_bucket_kind": "source_only_observation", "source_contract_change_count": 12, "source_contract_status": "warning", "transition_target": "source_only_keep_collecting"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 49. `order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_scalp_sim_scale_in_266afa66b7`

- title: Lifecycle bucket discovery follow-up: source_contract:source_added:scalp_sim_scale_in:source_key_scalp_sim_scale_in
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `source_contract`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `existing_family`
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
- evidence: `bucket_id=source_contract:source_added:scalp_sim_scale_in:source_key_scalp_sim_scale_in`, `source_bucket_id=source_contract:source_added:scalp_sim_scale_in:266afa66b7`, `canonical_bucket=source_contract:source_added:scalp_sim_scale_in`, `legacy_raw_bucket_key=scalp_sim_scale_in`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=keep_existing_bucket`, `ai_tier2_taxonomy_decision=keep_bucket`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=source_only_observation`, `stage=source_contract`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=update_source_contract_or_taxonomy`, `recommended_resolution=update_source_contract_or_taxonomy`, `source_dimension_gap=`, `missing_dimension_keys=[]`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"actual_order_submitted": false, "ai_tier2_taxonomy_decision": "keep_bucket", "allowed_runtime_apply": false, "broker_order_forbidden": true, "decision_authority": "source_contract_drift_detection", "evidence_grade": "source_only", "implementation_type": "lifecycle_source_contract_drift_source_only_provenance", "root_cause_closure_status_hint": "root_cause_closed", "runtime_effect": false, "source_bucket_kind": "source_only_observation", "source_contract_change_count": 12, "source_contract_status": "warning", "transition_target": "source_only_keep_collecting"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 50. `order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_scalp_sim_submit_4337b300b2`

- title: Lifecycle bucket discovery follow-up: source_contract:source_added:scalp_sim_submit:source_key_scalp_sim_submit
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `source_contract`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `existing_family`
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
- evidence: `bucket_id=source_contract:source_added:scalp_sim_submit:source_key_scalp_sim_submit`, `source_bucket_id=source_contract:source_added:scalp_sim_submit:4337b300b2`, `canonical_bucket=source_contract:source_added:scalp_sim_submit`, `legacy_raw_bucket_key=scalp_sim_submit`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=keep_existing_bucket`, `ai_tier2_taxonomy_decision=keep_bucket`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=source_only_observation`, `stage=source_contract`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=update_source_contract_or_taxonomy`, `recommended_resolution=update_source_contract_or_taxonomy`, `source_dimension_gap=`, `missing_dimension_keys=[]`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"actual_order_submitted": false, "ai_tier2_taxonomy_decision": "keep_bucket", "allowed_runtime_apply": false, "broker_order_forbidden": true, "decision_authority": "source_contract_drift_detection", "evidence_grade": "source_only", "implementation_type": "lifecycle_source_contract_drift_source_only_provenance", "root_cause_closure_status_hint": "root_cause_closed", "runtime_effect": false, "source_bucket_kind": "source_only_observation", "source_contract_change_count": 12, "source_contract_status": "warning", "transition_target": "source_only_keep_collecting"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 51. `order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_sim_post_sell_db99eef989`

- title: Lifecycle bucket discovery follow-up: source_contract:source_added:sim_post_sell:source_key_sim_post_sell
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `source_contract`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `existing_family`
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
- evidence: `bucket_id=source_contract:source_added:sim_post_sell:source_key_sim_post_sell`, `source_bucket_id=source_contract:source_added:sim_post_sell:db99eef989`, `canonical_bucket=source_contract:source_added:sim_post_sell`, `legacy_raw_bucket_key=sim_post_sell`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=keep_existing_bucket`, `ai_tier2_taxonomy_decision=keep_bucket`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=source_only_observation`, `stage=source_contract`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=update_source_contract_or_taxonomy`, `recommended_resolution=update_source_contract_or_taxonomy`, `source_dimension_gap=`, `missing_dimension_keys=[]`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"actual_order_submitted": false, "ai_tier2_taxonomy_decision": "keep_bucket", "allowed_runtime_apply": false, "broker_order_forbidden": true, "decision_authority": "source_contract_drift_detection", "evidence_grade": "source_only", "implementation_type": "lifecycle_source_contract_drift_source_only_provenance", "root_cause_closure_status_hint": "root_cause_closed", "runtime_effect": false, "source_bucket_kind": "source_only_observation", "source_contract_change_count": 12, "source_contract_status": "warning", "transition_target": "source_only_keep_collecting"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 52. `order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_wait6579_c8aa00f461`

- title: Lifecycle bucket discovery follow-up: source_contract:source_added:wait6579:source_key_wait6579
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `source_contract`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `existing_family`
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
- evidence: `bucket_id=source_contract:source_added:wait6579:source_key_wait6579`, `source_bucket_id=source_contract:source_added:wait6579:c8aa00f461`, `canonical_bucket=source_contract:source_added:wait6579`, `legacy_raw_bucket_key=wait6579`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=keep_existing_bucket`, `ai_tier2_taxonomy_decision=keep_bucket`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=source_only_observation`, `stage=source_contract`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=update_source_contract_or_taxonomy`, `recommended_resolution=update_source_contract_or_taxonomy`, `source_dimension_gap=`, `missing_dimension_keys=[]`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"actual_order_submitted": false, "ai_tier2_taxonomy_decision": "keep_bucket", "allowed_runtime_apply": false, "broker_order_forbidden": true, "decision_authority": "source_contract_drift_detection", "evidence_grade": "source_only", "implementation_type": "lifecycle_source_contract_drift_source_only_provenance", "root_cause_closure_status_hint": "root_cause_closed", "runtime_effect": false, "source_bucket_kind": "source_only_observation", "source_contract_change_count": 12, "source_contract_status": "warning", "transition_target": "source_only_keep_collecting"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 53. `order_lifecycle_quiet_gap_ai_review_coverage_rollup`

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
- evidence: `quiet_gap_count=156`, `rollup_required_count=156`, `sim_live_connected_quiet_gap_count=0`, `quiet_gap_type_counts={'positive_source_only_keep_collecting': 155, 'ai_review_parsed_low_coverage': 1}`, `ai_review_coverage={'status': 'parsed', 'shard_count': 5, 'parsed_shard_count': 4, 'reviewed_candidate_count': 4, 'low_coverage': True}`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 54. `order_lifecycle_quiet_gap_positive_source_only_rollup`

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
- evidence: `quiet_gap_count=156`, `rollup_required_count=156`, `sim_live_connected_quiet_gap_count=0`, `quiet_gap_type_counts={'positive_source_only_keep_collecting': 155, 'ai_review_parsed_low_coverage': 1}`, `ai_review_coverage={'status': 'parsed', 'shard_count': 5, 'parsed_shard_count': 4, 'reviewed_candidate_count': 4, 'low_coverage': True}`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: quiet_gap_summary rollup counts remain visible until explicitly resolved.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `terminal_existing_family_evidence`
- root_cause_closure_status: `-`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "terminal_existing_family_evidence", "previous_route": "positive_source_only_review", "repeat_count": 8, "repeat_key": "order_lifecycle_quiet_gap_positive_source_only_rollup", "repeat_signature": "sig:lifecycle_bucket_discovery_quiet_gap_rollup|lifecycle_bucket_discovery_taxonomy_provenance|multi_stage|quiet_gap_rollup_evidence|lifecycle_bucket_discovery|lifecycle_quiet_gap_positive_source_only_review", "review_disposition": "keep_visible_by_design"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose checklist/workorder should keep quiet_gap_summary visible until the gap is implemented, covered by parent policy, deferred for more sample, or explicitly rejected.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 55. `order_lifecycle_source_dimension_gap_rollup`

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
- evidence: `rollup_only_gap_count=21`, `unknown_source_dimensions=2`, `recommended_resolution_counts={'explicit_lifecycle_flow_source_only_blocker': 19, 'entry_label_not_applicable': 1, 'join_labels_before_bucket_decision': 1}`, `missing_dimension_key_counts={'entry': 8, 'exit': 34, 'holding': 36, 'submit': 20}`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: source_dimension_gap_summary rollup/actionable counts remain visible.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `terminal_existing_family_evidence`
- root_cause_closure_status: `-`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "terminal_existing_family_evidence", "previous_route": "source_dimension_rollup", "repeat_count": 6, "repeat_key": "order_lifecycle_source_dimension_gap_rollup", "repeat_signature": "sig:lifecycle_bucket_discovery_source_dimension_rollup|lifecycle_bucket_discovery_taxonomy_provenance|multi_stage|source_dimension_gap_rollup_evidence|lifecycle_bucket_discovery|unknown", "review_disposition": "keep_visible_by_design"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose checklist/workorder should keep source_dimension_gap_summary visible until actionable gaps are resolved or explicitly marked not applicable.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 56. `order_lifecycle_source_dimension_join_gap_enrichment`

- title: None
- decision: `attach_existing_family`
- decision_reason: source-dimension gap rollup is visibility evidence; actionable emit/backfill gaps are tracked by dedicated lifecycle_bucket_discovery implement_now orders
- source_report_type: `lifecycle_bucket_discovery_source_dimension_rollup`
- lifecycle_stage: `multi_stage`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `join_gap_enrichment`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_join_gap_enrichment`
- confidence: `postclose_discovery_source`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep LDM bucket label/join gaps visible as source-quality provenance before any bucket decision or runtime apply interpretation.
- evidence: `join_gap_candidate_count=1`, `join_gap_stage_counts={'scale_in': 1}`, `join_gap_bucket_type_counts={'ai_score_band': 1}`, `join_gap_recommended_resolution_counts={'join_labels_before_bucket_decision': 1}`, `join_gap_missing_dimension_key_counts={}`, `recommended_next_action=enrich_bucket_label_or_join_key_before_bucket_decision`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: source_dimension_gap_summary.join_gap_enrichment candidate_count is tracked until explicitly closed.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `terminal_existing_family_evidence`
- root_cause_closure_status: `-`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "terminal_existing_family_evidence", "previous_route": "join_gap_enrichment", "repeat_count": 6, "repeat_key": "order_lifecycle_source_dimension_join_gap_enrichment", "repeat_signature": "sig:lifecycle_bucket_discovery_source_dimension_rollup|lifecycle_bucket_discovery_taxonomy_provenance|multi_stage|source_dimension_join_gap_enrichment|lifecycle_bucket_discovery|unknown", "review_disposition": "keep_visible_by_design"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose checklist/workorder should keep source_dimension_gap_summary visible until actionable gaps are resolved or explicitly marked not applicable.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 57. `order_perf_daily_report_engine_singleton`

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
- evidence: `source_doc_hash=ffb2c2b9d6b8bf251d4f5665f1ea4ead0f680864428241fdcd6119d57f20722f`, `candidate_state=accepted`, `implementation_status=implemented`, `risk_tier=low`, `runtime_effect=false`, `strategy_effect=false`, `data_quality_effect=false`, `tuning_axis_effect=false`, `parity_contract=query result and rendered daily report exact match`
- parity_contract: query result and rendered daily report exact match
- next_postclose_metric: same report/output parity with lower runtime or CPU/IO overhead
- files_likely_touched: `src/engine/daily_report_service.py`
- acceptance_tests: `pytest src/tests/test_daily_report_service.py src/tests/test_daily_report.py`, `engine creation count regression test`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "performance_optimization_order", "repeat_count": 8, "repeat_key": "order_perf_daily_report_engine_singleton", "repeat_signature": "sig:codebase_performance_workorder|daily_report|ops_performance|||daily_report_sqlalchemy_engine_singleton", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose codebase performance source report must keep implementation_status=implemented and parity tests green.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 58. `order_rising_missed_classifier_prior_bridge`

- title: Attach cumulative ADM/LDM prior lookup to rising-missed classifier reports
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `rising_missed_classifier_prior`
- lifecycle_stage: `entry`
- target_subsystem: `rising_missed_entry_classifier`
- route: `existing_family`
- mapped_family: `rising_missed_classifier_prior_bridge`
- threshold_family: `rising_missed_classifier_prior_bridge`
- improvement_type: `-`
- confidence: `-`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: None
- evidence: `prior_count=37`, `positive_prior_count=1`, `source_quality_blocked_count=4`, `runtime_effect=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"actual_order_submitted": false, "allowed_runtime_apply": false, "broker_order_forbidden": true, "implementation_type": "rising_missed_classifier_prior_source_only", "requires_separate_runtime_apply_candidate": true, "root_cause_closure_status_hint": "implementation_done", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_rising_missed_classifier_prior_bridge", "repeat_signature": "sig:rising_missed_classifier_prior|rising_missed_entry_classifier|entry||rising_missed_classifier_prior_bridge|attach_cumulative_adm_ldm_prior_lookup_to_rising_missed_classifier_reports", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 59. `order_conversion_lane_key_lineage_active_arm_15f74aa27eef743d`

- title: Conversion lane blocker follow-up: key_lineage active_arm_15f74aa27eef743d
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
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=active_arm_15f74aa27eef743d`, `blocker_class=key_lineage`, `conversion_impact_rank=4`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 60. `order_conversion_lane_key_lineage_active_arm_1661ca30f0d594fd`

- title: Conversion lane blocker follow-up: key_lineage active_arm_1661ca30f0d594fd
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
- evidence: `conversion_candidate_id=active_arm_1661ca30f0d594fd`, `blocker_class=key_lineage`, `conversion_impact_rank=5`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_arm_1661ca30f0d594fd", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_1661ca30f0d594fd", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 61. `order_conversion_lane_key_lineage_active_arm_292c648e73675368`

- title: Conversion lane blocker follow-up: key_lineage active_arm_292c648e73675368
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
- evidence: `conversion_candidate_id=active_arm_292c648e73675368`, `blocker_class=key_lineage`, `conversion_impact_rank=6`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_conversion_lane_key_lineage_active_arm_292c648e73675368", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_292c648e73675368", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 62. `order_panic_sell_defense_lifecycle_transition_pack`

- title: panic sell defense lifecycle transition pack
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `threshold_cycle_calibration_source_bundle`
- lifecycle_stage: `holding_exit`
- target_subsystem: `panic_sell_defense`
- route: `existing_family`
- mapped_family: `panic_sell_defense`
- threshold_family: `panic_sell_defense`
- improvement_type: `runtime_transition_design`
- confidence: `consensus`
- priority: `6`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Use panic-sell simulation and post-sell rebound evidence to propose threshold/guard changes, then request explicit live-runtime approval without mutating exits automatically.
- evidence: `panic_state=RECOVERY_WATCH`, `panic_regime_mode=STABILIZING`, `stop_loss_exit_count=0`, `confirmation_eligible_exit_count=0`, `active_sim_probe_positions=3`, `post_sell_rebound_above_sell_10_20m_pct=0.0`, `microstructure_market_risk_state=NEUTRAL`, `microstructure_confirmed_risk_off_advisory=True`, `microstructure_portfolio_local_risk_off_only=False`, `market_breadth_followup_candidate=False`, `source_quality_blockers=[]`, `candidate_status={'panic_entry_freeze_guard': 'report_only_candidate', 'panic_stop_confirmation': 'hold_no_eligible_exit', 'panic_rebound_probe': 'hold_until_recovery_confirmed', 'panic_attribution_pack': 'active_report_only'}`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: panic_sell_defense should expose simulation EV, rollback guard, approval artifact status, market/breadth confirmation, and candidate-specific threshold recommendations before any runtime transition.
- files_likely_touched: `src/engine/panic_sell_defense_report.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/plan-korStockScanPerformanceOptimization.rebase.md`
- acceptance_tests: `pytest panic sell defense/report lifecycle tests`, `pytest src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py`
- implementation_status: `implemented_but_waiting_sample`
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "report_only_source_bundle", "implementation_type": "panic_lifecycle_report_only_source_bundle", "panic_regime_mode": "STABILIZING", "panic_state": "RECOVERY_WATCH", "runtime_effect": false, "source_metric_key": "panic_sell_defense", "source_quality_blockers": [], "source_report_type": "threshold_cycle_calibration_source_bundle"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_panic_sell_defense_lifecycle_transition_pack", "repeat_signature": "sig:threshold_cycle_calibration_source_bundle|panic_sell_defense|holding_exit|runtime_transition_design|panic_sell_defense|panic_sell_defense_lifecycle_transition_pack", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_but_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 63. `order_perf_monitor_snapshot_stream_tail`

- title: Monitor snapshot runtime streaming tail read
- decision: `attach_existing_family`
- decision_reason: report-only performance implementation is already present in code; keep the order as provenance and validate through regenerated reports/tests instead of re-implementing
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `monitor_snapshot`
- route: `performance_optimization_order`
- mapped_family: `ops_performance_report_only_implemented`
- threshold_family: `ops_performance_report_only_implemented`
- improvement_type: `-`
- confidence: `consensus`
- priority: `6`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: none_direct_ops_cpu_io_reduction_only
- evidence: `source_doc_hash=ffb2c2b9d6b8bf251d4f5665f1ea4ead0f680864428241fdcd6119d57f20722f`, `candidate_state=accepted`, `implementation_status=implemented`, `risk_tier=low`, `runtime_effect=false`, `strategy_effect=false`, `data_quality_effect=false`, `tuning_axis_effect=false`, `parity_contract=latest parsed snapshot payload and missing/malformed fallback behavior exact match`
- parity_contract: latest parsed snapshot payload and missing/malformed fallback behavior exact match
- next_postclose_metric: same report/output parity with lower runtime or CPU/IO overhead
- files_likely_touched: `src/engine/monitor_snapshot_runtime.py`
- acceptance_tests: `pytest src/tests/test_log_archive_service.py`, `last valid JSON line parity`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "performance_optimization_order", "repeat_count": 8, "repeat_key": "order_perf_monitor_snapshot_stream_tail", "repeat_signature": "sig:codebase_performance_workorder|monitor_snapshot|ops_performance|||monitor_snapshot_runtime_streaming_tail_read", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose codebase performance source report must keep implementation_status=implemented and parity tests green.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 64. `order_conversion_lane_key_lineage_active_arm_2c44a9b1dd392eb3`

- title: Conversion lane blocker follow-up: key_lineage active_arm_2c44a9b1dd392eb3
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
- evidence: `conversion_candidate_id=active_arm_2c44a9b1dd392eb3`, `blocker_class=key_lineage`, `conversion_impact_rank=7`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_arm_2c44a9b1dd392eb3", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_2c44a9b1dd392eb3", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 65. `order_perf_final_ensemble_records`

- title: Final ensemble scanner records conversion without iterrows
- decision: `attach_existing_family`
- decision_reason: report-only performance implementation is already present in code; keep the order as provenance and validate through regenerated reports/tests instead of re-implementing
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `final_ensemble_scanner`
- route: `performance_optimization_order`
- mapped_family: `ops_performance_report_only_implemented`
- threshold_family: `ops_performance_report_only_implemented`
- improvement_type: `-`
- confidence: `consensus`
- priority: `7`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: none_direct_ops_cpu_io_reduction_only
- evidence: `source_doc_hash=ffb2c2b9d6b8bf251d4f5665f1ea4ead0f680864428241fdcd6119d57f20722f`, `candidate_state=accepted`, `implementation_status=implemented`, `risk_tier=low`, `runtime_effect=false`, `strategy_effect=false`, `data_quality_effect=false`, `tuning_axis_effect=false`, `parity_contract=Code/Name record list, selection count, and diagnostics output exact match`
- parity_contract: Code/Name record list, selection count, and diagnostics output exact match
- next_postclose_metric: same report/output parity with lower runtime or CPU/IO overhead
- files_likely_touched: `src/scanners/final_ensemble_scanner.py`
- acceptance_tests: `pytest src/tests/test_swing_model_selection_funnel_repair.py`, `V2 CSV pick list parity`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "performance_optimization_order", "repeat_count": 8, "repeat_key": "order_perf_final_ensemble_records", "repeat_signature": "sig:codebase_performance_workorder|final_ensemble_scanner|ops_performance|||final_ensemble_scanner_records_conversion_without_iterrows", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose codebase performance source report must keep implementation_status=implemented and parity tests green.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 66. `order_conversion_lane_key_lineage_active_arm_2d256010e69684c1`

- title: Conversion lane blocker follow-up: key_lineage active_arm_2d256010e69684c1
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
- evidence: `conversion_candidate_id=active_arm_2d256010e69684c1`, `blocker_class=key_lineage`, `conversion_impact_rank=8`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_arm_2d256010e69684c1", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_2d256010e69684c1", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 67. `order_partial_only_표류_전용_timeout_report_only`

- title: partial-only 표류 전용 timeout report-only
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `holding_exit`
- route: `existing_family`
- mapped_family: `bad_entry_refined_canary`
- threshold_family: `bad_entry_refined_canary`
- improvement_type: `threshold_family_input`
- confidence: `solo`
- priority: `8`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve EV attribution and prepare bounded calibration input.
- evidence: `{'expected_effect': '1주 partial만 남긴 채 장시간 표류하는 케이스 조기 정리', 'risk': 'full fill 전 짧은 대기 케이스를 오분류할 수 있음', 'required_sample': 'partial-only 코호트 20건 이상', 'metric': 'partial-only held_sec 중앙값, timeout 이후 실현손익 분포', 'apply_stage': 'report_only_observation'}`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`
- implementation_status: `implemented_but_waiting_sample`
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "pattern_lab_analysis_workorder_source_only", "implementation_type": "pattern_lab_report_only_observation_contract", "implemented_scope": "bad_entry_refined_partial_only_timeout_report_contract", "runtime_effect": false, "sample_status": "contract_defined_waiting_sample", "source_contract": "bad_entry_refined_partial_only_timeout_report_contract_v1", "source_fields": ["expected_effect", "risk", "required_sample", "metric", "apply_stage"], "source_metric_snapshot": {"apply_stage": "report_only_observation", "expected_effect": "1주 partial만 남긴 채 장시간 표류하는 케이스 조기 정리", "mapped_family": "bad_entry_refined_canary", "metric": "partial-only held_sec 중앙값, timeout 이후 실현손익 분포", "required_sample": "partial-only 코호트 20건 이상", "risk": "full fill 전 짧은 대기 케이스를 오분류할 수 있음"}, "source_report_type": "scalping_pattern_lab_automation"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_partial_only_표류_전용_timeout_report_only", "repeat_signature": "sig:scalping_pattern_lab_automation|holding_exit||threshold_family_input||partial_only_표류_전용_timeout_report_only", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_but_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 68. `order_perf_sentinel_event_cache_incremental_review`

- title: Sentinel event cache incremental parse review
- decision: `attach_existing_family`
- decision_reason: report-only performance implementation is already present in code; keep the order as provenance and validate through regenerated reports/tests instead of re-implementing
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `sentinel_event_cache`
- route: `performance_optimization_order`
- mapped_family: `ops_performance_report_only_implemented`
- threshold_family: `ops_performance_report_only_implemented`
- improvement_type: `-`
- confidence: `consensus`
- priority: `8`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: none_direct_ops_cpu_io_reduction_only
- evidence: `source_doc_hash=ffb2c2b9d6b8bf251d4f5665f1ea4ead0f680864428241fdcd6119d57f20722f`, `candidate_state=accepted`, `implementation_status=implemented`, `risk_tier=medium`, `runtime_effect=false`, `strategy_effect=false`, `data_quality_effect=false`, `tuning_axis_effect=false`, `parity_contract=cached row ordering, malformed-line tolerance, source-quality fields, and empty/no-new-event fallback behavior exact match`
- parity_contract: cached row ordering, malformed-line tolerance, source-quality fields, and empty/no-new-event fallback behavior exact match
- next_postclose_metric: same report/output parity with lower runtime or CPU/IO overhead
- files_likely_touched: `src/engine/sentinel_event_cache.py`, `src/tests/test_sentinel_event_cache_parity.py`
- acceptance_tests: `pytest src/tests/test_buy_funnel_sentinel.py src/tests/test_holding_exit_sentinel.py`, `pytest src/tests/test_sentinel_event_cache_parity.py`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "performance_optimization_order", "repeat_count": 8, "repeat_key": "order_perf_sentinel_event_cache_incremental_review", "repeat_signature": "sig:codebase_performance_workorder|sentinel_event_cache|ops_performance|||sentinel_event_cache_incremental_parse_review", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose codebase performance source report must keep implementation_status=implemented and parity tests green.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 69. `order_conversion_lane_key_lineage_active_arm_3034ae45da8fefbc`

- title: Conversion lane blocker follow-up: key_lineage active_arm_3034ae45da8fefbc
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
- evidence: `conversion_candidate_id=active_arm_3034ae45da8fefbc`, `blocker_class=key_lineage`, `conversion_impact_rank=9`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_conversion_lane_key_lineage_active_arm_3034ae45da8fefbc", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_3034ae45da8fefbc", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 70. `order_split_entry_rebase_수량_정합성_report_only_감사`

- title: split-entry rebase 수량 정합성 report-only 감사
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `holding_exit`
- route: `existing_family`
- mapped_family: `bad_entry_refined_canary`
- threshold_family: `bad_entry_refined_canary`
- improvement_type: `threshold_family_input`
- confidence: `solo`
- priority: `9`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve EV attribution and prepare bounded calibration input.
- evidence: `{'expected_effect': 'rebase quantity 이상(cum_gt_requested / same_ts_multi_rebase) 케이스를 분리해 실제 경제 손실과 이벤트 복원 오류를 혼합하지 않게 함', 'risk': 'false-positive 제거 전 손절 임계값 튜닝 시 결론 왜곡 가능', 'required_sample': 'rebase_integrity_flag 케이스 20건 이상', 'metric': 'cum_filled_qty > requested_qty 비율, same_ts_multi_rebase_count 분포', 'apply_stage': 'report_only_observation'}`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`
- implementation_status: `implemented_but_waiting_sample`
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "pattern_lab_analysis_workorder_source_only", "implementation_type": "pattern_lab_report_only_observation_contract", "implemented_scope": "bad_entry_refined_rebase_integrity_report_contract", "runtime_effect": false, "sample_status": "contract_defined_waiting_sample", "source_contract": "bad_entry_refined_rebase_integrity_report_contract_v1", "source_fields": ["expected_effect", "risk", "required_sample", "metric", "apply_stage"], "source_metric_snapshot": {"apply_stage": "report_only_observation", "expected_effect": "rebase quantity 이상(cum_gt_requested / same_ts_multi_rebase) 케이스를 분리해 실제 경제 손실과 이벤트 복원 오류를 혼합하지 않게 함", "mapped_family": "bad_entry_refined_canary", "metric": "cum_filled_qty > requested_qty 비율, same_ts_multi_rebase_count 분포", "required_sample": "rebase_integrity_flag 케이스 20건 이상", "risk": "false-positive 제거 전 손절 임계값 튜닝 시 결론 왜곡 가능"}, "source_report_type": "scalping_pattern_lab_automation"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_split_entry_rebase_수량_정합성_report_only_감사", "repeat_signature": "sig:scalping_pattern_lab_automation|holding_exit||threshold_family_input||split_entry_rebase_수량_정합성_report_only_감사", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_but_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 71. `order_conversion_lane_key_lineage_active_arm_368b41a18c7e3a5e`

- title: Conversion lane blocker follow-up: key_lineage active_arm_368b41a18c7e3a5e
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
- evidence: `conversion_candidate_id=active_arm_368b41a18c7e3a5e`, `blocker_class=key_lineage`, `conversion_impact_rank=10`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_conversion_lane_key_lineage_active_arm_368b41a18c7e3a5e", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_368b41a18c7e3a5e", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 72. `order_pattern_lab_ai_review_lifecycle_bucket_discovery_automation_handoff_gap`

- title: Pattern Lab AI review follow-up: lifecycle_bucket_discovery_automation_handoff_gap
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
- evidence: `review_id=lifecycle_bucket_discovery_automation_handoff_gap`, `domain=scalping`, `final_state=automation_handoff_gap`, `final_decision=block_runtime_use`, `auditor_pass=False`, `explicit_gap_type=automation_handoff_gap`, `source_paths=['/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-07-29.json', '/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-07-29.json', '/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-07-29.json', '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-29.json']`
- parity_contract: -
- next_postclose_metric: pattern_lab_ai_review.lifecycle_bucket_discovery_automation_handoff_gap
- files_likely_touched: `src/engine/pattern_lab_ai_review.py`, `src/engine/pattern_lab_currentness_audit.py`, `analysis/gemini_scalping_pattern_lab`, `analysis/claude_scalping_pattern_lab`, `analysis/deepseek_swing_pattern_lab`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_ai_review.py src/tests/test_pattern_lab_currentness_audit.py`
- implementation_status: `terminal_existing_family_evidence`
- root_cause_closure_status: `-`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Keep as source-quality blocker evidence until pattern_lab_currentness_audit handoff orders close and the regenerated AI review parses sufficient context.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 73. `order_동일_종목_split_entry_soft_stop_재진입_cooldown_report_only`

- title: 동일 종목 split-entry soft-stop 재진입 cooldown report-only
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `holding_exit`
- route: `existing_family`
- mapped_family: `soft_stop_whipsaw_confirmation`
- threshold_family: `soft_stop_whipsaw_confirmation`
- improvement_type: `threshold_family_input`
- confidence: `solo`
- priority: `10`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve EV attribution and prepare bounded calibration input.
- evidence: `{'expected_effect': '같은 날 동일 종목 반복 손절 누수 차단', 'risk': 'cooldown 중 missed upside 발생 가능 — 차단 건수와 missed upside를 함께 추적해야 함', 'required_sample': 'same_symbol_repeat_flag 케이스 10건 이상', 'metric': 'same-symbol repeat soft stop 건수, cooldown 차단 후 10분 missed upside', 'apply_stage': 'report_only_observation'}`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`
- implementation_status: `implemented_but_waiting_sample`
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "pattern_lab_analysis_workorder_source_only", "implementation_type": "pattern_lab_report_only_observation_contract", "implemented_scope": "soft_stop_whipsaw_same_symbol_reentry_report_contract", "runtime_effect": false, "sample_status": "contract_defined_waiting_sample", "source_contract": "soft_stop_whipsaw_same_symbol_reentry_report_contract_v1", "source_fields": ["expected_effect", "risk", "required_sample", "metric", "apply_stage"], "source_metric_snapshot": {"apply_stage": "report_only_observation", "expected_effect": "같은 날 동일 종목 반복 손절 누수 차단", "mapped_family": "soft_stop_whipsaw_confirmation", "metric": "same-symbol repeat soft stop 건수, cooldown 차단 후 10분 missed upside", "required_sample": "same_symbol_repeat_flag 케이스 10건 이상", "risk": "cooldown 중 missed upside 발생 가능 — 차단 건수와 missed upside를 함께 추적해야 함"}, "source_report_type": "scalping_pattern_lab_automation"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_동일_종목_split_entry_soft_stop_재진입_cooldown_report_only", "repeat_signature": "sig:scalping_pattern_lab_automation|holding_exit||threshold_family_input||동일_종목_split_entry_soft_stop_재진입_cooldown_report_only", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_but_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 74. `order_conversion_lane_key_lineage_active_arm_400bb07e38eb1ab2`

- title: Conversion lane blocker follow-up: key_lineage active_arm_400bb07e38eb1ab2
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
- evidence: `conversion_candidate_id=active_arm_400bb07e38eb1ab2`, `blocker_class=key_lineage`, `conversion_impact_rank=11`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_arm_400bb07e38eb1ab2", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_400bb07e38eb1ab2", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 75. `order_conversion_lane_key_lineage_active_arm_400f801d872d0781`

- title: Conversion lane blocker follow-up: key_lineage active_arm_400f801d872d0781
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
- evidence: `conversion_candidate_id=active_arm_400f801d872d0781`, `blocker_class=key_lineage`, `conversion_impact_rank=12`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 76. `order_conversion_lane_key_lineage_active_arm_431cb98e1d4adfce`

- title: Conversion lane blocker follow-up: key_lineage active_arm_431cb98e1d4adfce
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
- evidence: `conversion_candidate_id=active_arm_431cb98e1d4adfce`, `blocker_class=key_lineage`, `conversion_impact_rank=13`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_arm_431cb98e1d4adfce", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_431cb98e1d4adfce", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 77. `order_conversion_lane_key_lineage_active_arm_449bf7156fc91f04`

- title: Conversion lane blocker follow-up: key_lineage active_arm_449bf7156fc91f04
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
- evidence: `conversion_candidate_id=active_arm_449bf7156fc91f04`, `blocker_class=key_lineage`, `conversion_impact_rank=14`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_conversion_lane_key_lineage_active_arm_449bf7156fc91f04", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_449bf7156fc91f04", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 78. `order_conversion_lane_key_lineage_active_arm_50c137ab85107620`

- title: Conversion lane blocker follow-up: key_lineage active_arm_50c137ab85107620
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
- evidence: `conversion_candidate_id=active_arm_50c137ab85107620`, `blocker_class=key_lineage`, `conversion_impact_rank=15`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_conversion_lane_key_lineage_active_arm_50c137ab85107620", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_50c137ab85107620", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 79. `order_conversion_lane_key_lineage_active_arm_518e85a70ac730e3`

- title: Conversion lane blocker follow-up: key_lineage active_arm_518e85a70ac730e3
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
- evidence: `conversion_candidate_id=active_arm_518e85a70ac730e3`, `blocker_class=key_lineage`, `conversion_impact_rank=16`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_arm_518e85a70ac730e3", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_518e85a70ac730e3", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 80. `order_conversion_lane_key_lineage_active_arm_52e8c1f2d0e05882`

- title: Conversion lane blocker follow-up: key_lineage active_arm_52e8c1f2d0e05882
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
- evidence: `conversion_candidate_id=active_arm_52e8c1f2d0e05882`, `blocker_class=key_lineage`, `conversion_impact_rank=17`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_arm_52e8c1f2d0e05882", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_52e8c1f2d0e05882", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 81. `order_conversion_lane_key_lineage_active_arm_57c8b15599062480`

- title: Conversion lane blocker follow-up: key_lineage active_arm_57c8b15599062480
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
- evidence: `conversion_candidate_id=active_arm_57c8b15599062480`, `blocker_class=key_lineage`, `conversion_impact_rank=18`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_conversion_lane_key_lineage_active_arm_57c8b15599062480", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_57c8b15599062480", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 82. `order_conversion_lane_key_lineage_active_arm_594203d8ae056b29`

- title: Conversion lane blocker follow-up: key_lineage active_arm_594203d8ae056b29
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
- evidence: `conversion_candidate_id=active_arm_594203d8ae056b29`, `blocker_class=key_lineage`, `conversion_impact_rank=19`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 8, "repeat_key": "order_conversion_lane_key_lineage_active_arm_594203d8ae056b29", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_594203d8ae056b29", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 83. `order_conversion_lane_key_lineage_active_arm_5ed5448f4e3ccb60`

- title: Conversion lane blocker follow-up: key_lineage active_arm_5ed5448f4e3ccb60
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
- evidence: `conversion_candidate_id=active_arm_5ed5448f4e3ccb60`, `blocker_class=key_lineage`, `conversion_impact_rank=20`, `next_repair_action=swing_active_arm_preopen_missing`, `acceptance_test=same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "key_lineage", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_conversion_lane_key_lineage_active_arm_5ed5448f4e3ccb60", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_key_lineage_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_key_lineage_active_arm_5ed5448f4e3ccb60", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

## Non-Selected Source Orders

아래 항목은 source order로 분류됐지만 selected implementation order에는 포함되지 않았다. 재작업 지시 시 `decision`, `decision_reason`, `runtime_effect`를 먼저 재판정한다.

### N1. `order_no_acute_observability_alert`

- title: No acute observability alert
- decision: `design_family_candidate`
- decision_reason: pattern lab can only propose source-only family design input; LDM/discovery/runtime bridge contracts must close before any auto_bounded_live consideration
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `scalping_logic`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_design_family_candidate`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "design_family_candidate", "previous_implementation_status": "terminal_design_family_candidate", "previous_route": "auto_family_candidate", "repeat_count": 6, "repeat_key": "order_no_acute_observability_alert", "repeat_signature": "sig:scalping_pattern_lab_automation|scalping_logic||no_acute_observability_alert||no_acute_observability_alert", "review_disposition": "review_required"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N2. `order_liquidity_gate_miss_ev_recovery`

- title: liquidity gate miss EV recovery
- decision: `design_family_candidate`
- decision_reason: pattern lab can only propose source-only family design input; LDM/discovery/runtime bridge contracts must close before any auto_bounded_live consideration
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `entry_filter_quality`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_design_family_candidate`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "design_family_candidate", "previous_implementation_status": "terminal_design_family_candidate", "previous_route": "auto_family_candidate", "repeat_count": 6, "repeat_key": "order_liquidity_gate_miss_ev_recovery", "repeat_signature": "sig:scalping_pattern_lab_automation|entry_filter_quality||liquidity_gate_miss_ev_recovery||liquidity_gate_miss_ev_recovery", "review_disposition": "review_required"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N3. `order_overbought_gate_miss_ev_recovery`

- title: overbought gate miss EV recovery
- decision: `design_family_candidate`
- decision_reason: pattern lab can only propose source-only family design input; LDM/discovery/runtime bridge contracts must close before any auto_bounded_live consideration
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `entry_filter_quality`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_design_family_candidate`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "design_family_candidate", "previous_implementation_status": "terminal_design_family_candidate", "previous_route": "auto_family_candidate", "repeat_count": 6, "repeat_key": "order_overbought_gate_miss_ev_recovery", "repeat_signature": "sig:scalping_pattern_lab_automation|entry_filter_quality||overbought_gate_miss_ev_recovery||overbought_gate_miss_ev_recovery", "review_disposition": "review_required"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N4. `order_scalp_entry_adm_daily_tuning_coverage`

- title: scalp entry ADM daily tuning coverage
- decision: `defer_evidence`
- decision_reason: Entry ADM warning is waiting on clean sample/runtime observation, not a code implementation gap
- source_report_type: `threshold_cycle_ev`
- lifecycle_stage: `entry`
- target_subsystem: `entry_funnel`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_deferred_evidence`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "defer_evidence", "previous_implementation_status": "terminal_deferred_evidence", "previous_route": "instrumentation_order", "repeat_count": 8, "repeat_key": "order_scalp_entry_adm_daily_tuning_coverage", "repeat_signature": "sig:threshold_cycle_ev|entry_funnel|entry|instrumentation_report_provenance|scalp_entry_action_decision_matrix_advisory|scalp_entry_adm_daily_tuning_coverage", "review_disposition": "review_required"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/sniper_state_handlers.py`, `src/engine/scalp_entry_adm_runtime.py`, `src/engine/threshold_cycle_ev_report.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_scalp_entry_action_decision_matrix.py src/tests/test_build_code_improvement_workorder.py`, `runtime_effect remains false and broker submit safety guards remain owner`

### N5. `order_perf_kiwoom_orders_http_session_review`

- title: Kiwoom orders HTTP session reuse manual review
- decision: `defer_evidence`
- decision_reason: broker request lifecycle may change; requires manual review before implementation
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `broker_transport`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_deferred_evidence`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "defer_evidence", "previous_implementation_status": "terminal_deferred_evidence", "previous_route": "performance_optimization_order", "repeat_count": 8, "repeat_key": "order_perf_kiwoom_orders_http_session_review", "repeat_signature": "sig:codebase_performance_workorder|broker_transport|ops_performance|||kiwoom_orders_http_session_reuse_manual_review", "review_disposition": "review_required"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/kiwoom_orders.py`
- acceptance_tests: `pytest src/tests/test_kiwoom_orders.py src/tests/test_sniper_scale_in.py`

### N6. `order_perf_config_cache_scope_review`

- title: Config cache scope review
- decision: `defer_evidence`
- decision_reason: runtime config reload semantics are not yet bounded
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `config_loading`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_deferred_evidence`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "defer_evidence", "previous_implementation_status": "terminal_deferred_evidence", "previous_route": "performance_optimization_order", "repeat_count": 8, "repeat_key": "order_perf_config_cache_scope_review", "repeat_signature": "sig:codebase_performance_workorder|config_loading|ops_performance|||config_cache_scope_review", "review_disposition": "review_required"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/utils/constants.py`, `src/utils/kiwoom_utils.py`
- acceptance_tests: `pytest config/import smoke tests`

### N7. `order_partial_fallback_확대_직후_즉시_재평가_report_only`

- title: partial → fallback 확대 직후 즉시 재평가 report-only
- decision: `reject`
- decision_reason: fallback revival or shadow reintroduction conflicts with current Plan Rebase policy
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `holding_exit`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_rejected`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N8. `order_perf_kiwoom_ws_tick_parse_fastpath`

- title: Kiwoom websocket tick parsing fast path
- decision: `reject`
- decision_reason: quote/data-quality semantics can change; requires separate data-quality approval owner
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `quote_data_quality`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_rejected`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/kiwoom_websocket.py`
- acceptance_tests: `pytest websocket parsing/data-quality tests`

### N9. `order_perf_raw_event_suppression_out_of_scope`

- title: Raw pipeline event suppression out of scope
- decision: `reject`
- decision_reason: raw suppression is governed by pipeline event V2 suppress guard
- source_report_type: `codebase_performance_workorder`
- lifecycle_stage: `ops_performance`
- target_subsystem: `pipeline_event_storage`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_rejected`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/utils/pipeline_event_logger.py`
- acceptance_tests: `pytest pipeline event verbosity tests`

## 자동화체인 재투입

- 구현 결과는 `2026-07-30` 이후 postclose `threshold_cycle`, `scalping_pattern_lab_automation`, `threshold_cycle_ev`가 자동으로 다시 읽는다.
- 구현자가 수동으로 threshold 값을 바꾸는 것이 아니라, source/report/provenance를 닫아 다음 calibration이 판단하게 한다.
- 다음 Codex 세션 입력 문구: `none_for_bucket_discovery_classification`

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
