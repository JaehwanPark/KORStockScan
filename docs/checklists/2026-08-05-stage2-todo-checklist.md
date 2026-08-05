# 2026-08-05 Stage2 To-Do Checklist

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

## 사용자 지시 구현

- [x] `[DoosanWidgetFirstPullbackV1Implementation0805] 두산에너빌리티 KRX 일 1회 진입·연계청산·관리자 텔레그램 구현 및 리뷰` (`Due: 2026-08-05`, `Slot: POSTCLOSE`, `TimeWindow: 16:55~17:30`, `Track: ScalpingLogic`)
  - Source: [doosan_widget_advisory.py](/home/ubuntu/KORStockScan/src/engine/monitoring/doosan_widget_advisory.py), [doosan_widget_telegram_notify.py](/home/ubuntu/KORStockScan/src/engine/monitoring/doosan_widget_telegram_notify.py), [doosan_price_widget_routes.py](/home/ubuntu/KORStockScan/src/web/doosan_price_widget_routes.py), [korstockscan-doosan-widget-collector.service](/home/ubuntu/KORStockScan/deploy/systemd/korstockscan-doosan-widget-collector.service)
  - 판정 기준: clean baseline KRX replay에서 train/holdout 모두 양수였던 세션 낙폭 `-0.50%` 이하·표준 반등거래량을 V1 기본군으로 사용하고, `-1.00%` 이하를 high-confidence로 분리한다. 두 번의 10초 확인, 일 1회 진입 episode, `+1%` 또는 진입 당시 구조지지의 이후 확정 1분봉 종가 이탈 청산, stable event-id 기반 관리자 텔레그램 중복방지·재시도를 검증한다.
  - 금지: absorption-only 표본의 V1 진입 승격, intrabar 저가 터치만으로 지지이탈 청산, 상대강도/외부시장 결측을 허위 양성근거로 사용, AI·실주문·계좌·수량·provider·bot 권한 연결, 신규 Kiwoom token 발급을 금지한다.
  - 구현 결과: `DOOSAN_FIRST_PULLBACK_V1`을 KRX 정규장 전용 별도 collector/API로 구현했다. 캐시 토큰의 `ka10001·ka10004·ka10080·ka10081` 읽기만 허용하고, entry/exit event 모두 `widget_advisory_only`, `runtime_effect=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`로 고정했다. 텔레그램은 `ADMIN_ID` 전용이며 entry 종료 뒤 지연 entry 발송을 차단한다. trading bot과 기존 Samsung collector는 재기동하지 않는다.
  - 공식 참조: Kiwoom upstream `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`의 `kiwoom_docs/종목정보.md`, `kiwoom_docs/차트.md`, `kiwoom/specs.py`, `kiwoom/core`, Postman collection을 `2026-08-05T16:55:23+09:00`에 확인했다.
  - 검증 결과: 두산 단위·route·notification·cached-token-only, 기존 Samsung widget, engine location gate까지 확대 회귀 `143 passed`; Black, Ruff, compile, systemd unit verify, web route registration, checklist parser(`27` open), `git diff --check`를 통과했다. 1차 리뷰의 전용키 우선순위·만료 event 노출, 2차 리뷰의 continuity 손상 복원·portable caution 우회·venue/profile 계약 결손, 최종 리뷰의 invalid actionable episode 선점 결함을 보완했으며 최종 미해결 finding=`0`이다.

- [x] `[FullMonitorSnapshotMemoryBound0805] 15:45 full monitor snapshot 구조적 메모리·재시도 보완 및 재검증` (`Due: 2026-08-05`, `Slot: INTRADAY`, `TimeWindow: 15:45~16:20`, `Track: RuntimeStability`)
  - Source: [sniper_missed_entry_counterfactual.py](/home/ubuntu/KORStockScan/src/engine/sniper_missed_entry_counterfactual.py), [log_archive_service.py](/home/ubuntu/KORStockScan/src/engine/log_archive_service.py), [run_monitor_snapshot_safe.sh](/home/ubuntu/KORStockScan/deploy/run_monitor_snapshot_safe.sh), [run_monitor_snapshot.log](/home/ubuntu/KORStockScan/logs/run_monitor_snapshot.log)
  - 판정 기준: 자동 full snapshot 6종과 manifest 생성을 유지하면서 multi-GB pipeline 입력을 전체 materialize하지 않고, stage별 start/complete·duration·process max RSS를 남긴다. 실제 당일 source dry build peak RSS가 장애 당시보다 유의하게 낮고 targeted/full profile 검증이 완료돼야 한다.
  - 금지: 자동 snapshot 중지·산출물 생략, live bot 종료·재기동, 주문/threshold/provider/runtime authority 변경, timeout/OOM/SIGTERM 직후 동일 workload 연속 재시도를 금지한다.
  - 원인·보완 (`2026-08-05 15:45~16:16 KST`): 2.18GB pipeline JSONL 전체 materialize와 전 필드 복사, missed-entry의 전 종목 분봉 cache 누적, holding-exit의 동일 원본 list materialize가 순차적으로 RSS를 약 5.3GB까지 키운 구조적 원인이었다. 이를 compact streaming field projection, 종목 전환 시 이전 candle release, streaming counter projection으로 교체했다. stage별 start/complete·duration·process max RSS를 남기고 timeout/OOM/SIGKILL/SIGTERM은 즉시 동일 workload를 재시도하지 않도록 completion evidence를 보존했다.
  - 실제 full 검증: 변경 코드로 16:12:26~16:16:10에 full profile 6종과 manifest를 모두 재생성했다(`duration_sec=223.938`). process max RSS는 `1,276,308KB`로 장애 시 약 5.3GB 대비 약 76% 감소했고, missed-entry 메타는 pipeline 2,175,561,577 bytes·369,983 compact events·candle fetch 163건·최대 보존 종목 1개, holding-exit 메타는 pipeline 373,943행·`pipeline_event_full_source_materialized=false`를 확인했다. live bot PID `262970`은 종료·재기동 없이 heartbeat를 유지했고 완료 뒤 available memory는 약 5.5GB였다. 진단 중 부모 wrapper가 먼저 종료돼 남은 `dispatched` completion은 성공 result/manifest를 표준 normalizer로 대조해 `success`, snapshot count 6으로 복구했다.
  - 리뷰·검증: completion normalizer와 관리자 알림 consumer가 새 `stage_metrics`를 snapshot으로 세어 7건으로 표시하는 자체리뷰 finding을 추가 보완했다. 관련 회귀 `90 passed`, Black, Ruff, compile, shell syntax, checklist parser, `git diff --check` 통과와 재리뷰 미해결 finding=`0`을 최종 조건으로 닫는다. 주문·threshold·provider·runtime authority와 bot 상태는 변경하지 않았다.

- [x] `[SmoothingBoundedExploration0805] smoothing 유효기회 탐색·trailing one-shot attribution 보완 및 리뷰` (`Due: 2026-08-05`, `Slot: INTRADAY`, `TimeWindow: 12:00~12:30`, `Track: ScalpingLogic`)
  - Source: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py), [threshold_cycle_registry.py](/home/ubuntu/KORStockScan/src/utils/threshold_cycle_registry.py)
  - 판정 기준: OFI action smoothing, soft-stop confirmation, protect-trailing smoothing은 현행 threshold를 바꾸지 않는 report-only parameter grid로 유효 전환 노출을 넓히고 forward outcome EV join 전에는 runtime 권한을 열지 않는다. `scalp_trailing_continuation_recheck`는 동일 포지션당 1회만 arm하고 TTL/veto·deadline lag·즉시 청산 counterfactual·실제 완료손익을 compact threshold report까지 연결한다.
  - 금지: grid 노출 count만으로 live apply, hard/protect/emergency stop 지연, stale/conflict·broker/order guard 우회, provider·수량·cap·bot 변경, 두 번째 trailing 연장을 금지한다.
  - 실행 결과 (`2026-08-05 12:30 KST`): OFI raw/smooth/regime/action provenance와 protect/soft-stop grid 입력 필드를 compact event에 보존하고, 세 grid를 `runtime_effect=false`, `allowed_runtime_apply=false`, `broker_order_forbidden=true`로 daily/cumulative snapshot에 연결했다. trailing recheck는 포지션 key·recheck id·min/max profit·counterfactual price/profit·deadline lag를 남기며, 동일 포지션의 재연장은 차단 provenance를 1회만 기록한다. record·실행가능 counterfactual 청산가·completed valid profit이 모두 연결된 표본만 `source_quality_adjusted_ev_pct`에 포함하고 record가 없는 arm은 false one-shot violation이 아니라 attribution 제외로 처리한다.
  - 검증 결과: 1차 관련 회귀 `374 passed` 뒤 자체리뷰에서 반복 차단 로그 오염, record 결손 arm의 false violation, 실행가능 counterfactual 청산가 없는 행의 EV 유입 가능성을 발견해 보완했다. OFI·holding override·daily/EV/postclose threshold 소비자까지 확대한 최종 회귀 `605 passed`, Black, Ruff, compile, checklist parser(`28` open), `git diff --check`를 통과했고 재리뷰 미해결 finding=`0`이다.
  - 후속 상태: 사용자 승인 우아한 재기동으로 아래 `SmoothingAttributionRuntimeObserve0805`가 clean-runtime 반영까지 닫혔다. 자연 arm/terminal/차단 표본은 아직 없어 장후 daily/cumulative attribution에서 이어 확인한다.

- [x] `[SmoothingAttributionRuntimeObserve0805] smoothing attribution 신계약 자연 관찰` (`Due: 2026-08-05`, `Slot: INTRADAY`, `TimeWindow: 12:30~15:20`, `Track: ScalpingLogic`)
  - Source: [pipeline_events_2026-08-05.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-05.jsonl), [threshold_events_2026-08-05.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-05.jsonl), [error_detector_heartbeat.json](/home/ubuntu/KORStockScan/tmp/error_detector_heartbeat.json)
  - 판정 기준: 별도 승인된 다음 우아한 재기동이 있는 경우에만 변경 소스 PID를 확인하고, 동일 `recheck_position_key`의 arm은 최대 1회, terminal은 동일 `recheck_id`, second-extension 차단 로그는 최대 1회여야 한다. OFI raw/smooth/regime/action 필드가 threshold compact event에 보존되는지도 함께 확인한다.
  - 금지: 이 관찰 항목을 근거로 bot 재기동, threshold 완화, hard/protect/emergency stop 변경, provider·주문·수량·cap 변경을 수행하지 않는다.
  - 재기동 결과 (`2026-08-05 13:21~13:22 KST`): review gate와 pre-restart full detector `summary_severity=pass`, 당일 runtime env verifier pass를 확인한 뒤 표준 `restart.sh`의 `restart.flag` handoff로 PID가 `62804 -> 262970`으로 교체됐다. 새 PID는 `KORSTOCKSCAN_RUNTIME_GIT_COMMIT=f10d63e5d33734adf5211f57dbaeeace67c29640`, `KORSTOCKSCAN_RUNTIME_SOURCE_DIRTY=false`, `KORSTOCKSCAN_RUNTIME_STARTED_AT_KST=2026-08-05T13:21:24+09:00`이며 PID verifier `status=pass`, `pid_passed=true`, unverified/runtime-policy/dated-override fail=`0`이다. 계좌 reconciliation, Kiwoom WS 연결·로그인·조건식·REG·첫 실시간 수신, OpenAI 초기화가 복구됐고 재기동 후 full detector도 `summary_severity=pass`, fresh 8005=`0`, process/thread/artifact health pass다.
  - 관찰 판정: 변경 commit은 clean runtime에 반영됐다. 13:21:24 이후 pipeline/threshold event의 recheck·OFI·soft-stop·protect-trailing 자연 표본은 아직 `0`이므로 `runtime_reflected_no_natural_match`로 닫고, one-shot/terminal/compact field 자연 검증은 장후 `ThresholdDailyEVReport0805`의 daily/cumulative attribution에서 이어 확인한다.

- [x] `[KiwoomAuth8005PidHandoff0805] 8005 graceful 재기동 후 이전 PID 로그 중복경보 귀속 보완` (`Due: 2026-08-05`, `Slot: PREOPEN`, `TimeWindow: 08:48~09:00`, `Track: RuntimeStability`)
  - Source: [kiwoom_auth_8005_restart.py](/home/ubuntu/KORStockScan/src/engine/error_detectors/kiwoom_auth_8005_restart.py), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 최초 fresh 8005는 기존처럼 token cache invalidation과 `restart.flag`를 수행한다. 새 PID 시작 전에 이전 PID가 남긴 timestamped 8005는 PID handoff provenance로 소비하고 중복 cache invalidation·Telegram·restart를 만들지 않으며, timestamp 결손 또는 새 PID 시작 이후 8005는 계속 actionable이어야 한다.
  - 금지: current-runtime 8005 은폐, cooldown/daily cap 우회, REST same-request retry 1회 확장, threshold/provider/order guard 변경을 금지한다.
  - 실행 결과: 08:48:26 첫 detector가 `restart.flag`를 생성해 PID `54536 -> 62804`로 교체했고, 새 PID는 08:48:42 token 발급 성공 후 REST 시세/계좌 호출에서 8005가 재발하지 않았다. 08:48:41 cooldown 경보는 이전 PID가 08:48:29까지 남긴 로그를 새 PID가 다시 읽은 중복 귀속으로 판정했다. 공식 Kiwoom upstream `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`의 `kiwoom/core/client.py`, `kiwoom/core/auth.py`, `kiwoom/core/errors.py`, `postman/kiwoom-openapi.postman_collection.json`을 확인해 8005 one-shot auth recovery와 `/oauth2/token` 계약을 재확인했다.
  - 검증 결과 (`2026-08-05 08:54 KST`): 이전 PID 행만 있는 handoff는 `pass`와 `prior_runtime_auth_8005_count=1`, 이전·현재 PID 행이 함께 있으면 현재 행만 `fresh_auth_8005_count=1`로 유지되는 회귀를 추가했다. 자체리뷰에서 stale heartbeat PID가 다른 프로세스로 재사용될 때 과거 로그로 잘못 억제될 수 있는 결함을 발견해 `/proc/<pid>/cmdline`의 `bot_main.py` identity를 fail-closed 검증하도록 보완했다. detector·process health·bot scheduler 확대 회귀 `48 passed`, full dry-run `summary_severity=pass`, Black, Ruff, compile, `git diff --check`, checklist parser를 통과했다. producer/consumer·silent-fail·runtime mutation authority 재리뷰 finding=`0`이다.
  - 다음 액션: 현재 정상 PID는 추가 재기동하지 않는다. 다음 소스 반영 재기동 뒤 자연 PID handoff에서 `prior_runtime_auth_8005_count`와 current-runtime 재발 여부를 확인한다.

- [x] `[KiwoomAuth8005TokenHandoff0805] 갱신 후 장수 caller의 stale token 반복 사용 해소` (`Due: 2026-08-05`, `Slot: PREOPEN`, `TimeWindow: 08:47~09:20`, `Track: RuntimeStability`)
  - Source: [kiwoom_utils.py](/home/ubuntu/KORStockScan/src/utils/kiwoom_utils.py), [kiwoom_orders.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_orders.py), [kiwoom_websocket.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 최초 auth 실패는 기존 one-shot refresh/retry 계약으로 복구하되, 성공한 `old -> new` token handoff 뒤 장수 REST/account/order caller와 WS manager의 다음 요청은 갱신 token부터 시작해야 한다. retry 확대, token endpoint 추가 호출, 주문·threshold·provider 권한 변화는 없어야 한다.
  - 원인 및 구현: 08:47:57 WS `code=1000 Bye` 뒤 기존 startup token이 REST `8005`와 WS `805004`에서 함께 거절됐다. 08:47:58 shared cache에는 새 token이 있었지만 기동 시 token을 주입받은 모듈들이 다음 요청 첫 시도에 이전 token을 반복 사용해 8005를 증폭했다. cache-path scoped·process-local·64-entry bounded replacement map으로 성공한 handoff를 기록하고 공통 REST, order/account, radar fallback, read-only advisory helper가 첫 전송 전에 이를 해석하도록 보완했다. WS 강제 refresh도 동일 handoff를 선제 등록한다.
  - 공식 참조: Kiwoom upstream `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`의 `kiwoom/core/client.py`, `kiwoom/core/auth.py`, `kiwoom/core/errors.py`, `postman/kiwoom-openapi.postman_collection.json`을 확인했다. 8005 auth retry와 `/oauth2/token` `client_credentials` 계약은 유지했다.
  - 검증 결과 (`2026-08-05 09:01 KST`): 자체리뷰에서 공통 helper를 우회하던 radar fallback과 read-only advisory 소비자를 찾아 동일 handoff resolver에 연결했다. 추가 리뷰에서는 발급된 갱신 token이 실제 REST retry 또는 WS LOGIN ACK를 통과하기 전에 handoff로 게시되는 결함과 역방향 mapping cycle 가능성을 발견해, 성공 응답 뒤에만 bounded replacement를 등록하고 cycle은 fail-closed하도록 보완했다. auth cache/retry·REST/order/account·WS·detector·radar fallback·read-only advisory 확대 회귀 `658 passed`, checklist parser, Black, targeted Ruff, compile, `git diff --check`를 통과했고 재리뷰 finding=`0`이다.
  - 다음 액션: 현재 PID `62804`는 변경 전 소스이므로 이 보완은 아직 runtime 미반영이다. 현재 detector와 process health가 pass이고 fresh 8005도 없으므로 이 변경만으로 즉시 재기동하지 않으며, 다음 승인된 우아한 재기동에서 자연 auth handoff를 관찰한다.

- [x] `[SamsungWidgetRecoveryEpisode0805] 완료봉 저항 회복 뒤 반등 눌림 관측 복구` (`Due: 2026-08-05`, `Slot: INTRADAY`, `TimeWindow: 09:00~15:30`, `Track: ScalpingLogic`)
  - Source: [samsung_widget_advisory.py](/home/ubuntu/KORStockScan/src/engine/monitoring/samsung_widget_advisory.py), [widget_mechanical_entry_replay.py](/home/ubuntu/KORStockScan/src/engine/monitoring/widget_mechanical_entry_replay.py), [samsung_price_widget.py](/home/ubuntu/KORStockScan/tools/windows/samsung_price_widget.py)
  - 판정 기준: 구조·거래량·3/5분 추세·상대강도·fresh BBO가 확인된 episode만 최대 3개 완료봉 동안 유지하고, 완료 1분봉 종가가 저항을 회복한 뒤 2틱 이내 눌림이 지지를 유지할 때만 `ENTRY_CAUTION` 관측을 복구한다.
  - 금지: 형성 중 현재가의 순간 저항 터치만으로 reclaim 확정, source-quality·지지이탈·하락추세·live reversal veto 우회, AI/실주문/threshold/provider/bot 권한 부여를 금지한다.
  - 검증 결과: `0f4258df` 구현을 재리뷰해 형성 중 현재가만으로 reclaim 시각이 기록되는 결함을 발견했고 완료봉 종가 기준으로 fail-closed 보완했다. widget advisory·알림·평가·mechanical replay 회귀 `127 passed`, Black, Ruff, compile, checklist parser, `git diff --check`를 통과했으며 재리뷰 finding=`0`이다. 모든 상태는 `runtime_effect=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`를 유지한다.

- [x] `[ErrorDetectorInstalledScheduleContract0805] 설치 cron·parent enable·terminal skip 기반 오탐 제거 및 startup provenance 보완` (`Due: 2026-08-05`, `Slot: PREOPEN`, `TimeWindow: 08:15~08:45`, `Track: RuntimeStability`)
  - Source: [cron_completion.py](/home/ubuntu/KORStockScan/src/engine/error_detectors/cron_completion.py), [artifact_freshness.py](/home/ubuntu/KORStockScan/src/engine/error_detectors/artifact_freshness.py), [process_health.py](/home/ubuntu/KORStockScan/src/engine/error_detectors/process_health.py)
  - 판정 기준: 설치되지 않은 registry job, crontab parent flag=false인 산출물, exit code 0의 disabled/skipped status, step-scoped `[SKIP]` 산출물을 실패로 경보하지 않는다. crontab 조회 실패는 기대값을 보존하고, 전일 heartbeat만 남은 당일 기동 실패는 current PID crash가 아니라 `startup_not_observed`로 분리한다.
  - 금지: 중간 step `[SKIP]`을 전체 wrapper 성공으로 확대, crontab 조회 실패 시 감시 비활성, PREOPEN handoff 실패 우회 재기동을 금지한다.
  - 실행 결과: detector·PREOPEN·wrapper targeted test `310 passed`, Ruff/Black/diff/parser validation 통과. 실제 crontab dry-run에서 미설치 swing job은 `disabled_not_installed`, parent OFF 산출물은 `disabled_by_parent`, 전일 heartbeat는 `startup_not_observed`로 분리됐다. 2026-08-05 PREOPEN 재생성 중 scale-in policy 파일 version/runtime-apply 계약 불일치를 발견해 해당 family만 `runtime_policy_preflight_failed:policy_version_mismatch`로 제외했으며, 재생성 status `succeeded`와 독립 handoff verify `pass`를 확인했다. AI correction provider는 `openai`이고 `provider=none`이 아니다.
  - 다음 액션: review/commit gate가 닫힌 소스로 supervised bot을 기동한 뒤 새 PID/heartbeat, `/proc/<pid>/environ` handoff와 detector recovery를 확인한다.

- [x] `[RuntimePolicyArchiveIntegrity0805] scale-in 갱신근거·대용량 JSONL retention·운영파일 원자성 보완 및 리뷰` (`Due: 2026-08-05`, `Slot: PREOPEN`, `TimeWindow: 07:50~08:20`, `Track: RuntimeStability`)
  - Source: [scale_in_split_order_plan.py](/home/ubuntu/KORStockScan/src/engine/scalping/scale_in_split_order_plan.py), [compress_db_backfilled_files.py](/home/ubuntu/KORStockScan/src/engine/compress_db_backfilled_files.py), [run_logs_rotation_cleanup_cron.sh](/home/ubuntu/KORStockScan/deploy/run_logs_rotation_cleanup_cron.sh)
  - 판정 기준: real outcome·MFE/MAE·price join refresh evidence가 없는 scale-in policy는 runtime loader와 PREOPEN audit가 함께 거부한다. canonical context/pipeline summary/완료 threshold partition은 gzip-aware consumer 계약과 검증된 atomic 압축을 갖고, system metric malformed row는 격리하며 sentinel/snapshot은 복원 검증 후에만 원본을 교체한다.
  - 금지: stale legacy policy의 runtime 적용, 미검증 JSONL 삭제, plain/gzip 이중 파일로 인한 소비 누락, system metric malformed row의 정상 표본 취급을 금지한다.
  - 다음 액션: targeted tests·parser·review gate finding 0 이후 dry-run으로 실제 압축 후보와 scale-in 전일 artifact 차단 상태를 검증한다. bot 재기동이나 runtime env 직접 변경은 별도 사용자 지시 없이는 수행하지 않는다.
  - 실행 결과 (`2026-08-05 08:07 KST`): 전일 scale-in policy를 재생성해 real outcome=`0/3`, additional MFE/MAE=`0/3`, price join coverage=`0.6667/0.8`의 3개 blocker로 `runtime_apply_allowed=false`를 확정했고 legacy evidence-less policy도 loader/PREOPEN audit 양쪽에서 거부한다. canonical context `4`개·`2,760`행·원본 `1.6GB`, manifest-verified pipeline summary `41`개·`382,279`행·`1.1GB`, completed-checkpoint threshold partition `588`개·`1,650,925`행·`4.0GB`를 row/gzip 검증 후 압축했으며 disk 사용률은 `72% -> 64%`로 하락했다. system metric malformed `1`행은 quarantine하고 유효 `2,857`행/invalid `0`을 확인했다. 자체리뷰에서 multi-part checkpoint tail count 오해와 archive helper의 Kiwoom import side effect, blocked policy의 부정확한 carry-forward 표현, atomic gzip temp를 partition으로 오인할 수 있는 consumer glob을 발견해 보완했다. 재리뷰 finding=`0`; targeted `415 passed`, Black, Ruff, shell syntax, compile, `git diff --check`, checklist parser를 통과했다. 현재 bot은 미기동이며 당일 기존 PREOPEN env는 재생성 전 policy version을 가리키므로 정규 PREOPEN 재선정/verify 전까지 runtime 반영으로 인정하지 않는다.

- [x] `[LimitDownObservationEffectiveness0805] 하한가 관찰 포착 및 exact-empty 근접 하한가 보조군 구현·리뷰` (`Due: 2026-08-05`, `Slot: INTRADAY`, `TimeWindow: 09:00~15:30`, `Track: ScalpingLogic`)
  - Source: [limit_down_watch.py](/home/ubuntu/KORStockScan/src/engine/scalping/limit_down_watch.py), [limit_down_watch_report.py](/home/ubuntu/KORStockScan/src/engine/monitoring/limit_down_watch_report.py), [kiwoom-api-data-contract.md](/home/ubuntu/KORStockScan/docs/kiwoom-api-data-contract.md)
  - 판정 기준: KRX 장중에만 체류시간을 계산하고 0B 체결과 0D 호가를 분리 포착한다. 공식 전일 하한가가 0건일 때만 전일 저가 `-29.5%~-27%` 및 저가 대비 종가 회복 `5% 이상`인 `near_limit_rebound`를 공식 일봉과 DB 일봉 교차검증 후 관찰 전용으로 등록한다.
  - 당시 금지: 후속 사용자 지시 전까지 `near_limit_rebound`를 기존 exact 하한가 unlock counterfactual/live-auto 표본에 합치거나 BUY·실주문 권한으로 사용하지 않는다. 후속 전환은 아래 `LimitDownSingleSampleAutoLive0805`가 독립 소유한다.
  - 다음 액션: targeted test와 review gate가 finding 0건이면 완료하고, 자연 0B/0D 및 유형별 postclose 산출물은 런타임 재기동 이후 별도 관찰한다.
  - 실행 결과 (`2026-08-05 07:43 KST`): 공식 upstream `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`의 `kiwoom_docs/종목정보.md`, `kiwoom_docs/실시간시세.md`, `kiwoom/realtime/packets.py`, `kiwoom/specs.py`를 재확인했다. KRX 장중 세션에서만 관찰 등록·체류를 시작하고, 0D 호가를 0B 체결과 분리해 5초 snapshot 및 REG route/item provenance로 기록하며, 유효 빈 소스도 idle heartbeat를 저장한다. exact 0건일 때만 `near_limit_rebound`를 DB 완성일 `2635`행 preflight, `ka10081` 전일/전전일 OHLC, `ka10099` 관리·환기·투자유의 상태로 교차검증한다. 신규 cohort는 exact unlock label/sim/live-auto와 runtime promotion에서 명시적으로 제외했다. 자체리뷰에서 0D 매 이벤트 디스크 쓰기와 관리·환기 필터 결손을 발견해 보완했고 재리뷰 finding=`0`; 관련 `263 passed`, compile, Ruff(기존 비변경 F841 제외), Black, `git diff --check`, checklist parser를 통과했다. 실 API 임시 smoke는 exact/near=`0/0`, status=`pass`, blocked=`0`이며 운영 artifact와 bot 상태는 변경하지 않았다.

- [x] `[LimitDownSingleSampleAutoLive0805] 유형별 1개 검증 표본 자동 실매매 후보화·누적 자동갱신 검증·리뷰·게시` (`Due: 2026-08-05`, `Slot: INTRADAY`, `TimeWindow: 09:00~15:30`, `Track: ScalpingLogic`)
  - Source: [limit_down_watch_research.py](/home/ubuntu/KORStockScan/src/engine/monitoring/limit_down_watch_research.py), [limit_down_watch.py](/home/ubuntu/KORStockScan/src/engine/scalping/limit_down_watch.py), [scalping_scanner.py](/home/ubuntu/KORStockScan/src/scanners/scalping_scanner.py)
  - 판정 기준: source-quality가 유효한 `cohort×가격대` ordered path 1개부터 비용 차감 EV·downside p10·MAE·BBO 기준을 모두 통과하면 장후 bounded-live artifact를 생성하고, 다음 거래일 런타임이 사용자 승인 없이 최신 prior-date 정책을 자동 로드한다. 매 장후 이전 rolling row와 당일 row를 row-id로 중복 제거해 cumulative를 자동 갱신하며 최신 artifact가 blocked이면 이전 ready 정책을 상속하지 않는다.
  - 보호장치: exact는 연속 두 unlock 체결, `near_limit_rebound`는 시가 회복 및 저가 대비 `1%` 이상 반등의 연속 두 체결을 요구한다. 공통으로 fresh BBO·spread `1.5%`·일 1회·동시 1종목·물타기/재진입/오버나이트 금지와 정상 scalping AI·submit·hard safety를 유지한다. provider·threshold·수량 owner·cap·bot 상태는 변경하지 않는다.
  - 다음 액션: review gate finding 0, targeted test, cumulative 자동갱신/자동철회, compile, formatter/lint, diff/checklist parser 검증 후 의미 단위 커밋·푸시한다. 봇 재기동은 이 항목의 권한이 아니다.
  - 실행 결과 (`2026-08-05 KST`): exact `2회+/1회`와 `near_limit_rebound`를 독립 `cohort×가격대` cell로 유지하면서 source-quality 유효 ordered path 1건부터 비용·EV·하방·MAE·BBO 기준을 모두 통과한 유형만 no-approval bounded-live artifact로 만든다. 런타임은 최신 prior-date artifact를 자동 로드하되 near 유형은 raw 0B 연속 두 틱의 시가 회복·저가 대비 `1%` 반등 확인 이벤트와 제출 직전 fresh quote를 재검증한다. 장후 producer는 최신 prior rolling rows와 당일 rows를 row-id로 중복 제거해 누적 갱신하고, prior 계약/행 유일성/누적 count 손상 또는 최신 누적 EV·하방 기준 이탈 시 source-quality 차단 및 다음 기동 정책 자동 철회를 수행한다. 리뷰에서 near sim provenance 오기, snapshot/raw-tick 확인 의미 불일치, prior 누적 artifact 무검증을 찾아 모두 보완했다. 확대 회귀 `321 passed`, Black, targeted Ruff(legacy E402/F401/F841 제외), compile, checklist parser, `git diff --check`를 통과하고 미해결 finding=`0`이다. provider·일반 threshold·position sizing owner·cap·bot 상태와 현재 PID는 변경하지 않았다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-08-04` postclose -> `2026-08-05`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0805] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-08-05`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-04.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0805] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-08-05`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-08-04.json), [code_improvement_workorder_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-04.json), [threshold_apply_2026-08-05.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-08-05.json), [threshold_runtime_env_2026-08-05.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-08-05.json), [threshold_runtime_env_verify_2026-08-05.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-08-05.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`4`, forced_scout_with_post_sell_count=`13`, post_sell_join_coverage_pct=`3.186275`, outcome_coverage_state=`partial`, profitable_forced_scout_count=`8`, loss_or_flat_forced_scout_count=`5`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0805] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-08-05`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-04.json)
  - 판정 기준: 전일 postclose `selected_families`는 candidate inventory이므로 실제 runtime 선택으로 간주하지 않는다. 당일 PREOPEN runtime env와 실행 PID env가 함께 선택한 family만 runtime event provenance에 찍히는지 확인하고, retired `ai_watching_score_smoothing_report_only`는 runtime 관찰 대상으로 요구하지 않는다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0805] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-08-05`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-04.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0805] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-08-05`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-08-05.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-05.jsonl), [threshold_events_2026-08-05.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-05.jsonl), [observation_source_quality_audit_2026-08-05.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-05.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-08-05 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[PostcloseSourceQualityGateReview0805] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-08-05`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-08-05.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-05.json), [threshold_cycle_ev_2026-08-05.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-05.json), [code_improvement_workorder_2026-08-05.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-05.json), [threshold_cycle_postclose_verification_2026-08-05.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-08-05.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0805] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-08-05`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-04.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0805] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-08-05`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-04.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0805] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-08-05`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-08-04.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-08-04.md), [code_improvement_workorder_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-04.json)
  - 판정 기준: selected_order_count=80와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0805] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-08-05`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-04.json), [runtime_apply_gap_audit_2026-08-04.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-04.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`327`, rollup_required_count=`327`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 326}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0805] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-08-05`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-08-04.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`15`, run_count=`15`, skip_count=`0`, source_missing_count=`7`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:14, source_missing_or_unreadable:7, upstream_drift_signal:7, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
