# 2026-07-21 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-07-20` postclose -> `2026-07-21`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0721] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-07-21`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-20.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-20.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0721] rising_missed_scout_workorder 구현분 다음 장전 runtime 반영 여부 확인` (`Due: 2026-07-21`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-07-20.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-07-20.json), [rising_missed_normal_buy_bridge_candidate_discovery_2026-07-20.json](/home/ubuntu/KORStockScan/data/report/rising_missed_normal_buy_bridge_candidate_discovery/rising_missed_normal_buy_bridge_candidate_discovery_2026-07-20.json), [code_improvement_workorder_2026-07-20.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-20.json), [threshold_apply_2026-07-21.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-07-21.json), [threshold_runtime_env_2026-07-21.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-21.json), [threshold_runtime_env_verify_2026-07-21.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-21.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`5`, forced_scout_with_post_sell_count=`15`, profitable_forced_scout_count=`12`, loss_or_flat_forced_scout_count=`3`, current_missed_count=`0`)과 `rising_missed_normal_buy_bridge_candidate_discovery` 요약(status=`source_missing`, bridge_candidate_count=`0`, code_improvement_order_count=`0`, runtime_env_key=`KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED`)을 함께 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder`/bridge discovery 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

- [ ] `[NxtPostBlockSamplerReflection0722] NXT downstream-block sampler 다음 런타임 반영·귀속 확인` (`Due: 2026-07-22`, `Slot: PREOPEN`, `TimeWindow: 07:50~08:10`, `Track: ScalpingLogic`)
  - Source: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [rising_missed_intraday_feedback.py](/home/ubuntu/KORStockScan/src/engine/monitoring/rising_missed_intraday_feedback.py), [threshold_runtime_env_verify_2026-07-22.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-22.json)
  - 판정 기준: 다음 정상 기동 PID가 기존 NXT post-block sampler에서 TP1-pass 이후 `latency_block|real_weak_ai_micro_entry_block|rising_missed_tick_speed_entry_block|residual_blocked`를 source block stage로 등록하고, 원래 block event 뒤 source-only sampler event만 생성하며 submit retry·threshold/runtime authority를 만들지 않는지 확인한다.
  - 금지: 관측 확장을 이유로 bot 재기동, 공통/KRX threshold 변경, post-block direct retry 복원, broker/order guard 우회 또는 NXT 거래 전 source-quality evidence 없는 완화를 수행하지 않는다.
  - 다음 액션: 다음 정상 기동의 PID/env handoff와 최초 자연발생 downstream block provenance를 확인해 `runtime_reflected_source_only|implemented_not_reflected|rollback_required` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [x] `[EntrySplitProbeScopeExpansion0721] probe-first 최초진입 source 범위 보완 및 런타임 반영` (`Due: 2026-07-21`, `Slot: INTRADAY`, `TimeWindow: 10:50~11:10`, `Track: ScalpingLogic`)
  - Source: [entry_split_order_plan.py](/home/ubuntu/KORStockScan/src/engine/scalping/entry_split_order_plan.py), [test_entry_split_order_plan.py](/home/ubuntu/KORStockScan/src/tests/test_entry_split_order_plan.py), [threshold_runtime_env_verify_2026-07-21.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-21.json)
  - 판정 기준: 총수량 2주 이상인 real SCALPING 최초진입에서 일반 scanner, `OPENING_ROTATION`, rising-missed 최초 scout가 probe-first를 사용할 수 있고, 기존 보유·scout upgrade·추가매수·sim/dry-run·1주 요청은 제외되는지 확인한다.
  - 금지: 기존 보유 또는 scout upgrade를 최초진입으로 오인하거나 stale quote, broker/account/order/quantity/cooldown, hard/protect/emergency 안전장치를 우회하지 않는다. probe 실패를 market-first로 폴백하지 않는다.
  - 실행 결과 (`2026-07-21 11:06 KST`): 판정=`runtime_reflected_scope_guard_passed`. 실제 rising-missed 최초 scout producer가 공통 submit 전에 설정하는 `rising_missed_scout_upgrade_pending=true`를 future-upgrade marker로 분리하고, `forced initial + buy_qty=0 + 비보유`일 때만 probe-first를 허용했다. `buy_qty>0|HOLDING|SELL_ORDERED`, `rising_missed_scout_upgrade_order_pending`, `pending_add_order`, sim/dry-run은 `non_initial_entry_excluded|simulated_entry_excluded`로 유지했다. 집중 `28 passed`, 주문/체결/scale-in/runtime wrapper 관련 회귀 `1002 passed`, Black/compile/`git diff --check` 및 review gate 미해결 finding `0`을 확인한 뒤 PID `18360 -> 119610`으로 우아한 재기동했다. verifier는 `status=pass`, `pid_passed=true`, missing/mismatch/finding=`0/0/0`; probe-first active date=`2026-07-21`, market-first=`false`, 계좌 동기화·WS 로그인·첫 실시간 수신이 정상이다. 재기동 시점까지 당일 probe bundle 자연 발생은 없어 runtime state 파일은 아직 생성되지 않았다.

- [x] `[DynamicEntryPricePostProbeP10721] P1 post-probe 방향 재검증·leg별 reprice 구현 및 런타임 반영` (`Due: 2026-07-21`, `Slot: INTRADAY`, `TimeWindow: 15:50~16:20`, `Track: ScalpingLogic`)
  - Source: [sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [entry_split_order_plan.py](/home/ubuntu/KORStockScan/src/engine/scalping/entry_split_order_plan.py), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py)
  - 판정 기준: 기존 P1이 `initial|post_probe|leg_reprice` 단일 가격 권한을 유지하고, real SCALPING probe-first 공통 경로에서 `STRONG=narrow`, `NEUTRAL=normal`, `WEAK|UNKNOWN=250ms bounded recheck`, `recovered=wide`, `TTL expiry=1주 유지`, `HARD_NEGATIVE=residual abort`가 적용되는지 확인한다. rising-missed는 별도 가격 owner를 만들지 않는다.
  - 금지: P1 손상 시 legacy fixed-offset fallback, stale/conflict·stop/exit·broker/account/order/quantity/cooldown guard 우회, 신규 AI/provider 호출, 요청수량 확대, scale-in·avg-down·pyramid 경로 혼입을 금지한다.
  - 다음 액션: Black/compile/targeted pytest/parser/`git diff --check`와 review gate 무결점 확인 후 operator env와 PID handoff, WS 첫 수신, `main_openai=ON`, defer/recover/abort provenance를 확인하고 `runtime_reflected_guard_passed|rollback_required|implemented_not_restarted` 중 하나로 닫는다.
  - 실행 결과 (`2026-07-21 16:07 KST`): 판정=`runtime_reflected_guard_passed`. 별도 resolver를 추가하지 않고 기존 P1에 `initial|post_probe|leg_reprice` 계약을 확장했다. probe receipt 이후 fresh BBO와 700ms 이내 live orderbook observer 또는 3초 이내 feature를 사용해 `STRONG|NEUTRAL|WEAK|UNKNOWN`을 분류하고, hard guard는 `HARD_NEGATIVE`로 기록한다. `WEAK|UNKNOWN`은 lock 밖에서 250ms bounded recheck, 회복 시 `-0.3%/-0.8%`, 미회복 시 1주 유지이며 각 residual leg의 fresh quote·direction·P1 가격을 다시 확인한다. receipt/holding 동시 claim은 공통 `ENTRY_LOCK`으로 직렬화했고 restart 중 pending recheck는 circuit을 열지 않고 1주 abort로 닫는다. P1/allocator/probe/receipt/runtime verifier 집중 `340 passed`, scale-in/revive/holding/관련 producer-consumer 회귀 `889 passed`, Black/compile/parser/`git diff --check` 및 review gate 미해결 finding=`0`이다. PID `294756 -> 319781` 우아한 재기동 후 verifier `passed=true`, `pid_passed=true`, missing/mismatch/finding=`0/0/0`; 새 PID env의 post-probe P1/probe-first=`true/true`, 계좌 동기화, WS 로그인과 0B/0D 첫 수신, `main_openai=ON`, 안정화 구간 신규 ERROR=`0`을 확인했다. 자연 발생 probe가 아직 없어 defer/recover/abort 실표본은 향후 같은 family provenance에서 관찰한다.
  - 재리뷰 보완 (`2026-07-21 16:16 KST`): 판정=`supplemented_not_restarted`. 후속 review gate에서 residual 첫 leg broker 접수 직후 중복 log field `TypeError`, stale/untrusted WS micro가 fresh observer를 덮을 수 있는 source-priority gap, 공용 receipt `ENTRY_LOCK`을 account/broker 네트워크 호출 동안 점유하는 latency gap을 재현했다. log field는 merge contract로 정규화하고, post-probe 방향 입력은 future/stale micro를 제외하며 fresh live observer와 명시적 fresh tick field를 분리했다. receipt/holding 동시 claim은 전용 `_ENTRY_SPLIT_PROBE_RESIDUAL_LOCK`으로 직렬화해 공용 receipt lock을 네트워크 호출 중 점유하지 않도록 보완했다. 최종 관련 producer/consumer 회귀 `1214 passed`, Black/compile/parser/`git diff --check`를 통과했다. 사용자 지시에 따라 추가 재기동은 실행하지 않았으므로 PID `319781`은 이 보완 전 source를 실행 중이며, 보완분의 runtime reflection은 다음 명시적 재기동 허용 전까지 pending이다.
  - 재기동 반영 (`2026-07-21 16:20 KST`): 사용자 명시 지시에 따라 review gate를 다시 확인하고 `./restart.sh`의 `restart.flag` handoff로 PID `319781 -> 327657` 우아한 재기동을 완료했다. runtime env verifier는 `passed=true`, `pid_passed=true`, missing/mismatch/finding=`0/0/0`; post-probe P1/probe-first=`true/true`, active date=`2026-07-21`을 확인했다. 새 PID에서 계좌-DB 동기화, WS 연결·로그인, 주문체결통보(00) 등록, 0B/0D 첫 실시간 수신, `main_openai=ON`을 확인했으며 시작 구간 신규 `ERROR|Traceback|Exception`은 없었다. 판정=`runtime_reflected_guard_passed`.

- [x] `[NxtRisingMissedRuntimeMonitor0721] NXT 거래 window rising-missed·freshness·submit·multi-leg·exit 관측 및 NXT 전용 보완 판정` (`Due: 2026-07-21`, `Slot: INTRADAY`, `TimeWindow: 16:00~19:20`, `Track: ScalpingLogic`)
  - Source: [pipeline_events_2026-07-21.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-21.jsonl), [threshold_events_2026-07-21.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-07-21.jsonl), [intraday_ws_freshness_monitor_2026-07-21.json](/home/ubuntu/KORStockScan/data/report/intraday_ws_freshness_monitor/intraday_ws_freshness_monitor_2026-07-21.json), [rising_missed_intraday_feedback_2026-07-21.json](/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-21.json)
  - 판정 기준: `nxt_entry_window`와 effective venue `NXT` 표본만 분리해 TP1 pass/block/defer, WS micro 결측·노후화, REST budget defer, rising-missed 미제출, counterfactual MFE/MAE, submit-safety·broker, probe-first 이후 P1 multi-leg reprice, shallow avg-down, latency dynamic band, reversal guard/watch, trailing 조기청산을 `decision -> evidence -> next action`으로 닫는다. 정상 threshold 병목 완화는 차단 뒤 명백한 상승과 반복되는 NXT 전용 인과·rollback guard가 확인될 때만 허용한다.
  - 금지: KRX·NXT 표본 혼합, 공통/KRX 로직·threshold·runtime 변경, stale submit·broker/account/order/quantity/cooldown 및 hard/protect/emergency guard 우회, 단일 표본 또는 단순 미체결만으로 완화하는 것을 금지한다. NXT 고유 특성은 기존 NXT 전용 family 또는 별도 NXT runtime capability로만 분기한다.
  - 다음 액션: 19:20 KST까지 PID/provider/WS와 NXT event provenance를 관찰하고 `nxt_runtime_healthy_no_change|nxt_specific_observation_gap|nxt_specific_bounded_change_applied_attributed|nxt_runtime_capability_required|common_runtime_contamination_detected|insufficient_nxt_sample_keep_observing` 중 하나로 닫는다.
  - 실행 결과 (`2026-07-21 19:20 KST`): 판정=`nxt_specific_observation_gap`. `nxt_entry_window + effective venue=NXT`만 분리한 표본은 31 evaluation/17종목으로 TP1 pass/block/defer=`20/9/2`, downstream latency/weak-micro/tick-speed block=`10/4/5`, 실제 broker 경로는 케이프 1주 probe 1건뿐이었다. selector/defer sampler는 cutoff 기준 등록/완료=`11/10`, 완료 10건은 `adverse_stop_first=4`, `no_hit_within_20m=6`, `gross_target_first=0`; 완료 표본 최대 MFE=`+0.690%`, 최저 MAE=`-2.429%`로 threshold 완화 근거가 없었다. 438개 price sample은 WS/REST 적용/spread 거절/budget defer/timeout=`198/211/17/10/2`였고 budget defer는 observation-only rate limiter에만 국한됐다. 케이프는 1주 market probe 체결 뒤 P1 post-probe가 stale/conflict를 `HARD_NEGATIVE`로 판정해 residual 42주를 미제출했고, 이후 holding 손익은 최저 `-3.04%`; avg-down은 stale/unusable micro와 `deep_recovery_pnl_out_of_range`로 차단됐으며 60초 soft-stop grace 뒤 회복해 추가 노출과 조기청산을 모두 피했다. `reversal_up_volatile_watch` 1건은 recheck-only로 broker 제출 0건, reversal-down/general reversal-up/trailing/exit 자연 표본은 없었다. PID `327657`, runtime verifier `pass`, WS 0B/0D integrated route, `main_openai=ON`, process/resource detector pass를 확인했고 공통/KRX threshold·runtime env, provider, bot process는 변경하지 않았다. TP1-pass 이후 latency/weak-micro/tick-speed/residual block에는 기존 sampler가 등록되지 않는 관측 공백을 기존 NXT source-only sampler 내부에서 보완했으며 Black/compile/관련 `921 passed`/`git diff --check`와 review gate finding `0`을 통과했다. NXT 창 보호를 위해 source 보완은 PID `327657`에 재기동 반영하지 않았다.
  - 재리뷰 보완 (`2026-07-21 19:42 KST`): downstream sampler가 60초를 넘긴 TP1-pass 문맥과 후속 block을 결합하지 않도록 freshness를 강제하고, counterfactual 기준가는 과거 TP1 가격보다 block 시점 canonical/executable/current 가격을 우선하도록 수정했다. 보고서 집계는 `nxt_entry_window + effective venue=NXT` exact cohort만 허용하며, partial residual block의 실제 선행 제출수량·leg 수를 source-block provenance로 분리 보존한다. source-only sampler 자체의 `actual_order_submitted=false` 권한과 submit retry 금지는 유지한다. 관련 producer/consumer `1015 passed`, Black/compile/parser/`git diff --check`, review gate 미해결 finding=`0`을 확인했으며 bot 재기동·provider/runtime env·threshold·주문 권한 변경은 수행하지 않았다.

- [ ] `[RuntimeEnvIntradayObserve0721] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-07-21`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-20.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-20.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, scale_in_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0721] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-07-21`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-07-20.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-20.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0721] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-07-21`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-07-21.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-21.jsonl), [threshold_events_2026-07-21.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-07-21.jsonl), [observation_source_quality_audit_2026-07-21.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-21.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-07-21 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[PostcloseSourceQualityGateReview0721] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-07-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-07-21.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-21.json), [threshold_cycle_ev_2026-07-21.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-21.json), [code_improvement_workorder_2026-07-21.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-21.json), [threshold_cycle_postclose_verification_2026-07-21.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-07-21.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0721] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-07-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-20.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-20.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0721] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-07-21`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-20.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-20.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0721] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-07-21`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-07-20.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-07-20.md), [code_improvement_workorder_2026-07-20.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-20.json)
  - 판정 기준: selected_order_count=186와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0721] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-07-21`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-07-20.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-20.json), [runtime_apply_gap_audit_2026-07-20.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-20.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`176`, rollup_required_count=`176`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'exclusion_dimension_candidate': 1, 'parent_conflict_child': 2, 'positive_source_only_keep_collecting': 173}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0721] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-07-21`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-07-20.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-07-20.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`16`, run_count=`16`, skip_count=`0`, source_missing_count=`7`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, scalp_sim_ai_deferred_review, pattern_lab_currentness_audit`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:15, source_missing_or_unreadable:7, upstream_drift_signal:7, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-07-21 15:47:16`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-07-21.md`
- `Trade Review`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Performance Tuning`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Post Sell Feedback`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Entry Pipeline Flow`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
<!-- AUTO_SERVER_COMPARISON_END -->
