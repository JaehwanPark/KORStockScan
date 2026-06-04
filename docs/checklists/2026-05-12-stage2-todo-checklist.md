# 2026-05-12 Stage2 To-Do Checklist

## 오늘 목적

- 2026-05-11 postclose 자동화가 만든 threshold apply 후보와 OpenAI WS 유지 상태를 장전 산출물 기준으로 확인한다.
- 스윙 실주문, 스윙 숫자 floor, 스윙 scale-in real canary는 approval request가 없으므로 사용자 artifact 없이 열지 않는다.
- 2026-05-11 code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.
- 장중 패닉셀 구간은 closed PnL 단독으로 보지 않고 `panic_sell_defense` report-only 산출물에서 방어/회복 attribution을 분리한다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- OpenAI WS 확인은 transport/provenance 검증이며 threshold 값, 주문가/수량 guard, 스윙 dry-run guard를 변경하지 않는다.
- `actual_order_submitted=false`인 sim/probe 표본은 실주문 전환 근거가 아니라 EV/source-quality 입력이다. 실주문 전환은 별도 approval artifact와 checklist가 필요하다.
- `panic_sell_defense`는 runtime mutation, bot restart, score/stop threshold 변경 권한이 없는 report-only 입력이다.
- 스윙 동일종목 손실 후 재진입 guard는 threshold 튜닝이 아니라 mandatory pre-submit safety이며, 막힌 후보는 `swing_reentry_counterfactual_after_loss`로만 남긴다.
- 스윙 `blocked_swing_gap`/`blocked_swing_score_vpw`/`blocked_gatekeeper_reject`는 각각 독립 튜닝 후보로 쪼개지 않고 `swing_blocked_origin_quality_guard` 단일 family 후보로 묶어 본다. 세부 origin은 threshold 기준이 아니라 attribution/cohort tag로만 사용한다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

## 장전 체크리스트 (08:50~09:00)

- Runbook 운영 확인은 [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md) `장전 확인 절차`와 `build_codex_daily_workorder --slot PREOPEN`의 `PreopenAutomationHealthCheckYYYYMMDD` 블록을 기준으로 본다.

### PreopenAutomationHealthCheck20260512 운영 확인 기록

- checked_at: `2026-05-12 08:36 KST`
- 판정: `warning`
- 근거: `threshold_cycle_preopen_cron.log`의 `[DONE] threshold-cycle preopen target_date=2026-05-12` marker, `threshold_apply_2026-05-12.json`의 `auto_bounded_live_ready`, runtime env 파일 생성, `run_bot.sh`의 당일 runtime env source, PID `4493` 환경변수 로드를 확인했다. 스윙 추천 생성은 `final_ensemble_scanner target_date=2026-05-12` `[DONE]` marker와 CSV 3개 우선 적재 로그를 확인했다.
- warning 사유: OpenAI `entry_price` transport provenance는 2026-05-11 리포트 기준 instrumentation gap이 남아 있고, 2026-05-12 08:36 KST 현재 장전이라 신규 `entry_price` 표본은 아직 없다. 또한 장전 error detector의 artifact freshness boundary 경고는 산출물 자체 실패가 아니라 detector 경계 판정 이슈로 분리한다.

- [x] `[ThresholdEnvAutoApplyPreopen0512] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-05-12`, `Slot: PREOPEN`, `TimeWindow: 08:50~09:00`, `Track: RuntimeStability`)
  - Source: [README.md](/home/ubuntu/KORStockScan/data/threshold_cycle/README.md), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_threshold_cycle_preopen.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_preopen.sh), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 트리거: `2026-05-12 07:35` PREOPEN apply wrapper가 종료됐거나 `08:50 KST`까지 runtime env/apply plan source 여부를 확인해야 할 때 실행한다.
  - 판단 입력: 전일 `threshold_cycle_ev_2026-05-11.{json,md}`, `data/threshold_cycle/apply_plans/threshold_apply_2026-05-12.json`, `data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-12.{env,json}`, `src/run_bot.sh`의 runtime env source 로그.
  - 필수 요건: apply mode `auto_bounded_live`, AI correction guard result, deterministic guard result, selected/blocked family, max step/bounds/sample window/safety/same-stage owner guard, generated env keys, `run_bot.sh` source log가 확인되어야 한다.
  - 판정 기준: `auto_bounded_live` guard를 통과한 family만 장전 runtime env로 반영됐는지 확인한다. blocked family는 `blocked_reason`, AI guard, same-stage owner conflict를 남기고 수동 env override를 하지 않는다.
  - 허용 결론: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나다. `partial_apply_with_blocked_families`는 selected env와 blocked reason이 모두 manifest에 있어야 한다.
  - 유지 가드: 장중 runtime threshold mutation은 계속 금지한다. 스윙 approval artifact가 없는 `approval_required` 요청은 env apply 대상이 아니다.
  - 완료 판정: `applied_guard_passed_env`.
  - 완료 근거: apply plan은 `status=auto_bounded_live_ready`, `apply_mode=auto_bounded_live`, `runtime_change=true`, selected family는 `soft_stop_whipsaw_confirmation`, `score65_74_recovery_probe`이며 env override는 `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=true`, `KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true`다. PID `4493` 환경에서도 `KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE=2026-05-12`와 두 env override가 로드됐다.
  - 완료 다음 액션: blocked family는 수동 env override하지 않고 장후 EV/blocked reason으로 재판정한다.


## 장전 체크리스트 (08:45~09:00)

- 해당 슬롯 자동 생성 항목 없음.

## 장중 체크리스트 (09:05~15:20)

### IntradayAutomationHealthCheck20260512 운영 확인 기록

- checked_at: `2026-05-12 09:08 KST`
- 판정: `pass`
- 근거: `bot_main.py` PID `15393`이 실행 중이고 `pipeline_events_2026-05-12.jsonl`은 09:08 KST 기준 5,121건으로 append 중이다. `buy_funnel_sentinel_2026-05-12`와 `holding_exit_sentinel_2026-05-12`는 모두 09:05 cron `[DONE]` marker와 `classification.primary=NORMAL`을 생성했다. `run_error_detection.log`도 09:05 full detector `[DONE]` marker를 남겼고 process/resource/stale-lock은 pass다. `threshold_events_2026-05-12.jsonl`은 7건으로 sparse stream이 생성됐으며, selected threshold family 직접 표본은 아직 없지만 runbook 기준 fatal stale이 아니라 source coverage 대기다.
- not_yet_due: `12:05` intraday threshold calibration과 장후/postclose 산출물은 아직 due 전이다.
- 다음 액션: Sentinel/Detector는 계속 report-only로 본다. selected runtime family, OpenAI `entry_price`, scalp sim BUY 확정 표본은 장후 EV/report에서 재확인하고 장중 runtime threshold mutation은 하지 않는다.
- 운영 메모 (`2026-05-12 12:13 KST`): `11:07:41` Kiwoom WS 재접속 후 REST 시세 API가 `8005 Token이 유효하지 않습니다`를 반복해 `scalp_vwap_reclaim_01` 전처리에서 `curr=0`, `vwap=0`, `missing_price_or_vwap`가 광범위하게 발생했다. runbook 기준 `8005` 반복은 graceful restart 우선으로 보고 `bot_main.py` PID `15393`에 TERM을 보내 `run_bot.sh` wrapper 재기동을 수행했다. 새 PID는 `40466`이며 `12:13:42` WS 로그인/조건검색식 등록, `12:13:45` 다수 종목 첫 실시간 수신, `ka10080` 분봉 직접 검증(`085660`, `397030`, `039200` 각 5개 반환)을 확인했다. 이 조치는 token/runtime data path 복구이며 threshold, 주문가/수량 guard, provider route, score/stop threshold는 변경하지 않았다.
- 구현 메모 (`2026-05-12 12:24 KST`): 동일 유형 재발 방지를 위해 System Error Detector에 `kiwoom_auth_8005_restart`를 추가했다. 대상은 `bot_history.log`, `kiwoom_utils_info.log`, `kiwoom_sniper_v2_error.log`, `sniper_state_handlers_error.log`, `kiwoom_orders*.log`의 fresh append 로그로 제한하며, 첫 실행은 기존 로그를 baseline 처리하고 이후 fresh `8005` 인증 실패만 `/home/ubuntu/KORStockScan/restart.flag` 생성 대상으로 본다. dry-run은 `would_restart=true`만 보고하고, live는 120초 cooldown을 둔 `restart.flag` 생성만 수행한다. 하루 3회 이상은 `fail`로 올려 operator 확인 대상이다. 전략 threshold, 주문가/수량 guard, provider route는 변경하지 않는다.
- 검증 메모 (`2026-05-12 12:26 KST`): `auth_only --dry-run`과 `full --dry-run`에서 `12:25:03` `kiwoom_utils_info.log`의 fresh `kt00008` 8005를 `would_restart=true`로 감지했다. live `auth_only` 실행으로 `restart.flag`를 생성했고, `bot_main.py`는 `12:26:07` flag를 소비해 graceful 종료 후 PID `40466 -> 42892`로 재기동했다. `12:26:27` WS 연결/로그인/조건검색식 수신을 확인했고, 직접 REST 검증은 `ka10080(085660)` 5개 row 반환으로 통과했다.

- [x] `[SwingMarketRegimeLocalBreadthGate0512] 스윙 market-regime 게이트 국내 breadth 반영 누락 점검` (`Due: 2026-05-12`, `Slot: INTRADAY`, `TimeWindow: 09:05~15:20`, `Track: SwingLogic`)
  - Source: [report_2026-05-12.json](/home/ubuntu/KORStockScan/data/report/report_2026-05-12.json), [market_regime_snapshot.json](/home/ubuntu/KORStockScan/data/cache/market_regime_snapshot.json), [service.py](/home/ubuntu/KORStockScan/src/market_regime/service.py), [sniper_market_regime.py](/home/ubuntu/KORStockScan/src/engine/sniper_market_regime.py)
  - 판정: `fix_applied_restarted`.
  - 근거: 일일 리포트 breadth는 `20일선 위 비율 62.8%`, `status_text=상승장`인데 기존 스윙 market-regime cache는 VIX/WTI/Fear&Greed만 점수화해 `oil=35`, `swing_score=35`, `risk_state=RISK_OFF`, `allow_swing_entry=false`로 닫혔다. 이는 표시 오류와 별개로 스윙 dry-run/probe 게이트에 영향을 주는 국내 breadth 반영 누락이다.
  - 조치: `MarketRegimeService`가 daily report/diagnostics의 국내 breadth context를 로드해 `local_breadth` component score로 합산하도록 수정했다. 현재 조건에서는 원유 반전 `35` + 국내 breadth `35`로 `swing_score=70`, `allow_swing_entry=true`가 된다. 단, VIX extreme이 아직 해소되지 않은 경우에는 local breadth override를 막는다.
  - 검증: `pytest` 10건 통과, `py_compile` 통과, `sync_docs_backlog_to_project --print-backlog-only --limit 500` parser 검증 통과. market regime cache는 `risk_state=RISK_ON`, `allow_swing_entry=true`, `swing_score=70`, `component_scores.local_breadth=35`로 재생성했다. 봇은 PID `4493 -> 15393`으로 재기동했고 `bot_history.log`에 `시장상태=상승장, 리스크=리스크온`, `시장환경 초기화 risk=RISK_ON, allow_swing=True`가 기록됐다.
  - 다음 액션: 장중 스윙 probe/dry-run 로그에서 `market_regime_pass`와 `actual_order_submitted=false` provenance를 분리 확인한다. 스윙 실주문 전환은 별도 approval artifact 없이는 열지 않는다.

- [x] `[RuntimeEnvIntradayObserve0512] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-05-12`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-11.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, score65_74_recovery_probe가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 완료 판정: `warning_sample_pending`.
  - 완료 근거: `threshold_runtime_env_2026-05-12.env`와 현재 봇 PID `15393` 환경에서 `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=true`, `KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true`, `KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE=2026-05-12` 로드를 확인했다. `data/pipeline_events/pipeline_events_2026-05-12.jsonl`은 09:08 KST 기준 5,121건으로 append 중이고, `data/threshold_cycle/threshold_events_2026-05-12.jsonl`은 7건의 sparse event를 생성했다. 다만 selected family `soft_stop_whipsaw_confirmation`, `score65_74_recovery_probe` 직접 provenance는 아직 0건이다. rollback/safety breach 문자열도 0건이다.
  - 완료 다음 액션: 표본 미발생은 runtime 실패가 아니라 `pending_applied_cohort`로 유지한다. 장후 `ThresholdDailyEVReport0512`에서 selected family 적용/미적용 cohort와 rollback guard를 다시 확인한다.


- [x] `[SimProbeIntradayCoverage0512] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-05-12`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-11.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 완료 판정: `pass_with_scalp_sim_no_sample_yet`.
  - 완료 근거: `pipeline_events_2026-05-12.jsonl`에서 simulation provenance가 `SwingIntradayLiveEquivalentProbe0511` 115건, `SwingLiveOrderDryRunSimulation0511` 3건으로 확인됐고, `actual_order_submitted=False`는 108건 확인됐다. `data/runtime/swing_intraday_probe_state.json`은 `simulation_book=swing_intraday_live_equiv_probe`, `owner=SwingIntradayLiveEquivalentProbe0511`, `updated_at=2026-05-12T09:05:48`, active 10개이며 모든 active probe가 `simulated_order=True`, `actual_order_submitted=False`, `broker_order_forbidden=True`다. origin은 `blocked_swing_score_vpw` 4개, `blocked_gatekeeper_reject` 4개, `blocked_swing_gap` 2개다. `scalp_live_simulator_state.json`은 active 0개로, 스캘핑 BUY 확정 sim 표본은 아직 없다.
  - 추가 점검(10:13 KST): `pipeline_events_2026-05-12.jsonl` 기준 스캘핑 sim event는 0건이고, 스윙 probe는 entry 14건, scale-in 가정체결 13건, sell 가정체결 11건이다. sell 가정체결 11건은 모두 `actual_order_submitted=False`, `broker_order_forbidden=True`이며 승률 36.4%, 평균 수익률 -0.283%, 수수료/세금 전 가상 gross PnL +1,405원이다. `swing_intraday_probe_state.json`은 `updated_at=2026-05-12T10:13:41`, active 10개이며 source date는 2026-05-11 3개, 2026-05-12 7개다.
  - 완료 다음 액션: sim/probe는 계속 real/sim split으로만 본다. 스윙 probe cap 도달/discard는 source-quality 정보로 장후 리포트에 넘기고, scalp sim 0건은 BUY 확정 hook 미발생으로 분리한다.

- [x] `[SentinelFollowupRouteReportOnly0512] Sentinel operator action/followup route 및 real/sim exit split 적용` (`Due: 2026-05-12`, `Slot: INTRADAY`, `TimeWindow: 11:10~11:35`, `Track: RuntimeStability`)
  - Source: [buy_funnel_sentinel.py](/home/ubuntu/KORStockScan/src/engine/buy_funnel_sentinel.py), [holding_exit_sentinel.py](/home/ubuntu/KORStockScan/src/engine/holding_exit_sentinel.py), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정: `report_only_enhancement_applied`.
  - 근거: BUY/HOLD-EXIT Sentinel JSON schema를 `2`로 올리고 `followup.route`, `followup.owner`, `operator_action_required`, `runtime_effect=report_only_no_mutation`, `next_artifact`를 추가했다. HOLD/EXIT는 `actual_order_submitted=false`, `broker_order_forbidden=true`, `simulation_book`, `simulation_owner`, probe 필드가 있는 event를 non-real observation으로 분리해 `real_exit_signal`, `real_sell_order_sent`, `non_real_exit_signal`, `non_real_sell_order_sent`를 별도 집계한다. `SELL_EXECUTION_DROUGHT` primary는 real exit path에만 적용하고, non-real drought는 provenance split reason으로만 남긴다.
  - 금지: 이 변경은 report/attribution 품질 개선이며 runtime threshold, 주문가/수량, 청산 판단, bot restart를 변경하지 않는다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_holding_exit_sentinel.py` 13건 통과, `py_compile` 통과. 2026-05-12 산출물 재생성 결과 BUY는 `UPSTREAM_AI_THRESHOLD -> score65_74_counterfactual_review`, `operator_action_required=false`; HOLD/EXIT는 `SELL_EXECUTION_DROUGHT -> sell_receipt_order_path_check`, `operator_action_required=true`, `real_exit_signal=16`, `real_sell_order_sent=0`, `non_real_exit_signal=0`으로 분리됐다.
  - 다음 액션: 장후 `trade_lifecycle_attribution`에서 HOLD/EXIT real sell receipt/order path를 확인한다. BUY `UPSTREAM_AI_THRESHOLD`는 `wait6579_ev_cohort`와 `missed_probe_counterfactual`로 넘기고 score threshold 완화나 fallback 재개는 하지 않는다.

- [x] `[PanicSellDefenseReportOnly0512] 패닉셀 방어 report-only 리포트 축 구현 및 당일 산출물 생성` (`Due: 2026-05-12`, `Slot: INTRADAY`, `TimeWindow: 11:35~12:00`, `Track: RuntimeStability`)
  - Source: [panic_sell_defense_report.py](/home/ubuntu/KORStockScan/src/engine/panic_sell_defense_report.py), [run_panic_sell_defense_intraday.sh](/home/ubuntu/KORStockScan/deploy/run_panic_sell_defense_intraday.sh), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [panic_sell_defense_2026-05-12.json](/home/ubuntu/KORStockScan/data/report/panic_sell_defense/panic_sell_defense_2026-05-12.json), [panic_sell_defense_2026-05-12.md](/home/ubuntu/KORStockScan/data/report/panic_sell_defense/panic_sell_defense_2026-05-12.md), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정: `report_only_axis_applied_and_automation_chain_wired`.
  - 근거: 신규 `panic_sell_defense` 산출물은 `pipeline_events`, BUY/HOLD Sentinel, market regime snapshot, swing/scalp sim state, post-sell feedback를 읽어 `NORMAL/PANIC_SELL/RECOVERY_WATCH/RECOVERY_CONFIRMED`를 분류한다. 2026-05-12 12:01 KST 산출물은 `panic_state=RECOVERY_WATCH`, `max_rolling_30m_stop_loss_exit_count=17`, `stop_loss_exit_ratio_pct=78.6`, active sim/probe `avg_unrealized_profit_rate_pct=0.7995`, `win_rate_pct=62.5`, provenance pass로 닫혔다. 이후 5분 반복 wrapper/cron installer, error detector cron/freshness registry, `threshold_cycle` calibration source bundle, workorder artifact check까지 연결했다.
  - 금지: runtime threshold mutation, score threshold 완화, stop-loss 완화, 자동매도, bot restart, 스윙 실주문 enable은 모두 금지 automation으로 남겼다. hard/protect/emergency stop은 confirmation 후보에서 제외하고, soft/trailing/flow 후보만 다음 장전 bounded canary 검토 후보로 라우팅한다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_panic_sell_defense_report.py src/tests/test_daily_threshold_cycle_report.py src/tests/test_error_detector_coverage.py` 통과. `bash -n deploy/run_panic_sell_defense_intraday.sh deploy/install_panic_sell_defense_cron.sh` 통과. 당일 JSON/Markdown 산출물 생성 완료.
  - 다음 액션: 장후 `trade_lifecycle_attribution`과 `threshold_cycle_ev`에서 `panic_attribution_pack`, `panic_entry_freeze_guard`, `panic_stop_confirmation`, `panic_rebound_probe` 후보를 closed PnL/forward return/active probe로 분리 재판정한다. 장중에는 report-only 유지한다.

## 장후 체크리스트 (16:30~18:55)

### PostcloseAutomationHealthCheck20260512 운영 확인 기록

- checked_at: `2026-05-12 18:28 KST`
- 판정: `pass_after_backfill`
- 근거: `logs/threshold_cycle_postclose_cron.log`에 `2026-05-12T17:03:48+0900 [DONE] threshold-cycle postclose target_date=2026-05-12 ... daily_ev=true runtime_approval_summary=true next_stage2_checklist=true` marker가 남았고, `threshold_cycle_ev_2026-05-12.md`, `runtime_approval_summary_2026-05-12.md`, `scalping_pattern_lab_automation_2026-05-12.md`, `code_improvement_workorder_2026-05-12.md`, `docs/checklists/2026-05-13-stage2-todo-checklist.md` 생성까지 확인했다.
- 최초 warning 사유 (`18:28 KST`): runbook 표준 확인 항목 중 `data/report/swing_daily_simulation/swing_daily_simulation_2026-05-12.json`이 없었고, `swing_lifecycle_audit`는 `simulation_opportunity.available=false`, `reason=swing_daily_simulation_report_missing`로 닫혀 있었다.
- 보정 (`18:14~18:17 KST`): 원인은 `run_threshold_cycle_postclose.sh`가 `swing_lifecycle_audit` 전에 `run_swing_daily_simulation_report.sh`를 호출하지 않던 체인 누락이었다. wrapper에 호출 순서를 추가하고 `bash deploy/run_swing_daily_simulation_report.sh 2026-05-12`, `PYTHONPATH=. .venv/bin/python -m src.engine.swing_lifecycle_audit --date 2026-05-12 --ai-review-provider openai`, `PYTHONPATH=. .venv/bin/python -m src.engine.runtime_approval_summary --date 2026-05-12`를 재실행했다.
- 후속 구현 (`2026-05-12 19:29 KST`): postclose wrapper에 direct predecessor artifact 대기 로직을 추가했다. 이제 `swing_daily_simulation -> swing_lifecycle_audit`, `threshold_cycle_ev(pre-pass) -> code_improvement_workorder -> threshold_cycle_ev(refresh) -> runtime_approval_summary -> next_stage2_checklist` 순서에서 직전 JSON/Markdown artifact가 없거나 JSON 검증이 안 끝나면 후행 단계는 대기하고, `THRESHOLD_CYCLE_ARTIFACT_WAIT_SEC` 초과 시 fail-closed 한다.
- 재검증 (`2026-05-12 19:52 KST`): `bash deploy/run_threshold_cycle_postclose.sh 2026-05-12`를 수정된 wrapper로 재실행했다. 기존 immutable snapshot/checkpoint를 재사용했고, direct predecessor artifact wait가 모두 `waited=0s`로 통과했다. wrapper는 `threshold_cycle_ev(pre_workorder) -> code_improvement_workorder -> threshold_cycle_ev(post_workorder_refresh) -> runtime_approval_summary -> next_stage2_checklist` 순서로 완료됐고 `[DONE] threshold-cycle postclose target_date=2026-05-12 ... finished_at=2026-05-12T19:52:15+0900`를 출력했다.
- DeepSeek schema 보정 (`2026-05-12 19:58 KST`): `deepseek_payload_summary.json`에 `total_cases`/`case_counts`를 추가해 `swing_pattern_lab_automation`의 required output schema mismatch를 해소했다. 재생성 후 `deepseek_lab_available=True`, `stale_reason=None`, `findings_count=4`, `code_improvement_order_count=2`로 전환됐고, `threshold_cycle_ev_2026-05-12.json` warning에서 `invalid_required_output:deepseek_payload_summary(missing_schema_keys)`가 제거됐다.
- data-quality threshold 보정 (`2026-05-12 20:04 KST`): DeepSeek one-day postclose run에서는 `swing_lifecycle_funnel_fact`가 날짜당 1 row가 정상인데도 고정 `MIN_VALID_SAMPLES=3` 기준으로 항상 warning이 뜨고 있었다. `prepare_dataset.py`를 수정해 funnel row 최소 기준을 `min(MIN_VALID_SAMPLES, analysis_days)`로 계산하도록 바꿨다. 재생성 후 `funnel fact has only 1 rows (min 3)`는 제거됐고, 남은 warning은 실제 source-quality 이슈인 `OFI/QI stale/missing ratio: 0.0776 (9/116)` 1건뿐이다.
- OFI/QI source-quality 분해 (`2026-05-12 20:20 KST`): `stale_missing_flag`를 단일 boolean으로만 보지 않고 `micro_missing`, `micro_stale`, `observer_unhealthy`, `micro_not_ready`, `state_insufficient` reason으로 분해해 DeepSeek fact/payload/data-quality, swing lifecycle audit, threshold EV, workorder evidence에 표면화했다. 2026-05-12 기준 `stale_missing_count=9/116`, reason은 `micro_missing=9`, `micro_not_ready=9`, `state_insufficient=9`, `observer_unhealthy=3`, `micro_stale=0`이다. 이는 runtime mutation이 아니라 `swing_entry_ofi_qi_execution_quality` source-quality/instrumentation 보강이다.
- OFI/QI source-quality 조합/unique record 분해 (`2026-05-12 20:37 KST`): 9건은 독립 9종목이 아니라 `scale_in` group의 3개 record가 `swing_scale_in_micro_context_observed`, `swing_sim_scale_in_order_assumed_filled`, `swing_probe_scale_in_order_assumed_filled` 3개 stage에 반복 표면화된 구조다. 조합은 `micro_missing+micro_not_ready+state_insufficient=6 events / 2 records`, `micro_missing+observer_unhealthy+micro_not_ready+state_insufficient=3 events / 1 record`다. `observer_unhealthy=3`은 독립 장애가 아니라 missing/not_ready/insufficient와 겹친 1개 record의 3개 stage 반복으로 확인했다. 다음 판정은 entry gate 튜닝이 아니라 swing scale-in micro-context 생성/ready 경로의 source-quality 보강으로 본다.
- OFI/QI source-quality 자동화 입력 승격 (`2026-05-12 20:55 KST`): report-only artifact는 유지하되 값은 자동화 체인의 입력으로 승격했다. `swing_scale_in_ofi_qi_confirmation`과 `swing_scale_in_real_canary_phase0`는 `scale_in_ofi_qi_invalid_micro_context`를 `source_quality_blocked_families`로 받으며, scale-in real canary arm decision은 raw sample이 아니라 `valid_micro_context_count=75/84`와 invalid unique `3 records`를 함께 본다. `threshold_cycle_ev_2026-05-12.json`의 swing pattern lab section에도 `source_quality_blocked_families=[swing_scale_in_ofi_qi_confirmation]`가 반영됐다. 이는 approval/workorder/EV 입력값이며 runtime threshold/order mutation은 아니다.
- postclose verification 자동화 (`2026-05-12 21:19 KST`): `threshold_cycle_postclose_verification_2026-05-12.{json,md}`를 추가했다. 이 artifact는 latest `START` 이후 `logs/threshold_cycle_postclose_cron.log`의 predecessor wait/timeout/fail을 요약하고, same-day workorder 재생성은 `mtime`이 아니라 `generation_id=2026-05-12-5abbfc31939d`, `source_hash=5abbfc31939d...`, `lineage.new/removed/decision_changed=[]`를 우선 판정한다. 2026-05-12 결과는 `status=pass`, `predecessor_wait_count=0`, `timeout_count=0`이다.
- 완료 근거: `swing_daily_simulation_2026-05-12.{json,md}`가 생성됐고, 재생성된 `swing_lifecycle_audit_2026-05-12.md`는 `simulation_opportunity.available=True`, `sample_state=hold_sample`, `rows=90`로 갱신됐다. `swing_improvement_automation_2026-05-12.json`과 `swing_runtime_approval_2026-05-12.json`도 `18:17 KST` 기준으로 다시 써졌다.
- 다음 액션: 이후 postclose에서는 `[DONE]` marker 이후 `swing_daily_simulation`, pre-pass `threshold_cycle_ev`, refreshed `threshold_cycle_ev`, `code_improvement_workorder` 중 하나라도 빠지면 wrapper regression으로 바로 본다. OFI/QI source-quality는 scale-in approval blocker/EV 입력으로 계속 보되, runtime mutation 후보는 별도 approval artifact 없이는 만들지 않는다.

- [x] `[ThresholdDailyEVReport0512] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-05-12`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-11.json)
  - 판정 기준: real/sim/combined split, selected/blocked family, runtime_change, warning을 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 중간 경과 (`2026-05-12 16:38~16:45 KST`): 기존 16:10 cron run은 `paused_by_availability_guard (iowait_pct>=20)`로 중단됐고 `[DONE]`/`[FAIL]` marker가 없었다. wrapper에 `[PAUSED]`/`[FAIL]` marker를 추가하고, retry가 새 immutable snapshot을 매번 다시 떠 `--overwrite`로 원점 재시작하던 문제를 수정해 기존 snapshot/checkpoint 재사용으로 바꿨다.
  - 완료 판정: `pass_after_retry_and_wrapper_fix`.
  - 완료 근거: `logs/threshold_cycle_postclose_cron.log`에 `2026-05-12T17:03:48+0900 [DONE] threshold-cycle postclose target_date=2026-05-12 ai_correction_provider=openai ... daily_ev=true runtime_approval_summary=true next_stage2_checklist=true` marker가 남았다. `data/report/threshold_cycle_calibration/threshold_cycle_calibration_2026-05-12_postclose.json`, `data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_2026-05-12_postclose.json`, `data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-12.json`, `data/report/runtime_approval_summary/runtime_approval_summary_2026-05-12.md`, `docs/checklists/2026-05-13-stage2-todo-checklist.md` 생성까지 확인했다.
  - 추가 구현 메모 (`2026-05-12 19:29 KST`): `run_threshold_cycle_postclose.sh`는 이제 direct predecessor artifact 대기 helper(`wait_for_json_artifact`, `wait_for_report_artifact`)를 사용한다. `threshold_cycle_ev`는 workorder source용 pre-pass와 workorder summary refresh용 post-pass로 2회 생성하고, `runtime_approval_summary`와 다음 checklist는 refreshed EV/workorder artifact가 닫힌 뒤에만 실행한다.
  - source-quality 입력 반영 (`2026-05-12 20:55 KST`): refreshed `threshold_cycle_ev_2026-05-12.json`은 `swing_pattern_lab_automation.source_quality_blocked_families`에 `swing_scale_in_ofi_qi_confirmation`, blocker `scale_in_ofi_qi_invalid_micro_context`, invalid unique `3 records`를 포함한다. 이 값은 다음 approval/workorder 판정 입력이며 runtime mutation은 아니다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_threshold_cycle_wrappers.py` `10 passed`; `bash -n deploy/run_threshold_cycle_postclose.sh`; parser 검증 `PYTHONPATH=. .venv/bin/python -m src.engine.build_codex_daily_workorder --target-date 2026-05-12 --slot POSTCLOSE --output tmp/codex_daily_workorder_postclose_2026-05-12.md --max-items 20`.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [x] `[CodeImprovementWorkorderReview0512] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-05-12`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-05-12.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-12.md), [code_improvement_workorder_2026-05-12.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-12.json)
  - 판정 기준: `generation_id`, `source_hash`, `lineage` diff와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다.
  - 2-pass 기준: 구현 요청 시 Pass1은 instrumentation/report/provenance만 수행하고, report/workorder 재생성 후 `lineage.new_order_ids` 중 `runtime_effect=false`만 Pass2 추가 구현 대상으로 본다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 판정: `pass_2pass_existing_plus_new_followup`.
  - 근거: 최초 workorder는 `generation_id=2026-05-12-59737d0c39de`, `source_hash=59737d0c39de...`, `implement_now=order_latency_guard_miss_ev_recovery` 1건이었다. Pass1 검토 결과 이 축은 [sniper_performance_tuning_report.py](/home/ubuntu/KORStockScan/src/engine/sniper_performance_tuning_report.py) `latency_guard_miss_ev_recovery` source metric과 [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py) `pre_submit_price_guard` calibration source 연결이 이미 존재해 `existing implementation`으로 판정했다. 이후 workorder 재생성으로 `generation_id=2026-05-12-46af01a69113`, `source_hash=46af01a69113...`로 갱신됐고 `lineage.new_order_ids=['order_holding_exit_decision_matrix_edge_counterfactual']`, `removed_order_ids=['order_split_entry_scalp_soft_stop_pct_손실패턴_분해']`가 확인됐다.
  - 조치: 신규 `runtime_effect=false implement_now` 1건만 Pass2 대상으로 받아 [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py)에 holding-exit matrix `summary.non_no_clear_edge_count`, `summary.per_action_edge_buckets`, counterfactual coverage markdown 표면을 추가했다.
  - 재생성 확인 (`2026-05-12 19:52 KST`): 수정된 postclose wrapper 재실행 후 workorder는 `generation_id=2026-05-12-9a49bf6ddeea`, `source_hash=9a49bf6ddeea290f7f0de0eaf21a3fd78cbb513556e595b8f487ff5aec00c1a4`로 갱신됐다. lineage는 `new_order_ids=[]`, `removed_order_ids=[]`, `decision_changed_order_ids=[]`라 작업지시 재실행 대상은 없다.
  - DeepSeek schema 보정 후 재생성 (`2026-05-12 19:58 KST`): workorder는 `generation_id=2026-05-12-79a9df431abf`, `source_hash=79a9df431abf8c61cba2e667fb1d731b179c3fdc14d1f19e928b40045600023a`로 갱신됐다. `new_order_ids=['order_swing_pattern_lab_deepseek_entry_no_submissions', 'order_swing_pattern_lab_deepseek_scale_in_events_observed']`, `removed_order_ids=['order_ai_threshold_miss_ev_회수_조건_점검', 'order_overbought_gate_miss_ev_회수_조건_점검']`, `decision_changed_order_ids=[]`다. 신규 2건은 각각 `design_family_candidate`, `attach_existing_family`이고 `runtime_effect=false`이므로 이번 세션의 추가 `implement_now` 재실행 대상은 아니다.
  - OFI/QI source-quality 분해 후 재생성 (`2026-05-12 20:20 KST`): workorder는 `generation_id=2026-05-12-4a17386a17f9`, `source_hash=4a17386a17f954d7b06a57b520cfa9117a6ba6554f4cc3b0e3d52f4093ef382d`로 갱신됐다. `summary.new_selected_order_count=0`, `removed_selected_order_count=0`, `decision_changed_order_count=0`이며 `implement_now`는 기존 2건 그대로다. `order_swing_ofi_qi_stale_or_missing_context` evidence에는 `stale_missing_reason_counts={'micro_missing': 9, 'micro_not_ready': 9, 'state_insufficient': 9, 'observer_unhealthy': 3}`가 추가됐고 decision은 `attach_existing_family` 유지다.
  - OFI/QI 조합/unique record 분해 후 재생성 (`2026-05-12 20:37 KST`): workorder는 `generation_id=2026-05-12-a02cfa1ec079`, `source_hash=a02cfa1ec079a773f358b26c4424aa2f3d320fb73f909b51fbda200d09e50ca4`로 갱신됐다. `summary.new_selected_order_count=0`, `removed_selected_order_count=0`, `decision_changed_order_count=0`이며 `implement_now`는 기존 2건 그대로다. `order_swing_ofi_qi_stale_or_missing_context` evidence에는 `stale_missing_unique_record_count=3`, `stale_missing_reason_combination_unique_record_counts={'micro_missing+micro_not_ready+state_insufficient': 2, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`, `observer_unhealthy_overlap={'observer_unhealthy_total': 3, 'observer_unhealthy_with_other_reason': 3, 'observer_unhealthy_only': 0}`가 추가됐다.
  - OFI/QI source-quality 자동화 입력 승격 후 재생성 (`2026-05-12 20:55 KST`): workorder는 `generation_id=2026-05-12-5abbfc31939d`, `source_hash=5abbfc31939dffedcaab60313d1641234dbc026363b0f2842778d63b45f9440a`로 갱신됐다. `summary.new_selected_order_count=0`, `removed_selected_order_count=0`, `decision_changed_order_count=0`이며 `implement_now`는 기존 2건 그대로다. 신규 source-quality blocker는 `attach_existing_family`/approval blocker 입력으로 반영됐고, 추가 `implement_now` 재실행 대상은 없다.
  - 검증: `PYTHONPATH=. .venv/bin/python -m src.engine.build_code_improvement_workorder --date 2026-05-12 --max-orders 12`, `PYTHONPATH=. .venv/bin/python -m src.engine.daily_threshold_cycle_report --date 2026-05-12 --calibration-run-phase postclose`, `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_daily_threshold_cycle_report.py src/tests/test_build_code_improvement_workorder.py src/tests/test_threshold_cycle_ev_report.py` `38 passed`.
  - 완료 다음 액션: final freeze는 regenerated workorder `generation_id=2026-05-12-5abbfc31939d`, `source_hash=5abbfc31939dffedcaab60313d1641234dbc026363b0f2842778d63b45f9440a` 기준으로 보고한다. remaining `implement_now` 2건은 기존 구현/당일 신규 구현 확인 항목으로 취급하고, source-quality blocker는 추가 workorder 재실행이 아니라 다음 approval/EV 입력으로 넘긴다.

- [x] `[CodeImprovementNonImplementTriage0512] attach/design/defer 항목 재판정 및 다음 소유자 고정` (`Due: 2026-05-12`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-05-12.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-12.md), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: `attach_existing_family`는 기존 family 입력 흡수 여부, `design_family_candidate`는 설계 backlog 필요 여부, `defer_evidence`는 승격/계속보류/폐기 여부로 분리한다.
  - 금지: 비-implement 항목을 자동 구현 또는 자동 runtime apply로 취급하지 않는다.
  - 판정: `triaged_without_runtime_mutation`.
  - 근거: regenerated workorder 기준 `attach_existing_family=4`(`order_ai_threshold_dominance`, `order_ai_threshold_miss_ev_recovery`, `order_swing_gatekeeper_reject_threshold_review`, `order_swing_ofi_qi_stale_or_missing_context`)는 기존 family 입력/계측 보강 bucket으로 유지해 `attached_to_existing_family` owner로 묶었다. `design_family_candidate=3`(`order_liquidity_gate_miss_ev_recovery`, `order_overbought_gate_miss_ev_recovery`, `order_swing_ai_contract_structured_output_eval`)는 `allowed_runtime_apply=false` 설계 backlog로만 유지했다. `defer_evidence=5`는 fresh lab/EV 반복 확인 전 `continue_defer`로 남기고, `reject=4`는 fallback/shadow/safety policy 충돌로 `drop_stale` 유지다.
  - 완료 다음 액션: non-implement 항목은 runtime apply 없이 다음 postclose automation/EV에서 다시 읽는다. 사람이 다시 Codex에 지시해야 하는 대상은 `design_backlog_required` 3건뿐이며, attach/defer/reject는 이번 세션에서 추가 구현하지 않는다.

- [x] `[HumanInterventionSummary0512] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-05-12`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:30`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-12.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-12.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `승인 artifact 필요`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 판정: `classified_no_missing_followup`.
  - 근거: `승인 artifact 필요`는 없음(이번 workorder 범위는 모두 `runtime_effect=false`). `Codex 구현 필요`는 2-pass로 처리된 `order_holding_exit_decision_matrix_edge_counterfactual` 1건과 existing implementation 확인 `order_latency_guard_miss_ev_recovery` 1건으로 닫았다. `수동 동기화 필요`는 checklist 갱신 후 Project/Calendar sync 1건뿐이다. 나머지 attach/design/defer/reject는 `관찰만` 또는 다음 별도 설계 지시 대상으로 분리돼 누락이 없다.
  - 완료 다음 액션: 사용자는 아래 표준 동기화 명령만 수동 실행한다.

- [x] `[ScalpingBlockerResolutionPlan0512] 스캘핑 blocker 해소계획 문서화 및 후속 owner 고정` (`Due: 2026-05-12`, `Slot: POSTCLOSE`, `TimeWindow: 17:30~17:45`, `Track: ScalpingLogic`)
  - Source: [scalping-runtime-blocker-resolution-plan-2026-05-12.md](/home/ubuntu/KORStockScan/docs/scalping-runtime-blocker-resolution-plan-2026-05-12.md), [runtime_approval_summary_2026-05-11.md](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-05-11.md), [threshold_apply_2026-05-12.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-12.json)
  - 판정 기준: `hold_sample`, `hold_no_edge`, `freeze`, `report_only_design`, `existing_guard_hold`를 한 문서에서 family별 blocker와 unblock 조건으로 분리한다.
  - 금지: 표본 부족을 모든 미적용 사유로 뭉뚱그리거나, sim/combined EV를 broker execution 품질 근거로 단독 사용하지 않는다.
  - 판정: `blocker_plan_frozen_with_family_owners`.
  - 근거: blocker resolution plan에 `2026-05-12 Postclose 판정 고정` 섹션을 추가해 family별 결론을 잠갔다. `protect_trailing_smoothing=continue_hold_sample(18/20)`, `trailing_continuation=freeze_live_risk(18/20 + GOOD_EXIT risk)`, `pre_submit_price_guard=continue_hold_sample(existing_guard_hold, 0/20)`, `liquidity_gate_refined_candidate=report_only_design(8360/20)`, `overbought_gate_refined_candidate=report_only_design(80361/20)`, `bad_entry_refined_canary=continue_hold_sample(candidate_records=1, joined=0)`, `holding_exit_decision_matrix_advisory=continue_hold_sample(non_no_clear_edge_count=0/14)`, `scale_in_price_guard=continue_hold_sample(existing_guard_hold, 56/20)`, `position_sizing_cap_release=continue_hold_sample(28/30, failed_safety_floor 명시)`, `holding_flow_ofi_smoothing=continue_hold_sample(0/20)`로 정리했다.
  - 완료 다음 액션: 다음 장전 runtime apply 후보는 `ready_for_preopen_apply`로 승격된 family가 생길 때만 늘리고, 나머지는 지금 문서의 unblock 입력 필드를 유지한 채 다음 postclose에서 재판정한다.

- [x] `[BadEntryLifecycleJoinReadiness0512] bad_entry refined canary lifecycle join readiness guard 수치화` (`Due: 2026-05-12`, `Slot: POSTCLOSE`, `TimeWindow: 17:45~18:00`, `Track: ScalpingLogic`)
  - Source: [scalping-runtime-blocker-resolution-plan-2026-05-12.md](/home/ubuntu/KORStockScan/docs/scalping-runtime-blocker-resolution-plan-2026-05-12.md), [README.md](/home/ubuntu/KORStockScan/data/threshold_cycle/README.md), [threshold_apply_2026-05-12.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-12.json)
  - 판정 기준: `record_id -> post_sell_evaluations` join floor, preventable EV benefit, false-positive GOOD_EXIT 손상 guard, rollback owner를 readiness 조건으로 제안한다.
  - 금지: `bad_entry_refined_candidate` runtime provisional signal을 post-sell outcome 없이 최종 bad-entry 라벨로 확정하지 않는다.
  - 판정: `continue_hold_sample_with_quantified_join_guard`.
  - 근거: `threshold_cycle_2026-05-12.json` source metrics 기준 lifecycle attribution은 `candidate_records=1`, `post_sell_joined_records=0`, `post_sell_pending_records=1`, `preventable_bad_entry_candidate_records=0`, `false_positive_risk_after_candidate_records=0`다. blocker plan에는 readiness floor를 `joined_candidate_records>=10`, `join_completion_rate>=0.90`, `preventable_bad_entry_candidate_records>=3`, `preventable_bad_entry_candidate_records > false_positive_risk_after_candidate_records`, `late_detected_soft_stop_zone_records 제외`로 고정했다. 오늘 표본은 이 floor를 전혀 충족하지 못해 `ready_for_bounded_canary_request`로 올릴 수 없다.
  - 완료 다음 액션: `post_sell_pending_records==0`가 되는 joined cohort가 누적되기 전까지 `bad_entry_refined_canary`는 observe-only hold로 두고, preventable vs false-positive dominance가 보일 때만 bounded request 후보로 다시 연다.

- [x] `[ScalpingBlockedFamilyReadinessGuards0512] 스캘핑 blocked family별 readiness guard 자동화 입력 정리` (`Due: 2026-05-12`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:20`, `Track: ScalpingLogic`)
  - Source: [scalping-runtime-blocker-resolution-plan-2026-05-12.md](/home/ubuntu/KORStockScan/docs/scalping-runtime-blocker-resolution-plan-2026-05-12.md), [threshold_apply_2026-05-12.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-12.json)
  - 판정 기준: `protect_trailing_smoothing`, `trailing_continuation`, `pre_submit_price_guard`, `holding_exit_decision_matrix_advisory`, `position_sizing_cap_release`가 각각 sample floor, GOOD_EXIT 훼손, quote freshness, minimum edge, safety floor 중 어느 blocker에 걸렸는지 자동 산출 입력을 정의한다.
  - 금지: entry gate 완화, score threshold 완화, spread cap 완화, fallback 재개를 blocker 해소 수단으로 섞지 않는다.
  - 판정: `guard_inputs_defined_without_runtime_relaxation`.
  - 근거: blocker plan에 `Blocked Family Readiness Guard Inputs` 표를 추가했다. `protect_trailing_smoothing`은 `good_exit_damage_rate`/`additional_worsen_after_defer_p95`, `trailing_continuation`은 `continuation_mfe_delta_pct`/`downside_tail_p95`, `pre_submit_price_guard`는 `stale_context_or_quote_count`/`ws_age_p95_ms`/`late_fill_count`, `holding_exit_decision_matrix_advisory`는 `summary.non_no_clear_edge_count`/`summary.per_action_edge_buckets`, `position_sizing_cap_release`는 `tradeoff_score`/`failed_safety_floor`/`submitted_sample`을 필수 입력으로 고정했다. 각 row에 live apply 금지 조건도 같이 적어 score threshold 완화나 fallback 재개가 우회로로 섞이지 않게 잠갔다.
  - 완료 다음 액션: 다음 postclose report는 이 필드를 source bundle에서 계속 내야 하며, 필드가 비면 `hold_sample` 또는 `freeze`를 유지한다.

- [x] `[ScalpSimDecisionAccelerationPolicy0512] sim 표본 기반 의사결정 가속 기준과 real-only guard 분리` (`Due: 2026-05-12`, `Slot: POSTCLOSE`, `TimeWindow: 18:20~18:40`, `Track: ScalpingLogic`)
  - Source: [scalping-runtime-blocker-resolution-plan-2026-05-12.md](/home/ubuntu/KORStockScan/docs/scalping-runtime-blocker-resolution-plan-2026-05-12.md), [threshold_cycle_ev_2026-05-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-11.json)
  - 판정 기준: sim/real/combined split에서 sim 표본이 EV/source-quality 판단을 빠르게 하는 항목과 broker execution 때문에 real-only 증거가 필요한 항목을 분리한다.
  - 금지: `actual_order_submitted=false` 표본을 실주문 전환 또는 체결품질 승인 근거로 단독 사용하지 않는다.
  - 장중 선반영: `score65_74_recovery_probe`는 `scalp_ai_buy_all` 확정 BUY sim과 섞지 않고 `scalp_score65_74_probe_counterfactual` missed/probe counterfactual로 분리한다. `wait6579_ev_cohort`는 이 축을 `actual_order_submitted=false`, `broker_order_forbidden=true`, `runtime_effect=counterfactual_report_only`, `calibration_authority=missed_probe_ev_only_not_broker_execution`로 집계하고, `threshold_cycle_ev_report`는 `missed_probe_counterfactual` 섹션으로 별도 노출한다. 장중 재집계는 허용하되 runtime threshold/order mutation이나 봇 restart 없이 report regeneration만 수행한다.
  - 판정: `sim_policy_split_frozen`.
  - 근거: `threshold_cycle_ev_2026-05-12.json`의 `missed_probe_counterfactual`는 `actual_order_submitted=false`, `broker_order_forbidden=true`, `runtime_effect=counterfactual_report_only`, `calibration_authority=missed_probe_ev_only_not_broker_execution`, `total_candidates=14`, `score65_74_probe_candidates=4`, `avg_expected_ev_pct=2.2277`로 분리돼 있다. blocker plan에는 family별 `sim_accelerates_decision`, `real_only_guard`, `approval_required` 매트릭스를 추가해 `score65_74_recovery_probe`/`liquidity_gate_refined_candidate`/`overbought_gate_refined_candidate`는 sim이 EV 판단을 가속하지만, `pre_submit_price_guard`/`scale_in_price_guard`는 execution-quality 때문에 real-only guard가 남는다고 고정했다. `position_sizing_cap_release`는 sim 가속 입력을 허용하되 approval-required로 분리했다.
  - 완료 다음 액션: sim 표본은 combined EV와 opportunity-cost 가속 입력으로만 쓰고, broker execution 품질과 실주문 전환은 real-only/approval gate를 유지한다.

- [x] `[ShadowCanaryCohortReview0512] shadow/canary/cohort 런타임 분류 및 정리 판정` (`Due: 2026-05-12`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: Plan`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: 당일 변경/관찰 결과를 기준으로 `remove`, `observe-only`, `baseline-promote`, `active-canary` 상태 변동 여부를 닫는다.
  - 금지: shadow 금지, canary-only, baseline 승격 원칙을 코드/문서 상태와 분리하지 않는다.
  - 판정: `classification_doc_rebased_to_current_runtime`.
  - 근거: shadow/canary 기준문서를 `2026-05-12` 기준으로 갱신했다. top snapshot에서 `bad_entry_refined_canary`는 더 이상 active live owner가 아니라 `observe-only / report-only hold`로 내렸고, runtime ON/OFF 표에는 `score65_74_recovery_probe`를 entry active canary로 추가했다. cohort 분류표와 요약표의 `bad_entry_refined_canary`도 `observe-only`, `guarded-off`로 수정해 `candidate_records=1`, `post_sell_joined_records=0`, `preventable_bad_entry_candidate_records=0` 상태를 문서 기준으로 잠갔다.
  - 완료 다음 액션: 이후 family 상태가 바뀌면 checklist와 이 기준문서를 같은 change set에서 같이 갱신한다.

- [x] `[SwingBlockedOriginQualityGuardPrinciple0512] 스윙 blocked origin 3축 단일 quality guard 묶음 판정` (`Due: 2026-05-12`, `Slot: POSTCLOSE`, `TimeWindow: 18:55~19:10`, `Track: SwingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [panic_sell_defense_2026-05-12.json](/home/ubuntu/KORStockScan/data/report/panic_sell_defense/panic_sell_defense_2026-05-12.json), [swing_intraday_probe_state.json](/home/ubuntu/KORStockScan/data/runtime/swing_intraday_probe_state.json)
  - 판정 기준: `blocked_swing_gap`, `blocked_swing_score_vpw`, `blocked_gatekeeper_reject`를 각각 별도 threshold/family로 미세조정하지 않고 `swing_blocked_origin_quality_guard` 단일 후보로 묶는다. 세부 origin은 손익/반복손실/missed rebound/source-quality attribution tag로만 유지한다.
  - 허용 결론: `single_guard_candidate`, `report_only_hold`, `hold_sample`, `drop_stale` 중 하나다.
  - 금지: origin별 gap %, score floor, gatekeeper reject reason을 당일 표본만으로 각각 runtime threshold 후보화하지 않는다. 스윙 실주문 전환, score threshold 완화, market regime/gap/gatekeeper 개별 live mutation은 별도 approval 없이 금지한다.
  - 판정: `single_guard_candidate`.
  - 근거: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)는 이미 세 origin을 `swing_blocked_origin_quality_guard` 단일 family 후보로 묶도록 고정한다. 당일 산출물도 이 원칙을 지지한다. `swing_selection_funnel_2026-05-12.md`와 `swing_lifecycle_audit_2026-05-12.md`에서 raw count는 `blocked_swing_score_vpw=558903`, `blocked_swing_gap=56344`, `blocked_gatekeeper_reject=40`로 크게 벌어지지만 unique record는 각각 `28`, `3`, `11`이라 loop/raw volume 편향이 심하다. `panic_sell_defense_2026-05-12.json`의 active swing probe `9`개는 provenance check passed, `actual_order_submitted=false`, `broker_order_forbidden=true`, `avg_unrealized_profit_rate_pct=0.6706`, `win_rate_pct=66.7`로 묶여 있고 origin별로도 `blocked_swing_gap`은 flat/loss, `blocked_gatekeeper_reject`는 혼합, `blocked_swing_score_vpw`는 우세 양수처럼 결과가 섞여 있어 origin별 threshold로 따로 승격할 근거가 아니다. 백필 후 `swing_lifecycle_audit`의 `simulation_opportunity.available=True`이지만 `sample_state=hold_sample`, `closed_count=0`, 전부 `PENDING_ENTRY`라 다음 장전 전까지도 단일 guard 원칙 이상으로 올릴 표본은 없다.
  - 완료 다음 액션: blocked origin은 계속 `attribution/cohort tag`로만 유지하고, 후속 판정은 단일 guard의 `cap 축소`, `real-like EV 제외`, `counterfactual 보존` 3가지만 본다. origin별 gap %, score floor, reject reason은 별도 family로 분해하지 않는다.

- [x] `[SwingSameSymbolLossReentryGuard0512] 스윙 동일종목 손실 후 재진입 guard 구현 및 문서 반영` (`Due: 2026-05-12`, `Slot: POSTCLOSE`, `TimeWindow: 18:55~19:10`, `Track: SwingLogic`)
  - 판정: pass
  - 근거: 스윙/probe 손실 청산 후 동일 종목/전략 신규 BUY·probe를 60분 차단하는 `swing_same_symbol_loss_reentry_guard`를 추가했다. stop-loss 계열 `<= -2.5%` 또는 당일 연속 손실 2회가 trigger이며, blocked 후보는 `swing_reentry_counterfactual_after_loss`로 분리해 `actual_order_submitted=false`, `broker_order_forbidden=true`, `runtime_effect=counterfactual_only`를 강제한다.
  - 다음 액션: 장후 swing lifecycle/EV에서 real-like EV와 cooldown counterfactual이 섞이지 않는지 확인하고, real canary approval 전에도 pre-submit guard를 mandatory로 유지한다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_model_selection_funnel_repair.py` 및 checklist/parser 검증 수행.

- [x] `[LogScannerDbErrorBurstFalsePositive0512] log_scanner DB_ERROR burst 오탐 보정` (`Due: 2026-05-12`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: RuntimeStability`)
  - Source: [log_scanner.py](/home/ubuntu/KORStockScan/src/engine/error_detectors/log_scanner.py), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정: `false_positive_fixed`.
  - 근거: `update_kospi_error.log`의 실제 DB 적재는 성공(`DB 일괄 삽입 성공`, `대시보드 파일 DB 업로드 완료`)했지만 `_error.log` 파일 안의 INFO성 DB 문장이 `DB_ERROR` 패턴에 걸려 `log_scanner` burst로 승격됐다. 실제 남은 실패는 `recommend_daily_v2` non-zero이며 DB 장애 근거는 아니다.
  - 조치: `log_scanner`가 `ERROR`/`CRITICAL`/traceback/exception/에러/오류/실패 등 에러 후보 라인만 분류하도록 좁혔다. `_error.log`에 섞인 INFO/WARNING성 DB 성공·업로드 라인은 더 이상 `DB_ERROR`로 계산하지 않는다.
  - 후속 조치 (`2026-05-12 21:43 KST`): `recommend_daily_v2` 실패 원인은 파일 경로 실행 시 repo root가 `sys.path`에 없어 joblib artifact unpickle 중 `ModuleNotFoundError: No module named 'src'`가 발생한 것이었다. [recommend_daily_v2.py](/home/ubuntu/KORStockScan/src/model/recommend_daily_v2.py)에 repo root sys.path bootstrap을 추가하고, [update_kospi.py](/home/ubuntu/KORStockScan/src/utils/update_kospi.py)의 subprocess 호출을 절대경로 + `cwd=PROJECT_ROOT`로 고정했다. 동일 실행 방식인 `.venv/bin/python src/model/recommend_daily_v2.py` 재실행은 성공했고 `data/daily_recommendations_v2.csv`가 `selected=3`, `floor=0.35`로 갱신됐다.
  - 완료 다음 액션: 운영 확인 시에는 `logs data` 전체 광역 검색을 피하고 대상 로그 tail/상태 JSON/개별 파일 grep으로 제한한다. 남은 `artifact_freshness` warning은 `threshold_events` sparse stream 및 swing daily simulation one-shot stale 판정으로, `recommend_daily_v2`/DB 장애와 분리한다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_error_detector_log_scanner.py src/tests/test_error_detector_artifact_freshness.py src/tests/test_swing_feature_ssot.py` 통과, `py_compile` 통과, `LogScanner(dry_run=True)=pass`, `update_kospi_status_content_status=completed`.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->


## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-05-12 19:05:37`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-05-12.md`
- `Trade Review`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Performance Tuning`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Post Sell Feedback`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Entry Pipeline Flow`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
<!-- AUTO_SERVER_COMPARISON_END -->
