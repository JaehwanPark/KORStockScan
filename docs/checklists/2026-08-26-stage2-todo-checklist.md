# 2026-08-26 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-08-25` postclose -> `2026-08-26`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0826] micro observer 저장공간·연속수집 source gap 복구 확인` (`Due: 2026-08-26`, `Slot: PREOPEN`, `TimeWindow: 08:40~08:45`, `Track: RuntimeStability`)
  - Source: [main_ai_quality_r0_r3_cycle_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-08-25.json)
  - 판정 기준: 2026-08-26 07:00 이전 source-only 재검증에서 갱신된 workorder `main-ai-gap-ba0d324d9d48bad7b39f8b1f`의 owner=`MicroReversionForwardCollectorContinuity`, reason_codes=`stop_required, past_market_row_missing=104`를 닫는다. 현재 exact canary stop reason은 `producer_callback_latency_p99_exceeded:2.073243>2.000000`과 그 prior auto-stop이며 queue full/drop은 모두 0이다. 장전 free bytes가 writer low-disk watermark를 충분히 상회하는지 확인하고, latency source owner를 보완한 뒤 신규 clean-date canary를 재검증한다.
  - 완료 조건: exact-date canary remains pass or row-exclusion-only through close; later clean windows continue collecting; provider replay remains held until queue-loss scope
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[ThresholdEnvAutoApplyPreopen0826] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-08-26`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-25.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0826] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-08-26`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-08-25.json), [code_improvement_workorder_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-25.json), [threshold_apply_2026-08-26.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-08-26.json), [threshold_runtime_env_2026-08-26.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-08-26.json), [threshold_runtime_env_verify_2026-08-26.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-08-26.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`4`, forced_scout_with_post_sell_count=`8`, post_sell_join_coverage_pct=`1.980198`, outcome_coverage_state=`partial`, profitable_forced_scout_count=`7`, loss_or_flat_forced_scout_count=`1`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0826] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-08-26`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-25.json)
  - 전일 postclose candidate_selected_families=score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, post_probe_winner_recovery, scalping_pyramid_quality_gate, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0826] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-08-26`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-25.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0826] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-08-26`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-08-26.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-26.jsonl), [threshold_events_2026-08-26.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-26.jsonl), [observation_source_quality_audit_2026-08-26.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-26.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-08-26 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[PostcloseSourceQualityGateReview0826] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-08-26`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-08-26.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-26.json), [threshold_cycle_ev_2026-08-26.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-26.json), [code_improvement_workorder_2026-08-26.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-26.json), [threshold_cycle_postclose_verification_2026-08-26.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-08-26.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0826] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-08-26`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-08-25.json), [threshold_cycle_ev_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-25.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0826] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-08-26`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-25.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0826] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-08-26`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-08-25.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-08-25.md), [code_improvement_workorder_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-25.json)
  - 판정 기준: selected_order_count=68와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0826] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-08-26`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-25.json), [runtime_apply_gap_audit_2026-08-25.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-25.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`390`, rollup_required_count=`390`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 389}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[MachineLifecycleTurnoverObjectiveFollowup0826] 위젯·episode 빠른 회전 목적의 미완료 후속 구현 확인` (`Due: 2026-08-26`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~21:40`, `Track: ScalpingLogic`)
  - Source: [machine_microstructure_policy_approval_postclose_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/machine_microstructure_policy_approval/machine_microstructure_policy_approval_postclose_2026-08-25.json), [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py)
  - 판정 기준: 승인 후보 수와 무관하게 `followup_required=true`인 미완료 목적 항목 `machine_lifecycle_turnover_policy_research_v1`(status=`EVIDENCE_ACCUMULATING`, next_action=`quarantine_current_source_date_and_continue_next_exact_date_collection`)의 상태와 상태별 `next_action`을 확인하고 구현 또는 표본수집 경로로 닫는다.
  - 상태별 다음 액션: `IMPLEMENTATION_REQUIRED`는 source-only rolling paired policy 연구를 구현하고, `EVIDENCE_ACCUMULATING`은 exact-date floor 충족까지 수집·재검증한다. `CANDIDATE_QUEUE_HANDOFF|COMPLETE`는 closed 상태이므로 report에서 제외되고 다음 refresh에서 builder-owned 항목이 제거된다.
  - 권한 경계: 이 POSTCLOSE 후속 항목은 source-only 구현·검증 작업이며 runtime env, 실주문, target/timeout/cooldown/cap, threshold, provider/bot, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[AutomationTriggerDecisionSummary0826] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-08-26`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-08-25.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`14`, run_count=`9`, skip_count=`0`, source_missing_count=`4`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:8, disabled_by_runtime_policy:5, upstream_drift_signal:5, source_missing_or_unreadable:4, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## 결함 해소 후속 체크리스트

- [x] `[MainAIQualityExactPreparedSourcePool0826] R2/P2 exact prepared request census와 단일 source-pool materialization 병목 해소` (`Due: 2026-08-26`, `Slot: OFFHOURS`, `TimeWindow: 00:00~23:59`, `Track: ScalpingLogic`)
  - Source: [ai_quality_bridge.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/ai_quality_bridge.py), [ai_decision_quality.py](/home/ubuntu/KORStockScan/src/engine/scalping/ai_decision_quality.py), [ai_quality_cycle.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/ai_quality_cycle.py)
  - 구현 범위: scheduled bridge는 exact prepared request trace census와 target/path/outer SHA/count를 결속하고, raw/config/window/coverage/hash/partition census를 검증한 재구축 가능 SQLite cache를 통해 A/B/C가 한 번 검증된 동일 source pool을 소비한다. Current materializer는 external bridge가 canonical sidecar status와 실제 sidecar 검증으로 증명한 ask-depletion source gap만 row-local 제외하고 fabricated exclusion은 계속 전역 차단하며, B→C의 `response_schema_application`을 명시적 prompt/response-contract 단일축으로 허용한다. Scheduled historical Provider backfill은 reviewed 30-calendar-day floor의 미완료 날짜를 oldest-first로 exact A/B/C 한 parent씩 처리하되 current slot을 남기고, cycle/direct leaf 공통 prior physical-ledger/checkpoint gate가 complete skip, capacity-partial exact resume, terminal·orphan permanent no-call을 보장해야 완료로 닫는다. 2026-08-25 재검증은 prepared 160건, source row 2건, materialization 2건/A·B·C request 6건, Provider 0 call로 통과했다.
  - 권한 경계: source-only materialization과 평가 입력 복구가 주 목적이다. reviewed cap·floor·prior-ledger gate를 모두 통과한 scheduled bounded replay 외의 수동·무제한 Provider 실행 권한과 runtime/order/policy apply, bot restart 권한은 열지 않는다.

- [ ] `[MainSellReceiptCustodyNaturalAcceptance0827] SELL pre-call custody 적용 후 자연 체결·부분체결·취소·재기동 acceptance 확인` (`Due: 2026-08-27`, `Slot: PREOPEN`, `TimeWindow: 07:50~20:00`, `Track: RuntimeStability`)
  - Source: [sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [main_lifecycle_paired.py](/home/ubuntu/KORStockScan/src/engine/scalping/main_lifecycle_paired.py)
  - 판정 기준: no-defect review와 targeted validation을 통과한 수정본이 로컬 commit/deploy까지 완료되어 `KORSTOCKSCAN_RUNTIME_SOURCE_DIRTY=false`로 기동 가능한 상태인지 먼저 확인한다. 그 조건을 충족한 뒤 기존 `07:55` cron이 자연 기동한 신규 표본에서 broker 호출 전 DB owner CAS와 fsynced exact pending journal이 존재하고, WS-before-HTTP·부분체결 잔량·취소·발생 시 재기동에서 동일 generation 재주문이 0건이며 terminal successor 영속화 뒤에만 interlock이 해제되는지 확인한다. acceptance를 위해 별도 수동 재기동이나 주문을 만들지 않는다.
  - 완료 조건: 신규 자연 lifecycle에서 diagnostic recovery 없이 entry/holding/final exit exact join이 생성되고 `FINAL_EXIT_RECONCILED`가 실거래 closed cycle과 수량·주문번호 기준으로 일치한다.
  - 권한 경계: 현재 dirty working tree 또는 미커밋 수정본의 `07:55` 기동은 이 acceptance의 적용 증거가 아니다. 이 항목 자체는 commit/push/deploy, 봇 재기동, 실주문·취소, provider/threshold/cap/hard-safety 변경 권한을 부여하지 않는다.

- [ ] `[PipelineReportDurableArchiveOwner0827] 무한 증가 raw/report 전체 producer retention·archive·restore 계약 확정` (`Due: 2026-08-27`, `Slot: POSTCLOSE`, `TimeWindow: 20:00~21:00`, `Track: RuntimeStability`)
  - Source: [storage_maintenance.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/storage_maintenance.py), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: `data/pipeline_events`와 `data/report`의 전체 producer/consumer/current-window manifest를 만들고, closed-date verified gzip, durable archive destination, content hash, restore manifest, consumer 보호기간을 결속한다.
  - 금지: durable archive destination과 restore 검증이 없거나 active/current consumer window가 확인되지 않은 상태에서 raw/report를 삭제하지 않는다.
  - 다음 액션: archive target과 보존기간이 확정되면 source-only canary로 압축·복원·hash 검증 후에만 local deletion 후보를 생성한다.

- [ ] `[IPOListingDaySellReceiptCustodyIsolation0827] IPO 독립 봇의 HTTP 성공 기반 synthetic fill/PnL/close 결함 격리·보완` (`Due: 2026-08-27`, `Slot: OFFHOURS`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [ipo_listing_day_runner.py](/home/ubuntu/KORStockScan/src/engine/ipo_listing_day_runner.py)
  - 판정 기준: code=0 응답만으로 fill·PnL·position close를 합성하지 않고 official execution receipt와 immutable order identity를 결속하며, 별도 main lifecycle/R3 비유입 계약을 회귀검증한다.
  - 금지: 결함 해소와 receipt acceptance 전까지 IPO 독립 봇을 기동하거나 실주문 권한을 열지 않는다.

- [ ] `[MainBuyCancellationReceiptCustody0827] 일반 BUY 취소 응답·부분체결·잔고의 exact custody 보완` (`Due: 2026-08-27`, `Slot: OFFHOURS`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py), [sniper_s15_fast_track.py](/home/ubuntu/KORStockScan/src/engine/sniper_s15_fast_track.py), [sniper_trade_utils.py](/home/ubuntu/KORStockScan/src/engine/sniper_trade_utils.py)
  - 판정 기준: `process_order_cancellation`은 non-dict/truthy 응답이나 오류 메시지를 성공으로 간주하지 않고 explicit broker `code=0` ACK를 요구한다. ACK 뒤에도 exact BUY execution receipt, 원주문 terminal 상태, KRX/NXT 전체 잔고를 대사해 부분체결 수량만 immutable owner에 결속한 뒤 DB/memory를 `HOLDING` 또는 terminal entry state로 전환한다. Direct-call census는 late-parent replacement BUY, S15 recovery/no-fill/partial-fill BUY, entry timeout/SOR retry/reprice bundle, pending-add/scale-in, generic cancellation을 각각 독립 crash boundary와 terminal-proof acceptance로 닫는다.
  - 금지: `취소가능수량|잔고|주문없음` 문자열, 단일 venue 잔고, 추정 수량만으로 phantom holding·부분체결 완료를 만들거나 신규 주문 권한을 열지 않는다. 이 항목은 현재 main SELL/R3 수정 범위와 분리하며 별도 구현·리뷰 전에는 완료 처리하지 않는다.





## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
