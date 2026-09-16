# 2026-09-17 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime 변경은 사용자 명시 지시가 있을 때만 기존 `bounded_tunable` 단일 축에 한해 허용한다. fresh/conflict-free source, 유효 effective price, 단일 blocker 인과, same-stage owner 비충돌, before/after·PID/env provenance·rollback·즉시 attribution을 모두 남긴다. hard safety, stale/conflict, price freshness, broker/account/order/quantity/cooldown, provider, bot, cap, 요청수량은 변경하거나 우회하지 않는다.
- 튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-05`, `clean_tuning_baseline_ts_kst=2026-06-05T00:00:00+09:00`이다. 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 보고 EV/rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다.
- Baseline 이후 raw source-quality contract 결손은 날짜 전체 차단이 아니라 결손 row/window를 `raw_row_exclusion`으로 제외하는 것이 기본이다. 전체 block은 preflight missing/invalid, row/window exclusion 실패, 또는 결손을 안정적으로 특정할 수 없는 high-volume no-contract 상황에만 사용한다.
- 장중과 장후에는 `observation_source_quality_audit --write` 또는 최신 artifact로 raw source-quality를 반복 확인한다. Hard contract gap은 결손 row/window 제외 또는 `source_quality_blocked` 없이는 튜닝 입력에 들어갈 수 없고, unknown-token warning은 hard block이 아니더라도 code-improvement workorder handoff 확인 대상이다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-09-16", "sources": {"automation_chain_trigger_decision": {"sha256": "4806e86a7fd2833381f9ae4b6fe99e3d662b443ad1748737ccfcafdd75549f45"}, "code_improvement_workorder": {"sha256": "e83fae0a61c730ff8688339015b1c2c24d76e497978c7e78dfbc520679ea7d7b"}, "conversion_lane": {"sha256": "f24fc21e2892adeb6ee6f9302eda52723051b418d7c928bc278d010de6be1eda"}, "entry_recheck_drought_controller": {"sha256": "067fe0492d7121c782b7d6aade2f7eab71f17a7247c3167393bd6cc3ef3ab146"}, "key_lineage_ledger": {"sha256": "c003ee41b4adc018d4ab94d22d28bf6ede2dc563a0a0344fcf256a507cc4d8df"}, "low_price_two_leg_expanded_candidate_research": {"sha256": "06142aa4e6679a5017fe5ed4985fb8f3423f9facf9e82bcbdab71c384e8eb066"}, "low_price_two_leg_tuning": {"sha256": "b42f9fab655a015f84abf0f39d642e0fbafa982eee2ec309d8fd75932efa041a"}, "machine_entry_timing_tuning": {"sha256": "bddf2fb8d58a7f0ff10fe7cc4937eebe3ee75035d7f56da20475c4af55926568"}, "machine_microstructure_attribution": {"sha256": "d369a02b2bd7496b01fd8854e0353cf331e018b05e467d1f7f0cd57467c71e26"}, "machine_microstructure_policy_approval": {"sha256": "7b26f98cd9df31e287ab50f1d5a6257d6a8e827d9e99d9823c2ee24652e7154e"}, "main_ai_quality_r0_r3": {"sha256": "ea9ca46c2af77d84963eb8944ab398564d6e663812a828c65bd6485d283c8c99"}, "postclose_recommendation_dispositions": {"sha256": null}, "preopen_apply_plan": {"sha256": "8951d22727e134912288ef61f2c447d80b1b7b85c02cfd41fbae3c4fe01b5f16"}, "preopen_pid_verification": {"sha256": "5189e884cd6ab7f143022cdd897b49f1ef514fb7854f8a249b9c94d80dd7f54d"}, "preopen_runtime_manifest": {"sha256": "adc678c77d9cbc7f1776a86ed8f4063e44956cd6b239a4865a12e4e618391299"}, "rising_missed_scout_workorder": {"sha256": "128c601bdab17ca8e68480208a90e4742919788665950a1e9a4c1424ae051094"}, "runtime_apply_gap_audit": {"sha256": "314f19ea2c2ff8adf58d62308dcdee2b3fa5eda6660ed6090f19fb13ace52a52"}, "samsung_machine_entry_tuning": {"sha256": "8aaa4c53634d296230ca56892d48794ebbf311574ce7c26a675e40408e0cc20c"}, "threshold_cycle_ev": {"sha256": "71feb0996b4aa89d55938838b741efafc2e5ab6bf330f516b0b64d9eb61c8a2f"}, "tuning_performance_control_tower": {"sha256": "12a675fab170ea197b8a3493e2b88320da12451bdd09b3fcdb04a5debfc751d7"}, "widget_advisory_calibration": {"sha256": "69935f3a2a296a2849a1692f7a7532d7bf7febc98496a98ee4e98436010e9a31"}, "widget_auto_trade_policy_calibration": {"sha256": "e45cd09f5713e4703e457b39e18681b608a738750be80d61854a955e04986384"}, "widget_collector_expansion_recommendation": {"sha256": null}, "widget_symbol_runtime_policy_apply": {"sha256": null}, "widget_symbol_signal_policy_research": {"sha256": null}}} -->
<!-- POSTCLOSE_RECOMMENDATION_INTAKE_START -->
## 추천 전수 전달 대사

- source-date: `2026-09-16`; status: `waiting_sources`
- native rows SHA256: `5b6beed3ee6b97c7ad3f9f0e77bde3b0cb751d2860a95bdb2d943b028962d131`
- counts: `{"already_implemented_verified_eligible": 0, "already_implemented_verified_nonrequest": 0, "blocked_external_dependency": 0, "blocked_external_dependency_nonrequest": 0, "blocked_missing_evidence": 7, "blocked_missing_evidence_nonrequest": 3, "deferred": 13, "eligible_actionable_open": 13, "eligible_runtime_effect_false_total": 20, "implement_now_unaccounted_count": 0, "implementation_requested_total": 20, "implemented_pass1": 0, "implemented_pass2": 0, "intake_total": 62, "intake_unaccounted_count": 0, "invalid_or_missing_authority_nonrequest": 0, "invalid_or_missing_authority_total": 0, "nonimplementation_total": 42, "observed_no_patch": 26, "rejected": 0, "user_authority_nonrequest": 0, "user_authority_total": 0}`
- dispositions: `{"blocked_missing_evidence": 10, "deferred": 13, "eligible_actionable_open": 13, "observed_no_patch": 26}`
- 운영 terminal, 구현 fixed-point, PREOPEN 선택, PID 소비, 경제성은 별도 상태다.

| Owner | Native recommendation dispositions |
| --- | --- |
| low_price_two_leg_expanded_candidate_research | `{"blocked_missing_evidence": 3}` |
| machine_microstructure_attribution | `{"observed_no_patch": 1}` |
| main | `{"blocked_missing_evidence": 7, "deferred": 13, "eligible_actionable_open": 13, "observed_no_patch": 25}` |
<!-- POSTCLOSE_RECOMMENDATION_INTAKE_END -->

## 자동 생성 체크리스트 (`2026-09-16` postclose -> `2026-09-17`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (07:45~09:00)

- [ ] `[MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0917] micro observer 저장공간·연속수집 source gap 복구 확인` (`Due: 2026-09-17`, `Slot: PREOPEN`, `TimeWindow: 08:40~08:45`, `Track: RuntimeStability`)
  - Source: [main_ai_quality_r0_r3_cycle_2026-09-16.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-09-16.json)
  - 판정 기준: workorder `main-ai-gap-f91651606dcb7d318033a46a`의 owner=`MicroReversionForwardCollectorContinuity`, reason_codes=`row_exclusion_required, past_market_row_missing=0`를 source-only producer 보완으로 닫는다. 장전 free bytes가 writer low-disk watermark를 충분히 상회하는지 확인하고, 부족하면 실주문과 무관한 closed-date verified compression만 실행한 뒤 observer canary를 재검증한다.
  - 완료 조건: exact-date canary remains pass or row-exclusion-only through close; later clean windows continue collecting; provider replay remains held until queue-loss scope has an exact exclusion receipt or the next clean date
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[ThresholdEnvAutoApplyPreopen0917] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-09-17`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-16.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-16.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0917] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-09-17`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-09-16.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-09-16.json), [code_improvement_workorder_2026-09-16.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-16.json), [threshold_apply_2026-09-17.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-09-17.json), [threshold_runtime_env_2026-09-17.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-09-17.json), [threshold_runtime_env_verify_2026-09-17.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-09-17.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`2`, forced_scout_with_post_sell_count=`0`, post_sell_join_coverage_pct=`0`, outcome_coverage_state=`no_closed_outcome`, profitable_forced_scout_count=`0`, loss_or_flat_forced_scout_count=`0`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0917] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-09-17`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-16.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-16.json)
  - 전일 postclose candidate_selected_families=entry_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, post_probe_winner_recovery, entry_opportunity_recheck_runtime, holding_decision_context_v1, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0917] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-09-17`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-09-16.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-16.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0917] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-09-17`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-09-17.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-09-17.jsonl), [threshold_events_2026-09-17.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-09-17.jsonl), [observation_source_quality_audit_2026-09-17.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-17.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-09-17 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (16:25~21:55)

- [ ] `[ThresholdDailyEVReport0917] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-09-17`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-09-16.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-09-16.json), [threshold_cycle_ev_2026-09-16.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-16.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0917] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-09-17`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-16.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-16.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[MainAIQualitySourceGapMainAIMicroExactEconomicIntersectionRepair0917] main AI micro exact 경제성 교집합 source gap 복구 확인` (`Due: 2026-09-17`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:20`, `Track: ScalpingLogic`)
  - Source: [main_ai_quality_r0_r3_cycle_2026-09-16.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-09-16.json)
  - 판정 기준: workorder `main-ai-gap-2c9b90cd801e400445453bfc`의 owner=`MainAIMicroExactEconomicIntersectionRepair`, reason_codes=`paired_decision_quality_eligible=2, net_economic_eligible=0, current_exact_source_eligible=0`를 source-only producer 보완으로 닫는다. 동일 primary trace의 paired/mature/sidecar/net-economic 교집합과 bridge/source-bundle parent census를 대사한다. 비용·원천 결손을 0 또는 대체 parent로 보간하지 않는다.
  - 완료 조건: bridge current exact trace census equals the source-bundle eligible parent census; a parent is materialized only when the same primary trace is paired, mature, sidecar-valid, and net-economic eligible
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[MainAIQualitySourceGapRuntimeExecutionReceiptCustodyRepair0917] RuntimeExecutionReceiptCustodyRepair main lifecycle source gap 복구 확인` (`Due: 2026-09-17`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:20`, `Track: ScalpingLogic`)
  - Source: [main_ai_quality_r0_r3_cycle_2026-09-16.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-09-16.json)
  - 판정 기준: workorder `main-ai-gap-28d6cb25c3fa721589278e76`의 owner=`RuntimeExecutionReceiptCustodyRepair`, reason_codes=`pipeline_lifecycle_instrumentation_gap_count=3, real_submitted_lifecycle_count=2, broker_execution_unique_count=1`를 source-only producer 보완으로 닫는다. 공식 raw execution envelope의 order/execution identity를 합성 없이 검증하고 결손 lifecycle만 제외한 뒤 paired producer를 재검증한다.
  - 완료 조건: official raw execution envelope/order/execution identity is complete for each repair-required lifecycle or the affected row remains explicitly excluded; custody and order authority remain unchanged
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[CodeImprovementWorkorderReview0917] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-09-17`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-09-16.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-09-16.md), [code_improvement_workorder_2026-09-16.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-16.json)
  - 판정 기준: selected_order_count=31와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[MachineLifecycleTurnoverObjectiveFollowup0917] 위젯·episode 빠른 회전 목적의 미완료 후속 구현 확인` (`Due: 2026-09-17`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~21:40`, `Track: ScalpingLogic`)
  - Source: [machine_microstructure_policy_approval_postclose_2026-09-16.json](/home/ubuntu/KORStockScan/data/report/machine_microstructure_policy_approval/machine_microstructure_policy_approval_postclose_2026-09-16.json), [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py)
  - 판정 기준: 승인 후보 수와 무관하게 `followup_required=true`인 미완료 목적 항목 `machine_lifecycle_turnover_policy_research_v1`(status=`EVIDENCE_ACCUMULATING`, next_action=`quarantine_current_source_date_and_continue_next_exact_date_collection`)의 상태와 상태별 `next_action`을 확인하고 구현 또는 표본수집 경로로 닫는다.
  - 상태별 다음 액션: `IMPLEMENTATION_REQUIRED`는 source-only rolling paired policy 연구를 구현하고, `EVIDENCE_ACCUMULATING`은 exact-date floor 충족까지 수집·재검증한다. `CANDIDATE_QUEUE_HANDOFF|COMPLETE`는 closed 상태이므로 report에서 제외되고 다음 refresh에서 builder-owned 항목이 제거된다.
  - 권한 경계: 이 POSTCLOSE 후속 항목은 source-only 구현·검증 작업이며 runtime env, 실주문, target/timeout/cooldown/cap, threshold, provider/bot, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[AutomationTriggerDecisionSummary0917] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-09-17`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-09-16.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-09-16.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`14`, run_count=`4`, skip_count=`2`, source_missing_count=`3`, force_override_count=`0`, run_steps_sample=`observation_source_quality_audit, pattern_lab_propagation_audit, runtime_apply_gap_audit, workorder_branch`, skip_steps_sample=`pattern_lab_currentness_audit, pattern_lab_ai_review`, top_reasons=`disabled_by_runtime_policy:8, source_missing_or_unreadable:3, fresh_outputs_no_trigger:2, upstream_artifact_newer:2`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

- [ ] `[PostcloseSourceQualityGateReview0917] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-09-17`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-09-17.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-17.json), [threshold_cycle_ev_2026-09-17.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-17.json), [code_improvement_workorder_2026-09-17.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-17.json), [threshold_cycle_postclose_verification_2026-09-17.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-09-17.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## 사용자 승인 통합 구현 후속

- [ ] `[KiwoomCommonHealthOpportunityCostAcceptance0917] 공통 health 부분 릴리스·미진입 전체 모집단 구현 잔여 확인` (`Due: 2026-09-17`, `Slot: INTRADAY`, `TimeWindow: 07:35~20:00`, `Track: RuntimeStability`)
  - Source: [통합 계획](../proposals/entry-opportunity-cost-full-population-tuning-implementation-plan-2026-09-17.md), [부분 구현 리뷰](../audit-reports/2026-09-17-common-health-opportunity-cost-scoped-implementation.md).
  - 이번 실행: 01시대 WS/common quote clock·quiet observation·observer 원 나이·#74→#82 all-VETO gate·중복 learning count targeted845건 검증. 06시대 common natural/paired 전수 소비·현재 incumbent 비교·양수 순 EV/paired 개선 v2·exact-parent 자동 발행과 verifier 보완, targeted736건 통과. existing selected release를 보존한 managed release integration을 사용한다. PID/자연 policy/실체결 경제성 미관측.
  - Acceptance: exact-date PREOPEN→07:55 selected release/PID·원 WS0B/0D/inline BBO receipt를 검증하고 U0–U12 ledger의 미완료 구현을 별도로 닫는다. 부분 H 배포를 전체 opportunity-cost 자동 선정·수익 완료로 표시하지 않는다.
  - 잔여: direct REST/widget/episode 전수 parity, single-flight/scheduler budget, U7 hierarchy 전체 population paired 선정, U8 CAUTION/INSUFFICIENT router, U9 price/quantity four-arm, U10 독립 owner, U11 family auto handoff. 신규 producer/수동 env/주문/owner·cap·hard-safety 변경 금지. 실제 기동 시 broker/custody·중복 PID·WS first-data와 dated policy receipt를 보존한다.

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
