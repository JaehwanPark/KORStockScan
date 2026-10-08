# Main 워밍업 이후 평가 지연·REST/WS 병목 개선 상세 구현계획 — 2026-10-08

## 1. 결정·범위·실행 owner

실제 상시감시 caller의 비동기 연결과 AI 실패 집계를 먼저 수정한다. 이어 소유권 저널의 반복 계산, WS 공유 lock의 복사, 분봉 REST 반복 조회, Telegram에 유입된 전역 HTTP 캐시를 개선한다. 각 변경은 같은 원천·정책·안전 계약에서 처리 비용을 줄이고 정상 `ENTER_NOW → 보조판정 → Main 최종 검증` 경로를 복구하는 작업이다.

최초 작성은 **상세계획 리뷰·보완**이었다. 이후 사용자가 compact 계획과 함께 구현·반복 코드리뷰·수정보완 및 완료 후 배포·재기동을 승인했다. 실행 결과는 [통합 구현 리뷰](../audits/main-post-warmup-bottleneck-compact-integration-review-2026-10-08.md)에 구분하여 남긴다. 이미 받은 승인을 다시 요구하지 않으며, 입증되지 않은 REST/WS source 의미 동등성을 추정하지 않는다.

실행 owner는 [오늘 체크리스트](../checklists/2026-10-08-stage2-todo-checklist.md)의 `DirectFamilySourceRepairMainMechanisticEntry` 하나다. B0~B7은 그 안의 구현 단계이며 새 OPEN 항목이나 전략 family가 아니다. 다음 문서의 역할을 유지한다.

| 문서 | 소유 범위와 이번 계획의 관계 |
|---|---|
| [15시까지 PID 206123 관측](../audits/main-pid-206123-post-warmup-latency-rest-ws-monitoring-2026-10-08.md) | 변경 전 실제 PID 증거·워밍업 제외 분모. 과거 기록을 수정하여 개선 결과로 만들지 않음 |
| [평가루프 계획](main-evaluation-loop-latency-remediation-plan-2026-10-08.md) LP7~LP12 | 원 claim·deadline·async Main commit·필수 저장·성능 계약. 이번 B1/B2/B3/B4가 실제 호출 누락과 잔여 비용을 보완 |
| [REST/WS 계획](main-rest-api-ws-substitution-and-load-reduction-plan-2026-10-08.md) RW0~RW6 | 공식 프로토콜·소비자별 source 선택·transport 계측. 이번 B4/B5/B7이 자연 관측 결과를 반영 |
| [compact 장중 채택 계획](main-auxiliary-compact-contract-intraday-adoption-implementation-plan-2026-10-08.md) AC0~AC7 | 네 scope의 codec/registry/요청·응답·발행·승계. B1/B2와 공통 파일의 최종 통합 호출 경로를 검사 |

현재 v6 기계정책·독립 탐지·추가 13개·상시감시 5종목, 보조 binding, 원 5초 claim 및 native 생존 규칙을 출발 계약으로 사용한다. 구현 착수 때 실제 최신 정책·소비 PID를 다시 고정한다. Main/manual custody·수동 veto·broker/account/order/수량/자본/cooldown·hard exit 및 provider 간격/예산/불확실 예약은 보존한다. episode/widget 자동 실행·연구·장후·복구는 영구 퇴역이며 잔여 체결분은 수동관리다. 이 수리에 경제적 적격성·EV·최소 실체결 수·추가 holdout을 붙이지 않는다.

## 2. 확인된 기준선과 추가 코드 검토

관측 release는 `main-rest-ws-latency-20261008-v3`, commit `6f3ee1c02955fa6c50913e8f598ac33904b2bede`, PID `206123`, start ticks `2010467`이다. 실제 소비 bundle은 `40fb3ec7d5f44e2e34044f2a14e2d0d06dd6ea264f69b5f1481be899f2a4a689`다. 이는 15시 관측의 신원이며 후속 배포 때의 current를 대신하지 않는다.

| 근거 | 관측값 | 설계에 반영할 의미 |
|---|---|---|
| 워밍업 제외 | 첫 루프 84.111초와 14:30 이전 제외; 14:30:49~14:59:25 | 동일 기준 snapshot 차이로 비교. 수집은 15시까지, 마지막 35초 전체 성능 계수는 미포함 |
| warm loop | 849회, >5초 11회, >10초 1회; p95 (2,3]초 / p99 (5,10]초 | 초기 기동만의 지연 아님. percentile 구간을 정확한 점값으로 바꾸지 않음 |
| AI 중단 뒤 | 14:44:03 이후 443회 중 >5초 7회 | provider 대기 제거만으로 닫히지 않는 반복 비용 존재 |
| 상시감시 | machine capture/trace join 56/56, ENTER_NOW 7 | WAIT 5 / DROP 2. 호출 2회 이후 복구 증거 없음 |
| async | claim 13, machine 7, 준비 queue/service·source/capacity·Main commit 0 | 함수 정의/생성 성공과 실제 Main caller 연결을 구별 |
| AI 비활성화 | provider timeout 2회 + 미호출 path change 3회 → 14:43:58 disable | 원천 적격성 종료를 provider 장애로 계산하는 오류 수정 |
| Kiwoom HTTP | 1,097 physical attempts 전부 response; timeout/exception 0 | 전송 장애 증거보다 반복 demand·페이지 비용 우선. server 처리 성공과 별개 |
| 분봉 | probe 400 + Main 116 = 516 physical attempts; logical demand/REST 유지 256/256 | 전체 516회를 WS 전환 가능량으로 가정하지 않음 |
| WS lock | 108,657개 중 >50ms wait 1,763 / hold 191; 파일 capture 최대 321.281ms | writer 직렬화 이동 이후 남은 freeze/copy 비용 점검 |
| CPU | Main 평가 24.75%, Telegram 22.09%, tick dispatch 15.54% | 1코어 대비 thread tick 비율. 각 함수의 wall-time 기여율로 사용하지 않음 |

계획 검토에서 원인을 두 가지 더 좁혔다.

1. [분봉 selector](../../src/trading/market/shared_ws_snapshot.py)의 `selected_completed_bar_payload`는 `ws_when_ready`에서 session capacity를 PRE 50 / REGULAR 390 / AFTER 240으로 제한하고, 더 긴 요구를 `requested_history_exceeds_projection_scope`로 REST 유지한다. [entry context](../../src/engine/scalping/entry_candle_context.py)는 `max(limit, SOURCE_BAR_LIMIT=430)`을 요구한다. 따라서 현재 계약은 장시작부터 WS를 수집해도 Main 430봉 요구를 만족하지 못한다. 재기동 직후 이력 부족만의 문제가 아니다. 같은 selector의 homogeneous REST seed는 raw WS와 임의 splice를 금지하고 있다.
2. [시장 국면 service](../../src/market_regime/service.py)의 module import가 설치된 `fear_and_greed` 0.4의 `cnn.py:13`을 거쳐 `requests_cache.install_cache('/tmp/cnn_cache', expire_after=1분)`를 전역 설치한다. 앞선 Telegram SQLite 스택과 cache 파일의 생성 주체가 코드상 연결된다. 이 사실만으로 Telegram 중복 update·명령 손실이나 CPU 22.09% 전부가 cache 때문이라고 결론 내리지는 않는다. 패키지는 import/실호출하지 않고 파일만 읽었다.

위 selector·registry·Main caller·handler·시장 국면 service의 workspace bytes는 조사 release와 같음을 대조했다. 계획 착수 당시 `ai_engine_openai.py`와 trace/auxiliary에 별도 compact 작업의 dirty 변경이 있었고, 문서 검토 중 workspace HEAD가 `0dc9dc893`으로 바뀌었다. 보존한 17개 source 파일 bytes는 동일했으며 이 계획이 수정하지 않았다. 그 commit을 PID 206123의 배포/소비 증거로 취급하지 않는다. 추가 정적 증거와 변경 전 source hash는 [계획 검토 baseline](../../tmp/main-post-warmup-remediation-plan-20261008/baseline.json)에 보존한다.

## 3. 구현 순서와 변경 단위

| 단계 | 선행 | 주된 산출물 | 종료 조건 |
|---|---|---|---|
| B0 기준·계측 고정 | 착수 | actual release/PID/정책·source/부하·dirty 변경 목록, bounded 비교 집계 | warmup/AI 중단/분모/eviction 경계 재현 |
| B1 실제 async 연결 | B0 | Main caller→coordinator→완료 수집→fixed-watch/scanner별 Main 소비 | 두 outer iteration 회귀에서 결과 유실 0·단일 commit·원 quote/deadline 계약 보존 |
| B2 실패 책임 분리 | B0; B1과 최종 통합 | native/source 종료와 provider 실패 처리 | 자연 발생한 2+3 사례 재현, 실제 provider 실패 guard 유지 |
| B3 소유권 조회 비용 | B0 | 검증 generation별 읽기 projection 재사용 | 동일 generation 반복 full copy/reducer 제거, custody 동등성 |
| B4 WS 복사 경계 | B0 | consumer별 immutable snapshot/freeze | lock 비용 감소, raw/history/route·epoch 소비 계약 동등성 |
| B5a 현재 REST 중복 | B0 | exact demand/cache/single-flight 재사용 | 유효한 같은 입력의 중복 전송 감소, stale 재사용 0 |
| B5b 430봉 source 계약 | B5a + 공식/보존 원천 검증 | 명시적 역사 prefix + 현재 완료봉 설계·버전·reader | source 의미가 입증된 범위에서만 WS 대체; 미해결은 REST 유지 |
| B6 전역 cache 격리 | B0 | 시장 국면 전용 HTTP 경계, Telegram 순수 polling | import가 타 소비자 session을 바꾸지 않음; 전달/국면 값 parity |
| B7 통합·인계·자연 수용 | 배포할 단계의 코드 gate | immutable release, 호환 rollback, 실제 PID/성능 증거 | 코드 종료·배포·자연 사용·경제성 각각 보고 |

첫 인계 단위는 **B0+B1+B2**다. B3/B4/B5/B6 전체를 기다리지 않는다. B3/B4/B6는 독립 작은 변경으로 검토하고 최종 합친 경로를 다시 검사한다. B5b의 source 의미가 미해결이어도 다른 수리를 묶어 중단하지 않는다. 이는 다수 동시 운영 canary나 별도 실행 owner를 만드는 계획이 아니다.

## 4. B0 — 기준 고정과 관측 공백 보완

- 착수 시 selector/systemd의 실행 경로, 실제 `/proc/<pid>/cwd`·start ticks·boot identity, immutable commit, 정책/보조 binding, 현재 account/custody data anchor를 읽어 고정한다. PID 교체·정책 세대 변경·clock reset은 별도 window다. 계좌/token 원문을 증거 파일에 남기지 않는다.
- 기존 [runtime performance](../../src/engine/monitoring/runtime_performance.py)와 [HTTP telemetry](../../src/utils/kiwoom_transport_telemetry.py)를 확장한다. 신규 daemon이나 매 tick 파일 쓰기 대신 기존 주기 출력·bounded counter/histogram을 사용한다.
- 첫 루프와 초기 준비를 제외하는 규칙을 전후에 동일하게 고정하고, 준비 완료 marker·선택한 보수적 cutoff와 제외된 수를 기록한다. 나쁜 steady-state 구간을 나중에 warmup으로 편입하지 않는다. AI enabled/disabled 구간도 분리한다.
- coordinator 전달 여부, supported fixed-watch/scanner route, 준비 enqueue/start/finish, Main consume/commit, native 종료·provider 전송/응답·필수 capture/outbox 비용을 기존 attempt/timeline에 연결한다. aggregate snapshot에 circuit 상태와 reset identity를 진단 필드로 남기는 변경을 검토한다. 진단 필드 자체는 신규 매매 gate가 아니다.
- 4,096개 retained sample이나 512개 minute key가 넘으면 누적 histogram/counter와 reset identity로 구간을 계산한다. minute snapshot 병합만으로 완전성을 주장하지 않는다. 현재 HTTP producer는 시작 때 잡은 minute 객체가 eviction된 뒤에도 그 객체에 terminal을 기록하므로, 병합에서 완료가 영구 누락될 수 있다. 기존 coarse 누적 counter의 전후 차이·overflow와 bounded inflight/terminal 연결로 전체 보존식을 검증하고, 수집 사이 key가 넘치거나 완료를 연결할 수 없으면 해당 세부 분모를 lower bound/coverage gap으로 표시한다. eviction된 상세 attempt를 성공/0으로 채우지 않는다.
- 관측 창의 carry-in/out, 시작 cohort와 완료 시각을 구별한다. 새 매 요청 파일을 만들지 않고 기존 bounded 집계에서 물리 작업은 실제 terminal까지 추적하거나 추적 불능을 명시한다. 512 key 초과 뒤 늦은 완료, 한 export 사이 초과, 256 coarse key의 overflow, 128 recent eviction, process reset, 창 종료 때 미완료를 회귀로 고정한다. CPU/I/O bytes의 consumer 귀속은 별도 근거가 있어야 한다.
- `p99<5초`는 `(3,5]` histogram만으로 PASS를 증명할 수 없다. quantile 정의·분모와 정확한 `<5초` 누적 counter 또는 동등한 bounded CDF를 함께 고정한다. 기존 coarse histogram만 있는 창은 percentile 구간만 보고하고 엄격한 목표의 PASS를 보류한다. p95≤2초도 그 경계와 일치하는 bin/계수로 판정한다.
- 분모는 ready membership, 실제 claim, machine capture, ENTER_NOW, provider 예약/physical start/응답, Main commit, submit intent를 구별한다. ready−claimed를 적격 기회 손실로 계산하지 않는다. 미호출·defer·source invalid·late/uncertain은 0초 성공이 아니다.

metric role·authority는 LP7/RW0의 기존 diagnostic 선언을 승계한다. 자연 관측에는 강제 provider/broker 호출이나 중복 shadow source 요청을 넣지 않는다. 배포 전 데이터가 없는 항목의 개선율은 null이다.

## 5. B1 — 상시감시 Main 실제 호출의 async 연결

변경 owner는 [Main caller](../../src/engine/kiwoom_sniper_v2.py), [state handler](../../src/engine/sniper_state_handlers.py), [기존 coordinator](../../src/engine/scalping/scanner_async_eval.py)다. 새 실행 엔진을 만들지 않는다.

1. 일반 WATCHING branch의 `handle_watching_state` 호출에 이미 생성한 coordinator를 전달한다. wrapper 기본값·runtime dict·helper까지 같은 instance가 도달하는지 추적한다. scanner, fixed watch, 허용된 recheck의 실제 진입점을 전수 확인하고 caller에서 누락된 원 claim/deadline도 함께 연결한다.
2. `FixedWatchGeneration.from_claim`의 native registration receipt, 원 signal/token/scope 실행 hash, venue/session/item/transport epoch, 원 epoch·monotonic deadline을 사용한다. fixed watch를 scanner promotion으로 합성하지 않는다. 지원 대상에서의 전달 누락은 진단상 결함으로 표시하고, 다른 비대상 caller에 새 전역 차단을 만들지 않는다.
3. prepare worker에 frozen stock/source 입력을 전달한다. worker 결과·callback은 evidence만 반환하고 현재 stock/계좌/주문 상태 변경은 Main의 기존 commit 경계에서 수행한다. closure가 live stock을 캡처하는 간접 소비자도 조사한다. provider 예약/physical 전송은 기존 outbox/dispatcher owner를 사용한다.
4. 준비 queue의 기존 크기·worker 수·provider 동시성/간격을 유지한다. 원 claim 있는 작업의 우선순위와 bounded aging을 함께 검증한다. 실행 중 blocking I/O는 선점됐다고 처리하지 않으며 holding/SELL/cancel/late-fill 처리 우선권을 보존한다.
5. 완료 통지는 기존 Main 대기를 깨우는 bounded 경로를 사용한다. polling 빈도 무제한 증가나 반복 전체 스냅샷으로 처리 지연을 바꾸지 않는다. queue 대기·capture·key 대기·network·응답 검증까지 원 deadline을 소비한다.
6. Main commit에서 현재 claim·quote·state version·manual veto·source/policy/보조 binding 및 native 허용 branch 부분집합을 확인하고 한 번만 소비한다. timeout/cancel 이후 물리 작업의 슬롯과 uncertain 예약은 완료 증거까지 유지한다. late response는 저장해도 주문 권한을 갖지 않는다.

### 5.1 완료 수집부터 마지막 소비자까지 연결

현재 `run_sniper`의 outer-loop `drain_completed()`는 모든 완료를 꺼낸 뒤 `scanner_generation_id`와 `_is_scanner_watching_target()`으로만 target을 찾는다. fixed-watch 결과는 `fixed-watch:<원 claim token>` identity이므로 해당 scanner 검색으로 연결되지 않아 `target_or_generation_missing`으로 `discard_completed()`될 수 있다. caller 인자 추가만으로 B1을 닫지 않는다.

- 준비 context→결과→Main 수집에 검증된 fixed-watch/scanner 종류와 원 admission/generation·claim·request identity를 유지한다. symbol이나 접두사만으로 권한을 추정하거나 scanner generation을 합성하지 않는다.
- Main 수집부가 fixed-watch 결과를 정확한 현재 admission/원 claim에 연결하고 기존 fixed-watch Main commit 한 곳에서 소비하게 한다. generic drain과 handler의 `take_completed()`가 경쟁하여 결과를 버리거나 두 번 commit하지 않도록 ready/ack 소유권을 명시한다.
- 완료 수집은 새 분석용 cooldown/trigger가 다시 충족될 때까지 미루지 않는다. 현재 target 상태·manual veto·원 policy/source/claim 유효성은 commit 시 그대로 검사한다. 새 tick의 다른 claim을 먼저 획득하여 이전 결과의 권한으로 쓰지 않는다.
- target 제거·state 전환·claim 교체·만료 결과는 한 번 reject/ack하고 해당 request의 pending 필드만 정리한다. `_fixed_watch_async_claim`과 `_scanner_async_*`의 오래된 상태가 다음 요청을 막거나 새 요청 상태를 삭제하지 않아야 한다. reject가 옛 claim의 재예약·새 cache key/provider 재호출을 유발하면 실패다. 실행 중 물리 요청의 슬롯·uncertain 소유권은 terminal까지 유지한다.

필수 회귀는 `run_sniper`의 실제 outer drain과 일반 WATCHING을 **최소 두 outer iteration** 실행하는 bounded harness다. 첫 호출 뒤 worker 완료→다음 outer drain→fixed-watch commit을 연결하며 fixture가 coordinator 인자를 직접 꽂아 누락을 숨기지 않는다. scanner/fixed-watch 혼합, drain 직전/직후 완료, cooldown 중 완료, target 제거·claim 교체·만료, queue-full, freeze 후 원본 변조, manual veto와 late response를 시험한다. 동일 요청의 consume/intent는 최대 한 번이며 유효 ENTER_NOW+PASS+기존 guard 통과 fixture는 정확히 한 번이어야 한다.

### 5.2 기존 quote 검증과 2초 성능 목표의 분리

공통 `_scanner_async_quote_is_fresh()`는 canonical quote 검증 후 `_get_ws_snapshot_age_sec()<=2.0`도 요구한다. 후자는 `last_ws_update_ts` 기준 transport age이며 quote proof가 아니다. fixed-watch를 async에 연결할 때 이 scanner 조건이 새로운 fixed-watch 진입 제한으로 유입되지 않도록 해당 경로의 기존 canonical quote receipt·effective freshness 설정을 재사용한다. scanner의 기존 계약을 전역 완화하지 않는다.

commit의 현재 clock으로 quote 수신 시각·route/epoch·결손·future clock을 재검증한다. 예를 들어 effective quote 한도가 3초인 fixture의 유효 2.5초 quote는 별도 2초 transport 조건만으로 거절하지 않고, 한도 초과 quote는 거절한다. 새 체결/heartbeat만 받은 오래된 호가, 체결이 없어도 신선한 호가, 잘못된 route/epoch를 각각 대조한다. 실제 한도는 실행 설정에서 읽고 숫자 3을 새 계약으로 고정하지 않는다. 원 5초 claim과 TTL 4.999/5.000/5.001초 native 경계는 유지한다.

### 5.3 준비 단계별 잔여 deadline

현재 prepare는 tick REST fallback→430봉→추가 source context를 만들고 coordinator는 주로 prepare 전체 앞뒤에서 만료를 확인한다. 각 물리 조회/admission 직전과 앞 단계 반환 직후에 원 epoch·monotonic deadline의 잔여 시간을 확인하도록 실제 helper까지 연결한다. tick 조회에서 이미 시간을 소진하면 다음 candle/investor/capacity/provider 요청을 새로 시작하지 않는다. 지원 transport에는 기존 잔여 budget을 전달하고 최소 timeout 재확대·자동 재시도·quota 추가는 하지 않는다.

이미 실행 중인 blocking I/O는 취소됐다고 가정하지 않는다. worker/예약은 실제 drain까지 소유하며 대체 작업을 중복 실행하지 않는다. entry 만료를 holding/SELL/cancel 보호에 전파하지 않는다. 첫 source를 지연시킨 fake transport에서 후속 물리 호출 0과 late drain 보존을 검사한다. Kiwoom 요청/recovery flow 수정이 수반되면 §10의 공식 gate를 먼저 수행한다. 자연 준비 계수 >0은 실제 claim이 발생한 창에서만 요구한다.

## 6. B2 — 원천 종료와 provider 실패 책임 분리

변경 owner는 [AI engine](../../src/engine/ai_engine_openai.py)의 `analyze_target`, 성공/실패 집계, caller에 반환되는 기존 결과·trace다. 현재 5회 제한이나 성공 reset 규칙을 임의 조정하지 않는다.

| 사건 | 실패 계수 처리 | 반환·원장 처리 |
|---|---|---|
| 전송 전 원 claim 만료·검증된 native path 변경 | 증가도 성공 reset도 하지 않음 | 기존 WAIT/DROP·원천 이유·provider 미호출·원 attempt 보존 |
| 실제 timeout/전송 오류 | 기존 실패 의미·횟수 유지 | physical attempt, 예약·uncertain, 원 deadline 보존 |
| 응답 후 native claim 소멸 | provider 결과와 claim 종료를 별도로 판정 | 원 응답 보존, 유효하지 않은 claim으로 commit 금지 |
| 기존 의미로 유효한 provider 응답 | 기존 성공 집계를 정확히 한 번 | PASS/CAUTION/VETO와 이후 Main guard 결과를 별도로 유지 |
| 알 수 없는 예외·검증되지 않은 parser/schema 문제 | 이번 수정으로 일괄 면제하지 않음 | 기존 보수적 처리와 원인 evidence 유지 |

`provider_called=false` 하나로 모든 예외를 면제하거나 문자열 `reversal_*` 전체를 무시하지 않는다. 정확히 확인한 entry/native 종료를 기존 typed exception/result 경계 또는 제한된 분류 helper로 연결한다. 다른 holding/exit/macro AI의 실패 의미를 함께 바꾸지 않는다. async와 sync의 동시 완료에서 실패/성공 집계가 중복되거나 순서 없이 lost update되지 않도록 기존 AI owner 경계의 직렬화/lock을 점검한다. 하나의 logical 호출과 그 physical attempt/terminal ID를 기존 outbox·trace에 결속하고, 이미 timeout으로 종료한 요청의 late drain을 두 번째 성공 reset이나 추가 실패로 세지 않는다. 새 별도 실패 원장을 만들지 않는다.

`provider_attempted=True`도 물리 전송 영수증이 아니다. 현재 flag 설정 이후 budget 산출·key/queue 대기에서 끝날 수 있고, [live outbox](../../src/engine/scalping/reversal_operating_outbox.py)의 `reserve()`는 실제 전송 전부터 `transmission_uncertain`으로 진행한다. 예약·adapter 진입·물리 전송 시작·응답을 기존 timeline에서 구별하고, 확인하지 못한 전송 여부는 unknown으로 둔다. 실패 분류에는 정확한 종료 stage/typed 사유와 존재하는 physical receipt를 사용한다. 검증된 native 종료의 실패 면제와 uncertain 예약/예산의 해제는 별개이며, 이번 수리로 outbox를 되감거나 새 재호출 권한을 만들지 않는다.

재현 fixture는 자연 순서 `timeout → path change → path change → timeout → path change`다. 전송 실패는 2회로 남고 native 종료는 3건 그대로 기록돼야 한다. 추가로 **실제 provider 실패 5회는 여전히 disable**, source 종료만 반복해도 기존 실패 수가 성공처럼 0으로 reset되지 않음, invalid 응답·late 성공·중복 callback을 시험한다. 예약 전 만료, 예약 후 전송 전 만료, key/queue 만료, 실제 전송 뒤 timeout, 유효 응답 뒤 native path 소멸을 분리하여 판정·counter·outbox terminal을 대조한다. 단지 물리 미전송이라는 이유로 알려지지 않은 parser/설정 오류를 native 종료로 면제하지 않는다.

이미 disable된 PID를 계획 작업 중 직접 reset하지 않는다. 후속 인계에서는 기존 승인된 정상 기동 절차로 새 코드와 정책을 소비하게 하고, 이전 pending/uncertain outbox·quota를 보존한다. 자동 재활성화 timer, API키 전환 또는 임의 probe 호출을 수리의 일부로 추가하지 않는다. 첫 자연 ENTER_NOW가 없으면 정상 provider 소비는 미관측으로 남긴다.

## 7. B3 — 소유권 journal 조회의 generation별 재사용

변경 owner는 [owner custody registry](../../src/trading/order/owner_custody_registry.py)와 이를 호출하는 Main/manual control 경계다. `native_owner_contract → _read_locked → _state`의 읽기 경로를 대상으로 한다.

1. journal hash chain과 파일 generation을 검증한 내부 상태에서 account/symbol별 registered 상태와 최신 manual disposition을 계산한다. 작은 불변 projection을 같은 generation에서 재사용한다. key에는 canonical journal path·검증된 generation/tail·현재 account identity·해석 버전을 포함한다.
2. 현재 `_read_locked`는 mutation caller에도 쓰이므로 모든 반환을 공유 mutable 객체로 바꾸지 않는다. writer가 소유하는 private copy/lock과 읽기 전용 projection을 구분하고, 외부 반환도 작은 독립값으로 제한한다.
3. append·replace·truncate·경로/계좌 교체·manual disposition 변경·동시 append를 정확히 무효화한다. stale stat/time TTL만으로 custody 권한을 유지하지 않는다. generation 읽기 전후가 바뀌면 기존 검증된 bounded retry 또는 fail closed 계약을 따른다.
4. 성능 최적화가 주문 reservation의 기존 flock·최종 재검증을 제거하지 않게 한다. manual veto는 현재 평가/submit 시점에 반영한다. 과거 retired owner의 attribution과 manual management disposition을 보존하며, 옛 잔량을 Main 자동 소유로 해석하지 않는다.
5. 동일 검증 generation에 대해서만 full reducer를 한 번 수행하는 단계부터 적용한다. append-only incremental reducer는 별도 동등성 증거가 있을 때 같은 owner 안에서 확장하고, 불확실한 변조/회전에는 full 검증으로 복귀한다.

검증: 1,489개 보존 event 규모 및 더 큰 fixture에서 반복 조회, account 교체, 동일 크기 rewrite·inode 교체, append 중 읽기, 잘린 마지막 행, hash 오류, concurrent reservation, caller의 반환값 변조, 수동 매도 뒤 역사적 잔량을 대조한다. 결과 hash/판정 parity와 full-copy/reducer invocation 감소를 함께 기록한다. offline deepcopy 18.456ms p50를 실제 루프 전체 절감량으로 사용하지 않는다.

## 8. B4 — WS freeze·복사·소비 경계 축소

변경 owner는 [WS manager](../../src/engine/kiwoom_websocket.py) 및 기존 snapshot/tick consumer다. raw journal, tick event, Main 평가 view, dashboard 파일 각각의 필수 필드·이력 길이·clock·동시성 계약을 먼저 표로 고정한다.

- ingress가 소유한 원천 state에서 필요한 immutable generation을 짧게 freeze하고, 후속 materialize/serialization은 해당 불변값으로 수행한다. shallow copy 뒤 lock을 풀고 mutable deque/dict를 읽는 구현은 제외한다. 기존 history를 bounded immutable chunk/버전별 view로 공유할 수 있는지 검토한다.
- 느린 consumer가 이전 generation을 붙잡을 때의 retained bytes·refcount·해제 시점을 제한한다. lock 시간을 줄인 대신 메모리나 queue가 무제한 늘면 실패다. 소비자 계약의 기존 backlog/실패 처리를 보존하고 raw evidence를 조용히 버려 한도를 맞추지 않는다.
- `market data lock → pending tick lock` 순서와 consume/publish 순서를 유지한다. freeze 중 새 tick이 들어오면 그 tick은 새 pending generation으로 남아야 한다. 오래된 pending batch의 완료가 새 quote/epoch를 덮거나 같은 event를 다시 publish하면 실패다.
- tick consumer가 full history를 요구하면 계약상 필요한 동일 이력을 제공한다. dashboard의 가벼운 projection을 raw/기계 source로 대신 공급하지 않는다. 소비자별 원본 시각·item/suffix·route·transport epoch와 history source 의미를 보존한다.
- 파일 writer는 기존 cadence와 atomic replace를 유지한다. 느린 파일 저장과 완성봉 writer backlog를 lock 밖에서 처리해도 required evidence/drop·queue overflow·writer loss는 숨기지 않는다. lossy 진단 화면과 lossless 원천이 같은 큐를 공유한다면 기존 owner 안에서 경계를 명시한다.
- reconnect, callback 예외, consumer mutation, 일부 FID 누락·잘못된 route, 대용량 history/복수 pending, 느린 writer, concurrent getter로 parity와 lock 경계를 재현한다. 추가 WS 연결·REG 확대·cap 변경을 성능 검증에 사용하지 않는다.

현재 lock p99 목표 10ms는 LP 계획의 성능 목표로 유지한다. 목표 미달만으로 runtime 차단기를 추가하지 않는다. byte/content·source freshness·consumer lag가 동등하면서 wait/hold/snapshot 시간이 감소했는지 검증한다. 프로토콜/FID/REG·recovery flow 변경이 필요하면 구현 전에 §10의 공식 gate를 적용한다.

## 9. B5 — 분봉 REST 절감의 두 단계

### B5a. 현행 homogeneous source의 중복 제거

owner는 [entry candle context](../../src/engine/scalping/entry_candle_context.py), [공통 분봉 source](../../src/trading/market/shared_ws_snapshot.py), 기존 `kiwoom_utils` cache/transport, [zero-base probe](../../src/engine/scalping/zero_base_probe.py)다.

logical demand가 생긴 시점의 목적, item/route/session, adjustment, candle interval, required history, completed cutoff, consumer schema/feature version을 고정한다. 같은 유효 cutoff와 source 계약의 요청만 cache/single-flight를 공유한다. key 대기 중 원 claim이 만료된 follower는 결과를 받더라도 사용하지 않는다. page/retry는 physical attempts로 유지하며 error·partial result를 완성 cache로 저장하지 않는다.

430봉 전체는 그대로 제공하고 기존 완료봉 선택·TTL/freshness를 유지한다. seed를 하루 종일 최신 평가 입력처럼 재사용하거나 오래된 seed의 수신시각을 now로 갱신하지 않는다. 현재 `shared_completed_bar_seed`의 session 단위 key를 그대로 최신 430봉 rolling cache로 전용하지 않는다. 새 완료 minute, corporate action/adjustment, reconnect gap, 원천 변경에 필요한 refresh/invalidation을 각각 검증한다. 사전 조회·복구 quota를 늘리지 않는다.

5개 fixed-watch `_AL`이 현행 WS selector 대상이다. probe의 400 physical attempts는 다른 종목·`mode=rest` 경로를 포함할 수 있으므로 exact request code/consumer별 전환 가능량을 먼저 산출한다. probe 관측 삭제·종목 축소·Main 외 종목의 자동 WS 등록 확대를 호출 절감으로 계산하지 않는다. 516회를 전부 없애는 목표를 선언하지 않는다.

### B5b. 430봉 역사 prefix와 WS continuation의 명시적 계약

현행 selector는 단일 session source이고 REST seed/WS 혼합을 금지한다. 따라서 단순히 `minimum_bars=390`, `history_scope='rolling'`, `ws` 강제 모드로 바꾸는 수정은 하지 않는다. 이 단계는 **새로운 source composition의 명세·동등성 검증**을 먼저 만든다.

1. MTF 430봉의 실제 용도를 추적해 이전 session/day prefix, 현재 session anchor/VWAP/OR, 모델별 마지막 완료봉을 구분한다. 각 파생값이 요구하는 이력을 임의 축소하지 않는다.
2. 허용 source 설계는 검증된 homogeneous REST 역사 prefix와 exact route의 현재 WS 완료봉을 별도 영역으로 보존하는 불변 view다. 기존 raw REST/WS를 수정하지 않고 각 segment의 source hash·시간·수정주가/거래량·날짜/session·transport epoch를 명시한다. 새 schema/version과 reader 지원을 함께 검토한다.
3. overlap에 대해 OHLC·volume·adjustment·종료시각·정렬·중복/늦은 수정의 동등성을 보존 원천과 공식 문서로 검증한다. 증명되지 않은 `_AL` 통합봉과 개별 venue tick을 합치지 않는다. REST row를 WS epoch에서 실제 관측한 것처럼 재태깅하지 않는다.
4. seed cutoff와 WS 첫 유효 구간 사이에 gap이 없고 요구된 prefix/430봉이 충족될 때만 새 reader가 선택한다. 미완성 최신 봉 제외, session/date 전환, 중간 시작, reconnect, 무체결 구간, 수정주가 발생을 시험한다. 관측하지 못한 분을 OHLC/volume=0으로 채우지 않는다.
5. 원천 의미가 충돌하면 해당 composition만 `unsupported/source_gap`으로 남기고 기존 bounded REST를 유지한다. 다른 B 단계는 계속할 수 있다. source contract에 맞는 적용 범위가 확인된 뒤 기존 source 선택 owner로 인계하며 새 전략/가격/수량 판단 권한을 만들지 않는다.

현행 WS의 `raw_same_day`와 REST seed의 `adjusted_1`은 동일 의미라는 증거 없이 합치지 않는다. 역사 prefix의 원 수신 시각/epoch와 현재 tail의 live producer/transport identity를 segment별로 검증한다. 오래된 REST 수신 시각을 현재 WS epoch로 덮거나 cache hit를 freshness 승인으로 취급하지 않는다. 최종 reader의 coverage·수정주가·완료시각 검증까지 닫혀야 composition 선택을 허용한다.

종료 증거는 430봉·파생값 parity, 원 provenance 보존, `ws_selected_http0` 또는 새 버전 composition 선택의 실제 consumer receipt와 수요당 physical attempts 감소다. 분봉 절감에는 경제적 입증을 추가하지 않는다. 자연 source 표본이 없으면 코드 검증과 자연 대체 확인을 별도로 보고한다.

## 10. B6 — 시장 국면 HTTP cache를 해당 소비자로 격리

owner는 [market regime service](../../src/market_regime/service.py)와 [Telegram manager](../../src/notify/telegram_manager.py)의 session 생성 경계다. 설치 패키지 파일을 직접 수정하거나 업그레이드/제거하는 계획이 아니다.

1. Main import graph에서 `fear_and_greed → cnn.py → install_cache`의 전역 patch를 제거하는 경로를 설계한다. 같은 package를 lazy import하는 것만으로는 부작용을 제거하지 못한다. 기존 market regime package 안에서 전용 HTTP session/cache와 동등한 response adapter를 소유하도록 한다.
2. 현재 CNN 요청의 결과 필드 `score/rating/timestamp`, source/previous-value/fallback 의미, 기존 갱신 주기·시장 국면 계산을 보존한다. package API를 계속 쓸 경우에도 global import 부작용이 Main에 전파되지 않는 구조가 실제로 입증돼야 한다. 새로운 별도 daemon은 만들지 않는다.
3. Telegram `getUpdates`는 명시된 순수 polling session, 기존 timeout/long-poll 및 offset/명령 처리 계약을 따른다. 계좌/주문·Kiwoom·provider session도 해당 cache의 영향을 받지 않는지 검사한다. 전체 프로세스에서 `uninstall_cache()`를 호출하는 다른 전역 mutation으로 교체하지 않는다.
4. 임의 순서 import, 반복 import, 이미 다른 cache가 존재하는 환경, fake Telegram offset 변화·같은 응답·network retry·중복 command 방지, CNN 성공/실패·stale 데이터 fallback을 네트워크 없는 테스트로 재현한다. session class/adapter와 cache 파일 접근을 검증하고 token/Telegram URL 원문은 로그에 남기지 않는다.
5. 배포 후 같은 polling 입력량의 CPU/SQLite 조회를 비교한다. 실제 command 누락/중복 증거가 없으면 기존 사고로 단정하지 않고 회귀 위험으로만 기록한다. 원래 조사에서의 22.09% 전부를 예상 절감치로 약속하지 않는다.

설치된 `pyTelegramBotAPI 4.32.0`의 마지막 소비자는 `_make_request → _get_req_session → per-thread req_session`이다. 로컬 `_configure_telebot_http()`는 대문자 `apihelper.SESSION`을 설정하지만 설치본 factory는 소문자 `session` 또는 `requests.sessions.Session()`을 읽는다. `requests-cache 1.3.1`은 `requests.Session`과 `requests.sessions.Session` 모두를 patch한다. 따라서 새 Session 생성/대문자 대입만 검사하지 말고 실제 polling·send worker와 TTL 만료/reset 이후의 factory까지 격리해야 한다. 지원 주입 경계를 사용하며 전역 공유 session으로 thread 안전을 악화시키지 않는다.

이 수정은 현재 실제 소비되는 timeout·retry·adapter 동작을 기준으로 한다. 사용되지 않던 로컬 adapter의 GET/POST 재시도 설정을 새로 활성화하여 라이브러리 retry와 중첩시키지 않는다. fake `getUpdates`/`sendMessage`의 다중 thread·TTL 재생성·실패 재시도에서 물리 횟수, offset, 중복 부작용, SQLite 접근 0을 검증한다. 실제 Telegram 메시지 전송이나 패키지 변경은 이 문서 검증에 포함하지 않는다.

**공식 Kiwoom gate:** B4/B5/B6에서 Kiwoom REST/WS 요청·parser/FID/REG·REMOVE·recovery·인증·계좌/주문·continuation을 수정하기 전 [공식 참조 gate](../kiwoom-api-data-contract.md#official-kiwoom-reference-gate)를 실행한다. 그 시점의 upstream SHA, 검사 파일, retrieval time과 protocol 차이를 기록한다. 기존 RW 계획의 10:34 확인 SHA는 역사적 증거다. protocol 의미 미확정은 raw provenance를 보존하고 해당 semantic 승격을 닫지 않으며, 이번 계획 작성은 이 API들을 호출하지 않는다.

## 11. B7 — compact 통합·검증·배포 인계

### 11.1 공통 파일과 정책 적용 순서

B1/B2와 AC2/AC5는 `ai_engine_openai.py`, source capture/trace, 원 deadline·registry binding·provider outbox를 공유한다. 변경 전 dirty diff를 보존하고 최소 변경 단위로 통합한다. 실제 요청은 `Main caller → async context → 원 policy/보조 binding → provider envelope → raw response → decode/validator → Main commit` 전체를 검사한다. helper만 통과하거나 compact 연구 157쌍의 성공을 이 통합 경로의 성공으로 전용하지 않는다.

B1/B2 수리의 단독 release는 현재 native 보조 계약과 호환되는 코드로 먼저 인계할 수 있다. compact의 구현/회귀·승인된 실행 상태는 [별도 실행 리뷰](../audits/main-auxiliary-compact-intraday-adoption-review-2026-10-08.md)를 따른다. 이미 끝난 연구 157쌍/AC5 검증을 다시 미완료로 바꾸지 않고, 새로 확인한 공통 경로 결함만 최종 통합 코드의 v1/v2 fake transport 회귀로 닫는다. 실제 compact overlay 발행 전에는 해당 경로의 B1/B2 결함이 닫혀야 한다. B3/B4/B5/B6의 자연 성능 목표나 전체 완료를 compact 정책 채택의 새 경제/표본 gate로 만들지 않는다. codec 추가 비용은 기존 loop/provider timing에 분리 기록한다.

보조 binding의 기준 시점은 enqueue/worker 시작/전송 시각이 아닌 **원 확인점의 `assessment.event.epoch`**다. 현행 `at_confirmation()`이 선택한 registry/binding/overlay를 원 claim과 함께 전달하고 `validate_decision()`의 현재 철회·부모·생존 검증을 유지한다. v1 확인 뒤 v2 발행→늦은 enqueue는 v1, 발행 뒤 새 확인점은 v2, 무관 scope 변경은 원 유효 claim 보존, 해당 scope 철회는 미제출 claim 거절로 회귀를 고정한다.

발행 자료 재생성 여부는 실제 source 의존성으로 정한다. B1/B2의 caller/AI 수정만으로 모든 registry/evaluation/report를 다시 발행하지 않는다. `reversal_auxiliary_intraday.code_hashes()`가 선언한 reader 파일 및 호환 계약이 바뀌었는지 확인하고, 불변 source가 같은 자료는 byte 그대로 재사용하되 새 release의 소비 호환성을 검증한다. reader 변경 시에만 영향받은 원 보고서 hash·이전/신규 reader·frozen reader의 호환 증거를 갱신한다. checklist 최종 바이트와 장중/다음 기동 준비의 영향 검증은 별도로 유지한다.

### 11.2 변경별 필수 회귀와 실행 명령

| 범위 | 기존 테스트 소유 위치 | 추가로 입증할 반례 |
|---|---|---|
| B0/B1 | `src/tests/test_main_rest_ws_latency.py`, `test_scanner_async_eval.py`, `test_scanner_async_entry_bridge.py`, `test_fixed_watch_submit_source_repair.py` | 두 outer iteration의 drain→fixed commit, cooldown/claim 교체·만료, canonical quote/transport age 구별, source별 잔여 budget, 늦은 terminal eviction·정확 CDF |
| B2/compact 접점 | `test_ai_engine_openai_transport.py`, `test_ai_engine_openai_v2_audit_fields.py`, AC5의 codec/transition 회귀 | 2+3 실패 분류·실제 5실패 차단, 예약/physical 분리, v1/v2 원 확인점 binding·철회·outbox 보존 |
| B3 | `test_main_only_retirement.py`, `test_symbol_owner_coexistence.py`, `test_strategy_owner_components.py` | generation/account/manual 전환·concurrent append·변조·retired 수량 비인수 |
| B4 | `test_kiwoom_websocket.py`, `test_micro_reversion_completed_bars.py`, `test_entry_snapshot_revalidation.py` | pending batch race, mutable alias, full history/route/epoch·slow writer |
| B5 | `test_entry_candle_context.py`, `test_main_rest_ws_latency.py`, `test_micro_reversion_completed_bars.py` 및 해당 MTF 소비자 | 430봉/390 capacity 거절, 같은 cutoff 재사용, gap/overlap/adjustment·새 완료봉·stale seed |
| B6 | `test_market_regime_local_context.py`, `test_kiwoom_sniper_market_regime_runtime.py`, Telegram 관련 기존 회귀 | import 순서·poll/send thread·TTL reset 뒤 실제 session/adapter, 물리 retry/offset/중복 parity, SQLite 0, 국면 fallback |

기존 `test_market_regime_data.py`에는 실제 `fear_and_greed.get()` 호출 검사가 있으므로 이 작업의 일반 offline 회귀에 묵시적으로 포함하지 않는다. 테스트 위치는 기존 `src/tests`에서 해당 계약 파일을 확장한다. 실제 Main caller 검증에 새 fixture 파일이 필요할 때만 먼저 location gate를 통과한다. 신규 runtime 구현도 `scalping`, `trading/market`, `trading/order`, `market_regime`, `notify`의 기존 owner를 우선하며 engine root에 새 모듈을 두지 않는다.

초기 B1/B2의 예시 검증 명령은 다음과 같다. 구현 diff에 맞춰 test selection을 확정하고 외부 I/O는 fake로 고정한다.

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_main_rest_ws_latency.py src/tests/test_scanner_async_eval.py src/tests/test_scanner_async_entry_bridge.py src/tests/test_ai_engine_openai_transport.py src/tests/test_fixed_watch_submit_source_repair.py
```

변경 Python은 관련 import/compile 검사를 수행하고 `git diff --check`를 통과시킨다. wrapper 변경 때만 `bash -n`과 해당 계약 테스트를 추가한다. 리뷰→결함 수정→반례 회귀→재리뷰의 미해결 in-scope 결함이 0이어야 코드 종료다. 운영 배포 전 실제 자연 주문/수익을 요구하지 않는다.

### 11.3 배포·인계와 복구

1. 선택한 단계와 최종 공통 diff만 검토된 immutable release로 만든다. 현재 유효 정책·보조 v1/v2 reader, data anchor, original outbox·pending intent/callback을 읽을 수 있는지 cold-start 검증한다. 미검토 dirty 전체를 함께 넣지 않는다.
2. 기존 승인 범위와 native `intraday_release_handoff`/기동 조건을 확인해 인계한다. PID 206123을 다시 시작해야 한다는 고정 지시로 사용하지 않는다. 실행 당시 PID·진행 요청·release와 그 변화를 기록하고 중복 Main PID를 방지한다.
3. checklist/코드/정책 또는 controller source가 달라지면 최종 byte hash와 원 strict snapshot을 비교한다. 기존 장중 인계·필요한 다음 PREOPEN 준비만 갱신하며 과거 PASS 수기 변경·EOD/연구/장후 전수 재실행으로 대응하지 않는다. 이번 문서 작성에서는 준비를 재생성하지 않는다.
4. 새 PID에서 현재 정책/보조 소비, async 실제 경로, circuit 상태, provider/outbox/commit을 각각 확인한다. 첫 자연 신호가 없으면 route wiring의 코드 검증만 닫고 자연 request는 `not_observed`다.
5. rollback 대상은 **현재 정책·보조 reader와 영구 퇴역 경계를 지원하는 검증된 이전 코드/source 경로**다. 기존 B1/B2 결함이 있는 v3는 무조건 정상 rollback 목표가 아니다. code와 binding 호환성·알려진 결함/제한을 사전에 기록한다. compact v2가 적용됐다면 AC6의 scope별 정책 복원/reader 지원 순서를 따른다.
6. receipt 유실, 잘못된 source/quote/custody, 중복 physical 요청/주문, hard exit 지연, manual veto 위반은 기존 안전 절차와 승인된 복구 경계로 처리한다. latency 목표만 미달이면 미달로 기록하고 다음 비용을 점검한다. TTL 확대·provider guard 해제·retired 서비스 재기동·outbox rewind를 복구로 사용하지 않는다.

## 12. 자연 수용·보고 계약

| 판정 대상 | 목표·검증 | 미관측/실패 표시 |
|---|---|---|
| 실제 async 연결 | supported native claim에서 준비 queue/service→Main consume/commit의 정확한 연결 | enqueue만 존재하면 commit 완료가 아님; no signal은 미관측 |
| 실패 분류 | native/source 종료가 provider 실패 수를 소모하지 않음; 실제 실패 차단 유지 | 엔진 disabled 상태의 짧은 루프를 성능 PASS로 계산하지 않음 |
| warm loop | 기존 LP 목표 p95≤2초, p99<5초; >5초 수와 max 별도 | 엄격한 5초 경계를 입증하지 못한 histogram은 구간만 보고; 개선율 미확정 null, 목표는 매매 cutoff가 아님 |
| signal→machine/dispatch | 기존 p95≤1.5초, p99≤2초 제안 및 dispatch age≤2초 목표 | 2초보다 늦었다는 새 호출 금지 조건을 추가하지 않음 |
| owner registry/WS | 같은 source·custody 결과에서 full-copy/reducer·lock 비용 감소, WS p99 wait/hold≤10ms 목표 | microbenchmark와 실제 wall-time 기여율 구분 |
| REST | exact demand당 physical attempts/페이지, 유효 source 비율, fallback 이유 | unavailable/defer 수요 포함; 분모 0/불완전이면 절감률 null |
| notifier cache | import 부작용 제거·polling 전달 동등성·CPU/SQLite 비용 관측 | 명령 사고를 추정으로 확정하지 않음 |
| 정상 제출 경로 | fake transport에서 유효 ENTER_NOW+PASS+기존 guard 통과 시 정확히 1 intent | 실제 submit/broker 접수/fill/손익은 독립 receipt |

비교 창은 release/정책/보조·종목/session·입력률·source 품질·AI enabled 상태를 함께 보존한다. 기존 RW의 15분 창/peak 관측 제안은 자연 수집 단위이지 새 최소 경제성 표본 gate가 아니다. 다음 승인된 가동에서 정상 부하와 peak를 기록하되 거래일·해당 PRE/REGULAR/AFTER 세션은 저장소 달력으로 확인한다. 지나간 세션의 신호를 재발행하지 않는다.

전후 다른 장세·정책 또는 관측 중단으로 HTTP가 줄면 총량 변화만 보고한다. 모든 claim을 defer해 provider 호출이 0이 되거나 source coverage가 줄어든 결과는 성능 성공이 아니다. 준비 완료·실행 적격 호출·source invalid·expired·uncertain의 같은 분모를 함께 공개한다. 코드, release selection, PID 소비, 자연 경로, 성능, 체결·비용조정 수익을 개별 상태로 남긴다.

## 13. 계획 리뷰·검증 기록

검토에서 단순 coordinator 인자 추가 외에도 실제 caller harness 누락, source 종료의 실패 reset 가능성, mutable registry cache 유출, WS pending/lock race, 430봉과 session capacity의 구조적 불일치, stale homogeneous seed 전용, probe WS 대상 확대 오인, 전역 cache의 생성 주체, compact와 rollback reader 충돌을 반영했다. 비용별 정확한 wall-time 기여율과 B5b의 REST/WS 의미 동등성은 구현 단계의 명시적 증거 항목으로 남긴다.

문서 검증은 링크·소유 위치·단일 현재 owner·권한/의존성·숫자 대조·AUTO 봉인 블록 보존·공백 검사와 print-only backlog parser로 수행한다. 코드/패키지·runtime 파일을 수정하지 않고 provider/broker·운영 테스트·보고서 재생성·외부 sync는 실행하지 않는다. 문서 검증 통과를 B1~B7 구현 또는 자연 수용 완료로 표시하지 않는다.

최초 계획 검증 결과: 변경 문서 5개의 로컬 링크/anchor 117개, 참조 테스트 파일 16개가 유효했다. print-only parser는 21개 작업·현재 실행 owner 1개·경고 0건이었다. 당시 checklist 원 AUTO 블록과 별도 작업 source 파일 17개의 hash를 보존했다. 이는 최초 계획의 문서 검증 기록이며 후속 코드 상태를 증명하지 않는다.

### 13.1 후속 리뷰에서 보완한 결손

| 우선순위·결손 | 확인한 소비 경로 | 계획 보완·구현 종료 검사 |
|---|---|---|
| P0 fixed-watch 완료 유실 | Main outer drain의 scanner-only target 조회→discard | B1 §5.1: 원 identity별 단일 수집/commit, 두 outer iteration·cooldown/만료/교체 회귀 |
| P0 비동기 연결 시 새 2초 차단 유입 | canonical quote 검증 뒤 transport-age helper 추가 적용 | B1 §5.2: 현재 fixed-watch freshness 계약·현재 clock 재검증, scanner 계약 분리 |
| P1 만료 뒤 source 연쇄 요청 | prepare 전체 앞뒤 budget 확인, 내부 tick/candle/context 호출 | B1 §5.3: 물리 요청별 원 잔여 budget, 늦은 작업 drain·중복 방지 |
| P1 미전송/예약/실패 혼동 | flag 이후 transport 준비, reserve에서 transmission_uncertain | B2: stage/physical receipt별 분류, 실패 counter와 uncertain 해제 권한 분리 |
| P1 cache 격리 후 실제 session 누락·retry 증가 | 대문자 SESSION 설정과 설치본 소문자/per-thread factory 불일치 | B6: 실제 poll/send·TTL/reset 경계 및 기존 소비 retry parity |
| P1 계측 소실·목표 과대 판정 | minute eviction 뒤 terminal·coarse histogram | B0: 누적 보존식/coverage gap, strict 5초 CDF 경계 |
| P1 장중 교체 시 원 binding 재선택 | at_confirmation(event.epoch)→validate_decision | B7/AC6: 원 확인점 v1/v2·scope 철회, 영향 reader만 호환 갱신 |

후속 리뷰 기준은 workspace `0dc9dc893` 및 [12개 source/의존 파일 기준 hash](../../tmp/main-post-warmup-remediation-plan-review-20261008/baseline.json)다. 검토 도중 별도 작업이 Main caller 인자 전달과 AI native 종료 분류 등을 수정했다. 해당 diff는 보존하며 인자 추가/분류 분기 존재만으로 위 종료 검사가 통과했다고 표시하지 않는다. PID 206123 관측과 별도 compact 구현 기록, 이번 문서 수정을 구별한다. 남은 항목은 계획 결손을 보완한 **구현·회귀 요구사항**이며 이미 수리됐다는 결과가 아니다.

후속 문서 검증: 관련 문서 5개의 로컬 링크/anchor 122개와 참조 테스트 경로 25개가 유효하다. print-only parser는 작업 21개·현재 실행 owner 1개이며 경고 출력이 없었다. 원 AUTO 블록 hash는 동일하다. 기준 파일 12개 중 10개는 동일하고 위 Main/AI 2개의 동시 변경은 별도 기록했다. 문서 공백 검사와 `git diff --check`를 통과했다. 결과는 [검증 기록](../../tmp/main-post-warmup-remediation-plan-review-20261008/validation.json)에 남겼다. 이번 수정은 문서에 한정하여 코드/거래 테스트·provider/broker 호출·배포·재기동·외부 sync는 실행하지 않았다. 실제 B1~B7 구현과 자연 성능 개선은 후속 검증 대상으로 남는다.

## 14. 승인된 구현 인계

2026-10-08 통합 작업에서 B0/B1/B2/B3/B4/B5a/B6를 구현했다. B7은 동일 정책·보조 overlay를 유지하는 native release handoff로 배포한다. 기존 compact reader 다섯 파일과 128경로의 binding을 대조하여 네 scope v2·124경로 v1을 그대로 승계하며, 새 연구 호출이나 비교 원장 복제를 하지 않는다.

B5b는 `adjusted_1` REST 역사와 `raw_same_day` WS tail의 동등성 미입증으로 composition 선택을 열지 않았다. 430봉 하한과 기존 bounded REST 경로를 보존한다. 이는 다른 단계의 배포를 막는 조건이 아니며, 완료된 코드 수리와 구분해 source contract 미지원으로 기록한다.

추가 운영 검증에서 native 신호가 없는 활성 fixed-watch가 `not_enabled`로 기존 Main inline REST 준비에 들어가는 결함을 발견해 B1에 포함했다. 검증된 당일 exact scope/route의 native 정책은 신호가 생길 때까지 `waiting_native_signal`을 반환하며, 실제 유효 claim의 비동기 dispatch/commit과 비지원 backend의 기존 동작은 유지한다. 원 5초 claim이나 quote/주문 guard는 늘리지 않는다. 중간 배포의 72.847초 warm loop를 실패 관측으로 보존하고 보완 배포의 별도 자연 창을 수집한다.

사용자 확인대로 통합 애프터장은 `_AL`·SOR다. 세 Main 이관 종목에만 남아 있던 NXT listing 추가 관찰 승격 조건은 NXT 전용 PRE에 한정하고, 통합 REGULAR/AFTER에서는 다섯 fixed-watch가 같은 기존 Main SOR 관찰 계약을 따른다. 감시 개수와 현재 session admission·유효 quote·실제 주문 가능성을 분리한다. 실제 주문 preflight와 소유권/계좌/수량 보호는 그대로 유지한다.

최종 회귀·수리 내용, 통제된 microbenchmark, 실제 새 PID의 소비 및 자연 성능/원천/호출 관측은 위 통합 리뷰와 [실행 증거 디렉터리](../../data/report/main_bottleneck_compact/2026-10-08/)가 소유한다. 단일 현재 checklist owner와 원 strict checklist 바이트는 유지한다. 배포 완료나 실제 주문·비용후 승률은 코드 검증으로 대신하지 않는다.


SOR 보완 후 관측한 59.550초 warm loop는 추가 실패 증거로 보존한다. 재현된 당일 3.1GB pipeline cold 조회를 byte block 검색으로 수리하고, 원 쿨다운 history의 cold 준비는 fast exit owner 시작 이후·Main entry evaluation 이전에 완료한다. 준비시간 자체는 별도 계측하며 행/순서/offset/gzip/partial-tail 및 기존 보호조건을 유지한다. 이후 tail은 원 incremental 경로를 사용한다. 이 변경으로 새 비교 원장이나 연구 호출을 생성하지 않는다.
