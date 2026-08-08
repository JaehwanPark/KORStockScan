# 2026-08-10 Stage2 To-Do Checklist

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

## 사용자 지시 구현 기록

- [x] `[WidgetSignalAutoTradeDailyLedger0810] 위젯 대상 3종목 당일원장 실주문 실행기 구현` (`Due: 2026-08-10`, `Slot: PREOPEN`, `TimeWindow: 08:50~09:00`, `Track: RuntimeStability`)
  - Source: [engine.py](/home/ubuntu/KORStockScan/src/trading/widget_auto_trade/engine.py), [gateway.py](/home/ubuntu/KORStockScan/src/trading/widget_auto_trade/gateway.py), [운영 계약](/home/ubuntu/KORStockScan/docs/widget-signal-auto-trading-runbook.md)
  - 판정: 3개 위젯 producer는 관측 권한을 유지하고 별도 실행 owner가 `ENTRY_CAUTION|ENTRY_READY` 새 에피소드 매수와 final EXIT 당일 체결수량 청산만 수행한다. 전일 미청산 수량은 이력으로만 남기고 다음 거래일 원장에서 제외한다.
  - 적용 상태: source와 systemd unit 설치·enable 완료, 현재 서비스는 미기동(`runtime_effect=false`)이며 `korstockscan-widget-signal-auto-trader-activate-20260810.timer`가 2026-08-10 07:58 KST에 최초 기동한다. 07:55 메인 봇 기동 후 shared token, collector freshness, manual_operator ownership, 단일 instance를 확인한다.
  - Rollback: 서비스 stop/disable. 장중 state 파일 삭제와 전일·수동·타 전략 수량 매도는 금지한다.

- [ ] `[WidgetSignalAutoTradeActivationVerify0810] 위젯 실주문 실행기 예약 기동 및 주문권한 검증` (`Due: 2026-08-10`, `Slot: PREOPEN`, `TimeWindow: 07:58~08:15`, `Track: RuntimeStability`)
  - Source: [systemd unit](/home/ubuntu/KORStockScan/deploy/systemd/korstockscan-widget-signal-auto-trader.service), [운영 계약](/home/ubuntu/KORStockScan/docs/widget-signal-auto-trading-runbook.md), [실행 상태](/home/ubuntu/KORStockScan/data/runtime/widget_signal_auto_trade_state.json)
  - 판정 기준: timer가 07:58 KST에 service를 1개 PID로 기동하고, 당일 shared cached token과 3개 collector fresh snapshot을 사용하며, `entry_qty=1`, `cash_precheck_performed=false`, `actual_order_submitted=false`가 최초 유효 신호 전까지 유지되는지 확인한다.
  - 금지: token 신규 발급·갱신, 메인 봇 재기동, state 파일 삭제, 전일·수동·타 전략 수량 매도, 신호 없는 시험주문.
  - 다음 액션: `active_ready_no_signal`, `active_and_source_qualified_entry_consumed`, `blocked_missing_daily_token`, `blocked_stale_collector`, `blocked_manual_owner_gap`, `service_start_failed` 중 하나로 닫는다.

- [x] `[ScalpMicroReversionV0Implementation0808] 도박사 entry-odds 제거 및 micro-reversion V0 4개 범위 구현` (`Due: 2026-08-08`, `Slot: OFFLINE`, `TimeWindow: 15:30~18:00`, `Track: ScalpingLogic`)
  - Source: [micro_reversion package](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion), [구현안](/home/ubuntu/KORStockScan/docs/proposals/scalp-micro-reversion-v1-plan.md)
  - 판정: `entry_odds` source/test는 제거했고 contracts, deterministic detector, 10-minute outcome labeler, replay/report를 source-only로 구현했다. 기존 engine/order/AI/ADM/LDM에는 연결하지 않았다.
  - 안전 계약: 수동관리 제외는 observation 등록 전 hard veto이며 `actual_order_submitted=false`, `broker_order_forbidden=true`, `runtime_effect=false`다.
  - 검증: targeted pytest, Ruff, Black, compile, parser, `git diff --check`를 review gate에서 닫는다.

- [x] `[ScalpMicroReversionV0ReplayReview0810] clean-baseline 15초~10분 V0 replay 및 coverage/EV 판정` (`Due: 2026-08-10`, `Slot: POSTCLOSE`, `TimeWindow: 20:05~20:30`, `Track: ScalpingLogic`)
  - Source: [V0 report JSON](/home/ubuntu/KORStockScan/data/report/scalp_micro_reversion_v0/scalp_micro_reversion_v0_2026-08-03_to_2026-08-07.json), [V0 report Markdown](/home/ubuntu/KORStockScan/data/report/scalp_micro_reversion_v0/scalp_micro_reversion_v0_2026-08-03_to_2026-08-07.md), [감리용 구현결과보고서](/home/ubuntu/KORStockScan/docs/audit-reports/2026-08-08-scalp-micro-reversion-v0-implementation-result.md)
  - 판정 기준: clean baseline과 수동관리 제외를 통과한 price/BBO/micro tier별 성숙 event, 3분·5분 비용 차감 EV, p90/p95 MAE, 날짜/종목 집중도, 결손 분모를 분리한다.
  - 금지: V0 결과를 실주문, BUY threshold, TP/stop, provider, bot, quantity/cap, broker guard 변경 근거로 사용하지 않는다.
  - 처리 결과: `document_status=superseded`, `superseded_by=scalp_micro_reversion_v0_report_v4`, `automation_consumption_allowed=false`. 기존 `v0_gross_edge_cost_sensitive_execution_unresolved`는 중간 판정이며 정식 상태는 `v0_aggregate_taxable_equity_gate_failed_subcohort_execution_unresolved`다. 5거래일 `2,644,506` raw rows에서 수동관리 제외 `130,303` rows를 hard veto했고 event leak은 `0`이다. deduplicated observations `469,231`, shock events `2,399`; 최고 관측 60초 gross EV `+0.144501%`는 인샘플 설명값이며 selection authority가 없다.
  - 다음 액션 실행: 비용 시나리오 `0/5/10/15/20/23bps`와 15~180초 fixed horizon을 report에 추가하고 동일 5거래일 산출물을 재생성했다. `0bps`는 friction-free이며 slippage-only가 아니다. sim/runtime 승격은 열지 않았다.

- [x] `[ScalpMicroReversionTaxGateCommonCohortJournal0808] tax-aware gate·공통성숙표본·forward journal P0 구현` (`Due: 2026-08-08`, `Slot: OFFLINE`, `TimeWindow: 18:00~20:00`, `Track: ScalpingLogic`)
  - Source: [tax.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/tax.py), [execution_journal.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/execution_journal.py), [V4 report JSON](/home/ubuntu/KORStockScan/data/report/scalp_micro_reversion_v0/scalp_micro_reversion_v0_2026-08-03_to_2026-08-07.json), [감리보고서](/home/ubuntu/KORStockScan/docs/audit-reports/2026-08-08-scalp-micro-reversion-v0-implementation-result.md)
  - 판정: 일반 과세주권 20bps counterfactual에서 최고 fixed-horizon gross `14.450139bps`, margin `-5.549861bps`로 aggregate gate는 실패했다. event tax class는 `0/2,399`로 exact gate가 차단됐으며 subcohort discovery는 유지한다. through-60s 동일표본에서는 30초 gross `15.188879bps`가 60초 `14.689606bps`보다 높아 60초 선택권한을 제거했다.
  - 구현: canonical report-only authority, 날짜/상품별 tax contract, explicit symbol metadata 입력, incremental common-maturity report, 주문권한 없는 append-only BBO/order/fill/cancel execution journal을 추가했다.
  - 안전 계약: 수동관리 제외는 replay/journal 전 hard veto, numeric market code 추정 금지, touch를 fill로 승격 금지, broker/order/AI/lifecycle consumer 연결 금지, `runtime_effect=false`를 유지한다.
  - 검증: targeted pytest `29 passed`, Ruff/Black/compileall, 5거래일 V3 replay, 금지 import scan, parser, `git diff --check`를 review gate에서 닫는다.

- [x] `[ScalpMicroReversionAuditRemediation0808] 감리 P0.4/P0.5 및 조건부 source-only 계약 보완` (`Due: 2026-08-08`, `Slot: OFFLINE`, `TimeWindow: 20:00~22:00`, `Track: ScalpingLogic`)
  - Source: [micro_reversion package](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion), [구현안](/home/ubuntu/KORStockScan/docs/proposals/scalp-micro-reversion-v1-plan.md), [감리보고서](/home/ubuntu/KORStockScan/docs/audit-reports/2026-08-08-scalp-micro-reversion-v0-implementation-result.md)
  - 구현: V4/report 재현성 sidecar, verified symbol master, OBSERVE/ECONOMIC gate 분리, CORE/DISCOVERY registry, multi-horizon parent-wave detector, non-blocking path journal, execution provenance V2, confirmation clustered LCB/tail/concentration/FDR 계약을 source-only로 추가했다.
  - 판정: path producer·order producer에는 연결하지 않았고 P2 entry×exit joint replay와 P3 sim assumed-fill은 `blocked_no_forward_continuous_path`로 남겼다. `actual_order_submitted=false`, `broker_order_forbidden=true`, `runtime_effect=false`다.
  - 후속 상태: 위 판정은 당시 completed evidence다. `ScalpMicroReversionObserverP2Skeleton0808`에서 P2 계약·synthetic/golden engine까지만 구현됐고, 실제 path discovery·selection·sim/runtime은 계속 blocked다.
  - 검증: targeted pytest, Ruff, Black, compileall, 금지 import scan, 5거래일 V4 재생성, parser, `git diff --check`를 review gate에서 닫는다.

- [x] `[ScalpMicroReversionObserverP2Skeleton0808] 감리 권고 observer/P2 source-only change set 구현` (`Due: 2026-08-08`, `Slot: OFFLINE`, `TimeWindow: 22:00~23:30`, `Track: ScalpingLogic`)
  - Source: [observation_adapter.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/observation_adapter.py), [path_capture.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/path_capture.py), [p2_replay.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/p2_replay.py), [감리보고서](/home/ubuntu/KORStockScan/docs/audit-reports/2026-08-08-scalp-micro-reversion-v0-implementation-result.md)
  - 구현: fail-isolated minimal `ObservationSink`, 기본 OFF 3개 flag, 30초 pre-event ring, parent-wave 단일 segment/reference, pre/active/post coverage, disk/partition/self-disable·runtime metric 계약, exchange/local/sequence watermark와 upper/lower fill bound를 가진 P2 synthetic/golden engine을 추가했다.
  - 판정: producer hook과 신규 구독은 추가하지 않았다. source-only integration commit과 manifest는 후속 항목에서 닫았지만 verified symbol master와 감리 재승인은 대기 중이므로 `observer_producer_connected=false`, `p2_real_data_discovery_run=false`, `selection_authority=false`, `trading_decision_effect=false`, `actual_order_submitted=false`다.
  - 검증: targeted pytest `69 passed`, Ruff/Black/compileall, thin adapter import graph·금지 dependency scan, parser(`count=30`), `git diff --check`를 review gate에서 통과했다. writer full-queue shutdown은 queue marker 비의존 stop-event 회귀테스트를 추가했다.

- [x] `[ScalpMicroReversionCleanIntegrationManifest0808] source-only clean integration commit 및 감리 manifest 생성` (`Due: 2026-08-08`, `Slot: OFFLINE`, `TimeWindow: 23:30~23:50`, `Track: ScalpingLogic`)
  - Source: [integration manifest](/home/ubuntu/KORStockScan/docs/audit-reports/2026-08-08-scalp-micro-reversion-source-only-integration-manifest.json), [감리보고서](/home/ubuntu/KORStockScan/docs/audit-reports/2026-08-08-scalp-micro-reversion-v0-implementation-result.md)
  - 판정: integration commit `e7051399`와 tree/archive/source 18개/test 14개/config hash를 고정했다. `entry_odds` 부재와 observer/runtime/order 권한 false를 증적화했으며 이것은 producer 연결 승인이 아니다.
  - 다음 owner: verified symbol master 원천 artifact와 conflict/coverage report를 만든 뒤 감리 재승인을 받는다.

- [ ] `[ScalpMicroReversionForwardCollector0810] verified symbol 원천 적재 및 non-blocking forward path collector 연결` (`Due: 2026-08-10`, `Slot: POSTCLOSE`, `TimeWindow: 20:30~21:00`, `Track: ScalpingLogic`)
  - Source: [symbol_master.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/symbol_master.py), [observation_adapter.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/observation_adapter.py), [path_journal.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/path_journal.py), [구현안](/home/ubuntu/KORStockScan/docs/proposals/scalp-micro-reversion-v1-plan.md)
  - 판정 기준: clean integration commit과 source/test/deployment manifest를 먼저 만들고 공식·검증 원천의 effective-date/conflict symbol metadata를 적재한 뒤 감리 재검토를 받는다. 재승인 후 기존 구독 범위 안에서 수동관리 hard veto 뒤 immutable envelope만 bounded queue에 넣는다. post-session compression/retention dry-run, process restart/last-sequence recovery, producer latency 악화 없음, 정상장 drop 0, 5거래일·성숙 event 200건·필수 path field coverage 90%·gap/restart/recovery는 collector 건강성만 판정한다.
  - 금지: dirty tree producer 연결, 신규 종목/호가/NXT·KRX 구독 확대, 임의 tax class 추정, 동기 JSON/fsync/detector/replay hot-path 연결, 실제 P2 data ranking 선행, sim/live·threshold·provider·bot·quantity/cap 변경.
  - 현재 상태: `clean_baseline_created_audit_review_pending`; verified symbol master 원천과 감리 재승인 전 producer hook은 금지한다.
  - 다음 액션: `audit_review_pending`, `collector_health_pass_research_data_only`, `symbol_master_conflict_blocked`, `path_coverage_insufficient`, `journal_degraded`, `manual_control_leak_blocked` 중 하나로 닫는다.

- [ ] `[ScalpMicroReversionP2DiscoveryAfterGateB0810] Gate B 이후 P2 actual-path discovery와 frozen confirmation 준비` (`Due: 2026-08-10`, `Slot: POSTCLOSE`, `TimeWindow: 21:00~21:15`, `Track: ScalpingLogic`)
  - Source: [p2_replay.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/p2_replay.py), [research_gate.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/research_gate.py), [구현안](/home/ubuntu/KORStockScan/docs/proposals/scalp-micro-reversion-v1-plan.md)
  - 판정 기준: `ScalpMicroReversionForwardCollector0810=collector_health_pass_research_data_only`인 경우에만 실제 path discovery를 실행한다. discovery에서 policy/cohort/cost를 고정하고 별도 confirmation window의 `net_ev_per_all_detected_signal` clustered LCB·tail·capital-time·집중도·FDR을 판정한다.
  - 금지: Gate B 전 실제 data run/ranking, touch=fill 단일 headline, discovery 최고 EV 자동선택, confirmation 전 selection authority, sim/runtime/order 연결.
  - 다음 액션: `blocked_gate_b_not_closed`, `discovery_source_quality_blocked`, `discovery_frozen_confirmation_pending`, `confirmation_failed`, `confirmation_passed_sim_audit_required` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-08-07` postclose -> `2026-08-10`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0810] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-08-10`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-07.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-07.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0810] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-08-10`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-08-07.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-08-07.json), [code_improvement_workorder_2026-08-07.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-07.json), [threshold_apply_2026-08-10.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-08-10.json), [threshold_runtime_env_2026-08-10.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-08-10.json), [threshold_runtime_env_verify_2026-08-10.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-08-10.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`1`, forced_scout_with_post_sell_count=`0`, post_sell_join_coverage_pct=`0`, outcome_coverage_state=`no_closed_outcome`, profitable_forced_scout_count=`0`, loss_or_flat_forced_scout_count=`0`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0810] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-08-10`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-07.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-07.json)
  - 전일 postclose candidate_selected_families=entry_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, scalping_pyramid_quality_gate, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0810] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-08-10`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-08-07.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-07.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0810] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-08-10`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-08-10.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-10.jsonl), [threshold_events_2026-08-10.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-10.jsonl), [observation_source_quality_audit_2026-08-10.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-10.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-08-10 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[PostcloseSourceQualityGateReview0810] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-08-10`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-08-10.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-10.json), [threshold_cycle_ev_2026-08-10.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-10.json), [code_improvement_workorder_2026-08-10.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-10.json), [threshold_cycle_postclose_verification_2026-08-10.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-08-10.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0810] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-08-10`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-07.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-07.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0810] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-08-10`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-07.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-07.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0810] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-08-10`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-08-07.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-08-07.md), [code_improvement_workorder_2026-08-07.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-07.json)
  - 판정 기준: selected_order_count=51와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0810] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-08-10`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-08-07.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-07.json), [runtime_apply_gap_audit_2026-08-07.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-07.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`207`, rollup_required_count=`207`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'exclusion_dimension_candidate': 1, 'parent_conflict_child': 2, 'positive_source_only_keep_collecting': 204}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0810] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-08-10`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-08-07.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-08-07.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`15`, run_count=`15`, skip_count=`0`, source_missing_count=`4`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`-`, top_reasons=`upstream_drift_signal:10, upstream_artifact_newer:7, output_missing_or_unreadable:6, source_missing_or_unreadable:4`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->



## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
