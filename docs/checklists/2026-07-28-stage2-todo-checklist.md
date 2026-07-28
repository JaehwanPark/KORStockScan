# 2026-07-28 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime 변경은 사용자 명시 지시가 있을 때만 기존 `bounded_tunable` 단일 축에 한해 허용한다. fresh/conflict-free source, 유효 effective price, 단일 blocker 인과, same-stage owner 비충돌, before/after·PID/env provenance·rollback·즉시 attribution을 모두 남긴다. hard safety, stale/conflict, price freshness, broker/account/order/quantity/cooldown, provider, bot, cap, 요청수량은 변경하거나 우회하지 않는다.
- 튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-04`, `clean_tuning_baseline_ts_kst=2026-06-04T14:29:09+09:00`이다. 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 보고 EV/rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다.
- Baseline 이후 raw source-quality contract 결손은 날짜 전체 차단이 아니라 결손 row/window를 `raw_row_exclusion`으로 제외하는 것이 기본이다. 전체 block은 preflight missing/invalid, row/window exclusion 실패, 또는 결손을 안정적으로 특정할 수 없는 high-volume no-contract 상황에만 사용한다.
- 장중과 장후에는 `observation_source_quality_audit --write` 또는 최신 artifact로 raw source-quality를 반복 확인한다. Hard contract gap은 결손 row/window 제외 또는 `source_quality_blocked` 없이는 튜닝 입력에 들어갈 수 없고, unknown-token warning은 hard block이 아니더라도 code-improvement workorder handoff 확인 대상이다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-07-27` postclose -> `2026-07-28`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0728] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-07-28`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-27.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0728] rising_missed_scout_workorder 구현분 다음 장전 runtime 반영 여부 확인` (`Due: 2026-07-28`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-07-27.json), [rising_missed_normal_buy_bridge_candidate_discovery_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/rising_missed_normal_buy_bridge_candidate_discovery/rising_missed_normal_buy_bridge_candidate_discovery_2026-07-27.json), [code_improvement_workorder_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-27.json), [threshold_apply_2026-07-28.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-07-28.json), [threshold_runtime_env_2026-07-28.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-28.json), [threshold_runtime_env_verify_2026-07-28.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-28.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`3`, forced_scout_with_post_sell_count=`2`, profitable_forced_scout_count=`1`, loss_or_flat_forced_scout_count=`1`, current_missed_count=`0`)과 `rising_missed_normal_buy_bridge_candidate_discovery` 요약(status=`source_missing`, bridge_candidate_count=`0`, code_improvement_order_count=`0`, runtime_env_key=`KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED`)을 함께 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder`/bridge discovery 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0728] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-07-28`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-27.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, scale_in_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0728] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-07-28`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-27.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0728] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-07-28`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-07-28.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-28.jsonl), [threshold_events_2026-07-28.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-07-28.jsonl), [observation_source_quality_audit_2026-07-28.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-28.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-07-28 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

- [x] `[MonitorArchiveIsolation0728] 15:45 full snapshot 메인 heartbeat 자원 격리` (`Due: 2026-07-28`, `Slot: INTRADAY`, `TimeWindow: 15:45~16:00`, `Track: RuntimeStability`)
  - Source: [bot_main.py](/home/ubuntu/KORStockScan/src/bot_main.py), [run_monitor_snapshot_safe.sh](/home/ubuntu/KORStockScan/deploy/run_monitor_snapshot_safe.sh), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정: 15:45 direct in-process full snapshot이 15:45~15:53 main heartbeat를 굶기고 parent RSS를 확대했다. KRX 거래 종료 공백이므로 해당 stale 자체를 missed EV로 합산하지 않지만, 16:00 NXT 재개 준비와 같은 PID의 source-quality를 오염시킬 수 있어 결함으로 닫았다.
  - 반영: named async dedupe는 유지하고 heavy snapshot만 기존 safe wrapper의 synchronous worker subprocess로 넘긴다. wrapper exit, fresh full manifest, target date/profile 계약이 모두 확인된 뒤에만 performance/log archive job을 성공으로 닫는다.
  - 검증/rollback: scheduler·heartbeat·dedupe·wrapper failure/stale manifest 테스트, Black, compile, `git diff --check`, checklist parser를 통과해야 한다. wrapper 실패 또는 다음 자연 15:45 표본에서 heartbeat/resource 회귀가 발생하면 이전 direct path로 돌아가지 않고 isolated worker 계약을 재검토한다.

- [x] `[ScannerExpiredRecheckFairness0728] NXT recurring recheck 만료 전환 기아 보완` (`Due: 2026-07-28`, `Slot: INTRADAY`, `TimeWindow: 16:20~16:40`, `Track: ScalpingLogic`)
  - Source: [scanner_runtime_scheduler.py](/home/ubuntu/KORStockScan/src/engine/scalping/scanner_runtime_scheduler.py), [test_scanner_runtime_scheduler.py](/home/ubuntu/KORStockScan/src/tests/test_scanner_runtime_scheduler.py), [pipeline_events_2026-07-28.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-28.jsonl)
  - 판정: 이미 최초 평가를 마친 한 generation의 `post_heavy_eval_fresh_recheck`가 계속 새 deadline을 얻으면 다른 generation의 만료된 recheck가 dispatchable peer 필터에서 제외되어 자기 `deadline_expired` 전환도 닫지 못했다. 이는 threshold가 아니라 평가 공정성 결함이며, 현금 0원·broker quantity guard와 분리한다.
  - 반영: FAST_PRECHECK claim 시 요청 generation 자신의 만료 work만 먼저 `deadline_expired`로 닫을 수 있게 한다. 시장 평가, BUY, 주문 수량, provider, threshold 권한은 추가하지 않으며 critical lane과 아직 유효한 initial precheck 예약은 유지한다.
  - 자연 표본 보완: `17:33` PID `1115206`에서 요청 generation의 work가 이미 완료되어 자기 lane item이 없는데 fresh peer가 남아 있으면 generation-scoped `claim()`이 `missing` 대신 peer 기준 `not_next`를 반환하는 두 번째 기아 원인이 확인됐다. 재기동 후 약 7분 동안 `claim_deferred=2459`건과 350초 이상 wait가 누적됐으며, 요청 generation 후보가 없으면 즉시 `missing -> 기존 bounded fresh precheck rebuild`로 닫도록 보완했다. 이 변경도 평가 순서만 소유하고 BUY·provider·threshold·주문 권한은 갖지 않는다.
  - runtime 적용: review gate에서 scheduler/async/NXT/AI cadence 관련 `958 passed`, scheduler 통합 `96 passed`, source-quality `127 passed`, compile/Black/Ruff/diff/checklist parser를 통과한 commit `550ad7ac`으로 PID `1115206 -> 1126134` graceful restart를 완료했다. 새 PID는 `source_dirty=false`, `async_v1`, 전 venue, runtime env verify `pass`, 계좌 reconciliation·WS 로그인·0B/0D 수신·OpenAI 2-key route가 정상이다. 첫 7개 boot/missing 표본은 `claim_missing -> fresh_precheck_after_missing_work`로 즉시 복구됐고 queue wait=`0.0s`, boot generation 첫 dispatch watch age 최대=`5.455s`, fresh attach initial queue wait 최대=`0.007s`였다. 이후 recurring recheck queue wait는 약 `12.5~16.0s`로 관측되어 기존 수백 초 무한 defer는 재현되지 않았다.
  - 검증/rollback: 실적 형태의 expired-requester/fresh-recurring-peer 회귀 테스트와 전체 scheduler targeted test, Black, compile, `git diff --check`, checklist parser를 통과해야 한다. 다음 PID에서 claim wait가 줄지 않거나 initial/critical 예약 회귀가 생기면 해당 fairness 분기만 되돌리고 중앙 `next_decision` 소비 경로를 별도 검토한다.

- [ ] `[ScannerExpiredRecheckFairnessRuntimeObserve0729] 보완된 recheck 공정성 다음 PID 자연 표본 확인` (`Due: 2026-07-29`, `Slot: INTRADAY`, `TimeWindow: 16:00~16:20`, `Track: ScalpingLogic`)
  - Source: [scanner_runtime_scheduler.py](/home/ubuntu/KORStockScan/src/engine/scalping/scanner_runtime_scheduler.py), [pipeline_events_2026-07-28.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-28.jsonl)
  - 판정 기준: 새 PID가 보완 commit을 반영한 상태에서 `post_heavy_eval_fresh_recheck` peer가 있어도 만료된 요청 generation이 `deadline_expired -> fresh enqueue`로 닫히고, 자기 lane item이 이미 없는 요청 generation은 peer 기준 `not_next` 반복 없이 `missing -> fresh enqueue`로 닫히며, initial precheck와 critical lane 예약이 유지되는지 확인한다.
  - 금지: 검증을 위해 provider, threshold, 주문가·수량, broker/account/order/cooldown guard를 변경하거나 실제 BUY를 강제하지 않는다.
  - 다음 액션: `runtime_fairness_confirmed`, `no_natural_expired_peer_sample`, `claim_starvation_regressed`, `initial_or_critical_reservation_regressed`, `implementation_not_reflected_in_pid` 중 하나로 닫는다.

- [x] `[HotPathAISymbolBudget0728] 동일 종목 live AI 호출 폭주와 판단 재사용 계약 보완` (`Due: 2026-07-28`, `Slot: INTRADAY`, `TimeWindow: 17:10~17:35`, `Track: RuntimeStability`)
  - Source: [hot_path_ai_symbol_budget.py](/home/ubuntu/KORStockScan/src/engine/ai/hot_path_ai_symbol_budget.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정/반영: scanner/rising-missed entry와 holding/scale-in holding-score가 같은 종목에서 서로 독립적으로 provider를 반복 호출하던 경로를 process-local 60초 rolling budget으로 묶었다. 기본값은 종목 전체 4회, entry·holding 각 group 2회이며 기존 endpoint 최소 간격을 함께 적용한다. 동일 scanner generation의 fresh·trusted 판단은 상태축과 가격이 유의미하게 변하지 않은 경우에만 제한 재사용하고, budget defer는 prior score를 usable AI 권한으로 승격하지 않는다.
  - 권한/rollback: 이 guard는 AI 호출 cadence에만 runtime effect가 있고 threshold, provider route, 주문가·수량, broker/account/order/cooldown, hard/protect/emergency 권한이 없다. provider 호출 누락으로 deterministic safety exit가 지연되거나 새 generation의 첫 평가가 막히거나 종목별 service share가 과도하게 축소되면 이 cadence 변경만 되돌린다.

- [ ] `[HotPathAISymbolBudgetRuntimeObserve0729] 동일 종목 AI cadence·service share 다음 PID 자연 귀속` (`Due: 2026-07-29`, `Slot: INTRADAY`, `TimeWindow: 09:05~16:30`, `Track: RuntimeStability`)
  - Source: [hot_path_ai_symbol_budget.py](/home/ubuntu/KORStockScan/src/engine/ai/hot_path_ai_symbol_budget.py), [pipeline_events_2026-07-28.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-28.jsonl)
  - 판정 기준: 새 PID에서 동일 종목 entry/holding group과 전체 cap, 최소 간격, recent-valid reuse가 provenance로 남고, budget defer가 stale 판단을 usable authority로 만들지 않으며 deterministic exit·새 scanner generation 평가를 지연시키지 않는지 확인한다.
  - 금지: 자연 표본 확보를 위해 provider, threshold, 주문가·수량, broker/account/order/cooldown/hard safety를 변경하거나 AI 호출을 강제하지 않는다.
  - 다음 액션: `cadence_guard_healthy`, `no_natural_multi_endpoint_sample`, `service_share_overthrottled`, `stale_reuse_authority_leak`, `deterministic_exit_delayed`, `implementation_not_reflected_in_pid` 중 하나로 닫는다.

- [x] `[RisingMissedWaitPersistentDirectionGuard0728] NXT WAIT 단일 TP1 통과·stale initial reprice 결함 보완` (`Due: 2026-07-28`, `Slot: INTRADAY`, `TimeWindow: 16:40~17:10`, `Track: ScalpingLogic`)
  - Source: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [test_sniper_scale_in.py](/home/ubuntu/KORStockScan/src/tests/test_sniper_scale_in.py), [test_entry_reprice_after_submit.py](/home/ubuntu/KORStockScan/src/tests/test_entry_reprice_after_submit.py), [pipeline_events_2026-07-28.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-28.jsonl)
  - 판정/구현: 펩트론 `087010`은 `16:42:26 DROP` 뒤 `16:42:57 WAIT + bid imbalance 없음 + NXT fast-tape fresh=false` 단일 TP1 평가가 통과했고, `16:43:14`에는 16초 이상 지난 TP1 문맥으로 initial 주문가를 상향 재제출한 뒤 20분 counterfactual이 `adverse_stop_first`로 끝났다. WAIT/no-bid 후보는 같은 promotion의 fresh NXT fast-tape와 0.25~20초 간격 2회 연속 확인을 요구하고, source gap·명시적 AI negative·promotion identity 결손은 체인을 초기화하거나 fail-closed한다. rising-missed initial reprice는 5초 이내의 허용된 TP1 방향 문맥만 사용하며 probe residual의 기존 post-probe P1 owner는 변경하지 않는다.
  - 실적 replay/검증: 당일 NXT 실주문 통과 표본 중 동일 `WAIT + no bid imbalance`는 2건이며 둘 다 fast-tape fresh=false였다. 펩트론은 실현 `-3.71%`, LIG디펜스앤에어로스페이스는 20분 `no_hit`이므로 새 gate가 당일 확인된 target-first 기회를 제거한 증거는 없다. 관련 reprice/TP1 회귀, Black, compile, `git diff --check`, checklist parser와 review gate를 통과해야 하며 현재 PID에는 미반영이다.
  - 최종 review gate: 1차 리뷰에서 promotion identity 결손 체인 결합, 중간 source-gap 뒤 count 잔존, NXT 근거의 KRX 공통경로 과확장을 찾아 모두 보완했다. 이어 holding replay의 `now_dt`와 freshness/session guard의 wall clock이 갈라지던 결함 및 테스트 간 datetime/runtime-rule 누수를 정리했다. NXT WAIT/TP1, entry reprice, 기존 KRX 경계와 확대 state-handler suite `920`건이 모두 통과했고 Black·compile·`git diff --check`·checklist parser도 통과하므로 재기동 gate를 연다.

- [ ] `[RisingMissedWaitPersistentDirectionRuntimeObserve0729] WAIT 지속확인·initial reprice guard 다음 PID 자연 귀속` (`Due: 2026-07-29`, `Slot: INTRADAY`, `TimeWindow: 16:00~17:10`, `Track: ScalpingLogic`)
  - Source: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [pipeline_events_2026-07-28.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-28.jsonl)
  - 판정 기준: 새 PID에서 NXT `WAIT + wait_without_bid_imbalance` 후보가 fast-tape 결손 시 defer되고, 같은 promotion의 fresh 연속확인 2회가 있을 때만 TP1을 통과하며, 중간 source gap/AI negative/identity 결손은 count를 초기화하는지 확인한다. 통과 뒤 5초가 지난 initial reprice는 broker cancel/resubmit 없이 차단되고 probe residual은 기존 post-probe P1 계약을 유지해야 한다.
  - 금지: 자연 표본 확보를 위해 BUY를 강제하거나 provider, threshold, 주문가·수량, broker/account/order/cooldown/hard safety를 변경하지 않는다.
  - 다음 액션: `persistent_confirmation_and_reprice_guard_confirmed`, `no_natural_wait_no_bid_sample`, `confirmation_chain_not_persistent`, `initial_reprice_guard_regressed`, `probe_residual_owner_regressed`, `implementation_not_reflected_in_pid` 중 하나로 닫는다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[PostcloseSourceQualityGateReview0728] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-07-28`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-07-28.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-28.json), [threshold_cycle_ev_2026-07-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-28.json), [code_improvement_workorder_2026-07-28.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-28.json), [threshold_cycle_postclose_verification_2026-07-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-07-28.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0728] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-07-28`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-27.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0728] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-07-28`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-27.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0728] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-07-28`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-07-27.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-07-27.md), [code_improvement_workorder_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-27.json)
  - 판정 기준: selected_order_count=184와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0728] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-07-28`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-27.json), [runtime_apply_gap_audit_2026-07-27.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-27.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`111`, rollup_required_count=`111`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'exclusion_dimension_candidate': 1, 'parent_conflict_child': 2, 'positive_source_only_keep_collecting': 108}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0728] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-07-28`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-07-27.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-07-27.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`16`, run_count=`16`, skip_count=`0`, source_missing_count=`7`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, scalp_sim_ai_deferred_review, pattern_lab_currentness_audit`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:15, source_missing_or_unreadable:7, upstream_drift_signal:7, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## 사용자 지시 실행 체크리스트

- [x] `[PanicSellDefenseMemoryBoundedStreaming0728] panic_sell_defense_report 대용량 JSONL 전량 적재 제거` (`Due: 2026-07-28`, `Slot: INTRADAY`, `TimeWindow: 14:10~14:20`, `Track: RuntimeStability`)
  - Source: [panic_sell_defense_report.py](/home/ubuntu/KORStockScan/src/engine/panic_sell_defense_report.py), [panic_sell_state_detector.py](/home/ubuntu/KORStockScan/src/engine/panic_sell_state_detector.py), [panic_sell_defense_2026-07-28.json](/home/ubuntu/KORStockScan/data/report/panic_sell_defense/panic_sell_defense_2026-07-28.json)
  - 판정/구현: `read_jsonl -> list` 전량 적재를 제거하고 1회 streaming에서 exit/non-real provenance만 보존하며 micro detector는 종목별 bounded state로 갱신한다. out-of-order row는 monotonic state 보호를 위해 제외하고 count를 남긴다.
  - 실제 검증: `14:14:01~14:14:13`, `14:16:02~14:16:13` 자연 cron이 당일 `292,023`행을 처리해 exit/provenance `2,820`행만 보존했고 full event list는 생성하지 않았다. micro 후보 `31,751`, out-of-order `0`, report 상태는 기존과 동일한 `RECOVERY_WATCH`였다. 별도 동일 입력 dry-run은 `10.17초`, 최대 RSS `54,772KB`, major page fault `0`으로 종료했고 main process/resource detector는 PASS를 유지했다.
  - 금지/rollback: report-only/source-quality 권한을 유지한다. out-of-order 증가, panic state 회귀, heartbeat stale 또는 자원 경고가 재발하면 해당 cron을 중단하고 streaming ordering 계약을 재검토한다.

- [x] `[PanicBuyingReportPermanentOperatorStop0728] panic_buying_report 영구 OFF 및 명시적 운영 override gate 적용` (`Due: 2026-07-28`, `Slot: INTRADAY`, `TimeWindow: 14:00~14:10`, `Track: RuntimeStability`)
  - Source: [run_panic_buying_intraday.sh](/home/ubuntu/KORStockScan/deploy/run_panic_buying_intraday.sh), [panic_buying_report.py](/home/ubuntu/KORStockScan/src/engine/panic_buying_report.py), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정/구현: `13:59` 실행 중이던 report-only 프로세스를 종료하고 intraday cron을 제거했다. wrapper와 직접 CLI는 `KORSTOCKSCAN_PANIC_BUYING_REPORT_OPERATOR_OVERRIDE=true`가 없으면 실행을 거부하며, postclose 기본값도 false다. cron/artifact detector inventory에서 중지 작업을 제외해 stale 오탐을 막는다.
  - 재활성화 조건: 사용자의 명시적 운영 지시, 자원 제한 보완, 코드리뷰·targeted validation을 모두 거친 뒤에만 override와 schedule을 복원한다. 기존 산출물은 archive-only이며 주문·threshold·provider·봇 상태 변경 권한이 없다.

- [x] `[ScannerHeavyEvalTickChurnBound0728] 동일 generation heavy-eval 틱 변동 우회 및 scheduler 작업 증폭 보완` (`Due: 2026-07-28`, `Slot: INTRADAY`, `TimeWindow: 13:30~14:10`, `Track: RuntimeStability`)
  - Source: [kiwoom_sniper_v2.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py), [test_kiwoom_sniper_market_regime_runtime.py](/home/ubuntu/KORStockScan/src/tests/test_kiwoom_sniper_market_regime_runtime.py), [scanner_runtime_scheduler.py](/home/ubuntu/KORStockScan/src/engine/scalping/scanner_runtime_scheduler.py), [pipeline_events_2026-07-28.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-28.jsonl)
  - 판정/구현: 13:00~13:30 KST에 work enqueue `1,899`, claim deferred `818`, deadline expired `295`, heavy-eval lag `259`가 발생했다. 동일 generation의 BBO·strength·누적거래량 변경이 15초 heavy 재시도 제한을 우회하던 경로를 막고, 새 promotion generation은 평가 상태를 초기화해 즉시 평가하며 COMMIT·RECOVERY lane은 기존 우선순위를 유지하도록 보완했다.
  - 검증: scheduler/runtime targeted pytest `344 passed`, candle/AI/state-handler targeted pytest `260 passed`, Black·compile·`git diff --check` 통과. 현재 PID에는 미반영이며 별도 승인된 graceful restart 이후 generation별 enqueue/deadline-expired와 attach-to-first-heavy 지연을 재귀속한다.
  - 금지/rollback: 매매 threshold, provider, 주문·가격·수량, broker/account/order guard는 변경하지 않는다. 신규 generation 첫 heavy 평가 또는 COMMIT/RECOVERY cadence가 지연되면 이 코드 변경을 되돌린 뒤 review gate를 다시 통과한다.

- [ ] `[SamsungPriceWidgetWindowsInstall0728] AWS 공유토큰 전용 삼성전자 1분 가격 위젯 Windows 설치·1분 차이값 확인` (`Due: 2026-07-28`, `Slot: INTRADAY`, `TimeWindow: 10:30~15:20`, `Track: RuntimeStability`)
  - Source: [samsung_price_widget_routes.py](/home/ubuntu/KORStockScan/src/web/samsung_price_widget_routes.py), [Windows 설치 안내](/home/ubuntu/KORStockScan/tools/windows/README.md), [Gunicorn widget drop-in](/home/ubuntu/KORStockScan/deploy/systemd/korstockscan-gunicorn-widget.conf)
  - 실행 결과 (`2026-07-28 10:28 KST`): `https://korstockscan.ddns.net/api/widget/samsung-price`는 무인증 `401`, AWS key 인증 `200`을 확인했다. 응답은 `source=kiwoom_ka10001`, `token_mode=shared_cache_only`, `current_price=230000`이며 Kiwoom token cache 재사용 로그만 남겼다. AWS key는 `/etc/korstockscan/samsung-price-widget.key` (`root:www-data 640`, 상위 디렉터리 `root:www-data 750`)에만 있고 repository/Windows에는 Kiwoom appkey·secret·bearer token을 저장하지 않는다.
  - 코드 보완 (`2026-07-28 16:10 KST`): Windows 조회 주기를 10초로 조정하고 NXT 애프터마켓에는 `ka10001`·`ka10080` 모두 공식 거래소별 코드 `005930_NX`를 사용한다. 응답에는 `market_venue`, `market_session`, `quote_request_code`를 남긴다. 공식 Kiwoom upstream `1504d45fa145eb11fdd662a08aa9d873eee55849`의 `kiwoom_docs/종목정보.md`, `kiwoom_docs/차트.md`, SDK spec을 재검증했다.
  - 금지: widget endpoint가 token 발급/refresh/revoke, 주문·계좌·bot control 또는 `restart.sh`를 호출하거나, Windows에 Kiwoom credential을 배포하는 것을 금지한다.
  - 다음 액션: Windows PC에 `tools/windows`를 복사하고, AWS key는 승인된 비밀 전달 경로로만 전달한 뒤 `Install-SamsungPriceWidget.ps1`을 실행한다. 20초 뒤 현재가·직전 성공 조회 차이와 KRX/NXT venue 표시가 갱신되는지 확인한다.

- [ ] `[UnexpectedBotRestartTrace0728] 10:28 KST bot 재기동 원인과 widget/token 비인과성 확인` (`Due: 2026-07-28`, `Slot: INTRADAY`, `TimeWindow: 10:30~15:20`, `Track: RuntimeStability`)
  - Source: [bot_history.log](/home/ubuntu/KORStockScan/logs/bot_history.log), [kiwoom_utils_info.log](/home/ubuntu/KORStockScan/logs/kiwoom_utils_info.log), [kiwoom_sniper_v2_info.log](/home/ubuntu/KORStockScan/logs/kiwoom_sniper_v2_info.log)
  - 관측: widget web 배포 중 bot PID가 `805625 -> 825445`로 바뀌었고 새 PID는 계좌 동기화·WS 로그인·00 등록·0B/0D 첫 수신을 완료했다. endpoint 호출 시각 `10:28:55`에는 token cache reuse만 보이며 신규 발급 log는 없다. 즉 현재 증거로는 widget token flow가 재기동 원인이라는 인과는 확인되지 않았다.
  - 금지: 원인 미확정 상태에서 bot restart, token invalidation/force refresh, broker/order/provider/threshold 변경을 하지 않는다.
  - 다음 액션: supervisor/restart.flag/error-detector 로그를 10:27~10:28 KST window로 최소 범위 재구성해 trigger를 특정하고 `external_restart|auth_8005|process_health|manual_signal|unresolved`로 닫는다.

- [x] `[ExactV2RuntimeStartupProvenance0728] Exact V2 PREMARKET 기동 provenance·effective holding context 확인` (`Due: 2026-07-28`, `Slot: PREOPEN`, `TimeWindow: 07:55~08:20`, `Track: AIPrompt`)
  - Source: [Exact V2 작업지시](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/exact_v2_premarket_promotion_work_instruction_2026-07-28.md), [holding_decision_context.py](/home/ubuntu/KORStockScan/src/engine/scalping/holding_decision_context.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 완료 결과: `2026-07-28 07:55:02 KST` PID `712183`, commit `436b98e5`, scheduler `async_v1` 초기화는 확인됐으나 runtime provenance가 `source_dirty=true`다. effective env의 holding cohort keys는 모두 true지만 promotion activation은 `promotion_artifact_required_missing_or_invalid`; 실제 effective context는 KRX/PREMARKET=false, NXT=true다. 이는 PASS가 아닌 bounded NXT fallback이며 `input_preflight_mode=baseline_v1`이다.
  - 권한 경계: source-dirty PID는 exact_v2 promotion, first-observation, Control/Baseline natural cohort의 runtime acceptance 증거가 아니다. 주문·가격·수량·threshold·provider route·hard safety·bot 상태를 변경하지 않는다.

- [ ] `[ExactV2PremarketPromotionRevalidation0728] clean runtime 이후 Exact V2 binary full-market promotion 재검증` (`Due: 2026-07-28`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:40`, `Track: AIPrompt`)
  - Source: [Exact V2 작업지시](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/exact_v2_premarket_promotion_work_instruction_2026-07-28.md), [promotion artifact 2026-07-27](/home/ubuntu/KORStockScan/data/runtime/ai_multi_timeframe_context_promotion_2026-07-27.json)
  - 시작 gate: clean review finding=0, targeted tests/compile/diff=pass, `source_dirty=false` 신규 PID, runtime-env handoff/read-back, rollback/first-observation hook가 모두 확인될 때만 validation-only actual call을 수행한다. 현 PID `712183`은 `blocked_review_or_env`이므로 시작하지 않는다.
  - 판정 기준: `analyze_target`, `entry_price`, `holding_score`, `holding_flow` 각각에서 completed-bar-only canonical context, exact request/prompt/payload/response hash, provider non-none, route/venue/session/source-quality, 비교 가능 외부 필드 `MISMATCH=0`을 모두 통과해야 한다. PASS만 `promoted_all_market_sessions_full`; 그 외는 blocker artifact와 `runtime_activation=false`로 닫는다.
  - 금지: dirty runtime을 PASS 증거로 사용, partial/canary promotion, context 강제 활성화, 사후 payload 복원, 주문·가격·수량·threshold·provider/bot/hard-safety 변경을 금지한다.

- [x] `[ExactV2KrxValidationOnly0920_0728] KRX 정규장 exact context validation-only 재검증` (`Due: 2026-07-28`, `Slot: INTRADAY`, `TimeWindow: 09:20~09:30`, `Track: AIPrompt`)
  - Source: [Exact V2 작업지시](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/exact_v2_premarket_promotion_work_instruction_2026-07-28.md), [entry_context_intraday_probe.py](/home/ubuntu/KORStockScan/src/engine/scalping/entry_context_intraday_probe.py), [ai_input_external_validation.py](/home/ubuntu/KORStockScan/src/engine/scalping/ai_input_external_validation.py)
  - 목적/권한: 사용자 지시에 따른 KRX 정규장 검증 증거 수집이다. fresh natural candidate만 real endpoint에 validation-only로 호출하며, 결과는 다음 PREMARKET binary promotion 판정에만 사용한다. 이 항목은 runtime activation·partial promotion·주문 제출 권한을 갖지 않는다.
  - 시작 조건: KRX venue/session 정합, fresh conflict-free source, canonical context/raw 1분봉/completed bar 1개 이상, provider route가 유효한 자연 candidate가 endpoint별로 존재해야 한다. source-dirty PID는 사용자의 명시 지시대로 이 검증의 배제 사유로 쓰지 않되, provenance에는 그대로 남긴다.
  - 판정 기준: `analyze_target`, `entry_price`, `holding_score`, `holding_flow` 각각에 대해 request/prompt/payload/response hash, request/response ID, provider non-none, venue/session, canonical context, completed-bar-only, source quality, API→payload 변환을 확인한다. 비교 가능한 외부 필드는 `MISMATCH=0`이어야 하며, 표본·원천 제약은 `NOT_COMPARABLE` 또는 `SOURCE_UNAVAILABLE` 사유로 보존한다.
  - 종료: endpoint/표본이 없거나 계약 불충족이면 명시적 `sample_floor_keep_collecting` 또는 blocker로 종료하며, 이를 PASS 또는 runtime activation으로 해석하지 않는다. PASS 증거가 충분해도 KRX 창에서 apply하지 않고 다음 PREMARKET 작업지시에서만 binary full-market promotion을 재판정한다.
  - 금지: synthetic/사후 재구성 context, provider/model/route 변경, prompt 승격, 주문·가격·수량·threshold·hard-safety·bot 상태 변경.
  - 2026-07-28 09:20~09:22 KST 결과: fresh KRX `analyze_target` natural candidate `034940` 1건만 validation-only actual call로 완료했다. OpenAI `gpt-5.4-nano`, `provider != none`, response ID/hash, payload/request/prompt hash 및 token/latency가 기록됐고, exact payload의 completed 1분봉 필드 95/95 `MATCH`, mismatch=`0`, forming bar included=`0`이었다. 주문·runtime activation·provider route 변경은 `0`이다.
  - 종료 판정: `sample_floor_keep_collecting` 및 `source_quality_blocked`. `entry_price`, `holding_score`, `holding_flow`은 fresh natural candidate가 없어 합성 호출하지 않았다. 대상의 Kiwoom completed minute 원본에 `09:01`, `09:04` 결손이 있어 VWAP/opening-range 파생값은 fail-closed했고, KRX Open API 일별 outblock도 비어 `source_unavailable`이었다. 네이버 보조 원천의 비교 가능 33개는 모두 `MATCH`, 외부 mismatch=`0`이지만 이 값은 full-market promotion PASS 근거가 아니다.
  - 다음 조치: 새 KRX 자연 후보가 각 미확보 endpoint에 발생한 뒤 같은 validation-only capture를 재수행한다. 일봉 KRX Open API outblock 계약과 KRX 1분봉 결손 원인은 별도 source-quality 결함으로 유지한다.
  - 2026-07-28 09:12 KST 재기동 후 재검증: PID `767851` (runtime commit `33b8ecf`, `source_dirty=true`, `input_preflight_mode=baseline_v1`)에서 fresh·conflict-free KRX `analyze_target` candidate `413630` 1건을 다시 validation-only 호출했다. OpenAI `gpt-5.4-nano` 호출은 provider response ID/hash와 함께 성공했고, exact payload 95/95 `MATCH`, provider none=`0`, forming bar included=`0`, 네이버 비교 가능 68개 `MATCH`, mismatch=`0`이었다.
  - 재기동 후 종료 판정: `sample_floor_keep_collecting` 및 `source_quality_blocked` 유지. Kiwoom completed minute `09:19` 결손으로 source-quality gate가 차단됐고, KRX Open API 일별 outblock은 여전히 비어 있다. `entry_price`, `holding_score`, `holding_flow` fresh natural candidate가 없어 호출하지 않았으며, 이 결과는 runtime activation 또는 full-market promotion PASS가 아니다.
  - 2026-07-28 09:55 KST 계측 결함보완: decision trace는 이제 `canonical_context_application_state`로 `applied_exact`, `promotion_gated_forensic_exact_available`, `forensic_candidate_ineligible`, `no_exact_payload_or_candidate`, `legacy_or_uninstrumented`를 분리 기록한다. candidate가 존재하지만 promotion 때문에 live payload에 미적용된 경우를 적용 실패와 혼동하지 않는다. 이 변경은 trace/provenance 전용이며 prompt/payload, provider route, 주문·가격·수량·threshold, runtime activation을 변경하지 않는다. 새 PID의 KRX 자연 호출에서 해당 상태 필드를 확인한다.
  - 2026-07-28 KST 기준 변경: 승인된 KRX Open API 일별 서비스의 빈 `OutBlock_1`은 현재 해결 불가한 외부 일별 응답 결함으로 기록만 유지한다. 이는 completed intraday bar·AI payload 정확성·promotion의 required-source gate가 아니며, `non_blocking_external_daily_observation`으로 분류한다. KRX/NAVER 분봉의 동일 venue·completed-bar 비교, Kiwoom→AI exact payload 변환, provider non-none 및 Kiwoom 원천 결손/충돌 검증은 계속 필수다.

- [ ] `[ExactV2NaturalSampleControlBaseline0728] promotion PASS 후 자연 Exact V2 표본·60분 Control baseline 전환` (`Due: 2026-07-28`, `Slot: INTRADAY`, `TimeWindow: 08:40~23:00`, `Track: AIPrompt`)
  - Source: [Exact V2 작업지시](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/exact_v2_premarket_promotion_work_instruction_2026-07-28.md), [ai_decision_trace.py](/home/ubuntu/KORStockScan/src/engine/scalping/ai_decision_trace.py), [ai_decision_quality.py](/home/ubuntu/KORStockScan/src/engine/scalping/ai_decision_quality.py)
  - 시작 조건: `[ExactV2PremarketPromotionRevalidation0728]`가 `promoted_all_market_sessions_full`일 때만 시작한다. validation-only 호출과 `baseline_v1`, compact, promotion 이전 payload는 Control/Baseline primary cohort에서 제외한다.
  - 판정 기준: promotion 이후 자연 `exact_completed_bars_captured`, exact_v2 preflight allowed, provider non-none, canonical context/bundle/raw 1분봉/completed bar, venue/session consistency, source-quality pass row만 수집한다. 동일 venue/session 1/3/5/10/20/30/60분 outcome을 연결하고 60분 maturity·stage/venue sample floor 충족 시에만 `control_error_baseline_ready`로 닫는다.
  - 다음 액션: `control_error_baseline_ready`, `sample_floor_keep_collecting`, `partial_horizons_keep_maturing`, `promotion_failed_no_collection`, `source_quality_blocked` 중 하나로 닫는다.

- [ ] `[LimitDownRotationPreopenActivation0728] 연속 하한가 순환관찰 ON 기동·PID 귀속·무주문 검증` (`Due: 2026-07-28`, `Slot: PREOPEN`, `TimeWindow: 08:00~09:00`, `Track: ScalpingLogic`)
  - Source: [limit-down PREOPEN 작업지시](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/limit_down_rotation_preopen_activation_work_instruction_2026-07-28.md), [dated runtime override](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/operator_runtime_overrides_2026-07-28.env), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 시작 gate: target-date handoff `status=pass`, dirty source review-gate finding `0`, relevant targeted test, provider config non-empty, dated override final load를 모두 확인한다. 명시적 operator start 지시 전에는 봇을 기동하지 않는다.
  - 검증 기준: 신규 PID handoff `status=pass`/`pid_passed=true`, `general1/opening2/limit_down1/rising12`, 실제 WS route/item cap, candidate provenance 또는 valid no-candidate, raw `0B` tick, `LIMIT_DOWN_WATCH`의 Recommendation/ACTIVE_TARGET/BUY/주문 event `0`을 확인한다. 자연 AI/provider audit row가 발생한 경우 `provider=none`은 `0`이어야 하며, 아직 호출이 없으면 `pending_natural_provider_observation`으로 남긴다.
  - rollback: source-quality block, WS cap 초과, registry leak, ordered tick capture 실패, trade-authority leak이면 이 레인만 OFF·UNREG·graceful restart하고 legacy opening 3을 복원한다. provider·threshold·가격·수량·cap·broker/hard safety는 변경하지 않는다.
  - 2026-07-28 08:05 KST runtime observation: the already-running PID emitted `candidate_source_exception:TypeError` before any observation registration. The failure was reproduced as a `ka10081` daily-index `NaT` comparison error; no `LIMIT_DOWN_WATCH` Recommendation/ACTIVE_TARGET/BUY/order event was emitted.
  - 2026-07-28 repair evidence: malformed `ka10081` date rows are now excluded per symbol while an all-invalid daily index remains fail-closed. Official source smoke returned `partial`, with 3 eligible candidates and 1 `ka10081_no_valid_completed_dates` row. The repair is review-gated but is not loaded into the existing PID; retain this item open until a separately explicit supervised restart and Pass 3 runtime verification.
  - 2026-07-28 08:20 KST supervised graceful restart: reviewed PID `712183` exited through `restart.flag`; the existing `run_bot.sh` supervisor started PID `729936`. PID handoff was `pass` with no missing/mismatched key, limit-down flag=`true`, and the reviewed dirty-source provenance. New runtime loaded the official source as `partial` (3 valid candidates, 1 blocked row), registered `131100` with one WS item, and retained `runtime_effect=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`. At 08:22 KST the candidate remained `WAITING_FIRST_TICK` because no trade tick had arrived; the manager recorded a `first_tick_pending` re-REG/heartbeat. No lane-attributable Recommendation/ACTIVE_TARGET/BUY/order/Telegram event was present. Keep the item open for natural raw-0B capture or the bounded no-tick rotation outcome.

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
