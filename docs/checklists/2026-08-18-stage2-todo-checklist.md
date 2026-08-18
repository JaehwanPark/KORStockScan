# 2026-08-18 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-08-14` postclose -> `2026-08-18`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[SniperStartupBindingRecovery0818] 스나이퍼 dependency binding 기동 장애 복구` (`Due: 2026-08-18`, `Slot: PREOPEN`, `TimeWindow: 07:55~08:45`, `Track: RuntimeStability`)
  - Source: [kiwoom_sniper_v2.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py), [process_health.py](/home/ubuntu/KORStockScan/src/engine/error_detectors/process_health.py), [bot heartbeat](/home/ubuntu/KORStockScan/tmp/error_detector_heartbeat.json)
  - 판정: execution-only fast-state callback 두 개가 state-handler binding에도 중복 전달되어 스나이퍼 루프가 첫 iteration에서 종료됐다. state owner의 인자 집합에서 제거하고, 루프 종료 시 `alive=false`를 기록하며 detector가 이를 즉시 FAIL로 처리한다.
  - 권한 경계: dependency wiring과 장애 탐지 복구만 수행하며 진입·청산 판단, threshold, provider, 주문가·수량, broker/account/order/cooldown, hard safety를 변경하지 않는다.

- [x] `[WidgetEvaluationPersistentCatchupRepair0818] widget evaluation persistent timer source-date 불일치 복구` (`Due: 2026-08-18`, `Slot: PREOPEN`, `TimeWindow: 07:10~08:30`, `Track: RuntimeStability`)
  - Source: [widget evaluation wrapper](/home/ubuntu/KORStockScan/deploy/run_widget_evaluation.sh), [systemd service](/home/ubuntu/KORStockScan/deploy/systemd/korstockscan-samsung-widget-evaluation.service), [runtime policy producer](/home/ubuntu/KORStockScan/src/engine/monitoring/widget_symbol_runtime_policy.py)
  - 판정: persistent timer의 장전 catch-up에서 research는 완료 영업일, runtime-policy는 당일을 선택해 source JSON이 불일치했다. wrapper가 completed KRX date를 한 번 확정해 네 단계에 명시 전달하도록 단일 owner로 통합한다.
  - 권한 경계: report/policy 생성 복구만 수행하며 실주문, account/order/token, provider, bot, threshold, quantity, cap, hard-safety 권한을 변경하지 않는다.

- [ ] `[ThresholdEnvAutoApplyPreopen0818] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-08-18`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-14.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0818] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-08-18`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-08-14.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-08-14.json), [code_improvement_workorder_2026-08-14.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-14.json), [threshold_apply_2026-08-18.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-08-18.json), [threshold_runtime_env_2026-08-18.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-08-18.json), [threshold_runtime_env_verify_2026-08-18.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-08-18.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`3`, forced_scout_with_post_sell_count=`5`, post_sell_join_coverage_pct=`1.091703`, outcome_coverage_state=`partial`, profitable_forced_scout_count=`4`, loss_or_flat_forced_scout_count=`1`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [x] `[KiwoomWsReconnectResubscriptionRecovery0818] 09:05 WebSocket 단절 후 재구독 readiness 순서 복구` (`Due: 2026-08-18`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:15`, `Track: RuntimeStability`)
  - Source: [kiwoom_websocket.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py), [kiwoom_websocket_error.log](/home/ubuntu/KORStockScan/logs/kiwoom_websocket_error.log), [Kiwoom API data contract](/home/ubuntu/KORStockScan/docs/kiwoom-api-data-contract.md)
  - 판정: `09:05:07` code `1006` 단절 한 건이 동시 REG 3건·REMOVE 7건의 `no close frame received or sent` fan-out을 만들었다. `09:05:11` LOGIN은 복구됐으나 기존 종목 재구독이 unset `_session_ready`를 10초 기다리다 실패하고 스캐너 재부착에 의존했다. LOGIN ACK·`00`·`0s` 등록 후 readiness를 공개한 다음 기존 symbol inventory를 `refresh=1` REG로 복원하도록 순서를 고정했다.
  - 검증/권한: 공식 upstream commit·문서·SDK packet/client를 재확인했고 reconnect bootstrap 회귀 테스트를 추가했다. 이 변경은 연결 lifecycle 복구만 소유하며 진입·청산, provider, threshold, 주문가·수량, broker/account/order/cooldown, hard safety를 변경하지 않는다.
  - PID 귀속: 현재 PID `12158`은 스캐너 재부착으로 실시간 수신이 복구된 기존 코드이며, 본 readiness 순서 보완은 코드 재기동 전까지 미반영이다. 현재 장애가 소멸된 상태에서 장중 재기동을 자동 수행하지 않고 다음 승인된 우아한 재기동에 반영한다.

- [x] `[SniperAwareDatetimeElapsedRecovery0818] 체결 직후 aware/naive datetime 혼용으로 종료된 스나이퍼 복구` (`Due: 2026-08-18`, `Slot: INTRADAY`, `TimeWindow: 09:51~10:10`, `Track: RuntimeStability`)
  - Source: [sniper_scale_in.py](/home/ubuntu/KORStockScan/src/engine/sniper_scale_in.py), [kiwoom_sniper_v2.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py), [kiwoom_sniper_v2_error.log](/home/ubuntu/KORStockScan/logs/kiwoom_sniper_v2_error.log)
  - 판정: `322000` 1주 체결 영수증이 KST offset-aware `holding_started_at`을 저장한 직후 scale-in/holding 경과시간 계산이 naive `datetime.now()`와 직접 빼기를 수행해 스나이퍼 스레드가 종료됐다. 공용 elapsed-time resolver가 datetime 형식과 timezone 유무를 정규화하고 scale-in 및 legacy exit 시간가치 경로가 이를 함께 사용하도록 단일화했다.
  - 검증/권한: aware broker datetime, naive/aware ISO, holding/exit 회귀 테스트로 재현·복구를 검증한다. 변경은 보유 경과시간 계산과 장애 복구만 소유하며 진입·청산 threshold, provider, 주문가·수량, broker/account/order/cooldown, hard safety를 변경하지 않는다.
  - 적용 결과: review/fix/re-review 후 scale-in·holding·exit·process-health·checklist parser·WebSocket 회귀 테스트와 compile/변경행 lint/`git diff --check`를 통과했다. `./restart.sh`로 PID `12158 -> 53592` 우아한 재기동을 완료했고 runtime env verify=`pass`, provider=`OpenAI`, 스나이퍼 heartbeat=`alive`, `322000` HOLDING 1주 boot restore 및 실시간 WS 수신을 확인했다. probe 잔여 3주는 `residual_not_submitted` terminal 상태이므로 미체결 복원 대상이 아니다.

- [ ] `[RuntimeEnvIntradayObserve0818] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-08-18`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-14.json)
  - 전일 postclose candidate_selected_families=entry_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime, scalping_pyramid_quality_gate, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0818] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-08-18`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-08-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-14.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0818] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-08-18`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-08-18.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-18.jsonl), [threshold_events_2026-08-18.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-18.jsonl), [observation_source_quality_audit_2026-08-18.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-18.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-08-18 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [x] `[SniperMarketCloseHeartbeatContract0818] 20:00 스나이퍼 정상 종료 process-health 오탐 해소` (`Due: 2026-08-18`, `Slot: POSTCLOSE`, `TimeWindow: 20:00~20:10`, `Track: RuntimeStability`)
  - Source: [process_health.py](/home/ubuntu/KORStockScan/src/engine/error_detectors/process_health.py), [kiwoom_sniper_v2.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py), [run_error_detection.log](/home/ubuntu/KORStockScan/logs/run_error_detection.log)
  - 판정: 스나이퍼는 `20:00:01` 정상 장 종료 분기에서 멈췄으나 bot expected window가 `20:10`까지라서 일반 `alive=false`가 장애로 오인됐다. owner가 동일 거래일 20:00 이후 `terminal_reason=market_close`를 명시한 경우만 `expected_terminal` PASS로 분리하고, reason 누락·조기 종료·과거 날짜·다른 thread는 기존 FAIL을 유지한다.
  - 권한 경계: detector 분류와 heartbeat provenance만 보완하며 bot 재기동, 실주문, threshold, provider, 주문가·수량, broker/account/order/cooldown 및 hard safety를 변경하지 않는다.
  - 검증/적용: error-detector·scheduler 회귀 `166 passed`, Ruff/compile/`git diff --check`, checklist parser를 통과했고 health-only dry-run은 `summary_severity=pass`, process-health=`expected_terminal`로 재판정했다. 기존 PID는 이미 로드한 detector 코드로 20:10 종료 전까지 과거 분류를 반복할 수 있으나, 장후 작업 직전 불필요한 재기동은 수행하지 않는다. 다음 프로세스부터 owner marker가 자동 기록된다.

- [ ] `[PostcloseSourceQualityGateReview0818] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-08-18`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-08-18.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-18.json), [threshold_cycle_ev_2026-08-18.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-18.json), [code_improvement_workorder_2026-08-18.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-18.json), [threshold_cycle_postclose_verification_2026-08-18.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-08-18.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0818] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-08-18`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-14.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0818] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-08-18`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-14.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[LifecycleQuietGapReview0818] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-08-18`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-08-14.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-14.json), [runtime_apply_gap_audit_2026-08-14.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-14.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`290`, rollup_required_count=`290`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 289}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[MachineLifecycleTurnoverObjectiveFollowup0818] 위젯·episode 빠른 회전 목적의 미완료 후속 구현 확인` (`Due: 2026-08-18`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~21:40`, `Track: ScalpingLogic`)
  - Source: [machine_microstructure_policy_approval_postclose_2026-08-14.json](/home/ubuntu/KORStockScan/data/report/machine_microstructure_policy_approval/machine_microstructure_policy_approval_postclose_2026-08-14.json), [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py)
  - 판정 기준: 승인 후보 수와 무관하게 `followup_required=true`인 미완료 목적 항목 `machine_lifecycle_turnover_policy_research_v1`(status=`EVIDENCE_ACCUMULATING`, next_action=`continue_exact_date_collection_and_rolling_readiness_review`)의 상태와 상태별 `next_action`을 확인하고 구현 또는 표본수집 경로로 닫는다.
  - 상태별 다음 액션: `IMPLEMENTATION_REQUIRED`는 source-only rolling paired policy 연구를 구현하고, `EVIDENCE_ACCUMULATING`은 exact-date floor 충족까지 수집·재검증한다. `CANDIDATE_QUEUE_HANDOFF|COMPLETE`는 closed 상태이므로 report에서 제외되고 다음 refresh에서 builder-owned 항목이 제거된다.
  - 권한 경계: 이 POSTCLOSE 후속 항목은 source-only 구현·검증 작업이며 runtime env, 실주문, target/timeout/cooldown/cap, threshold, provider/bot, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[AutomationTriggerDecisionSummary0818] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-08-18`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-08-14.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-08-14.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`14`, run_count=`9`, skip_count=`0`, source_missing_count=`1`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`-`, top_reasons=`upstream_drift_signal:8, upstream_artifact_newer:6, disabled_by_runtime_policy:5, source_missing_or_unreadable:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## 사용자 지시 구현

- [x] `[LowPriceEpisodeRecommendationImplementation0818] 장후 추천 14개 프로필 구현 및 PREOPEN 세대 경계 고정` (`Due: 2026-08-18`, `Slot: POSTCLOSE`, `TimeWindow: 21:45~22:30`, `Track: ScalpingLogic`)
  - Source: [추천 동결 증거](/home/ubuntu/KORStockScan/data/config/low_price_two_leg_expanded_profile_evidence_2026-08-18.json), [profiles.py](/home/ubuntu/KORStockScan/src/trading/low_price_two_leg/profiles.py), [policy_runtime.py](/home/ubuntu/KORStockScan/src/trading/low_price_two_leg/policy_runtime.py), [lower-price runbook](/home/ubuntu/KORStockScan/docs/low-price-two-leg-machines.md)
  - 판정: clean baseline 51거래일 추천 통과행 14개를 신규 profile 7개와 기존 profile 로직개선 7개로 정확히 결속했다. 2026-08-18까지 13-profile 과거 세대를 유지하고 2026-08-19 exact-date PREOPEN부터 20-profile 세대를 적용한다.
  - 보호장치: 더본코리아 morning 고정 관찰은 source-only로 유지한다. 전일 미청산 원장은 생성 당시 entry/target 세대로 검증하며 새 target으로 취소·교체·재해석하지 않는다. 수량 10주×2leg, SOR, 무손절·미청산 보유, owner별 state/order ledger 분리는 변경하지 않는다.

- [ ] `[LowPriceEpisodeNewTimersActivation0819] 신규 7개 episode timer 설치·owner 전환·기동 검증` (`Due: 2026-08-19`, `Slot: PREOPEN`, `TimeWindow: 08:45~09:00`, `Track: RuntimeStability`)
  - Source: [installer](/home/ubuntu/KORStockScan/deploy/install_low_price_two_leg_systemd.sh), [systemd units](/home/ubuntu/KORStockScan/deploy/systemd), [lower-price runbook](/home/ubuntu/KORStockScan/docs/low-price-two-leg-machines.md)
  - 판정 기준: 사용자 별도 설치·기동 지시 후에만 신규 7개 timer를 설치하고, SK텔레콤·삼성E&A `manual_operator` exclusion, 20-profile exact-date applied artifact, profile별 authority, timer/service 상태를 확인한다.
  - 금지: 코드리뷰 완료만으로 systemd install/enable/start, 메인 봇 재기동, 실주문 또는 기존 보유 target 취소·교체를 수행하지 않는다.

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
