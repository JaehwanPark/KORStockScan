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
  - 판정 기준: EV보다 먼저 데이터 수집/소비 계약을 확인한다. `max_daily=160`과 reserve/bucket quota 적용 후 postclose LDM의 `stage sample`, `joined_sample`, `join_rate`, `action_namespace`, `source_stage`, `risk_context_owner`, `risk_direction` bucket coverage를 확인한다. stage floor만 통과한 상태가 아니라 entry/scale_in/exit와 panic/euphoria action bucket이 한쪽으로 과도하게 쏠리지 않았는지 본 뒤 `240` 상향 후보 여부를 결정한다.
  - 필수 확인: `sim_record_id` join rate, `sim_parent_record_id` 연결률, stage별 소비율(`entry -> holding -> scale_in -> exit`), `scalp_sim_candidate_window_discarded` reason 분포(`time_bucket_quota_reached`, `max_open_reached` 등), `scalp_sim_duplicate_buy_signal` 비중, time bucket quota 조기 소진 여부(`09:00-10:00=56`, 이후 bucket), `actual_order_submitted=false`/`broker_order_forbidden=true` 유지 여부를 기록한다.
  - 자동화 보강 메모 (`2026-05-21 KST`): [lifecycle_decision_matrix.py](/home/ubuntu/KORStockScan/src/engine/lifecycle_decision_matrix.py)는 `entry_bucket_attribution`을 생성해 `score_band/source_stage/stale/liquidity/strength/overbought/time_bucket/combo_entry_spot`별 `source_quality_adjusted_ev_pct`, `MFE/MAE/close`, `runtime_approval_candidates`, `code_improvement_workorders`를 source-only로 노출한다. 후보는 `approval_required=true`, `allowed_runtime_apply=false`이며 rolling/cumulative 확인 전 단독 runtime apply 권한이 없다.
  - AI budget 확인: [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)의 `scalp_sim_ai_budget_manager` 계약에 따라 `scalp_sim_ai_holding_live_call`, `scalp_sim_ai_holding_reuse`, `scalp_sim_ai_holding_deferred`, `sim_ai_budget_exhausted`, `sim_ai_critical_bypass`를 집계하고, deferred/exhausted feature packet이 장후 `scalp_sim_ai_deferred_review` 또는 LDM source row로 소비됐는지 확인한다. AI 호출 절약이 `sim_record_id`/stage/action bucket 누락으로 이어졌으면 `defer_source_quality_or_bucket_skew`로 닫고 source-quality workorder 후보를 남긴다.
  - 금지: `240` 상향을 장중 runtime env 직접 수정, restart만으로 적용, real order enable, Telegram BUY/SELL, provider route, bot restart trigger로 연결하지 않는다.
  - 다음 액션: `keep_160_coverage_enough`, `preopen_candidate_240`, `hold_160_until_persistent_counter_fixed`, `defer_source_quality_or_bucket_skew` 중 하나로 닫고, `preopen_candidate_240`이면 다음 PREOPEN `threshold_cycle_preopen_apply` 확인 항목을 생성한다.

- [ ] `[BedrockNovaMicroBypassPromotionReview0521] OpenAI nano 호출 지점의 Bedrock Nova Micro 우회 정식 승격 여부 판단` (`Due: 2026-05-21`, `Slot: POSTCLOSE`, `TimeWindow: 17:40~18:05`, `Track: AITransport`)
  - Source: [bedrock_nova_micro_shadow_report_2026-05-21.json](/home/ubuntu/KORStockScan/data/report/bedrock_nova_micro_shadow/bedrock_nova_micro_shadow_report_2026-05-21.json), [bedrock_nova_micro_shadow_report_2026-05-21.md](/home/ubuntu/KORStockScan/data/report/bedrock_nova_micro_shadow/bedrock_nova_micro_shadow_report_2026-05-21.md), [bedrock_nova_micro_shadow_2026-05-21.jsonl](/home/ubuntu/KORStockScan/data/report/bedrock_nova_micro_shadow/bedrock_nova_micro_shadow_2026-05-21.jsonl), [sim_post_sell_candidates_2026-05-21.jsonl](/home/ubuntu/KORStockScan/data/post_sell/sim_post_sell_candidates_2026-05-21.jsonl), [bedrock_nova_provider.py](/home/ubuntu/KORStockScan/src/engine/bedrock_nova_provider.py), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py)
  - 판정 기준: `outcome_linked_performance`의 exact `sim_record_id` matched sample을 primary로 보고, `entry/watch`, `scalp_sim_holding_review`, `unknown/no-stage`를 분리한다. `nova_minus_openai_outcome_score`, `nova_edge_count/openai_edge_count/tie_count`, stage별 `avg_profit_rate`, action confusion, parse_ok_rate, cache 포함 cost ratio, p50/p90/p95 latency를 함께 확인한다.
  - 코드 준비 확인: Micro 승격은 `KORSTOCKSCAN_BEDROCK_NOVA_MICRO_ROUTE_MODE=primary`만 사용하고 Lite 승격과 분리한다. Micro primary 성공 시 OpenAI 호출과 Micro shadow enqueue가 발생하지 않아야 하며, Bedrock primary 실패 후 OpenAI failback 시에도 같은 모델 shadow 재호출로 중복 지출하지 않아야 한다.
  - 표본 기준: exact outcome match가 부족하거나 stage별 표본이 한쪽에 쏠리면 `defer_source_quality_gap` 또는 `keep_shadow_collecting`으로 닫는다. unmatched row, 근접 시간 매칭, instrumentation 이전 row는 승격 근거가 아니라 join-quality 보완 근거로만 쓴다.
  - 금지: 장중 provider route 변경, threshold 변경, 주문 판단 변경, real order enable, bot restart trigger, OpenAI route 즉시 대체, Lite 승격과 합산 판단, 튜닝체인 자동 apply 연결 금지. 승격 후보가 나오면 별도 approval/workorder와 rollback guard를 만든 뒤 다음 PREOPEN 후보로만 넘긴다.
  - 다음 액션: `promote_candidate_requires_approval`, `keep_shadow_collecting`, `reject_provider_bypass`, `defer_source_quality_gap` 중 하나로 닫고, 승격 후보일 경우 `target_stage`, `baseline cohort`, `candidate provider cohort`, `observe-only cohort`, `excluded cohort`, `rollback owner`, `cross-contamination check`를 함께 기록한다.

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

- `PanicSellNotifyStaleReleaseGuard0521` 패닉셀 해제 알림 stale state 오발송 방지
  - Source: [notify_panic_state_transition.py](/home/ubuntu/KORStockScan/src/engine/notify_panic_state_transition.py), [panic_sell_defense_2026-05-21.json](/home/ubuntu/KORStockScan/data/report/panic_sell_defense/panic_sell_defense_2026-05-21.json), [market_panic_breadth_2026-05-21.json](/home/ubuntu/KORStockScan/data/report/market_panic_breadth/market_panic_breadth_2026-05-21.json)
  - 판정: `stale_previous_active_release_suppressed`
  - 근거: 2026-05-21 09:12 리포트는 KOSPI/KOSDAQ 약 `+4.37%`, 상승 종목 비율 80%대, `panic_state=NORMAL`, `panic_detected=false`, `risk_off_advisory=false`, `risk_on_advisory=true`였으나 이전 날짜 active notify state가 남으면 해제 알림만 전송될 수 있었다. notifier state에 `session_key`를 저장하고 이전 active session이 현재 report date와 다르면 release를 보내지 않고 `stale_previous_active_reset`으로 닫도록 보강했다.
  - 금지: 패닉셀 해제 알림을 runtime threshold/order/provider/bot 변경 근거로 쓰지 않는다. 같은 날짜/session에서 active start/update 알림이 선행된 경우에만 해제 알림을 허용한다.
  - 검증: `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_notify_panic_state_transition.py -q` 통과.

- `MarketRegimeContinuousScoreV10521` 시장국면 연속 점수 및 ADM/LDM risk-context 연결 1차 개발
  - Source: [rules.py](/home/ubuntu/KORStockScan/src/market_regime/rules.py), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [lifecycle_decision_matrix.py](/home/ubuntu/KORStockScan/src/engine/lifecycle_decision_matrix.py), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정: `context_only_first_pass`
  - 근거: 기존 `swing_score` gate는 `swing_entry_recovery_gate_score`로 보존하고, `market_regime_continuous_score/label/component_scores`를 daily report/cache와 LDM runtime feature에 병렬 추가했다. `market_regime_continuous_thresholds` family는 source bundle과 calibration candidate를 만들지만 `allowed_runtime_apply=false`, `runtime_effect=false`로 시작한다.
  - 금지: 연속 점수 단독 BUY/SELL/scale-in 확정, hard safety/broker/stale quote/price freshness/stop/qty/cooldown guard 우회, 장중 env mutation, provider route/bot restart 변경 금지.
  - 다음 액션: 자체 코드리뷰 finding은 즉시 보완하고, 2차 review pass 전까지 `KORSTOCKSCAN_MARKET_REGIME_*` env apply 승격을 열지 않는다.

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

- `IntradayAutomationHealthCheck20260521` 장중 자동화체인 상태 확인
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md) `장중 확인 절차`
  - 판정: `pass`
  - 근거: `2026-05-21 09:18 KST` 기준 error detector dry-run은 `summary_severity=pass`다. `process_health=pass`로 `bot_main.py` PID `4069`, main loop age 약 `1.2s`, `telegram/crisis_monitor/sniper_engine/scalping_scanner/error_detection` thread가 모두 alive였다. `artifact_freshness=pass`로 `pipeline_events_age_sec=0.0`, `threshold_events_age_sec=0.0`, sentinel/panic report freshness가 정상이고, `cron_completion=pass`에서 장중 전까지 도래한 sentinel/panic 계열 cron은 정상 완료됐다.
  - 금지: 장중 확인 결과를 runtime threshold/order/provider/bot 변경으로 연결하지 않는다. `threshold_cycle_calibration_intraday`와 장후 체인은 당시 `not_yet_due`로 별도 postclose/12:05 확인 owner가 소유한다.
  - 테스트/검증: `PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode full --dry-run` 통과. `data/pipeline_events/pipeline_events_2026-05-21.jsonl`와 `data/threshold_cycle/threshold_events_2026-05-21.jsonl` append freshness를 확인했다.
  - 다음 액션: 장중 운영 확인은 `pass`로 닫고, 12:05 calibration과 postclose R1~R6는 기존 POSTCLOSE/RunbookOps 항목에서 확인한다.

- `BuySignalTelegramReceiptBoundary0521` BUY 신호/체결 Telegram 경계 정리
  - Source: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [test_sniper_scale_in.py](/home/ubuntu/KORStockScan/src/tests/test_sniper_scale_in.py), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정: `signal_only_before_fill_receipt_only_after_fill`
  - 근거: `2026-05-21 09:12 KST` 엘앤씨바이오(290650)는 원 매수주문 `0017489`가 접수된 뒤 약 29초 후 같은 원주문에 대한 취소주문 `0017596`이 성공했다. 기존 Telegram 문구가 `BUY 신호/주문 제출`, `주문수량`이라 미체결 취소 주문도 뒤늦게 제출 완료처럼 보일 수 있었다.
  - 변경: 체결 전 알림은 `BUY 신호 감지`, `후보수량`으로만 표기하고 `주문 제출` 표현을 제거했다. BUY 신호 외의 실거래 Telegram은 실제 체결 receipt 확인 후 발송한다는 운영 계약을 runbook에 명시했다.
  - 금지: Telegram 수신 순서만으로 주문/체결/취소 원천 상태를 판정하지 않는다. 원천 증적은 Kiwoom receipt, DB, pipeline event를 우선한다.
  - 검증: `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_sniper_scale_in.py -k "publish_buy_signal_submission_notice or buy_execution_thread_receives_snapshot" -q` 통과.

## 장중 체크리스트 (09:05~15:20)

- [x] `[RuntimeEnvIntradayObserve0521] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-05-21`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-20.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-20.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, latency_classifier_runtime_profile, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 실행 메모 (`2026-05-21 09:18 KST`): [threshold_apply_2026-05-21.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-21.json)은 `status=auto_bounded_live_ready`, `apply_mode=auto_bounded_live`, `runtime_change=true`, `approval_requests=[]`, `approval_contract_gaps=[]`다. [threshold_runtime_env_2026-05-21.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-21.env)는 `lifecycle_decision_matrix_runtime`, `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `scalp_sim_scale_in_window_expansion`, `soft_stop_whipsaw_confirmation`, `score65_74_recovery_probe` env를 포함하고, LDM action mutation은 `KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_RUNTIME_EFFECT_ENABLED=false`로 유지한다.
  - 판정 결과: `pass_provenance_present_no_rollback_breach`. 당일 pipeline event에서 `lifecycle_decision_matrix_runtime` 1081건, `scalp_sim_candidate_window_expansion` 236건, `soft_stop_whipsaw_confirmation` 16건, `latency_classifier_runtime_profile` 6건, `scalp_sim_scale_in_window_expansion` 11건이 확인됐다. `scalp_sim_ai_budget_manager`는 env enabled와 deferred review 설정은 확인됐지만 09:18 기준 별도 family 문자열 event는 아직 없으므로 `runtime_env_present_event_pending`으로 postclose budget report에서 재확인한다. rollback/safety breach 유사 이벤트는 0건이다.
  - 다음 액션: 장중 runtime mutation 금지를 유지하고, postclose `ThresholdDailyEVReport0521`에서 selected/not-applied attribution과 budget event coverage를 재확인한다.

- [x] `[SimProbeIntradayCoverage0521] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-05-21`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-20.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-20.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 실행 메모 (`2026-05-21 09:18 KST`): 당일 pipeline event의 sim/probe 전체 후보성 row는 2059건이고, 주문형 sim/probe row 1603건은 모두 `actual_order_submitted=false`, `broker_order_forbidden=true`였다. source-quality/authority 계약은 주문형 row 1602건에서 확인됐고, 누락 1건은 order authority 변경이 아닌 source-quality 계측 보강 후보로만 본다.
  - 판정 결과: `pass_sim_order_provenance_separated`. `scalp_sim_candidate_window_expansion`은 `scalp_sim_entry_armed`, `scalp_sim_buy_order_virtual_pending`, `scalp_sim_buy_order_assumed_filled`, `scalp_sim_holding_started` 등으로 real execution과 분리됐다. state restore/persist 계열 일부는 `actual_order_submitted` 필드가 없지만 주문형 row가 아니므로 broker execution 품질 판정에 쓰지 않는다.
  - 다음 액션: postclose LDM joined/action bucket coverage와 source-quality split을 `ScalpSimLdmMaxDaily240Review0521`에서 다시 확인하고, sim/probe EV 단독 실주문 전환은 계속 금지한다.

## 장후 체크리스트 (16:30~18:55)

- [x] `[ScalpSimPanicLifecycleL1FullExitGuard0521] L1 panic sim partial의 full-exit 승격 차단` (`Due: 2026-05-21`, `Slot: INTRADAY`, `TimeWindow: 11:40~11:55`, `Track: RuntimeStability`)
  - Source: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [test_scalp_sim_panic_lifecycle.py](/home/ubuntu/KORStockScan/src/tests/test_scalp_sim_panic_lifecycle.py), [panic_sell_defense_2026-05-21.json](/home/ubuntu/KORStockScan/data/report/panic_sell_defense/panic_sell_defense_2026-05-21.json), [market_panic_breadth_2026-05-21.json](/home/ubuntu/KORStockScan/data/report/market_panic_breadth/market_panic_breadth_2026-05-21.json)
  - owner/status: `scalp_sim_panic_lifecycle`, `sim_only`, `runtime_effect=simulated_state_only`, `decision_authority=sim_observation_only`
  - 근거: 당일 report는 `panic_state=NORMAL`, `panic_regime_mode=NORMAL`, market breadth `risk_off_advisory=false`인데 `panic_epoch_id=NORMAL|NORMAL|L1` sim row에서 `scalp_sim_panic_lifecycle_full_exit`가 발생했다. L1 partial이 소량 포지션에서 full exit로 승격되는 경로를 차단한다.
  - 금지: real auto-sell, order cancel, threshold/provider/bot 변경, 실계좌 holding 강제 축소/청산 금지.
  - 검증 결과: `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_scalp_sim_panic_lifecycle.py src/tests/test_bedrock_nova_micro_shadow.py src/tests/test_bedrock_nova_micro_shadow_report.py -q`, `py_compile`, `git diff --check`, checklist parser 검증 통과.
  - 판정 결과: `implemented_l1_no_full_exit_escalation`. L1에서 partial 후 잔량이 `min_remaining` 미만이면 full exit 대신 `scalp_sim_panic_level1_partial_skipped_min_remaining`와 `TRAIL_TIGHT` 상태만 남긴다.

- [x] `[BedrockNovaMicroShadowObservation0521] gpt-5-nano Tier1 호출 대상 Nova Micro shadow 비교 구현/검증` (`Due: 2026-05-21`, `Slot: POSTCLOSE`, `TimeWindow: 18:10~18:25`, `Track: RuntimeStability`)
  - Source: [bedrock_nova_micro_shadow.py](/home/ubuntu/KORStockScan/src/tests/bedrock_nova_micro_shadow.py), [bedrock_nova_micro_shadow_report.py](/home/ubuntu/KORStockScan/src/tests/bedrock_nova_micro_shadow_report.py), [data/report/README.md](/home/ubuntu/KORStockScan/data/report/README.md), [config_prod.json](/home/ubuntu/KORStockScan/data/config_prod.json)
  - owner/status: `bedrock_nova_micro_shadow_observation`, `report_only`, `runtime_effect=false`, `decision_authority=shadow_observation_only`
  - 판정 기준: 기본 설계는 토글 기반이며, 사용자가 당일 남은 시간 shadow 수집을 명시해 `run_bot.sh`에서 enable한 운영 세션만 `gpt-5-nano` Tier1 JSON 호출을 Nova Micro 비동기 shadow enqueue 대상으로 본다. OpenAI primary result/order flow/threshold/provider route가 변경되지 않아야 한다. 장후 report는 latency, cost, prompt cache, action agreement, parse/schema quality, tuning linkage join key를 제공해야 한다.
  - 금지: provider route 변경, threshold 변경, 주문 판단 변경, bot restart trigger, threshold-cycle 자동 apply 연결 금지.
  - 검증: `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_bedrock_nova_micro_shadow.py src/tests/test_bedrock_nova_micro_shadow_report.py -q`, `py_compile`, checklist parser 검증을 실행한다.
  - 실행 메모: `bedrock_nova_micro_shadow_observation` 구현 완료. `src/tests`의 Bedrock 전용 모듈이 JSONL/report를 소유하고, 운영 engine에는 `KORSTOCKSCAN_BEDROCK_NOVA_MICRO_SHADOW_ENABLED`가 켜진 경우 `gpt-5-nano` JSON 결과 반환 뒤에만 enqueue하는 최소 hook을 둔다. `config_prod.json`에는 장기 테스트 API key 입력용 `BEDROCK_API_KEY`를 사용하고, 기본 region은 한국 `ap-northeast-2`, 기본 model id는 한국 리전에서 호출 가능한 APAC inference profile `apac.amazon.nova-micro-v1:0`다. 장후 report CLI는 `PYTHONPATH=. .venv/bin/python -m src.tests.bedrock_nova_micro_shadow_report --date YYYY-MM-DD`다.
  - cache 준비: `KORSTOCKSCAN_BEDROCK_NOVA_MICRO_PROMPT_CACHE_ENABLED=true`이면 Nova system prompt 뒤에 Bedrock explicit `cachePoint`를 추가하고, JSONL/report에 `nova_cache_read_input_tokens`, `nova_cache_write_input_tokens`, `nova_total_input_tokens`를 남긴다. 비용 계산은 cache read/write 단가 env override를 허용하며, prompt cache는 shadow observation 비용/latency 계측용일 뿐 provider route/order/threshold를 바꾸지 않는다.
  - join key 보강: 장후 sim lifecycle 교차분석을 위해 shadow JSONL/report에 `record_id`, `sim_record_id`, `sim_parent_record_id`, `entry_adm_candidate_id`, `source_event_stage`를 남긴다. 기존 row는 소급 보정하지 않고 보강 이후 row부터 적용한다.
  - 코드리뷰 결과: OpenAI primary payload 반환 후 비동기 enqueue만 수행하며 queue/AWS/cache/parse 실패는 shadow artifact로만 남긴다. 남은 high/medium finding 없음.
  - 검증 결과: `pytest` 대상 24건 통과, shadow report test 1건 통과, cache 준비 후 `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_bedrock_nova_micro_shadow.py src/tests/test_bedrock_nova_micro_shadow_report.py -q` 8건 통과, `py_compile`, `git diff --check`, `sync_docs_backlog_to_project --print-backlog-only --limit 500` 통과.
  - 다음 액션: `implemented_operator_enabled_shadow_only`, `hold_review_finding`, `blocked_dependency_or_credentials`, `reject_primary_path_risk` 중 하나로 닫는다.
  - 판정 결과: `implemented_operator_enabled_shadow_only`. 실제 장중 수집은 AWS credentials/region 권한이 준비되고 사용자가 env enable을 지시한 운영 세션에서만 시작하며, `decision_authority=shadow_observation_only`와 `runtime_effect=false`를 유지한다.

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
