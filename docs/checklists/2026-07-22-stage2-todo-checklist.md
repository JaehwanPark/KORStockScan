# 2026-07-22 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- 튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-04`, `clean_tuning_baseline_ts_kst=2026-06-04T14:29:09+09:00`이다. 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 보고 EV/rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다.
- Baseline 이후 raw source-quality contract 결손은 날짜 전체 차단이 아니라 결손 row/window를 `raw_row_exclusion`으로 제외하는 것이 기본이다. 전체 block은 preflight missing/invalid, row/window exclusion 실패, 또는 결손을 안정적으로 특정할 수 없는 high-volume no-contract 상황에만 사용한다.
- 장중과 장후에는 `observation_source_quality_audit --write` 또는 최신 artifact로 raw source-quality를 반복 확인한다. Hard contract gap은 결손 row/window 제외 또는 `source_quality_blocked` 없이는 튜닝 입력에 들어갈 수 없고, unknown-token warning은 hard block이 아니더라도 code-improvement workorder handoff 확인 대상이다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-07-21` postclose -> `2026-07-22`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[KrxEvNetProfitMonitor0840] KRX explicit cohort·08:00~08:40 KRX-like 프리마켓 격리 EV·순이익 모니터링` (`Due: 2026-07-22`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:40`, `Track: ScalpingLogic`)
  - Source: [pipeline_events_2026-07-22.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-22.jsonl), [threshold_runtime_env_2026-07-22.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-22.json), [threshold_runtime_env_verify_2026-07-22.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-22.json)
  - 판정 기준: 현재 PID의 env/provider/WS와 explicit `effective_venue=KRX` 표본을 tuning authority로 사용한다. 08:00~08:50 NXT 프리마켓은 사용자 운영 판단에 따라 오후 16:00 이후 NXT 애프터마켓 런타임과 묶지 않고 `PREMARKET_KRX_LIKE` 관찰 cohort로 격리한다. rising-missed funnel, Freshness Envelope, P1 `initial -> post_probe -> leg_reprice`, probe-first/residual, 중앙 allocator, scale-in, trailing/exit의 실제 provenance와 counterfactual EV를 분리 확인한다.
  - 금지: KRX tuning EV에 NXT 애프터마켓/OFF_SESSION/venue unknown 표본을 혼입하지 않고, KRX-like 프마켓 표본은 시장 전용 provenance·threshold authority가 닫히기 전에 공통/KRX/NXT 애프터마켓 threshold 변경 근거로 사용하지 않는다. counterfactual과 실현손익 합산, stale/conflict·broker/account/order/quantity/cooldown·가격 freshness·95% safe budget 완화, 별도 price owner/fixed-offset fallback, PID/provider/cap/실주문 권한 변경을 금지한다.
  - 완료 기록 (`2026-07-22 08:40 KST`): 판정=`implemented_not_runtime_reflected`, 보조 판정=`source_quality_gap|insufficient_sample_keep_observing`. PID=`14408`, runtime env verify=`pass`, selected family=`26`, provider=`main_openai=ON`, WS 0B/0D 수신을 확인했다. 현 PID의 08:00~08:40 표본은 기존 분류상 `OFF_SESSION/UNKNOWN`이어서 explicit KRX 표본은 `0`건이며, 이를 KRX EV 확정 근거로 사용하지 않았다. KRX-like 프마켓 관찰상 TP1은 `pass=8/block=9/defer=4`, 0B/0D fresh와 WS micro ready는 `20/21`, effective source는 `WS=17/REST orderbook=4`, REST budget defer는 `0`건이다. probe 실체결 `3`건의 residual 제출은 `0`건(계좌 capacity `2`, WEAK/UNKNOWN TTL `1`), 실현 수익률은 각각 `0.00%/+1.10%/+2.35%`로 equal-weight 평균 `+1.15%`이며 counterfactual과 합산하지 않았다. 이체 후 브로커 신선 조회의 `kt00001` 주문가능금액은 `1,078,208원`, 현금 전용 주문가능금액은 `11,983,424원`이다. terminal probe 보유수량을 DB 계획수량으로 재확장하던 매도 수량 결함과 프리마켓 provenance 결손을 보완했으나 현 PID에는 미반영이다. threshold/runtime env/provider/cap는 변경하지 않았고 재기동도 수행하지 않았다.
  - 다음 액션: 다음 허용된 우아한 재기동 후 `PREMARKET_KRX_LIKE` provenance와 terminal probe receipt 수량 권한을 신규 PID에서 확인한다. 고가 종목의 `MAX_POSITION_PCT=20%` 0주 차단은 계좌 이체로 해소되지 않은 별도 hard capacity guard이며 이 작업에서 완화하지 않는다.

- [x] `[Kt00001OrderableFloorRestart0722] kt00001 300만원 operator floor 적용·코드리뷰·우아한 재기동` (`Due: 2026-07-22`, `Slot: PREOPEN`, `TimeWindow: 08:43~09:00`, `Track: RuntimeStability`)
  - Source: [kiwoom_orders.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_orders.py), [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [test_kiwoom_orders.py](/home/ubuntu/KORStockScan/src/tests/test_kiwoom_orders.py), [test_sniper_scale_in.py](/home/ubuntu/KORStockScan/src/tests/test_sniper_scale_in.py)
  - 판정 기준: 사용자 승인에 따라 유효한 `kt00001` 원본 주문가능금액이 `3,000,000원` 미만이면 실주문 예산 권한을 `3,000,000원`으로 보정한다. 원본/적용값, 권한, rollback 값을 meta·log에 남기고, 스캘핑은 `kt00011` 현금 주문가능금액·수량 범위 안에서만 floor를 유지한다.
  - 금지: API transport/auth/schema 실패를 `3,000,000원`으로 바꾸지 않고 `0원` fail-closed를 유지한다. broker 최종 거절, 현금 수량, `MAX_POSITION_PCT`, 주문/수량/cooldown, stale/price freshness, hard/protect/emergency guard는 우회하지 않는다.
  - 다음 액션: `korstockscan-review-gate` 무결점, targeted pytest·Black·compile·parser·diff check 통과 후만 `./restart.sh`로 우아하게 재기동한다. 신규 PID에서 runtime env/provider/WS와 `raw=1,078,208 -> effective=3,000,000`, floor authority·cash cap provenance를 확인한다. rollback은 `KORSTOCKSCAN_KT00001_ORDERABLE_AMOUNT_MIN_FLOOR_KRW=0` 적용 후 우아한 재기동이다.
  - 완료 기록 (`2026-07-22 08:53 KST`): 판정=`implemented_reviewed_runtime_reflected`. 1차 리뷰에서 kt00001 floor가 `kt00011.deposit`으로 다시 낮아지는 consumer 결함을 발견해, floor 적용 시 `kt00011` 현금 주문가능금액·수량을 상한으로 두고 `3,000,000원` budget base를 유지하도록 보완했다. 재리뷰 미해결 finding=`0`, 관련 통합 pytest=`1003 passed, 1 skipped`, Black/compile/checklist parser/`git diff --check`=`pass`이다. 브로커 read-only smoke는 `raw_amount=1,078,208`, `effective_amount=3,000,000`, `budget_source=kt00001_operator_floor_bounded_by_kt00011_cash`, `cash_orderable_amount=11,983,424`, `cash_orderable_qty_cap=699`를 확인했다. `./restart.sh`는 old PID=`14408`을 종료하고 new PID=`45017`을 기동했으며 runtime env handoff=`pass`, selected family=`26`, missing/mismatch=`0`, provider=`main_openai=ON`, WS login·첫 0D 실수신=`pass`이다. 08:00~08:50은 신규 PID에서 `PREMARKET_KRX_LIKE`로 격리되고 NXT 애프터마켓 런타임으로 분류되지 않는다.

- [x] `[KrxEvNetProfitMonitor1000] explicit KRX EV·순이익 극대화 장중 모니터링·보완` (`Due: 2026-07-22`, `Slot: INTRADAY`, `TimeWindow: 08:54~10:00`, `Track: ScalpingLogic`)
  - Source: [pipeline_events_2026-07-22.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-22.jsonl), [bot_history.log](/home/ubuntu/KORStockScan/logs/bot_history.log), [threshold_runtime_env_2026-07-22.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-22.json), [threshold_runtime_env_verify_2026-07-22.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-22.json), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [test_sniper_scale_in.py](/home/ubuntu/KORStockScan/src/tests/test_sniper_scale_in.py)
  - 판정 기준: current PID/source/runtime env/provider/WS를 기준으로 explicit `effective_venue=KRX`만 분리해 Rising Missed/Freshness Envelope, complete submit funnel, P1 `initial -> post_probe -> leg_reprice`, probe/residual, `entry_type_5stage_cap25_v1`, holding/scale-in/trailing·exit와 counterfactual MFE/MAE를 분리 확인한다.
  - 금지: NXT·`PREMARKET_KRX_LIKE`·OFF_SESSION·venue unknown 혼입, sim/probe/counterfactual과 실현 PnL 합산, stale/conflict·broker/account/order/quantity/cooldown·가격 freshness·`MAX_POSITION_PCT`·95% safe budget 완화, 별도 price owner/fixed-offset fallback, provider/PID/cap/실주문 권한 변경을 금지한다.
  - 다음 액션: 10:00 KST까지 최초·중복 blocker, 다음 loop 재평가, submit/fill, sizing/price/receipt, exit 후 추가 MFE를 집계한다. 유효 explicit KRX 반복 표본·단일 bounded threshold 직접 인과·same-stage 무충돌·rollback이 모두 닫히는 경우에만 단일 축을 적용·attribution하고, 그 외에는 무변경 관찰로 닫는다.
  - 완료 기록 (`2026-07-22 10:00 KST`): 판정=`implemented_not_runtime_reflected`, 보조 판정=`source_quality_gap|code_improvement_required`. PID=`45017`(start=`08:52:42`), runtime env verify=`pass`, selected family=`26`, provider=`main_openai=ON`, WS 0B/0D 실수신을 유지했다. explicit KRX 이벤트는 `461`건/`29`종목, TP1 evaluation id는 `90`개이며 submit-context allowed=`76`, candidate-block event=`43`이다. 주요 TP1 block은 AI state=`27`, positive support 부족=`10`, lane 부적합=`6`; submit-safety는 latency DANGER=`24`, weak micro=`13`, entry AI authority unavailable=`3`, observed-mark gap=`3`, tick-speed=`2`였다. Freshness는 `fresh_ws=188`, `rest_enriched=9`, effective price source는 unique TP1 기준 `WS=88/REST orderbook=5`, WS micro ready=`76`; final-envelope REST reserve는 `135`건 모두 allowed라 REST budget defer는 확인되지 않았다. signed-tape는 stale/missing 비중이 높아 source-quality 관찰 gap으로 남긴다.
  - 실체결/가격 판정: broker order는 로보스타·대명에너지 각 1주 probe `2`건이다. 두 건 모두 P1 post-probe가 `UNKNOWN/WEAK -> bounded recheck -> NEUTRAL/RECOVERED_WIDE`를 거친 뒤 leg 직전 direction defer로 residual을 전량 차단했다. 로보스타는 `70,600원` 1주 진입 후 `68,000원`, `-3.90%`로 종료했고 대명에너지는 10:00 시점 1주 보유 후 10:01:35에 `+0.24%`로 종료되어 10:00 실현 EV에는 합산하지 않았다. allocator는 300만원 base·tier1 10%를 사용했으나 event의 sizing venue가 `UNKNOWN`으로 남아 explicit KRX venue consumer gap을 기록한다.
  - bounded 보완: clean baseline 이후 `AI WAIT + latency DANGER + direct-canary applied`의 explicit KRX `COMPLETED + valid profit_rate` 9건은 승 `3`/패 `6`, equal-weight 평균 `-1.47%`, notional-weighted EV `-2.19%`, profit-rate 기준 추정 순손익 `-125,684원`이다. 이에 기존 `latency_true_ofi_direct_canary` owner 안에서 explicit KRX real SCALPING의 fresh live AI `WAIT`만 broker 제출 직전 차단하도록 구현했다. NXT/unknown venue, CAUTION, AI BUY, transport-timeout WAIT에는 적용하지 않으며 rollback은 `KORSTOCKSCAN_KRX_DIRECT_CANARY_LIVE_AI_WAIT_BLOCK_ENABLED=false` 후 허용된 우아한 재기동이다. review gate 최종 finding=`0`, target regression=`808 passed + 19 passed`, Black/compile/`git diff --check`=`pass`이다. 현재 PID에는 소스 변경이 반영되지 않았고 runtime/provider/PID/cap/threshold env는 변경하지 않았다.
  - 다음 액션: 별도 승인된 우아한 재기동 후 신규 PID에서 `krx_direct_canary_live_ai_wait_submit_block`, `broker_order_forbidden=true`, 실제 broker order 미호출 및 다음 scanner loop 재평가를 확인한다. sizing venue `UNKNOWN`과 signed-tape stale/missing은 source-quality/code-improvement 후속으로 유지하고, 새 veto의 rollback trigger는 동일 cohort의 post-apply target-first 기회 반복 또는 realized/counterfactual EV 악화다.

- [ ] `[ThresholdEnvAutoApplyPreopen0722] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-07-22`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-21.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-21.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 사전 준비 (`2026-07-21 22:39 KST`): `threshold_cycle_preopen_2026-07-22.status.json`은 `succeeded`, apply manifest는 `auto_bounded_live_ready`, handoff verifier는 `status=pass`다. 2026-07-21 대비 selected family 26개와 env key 317개의 누락은 없고 최신 entry/scale-in split 정책 및 dated override 21건이 모두 pass다. 이 항목은 다음 정상 기동 PID의 env가 확인되기 전까지 완료 처리하지 않는다.

- [ ] `[RisingMissedScoutRuntimePreopen0722] rising_missed_scout_workorder 구현분 다음 장전 runtime 반영 여부 확인` (`Due: 2026-07-22`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-07-21.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-07-21.json), [rising_missed_normal_buy_bridge_candidate_discovery_2026-07-21.json](/home/ubuntu/KORStockScan/data/report/rising_missed_normal_buy_bridge_candidate_discovery/rising_missed_normal_buy_bridge_candidate_discovery_2026-07-21.json), [code_improvement_workorder_2026-07-21.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-21.json), [threshold_apply_2026-07-22.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-07-22.json), [threshold_runtime_env_2026-07-22.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-22.json), [threshold_runtime_env_verify_2026-07-22.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-22.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`2`, forced_scout_with_post_sell_count=`3`, profitable_forced_scout_count=`0`, loss_or_flat_forced_scout_count=`3`, current_missed_count=`0`)과 `rising_missed_normal_buy_bridge_candidate_discovery` 요약(status=`source_missing`, bridge_candidate_count=`0`, code_improvement_order_count=`0`, runtime_env_key=`KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED`)을 함께 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder`/bridge discovery 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0722] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-07-22`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-21.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-21.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, entry_split_order_plan, scale_in_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0722] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-07-22`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-07-21.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-21.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0722] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-07-22`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-07-22.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-22.jsonl), [threshold_events_2026-07-22.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-07-22.jsonl), [observation_source_quality_audit_2026-07-22.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-22.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-07-22 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[PostcloseSourceQualityGateReview0722] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-07-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-07-22.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-22.json), [threshold_cycle_ev_2026-07-22.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-22.json), [code_improvement_workorder_2026-07-22.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-22.json), [threshold_cycle_postclose_verification_2026-07-22.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-07-22.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0722] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-07-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-21.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-21.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0722] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-07-22`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-21.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-21.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0722] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-07-22`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-07-21.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-07-21.md), [code_improvement_workorder_2026-07-21.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-21.json)
  - 판정 기준: selected_order_count=168과 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0722] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-07-22`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-07-21.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-21.json), [runtime_apply_gap_audit_2026-07-21.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-21.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`133`, rollup_required_count=`133`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 132}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0722] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-07-22`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-07-21.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-07-21.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`16`, run_count=`16`, skip_count=`0`, source_missing_count=`7`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, scalp_sim_ai_deferred_review, pattern_lab_currentness_audit`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:15, source_missing_or_unreadable:7, upstream_drift_signal:7, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
