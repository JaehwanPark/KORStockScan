# 2026-08-13 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-08-12` postclose -> `2026-08-13`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0813] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-08-13`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-12.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-12.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0813] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-08-13`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-08-12.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-08-12.json), [code_improvement_workorder_2026-08-12.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-12.json), [threshold_apply_2026-08-13.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-08-13.json), [threshold_runtime_env_2026-08-13.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-08-13.json), [threshold_runtime_env_verify_2026-08-13.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-08-13.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`1`, forced_scout_with_post_sell_count=`0`, post_sell_join_coverage_pct=`0`, outcome_coverage_state=`no_closed_outcome`, profitable_forced_scout_count=`0`, loss_or_flat_forced_scout_count=`0`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [x] `[EmbeddedHypothesisCleanBaselineGate0813] embedded 가설 관측계획 clean-baseline 소비 가드 구현·리뷰` (`Due: 2026-08-13`, `Slot: INTRADAY`, `TimeWindow: 08:00~15:20`, `Track: RuntimeStability`)
  - Source: [source_quality_clean_baseline.py](/home/ubuntu/KORStockScan/src/engine/automation/source_quality_clean_baseline.py), [scalp_sim_auto_approval_control_tower.py](/home/ubuntu/KORStockScan/src/engine/scalping/scalp_sim_auto_approval_control_tower.py), [sim_auto_approval_control_tower.py](/home/ubuntu/KORStockScan/src/engine/swing/sim_auto_approval_control_tower.py), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py)
  - 구현 결과: scalp/swing sim policy catalog는 target date 이하의 가설 관측계획을 최신순으로 탐색하되 `source_report_date>=2026-06-05`인 첫 artifact만 포함한다. runtime policy loader와 PREOPEN manifest/handoff 검증은 pre-baseline·누락·비정상 embedded evidence를 소비하지 않으며 provenance gate를 보존한다.
  - 권한 경계: source-quality/sim policy 소비 가드이며 실주문·수량·provider·threshold 권한을 추가하지 않는다. `runtime_effect=false`인 hypothesis evidence만 대상으로 하고, invalid embedded plan은 archive-only 또는 runtime-policy unusable로 fail-closed한다.

- [x] `[SamsungWidgetWebSocketPriceComparison0813] 삼성 위젯 기존가·WS 0B 현재가 2초 비교 관측 구현·리뷰` (`Due: 2026-08-13`, `Slot: INTRADAY`, `TimeWindow: 08:00~15:20`, `Track: RuntimeStability`)
  - Source: [samsung_price_widget.py](/home/ubuntu/KORStockScan/tools/windows/samsung_price_widget.py), [samsung_price_widget_routes.py](/home/ubuntu/KORStockScan/src/web/samsung_price_widget_routes.py), [kiwoom_websocket.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py), [키움 API 데이터 계약](/home/ubuntu/KORStockScan/docs/kiwoom-api-data-contract.md)
  - 구현 결과: 기존 10초 collector/REST 표시가와 공유 Kiwoom WebSocket `0B` 체결 현재가를 분리해 `WS/KRX|NXT|SOR`, 가격차, 수신 경과시간을 2초 Windows 주기로 표시한다. WS dashboard bridge는 1초 상한이며 5초 stale, source/item/timestamp/authority 불일치는 `WS: 수신 대기`로 fail-closed한다.
  - 권한 경계: `widget_ws_price_comparison_only`, `runtime_effect=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`, `used_for_manual_order=false`이며 큰 표시가·수동주문 가격검증·수량·제출은 기존 collector snapshot만 사용한다. 비교전용 삼성 SOR item `005930_AL` 하나만 거래 WS item budget에서 제외하여 기존 거래 구독을 대체하지 않고, 비활성 target prune/REMOVE에서 유지한다. 같은 종목의 KRX/NXT 등 비고정 route는 정상 예산·REMOVE 대상이다.
  - Official reference gate: upstream `Kiwoom-Securities/Kiwoom-REST-API` SHA `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`, retrieval `2026-08-13T08:00:25+09:00`; `kiwoom_docs/실시간시세.md`, `kiwoom/realtime/packets.py`, `kiwoom/realtime/{events,decoders,schemas,stream}.py`, `kiwoom/core/ws_client.py`, Postman의 `REG/REMOVE`, `refresh=1`, `0B` FID 10/20, KRX/NXT/SOR suffix를 검증했다.
  - 반영 상태 (`2026-08-13 08:10~08:11 KST`): 사용자의 명시적 승인 후 Gunicorn master `635`를 유지하고 worker `935/977 -> 31103/31105`를 HUP 교체했다. 표준 `restart.flag` 경로로 main bot PID `22015 -> 31454`를 graceful 재기동했고 flag 소비, tmux `bot` active, PREOPEN runtime env verify `status=pass`, `pid_passed=true`, finding/runtime-policy/dated-override/unverified family=`0`-을 확인했다. 신규 PID는 `005930_AL` REG source=`sniper_boot_priority_and_widget_observation_ws_budget`로 고정 구독했고 1초 dashboard에 fresh `0B` tick을 남겼다. 인증 API 실관측은 primary `266,500원`, WS/SOR `266,000원`, delta `-500원`, age `882ms`, `runtime_effect=false`, `used_for_manual_order=false`였다. 독립 삼성 morning/add-on 기계와 widget auto trader service는 모두 active를 유지했으며 주문·threshold·provider는 변경하지 않았다. Windows 2초 UI는 신규 파일 재설치 후 표시된다.

- [x] `[EpisodeKa10080RateLimitGuard0813] 에피소드 기계 ka10080 1700 요청량 초과 완화·리뷰` (`Due: 2026-08-13`, `Slot: INTRADAY`, `TimeWindow: 10:00~15:20`, `Track: RuntimeStability`)
  - Source: [kiwoom_episode_read_control.py](/home/ubuntu/KORStockScan/src/trading/order/kiwoom_episode_read_control.py), [regular_two_leg_machine.py](/home/ubuntu/KORStockScan/src/trading/order/regular_two_leg_machine.py), [low-price two-leg runbook](/home/ubuntu/KORStockScan/docs/low-price-two-leg-machines.md), [Kiwoom API data contract](/home/ubuntu/KORStockScan/docs/kiwoom-api-data-contract.md)
  - 구현 결과: 저가 2-leg 13개 profile과 삼성 morning/midday/afternoon이 같은 KST 분 안에서 직전 1분 완료봉까지 포함한 정상 snapshot만 프로세스 안에서 재사용하고, 분 경계에서 아직 최신 완료봉이 공개되지 않은 정상 응답은 캐시하지 않아 다음 bounded poll이 재조회한다. 에피소드 `ka10080` 요청은 공유 파일락으로 최소 0.4초 분산한다. 명시적인 Kiwoom `1700` 또는 HTTP 429 읽기만 0.8초/1.6초 backoff로 최대 2회 재시도하며 실패·계약오류 snapshot은 캐시하지 않는다. 정상 소스 회복 시 일시 `blocked_reason`도 해제한다.
  - 권한 경계: 로컬 0.4초는 공식 rate 수치가 아니라 당일 관측된 `유량=5` 버스트에 여유를 둔 운영 guard다. `kt10000/kt10001/kt10003` 주문·매도·취소는 재시도 경로에 들어가지 않으며 수량·가격·진입·청산·무손절·owner·provider·main bot 계약을 바꾸지 않는다. 공식 upstream SHA `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`의 `kiwoom_docs/차트.md`, `kiwoom/specs.py`, `kiwoom/core`, Postman을 `2026-08-13T10:07:49+09:00`에 재확인했다.
  - 장중 반영 안전: 10:09 KST 카카오 late-morning에 자체 매수·목표 주문 custody가 있어 리뷰 전 및 주문 보유 중인 프로세스 재기동을 금지했다. 이후 시작하는 midday/afternoon 서비스는 새 코드로 자동 기동하고, 실행 중 late-morning은 자기 주문이 terminal이 된 뒤에만 필요 시 재기동한다.
  - 리뷰/검증: 1차 자체리뷰에서 1700 복구 뒤 전략은 계속 평가해도 상태의 일시 `blocked_reason`이 남는 표시 결함을 찾아 정상 source 회복 시에만 해제하도록 보완했다. PR #49 P1 리뷰에서는 분 경계 pre-publication 정상 응답도 1분 전체 캐시되어 신호가 늦어질 수 있는 결함을 찾아 네 gateway 모두 최신 완료봉 존재 시에만 캐시하도록 보완했다. 에피소드 읽기 제어·저가 2-leg policy/service/preflight/research/postclose consumer·삼성 세 기계 회귀 `471 passed`, Ruff, 저장소 전체 Black, compileall, checklist parser count=`30`, `git diff --check`와 PR 보호체크를 통과한 뒤 미해결 finding `0`으로 닫는다. 10:13 KST 주문 없는 인증 `ka10080` smoke는 `source_ok=true`, 완료봉 `72`, 오류 없음이었고 공용 pacer 파일 생성을 확인했다.

- [x] `[EpisodeOrderQuantityTenPerLeg0813] 독립 에피소드 기계 신규 주문 leg당 10주 전환·부분체결 보호·당일 반영` (`Due: 2026-08-13`, `Slot: INTRADAY`, `TimeWindow: 11:30~13:10`, `Track: RuntimeStability`)
  - Source: [episode_quantity.py](/home/ubuntu/KORStockScan/src/trading/order/episode_quantity.py), [regular_two_leg_machine.py](/home/ubuntu/KORStockScan/src/trading/order/regular_two_leg_machine.py), [삼성 오전 runbook](/home/ubuntu/KORStockScan/docs/samsung-morning-one-share-machine.md), [저가 2-leg runbook](/home/ubuntu/KORStockScan/docs/low-price-two-leg-machines.md)
  - 사용자 결정: 지금 이후 독립 에피소드 기계의 신규 매수는 기존 leg당 1주에서 leg당 10주로 변경한다. 두 leg 50:50 구조이므로 기계별 신규 episode 상한은 20주다. widget 자동매매와 메인 봇은 별도 owner이며 변경 대상이 아니다.
  - 구현 계약: 신규 state만 leg당 10주로 만들고, 배포 전부터 소유한 1주 주문·목표·보유는 수량을 소급 변경하지 않고 같은 주문 ledger로 계속 custody한다. 1~9주 부분체결이면 그 exact buy order의 잔량만 취소·재확인한 뒤 최종 확인 체결수량만 +2호가 목표 주문으로 낸다. 목표 부분체결은 잔여 보유수량을 보존하며 손절·시간청산·강제매도는 추가하지 않는다.
  - 정책/자동화 경계: 수량은 postclose 튜닝 축이 아니라 명시적 operator baseline이다. 과거 2주 clean-baseline 연구 artifact는 소급 재작성하지 않고 연구 provenance로만 유지하며, 신규 실제 수량은 당일 authority와 이후 실제 outcome attribution에 기록한다. 기존 주문 custody가 있는 서비스는 재기동하지 않고 향후 신규 episode에만 반영한다.
  - Official reference gate: upstream `Kiwoom-Securities/Kiwoom-REST-API` SHA `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`, retrieval `2026-08-13T11:30:00+09:00`; `kiwoom_docs/주문.md`, `kiwoom/specs.py`, `kiwoom/_data/kiwoom_api_spec.json`, Postman의 `kt10000/kt10001 ord_qty`, `kt10003 cncl_qty=0` exact-order 잔량취소, `kt00007 ord_qty/cntr_qty/oso_qty`를 재확인했다.
  - 완료 기준: 리뷰 게이트 finding `0`, 신규 10주·부분체결·legacy 1주·owner 격리·authority schema 회귀 통과, checklist parser와 `git diff --check` 통과, 당일 아직 시작하지 않은 midday/afternoon authority 재생성 및 시작상태 확인. 현재 보유 주문 또는 terminal morning 서비스는 재기동하지 않는다.
  - 리뷰/검증/반영: 1차 리뷰에서 손상 구형 state 숫자 필드의 생성자 예외와 장후 consumer의 목표 부분체결 오분류를 보완했다. 전체 회귀에서 2026-08-12 `quantity=2` candidate가 내일 PREOPEN에서 invalid로 막히는 마이그레이션 결손을 찾아, 원본 hash/provenance 검증 뒤 runtime에서만 `quantity=20`으로 정규화했다. 게시 전 재리뷰에서는 삼성·저가 2-leg 장후 consumer가 여전히 leg당 1주만 허용하고 EV 명목금액에 실제 수량을 반영하지 않는 결함과 한 episode 안의 legacy 1주/new 10주 혼합 손상 상태를 찾아, 양 수량의 동질적인 episode만 수용하면서 실제 체결수량과 주문수량으로 EV를 계산하도록 보완했다. 직접 2026-08-14 apply는 `candidate_applied`, validation=`valid`, 전 profile quantity=`20`, 카카오 morning target=`3`을 확인했다. 관련 회귀 `279 passed`, Black/Ruff/compileall/checklist parser/`git diff --check`를 통과했고 최종 finding은 `0`이다. 저장소 전체 회귀는 `7505 passed, 18 skipped`와 실패 `7`이었으며, 이번 API signature 회귀 1건은 수정·재통과했고 나머지 6건은 작업 전 별도 dirty 변경/기준일 테스트로 분리했다. 11:54 KST 신규 주문·보유가 없는 midday/afternoon 8개 authority를 schema v2/v4, total=`20`, leg=`10`으로 재생성·검증했으며 13:14/13:59 기존 timer 기동을 유지했다. 종료된 morning, widget, main bot은 재기동하지 않았다.

- [ ] `[RuntimeEnvIntradayObserve0813] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-08-13`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-12.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-12.json)
  - 전일 postclose candidate_selected_families=entry_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, scalping_pyramid_quality_gate, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0813] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-08-13`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-08-12.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-12.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0813] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-08-13`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-08-13.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-13.jsonl), [threshold_events_2026-08-13.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-13.jsonl), [observation_source_quality_audit_2026-08-13.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-13.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-08-13 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[PostcloseSourceQualityGateReview0813] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-08-13`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-08-13.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-13.json), [threshold_cycle_ev_2026-08-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-13.json), [code_improvement_workorder_2026-08-13.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-13.json), [threshold_cycle_postclose_verification_2026-08-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-08-13.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0813] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-08-13`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-08-12.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-08-12.json), [threshold_cycle_ev_2026-08-12.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-12.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0813] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-08-13`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-12.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-12.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0813] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-08-13`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-08-12.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-08-12.md), [code_improvement_workorder_2026-08-12.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-12.json)
  - 판정 기준: selected_order_count=55와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0813] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-08-13`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-08-12.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-12.json), [runtime_apply_gap_audit_2026-08-12.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-12.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`254`, rollup_required_count=`254`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 253}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0813] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-08-13`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-08-12.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-08-12.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`14`, run_count=`9`, skip_count=`0`, source_missing_count=`4`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:8, disabled_by_runtime_policy:5, upstream_drift_signal:5, source_missing_or_unreadable:4, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Micro-Reversion 관찰

- [x] `[MicroReversionExactSourceExclusion0813] current-source baseline·실패 epoch 제외·P2 fail-closed 소비 구현 및 리뷰` (`Due: 2026-08-13`, `Slot: INTRADAY`, `TimeWindow: 08:50~09:15`, `Track: ScalpingLogic`)
  - Source: [source exclusion manifest](/home/ubuntu/KORStockScan/configs/scalp_micro_reversion_source_exclusions.json.txt), [P2 replay](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/p2_replay.py), [Gate B source-quality result](/home/ubuntu/KORStockScan/docs/audit-reports/2026-08-13-scalp-micro-reversion-gate-b-source-quality-result.md), [current-source baseline](/home/ubuntu/KORStockScan/docs/audit-reports/2026-08-13-scalp-micro-reversion-callback-latency-baseline-depth-source.json.txt)
  - 구현 결과: 실패 범위를 `trade_date+venue+session+sequence_epoch` 7개 scope로 고정해 stream `196,935`행과 reference `5,689`건을 제외한다. P2 canonical loader는 manifest missing/invalid/authority/count drift와 제외 reference를 fail-closed하고, canonical V3 timestamp regression row를 imputation 없이 제외한다.
  - 관찰 결과: 보존 stream `1,203,067`, unique segment `15,306`, reference coverage `100%`, complete segment `14,289` (`93.356%`)다. current-source 0B internal p95/p99 max는 `0.024541/0.037579ms`, 0D 5,000건은 drop/error 없이 전량 persist했다.
  - 권한 경계: Gate B=`HOLD`, P2 real-data discovery/ranking·sim·trading runtime·broker order·threshold/provider/bot/quantity/cap 변경은 열지 않는다.

- [ ] `[MicroReversionGateBRecheck0814] 5번째 거래일 exact-scope source-quality 및 Gate B 재판정` (`Due: 2026-08-14`, `Slot: POSTCLOSE`, `TimeWindow: 20:05~20:25`, `Track: ScalpingLogic`)
  - Source: [source exclusion manifest](/home/ubuntu/KORStockScan/configs/scalp_micro_reversion_source_exclusions.json.txt), [Gate B source-quality result](/home/ubuntu/KORStockScan/docs/audit-reports/2026-08-13-scalp-micro-reversion-gate-b-source-quality-result.md), [forward observations](/home/ubuntu/KORStockScan/data/observations/scalp_micro_reversion_forward)
  - 판정 기준: 최소 5거래일, 성숙/complete segment `>=200`, required path/reference coverage `>=90%`, duplicate/gap/drop/writer/recovery 계약과 raw-row exact exclusion을 함께 확인한다. timestamp regression row는 제외하되 날짜 전체를 자동 폐기하거나 보간하지 않는다.
  - 금지: Gate B 이전 P2 actual-path discovery/ranking, Gate B만으로 sim/live 승격, broker/order/provider/bot/threshold/quantity/cap 변경을 열지 않는다.
  - 다음 액션: `collector_health_pass_research_data_only`, `path_coverage_insufficient`, `source_exclusion_incomplete`, `journal_degraded` 중 하나로 닫고, 통과 시에만 별도 P2 discovery policy/cohort/cost freeze 작업을 연다.



## 독립시간대 매매기계

- [x] `[RepositoryBlackGate0813] PR #49 저장소 전체 Black 보호체크 보완` (`Due: 2026-08-13`, `Slot: INTRADAY`, `TimeWindow: 10:52~11:10`, `Track: RuntimeStability`)
  - Source: [PR #49](https://github.com/JaehwanPark/KORStockScan/pull/49), [P2 replay](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/p2_replay.py), [frozen baseline](/home/ubuntu/KORStockScan/docs/audit-reports/2026-08-13-scalp-micro-reversion-callback-latency-baseline-depth-source.json.txt)
  - 판정: 사용자 지시 변경은 로컬 Black을 통과했으나 GitHub 저장소 전체 `black --check .`가 main 선행 변경의 미포맷 파일 4개를 검출했다. 해당 파일에 기계적 포맷만 적용하고 P2 source SHA 변경은 frozen baseline에 이전/현재 hash·사유·`runtime_effect=false`로 기록한다.
  - 금지: callback 측정값·frozen limit·Gate B HOLD·discovery/sim/trading/order/provider/bot/quantity/cap 권한 변경, baseline 재측정으로 오인, 운영 프로세스 재기동을 허용하지 않는다.
  - 리뷰/검증: 포맷 diff는 괄호·줄바꿈·trailing comma만 바뀌어 의미 불변이다. micro-reversion/Opening/Error Detector 회귀 `215 passed`, frozen hash guard, 저장소 전체 Black `754 files unchanged`, compile, baseline JSON parse, checklist parser, `git diff --check`를 통과했다. 보완 commit push 뒤 PR 보호체크가 통과한 경우에만 main 병합한다.

- [x] `[KakaoMorningTarget3Transition0813] 카카오 morning +3호가 목표의 익일 PREOPEN 전환·실소비 계약 보완` (`Due: 2026-08-13`, `Slot: INTRADAY`, `TimeWindow: 10:20~15:20`, `Track: RuntimeStability`)
  - Source: [policy runtime](/home/ubuntu/KORStockScan/src/trading/low_price_two_leg/policy_runtime.py), [PREOPEN apply](/home/ubuntu/KORStockScan/src/engine/automation/low_price_two_leg_policy_apply.py), [service](/home/ubuntu/KORStockScan/src/trading/low_price_two_leg/service.py), [preflight](/home/ubuntu/KORStockScan/src/trading/low_price_two_leg/preflight.py), [runbook](/home/ubuntu/KORStockScan/docs/low-price-two-leg-machines.md)
  - 구현: `2026-08-13` 카카오 morning의 +2호가 실행·귀속은 보존하고 `2026-08-14` exact-date PREOPEN 정책부터 해당 profile만 +3호가를 적용한다. 서비스는 applied target을 실제 profile에 결합하고 authority에는 baseline/effective-date/사용자 지시 provenance를 기록한다. source-only 실행계획에는 +3호가 비교축을 추가한다. 장후 evidence 검토 뒤 사용자가 명시적으로 복귀를 지시한 경우에만 다음 PREOPEN에서 +2호가로 복원하며 기존 소유 목표주문은 취소·교체하지 않는 rollback을 전환 메타데이터에 고정한다.
  - 판정: 오늘 체결 39,250/39,200원 기준 익일 정책 목표는 각각 39,400/39,350원이다. Kakao late morning과 다른 profile, 진입, 1주×2 allocation, no-stop 보유, broker/order/provider/bot guard는 불변이어야 하며 오늘 서비스·주문은 재기동하거나 변경하지 않는다.
  - 리뷰/검증: 1차 리뷰에서 profile 객체에 없는 `discovery_lane` 조건 때문에 카카오 전용 +3호가 source-only 비교축이 후보 grid에 들어가지 않는 결함을 확인해, 다른 profile을 확장하지 않는 전용 축으로 보완했다. 게시 전 리뷰에서는 전환 메타데이터의 rollback 누락과 자동 rollback consumer가 없는 상태에서 장후 자동복원으로 읽힐 수 있는 문구를 발견해 사용자 명시 복귀 전용 계약으로 보완했다. 에피소드 읽기 제어·저가 2-leg policy/service/preflight/research/postclose consumer·삼성 세 기계 회귀 `467 passed`, Black, Ruff, compileall, checklist parser count=`30`, `git diff --check`를 통과했고 최종 미해결 finding은 `0`이다. 2026-08-14 actual candidate dry-run은 source date=`2026-08-12`, hash=`f235fc0bb11157225dbb99053c70f84b17dab2af8696fbe4726559cce28a4d99`, compiled baseline 대비 변경=`kakao_morning.target_ticks 2 -> 3` 한 건임을 확인했다. 오늘 exact-date 정책은 target=`2`, validation=`valid`를 유지하며 서비스·주문 재기동/변경은 수행하지 않았다.

- [ ] `[SamsungMorningManualAddon1000813] 삼성전자 morning 오늘 한정 100주 수동매도용 추가 BUY 실행·귀속 확인` (`Due: 2026-08-13`, `Slot: PREOPEN`, `TimeWindow: 07:57~09:35`, `Track: RuntimeStability`)
  - Source: [manual_addon.py](/home/ubuntu/KORStockScan/src/trading/samsung_morning_one_share/manual_addon.py), [exact-date timer](/home/ubuntu/KORStockScan/deploy/systemd/korstockscan-samsung-morning-manual-addon-20260813.timer), [Kiwoom contract](/home/ubuntu/KORStockScan/docs/kiwoom-api-data-contract.md)
  - 실행: 사용자 명시 지시에 따라 `2026-08-13`에만 기존 morning BUY leg의 route·가격을 따라 50주씩 2개, 최대 100주를 별도 원장으로 주문한다. 기존 1주×2 episode 주문과 자동 +2호가 목표는 변경하지 않는다.
  - 판정: normal morning source order가 broker 접수되고 source episode/leg가 아직 active인 경우에만 mirror하며, terminal/completed source의 지연 추종은 금지한다. add-on exact-order fill/remainder와 NXT 취소 후 SOR 잔량 이동을 대사한다. 체결수량은 `manual_sell_required_quantity`로 기록하고 기계 SELL은 금지한다.
  - 금지: add-on target/stop/강제청산, 자동매도, 100주 초과, 기존 episode/widget/main-bot 주문 취소·매도, 다른 날짜 재실행, source order 이전 선행 주문을 허용하지 않는다.

- [ ] `[EpisodeMachineExpandedProfileFirstPreflight0813] 13-profile 첫 PREOPEN 실기동 검증` (`Due: 2026-08-13`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:15`, `Track: RuntimeStability`)
  - Source: [tracked evidence projection](/home/ubuntu/KORStockScan/data/config/low_price_two_leg_expanded_profile_evidence_2026-08-12.json), [installer](/home/ubuntu/KORStockScan/deploy/install_low_price_two_leg_systemd.sh), [runbook](/home/ubuntu/KORStockScan/docs/low-price-two-leg-machines.md)
  - 선행 실행 완료 (`2026-08-12 22:30 KST`): 사용자 지시에 따라 reviewed installer로 13-profile 26개 timer와 2개 template unit을 설치·활성화했다. 설치본은 tracked source와 일치하고 active profile service는 `0`이라 소급 실주문이 없으며, 카카오·한국전력 owner는 `manual_operator`로 분리됐다. 다음 session dry-run은 13-profile candidate hash `aa066f3c84db7abad3421ee35bae6a26a792e140cc098a441601c4496ab3cd30`을 통과했고 exact-date applied artifact는 첫 09:05 preflight가 생성하도록 유지했다. main bot은 crontab 기준 07:55 기동되어 첫 preflight보다 앞선다.
  - 판정: 신규 여섯 preflight의 frozen evidence·shared token·main bot active·manual owner·exact applied hash가 모두 통과하고, 각 service가 자기 profile/state/authority/order ledger만 읽는 경우에만 예약 기동을 인정한다. 설치 전이거나 blocker가 있으면 실주문 없이 `not_installed_or_fail_closed`로 남긴다.
  - 금지: 리뷰 미종료 상태의 설치, 장전 window를 지난 소급 기동, report 원본 누락 우회, widget/다른 episode 원장 사용, 손절·target timeout·강제청산, 수량·provider·bot·cap·broker guard 변경을 허용하지 않는다.


## 위젯 수집·자동매매 운영 보완

- [x] `[WidgetLowSymbolAutoPromotion0813] 두산·한화 장후 검증정책의 익일 자동 런타임 승격 보강` (`Due: 2026-08-13`, `Slot: INTRADAY`, `TimeWindow: 12:55~15:00`, `Track: RuntimeStability`)
  - 판정/owner: 20:10 `widget_auto_trade_policy_calibration --write`가 clean-baseline 누적자료에서 두산·한화의 40 qualified KRX 관측일, calibration/chronological holdout, source quality, execution-quality safety gate를 모두 통과한 세션만 다음 영업일 exact-date 정책으로 승격한다. 07:58 service start 또는 거래일 경계 reload가 `new_entry_runtime_eligible=true`를 자동 반영하며 장중 수동 승격·재기동은 사용하지 않는다.
  - 보완: 미승격 두산·한화 세션도 exact-date `blocked_sessions`와 research count/status/reason으로 loader·runtime에 전달하여 generic `session_unavailable` 대신 누적연구 차단 provenance를 남긴다. ready 세션은 runtime eligible, blocked 세션은 ineligible/reason 일치까지 policy round-trip verifier가 검증한다.
  - 안전/rollback: 신규 leg 10주, KRX SOR, force-flat/overnight 금지, manual owner, stale/price/broker/order/quantity/cooldown guard는 유지한다. 정책 미생성·source/holdout/execution-quality 실패·loader mismatch는 fail-closed 관측 전용이며 rollback은 blocked-session 확장과 강화 verifier를 복원하는 것이다.
  - 검증: producer→evidence→exact-date policy→loader temp replay는 ready 1/blocked 4 session, verification PASS였고 기존 widget 확장 회귀 `462 passed`를 확인했다. Black/Ruff/compile/systemd/checklist parser/`git diff --check`를 통과하고 review gate finding 0에서 닫는다.

- [x] `[WidgetAutoTradeTenShareQty0813] 위젯 매매기계 신규 BUY leg 1주→10주 운영 변경` (`Due: 2026-08-13`, `Slot: INTRADAY`, `TimeWindow: 11:30~15:00`, `Track: RuntimeStability`)
  - 사용자 권한/범위: 사용자의 명시적 수량 변경 지시에 따라 위젯 자동매매 owner의 이후 신규 BUY leg만 `1→10주`로 변경한다. 기존 에피소드·접수 주문·체결·익절 잔량은 원래 수량으로 귀속하며 main bot, 독립 시간대 기계, 수동 위젯 주문은 범위 밖이다.
  - 단일 owner/노출: service env, legacy fallback, postclose exact-date producer/loader가 공통 `leg_quantity_each=10`을 사용한다. 추가매수 2개가 선택된 정책은 에피소드 최대 30주이며 기존 freshness, manual-owner, global BUY pause, 중복·미체결, broker route/체결대사/TP coverage guard를 유지한다.
  - 적용/rollback: 적용 전 삼성전자 기존 원장은 BUY 1주 체결과 TP SELL 1주 미체결을 보존한다. rollback은 공통 leg 수량, service env, legacy policy를 1주 정책으로 복원하고 새 exact-date policy를 재생성한 뒤 기존 주문 대사 후 우아하게 재기동하는 것이다.
  - Kiwoom 공식 참조: upstream SHA `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`의 `kiwoom_docs/주문.md`, `kiwoom_docs/계좌.md`, `kiwoom/specs.py`, `kiwoom/core`, Postman `kt10000/kt10001/kt10003/kt00007` 및 `ord_qty` 단위 계약을 `2026-08-13T11:31:37+09:00`에 재확인했다.
  - 리뷰/검증/반영: review gate 무결함, policy temp replay verified, 기존 1주 원장 복원 회귀를 포함한 widget 확장 회귀 `460 passed`, Black/Ruff/compile/systemd/checklist parser/`git diff --check`를 통과했다. exact-date policy와 설치 unit 반영 후 PID `24014→170214`, `ENTRY_QTY=10`, legacy policy `SAMSUNG_EQUAL_10_ADD0P5_ADD1P0_TP0P5_V2`, runtime state `entry_qty=10`을 확인했다. 재기동 전 체결 BUY 1주와 TP SELL 1주 주문 `0015385`는 그대로 보존됐고 재기동 시각 이후 신규 주문 이벤트는 없다.

- [x] `[WidgetRuntimeCollectorStability0813] 4종목 수집기 budget 경계·종목 격리 및 자동매매 상태 provenance 보완` (`Due: 2026-08-13`, `Slot: INTRADAY`, `TimeWindow: 10:05~10:35`, `Track: RuntimeStability`)
  - 판정: 4종목 primary/peer/2개 index/수급 호출이 rolling-minute 캐시 경계에서 36회 한도를 초과해 required `ka10080`이 실패하고 systemd 재시작한 원인을 확인했다. 계산된 경계 overlap 52회에 제한된 여유를 둔 로컬 read-only 64회 한도와 종목별 `DATA_WAIT` fail-closed 격리·순환 시작 순서·budget provenance를 추가했다. 주문·계좌·token issue/refresh·실주문 정책은 변경하지 않았다.
  - 자동매매 provenance: 동일 source exit의 invalid-policy 차단 이벤트는 signal ID별 1회만 기록하고, 정책 적격(`policy_execution_eligible_symbols`, `policy_execution_sessions`)과 현재 주문권한 적격(`execution_eligible_symbols`, `runtime_execution_policy_sessions`), `monitored_symbols`, `observation_only_symbols`를 분리했다. 기존 `enabled_symbols`는 호환 필드로 유지한다.
  - Kiwoom 공식 참조: `Kiwoom-Securities/Kiwoom-REST-API` SHA `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`, 확인시각 `2026-08-13T10:18:06+09:00`, `kiwoom_docs/시세.md`, `kiwoom_docs/차트.md`, `kiwoom_docs/종목정보.md`, `kiwoom/specs.py`, `kiwoom/core`, `kiwoom/realtime`, Postman을 재확인했다. 기존 `ka10001/ka10004/ka10064/ka10080/ka20005/ka90008` 요청 계약은 변경하지 않았다.
  - 리뷰/검증: widget consumer 확장 회귀 `271 passed`, 최종 targeted 회귀 `80 passed`, Black, Ruff, compile, checklist parser count=`30`, `git diff --check`를 통과했고 최종 미해결 finding은 `0`이다. 명시적 서비스 재기동은 수행하지 않았으나 기존 crash-loop의 systemd 자동복구가 새 collector 코드를 10:24:16 KST에 로드했고, 10:30:48까지 restart counter=`98` 고정·4종목 snapshot `PASS`를 확인했다. 장기 실행 auto-trader PID `24014`에는 provenance/dedup 보완이 아직 미반영이다.

- [x] `[EpisodePostcloseTuningIntegrity0813] 에피소드 장후 튜닝 exact-policy·rolling·실체결 EV·verifier 보완` (`Due: 2026-08-13`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~22:30`, `Track: RuntimeStability`)
  - 판정/구현: 2026-08-14 이후 저가 2-leg와 삼성 기계 attempted row는 exact-date PREOPEN applied policy/hash/entry fields를 대조한다. 카카오 morning +3호가는 compiled +2호가가 아니라 당일 applied policy로 target을 검증한다. 삼성은 clean cumulative 외 rolling 10/20 거래일 창을 생성하고 세 창의 broker-priced notional EV가 모두 양수일 때만 bounded candidate를 허용한다.
  - 실체결/안전: 신규 target reconciliation은 공식 `kt00007.cntr_uv` 매도 체결단가를 owner state에 저장한다. 실제 broker-price 표본만 decision EV와 20-leg floor에 사용하고 기존 목표가 proxy는 별도 진단값으로 분리한다. 날짜를 넘겨 체결된 durable state는 원 거래일 row로 재귀속해 과거 HELD를 중복·영구 잔존시키지 않는다. 수량·진입·목표 정책, no-stop/HELD, provider/bot/cap, broker/account/order/cooldown guard와 owner 격리는 변경하지 않는다.
  - chain verifier: final postclose verifier가 Samsung report/candidate schema, target date, machine inventory, cumulative·rolling10·rolling20 window, authority, candidate hash/lineage를 검증하며 wrapper의 `samsung_machine_entry_tuning=true`인데 산출물이 누락되면 fail-close한다.
  - Kiwoom 공식 참조: upstream `Kiwoom-Securities/Kiwoom-REST-API` SHA `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`, 확인시각 `2026-08-13T22:12:21+09:00`; `kiwoom_docs/계좌.md`, `kiwoom/specs.py`, `kiwoom/core`, Postman의 `kt00007`, `cntr_uv`, `ord_remnq`, 연속조회와 SOR 계약을 재확인했다.
  - 완료 기준: 에피소드 producer/consumer/runtime-state/verifier targeted 회귀, Black/Ruff/compileall, checklist parser, `git diff --check`를 통과하고 review gate 미해결 finding 0으로 닫는다. 서비스 재기동·실주문·리포트 재생성은 수행하지 않는다.

- [x] `[SmoothingExactPathIngestion0813] smoothing source-only exact-path 수집·partition 대사·SELL_ORDERED 관찰 보완` (`Due: 2026-08-13`, `Slot: POSTCLOSE`, `TimeWindow: 22:30~23:20`, `Track: ScalpingLogic`)
  - 판정/구현: `smoothing_source_only_path_{armed,horizon,closed}`를 검증된 `journal_family`별 threshold partition으로 동적 라우팅하고 raw→written→partition→daily journal `source_event_counts`를 대사한다. 구형 completed checkpoint는 0→0으로 승격하지 않고 `coverage_complete=false`, 잘못된 family는 `unroutable_stage_count`로 fail-close한다. SELL_ORDERED 보유 중에는 주문 취소·교체·제출 없이 source-only 상태만 계속 관찰해 체결 대기 때문에 10/20/40/60/90초 exact horizon이 끊기지 않게 했다.
  - 권한 경계: `runtime_effect=false`, `allowed_runtime_apply=false`, `eligible_for_live_review=false`이며 soft-stop OFF/ON, OFI smoothing ON/OFF, 매도 주문, hard/emergency stop, threshold, 수량, provider, cap, bot 상태를 변경하지 않는다.
  - 장후 원천 재검증: postclose 표준 immutable snapshot gzip(`309,011,027` bytes)을 raw 293,908행까지 bounded 59-chunk로 재생성해 threshold row 19,491건을 기록했다. ingestion audit는 `coverage_complete=true`, `unroutable=0`, raw=written=partition이고 soft-stop armed=`2`, horizon/closed=`0`, OFI armed/horizon/closed=`0`이다. read-only daily build도 soft-stop arm=`2`, exact complete=`0`, sample floor 미달, pending/missing horizon=`10`을 동일하게 노출했다. 기존 장후 canonical report/AI review는 별도 전체 chain 재실행으로 덮어쓰지 않았다.
  - 리뷰/검증: 2차 리뷰에서 구형 completed checkpoint와 invalid family가 0→0으로 조용히 통과할 수 있는 결함을 찾아 fail-closed coverage/unroutable 계약을 추가했다. 게시 전 재리뷰에서는 partial checkpoint도 처리분의 raw=written=partition만으로 PASS가 될 수 있는 결함을 찾아 checkpoint 완료와 immutable source 존재를 필수화했다. backfill/verifier/journal/loader/pending-sell 결합 회귀 `216 passed`, Black, py_compile, Ruff critical rule, checklist parser, `git diff --check`를 통과하고 최종 미해결 finding은 `0`이다.

## Project/Calendar 동기화

- [ ] `[SmoothingPendingSellRuntimeReflection0814] reviewed smoothing pending-sell observer 최초 runtime 귀속 확인` (`Due: 2026-08-14`, `Slot: PREOPEN`, `TimeWindow: 08:50~10:30`, `Track: ScalpingLogic`)
  - Source: [smoothing source-only observer](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [main sniper loop](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py), [threshold traceability](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정 기준: reviewed commit이 다음 승인된 우아한 재기동/PREOPEN 기동 PID에 반영된 뒤 자연발생 SELL_ORDERED arm에서 `observation_phase=holding` exact horizon이 기록되는지 확인한다. raw→written→partition audit PASS와 daily `source_event_counts` 일치를 함께 확인한다.
  - 금지: 검증을 위해 매도 주문을 만들거나 취소·교체하지 않고, soft-stop/OFI runtime state, threshold, hard/emergency stop, provider, 수량, cap을 바꾸지 않는다.
  - 다음 액션: `runtime_observation_pass`, `no_natural_arm_keep_collecting`, `source_quality_blocked`, `partition_report_mismatch`, `reviewed_code_not_loaded` 중 하나로 닫는다.

- [ ] `[EntryPriceV25KRXFirstObservation0814] KRX 정규장 entry_price V2.5 PREOPEN 반영 및 최초 자연호출 귀속` (`Due: 2026-08-14`, `Slot: PREOPEN`, `TimeWindow: 08:50~10:30`, `Track: ScalpingLogic`)
  - Source: [KRX V2.5 cumulative replay](/home/ubuntu/KORStockScan/data/report/ai_prompt_stage_coverage_replay/ai_prompt_stage_coverage_replay_2026-08-13-v2_5-cumulative-krx_entry_price.json), [live policy](/home/ubuntu/KORStockScan/src/engine/scalping/entry_price_live_policy.py), [AI engine](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py), [dated operator env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/operator_runtime_overrides_2026-08-14.env)
  - 판정 기준: PREOPEN 기동 PID가 reviewed commit과 dated env를 로드하고, exact_v2 preflight를 통과한 `KRX/KRX_REGULAR` 자연 `entry_price` 호출만 `decision_quality_entry_price_v2_5_explicit_fill_value_live_krx_v1`을 사용해야 한다. `provider!=none`, Bedrock Qwen3 32B→Nova Lite v2 failback 경로 불변, V2.5 의미계약 통과, selected exact price와 downstream resolver/submit 결과 귀속을 확인한다. NXT와 PREMARKET은 `entry_price_v1`이어야 한다.
  - rollback: evidence hash·venue/session·preflight·schema/semantic 계약 결손, provider 실패, 신규 missed-upside 또는 severe-tail 증가가 확인되면 `KORSTOCKSCAN_ENTRY_PRICE_V2_5_KRX_ENABLED=false`로 `entry_price_v1`을 복원한다. 가격·수량·threshold·provider route·broker/account/order/cooldown·hard safety guard는 변경하지 않는다.
  - 다음 액션: `krx_v2_5_first_observation_pass`, `control_v1_due_to_contract_gap`, `schema_semantic_rejected_defensive_close`, `provider_route_regression_rollback`, `post_apply_quality_rollback` 중 하나로 닫는다.

- [ ] `[LatencyFalseNegativeVenueBackfill0813] clean-baseline latency false-negative venue/session rolling backfill` (`Due: 2026-08-13`, `Slot: POSTCLOSE`, `TimeWindow: 19:55~20:10`, `Track: ScalpingLogic`)
  - Source: [rising missed feedback producer](/home/ubuntu/KORStockScan/src/engine/monitoring/rising_missed_intraday_feedback.py), [current feedback artifact](/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-08-13.json), [traceability contract](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 현재 판정: 최신 20개 artifact의 latency candidate 482행 중 과거 schema 470행은 explicit venue/session 결손으로 격리됐고, 2026-08-13 KRX 12행만 rolling usable이다. KRX true-OFI cohort는 11행, low-adverse 3행(`27.272727%`), ready 2행(`18.181818%`)으로 두 최소비율 `30%`에 미달하므로 `hold_no_consistent_low_adverse_edge`다.
  - 실행/검증: clean baseline 이후 보존된 exact-date pipeline만 최신 19거래일 범위에서 bounded 순차 재생하고 KRX/NXT/PREMARKET_KRX_LIKE·session·cohort를 혼합하지 않는다. backfill 후 usable/source-gap row와 날짜 coverage, executable ask→후행 executable bid MFE/MAE, `runtime_effect=false`, `allowed_runtime_apply=false`, `decision_authority=source_only_no_retry_or_runtime_mutation`을 검증한다.
  - 금지: 삭제된 latency retry/repass 경로 복원, 장중 threshold/env mutation, stale/broker/order/quantity/cooldown/price guard 완화, provider/bot/cap 변경, 과거 mark/last-trade-only 행의 executable BBO 대체를 허용하지 않는다.
  - 다음 액션: `rolling_venue_backfill_pass`, `source_pipeline_missing`, `source_quality_blocked`, `bounded_replay_resource_deferred` 중 하나로 닫고, pass여도 다음 scanner loop의 normal feature-envelope 검토 근거로만 사용한다.

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
