# 2026-08-26 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-08-25` postclose -> `2026-08-26`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0826] micro observer 저장공간·연속수집 source gap 복구 확인` (`Due: 2026-08-26`, `Slot: PREOPEN`, `TimeWindow: 08:40~08:45`, `Track: RuntimeStability`)
  - Source: [main_ai_quality_r0_r3_cycle_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-08-25.json)
  - 판정 기준: 2026-08-26 07:00 이전 source-only 재검증에서 갱신된 workorder `main-ai-gap-ba0d324d9d48bad7b39f8b1f`의 owner=`MicroReversionForwardCollectorContinuity`, reason_codes=`stop_required, past_market_row_missing=104`를 닫는다. 현재 exact canary stop reason은 `producer_callback_latency_p99_exceeded:2.073243>2.000000`과 그 prior auto-stop이며 queue full/drop은 모두 0이다. 장전 free bytes가 writer low-disk watermark를 충분히 상회하는지 확인하고, latency source owner를 보완한 뒤 신규 clean-date canary를 재검증한다.
  - 완료 조건: exact-date canary remains pass or row-exclusion-only through close; later clean windows continue collecting; provider replay remains held until queue-loss scope
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.
  - 장중 중간 결과: 09:16 현재 exact 5,000회×5 synthetic callback preflight는 queue drop·worker error 0, external p95/p99=`0.028448/0.054021ms`, internal p95/p99=`0.025815/0.048828ms`로 frozen `1/2ms` 한계 안이다. 현재 live collector도 stop_required=false, queue drop·worker/writer error 0으로 수집 중이며 종가까지의 자연 연속성 조건 때문에 항목은 열린 상태로 유지한다.
  - 12:32 후속 보완: 12:30 대형 리포트와 겹친 rolling 0B p99=`2.273851ms` 단일 초과가 observation queue drop·worker/writer error 0인 collector를 즉시 영구 중지해 이후 local census를 right-censor했다. Provider replay/R3는 첫 초과부터 기존 `stop_required`로 fail-closed하되, frozen 한도의 1~2배인 latency-only 초과는 10초 monitor snapshot 3회 연속 확인될 때 collector를 중지하고 2배 이상 severe latency와 worker/writer/lifecycle/monitor 오류는 즉시 중지하도록 보완했다. Bounded ingress queue loss는 기존 계약대로 collector를 유지하면서 raw row exclusion과 Provider replay hold로 처리한다. 실주문·threshold·provider route 권한은 열지 않는다.

- [ ] `[ThresholdEnvAutoApplyPreopen0826] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-08-26`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-25.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0826] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-08-26`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-08-25.json), [code_improvement_workorder_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-25.json), [threshold_apply_2026-08-26.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-08-26.json), [threshold_runtime_env_2026-08-26.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-08-26.json), [threshold_runtime_env_verify_2026-08-26.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-08-26.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`4`, forced_scout_with_post_sell_count=`8`, post_sell_join_coverage_pct=`1.980198`, outcome_coverage_state=`partial`, profitable_forced_scout_count=`7`, loss_or_flat_forced_scout_count=`1`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0826] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-08-26`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-25.json)
  - 전일 postclose candidate_selected_families=score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, post_probe_winner_recovery, scalping_pyramid_quality_gate, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0826] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-08-26`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-25.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0826] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-08-26`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-08-26.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-26.jsonl), [threshold_events_2026-08-26.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-26.jsonl), [observation_source_quality_audit_2026-08-26.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-26.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-08-26 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [x] `[PostcloseTuningGenerationRepairAcceptance0826] EV receipt 정합성·AI lifecycle workorder·자정 경계·후속 follower 정상생성 수용검증` (`Due: 2026-08-26`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~08:40`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-25.json), [main_ai_quality_r0_r3_cycle_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-08-25.json), [main_ai_quality_runtime_family_postclose_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_runtime_family/main_ai_quality_runtime_family_postclose_2026-08-25.json), [tuning_monitoring_postclose_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/tuning_monitoring/status/tuning_monitoring_postclose_2026-08-25.json), [ai_entry_setup_paired_replay_batch_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/ai_entry_setup_paired_replay_batch/ai_entry_setup_paired_replay_batch_2026-08-25.json)
  - 판정 기준: `trade_performance_facts` exact receipt economics가 daily/calibration/EV의 실거래 8건·승패 7/1과 일치하고 `count_match=true`여야 한다. real submitted lifecycle인데 accepted broker execution이 0인 rejected instrumentation gap과 rolling companion mismatch가 `RuntimeExecutionReceiptCustodyRepair` source-only workorder로 표면화돼야 한다. POSTCLOSE runtime-family는 동일 거래일의 자정 이후 bounded tail에서 날짜 오류 없이 fail-closed authority를 유지해야 한다. monitoring과 entry paired replay follower는 predecessor tail-repair 완료를 최대 12시간 bounded wait로 소비해 terminal artifact를 생성해야 한다. NXT eligible 수가 cap 이하일 때는 outcome-blind `complete_eligible_census`가 `deferred=0`, `selected=eligible`, `distinct<=cap`을 모두 증명하고 재시도에서 valid result를 재호출 없이 재사용해야 한다.
  - 금지: DB economics 추정 보정, 실주문·취소, threshold/provider route/bot/cap/quantity/hard safety 변경, invalid lifecycle의 R3 promotion, PREOPEN current-date guard 완화.
  - 완료 조건: targeted tests·parser·최종 review 무결함 후 2026-08-25 제한 재생성에서 EV reconciliation pass, runtime-family 날짜 오류 0, source-only gap workorder 존재, follower terminal status와 지연 생성 entry 후보의 아직 소비되지 않은 effective PREOPEN date를 확인한다. 자연 데이터 부족이나 canary stop은 명시적 source-only blocker로 남길 수 있으나 command failure·artifact 미생성·silent mismatch·이미 지난 PREOPEN 후보는 허용하지 않는다.
  - 결과: EV는 실거래 8건·승 7·패 1·`count_match=true`, OpenAI correction은 20 family parsed·비용 0원·runtime change false로 재생성했다. R0→R3는 lifecycle gap 36·real submitted 15·broker execution 0·companion mismatch 1·exact join missing 7을 `RuntimeExecutionReceiptCustodyRepair`로 표면화하고 R3 0건을 source-only fail-closed했다. POSTCLOSE runtime-family는 자정 이후 날짜 오류 없이 `blocked_fail_closed`, monitoring follower는 JSONL/DuckDB 전 지표 match 및 verified archive 완료, entry follower는 KRX 30/NXT 20 checkpoint를 신규 호출 0으로 재사용해 cohort failure 0으로 완료했다. 최종 controller=`done`, verifier=`warning`(허용된 next-PREOPEN handoff pending only), missing/stale/fingerprint issue=0이다. 리뷰에서 08:19 지연 생성 후보가 이미 소비된 08:26 PREOPEN을 가리키는 결함을 추가 발견해 `generated_at + first_available_krx_preopen_v1 + 07:35 cutoff` hash 계약으로 보완했다. 제한 재생성은 KRX 30/NXT 20을 다시 모두 재사용(`selected_new_count=0`)했고, 후보는 `bounded_exploration_apply_ready`, one-share exploration, `effective_date=2026-08-27`, `runtime_effect=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`로 정상 생성됐다. 현재 bot PID는 유지했고 실주문·runtime 적용은 수행하지 않았다.

- [x] `[CentralAllocatorProbeSubmissionAttributionRepair0826] 1주 probe 계획수량·실제제출수량 혼합 귀속 결함 보완` (`Due: 2026-08-26`, `Slot: POSTCLOSE`, `TimeWindow: 16:40~17:10`, `Track: ScalpingLogic`)
  - Source: [ai_quality_bridge.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/ai_quality_bridge.py), [test_micro_reversion_ai_quality_bridge.py](/home/ubuntu/KORStockScan/src/tests/test_micro_reversion_ai_quality_bridge.py), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정 기준: `probe_submitted`의 실제 1주를 계획 `effective_qty` 전체가 제출된 것으로 해석하지 않는다. 동일 trace·symbol·venue·session의 exact broker 주문번호별 제출수량을 중복 제거해 합산하고, 합계가 계획수량과 정확히 같을 때만 `central_allocator_provenance_joined`와 outcome-only notional 평가를 허용한다. probe/residual partial은 `allocator_provenance_partial_submission_observation_only`, 주문번호·수량 결손/충돌은 exact-row fail-closed로 닫는다.
  - 금지: terminal one-share 표본을 다주 notional EV·economic promotion evidence로 사용, 계획수량을 실제 제출수량으로 대체, quantity/cap·broker/order guard·runtime/provider/bot 변경, 봇 재기동 또는 비싼 R0→R3 재생성.
  - 결과: bridge producer를 `micro_reversion_ai_quality_bridge_v1_5`로 갱신하고 `probe_submitted + residual_submitted` exact 주문수량 합계 계약, partial coverage/status/summary를 추가했다. terminal 1/40주 표본은 standardized one-share observation-only로 유지되고, 중복 probe leg를 제거한 1+39주는 full allocator outcome-only로 결속된다. targeted bridge/cycle 273 tests, Ruff, report/checklist parser, compile, `git diff --check`와 최종 재리뷰가 모두 통과했다. runtime/order/provider/quantity/cap은 변경하지 않았고 봇 재기동·비싼 R0→R3 재생성도 수행하지 않았다.

- [x] `[EntrySetupFollowerDoneRetriggerRepair0826] postclose tail-repair 후 entry-setup terminal follower 자동 재호출 보완` (`Due: 2026-08-26`, `Slot: POSTCLOSE`, `TimeWindow: 15:05~15:40`, `Track: RuntimeStability`)
  - Source: [run_postclose_done_controller.sh](/home/ubuntu/KORStockScan/deploy/run_postclose_done_controller.sh), [test_threshold_cycle_wrappers.py](/home/ubuntu/KORStockScan/src/tests/test_threshold_cycle_wrappers.py), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정 기준: 고정 21:05 entry runner가 bounded predecessor timeout으로 끝난 뒤에도 main postclose controller가 target-date `succeeded`로 복구되면 같은 offline runner가 자동 재호출돼 `completed_offline_only` terminal batch를 남겨야 한다. 이미 terminal batch와 KRX candidate가 있으면 target/source date, status, path, artifact hash를 검증해 Provider 재호출 없이 건너뛰고, runner 0 종료 뒤 terminal evidence가 없으면 wrapper DONE을 차단해야 한다.
  - 금지: 실주문·취소, live runtime/PREOPEN policy 직접 적용, threshold/provider route/bot/cap/quantity/broker guard/hard safety 변경 또는 봇 재기동.
  - 완료 조건: wrapper targeted test, `bash -n`, checklist parser, `git diff --check`, review finding 0. 기존 2026-08-25 terminal artifact에 대한 follower state 검증이 `terminal_ready`이고 Provider 실행·runtime mutation·bot restart가 0이어야 한다.
  - 결과: postclose controller가 target-date 21:05 이후 `done`이면 fixed runner와 같은 lock의 활성 owner를 최대 1시간 기다리고, terminal batch가 없거나 무효일 때만 predecessor fail-fast로 동일 offline runner를 재호출하도록 보완했다. terminal reuse는 exact batch date/status와 expected candidate path, source/effective date, first-available PREOPEN policy, 07:35 cutoff, candidate contract, candidate 본문 재계산 self-hash와 batch reference artifact hash까지 검증한다. 리뷰에서 active fixed-runner lock을 성공으로 오인할 경쟁조건, legacy stale candidate 재사용 가능성, candidate/batch 동시 오염 시 self-hash 미검증 가능성을 찾아 보완했고 재리뷰 finding 0으로 닫았다. wrapper 전체 81 tests, targeted validator/follower tests, `bash -n`, Ruff, checklist parser, `git diff --check`가 통과했으며 기존 2026-08-25 artifact는 `terminal_ready:validated_batch_and_candidate`였다. Provider 실행·runtime mutation·bot restart는 수행하지 않았다.

- [ ] `[PostcloseSourceQualityGateReview0826] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-08-26`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-08-26.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-26.json), [threshold_cycle_ev_2026-08-26.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-26.json), [code_improvement_workorder_2026-08-26.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-26.json), [threshold_cycle_postclose_verification_2026-08-26.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-08-26.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0826] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-08-26`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-08-25.json), [threshold_cycle_ev_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-25.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0826] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-08-26`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-25.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0826] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-08-26`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-08-25.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-08-25.md), [code_improvement_workorder_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-25.json)
  - 판정 기준: selected_order_count=68와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0826] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-08-26`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-25.json), [runtime_apply_gap_audit_2026-08-25.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-25.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`390`, rollup_required_count=`390`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 389}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[MachineLifecycleTurnoverObjectiveFollowup0826] 위젯·episode 빠른 회전 목적의 미완료 후속 구현 확인` (`Due: 2026-08-26`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~21:40`, `Track: ScalpingLogic`)
  - Source: [machine_microstructure_policy_approval_postclose_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/machine_microstructure_policy_approval/machine_microstructure_policy_approval_postclose_2026-08-25.json), [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py)
  - 판정 기준: 승인 후보 수와 무관하게 `followup_required=true`인 미완료 목적 항목 `machine_lifecycle_turnover_policy_research_v1`(status=`EVIDENCE_ACCUMULATING`, next_action=`quarantine_current_source_date_and_continue_next_exact_date_collection`)의 상태와 상태별 `next_action`을 확인하고 구현 또는 표본수집 경로로 닫는다.
  - 상태별 다음 액션: `IMPLEMENTATION_REQUIRED`는 source-only rolling paired policy 연구를 구현하고, `EVIDENCE_ACCUMULATING`은 exact-date floor 충족까지 수집·재검증한다. `CANDIDATE_QUEUE_HANDOFF|COMPLETE`는 closed 상태이므로 report에서 제외되고 다음 refresh에서 builder-owned 항목이 제거된다.
  - 권한 경계: 이 POSTCLOSE 후속 항목은 source-only 구현·검증 작업이며 runtime env, 실주문, target/timeout/cooldown/cap, threshold, provider/bot, hard safety 또는 broker guard 변경 권한이 없다.
  - 장중 중간 결과: 8월 25일 추천 4종목은 모두 기존 research watch에 등록돼 있고, 8월 26일 source-only collection target은 episode `111770/181710/475150`, widget `475150/138080`을 선택했다. widget symbol/research collector와 40개 저가 episode timer는 설치·기동 상태이며, 승인 후보 0건·policy mutation 0건이므로 차단된 추천을 실매매 파라미터로 승격하지 않고 exact-date 표본만 계속 수집한다.

- [ ] `[AutomationTriggerDecisionSummary0826] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-08-26`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-08-25.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-08-25.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`14`, run_count=`9`, skip_count=`0`, source_missing_count=`4`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:8, disabled_by_runtime_policy:5, upstream_drift_signal:5, source_missing_or_unreadable:4, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## 결함 해소 후속 체크리스트

- [x] `[MainAIQualityObserverLabelGateSeparation0826] observer blocker의 local label·Provider·R3 단계 결속 분리` (`Due: 2026-08-26`, `Slot: OFFHOURS`, `TimeWindow: 00:00~23:59`, `Track: ScalpingLogic`)
  - Source: [ai_quality_cycle.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/ai_quality_cycle.py), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정 기준: exact bridge/materialized companion 검증을 통과한 action-neutral label과 Provider floor receipt는 observer canary stop/row-exclusion blocker와 무관하게 Provider 0-call source-only artifact로 생성한다. 같은 observer blocker는 두 로컬 산출물 생성 직후 Provider replay와 R3 promotion에 결속돼야 하며, 5거래일·20 common parent·10종목 Provider floor 또는 lifecycle/source-quality blocker를 완화하지 않는다.
  - 완료 조건: 단계 gate artifact가 `observer_blocks_action_neutral_label_generation=false`, `observer_blocks_provider_floor_materialization=false`, blocker 날짜의 `observer_blocks_provider_replay=true`, `observer_blocks_r3_promotion=true`를 명시하고 targeted test·parser·최종 review를 통과한다.
  - 권한 경계: 이 분리는 로컬 label 미생성 결함만 해소하며 Provider 호출, runtime/PREOPEN apply, 실주문·취소, threshold/provider route/bot/cap/quantity/hard safety 변경 권한을 열지 않는다.
  - 결과: 2026-08-25 persisted exact companion의 read-only smoke에서 materialized request 6건, action-neutral eligible label 2건을 정상 재구성했고 Provider floor는 1거래일·2 common parent·2종목으로 `keep_collecting_provider_ablation_floor`를 정확히 유지했다. label/floor 모두 `provider_call_performed=false`, `runtime_effect=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`다. 후속 리뷰에서 일반 BUY reprice 테스트를 취소 terminal absence·전시장 inventory exact reconciliation 계약에 맞추고 미증명 재주문 차단 회귀를 추가했으며, current callback/path/storage/WebSocket source hash를 5,000회×5 무손실 preflight에 재결속했다. Targeted 989건과 canonical 전체 9,467건(18 skip), parser/Ruff/compile/shell/diff 검증이 모두 통과했다. `[MainBuyCancellationReceiptCustody0827]`의 나머지 direct-call 자연 acceptance 범위는 별도 OPEN 상태를 유지한다.

- [x] `[MainAIQualityExactPreparedSourcePool0826] R2/P2 exact prepared request census와 단일 source-pool materialization 병목 해소` (`Due: 2026-08-26`, `Slot: OFFHOURS`, `TimeWindow: 00:00~23:59`, `Track: ScalpingLogic`)
  - Source: [ai_quality_bridge.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/ai_quality_bridge.py), [ai_decision_quality.py](/home/ubuntu/KORStockScan/src/engine/scalping/ai_decision_quality.py), [ai_quality_cycle.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/ai_quality_cycle.py)
  - 구현 범위: scheduled bridge는 exact prepared request trace census와 target/path/outer SHA/count를 결속하고, raw/config/window/coverage/hash/partition census를 검증한 재구축 가능 SQLite cache를 통해 A/B/C가 한 번 검증된 동일 source pool을 소비한다. Current materializer는 external bridge가 canonical sidecar status와 실제 sidecar 검증으로 증명한 ask-depletion source gap만 row-local 제외하고 fabricated exclusion은 계속 전역 차단하며, B→C의 `response_schema_application`을 명시적 prompt/response-contract 단일축으로 허용한다. Scheduled historical Provider backfill은 reviewed 30-calendar-day floor의 미완료 날짜를 oldest-first로 exact A/B/C 한 parent씩 처리하되 current slot을 남기고, cycle/direct leaf 공통 prior physical-ledger/checkpoint gate가 complete skip, capacity-partial exact resume, terminal·orphan permanent no-call을 보장해야 완료로 닫는다. 2026-08-25 재검증은 prepared 160건, source row 2건, materialization 2건/A·B·C request 6건, Provider 0 call로 통과했다.
  - 권한 경계: source-only materialization과 평가 입력 복구가 주 목적이다. reviewed cap·floor·prior-ledger gate를 모두 통과한 scheduled bounded replay 외의 수동·무제한 Provider 실행 권한과 runtime/order/policy apply, bot restart 권한은 열지 않는다.

- [ ] `[MainSellReceiptCustodyNaturalAcceptance0827] SELL pre-call custody 적용 후 자연 체결·부분체결·취소·재기동 acceptance 확인` (`Due: 2026-08-27`, `Slot: PREOPEN`, `TimeWindow: 07:50~20:00`, `Track: RuntimeStability`)
  - Source: [sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [main_lifecycle_paired.py](/home/ubuntu/KORStockScan/src/engine/scalping/main_lifecycle_paired.py)
  - 판정 기준: no-defect review와 targeted validation을 통과한 수정본이 로컬 commit/deploy까지 완료되어 `KORSTOCKSCAN_RUNTIME_SOURCE_DIRTY=false`로 기동 가능한 상태인지 먼저 확인한다. 그 조건을 충족한 뒤 기존 `07:55` cron이 자연 기동한 신규 표본에서 broker 호출 전 DB owner CAS와 fsynced exact pending journal이 존재하고, WS-before-HTTP·부분체결 잔량·취소·발생 시 재기동에서 동일 generation 재주문이 0건이며 terminal successor 영속화 뒤에만 interlock이 해제되는지 확인한다. acceptance를 위해 별도 수동 재기동이나 주문을 만들지 않는다.
  - 완료 조건: 신규 자연 lifecycle에서 diagnostic recovery 없이 entry/holding/final exit exact join이 생성되고 `FINAL_EXIT_RECONCILED`가 실거래 closed cycle과 수량·주문번호 기준으로 일치한다.
  - 권한 경계: 현재 dirty working tree 또는 미커밋 수정본의 `07:55` 기동은 이 acceptance의 적용 증거가 아니다. 이 항목 자체는 commit/push/deploy, 봇 재기동, 실주문·취소, provider/threshold/cap/hard-safety 변경 권한을 부여하지 않는다.

- [ ] `[PipelineReportDurableArchiveOwner0827] 무한 증가 raw/report 전체 producer retention·archive·restore 계약 확정` (`Due: 2026-08-27`, `Slot: POSTCLOSE`, `TimeWindow: 20:00~21:00`, `Track: RuntimeStability`)
  - Source: [storage_maintenance.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/storage_maintenance.py), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: `data/pipeline_events`와 `data/report`의 전체 producer/consumer/current-window manifest를 만들고, closed-date verified gzip, durable archive destination, content hash, restore manifest, consumer 보호기간을 결속한다.
  - 금지: durable archive destination과 restore 검증이 없거나 active/current consumer window가 확인되지 않은 상태에서 raw/report를 삭제하지 않는다.
  - 다음 액션: archive target과 보존기간이 확정되면 source-only canary로 압축·복원·hash 검증 후에만 local deletion 후보를 생성한다.

- [ ] `[IPOListingDaySellReceiptCustodyIsolation0827] IPO 독립 봇의 HTTP 성공 기반 synthetic fill/PnL/close 결함 격리·보완` (`Due: 2026-08-27`, `Slot: OFFHOURS`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [ipo_listing_day_runner.py](/home/ubuntu/KORStockScan/src/engine/ipo_listing_day_runner.py)
  - 판정 기준: code=0 응답만으로 fill·PnL·position close를 합성하지 않고 official execution receipt와 immutable order identity를 결속하며, 별도 main lifecycle/R3 비유입 계약을 회귀검증한다.
  - 금지: 결함 해소와 receipt acceptance 전까지 IPO 독립 봇을 기동하거나 실주문 권한을 열지 않는다.

- [ ] `[MainBuyCancellationReceiptCustody0827] 일반 BUY 취소 응답·부분체결·잔고의 exact custody 보완` (`Due: 2026-08-27`, `Slot: OFFHOURS`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py), [sniper_s15_fast_track.py](/home/ubuntu/KORStockScan/src/engine/sniper_s15_fast_track.py), [sniper_trade_utils.py](/home/ubuntu/KORStockScan/src/engine/sniper_trade_utils.py)
  - 판정 기준: `process_order_cancellation`은 non-dict/truthy 응답이나 오류 메시지를 성공으로 간주하지 않고 explicit broker `code=0` ACK를 요구한다. ACK 뒤에도 exact BUY execution receipt, 원주문 terminal 상태, KRX/NXT 전체 잔고를 대사해 부분체결 수량만 immutable owner에 결속한 뒤 DB/memory를 `HOLDING` 또는 terminal entry state로 전환한다. Direct-call census는 late-parent replacement BUY, S15 recovery/no-fill/partial-fill BUY, entry timeout/SOR retry/reprice bundle, pending-add/scale-in, generic cancellation을 각각 독립 crash boundary와 terminal-proof acceptance로 닫는다.
  - 금지: `취소가능수량|잔고|주문없음` 문자열, 단일 venue 잔고, 추정 수량만으로 phantom holding·부분체결 완료를 만들거나 신규 주문 권한을 열지 않는다. 이 항목은 현재 main SELL/R3 수정 범위와 분리하며 별도 구현·리뷰 전에는 완료 처리하지 않는다.

- [x] `[LowPriceRecommendationImplementation0826] 8월 26일 저가주 에피소드 추천 12건 exact-date 구현·리뷰` (`Due: 2026-08-26`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~23:59`, `Track: ScalpingLogic`)
  - Source: [low_price_two_leg_expanded_candidate_research_2026-08-26.json](/home/ubuntu/KORStockScan/data/report/low_price_two_leg_expanded_candidate_research/low_price_two_leg_expanded_candidate_research_2026-08-26.json), [low_price_two_leg_expanded_profile_evidence_2026-08-26.json](/home/ubuntu/KORStockScan/data/config/low_price_two_leg_expanded_profile_evidence_2026-08-26.json), [low-price-two-leg-machines.md](/home/ubuntu/KORStockScan/docs/low-price-two-leg-machines.md)
  - 구현: 2026-08-27 exact-date 경계에서 기존 entry 로직 7건과 신규 독립 profile 5건을 반영해 40→45개 세대로 전환한다. 2026-08-26 이하 조회는 40개 snapshot을 유지하며 기존 주문·보유 custody를 재해석하지 않는다.
  - 권한 경계: quantity, provider, main bot, broker/order guard, hard safety, 다른 owner 주문은 변경하지 않는다. 신규 profile은 same-day applied policy·evidence hash·manual owner·preflight authority가 모두 유효할 때만 시작한다.
  - 결과: PREOPEN read-only build는 `candidate_validated_profile_revision_applied`, 45 profiles, 12 evidence `ready`, applied payload `valid`를 반환했다. 신규 5개 profile의 preflight/live timer 10개를 포함한 90개 timer가 enabled·`NeedDaemonReload=no`이고 모두 2026-08-27 정확 시각을 가리킨다. 오늘 `kepco_afternoon`은 두 매수 10주 leg와 두 target order를 소유한 20주 `TARGET_OPEN` 정상 custody라 중지·취소하지 않았다. 표적 및 관련 525 tests, Ruff, format, compile, `bash -n`, systemd verify, parser, `git diff --check`가 모두 통과했고 최종 리뷰 finding은 0건이다.





## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
