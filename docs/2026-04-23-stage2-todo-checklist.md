# 2026-04-23 Stage 2 To-Do Checklist

## 오늘 목적

- `entry_filter_quality` 착수 가능성을 `2026-04-23 POSTCLOSE 15:20~15:35 KST`에 재판정하고 오늘 안에 닫는다.
- `AI threshold` 완화축은 독립 Pain Point 승격이 아니라 `score/promote` 단일 live 축 후보인지 여부만 `why`까지 포함해 재판정한다.
- `gatekeeper latency`는 모델 응답 지연만이 아니라 `engine lock 직렬화`, `cache miss`, `quote_fresh latency block`이 겹친 문제인지 분해 확인한다.
- `09:00~11:00 KST`까지 BUY 신호가 여전히 부족하면 장후까지 기다리지 않고 기존 축을 OFF한 뒤 준비된 다음 축 1개를 장중 즉시 ON해 live 타당성을 확인한다.
- `AIPrompt 작업 12 Raw 입력 축소 A/B 점검`은 `2026-04-21` 미확정이 남아 있을 때만 최종확정으로 닫는다.
- `PYRAMID zero_qty Stage 1`은 현재 관찰축과 분리된 `main-only canary 후보 범위/flag/rollback guard`까지만 고정한다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- live 변경은 하루 `1축 canary`만 허용하고, 신규/보완축은 `shadow 금지`다.
- 일정은 모두 `YYYY-MM-DD KST`, `Slot`, `TimeWindow`로 고정한다.
- 손익은 `COMPLETED + valid profit_rate`만 사용하고 `full fill`과 `partial fill`은 분리한다.
- `11:00 KST BUY sufficiency checkpoint`를 넘겼는데 BUY 신호가 여전히 부족하면 같은 날 `INTRADAY`에 기존 축 OFF -> `restart.flag` -> 준비된 다음 축 ON까지 진행한다. `아무 작업 없이 장후까지 대기`는 금지한다.
- same-day 전환은 `1축 추가`가 아니라 `기존 축 교체`로 처리한다. 같은 서버/같은 창에서 2축 동시 live는 금지한다.
- canary 판정/재교정/롤백 전후에는 main bot PID의 `/proc/<pid>/environ`에서 핵심 `KORSTOCKSCAN_*` 증적을 남긴다. 최소 대상은 enable flag, 관련 threshold/prompt split, runtime route다.
- `유지/보류/미완/폐기/완료`는 모두 수치 + why(기대값 영향, 원인귀속, 표본충분성/미달 이유)를 함께 남긴다.
- `entry_filter_quality`, `position_addition_policy`, `EOD/NXT`, `AI 엔진 A/B`는 같은 날 live 축으로 섞지 않는다.

## 장전 체크리스트 (08:20~08:40)

- [x] `[LatencyOps0423] gatekeeper latency 계측 반영 재시작 확인` (`Due: 2026-04-23`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:30`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `restart.flag` 기반 우아한 재시작 이후 신규 로그에 `gatekeeper_lock_wait_ms`, `gatekeeper_model_call_ms`, `gatekeeper_total_internal_ms` 필드가 실제 기록되는지 확인한다.
  - 실행 메모: 반영 표준은 `touch restart.flag`다. 재시작 직후 첫 `gatekeeper` 관련 pipeline event 1건 이상을 확인한다.
  - why 기준: 코드 반영만 되고 프로세스 재시작이 누락되면 내일 오전 관찰값이 전부 구버전 포맷으로 남아 판정 근거가 무효가 된다.
  - 실행 결과 1차 (`2026-04-23 08:08~08:09 KST`): `touch restart.flag` 후 `bot_main.py` PID가 `77993 -> 80118`로 교체됐고, `logs/bot_history.log`에 `08:08:53` 우아한 종료 및 `run_bot.sh` 재기동이 확인됐다.
  - 실행 결과 2차 (`2026-04-23 09:18:47 KST`): `logs/pipeline_event_logger_info.log` 첫 live `blocked_gatekeeper_reject` 이벤트에서 `gatekeeper_eval_ms=11598`, `gatekeeper_lock_wait_ms=0`, `gatekeeper_packet_build_ms=0`, `gatekeeper_model_call_ms=11598`, `gatekeeper_total_internal_ms=11598`가 실제 기록됐다.
  - why: 재시작 확인만으로는 live 경로 직렬화가 보장되지 않는다. 이번에는 재시작 이후 동일 거래일 첫 gatekeeper reject 이벤트에 신규 필드가 함께 찍혀 `코드 반영 -> 프로세스 재시작 -> live 로그 직렬화` 3단계가 모두 연결됐다고 볼 수 있다. 또한 이 첫 표본은 `lock_wait=0`, `model_call_ms=total_internal_ms`라서 최소한 해당 건에서는 엔진 lock 병목보다 모델 호출 시간이 지연의 전부였다는 해석이 가능하다.
- [x] `[LatencyOps0423] gatekeeper latency 신규 계측 장전 sanity check` (`Due: 2026-04-23`, `Slot: PREOPEN`, `TimeWindow: 08:30~08:40`, `Track: Plan`)
  - Source: [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py), [sniper_performance_tuning_report.py](/home/ubuntu/KORStockScan/src/engine/sniper_performance_tuning_report.py)
  - 판정 기준: 오전 첫 관찰 시점에 `gatekeeper_eval_ms`, `gatekeeper_lock_wait_ms`, `gatekeeper_model_call_ms`, `gatekeeper_fast_reuse_ratio` raw log 또는 snapshot 중 최소 1경로에서 확인되면 통과로 닫는다.
  - 산출물: `수치 + why + 누락 필드 여부`를 기록한다.
  - 근거 (`2026-04-23 08:09:40 KST` intraday_light snapshot): `performance_tuning_2026-04-23.json` 기준 `gatekeeper_eval_ms=null`, `gatekeeper_eval_ms_p95=0.0`, `gatekeeper_lock_wait_ms_p95=0.0`, `gatekeeper_model_call_ms_p95=0.0`, `gatekeeper_total_internal_ms_p95=0.0`, `gatekeeper_fast_reuse_ratio=0.0`.
  - why: 장전 시점에는 아직 gatekeeper 평가 표본이 없어 수치가 `0/null`인 것이 정상이다. 이번 sanity check의 목적은 성능 좋고 나쁨이 아니라 신규 계측 필드가 snapshot 경로에 실제로 노출되는지 확인하는 것이다.
  - 누락 필드 여부: `gatekeeper_eval_ms`, `gatekeeper_lock_wait_ms_*`, `gatekeeper_model_call_ms_*`, `gatekeeper_total_internal_ms_*`, `gatekeeper_fast_reuse_ratio` 모두 확인됨.

## 장중 체크리스트 (09:00~09:10)

- [x] `[LatencyOps0423] 장개시 후 첫 gatekeeper event 필드 실기록 확인` (`Due: 2026-04-23`, `Slot: INTRADAY`, `TimeWindow: 09:00~09:10`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정 기준: `08:08~08:09 KST restart.flag` 반영 이후 오늘 첫 `gatekeeper` 관련 pipeline event/log 1건 이상에서 `gatekeeper_lock_wait_ms`, `gatekeeper_model_call_ms`, `gatekeeper_total_internal_ms`가 실제 기록되면 닫는다.
  - why 기준: 장전 재기동 확인만으로는 계측 필드가 live 경로에서 실제 직렬화되는지 확정할 수 없다. 첫 gatekeeper 호출 1건을 찍어야 재시작 확인 항목이 완결된다.
  - 근거 (`2026-04-23 09:18:35~09:18:47 KST`): `logs/pipeline_event_logger_info.log`에서 `KT(030200)`의 `gatekeeper_fast_reuse_bypass` 후 `blocked_gatekeeper_reject`가 이어졌고, reject 이벤트에 `gatekeeper_lock_wait_ms=0`, `gatekeeper_model_call_ms=11598`, `gatekeeper_total_internal_ms=11598`가 포함됐다.
  - why: `gatekeeper_fast_reuse_bypass`만으로는 신규 latency 계측 필드가 보이지 않지만, 이어진 reject 이벤트에는 세부 계측치가 함께 기록됐다. 즉 gatekeeper가 실제 평가를 수행한 표본에서 신규 필드가 살아 있음을 확인했으므로 장개시 후 첫 실기록 확인 항목은 완료로 닫는다.

## 장중 체크리스트 (10:40~11:20)

- [x] `[BuySignal0423] 오전 BUY sufficiency checkpoint` (`Due: 2026-04-23`, `Slot: INTRADAY`, `TimeWindow: 10:40~10:50`, `Track: ScalpingLogic`) (`실행: 2026-04-23 11:03 KST`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-22-auditor-performance-result-report.md](/home/ubuntu/KORStockScan/docs/2026-04-22-auditor-performance-result-report.md)
  - 판정 기준: `09:00~10:40 KST main-only` 기준 `primary_buy(ai_confirmed action=BUY)`, `recovered_buy(buy_recovery_canary promoted=true)`, `entry_armed`, `submitted_orders`, `WAIT65~79 recovery_check/promoted`, `blocked_ai_score_share` 또는 동등 blocker 분포를 보고 `BUY 충분 / BUY 부족 / BUY는 충분하나 entry_armed 이후 병목` 중 하나로 닫는다.
  - 실행 메모: 이 항목은 `intraday_light` snapshot을 자동 생성하지 않는다. raw log만으로 우선 판정 가능하되, 근거 파일을 남기거나 raw log가 부족하면 `deploy/run_monitor_snapshot_midcheck_safe.sh 2026-04-23`을 즉시 수동 실행해 `trade_review`, `performance_tuning`, `wait6579_ev_cohort`를 함께 사용한다. 직접 CLI는 timeout 보호가 없으므로 장중 수동 점검에서는 쓰지 않는다. snapshot 근거를 남길 때는 `max_date_basis=2026-04-23`, `evidence_cutoff=10:40 KST`, `trend_max_dates=MONITOR_SNAPSHOT_INTRADAY_TREND_MAX_DATES 또는 기본값`을 같이 기록한다.
  - why 기준: BUY 신호 자체가 계속 부재하면 `entry_filter_quality`, `AI threshold`, HOLDING, EOD/NXT 모든 후속축이 표본 부족으로 밀린다. 반대로 `recovered_buy/entry_armed`가 충분한데 `submitted_orders`가 낮으면 BUY 회복축을 유지관찰로 닫지 말고 `entry_armed -> submitted` 병목을 같은 장중에 즉시 연다.
  - 산출물: `수치 + why + 11:00 이후 same-day live 전환 필요 여부 + buy_recovery_canary 유지/고정 여부`를 기록한다.
  - 판정: 완료. `BUY는 충분하나 entry_armed 이후 병목`으로 닫는다.
  - 근거: `performance_tuning_2026-04-23.json` (`saved_snapshot_at=2026-04-23 11:02:55`, `max_date_basis=2026-04-23`, `evidence_cutoff=11:00 KST`) 기준 `candidates=124`, `ai_confirmed=66`, `entry_armed=36`, `submitted=1`이다. 같은 snapshot에서 `budget_pass_events=1893`, `order_bundle_submitted_events=2`, `latency_block_events=1891`, `quote_fresh_latency_blocks=1693`, `gatekeeper_eval_ms_p95=16869ms`, `expired_armed_events=225`, `full_fill_events=1`, `partial_fill_events=0`이라 BUY 표본 부족보다 제출 직전 병목이 훨씬 크다.
  - 근거: `wait6579_ev_cohort_2026-04-23.json` (`saved_snapshot_at=2026-04-23 11:03:12`) 기준 `recovery_check_candidates=20`, `recovery_promoted_candidates=13`, `budget_pass_candidates=15`, `latency_block_candidates=15`, `submitted_candidates=0`이다. 즉 `buy_recovery_canary`는 upstream 후보를 만들고 있지만 `entry_armed -> submitted` 연결은 회복되지 않았다.
  - 근거: `trade_review_2026-04-23.json` (`saved_snapshot_at=2026-04-23 11:02:42`) 기준 `completed_trades=1`, `avg_profit_rate=0.67`, `full_fill_events=1`, `partial_fill_events=0`이다. raw log에서도 덕산하이메탈(`077360`)이 `10:03:40 KST` score50 mechanical fallback 후 `10:06:36 KST` 접수, `10:10:05 KST` 체결, `10:39:15 KST` 재접수로 이어져 `BUY=0` 상태는 아니다.
  - why: 오전 표본은 이미 `BUY 부족`이 아니라 `upstream 표본은 있으나 downstream 제출 병목이 지배적`인 상태를 보여준다. 다만 `submitted/full/partial` low-N이므로 hard pass/fail이 아니라 방향성 판정으로 잠근다.
  - 다음 액션: `11시 same-day live 전환 필요 여부=검토 필요`, `buy_recovery_canary=유지/고정`. 신규 판단은 아래 `[PlanRebase0423]` 항목에서 downstream 1축 준비도까지 포함해 닫는다.
- [x] `[PlanRebase0423] 11시 BUY 판정 결과별 same-day next-axis live 전환` (`Due: 2026-04-23`, `Slot: INTRADAY`, `TimeWindow: 10:50~11:20`, `Track: ScalpingLogic`) (`실행: 2026-04-23 11:08 KST`)
  - Source: [audit-reports/2026-04-22-plan-rebase-central-audit-review.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-22-plan-rebase-central-audit-review.md)
  - 판정 기준 A: `[BuySignal0423]`가 `BUY 부족`이면 `buy_recovery_canary prompt/score/promote` 또는 `AI threshold score/promote` 중 준비된 upstream 1축만 선택해 기존 live 축과 충돌하지 않게 반영한다.
  - 판정 기준 B: `[BuySignal0423]`가 `BUY는 충분하나 entry_armed 이후 병목`이면 `buy_recovery_canary`는 upstream 표본 생성 조건으로 유지/고정하고, 새 live 변경은 `entry_armed -> submitted` downstream 1축(`latency/quote 재검증`, `spread/quote_stale 분리`, 또는 동등 제출 전 병목 해소축)만 ON/OFF 비교한다.
  - 판정 기준 C: `[BuySignal0423]`가 `BUY 충분`이고 `submitted_orders`도 회복 중이면 신규 live 축을 열지 않고 `submitted/full/partial/soft_stop` 품질 관찰로 넘긴다.
  - why 기준: BUY 부재는 장후까지 기다린다고 해소되지 않고, `entry_armed` 이후 차단도 장후 설계만으로는 실제 주문 제출 반응을 볼 수 없다. 단, `buy_recovery_canary`가 `recovered_buy/entry_armed` 표본을 만들고 있다면 이를 OFF하면 downstream 축 검증 입력이 줄어드므로, 교체가 아니라 upstream 조건 고정 + downstream 1축 확장으로 해석한다.
  - 금지: `entry_filter_quality`와 `score/promote` 동시 ON, `buy_recovery_canary` OFF 후 downstream 표본을 고갈시키는 전환, 전역 threshold 하향, fallback 계열 재개, `entry_armed -> submitted` 축과 별도 보유/청산 축 혼합.
  - 판정: 완료. same-day `next-axis live 전환`은 오늘 장중에는 `미실행`으로 닫고, `buy_recovery_canary`는 유지/고정한다.
  - 근거: `[BuySignal0423]` 결과가 `BUY 부족`이 아니라 `BUY는 충분하나 entry_armed 이후 병목`이므로 upstream 교체 조건 A가 아니다. 동시에 현재 코드에서 바로 켤 수 있는 downstream 후보는 [src/utils/constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py) `SCALP_LATENCY_GUARD_CANARY_ENABLED`뿐인데, [src/engine/sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py)의 `_should_apply_latency_guard_canary()`는 `SCALP_LATENCY_FALLBACK_ENABLED=False`면 즉시 `latency_fallback_disabled`를 반환하고, 허용 시에도 결과를 `ALLOW_FALLBACK`으로 연결한다.
  - 근거: `Plan Rebase` 기준선은 `post_fallback_deprecation`이며 `fallback_scout/main`, `fallback_single`, `latency fallback split-entry`는 폐기 확정 축이다. 따라서 위 경로를 오늘 downstream 1축으로 재사용하면 `entry_armed -> submitted` 병목 개선이 아니라 `fallback 재개`와 섞여 원인 귀속이 깨진다.
  - why: 장중 실전 전환은 `준비된 단일 downstream 축`이어야 하는데, 현재 저장소에 남아 있는 즉시 사용 가능 후보는 fallback 결합 경로라 Plan Rebase 기준을 만족하지 못한다. 무리하게 켜면 `main-only`, `shadow 금지`, `fallback 폐기`, `1축 canary` 원칙을 동시에 흔들게 된다.
  - 다음 액션: 장중 live는 기존 `buy_recovery_canary`만 유지하고, 장후 `[LatencyOps0423] gatekeeper latency 경로 분해(lock/cache/quote_fresh)`에서 `quote_stale=False/ws_age/ws_jitter/spread`를 분리한 `fallback 비결합 downstream 축` 1개를 새로 정의한다. 정의 가능 조건은 `submitted 단절이 주병목으로 잠금`, `분해 계측 live 확인`, `fallback과 분리된 단일 조작점 + rollback guard` 3개가 모두 충족될 때다.
- [x] `[LatencyOps0423] latency/quote 제출축 사전착수 가능 여부 판정` (`Due: 2026-04-23`, `Slot: INTRADAY`, `TimeWindow: 11:20~11:35`, `Track: Plan`) (`실행: 2026-04-23 11:22 KST`)
  - Source: [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py), [sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py)
  - 판정 기준: `entry_armed -> submitted` 병목에 대해 `지금 바로 할 수 있는 일`과 `장후까지 남겨야 하는 일`을 분리해 기록한다. 장중에는 원인귀속 정리, 로그/스냅샷 분해, 다음 코드수정 후보 고정까지 가능하면 `사전착수 가능`으로 닫는다.
  - 판정: 완료. `사전착수 가능`이다. 다만 `독립 downstream live 전환`은 아직 불가하다.
  - 근거: 오늘 snapshot 기준 `budget_pass_events=1893`, `order_bundle_submitted_events=2`, `latency_block_events=1891`, `quote_fresh_latency_blocks=1693`, `gatekeeper_eval_ms_p95=16869ms`라서 blocker 분해/원인귀속 정리는 지금도 충분히 가능하다. 또한 gatekeeper 계측 필드(`lock_wait/model_call/total_internal`)는 오늘 PREOPEN/INTRADAY에서 이미 live 기록이 확인됐다.
  - 근거: 반면 현재 코드에서 즉시 사용 가능한 downstream 후보는 `SCALP_LATENCY_GUARD_CANARY_ENABLED`뿐인데, `sniper_entry_latency.py`에서 `SCALP_LATENCY_FALLBACK_ENABLED=False` 시 `latency_fallback_disabled`를 반환하고 허용 시에도 `ALLOW_FALLBACK`으로 연결된다. 따라서 `fallback 비결합 제출축` 정의 없이 장중 live ON은 불가하다.
  - why: 즉시 가능한 일은 `분해/설계/코드수정 후보 고정`이고, 아직 불가능한 일은 `실전 1축 교체`다. 장후 task를 기다릴 필요 없이 원인귀속 정리 자체는 지금 착수해도 된다.
  - 다음 액션: 장중에는 `quote_stale=False vs true`, `ws_age/ws_jitter/spread`, `gatekeeper lock/model/cache` 분포를 먼저 정리하고, 장후 `[LatencyOps0423] gatekeeper latency 경로 분해(lock/cache/quote_fresh)`에서 `fallback 비결합 downstream 축` 여부를 최종 판정한다. 여기서 말하는 정의는 `단일 조작점 1개`, `주 KPI 1개`, `rollback guard 3개 이상`이 함께 고정되는 수준을 뜻한다.
- [x] `[LatencyOps0423] latency/quote 제출축 1차 blocker 분해(quote_stale/ws_age/ws_jitter/spread/lock-model-cache)` (`Due: 2026-04-23`, `Slot: INTRADAY`, `TimeWindow: 11:25~11:45`, `Track: Plan`) (`실행: 2026-04-23 11:37 KST`)
  - Source: [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py), [sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py)
  - 판정 기준: 오늘 live 로그와 `performance_tuning` snapshot을 기준으로 `quote_stale=False vs true`, `ws_age/ws_jitter/spread`, `gatekeeper lock/model/cache` 3축 분포를 1차 정리하고, `fallback 비결합 downstream 1축`의 단일 조작점 후보 1개를 남긴다.
  - why 기준: 지금 필요한 것은 장후까지 새 데이터를 기다리는 것이 아니라, 이미 쌓인 표본으로 `entry_armed -> submitted` 단절의 하위 원인을 좁혀 `단일 조작점 1개 + 주 KPI 1개 + rollback guard 3개`까지 정의 가능한 상태로 만드는 것이다.
  - 산출물: `수치 + why + 다음 코드수정 후보 1개`를 기록하고, 장후 `[LatencyOps0423] gatekeeper latency 경로 분해(lock/cache/quote_fresh)`의 입력으로 넘긴다.
  - 판정: 완료. `fresh quote spread 지배 + gatekeeper는 모델응답 경고이지만 현재 제출 병목의 주원인으로 보긴 어려움`으로 1차 잠근다.
  - 근거: `performance_tuning_2026-04-23.json` (`saved_snapshot_at=2026-04-23 11:21:13`) 기준 `budget_pass_events=2091`, `order_bundle_submitted_events=2`, `latency_block_events=2089`, `quote_fresh_latency_blocks=1882`, `quote_fresh_latency_passes=2`, `quote_fresh_latency_pass_rate=0.1`, `gatekeeper_eval_ms_p95=16869ms`, `gatekeeper_lock_wait_ms_p95=0`, `gatekeeper_model_call_ms_p95=16869`, `gatekeeper_total_internal_ms_p95=16869`, `gatekeeper_fast_reuse_ratio=0.0`, `gatekeeper_ai_cache_hit_ratio=0.0`다.
  - 근거: 오늘 `ENTRY_PIPELINE stage=latency_block` raw log 228건 1차 집계 기준 `quote_stale=False 203건`, `quote_stale=True 25건`으로 fresh quote 차단이 우세하다. `reason=latency_state_danger 208건`, `reason=latency_fallback_disabled 20건`이며 danger reason overlap은 `spread_too_wide 177`, `ws_age_too_high 42`, `ws_jitter_too_high 36`, `quote_stale 25`, `other_danger 22`다.
  - 근거: gatekeeper 관련 live 이벤트는 오늘 `blocked_gatekeeper_reject 2건`, `gatekeeper_fast_reuse_bypass 2건`만 확인됐다. reject 2건의 `gatekeeper_eval_ms`는 `8.4~11.6s`, `gatekeeper_lock_wait_ms=0`, `gatekeeper_model_call_ms≈total_internal_ms`, `gatekeeper_cache=miss`였다.
  - why: 지금 제출축을 가장 많이 막는 것은 `quote_stale=False` 구간의 `spread_too_wide`다. 따라서 첫 downstream 정의는 `latency 전체 완화`보다 `fresh quote spread 지배 구간`을 별도 cohort로 고정하는 쪽이 원인귀속이 가장 깨끗하다. 반면 gatekeeper는 느리지만 아직 low-N이고, 관찰된 표본도 제출 직전 대량 차단의 1차 설명력보다는 보조 경고에 가깝다.
  - 다음 액션: 장후 `[LatencyOps0423] gatekeeper latency 경로 분해(lock/cache/quote_fresh)`에서는 `fallback 비결합 downstream 1축`의 첫 후보를 `quote_stale=False + spread_too_wide 지배 구간 분리`로 두고, 보조 가설로 `ws_age/ws_jitter`와 `gatekeeper model_call/cache miss`를 같이 적는다. 다음 코드수정 후보 1개는 `latency_danger_reasons=spread_too_wide` 전용 분리 집계/allowlist 설계다.
- [x] `[LatencyOps0423] fallback 비결합 spread relief canary 구현 + 테스트` (`Due: 2026-04-23`, `Slot: INTRADAY`, `TimeWindow: 11:40~12:00`, `Track: ScalpingLogic`) (`실행: 2026-04-23 11:47 KST`)
  - Source: [sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py), [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py), [test_sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/tests/test_sniper_entry_latency.py)
  - 판정 기준: `REJECT_DANGER` 중 `quote_stale=False + spread_too_wide 단독` 케이스만 `ALLOW_NORMAL`로 직접 넘기는 fallback 비결합 조작점을 코드에 반영하고, 혼합 danger(`ws_age/ws_jitter/quote_stale` 동반)는 계속 차단되게 유지한다.
  - 판정: 완료. `spread-only + quote fresh` 구간 전용 `spread relief canary`를 구현했다.
  - 근거: [sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py)에 `_should_apply_latency_spread_relief_canary()`를 추가했고, `REJECT_DANGER -> ALLOW_NORMAL` 직접 override 경로와 `[LATENCY_SPREAD_RELIEF_CANARY]` 로그를 넣었다. [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py)에는 `KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_*` env/설정축을 추가했다.
  - why: 장중 blocker 분해 결과의 단일 조작점이 `fresh quote spread 지배`로 잠겼으므로, `ALLOW_FALLBACK` 재유입 없이 바로 제출축을 건드릴 수 있는 live 후보를 코드로 고정해야 남은 장에서 검증이 가능하다.
  - 테스트/검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_entry_latency.py` 결과 `10 passed`. 신규 테스트는 `spread-only danger -> ALLOW_NORMAL`, `mixed danger -> 차단 유지`를 함께 확인했다.
  - 다음 액션: 같은 날 1축 원칙을 지키려면 기존 live 축을 끈 뒤 이 canary만 켜서 남은 장을 본다. 잔여장 검증은 아래 항목으로 이어간다.
- [x] `[LatencyOps0423] same-day live 축 교체(constants default -> restart.flag)` (`Due: 2026-04-23`, `Slot: INTRADAY`, `TimeWindow: 11:50~12:05`, `Track: ScalpingLogic`) (`실행: 2026-04-23 11:58 KST`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py), [bot_main.py](/home/ubuntu/KORStockScan/src/bot_main.py)
  - 판정 기준: 현재 런타임에 별도 `KORSTOCKSCAN_*` env override가 없으면 `constants.py` 기본값으로 기존 live 축 OFF, 신규 live 축 ON을 반영하고 `restart.flag`로 same-day 교체를 완료한다.
  - 판정: 완료. 기본값 기준 live 축을 `buy_recovery_canary OFF -> spread_relief_canary ON`으로 교체하고 `restart.flag` 반영을 시작했다.
  - 근거: 교체 직전 `bot_main.py` PID `91091`의 `/proc/91091/environ`에는 `KORSTOCKSCAN_*` override가 없었고, 저장소 내 `.env`/compose/service 경로에서도 봇용 env 주입 흔적은 확인되지 않았다. 따라서 현재 런타임 소스는 `constants.py` 기본값으로 보는 것이 맞다.
  - 변경값: `AI_MAIN_BUY_RECOVERY_CANARY_ENABLED=False`, `SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=True`.
  - 다음 액션: 재시작 후 새 PID에서 `/proc/<pid>/environ`, 초기 로그, `[LATENCY_SPREAD_RELIEF_CANARY]` 발생 여부를 확인하고 아래 잔여장 검증 항목으로 이어간다.
- [x] `[LatencyOps0423] spread relief canary 잔여장 live 검증(submitted/pass_rate/fill quality)` (`Due: 2026-04-23`, `Slot: INTRADAY`, `TimeWindow: 12:00~15:20`, `Track: ScalpingLogic`) (`실행: 2026-04-23 14:00 KST, 중간판정`)
  - Source: [sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py), [performance_tuning_2026-04-23.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/performance_tuning_2026-04-23.json), [trade_review_2026-04-23.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/trade_review_2026-04-23.json)
  - 전제: `main-only`, `1축 canary` 원칙에 따라 기존 live 축 OFF 후 `KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=true`만 ON한 상태에서 기록한다. same-day 교체 시 `기존 축 OFF -> restart.flag -> 새 축 ON` 순서를 유지한다.
  - 판정 기준: `budget_pass_to_submitted_rate`, `quote_fresh_latency_pass_rate`, `submitted/full/partial fill quality`, `COMPLETED + valid profit_rate`, `fallback_regression=0`를 함께 보고 `유지/확대/롤백` 중 하나로 닫는다.
  - 금지: 기존 fallback 관련 플래그 재사용, 다축 동시 ON, `spread_only_required`를 무시하는 전역 완화.
  - 판정: 완료. `유지/확대`가 아니라 `효과 미확인 + 장후 원인 재분해`로 닫는다.
  - 근거(snapshot): `performance_tuning_2026-04-23.json` (`saved_snapshot_at=2026-04-23 14:03:44`, `max_date_basis=2026-04-23`, `trend_max_dates=5`, `evidence_cutoff=14:00 KST`) 기준 `budget_pass_events=4373`, `order_bundle_submitted_events=3`, `budget_pass_to_submitted_rate=0.1%`, `latency_block_events=4370`, `quote_fresh_latency_blocks=4029`, `quote_fresh_latency_passes=3`, `quote_fresh_latency_pass_rate=0.1%`, `full_fill_events=2`, `partial_fill_events=0`, `gatekeeper_eval_ms_p95=22653ms`, `gatekeeper_lock_wait_ms_p95=0`, `gatekeeper_model_call_ms_p95=22653`이다.
  - 근거(12:00~14:00 raw): `ENTRY_PIPELINE` raw 집계 기준 `budget_pass=1882`, `latency_block=1882`, `order_bundle_submitted=0`, `entry_armed=5`, `entry_armed_expired_after_wait=178`이다. 같은 구간 latency block은 `quote_stale=False 1817건`, `quote_stale=True 65건`, danger overlap은 `spread_too_wide=1380`, `ws_jitter_too_high=566`, `ws_age_too_high=217`, `quote_stale=65`다.
  - 근거(품질/손익): `trade_review_2026-04-23.json` (`saved_snapshot_at=2026-04-23 14:01:52`) 기준 `completed_trades=2`, `full_fill_events=2`, `partial_fill_events=0`, `avg_profit_rate=-0.47%`, `realized_pnl_krw=-10317`, open trade는 0이다. 손익 표본은 `COMPLETED + valid profit_rate` 2건만 사용했고 partial fill은 합산하지 않았다.
  - 근거(fallback): `2026-04-23 12:00~14:00 KST` raw 로그에서 `fallback_scout/main`, `fallback_single` 신규 회귀는 0건이다.
  - why: spread relief canary가 켜진 상태에서도 제출은 12시 이후 0건이고, fresh quote 구간의 spread 차단이 계속 지배적이다. 다만 실제 canary 통과 로그는 실전 후보에서 0건이며, `latency_canary_reason`은 `spread_only_required=964`, `low_signal=842`, `quote_stale=65`, `missing=11`로 나뉜다. 특히 `fresh spread-only` 964건 중 `ai_score>=85` 표본이 0건이라 `min_signal=85` 조건이 실제 제출 회복을 만들지 못했다. 따라서 전역 완화나 즉시 확대가 아니라 장후에 `min_signal/tag/allowlist`와 `spread_only_required` 조건을 분리 재판정해야 한다.
  - 검증 메모: 당시 수동 점검 중 `PYTHONPATH=. .venv/bin/python -m src.engine.run_monitor_snapshot --date 2026-04-23 --profile intraday_light`로 갱신 시도가 있었고, 프로세스가 산출물 생성 후 종료 반환 없이 잔류해 PID `112774`를 수동 종료 처리했다. 현재 운영 방침은 wrapper 강제 실행이므로 동일 케이스 재현 방지 위해 동일 실행은 `run_monitor_snapshot_safe.sh` 경로로만 수행한다.
  - 운영 보정: 직접 CLI는 timeout 보호가 없으므로 장중 표준 실행은 `deploy/run_monitor_snapshot_midcheck_safe.sh 2026-04-23`로 보정한다. wrapper는 `timeout`과 lock을 갖고 있으며, `bot_main.py` 감지 패턴을 실제 `python bot_main.py` 실행 형태까지 잡도록 수정했다.
- [x] `[HoldingSoftStop0423] soft stop forensic baseline 수집 필드 반영 + 테스트` (`Due: 2026-04-23`, `Slot: INTRADAY`, `TimeWindow: 13:55~14:15`, `Track: AIPrompt`) (`실행: 2026-04-23 14:08 KST`)
  - Source: [sniper_post_sell_feedback.py](/home/ubuntu/KORStockScan/src/engine/sniper_post_sell_feedback.py), [sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정 기준: 장후 분석 전에 `scalp_soft_stop_pct` 케이스에 대해 `peak_profit`, `held_sec`, `current_ai_score`, `soft_stop_threshold_pct`, `same_symbol_soft_stop_cooldown_would_block`, `1/3/5/10분 sell/buy 재상회`가 post-sell candidate/evaluation/report에 남도록 코드 경로를 반영한다.
  - 판정: 완료. soft stop forensic baseline에 필요한 수집 필드를 장중부터 누적되게 반영했다.
  - 근거: `sniper_state_handlers.py` exit_signal 경로에서 마지막 청산 문맥(`peak_profit/held_sec/ai_score/threshold/cooldown`)을 stock에 보존하고, `sniper_execution_receipts.py` sell_completed에서 이를 `record_post_sell_candidate()`로 넘기도록 연결했다. `sniper_post_sell_feedback.py`는 `rebound_above_sell`, `rebound_above_buy`, `overshoot`, `tag/held_sec/peak_profit bucket`, `cooldown overlap`까지 리포트 `soft_stop_forensics`로 직렬화한다.
  - 테스트/검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_post_sell_feedback.py` 기준 신규 `soft stop forensic` 케이스 포함 통과.
  - why: 오늘 장중 표본부터 `soft stop rebound miss`를 정량화해놔야 장후 HOLDING 판정에서 감각이 아니라 `-1.5% 적정성 / rebound above sell,buy / cooldown overlap`으로 바로 닫을 수 있다.
- [x] `[LatencyOps0423] runtime env override provenance 1차 점검` (`Due: 2026-04-23`, `Slot: INTRADAY`, `TimeWindow: 11:55~12:05`, `Track: Plan`) (`실행: 2026-04-23 11:57 KST`)
  - Source: [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py), `/proc/<pid>/environ`
  - 판정 기준: 현재 봇 프로세스의 실제 env와 저장소 내 `.env`/service/compose 흔적을 확인해 `constants.py` 기본값과 충돌할 override가 존재하는지 점검한다.
  - 판정: 완료. 현재 main bot 런타임에는 `KORSTOCKSCAN_*` override가 보이지 않는다.
  - 근거: PID `91091`의 `/proc/91091/environ`에는 `PATH`만 확인됐고 `KORSTOCKSCAN_*`, `OPENAI_*`, `GEMINI_*`는 없었다. 저장소 기준으로는 [src/run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)가 env export 없이 `python bot_main.py`만 실행하고, `docker-compose.yml`은 DB만 정의한다. `deploy/systemd/*.service`는 웹 서비스용이며 bot_main 실행 경로는 아니다.
  - why: 이 결과는 "현재 세션/프로세스 기준"이다. 과거 다른 세션에서 override가 있었다 해도 지금 PID 기준 런타임은 기본값 충돌 상태가 아니며, hidden env 때문에 오늘 live 판정이 즉시 무효라고 보긴 어렵다.
- [x] `[LatencyOps0423] 14시 entry_armed -> submitted latency/quote freshness 중간점검` (`Due: 2026-04-23`, `Slot: INTRADAY`, `TimeWindow: 14:00~14:10`, `Track: ScalpingLogic`) (`실행: 2026-04-23 14:00 KST`)
  - Source: [run_monitor_snapshot.py](/home/ubuntu/KORStockScan/src/engine/run_monitor_snapshot.py), [sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py), [performance_tuning_2026-04-23.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/performance_tuning_2026-04-23.json)
  - 판정 기준: `12:00 KST` same-day live 교체 이후 `intraday_light` snapshot과 raw `ENTRY_PIPELINE stage=latency_block` 로그를 기준으로 `budget_pass_to_submitted_rate`, `quote_fresh_latency_pass_rate`, `latency_block_events`, `quote_stale=False/True`, `spread_too_wide/ws_age/ws_jitter` 분포, `[LATENCY_SPREAD_RELIEF_CANARY]` 발생 여부를 중간점검한다.
  - 실행 메모: 표준 명령은 `deploy/run_monitor_snapshot_midcheck_safe.sh 2026-04-23`다. 직접 CLI는 timeout 보호가 없으므로 수동 장중 점검에서는 쓰지 않는다. 문서 근거에는 `max_date_basis=2026-04-23`, `evidence_cutoff=14:00 KST`, `trend_max_dates=MONITOR_SNAPSHOT_INTRADAY_TREND_MAX_DATES 또는 기본값`을 함께 남긴다.
  - why: 15:20 POSTCLOSE까지 기다리면 `spread relief canary`가 제출 병목을 풀고 있는지, 아니면 여전히 `quote_fresh/spread/ws_age/ws_jitter`가 막는지 장중 보정 여지를 잃는다. 단, 이 항목은 신규 live 축 추가가 아니라 기존 `spread relief canary` 단일축의 중간 품질 점검이다.
  - 판정: 완료. `entry_armed -> submitted`는 중간점검 기준 회복되지 않았다.
  - 근거: `12:00~14:00 KST` raw 기준 `entry_armed=5`, `budget_pass=1882`, `latency_block=1882`, `order_bundle_submitted=0`, `entry_armed_expired_after_wait=178`이다. 14시 snapshot 누적 기준도 `budget_pass_to_submitted_rate=0.1%`, `quote_fresh_latency_pass_rate=0.1%`라서 12시 이후 제출 회복으로 해석할 수 없다.
  - 근거: `quote_stale=False 1817건` 대 `quote_stale=True 65건`으로 stale quote보다 fresh quote 상태의 spread/jitter/age 차단이 지배적이다. danger overlap은 `spread_too_wide=1380`, `ws_jitter_too_high=566`, `ws_age_too_high=217`, `quote_stale=65`다.
  - 근거: `[LATENCY_SPREAD_RELIEF_CANARY]` 실전 후보 로그는 `12:00~14:00 KST` 0건이다. 테스트 로그는 11:42~11:50에만 존재하므로 실전 제출 회복 근거로 쓰지 않는다.
  - why: 현재 병목은 `quote freshness 없음`이 아니라 `fresh quote에서도 spread_too_wide가 계속 지배`하는 구조다. 단, `fresh spread-only` 964건 중 `ai_score>=85` 표본이 0건이라 canary가 실제 완화 기회를 만들지 못했다. 따라서 다음 액션은 신규 canary 추가가 아니라 장후 `[LatencyOps0423] gatekeeper latency 경로 분해(lock/cache/quote_fresh)`에서 `min_signal=85`, tag allowlist, `spread_only_required` 동반조건을 별도 원인으로 분해하는 것이다.
  - 재점검 (`2026-04-23 14:15 KST`): `12:00~14:00` raw는 `ai_confirmed unique=29`, `entry_armed unique=5`, `blocked_ai_score unique share=96.6%`로 오전 `09:00~11:00`의 `ai_confirmed unique=65`, `entry_armed unique=36`, `blocked_ai_score unique share=95.4%` 대비 upstream 수량이 다시 줄었다. `14:04:30~14:15:17`에는 신규 `ai_confirmed`가 없고 `entry_armed unique=2`만 추가되어, 지금 추가 완화로 제출 회복을 기대할 표본이 없다.
  - 재점검 (`2026-04-23 14:15 KST`): `12:00~14:00` latency block 1882건 중 `latency_canary_reason`은 `spread_only_required=964`, `low_signal=842`, `quote_stale=65`, `missing=11`이며 `fresh spread-only` 964건의 `ai_score>=85` 표본은 0건이다. 즉 코드는 이미 `min_signal/tag/spread_only/quote_stale`로 분해해서 보고 있으며, 지금 가능한 판정은 `min_signal 완화 또는 전역 spread 완화 즉시 적용 금지`다.
  - 다음 액션: 장후 항목에서 `spread relief 유지/롤백/조건 재설계`를 닫는다. 그 전까지는 전역 spread 완화, fallback 재개, 다축 동시 ON은 금지한다.
- [x] `[PlanSync0423] Project 중복 생성 방지 로직 반영` (`Due: 2026-04-23`, `Slot: INTRADAY`, `TimeWindow: 13:40~13:55`, `Track: Plan`) (`실행: 2026-04-23 13:40 KST`)
  - Source: [sync_docs_backlog_to_project.py](/home/ubuntu/KORStockScan/src/engine/sync_docs_backlog_to_project.py), [sync_docs_backlog_to_project.yml](/home/ubuntu/KORStockScan/.github/workflows/sync_docs_backlog_to_project.yml), [2026-04-11-github-project-google-calendar-setup.md](/home/ubuntu/KORStockScan/docs/2026-04-11-github-project-google-calendar-setup.md)
  - 판정 기준: 같은 자동관리 제목의 Project 항목이 2건 이상이면 1건만 유지하고 나머지를 삭제하는 로직과, GitHub Actions 동시 실행 방지 concurrency를 반영한다.
  - 판정: 완료. 중복 정리 로직과 Actions concurrency를 코드/운영문서에 반영했다.
  - why: 04-23 장후 체크리스트 자체에는 `[OpsEODSplit0423]` 항목이 1건만 있으므로, 예시 중복은 문서 중복이 아니라 Project upsert/실행 중복 문제다. 생성 단계와 실행 단계 양쪽에 가드를 둬야 같은 항목이 다시 Todo 2건으로 보이는 왜곡을 줄일 수 있다.
- [x] `[KiwoomAuth0423] REST token invalid 8005 운영 복구` (`Due: 2026-04-23`, `Slot: INTRADAY`, `TimeWindow: 14:43~14:50`, `Track: ScalpingLogic`) (`실행: 2026-04-23 14:45 KST`)
  - 판정: 완료. `8005 Token이 유효하지 않습니다`는 upstream 수량 악화가 아니라 Kiwoom REST 인증 토큰 런타임 만료/무효화 장애로 판정하고, 표준 `restart.flag`로 새 토큰을 재발급해 복구했다.
  - 근거: `kiwoom_orders_error.log`에서 `14:43:56~14:45:41` 예수금조회 실패가 반복됐고, `get_deposit()` 실패 시 주문가능금액이 0원으로 fail-closed되어 매수가 보류됐다. 수동 토큰 발급 테스트는 성공(`len=86`)했고, `14:45:40 KST` 기존 `bot_main.py` PID `107007`에 재시작 플래그를 반영한 뒤 신규 PID `116622`가 `14:46:12 KST` 토큰 발급 성공 로그를 남겼다. `14:46:12` 이후 확인 구간에서는 `8005` 재발이 보이지 않는다.
  - 다음 액션: 장후 `[KiwoomAuth0423] REST token invalid 자동 복구/중복 발급 가드 판정`에서 런타임 `8005` 감지 시 `restart.flag` 기반 우아한 재시작 fallback만 표준 복구 경로로 고정한다. 인증 장애와 별개로 보이는 `kt00007 sell_tp 누락`, `ka10076 URI 불일치`는 같은 항목에서 분리 기록만 하고 canary 판단 근거로 섞지 않는다.

## 장후 체크리스트 (15:20~)

### 주병목 결과 잠금

- 주병목 결과 잠금의 대상은 `entry_armed -> submitted` 제출축이다.
- 아래 항목 중 주병목 판정은 `LatencyOps0423 gatekeeper latency 경로 분해(lock/cache/quote_fresh)` 하나로 읽고, 나머지는 `후순위 축 parking`으로 읽는다.

- [x] `[PlanRebase0423] entry_filter_quality 착수 가능성 재판정` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 15:20~15:35`, `Track: ScalpingLogic`) (`실행: 2026-04-23 16:37 KST`)
  - Source: [audit-reports/2026-04-22-plan-rebase-central-audit-review.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-22-plan-rebase-central-audit-review.md)
  - 판정: `미착수 유지`. 다음 live 축 후보로 올리지 않는다.
  - 근거: `trade_review` 기준 `COMPLETED=2`, `avg_profit_rate=-0.47`, `full_fill=2`, `partial_fill=0`이고, `performance_tuning` 기준 `budget_pass=4373 -> submitted=3(0.1%)`, `latency_block=4370`, `quote_fresh_latency_blocks=4029`, `gatekeeper_model_call_ms_p95=22653`다. BUY 후보는 통과하지만 실제 제출로 이어지지 못하는 비중이 압도적이라 지금 `entry_filter_quality`를 열면 기대값 개선보다 표본 고갈 위험이 더 크다.
  - 다음 액션: 오늘 결론은 `entry_filter_quality` 코드/상수 변경 금지로 즉시 잠그고, [2026-04-24-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-24-stage2-todo-checklist.md)의 `[PlanRebase0424] entry_filter_quality 착수 재판정`에서 `budget_pass`, `submitted`, `quote_fresh_latency_blocks` 3지표가 동시에 완화됐는지 먼저 확인한 뒤에만 후보 복귀를 검토한다.
- [x] `[PlanSync0423] AI 엔진 A/B preflight 범위 확정` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 15:35~15:50`, `Track: AIPrompt`) (`실행: 2026-04-23 16:37 KST`)
  - 판정: `범위 확정, 재개 보류`.
  - 근거: `Plan Rebase` 기준상 오늘 live는 `1축 canary`만 허용이고, 현재 upstream보다 downstream 제출 병목이 커서 A/B는 운영판정 축과 분리해야 한다. preflight 범위는 `main-only`, `normal_only`, `COMPLETED+valid profit_rate`, `full/partial 분리`, `ai_confirmed_buy_count/share`, `WAIT65/70/75~79`, `blocked_ai_score`, `ai_confirmed->submitted`, rollback guard는 `submitted 감소`, `fill quality 악화`, `fallback_regression=0`으로 고정한다.
  - 다음 액션: [2026-04-24-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-24-stage2-todo-checklist.md)의 `[AIPrompt0424] AI 엔진 A/B 재개 여부 판정`에서 오늘 확정한 preflight 범위를 그대로 사용한다.
- [x] `[PlanRebase0423] AI threshold 완화축(score/promote) 승격 조건 재판정` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 17:05~17:15`, `Track: ScalpingLogic`) (`실행: 2026-04-23 16:37 KST`)
  - Source: [2026-04-23-stage2-todo-checklist.md](./2026-04-23-stage2-todo-checklist.md)
  - 판정: `보류`.
  - 근거: `wait6579_ev_cohort` 기준 `approval_gate.min_sample_gate_passed=false`, `full_samples=305`, `partial_samples=1`, `threshold_relaxation_approved=false`이고, `performance_tuning` 기준 `gatekeeper_decisions=33`, `gatekeeper_eval_ms_p95=22653ms`인데 같은 시점에 `budget_pass_to_submitted_rate=0.1%`라서 threshold보다 제출 병목이 훨씬 크다. 시간대 감소 역시 기존 intraday decay 범위 설명이 가능해 `score/promote`를 주원인으로 승격할 근거가 없다.
  - 다음 액션: 오늘 결론은 [2026-04-24-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-24-stage2-todo-checklist.md)의 `VisibleResult0424`/`AIPrompt0424` 항목 입력으로만 사용하고, 전역 threshold 하향은 계속 금지한다.
- [x] `[LatencyOps0423] gatekeeper latency 경로 분해(lock/cache/quote_fresh)` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:30`, `Track: Plan`) (`실행: 2026-04-23 16:37 KST`)
  - Source: [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정: `engine lock 원인 아님`, `quote_fresh + 모델응답 지배`.
  - 근거: `gatekeeper_lock_wait_ms_p95=0ms`, `gatekeeper_ai_cache_hit_ratio=0.0`, `gatekeeper_fast_reuse_ratio=0.0`, `gatekeeper_model_call_ms_p95=22653ms`, `quote_fresh_latency_blocks=4029`, `budget_pass=4373 -> submitted=3`라서 lock 직렬화보다 `quote_fresh/spread`와 느린 모델응답이 먼저 병목이다.
  - 다음 액션: 신규 live 축은 열지 않고, [2026-04-24-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-24-stage2-todo-checklist.md)의 `VisibleResult0424` 판정에서 `spread-only downstream 완화`만 다음 후보로 유지한다.

### 후순위 축 Parking

- 아래 항목들은 주병목 원인 판정이 아니라, `entry_armed -> submitted` 제출병목이 잠긴 상태에서 오늘 승격하지 않을 축을 parking 처리하는 용도다.
- [x] `[KiwoomAuth0423] REST token invalid 자동 복구/중복 발급 가드 판정` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 17:45~17:55`, `Track: ScalpingLogic`) (`실행: 2026-04-23 16:37 KST`)
  - Source: [kiwoom_orders.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_orders.py), [kiwoom_utils.py](/home/ubuntu/KORStockScan/src/utils/kiwoom_utils.py), [kiwoom_sniper_v2.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py)
  - 판정: `restart.flag 우아한 재시작으로 고정`, `auth_zero_qty`를 별도 운영 장애 코호트로 분리.
  - 근거: `logs/bot_history.log`에 `2026-04-23 14:34~14:45 KST` `8005 Token이 유효하지 않습니다`가 반복됐고, 코드에서는 `kiwoom_orders.get_deposit()` 실패 이력을 저장해 `blocked_zero_qty` 중 인증실패 건을 `auth_zero_qty`로 분리했다. `sniper_sync.sync_balance_with_db()`는 런타임 `8005`에서 hot-refresh 대신 `restart.flag`만 세우도록 바꿨다.
  - 다음 액션: 오늘 변경은 리포트/집계 반영까지 완료했고, 추가 일정은 열지 않는다. 기준 검증은 `PYTHONPATH=. .venv/bin/pytest src/tests/test_kiwoom_orders.py src/tests/test_live_trade_profit_rate.py -q`로 닫는다.
- [x] `[AuditFix0423] HOLDING 성과 재판정(missed_upside_rate/capture_efficiency/GOOD_EXIT)` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 15:50~16:00`, `Track: AIPrompt`) (`실행: 2026-04-23 16:37 KST`)
  - 판정 기준: `post_sell_feedback_2026-04-23`의 `evaluated_candidates`, `missed_upside_rate`, `capture_efficiency_avg_pct`, `GOOD_EXIT`와 `trade_review`의 `COMPLETED + valid profit_rate`를 함께 대조해 방향성/승격 여부를 확정한다.
  - 판정: `방향성만 확보`, `승격/완화는 보류`.
  - 근거: `post_sell_feedback` 기준 `evaluated_candidates=2`, `missed_upside_rate=0.0`, `good_exit_rate=50.0`, `capture_efficiency_avg_pct=58.3`이고 `trade_review` 기준 `COMPLETED=2`, `avg_profit_rate=-0.47`다. 표본 2건으로 HOLDING 축 확대나 threshold 조정 결론을 내릴 수 없고, soft stop 1건의 rebound miss는 별도 forensic으로 다뤄야 한다.
  - 다음 액션: [2026-04-24-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-24-stage2-todo-checklist.md)의 `[HoldingSoftStop0424] soft stop cooldown/threshold 재판정`에서 동일종목 재진입/cooldown까지 묶어 다시 본다.
- [x] `[HoldingSoftStop0423] soft stop rebound/threshold forensic baseline 정리` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 17:30~17:45`, `Track: AIPrompt`) (`실행: 2026-04-23 16:37 KST`)
  - Source: [sniper_post_sell_feedback.py](/home/ubuntu/KORStockScan/src/engine/sniper_post_sell_feedback.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [trade_review_2026-04-23.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/trade_review_2026-04-23.json), [post_sell_feedback_2026-04-23.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/post_sell_feedback_2026-04-23.json)
  - 판정: `baseline 정리 완료, 전역 완화 보류`.
  - 근거: `soft_stop_forensics.total_soft_stop=1`, `rebound_above_sell_rate 1/3/5/10m=100%`, `rebound_above_buy_rate 1/3/5/10m=0%`, `median/p95 overshoot=0.0`, `same_symbol_soft_stop_cooldown_would_block=false`다. 손절선 자체보다 동일종목 재진입과 rebound miss의 해석 문제가 먼저다.
  - 다음 액션: [2026-04-24-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-24-stage2-todo-checklist.md)의 `[HoldingSoftStop0424] soft stop cooldown/threshold 재판정`에서 `same_symbol cooldown` 후보를 추가 검토한다.
- [x] `[HolidayCarry0423] AIPrompt 작업 10 HOLDING hybrid 확대 여부 재판정` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:10`, `Track: AIPrompt`) (`실행: 2026-04-23 16:37 KST`)
  - 판정 기준: `holding_action_applied`, `holding_force_exit_triggered`, `holding_override_rule_version_count`, `force_exit_shadow_samples` 관찰축 확보 시에만 확대 여부를 닫고, 미확보면 보류 사유를 고정한다.
  - 판정: `확대 보류 유지`.
  - 근거: `performance_tuning.sections.holding_axis` 기준 `holding_action_applied=0`, `holding_force_exit_triggered=0`, `holding_override_rule_version_count=0`, `force_exit_shadow_samples=0`로 관찰축이 여전히 비어 있다. `post_sell_feedback`도 `evaluated_candidates=2`, `capture_efficiency_avg_pct=58.3`, `good_exit_rate=50.0` 수준이라 표본 2건으로는 hybrid 확대가 기대값 개선인지, 단순 hold 연장인지 분리할 수 없다.
  - 다음 액션: 오늘 결론은 `HOLDING hybrid` live 확대 금지로 즉시 잠그고, [2026-04-24-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-24-stage2-todo-checklist.md)의 `[HolidayCarry0424] HOLDING hybrid 확대 재판정`에서 `holding_action_applied>0` 또는 `holding_override_rule_version_count>0`가 확인되지 않으면 확대 논의를 닫는다.
- [x] `[AuditFix0423] 2026-04-21 미확정 시 AIPrompt 작업 12 Raw 입력 축소 A/B 점검 범위 최종확정` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 15:50~16:00`, `Track: AIPrompt`) (`실행: 2026-04-23 16:37 KST`)
  - 실행 메모: `2026-04-21`에 확정됐다면 상태 확인만 하고 재작성하지 않는다.
  - 판정: `2026-04-21 확정본 유지`.
  - 근거: [2026-04-21-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-21-stage2-todo-checklist.md)에서 이미 `2026-04-21 15:24 KST`에 `ai_confirmed_buy_count/share`, `WAIT65/70/75~79`, `blocked_ai_score`, `ai_confirmed->submitted`, `full/partial 분리`, `COMPLETED+valid profit_rate` 범위가 확정돼 있다. 오늘 다시 쓸 항목이 아니라 `2026-04-24` A/B preflight와 재판정이 이 확정본을 그대로 재사용해야 한다는 의미다.
  - 다음 액션: [2026-04-24-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-24-stage2-todo-checklist.md)의 `[AIPrompt0424] AI 엔진 A/B 재개 여부 판정`은 오늘 재작성 없이 `2026-04-21` 확정 범위를 그대로 입력으로 사용한다.
- [x] `[AuditFix0423] 작업12 범위 미확정 시 사유 + 다음 실행시각 + escalation 경로 기록` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:10`, `Track: Plan`) (`실행: 2026-04-23 16:37 KST`)
  - 판정: `해당 없음`.
  - 근거: 바로 위 항목이 이미 `확정` 상태라서 미확정 사유/escalation 분기 자체가 열리지 않는다.
  - 다음 액션: 없음.
- [x] `[ScaleIn0423] PYRAMID zero_qty Stage 1 원격 범위/feature flag/rollback guard 확정` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:10~16:20`, `Track: ScalpingLogic`) (`실행: 2026-04-23 16:37 KST`)
  - 판정 기준: `SCALPING/PYRAMID only`, `main-only`, `flag OFF code-load tonight`, `zero_qty/cap_qty/floor_applied` 관찰 로그 필수
  - 판정: `오늘 밤 코드 적재까지 진행, live ON은 내일 단일축 판정`.
  - 근거: `Plan Rebase` 기준은 `main-only`, `1축 canary`, `shadow 금지`다. 그래서 기존 `remote canary 후보` 해석은 폐기하고, 오늘은 `SCALPING/PYRAMID`에서만 `buy_qty=1`일 때 `floor_applied` 관찰이 가능한 Stage 1 코드를 `flag OFF`로 적재한다. `auth_zero_qty`는 인증장애 분리 코호트이고, Stage 1은 예산이 남았는데 `template_qty=0`인 케이스만 다룬다.
  - 다음 액션: 오늘 코드 적재 후 [2026-04-24-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-24-stage2-todo-checklist.md)의 `ScaleIn0424` 항목에서 `flag OFF 유지 증적 -> PREOPEN env/restart 확인 -> POSTCLOSE live ON 승인/보류` 순서로 닫는다.
- [x] `[ScaleIn0423] PYRAMID zero_qty Stage 1은 split-entry/HOLDING 관찰축과 분리 유지 확인` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:30`, `Track: Plan`) (`실행: 2026-04-23 16:37 KST`)
  - 판정 기준: 같은 서버/같은 관찰창에 실주문 변경 2축 이상 금지
  - 판정: `분리 유지`.
  - 근거: `Plan Rebase` 기준상 same-day 다축 변경이 금지되고, 오늘도 `entry_filter_quality/HOLDING/EOD`와 섞지 않기로 고정했다.
  - 다음 액션: [2026-04-24-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-24-stage2-todo-checklist.md)의 `ScaleIn0424` 항목에서 Stage 1을 독립 판단축으로 유지한다.
- [x] `[ScaleIn0423] 물타기축(AVG_DOWN/REVERSAL_ADD) 재오픈 일정 및 shadow 전제조건 확정` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:40`, `Track: ScalpingLogic`) (`실행: 2026-04-23 16:37 KST`)
  - 판정 기준: `buy_qty 분포`, `reversal_add_candidate 표본`, `add_judgment_locked 교차`, `next-week remote shadow-only 여부`를 함께 기록하고, 이번 주 실주문 변경 금지를 명시
  - 판정: `재오픈 일정만 유지, shadow 전제는 폐기`.
  - 근거: `Plan Rebase` 기준상 신규/보완축 `shadow 금지`라서 기존 문구의 `next-week remote shadow-only`는 더 이상 유효하지 않다. `AVG_DOWN/REVERSAL_ADD`는 이번 주 실주문 변경 금지를 유지하고, 다음주에도 canary 후보성만 재판정한다.
  - 다음 액션: [2026-04-24-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-24-stage2-todo-checklist.md)의 `[ScaleIn0424] 물타기축(AVG_DOWN/REVERSAL_ADD) 다음주 착수 재판정`에서 `canary-only 가능/보류`만 남긴다.
- [x] `[PlanRebase0423] position_addition_policy 후순위 설계 초안` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:40~16:50`, `Track: ScalpingLogic`) (`실행: 2026-04-23 16:37 KST`)
  - Source: [audit-reports/2026-04-22-plan-rebase-central-audit-review.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-22-plan-rebase-central-audit-review.md)
  - 판정: `후순위 설계만 유지`.
  - 근거: 오늘 기준 주병목이 여전히 `submitted 단절`이라 `position_addition_policy` live 논의를 열 단계가 아니다. 따라서 상태머신 초안/문서 레벨 후순위 설계로만 남긴다.
  - 다음 액션: [2026-04-24-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-24-stage2-todo-checklist.md)의 `VisibleResult0424` 판정에서 승격축이 없을 때만 후순위 설계 문맥으로 재사용한다.
- [x] `[OpsEODSplit0423] 관찰축 정리 완료 시 KRX/NXT 분리 EOD 청산 시간/실행경로 확정` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:50~17:00`, `Track: ScalpingLogic`) (`실행: 2026-04-23 16:37 KST`)
  - 판정 기준: `partial/rebase/soft-stop` 관찰축이 당일 기준으로 잠겼을 때만 착수한다. `KRX`는 정규장 종료 전 청산 재시도 버퍼를 확보하고, `NXT 가능` 종목은 별도 시간창/경로로 분리해 `sell_order_failed -> HOLDING 롤백 반복` 감소 목표를 수치로 기록한다.
  - 판정: `보류, 내일 재판정`.
  - 근거: today 표본은 `COMPLETED=2`, `partial_fill=0`, soft-stop forensic도 1건뿐이라 KRX/NXT 분리 시간을 지금 확정하면 원인귀속보다 출구축을 앞세우게 된다.
  - 다음 액션: [2026-04-24-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-24-stage2-todo-checklist.md)의 `[OpsEODSplit0424] EOD/NXT 착수 여부 재판정`에서만 다시 연다.
- [x] `[DataArch0423] monitor snapshot raw 압축 검증축 보강(parquet/manifest)` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 18:30~18:40`, `Track: Plan`) (`실행: 2026-04-23 16:37 KST`)
  - 판정 기준: `compress_db_backfilled_files` snapshot 검증을 DB snapshot 테이블 의존에서 parquet/manifest(또는 동등 검증) 기준으로 보강하고, `skipped_unverified` 감소 여부를 기록한다.
  - 판정: `완료`.
  - 근거: `log_archive_service`가 snapshot manifest를 자동 생성하고, `compress_db_backfilled_files`가 manifest 우선 검증을 보게 수정했다. 실데이터 dry-run 결과 `cutoff=2026-04-22`, `pipeline verified=1`, `snapshots verified=20`, `skipped_unverified=0`으로 확인됐고, `deploy/run_monitor_snapshot_safe.sh`는 `bot_main` 동작 중 기존 full manifest가 있으면 duplicate full rerun을 skip하도록 가드했다.
  - 다음 액션: 없음. 검증 기준은 `PYTHONPATH=. .venv/bin/pytest src/tests/test_log_archive_service.py src/tests/test_compress_db_backfilled_files.py -q`와 `PYTHONPATH=. .venv/bin/python -m src.engine.compress_db_backfilled_files --days 1 --dry-run`으로 닫는다.
- [x] 범위 확정 실패 시 `사유 + 다음 실행시각` 기록 (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:05`, `Track: Plan`) (`실행: 2026-04-23 16:37 KST`)
  - 판정: `미확정 0건`.
  - 근거: 오늘 POSTCLOSE 항목은 모두 `판정/보류/후속 일정`으로 닫혔고, 미래 액션은 `2026-04-24` 체크리스트 항목으로 연결했다.
  - 다음 액션: 없음.

## 참고 문서

- [2026-04-22-stage2-todo-checklist.md](./2026-04-22-stage2-todo-checklist.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
- [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)
- [2026-04-20-add-position-axis-trader-review.md](./archive/legacy-tuning-2026-04-06-to-2026-04-20/2026-04-20-add-position-axis-trader-review.md)

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-04-23 11:03:12`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-04-23.md`
- `Trade Review`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Performance Tuning`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Post Sell Feedback`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Entry Pipeline Flow`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
<!-- AUTO_SERVER_COMPARISON_END -->
