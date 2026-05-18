# 2026-05-19 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-05-18` postclose -> `2026-05-19`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[ThresholdEnvAutoApplyPreopen0519] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-05-19`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-18.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-18.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 완료 메모 (`2026-05-19 08:25 KST`): `warning`. `logs/threshold_cycle_preopen_cron.log`는 `[DONE] threshold-cycle preopen target_date=2026-05-19 finished_at=2026-05-19T07:35:01+0900`를 남겼고, apply plan은 `status=auto_bounded_live_ready`, `apply_mode=auto_bounded_live`, `runtime_change=true`다. `threshold_runtime_env_2026-05-19.{env,json}`은 07:52에 재생성되어 `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=true`, latency classifier age/jitter/spread override, `KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true`를 포함한다. 이는 사용자 `operator_override_reopen_score65_74_probe` lock 반영이며 threshold/provider/order guard 우회 권한은 없다. 봇 PID `7079`는 `2026-05-19 07:52:26 KST` 시작했고 `/proc/7079/environ`에서 위 runtime env 로드를 확인했다.
  - 다음 액션: `applied_guard_passed_env_with_operator_reopen_warning`으로 닫는다. 장중에는 `RuntimeEnvIntradayObserve0519`에서 score65_74 probe, latency classifier profile, rollback guard provenance를 분리 확인한다.

- [x] `[OpenAIWSPreopenConfirm0519] OpenAI WS 유지 설정 및 entry_price/analyze_target provenance 확인` (`Due: 2026-05-19`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-18.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-18.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py)
  - 판정 기준: startup env의 OpenAI route/Responses WS 설정과 `analyze_target`, `entry_price` transport provenance를 분리 확인한다.
  - 금지: provider transport 확인을 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경으로 해석하지 않는다.
  - 완료 메모 (`2026-05-19 08:25 KST`): `pass`. `run_bot.sh`는 `KORSTOCKSCAN_SCALPING_AI_ROUTE=openai`, `KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED=true`, pool size `2`, timeout `15000ms`, max output tokens `512`를 export한다. 봇 PID `7079`의 `/proc/7079/environ`에서도 동일 env 로드를 확인했다. `openai_ws_stability_2026-05-18.md`는 decision=`keep_ws`, unique WS calls=`799`, endpoint counts=`analyze_target 797`, `entry_price 2`, WS fallback=`0/799`, WS success rate=`1.0`, entry_price instrumentation_gap=`False`로 닫혔다.
  - 다음 액션: provider/threshold/order guard 변경 없이 OpenAI WS 유지. 당일 live 표본은 장중 provenance 항목에서 `openai_endpoint_name`, `openai_schema_name`, `openai_ws_used`, `openai_ws_http_fallback`을 계속 분리 확인한다.

## Runbook 운영 확인 기록

- [x] `[PreopenAutomationHealthCheck20260519] 장전 자동화체인 상태 확인` (`Due: 2026-05-19`, `Slot: PREOPEN`, `TimeWindow: 08:00~09:00`, `Track: RunbookOps`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md#장전-확인-절차)
  - 판정: `warning`
  - 근거: preopen apply `[DONE]` marker와 runtime env 생성은 확인됐다. `final_ensemble_scanner target_date=2026-05-19`도 `[DONE]`으로 종료했고 추천 3건이 적재됐다. apply plan은 `auto_bounded_live_ready`, runtime env는 07:52 재생성본 기준으로 로드됐다. 봇 PID `7079`는 env 재생성 이후 시작되어 `/proc/7079/environ`에서 runtime env와 OpenAI WS env 로드를 확인했다. 다만 `score65_74_recovery_probe`는 사용자 operator reopen lock으로 `true`가 반영된 상태라 순수 자동 apply와 구분한다.
  - 다음 액션: 장중 `RuntimeEnvIntradayObserve0519`에서 operator reopen cohort와 latency classifier profile provenance를 확인하고, 장중 threshold/provider/order guard 변경은 하지 않는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0519] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-05-19`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-18.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-18.json)
  - 판정 기준: `score65_74_recovery_probe`는 사용자 지시로 다시 열린 상태를 확인하고, selected_families 중 score65_74_recovery_probe, latency classifier profile, bad_entry_refined_canary, swing_one_share_real_canary_phase0, swing_gatekeeper_reject_cooldown가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[LatencyClassifierProfileOverride0519] 스캘핑 latency classifier age/jitter/spread override 로드 및 latency_pass 회복 확인` (`Due: 2026-05-19`, `Slot: INTRADAY`, `TimeWindow: 09:20~09:35`, `Track: ScalpingLogic`)
  - Source: [latency_classifier_recommendation_2026-05-18.json](/home/ubuntu/KORStockScan/data/report/latency_classifier_recommendation/latency_classifier_recommendation_2026-05-18.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py), [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py), [pipeline_events_2026-05-18.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-18.jsonl)
  - 판정 기준: PREOPEN runtime env에서 `KORSTOCKSCAN_SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION`, `KORSTOCKSCAN_SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION`, `KORSTOCKSCAN_SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION`이 로드됐는지 확인하고, `latency_block` 비중이 줄고 `latency_pass` 또는 `order_leg_request`가 발생하는지 본다.
  - 금지: fallback split-entry 재개, provider 변경, order guard 우회, 장중 threshold mutation으로 해석하지 않는다. `quote_stale`/`spread_too_wide`/stale submit block은 별도 safety로 유지한다.
  - 다음 액션: `override_loaded_latency_pass_recovered`, `override_loaded_still_blocked_by_quote_or_spread`, `override_missing`, `runtime_restart_needed`, `rollback_guard_breach` 중 하나로 닫는다.

- [ ] `[SimProbeIntradayCoverage0519] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-05-19`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-18.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-18.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[EntryADMRuntimeEffectObserve0519] Entry ADM runtime effect 및 실제 API prompt 적용 재확인` (`Due: 2026-05-19`, `Slot: INTRADAY`, `TimeWindow: 10:00~10:20`, `Track: ScalpingLogic`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md), [scalp_entry_adm_runtime.py](/home/ubuntu/KORStockScan/src/engine/scalp_entry_adm_runtime.py), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py), [scalp_entry_action_decision_matrix_2026-05-18.json](/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-05-18.json)
  - 판정 기준: `/proc/<bot_pid>/environ` 또는 신규 event에서 `KORSTOCKSCAN_SCALP_ENTRY_ADM_ADVISORY_ENABLED=true`, `KORSTOCKSCAN_SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED=true` 로드를 확인하고, `analyze_target` actual API live 호출 또는 당일 live event에서 `entry_adm_prompt_applied=true`, `openai_endpoint_name=analyze_target`, `openai_schema_name=entry_v1`, `entry_adm_cache_token` prefix를 확인한다. 신규 cohort에 `entry_adm_runtime_effect`, `entry_adm_forced_action`, `entry_adm_runtime_reason`이 찍히는지도 분리 확인한다.
  - 금지: 실제 API smoke를 broker order submit, threshold mutation, provider 변경, bot restart 근거로 사용하지 않는다. `BUY_NOW`/`BUY_DEFENSIVE` positive bucket은 표본 충족 전 강제 BUY 승격으로 해석하지 않는다.
  - 다음 액션: `api_prompt_loaded_no_forced_effect`, `forced_wait_drop_observed`, `prompt_not_loaded`, `runtime_env_missing`, `fixture_schema_gap`, `api_transport_fail` 중 하나로 닫고, gap은 `order_scalp_entry_adm_daily_tuning_coverage` 또는 후속 workorder로 연결한다.

## 장후 체크리스트 (16:30~18:55)

- [ ] `[ThresholdDailyEVReport0519] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-05-19`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-18.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-18.json)
  - 판정 기준: real/sim/combined split, selected/blocked family, runtime_change, warning을 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[CodeImprovementWorkorderReview0519] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-05-19`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-05-18.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-18.md), [code_improvement_workorder_2026-05-18.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-18.json)
  - 판정 기준: selected_order_count=12와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented 중 하나로 닫는다.

- [ ] `[HumanInterventionSummary0519] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-05-19`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-18.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-18.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[ShadowCanaryCohortReview0519] shadow/canary/cohort 런타임 분류 및 정리 판정` (`Due: 2026-05-19`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: Plan`)
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
