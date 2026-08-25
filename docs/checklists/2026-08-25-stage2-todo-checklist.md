# 2026-08-25 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-08-24` postclose -> `2026-08-25`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0825] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-08-25`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-24.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-24.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 2026-08-25 08:24 KST 조기 검증: PID `9978`에서 daily entry-split baseline은 유효했지만 launcher가 표준 policy enabled key만 dependency로 보아 `KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED=false`로 변조한 계약 불일치를 확인했다. daily baseline을 신규 live 정책으로 승격하지 않고 기존 daily operator contract를 probe dependency로 인정하도록 launcher를 보완했다. 현 PID는 사용자 명시 재기동 전까지 `implemented_but_runtime_not_reflected`로 분류한다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0825] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-08-25`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-08-24.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-08-24.json), [code_improvement_workorder_2026-08-24.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-24.json), [threshold_apply_2026-08-25.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-08-25.json), [threshold_runtime_env_2026-08-25.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-08-25.json), [threshold_runtime_env_verify_2026-08-25.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-08-25.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`3`, forced_scout_with_post_sell_count=`8`, post_sell_join_coverage_pct=`1.565558`, outcome_coverage_state=`partial`, profitable_forced_scout_count=`4`, loss_or_flat_forced_scout_count=`4`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[KakaoManualCustodyReconciliation0825] 카카오 morning/midday custody 수동청산 및 broker receipt 원장 종료` (`Due: 2026-08-25`, `Slot: INTRADAY`, `TimeWindow: 08:00~15:20`, `Track: ScalpingLogic`)
  - Source: [kakao_morning_state.json](/home/ubuntu/KORStockScan/data/runtime/low_price_two_leg/kakao_morning_state.json), [kakao_midday_state.json](/home/ubuntu/KORStockScan/data/runtime/low_price_two_leg/kakao_midday_state.json), [manual_episode_exit_reconciliation.py](/home/ubuntu/KORStockScan/src/trading/order/manual_episode_exit_reconciliation.py), [2026-08-25_kakao_custody backup](/home/ubuntu/KORStockScan/data/runtime/low_price_two_leg/manual_handoff_backups/2026-08-25_kakao_custody)
  - 판정 기준: owner별 20주 전량 수동매도 receipt를 각각 검증해 `kakao_morning`과 `kakao_midday`를 독립적으로 `COMPLETE/0주`에 귀속한다. 종료된 profile만 사용자 지시에 따라 timer를 재활성화하고, custody가 남은 profile은 disabled·inactive를 유지한다.
  - 금지: broker receipt 전 원장 0주 초기화, 두 owner를 하나의 40주 매도 receipt로 합산, target 주문이 열린 상태의 강제 종료, reconciliation 완료 전 해당 profile timer 재활성화를 금지한다.
  - 2026-08-25 07:54 KST FIFO 중간 결과: `kakao_midday`(entry `2026-08-20`)는 과거 target `0043676`/`0043814`의 `kt00007` 체결수량 0과 2026-08-24 수동매도 `0048080` 20주 전량 @ 35,750원을 검증해 `COMPLETE/0주`로 귀속했다. `kakao_morning`은 20주 custody와 timer disabled/inactive를 유지하며 계좌 카카오 잔고도 20주다.
  - 2026-08-25 08:00 KST 운영 반영: 사용자 지시로 `kakao_midday` preflight/live timer만 enabled/active(13:15/13:19)로 재활성화했고, `kakao_morning` timer 두 개는 disabled/inactive를 유지했다.
  - 다음 액션: 현재 상태는 `midday_reconciled_and_scheduled_morning_pending`. `kakao_morning` 20주를 수동 청산한 뒤 별도 exact receipt로 정산하며, 그 전에는 morning timer를 재활성화하지 않는다.

- [ ] `[RuntimeEnvIntradayObserve0825] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-08-25`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-24.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-24.json)
  - 전일 postclose candidate_selected_families=entry_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, post_probe_winner_recovery, scalping_pyramid_quality_gate, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 2026-08-25 09:00 KST transport 보완: 08:08 `analyze_target` 자연 호출에서 5,000ms 예산 대비 HTTP provider 15,238ms가 관측됐다. SDK retry는 0이었으므로 inactivity timeout과 end-to-end deadline의 계약 불일치로 판정해 단일 worker wall-clock deadline과 `wall_deadline_exceeded/provider_future_cancelled/deadline_overshoot_ms` provenance를 구현했다. 현 PID `9978`에는 미반영이며 사용자 명시 재기동 전에는 기존 transport를 유지한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0825] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-08-25`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-08-24.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-24.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0825] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-08-25`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-08-25.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-25.jsonl), [threshold_events_2026-08-25.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-25.jsonl), [observation_source_quality_audit_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-25.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-08-25 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[PostcloseSourceQualityGateReview0825] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-08-25`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-25.json), [threshold_cycle_ev_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-25.json), [code_improvement_workorder_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-25.json), [threshold_cycle_postclose_verification_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-08-25.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0825] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-08-25`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-08-24.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-08-24.json), [threshold_cycle_ev_2026-08-24.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-24.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0825] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-08-25`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-24.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-24.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[MainAIQualitySourceGapRuntimeExecutionReceiptCustodyRepair0825] RuntimeExecutionReceiptCustodyRepair main lifecycle source gap 복구 확인` (`Due: 2026-08-25`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:20`, `Track: ScalpingLogic`)
  - Source: [main_ai_quality_r0_r3_cycle_2026-08-24.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-08-24.json)
  - 판정 기준: workorder `main-ai-gap-5fa7e58712ccad2817ff3580`의 owner=`RuntimeExecutionReceiptCustodyRepair`, reason_codes=`broker_execution_provenance_gap_count=6`를 source-only producer 보완으로 닫는다. 공식 raw execution envelope의 order/execution identity를 합성 없이 검증하고 결손 lifecycle만 제외한 뒤 paired producer를 재검증한다.
  - 완료 조건: official raw execution envelope/order/execution identity is complete for at least one reconciled lifecycle while custody and order authority remain unchanged
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[CodeImprovementWorkorderReview0825] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-08-25`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-08-24.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-08-24.md), [code_improvement_workorder_2026-08-24.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-24.json)
  - 판정 기준: selected_order_count=62와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0825] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-08-25`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-08-24.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-24.json), [runtime_apply_gap_audit_2026-08-24.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-24.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`307`, rollup_required_count=`307`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 306}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[MachineLifecycleTurnoverObjectiveFollowup0825] 위젯·episode 빠른 회전 목적의 미완료 후속 구현 확인` (`Due: 2026-08-25`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~21:40`, `Track: ScalpingLogic`)
  - Source: [machine_microstructure_policy_approval_postclose_2026-08-24.json](/home/ubuntu/KORStockScan/data/report/machine_microstructure_policy_approval/machine_microstructure_policy_approval_postclose_2026-08-24.json), [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py)
  - 판정 기준: 승인 후보 수와 무관하게 `followup_required=true`인 미완료 목적 항목 `machine_lifecycle_turnover_policy_research_v1`(status=`EVIDENCE_ACCUMULATING`, next_action=`continue_exact_date_collection_and_rolling_readiness_review`)의 상태와 상태별 `next_action`을 확인하고 구현 또는 표본수집 경로로 닫는다.
  - 상태별 다음 액션: `IMPLEMENTATION_REQUIRED`는 source-only rolling paired policy 연구를 구현하고, `EVIDENCE_ACCUMULATING`은 exact-date floor 충족까지 수집·재검증한다. `CANDIDATE_QUEUE_HANDOFF|COMPLETE`는 closed 상태이므로 report에서 제외되고 다음 refresh에서 builder-owned 항목이 제거된다.
  - 권한 경계: 이 POSTCLOSE 후속 항목은 source-only 구현·검증 작업이며 runtime env, 실주문, target/timeout/cooldown/cap, threshold, provider/bot, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[AutomationTriggerDecisionSummary0825] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-08-25`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-08-24.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-08-24.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`14`, run_count=`9`, skip_count=`0`, source_missing_count=`8`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:8, source_missing_or_unreadable:8, disabled_by_runtime_policy:5, upstream_artifact_newer:1, upstream_drift_signal:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## 사용자 지시 운영 확인

- [ ] `[LowPriceTwoLegNewProfilesRuntimeObserve0825] 신규 저가 2-leg profile 5종 exact-date 설치·기동 및 귀속 확인` (`Due: 2026-08-25`, `Slot: PREOPEN`, `TimeWindow: 09:25~10:55`, `Track: ScalpingLogic`)
  - Source: [low_price_two_leg_policy_2026-08-25.json](/home/ubuntu/KORStockScan/data/threshold_cycle/low_price_two_leg/applied/low_price_two_leg_policy_2026-08-25.json), [low_price_two_leg_expanded_profile_evidence_2026-08-24.json](/home/ubuntu/KORStockScan/data/config/low_price_two_leg_expanded_profile_evidence_2026-08-24.json), [install_low_price_two_leg_systemd.sh](/home/ubuntu/KORStockScan/deploy/install_low_price_two_leg_systemd.sh)
  - 판정 기준: `sk_eternix_late_morning`, `mirae_asset_late_morning`, `kepco_morning`, `nhn_morning`, `nhn_late_morning`의 preflight/live timer가 enabled+waiting이고 설치본 hash가 repo unit과 일치하며, exact-date policy 40-profile generation과 profile별 authority가 일치해야 한다. 예약된 live service는 preflight ready 이후 해당 시간창에서만 자연 기동하며 수동 조기 실행하지 않는다.
  - 금지: main/widget/다른 episode의 주문·보유·청산 귀속 혼합, preflight 우회, 수량·no-stop custody·SOR route·broker guard 변경, source-only evidence만으로 임의 profile 추가를 금지한다.
  - 다음 액션: profile별 `timer_waiting`, `preflight_ready`, `live_started`, `no_trade`, `held`, `complete`, `blocked`를 구분하고 broker order/leg/target lineage를 확인한다.






## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
