# 2026-05-19 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.
- lifecycle decision matrix는 ADM 확장 umbrella로 문서화하고, 기존 fixed threshold는 `hard_safety|baseline_prior|bounded_tunable|legacy_archive` 역할 계약에 맞춰 판정한다.

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
  - 재확인 (`2026-05-19 08:46 KST`): Project 항목 `PVTI_lAHOAXZuE84BUTcPzgtFDOM` 처리 요청 기준으로 재검증했다. `logs/threshold_cycle_preopen_cron.log`의 `[DONE] threshold-cycle preopen target_date=2026-05-19 finished_at=2026-05-19T07:35:01+0900`, `logs/ensemble_scanner.log`의 `[DONE] final_ensemble_scanner target_date=2026-05-19 finished_at=2026-05-19T07:21:27`, `threshold_runtime_env_2026-05-19.env`의 latency override와 `KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true`, 봇 PID `7079` env 로드를 재확인했다. 판정은 계속 `warning`이며 추가 runtime 변경은 없다.
  - 다음 액션: 장중 `RuntimeEnvIntradayObserve0519`에서 operator reopen cohort와 latency classifier profile provenance를 확인하고, 장중 threshold/provider/order guard 변경은 하지 않는다.

## 장중 체크리스트 (09:05~15:20)

- [x] `[RuntimeEnvIntradayObserve0519] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-05-19`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-18.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-18.json)
  - 판정 기준: `score65_74_recovery_probe`는 사용자 지시로 다시 열린 상태를 확인하고, selected_families 중 score65_74_recovery_probe, latency classifier profile, bad_entry_refined_canary, swing_one_share_real_canary_phase0, swing_gatekeeper_reject_cooldown가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 완료 메모 (`2026-05-19 10:51 KST`): `pass`. `threshold_runtime_env_2026-05-19.env`와 봇 PID `7079` `/proc/7079/environ`에서 `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=true`, latency classifier age/jitter/spread override, `KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true` 로드를 확인했다. 장중 이벤트 기준 `score65_74_recovery_probe=2`, `score65_74_recovery_probe_entry_unlocked=11`, `soft_stop_whipsaw_confirmation=20`, `latency_pass=1`이 관찰됐고 `rollback|safety_revert|runtime_mutation|threshold_runtime_mutation|severe_loss|receipt_missing` 검색성 이벤트는 `0건`이었다.
  - 다음 액션: runtime env는 유지한다. 장중 threshold/provider/order guard 변경은 하지 않고, postclose `threshold_cycle_ev`에서 selected/applied/not-applied attribution으로 재확인한다.

- [x] `[LatencyClassifierProfileOverride0519] 스캘핑 latency classifier age/jitter/spread override 로드 및 latency_pass 회복 확인` (`Due: 2026-05-19`, `Slot: INTRADAY`, `TimeWindow: 09:20~09:35`, `Track: ScalpingLogic`)
  - Source: [latency_classifier_recommendation_2026-05-18.json](/home/ubuntu/KORStockScan/data/report/latency_classifier_recommendation/latency_classifier_recommendation_2026-05-18.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py), [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py), [pipeline_events_2026-05-18.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-18.jsonl)
  - 판정 기준: PREOPEN runtime env에서 `KORSTOCKSCAN_SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION`, `KORSTOCKSCAN_SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION`, `KORSTOCKSCAN_SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION`이 로드됐는지 확인하고, `latency_block` 비중이 줄고 `latency_pass` 또는 `order_leg_request`가 발생하는지 본다.
  - 금지: fallback split-entry 재개, provider 변경, order guard 우회, 장중 threshold mutation으로 해석하지 않는다. `quote_stale`/`spread_too_wide`/stale submit block은 별도 safety로 유지한다.
  - 완료 메모 (`2026-05-19 10:51 KST`): `warning / override_loaded_still_blocked_by_quote_or_spread`. runtime env와 PID `7079` env에서 `KORSTOCKSCAN_SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION=1200`, `KORSTOCKSCAN_SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION=1500`, `KORSTOCKSCAN_SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION=0.01` 로드를 확인했다. 그러나 장중 pipeline 기준 `budget_pass=512`, `latency_block=511`, `latency_pass=1`이며 latency reason은 `latency_state_danger=421`, `latency_fallback_deprecated=90`으로 submit 회복은 아직 미약하다.
  - 다음 액션: 장중 추가 완화는 금지한다. postclose에서 latency classifier profile의 missed/avoided attribution과 stale/price guard 분리를 다시 보고 `hold_sample|adjust_up|freeze`로 닫는다.

- [x] `[SimProbeIntradayCoverage0519] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-05-19`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-18.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-18.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 완료 메모 (`2026-05-19 10:51 KST`): `pass`. pipeline 기준 `actual_order_submitted=False` 이벤트 `33,003건`, threshold compact 기준 `31,272건`이며 `actual_order_submitted=True` 혼입은 없었다. sim/probe는 `scalp_sim_buy_order_assumed_filled=5`, `scalp_sim_holding_started=5`, `scalp_sim_sell_order_assumed_filled=2`, `scalp_sim_duplicate_buy_signal=506`, `wait65_79_ev_candidate=8`, `score65_74_recovery_probe=2`로 관찰됐다. `scalp_live_simulator_state.json` active position은 `3건`이고 `네이처셀(72)`, `엘앤케이바이오(66)`는 score65_74 probe, `에스엠(82)`은 AI BUY sim이다.
  - 다음 액션: sim/probe 손익은 postclose MFE/MAE/close/EV와 lifecycle matrix source로만 사용하고, broker execution 품질 또는 실주문 전환 근거로 단독 사용하지 않는다.

- [x] `[ScalpSimCandidateWindowExpansionOverride0519] 스캘핑 sim-only 후보 창 장중 확장 override 적용` (`Due: 2026-05-19`, `Slot: INTRADAY`, `TimeWindow: 12:20~12:30`, `Track: ScalpingLogic`)
  - Source: [threshold_runtime_env_2026-05-19.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-19.env), [threshold_runtime_env_2026-05-19.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-19.json), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py)
  - 판정 기준: 사용자 장중 override로 스캘핑 WAIT/blocked 후보를 실주문 없이 `scalp_sim_candidate_window_expansion` 관찰창에 편입하되, `actual_order_submitted=false`, `broker_order_forbidden=true`, `decision_authority=sim_observation_only`를 유지한다.
  - 금지: broker submit, real execution 품질 주장, live BUY 승격, threshold/provider/order guard 변경 근거로 사용하지 않는다.
  - 완료 메모 (`2026-05-19 12:22 KST`): `pass / operator_sim_only_override_applied`. `KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_EXPANSION_ENABLED=true`, score range `55~100`, `MAX_OPEN=20`, `MAX_DAILY=80`를 당일 runtime env/json에 추가했다. 코드에는 blocked AI score와 first AI wait 후보가 기존 scalp simulator 함수로만 편입되도록 구현했고, sim target/event에 원래 AI action/score/reason, source stage, blocked reason, `would_real_submit=false`를 남긴다. 봇 Python PID `7079`를 TERM으로 종료했고 `run_bot.sh`가 PID `63111`로 재기동했다. `/proc/63111/environ`에서 신규 env key 로드를 확인했다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_scalp_live_simulator.py src/tests/test_state_handler_fast_signatures.py` -> `48 passed, 2 warnings`; `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/sniper_state_handlers.py src/utils/constants.py src/utils/threshold_cycle_registry.py`; runtime env shell/JSON validation 및 `git diff --check` 통과.
  - 다음 액션: 장후 `sim_post_sell_evaluations`, `threshold_cycle_ev`, `lifecycle_decision_matrix`에서 `scalp_sim_candidate_window_expansion` cohort를 BUY/submit blocker별 MFE/MAE/close/EV로 분리한다.

- [x] `[ScalpSimTelegramSuppression0519] 스캘핑 sim-only 후보 텔레그램 BUY 알림 차단 확인` (`Due: 2026-05-19`, `Slot: INTRADAY`, `TimeWindow: 12:35~12:45`, `Track: ScalpingLogic`)
  - Source: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [test_state_handler_fast_signatures.py](/home/ubuntu/KORStockScan/src/tests/test_state_handler_fast_signatures.py)
  - 판정 기준: score65_74 probe, `scalp_sim_candidate_window_expansion`, 기존 scalp simulator 포지션처럼 `actual_order_submitted=false` 후보는 `TELEGRAM_BROADCAST` BUY 분석/주문 알림을 보내지 않고 suppression provenance만 남긴다.
  - 금지: sim/probe BUY를 사용자 알림에서 real BUY 후보처럼 표시하지 않는다.
  - 완료 메모 (`2026-05-19 12:45 KST`): `pass / sim_telegram_suppression_applied`. WATCHING AI `BUY` 분석 알림 발송 전 `_should_publish_watching_buy_analysis_telegram`을 추가해 simulation context, score65_74 probe source, candidate-window expansion, score cutoff 미달을 차단한다. 차단 시 `buy_analysis_telegram_suppressed` 이벤트에 reason과 `actual_order_submitted=false`, `broker_order_forbidden=true`를 남긴다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_state_handler_fast_signatures.py src/tests/test_scalp_live_simulator.py` -> `50 passed, 2 warnings`; `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/sniper_state_handlers.py src/tests/test_state_handler_fast_signatures.py`.
  - 다음 액션: 장후 sim cohort report에서 `buy_analysis_telegram_suppressed` count와 real `buy_signal_telegram_enqueued` count를 분리 확인한다.

- [x] `[ScalpSimAIBudgetManagerOverride0519] 스캘핑 sim-only holding AI 호출 예산 manager 장중 override 적용` (`Due: 2026-05-19`, `Slot: INTRADAY`, `TimeWindow: 13:20~13:35`, `Track: ScalpingLogic`)
  - Source: [threshold_runtime_env_2026-05-19.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-19.env), [threshold_runtime_env_2026-05-19.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-19.json), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [scalp_sim_ai_deferred_review.py](/home/ubuntu/KORStockScan/src/engine/scalp_sim_ai_deferred_review.py)
  - 판정 기준: `actual_order_submitted=false`인 `scalp_ai_buy_all` holding에만 AI call budget/reuse/deferred event가 적용되고, real holding/provider route/broker submit/B.U.Y. threshold는 변경하지 않는다.
  - 금지: real 주문 경로, broker guard, provider route, BUY/submit threshold 변경 근거로 사용하지 않는다.
  - 완료 메모 (`2026-05-19 13:37 KST`): `pass / operator_sim_only_override_applied`. `KORSTOCKSCAN_SCALP_SIM_AI_BUDGET_ENABLED=true`, `MAX_CALLS_PER_MIN=10`, holding cooldown `90/30/180s`, deferred review enabled를 runtime env/json과 operator lock에 추가했다. handler는 sim-only target에서 `scalp_sim_ai_holding_live_call|reuse|deferred`, `sim_ai_budget_exhausted`, `sim_ai_critical_bypass` provenance를 남기고, 장후 `scalp_sim_ai_deferred_review` artifact를 postclose chain에 연결한다. 봇 Python PID `65410`을 TERM으로 종료했고 `run_bot.sh`가 PID `87251`로 재기동했다. `/proc/87251/environ`에서 신규 env key와 OpenAI WS env 로드를 확인했다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_scalp_live_simulator.py src/tests/test_state_handler_fast_signatures.py` -> `54 passed, 2 warnings`; `RUN_OPENAI_LIVE_TESTS=1 PYTHONPATH=. .venv/bin/pytest -q src/tests/test_openai_live_sim_ai_budget.py` -> `1 passed`; `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/sniper_state_handlers.py src/utils/constants.py src/utils/threshold_cycle_registry.py src/engine/scalp_sim_ai_deferred_review.py src/engine/scalp_sim_ev_midcheck.py src/engine/daily_threshold_cycle_report.py`; `bash -n deploy/run_threshold_cycle_postclose.sh`; runtime env JSON/lock JSON validation, checklist parser, `git diff --check` 통과.
  - 다음 액션: 장후 `scalp_sim_ai_deferred_review`와 `scalp_sim_ev_midcheck`에서 live/reuse/deferred count를 분리한다.

- [x] `[EntryADMRuntimeEffectObserve0519] Entry ADM runtime effect 및 실제 API prompt 적용 재확인` (`Due: 2026-05-19`, `Slot: INTRADAY`, `TimeWindow: 10:00~10:20`, `Track: ScalpingLogic`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md), [scalp_entry_adm_runtime.py](/home/ubuntu/KORStockScan/src/engine/scalp_entry_adm_runtime.py), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py), [scalp_entry_action_decision_matrix_2026-05-18.json](/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-05-18.json)
  - 판정 기준: `/proc/<bot_pid>/environ` 또는 신규 event에서 `KORSTOCKSCAN_SCALP_ENTRY_ADM_ADVISORY_ENABLED=true`, `KORSTOCKSCAN_SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED=true` 로드를 확인하고, `analyze_target` actual API live 호출 또는 당일 live event에서 `entry_adm_prompt_applied=true`, `openai_endpoint_name=analyze_target`, `openai_schema_name=entry_v1`, `entry_adm_cache_token` prefix를 확인한다. 신규 cohort에 `entry_adm_runtime_effect`, `entry_adm_forced_action`, `entry_adm_runtime_reason`이 찍히는지도 분리 확인한다.
  - 금지: 실제 API smoke를 broker order submit, threshold mutation, provider 변경, bot restart 근거로 사용하지 않는다. `BUY_NOW`/`BUY_DEFENSIVE` positive bucket은 표본 충족 전 강제 BUY 승격으로 해석하지 않는다.
  - 완료 메모 (`2026-05-19 10:51 KST`): `pass / api_prompt_loaded_no_forced_effect`. 당일 이벤트에서 `entry_adm_status=advisory_prompt_applied`, `entry_adm_prompt_applied=True`, `entry_adm_cache_token=entry_adm:...`, `openai_endpoint_name=analyze_target`, `openai_schema_name=entry_v1`가 확인됐다. pipeline 기준 OpenAI provenance는 `analyze_target/entry_v1/ws_used=True/http_fallback=False 1,723건`, `holding_exit_v1 116건`, `entry_price_v1 13건`이다. Entry ADM runtime effect는 `non_buy_action_passthrough=2,130`, `no_matching_runtime_bias=6`, forced action은 관찰되지 않았다.
  - 다음 액션: Entry ADM은 현재 BUY 승격이 아니라 advisory/passthrough 위주로 동작 중이다. forced WAIT/DROP 또는 positive bucket 효과는 postclose `scalp_entry_action_decision_matrix`와 lifecycle matrix source join 이후 재판정한다.

- [x] `[IntradayAutomationHealthCheck20260519] 장중 자동화체인 상태 확인` (`Due: 2026-05-19`, `Slot: INTRADAY`, `TimeWindow: 09:05~15:30`, `Track: RunbookOps`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md#장중-확인-절차)
  - 판정: `warning`
  - 근거: pipeline/threshold JSONL은 10:50 KST까지 append 중이고 봇 PID `7079`가 살아 있다. BUY funnel sentinel, holding/exit sentinel, panic sell defense, panic buying report는 반복 `[DONE]` marker와 report artifact를 생성했다. panic sell은 `RECOVERY_WATCH`, panic buying은 `NORMAL`, 둘 다 `runtime_effect=report_only_no_mutation`이다. `threshold_cycle_calibration_intraday`는 12:05 작업이라 10:51 KST 기준 아직 `not_yet_due`이며 fail이 아니다. 장중 runtime mutation/rollback-like 이벤트는 관찰되지 않았다.
  - 다음 액션: 12:05 이후 `threshold_cycle_calibration_intraday_cron.log`의 `[DONE] threshold-cycle calibration target_date=2026-05-19 phase=intraday`를 별도 확인한다. Sentinel/panic 경고는 report-only로 유지하고 threshold/provider/order/bot 변경 근거로 쓰지 않는다.

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

- [x] `[ScalpSimAIBudgetCriticalBypassReview0519] sim holding AI critical bypass 과다 및 deferred 기준 개선 검토` (`Due: 2026-05-19`, `Slot: POSTCLOSE`, `TimeWindow: 16:55~17:10`, `Track: ScalpingLogic`)
  - Source: [scalp_sim_ev_midcheck_2026-05-19.json](/home/ubuntu/KORStockScan/data/report/scalp_simulator/scalp_sim_ev_midcheck_2026-05-19.json), [scalp_sim_ai_deferred_review_2026-05-19.json](/home/ubuntu/KORStockScan/data/report/scalp_sim_ai_deferred_review/scalp_sim_ai_deferred_review_2026-05-19.json), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [scalp_sim_ai_deferred_review.py](/home/ubuntu/KORStockScan/src/engine/scalp_sim_ai_deferred_review.py)
  - 판정 기준: `scalp_sim_ai_holding_live_call`, `sim_ai_critical_bypass`, `scalp_sim_ai_holding_deferred`, `sim_ai_budget_exhausted` count와 call_reason을 분리하고, 단순 `profit_rate < 0`로 인한 critical bypass와 soft/hard stop 근접, drawdown 급변, max cooldown 초과를 구분한다.
  - 금지: 장중 critical 조건 변경, real holding/exit 변경, provider route 변경, BUY/submit threshold 변경, broker guard 우회 근거로 사용하지 않는다.
  - 완료 메모 (`2026-05-19 15:32 KST`): `pass / implemented_sim_only_classifier_correction_pending_postclose_attribution`. 15시 수치 `live=1315`, `deferred=25`, `critical_bypass=1293`, `reuse=0`에서 현행화 시 pipeline 기준 `live=1749+`, `deferred=35`, `critical_bypass=1725+`, `reuse=0`로 critical bypass가 과다했다. 원인은 `profit_rate < 0` 전체를 critical로 보아 cap을 우회한 것이다. 구현은 sim-only budget target에만 적용했고 `hard_critical|soft_critical|non_critical` 분류, `KORSTOCKSCAN_SCALP_SIM_AI_HARD_CRITICAL_MIN_LOSS_PCT`, `KORSTOCKSCAN_SCALP_SIM_AI_SOFT_LOSS_DEFER_ENABLED`, `KORSTOCKSCAN_SCALP_SIM_AI_SAFE_PROFIT_BYPASS_ENABLED`, `KORSTOCKSCAN_SCALP_SIM_AI_CRITICAL_DRAWDOWN_PCT` env hook, `critical_class|critical_reason|loss_bucket|drawdown_pct` attribution을 추가했다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_scalp_live_simulator.py src/tests/test_state_handler_fast_signatures.py src/tests/test_scalp_sim_ev_midcheck.py src/tests/test_scalp_sim_ai_deferred_review.py` -> `61 passed, 2 warnings`; `RUN_OPENAI_LIVE_TESTS=1 PYTHONPATH=. .venv/bin/pytest -q src/tests/test_openai_live_sim_ai_budget.py` -> `1 passed`; py_compile 및 `/tmp` report generation 검증 통과.
  - 다음 액션: 장후 실제 postclose 산출물에서 새 attribution은 구현 이후 이벤트부터 hard/soft/non-critical로 분리된다. 기존 5/19 과거 이벤트는 필드가 없어 `unknown`으로 남기는 것이 정상이며, real holding/provider/B.U.Y./submit/broker guard는 변경하지 않는다.

- [x] `[ScalpSimOvernightAIPlusCarry0519] 스캘핑 sim-only overnight AI+carry 및 자동화체인 source 편입` (`Due: 2026-05-19`, `Slot: POSTCLOSE`, `TimeWindow: 15:30~16:10`, `Track: ScalpingLogic`)
  - Source: [scalp_live_simulator_state.json](/home/ubuntu/KORStockScan/data/runtime/scalp_live_simulator_state.json), [scalp_sim_overnight.py](/home/ubuntu/KORStockScan/src/engine/scalp_sim_overnight.py), [scalp_sim_overnight_2026-05-19.json](/home/ubuntu/KORStockScan/data/report/scalp_sim_overnight/scalp_sim_overnight_2026-05-19.json), [lifecycle_decision_matrix.py](/home/ubuntu/KORStockScan/src/engine/lifecycle_decision_matrix.py)
  - 판정 기준: `actual_order_submitted=false`, `simulation_book=scalp_ai_buy_all`, `status=HOLDING` active sim만 `overnight_v1` 판단 대상으로 삼고, `SELL_TODAY`는 sim 가상 청산, `HOLD_OVERNIGHT`는 active carry로 유지한다.
  - 금지: real overnight gatekeeper, broker 주문, provider route, BUY/submit threshold, real holding/exit 로직을 변경하지 않는다. 자동화체인 편입은 source bundle/lifecycle matrix 입력까지만 허용하고 threshold-cycle auto-apply family로 만들지 않는다.
  - 완료 메모 (`2026-05-19 16:05 KST`): `warning / ai_timeout_fallback_sell_today_completed`. runner/report/restore event/postclose wrapper/lifecycle adapter를 구현했다. one-shot 실행 전 active sim은 `13건`이었고 dry-run 대상도 `13건`으로 확인됐다. 실제 `--live-openai` one-shot에서는 OpenAI overnight 호출이 5회 연속 timeout 후 engine disabled가 되어 설계된 실패 정책대로 `SELL_TODAY` fallback 가상 청산을 적용했다. 결과는 `decision=13`, `sell_today=13`, `hold_overnight=0`, `sell_assumed_filled=13`, `carry_open_count=0`, state active `0건`이다. Telegram 발송은 없다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_scalp_sim_overnight_gatekeeper.py src/tests/test_scalp_sim_overnight_report.py src/tests/test_scalp_sim_ev_midcheck.py src/tests/test_scalp_sim_ai_deferred_review.py` -> `10 passed`; `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_scalp_live_simulator.py src/tests/test_state_handler_fast_signatures.py src/tests/test_scalp_sim_ev_midcheck.py src/tests/test_scalp_sim_ai_deferred_review.py` -> `61 passed, 2 warnings`; `RUN_OPENAI_LIVE_TESTS=1 PYTHONPATH=. .venv/bin/pytest -q src/tests/test_openai_live_sim_ai_budget.py` -> `2 passed`; `py_compile`, `bash -n deploy/run_threshold_cycle_postclose.sh` 통과.
  - 다음 액션: postclose 본체에서 `scalp_sim_overnight`, `scalp_sim_ev_midcheck`, `lifecycle_decision_matrix`, `threshold_cycle_ev`, `runtime_approval_summary`가 source-only로 이어지는지 재확인한다. 오늘 overnight AI timeout은 provider 변경/threshold 변경 근거가 아니라 운영 incident/provenance로만 분리한다.

- [ ] `[HumanInterventionSummary0519] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-05-19`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-18.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-18.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[LifecycleDecisionMatrixRuntime0519] lifecycle decision matrix postclose 산출 및 다음 PREOPEN bounded apply 연결 확인` (`Due: 2026-05-19`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:35`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md), [lifecycle_decision_matrix.py](/home/ubuntu/KORStockScan/src/engine/lifecycle_decision_matrix.py), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py)
  - 판정 기준: `lifecycle_decision_matrix_2026-05-19.{json,md}` 생성, `threshold_cycle_ev`/`runtime_approval_summary` source link, fixed threshold role contract, hard safety passthrough, selected/not-applied attribution을 확인한다.
  - 금지: score bucket 고정 정책, score 단조 EV 가정, hard safety override, 장중 threshold mutation, sim-only real execution 품질 주장.
  - 다음 액션: `pass`, `hold_sample`, `hold_no_edge`, `source_quality_blocker`, `runtime_env_mapping_gap` 중 하나로 닫고, selected되면 다음 PREOPEN env의 policy file/version/promote cap을 확인한다.

- [ ] `[ScalpSimScaleInMatrixFrameworkPrep0519] 스캘핑 sim scale-in 확대 전 lifecycle matrix scale_in source 귀속 확인` (`Due: 2026-05-19`, `Slot: POSTCLOSE`, `TimeWindow: 17:35~17:50`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md), [lifecycle_decision_matrix.py](/home/ubuntu/KORStockScan/src/engine/lifecycle_decision_matrix.py), [scalp_sim_ev_midcheck.py](/home/ubuntu/KORStockScan/src/engine/scalp_sim_ev_midcheck.py)
  - 판정 기준: `scalp_sim_scale_in_order_assumed_filled/unfilled`가 `lifecycle_decision_matrix`의 `stage=scale_in` row로 들어가고, add type/가격/수량은 runtime feature, final exit profit/post-add MFE/MAE는 label 전용으로 분리되는지 확인한다.
  - 금지: scale-in window 확대를 고정 threshold 정책, 실주문 scale-in, 수량 cap 해제, hard safety 완화, 장중 threshold mutation 근거로 쓰지 않는다.
  - 다음 액션: framework source 귀속이 `pass`면 `data/threshold_cycle/approvals/scalp_sim_scale_in_window_expansion_2026-05-19.json` 승인 artifact를 확인한다. 사용자가 `approved=true`로 승인한 경우에만 다음 영업일 PREOPEN `threshold_cycle_preopen_apply`가 `KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_*` env를 쓰며, source gap이면 actuator보다 adapter/test 보강을 우선한다.

- [ ] `[ShadowCanaryCohortReview0519] shadow/canary/cohort 런타임 분류 및 정리 판정` (`Due: 2026-05-19`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: Plan`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: 당일 변경/관찰 결과를 기준으로 `remove`, `observe-only`, `baseline-promote`, `active-canary` 상태 변동 여부를 닫는다.
  - 금지: shadow 금지, canary-only, baseline 승격 원칙을 코드/문서 상태와 분리하지 않는다.
  - 완료 메모 (`2026-05-19 15:10 KST`): `pass / active_shadow_none_runtime_shadow_refs_are_off_or_report_only`. `threshold_runtime_env_2026-05-19.json` 기준 active shadow env는 없고, constants의 shadow류(`hard_time_stop`, `partial_only_timeout`, `same_symbol_soft_stop_cooldown`, split-entry, dual-persona)는 기본 OFF다. `workorder-shadow-canary-runtime-classification.md`를 5/19 기준으로 현행화해 `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `scalp_sim_scale_in_window_expansion`을 shadow가 아닌 sim-only cohort/approval-required actuator로 잠갔다.
  - 다음 액션: 남은 shadow 명칭은 runtime owner가 아니라 OFF/historical/report-only cleanup 후보로 관리한다. 신규 shadow 경로를 열지 않고, sim-only cohort는 lifecycle matrix/source bundle attribution으로만 판정한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-05-19 15:47:01`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-05-19.md`
- `Trade Review`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Performance Tuning`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Post Sell Feedback`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Entry Pipeline Flow`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
<!-- AUTO_SERVER_COMPARISON_END -->
