# 2026-07-31 Stage2 To-Do Checklist

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

- [ ] `[MarketGainerSixSlotRuntimeObserve0731] 키움 ka10027 시장상승 후보 rising_missed 6/12 할당 및 scanner→AI 도달률 확인` (`Due: 2026-07-31`, `Slot: INTRADAY`, `TimeWindow: 08:00~20:00`, `Track: ScalpingLogic`)
  - Source: [market_opportunity_census.py](/home/ubuntu/KORStockScan/src/engine/monitoring/market_opportunity_census.py), [scalping_scanner.py](/home/ubuntu/KORStockScan/src/scanners/scalping_scanner.py), [watch_budget.py](/home/ubuntu/KORStockScan/src/engine/scalping/watch_budget.py), [market_opportunity_census_2026-07-30.json](/home/ubuntu/KORStockScan/data/report/market_opportunity_census/market_opportunity_census_2026-07-30.json)
  - 판정 기준: KRX/PREMARKET은 `stex_tp=1`, NXT 및 16:00 직전 prewarm은 `stex_tp=2`인 ka10027 `liquid_common` 후보만 사용하고, 전체 SCALPING WATCHING cap=16과 rising_missed guaranteed=12를 유지한 채 `PREV_CLOSE_GAINER` active가 최대 6인지 확인한다. source unavailable·유효 후보 부족·source guard 거부 시 기존 WATCHING이 선제 만료되지 않아야 하며, 슬롯 교체는 기존 row 만료와 신규 row 저장이 같은 DB transaction에서 성공한 뒤에만 WS 해제가 발생해야 한다. 승격 후보는 `scanner_promoted → fast_precheck → heavy_eval → entry_ai_trace → entry_ai_provider_called → submitted`의 `forward_exact` 도달률과 최초 결손 단계를 venue별로 확인한다.
  - 금지: ka10027 포함만으로 BUY를 확정하거나 threshold/provider/order/quantity/broker guard/bot cap을 변경하지 않는다. 보유·매수·비-SCANNER WATCHING은 6석 재배치 대상으로 삼지 않고, `same_day_*_retrospective`는 비인과 진단으로만 사용한다.
  - 다음 액션: `six_slot_allocation_observed`, `eligible_source_under_six_borrow_retained`, `source_unavailable_no_eviction`, `scanner_discovery_gap`, `scanner_heavy_eval_gap`, `entry_ai_preflight_or_transport_block`, `post_ai_or_submit_gap` 중 하나로 종목·venue별 귀속을 닫는다.
  - 08:45 중간 증거: `PREMARKET_KRX_LIKE` 구간의 76개 관련 관측 row에서 `scanner_market_gainer_active_count` 최대값과 reserved promotion은 모두 0이었다. 정규장 ka10027 자연 표본 전이므로 `natural_sample_missing`으로 유지한다. 전체 scanner heavy queue 3,471건의 wait 중앙값은 0.205초, p95는 0.533초, 최대값은 2.713초로 queue starvation 근거는 없었다.

- [ ] `[DatedRuntimeAutoRenewUtilityObserve0731] 자동연장 dated runtime 실제 호출·EV·순이익 효용성 검증` (`Due: 2026-07-31`, `Slot: INTRADAY`, `TimeWindow: 08:00~20:00`, `Track: RuntimeStability`)
  - Source: [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [operator_runtime_overrides_2026-07-31.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/operator_runtime_overrides_2026-07-31.env), [intraday-monitoring-task-instructions.md](/home/ubuntu/KORStockScan/docs/intraday-monitoring-task-instructions.md)
  - 판정 기준: 현재 PID env의 `KORSTOCKSCAN_DATED_RUNTIME_AUTO_RENEW_POLICY_VERSION=dated_runtime_auto_renew_v1`, target date, active key 목록·개수를 launcher log 및 당일 override와 대조한다. 각 active key를 실제 소비 family/stage에 연결해 eligible 표본, 호출·pass·block·defer·recheck·submit·exit 수, source quality, 1·3·5·10·20·30·60분 MFE/MAE, target/adverse first-hit, 실현손익·슬리피지·수수료와 `source_quality_adjusted_ev_pct`를 KRX/`PREMARKET_KRX_LIKE`/NXT별로 평가한다. source-only sampler는 주문효과와 분리해 coverage와 downstream attribution을 본다.
  - 금지: `enabled=true` 또는 로그 존재만으로 효용성을 확정하지 않는다. 자동연장을 threshold/provider/order/quantity/cap/broker/hard-safety 변경 권한으로 사용하지 않고, 서로 다른 family의 실현손익과 counterfactual을 합산하지 않는다.
  - 다음 액션: 각 runtime을 `effect_confirmed`, `neutral`, `natural_sample_missing`, `hook_or_input_defect`, `profit_harm_explicit_off_rollback`, `safety_or_provenance_explicit_off_rollback` 중 하나로 닫는다.
  - 08:45 중간 증거: PID 20630은 26개 dated family의 당일 활성값을 소비했지만 `KORSTOCKSCAN_DATED_RUNTIME_AUTO_RENEW_POLICY_VERSION`, target date, active key 목록·개수 provenance가 없었다. 원인은 07:55에 적재된 장수명 parent launcher가 08:03 이후의 `run_bot.sh` 소스를 다시 읽지 않은 채 08:04:41 child만 재실행한 것이며, child의 `KORSTOCKSCAN_RUNTIME_GIT_COMMIT`만으로 launcher 반영을 증명할 수 없었다. `run_bot.sh`에 launcher load 시점 commit·SHA256·시각 provenance를 추가했고 targeted wrapper tests와 `bash -n`, `git diff --check`를 통과했다. 현재 PID에는 미반영이므로 종일 효용 판정은 OPEN으로 유지한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-07-30` postclose -> `2026-07-31`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0731] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-07-31`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-30.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-30.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0731] rising_missed_scout_workorder 구현분 다음 장전 runtime 반영 여부 확인` (`Due: 2026-07-31`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-07-30.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-07-30.json), [rising_missed_normal_buy_bridge_candidate_discovery_2026-07-30.json](/home/ubuntu/KORStockScan/data/report/rising_missed_normal_buy_bridge_candidate_discovery/rising_missed_normal_buy_bridge_candidate_discovery_2026-07-30.json), [code_improvement_workorder_2026-07-30.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-30.json), [threshold_apply_2026-07-31.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-07-31.json), [threshold_runtime_env_2026-07-31.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-31.json), [threshold_runtime_env_verify_2026-07-31.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-31.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`2`, forced_scout_with_post_sell_count=`1`, profitable_forced_scout_count=`0`, loss_or_flat_forced_scout_count=`1`, current_missed_count=`0`)과 `rising_missed_normal_buy_bridge_candidate_discovery` 요약(status=`source_missing`, bridge_candidate_count=`0`, code_improvement_order_count=`0`, runtime_env_key=`KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED`)을 함께 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder`/bridge discovery 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0731] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-07-31`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-30.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-30.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, entry_split_order_plan, scale_in_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, lifecycle_decision_matrix_runtime, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0731] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-07-31`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-07-30.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-30.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0731] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-07-31`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-07-31.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-31.jsonl), [threshold_events_2026-07-31.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-07-31.jsonl), [observation_source_quality_audit_2026-07-31.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-31.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-07-31 --write --print-summary` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다. 전체 JSON은 artifact에서 읽고 장중 stdout에는 중복 출력하지 않는다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

- [x] `[IntradayWsIncrementalResourceVerify0731] WS freshness 증분 상태 재사용 및 CPU/RSS 절감 확인` (`Due: 2026-07-31`, `Slot: INTRADAY`, `TimeWindow: 12:45~13:15`, `Track: RuntimeStability`)
  - Source: [intraday_ws_freshness_monitor.py](/home/ubuntu/KORStockScan/src/engine/monitoring/intraday_ws_freshness_monitor.py), [run_intraday_ws_freshness_monitor.sh](/home/ubuntu/KORStockScan/deploy/run_intraday_ws_freshness_monitor.sh), [intraday_ws_freshness_monitor_2026-07-31.json](/home/ubuntu/KORStockScan/data/report/intraday_ws_freshness_monitor/intraday_ws_freshness_monitor_2026-07-31.json)
  - 판정 기준: 최초 `full_streaming_rebuild` 이후 다음 자연 실행이 `input_processing.mode=incremental_streaming_aggregation`, `incremental_state_reason=state_reused`, `appended_event_count < aggregated_event_count`로 닫히고 실행시간·RSS가 full rebuild보다 감소하는지 확인한다.
  - 금지: 검증을 위해 cooldown을 우회해 장중 full rebuild를 강제하지 않는다. 결과로 stale submit/broker/order/threshold/provider/bot 동작을 변경하지 않는다.
  - 다음 액션: `incremental_reuse_effect_confirmed`, `state_rebuild_expected_first_run`, `unexpected_state_invalidation`, `resource_reduction_not_confirmed` 중 하나로 닫는다.
  - 판정: `incremental_reuse_effect_confirmed`. 12:45 최초 상태 생성 실행은 약 33초, 13:05·13:20 자연 증분 실행은 각각 약 4초였다. 13:20 report는 `mode=incremental_streaming_aggregation`, `incremental_state_reason=state_reused`, `aggregated_event_count=201773`, `appended_event_count=11001`, `memory_bounded_streaming=true`, `full_event_list_materialized=false`를 기록했다.

## 장후 체크리스트 (20:05~21:55)

- [x] `[FullMonitorSnapshotMemoryBound0731] 자동 full monitor snapshot JSONL 전량 적재·swap 압박 해소` (`Due: 2026-07-31`, `Slot: POSTCLOSE`, `TimeWindow: 15:45~16:15`, `Track: RuntimeStability`) (`실행: 2026-07-31 16:09 KST`)
  - Source: [dashboard_data_repository.py](/home/ubuntu/KORStockScan/src/engine/dashboard_data_repository.py), [sniper_performance_tuning_report.py](/home/ubuntu/KORStockScan/src/engine/sniper_performance_tuning_report.py), [bot_main.py](/home/ubuntu/KORStockScan/src/bot_main.py), [system_metric_samples.jsonl](/home/ubuntu/KORStockScan/logs/system_metric_samples.jsonl)
  - 판정: `resolved_code_pending_runtime_reflection`. 15:45 구 구현은 2.94GB `pipeline_events`를 전량 list 적재해 RSS 약 5.2GB와 process swap 약 2.9GB를 사용했고 가용 메모리를 458.5MB까지 낮췄다. canonical iterator와 performance 필드 투영으로 변경한 exact-date replay는 274,192건, 16.5초, peak RSS 345MB, swap 0으로 통과했다.
  - 안전 경계: snapshot payload/report 지표 계약과 기존 list API를 유지하며 BUY/SELL, provider, threshold, broker/account/order/quantity/cooldown, hard/protect/emergency 동작은 변경하지 않는다. 스케줄러는 stale manifest 수용 회귀를 막기 위해 당일 15:45 full freshness 강제 생성 계약을 유지하고 stage I/O delay 1초를 적용한다.
  - 검증: 관련 pytest 159건, Ruff, Black, py_compile, `git diff --check` 통과. 최종 graceful restart PID 442973(16:34 시작)은 streaming/projection과 scheduler I/O delay·freshness 보완을 모두 반영했고 runtime env verify, 계좌 reconciliation, WS 로그인, OpenAI main route가 통과했다. 리소스 detector는 16:08 `pass`로 회복했다.

- [x] `[PipelineEventDiskGrowthBound0731] 고빈도 pipeline event 중복 text 및 producer summary 용량 제한` (`Due: 2026-07-31`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:40`, `Track: RuntimeStability`) (`실행: 2026-07-31 18:30 KST`)
  - Source: [pipeline_event_logger.py](/home/ubuntu/KORStockScan/src/utils/pipeline_event_logger.py), [pipeline_event_summary.py](/home/ubuntu/KORStockScan/src/engine/pipeline_event_summary.py), [pipeline_event_verbosity_report.py](/home/ubuntu/KORStockScan/src/engine/pipeline_event_verbosity_report.py), [pipeline_events_2026-07-31.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-31.jsonl)
  - 판정: `resolved_code_pending_runtime_reflection`. 실주문·체결·exit·safety·source-quality/provenance raw `fields`와 suppression OFF 계약은 유지하고, 용량 상위 11개 observation stage의 중복 `text_payload`만 `diagnostic_compact_v1`으로 투영했다. 동일상태는 기존 5초 producer shadow bucket에서 집계되며 high-volume summary는 필수 진단 필드만 `high_volume_diagnostic_v1`으로 보존한다.
  - replay: 최근 real payload 10,000행에서 text projection은 106,970,533 bytes를 65,986,926 bytes로 줄여 38.31% 절감했고, high-volume 8,849건은 5,432개 summary row로 집계되어 dedupe 38.61%, compact summary 21,436,821 bytes였다. summary 비용 포함 순저장 절감 추정은 약 18%이며 raw suppression은 적용하지 않았다.
  - 안전 경계: BUY/SELL, provider, threshold, broker/account/order/quantity/cooldown, hard/protect/emergency 동작과 raw structured fields를 변경하지 않는다. `suppress` 전환은 최소 2영업일 parity와 별도 workorder/approval 전까지 금지한다.
  - 20:10 추가 결함보완: postclose immutable snapshot이 4.38GB 원본을 plain `cp --reflink=auto`로 복제하다 root filesystem을 100% 소진하고 2.97GB orphan을 남겼다. snapshot owner를 atomic gzip stream으로 변경하고 checkpoint 없는 orphan 및 실패 임시파일을 재시도 전에 정리하도록 보완했다. 이는 저장/수집 경로만 변경하며 raw source와 tuning 계약은 유지한다.

- [x] `[CleanBaselineRetirement0604To0605] 가장 오래된 clean-baseline 일자 폐기 및 기준일 전환` (`Due: 2026-07-31`, `Slot: POSTCLOSE`, `TimeWindow: 20:20~20:40`, `Track: RuntimeStability`) (`실행: 2026-07-31 20:29 KST`)
  - Source: [clean_baseline_policy.json](/home/ubuntu/KORStockScan/data/source_quality/clean_baseline_policy.json), [observation_source_quality_audit_2026-06-05.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-05.json), [threshold_cycle_postclose_verification_2026-06-05.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-06-05.json)
  - 판정: `resolved_runtime_effect_false`. 2026-06-05 source-quality audit는 `status=pass`, `tuning_input_allowed=true`, hard contract gap/unknown token 0건이며 postclose verification도 PASS다. clean baseline을 `2026-06-05T00:00:00+09:00`으로 이동하고 정책·fallback·패턴랩·운영문서를 함께 현행화했다.
  - 삭제: 진행 중이던 2026-07-31 threshold postclose 프로세스가 `paused_by_chunk_limit`로 종료되고 관련 open handle이 없음을 확인한 뒤, 이름에 `2026-06-04` 또는 `20260604`가 귀속된 최상위 191경로/내부 890파일/1,255,234,608 bytes를 삭제했다. 날짜가 파일명에 없지만 내용상 6월 4일부터 집계된 pattern-lab 최신 출력 5개도 stale 재소비를 막기 위해 삭제했다. 6월 4일 단일일 raw/report/analytics뿐 아니라 구 baseline 시작일을 포함한 파생 리포트도 제거했으며 별도 백업 없이는 복구할 수 없다.
  - 안전 경계: runtime/order/provider/broker/threshold/bot 상태는 변경하지 않았다. 실행 중이던 7월 31일 postclose 실패는 baseline 전환 이전 compact backfill chunk 완료 계약 문제이며 이번 변경으로 재실행하거나 우회하지 않는다.

- [x] `[ThresholdSnapshotCompressedRetry0731] 실패 orphan 정리 후 gzip snapshot 기반 postclose 재실행 확인` (`Due: 2026-07-31`, `Slot: POSTCLOSE`, `TimeWindow: 20:15~21:55`, `Track: RuntimeStability`) (`실행: 2026-08-01 02:06 KST`)
  - Source: [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh), [threshold_cycle_postclose_2026-07-31.status.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_2026-07-31.status.json), [pipeline_events_2026-07-31.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-31.jsonl)
  - 판정 기준: checkpoint 없는 20:10 orphan이 정리되고 `.jsonl.gz` snapshot이 atomic rename으로 완성되어 `backfill_threshold_cycle_events`가 같은 compressed source를 소비하며 controller가 최종 `DONE`을 표시하는지 확인한다. 실행 전 root filesystem 여유와 gzip 예상 용량을 확보하고, 실패 시 `.tmp.<pid>`가 남지 않아야 한다.
  - 금지: 원본 pipeline event 삭제, clean-baseline 증거 삭제, provider=none, source-quality/verify 우회, bot 자동 재기동, broker/order/threshold/quantity guard 변경으로 복구하지 않는다.
  - 다음 액션: `compressed_snapshot_postclose_done`, `insufficient_space_before_retry`, `compressed_source_consumer_failure`, `postclose_downstream_failure` 중 하나로 닫는다.
  - 판정: `compressed_snapshot_postclose_done`. compressed source를 소비한 threshold recovery와 downstream 산출물 재생성이 종료됐고, postclose verifier는 필수 산출물·downstream link·stale link·source generation 결손 0건으로 exit 0을 반환했다. 허용된 source-only 경고를 보존한 controller 재실행은 2026-08-01 02:06 KST에 최종 `DONE`을 표시했으며 AI correction/one-share review는 OpenAI parsed/reused-valid 상태를 유지했다.

- [ ] `[FullMonitorSnapshotMemoryPostApply0803] 다음 자동 15:45 full snapshot 메모리·완료 artifact post-apply 확인` (`Due: 2026-08-03`, `Slot: POSTCLOSE`, `TimeWindow: 15:45~16:10`, `Track: RuntimeStability`)
  - Source: [monitor_snapshot_manifest_2026-07-31_full.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/manifests/monitor_snapshot_manifest_2026-07-31_full.json), [monitor_snapshot_runtime.py](/home/ubuntu/KORStockScan/src/engine/monitor_snapshot_runtime.py), [error_detection_2026-07-31.json](/home/ubuntu/KORStockScan/data/report/error_detection/error_detection_2026-07-31.json)
  - 판정 기준: 수정 반영 PID에서 자동 full snapshot이 timeout 없이 completion/manifest를 fresh success로 닫고, worker peak RSS 500MB 이하, swap-in/out 급증 없음, `resource_usage=pass` 또는 일시 warning 후 즉시 회복인지 확인한다.
  - 금지: post-apply 검증을 위해 장중 full rebuild를 강제하거나 cooldown/lock, broker/order/provider/threshold/bot safety를 우회하지 않는다.
  - 다음 액션: `memory_bound_effect_confirmed`, `artifact_success_memory_warning`, `timeout_or_stale_completion_defect`, `runtime_not_reflected` 중 하나로 닫는다.

- [ ] `[PipelineEventDiskGrowthPostApply0803] 고빈도 pipeline event projection·shadow parity 자연 표본 확인` (`Due: 2026-08-03`, `Slot: INTRADAY`, `TimeWindow: 08:00~15:20`, `Track: RuntimeStability`)
  - Source: [pipeline_event_logger.py](/home/ubuntu/KORStockScan/src/utils/pipeline_event_logger.py), [pipeline_event_summary.py](/home/ubuntu/KORStockScan/src/engine/pipeline_event_summary.py), [pipeline_event_verbosity_2026-08-03.json](/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-08-03.json)
  - 판정 기준: 수정 반영 PID에서 high-volume observation raw `fields`가 lossless로 유지되고 compact `text_payload`가 생성되는지 확인한다. 시간당 raw 증가량, producer summary 크기, 동일상태 dedupe율, V1 raw-derived/producer stage·reason parity를 측정해 기존 약 300MB/시간 대비 순저장 감소와 `raw_suppression_enabled=false`를 함께 확인한다.
  - 금지: 자연 표본 없이 suppress를 켜거나 주문·체결·exit·safety·source-quality/provenance event를 throttle하지 않는다. summary count를 실주문 품질·EV·threshold/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `disk_growth_reduction_confirmed`, `text_projection_effect_only`, `summary_overhead_regression`, `shadow_parity_fail`, `runtime_not_reflected` 중 하나로 닫는다.

- [x] `[PostcloseSourceQualityGateReview0731] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-07-31`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`) (`실행: 2026-08-01 02:03 KST`)
  - Source: [observation_source_quality_audit_2026-07-31.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-31.json), [threshold_cycle_ev_2026-07-31.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-31.json), [code_improvement_workorder_2026-07-31.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-31.json), [threshold_cycle_postclose_verification_2026-07-31.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-07-31.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.
  - 판정: `source_quality_gate_pass_with_review_warning`. 406,281 events 재감사 결과 hard blocking contract gap 0건, tuning input allowed=true이며 reviewed unknown stage는 86건, 미해결 unknown-token stage는 24건이다. 신규 producer/provenance 보완은 runtime_effect=false로 제한했고 generic unknown workorder는 `implemented_but_waiting_sample` existing-family로 재분류했다. unknown은 review warning으로 보존하되 live/runtime 승인 근거로 사용하지 않는다.

- [x] `[IntradayHeavyAnalysisSerialization0731] 리소스 경보 원인 분리 및 무거운 장중 분석 직렬화` (`Due: 2026-07-31`, `Slot: INTRADAY`, `TimeWindow: 14:45~15:10`, `Track: RuntimeStability`)
  - Source: [system_metric_sampler.py](/home/ubuntu/KORStockScan/src/engine/monitoring/system_metric_sampler.py), [resource_usage.py](/home/ubuntu/KORStockScan/src/engine/error_detectors/resource_usage.py), [run_rising_missed_intraday_feedback.sh](/home/ubuntu/KORStockScan/deploy/run_rising_missed_intraday_feedback.sh), [run_scalping_pyramid_intraday_feedback.sh](/home/ubuntu/KORStockScan/deploy/run_scalping_pyramid_intraday_feedback.sh), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정: 14:52 `cpu_busy_pct=97.96` 표본은 `iowait_pct=51.76`이 포함된 non-idle 값이었다. sampler는 호환 필드를 유지하면서 compute busy와 I/O wait를 분리하고, detector는 두 병목을 독립 판정한다. rising-missed, pyramid, source-quality full audit는 공용 non-blocking heavy-analysis lock으로 직렬화하며 busy skip은 성공 artifact로 오인되지 않도록 audit에서 exit 75로 닫는다.
  - 안전 경계: report/source-quality 전용 변경이며 BUY/SELL, provider, threshold, broker/account/order/quantity/cooldown, hard/protect/emergency 및 bot process state는 변경하지 않는다. source-quality audit의 report 직렬화가 끝날 때까지 공용 lock을 유지한다.

- [x] `[ThresholdDailyEVReport0731] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-07-31`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`) (`실행: 2026-08-01 06:56 KST`)
  - Source: [tuning_performance_control_tower_2026-07-31.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-07-31.json), [threshold_cycle_ev_2026-07-31.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-31.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.
  - 판정: `daily_ev_ready_with_warning`. source-quality tuning input allowed=true, real/sim sample=`26/12`, real outcome joined sample=`105`, primary verdict=`real_primary_evidence_present`로 생성되었다. live-auto ready=0은 계약·표본 블로커로 유지하며 본 리포트 자체는 runtime_effect=false이다.

- [x] `[HumanInterventionSummary0731] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-07-31`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`) (`실행: 2026-08-01 06:56 KST`)
  - Source: [threshold_cycle_ev_2026-07-31.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-31.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.
  - 판정: `observe_only_no_human_intervention`. approval_requests=0, operator_action_required=false, human_intervention_required=false이며 누락된 승인 artifact나 추가 사용자 개입 요구는 없다.

- [x] `[CodeImprovementWorkorderReview0731] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-07-31`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`) (`실행: 2026-08-01 02:03 KST`)
  - Source: [code_improvement_workorder_2026-07-31.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-07-31.md), [code_improvement_workorder_2026-07-31.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-31.json)
  - 판정 기준: selected_order_count=72와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.
  - 판정: `already_implemented_and_keep_visible_by_design`. pass-0 selected 78건 중 runtime_effect=false `implement_now` 4건을 instrumentation/report/provenance 범위로 구현·재리뷰하고 관련 리포트를 재생성했다. 최종 selected 74건은 전부 `attach_existing_family`, selected implement_now/미구현 runtime_effect=false/needs-followup/repeat structural blocker는 각각 0건이다. unknown provenance 1건은 non-selected existing implementation waiting sample로 이동했고 pattern-lab 3건은 재판정으로 제거됐다. 장기 non-implement 4건은 action-required 없이 `keep_visible_by_design`, conversion-lane 20건은 구현 누락이 아니라 자연 lifecycle/PREOPEN attribution을 기다리는 `handoff_closed_root_cause_open`으로 유지한다.

- [x] `[LifecycleQuietGapReview0731] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-07-31`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`) (`실행: 2026-08-01 06:56 KST`)
  - Source: [runtime_apply_gap_audit_2026-07-31.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-31.json), [runtime_apply_gap_audit_2026-07-31.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-31.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`138`, rollup_required_count=`138`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 137}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.
  - 판정: `rollup_only`. quiet gap/rollup=`245/245`, actionable unknown gap=0, Codex directive=0, retry queue=0으로 자동 표면화가 닫혔다. 장기 non-implement 4건은 action-required 없는 `keep_visible_by_design`으로 유지한다.

- [x] `[AutomationTriggerDecisionSummary0731] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-07-31`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`) (`실행: 2026-08-01 06:56 KST`)
  - Source: [automation_chain_trigger_decision_2026-07-31.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-07-31.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`16`, run_count=`15`, skip_count=`1`, source_missing_count=`4`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`scalp_sim_ai_deferred_review`, top_reasons=`upstream_drift_signal:10, upstream_artifact_newer:7, output_missing_or_unreadable:6, source_missing_or_unreadable:4, fresh_outputs_no_trigger:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.
  - 판정: `trigger_contract_pass`. total/run/skip=`16/15/1`, force override=0이며 `scalp_sim_ai_deferred_review`는 fresh output으로 정상 skip되었다. source missing 7건은 필요 producer/audit run으로 라우팅되었고 최종 required artifact 누락으로 전이되지 않았다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->



## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
