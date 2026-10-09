# Main 비상시감시 신호 관측·소비 개선 상세계획 — 2026-10-08

**2026-10-08 후속 구현 상태:** PASS 소비·잔여 병목·430봉·비상시감시를 통합 구현하고 반복 리뷰·회귀를 수행했다. 10/8 구현 완료 때는 배포를 보류했으며, **10/9 후속 사용자 지시로 전체 미커밋 통합 배포가 승인됐다**. 현재 배포·준비 검증 상태는 [통합 배포 리뷰](../audits/main-integrated-uncommitted-deployment-review-2026-10-09.md)에서 확인한다. H4의 수정주가/WS 동등성 미입증 범위는 REST를 유지한다. [구현·검증·한계 기록](../audits/main-pass-residual-history-nonfixed-implementation-review-2026-10-08.md)을 현재 실행 결과로 사용하며 아래의 계획 작성 당시 승인·미실행 문구는 그 시점의 이력이다.

상태: **실제 호출·원천·loader 경계를 대조하여 재리뷰한 구현계획**. 이번 요청은 계획 리뷰·보완이며 코드 구현·정책 발행·배포·재기동을 실행하지 않는다.

## 1. 목표와 실행 owner

비상시감시 후보가 필요한 원천을 갖춘 뒤 발생한 유효 native 신호를 원 5초 안에 기계판정과 Main의 기존 실행 경로로 연결한다. 관측이 부족한 시도, 충분히 관측했지만 조건이 맞지 않은 시도, 발생했으나 만료된 신호를 같은 `no_current_operating_signal`만으로 설명하는 결손을 보완한다. 모든 후보가 ENTER_NOW 또는 주문으로 이어지는 것을 목표로 삼지 않는다.

실행 owner는 [오늘 체크리스트](../checklists/2026-10-08-stage2-todo-checklist.md)의 기존 `DirectFamilySourceRepairMainMechanisticEntry` 하나다. 본 문서 NS0~NS5는 [지연 개선계획 §16](main-post-warmup-latency-rest-ws-bottleneck-remediation-implementation-plan-2026-10-08.md#16-비상시감시-no_current_operating_signal-후속-개선계획)과 [잔여 병목 통합계획 R2b](main-residual-capacity-budget-pass-history-bottleneck-implementation-plan-2026-10-08.md#53-r2b-신호-전달과-준비-단축)의 비상시감시 세부 명세다. 새 OPEN stable ID나 전략 family를 만들지 않는다.

| 기존 owner | 본 계획과의 경계 |
|---|---|
| R0/R2b | native 신호 발생→탐색 관측→Main claim까지의 시계·입력 준비. 본 NS 계약을 같은 구현에 반영 |
| R2a / PB1·PB3 | 보조판정 완료→Main 최종 guard→intent 및 종료 영수증. 별도 완료 worker·주문 owner를 만들지 않음 |
| R1 capacity | 실제 수요에 결속한 계좌 준비. 관측 probe가 계좌 prefetch·provider 호출 권한을 얻지 않음 |
| R4 / [430봉 H0~H5](main-430-bar-shared-history-and-incremental-refresh-implementation-plan-2026-10-08.md) | 분봉 이력 공유·증분 갱신. WS native 60/120초 이력의 대체물이 아니며 NS 구현의 전체 선행 조건도 아님 |
| [compact AC0~AC7](main-auxiliary-compact-contract-intraday-adoption-implementation-plan-2026-10-08.md) | 현재 machine ENTER 이후 보조판정 계약. 완료 연구·등록 목록·prompt를 다시 선발하지 않음 |

상시감시 5종목, 기존 등록 기계정책·원 5초 TTL·FIRST/native 생존 규칙·provider 횟수/간격/불확실 예약과 Main/manual custody·주문/수량/자본/cooldown·원천/hard safety를 유지한다. episode/widget 및 영구 제외 종목을 복구하지 않는다. 경제적 적격성·최소 실체결·양의 EV·새 holdout gate를 이 처리 수리에 추가하지 않는다.

## 2. 근거와 해석 한계

### 2.1 조사 기준

조사 release는 `main-retired-postclose-cleanup-20261008-v1`, commit `0c1f68968906395f12c121862876704afadc1e83`, PID `381039`, start ticks `3597010`이다. 10/8 18:49~19:40 기계 캡처 71개 고유 attempt·37개 비상시감시 종목과 별도 19:59:38 성능 snapshot을 사용했다. 구현 시작 때 최신 release/PID/작업본을 다시 고정하며 이 PID를 현재 실행 중이라고 전제하지 않는다.

원문 위치·읽은 byte 범위는 [원천 요약](../../tmp/no-current-operating-signal-analysis-20261008/source-summary.json), 집계는 [분석 요약](../../tmp/no-current-operating-signal-analysis-20261008/analysis-summary.json), 재현은 [상태 재현 결과](../../tmp/no-current-operating-signal-analysis-20261008/replay-diagnostic.json)에 남았다. 이들은 로컬 scratch 근거이며 영구 보존이나 새 자동화 입력을 뜻하지 않는다. 아래 표에 핵심 사실을 고정하고 NS0에서 구현에 필요한 최소 fixture와 source manifest만 기존 검증 산출물 위치에 보존한다. 원 파일 소실 시 재현 가능한 것처럼 표시하지 않는다.

| 근거 | 확인 내용 | 해석 한계 |
|---|---|---|
| 직접 코드 | `assess(snapshot=None)`가 `BLOCK/no_current_operating_signal` 반환 | 모든 branch가 충분한 입력으로 평가됐다는 뜻이 아님 |
| 현재 callback | 비상시감시 0B도 `observe_normalized`에 전달 | 삼성/5종목 allowlist 누락으로 단정하지 않음 |
| 실제 최근 probe 13건 | WS 대기 15.004~20.000초 후 추가 준비·기계 조회 | 최초 프로세스 워밍업과 별개인 반복 후보 관측 비용 |
| 보존 raw 761행 | 115개 관측 종목 중 위 37종목 71회 조회를 재현; 모두 current snapshot 없음 | 관측 종목 115개를 기계판정 115종목으로 집계하지 않음 |
| 재현된 입력 | 조회 시 structure 결손 71/71, ret60 결손 20/71, native turn 없음 46/71 | 서로 중복되는 특성. 필요한 branch만 평가하며 71건 전체를 원천 결손으로 바꾸지 않음 |
| native 계수 | live other `ready=11, claimed=0`; 재현 누적값은 보존 성능 snapshot 71개에서 일치 | ready에는 실제 가격대 5건과 다른 가격대 6건이 혼재. 11건 모두 실행 가능 기회가 아님 |

실제 가격대에 맞는 재현 신호의 조회 지연은 다음과 같다. 신호 시각·identity는 원문에 남기며 표는 KST다.

| 종목 | signal 시각 | 캡처 attempt | 조회 시 signal age |
|---|---|---|---:|
| 알루코 001780 | 19:07:27.674 | `aims-23181bf7f87e7726b783` | 11.830초 |
| 알루코 001780 | 19:13:11.672 | `aims-b440ad5b596365f49c48` | 14.780초 |
| 알루코 001780 | 19:20:10.275 | `aims-3fc86f344e85c7e6b8e8` | 16.631초 |
| 에스엠벡셀 010580 | 19:26:56.975 | `aims-f86b33507cd988dfca55` | 14.242초 |
| 알루코 001780 | 19:36:48.874 | `aims-93bca1f7ea38061b5ac9` | 8.836초 |

collector의 sequence/epoch와 live callback의 sequence/epoch는 같지 않고, 보존 timestamp는 millisecond 정밀도다. 구독의 전체 생애·누락된 invalid 입력·live 메모리 state까지 복원하지 않았다. FIRST turn 변경도 별도 거절 원인일 수 있다. 따라서 위 5건은 조회 시 유효기간 초과를 뒷받침하는 진단이며 실제 주문 가능성·유일 원인·놓친 수익의 증거가 아니다.

분석 요약 SHA256은 `f18f881e7c94f1f6c55053eb59573efd1a0f25f9d8ef6e832e5561dd0d160871`, 재현 결과는 `10b691c497e92d461b316c03294988064ff84eaa4e68308664aee890454cd1dd`다. 관련 코드 9개의 workspace/release hash가 일치했다. 당시 machine bundle `40fb3ec7d5f44e2e34044f2a14e2d0d06dd6ea264f69b5f1481be899f2a4a689`, v6 family `9ca49866d9042d9954e6bc2f64118eafea9a4b8165458c3d4420069990b1ed8b`는 비교 기준이며 후속 소비 증거를 대신하지 않는다.

### 2.2 계획 작성 중 확인한 추가 코드 경계

- [probe](../../src/engine/scalping/zero_base_probe.py)는 WS 대기→분봉→필요한 tick REST→context→최종 WS refresh→`machine_only` 순서다. BLOCK이면 구독 lease를 반환한다. RECHECK만 제한적으로 유지한다.
- [discovery runtime](../../src/scanners/zero_base_discovery_runtime.py)의 동시 probe 상한은 5, 기존 in-flight timeout은 60초, discovery hint의 입장 freshness는 120초다. 관측 대기만 120초로 늘리면 watchdog이 살아 있는 작업을 먼저 만료시킬 수 있다.
- [AI engine](../../src/engine/ai_engine_openai.py)은 `machine_only`에서도 현재 `claim_snapshot_with_receipt`를 호출한다. 이후 probe 반환에는 실행용 claim 전달이 없고, Main 편입은 새 WATCHING 판정을 요구한다. 이 소비 경계는 코드상 수리 대상이며 위 71건의 실현 원인으로 추가 확정한 것은 아니다.
- [Main attach](../../src/engine/kiwoom_sniper_v2.py)는 result 시각·quote 시각·bundle·capacity를 검사하지만 result 시각은 native event 시각을 대체할 수 없다. probe 종료 직후 REMOVE와 WATCHING REG 사이의 실제 원천 공백도 검증해야 한다.
- [async coordinator](../../src/engine/scalping/scanner_async_eval.py)는 현재 `FixedWatchGeneration` 결과에만 `native_claim`을 보존하고, handler의 별도 native 재검증도 fixed-watch 분기에 있다. 비상시감시 신호를 전달할 때 이 결과·최종 검증 경계까지 확장해야 한다. `ScannerGeneration`을 fixed-watch로 위장해 기존 scheduler 계약을 우회하지 않는다.
- [연속성 함수](../../src/engine/scalping/continuous_reversal.py)의 `connected`는 quality/epoch/sequence를 검사한다. 조용한 거래 간격은 자동 원천 결손이 아니다. 마지막 구독 owner가 떠난 기간은 별도 lifecycle 근거로 구분해야 한다.
- [스캐너 제어 루프](../../src/scanners/scalping_scanner.py)의 `run_zero_base_scanner`는 `drain_results`와 동기 `scan_once`를 같은 thread에서 실행한 뒤 0.5초 sleep한다. 결과 수신은 메모리 queue 적재뿐이고, drain은 queue 전체 snapshot의 fsync 후 promotion을 발행한다. WS 쪽 wakeup만 추가해도 결과 전달이 REST scan/저장 뒤에서 늦어질 수 있다.
- [EventBus](../../src/core/event_bus.py)는 발행 thread에서 callback을 동기 실행한다. 현재 `MACHINE_ENTER_EVENT` callback의 provisional DB/입장 확인은 scanner thread, 최종 scheduler inbox 적용은 Main에서 수행될 수 있다. 이름에 Main이 있어도 callback 전체가 Main thread라는 뜻은 아니다.
- WS exact lease는 범용 reference count가 아니다. `_exact_probe_item_leases[item]`에 단일 `lease_id`와 `adopted/removing` 상태가 있으며, 이미 등록된 borrowed item은 별도 probe REMOVE 권한을 얻지 않는다. REG 기록은 로컬 송신 증거이고 broker ACK가 아니다.
- `run_zero_base_probe`는 같은 lease의 재호출에서도 `registered_epoch=now()`를 만든다. 물리 구독을 유지해도 feature tick 필터가 과거 prefix를 다시 잘라낼 수 있어 lease 시작·현재 attempt 시작·원 native 시각을 분리해야 한다.
- [v6 source validator](../../src/engine/scalping/continuous_reversal_policy_v6.py)의 `contract_modules()`에는 `reversal_extended_runtime/state`, `reversal_current_backend`가 포함된다. 이 파일을 수정한 채 현재 bundle을 그대로 쓰면 `v6_contract_code_changed` 대상이다. 일반 release handoff나 auxiliary reader 호환 영수증만으로 기계 code pin이 갱신되지는 않는다.

## 3. 구현 단계와 변경 위치

새 코드가 필요하더라도 기존 역할 package를 우선 사용한다. `src/engine` root에 새 모듈을 만들지 않는다. 아래 파일의 실제 caller와 반환 소비를 함께 수정한다.

| 단계 | 우선순위·선행 | 변경 owner | 산출물·종료 증거 |
|---|---|---|---|
| NS0 기준 고정 | P0, 최초 | 기존 진단 자료·관련 테스트 | source/정책/PID·clock·branch 요구 이력·caller 목록, 축소 fixture와 합성 구간 표시 |
| NS1 관측 생애 | P1, NS0 | `zero_base_probe`, `zero_base_discovery_queue/runtime`, Main probe caller, WS exact lease | branch별 실제 관측 coverage·bounded residence·watchdog·해제/편입 수명 일치 |
| NS2 신호 적시 판정 | P0, NS0 | 기존 diagnostics/caller adapter·`ai_engine_openai`·probe; pinned backend는 우선 기존 인터페이스 소비 | 비소비 snapshot 관측, 원천 사전 준비, 이벤트 기반 bounded 평가, 원 deadline 유지. pinned 파일 변경은 §9.1 별도 계약 |
| NS3 Main 편입 연결 | P0, NS2 | scanner 제어/결과 queue, Main attach/inbox, `sniper_state_handlers`, `scanner_async_eval` | REST scan과 결과 소비 분리, probe 증거와 실제 claim 분리, Main admission 이후 원 event를 단일 claim·현재 입력으로 독립 판정 |
| NS4 원인·집계 소비 | NS1~NS3와 동시 | 기존 diagnostics·capture/pipeline, `runtime_performance`, 기존 monitor | no-snapshot 원인·선택 scope의 ready 분모·attempt 연결과 unknown 보존 |
| NS5 검증·인계 | NS1~NS4 | 동일 checklist/B7/R5 owner | 반복 리뷰·표적 회귀·release/PID·자연 수용 각각의 증거 |

첫 수리는 **NS0+NS2+NS3와 해당 NS4** 및 기존 길이의 lease 인계·관측 시작시각 보존을 하나의 실제 probe→Main 통합 경로로 닫는다. 이 최소 lease 보완은 P0이며 NS1 장기관측 확대와 분리한다. claim 조회만 앞당기고 probe가 그 신호를 소모하거나 scanner REST/결과 drain 뒤에서 잃는 중간 상태를 완료로 인계하지 않는다. NS1의 장기관측은 watchdog/공정성/구독 계약까지 묶어 별도 검증할 수 있지만, 미완료 상태에서 60/120초 패턴 관측 문제까지 해결했다고 보고하지 않는다. 기존 PASS 소비 PB/R2a 수리를 NS1 완료까지 지연시키지 않는다.

## 4. NS1 — branch별 관측 이력과 제한된 구독 수명

### 4.1 관측 충족 여부

[등록 state](../../src/engine/scalping/reversal_registered_runtime.py), [확장 state](../../src/engine/scalping/reversal_extended_state.py), [정확 정의](../../src/engine/scalping/reversal_extended_catalog.py)에서 선택된 branch의 실제 입력 요구를 추출한다. 정책 정의/hash를 바꾸지 않고 readiness metadata를 기존 소유 위치에 둔다. 300초 drawdown lookback을 모든 branch의 300초 의무 대기로 해석하지 않는다.

| 현재 other_non_fixed AFTER/SOR의 확장 branch | 필요한 실제 입력 | 관측 계약 |
|---|---|---|
| LT_20000 `manual_extended_32242b888bb0a643` | ret60·session·structure, RETEST/FIRST 최대 30초 | 두 30초 구간의 실제 고저 자료와 60초 predecessor, 원 root와 retest 진행을 보존 |
| 20000~100000 미만 `manual_extended_95033e152c7e5287` | ret60·session·drawdown·volume, MOMENTUM 교차 | 60초 수익률 및 현재/이전 60초 수량. 빈 이전 구간을 0 수량으로 만들어 충족시키지 않음 |
| GE_100000 `manual_extended_5c7e6db237e63de0` | ret60·session·structure, RETEST/FIRST 최대 30초 | 원 정의의 tolerance/확인 순서를 유지하고 실제 60초 자료로 검사 |

위 표는 10/8 AFTER 기준이다. NS0에서 PRE/REGULAR와 carried backend까지 실제 선택 목록을 같은 방법으로 연결한다. 모르는 요구를 0초로 기본 처리하지 않는다. 반대로 해당 branch에 필요 없는 구조값 결손을 정상 native/legacy branch 전체의 veto로 올리지 않는다. root가 없다는 FALSE와 root 평가에 필요한 자료가 없다는 UNKNOWN은 detector의 원 truth를 그대로 사용한다.

`observed_seconds` 하나로 충족을 판정하지 않는다. exact symbol/item/route/session/date/transport와 구독 유지 증거, 필요한 window별 row·quantity 유효성·빈 구간, branch의 기존 readiness를 함께 기록한다. WS 체결 간격만으로 임의 gap 임계값을 추가하지 않는다. REST 분봉/collector archive를 live tick window에 채워 넣거나 오래된 event를 다시 발행하지 않는다.

### 4.2 짧은 관측과 장기관측

1. 기존 5개 probe 동시 상한과 전체 WS/감시 cap을 유지한다. 새로운 상시감시 종목을 추가하는 계획이 아니다. Main 보호·체결/계좌 관리와 기존 fixed-watch 구독을 먼저 보존한다.
2. 최초 10/15초 원천 관측 하한·exact 0B 최소 수·0D/BBO·freshness는 유지한다. 같은 lease 내 재확인에는 `subscription_interval_id/start`, `attempt_started_at`, `last_source_received_at`을 구분한다. 현재 `registered_epoch=now()`를 매 호출마다 생성하는 대신 처음 확인된 exact 구독 생애/수신 prefix의 시작을 전달하여 `after_epoch` 필터와 warmup 계측을 일치시킨다. 새 lease·reconnect·실제 REMOVE 이후에는 이전 prefix를 사용할 수 없다. borrowed item의 정확한 지속 관측 증거가 없으면 현재 확인점부터 보수적으로 관측하며 요청 시각을 과거로 위조하지 않는다. 기존 RECHECK의 짧은 재확인 하한은 별도 유지하고 매번 최초 10/15초를 다시 기다리게 하지 않는다.
3. 입력이 부족한 branch를 위해 **제한된 장기관측 lease**를 지원한다. 초기 구현 설계값은 5개 중 최대 2개 장기관측, 나머지는 짧은 탐색용이다. 최대 150초의 절대 residence 안에서 필요한 60/120초 이력과 실제 root 진행을 기다린다. 이 값은 신규 resource scheduling 제안이며 현재 운용값 변경을 뜻하지 않는다. 정책별로 더 짧게 종료할 수 있고, 150초가 됐다는 이유로 부족한 입력을 충족 처리하지 않는다.
4. 장기관측 슬롯은 기존 route/market/activity:gainers 공정 순환 안에서 배정한다. 종목명·최근 수익으로 고정 우선권을 주거나 같은 코드가 연속 재선점하게 하지 않는다. 늦게 들어온 후보의 대기시간·관측 누락을 분모에서 제외하지 않는다. 기존 전체 cap 안에서 장기관측을 배정할 수 없으면 명시적 capacity defer로 남긴다.
5. 5개 전체를 150초씩 점유하면 준비·해제를 제외해도 이론상 분당 2개 후보밖에 처리하지 못한다. 따라서 WS/REST 감소만 보고 성공으로 판정하지 않는다. NS5에서 distinct 후보/분·대기 분포·long/short lease-time·실제 branch coverage를 함께 비교하여 제안 배분을 확정한다. 숫자 조정은 동일 owner의 자원 계약 검토로 수행하며 API/감시 상한을 늘리는 해법을 기본값으로 두지 않는다.
6. no-current 한 번을 이유로 즉시 BLOCK terminal→REMOVE하지 않는다. 원천/branch 관측 미완료인 경우에는 남은 lease 안에서 관측 상태를 유지한다. 유효 snapshot의 실제 BLOCK, 명시 root 종료, session 전환, 원천 불량, 절대 residence 종료는 각기 원 사실로 종료한다. 기존 RECHECK와 중첩된 무한 재시도는 만들지 않는다. 원 machine action을 RECHECK로 바꾸어 구독을 유지하지 않는다.

150초는 관측 자원의 설계 상한이며 모든 늦은 root의 확인을 보장하는 시간이 아니다. 예를 들어 종료 직전에 발생한 retest root의 원 30초 확인창이 lease 밖으로 나가면 `resource_censored` 원인으로 관측 종료를 기록한다. 이를 branch FALSE/신호 만료로 바꾸거나 lease를 새로 시작해 상한을 늘리지 않는다. 120초 자료가 충족돼도 MOMENTUM의 기존 known-false→known-true 전이가 없으면 새 신호를 합성하지 않는다.

### 4.3 watchdog·clock·해제

| 시계 | 역할·보존/보완 |
|---|---|
| discovery hint 120초 | 기존 queue 입장 freshness. 원 observed_epoch/source hash를 보존하며 장기관측 허용을 위해 현재 시각으로 덮지 않음 |
| 기존 in-flight watchdog 60초 | 현재 일괄 abandon을 claim별 lease deadline/worker 상태와 결속. 정상 장기관측을 60초에 재발급하지 않음 |
| probe residence 최대 150초 제안 | 원 lease 시작에서 고정. heartbeat·새 tick·새 panel 관측으로 절대 상한을 갱신하지 않음 |
| native signal 5초 | 원 event epoch 기반 실행 유효기간. probe/result/attach 시각으로 새 5초를 만들지 않음 |
| quote/source freshness | 현행 exact probe 3초와 후단 각 consumer의 기존 bound 유지. residence와 별개 |

watchdog heartbeat는 worker와 lease가 살아 있다는 liveness 증거이며 시장자료의 fresh 증거가 아니다. 현재 pending queue·physical worker slot·WS lease를 같은 claim generation으로 연결한다. 만료/late result는 원 generation에만 정리하고 새 claim의 slot/구독을 해제하지 않는다. timeout 후의 실제 REMOVE 대기와 물리 slot 점유도 보존한다. 재기동에는 observation lease/claim을 실행 권한으로 복원하지 않고 기존 durable queue의 잔여를 명시적으로 정리한다.

진행 상태는 기존 결과 verdict와 분리한 lease 단계 `observing → handoff_pending 또는 cleanup_pending → closed`로 표현한다. `assessed` 관측 결과가 생겼다는 이유만으로 물리 slot까지 해제하지 않는다. queue의 버전·Candidate 필드·snapshot/restore·result 소비자를 함께 변경하여 원 claim별 lease ID/절대 deadline/PID-start/상태/마지막 heartbeat와 종료·인계 참조를 보존한다. 기존 v1 snapshot은 원 바이트를 유지한 읽기 호환/명시적 이관으로 처리하고, 모르는 schema·손상을 빈 queue로 초기화하지 않는다. 이전 PID의 in-flight는 현재 실행 권한 없이 recovery terminal로 정리하며 monotonic 값을 새 PID에서 비교하지 않는다.

terminal을 먼저 `resolve`해 in-flight를 풀어놓고 백그라운드 구독만 남기지 않는다. source gap을 무조건 정상 BLOCK의 180초 재방문으로 보내지 않으며 종료 유형의 기존 60/120/180초 정책과 새 lease 내부 대기를 명시적으로 구분한다. 신규 panel이 claim 도중 들어오면 `claimed_observed_epoch/source_sha256`는 기존 결과의 신원으로 유지하고 새 hint는 다음 입장 후보로만 갱신한다. 120초 hint freshness는 queue 입장 검사이고 이미 유효하게 시작한 lease의 120초 강제 종료/시각 재발급 규칙으로 바꾸지 않는다.

마지막 물리 구독 owner가 제거되거나 reconnect/route/session이 바뀌면 영향 stream의 관측 생애를 끝낸다. shared fixed-watch/Main owner가 남아 있는 경우 probe lease 해제만으로 detector를 reset하지 않는다. 재획득 시 알려진 미관측 기간을 연결된 tick history로 사용하지 않도록 기존 runtime adapter에서 해당 interval의 legacy turn/peak·rolling·pending·ready 전체를 함께 무효화한다. 일부 window만 reset하여 이전 turn을 남기지 않는다. 같은 stream의 v6 및 carried state, 모든 가격대와 claim 생존 검사를 대조한다. lock 획득 후 interval/lease generation을 다시 확인해 늦은 cleanup이 새 구독 state를 지우지 않게 한다. 실제 transport epoch/sequence를 임의 조작하거나 frozen 연구 kernel의 `connected`를 변경하지 않는다. 유효 session anchor·과거 claim/주문 attribution은 보존하고 이미 발급된 claim은 원 validator와 정확한 종료 사유로 처리한다. 이 source lifecycle 보완의 runtime/research 의미·code pin 영향은 NS5와 §9.1에서 따로 검증한다.

## 5. NS2 — 준비된 원천과 ready event를 즉시 연결

목표 경로는 다음과 같다. 화살표는 동기 작업의 직렬화를 의미하지 않는다.

```text
fresh discovery -> exact bounded WS lease -> source preparation + native observation
  -> source-ready AND live eligible-ready
  -> observation-only machine assessment -> Main admission/inbox
  -> one native execution claim -> independent live machine -> auxiliary -> existing Main guard
```

1. exact item/route와 등록 생애를 확인한 뒤 이미 허용된 candle 준비를 WS 관측과 겹치게 배치한다. 430봉 공유는 R4 계약의 검증된 동일-source cache만 사용한다. probe에 허용된 candle/tick source-only 범위를 늘리지 않는다. index/investor/account/provider 조회를 새로 붙이지 않는다.
2. source-ready는 candle 완료 여부만이 아니다. 공통 필수 context·exact 0B/0D·최소 관측이 최종 시각에도 유효해야 한다. native 입력 readiness는 branch별로 검사하며, 실제 hit의 필수 입력이 유효하면 관련 없는 branch의 UNKNOWN 때문에 전체 union을 대기시키지 않는다. source 준비가 끝나기 전에 생긴 신호는 원 deadline 안에 준비가 완료된 경우만 평가하며, 만료한 신호를 보관했다가 부활시키지 않는다. 초기에 지나간 신호는 `source_not_ready_at_signal` 근거로 남길 수 있으나 매수 기회 누락이라고 확정하지 않는다.
3. native ingress에는 작은 ready identity/sequence 알림만 붙인다. WS callback에서 REST·기계 전체 계산·AI·DB·대형 JSON을 수행하지 않는다. 기존 bounded probe executor를 재사용하고 polling 주기를 무조건 줄이거나 probe worker를 늘리지 않는다. source-ready 완료도 같은 이벤트를 깨우므로 native 이벤트가 먼저 왔어도 다음 tick을 기다리지 않는다. event는 알림이고 실제 상태는 detector/lease에 있다. clear 직전 게시·source/ready 도착 순서·batch 잔여·종료 시 wakeup을 검사한다. 스캐너 REST 작업의 격리는 §6.1의 단일 source worker로 별도 제한한다.
4. 준비된 context는 source hash/route/session/완료봉 cutoff로 재사용한다. 신호가 생길 때마다 candle REST를 처음부터 반복하지 않는다. 최종 trade/quote/source refresh와 현재 policy 확인은 생략하지 않는다. 의존성 없는 준비만 기존 source-only 예산 안에서 겹치며 tick은 최종 freshness가 보장되는 시점에 확보한다.
5. `machine_only`의 native 조회를 **상태를 소비하지 않는 snapshot 관측**으로 분리한다. adapter가 backend의 같은 lock 경계에서 선택·price-band·generation·원 TTL·FIRST 생존·claimed 여부를 검사하고 기존 snapshot/proof 함수를 통해 복사본을 반환한다. 현재 native 함수의 FIFO/phase/primary·branch union·`confirmed_set`/`opportunity_key`/source prefix를 그대로 재현하되 `_CLAIMS` 삽입, `ready.claimed=True`, live claim 계수 증가를 수행하지 않는다. FIRST 필터 등은 복사본에만 적용한다. shadow claim을 만든 뒤 삭제하거나 live claim 후 `claimed=False`로 되돌리는 방식은 금지한다. carried backend/v4·v6를 모두 검사한다. pinned selector를 수정해야만 공통화가 가능한 경우는 §9.1의 code-pin 계약을 먼저 닫는다.
6. observer snapshot은 별도 읽기 증거이며 주문 token이 아니다. `analyze_target(machine_only=True)`의 `provider_called=false`, `broker_order_forbidden=true`, `ai_decision_outcome_eligible=false`를 유지한다. 관측 capture/diagnostics가 claim registration을 필수값으로 오해하지 않도록 version/nullable 의미를 함께 고친다. 현재 일반 Main/fixed-watch의 live claim·outbox 경로는 보존한다.
7. live claim이 아직 없는 구간도 원 event epoch+5초에서 남은 예산을 계산한다. [EntryDeadline](../../src/engine/scalping/entry_deadline.py)은 `claim=None, caller_epoch, caller_perf`를 지원하므로 observer를 가짜 claim으로 포장하지 않는다. 최초 신호 참조에서 epoch/perf 쌍과 PID/start를 고정하고 모든 queue/prepare/provider/commit에서 기존 caller bound와 더 이른 값을 전달한다. 현재 [async context](../../src/engine/scalping/scanner_async_eval.py)의 `create()`는 epoch에서 perf를 다시 만들므로 원 caller_perf를 min으로 승계하도록 보완한다. wall clock 역행·새 context·worker 재전달로 monotonic 예산을 늘리지 않는다. 없는 snapshot에는 가짜 deadline/claim을 만들지 않는다. 실제 source/queue/I/O가 예산을 소진하면 해당 event는 종료하며 새 event와 혼합하지 않는다.

## 6. NS3 — probe 결과에서 Main 실행까지 신원과 단일 소비

probe는 후보 WATCHING 편입의 근거만 제공한다. 원 관측 결과를 그대로 실주문 판정으로 승격하지 않고, Main의 현재 원천·정책으로 독립 판정을 유지한다. 같은 native event가 여전히 유효하면 Main이 처음이자 한 번의 실행 claim을 취득할 수 있게 한다.

1. probe 결과→discovery result 소비→`handle_zero_base_machine_enter`→scheduler inbox→WATCHING에 다음 참조를 손실 없이 전달한다: discovery claim generation/source hash, observation attempt/capture hash, exact symbol/item/route/session/date, family/bundle/scope hash, native event/opportunity/epoch/sequence, 원 signal epoch/deadline, observer snapshot digest. `_scanner_runtime_handoff_updates`, 실제 target 생성/refresh의 필드 선택, immutable stock snapshot과 result writer를 함께 검증한다. 아직 없는 live claim/evaluation/intent ID는 null과 생산 전 상태로 둔다.
2. `result_epoch+5초`는 probe 결과 운반 freshness일 뿐이다. attach와 inbox의 지연 경계에서 원 native deadline도 확인한다. 이미 만료하거나 원 path·policy가 바뀌면 이 이벤트에 의한 promotion은 종료한다. 새 native 신호를 발견하면 별개의 신원·관측 근거로 처리하며 이전 probe의 attempt에 끼워 넣지 않는다.
3. Main은 기존 capacity·동일 종목 충돌·소유권/영구 제외·manual veto·bot/session·provisional DB/inbox 규칙을 통과한 후 execution claim을 취득한다. 관측 probe를 위해 WATCHING 자리를 미리 확정하거나 만석일 때 다른 owner를 임의 퇴출하지 않는다. **expected native identity 대조와 claim 취득을 같은 backend lock 아래 원자적으로 수행**한다. 기존 순서로 선택될 ready가 기대 event와 다르면 다른 기회를 선점하지 않고 그 시도를 종료한다. 구형 claim 함수를 호출해 다른 event를 소모한 뒤 token을 폐기하는 구현은 금지한다. 원 선택 순서/동시 branch union·FIRST 생존 의미를 유지하고 관측 후 일부 FIRST만 사라진 경우 현재 유효 subset을 기존 규칙으로 다시 판단한다. observer digest와 live snapshot이 다를 수 있다는 사실을 기록하되 새 event로 대체하지 않는다.
4. claim 취득 후 기존 live `analyze_target`와 async coordinator에 동일 claim을 전달한다. 비상시감시의 `ScannerGeneration`과 별도의 native claim을 함께 보존하고 context의 deadline은 scheduler 원 예산과 native 원 예산 중 이른 값을 사용한다. 현재 fixed-watch에 한정된 `result.native_claim` 보존·최종 native 재검증·ack/정리를 native claim이 있는 scanner에도 연결한다. generation/state/version/route/source 검사와 원 native path/TTL 검사를 모두 통과해야 하며 다른 scanner에 native claim을 새 필수값으로 강요하지 않는다. 신호를 두 번 취득하거나 새 tick으로 native deadline을 갱신하지 않는다. live machine ENTER 이후에만 현재 보조판정이 가능하다. observational ENTER가 live BLOCK/source-invalid로 바뀌면 정확한 새 판단을 남기고 강제 승계하지 않는다.
5. probe→Main 구독 인계는 현재 item별 단일 lease와 `adopted/removing` 프로토콜을 보완한다. reference count가 있다고 가정하거나 중복 registry를 만들지 않는다. `handoff_pending`을 worker finally의 무조건 release와 분리하고, 같은 lease ID·transport·interval의 Main adoption 성공/거절 ACK를 원 worker/queue에 전달한다. borrowed item은 원래 REMOVE 권한이 없음을 보존한다. `adopted=True`만으로 fresh 구독 성공을 선언하지 않으며 실제 Main owner·exact 등록/원천을 확인한다. 이미 REMOVE가 전송됐다면 기존 wire lock의 REMOVE→additive REG 순서를 유지하고 그 사이 원천/신호는 무효화한다. 복구된 REG로 이전 신호를 살리지 않는다. pending attach는 원 deadline·residence 안에 한정하고, ACK/실패 후 자기 lease와 실제 slot을 정확히 한 번 정리한다.
6. 현재 동기 EventBus callback과 Main inbox의 실행 thread를 §6.1대로 명시적으로 분리한다. 이 경로의 DB/target/claim mutation은 Main의 기존 처리 순서와 lock owner로 합류시키며 worker/WS callback에 새 주문 mutation을 만들지 않는다. provisional insert→inbox 적용→최종화 실패의 현재 rollback과 exact event terminal을 연결한다. 기존 ENTRY_LOCK·WS lock·detector lock을 동시에 쥔 채 I/O하지 않는다. 구독 adoption의 future를 Main/ENTRY_LOCK 안에서 동기 대기하지 않고 pending ACK로 처리한다.
7. 재기동/중복 callback/관측 반복에도 기존 live outbox와 canonical opportunity dedup이 실행 권한을 소유한다. observer attempt를 outbox 실행 예약으로 쓰지 않는다. 이미 `claimed`인 신호의 관측은 `already_claimed`로 남기며 새로운 기회를 만들지 않는다. 메모리 source 참조만으로 이전 PID의 claim/예산을 복원하지 않는다.

NS3 완료는 Main claim→live machine→보조→PB/R2a의 기존 최종 소비자까지 통합 stub으로 확인한다. attach 성공이나 기계 capture만으로 실제 제출 연결 완료를 선언하지 않는다. 후단 정상 거절·provider 미호출·uncertain·intent/submit/fill은 별도 단계다.

### 6.1 결과 전달·queue writer·Main thread

아래 연결은 NS3의 필수 P0다. 0.5초 sleep을 event wait로 바꾸는 것만으로 동기 REST scan의 blocking은 해결되지 않는다.

| 구간 | 단일 owner와 변경 | 경계 검증 |
|---|---|---|
| discovery panel HTTP | scanner 소유의 **최대 1개 source fetch worker**로 기존 직렬 fetch를 분리. 기존 scanner thread는 제어 owner로 유지 | panel 1건 in-flight, 중복 scan 없음, 기존 cadence·API budget/전송 순서 유지. 만료 완료·날짜 변경 결과는 원 신원으로 거절 |
| queue 갱신/resolve/저장 | scanner 제어 thread 하나만 수행. source worker는 immutable panel만 반환하고 probe/ACK callback은 queue 적재+wakeup만 수행 | 이전 원장 포맷/새 lease 상태 동시 검증, mutation 경쟁 0. 시장 HTTP를 queue lock 아래 실행하지 않음 |
| probe result drain | 결과·source 완료 이벤트로 깨우고 bounded batch 처리. 다음 scan/dispatch보다 완료 신호 우선 | `_persist`의 필수 atomic write/fsync 순서를 보존하고 저장 완료 후에만 Main으로 handoff. 저장 지연도 원 5초에 포함 |
| `MACHINE_ENTER_EVENT` | callback은 bounded Main inbox 적재+wakeup까지만 수행하도록 해당 경로를 변경 | 현재 EventBus 전체를 비동기로 바꾸지 않음. subscriber 부재/overflow·close race는 silent drop 없이 원 terminal/cleanup |
| Main inbox | 기존 fast exit/계좌·체결 보호/완료 PASS 소비 이후 제한된 attach batch. 현재 admission/DB/target 적용 함수를 공통 호출 | current PID/session/policy/source·원 native deadline을 다시 검사. 보호 처리를 굶기거나 worker가 DB를 변경하지 않음 |
| 인계 ACK | Main→scanner/원 lease의 작은 결과. 제어 owner가 handoff 종료를 기록 | duplicate ACK·late ACK가 후속 claim/lease를 해제하지 않음 |

panel worker는 network 호출량 확대가 아니라 기존 동기 HTTP를 제어 루프에서 분리하는 명시적 예외다. probe 5개 executor·live AI/preparation·계좌/보호 worker와 섞지 않으며 기존 read admission을 그대로 쓴다. source worker를 재시작마다 누적하지 않고 stop/date change에서 원 작업을 drain/cancel하고 늦은 결과를 폐기한다. 새로운 Python 모듈 없이 우선 기존 `src/scanners` owner 내부에서 구현한다.

기존 `_persist`는 전체 queue snapshot을 쓰므로 별도 p95·bytes·fsync를 계측하고 한 bounded batch의 상태 전이를 한 번 저장한다. 필요한 durable 저장을 생략하거나 ACK 전에 물리 slot을 반환해 속도를 얻지 않는다. 저장 후 publish 전 crash는 보존된 handoff-pending과 원 deadline으로 구분하여 `unobservable/expired`로 정리하며, 재기동 때 이전 신호를 주문으로 재생하지 않는다. 그 최소 pending 상태는 기존 queue snapshot 안에 둔다. 새 주문/Provider 원장은 만들지 않는다. 저장 실패 뒤 다음 iteration이 같은 결과를 중복 발행하지 않도록 memory/durable/published 경계를 원 handoff ID로 연결한다.

`closed/runtime-generation` 검사는 EventBus가 복사한 callback이 unsubscribe 뒤 늦게 실행되는 경우에도 적용한다. 각 queue 용량은 실제 in-flight 5개와 제한된 종료/ACK backlog에 결속하고 queue-full은 신규 관측 admission을 defer한다. 이미 생긴 terminal/cleanup을 조용히 버리지 않으며 이 defer를 정책 BLOCK으로 기록하지 않는다.

## 7. NS4 — 원인 영수증과 올바른 분모

### 7.1 no-snapshot 진단

기존 action/reason은 호환성을 유지하고, source diagnostics에 아래 사실을 추가한다. 새 전략 verdict·매매 veto·새 대형 원장을 만들지 않는다.

| 필드군 | 최소 기록 |
|---|---|
| 요청 신원 | PID/start, discovery/observation/live attempt의 명시적 관계, item/route/session/date, bundle/scope/lease generation |
| 관측 | exact subscription interval, window coverage, 해당 branch의 필수값 결손, detector 원 TRUE/FALSE/UNKNOWN, 조회 시각 |
| 신호 | event/opportunity/원 epoch/deadline, selected backend/cell, candidate 수, already-claimed/expiry/FIRST 변경 근거 |
| 준비·처리 | lease/source-ready/ready publication/peek/machine/attach/Main claim 시각, epoch와 동일 PID monotonic, terminal 또는 as-of pending |

원인 표현은 `state_absent`, `required_window_incomplete`, `no_matching_pattern`, `signal_expired`, `native_path_changed`, `already_claimed`, `scope_or_generation_mismatch`, `unobservable` 등 기존 사유와 대응되는 작은 diagnostic 필드로 둔다. primary는 실제로 막은 가장 이른 경계이고, 나머지 사실은 보조 배열로 둔다. 여러 결손을 서로 배타적인 사건처럼 합산하지 않는다. `no_matching_pattern`은 정확한 detector coverage가 FALSE임을 입증할 때만 사용하며, 알려진 root 부재를 무관한 rolling 결손으로 UNKNOWN으로 바꾸지도 않는다.

snapshot=None의 사유는 해당 조회와 같은 detector lock/clock에서 작은 inspection receipt로 얻는다. 나중에 state를 다시 읽어 원인을 소급 추정하지 않는다. 잠금 안에서는 bounded 필드 복사만 하고 serialization/append는 밖에서 한다. 진단 실패는 `unobservable`과 기존 append 상태로 남기며 새 매매 차단 사유가 되지 않는다. 다만 기존 필수 capture/outbox 저장 실패 계약은 유지한다.

### 7.2 ready와 claim 집계

[runtime_performance](../../src/engine/monitoring/runtime_performance.py)의 현재 B/R 및 모든 가격대 순회로 얻는 raw-ready는 역사 비교용으로 이름/의미를 보존한다. 별도 정의의 selected-ready에는 **실제 confirmation 가격대·현재 선택 backend/scope·policy generation·canonical opportunity**를 적용한다. carried backend와 union 양쪽에서 같은 기회를 두 번 세지 않는다. 동일 확인점의 여러 branch도 한 기회이며 branch별 탐지 기여도는 별도로 유지한다.

`selected_ready`는 주문 가능 신호 수가 아니다. source 준비 전 발생·이미 claim됨·당시 source 불량·Main capacity 거절을 각각 연결한다. window 안 고유 selected opportunity에 대해 `Main claimed / native expired-or-invalidated before claim / pending / unobservable`의 상호배타적 현재 disposition을 두고 carry-in/out을 명시한다. source/관측 부족은 disposition의 원인 필드이고 추가 기회 수로 합산하지 않는다. Main claim 뒤 source·보조·주문 거절은 뒤 단계 분모다.

기존 `entry_machine_capture`/pipeline의 작은 receipt→lifecycle/summary→[buy funnel](../../src/engine/buy_funnel_sentinel.py)·[submission monitor](../../src/engine/monitoring/submission_bottleneck_monitor.py)의 실제 projection/allowlist까지 연결한다. 사용하지 않는 consumer에는 필드를 억지로 추가하지 않으며 구현 시 실제 읽는 위치를 NS0 목록으로 고정한다. 기존 schema와 새 schema의 혼합일·구버전 reader·partial tail·write failure·bounded retention을 검증한다. 과거 71건에 추정 terminal을 써 넣지 않는다.

probe/live capture는 각자의 원 attempt와 source cutoff를 보존하고 `evaluation_role=probe_observation|main_live` 및 부모 관측 참조로 연결한다. probe의 null claim token을 source-invalid로 오분류하거나 live 입력으로 위조하지 않는다. 동일 native opportunity의 probe/live 두 capture를 자연 실행 기회 2개로 합산하지 않으며, 원천 prefix가 바뀐 둘을 동일 AI 입력으로 재사용하지 않는다. 기존 postclose/독립 탐지 consumer의 모집단·outcome eligibility도 확인한다. 진단 지표 개선을 위해 실제 관측 행을 삭제하지 않는다.

진단 계약은 `metric_role=source_quality_gate`, `decision_authority=report_only`, `sample_floor=none`, `window_policy=current_pid_exact_attempt_with_carry_in_out`이며, `forbidden_uses=policy_promotion,order_authority,missed_profit_inference`다. 영수증 coverage와 처리 지연은 운영 수리 지표이고 비용 후 EV/승률은 별도 기존 owner다.

## 8. NS5 — 표적 검증과 수용

### 8.1 필수 반례·실제 caller 통합

| 검증 대상 | 반례와 통과 기준 | 기존 테스트 owner |
|---|---|---|
| 원 시간 예산 | event+4.999/5.001초, 준비 전 event, result가 새로워도 native 만료, FIRST 변경. 기존 경계 그대로 판정·재생성 0 | [reversal policy](../../src/tests/test_reversal_extended_policy.py), [path policy](../../src/tests/test_reversal_path_policy.py) |
| branch coverage | 15초·59/60초·119/120초, 빈 30초 구간, qty 결손, root 부재, union 일부 UNKNOWN/일부 TRUE. branch 정의와 기존 정상 판정 보존 | 위 policy 및 [operating](../../src/tests/test_reversal_operating_policy.py) |
| 비소비 관측 | 반복 peek·동시 live claim·v4 carry/v6·다른 가격대·policy 교체. probe의 `_CLAIMS`/claimed/claim 계수 mutation 0 | 위 policy 및 [probe](../../src/tests/test_zero_base_probe.py) |
| lease/watchdog | 60초를 넘긴 정상 관측, 절대 상한·heartbeat 중단, stale hint, 늦은 결과/REMOVE, session 전환. 실제 slot·queue claim·WS owner 불일치 0 | [queue](../../src/tests/test_zero_base_discovery_queue.py), [runtime](../../src/tests/test_zero_base_discovery_runtime.py), probe |
| 원천 연속성 | 조용하지만 연결된 구독, 마지막 owner REMOVE, 다른 owner 잔존, reconnect/route 변경. 무관 stream reset·가짜 tick/epoch·archive event 재발행 0 | [WS](../../src/tests/test_kiwoom_websocket.py), [continuous](../../src/tests/test_continuous_reversal.py) |
| 실제 편입 | machine_only ENTER→result queue→Main admission→inbox→live claim→독립 기계→보조 stub→기존 guard. 실제 활성 scheduler mode와 생존 호환 mode의 generation+native claim 전달·ACK·최종 native 변경/만료, provider 1회 이하·intent 1회 이하, probe provider/order 0 | [Main attach](../../src/tests/test_zero_base_main_attach.py), [async bridge](../../src/tests/test_scanner_async_entry_bridge.py), [coordinator](../../src/tests/test_scanner_async_eval.py) |
| 결과 전달의 실제 thread | 지연된 panel HTTP 중 probe 결과 수신, 0.5초 sleep 제거 후 wakeup, 느린 fsync, EventBus 동기 callback·subscriber 소실·queue-full·close race. Main 진입·DB는 지정 thread, queue writer 하나, 저장 전 promotion 0 | [discovery runtime](../../src/tests/test_zero_base_discovery_runtime.py), Main attach, coordinator |
| probe→Main 구독 인계 | `created/borrowed/adopted/removing` 각각에서 finally·Main ACK·REMOVE 완료의 순서를 교차. REG 미래/실패·늦은 cleanup·RECHECK의 기존 prefix 보존 | [WS](../../src/tests/test_kiwoom_websocket.py), probe, Main attach |
| 동일 신호의 원자적 취득 | peek 뒤 타 consumer가 claim, 다른 ready가 먼저 선택됨, 일부 FIRST만 무효, 정책/가격대 변경. 불일치 시 다른 event의 claimed/claim 계수 mutation 0 | reversal/path/operating policy 및 Main attach |
| 시계·복구 | wall clock 전진/역행, observer→context 재생성, PID 교체, queue v1 읽기와 새 schema, late ACK·duplicate result, persist 후 publish 전 crash. 원 perf bound 연장·이전 신호 재실행 0 | queue/runtime, coordinator, [deadline 회귀](../../src/tests/test_main_rest_ws_latency.py) |
| 자원·공정성 | 5개 상한, long/short 경쟁·activity:gainers 순환·동일 코드 중복·Main capacity 만석·영구 제외. 기존 owner 퇴출/무신호 capacity HTTP 0 | 위 runtime/Main attach 및 [watch budget](../../src/tests/test_scalping_watch_budget.py) |
| 진단·집계 | all-band 11/selected 5 fixture, carry 중복·다중 branch·pending/expiry·write error·과거 unknown·probe/live 동일 기회·null claim token·scope 변경. 분모 보존·현재사유 소급 추정 0 | [latency](../../src/tests/test_main_rest_ws_latency.py), [capture](../../src/tests/test_entry_machine_observation.py), [monitor](../../src/tests/test_submission_bottleneck_monitor.py) |
| code pin·적용 | 현재 bundle에서 pinned 파일 변경 거부, unpinned adapter 변경의 현재 bundle loader, 필요 시 code-only successor의 부모 CAS·날짜·scope/auxiliary binding·재기동 및 중복 권한 방지 | reversal/operating policy, 기존 handoff 영향 회귀 |

5개 지연 사례는 보존된 원 시간만 고정한 회귀와 합성된 정상 원천/반례를 분리한다. 시간 이동으로 과거 실패를 성공한 실제 거래처럼 만들지 않는다. deterministic clock·provider/broker stub으로 경합·원 budget을 검증하고 유닛 helper만 통과한 상태로 닫지 않는다.

Kiwoom 요청/parser/FID/REG/REMOVE/recovery를 실제 수정하기 전에는 [공식 reference gate](../kiwoom-api-data-contract.md)의 최신 upstream SHA·조회 시각·관련 `kiwoom_docs` 및 SDK/core/realtime/Postman 경로를 기록한다. 이번 문서는 wire 프로토콜의 새 의미·공식 허용 구독 수를 주장하거나 그 검증을 실행한 기록이 아니다. exact lease 제어만 바꾸더라도 REG/REMOVE 경계의 영향 범위를 먼저 확인한다.

구현 검증은 `.venv/bin/python -m pytest`로 위 영향 테스트를 선택 실행하고 수정 Python compile·`git diff --check`를 수행한다. baseline/code pin에 영향을 주는 source adapter·machine caller는 관련 loader/compatibility 검사를 추가한다. 정의·정책 목록을 재선발하거나 새 연구/provider 호출로 검증을 대체하지 않는다. 리뷰→보완→재리뷰→표적 회귀를 반복해 미해결 in-scope 결함을 닫는다.

### 8.2 성능과 자연 수용

R2b의 기존 목표 `native-ready→claim p95 ≤250ms`, `signal→machine capture p95 ≤1초`, `coordinator ready→Main guard p95 ≤100ms/p99 ≤250ms`를 재사용한다. 이는 성능 목표이며 새로운 거래 차단 임계값이 아니다. 비상시감시는 `source_ready_at_event`, `source_became_ready_within_original_deadline`, `source_not_ready_before_deadline`를 실제 clock으로 구분한다. 앞의 두 신호→Main 지연을 서로 섞지 않고 제시하며 전체 selected-ready의 pending/expiry·Main capacity 거절도 함께 보고한다. 첫 분모의 빠른 표본만 전체 개선율로 제시하지 않는다.

위 claim과 machine capture 목표는 실제 Main 실행 경로의 시각이다. probe의 비소비 snapshot/관측 capture는 별도 구간으로 기록하고 두 기계 캡처를 합쳐 처리량을 부풀리지 않는다. `no_current_operating_signal` 건수 0이나 ENTER 증가율을 완료 조건으로 삼지 않는다. 정상적인 무신호와 입력 결손을 구별하면서 실제 유효 신호의 처리 지연을 줄이는 것이 수용 대상이다.

`ready→probe peek→관측 capture→result enqueue→scanner take/persist→Main inbox take→adoption ACK→live claim→live capture`의 각 clock과 queue wait를 기존 stage 계측에 연결한다. `persist→publish` 사이 만료, 느린 panel fetch 중 결과 처리, 후단 live 준비에서 동일 candle 재조회가 발생하는지를 실제 caller 통합에서 검사한다. probe에서 준비한 candle/context는 immutable source/cutoff 참조만 전달하여 기존 cache 계약이 허용할 때 재사용하고, Main의 현재 source refresh와 정책 재판정을 건너뛰지 않는다.

검증 창은 같은 session/route/등록 generation·동종 후보 부하를 가진 전후 release/PID의 워밍업 제외 구간이다. 최초 프로세스 준비는 별도 표로 분리하되 반복 probe 15~20초 대기와 장기관측은 운용 비용에 포함한다. 자연 표본 수·개별 지연·p50/p95·미관측을 명시하고 작은 N의 p99를 일반화하지 않는다.

종료 기준:

1. 충분한 실제 원천·유효 신호를 준 통합 fixture가 원 5초 안에 Main의 단일 실행 경로로 도달하며 기존 거절·수량·주문·source guard를 모두 유지한다.
2. probe가 실행 claim을 선점하지 않고, 동일 native 기회의 중복 provider/outbox/intent가 없다. 실제 결과의 거절도 같은 원 신원으로 남는다.
3. 필요한 branch의 60/120초 coverage를 사실대로 표현한다. 미성숙·미지원 branch를 정상 미충족으로 숨기거나 한 branch 결손으로 전체 기회를 차단하지 않는다.
4. current selected-ready→Main claim/만료/변경/pending/unobservable 연결과 no-current 원인 coverage를 입증한다. 자연 구간에서 미연결 건이 있으면 원인·owner를 남기며 완료로 숨기지 않는다. raw-ready 11을 과거 실행 가능 11로 재표기하지 않는다.
5. 후보 처리량·대기/lease-time·WS callback 지연/구독 churn·read HTTP physical·Main/holding/exit 지연을 함께 비교한다. 필수 source 품질과 실행 가능 후보 coverage가 악화되는 자원 배분은 성공으로 채택하지 않는다. 아직 관측하지 못한 session은 `not_observed`다.

정상 패턴 미발생은 valid-empty일 수 있다. 자연 유효 신호가 없으면 코드/배포 확인과 자연 경로 미관측을 분리한다. 실주문·체결·수익 발생을 강제로 만들거나 이 source/latency 수리의 경제적 승인 조건으로 붙이지 않는다.

## 9. 배포·복구·문서 인계

### 9.1 machine code pin과 reader 호환

기본 구현은 현재 정책에 pin되지 않은 기존 diagnostics/WS·scanner·Main caller adapter에 둔다. `reversal_current_backend`, `reversal_extended_runtime/state` 등의 내용을 바꾸지 않고 검증된 기존 snapshot/claim 함수와 상태 계약을 사용한다. read-only inspection을 위해 pinned callback 전체를 복제하거나 오류를 숨기는 compatibility wrapper를 만들지 않는다. 동일 retained prefix에서 probe 관측과 원 live 선택의 identity·valid branch·source/proof parity를 검증한다. lifecycle 종료 처리는 원천 adapter의 명시적 경계로 기록하며 detector의 경제 조건을 변경하지 않는다.

NS0에서 변경 파일과 v6의 실제 `contract_modules()`·auxiliary reader hash 목록을 대조해 다음 중 하나를 확정한다.

| 변경 종류 | 필요한 인계 | 금지할 우회 |
|---|---|---|
| machine pin 밖의 caller/원천 adapter | 현재 machine bundle을 수정하지 않고 새 release의 실제 loader·source 생애·native parity 검증. 영향받은 보조 reader는 그 기존 호환 계약만 적용 | reader 검증 PASS를 실제 PID 소비로 대신하거나 예전 caller만 소비한 상태를 새 수리 적용으로 표시 |
| pinned 기계 파일 변경이 불가피 | **versioned v6 code-only successor와 loader/activation 지원을 같은 변경 범위에 포함**. 기존 지원 여부를 먼저 확인하고 미지원이면 해당 구현 없이는 변경 코드 cutover를 닫지 않음 | 기존 family의 hash만 고쳐 current에 덮기, `v6_contract_code_changed` 무시, auxiliary 호환 영수증을 기계 pin 예외로 전용 |

code-only successor가 필요하면 부모 bundle·origin source/publication/effective 날짜·원 연구/초기 등록 근거를 보존하고 실제 repair 작성/효력 시각·검토 코드 SHA·변경 파일/hash·부모 CAS를 별도 결속한다. 등록 branch/필터/auxiliary arm·provider 계약은 동일하게 유지하되 code hash에 종속된 scope execution hash·manifest·보조 overlay의 참조는 검증된 successor로 일관되게 이관한다. 기존 단일 canonical opportunity와 uncertain/outbox 권한은 새 scope hash 때문에 reset하지 않는다. 부모 current 동시 교체·이전 PID의 late 결과·half-applied overlay·rollback을 검증한다.

[현재 intraday 등록 함수](../../src/engine/scalping/reversal_extended_intraday.py)는 지정된 13개 ADD와 해당 등록 승인을 처리한다. 이를 code-only 갱신 API라고 가정하여 같은 ADD를 재발행하거나 그 등록 승인 문구를 다른 변경 권한으로 전용하지 않는다. 새 경제성 심사나 연구 재호출은 요구하지 않지만, 구현된 schema/loader의 정상 읽기와 당시 유효한 코드/배포 권한은 필요하다. 기존 rollout 지시가 유효한 범위에서는 다시 승인을 묻지 않는다.

### 9.2 실행·복구 경계

실행 지시가 있을 때 NS5를 통과한 변경만 기존 B7/R5 handoff로 인계한다. 이미 유효한 별도 승인 범위는 보존하고 문서 작성으로 새 runtime 권한을 생성하지 않는다. 선택 release·실제 PID cwd/start·loader/정책/overlay hash·exact-date 준비는 각각 검증한다. 변경된 caller/source code pin의 호환 근거와 필요한 장중/다음 기동 준비만 갱신하며 EOD/장후 전체 연구를 중복 재생성하지 않는다.

복구는 실패한 장기관측/이벤트 인계의 신규 부분에 한정한다. 실제 pending/uncertain outbox·기존 Main 소유권·원 event/claim/intent 이력은 보존한다. observer snapshot을 live claim으로 복원하거나 만료 이벤트를 다시 실행하지 않는다. source continuity·dedup 수리가 포함된 호환 release를 사용하고 퇴역 episode/widget 또는 알려진 중복 실행 경로를 복구하지 않는다. 장기관측을 닫는 동안에도 자기 lease의 물리 해제와 기존 Main owner 유지까지 확인한다.

체크리스트는 현재 봉인 SHA `4aee28ee1c0fa26d34d8f7f7ecac25432e6680ab226ec805c59b635bb11b48ed`를 유지한다. 실행 일정·새 OPEN을 이 문서에 따로 만들지 않고 기존 owner가 연결한 B0~B7 문서 §16에서 본 상세계획을 찾도록 한다. 후속 날짜에 실제 실행이 넘어가면 당시 checklist의 동일 stable ID로 원 Acceptance/검증 이력을 인계하고 유일한 parsed owner를 확인한다. 이번 문서 작업에서는 checklist/AUTO·README/runbook/Rebase/prompt/AGENTS를 수정하지 않는다.

## 10. 계획 자체의 리뷰 기록

계획 검토에서 다음 공백을 보완했다: snapshot 부재를 정상 패턴 미충족으로 단정하는 문제, 관련 없는 branch 결손의 전역 veto, 60초 watchdog과 120초 관측의 충돌, 5개 장기관측의 후보 처리량 감소, machine-only의 실행 claim 선점, result 시각에 의한 원 TTL 연장, probe REMOVE와 Main REG 사이의 구독 공백, aggregate ready의 가격대/backend 중복, 과거 raw 재현과 실제 실행 증거의 혼동.

후속 재검토에서 source-ready를 전체 branch의 이력 충족으로 오해하지 않도록 공통 원천과 개별 branch readiness를 구분했다. 또한 현 async result가 fixed-watch native claim만 보존한다는 경계를 확인해 scanner generation을 유지한 claim 전달·최종 native 검증·ACK와 target/inbox의 실제 필드 선택을 NS3/통합 반례에 추가했다.

문서 검증과 후속 코드/운영 수용을 분리한다. 로컬 링크/anchor·기존 stable ID owner·권한 경계·print-only parser·diff 검사를 수행하며, 문서 작성 중 pytest/compile·provider/broker 호출·장후 재생성·배포/재기동·외부 sync는 실행하지 않는다. 실제 코드 검증·자연 성능 수용은 NS0~NS5의 미완료 작업이다.

최초 계획 문서 검증은 로컬 링크 97개/anchor 3개 결손 0, print-only parser 22항목·현재 Main owner 1개·stderr 경고 0, diff/공백 검사를 통과했다. 다음 재리뷰의 검증은 변경 후 바이트를 대상으로 별도 기록한다.

### 10.1 호출 경로 재리뷰의 보완

| 발견한 구현 공백 | 보완 계약과 종료 반례 |
|---|---|
| ready wakeup 뒤에도 scanner의 동기 REST·0.5초 주기·fsync에서 결과가 늦어질 수 있음 | §6.1: source fetch 1개와 scanner 제어 owner 분리, 결과 event/단일 queue writer, 저장·Main inbox까지 원 deadline |
| EventBus callback이 Main thread라는 암묵적 가정 | §6.1: 실제 발행 thread 명시, callback은 enqueue, admission/DB/target은 Main 처리 경로로 연결 |
| 없는 reference count에 기댄 구독 인계 | §6: 단일 lease의 created/borrowed/adopted/removing과 ACK/finally 경합, REMOVE가 시작된 interval의 신호 무효 |
| 같은 lease에서 호출마다 `registered_epoch` 재설정 | §4.2: interval 시작·attempt 시작·수신 clock 분리, retained prefix와 RECHECK floor 보존 |
| peek와 claim 사이 다른 ready를 소모할 위험 | §6: expected identity 비교와 native claim을 같은 lock에서 수행, 동시 claim·부분 FIRST 무효 반례 |
| epoch에서 새 perf deadline을 만들어 예산이 늘 수 있음 | §5/§8: 최초 caller_perf를 min으로 승계, wall clock 역행·context 재생성 반례 |
| 관측시간만 늘리고 queue schema/restore·late ACK는 미정 | §4.3/§6.1: observing/handoff/cleanup 수명, 기존 snapshot 이관·단일 writer·crash 복구 |
| pin된 E/D/state를 수정해도 기존 handoff면 충분하다는 공백 | §9.1: 기본 unpinned adapter와 필요 시 code-only successor 구분, 현재 ADD publisher/auxiliary 호환의 범위 제한 |
| probe와 live capture의 중복 분모·장기 lease 끝의 FALSE 오분류 | §4.2/§7/§8: resource censoring과 evaluation role, 독립 source cutoff/시계·전체 opportunity 분모 |

이 표는 계획 결함의 수정 기록이다. 당시 PID에서 새 실제 실패 건수를 확인하거나 위 코드가 이미 구현됐다는 뜻은 아니다. 정책·정의·5초/원천/주문 가드는 유지한다.

재리뷰 검증 결과: 변경 문서 3개의 로컬 링크 **106개/anchor 3개 결손 0**, print-only parser **22항목·현재 Main owner 1개·경고 0**, `git diff --check`·공백/코드블록 검사를 통과했다. 체크리스트 SHA는 위 봉인과 동일하며 상위·통합계획의 다른 본문도 작업 전 사본과 대조해 보존했다. 코드 pytest/compile·실제 source/provider/broker 호출·정책 발행·배포/재기동·외부 sync는 수행하지 않았다. 제안된 관측 배분과 성능 목표의 실제 수용, code-pin 변경 필요 여부는 NS0/NS5 실행 증거로 남긴다.

## 11. NS0~NS5 구현·리뷰 결과

probe는 native snapshot을 비소비 관측하고 Main이 현재 원천·DB 입장·원 event를 검증한 후 claim한다. 관측 lease는 총 5개 이내에서 최대150초 2개/60초 나머지로 나누며 최초 deadline을 갱신하지 않는다. panel 수집과 결과 제어를 분리했고 Main bounded inbox와 원 PID/start/epoch/perf를 사용한다. 결과 저장 실패 후 재시도와 REMOVE 실패도 동일 lease를 유지하며 확인된 종료에서만 큐/물리 슬롯을 반환한다. 관측 원인/selected-ready 분모를 추가했으며 전체 시장의 신호 모집단으로 해석하지 않는다. NS5 작업본 검증과 정책 27개 code pin 일치를 확인했고 배포/PID/자연 통과율은 후속 지시 대상이다.

검증 수치·수정한 반례·공식 API SHA·배포 보류 경계는 [통합 실행 리뷰](../audits/main-pass-residual-history-nonfixed-implementation-review-2026-10-08.md)에 한 번 기록한다. 실행 owner는 기존 `DirectFamilySourceRepairMainMechanisticEntry`를 유지하며 이번 작업은 checklist 봉인/현행 정책을 재발행하지 않는다.
