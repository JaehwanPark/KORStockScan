# Code Improvement Workorder - 2026-05-28

## 목적

- Postclose 자동화가 생성한 `code_improvement_order`를 Codex 실행용 작업지시서로 변환한다.
- 입력은 scalping pattern lab automation, swing lifecycle improvement automation, swing pattern lab automation을 함께 포함할 수 있다.
- 이 문서는 repo/runtime을 직접 변경하지 않는다. 사용자가 이 문서를 Codex 세션에 넣고 구현을 요청하는 지점만 사람 개입으로 남긴다.
- 구현 후 자동화체인 재투입은 다음 postclose report, threshold calibration, daily EV report가 담당한다.

## Source

- pattern_lab_automation: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-28.json`
- swing_improvement_automation: `/home/ubuntu/KORStockScan/data/report/swing_improvement_automation/swing_improvement_automation_2026-05-28.json`
- swing_pattern_lab_automation: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-05-28.json`
- swing_strategy_discovery_ev: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-05-28.json`
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-05-28.json`
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-05-28.json`
- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-28.json`
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-28.json`
- threshold_cycle_calibration: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_calibration/threshold_cycle_calibration_2026-05-28_postclose.json`
- pipeline_event_verbosity: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-05-28.json`
- observation_source_quality_audit: `/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-05-28.json`
- codebase_performance_workorder: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-05-28.json`
- pattern_lab_currentness_audit: `/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-05-28.json`
- pattern_lab_ai_review: `/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-05-28.json`
- producer_gap_discovery: `/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-05-28.json`
- stage_hook_workorder_discovery: `/home/ubuntu/KORStockScan/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_2026-05-28.json`
- stage_hook_runtime_scaffold: `/home/ubuntu/KORStockScan/data/report/stage_hook_runtime_scaffold/stage_hook_runtime_scaffold_2026-05-28.json`
- buy_funnel_sentinel: `/home/ubuntu/KORStockScan/data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-05-28.json`
- generated_at: `2026-06-01T13:19:31+09:00`
- generation_id: `2026-05-28-2dbbd840cc1c`
- source_hash: `2dbbd840cc1c17a4b958ca92a920696b0985749236a934d28ce426ad34f4de30`

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
- previous_generation_id: `2026-05-28-ef93a194bd67`
- previous_source_hash: `ef93a194bd675747d991a6e1aa8785a1342f010ba50ed21100049eaabc83537c`
- new_order_ids: `['order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_04a0c69a', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_053f28f4', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_073abebc', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_0edb5f2a', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_0f872dff', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_16a37be5', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_176ca4a5', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_1f827df7', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32944f7b', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_37fe95f3', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_400a4a2f', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_49ffaa8f', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_5692617f', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_5ed2e634', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_62ed3bc6', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_6582cca5', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_68382cb8', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_6b9f32f4', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_6e894a29', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_70579ca1', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_716f10d2', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_74efe6b6', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_784d400b', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_856e80ad', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_8a4fcc4f', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_90c6ece7', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_9b00315a', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_9c6ccf88', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_a50d7d03', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_a73a8569', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_a924bc1f', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_acec2360', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_ad3a375f', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b2730915', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c0bae630', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_d6fcbc90', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_d7034dce', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_dd41d703', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_e8130b27', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_f13463b9', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_f2bb4423', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_f4fedf98', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_8fbb74dd', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_98147c80', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_m_d40bb847', 'order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_m_e2e1e58f', 'order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_diagnostic', 'order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_insurance_보험_생명보험_', 'order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_computer_programming_syste', 'order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_insurance_보험_생명보험_diagnost', 'order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_of_other_chemi', 'order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_other_financial_intermedia', 'order_swing_ldm_selection_discovery_arm_attribution_pullback_limit_entry_risk_capped_mae_stop_time_stop_manufacture_of_basic_chemica', 'order_swing_ldm_selection_discovery_arm_attribution_pullback_limit_entry_risk_capped_mae_stop_time_stop_sea_and_coastal_water_transp']`
- removed_order_ids: `['order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manufacture_of_par', 'order_swing_ldm_selection_discovery_arm_attribution_pullback_limit_entry_risk_capped_mae_stop_time_stop_manufacture_of_electronic_co']`
- decision_changed_order_ids: `[]`

## Summary

- source_order_count: `176`
- scalping_source_order_count: `0`
- swing_source_order_count: `8`
- swing_entry_bottleneck_primary: `SWING_ENTRY_BOTTLENECK_OBSERVE`
- swing_entry_bottleneck_selected: `False`
- swing_lab_source_order_count: `3`
- swing_strategy_discovery_source_order_count: `2`
- swing_lifecycle_matrix_source_order_count: `17`
- swing_lifecycle_bucket_discovery_source_order_count: `0`
- pattern_lab_currentness_source_order_count: `0`
- pattern_lab_ai_review_source_order_count: `1`
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
- selected_order_count: `148`
- non_selected_order_count: `28`
- source_decision_counts: `{'implement_now': 47, 'attach_existing_family': 119, 'design_family_candidate': 3, 'defer_evidence': 5, 'reject': 2}`
- selected_decision_counts: `{'implement_now': 47, 'attach_existing_family': 101}`
- selected_route_counts: `{'auto_patch_required': 47, 'existing_family': 101}`
- selected_implement_now_route_count: `0`
- selected_runtime_effect_false_count: `148`
- selected_unimplemented_runtime_effect_false_count: `47`
- selected_unimplemented_route_counts: `{'auto_patch_required': 47}`
- non_selected_decision_counts: `{'attach_existing_family': 18, 'design_family_candidate': 3, 'defer_evidence': 5, 'reject': 2}`
- gemini_fresh: `False`
- claude_fresh: `False`
- swing_lifecycle_audit_available: `True`
- swing_pattern_lab_automation_available: `True`
- swing_pattern_lab_fresh: `True`
- pattern_lab_currentness_status: `pass`
- pattern_lab_currentness_fail_count: `0`
- pattern_lab_ai_review_status: `warning`
- pattern_lab_ai_review_workorder_count: `1`
- swing_threshold_ai_status: `parsed_empty`
- daily_ev_available: `True`

### Duplicate Order Collisions
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

### 1. `order_lifecycle_bucket_discovery_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_f6cddc94`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `bucket_classifier_hook_or_taxonomy_gap`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_:db6350b072`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_60_62_source_scalp_entry_action_decision_snapshot_stale_stale_block_liquidity_liquid|submit=submit:missing|holding=holding:missing|scale_in=scale_in:none|exit=exit:missing`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_60_62_source_scalp_entry_action_decision_snapshot_stale_stale_block_liquidity_liquid|submit=submit:missing|holding=holding:missing|scale_in=scale_in:none|exit=exit:missing`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=composite_bucket_should_roll_up_to_parent_plus_dimensions`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=hybrid`, `source_bucket_kind=source_quality_gap`, `stage=lifecycle_flow`, `classification_state=runtime_blocked_contract_gap`, `bucket_relation=existing_bucket_refinement`, `recommended_action=keep_collecting`, `recommended_resolution=instrumentation_gap`, `source_dimension_gap=`, `missing_dimension_keys=[]`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 2. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_04a0c69a`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked:1b04ee0959`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_over|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_good_exit_profit_profit_lt_neg0`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_over|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_good_exit_profit_profit_lt_neg0`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-2.2929`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 3. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_053f28f4`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked:e1eb98b647`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquidity_liquidity_unknown_overbou|submit=submit:missing|holding=holding:missing|scale_in=scale_in:none|exit=exit:missing`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquidity_liquidity_unknown_overbou|submit=submit:missing|holding=holding:missing|scale_in=scale_in:none|exit=exit:missing`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=keep_collecting`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 4. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_073abebc`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocke:70a13413bc`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidity_liquidity_unknown_overboug|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_holding_action_not_applicable_at_start_profit_profit_unk|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_exit_profit_profit_lt_neg0`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidity_liquidity_unknown_overboug|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_holding_action_not_applicable_at_start_profit_profit_unk|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_exit_profit_profit_lt_neg0`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-1.699`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 5. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_0edb5f2a`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocke:5e3234d62f`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_ok_or_unflagged_quote_age_q|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_exit_profit_profit_lt_neg0`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_ok_or_unflagged_quote_age_q|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_exit_profit_profit_lt_neg0`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-1.624`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 6. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_0f872dff`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked:2509d49c55`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquidity_liquidity_unknown_overbou|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_neutral_profit_profit_lt_neg070`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquidity_liquidity_unknown_overbou|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_neutral_profit_profit_lt_neg070`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-1.0921`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 7. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_16a37be5`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocke:7d7179466a`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidity_liquidity_unknown_overboug|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_missed_upside_profit_profit_lt_`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidity_liquidity_unknown_overboug|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_missed_upside_profit_profit_lt_`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-1.0056`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 8. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_176ca4a5`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked:ecd3562fd2`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquidity_liquidity_unknown_overbou|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_missed_upside_profit_pro`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquidity_liquidity_unknown_overbou|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_missed_upside_profit_pro`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=lifecycle_flow_sim_probe_policy`, `stage=lifecycle_flow`, `classification_state=lifecycle_flow_sim_probe_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=relax_or_recover`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=0.6803`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 9. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_1f827df7`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocke:5acc522ffb`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_neutral_profit_profit_ne`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_neutral_profit_profit_ne`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=lifecycle_flow_sim_probe_policy`, `stage=lifecycle_flow`, `classification_state=lifecycle_flow_sim_probe_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=relax_or_recover`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=0.4617`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 10. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32944f7b`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_blocked_ai_score_stale_fresh_liquidity_liq
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_blocked_ai_score_stale_fresh_liquidity_liq`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_blocke:49917f4fb3`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_66_69_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_holding_action_not_applicable_at_start_profit_profit_unk|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_missed_upside_profit_pro`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_66_69_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_holding_action_not_applicable_at_start_profit_profit_unk|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_missed_upside_profit_pro`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=lifecycle_flow_sim_probe_policy`, `stage=lifecycle_flow`, `classification_state=lifecycle_flow_sim_probe_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=hold_no_edge`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=0.0765`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 11. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_37fe95f3`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_en:dc8030505a`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_70p_source_scalp_entry_action_decision_snapshot_stale_stale_watch_liquidity_liquidit|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_good_exit_profit_profit_`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_70p_source_scalp_entry_action_decision_snapshot_stale_stale_watch_liquidity_liquidit|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_good_exit_profit_profit_`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-1.3142`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 12. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_400a4a2f`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked:d5b205c74b`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_over|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_holding_action_not_applicable_at_start_profit_profit_unk|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutral_profit_profit_lt_neg070`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_over|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_holding_action_not_applicable_at_start_profit_profit_unk|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutral_profit_profit_lt_neg070`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-1.198`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 13. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_49ffaa8f`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocke:6ef66e7bb5`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidity_liquidity_unknown_overboug|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_holding_action_not_applicable_at_start_profit_profit_unk|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_missed_upside_profit_pro`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidity_liquidity_unknown_overboug|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_holding_action_not_applicable_at_start_profit_profit_unk|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_missed_upside_profit_pro`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=lifecycle_flow_sim_probe_policy`, `stage=lifecycle_flow`, `classification_state=lifecycle_flow_sim_probe_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=relax_or_recover`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=0.4138`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 14. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_5692617f`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocke:3dcd9c6c15`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_good_exit_profit_profit_`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_good_exit_profit_profit_`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=lifecycle_flow_sim_probe_policy`, `stage=lifecycle_flow`, `classification_state=lifecycle_flow_sim_probe_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=hold_no_edge`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=0.1575`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 15. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_5ed2e634`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liqui
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liqui`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_:25fc6cf713`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_overb|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_missed_upside_profit_pro`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_overb|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_missed_upside_profit_pro`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=lifecycle_flow_sim_probe_policy`, `stage=lifecycle_flow`, `classification_state=lifecycle_flow_sim_probe_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=relax_or_recover`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=0.7773`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 16. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_62ed3bc6`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocke:f30f50f34b`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_missed_upside_profit_pro`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_missed_upside_profit_pro`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=lifecycle_flow_sim_probe_policy`, `stage=lifecycle_flow`, `classification_state=lifecycle_flow_sim_probe_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=relax_or_recover`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=0.5166`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 17. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_6582cca5`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai_confirmed_stale_fresh_liquidity_liquidi
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai_confirmed_stale_fresh_liquidity_liquidi`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai_con:324c038145`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_60_62_source_ai_confirmed_stale_fresh_liquidity_liquidity_unknown_overbought_overbou|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_exit_profit_profit_lt_neg0`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_60_62_source_ai_confirmed_stale_fresh_liquidity_liquidity_unknown_overbought_overbou|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_exit_profit_profit_lt_neg0`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-1.0715`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 18. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_68382cb8`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked:e095eb877a`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquidity_liquidity_unknown_overbou|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_holding_action_not_applicable_at_start_profit_profit_unk|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_good_exit_profit_profit_`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquidity_liquidity_unknown_overbou|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_holding_action_not_applicable_at_start_profit_profit_unk|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_good_exit_profit_profit_`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-0.7482`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 19. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_6b9f32f4`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocke:7c141e2d0f`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_holding_action_not_applicable_at_start_profit_profit_unk|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_good_exit_profit_profit_`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_holding_action_not_applicable_at_start_profit_profit_unk|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_good_exit_profit_profit_`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=lifecycle_flow_sim_probe_policy`, `stage=lifecycle_flow`, `classification_state=lifecycle_flow_sim_probe_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=hold_no_edge`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=0.2802`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 20. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_6e894a29`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocke:21e6eeef32`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_good_exit_profit_profit_lt_neg0`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_good_exit_profit_profit_lt_neg0`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-2.1094`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 21. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_70579ca1`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocke:0cddf0ad3b`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_neutral_profit_profit_po`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_neutral_profit_profit_po`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=lifecycle_flow_sim_probe_policy`, `stage=lifecycle_flow`, `classification_state=lifecycle_flow_sim_probe_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=relax_or_recover`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=0.55`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 22. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_716f10d2`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked:581594fe20`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquidity_liquidity_unknown_overbou|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutral_profit_profit_lt_neg070`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquidity_liquidity_unknown_overbou|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutral_profit_profit_lt_neg070`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-0.8716`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 23. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_74efe6b6`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_stale_block_liquidity
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_stale_block_liquidity`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_:51a586b660`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_70p_source_blocked_ai_score_stale_stale_block_liquidity_liquidity_unknown_overbought|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutral_profit_profit_lt_neg070`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_70p_source_blocked_ai_score_stale_stale_block_liquidity_liquidity_unknown_overbought|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutral_profit_profit_lt_neg070`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-1.0869`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 24. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_784d400b`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocke:caa1101fb1`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_missed_upside_profit_profit_lt_`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_missed_upside_profit_profit_lt_`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-2.3308`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 25. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_856e80ad`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked:9d19f3363f`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquidity_liquidity_unknown_overbou|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_exit_profit_profit_lt_neg0`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquidity_liquidity_unknown_overbou|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_exit_profit_profit_lt_neg0`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-2.0949`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 26. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_8a4fcc4f`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liqui
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liqui`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_:3e9dbea451`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_overb|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_buy_profit_profit_unknown_held_held_not_applicable_at_st|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutral_profit_profit_lt_neg070`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_overb|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_buy_profit_profit_unknown_held_held_not_applicable_at_st|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutral_profit_profit_lt_neg070`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-0.9891`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 27. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_90c6ece7`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocke:bec63d8df9`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_holding_action_not_applicable_at_start_profit_profit_unk|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_good_exit_profit_profit_`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_holding_action_not_applicable_at_start_profit_profit_unk|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_good_exit_profit_profit_`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=lifecycle_flow_sim_probe_policy`, `stage=lifecycle_flow`, `classification_state=lifecycle_flow_sim_probe_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=relax_or_recover`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=0.8064`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 28. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_9b00315a`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocke:71150c1c29`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_holding_action_not_applicable_at_start_profit_profit_unk|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_missed_upside_profit_pro`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_holding_action_not_applicable_at_start_profit_profit_unk|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_missed_upside_profit_pro`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=lifecycle_flow_sim_probe_policy`, `stage=lifecycle_flow`, `classification_state=lifecycle_flow_sim_probe_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=relax_or_recover`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=0.4179`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 29. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_9c6ccf88`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocke:99ac133bdb`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutral_profit_profit_lt_neg070`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutral_profit_profit_lt_neg070`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-1.4306`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 30. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_a50d7d03`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked:47a3e54a94`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquidity_liquidity_unknown_overbou|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_ok_or_unflagged_quote_age_q|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_good_exit_profit_profit_lt_neg0`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquidity_liquidity_unknown_overbou|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_ok_or_unflagged_quote_age_q|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_good_exit_profit_profit_lt_neg0`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-4.9771`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 31. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_a73a8569`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocke:696a47391c`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_holding_action_not_applicable_at_start_profit_profit_unk|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_missed_upside_profit_profit_lt_`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_holding_action_not_applicable_at_start_profit_profit_unk|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_missed_upside_profit_profit_lt_`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-0.5129`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 32. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_a924bc1f`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liqui
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liqui`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_:6c8a0f89e4`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_overb|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_good_exit_profit_profit_lt_neg0`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_overb|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_good_exit_profit_profit_lt_neg0`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-1.9892`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 33. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_acec2360`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocke:376060c7e0`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutral_profit_profit_lt_neg070`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutral_profit_profit_lt_neg070`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-1.3347`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 34. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_ad3a375f`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocke:5be1c380a4`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidity_liquidity_unknown_overboug|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_holding_action_not_applicable_at_start_profit_profit_unk|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_good_exit_profit_profit_`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidity_liquidity_unknown_overboug|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_holding_action_not_applicable_at_start_profit_profit_unk|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_good_exit_profit_profit_`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-0.4625`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 35. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b2730915`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocke:cf4f6c2616`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidity_liquidity_unknown_overboug|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_holding_action_not_applicable_at_start_profit_profit_unk|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_missed_upside_profit_profit_lt_`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidity_liquidity_unknown_overboug|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_holding_action_not_applicable_at_start_profit_profit_unk|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_missed_upside_profit_profit_lt_`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-0.8489`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 36. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c0bae630`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_e:de8d2134e1`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_stale_block_liquidity_liquidi|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutral_profit_profit_lt_neg070`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_stale_block_liquidity_liquidi|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutral_profit_profit_lt_neg070`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-0.886`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 37. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_d6fcbc90`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocke:262d7881f2`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_exit_profit_profit_lt_neg0`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_exit_profit_profit_lt_neg0`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-1.3163`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 38. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_d7034dce`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liqui
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liqui`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_:0c0f39c881`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_overb|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_neutral_profit_profit_lt_neg070`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_overb|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_neutral_profit_profit_lt_neg070`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-0.9975`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 39. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_dd41d703`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocke:f60ff97671`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_ok_or_unflagged_quote_age_q|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_missed_upside_profit_profit_lt_`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_ove|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_ok_or_unflagged_quote_age_q|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_missed_upside_profit_profit_lt_`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-0.6405`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 40. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_e8130b27`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked:eb35f37539`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquidity_liquidity_unknown_overbou|submit=submit:combo_submit_quality:source_scalp_sim_entry_submit_revalidation_warning_revalidation_warning_stale_context_or_quote_q|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_holding_action_not_applicable_at_start_profit_profit_unk|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutral_profit_profit_lt_neg070`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquidity_liquidity_unknown_overbou|submit=submit:combo_submit_quality:source_scalp_sim_entry_submit_revalidation_warning_revalidation_warning_stale_context_or_quote_q|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_holding_action_not_applicable_at_start_profit_profit_unk|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutral_profit_profit_lt_neg070`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-0.7549`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 41. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_f13463b9`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_en:575c5dd77b`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_70p_source_scalp_entry_action_decision_snapshot_stale_fresh_liquidity_liquidity_unkn|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_exit_profit_profit_lt_neg0`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_70p_source_scalp_entry_action_decision_snapshot_stale_fresh_liquidity_liquidity_unkn|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_exit_profit_profit_lt_neg0`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-1.9595`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 42. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_f2bb4423`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked:f0273aaa1d`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_over|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_exit_profit_profit_lt_neg0`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liquidity_unknown_overbought_over|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_exit_profit_profit_lt_neg0`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-1.0212`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 43. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_f4fedf98`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked:e531ef6981`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:combo_entry_spot:score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquidity_liquidity_unknown_overbou|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_good_exit_profit_profit_`, `legacy_raw_bucket_key=entry=entry:combo_entry_spot:score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquidity_liquidity_unknown_overbou|submit=submit:combo_submit_quality:source_scalp_sim_pre_submit_liquidity_guard_would_block_revalidation_warning_stale_context_or_qu|holding=holding:combo_holding_flow:source_scalp_sim_holding_started_action_wait_profit_profit_unknown_held_held_not_applicable_at_s|scale_in=scale_in:none|exit=exit:combo_exit_result:source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_good_exit_profit_profit_`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=tighten_or_exclude`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['entry', 'holding']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=-1.835`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 44. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_8fbb74dd`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_latency_block_revalidation_block_f
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_latency_block_revalidation_block_f`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_sourc:96839b309e`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:missing|submit=submit:combo_submit_quality:source_latency_block_revalidation_block_false_quote_age_quote_age_unknown_liquidity_liquidity_un|holding=holding:missing|scale_in=scale_in:none|exit=exit:missing`, `legacy_raw_bucket_key=entry=entry:missing|submit=submit:combo_submit_quality:source_latency_block_revalidation_block_false_quote_age_quote_age_unknown_liquidity_liquidity_un|holding=holding:missing|scale_in=scale_in:none|exit=exit:missing`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=keep_collecting`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['submit']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 45. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_98147c80`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_latency_pass_revalidation_block_fa
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_latency_pass_revalidation_block_fa`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_sourc:a37c3aaad0`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:missing|submit=submit:combo_submit_quality:source_latency_pass_revalidation_block_false_quote_age_quote_age_unknown_liquidity_liquidity_unk|holding=holding:missing|scale_in=scale_in:none|exit=exit:missing`, `legacy_raw_bucket_key=entry=entry:missing|submit=submit:combo_submit_quality:source_latency_pass_revalidation_block_false_quote_age_quote_age_unknown_liquidity_liquidity_unk|holding=holding:missing|scale_in=scale_in:none|exit=exit:missing`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=keep_collecting`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['submit']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 46. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_m_d40bb847`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_mi:1862cb7428`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:missing|submit=submit:missing|holding=holding:missing|scale_in=scale_in:none|exit=exit:combo_exit_result:source_scalp_sim_euphoria_context_noop_rule_exit_rule_unknown_outcome_outcome_unknown_profit_pro`, `legacy_raw_bucket_key=entry=entry:missing|submit=submit:missing|holding=holding:missing|scale_in=scale_in:none|exit=exit:combo_exit_result:source_scalp_sim_euphoria_context_noop_rule_exit_rule_unknown_outcome_outcome_unknown_profit_pro`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=keep_collecting`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['exit']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 47. `order_lifecycle_source_dimension_gap_lifecycle_flow_combo_lifecycle_flow_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_m_e2e1e58f`

- title: Lifecycle bucket discovery follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `auto_patch_required`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_resolution`
- confidence: `postclose_discovery_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex`, `source_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_mi:8ad3861285`, `canonical_bucket=lifecycle_flow:combo_lifecycle_flow:entry=entry:missing|submit=submit:missing|holding=holding:missing|scale_in=scale_in:none|exit=exit:combo_exit_result:source_scalp_sim_panic_context_warning_rule_exit_rule_unknown_outcome_outcome_unknown_profit_pro`, `legacy_raw_bucket_key=entry=entry:missing|submit=submit:missing|holding=holding:missing|scale_in=scale_in:none|exit=exit:combo_exit_result:source_scalp_sim_panic_context_warning_rule_exit_rule_unknown_outcome_outcome_unknown_profit_pro`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=unknown_dimension_requires_source_contract_or_dimension_fix`, `ai_tier2_taxonomy_decision=instrumentation_gap`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=taxonomy_provenance_gap`, `stage=lifecycle_flow`, `classification_state=source_only_keep_collecting`, `bucket_relation=new_bucket_candidate`, `recommended_action=keep_collecting`, `recommended_resolution=resolve_unknown_source_dimensions`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=['exit']`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime approval summary, threshold EV, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 48. `order_entry_submit_drought_auto_resolution`

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
- evidence: `ai_confirmed_unique=108`, `budget_pass_unique=56`, `latency_pass_unique=28`, `submitted_unique=2`, `submitted_to_ai_pct=1.9`, `submitted_to_budget_pct=3.6`, `blocker:latency_block:latency_state_danger=20789`, `blocker:blocked_swing_score_vpw:-=14359`, `blocker:blocked_gatekeeper_reject:눌림 대기=3852`, `upstream:blocked_ai_score:score_62.0=795`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=463`, `upstream:first_ai_wait:-=165`, `latency:latency_block:latency_state_danger=20789`
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

### 49. `order_entry_broker_receipt_contract_gap_review`

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
- evidence: `ai_confirmed_unique=108`, `budget_pass_unique=56`, `latency_pass_unique=28`, `submitted_unique=2`, `submitted_to_ai_pct=1.9`, `submitted_to_budget_pct=3.6`, `blocker:latency_block:latency_state_danger=20789`, `blocker:blocked_swing_score_vpw:-=14359`, `blocker:blocked_gatekeeper_reject:눌림 대기=3852`, `upstream:blocked_ai_score:score_62.0=795`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=463`, `upstream:first_ai_wait:-=165`, `latency:latency_block:latency_state_danger=20789`, `weak_contract_gap=broker_receipt_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 50. `order_entry_fill_quality_contract_gap_review`

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
- evidence: `ai_confirmed_unique=108`, `budget_pass_unique=56`, `latency_pass_unique=28`, `submitted_unique=2`, `submitted_to_ai_pct=1.9`, `submitted_to_budget_pct=3.6`, `blocker:latency_block:latency_state_danger=20789`, `blocker:blocked_swing_score_vpw:-=14359`, `blocker:blocked_gatekeeper_reject:눌림 대기=3852`, `upstream:blocked_ai_score:score_62.0=795`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=463`, `upstream:first_ai_wait:-=165`, `latency:latency_block:latency_state_danger=20789`, `weak_contract_gap=fill_quality_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 51. `order_entry_post_submit_contract_gap_review`

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
- evidence: `ai_confirmed_unique=108`, `budget_pass_unique=56`, `latency_pass_unique=28`, `submitted_unique=2`, `submitted_to_ai_pct=1.9`, `submitted_to_budget_pct=3.6`, `blocker:latency_block:latency_state_danger=20789`, `blocker:blocked_swing_score_vpw:-=14359`, `blocker:blocked_gatekeeper_reject:눌림 대기=3852`, `upstream:blocked_ai_score:score_62.0=795`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=463`, `upstream:first_ai_wait:-=165`, `latency:latency_block:latency_state_danger=20789`, `weak_contract_gap=post_submit_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 52. `order_entry_source_taxonomy_contract_gap_review`

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
- evidence: `ai_confirmed_unique=108`, `budget_pass_unique=56`, `latency_pass_unique=28`, `submitted_unique=2`, `submitted_to_ai_pct=1.9`, `submitted_to_budget_pct=3.6`, `blocker:latency_block:latency_state_danger=20789`, `blocker:blocked_swing_score_vpw:-=14359`, `blocker:blocked_gatekeeper_reject:눌림 대기=3852`, `upstream:blocked_ai_score:score_62.0=795`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=463`, `upstream:first_ai_wait:-=165`, `latency:latency_block:latency_state_danger=20789`, `weak_contract_gap=source_taxonomy_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`, `taxonomy_leakage_labels=['blocked_swing_score_vpw:-', 'blocked_swing_gap:-']`
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

### 53. `order_entry_telegram_post_submit_contract_gap_review`

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
- evidence: `ai_confirmed_unique=108`, `budget_pass_unique=56`, `latency_pass_unique=28`, `submitted_unique=2`, `submitted_to_ai_pct=1.9`, `submitted_to_budget_pct=3.6`, `blocker:latency_block:latency_state_danger=20789`, `blocker:blocked_swing_score_vpw:-=14359`, `blocker:blocked_gatekeeper_reject:눌림 대기=3852`, `upstream:blocked_ai_score:score_62.0=795`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=463`, `upstream:first_ai_wait:-=165`, `latency:latency_block:latency_state_danger=20789`, `weak_contract_gap=telegram_post_submit_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 54. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_10_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_10`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:fcd588ff6c`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 55. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_11_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_11`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:fcd588ff6c`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 56. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_12_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_ce8ff0c6`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6f3404e612
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_12`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6f3404e612`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 57. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_13_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_13`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:fcd588ff6c`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 58. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_14_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_ce8ff0c6`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6f3404e612
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_14`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6f3404e612`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 59. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_15_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_85a4bb2f`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4690e15525
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_15`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4690e15525`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 60. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_16_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_d46f2fa2`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:ab1924a1fc
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_16`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:ab1924a1fc`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 61. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_17_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_ffbb2a48`

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

### 62. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_18_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_d46f2fa2`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:ab1924a1fc
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_18`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:ab1924a1fc`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 63. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_19_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_ffbb2a48`

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

### 64. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_1_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_264969e0`

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

### 65. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_20_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_d46f2fa2`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:ab1924a1fc
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_20`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:ab1924a1fc`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 66. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_2_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_2`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:fcd588ff6c`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 67. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_3_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_3`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:fcd588ff6c`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 68. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_4_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_4`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:fcd588ff6c`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 69. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_5_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_ffbb2a48`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_5`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bfc859574f`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 70. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_6_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_ffbb2a48`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_6`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bfc859574f`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 71. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_7_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_ffbb2a48`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_7`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bfc859574f`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 72. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_8_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_8`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:fcd588ff6c`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 73. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_9_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_9`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:fcd588ff6c`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 74. `order_stage_hook_workorder_discovery_stage_hook_holding_flow_runner_debounce_guard`

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
- evidence: `strict_match_count=123`, `ambiguous_match_count=0`, `top_symbols=001740,001820,002220,005380,005680,005950,006660,007390`, `estimated_uplift_pct_sum=588.2600`, `gap=sim-only early stop/loss followed by later runner is not isolated as a dedicated producer`, `required_microstructure_features=ws_orderbook_churn,ofi_qi_persistence,large_trade_absorption,spread_flicker,top_depth_replenishment,holding_flow_cache_freshness`, `required_producer=runner_regime_counterfactual_producer`, `readiness_tier=implementation_workorder_ready`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `data/report/producer_gap_discovery/producer_gap_discovery_2026-05-28.json`, `tests/hook_input_output_contract_test.py`, `tests/forbidden_use_authority_test.py`, `tests/disabled_initial_runtime_state_test.py`, `docs/stage_hooks/holding_flow_runner_debounce_guard.md`
- acceptance_tests: `hook_input_output_contract_test validates EXIT_CONFIRM/HOLD_REVIEW/TRIM as labels only.`, `forbidden_use_authority_test rejects runtime arbitration authority and broker-order submission.`, `disabled_initial_runtime_state_test confirms no live apply path.`, `Microstructure coverage test verifies ws_orderbook_churn, ofi_qi_persistence, large_trade_absorption, spread_flicker, top_depth_replenishment, holding_flow_cache_freshness.`, `Source artifact test requires runner_regime_counterfactual_producer.`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "hook_name": "holding_flow_runner_debounce_guard", "implementation_files": ["src/engine/automation/stage_hook_runtime_scaffold.py"], "initial_runtime_state": "disabled", "requires_separate_runtime_apply_candidate": true, "runtime_effect": false, "source_report_type": "stage_hook_runtime_scaffold"}`
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

### 75. `order_stage_hook_workorder_discovery_stage_hook_plateau_breakdown_exit_arbitration_probe`

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
- evidence: `strict_match_count=142`, `ambiguous_match_count=0`, `top_symbols=000990,001740,001820,002220,005680,006660,009150,009420`, `estimated_giveback_pct_sum=677.3400`, `gap=sim-only prior modest win followed by late stop/giveback is not isolated as a dedicated producer`, `required_producer=plateau_breakdown_exit_counterfactual_producer`, `readiness_tier=implementation_workorder_ready`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `data/report/producer_gap_discovery/producer_gap_discovery_2026-05-28.json`, `tests/hook_input_output_contract_test.py`, `tests/forbidden_use_authority_test.py`, `tests/disabled_initial_runtime_state_test.py`, `docs/stage_hooks/plateau_breakdown_exit_arbitration_probe.md`
- acceptance_tests: `hook_input_output_contract_test validates EXIT_CONFIRM/TAKE_PROFIT_ON_PLATEAU/HOLD_REVIEW as non-runtime labels.`, `forbidden_use_authority_test blocks exit-decision override and hard-stop override.`, `disabled_initial_runtime_state_test confirms no live order or runtime effect.`, `Source artifact test requires plateau_breakdown_exit_counterfactual_producer.`, `Evidence contract test confirms sim/probe EV remains the primary source.`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "hook_name": "plateau_breakdown_exit_arbitration_probe", "implementation_files": ["src/engine/automation/stage_hook_runtime_scaffold.py"], "initial_runtime_state": "disabled", "requires_separate_runtime_apply_candidate": true, "runtime_effect": false, "source_report_type": "stage_hook_runtime_scaffold"}`
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

### 76. `order_lifecycle_entry_bucket_exit_rule_exit_unknown`

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
- evidence: `workorder_id=entry_bucket_source_quality_6`, `bucket_type=exit_rule`, `bucket_key=exit_unknown`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "entry_label_not_applicable", "source_field_coverage": {"exit_rule": {"coverage_rate": 0.0, "present_count": 0, "sample_count": 553, "source_fields": ["labels.exit_rule"]}}, "unknown_reason_counts": {"entry_label_not_applicable": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 77. `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_29f17ae0`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300
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
- evidence: `workorder_id=exit_bucket_source_quality_9`, `bucket_type=combo_exit_result`, `bucket_key=source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_recovery_or_relax", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 78. `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_73281913`

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

### 79. `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_823fe278`

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

### 80. `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_df836236`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150
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
- evidence: `workorder_id=exit_bucket_source_quality_8`, `bucket_type=combo_exit_result`, `bucket_key=source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_recovery_or_relax", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 81. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_good_e_d8c33947`

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
- evidence: `workorder_id=exit_bucket_source_quality_4`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
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

### 82. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_missed_30bb5c8f`

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
- evidence: `workorder_id=exit_bucket_source_quality_6`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
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

### 83. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_neutra_d5168c3c`

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
- evidence: `workorder_id=exit_bucket_source_quality_7`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
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

### 84. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_e_71b132b9`

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
- evidence: `workorder_id=exit_bucket_source_quality_5`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
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

### 85. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutra_d73738ba`

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
- evidence: `workorder_id=exit_bucket_source_quality_3`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
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

### 86. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_eb03513e`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150
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
- evidence: `workorder_id=exit_bucket_source_quality_10`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_recovery_or_relax", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 87. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_not_applicable_a_50644c4a`

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

### 88. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_not_applicable_a_828a0f68`

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
- evidence: `workorder_id=holding_bucket_source_quality_6`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
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

### 89. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_not_applicable_a_d19d801a`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start
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
- evidence: `workorder_id=holding_bucket_source_quality_8`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 90. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_not_applicable_a_f7731cc4`

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

### 91. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_not_applicable_a_fc555278`

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

### 92. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_lt_neg070_he_ed505a3f`

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

### 93. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_pos080_pos15_aaaecaaf`

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
- evidence: `workorder_id=holding_bucket_source_quality_4`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "candidate_recovery_or_relax", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 94. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_pos150_pos30_562da131`

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
- evidence: `workorder_id=holding_bucket_source_quality_7`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_recovery_or_relax`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
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

### 95. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_pos150_pos30_6f3188b0`

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

### 96. `order_lifecycle_holding_bucket_held_bucket_held_not_applicable_at_start_508784a3`

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

### 97. `order_producer_gap_discovery_producer_gap_missed_fill_recovery_counterfactual_missing`

- title: Implement missing producer: missed_fill_recovery_counterfactual_missing
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `producer_gap_discovery`
- lifecycle_stage: `submit`
- target_subsystem: `scalping submit/fill recovery source-only producer`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `missed_fill_recovery_counterfactual_missing`
- confidence: `high`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve source-quality adjusted EV attribution by making the missing producer observable.
- evidence: `matched_submit_fill_gap_rows=3`, `source_labels=lifecycle_decision_matrix`, `gap=post-submit missed fill and re-entry/recovery quality lacks a dedicated producer`, `ai_priority=high`, `ai_route=implement_now`
- parity_contract: -
- next_postclose_metric: producer_gap_discovery.producer_gap_missed_fill_recovery_counterfactual_missing
- files_likely_touched: `src/reporting/producer_gap_discovery.py`, `src/producers/scalping/missed_fill_recovery_counterfactual_producer.py`, `data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-28.json`
- acceptance_tests: `Producer records missed-fill recovery rows without runtime actions.`, `Source quality gate and forbidden-use contract are present.`, `No preapply real PnL is used as primary EV.`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "source_only_producer_gap_source_bundle", "join_keys": ["sim_record_id", "code", "submit_time", "fill_quality"], "missing_fields": [], "pattern_type": "missed_fill_recovery_counterfactual", "runtime_effect": false, "sample_count": 1, "section_id": "missed_fill_recovery_counterfactual", "source_paths": ["/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-28.json"], "source_quality_status": "implemented", "source_report_type": "producer_gap_source_bundle"}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 98. `order_producer_gap_discovery_producer_gap_scale_in_counterfactual_gap_missing`

- title: Implement missing producer: scale_in_counterfactual_gap_missing
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `producer_gap_discovery`
- lifecycle_stage: `scale_in`
- target_subsystem: `cross-domain scale-in lifecycle lineage`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `scale_in_counterfactual_gap_missing`
- confidence: `medium`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve source-quality adjusted EV attribution by making the missing producer observable.
- evidence: `matched_scale_in_gap_rows=2665`, `source_labels=lifecycle_decision_matrix,swing_lifecycle_bucket_discovery,swing_lifecycle_decision_matrix`, `gap=scale-in blocked/fill/unfill outcome comparison lacks a dedicated source producer`, `ai_priority=high`, `ai_route=implement_now`
- parity_contract: -
- next_postclose_metric: producer_gap_discovery.producer_gap_scale_in_counterfactual_gap_missing
- files_likely_touched: `src/reporting/producer_gap_discovery.py`, `src/producers/cross_domain/scale_in_lifecycle_extension.py`, `data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-28.json`
- acceptance_tests: `Scale-in comparison rows can be emitted as an extended lineage.`, `Forbidden uses remain absent.`, `Source-quality-adjusted metrics are present.`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "source_only_producer_gap_source_bundle", "join_keys": ["code", "entry_time", "scale_in_arm"], "missing_fields": [], "pattern_type": "scale_in_counterfactual_gap", "runtime_effect": false, "sample_count": 45, "section_id": "scale_in_counterfactual_gap", "source_paths": ["/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-05-28.json", "/home/ubuntu/KORStockScan/data/report/swing_lifecycle_audit/swing_lifecycle_audit_2026-05-28.json", "/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-05-28.json"], "source_quality_status": "implemented", "source_report_type": "producer_gap_source_bundle"}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 99. `order_producer_gap_discovery_producer_gap_sim_entry_selection_gap_missing`

- title: Implement missing producer: sim_entry_selection_gap_missing
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `producer_gap_discovery`
- lifecycle_stage: `entry`
- target_subsystem: `scalping entry provenance source-only producer`
- route: `existing_family`
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
- evidence: `sim_rows=1155`, `entry_time_field_rate=0.0000`, `gap=sim entry/selection rows are present but entry provenance is insufficient for bucket producer coverage`, `required_producer=sim_entry_selection_bucket_producer`, `ai_priority=high`, `ai_route=implement_now`
- parity_contract: -
- next_postclose_metric: producer_gap_discovery.producer_gap_sim_entry_selection_gap_missing
- files_likely_touched: `src/reporting/producer_gap_discovery.py`, `src/producers/scalping/sim_entry_selection_bucket_producer.py`, `data/report/producer_gap_source_bundle/producer_gap_source_bundle_2026-05-28.json`
- acceptance_tests: `Entry provenance rows are produced for sim-first cohorts.`, `No entry override or broker authority exists.`, `Required source fields are fully populated.`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "source_only_producer_gap_source_bundle", "join_keys": ["sim_record_id", "candidate_id", "code", "source_stage"], "missing_fields": [], "pattern_type": "sim_entry_selection_gap", "runtime_effect": false, "sample_count": 653, "section_id": "sim_entry_selection_bucket_producer", "source_paths": ["/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-05-28.json", "/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-28.json", "/home/ubuntu/KORStockScan/data/post_sell/post_sell_candidates_2026-05-28.jsonl", "/home/ubuntu/KORStockScan/data/post_sell/sim_post_sell_candidates_2026-05-28.jsonl", "/home/ubuntu/KORStockScan/data/post_sell/sim_post_sell_evaluations_2026-05-28.jsonl", "/home/ubuntu/KORStockScan/data/report/swing_lifecycle_audit/swing_lifecycle_audit_2026-05-28.json", "/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-05-28.json", "/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-05-28.json"], "source_quality_status": "implemented", "source_report_type": "producer_gap_source_bundle"}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 100. `order_producer_gap_discovery_producer_gap_sim_stop_recovery_gap_missing`

- title: Implement missing producer: sim_stop_recovery_gap_missing
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `producer_gap_discovery`
- lifecycle_stage: `exit`
- target_subsystem: `scalping sim-first stop-recovery producer`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `sim_stop_recovery_gap_missing`
- confidence: `high`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve source-quality adjusted EV attribution by making the missing producer observable.
- evidence: `sim_stop_or_loss_rows=1192`, `gap=sim stop/recovery variants need a sim-first source producer independent of real exits`, `required_producer=sim_stop_recovery_counterfactual_producer`, `ai_priority=high`, `ai_route=implement_now`
- parity_contract: -
- next_postclose_metric: producer_gap_discovery.producer_gap_sim_stop_recovery_gap_missing
- files_likely_touched: `src/reporting/producer_gap_discovery.py`, `src/producers/scalping/sim_stop_recovery_counterfactual_producer.py`, `data/report/producer_gap_source_bundle/producer_gap_source_bundle_2026-05-28.json`
- acceptance_tests: `Sim-first stop-recovery rows are emitted.`, `No runtime authority or broker submit authority exists.`, `The producer remains source-only.`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "source_only_producer_gap_source_bundle", "join_keys": ["sim_record_id", "code", "exit_reason"], "missing_fields": [], "pattern_type": "sim_stop_recovery_counterfactual", "runtime_effect": false, "sample_count": 3798, "section_id": "sim_stop_recovery_counterfactual", "source_paths": ["/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-05-28.json", "/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-28.json", "/home/ubuntu/KORStockScan/data/post_sell/post_sell_candidates_2026-05-28.jsonl", "/home/ubuntu/KORStockScan/data/post_sell/sim_post_sell_candidates_2026-05-28.jsonl", "/home/ubuntu/KORStockScan/data/post_sell/sim_post_sell_evaluations_2026-05-28.jsonl", "/home/ubuntu/KORStockScan/data/report/swing_lifecycle_audit/swing_lifecycle_audit_2026-05-28.json", "/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-05-28.json", "/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-05-28.json", "/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-05-28.json", "/home/ubuntu/KORStockScan/data/report/time_window_regime_counterfactual/time_window_regime_counterfactual_2026-05-28.json"], "source_quality_status": "implemented", "source_report_type": "producer_gap_source_bundle"}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 101. `order_producer_gap_discovery_producer_gap_stop_recovery_counterfactual_missing`

- title: Implement missing producer: stop_recovery_counterfactual_missing
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `producer_gap_discovery`
- lifecycle_stage: `exit`
- target_subsystem: `scalping stop/recovery source-only producer`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `stop_recovery_counterfactual_missing`
- confidence: `high`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve source-quality adjusted EV attribution by making the missing producer observable.
- evidence: `matched_stop_exit_rows=123`, `symbols=000270,000660,000880,001740,001820,003670,004090,005380`, `gap=post-stop recovery is not isolated as a dedicated producer input`, `ai_priority=high`, `ai_route=implement_now`
- parity_contract: -
- next_postclose_metric: producer_gap_discovery.producer_gap_stop_recovery_counterfactual_missing
- files_likely_touched: `src/reporting/producer_gap_discovery.py`, `src/producers/scalping/stop_recovery_counterfactual_producer.py`, `data/report/producer_gap_source_bundle/producer_gap_source_bundle_2026-05-28.json`
- acceptance_tests: `Producer emits the canonical bucket with all required source fields.`, `No runtime, threshold, broker, or exit authority is present.`, `Output uses sim/probe lifecycle evidence only.`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "source_only_producer_gap_source_bundle", "join_keys": ["code", "sell_time", "exit_reason"], "missing_fields": [], "pattern_type": "stop_recovery_counterfactual", "runtime_effect": false, "sample_count": 583, "section_id": "stop_recovery_counterfactual", "source_paths": ["/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-05-28.json", "/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-28.json", "/home/ubuntu/KORStockScan/data/report/swing_lifecycle_audit/swing_lifecycle_audit_2026-05-28.json", "/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-05-28.json", "/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-05-28.json", "/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-05-28.json", "/home/ubuntu/KORStockScan/data/report/time_window_regime_counterfactual/time_window_regime_counterfactual_2026-05-28.json"], "source_quality_status": "implemented", "source_report_type": "producer_gap_source_bundle"}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 102. `order_producer_gap_discovery_producer_gap_swing_sim_probe_label_gap_missing`

- title: Implement missing producer: swing_sim_probe_label_gap_missing
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `producer_gap_discovery`
- lifecycle_stage: `selection`
- target_subsystem: `swing lifecycle audit / label handoff`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_sim_probe_label_gap_missing`
- confidence: `medium`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve source-quality adjusted EV attribution by making the missing producer observable.
- evidence: `matched_swing_label_or_source_gap_rows=7404`, `source_labels=swing_lifecycle_audit,swing_lifecycle_bucket_discovery,swing_lifecycle_decision_matrix,swing_strategy_discovery_ev`, `gap=swing sim/probe label and EV handoff defects need a dedicated source producer`, `ai_priority=high`, `ai_route=implement_now`
- parity_contract: -
- next_postclose_metric: producer_gap_discovery.producer_gap_swing_sim_probe_label_gap_missing
- files_likely_touched: `src/reporting/producer_gap_discovery.py`, `src/producers/swing/swing_lifecycle_audit.py`, `src/producers/swing/swing_strategy_discovery_ev.py`
- acceptance_tests: `Existing swing artifact family can emit the label-gap dimension.`, `No new runtime authority is introduced.`, `The source-quality gate is explicit and deterministic.`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "source_only_producer_gap_source_bundle", "join_keys": ["code", "date", "source_probe_id"], "missing_fields": [], "pattern_type": "swing_sim_probe_label_gap", "runtime_effect": false, "sample_count": 137, "section_id": "swing_sim_probe_label_gap", "source_paths": ["/home/ubuntu/KORStockScan/data/report/swing_lifecycle_audit/swing_lifecycle_audit_2026-05-28.json", "/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-05-28.json"], "source_quality_status": "implemented", "source_report_type": "producer_gap_source_bundle"}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 103. `order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_low_missing_held_missing_kospi_regime_stop_loss`

- title: Swing LDM source field follow-up: mfe_low|missing|held_missing|kospi_regime_stop_loss|-|-|-
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
- evidence: `section=holding_exit_bucket_attribution`, `bucket_type=holding_exit_bucket_attribution`, `bucket_key=mfe_low|missing|held_missing|kospi_regime_stop_loss|-|-|-`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": ["mae_bucket", "held_bucket", "selection_arm", "sizing_arm", "exit_arm", "sector", "theme"], "runtime_effect": false, "sample_status": "waiting_source_field_sample", "source_field_coverage": {"exit_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.exit_policy"], "present_count": 0, "total_count": 3}, "exit_rule": {"coverage_ratio": 1.0, "paths": ["label_fields.exit_reason"], "present_count": 3, "total_count": 3}, "held_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.held_sec"], "present_count": 0, "total_count": 3}, "mae_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.mae_pct"], "present_count": 0, "total_count": 3}, "market_regime": {"coverage_ratio": 1.0, "paths": ["runtime_features.panic_context", "runtime_features.market_regime"], "present_count": 3, "total_count": 3}, "mfe_bucket": {"coverage_ratio": 1.0, "paths": ["label_fields.mfe_pct"], "present_count": 3, "total_count": 3}, "sector": {"coverage_ratio": 0.0, "paths": ["runtime_features.sector"], "present_count": 0, "total_count": 3}, "selection_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.entry_policy"], "present_count": 0, "total_count": 3}, "sizing_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.sizing_policy"], "present_count": 0, "total_count": 3}, "theme": {"coverage_ratio": 0.0, "paths": ["runtime_features.theme_tags"], "present_count": 0, "total_count": 3}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 3, "bucket_value_held_missing": 1, "bucket_value_missing": 1, "source_field_missing:exit_arm": 1, "source_field_missing:held_bucket": 1, "source_field_missing:mae_bucket": 1, "source_field_missing:sector": 1, "source_field_missing:selection_arm": 1, "source_field_missing:sizing_arm": 1, "source_field_missing:theme": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 104. `order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_low_missing_held_missing_kospi_trailing_start_take_profit`

- title: Swing LDM source field follow-up: mfe_low|missing|held_missing|kospi_trailing_start_take_profit|-|-|-
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
- evidence: `section=holding_exit_bucket_attribution`, `bucket_type=holding_exit_bucket_attribution`, `bucket_key=mfe_low|missing|held_missing|kospi_trailing_start_take_profit|-|-|-`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": ["mae_bucket", "held_bucket", "selection_arm", "sizing_arm", "exit_arm", "sector", "theme"], "runtime_effect": false, "sample_status": "waiting_source_field_sample", "source_field_coverage": {"exit_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.exit_policy"], "present_count": 0, "total_count": 3}, "exit_rule": {"coverage_ratio": 1.0, "paths": ["label_fields.exit_reason"], "present_count": 3, "total_count": 3}, "held_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.held_sec"], "present_count": 0, "total_count": 3}, "mae_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.mae_pct"], "present_count": 0, "total_count": 3}, "market_regime": {"coverage_ratio": 1.0, "paths": ["runtime_features.panic_context", "runtime_features.market_regime"], "present_count": 3, "total_count": 3}, "mfe_bucket": {"coverage_ratio": 1.0, "paths": ["label_fields.mfe_pct"], "present_count": 3, "total_count": 3}, "sector": {"coverage_ratio": 0.0, "paths": ["runtime_features.sector"], "present_count": 0, "total_count": 3}, "selection_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.entry_policy"], "present_count": 0, "total_count": 3}, "sizing_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.sizing_policy"], "present_count": 0, "total_count": 3}, "theme": {"coverage_ratio": 0.0, "paths": ["runtime_features.theme_tags"], "present_count": 0, "total_count": 3}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 3, "bucket_value_held_missing": 1, "bucket_value_missing": 1, "source_field_missing:exit_arm": 1, "source_field_missing:held_bucket": 1, "source_field_missing:mae_bucket": 1, "source_field_missing:sector": 1, "source_field_missing:selection_arm": 1, "source_field_missing:sizing_arm": 1, "source_field_missing:theme": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 105. `order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_mid_missing_2h_1d_kospi_trailing_start_take_profit`

- title: Swing LDM source field follow-up: mfe_mid|missing|2h_1d|kospi_trailing_start_take_profit|-|-|-
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
- evidence: `section=holding_exit_bucket_attribution`, `bucket_type=holding_exit_bucket_attribution`, `bucket_key=mfe_mid|missing|2h_1d|kospi_trailing_start_take_profit|-|-|-`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": ["mae_bucket", "selection_arm", "sizing_arm", "exit_arm", "sector", "theme"], "runtime_effect": false, "sample_status": "waiting_source_field_sample", "source_field_coverage": {"exit_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.exit_policy"], "present_count": 0, "total_count": 3}, "exit_rule": {"coverage_ratio": 1.0, "paths": ["label_fields.exit_reason"], "present_count": 3, "total_count": 3}, "held_bucket": {"coverage_ratio": 1.0, "paths": ["label_fields.held_sec"], "present_count": 3, "total_count": 3}, "mae_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.mae_pct"], "present_count": 0, "total_count": 3}, "market_regime": {"coverage_ratio": 1.0, "paths": ["runtime_features.panic_context", "runtime_features.market_regime"], "present_count": 3, "total_count": 3}, "mfe_bucket": {"coverage_ratio": 1.0, "paths": ["label_fields.mfe_pct"], "present_count": 3, "total_count": 3}, "sector": {"coverage_ratio": 0.0, "paths": ["runtime_features.sector"], "present_count": 0, "total_count": 3}, "selection_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.entry_policy"], "present_count": 0, "total_count": 3}, "sizing_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.sizing_policy"], "present_count": 0, "total_count": 3}, "theme": {"coverage_ratio": 0.0, "paths": ["runtime_features.theme_tags"], "present_count": 0, "total_count": 3}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 3, "bucket_value_missing": 1, "source_field_missing:exit_arm": 1, "source_field_missing:mae_bucket": 1, "source_field_missing:sector": 1, "source_field_missing:selection_arm": 1, "source_field_missing:sizing_arm": 1, "source_field_missing:theme": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 106. `order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_mid_missing_held_missing_kospi_trailing_start_take_profit`

- title: Swing LDM source field follow-up: mfe_mid|missing|held_missing|kospi_trailing_start_take_profit|-|-|-
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
- evidence: `section=holding_exit_bucket_attribution`, `bucket_type=holding_exit_bucket_attribution`, `bucket_key=mfe_mid|missing|held_missing|kospi_trailing_start_take_profit|-|-|-`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": ["mae_bucket", "held_bucket", "selection_arm", "sizing_arm", "exit_arm", "sector", "theme"], "runtime_effect": false, "sample_status": "waiting_source_field_sample", "source_field_coverage": {"exit_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.exit_policy"], "present_count": 0, "total_count": 4}, "exit_rule": {"coverage_ratio": 1.0, "paths": ["label_fields.exit_reason"], "present_count": 4, "total_count": 4}, "held_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.held_sec"], "present_count": 0, "total_count": 4}, "mae_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.mae_pct"], "present_count": 0, "total_count": 4}, "market_regime": {"coverage_ratio": 1.0, "paths": ["runtime_features.panic_context", "runtime_features.market_regime"], "present_count": 4, "total_count": 4}, "mfe_bucket": {"coverage_ratio": 1.0, "paths": ["label_fields.mfe_pct"], "present_count": 4, "total_count": 4}, "sector": {"coverage_ratio": 0.0, "paths": ["runtime_features.sector"], "present_count": 0, "total_count": 4}, "selection_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.entry_policy"], "present_count": 0, "total_count": 4}, "sizing_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.sizing_policy"], "present_count": 0, "total_count": 4}, "theme": {"coverage_ratio": 0.0, "paths": ["runtime_features.theme_tags"], "present_count": 0, "total_count": 4}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 3, "bucket_value_held_missing": 1, "bucket_value_missing": 1, "source_field_missing:exit_arm": 1, "source_field_missing:held_bucket": 1, "source_field_missing:mae_bucket": 1, "source_field_missing:sector": 1, "source_field_missing:selection_arm": 1, "source_field_missing:sizing_arm": 1, "source_field_missing:theme": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 107. `order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_neg_missing_held_missing_kospi_regime_stop_loss`

- title: Swing LDM source field follow-up: mfe_neg|missing|held_missing|kospi_regime_stop_loss|-|-|-
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
- evidence: `section=holding_exit_bucket_attribution`, `bucket_type=holding_exit_bucket_attribution`, `bucket_key=mfe_neg|missing|held_missing|kospi_regime_stop_loss|-|-|-`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": ["mae_bucket", "held_bucket", "selection_arm", "sizing_arm", "exit_arm", "sector", "theme"], "runtime_effect": false, "sample_status": "waiting_source_field_sample", "source_field_coverage": {"exit_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.exit_policy"], "present_count": 0, "total_count": 4}, "exit_rule": {"coverage_ratio": 1.0, "paths": ["label_fields.exit_reason"], "present_count": 4, "total_count": 4}, "held_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.held_sec"], "present_count": 0, "total_count": 4}, "mae_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.mae_pct"], "present_count": 0, "total_count": 4}, "market_regime": {"coverage_ratio": 1.0, "paths": ["runtime_features.panic_context", "runtime_features.market_regime"], "present_count": 4, "total_count": 4}, "mfe_bucket": {"coverage_ratio": 1.0, "paths": ["label_fields.mfe_pct"], "present_count": 4, "total_count": 4}, "sector": {"coverage_ratio": 0.0, "paths": ["runtime_features.sector"], "present_count": 0, "total_count": 4}, "selection_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.entry_policy"], "present_count": 0, "total_count": 4}, "sizing_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.sizing_policy"], "present_count": 0, "total_count": 4}, "theme": {"coverage_ratio": 0.0, "paths": ["runtime_features.theme_tags"], "present_count": 0, "total_count": 4}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 3, "bucket_value_held_missing": 1, "bucket_value_missing": 1, "source_field_missing:exit_arm": 1, "source_field_missing:held_bucket": 1, "source_field_missing:mae_bucket": 1, "source_field_missing:sector": 1, "source_field_missing:selection_arm": 1, "source_field_missing:sizing_arm": 1, "source_field_missing:theme": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 108. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_diagnostic`

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
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 5, "total_count": 5}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 5, "total_count": 5}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 5, "total_count": 5}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 5, "total_count": 5}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 5, "total_count": 5}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 2}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 109. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_insurance_보험_생명보험_`

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
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 7, "total_count": 7}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 7, "total_count": 7}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 7, "total_count": 7}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 7, "total_count": 7}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 7, "total_count": 7}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 110. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manufacture_of_bas`

- title: Swing LDM source field follow-up: breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Basic Chemicals|-|DIAGNOSTIC
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Basic Chemicals|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 6, "total_count": 6}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 6, "total_count": 6}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 6, "total_count": 6}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 6, "total_count": 6}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 6, "total_count": 6}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 111. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_computer_programming_syste`

- title: Swing LDM source field follow-up: breakout_confirm_entry|risk_capped|mae_stop_time_stop|Computer programming, System Integration and Management Services|-|DIAGNOSTIC
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|risk_capped|mae_stop_time_stop|Computer programming, System Integration and Management Services|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 4, "total_count": 4}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 4, "total_count": 4}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 4, "total_count": 4}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 4, "total_count": 4}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 4, "total_count": 4}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 112. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_insurance_보험_생명보험_diagnost`

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
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 7, "total_count": 7}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 7, "total_count": 7}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 7, "total_count": 7}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 7, "total_count": 7}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 7, "total_count": 7}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 113. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_of_basic_chemi`

- title: Swing LDM source field follow-up: breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Basic Chemicals|-|DIAGNOSTIC
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Basic Chemicals|-|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 6, "total_count": 6}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 6, "total_count": 6}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 6, "total_count": 6}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 6, "total_count": 6}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 6, "total_count": 6}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 114. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_of_electronic_`

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
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 14, "total_count": 14}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 14, "total_count": 14}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 14, "total_count": 14}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 14, "total_count": 14}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 14, "total_count": 14}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 115. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_of_other_chemi`

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
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 11, "total_count": 11}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 11, "total_count": 11}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 11, "total_count": 11}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 11, "total_count": 11}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 11, "total_count": 11}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 116. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_other_financial_intermedia`

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
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 14, "total_count": 14}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 14, "total_count": 14}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 14, "total_count": 14}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 14, "total_count": 14}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 14, "total_count": 14}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 117. `order_swing_ldm_selection_discovery_arm_attribution_pullback_limit_entry_risk_capped_mae_stop_time_stop_manufacture_of_basic_chemica`

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
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 6, "total_count": 6}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 6, "total_count": 6}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 6, "total_count": 6}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 6, "total_count": 6}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 6, "total_count": 6}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 118. `order_swing_ldm_selection_discovery_arm_attribution_pullback_limit_entry_risk_capped_mae_stop_time_stop_manufacture_of_semiconductor`

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
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 4, "total_count": 4}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 4, "total_count": 4}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 4, "total_count": 4}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 4, "total_count": 4}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 4, "total_count": 4}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 119. `order_swing_ldm_selection_discovery_arm_attribution_pullback_limit_entry_risk_capped_mae_stop_time_stop_sea_and_coastal_water_transp`

- title: Swing LDM source field follow-up: pullback_limit_entry|risk_capped|mae_stop_time_stop|Sea and Coastal Water Transport|운송_해운|DIAGNOSTIC
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
- evidence: `section=discovery_arm_attribution`, `bucket_type=discovery_arm_attribution`, `bucket_key=pullback_limit_entry|risk_capped|mae_stop_time_stop|Sea and Coastal Water Transport|운송_해운|DIAGNOSTIC`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 6, "total_count": 6}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 6, "total_count": 6}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 6, "total_count": 6}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 6, "total_count": 6}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 6, "total_count": 6}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 120. `order_lifecycle_overnight_bucket_combo_overnight_decision_action_action_unknown_status_sell_today_confidence_confidence_unknown_profit_pro`

- title: LDM overnight bucket attribution follow-up: combo_overnight_decision=action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_pos150_pos300
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
- evidence: `workorder_id=overnight_bucket_source_quality_2`, `bucket_type=combo_overnight_decision`, `bucket_key=action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_pos150_pos300`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 121. `order_lifecycle_overnight_bucket_combo_overnight_decision_action_sell_today_status_sell_today_confidence_confidence_070p_profit_profit_pos`

- title: LDM overnight bucket attribution follow-up: combo_overnight_decision=action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300
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
- evidence: `workorder_id=overnight_bucket_source_quality_1`, `bucket_type=combo_overnight_decision`, `bucket_key=action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 122. `order_lifecycle_overnight_bucket_confidence_band_confidence_070p`

- title: LDM overnight bucket attribution follow-up: confidence_band=confidence_070p
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
- evidence: `workorder_id=overnight_bucket_source_quality_3`, `bucket_type=confidence_band`, `bucket_key=confidence_070p`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 123. `order_lifecycle_overnight_bucket_confidence_band_confidence_unknown`

- title: LDM overnight bucket attribution follow-up: confidence_band=confidence_unknown
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
- evidence: `workorder_id=overnight_bucket_source_quality_4`, `bucket_type=confidence_band`, `bucket_key=confidence_unknown`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 124. `order_lifecycle_overnight_bucket_held_bucket_held_600_1800s_plus`

- title: LDM overnight bucket attribution follow-up: held_bucket=held_600_1800s_plus
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
- evidence: `workorder_id=overnight_bucket_source_quality_5`, `bucket_type=held_bucket`, `bucket_key=held_600_1800s_plus`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 125. `order_lifecycle_overnight_bucket_held_bucket_held_unknown`

- title: LDM overnight bucket attribution follow-up: held_bucket=held_unknown
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
- evidence: `workorder_id=overnight_bucket_source_quality_6`, `bucket_type=held_bucket`, `bucket_key=held_unknown`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 126. `order_lifecycle_overnight_bucket_overnight_action_action_unknown`

- title: LDM overnight bucket attribution follow-up: overnight_action=action_unknown
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
- evidence: `workorder_id=overnight_bucket_source_quality_8`, `bucket_type=overnight_action`, `bucket_key=action_unknown`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 127. `order_lifecycle_overnight_bucket_overnight_action_sell_today`

- title: LDM overnight bucket attribution follow-up: overnight_action=SELL_TODAY
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
- evidence: `workorder_id=overnight_bucket_source_quality_7`, `bucket_type=overnight_action`, `bucket_key=SELL_TODAY`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 128. `order_lifecycle_overnight_bucket_overnight_status_sell_today`

- title: LDM overnight bucket attribution follow-up: overnight_status=SELL_TODAY
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
- evidence: `workorder_id=overnight_bucket_source_quality_9`, `bucket_type=overnight_status`, `bucket_key=SELL_TODAY`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 129. `order_lifecycle_overnight_bucket_peak_profit_band_peak_unknown`

- title: LDM overnight bucket attribution follow-up: peak_profit_band=peak_unknown
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
- evidence: `workorder_id=overnight_bucket_source_quality_10`, `bucket_type=peak_profit_band`, `bucket_key=peak_unknown`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 130. `order_lifecycle_scale_in_bucket_ai_score_band_score_63_65`

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
- evidence: `workorder_id=scale_in_bucket_source_quality_3`, `bucket_type=ai_score_band`, `bucket_key=score_63_65`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 131. `order_lifecycle_scale_in_bucket_ai_score_band_score_66_69`

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

### 132. `order_lifecycle_scale_in_bucket_ai_score_band_score_70p`

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

### 133. `order_lifecycle_scale_in_bucket_ai_score_band_score_lt60`

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

### 134. `order_lifecycle_scale_in_bucket_ai_score_source_score_field_backfilled`

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
- evidence: `workorder_id=scale_in_bucket_source_quality_5`, `bucket_type=ai_score_source`, `bucket_key=score_field_backfilled`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 135. `order_lifecycle_scale_in_bucket_arm_avg_down`

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
- evidence: `workorder_id=scale_in_bucket_source_quality_6`, `bucket_type=arm`, `bucket_key=AVG_DOWN`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 136. `order_lifecycle_scale_in_bucket_arm_pyramid`

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
- evidence: `workorder_id=scale_in_bucket_source_quality_7`, `bucket_type=arm`, `bucket_key=PYRAMID`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 137. `order_lifecycle_scale_in_bucket_blocker_namespace_avg_down`

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
- evidence: `workorder_id=scale_in_bucket_source_quality_8`, `bucket_type=blocker_namespace`, `bucket_key=AVG_DOWN`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 138. `order_lifecycle_scale_in_bucket_blocker_namespace_avg_down_only`

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

### 139. `order_lifecycle_scale_in_bucket_blocker_namespace_pyramid`

- title: LDM scale-in bucket attribution follow-up: blocker_namespace=PYRAMID
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
- evidence: `workorder_id=scale_in_bucket_source_quality_9`, `bucket_type=blocker_namespace`, `bucket_key=PYRAMID`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 140. `order_lifecycle_entry_bucket_chosen_action_no_buy_ai`

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
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 141. `order_lifecycle_entry_bucket_chosen_action_wait_requote`

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
- evidence: `workorder_id=entry_bucket_source_quality_1`, `bucket_type=chosen_action`, `bucket_key=WAIT_REQUOTE`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 142. `order_lifecycle_entry_bucket_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_l`

- title: LDM entry bucket attribution follow-up: combo_entry_spot=score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1000_1200
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
- evidence: `workorder_id=entry_bucket_source_quality_3`, `bucket_type=combo_entry_spot`, `bucket_key=score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1000_1200`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 143. `order_lifecycle_entry_bucket_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liq`

- title: LDM entry bucket attribution follow-up: combo_entry_spot=score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_chase_risk|time=time_0900_1000
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
- evidence: `workorder_id=entry_bucket_source_quality_4`, `bucket_type=combo_entry_spot`, `bucket_key=score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_chase_risk|time=time_0900_1000`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 144. `order_lifecycle_entry_bucket_liquidity_bucket_liquidity_high`

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
- evidence: `workorder_id=entry_bucket_source_quality_7`, `bucket_type=liquidity_bucket`, `bucket_key=liquidity_high`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 145. `order_lifecycle_entry_bucket_overbought_bucket_overbought_proxy_chase_risk`

- title: LDM entry bucket attribution follow-up: overbought_bucket=overbought_proxy_chase_risk
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
- evidence: `workorder_id=entry_bucket_source_quality_10`, `bucket_type=overbought_bucket`, `bucket_key=overbought_proxy_chase_risk`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 146. `order_lifecycle_entry_bucket_overbought_bucket_overbought_proxy_normal`

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
- evidence: `workorder_id=entry_bucket_source_quality_8`, `bucket_type=overbought_bucket`, `bucket_key=overbought_proxy_normal`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 147. `order_lifecycle_entry_bucket_overbought_bucket_overbought_proxy_watch`

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
- evidence: `workorder_id=entry_bucket_source_quality_9`, `bucket_type=overbought_bucket`, `bucket_key=overbought_proxy_watch`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 148. `order_pattern_lab_ai_review_swing_pattern_lab_automation`

- title: Pattern Lab AI review follow-up: swing_pattern_lab_automation
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `pattern_lab_ai_review`
- lifecycle_stage: `pattern_lab_ai_review`
- target_subsystem: `pattern_lab`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `source_quality_gap`
- confidence: `ai_two_pass_review`
- priority: `10`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `True`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve pattern lab feedback quality without runtime mutation.
- evidence: `review_id=swing_pattern_lab_automation`, `domain=swing`, `final_state=source_quality_gap`, `final_decision=block_runtime_use`, `auditor_pass=False`, `explicit_gap_type=source_quality_gap`, `source_paths=['/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-05-28.json', '/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-05-28.json', '/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-28.json', '/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-05-28.json', '/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-05-28.json', '/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-05-28.json']`
- parity_contract: -
- next_postclose_metric: pattern_lab_ai_review.swing_pattern_lab_automation
- files_likely_touched: `src/engine/pattern_lab_ai_review.py`, `src/engine/pattern_lab_currentness_audit.py`, `analysis/gemini_scalping_pattern_lab`, `analysis/claude_scalping_pattern_lab`, `analysis/deepseek_swing_pattern_lab`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_ai_review.py src/tests/test_pattern_lab_currentness_audit.py`
- implementation_status: `implemented`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocked_families": [{"family": "swing_entry_ofi_qi_execution_quality", "invalid_micro_context_unique_record_count": 17, "runtime_effect": false, "source_quality_blockers": ["entry_ofi_qi_invalid_micro_context"], "stage": "entry"}, {"family": "swing_scale_in_ofi_qi_confirmation", "invalid_micro_context_unique_record_count": 1, "runtime_effect": false, "source_quality_blockers": ["scale_in_ofi_qi_invalid_micro_context"], "stage": "scale_in"}], "blocked_family_count": 2, "decision_authority": "swing_pattern_lab_analysis_workorder_source_only", "implementation_type": "source_quality_report_provenance", "ofi_qi_reason_counts": {"micro_missing": 4070, "micro_not_ready": 4078, "micro_stale": 0, "observer_unhealthy": 8, "state_insufficient": 4078}, "runtime_effect": false, "source_report_type": "swing_pattern_lab_automation"}`
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

### N2. `order_perf_daily_report_bulk_history`

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

### N3. `order_observation_source_quality_warning_rollup`

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

### N4. `order_perf_daily_report_engine_singleton`

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

### N5. `order_swing_gatekeeper_reject_threshold_review`

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

### N6. `order_perf_recommend_update_vectorization`

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

### N7. `order_swing_holding_exit_contract_gap_review`

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

### N8. `order_swing_market_regime_sensitivity_review`

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

### N9. `order_swing_ofi_qi_stale_or_missing_context`

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

### N10. `order_swing_scale_in_contract_gap_review`

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

### N11. `order_perf_swing_simulation_iteration`

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

### N12. `order_swing_discovery_label_contract_gap_review`

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

### N13. `order_perf_monitor_snapshot_stream_tail`

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

### N14. `order_swing_exit_ofi_qi_smoothing_distribution`

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

### N15. `order_swing_pattern_lab_deepseek_scale_in_events_observed`

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

### N16. `order_swing_strategy_discovery_source_quality_followup`

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

### N17. `order_perf_final_ensemble_records`

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

### N18. `order_swing_strategy_discovery_avoid_bucket_review`

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

### N19. `order_swing_pattern_lab_deepseek_entry_no_submissions`

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

### N20. `order_swing_ai_contract_structured_output_eval`

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

### N21. `order_panic_sell_defense_lifecycle_transition_pack`

- title: panic sell defense lifecycle transition pack
- decision: `design_family_candidate`
- decision_reason: finding needs family design; allowed_runtime_apply remains false until metadata/tests/guards are closed
- source_report_type: `threshold_cycle_calibration_source_bundle`
- lifecycle_stage: `holding_exit`
- target_subsystem: `panic_sell_defense`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `-`
- files_likely_touched: `src/engine/panic_sell_defense_report.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/plan-korStockScanPerformanceOptimization.rebase.md`
- acceptance_tests: `pytest panic sell defense/report lifecycle tests`, `pytest src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py`

### N22. `order_panic_buying_source_quality_market_breadth_micro_coverage`

- title: panic buying source-quality market breadth and micro coverage
- decision: `defer_evidence`
- decision_reason: route is not strong enough for immediate implementation
- source_report_type: `threshold_cycle_calibration_source_bundle`
- lifecycle_stage: `source_quality`
- target_subsystem: `panic_buying`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `-`
- files_likely_touched: `src/engine/panic_buying_report.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/plan-korStockScanPerformanceOptimization.rebase.md`, `docs/code-improvement-workorders/panic_buying_regime_mode_v2_2026-05-14.md`
- acceptance_tests: `pytest src/tests/test_panic_buying_report.py`, `pytest src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py`

### N23. `order_swing_pattern_lab_deepseek_ofi_qi_smoothing_review`

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

### N24. `order_perf_kiwoom_orders_http_session_review`

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

### N25. `order_perf_config_cache_scope_review`

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

### N26. `order_perf_dashboard_db_pool_review`

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

### N27. `order_perf_kiwoom_ws_tick_parse_fastpath`

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

### N28. `order_perf_raw_event_suppression_out_of_scope`

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

- 구현 결과는 `2026-05-29` 이후 postclose `threshold_cycle`, `scalping_pattern_lab_automation`, `threshold_cycle_ev`가 자동으로 다시 읽는다.
- 구현자가 수동으로 threshold 값을 바꾸는 것이 아니라, source/report/provenance를 닫아 다음 calibration이 판단하게 한다.
- 다음 Codex 세션 입력 문구: `none_for_bucket_discovery_classification`

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
