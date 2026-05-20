# 2026-05-21 Stage2 To-Do Checklist

## 오늘 목적

- 2026-05-20 postclose에서 산출된 `SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY=160` 후보가 장전 runtime env에 정상 반영됐는지 확인한다.
- 장중 수집된 scalp sim row가 LDM stage/action bucket별로 충분히 분산됐는지 장후에 판정한다.
- `max_daily=160` 및 reserve/bucket quota 적용 결과를 검증한 뒤 `240` 상향 여부를 postclose LDM joined/action bucket coverage로만 결정한다.
- sim/probe 표본은 source-quality/EV 입력으로만 쓰고 real execution 품질이나 실주문 전환 근거로 쓰지 않는다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- `SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY` 추가 상향 또는 reserve/bucket quota 변경은 장중 env 수정이나 restart flag로 처리하지 않고, postclose 산출물과 다음 PREOPEN 후보로만 다룬다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

## 장후 체크리스트

- [ ] `[ScalpSimLdmMaxDaily240Review0521] LDM joined/action bucket coverage 확인 후 scalp sim max_daily 240 상향 여부 결정` (`Due: 2026-05-21`, `Slot: POSTCLOSE`, `TimeWindow: 17:25~17:40`, `Track: ScalpingLogic`)
  - Source: [lifecycle_decision_matrix.py](/home/ubuntu/KORStockScan/src/engine/lifecycle_decision_matrix.py), [lifecycle_decision_matrix_2026-05-21.json](/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-21.json), [threshold_runtime_env_2026-05-21.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-21.env)
  - 판정 기준: `max_daily=160`과 reserve/bucket quota 적용 후 postclose LDM의 `stage sample`, `joined_sample`, `join_rate`, `action_namespace`, `source_stage`, `risk_context_owner`, `risk_direction` bucket coverage를 확인한다. stage floor만 통과한 상태가 아니라 entry/scale_in/exit와 panic/euphoria action bucket이 한쪽으로 과도하게 쏠리지 않았는지 본 뒤 `240` 상향 후보 여부를 결정한다.
  - 금지: `240` 상향을 장중 runtime env 직접 수정, restart만으로 적용, real order enable, Telegram BUY/SELL, provider route, bot restart trigger로 연결하지 않는다.
  - 다음 액션: `keep_160_coverage_enough`, `preopen_candidate_240`, `hold_160_until_persistent_counter_fixed`, `defer_source_quality_or_bucket_skew` 중 하나로 닫고, `preopen_candidate_240`이면 다음 PREOPEN `threshold_cycle_preopen_apply` 확인 항목을 생성한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-05-20` postclose -> `2026-05-21`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[ThresholdEnvAutoApplyPreopen0521] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-05-21`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-20.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-20.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 실행 메모 (`2026-05-21 07:41 KST`): [threshold_cycle_preopen_2026-05-21.status.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-05-21.status.json)은 `status=succeeded`, `exit_code=0`, `apply_mode=auto_bounded_live`, `runtime_effect=preopen_runtime_env_apply_only`다. [threshold_apply_2026-05-21.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-21.json)은 `status=auto_bounded_live_ready`, `source_date=2026-05-20`, `target_date=2026-05-21`, `runtime_change=true`, `approval_requests=[]`, `approval_contract_gaps=[]`다.
  - 판정 결과: `applied_guard_passed_env`. runtime env selected family는 `soft_stop_whipsaw_confirmation`, `score65_74_recovery_probe`, `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `lifecycle_decision_matrix_runtime`, `scalp_sim_scale_in_window_expansion`이다. `SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY=160` 및 time bucket policy가 반영됐고, `lifecycle_decision_matrix_runtime`의 action mutation은 `RUNTIME_EFFECT_ENABLED=false`로 유지된다. `latency_classifier_recommendation`은 loaded 상태지만 `recommended_action=hold`, `allowed_runtime_apply=false`라 latency env override는 없다.
  - 다음 액션: 장중 runtime mutation 금지를 유지하고, `RuntimeEnvIntradayObserve0521`에서 selected family provenance/rollback guard를, `SimProbeIntradayCoverage0521`에서 sim-only provenance를 확인한다.

- [x] `[OpenAIWSPreopenConfirm0521] OpenAI WS 유지 설정 및 entry_price/analyze_target provenance 확인` (`Due: 2026-05-21`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-20.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-20.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py)
  - 판정 기준: startup env의 OpenAI route/Responses WS 설정과 `analyze_target`, `entry_price` transport provenance를 분리 확인한다.
  - 금지: provider transport 확인을 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경으로 해석하지 않는다.
  - 다음 액션: entry_price transport 표본이 부족하면 장중 표본 재확인 항목과 연결한다.
  - 실행 메모 (`2026-05-21 07:41 KST`): [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)는 `KORSTOCKSCAN_SCALPING_AI_ROUTE=openai`, `KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED=true`, WS pool size `2`, request timeout `15000ms`를 기본값으로 사용하고 당일 runtime env를 source한다. `bot_history.log` 07:40 startup에는 OpenAI 엔진 고정, `role=main route=openai`, `main_scalping_openai=ON`, `main_scalping_deepseek=OFF`가 기록됐다.
  - 판정 결과: `pass`. [openai_ws_stability_2026-05-20.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-20.md)는 `decision=keep_ws`, unique WS calls `3074`, `analyze_target=2830`, `entry_price=244`, WS fallback `0`, success rate `1.0`, `entry_price` instrumentation gap `false`로 판정됐다.
  - 다음 액션: provider transport 확인은 threshold/order guard/provider 변경으로 쓰지 않고, 장중/장후 fallback, fail-closed, latency guard split을 계속 관찰한다.

## Runbook 운영 확인 완료 기록

- `EODTop5FeatureRemoval0521` 내일의 주도주 TOP5 기능 제거
  - Source: [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py), [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정: `removed_no_ai_call_path`
  - 근거: `src/scanners/eod_analyzer.py` 진입점을 삭제하고, `KORSTOCKSCAN_EOD_TOP5_ENABLED`, `generate_eod_tomorrow_*`, `EOD_TOMORROW_LEADER_*`, `eod_top5_v1` schema/test/live smoke case를 제거했다. 스윙 sim/approval 입력에서 `EOD_TOP5`/`DB_EOD_TOP5` 선택 모드도 제외했다.
  - 금지: 이 제거를 threshold daily EV, 스윙 dry-run/lifecycle, final ensemble scanner, update_kospi, 실주문 runtime guard 변경 근거로 쓰지 않는다.
  - 다음 액션: 재개하려면 신규 workorder, 신규 acceptance schema, cron/detector/runbook 복구, AI 비용 guard를 별도 변경 세트로 열어야 한다.

- `PreopenAutomationHealthCheck20260521` 장전 자동화체인 상태 확인
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md) `장전 확인 절차`
  - 판정: `pass`
  - 근거: preopen cron log에 `[DONE] threshold-cycle preopen target_date=2026-05-21`가 있으며, [threshold_cycle_preopen_2026-05-21.status.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-05-21.status.json)은 `status=succeeded`다. [threshold_runtime_env_2026-05-21.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-21.env)는 07:35에 생성됐고, `tmux`의 `bot` 세션 및 `bot_main.py` 프로세스는 07:40 startup 이후 실행 중이다.
  - 테스트/검증: `PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode full --dry-run` 결과 `summary_severity=pass`, `threshold_cycle_preopen_status=pass`, `process_health=pass`, `artifact_freshness=pass`, `resource_usage=pass`, `stale_lock=pass`다.
  - 다음 액션: 장전 반복 운영 확인은 완료로 닫고, 장중 확인은 `RuntimeEnvIntradayObserve0521`, `SimProbeIntradayCoverage0521`에서 별도 수행한다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0521] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-05-21`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-20.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-20.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, latency_classifier_runtime_profile, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0521] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-05-21`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-20.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-20.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

## 장후 체크리스트 (16:30~18:55)

- [ ] `[ThresholdDailyEVReport0521] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-05-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-20.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-20.json)
  - 판정 기준: real/sim/combined split, selected/blocked family, runtime_change, warning을 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[CodeImprovementWorkorderReview0521] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-05-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-05-20.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-20.md), [code_improvement_workorder_2026-05-20.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-20.json)
  - 판정 기준: selected_order_count=12와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented 중 하나로 닫는다.

- [ ] `[HumanInterventionSummary0521] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-05-21`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-20.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-20.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[ShadowCanaryCohortReview0521] shadow/canary/cohort 런타임 분류 및 정리 판정` (`Due: 2026-05-21`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: Plan`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: 당일 변경/관찰 결과를 기준으로 `remove`, `observe-only`, `baseline-promote`, `active-canary` 상태 변동 여부를 닫는다.
  - 금지: shadow 금지, canary-only, baseline 승격 원칙을 코드/문서 상태와 분리하지 않는다.
  - 다음 액션: 변경이 있으면 기준문서와 checklist를 함께 갱신하고 cohort 잠금 필드를 남긴다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->
