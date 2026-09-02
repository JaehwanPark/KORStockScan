# 2026-09-02 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-09-01` postclose -> `2026-09-02`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (07:45~09:00)

- [x] `[SamsungMorningProcessSequencingAcceptance0902] 삼성 오전 exact-date 기계의 main-bot 선행조건과 단일 기동 확인` (`Due: 2026-09-02`, `Slot: PREOPEN`, `TimeWindow: 07:45~08:05`, `Track: RuntimeStability`)
  - Source: [run_samsung_morning_one_share_preflight.sh](/home/ubuntu/KORStockScan/deploy/run_samsung_morning_one_share_preflight.sh), [korstockscan-samsung-one-share-preflight.service](/home/ubuntu/KORStockScan/deploy/systemd/korstockscan-samsung-one-share-preflight.service), [korstockscan-samsung-morning-one-share.timer](/home/ubuntu/KORStockScan/deploy/systemd/korstockscan-samsung-morning-one-share.timer), [threshold_runtime_env_verify_2026-09-02.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-09-02.json)
  - 전일 결함: `2026-09-01` 07:57 timer와 07:59 dependency가 preflight oneshot을 각각 시작했고 두 실행 모두 18회 `main_bot_inactive`로 소진돼 오전 process가 fail-closed했다. 주문·custody는 생성되지 않았고 midday/afternoon은 정상 preflight 후 `NO_TRADE`로 종료됐다. 보완본은 07:57 machine timer의 단일 transaction에서 preflight dependency를 정확히 한 번만 실행한다.
  - 당일 08:05 판정: timer/preflight는 한 번만 시작됐으나 main bot=`ubuntu:ubuntu`, preflight/live=`ubuntu:www-data` primary-group 불일치로 `/proc/<bot-pid>/environ`이 unreadable이었다. 검증기가 이를 모든 key의 `runtime_env_pid_missing`으로 오인해 preflight가 `activating`에 머물고 live service는 시작되지 않았다. exact-date authority와 삼성 owner 주문·custody는 생성되지 않았으며 08:05 Error Detector 7/7 PASS도 이 expected owner를 누락한 false-pass였다.
  - 보완 상태: repository unit의 preflight/live primary group을 `ubuntu`로 정합화하고, procfs 접근 실패를 `runtime_env_pid_unreadable` 단일 finding으로 분리하며, `process_health`가 07:57~08:04 bounded warning과 08:05 이후 exact-date authority/live terminal 결손 FAIL을 판정하도록 source·test·문서 보완을 review gate에서 검증한다. 재리뷰에서는 평일 휴장일 차단, 09:25 authority write race 차단, 당일 systemd start·authority v7/policy/rollback/bound PID 검증, timer enable/trigger와 installed credential 검증, main heartbeat와 삼성 finding 동시 보존을 추가했다. 설치 unit 반영·실서비스 재기동은 이 코드리뷰 범위 밖의 별도 운영 변경이다.
  - 08:34 운영 복구 판정: reviewed installer로 source/installed unit hash를 일치시키고 `daemon-reload` 후 preflight/live의 manager credential과 새 process 실제 credential을 모두 `ubuntu:ubuntu`로 확인했다. 기존 `ubuntu:www-data` preflight transaction을 terminal stop한 뒤 새 live transaction을 한 번만 요청했으며, preflight는 08:34:39~08:34:57 한 번 성공하고 live PID `36427`이 재시작 0·중복 PID 0으로 시작했다. exact-date policy `9ae877a75cd63240fb7caabb656fbb80898eab53073f7c79b3e46452289a1f14`, authority v7 `ready`, main bot PID `14307` runtime-env verify `pass`가 결속됐고 독립 Error Detector는 `healthy_active`를 판정했다. 08:36 기준 삼성 state는 09:00 SOR 창을 기다리는 `BUY_OPEN`이며 주문번호·체결·보유·owner custody는 모두 0이므로 운영 acceptance만 `sequencing_pass_machine_started_once`로 닫고 이후 주문 결과를 선반영하지 않는다.
  - 판정 기준: main bot의 당일 PID/env/runtime verify가 오전 preflight 전에 terminal pass이고, exact-date policy hash가 process에 결속되며, preflight와 machine이 각각 한 번만 실행되고 중복 PID·주문·owner custody 혼합이 0건인지 확인한다.
  - 금지: acceptance를 맞추기 위해 timer/service를 즉석 변경하거나 bot을 재기동하고, broker/order/quantity/threshold/provider/hard-safety 계약을 완화하지 않는다.
  - 다음 액션: `sequencing_pass_machine_started_once`, `no_trade_after_valid_start`, `main_bot_precondition_failed`, `duplicate_or_policy_hash_mismatch`, `not_yet_due` 중 하나로 닫는다.

- [x] `[SamsungMorningBoundedRecoveryOutcome0902] 삼성 오전 reviewed recovery의 SOR 주문·terminal·custody 확인` (`Due: 2026-09-02`, `Slot: OPEN`, `TimeWindow: 09:00~09:35`, `Track: RuntimeStability`)
  - Source: [samsung_morning_one_share_authority.json](/home/ubuntu/KORStockScan/data/runtime/samsung_morning_one_share_authority.json), [samsung_morning_one_share_state.json](/home/ubuntu/KORStockScan/data/runtime/samsung_morning_one_share_state.json), `journalctl -u korstockscan-samsung-morning-one-share.service --since '2026-09-02 08:34:57'`.
  - 확인: live PID `36427`의 단일성·재시작 여부, 09:00~09:30 SOR leg별 원주문번호·부분/전량체결·target·잔량, owner custody와 main/widget 주문 혼합 0건을 확인한다. `BUY_OPEN`을 미리 `NO_TRADE`나 성공 체결로 정규화하지 않는다.
  - 금지: 결과 확인을 위해 주문 취소·수량/가격/target 변경·서비스 재기동·owner custody 이동을 수행하지 않는다.
  - 다음 액션: `no_trade_after_valid_start`, `submitted_owner_isolated`, `held_owner_isolated`, `complete_owner_isolated`, `blocked_fail_closed`, `duplicate_or_owner_mismatch` 중 하나로 닫는다.
  - 10:00 완료 판정: `no_trade_after_valid_start`. live PID `36427`은 중복·재시작 없이 실행됐고 두 10주 SOR 원주문 `0009373`, `0009374`는 exact owner의 market-weakness guard가 잔량을 취소한 뒤 각각 `NO_FILL`, filled/remaining/position=`0/0/0`으로 닫혔다. 삼성 machine owner의 target·custody는 생성되지 않았고 main/widget 주문번호나 보유수량과 혼합된 증거가 없다.

- [x] `[ThresholdEnvAutoApplyPreopen0902] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-09-02`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-01.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 10:00 완료 판정: `applied_guard_passed_env`. 당일 runtime env verify는 selected family `25`, missing/mismatch `0`, status=`pass`였고 main PID `14307`의 자연 runtime event에서 LDM, entry opportunity recheck, cancel-wait attribution과 entry-price 계열 provenance를 확인했다. 수동 env override나 provider/bot/threshold 변경은 수행하지 않았다.

- [x] `[RisingMissedScoutRuntimePreopen0902] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-09-02`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-09-01.json), [code_improvement_workorder_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-01.json), [threshold_apply_2026-09-02.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-09-02.json), [threshold_runtime_env_2026-09-02.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-09-02.json), [threshold_runtime_env_verify_2026-09-02.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-09-02.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`3`, forced_scout_with_post_sell_count=`3`, post_sell_join_coverage_pct=`0.707547`, outcome_coverage_state=`partial`, profitable_forced_scout_count=`3`, loss_or_flat_forced_scout_count=`0`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.
  - 10:00 완료 판정: `runtime_env_reflected_and_verified`와 source-only 경제성 차단을 분리했다. runtime env의 `rising_missed_normal_buy_bridge`와 관련 관찰 provenance는 검증됐지만 09:35 feedback의 risky-micro rolling diagnostic EV는 `-0.014849%`, filled terminal `9/10`, promotion state=`blocked_sample_floor`이며 code-improvement order는 `0`이다. 이 표본으로 실주문·threshold 권한을 만들지 않았다.

## 장중 체크리스트 (09:05~15:20)

- [x] `[RuntimeEnvIntradayObserve0902] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-09-02`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-01.json)
  - 전일 postclose candidate_selected_families=entry_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime, post_probe_winner_recovery, scalping_pyramid_quality_gate, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.
  - 10:00 완료 판정: `provenance_present`, rollback guard breach `0`. main PID `14307`은 07:55 기동 이후 유지됐고 selected runtime provenance가 threshold/pipeline event에 나타났다. 09:17:05와 09:56:40 WebSocket transport reconnect는 아래 별도 OPEN 항목으로 분리하며 runtime family 적용 성공으로 포장하지 않는다.

- [x] `[MainSubmitDroughtCausalClosure0902] main KRX/NXT submit drought 최초 0-conversion 축 재확인` (`Due: 2026-09-02`, `Slot: INTRADAY`, `TimeWindow: 09:20~09:35`, `Track: ScalpingLogic`)
  - Source: [buy_funnel_sentinel_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-09-01.json), [conversion_lane_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/conversion_lane/conversion_lane_2026-09-01.json), [code_improvement_workorder_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-01.json)
  - 전일 상태: KRX와 NXT가 각각 `SUBMIT_DROUGHT_CRITICAL`이었고 broker submit failure는 없었다. entry-AI authority revalidation과 upstream AI threshold가 공통 최초 병목이며 KRX에는 latency·spread·stale 축이 추가됐다.
  - 판정 기준: venue/session별 AI-confirmed→budget→latency/price→submit unique funnel, exact blocker receipt, broker terminal receipt를 다시 결속하고 `order_conversion_lane_submit_drought_submit_drought_entry_ai_authority_revalidation` 및 `order_conversion_lane_submit_drought_submit_drought_upstream_gate`의 신규 자연 표본을 확인한다.
  - 금지: drought 해소를 위해 hard safety, stale/conflict, broker/account/order/quantity/cooldown, score/entry threshold, provider/bot/cap을 완화하지 않는다. 정상 hard-safety 차단은 `structural_by_design_safety_exclusion`으로 분리한다.
  - 다음 액션: `causal_stage_confirmed_collect`, `source_or_receipt_gap_workorder`, `structural_by_design_safety_exclusion`, `drought_resolved_with_terminal_receipts`, `no_natural_sample` 중 하나로 닫는다.
  - 10:00 완료 판정: `causal_stage_confirmed_collect`. KRX unique funnel은 AI-confirmed `19` → budget `25` → latency-pass `6` → submitted `1`, submitted/AI=`5.3%`, submitted/budget=`4.0%`로 `SUBMIT_DROUGHT_CRITICAL`이다. 최초 병목은 entry-AI authority revalidation, 알려진 spread/micro latency guard와 AI WAIT/DROP이며 broker submit failure는 `0`이다. follow-up은 `runtime_effect=false`, `operator_action_required=false`의 postclose LDM/workorder 자동 handoff로 유지했다.

- [x] `[SimProbeIntradayCoverage0902] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-09-02`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-01.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.
  - 10:00 완료 판정: source-only/sim과 real probe를 분리했다. risky-micro source-only candidate `1`은 `actual_order_submitted=false`, `broker_order_forbidden=true`를 유지했고 negative EV/sample-floor blocker로 승격되지 않았다. 별도 main real exploration probe 일동제약 주문 `0012795`는 1주 미체결 후 취소 `0013143`, filled/remaining=`0/0`으로 닫혀 sim 분모에 합산하지 않았다. 09:50 source-quality 재감사는 status=`pass`, events=`38803`, stages=`95`, hard gap/excluded/warning=`0/0/0`, `tuning_input_allowed=true`였다.

- [x] `[IntradayRuntimeMonitoring1130_0902] 11:30까지 main·widget·episode 런타임과 source-quality 재점검` (`Due: 2026-09-02`, `Slot: INTRADAY`, `TimeWindow: 10:00~11:30`, `Track: RuntimeStability`)
  - Source: [threshold_runtime_env_verify_2026-09-02.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-09-02.json), [observation_source_quality_audit_2026-09-02.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-02.json), [pipeline_events_2026-09-02.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-09-02.jsonl), [process_health.py](/home/ubuntu/KORStockScan/src/engine/error_detectors/process_health.py)
  - 판정: `RED_active_holding_exit_monitor_unowned_block`. main PID `85807`은 10:03:20 이후 생존했고 runtime-env verify는 selected=`25`, missing/mismatch=`0/0`, observer writer error/drop/out-of-order=`0/0/0`이었다. 11:29 latest callback census는 `303667/402931`, WebSocket error 누계는 `16`에서 추가 증가하지 않았다. 11:24 source-quality 재감사는 events=`79922`, stages=`153`, hard gap/excluded/warning=`0/0/0`, `tuning_input_allowed=true`였다.
  - owner 결과: widget 삼성전자 exact episode는 entry 10주 `253000`원, target 10주 `254500`원으로 COMPLETE이며 gross `+0.5929%`, 고정 23bps 근사 비용 차감 `+0.3629%`이고 prior-day unmanaged 10주는 별도 custody다. 삼성·한전·SD바이오센서·SK이터닉스·SK텔레콤·NHN episode owner는 당일 terminal `NO_TRADE`, 주문·보유·custody=`0`으로 main과 혼합되지 않았다.
  - main P0: 일동제약 `record_id=38741`, buy=`17450`, qty=`1`의 `late_loss_avg_down_retry`에서 현금가능수량 `8`과 별개로 종목 포지션 상한의 remaining whole-share cap이 `0`이어서 추가매수가 정상 차단됐다. 직후 자동 manual-control exclusion이 in-memory flag로 남아 11:02 이후 `manual_control_fast_exit_monitor_blocked`와 일반 holding handler를 반복 차단했고, 현재 명시적 operator owner나 terminal sell receipt가 없어 자동 보유·청산 감시가 비활성이다.
  - 보완/검증: 주문·수량·cap·stop·provider·bot 상태를 바꾸지 않고 `process_health`가 최신 holding receipt와 현재 explicit operator provenance를 대조해 이 상태를 FAIL로 검출하도록 계측했다. 관련 error-detector/manual-control/exit-safety/weakness-guard targeted test `143 passed`, 이전 guard/machine review `353 passed`, compile과 `git diff --check`를 통과했다. 새 코드는 현재 PID에 hot apply하지 않았다.

- [ ] `[MainHoldingManualControlAutoExclusionReconciliation0902] 일동제약 자동 manual-control handoff의 exact owner·custody·exit-monitor 복구 판정` (`Due: 2026-09-02`, `Slot: INTRADAY`, `TimeWindow: 11:30~12:00`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-09-02.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-09-02.jsonl), [manual_control_excluded_codes.txt](/home/ubuntu/KORStockScan/data/config/manual_control_excluded_codes.txt), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [process_health.py](/home/ubuntu/KORStockScan/src/engine/error_detectors/process_health.py)
  - 판정 기준: broker exact holding/terminal receipt와 `record_id=38741`을 대조하고, explicit operator owner가 없는데 file auto row 제거 뒤 in-memory `manual_control_auto_scale_in_qty_blocked`가 보유·fast-exit monitor를 계속 차단하는 상태를 해소하거나 명시적 manual owner handoff로 닫는다. source 보완은 soft-loss fallback과 hard/protect/emergency safety를 분리하고 review finding 0·targeted validation 후에만 다음 PID 반영 후보가 된다.
  - 금지: 현금 보유만으로 `MAX_POSITION_PCT`, 요청수량, broker/order/quantity guard, soft/hard stop을 완화하거나 exclusion을 무근거 삭제하고, bot 재기동·수동 매도·owner custody 이동을 수행하지 않는다.
  - 다음 액션: `explicit_manual_owner_acknowledged`, `terminal_receipt_reconciled`, `source_fix_reviewed_next_pid_only`, `blocked_user_authority` 중 하나로 닫는다.
  - 11:46 source 보완 판정: `source_fix_reviewed_next_pid_only`. `position_cap_or_budget`는 추가매수를 계속 차단하되 manual owner를 생성하지 않고 기존 loss-exit safety path로 fallthrough하도록 수정했다. exact `return_code=0|order_no` 없는 다른 block dict를 제출 성공으로 보지 않으며, 명시적 `manual_operator`·open-loss·hard-stop handoff는 유지한다. 과거 `auto_scale_in_qty_guard_block` 파일 행과 stale in-memory flag는 explicit owner가 없을 때만 다음 PID에서 폐기되고 health detector는 최신 retirement receipt를 해소 상태로 소비한다. 당시 가동 PID에는 hot apply·재기동·주문 변경을 수행하지 않았다.

- [ ] `[WebSocketProtocolReconnectPostcloseReview0902] 오전 반복 WebSocket protocol-close의 exact lineage와 영향 재검증` (`Due: 2026-09-02`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~20:30`, `Track: RuntimeStability`)
  - Source: [kiwoom_websocket_error.log](/home/ubuntu/KORStockScan/logs/kiwoom_websocket_error.log), [intraday_ws_freshness_monitor_2026-09-02.json](/home/ubuntu/KORStockScan/data/report/intraday_ws_freshness_monitor/intraday_ws_freshness_monitor_2026-09-02.json), [error_detection_2026-09-02.json](/home/ubuntu/KORStockScan/data/report/error_detection/error_detection_2026-09-02.json), [latest.json](/home/ubuntu/KORStockScan/data/runtime/scalp_micro_reversion_forward_collector/latest.json)
  - 오전 증거: 09:17:05 `1002 reserved bits must be 0` REG 9건/REMOVE 3건, 09:56:40 `1002 invalid opcode` REG 1건, 10:20 2건, 10:58 1건으로 WebSocket error 누계는 `16`이다. 각 run은 3초 안에 로그인·계좌통보/장상태·종목·조건검색 재등록과 새 sequence epoch의 0B/0D 실수신으로 복구됐고, 11:30 observer는 writer error/drop/out-of-order=`0/0/0`, `stop_required=false`였다. 수동 restart·runtime mutation은 없었다.
  - 판정 기준: 두 transport generation의 disconnect→login→REG/CNSRREQ→first 0B/0D와 main/widget/episode order receipt를 exact time으로 결속하고, 누락 구간·중복 등록·stale epoch 소비·owner custody 영향과 postclose source-quality/workorder handoff를 재검증한다.
  - 금지: 반복 error count만으로 bot을 재기동하거나 stale/conflict, broker/order/quantity, provider, threshold, hard safety를 완화하지 않는다. protocol/recovery 코드를 수정해야 하면 공식 Kiwoom reference gate와 review finding 0을 먼저 닫는다.
  - 다음 액션: `recovered_no_downstream_loss`, `source_rows_excluded_and_handoff`, `structural_reconnect_defect_workorder`, `runtime_or_owner_impact_blocked` 중 하나로 닫는다.

- [ ] `[IntradaySourceQualityGateCheck0902] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-09-02`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-09-02.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-09-02.jsonl), [threshold_events_2026-09-02.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-09-02.jsonl), [observation_source_quality_audit_2026-09-02.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-02.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-09-02 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (16:25~21:55)

- [ ] `[ThresholdDailyEVReport0902] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-09-02`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-09-01.json), [threshold_cycle_ev_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-01.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0902] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-09-02`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-01.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[MainAIQualitySourceGapMainAIQualityMaterializedCompanionBindingRepair0902] main AI materialized companion exact-hash 결속 복구 확인` (`Due: 2026-09-02`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:20`, `Track: ScalpingLogic`)
  - Source: [main_ai_quality_r0_r3_cycle_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-09-01.json)
  - 판정 기준: workorder `main-ai-gap-24c4a17af50fc97358f4bbfd`의 owner=`MainAIQualityMaterializedCompanionBindingRepair`, reason_codes=`execution_report_materialized_companion_binding_mismatch_count=1, execution_report_materialized_companion_binding_mismatch_dates=2026-08-24`를 source-only producer 보완으로 닫는다. reason_codes에 명시된 source date별 execution report와 materialized request/response companion의 exact hash를 재검증하고, 불변 원천에 결속할 수 없는 historical row는 합성 없이 제외한다.
  - 완료 조건: each affected execution report binds the exact materialized request and response companion hashes for its own source date; unchanged immutable historical rows remain excluded and no runtime or order authority changes
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[MainAIQualitySourceGapRuntimeExecutionReceiptCustodyRepair0902] RuntimeExecutionReceiptCustodyRepair main lifecycle source gap 복구 확인` (`Due: 2026-09-02`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:20`, `Track: ScalpingLogic`)
  - Source: [main_ai_quality_r0_r3_cycle_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-09-01.json)
  - 판정 기준: workorder `main-ai-gap-0d91bc921a0039b10af57f0c`의 owner=`RuntimeExecutionReceiptCustodyRepair`, reason_codes=`lifecycle_exact_join_missing_count=7, lifecycle_exact_join_missing_dates=2026-08-18`를 source-only producer 보완으로 닫는다. 공식 raw execution envelope의 order/execution identity를 합성 없이 검증하고 결손 lifecycle만 제외한 뒤 paired producer를 재검증한다.
  - 완료 조건: official raw execution envelope/order/execution identity is complete for each repair-required lifecycle or the affected row remains explicitly excluded; custody and order authority remain unchanged
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[CodeImprovementWorkorderReview0902] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-09-02`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-09-01.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-09-01.md), [code_improvement_workorder_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-01.json)
  - 판정 기준: selected_order_count=45와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[SourceOnlyFloorContractClosure0902] NXT paired replay와 holding smoothing 부족의 floor·유입률 계약 보완 확인` (`Due: 2026-09-02`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:30`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_cumulative_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_2026-09-01.json), [threshold_cycle_ev_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-01.json)
  - 전일 상태: NXT paired replay probe 표본은 9/10, `holding_flow_ofi_smoothing`은 daily floor 20 대비 유효 표본이 미달했으나 completed due-day, floor-qualified unique 유입·expiry, fixed lower-bound estimator가 없어 finite ETA를 입증하지 못했다.
  - 판정 기준: 각 exact floor denominator와 dedup key, completed due trading-day 0건 포함 일별 신규 floor-qualified unique, rolling expiry, minimum classification window와 conservative reachable N을 선언한다. 계약이 여전히 없으면 `blocked_missing_evidence`를 유지하고 시간 해결형으로 승격하지 않는다.
  - 금지: 양(+) 유입일만 선택하거나 owner/venue를 합치고, row 복제·HELD 완료처리·sample floor 하향·runtime/provider/threshold/order 변경으로 표본을 맞추지 않는다.
  - 다음 액션: `metric_contract_closed_reclassify`, `blocked_missing_evidence`, `time_resolvable_with_finite_eta`, `structural_population_exhaustion`, `N/A_by_contract` 중 하나로 닫는다.

- [ ] `[CrossOwnerCalculationSampleManifest0902] main·widget·episode·AI·micro 결정론적 층화 sample manifest와 독립 재계산 확인` (`Due: 2026-09-02`, `Slot: POSTCLOSE`, `TimeWindow: 21:20~21:40`, `Track: RuntimeStability`)
  - Source: [postclose-tuning-result-review-task-instructions.md](/home/ubuntu/KORStockScan/docs/postclose-tuning-result-review-task-instructions.md), [threshold_cycle_postclose_verification_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-09-01.json)
  - 전일 결손: producer별 보존식과 targeted golden/metamorphic tests는 통과했지만 owner·venue/session·fill/terminal·first-hit·source-quality 경계를 함께 고정한 별도 deterministic `sample_manifest`와 manifest hash가 남지 않아 repository 전 범위 “오류 없음” 판정을 유보했다.
  - 판정 기준: stable row-key hash로 owner, KRX/NXT, lifecycle stage/action, full/partial/unfilled, terminal/right-censored, target/adverse/same-hit/unresolved, source pass/excluded, session/window 경계를 층화하고 선택 규칙·모집단·선택 수·manifest hash를 기록한다. 선택 row를 raw→parser→join→label→cost→aggregation까지 독립 재계산하고 전체 count/key/notional/numerator/denominator/exclusion 보존식과 JSON/Markdown parity를 대조한다.
  - 금지: 결과에 맞춰 표본을 재선택하거나 미래 outcome을 R0 입력으로 역류시키고, owner/venue를 합치거나 결손·right-censored를 0/완료로 보간하지 않는다.
  - 다음 액션: `manifest_and_recalculation_pass`, `calculation_defect_workorder_required`, `source_quality_blocked`, `coverage_incomplete_keep_red` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0902] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-09-02`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-09-01.json), [runtime_apply_gap_audit_2026-09-01.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-09-01.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`328`, rollup_required_count=`328`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 327}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[MachineLifecycleTurnoverObjectiveFollowup0902] 위젯·episode 빠른 회전 목적의 미완료 후속 구현 확인` (`Due: 2026-09-02`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~21:40`, `Track: ScalpingLogic`)
  - Source: [machine_microstructure_policy_approval_postclose_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/machine_microstructure_policy_approval/machine_microstructure_policy_approval_postclose_2026-09-01.json), [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py)
  - 판정 기준: 승인 후보 수와 무관하게 `followup_required=true`인 미완료 목적 항목 `machine_lifecycle_turnover_policy_research_v1`(status=`EVIDENCE_ACCUMULATING`, next_action=`repair_excluded_source_report_contracts_and_rerun`)의 상태와 상태별 `next_action`을 확인하고 구현 또는 표본수집 경로로 닫는다.
  - 상태별 다음 액션: `IMPLEMENTATION_REQUIRED`는 source-only rolling paired policy 연구를 구현하고, `EVIDENCE_ACCUMULATING`은 exact-date floor 충족까지 수집·재검증한다. `CANDIDATE_QUEUE_HANDOFF|COMPLETE`는 closed 상태이므로 report에서 제외되고 다음 refresh에서 builder-owned 항목이 제거된다.
  - 권한 경계: 이 POSTCLOSE 후속 항목은 source-only 구현·검증 작업이며 runtime env, 실주문, target/timeout/cooldown/cap, threshold, provider/bot, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[MachineEntryExactJoinShortage0902] exact entry-anchor BBO·0B/0D join 구조 고갈 재판정` (`Due: 2026-09-02`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~21:45`, `Track: ScalpingLogic`)
  - Source: [machine_entry_timing_tuning_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/machine_entry_timing_tuning/machine_entry_timing_tuning_2026-09-01.json), [machine_microstructure_attribution_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/machine_microstructure_attribution/machine_microstructure_attribution_2026-09-01.json)
  - shortage owner: `machine_entry_timing:all_exact_scopes:entry_confirmation_delay`; 전일 target actual-entry anchor 11/11이 exact signal timestamp, executable BBO 및 canonical 0B/0D market-anchor 결손으로 source-quality blocked였고 `structural_population_exhaustion`으로 분류됐다.
  - 판정 기준: 신규 source-quality-valid unique anchor가 같은 exact owner·symbol·venue/session 경로에서 first depleted join stage를 통과하고, owner 분리·row 보존식·downstream source hash가 닫혔는지 확인한다. 단순 report 재생성이나 0초 baseline carry-forward는 해결로 세지 않는다.
  - 재분류 trigger: corrected generation에서도 신규 floor-qualified unique가 0이거나 producer-consumer gap이 남으면 구조형을 유지하고 최소 parser/key-lineage/instrumentation workorder와 acceptance를 갱신한다. 유입·expiry 계약과 finite reach가 새로 입증된 경우에만 시간 해결형으로 재분류한다.
  - 권한 경계: source-quality·instrumentation·report-only이며 entry delay, target, 수량, 실주문, provider/bot, broker guard 또는 hard safety 변경 권한이 없다.

- [ ] `[AutomationTriggerDecisionSummary0902] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-09-02`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-09-01.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`14`, run_count=`9`, skip_count=`0`, source_missing_count=`4`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:8, disabled_by_runtime_policy:5, upstream_drift_signal:5, source_missing_or_unreadable:4, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

- [ ] `[PostcloseSourceQualityGateReview0902] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-09-02`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-09-02.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-02.json), [threshold_cycle_ev_2026-09-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-02.json), [code_improvement_workorder_2026-09-02.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-02.json), [threshold_cycle_postclose_verification_2026-09-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-09-02.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## 당일 사용자 지시 구현 기록

- [x] `[ScannerLookupAttentionAutoPromotion0902] 조회수급증 기반 scanner same-tier 가중치 자동승격 폐루프 구현·리뷰` (`Due: 2026-09-02`, `Slot: INTRADAY`, `TimeWindow: user-directed`, `Track: ScalpingLogic`)
  - Source: [scanner_lookup_attention_tuning.py](/home/ubuntu/KORStockScan/src/engine/monitoring/scanner_lookup_attention_tuning.py), [scanner_lookup_attention_policy.py](/home/ubuntu/KORStockScan/src/engine/scalping/scanner_lookup_attention_policy.py), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 구현: exact scanner promotion/record/symbol을 같은 날짜·KRX regular·매수 방향의 `FULL_FILL` receipt 및 no-scale-in `COMPLETED` main SCANNER lifecycle과 결속한다. 모든 포함 outcome 날짜의 source-quality audit와 공식 보통주 master, `1.5/1.5/20 bps` 고정 비교비용을 검증한다. base `20/5`와 candidate/control `10/3` pass는 no-effect forward holdout만 arm하고, arm 날짜 이전 base를 고정한 독립 미래 holdout이 같은 EV·tail floor를 통과할 때만 다음 영업일 hash-valid policy가 exact `dt/tm` age 120초 이내 KRX regular snapshot에 한해 기존 tier 내부 점수에 `0..200` 가중치를 적용한다. PREMARKET/NXT, stale snapshot, tier/pool/slot, BUY/DROP, provider, 주문가격·수량·cap, broker/safety owner는 변경하지 않는다.
  - 폐루프: postclose wrapper가 exact trade-fact sync 뒤 report/policy 생성과 `--verify-only`를 실행하고 central verifier가 artifact/status/authority를 검사한다. 적용 뒤 exact policy provenance가 붙은 표본에서 candidate worst `<-5%`이면 floor 전 조기 rollback, mature `20/5`의 EV/uplift/tail 실패면 다음 영업일 zero-bonus policy로 rollback한다. missing/stale/hash/source-quality/evidence 결손과 non-live 상태도 runtime에서 zero bonus로 닫는다.
  - 당일 artifact 판정: valid observation=`107`, invalid observation/fill/policy provenance=`0/0/0`, full/partial=`0/0`, fill receipt missing=`107`, completed outcome=`0`, source quality/master=`pass/pass`, promotion=`hold_sample`, `allowed_runtime_apply=false`; report/policy hash와 policy-evidence hash 결속 및 `--verify-only`가 통과했다. 현재 PID 재기동·runtime mutation·주문 변경은 수행하지 않았다.

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
