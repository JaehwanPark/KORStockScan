# 2026-08-06 Stage2 To-Do Checklist

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

## 당일 완료 기록

- [x] `[WidgetDailyAutoCalibrationAndExpansionRecommendation0806] 세 종목 위젯 장후 누적 calibration·다음 거래일 자동 적용 및 확대 후보 관리자 추천` (`Due: 2026-08-06`, `Slot: INTRADAY`, `TimeWindow: 13:28~14:28`, `Track: ScalpingLogic`)
  - Source: [widget_advisory_calibration.py](/home/ubuntu/KORStockScan/src/engine/monitoring/widget_advisory_calibration.py), [widget_advisory_calibration_policy.py](/home/ubuntu/KORStockScan/src/engine/monitoring/widget_advisory_calibration_policy.py), [widget_collector_expansion_recommendation.py](/home/ubuntu/KORStockScan/src/engine/monitoring/widget_collector_expansion_recommendation.py), [korstockscan-samsung-widget-evaluation.service](/home/ubuntu/KORStockScan/deploy/systemd/korstockscan-samsung-widget-evaluation.service)
  - calibration: 삼성·두산·한화의 종목/세션별 exact entry-touch MFE/MAE와 10분 target/adverse first-hit을 매일 생성한다. 첫 유효 decisive outcome 1건부터 clean-baseline cumulative에 포함하고, 단일 bounded 축인 actionable 10초 연속확인 횟수를 `2~3` 범위·일 최대 1단계로 선택해 다음 KRX 거래일 날짜별 정책으로 원자 저장한다. 다음날 collector는 재기동 없이 최신 유효 정책을 읽고, 미래·손상 정책은 배제하며 report/source 결함이나 무표본은 직전 유효값을 자동 연장한다. 두산·한화 target은 전략 계약대로 `+1%`, 삼성은 `+0.5%`로 분리했다.
  - 확대 추천: 전일 실제 outcome-label 완료시각을 반영해 calibration과 분리된 21:15 timer가 최대 20 clean-baseline exact replay/payload 날짜에서 source-qualified portable widget signal/pre-spread 후보의 target/adverse, equal-weight EV, 유동성, 장중 범위, quote freshness를 결합한다. AI outcome만 좋고 portable widget 구조가 발생하지 않은 행은 제외한다. 기존 3종목·manual-control 제외 종목을 뺀 상위 5개를 `ADMIN_ID`에 일 1회 전송하며 `recommendation_only=true`, `collector_created=false`, `service_started=false`이므로 사용자 후속 지시 없이는 신규 collector/service를 생성하거나 기동하지 않는다.
  - 안전/적용: 두 자동화 모두 cached observation/report만 소비하며 Kiwoom·token·계좌·주문·실매매 bot/provider 경로를 호출하지 않는다. `widget_runtime_effect=true`인 날짜별 확인횟수 정책도 `trading_runtime_effect=false`, `runtime_effect=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`를 유지한다. `2026-08-06 14:26 KST` 검증된 systemd unit을 설치해 20:10 calibration과 21:15 recommendation timer를 enabled 처리하고, 읽기 전용 collector만 삼성→두산→한화 순서로 재기동했다. 새 PID는 `282255/282307/282333`, 모두 `active/running`, `NRestarts=0`, 최신 KRX snapshot `status=ok`, `source_quality=PASS`, `required_actionable_confirmations=2`, `runtime_effect=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`이다. 실매매 bot과 Gunicorn은 재기동하지 않았다.
  - 재리뷰 보완: 누적 rolling의 symbol/schema/authority/clean-baseline 검증, 평가 metric의 widget-only calibration 소비 계약, 휴장일 persistent catch-up 날짜 선택, 동일 날짜 stale report 대신 현재 in-memory report 사용, policy 파일명 대신 payload effective-date 우선순위, report 원자 기록 후 policy publish 순서를 보완했다. Collector의 10초 주기 정책 조회는 디렉터리 atomic publish가 감지될 때만 JSON을 다시 읽도록 캐시해 누적 이력 I/O 증가를 막았다. 확대 추천은 exact source contract와 portable widget 후보가 모두 성립한 행만 EV 표본으로 사용하고, 성과 선별을 먼저 수행해 탈락 종목 feature를 메모리에 보관하지 않는다. outcome-label/payload가 미생성·stale·authority 불일치이면 잘못된 `no candidate` Telegram을 보내지 않고 5분 간격·30분 내 최대 6회만 재시도한다.
  - 검증: widget/calibration/evaluation/replay/Telegram/API/location 회귀 `238 passed`, 실제 2026-08-05 calibration/recommendation dry-run, Black/Ruff/compile, systemd unit verify, checklist parser, `git diff --check`를 통과했으며 review-gate 최종 finding은 `0`이다.

- [x] `[WidgetMultipleEntryEpisodes0806] 두산·한화오션 위젯 일 1회 제한 해제 및 다회차 재무장 적용` (`Due: 2026-08-06`, `Slot: INTRADAY`, `TimeWindow: 11:48~12:00`, `Track: ScalpingLogic`)
  - Source: [doosan_widget_advisory.py](/home/ubuntu/KORStockScan/src/engine/monitoring/doosan_widget_advisory.py), [hanwha_ocean_widget_advisory.py](/home/ubuntu/KORStockScan/src/engine/monitoring/hanwha_ocean_widget_advisory.py), [tools/windows/README.md](/home/ubuntu/KORStockScan/tools/windows/README.md)
  - 구현: 거래일 첫 진입만 허용하던 tracker 제한을 제거하고 `multiple_non_overlapping_after_exit_and_new_bar_rearm` 계약으로 전환했다. 동시 활성 진입은 1회로 유지하며, 연계 청산 이벤트 만료·신선한 비진입 관측·청산 이후 새 확정 1분봉을 모두 확인한 뒤 다음 회차를 허용한다. 새 회차는 기존 2회 연속 10초 승격을 다시 통과하며 회차 번호가 포함된 고유 event id를 사용한다.
  - 호환/안전: 기존 오늘자 일 1회 snapshot은 `daily_entry_count=1`과 `rearm_required=true`로 보수적으로 복구한다. 삼성전자는 이미 비진입 재무장 후 다회차 신호가 가능해 로직을 변경하지 않았다. 세 종목 모두 관측 전용이며 주문·계좌·token 발급·실매매 runtime 권한은 추가하지 않는다.
  - 검증/적용: 리뷰에서 완료-재무장 불일치 snapshot과 `state=WATCH/raw_state=ENTRY_*` 승격대기 오인 가능성을 찾아 fail-closed로 보완했다. 삼성·두산·한화 widget/API/notifier/replay/location 회귀 `220 passed`, Black/Ruff, parser, 실제 한화오션 구 snapshot 마이그레이션을 통과했다. 두 독립 collector만 재기동해 두산 PID `178860`, 한화오션 PID `178862`, 양쪽 `active/running`, `NRestarts=0`, snapshot `status=ok`, `source_quality=PASS`, `token_mode=shared_cache_only`를 확인했다. 한화오션은 기존 1회차를 `daily_entry_count=1`로 보존하고 재무장됐으며 기존 Telegram entry/exit id 외 중복 발송은 없었다. 실매매 봇과 Gunicorn은 재기동하지 않았다.

- [x] `[ThreeSymbolWidgetReplayAndSamsungExitTelegramFix0806] 삼성·두산·한화오션 replay 재판정 및 삼성 EXIT_READY 관리자 알림 보완` (`Due: 2026-08-06`, `Slot: INTRADAY`, `TimeWindow: 09:38~09:50`, `Track: ScalpingLogic`)
  - Source: [samsung_widget_entry_notify.py](/home/ubuntu/KORStockScan/src/engine/monitoring/samsung_widget_entry_notify.py), [widget_mechanical_entry_replay.py](/home/ubuntu/KORStockScan/src/engine/monitoring/widget_mechanical_entry_replay.py), [samsung_widget_advisory_evaluation_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/samsung_widget_advisory_evaluation/samsung_widget_advisory_evaluation_2026-08-04.json), [widget_mechanical_entry_replay_2026-08-04.md](/home/ubuntu/KORStockScan/data/report/widget_mechanical_entry_replay/widget_mechanical_entry_replay_2026-08-04.md), [widget_mechanical_entry_replay_2026-08-05.md](/home/ubuntu/KORStockScan/data/report/widget_mechanical_entry_replay/widget_mechanical_entry_replay_2026-08-05.md)
  - replay 판정: 삼성 실제 widget 관측은 8/4 actionable 11개와 horizon 평가 63개가 있었으나 8/3·8/5는 mature actionable 표본이 없고 8/6은 장중 진행 중이므로 threshold 자동 조정 근거가 아니다. 두산 exact 10분 표본 3개는 모두 `adverse_first`, 한화오션 23개는 `adverse_first=9/neither=14`였으며 두 종목 모두 portable signal은 0개였다. 두산 pre-spread 1개와 한화 pre-spread 3개도 4~5틱 spread에서 차단돼 기존 2틱·거래량·확정지지 조건을 완화하지 않았다.
  - 청산 판정: 삼성 `EXIT_READY`는 8/5 2회와 8/6 장중 1회가 확인됐고 이후 하락 구간 관측과 방향이 일치했다. 메시지 누락 원인은 Telegram 전송 장애가 아니라 기존 notifier가 `EXIT_READY`를 `exit_advisory_conflict`로만 반환한 구현 공백이었다.
  - 보완: fresh `EXIT_READY` 계약·세션/venue·유효시각을 fail-closed 검증하고 관리자에게 회차당 1회 전송한다. entry/exit dedup·retry 상태를 분리했으며 보유·계좌·주문·실매매 runtime 권한은 추가하지 않았다. replay 리포트에는 종목코드별 signal/candidate/outcome/blocker cohort를 추가했다.
  - 검증: 세 위젯과 replay/location gate 회귀 `213 passed`, 실제 8/6 `EXIT_READY` payload 격리 전송 `exit_sent -> duplicate_exit_episode`, Black/Ruff/compile, checklist parser, `git diff --check`를 통과했으며 서비스 재기동은 수행하지 않았다.

- [x] `[HanwhaOceanWidgetFirstPullbackV1Implementation0806] 한화오션 KRX 첫 눌림 진입·연계청산·관리자 텔레그램 구현 및 리뷰` (`Due: 2026-08-06`, `Slot: INTRADAY`, `TimeWindow: 09:25~09:50`, `Track: ScalpingLogic`)
  - Source: [hanwha_ocean_widget_advisory.py](/home/ubuntu/KORStockScan/src/engine/monitoring/hanwha_ocean_widget_advisory.py), [hanwha_ocean_widget_telegram_notify.py](/home/ubuntu/KORStockScan/src/engine/monitoring/hanwha_ocean_widget_telegram_notify.py), [hanwha_ocean_price_widget_routes.py](/home/ubuntu/KORStockScan/src/web/hanwha_ocean_price_widget_routes.py), [korstockscan-hanwha-ocean-widget-collector.service](/home/ubuntu/KORStockScan/deploy/systemd/korstockscan-hanwha-ocean-widget-collector.service)
  - 판정: `HANWHA_OCEAN_VWAP_FIRST_PULLBACK_V1`은 KRX 확정 지지구조, VWAP 또는 직전 저항 회복, 표준 반등거래량, fresh BBO, 2회 연속 관측을 요구한다. 고정 가격·고정 세션낙폭·AI score를 쓰지 않고, 일 1회 진입 이벤트와 tick-rounded `+1%` 또는 후속 확정 1분봉 지지 이탈 청산 이벤트만 생성한다.
  - 안전 경계: 기존 cached Kiwoom token과 read-only `ka10001/ka10004/ka10080/ka10081`만 사용하며 `authority=widget_advisory_only`, `runtime_effect=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`를 유지한다. 주문·계좌·token issue/refresh·실매매 runtime·bot 제어 경로는 없다.
  - 배포 상태: 사용자 지시에 따라 `2026-08-06 09:52 KST` 두산·한화오션 독립 collector unit을 설치하고 `enabled/active`로 기동했다. 최초 PID는 각각 `91836/91837`, `NRestarts=0`이며 두 snapshot 모두 `status=ok`, KRX `source_quality=PASS`, `token_mode=shared_cache_only`, `runtime_effect=false`, `actual_order_submitted=false`로 10초 갱신을 확인했다. `10:08 KST` Gunicorn master `633`에 `SIGHUP`을 보내 시작 시각과 master를 유지하면서 worker를 `892/897 -> 102171/102208`로 교체했고 삼성·두산·한화 API route의 `401 unauthorized` 응답을 확인했다. 실매매 봇은 재기동하지 않았다. 두산과 한화오션은 모두 KRX 정규장 전용이며 NXT 세션 판정은 포함하지 않는다.
  - 검증: 한화오션·두산·삼성 widget 및 engine location gate 회귀 `161 passed`, Black/Ruff/compile, systemd unit verify, web route registration, checklist parser, `git diff --check`를 통과했으며 최종 미해결 finding=`0`이다.

- [x] `[PostcloseRiskBudgetExplorationReview0806] parent-count 과차단 분리 및 Swing-OFF tail 재검증` (`Due: 2026-08-06`, `Slot: PREOPEN`, `TimeWindow: 08:25~08:45`, `Track: ScalpingLogic`)
  - Source: [lifecycle_bucket_discovery_2026-08-05_rolling5d.json](/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-08-05_rolling5d.json), [lifecycle_bucket_discovery_2026-08-05_mtd.json](/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-08-05_mtd.json), [pattern_lab_currentness_audit_2026-08-05.json](/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-08-05.json), [pattern_lab_propagation_audit_2026-08-05.json](/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-08-05.json), [threshold_cycle_postclose_verification_2026-08-05.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-08-05.json)
  - 판정: clean source-quality와 positive EV가 있는 parent는 전체 parent 개수 목표 미달만으로 sim-only 탐색을 닫지 않는다. rolling5d/MTD에서 3개 seed가 bounded sim active로 복원됐고 real/live authority는 0건으로 유지됐다.
  - 안전 경계: parent granularity, complete lifecycle flow, source quality, entry-source taxonomy는 live conversion 필수 조건으로 유지하며 `runtime_effect=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`를 검증했다.
  - 산출물 순서: Swing-OFF currentness/workorder/propagation, gap audit, key lineage, conversion lane, rising prior/scout, EV, runtime summary, verifier 순으로 재생성했고 verifier는 stale/missing downstream 없이 warning으로 종료했다.
  - 잔여 warning: rolling5d/MTD parent granularity 27<30, limit-down ordered-path 자연 표본 없음, Entry ADM joined outcome 표본 부족. 이들은 sim 탐색 차단이나 실주문 완화 근거로 사용하지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-08-05` postclose -> `2026-08-06`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0806] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-08-06`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-05.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-05.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0806] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-08-06`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-08-05.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-08-05.json), [code_improvement_workorder_2026-08-05.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-05.json), [threshold_apply_2026-08-06.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-08-06.json), [threshold_runtime_env_2026-08-06.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-08-06.json), [threshold_runtime_env_verify_2026-08-06.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-08-06.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`1`, forced_scout_with_post_sell_count=`0`, post_sell_join_coverage_pct=`0`, outcome_coverage_state=`no_closed_outcome`, profitable_forced_scout_count=`0`, loss_or_flat_forced_scout_count=`0`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0806] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-08-06`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-05.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-05.json)
  - 전일 postclose candidate_selected_families=entry_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, scalping_pyramid_quality_gate, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0806] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-08-06`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-08-05.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-05.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0806] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-08-06`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-08-06.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-06.jsonl), [threshold_events_2026-08-06.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-06.jsonl), [observation_source_quality_audit_2026-08-06.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-06.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-08-06 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[PostcloseSourceQualityGateReview0806] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-08-06`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-08-06.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-06.json), [threshold_cycle_ev_2026-08-06.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-06.json), [code_improvement_workorder_2026-08-06.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-06.json), [threshold_cycle_postclose_verification_2026-08-06.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-08-06.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0806] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-08-06`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-05.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-05.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0806] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-08-06`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-05.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-05.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0806] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-08-06`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-08-05.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-08-05.md), [code_improvement_workorder_2026-08-05.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-05.json)
  - 판정 기준: selected_order_count=80와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0806] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-08-06`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-08-05.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-05.json), [runtime_apply_gap_audit_2026-08-05.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-05.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`251`, rollup_required_count=`251`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'exclusion_dimension_candidate': 1, 'parent_conflict_child': 2, 'positive_source_only_keep_collecting': 248}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0806] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-08-06`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-08-05.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-08-05.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`15`, run_count=`15`, skip_count=`0`, source_missing_count=`7`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:14, source_missing_or_unreadable:7, upstream_drift_signal:7, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## 수시 완료 기록

- [x] `[PostcloseAttributionCausalSplit0806] lifecycle/source-contract·submit drought·overbought 반사실 provenance 보완` (`Due: 2026-08-06`, `Slot: ADHOC`, `TimeWindow: 08:00~23:59`, `Track: ScalpingLogic`)
  - Source: [lifecycle_bucket_discovery.py](/home/ubuntu/KORStockScan/src/engine/lifecycle_bucket_discovery.py), [buy_funnel_sentinel.py](/home/ubuntu/KORStockScan/src/engine/buy_funnel_sentinel.py), [conversion_lane.py](/home/ubuntu/KORStockScan/src/engine/automation/conversion_lane.py), [entry_hurdle_backtest.py](/home/ubuntu/KORStockScan/src/engine/scalping/entry_hurdle_backtest.py)
  - 판정: canonical daily source-contract 비교, causal submit-drought axis만 blocker 귀속, incomplete lifecycle/source-quality 분리, executable-BBO+first-hit overbought promotion gate를 report/provenance 범위에서 구현했다.
  - 실제 재생성: BUY funnel causal axis=`UPSTREAM_GATE,BUDGET_PASS_COLLAPSE,LATENCY_PRE_SUBMIT,BROKER_RECEIPT`; conversion blocker는 submit drought `6 -> 4`, raw source-quality `28 -> 10`, lifecycle stage underproduction `0 -> 17`, total `50 -> 47`로 재귀속됐다. clean baseline 이후 entry hurdle은 43영업일·overbought 327건을 읽었고 executable BBO/first-hit/joint=`0/0/0`이라 runtime candidate는 열리지 않았다.
  - 금지 유지: threshold/provider/bot/broker/order/quantity/hard-safety 권한 변경 없음. 새 runtime instrumentation은 `runtime_effect=false`이며 현재 PID에는 재기동 전 미반영이다.

- [x] `[PostcloseRecoveryProfile0806] controller recovery 실행계약·Swing OFF·최종 EV 계보 보존` (`Due: 2026-08-06`, `Slot: ADHOC`, `TimeWindow: 08:00~23:59`, `Track: RuntimeStability`)
  - Source: [postclose_done_controller.py](/home/ubuntu/KORStockScan/src/engine/automation/postclose_done_controller.py), [verify_threshold_cycle_postclose_chain.py](/home/ubuntu/KORStockScan/src/engine/verify_threshold_cycle_postclose_chain.py)
  - 판정: recovery DONE marker가 직전 full-run execution flags를 상속하고, Swing 4개 축이 모두 OFF이면 workorder 재생성도 `--exclude-swing`을 유지하며 workorder 이후 final EV를 다시 생성한다.
  - 검증: controller/verifier 표적 테스트 `193 passed`; recovery artifact와 disabled-stage flag를 일반 source-quality/runtime 결함으로 오인하지 않는다.
  - 금지 유지: runtime/order/provider/cap/bot/hard-safety 권한 변경 없음.

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
