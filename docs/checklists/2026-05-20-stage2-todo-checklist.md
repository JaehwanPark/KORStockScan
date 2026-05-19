# 2026-05-20 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-05-19` postclose -> `2026-05-20`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[ThresholdEnvAutoApplyPreopen0520] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-05-20`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-19.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-19.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 실행 메모 (`2026-05-20 07:49 KST`): `threshold_apply_2026-05-20.json`은 `status=auto_bounded_live_ready`, `apply_mode=auto_bounded_live`, `runtime_change=true`, `source_date=2026-05-19`, `warnings=[]`였다. `threshold_runtime_env_2026-05-20.{json,env}`는 07:35 생성됐고 selected family는 `soft_stop_whipsaw_confirmation`, `latency_classifier_runtime_profile`, `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `lifecycle_decision_matrix_runtime`, `scalp_sim_scale_in_window_expansion`이다. swing approval은 `requested=0`, `approved=0`이며 별도 사용자 개입 artifact는 없었다. `logs/threshold_cycle_preopen_cron.log`에는 `[DONE] threshold-cycle preopen target_date=2026-05-20 finished_at=2026-05-20T07:35:01+0900`가 남았다.
  - 판정 결과: `applied_guard_passed_env`
  - 다음 액션: 장중에는 runtime threshold mutation 없이 `RuntimeEnvIntradayObserve0520`에서 selected family provenance와 rollback guard만 관찰한다.

- [x] `[OpenAIWSPreopenConfirm0520] OpenAI WS 유지 설정 및 entry_price/analyze_target provenance 확인` (`Due: 2026-05-20`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-19.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-19.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py)
  - 판정 기준: startup env의 OpenAI route/Responses WS 설정과 `analyze_target`, `entry_price` transport provenance를 분리 확인한다.
  - 금지: provider transport 확인을 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경으로 해석하지 않는다.
  - 다음 액션: entry_price transport 표본이 부족하면 장중 표본 재확인 항목과 연결한다.
  - 실행 메모 (`2026-05-20 07:49 KST`): `run_bot.sh` 기본값은 `KORSTOCKSCAN_SCALPING_AI_ROUTE=openai`, `KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED=true`, pool size `2`, timeout `15000ms`다. `bot_history.log` 07:40 startup에서 OpenAI 엔진 초기화, `메인 스캘핑 OpenAI 엔진 고정 완료`, `AI 라우팅 활성화: role=main route=openai (main_scalping_openai=ON / main_scalping_deepseek=OFF)`를 확인했다. 전일 WS 리포트는 unique WS calls `3960`, endpoint counts `analyze_target=3854`, `entry_price=106`, WS fallback `0`, success rate `1.0`, entry_price transport observable `106`으로 provenance 표본이 충분했다.
  - 판정 결과: `pass`
  - 다음 액션: provider transport 확인은 threshold/주문가/수량 guard 변경 근거로 쓰지 않고, 장중 실제 표본은 `RuntimeEnvIntradayObserve0520`/관련 provenance 관찰에서만 분리 확인한다.

## Runbook 운영 확인 완료 기록

- `PreopenAutomationHealthCheck20260520` (`Slot: PREOPEN`, `TimeWindow: 08:00~09:00`, `Track: RunbookOps`) 판정: `pass`
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md) `장전 확인 절차`
  - 근거: 07:35 preopen wrapper가 `[DONE]`으로 종료했고, error detector 로그의 07:35/07:40/07:45 run에서 `threshold_cycle_preopen_status=pass`, `threshold_runtime_env_status=pass`, `threshold_apply_plan_status=pass`가 확인됐다. 07:40 tmux `bot` 세션과 `bot_main.py` 프로세스가 기동 중이며 키움 WS 연결/로그인과 조건검색식 등록이 완료됐다.
  - 다음 액션: 반복 운영 확인은 완료로 보며, 이후 장중 항목은 별도 checklist owner가 소유한다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0520] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-05-20`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-19.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-19.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, latency_classifier_runtime_profile, score65_74_recovery_probe가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0520] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-05-20`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-19.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-19.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

## 장후 체크리스트 (16:30~18:55)

- [ ] `[ThresholdDailyEVReport0520] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-05-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-19.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-19.json)
  - 판정 기준: real/sim/combined split, selected/blocked family, runtime_change, warning을 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[CodeImprovementWorkorderReview0520] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-05-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-05-19.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-19.md), [code_improvement_workorder_2026-05-19.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-19.json)
  - 판정 기준: selected_order_count=12와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented 중 하나로 닫는다.

- [ ] `[HumanInterventionSummary0520] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-05-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-19.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-19.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[ShadowCanaryCohortReview0520] shadow/canary/cohort 런타임 분류 및 정리 판정` (`Due: 2026-05-20`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: Plan`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: 당일 변경/관찰 결과를 기준으로 `remove`, `observe-only`, `baseline-promote`, `active-canary` 상태 변동 여부를 닫는다.
  - 금지: shadow 금지, canary-only, baseline 승격 원칙을 코드/문서 상태와 분리하지 않는다.
  - 다음 액션: 변경이 있으면 기준문서와 checklist를 함께 갱신하고 cohort 잠금 필드를 남긴다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

## 수동 개발 반영 기록

- [x] `[SwingStrategyDiscoveryFollowupV1Implement0520] Swing Strategy Discovery Sim v1 label/EV/source-only 자동화체인 1차 구현` (`Due: 2026-05-20`, `Slot: POSTCLOSE`, `TimeWindow: 19:00~20:30`, `Track: SwingLogic`)
  - Source: [swing-strategy-discovery-sim-v1.md](/home/ubuntu/KORStockScan/docs/swing-strategy-discovery-sim-v1.md), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정 기준: candidate/arm 생성 후 label builder, EV report, sector/theme source, postclose wrapper, threshold EV/runtime summary/code-improvement source-only 연결이 모두 `runtime_effect=false` 계약을 유지한다.
  - 금지: 실주문, `recommendation_history` 대체, runtime env apply, broker guard 변경.
  - 실행 메모 (`2026-05-20 Codex`): `swing_sector_theme_source`, `swing_strategy_discovery_label_builder`, `swing_strategy_discovery_ev_report`를 추가하고 postclose wrapper에 `swing_daily_simulation -> discovery sim -> label builder -> discovery EV -> swing lifecycle audit` 순서를 연결했다. `threshold_cycle_ev`, `runtime_approval_summary`, `build_code_improvement_workorder`는 source-only 요약/주문만 소비한다.
  - 판정 결과: `implemented_source_only`
  - 다음 액션: 다음 postclose에서 `swing_strategy_discovery_ev_YYYY-MM-DD` 생성 여부와 `pending_future_quotes` 감소/성숙 label 갱신을 확인한다.
