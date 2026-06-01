# Code Improvement Workorder - 2026-05-26

## 목적

- Postclose 자동화가 생성한 `code_improvement_order`를 Codex 실행용 작업지시서로 변환한다.
- 입력은 scalping pattern lab automation, swing lifecycle improvement automation, swing pattern lab automation을 함께 포함할 수 있다.
- 이 문서는 repo/runtime을 직접 변경하지 않는다. 사용자가 이 문서를 Codex 세션에 넣고 구현을 요청하는 지점만 사람 개입으로 남긴다.
- 구현 후 자동화체인 재투입은 다음 postclose report, threshold calibration, daily EV report가 담당한다.

## Source

- pattern_lab_automation: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-26.json`
- swing_improvement_automation: `/home/ubuntu/KORStockScan/data/report/swing_improvement_automation/swing_improvement_automation_2026-05-26.json`
- swing_pattern_lab_automation: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-05-26.json`
- swing_strategy_discovery_ev: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-05-26.json`
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-05-26.json`
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-05-26.json`
- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-26.json`
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-26.json`
- threshold_cycle_calibration: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_calibration/threshold_cycle_calibration_2026-05-26_postclose.json`
- pipeline_event_verbosity: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-05-26.json`
- observation_source_quality_audit: `/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-05-26.json`
- codebase_performance_workorder: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-05-26.json`
- pattern_lab_currentness_audit: `/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-05-26.json`
- pattern_lab_ai_review: `/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-05-26.json`
- producer_gap_discovery: `/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-05-26.json`
- stage_hook_workorder_discovery: `/home/ubuntu/KORStockScan/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_2026-05-26.json`
- stage_hook_runtime_scaffold: `/home/ubuntu/KORStockScan/data/report/stage_hook_runtime_scaffold/stage_hook_runtime_scaffold_2026-05-26.json`
- buy_funnel_sentinel: `/home/ubuntu/KORStockScan/data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-05-26.json`
- generated_at: `2026-06-01T13:16:24+09:00`
- generation_id: `2026-05-26-b5595e12da91`
- source_hash: `b5595e12da91ae8306b64af534126a074677323937c77bd24d58afe9ef2e8015`

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
- previous_generation_id: `2026-05-26-c291c35c76db`
- previous_source_hash: `c291c35c76db5e3cf675dc5c82e47497098510a0d54059fe479e3d7cca339ca8`
- new_order_ids: `['order_lifecycle_entry_bucket_overbought_bucket_overbought_ok', 'order_lifecycle_entry_bucket_score_band_score_60_62', 'order_lifecycle_entry_bucket_score_band_score_70p', 'order_lifecycle_entry_bucket_source_stage_scalp_entry_action_decision_snapshot', 'order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_4b4d95ef', 'order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_54959057', 'order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_8228e2d3', 'order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_d0f009b8', 'order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_f40e0622', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_good_e_d8c33947', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_missed_30bb5c8f', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_e_71b132b9', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_missed_bb293be8', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutra_d73738ba', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_10_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_70c74920', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_11_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_70c74920', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_12_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_70c74920', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_13_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_70c74920', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_14_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2f79cb41', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_15_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_992aa9df', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_16_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_17_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_18_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_19_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_1_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_0eef75e0', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_20_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_2_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_70c74920', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_3_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_70c74920', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_4_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_5c4afb97', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_5_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_70c74920', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_6_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_7_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_70c74920', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_8_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_70c74920', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_9_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_unknown_profit_p_6f63e810', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_unknown_profit_p_96e568f2', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_unknown_profit_p_9b5897ca', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_unknown_profit_p_9c31b140', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_unknown_profit_p_c6db79d9', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_unknown_profit_p_c9a72bc6', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_lt_neg070_he_cfc98129', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_neg010_pos08_9ba67c14', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_pos080_pos15_98664069', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_pos150_pos30_8a305aa1', 'order_lifecycle_source_dimension_gap_entry_combo_entry_spot_entry_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_cf6001dd', 'order_lifecycle_source_dimension_gap_entry_time_bucket_entry_time_bucket_time_unknown_cb0534f19f_432c214f', 'order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manufacture_of_bas', 'order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_of_electronic_', 'order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_of_other_chemi']`
- removed_order_ids: `['order_lifecycle_entry_bucket_chosen_action_action_unknown', 'order_lifecycle_entry_bucket_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_l', 'order_lifecycle_entry_bucket_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liq', 'order_lifecycle_entry_bucket_exit_rule_exit_unknown', 'order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_activities_auxilia', 'order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_insurance_보험_생명보험_', 'order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manufacture_of_ele', 'order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_other_financial_in', 'order_swing_lifecycle_bucket_discovery_swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_low_missing_30m_2h', 'order_swing_lifecycle_bucket_discovery_swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_low_missing_held_m', 'order_swing_lifecycle_bucket_discovery_swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_neg_missing_30m_2h', 'order_swing_lifecycle_bucket_discovery_swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_neg_missing_held_m', 'order_swing_lifecycle_bucket_discovery_swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_neg_missing_lt_30m', 'order_swing_lifecycle_bucket_discovery_swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confiden', 'order_swing_lifecycle_bucket_discovery_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_low_missing_30m_2h_ko', 'order_swing_lifecycle_bucket_discovery_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_low_missing_held_miss', 'order_swing_lifecycle_bucket_discovery_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_neg_missing_30m_2h_ko', 'order_swing_lifecycle_bucket_discovery_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_neg_missing_held_miss', 'order_swing_lifecycle_bucket_discovery_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_neg_missing_lt_30m_ko', 'order_swing_lifecycle_bucket_discovery_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_']`
- decision_changed_order_ids: `['order_entry_broker_receipt_contract_gap_review', 'order_entry_fill_quality_contract_gap_review', 'order_entry_post_submit_contract_gap_review', 'order_entry_source_taxonomy_contract_gap_review', 'order_entry_submit_drought_auto_resolution', 'order_entry_telegram_post_submit_contract_gap_review', 'order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_low_missing_30m_2h_kospi_regime_stop_loss', 'order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_low_missing_held_missing_kospi_regime_stop_loss', 'order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_neg_missing_30m_2h_kospi_regime_stop_loss', 'order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_neg_missing_held_missing_kospi_regime_stop_loss', 'order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_neg_missing_lt_30m_kospi_regime_stop_loss']`

## Summary

- source_order_count: `130`
- scalping_source_order_count: `12`
- swing_source_order_count: `8`
- swing_entry_bottleneck_primary: `SWING_ENTRY_DROUGHT_CRITICAL`
- swing_entry_bottleneck_selected: `True`
- swing_lab_source_order_count: `3`
- swing_strategy_discovery_source_order_count: `1`
- swing_lifecycle_matrix_source_order_count: `8`
- swing_lifecycle_bucket_discovery_source_order_count: `1`
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
- selected_order_count: `93`
- non_selected_order_count: `37`
- source_decision_counts: `{'implement_now': 28, 'attach_existing_family': 83, 'design_family_candidate': 6, 'defer_evidence': 10, 'reject': 3}`
- selected_decision_counts: `{'implement_now': 28, 'attach_existing_family': 65}`
- selected_route_counts: `{'instrumentation_order': 18, 'auto_patch_required': 2, 'block_source_quality': 1, 'implement_now': 7, 'existing_family': 65}`
- selected_implement_now_route_count: `7`
- selected_runtime_effect_false_count: `93`
- selected_unimplemented_runtime_effect_false_count: `28`
- selected_unimplemented_route_counts: `{'instrumentation_order': 18, 'auto_patch_required': 2, 'block_source_quality': 1, 'implement_now': 7}`
- non_selected_decision_counts: `{'attach_existing_family': 18, 'design_family_candidate': 6, 'defer_evidence': 10, 'reject': 3}`
- gemini_fresh: `True`
- claude_fresh: `True`
- swing_lifecycle_audit_available: `True`
- swing_pattern_lab_automation_available: `True`
- swing_pattern_lab_fresh: `True`
- pattern_lab_currentness_status: `pass`
- pattern_lab_currentness_fail_count: `0`
- pattern_lab_ai_review_status: `pass`
- pattern_lab_ai_review_workorder_count: `0`
- swing_threshold_ai_status: `unavailable`
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

### 1. `order_swing_entry_bottleneck_auto_resolution`

- title: swing entry bottleneck automatic resolution handoff
- decision: `implement_now`
- decision_reason: SWING_ENTRY_DROUGHT_CRITICAL is a source-only swing entry bottleneck handoff and must not be dropped by workorder selection limits
- source_report_type: `swing_improvement_automation`
- lifecycle_stage: `entry`
- target_subsystem: `swing_entry`
- route: `instrumentation_order`
- mapped_family: `swing_gatekeeper_accept_reject`
- threshold_family: `swing_gatekeeper_accept_reject`
- improvement_type: `entry_bottleneck_handoff`
- confidence: `consensus`
- priority: `0`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: restore swing entry/probe/submit coverage before evaluating dry-run or real-canary EV.
- evidence: `primary=SWING_ENTRY_DROUGHT_CRITICAL`, `matches=['GATEKEEPER_PULLBACK_WAIT', 'SCORE_VPW_BLOCK', 'GAP_REGIME_BLOCK', 'ENTRY_MICRO_CONTEXT_GAP', 'SUBMIT_ZERO']`, `entry_unique=33`, `submitted_unique_records=0`, `blocker_unique_total=33`, `probe_to_blocked_unique_pct=39.3939`, `simulated_to_entry_unique_pct=42.4242`, `gatekeeper_actions={'전량 회피': 10, '눌림 대기': 23}`
- parity_contract: -
- next_postclose_metric: restore swing entry/probe/submit coverage before evaluating dry-run or real-canary EV.
- files_likely_touched: `src/engine/swing_lifecycle_audit.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `pytest swing lifecycle audit tests`, `pytest code improvement workorder swing entry bottleneck tests`, `pytest swing LDM/bucket discovery handoff tests`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, regenerate swing audit, Swing LDM, bucket discovery, code workorder, EV/runtime summary, and postclose verifier; runtime/live order guards remain unchanged.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 2. `order_lifecycle_source_dimension_gap_entry_combo_entry_spot_entry_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_cf6001dd`

- title: Lifecycle bucket discovery follow-up: entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown_o
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `entry`
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
- evidence: `bucket_id=entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown_o`, `source_bucket_id=entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unf:bf10fe3b93`, `canonical_bucket=None`, `legacy_raw_bucket_key=None`, `bucket_alias_version=None`, `dimension_set_version=None`, `bucket_absorption_reason=None`, `ai_tier2_taxonomy_decision=None`, `ai_tier2_selected_source=None`, `source_bucket_kind=sim_auto_policy`, `stage=entry`, `classification_state=sim_auto_approved`, `bucket_relation=existing_bucket_refinement`, `recommended_action=relax_or_recover`, `recommended_resolution=emit_or_backfill_source_field`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=[]`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={'missing_source_field': 3}`, `source_quality_adjusted_ev_pct=3.9731`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
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

### 3. `order_lifecycle_source_dimension_gap_entry_time_bucket_entry_time_bucket_time_unknown_cb0534f19f_432c214f`

- title: Lifecycle bucket discovery follow-up: entry:time_bucket:time_unknown
- decision: `implement_now`
- decision_reason: lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains blocked until the regenerated reports and verifier pass
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `entry`
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
- evidence: `bucket_id=entry:time_bucket:time_unknown`, `source_bucket_id=entry:time_bucket:time_unknown:cb0534f19f`, `canonical_bucket=None`, `legacy_raw_bucket_key=None`, `bucket_alias_version=None`, `dimension_set_version=None`, `bucket_absorption_reason=None`, `ai_tier2_taxonomy_decision=None`, `ai_tier2_selected_source=None`, `source_bucket_kind=sim_auto_policy`, `stage=entry`, `classification_state=sim_auto_approved`, `bucket_relation=existing_bucket_refinement`, `recommended_action=relax_or_recover`, `recommended_resolution=emit_or_backfill_source_field`, `source_dimension_gap=unknown_source_dimensions`, `missing_dimension_keys=[]`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={'missing_source_field': 1}`, `source_quality_adjusted_ev_pct=3.3661`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
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

### 4. `order_producer_gap_discovery_producer_gap_sim_entry_selection_gap_missing`

- title: Implement missing producer: sim_entry_selection_gap_missing
- decision: `implement_now`
- decision_reason: producer gap discovery high-priority order is source-only missing producer work; implementation still requires Codex implement_now and cannot mutate runtime/order/provider/bot state
- source_report_type: `producer_gap_discovery`
- lifecycle_stage: `entry`
- target_subsystem: `sim_entry_selection_lineage_join`
- route: `block_source_quality`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `sim_entry_selection_gap_missing`
- confidence: `high`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve source-quality adjusted EV attribution by making the missing producer observable.
- evidence: `sim_rows=789`, `entry_time_field_rate=0.0000`, `gap=sim entry/selection rows are present but entry provenance is insufficient for bucket producer coverage`, `required_producer=sim_entry_selection_bucket_producer`, `ai_priority=critical`, `ai_route=block_source_quality`
- parity_contract: -
- next_postclose_metric: producer_gap_discovery.producer_gap_sim_entry_selection_gap_missing
- files_likely_touched: `src/report/post_sell/sim_entry_selection_bucket_producer.py`, `src/report/post_sell/sim_post_sell_source_lineage_join.py`, `src/report/registry/producer_registry.py`
- acceptance_tests: `For each scanned sim row, the join emits either strict entry provenance or an explicit missing-reason code.`, `Producer output can be linked from candidate rows to evaluation rows without orphan records across the six scanned dates.`, `No runtime control fields are added.`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun producer_gap_discovery, code improvement workorder, threshold EV, runtime summary, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 5. `order_producer_gap_discovery_producer_gap_swing_sim_probe_label_gap_missing`

- title: Implement missing producer: swing_sim_probe_label_gap_missing
- decision: `implement_now`
- decision_reason: producer gap discovery high-priority order is source-only missing producer work; implementation still requires Codex implement_now and cannot mutate runtime/order/provider/bot state
- source_report_type: `producer_gap_discovery`
- lifecycle_stage: `selection`
- target_subsystem: `swing_label_source_quality_handoff`
- route: `implement_now`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_sim_probe_label_gap_missing`
- confidence: `high`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve source-quality adjusted EV attribution by making the missing producer observable.
- evidence: `matched_swing_label_or_source_gap_rows=1526`, `source_labels=swing_lifecycle_audit,swing_lifecycle_bucket_discovery,swing_lifecycle_decision_matrix,swing_strategy_discovery_ev`, `gap=swing sim/probe label and EV handoff defects need a dedicated source producer`, `ai_priority=critical`, `ai_route=implement_now`
- parity_contract: -
- next_postclose_metric: producer_gap_discovery.producer_gap_swing_sim_probe_label_gap_missing
- files_likely_touched: `src/report/swing/swing_label_source_quality_producer.py`, `src/report/swing/swing_source_lineage_join.py`, `src/report/registry/producer_registry.py`
- acceptance_tests: `Producer joins the four 2026-05-26 swing artifacts and reproduces the 1526 matched gap rows.`, `Every output row includes lineage keys and a source-quality status.`, `Strict and ambiguous chronology states are reported separately.`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun producer_gap_discovery, code improvement workorder, threshold EV, runtime summary, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 6. `order_high_volume_diagnostic_stage_contract_labels`

- title: High-volume diagnostic stage metric contract labels
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `observation_source_quality_audit`
- lifecycle_stage: `source_quality_gate`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `-`
- confidence: `audit`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: none_direct_source_quality_attribution_only
- evidence: `status=warning`, `event_count=470359`, `warning_stage_count=4`, `warning_stages=blocked_strength_momentum,blocked_overbought,scalp_sim_pre_submit_overbought_guard_would_pass,scalp_sim_sell_order_assumed_filled`, `high_volume_no_source_field_stage_count=1`, `decision_authority=source_quality_only`, `runtime_effect=false`, `gap_stages=initial_entry_qty_cap_applied`
- parity_contract: -
- next_postclose_metric: observation_source_quality_audit.warning_stage_count and high_volume_no_source_field_stage_count
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/observation_source_quality_audit.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `pytest src/tests/test_observation_source_quality_audit.py src/tests/test_build_code_improvement_workorder.py`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 7. `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_4b4d95ef`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_lt_neg070
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `lifecycle_decision_matrix_exit_bucket_attribution`
- lifecycle_stage: `exit`
- target_subsystem: `lifecycle_decision_matrix`
- route: `instrumentation_order`
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
- evidence: `workorder_id=exit_bucket_source_quality_2`, `bucket_type=combo_exit_result`, `bucket_key=source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=source_quality_workorder`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `open`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "source_quality_workorder", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "mark_not_applicable_explicitly", "source_field_coverage": {"outcome": {"coverage_rate": 1.0, "present_count": 250, "sample_count": 250, "source_fields": ["source_stage", "labels.exit_rule", "runtime_features.chosen_action", "labels.sim_post_sell_outcome", "labels.outcome", "labels.profit_rate"]}}, "unknown_reason_counts": {"not_applicable": 1}}`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 8. `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_54959057`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos150_pos300
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `lifecycle_decision_matrix_exit_bucket_attribution`
- lifecycle_stage: `exit`
- target_subsystem: `lifecycle_decision_matrix`
- route: `instrumentation_order`
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
- evidence: `workorder_id=exit_bucket_source_quality_10`, `bucket_type=combo_exit_result`, `bucket_key=source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos150_pos300`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=source_quality_workorder`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `open`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos150_pos300", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "source_quality_workorder", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "mark_not_applicable_explicitly", "source_field_coverage": {"outcome": {"coverage_rate": 1.0, "present_count": 12, "sample_count": 12, "source_fields": ["source_stage", "labels.exit_rule", "runtime_features.chosen_action", "labels.sim_post_sell_outcome", "labels.outcome", "labels.profit_rate"]}}, "unknown_reason_counts": {"not_applicable": 1}}`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 9. `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_8228e2d3`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos080_pos150
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `lifecycle_decision_matrix_exit_bucket_attribution`
- lifecycle_stage: `exit`
- target_subsystem: `lifecycle_decision_matrix`
- route: `instrumentation_order`
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
- evidence: `workorder_id=exit_bucket_source_quality_8`, `bucket_type=combo_exit_result`, `bucket_key=source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos080_pos150`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=source_quality_workorder`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `open`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos080_pos150", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "source_quality_workorder", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "mark_not_applicable_explicitly", "source_field_coverage": {"outcome": {"coverage_rate": 1.0, "present_count": 17, "sample_count": 17, "source_fields": ["source_stage", "labels.exit_rule", "runtime_features.chosen_action", "labels.sim_post_sell_outcome", "labels.outcome", "labels.profit_rate"]}}, "unknown_reason_counts": {"not_applicable": 1}}`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 10. `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_d0f009b8`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg010_pos080
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `lifecycle_decision_matrix_exit_bucket_attribution`
- lifecycle_stage: `exit`
- target_subsystem: `lifecycle_decision_matrix`
- route: `instrumentation_order`
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
- evidence: `workorder_id=exit_bucket_source_quality_3`, `bucket_type=combo_exit_result`, `bucket_key=source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg010_pos080`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=source_quality_workorder`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `open`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg010_pos080", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "source_quality_workorder", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "mark_not_applicable_explicitly", "source_field_coverage": {"outcome": {"coverage_rate": 1.0, "present_count": 104, "sample_count": 104, "source_fields": ["source_stage", "labels.exit_rule", "runtime_features.chosen_action", "labels.sim_post_sell_outcome", "labels.outcome", "labels.profit_rate"]}}, "unknown_reason_counts": {"not_applicable": 1}}`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 11. `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_f40e0622`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg070_neg010
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `lifecycle_decision_matrix_exit_bucket_attribution`
- lifecycle_stage: `exit`
- target_subsystem: `lifecycle_decision_matrix`
- route: `instrumentation_order`
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
- evidence: `workorder_id=exit_bucket_source_quality_1`, `bucket_type=combo_exit_result`, `bucket_key=source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg070_neg010`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=source_quality_workorder`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `open`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg070_neg010", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "source_quality_workorder", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "mark_not_applicable_explicitly", "source_field_coverage": {"outcome": {"coverage_rate": 1.0, "present_count": 358, "sample_count": 358, "source_fields": ["source_stage", "labels.exit_rule", "runtime_features.chosen_action", "labels.sim_post_sell_outcome", "labels.outcome", "labels.profit_rate"]}}, "unknown_reason_counts": {"not_applicable": 1}}`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 12. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_unknown_profit_p_6f63e810`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg010_pos080|held=held_unknown
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `lifecycle_decision_matrix_holding_bucket_attribution`
- lifecycle_stage: `holding`
- target_subsystem: `lifecycle_decision_matrix`
- route: `instrumentation_order`
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
- evidence: `workorder_id=holding_bucket_source_quality_3`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg010_pos080|held=held_unknown`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=source_quality_workorder`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `open`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg010_pos080|held=held_unknown", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "source_quality_workorder", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "mark_not_applicable_explicitly", "source_field_coverage": {"action": {"coverage_rate": 1.0, "present_count": 21, "sample_count": 21, "source_fields": ["source_stage", "runtime_features.chosen_action", "runtime_features.ai_action", "runtime_features.profit_rate_live", "runtime_features.held_sec"]}, "held": {"coverage_rate": 1.0, "present_count": 21, "sample_count": 21, "source_fields": ["source_stage", "runtime_features.chosen_action", "runtime_features.ai_action", "runtime_features.profit_rate_live", "runtime_features.held_sec"]}}, "unknown_reason_counts": {"not_applicable": 2}}`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 13. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_unknown_profit_p_96e568f2`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300|held=held_unknown
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `lifecycle_decision_matrix_holding_bucket_attribution`
- lifecycle_stage: `holding`
- target_subsystem: `lifecycle_decision_matrix`
- route: `instrumentation_order`
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
- evidence: `workorder_id=holding_bucket_source_quality_7`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300|held=held_unknown`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=source_quality_workorder`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `open`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300|held=held_unknown", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "source_quality_workorder", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "mark_not_applicable_explicitly", "source_field_coverage": {"action": {"coverage_rate": 1.0, "present_count": 10, "sample_count": 10, "source_fields": ["source_stage", "runtime_features.chosen_action", "runtime_features.ai_action", "runtime_features.profit_rate_live", "runtime_features.held_sec"]}, "held": {"coverage_rate": 1.0, "present_count": 10, "sample_count": 10, "source_fields": ["source_stage", "runtime_features.chosen_action", "runtime_features.ai_action", "runtime_features.profit_rate_live", "runtime_features.held_sec"]}}, "unknown_reason_counts": {"not_applicable": 2}}`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 14. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_unknown_profit_p_9b5897ca`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos080_pos150|held=held_unknown
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `lifecycle_decision_matrix_holding_bucket_attribution`
- lifecycle_stage: `holding`
- target_subsystem: `lifecycle_decision_matrix`
- route: `instrumentation_order`
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
- evidence: `workorder_id=holding_bucket_source_quality_6`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos080_pos150|held=held_unknown`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=source_quality_workorder`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `open`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos080_pos150|held=held_unknown", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "source_quality_workorder", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "mark_not_applicable_explicitly", "source_field_coverage": {"action": {"coverage_rate": 1.0, "present_count": 12, "sample_count": 12, "source_fields": ["source_stage", "runtime_features.chosen_action", "runtime_features.ai_action", "runtime_features.profit_rate_live", "runtime_features.held_sec"]}, "held": {"coverage_rate": 1.0, "present_count": 12, "sample_count": 12, "source_fields": ["source_stage", "runtime_features.chosen_action", "runtime_features.ai_action", "runtime_features.profit_rate_live", "runtime_features.held_sec"]}}, "unknown_reason_counts": {"not_applicable": 2}}`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 15. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_unknown_profit_p_9c31b140`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg070_neg010|held=held_unknown
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `lifecycle_decision_matrix_holding_bucket_attribution`
- lifecycle_stage: `holding`
- target_subsystem: `lifecycle_decision_matrix`
- route: `instrumentation_order`
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
- evidence: `workorder_id=holding_bucket_source_quality_8`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg070_neg010|held=held_unknown`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=source_quality_workorder`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `open`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg070_neg010|held=held_unknown", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "source_quality_workorder", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "mark_not_applicable_explicitly", "source_field_coverage": {"action": {"coverage_rate": 1.0, "present_count": 9, "sample_count": 9, "source_fields": ["source_stage", "runtime_features.chosen_action", "runtime_features.ai_action", "runtime_features.profit_rate_live", "runtime_features.held_sec"]}, "held": {"coverage_rate": 1.0, "present_count": 9, "sample_count": 9, "source_fields": ["source_stage", "runtime_features.chosen_action", "runtime_features.ai_action", "runtime_features.profit_rate_live", "runtime_features.held_sec"]}}, "unknown_reason_counts": {"not_applicable": 2}}`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 16. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_unknown_profit_p_c6db79d9`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_lt_neg070|held=held_unknown
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `lifecycle_decision_matrix_holding_bucket_attribution`
- lifecycle_stage: `holding`
- target_subsystem: `lifecycle_decision_matrix`
- route: `instrumentation_order`
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
- evidence: `workorder_id=holding_bucket_source_quality_1`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_lt_neg070|held=held_unknown`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=source_quality_workorder`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `open`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_lt_neg070|held=held_unknown", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "source_quality_workorder", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "mark_not_applicable_explicitly", "source_field_coverage": {"action": {"coverage_rate": 1.0, "present_count": 67, "sample_count": 67, "source_fields": ["source_stage", "runtime_features.chosen_action", "runtime_features.ai_action", "runtime_features.profit_rate_live", "runtime_features.held_sec"]}, "held": {"coverage_rate": 1.0, "present_count": 67, "sample_count": 67, "source_fields": ["source_stage", "runtime_features.chosen_action", "runtime_features.ai_action", "runtime_features.profit_rate_live", "runtime_features.held_sec"]}}, "unknown_reason_counts": {"not_applicable": 2}}`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 17. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_unknown_profit_p_c9a72bc6`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300_plus|held=held_unknown
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `lifecycle_decision_matrix_holding_bucket_attribution`
- lifecycle_stage: `holding`
- target_subsystem: `lifecycle_decision_matrix`
- route: `instrumentation_order`
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
- evidence: `workorder_id=holding_bucket_source_quality_10`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300_plus|held=held_unknown`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=source_quality_workorder`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `open`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300_plus|held=held_unknown", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "source_quality_workorder", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "mark_not_applicable_explicitly", "source_field_coverage": {"action": {"coverage_rate": 1.0, "present_count": 4, "sample_count": 4, "source_fields": ["source_stage", "runtime_features.chosen_action", "runtime_features.ai_action", "runtime_features.profit_rate_live", "runtime_features.held_sec"]}, "held": {"coverage_rate": 1.0, "present_count": 4, "sample_count": 4, "source_fields": ["source_stage", "runtime_features.chosen_action", "runtime_features.ai_action", "runtime_features.profit_rate_live", "runtime_features.held_sec"]}}, "unknown_reason_counts": {"not_applicable": 2}}`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 18. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_lt_neg070_he_cfc98129`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_unknown
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `lifecycle_decision_matrix_holding_bucket_attribution`
- lifecycle_stage: `holding`
- target_subsystem: `lifecycle_decision_matrix`
- route: `instrumentation_order`
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
- evidence: `workorder_id=holding_bucket_source_quality_2`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_unknown`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=source_quality_workorder`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `open`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_unknown", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "source_quality_workorder", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "mark_not_applicable_explicitly", "source_field_coverage": {"held": {"coverage_rate": 1.0, "present_count": 45, "sample_count": 45, "source_fields": ["source_stage", "runtime_features.chosen_action", "runtime_features.ai_action", "runtime_features.profit_rate_live", "runtime_features.held_sec"]}}, "unknown_reason_counts": {"not_applicable": 1}}`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 19. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_neg010_pos08_9ba67c14`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_unknown
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `lifecycle_decision_matrix_holding_bucket_attribution`
- lifecycle_stage: `holding`
- target_subsystem: `lifecycle_decision_matrix`
- route: `instrumentation_order`
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
- evidence: `workorder_id=holding_bucket_source_quality_4`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_unknown`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=source_quality_workorder`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `open`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_unknown", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "source_quality_workorder", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "mark_not_applicable_explicitly", "source_field_coverage": {"held": {"coverage_rate": 1.0, "present_count": 13, "sample_count": 13, "source_fields": ["source_stage", "runtime_features.chosen_action", "runtime_features.ai_action", "runtime_features.profit_rate_live", "runtime_features.held_sec"]}}, "unknown_reason_counts": {"not_applicable": 1}}`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 20. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_pos080_pos15_98664069`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_unknown
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `lifecycle_decision_matrix_holding_bucket_attribution`
- lifecycle_stage: `holding`
- target_subsystem: `lifecycle_decision_matrix`
- route: `instrumentation_order`
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
- evidence: `workorder_id=holding_bucket_source_quality_5`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_unknown`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=source_quality_workorder`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `open`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_unknown", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "source_quality_workorder", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "mark_not_applicable_explicitly", "source_field_coverage": {"held": {"coverage_rate": 1.0, "present_count": 13, "sample_count": 13, "source_fields": ["source_stage", "runtime_features.chosen_action", "runtime_features.ai_action", "runtime_features.profit_rate_live", "runtime_features.held_sec"]}}, "unknown_reason_counts": {"not_applicable": 1}}`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 21. `order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_pos150_pos30_8a305aa1`

- title: LDM holding bucket source-quality follow-up: combo_holding_flow=source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_unknown
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `lifecycle_decision_matrix_holding_bucket_attribution`
- lifecycle_stage: `holding`
- target_subsystem: `lifecycle_decision_matrix`
- route: `instrumentation_order`
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
- evidence: `workorder_id=holding_bucket_source_quality_9`, `bucket_type=combo_holding_flow`, `bucket_key=source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_unknown`, `reason=holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=source_quality_workorder`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: holding_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `open`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_unknown", "bucket_type": "combo_holding_flow", "decision_point": "holding_bucket_classification", "deterministic_decision": "source_quality_workorder", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "mark_not_applicable_explicitly", "source_field_coverage": {"held": {"coverage_rate": 1.0, "present_count": 8, "sample_count": 8, "source_fields": ["source_stage", "runtime_features.chosen_action", "runtime_features.ai_action", "runtime_features.profit_rate_live", "runtime_features.held_sec"]}}, "unknown_reason_counts": {"not_applicable": 1}}`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 22. `order_producer_gap_discovery_producer_gap_limit_up_plateau_breakdown_exit_missing`

- title: Implement missing producer: limit_up_plateau_breakdown_exit_missing
- decision: `implement_now`
- decision_reason: producer gap discovery high-priority order is source-only missing producer work; implementation still requires Codex implement_now and cannot mutate runtime/order/provider/bot state
- source_report_type: `producer_gap_discovery`
- lifecycle_stage: `exit`
- target_subsystem: `real_vs_sim_plateau_breakdown_counterfactual`
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
- files_likely_touched: `src/report/post_sell/plateau_breakdown_exit_counterfactual_producer.py`, `src/report/post_sell/plateau_state_classifier.py`, `src/report/registry/producer_registry.py`
- acceptance_tests: `Producer reproduces the 036010 incident row and its same-parent comparison fields from 2026-05-26 sources.`, `Rows are classified into plateau-hold versus breakdown states with lineage keys present.`, `Output contains observation metrics only.`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun producer_gap_discovery, code improvement workorder, threshold EV, runtime summary, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 23. `order_producer_gap_discovery_producer_gap_sim_exit_plateau_breakdown_gap_missing`

- title: Implement missing producer: sim_exit_plateau_breakdown_gap_missing
- decision: `implement_now`
- decision_reason: producer gap discovery high-priority order is source-only missing producer work; implementation still requires Codex implement_now and cannot mutate runtime/order/provider/bot state
- source_report_type: `producer_gap_discovery`
- lifecycle_stage: `exit`
- target_subsystem: `sim_plateau_breakdown_counterfactual`
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
- files_likely_touched: `src/report/post_sell/plateau_breakdown_exit_counterfactual_producer.py`, `src/report/post_sell/sim_plateau_state_builder.py`, `src/report/registry/producer_registry.py`
- acceptance_tests: `Producer reproduces strict_match_count=56 and ambiguous_match_count=0 over the scanned windows.`, `Output includes estimated giveback fields for the matched rows.`, `All emitted fields are observational.`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun producer_gap_discovery, code improvement workorder, threshold EV, runtime summary, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 24. `order_producer_gap_discovery_producer_gap_sim_holding_runner_gap_missing`

- title: Implement missing producer: sim_holding_runner_gap_missing
- decision: `implement_now`
- decision_reason: producer gap discovery high-priority order is source-only missing producer work; implementation still requires Codex implement_now and cannot mutate runtime/order/provider/bot state
- source_report_type: `producer_gap_discovery`
- lifecycle_stage: `holding`
- target_subsystem: `sim_runner_regime_counterfactual`
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
- files_likely_touched: `src/report/post_sell/runner_regime_counterfactual_producer.py`, `src/report/post_sell/sim_runner_feature_builder.py`, `src/report/registry/producer_registry.py`
- acceptance_tests: `Producer reproduces strict_match_count=61 and ambiguous_match_count=0 over the scanned windows.`, `Output includes uplift metrics and the declared microstructure feature fields for strict rows.`, `No runtime control or decision fields are emitted.`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun producer_gap_discovery, code improvement workorder, threshold EV, runtime summary, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 25. `order_producer_gap_discovery_producer_gap_sim_scale_in_counterfactual_gap_missing`

- title: Implement missing producer: sim_scale_in_counterfactual_gap_missing
- decision: `implement_now`
- decision_reason: producer gap discovery high-priority order is source-only missing producer work; implementation still requires Codex implement_now and cannot mutate runtime/order/provider/bot state
- source_report_type: `producer_gap_discovery`
- lifecycle_stage: `scale_in`
- target_subsystem: `sim_scale_in_would_add_counterfactual`
- route: `implement_now`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `sim_scale_in_counterfactual_gap_missing`
- confidence: `high`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve source-quality adjusted EV attribution by making the missing producer observable.
- evidence: `gap=sim scale-in blocked/fill/unfill would-add comparison needs a dedicated producer`, `required_producer=sim_scale_in_would_add_counterfactual_producer`, `ai_priority=high`, `ai_route=implement_now`
- parity_contract: -
- next_postclose_metric: producer_gap_discovery.producer_gap_sim_scale_in_counterfactual_gap_missing
- files_likely_touched: `src/report/post_sell/sim_scale_in_would_add_counterfactual_producer.py`, `src/report/common/scale_in_lineage_builder.py`, `src/report/registry/producer_registry.py`
- acceptance_tests: `Producer reproduces the current 3286-row cohort from the scanned sim sources.`, `Blocked, filled, and unfilled states are emitted as separate labels.`, `Output remains observational only.`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun producer_gap_discovery, code improvement workorder, threshold EV, runtime summary, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 26. `order_producer_gap_discovery_producer_gap_sim_stop_recovery_gap_missing`

- title: Implement missing producer: sim_stop_recovery_gap_missing
- decision: `implement_now`
- decision_reason: producer gap discovery high-priority order is source-only missing producer work; implementation still requires Codex implement_now and cannot mutate runtime/order/provider/bot state
- source_report_type: `producer_gap_discovery`
- lifecycle_stage: `exit`
- target_subsystem: `sim_stop_recovery_counterfactual`
- route: `implement_now`
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
- evidence: `sim_stop_or_loss_rows=704`, `gap=sim stop/recovery variants need a sim-first source producer independent of real exits`, `required_producer=sim_stop_recovery_counterfactual_producer`, `ai_priority=high`, `ai_route=implement_now`
- parity_contract: -
- next_postclose_metric: producer_gap_discovery.producer_gap_sim_stop_recovery_gap_missing
- files_likely_touched: `src/report/post_sell/sim_stop_recovery_counterfactual_producer.py`, `src/report/post_sell/stop_recovery_state_builder.py`, `src/report/registry/producer_registry.py`
- acceptance_tests: `Producer reproduces the 704 matched sim stop-or-loss rows across the scanned windows.`, `Recovery states are mutually exclusive and lineage keyed.`, `No runtime control fields are emitted.`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun producer_gap_discovery, code improvement workorder, threshold EV, runtime summary, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 27. `order_producer_gap_discovery_producer_gap_volatile_runner_exit_counterfactual_missing`

- title: Implement missing producer: volatile_runner_exit_counterfactual_missing
- decision: `implement_now`
- decision_reason: producer gap discovery high-priority order is source-only missing producer work; implementation still requires Codex implement_now and cannot mutate runtime/order/provider/bot state
- source_report_type: `producer_gap_discovery`
- lifecycle_stage: `exit`
- target_subsystem: `real_vs_sim_runner_regime_counterfactual`
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
- files_likely_touched: `src/report/post_sell/runner_regime_counterfactual_producer.py`, `src/report/post_sell/real_sim_parent_matcher.py`, `src/report/registry/producer_registry.py`
- acceptance_tests: `Producer reproduces the 003720 incident row and the real-versus-sim uplift fields from 2026-05-26 sources.`, `Same-parent matching is explicit and rows failing strict linkage are excluded or separately labeled.`, `Output contains no fields that mutate runtime behavior.`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, rerun producer_gap_discovery, code improvement workorder, threshold EV, runtime summary, and postclose verifier.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 28. `order_swing_lifecycle_bucket_discovery_swing_entry_bottleneck_swing_entry_drought_critical`

- title: Swing lifecycle bucket discovery handoff follow-up: swing_entry_bottleneck_swing_entry_drought_critical
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `swing_lifecycle_bucket_discovery`
- lifecycle_stage: `entry`
- target_subsystem: `swing_lifecycle_bucket_discovery`
- route: `instrumentation_order`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `swing_bucket_handoff_or_contract_gap`
- confidence: `postclose_bucket_discovery_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep Swing bucket discovery handoff explicit without allowing sim-only output to mutate real runtime.
- evidence: `bucket_id=swing_entry_bottleneck_swing_entry_drought_critical`, `canonical_bucket=-`, `legacy_raw_bucket_key=-`, `ai_tier2_taxonomy_decision=-`, `ai_tier2_selected_source=-`, `classification_state=code_patch_required`, `reason=swing_ldm_bucket_contract_or_source_quality_gap`, `source_workorder_id=-`, `parent_bucket_id=swing_entry_bottleneck_swing_entry_drought_critical`, `decision_authority=swing_ldm_bucket_discovery_sim_auto`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Swing bucket discovery candidates and workorders should be visible in EV, runtime summary, workorder, and verifier.
- files_likely_touched: `src/engine/swing_lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_ev_report.py`, `src/engine/runtime_approval_summary.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `-`
- implementation_provenance: `-`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 29. `order_entry_submit_drought_auto_resolution`

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
- evidence: `ai_confirmed_unique=169`, `budget_pass_unique=81`, `latency_pass_unique=37`, `submitted_unique=20`, `submitted_to_ai_pct=11.8`, `submitted_to_budget_pct=24.7`, `blocker:blocked_swing_score_vpw:-=138819`, `blocker:blocked_overbought:-=20849`, `blocker:blocked_strength_momentum:below_strength_base=11868`, `upstream:blocked_ai_score:score_62.0=1247`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=738`, `upstream:first_ai_wait:-=344`, `latency:latency_block:latency_state_danger=2382`
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

### 30. `order_entry_broker_receipt_contract_gap_review`

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
- evidence: `ai_confirmed_unique=169`, `budget_pass_unique=81`, `latency_pass_unique=37`, `submitted_unique=20`, `submitted_to_ai_pct=11.8`, `submitted_to_budget_pct=24.7`, `blocker:blocked_swing_score_vpw:-=138819`, `blocker:blocked_overbought:-=20849`, `blocker:blocked_strength_momentum:below_strength_base=11868`, `upstream:blocked_ai_score:score_62.0=1247`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=738`, `upstream:first_ai_wait:-=344`, `latency:latency_block:latency_state_danger=2382`, `weak_contract_gap=broker_receipt_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 31. `order_entry_fill_quality_contract_gap_review`

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
- evidence: `ai_confirmed_unique=169`, `budget_pass_unique=81`, `latency_pass_unique=37`, `submitted_unique=20`, `submitted_to_ai_pct=11.8`, `submitted_to_budget_pct=24.7`, `blocker:blocked_swing_score_vpw:-=138819`, `blocker:blocked_overbought:-=20849`, `blocker:blocked_strength_momentum:below_strength_base=11868`, `upstream:blocked_ai_score:score_62.0=1247`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=738`, `upstream:first_ai_wait:-=344`, `latency:latency_block:latency_state_danger=2382`, `weak_contract_gap=fill_quality_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 32. `order_entry_post_submit_contract_gap_review`

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
- evidence: `ai_confirmed_unique=169`, `budget_pass_unique=81`, `latency_pass_unique=37`, `submitted_unique=20`, `submitted_to_ai_pct=11.8`, `submitted_to_budget_pct=24.7`, `blocker:blocked_swing_score_vpw:-=138819`, `blocker:blocked_overbought:-=20849`, `blocker:blocked_strength_momentum:below_strength_base=11868`, `upstream:blocked_ai_score:score_62.0=1247`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=738`, `upstream:first_ai_wait:-=344`, `latency:latency_block:latency_state_danger=2382`, `weak_contract_gap=post_submit_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 33. `order_entry_source_taxonomy_contract_gap_review`

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
- evidence: `ai_confirmed_unique=169`, `budget_pass_unique=81`, `latency_pass_unique=37`, `submitted_unique=20`, `submitted_to_ai_pct=11.8`, `submitted_to_budget_pct=24.7`, `blocker:blocked_swing_score_vpw:-=138819`, `blocker:blocked_overbought:-=20849`, `blocker:blocked_strength_momentum:below_strength_base=11868`, `upstream:blocked_ai_score:score_62.0=1247`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=738`, `upstream:first_ai_wait:-=344`, `latency:latency_block:latency_state_danger=2382`, `weak_contract_gap=source_taxonomy_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`, `taxonomy_leakage_labels=['blocked_swing_score_vpw:-', 'blocked_swing_gap:-']`
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

### 34. `order_entry_telegram_post_submit_contract_gap_review`

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
- evidence: `ai_confirmed_unique=169`, `budget_pass_unique=81`, `latency_pass_unique=37`, `submitted_unique=20`, `submitted_to_ai_pct=11.8`, `submitted_to_budget_pct=24.7`, `blocker:blocked_swing_score_vpw:-=138819`, `blocker:blocked_overbought:-=20849`, `blocker:blocked_strength_momentum:below_strength_base=11868`, `upstream:blocked_ai_score:score_62.0=1247`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=738`, `upstream:first_ai_wait:-=344`, `latency:latency_block:latency_state_danger=2382`, `weak_contract_gap=telegram_post_submit_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 35. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_10_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_70c74920`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:83c74e766d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_10`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:83c74e766d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=[]`, `required_producer_consumer_candidates=[]`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 36. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_11_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_70c74920`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:83c74e766d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_11`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:83c74e766d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=[]`, `required_producer_consumer_candidates=[]`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 37. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_12_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_70c74920`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:83c74e766d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_12`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:83c74e766d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=[]`, `required_producer_consumer_candidates=[]`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 38. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_13_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_70c74920`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:83c74e766d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_13`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:83c74e766d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=[]`, `required_producer_consumer_candidates=[]`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 39. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_14_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2f79cb41`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:8c2e10849d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_14`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:8c2e10849d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=[]`, `required_producer_consumer_candidates=[]`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 40. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_15_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_992aa9df`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:056e341249
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_15`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:056e341249`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=[]`, `required_producer_consumer_candidates=[]`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 41. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_16_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_16`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:fcd588ff6c`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=[]`, `required_producer_consumer_candidates=[]`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 42. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_17_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_17`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:fcd588ff6c`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=[]`, `required_producer_consumer_candidates=[]`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 43. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_18_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_18`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:fcd588ff6c`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=[]`, `required_producer_consumer_candidates=[]`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 44. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_19_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_19`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:fcd588ff6c`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=[]`, `required_producer_consumer_candidates=[]`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 45. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_1_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_submit_submit_c_0eef75e0`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:5dedc4958e
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_1`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:5dedc4958e`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=[]`, `required_producer_consumer_candidates=[]`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 46. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_20_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_20`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:fcd588ff6c`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=[]`, `required_producer_consumer_candidates=[]`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 47. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_2_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_70c74920`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:83c74e766d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_2`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:83c74e766d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=[]`, `required_producer_consumer_candidates=[]`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 48. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_3_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_70c74920`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:83c74e766d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_3`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:83c74e766d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=[]`, `required_producer_consumer_candidates=[]`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 49. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_4_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_5c4afb97`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:e63a874037
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_4`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:e63a874037`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=[]`, `required_producer_consumer_candidates=[]`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 50. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_5_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_70c74920`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:83c74e766d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_5`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:83c74e766d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=[]`, `required_producer_consumer_candidates=[]`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 51. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_6_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_6`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:fcd588ff6c`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=[]`, `required_producer_consumer_candidates=[]`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 52. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_7_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_70c74920`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:83c74e766d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_7`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:83c74e766d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=[]`, `required_producer_consumer_candidates=[]`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 53. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_8_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_70c74920`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:83c74e766d
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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_8`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:83c74e766d`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=[]`, `required_producer_consumer_candidates=[]`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 54. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_9_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04`

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
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_9`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:fcd588ff6c`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=[]`, `required_producer_consumer_candidates=[]`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 55. `order_stage_hook_workorder_discovery_stage_hook_holding_flow_runner_debounce_guard`

- title: Implement stage hook: holding_flow_runner_debounce_guard
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `stage_hook_workorder_discovery`
- lifecycle_stage: `holding`
- target_subsystem: `holding_runner_regime`
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
- evidence: `strict_match_count=61`, `ambiguous_match_count=0`, `top_symbols=001740,001820,005680,005950,009150,009470,019180,025560`, `estimated_uplift_pct_sum=272.8800`, `gap=sim-only early stop/loss followed by later runner is not isolated as a dedicated producer`, `required_microstructure_features=ws_orderbook_churn,ofi_qi_persistence,large_trade_absorption,spread_flicker,top_depth_replenishment,holding_flow_cache_freshness`, `required_producer=runner_regime_counterfactual_producer`, `readiness_tier=implementation_workorder_ready`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-05-26.json`, `producers/runner_regime_counterfactual_producer.py`, `hooks/holding/holding_flow_runner_debounce_guard.py`, `tests/producers/test_runner_regime_counterfactual_producer.py`, `tests/stage_hooks/test_holding_flow_runner_debounce_guard.py`
- acceptance_tests: `Producer fixtures reproduce strict runner cases with zero ambiguous assignments.`, `Feature-availability test fails when required microstructure inputs or freshness metadata are missing.`, `Hook contract test proves no broker order submission, exit override, threshold mutation, or safety-bypass authority is exposed.`, `Attribution test reports uplift deltas without changing runtime behavior or enabling live application.`
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
- forbidden_uses: `account guard bypass`, `bot restart`, `broker guard bypass`, `broker order submit`, `cooldown guard bypass`, `emergency stop override`, `entry decision override`, `exit decision override`, `hard stop override`, `order guard bypass`, `position cap release`, `protect stop override`, `provider change`, `quantity guard bypass`, `real order enablement`, `threshold mutation`

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 56. `order_stage_hook_workorder_discovery_stage_hook_plateau_breakdown_exit_arbitration_probe`

- title: Implement stage hook: plateau_breakdown_exit_arbitration_probe
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `stage_hook_workorder_discovery`
- lifecycle_stage: `exit`
- target_subsystem: `exit_plateau_breakdown`
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
- evidence: `strict_match_count=56`, `ambiguous_match_count=0`, `top_symbols=000990,001820,005680,017900,027360,031330,036010,043260`, `estimated_giveback_pct_sum=258.6200`, `gap=sim-only prior modest win followed by late stop/giveback is not isolated as a dedicated producer`, `required_producer=plateau_breakdown_exit_counterfactual_producer`, `readiness_tier=implementation_workorder_ready`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-05-26.json`, `producers/plateau_breakdown_exit_counterfactual_producer.py`, `hooks/exit/plateau_breakdown_exit_arbitration_probe.py`, `tests/producers/test_plateau_breakdown_exit_counterfactual_producer.py`, `tests/stage_hooks/test_plateau_breakdown_exit_arbitration_probe.py`
- acceptance_tests: `Producer fixtures recreate known plateau-breakdown cases with deterministic chronology and zero ambiguous mapping.`, `Hook mapping test proves review-only labels cannot trigger live exit overrides, broker actions, or stop mutations.`, `Disabled-initial-state test confirms runtime application remains off by default.`, `Attribution test quantifies avoided giveback versus baseline without changing any runtime thresholds.`
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
- forbidden_uses: `account guard bypass`, `bot restart`, `broker guard bypass`, `broker order submit`, `cooldown guard bypass`, `emergency stop override`, `entry decision override`, `exit decision override`, `hard stop override`, `order guard bypass`, `position cap release`, `protect stop override`, `provider change`, `quantity guard bypass`, `real order enablement`, `threshold mutation`

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 57. `order_lifecycle_entry_bucket_liquidity_bucket_liquidity_unknown`

- title: LDM entry bucket attribution follow-up: liquidity_bucket=liquidity_unknown
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
- evidence: `workorder_id=entry_bucket_source_quality_5`, `bucket_type=liquidity_bucket`, `bucket_key=liquidity_unknown`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "keep_collecting_post_instrumentation", "source_field_coverage": {"liquidity_bucket": {"coverage_rate": 0.7791, "present_count": 910, "sample_count": 1168, "source_fields": ["runtime_features.liquidity_bucket"]}}, "unknown_reason_counts": {"pre_instrumentation": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 58. `order_lifecycle_entry_bucket_overbought_bucket_overbought_unknown`

- title: LDM entry bucket attribution follow-up: overbought_bucket=overbought_unknown
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
- evidence: `workorder_id=entry_bucket_source_quality_6`, `bucket_type=overbought_bucket`, `bucket_key=overbought_unknown`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "keep_collecting_post_instrumentation", "source_field_coverage": {"overbought_bucket": {"coverage_rate": 0.7162, "present_count": 651, "sample_count": 909, "source_fields": ["runtime_features.overbought_bucket"]}}, "unknown_reason_counts": {"pre_instrumentation": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 59. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_good_e_d8c33947`

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
- evidence: `workorder_id=exit_bucket_source_quality_9`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
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

### 60. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_missed_30bb5c8f`

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

### 61. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_e_71b132b9`

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

### 62. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_missed_bb293be8`

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
- evidence: `workorder_id=exit_bucket_source_quality_7`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
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

### 63. `order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutra_d73738ba`

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
- evidence: `workorder_id=exit_bucket_source_quality_5`, `bucket_type=combo_exit_result`, `bucket_key=source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
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

### 64. `order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_low_missing_30m_2h_kospi_regime_stop_loss`

- title: Swing LDM source field follow-up: mfe_low|missing|30m_2h|kospi_regime_stop_loss|-|-|-
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
- evidence: `section=holding_exit_bucket_attribution`, `bucket_type=holding_exit_bucket_attribution`, `bucket_key=mfe_low|missing|30m_2h|kospi_regime_stop_loss|-|-|-`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
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

### 65. `order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_low_missing_held_missing_kospi_regime_stop_loss`

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
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": ["mae_bucket", "held_bucket", "selection_arm", "sizing_arm", "exit_arm", "sector", "theme"], "runtime_effect": false, "sample_status": "waiting_source_field_sample", "source_field_coverage": {"exit_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.exit_policy"], "present_count": 0, "total_count": 6}, "exit_rule": {"coverage_ratio": 1.0, "paths": ["label_fields.exit_reason"], "present_count": 6, "total_count": 6}, "held_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.held_sec"], "present_count": 0, "total_count": 6}, "mae_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.mae_pct"], "present_count": 0, "total_count": 6}, "market_regime": {"coverage_ratio": 1.0, "paths": ["runtime_features.panic_context", "runtime_features.market_regime"], "present_count": 6, "total_count": 6}, "mfe_bucket": {"coverage_ratio": 1.0, "paths": ["label_fields.mfe_pct"], "present_count": 6, "total_count": 6}, "sector": {"coverage_ratio": 0.0, "paths": ["runtime_features.sector"], "present_count": 0, "total_count": 6}, "selection_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.entry_policy"], "present_count": 0, "total_count": 6}, "sizing_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.sizing_policy"], "present_count": 0, "total_count": 6}, "theme": {"coverage_ratio": 0.0, "paths": ["runtime_features.theme_tags"], "present_count": 0, "total_count": 6}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 3, "bucket_value_held_missing": 1, "bucket_value_missing": 1, "source_field_missing:exit_arm": 1, "source_field_missing:held_bucket": 1, "source_field_missing:mae_bucket": 1, "source_field_missing:sector": 1, "source_field_missing:selection_arm": 1, "source_field_missing:sizing_arm": 1, "source_field_missing:theme": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 66. `order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_neg_missing_30m_2h_kospi_regime_stop_loss`

- title: Swing LDM source field follow-up: mfe_neg|missing|30m_2h|kospi_regime_stop_loss|-|-|-
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
- evidence: `section=holding_exit_bucket_attribution`, `bucket_type=holding_exit_bucket_attribution`, `bucket_key=mfe_neg|missing|30m_2h|kospi_regime_stop_loss|-|-|-`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
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

### 67. `order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_neg_missing_held_missing_kospi_regime_stop_loss`

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
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": ["mae_bucket", "held_bucket", "selection_arm", "sizing_arm", "exit_arm", "sector", "theme"], "runtime_effect": false, "sample_status": "waiting_source_field_sample", "source_field_coverage": {"exit_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.exit_policy"], "present_count": 0, "total_count": 12}, "exit_rule": {"coverage_ratio": 1.0, "paths": ["label_fields.exit_reason"], "present_count": 12, "total_count": 12}, "held_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.held_sec"], "present_count": 0, "total_count": 12}, "mae_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.mae_pct"], "present_count": 0, "total_count": 12}, "market_regime": {"coverage_ratio": 1.0, "paths": ["runtime_features.panic_context", "runtime_features.market_regime"], "present_count": 12, "total_count": 12}, "mfe_bucket": {"coverage_ratio": 1.0, "paths": ["label_fields.mfe_pct"], "present_count": 12, "total_count": 12}, "sector": {"coverage_ratio": 0.0, "paths": ["runtime_features.sector"], "present_count": 0, "total_count": 12}, "selection_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.entry_policy"], "present_count": 0, "total_count": 12}, "sizing_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.sizing_policy"], "present_count": 0, "total_count": 12}, "theme": {"coverage_ratio": 0.0, "paths": ["runtime_features.theme_tags"], "present_count": 0, "total_count": 12}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 3, "bucket_value_held_missing": 1, "bucket_value_missing": 1, "source_field_missing:exit_arm": 1, "source_field_missing:held_bucket": 1, "source_field_missing:mae_bucket": 1, "source_field_missing:sector": 1, "source_field_missing:selection_arm": 1, "source_field_missing:sizing_arm": 1, "source_field_missing:theme": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 68. `order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_neg_missing_lt_30m_kospi_regime_stop_loss`

- title: Swing LDM source field follow-up: mfe_neg|missing|lt_30m|kospi_regime_stop_loss|-|-|-
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
- evidence: `section=holding_exit_bucket_attribution`, `bucket_type=holding_exit_bucket_attribution`, `bucket_key=mfe_neg|missing|lt_30m|kospi_regime_stop_loss|-|-|-`, `reason=source_quality_or_instrumentation_gap`, `implementation_status=implemented_source_quality_contract_waiting_sample`, `decision_authority=swing_ldm_source_only`, `actual_order_submitted=false`
- parity_contract: -
- next_postclose_metric: Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.
- files_likely_touched: `src/engine/swing_lifecycle_decision_matrix.py`, `src/engine/swing_lifecycle_bucket_discovery.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py`
- implementation_status: `implemented_source_quality_contract_waiting_sample`
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": ["mae_bucket", "selection_arm", "sizing_arm", "exit_arm", "sector", "theme"], "runtime_effect": false, "sample_status": "waiting_source_field_sample", "source_field_coverage": {"exit_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.exit_policy"], "present_count": 0, "total_count": 8}, "exit_rule": {"coverage_ratio": 1.0, "paths": ["label_fields.exit_reason"], "present_count": 8, "total_count": 8}, "held_bucket": {"coverage_ratio": 1.0, "paths": ["label_fields.held_sec"], "present_count": 8, "total_count": 8}, "mae_bucket": {"coverage_ratio": 0.0, "paths": ["label_fields.mae_pct"], "present_count": 0, "total_count": 8}, "market_regime": {"coverage_ratio": 1.0, "paths": ["runtime_features.panic_context", "runtime_features.market_regime"], "present_count": 8, "total_count": 8}, "mfe_bucket": {"coverage_ratio": 1.0, "paths": ["label_fields.mfe_pct"], "present_count": 8, "total_count": 8}, "sector": {"coverage_ratio": 0.0, "paths": ["runtime_features.sector"], "present_count": 0, "total_count": 8}, "selection_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.entry_policy"], "present_count": 0, "total_count": 8}, "sizing_arm": {"coverage_ratio": 0.0, "paths": ["runtime_features.sizing_policy"], "present_count": 0, "total_count": 8}, "theme": {"coverage_ratio": 0.0, "paths": ["runtime_features.theme_tags"], "present_count": 0, "total_count": 8}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 3, "bucket_value_missing": 1, "source_field_missing:exit_arm": 1, "source_field_missing:mae_bucket": 1, "source_field_missing:sector": 1, "source_field_missing:selection_arm": 1, "source_field_missing:sizing_arm": 1, "source_field_missing:theme": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 69. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manufacture_of_bas`

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
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 4, "total_count": 4}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 4, "total_count": 4}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 4, "total_count": 4}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 4, "total_count": 4}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 4, "total_count": 4}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 70. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_of_electronic_`

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
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 11, "total_count": 11}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 11, "total_count": 11}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 11, "total_count": 11}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 11, "total_count": 11}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 11, "total_count": 11}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 71. `order_swing_ldm_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_of_other_chemi`

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
- implementation_provenance: `{"allowed_runtime_apply": false, "implementation_type": "swing_ldm_source_field_coverage_contract", "missing_dimensions": [], "runtime_effect": false, "sample_status": "source_fields_available", "source_field_coverage": {"exit_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.exit_policy"], "present_count": 7, "total_count": 7}, "sector": {"coverage_ratio": 1.0, "paths": ["runtime_features.sector"], "present_count": 7, "total_count": 7}, "selection_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.entry_policy"], "present_count": 7, "total_count": 7}, "sizing_arm": {"coverage_ratio": 1.0, "paths": ["runtime_features.sizing_policy"], "present_count": 7, "total_count": 7}, "theme": {"coverage_ratio": 1.0, "paths": ["runtime_features.theme_tags"], "present_count": 7, "total_count": 7}}, "source_report_type": "swing_lifecycle_decision_matrix", "unknown_reason_counts": {"bucket_value_-": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 72. `order_lifecycle_overnight_bucket_combo_overnight_decision_action_action_unknown_status_sell_today_confidence_confidence_unknown_profit_pro`

- title: LDM overnight bucket attribution follow-up: combo_overnight_decision=action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_lt_neg070
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
- evidence: `workorder_id=overnight_bucket_source_quality_2`, `bucket_type=combo_overnight_decision`, `bucket_key=action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_lt_neg070`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 73. `order_lifecycle_overnight_bucket_combo_overnight_decision_action_sell_today_status_sell_today_confidence_confidence_070p_profit_profit_lt_`

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
- evidence: `workorder_id=overnight_bucket_source_quality_1`, `bucket_type=combo_overnight_decision`, `bucket_key=action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 74. `order_lifecycle_overnight_bucket_peak_profit_band_peak_lt_zero`

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

### 75. `order_lifecycle_overnight_bucket_profit_band_profit_lt_neg070`

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
- evidence: `workorder_id=overnight_bucket_source_quality_4`, `bucket_type=profit_band`, `bucket_key=profit_lt_neg070`, `reason=overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_overnight_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 76. `order_lifecycle_scale_in_bucket_ai_score_band_score_63_65`

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

### 77. `order_lifecycle_scale_in_bucket_ai_score_band_score_66_69`

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
- evidence: `workorder_id=scale_in_bucket_source_quality_1`, `bucket_type=ai_score_band`, `bucket_key=score_66_69`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 78. `order_lifecycle_scale_in_bucket_ai_score_band_score_lt60`

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
- evidence: `workorder_id=scale_in_bucket_source_quality_2`, `bucket_type=ai_score_band`, `bucket_key=score_lt60`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 79. `order_lifecycle_scale_in_bucket_ai_score_source_ai_source_unknown`

- title: LDM scale-in bucket attribution follow-up: ai_score_source=ai_source_unknown
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
- evidence: `workorder_id=scale_in_bucket_source_quality_4`, `bucket_type=ai_score_source`, `bucket_key=ai_source_unknown`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.scale_in_bucket_attribution candidates/workorders must remain visible in threshold EV/runtime summary, and postclose verifier must fail if dropped.
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM scale-in bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- implementation_provenance: `{"recommended_resolution": "emit_or_backfill_source_field", "source_field_coverage": {"ai_score_source": {"coverage_rate": 0.0, "present_count": 0, "sample_count": 45601, "source_fields": ["runtime_features.ai_score_source"]}}, "unknown_reason_counts": {"missing_source_field": 1}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 80. `order_lifecycle_scale_in_bucket_arm_avg_down`

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
- evidence: `workorder_id=scale_in_bucket_source_quality_5`, `bucket_type=arm`, `bucket_key=AVG_DOWN`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 81. `order_lifecycle_scale_in_bucket_arm_pyramid`

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
- evidence: `workorder_id=scale_in_bucket_source_quality_6`, `bucket_type=arm`, `bucket_key=PYRAMID`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 82. `order_lifecycle_scale_in_bucket_blocker_namespace_avg_down`

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
- evidence: `workorder_id=scale_in_bucket_source_quality_7`, `bucket_type=blocker_namespace`, `bucket_key=AVG_DOWN`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 83. `order_lifecycle_scale_in_bucket_blocker_namespace_avg_down_only`

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
- evidence: `workorder_id=scale_in_bucket_source_quality_8`, `bucket_type=blocker_namespace`, `bucket_key=AVG_DOWN_ONLY`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 84. `order_lifecycle_scale_in_bucket_blocker_namespace_pyramid`

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

### 85. `order_lifecycle_scale_in_bucket_blocker_reason_profit_not_enough`

- title: LDM scale-in bucket attribution follow-up: blocker_reason=profit_not_enough
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
- evidence: `workorder_id=scale_in_bucket_source_quality_10`, `bucket_type=blocker_reason`, `bucket_key=profit_not_enough`, `reason=scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`, `recommended_route=candidate_recovery_or_relax`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_scale_in_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 86. `order_lifecycle_entry_bucket_chosen_action_buy_now`

- title: LDM entry bucket attribution follow-up: chosen_action=BUY_NOW
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
- evidence: `workorder_id=entry_bucket_source_quality_1`, `bucket_type=chosen_action`, `bucket_key=BUY_NOW`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 87. `order_lifecycle_entry_bucket_chosen_action_no_buy_ai`

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

### 88. `order_lifecycle_entry_bucket_exit_rule_scalp_soft_stop_pct`

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
- evidence: `workorder_id=entry_bucket_source_quality_3`, `bucket_type=exit_rule`, `bucket_key=scalp_soft_stop_pct`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 89. `order_lifecycle_entry_bucket_exit_rule_scalp_trailing_take_profit`

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
- evidence: `workorder_id=entry_bucket_source_quality_4`, `bucket_type=exit_rule`, `bucket_key=scalp_trailing_take_profit`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 90. `order_lifecycle_entry_bucket_overbought_bucket_overbought_ok`

- title: LDM entry bucket attribution follow-up: overbought_bucket=overbought_ok
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
- evidence: `workorder_id=entry_bucket_source_quality_7`, `bucket_type=overbought_bucket`, `bucket_key=overbought_ok`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 91. `order_lifecycle_entry_bucket_score_band_score_60_62`

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
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 92. `order_lifecycle_entry_bucket_score_band_score_70p`

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
- evidence: `workorder_id=entry_bucket_source_quality_8`, `bucket_type=score_band`, `bucket_key=score_70p`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### 93. `order_lifecycle_entry_bucket_source_stage_scalp_entry_action_decision_snapshot`

- title: LDM entry bucket attribution follow-up: source_stage=scalp_entry_action_decision_snapshot
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
- evidence: `workorder_id=entry_bucket_source_quality_10`, `bucket_type=source_stage`, `bucket_key=scalp_entry_action_decision_snapshot`, `reason=bucket_has_edge_but_needs_rolling_or_feature_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
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

### N1. `order_ai_threshold_dominance`

- title: AI threshold dominance
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

### N2. `order_perf_buy_funnel_json_scan`

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

### N3. `order_ai_threshold_miss_ev_recovery`

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

### N4. `order_perf_daily_report_bulk_history`

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

### N5. `order_latency_guard_miss_ev_recovery`

- title: latency guard miss EV recovery
- decision: `attach_existing_family`
- decision_reason: instrumentation/provenance contract is already implemented; keep as report source for the existing family
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `runtime_instrumentation`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `-`
- files_likely_touched: `src/engine/sniper_performance_tuning_report.py`, `src/engine/daily_threshold_cycle_report.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

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

### N11. `order_swing_ofi_qi_stale_or_missing_context`

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

### N12. `order_swing_scale_in_contract_gap_review`

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

### N13. `order_perf_swing_simulation_iteration`

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

### N14. `order_swing_discovery_label_contract_gap_review`

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

### N15. `order_perf_monitor_snapshot_stream_tail`

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

### N16. `order_swing_exit_ofi_qi_smoothing_distribution`

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

### N17. `order_swing_strategy_discovery_source_quality_followup`

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

### N18. `order_perf_final_ensemble_records`

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

### N20. `order_liquidity_gate_miss_ev_recovery`

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

### N21. `order_overbought_gate_miss_ev_recovery`

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

### N22. `order_swing_ai_contract_structured_output_eval`

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

### N23. `order_panic_sell_defense_lifecycle_transition_pack`

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

### N24. `order_overbought_gate_miss_ev_회수_조건_점검`

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

### N25. `order_swing_pattern_lab_deepseek_ofi_qi_smoothing_review`

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

### N26. `order_latency_canary_tag_완화_1축_canary_승인`

- title: latency canary tag 완화 1축 canary 승인
- decision: `defer_evidence`
- decision_reason: single-lab finding; keep as low-confidence backlog until repeated by fresh lab or EV report
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `runtime_instrumentation`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `-`
- files_likely_touched: `src/engine/sniper_performance_tuning_report.py`, `src/engine/daily_threshold_cycle_report.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N27. `order_ai_threshold_miss_ev_회수_조건_점검`

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

### N28. `order_panic_buying_source_quality_market_breadth_micro_coverage`

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

### N29. `order_partial_only_표류_전용_timeout_report_only`

- title: partial-only 표류 전용 timeout report-only
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

### N30. `order_split_entry_rebase_수량_정합성_report_only_감사`

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

### N31. `order_동일_종목_split_entry_soft_stop_재진입_cooldown_report_only`

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

### N32. `order_perf_kiwoom_orders_http_session_review`

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

### N33. `order_perf_config_cache_scope_review`

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

### N34. `order_perf_dashboard_db_pool_review`

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

### N35. `order_partial_fallback_확대_직후_즉시_재평가_report_only`

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

### N36. `order_perf_kiwoom_ws_tick_parse_fastpath`

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

### N37. `order_perf_raw_event_suppression_out_of_scope`

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

- 구현 결과는 `2026-05-27` 이후 postclose `threshold_cycle`, `scalping_pattern_lab_automation`, `threshold_cycle_ev`가 자동으로 다시 읽는다.
- 구현자가 수동으로 threshold 값을 바꾸는 것이 아니라, source/report/provenance를 닫아 다음 calibration이 판단하게 한다.
- 다음 Codex 세션 입력 문구: `none_for_bucket_discovery_classification`

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
