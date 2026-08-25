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
  - 2026-08-25 08:24~09:10 KST 조기 검증: PID `9978`에서 daily entry-split baseline은 유효했지만 launcher가 표준 policy enabled key만 dependency로 보아 `KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED=false`로 변조한 계약 불일치를 확인했다. daily baseline을 신규 live 정책으로 승격하지 않고 기존 daily operator contract를 probe dependency로 인정하도록 launcher를 보완했다. 1차 graceful child handoff `9978 -> 39468` 뒤에도 PID 값이 false로 남아 verify가 `runtime_env_pid_mismatch`로 정확히 실패했다. 직접 원인은 child만 교체되고 07:55에 `d2b5bbe2`에서 로드된 장수 `run_bot.sh` supervisor가 이전 함수 세대를 재사용한 것이었다. `restart.sh`는 launcher SHA drift가 있으면 기존 child가 완전히 종료된 뒤 tmux supervisor만 교체하고, PID verify 실패도 성공으로 삼지 않도록 보완했다. 다음 acceptance는 신규 PID의 launcher commit/hash=current HEAD, source-dirty=false, probe-first=true/DAILY 및 verify `status=pass,pid_passed=true`다.
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
  - 2026-08-25 09:00 KST transport 보완: 08:08 `analyze_target` 자연 호출에서 5,000ms 예산 대비 HTTP provider 15,238ms가 관측됐다. SDK retry는 0이었으므로 inactivity timeout과 end-to-end deadline의 계약 불일치로 판정해 단일 worker wall-clock deadline과 `wall_deadline_exceeded/provider_future_cancelled/deadline_overshoot_ms` provenance를 구현했다. 1차 child handoff PID `39468`에는 transport 코드가 반영됐지만 launcher 세대 불일치가 남아 전체 runtime handoff는 미완료로 유지한다.
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
  - 2026-08-25 구현 결과: P0는 WebSocket `ws.recv()` 직후의 명시적 `websocket_packet_ingress` 시각으로만 type `00` receipt를 정렬하고 FID 908의 초 단위 발생시각을 별도 검증한다. logical trade date는 FID 908 occurrence date, transition ordering은 packet-ingress receive time으로 분리한다. 하루 이내 자정 경계 exact lifecycle JSONL은 검증·압축된 base gzip을 다시 변경하지 않고 cross-process lock+fsync가 적용된 명시적 `*.late.jsonl` sidecar에 기록하며, paired consumer가 base gzip/plain 뒤 late gzip/plain을 결정적으로 모두 census한다. source tag가 없거나 timing fragment만 있는 기존 handler-dispatch 시각은 소급 합성하거나 promotion 증거로 사용하지 않으며, exact lineage가 확인되면 해당 lifecycle만 격리한다. `holding_started` companion은 직전 수락 또는 replay 확인된 BUY entry-fill의 동일 raw identity/content에만 일회성 결속하고 동일 raw 재전송은 replay로 버린다. venue/session은 lifecycle immutable identity가 아니라 `decision_trace_id + lifecycle stage`별 exact provenance path로 보존하고, 같은 trace/stage의 context가 둘 이상이면 R2 join을 fail closed한다. paired daily schema는 v2이고 downstream도 official-FID908 duration과 timing source를 검증한다. P1은 고정 매도호가 0.5/1/3/5/10초 ask-depletion·top3/top5·trade backing·cancel-like·refill/half-life를 source-only sidecar로 추가했다. P2 current A/B/C는 `A=current prompt+exact tactical micro`, `B=A+ask-depletion feature only`, `C=B와 byte-identical input+candidate prompt/response contract only`로 단일축 결속하고 A→B 비열화 및 A→C EV/상대 uplift/p10/severe-tail gate를 R3 후보 생성 전에 강제한다. `2026-08-25 KST` 이후 request/evidence/outcome의 embedded KST date가 target date와 다르면 재봉인된 artifact도 거부한다. Bridge의 future market/depth/ENTRY_PIPELINE 원본은 단일 content-addressed pool에 저장하고 row별 ordered hash reference만 반복하며, source bundle은 독립 재열람 원본과 bridge reference를 provider materialization 전에 대조한다. Action-neutral label은 raw pool/rebuild row를 중복하지 않되 exact 검증을 위해 parent별 tactical evidence/future outcome을 한 번 더 보존하고 bridge/pool/commitment hash와 materialized-parent census에 결속한다. execution/R2는 persisted external companion을 날짜별 lazy-load하여 exact bridge row에서 evaluation을 재구성하므로 companion 누락·shifted outcome·평가값 재작성·부모 누락은 fail closed한다. 원시 lifecycle report/trace가 실제 존재하지만 invalid/ambiguous인 current parent만 R3 전역 blocker이며 자연스러운 비주문 WAIT/DROP lifecycle 결손은 parent-local exclusion이다. 미성숙 parent는 provider materialization 전에 제외하고, 활성일 이전 invalid legacy artifact는 current-design 전체 R3의 global blocker로 전파하지 않는다. WAIT one-share probe와 full exposure의 수익률 EV는 동일한 비용차감 percentage basis로 비교하되, one-share probe notional은 full-exposure notional·순이익 합계에 혼합하지 않는다. exact-date P2 JSON allowlist는 장후 verified gzip으로 전환하고 90일 초과분은 삭제 없이 retention count/bytes만 집계한다. runtime/order/provider/PREOPEN apply 권한은 계속 false다.
  - 2026-08-25 supplemental review 결과: current holding/holding-flow/exit `TRIM`은 진단 action을 유지하되 현 runtime 의미와 같이 HOLD exposure로 평가하여 parent를 선택적으로 제외하지 않는다. Tactical bridge는 causal market/depth/event-reference 전체에서 최신 native positive reconnect epoch을 먼저 선택하며, 최신 epoch에 market이 없으면 과거 epoch로 후퇴하지 않고 `past_market_row_missing`, 동일 최신 timestamp competing epoch이면 ambiguous로 닫는다. 현재 source-audit/economic/storage/Provider/composed-chain blocker는 rolling 성과와 무관하게 hash-bound R2 blocker 및 R3 candidate 0건을 강제하고, Provider floor의 5개 companion 일부만 남은 날짜도 orphan generation으로 차단한다. Provider leaf는 canonical owner/policy/manifest/pricing generation, KST generated-at·보통주 census·50% budget basis, 전체 batch provider/model과 Bedrock physical route를 call 전에 검증하고 KST-day 130 parent/390 logical request·attempt/USD 1 상한을 강제한다. checkpoint는 real-directory/no-symlink dirfd custody와 cross-process transaction lock을 사용한다. P2 storage owner는 exact-date report allowlist 17개와 exact AI payload/trace/outcome/request/prompt JSONL+outcome-label JSON 6개 root를 verified closed-date gzip으로 관리하고 micro-reversion daily policy owner bytes/hash 및 90일 retention candidate를 census하되 자동삭제/offload하지 않는다.
  - 2026-08-25 final authority review 결과: persisted APPLIED cardinality와 exact queue identity를 publication 전에 검사하고, 2개 APPLIED 중 하나만 R6-valid여도 zero-write로 닫는다. 이어 enrollment의 최초 apply/R6 영수증 재검증과 handoff·activation causal timestamp가 legacy PREOPEN/live 전체에서 완전하게 증명되지 않는 변형이 발견되어 개별 수선을 반복하지 않고 `main_ai_quality_legacy_runtime_authority_fail_closed`를 적용했다. PREOPEN은 authority input을 읽거나 게시하기 전에 `runtime_effect=false`, `allowed_runtime_apply=false`로 종료하고 live selector는 기존 artifact가 있어도 control prompt를 유지한다. P0/P1/P2 postclose source·A/B/C·R2/R3·queue reporting은 유지되며, 신규 ask-depletion 축과 legacy 축 모두 별도 신규 family 승인 전에는 runtime 권한이 없다.
  - Official reference gate: `2026-08-25T12:53:54+09:00`, upstream `Kiwoom-Securities/Kiwoom-REST-API@69642586f7d84ba9fd8a6faf1f1537c7fda6568b`, inspected `kiwoom_docs/실시간시세.md`, `kiwoom/_data/kiwoom_api_spec.json`, `postman/kiwoom-openapi.postman_collection.json`의 WebSocket `00` 및 FID `908/909/910/911/2134/2135/2136`.
  - 현재 historical disposition: read-only 2026-08-25 replay에서 source tag가 없던 기존 broker/companion 16 row는 `pipeline_broker_execution_receive_source_invalid`로 격리되며 소급 승격되지 않는다. exact identity/authority가 확인된 row는 영향받은 lifecycle window만 제외하고 다른 clean lifecycle을 일별 global gate로 차단하지 않는다. 다음 acceptance는 변경 배포 뒤 동일 날짜 exact source에서 `FINAL_EXIT_RECONCILED` lifecycle, packet-ingress receive provenance, official FID908 duration, BBO/depth floor, resolved execution venue가 함께 충족된 자연 parent가 R0→R3에 들어가는지 다음 postclose 재생성에서 확인하는 것이다. report 재생성 전까지 이 checkbox는 OPEN이며 source-only 구현 완료를 실 runtime 적용으로 해석하지 않는다.

- [ ] `[MainLifecycleLateOverlayArchiveOwner0826] 자정 경계 late overlay의 archive·generic consumer ownership 확정` (`Due: 2026-08-26`, `Slot: POSTCLOSE`, `TimeWindow: 20:50~21:10`, `Track: RuntimeStability`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정 기준: immutable `pipeline_events_YYYY-MM-DD.late.jsonl[.gz]`를 paired consumer 밖의 parquet/archive/generic reader가 필요로 하는지 producer-consumer census로 확정하고, 필요하면 동일 logical-partition lock과 no-clobber 검증을 갖춘 단일 owner를 지정한다.
  - 권한 경계: late overlay 결손을 기존 base gzip 재개방·변경, timestamp 합성, runtime/order/provider/threshold/bot 변경으로 우회하지 않는다.
  - 완료 조건: paired-only ownership이 명시적으로 수용되거나, 필요한 모든 generic consumer가 byte-exact overlay를 중복 없이 읽는 acceptance test와 archive receipt를 갖춘다.

- [ ] `[MainAIQualityP2RetentionCapacityOwner0826] P2 압축 후 잔여 증가량의 retention·offload 권한 결정` (`Due: 2026-08-26`, `Slot: POSTCLOSE`, `TimeWindow: 21:00~21:20`, `Track: RuntimeStability`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: verified closed-date lossless compression 뒤 실제 일별 compressed 증가량, 5 GiB low/1 GiB critical free-space 상태, 보존기간별 projected exhaustion을 측정하고 local retention, 외부 immutable offload, 운영자 승인 purge 중 장기 owner를 확정한다.
  - 권한 경계: 별도 운영 승인 전에는 source/report 자동삭제와 `--purge-expired`를 금지한다. low 상태는 durable source-only workorder로 남기고, critical 상태는 새 P2 materialization/provider replay를 fail closed하되 매매 runtime/order 권한을 바꾸지 않는다.
  - 완료 조건: 선택한 owner가 hash/roundtrip/restore 검증과 free-space postcondition을 갖추고, 삭제를 선택한 경우 exact scope·retention·rollback 권한이 명시적으로 승인된다.

- [ ] `[MainAIQualityCurrentAskTrailingView0826] decision 직전 현재 매도1호가 감소축의 causal feature owner 확정` (`Due: 2026-08-26`, `Slot: POSTCLOSE`, `TimeWindow: 20:40~21:00`, `Track: ScalpingLogic`)
  - Source: [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정 기준: 이번 P1의 shock-event 고정 ask 0.5/1/3/5/10초 감소와 별도로, AI decision 직전 executable current ask의 짧은 trailing depletion/refill을 same symbol·venue·session·sequence epoch에서 causal하게 산출할 owner를 설계한다. same-millisecond depth/trade ambiguity, stale BBO, current-price level 이동, quote replacement를 실제 체결 backing과 분리하고 기존 A/B/C 축과 한 번에 한 feature만 비교한다.
  - 권한 경계: 이 항목은 source-only feature/ablation 설계이며 entry prompt runtime, BUY/WAIT/DROP, 주문가격·수량, provider route, bot, threshold, broker/hard-safety 변경 권한이 없다.
  - 완료 조건: 독립 schema·metric role·window/sample floor·forbidden uses, exact source/label lineage, A/B/C 또는 별도 단일축 비교계획과 적대적 same-ms/stale/refill 테스트가 준비된다.

- [ ] `[MainAIQualityAskDepletionRuntimeConsumerDesign0826] ask-depletion 조건부 prompt 후보의 별도 runtime family·standing intent 계약 설계` (`Due: 2026-08-26`, `Slot: POSTCLOSE`, `TimeWindow: 21:20~21:40`, `Track: ScalpingLogic`)
  - Source: [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: current R3 axis `prompt_contract_effect_on_ask_depletion_context`를 legacy `prompt_contract_effect` consumer에 이름변경으로 연결하지 않는다. exact R2 partition에서 재구성된 단일 R3 candidate, exact candidate-bound standing intent, trusted registry의 별도 family/stage/axis, same-stage conflict guard, PREOPEN apply/rollback receipt와 post-apply attribution을 모두 갖춘 설계를 검토한다.
  - 권한 경계: 설계·source-only 검증 전용이다. exact standing intent와 등록 consumer가 모두 닫히기 전에는 prompt runtime, BUY/WAIT/DROP, 주문가격·수량, provider/model, bot, threshold, broker/hard-safety 또는 PREOPEN env를 변경하지 않는다.
  - 완료 조건: fabricated/self-resealed R3가 R2 canonical projection과 불일치하면 차단되고, exact 후보만 별도 runtime family의 approval 입력이 되며, 그 전까지 `runtime_effect=false`, `allowed_runtime_apply=false`가 유지된다.

- [ ] `[MainAIQualityEntryPriceAblationOwner0826] entry_price Qwen/Nova 별도 A/B/C·action-neutral fill owner 설계` (`Due: 2026-08-26`, `Slot: POSTCLOSE`, `TimeWindow: 21:00~21:20`, `Track: ScalpingLogic`)
  - Source: [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 현재 ask-depletion A/B/C에서 명시적으로 제외된 `entry_price` Bedrock Qwen3 32B primary/Nova Lite v2 failback을 prompt/price-value 단일축으로 평가할 exact paired producer를 정의한다. provider route 자체를 바꾸지 않고 동일 causal BBO/depth·allocator·cancel-wait·submit revalidation에서 fill/partial/cancel/missed-upside와 비용차감 EV를 action-neutral하게 결속한다.
  - 권한 경계: source-only design/probe 전용이며 실주문 가격·cancel wait, provider route/failback, 주문수량·cap, bot/PREOPEN/runtime, broker/hard-safety 변경 권한이 없다.
  - 완료 조건: exact provider receipt/price schema, action-neutral execution label, 5/10/20일 sample floor·tail/capital-time gate, source-quality/rollback/consumer 경계가 정해지고 현 R0→R3 완료 범위와 별도임이 검증된다.

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
