# Main 워밍업 이후 평가 지연·REST/WS 병목 개선 상세 구현계획 — 2026-10-08

**2026-10-08 후속 구현 상태:** PASS 소비·잔여 병목·430봉·비상시감시를 통합 구현하고 반복 리뷰·회귀를 수행했다. 10/8 구현 완료 때는 배포를 보류했으며, **10/9 후속 사용자 지시로 전체 미커밋 통합 배포가 승인됐다**. 현재 배포·준비 검증 상태는 [통합 배포 리뷰](../audits/main-integrated-uncommitted-deployment-review-2026-10-09.md)에서 확인한다. H4의 수정주가/WS 동등성 미입증 범위는 REST를 유지한다. [구현·검증·한계 기록](../audits/main-pass-residual-history-nonfixed-implementation-review-2026-10-08.md)을 현재 실행 결과로 사용하며 아래의 계획 작성 당시 승인·미실행 문구는 그 시점의 이력이다.

## 1. 결정·범위·실행 owner

실제 상시감시 caller의 비동기 연결과 AI 실패 집계를 먼저 수정한다. 이어 소유권 저널의 반복 계산, WS 공유 lock의 복사, 분봉 REST 반복 조회, Telegram에 유입된 전역 HTTP 캐시를 개선한다. 각 변경은 같은 원천·정책·안전 계약에서 처리 비용을 줄이고 정상 `ENTER_NOW → 보조판정 → Main 최종 검증` 경로를 복구하는 작업이다.

최초 작성은 **상세계획 리뷰·보완**이었다. 이후 사용자가 compact 계획과 함께 구현·반복 코드리뷰·수정보완 및 완료 후 배포·재기동을 승인했다. 실행 결과는 [통합 구현 리뷰](../audits/main-post-warmup-bottleneck-compact-integration-review-2026-10-08.md)에 구분하여 남긴다. 이미 받은 승인을 다시 요구하지 않으며, 입증되지 않은 REST/WS source 의미 동등성을 추정하지 않는다.

**후속 계획은 §15의 AI PASS→Main 소비·제출 연결과 §16의 비상시감시 신호 관측·소비 보완이다.** PID 381039에서 확인한 별개의 처리 경계를 같은 실행 owner에 인계하며, B0~B7의 구현 이력을 되돌리거나 compact 연구를 재실행하지 않는다. 이번 사용자 지시는 상세계획 수립이며 §15/§16의 코드 구현·배포를 이 문서 수정과 함께 실행하지 않는다.

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

최초 계획 시점의 `run_sniper` outer-loop `drain_completed()`는 모든 완료를 꺼낸 뒤 `scanner_generation_id`와 `_is_scanner_watching_target()`으로만 target을 찾았다. fixed-watch 결과는 `fixed-watch:<원 claim token>` identity이므로 해당 scanner 검색으로 연결되지 않아 `target_or_generation_missing`으로 `discard_completed()`될 수 있었다. 이 분기 수리는 §14에 구현 인계됐으며, 그 이후 발견된 완료 소비 순서·terminal 결손은 §15에서 다룬다. caller 인자 추가만으로 B1을 닫지 않는다.

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

10/8 19:30 관측 이후의 후속 구현은 [잔여 네 병목 통합 개선계획](main-residual-capacity-budget-pass-history-bottleneck-implementation-plan-2026-10-08.md)을 따른다. 무신호 `kt00011` 예약·원 5초 예산·PASS의 Main 소비를 먼저 보완하고, 이 B5의 새 source 계약은 [430봉 상세계획 H0~H5](main-430-bar-shared-history-and-incremental-refresh-implementation-plan-2026-10-08.md)로 구체화한다. 이미 완료한 B0~B6 구현과 당시 배포 증거는 아래 이력대로 보존한다. 새 계획은 추가 구현·배포 영수증이 아니다.

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

후속 H0/H3는 430 raw 요청과 실제 필요한 완료봉/세션 구간을 구분한다. 현재 MTF는 다른 날짜·세션을 제외하므로 모든 소비자에 전일 prefix를 강제로 합성하지 않는다. 초기 adapter는 현행 입력을 보존하고, 필수 특징·quality·판정 parity가 확인된 consumer부터 명시적 필요 window로 selector를 보완한다. 동일 REST 이력 공유·분 단위 갱신은 raw/adjusted WS 합성 입증과 독립하여 진행할 수 있다.

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


최종 구현·배포는 `main-bottleneck-compact-20261008-v9` / code `7edeffe34cdca018b87fe981d24e4d61f91911a3` / Main PID 346886으로 완료했다. 활성 회귀 1,834건과 base/auxiliary 실제 소비를 확인했다. 최종 JSON stage 선택은 큰 AI 증빙 본문의 동일 문구를 사건으로 세지 않는다. 당일 5종목의 AFTER `_AL`·SOR admission/generation도 확인했다. 준비 이후 제한된 자연 창 144회는 모두 5초 미만이었으며, PID warm 누적 p99 2.693초·초기 원천 복원 9.102초와 미관측 provider/submit 단계는 위 통합 리뷰에 별도 남긴다. B5b 미지원과 과거 cron 지연 복구 warning을 전체 성공으로 바꾸지 않는다.

## 15. 최신 PID의 AI PASS 이후 제출 병목 보완계획

후속 사용자 요청의 네 병목 전체(무신호 용량·신호 예산·PASS 소비·430봉)는 [통합 개선계획 R0~R5](main-residual-capacity-budget-pass-history-bottleneck-implementation-plan-2026-10-08.md)에서 다룬다. 본 절 PB0~PB4는 그 안의 PASS 처리 세부 명세로 재사용하며, 구현·worker·terminal writer·배포를 중복 수행하지 않는다.

### 15.1 결정·기준선·범위

목표는 **정상 ENTER_NOW+PASS가 원 유효기간 안에 기존 Main 주문 경로로 한 번 전달되고, 전달하지 못한 판정도 정확한 종료 사유가 남도록 하는 것**이다. 정책 승률 재비교·새 prompt 연구·AI 호출 한도 변경은 이 수리의 선행 조건이 아니다. 기존 실행 owner `DirectFamilySourceRepairMainMechanisticEntry`와 B1/B2/B7 안에서 후속 P0 수리로 수행한다. 새 strategy family나 OPEN stable ID를 만들지 않는다.

기준은 [19:41:57 판정별 원천 대조](../../data/report/auxiliary_compact_adoption/2026-10-08/pass-submit-bottleneck-381039-194157.json)와 [19:30까지 자연 관찰](../audits/main-latest-release-post-warmup-rest-ws-monitoring-2026-10-08-1930.md)이다. 선택 릴리스 `main-retired-postclose-cleanup-20261008-v1`, commit `0c1f68968906395f12c121862876704afadc1e83`, PID `381039` / start ticks `3597010`, 재기동 18:48이다. 이 값들은 조사 기준이며 구현 시 실제 최신 selector/PID로 다시 고정한다.

| PASS 시도 | trace 생성 시 원 5초 잔여 | 확인한 결손·한계 |
| --- | ---: | --- |
| 주성 `aims-7793fcc0b31449c3d864` | 0.124초 | 첫 응답 후 검증·기록 4.422초. Provider 응답은 이미 신호 후 4.629초여서 원 예산 내 반환 불가. `_load_seen`의 당일 대형 trace 전체 해독은 유력 세부 원인이며 전 구간 귀속은 미확정 |
| 알테오젠 `aims-29c09add92d32848e9d9` | 0.739초 | outbox `response_received`, 실행 intent 미관측. 정확한 reject terminal 결손 |
| 알테오젠 `aims-d37f15a4907ddb798fad` | −0.100초 | trace 생성 시 이미 만료. 이후 native 종료 사유의 영구 연결 결손 |
| 알테오젠 `aims-a2bf764066d21c596b7f` | 0.143초 | 19:18:48.192 Main의 `trade_tick_quiet` 조기 반환 관측. worker 완료 시각과 최종 reject의 exact 연결이 없어 유일 원인으로 단정하지 않음 |

현재 PID의 정확한 ENTER_NOW→AI 시도는 8, PASS 4, transport timeout 4다. PASS outbox 4개는 모두 `response_received`, `intent_assigned`는 없고 주문 physical API 시작·submit guard 표본은 0이다. Main commit metric 3건을 PASS 3건 소비로 읽지 않는다. `decision_ts`는 trace 함수 진입 시각이며 worker 완료 시각이 아니다. 기존 보조 v2 네 scope의 자연 호출은 별도 미관측이고 위 4건은 v1 union 경로다.

현재 코드에는 worker 완료 event로 Main wait를 깨우는 연결이 이미 있다. wake-up을 새로 추가하는 것만으로 수리됐다고 하지 않는다. 문제는 wake-up 이후 fixed-watch를 WATCHING handler에 맡기는 순서, 그 앞의 새 평가/source gate, 원 claim 만료 처리와 기록, 첫 응답 후처리다. 이미 완료된 B1 caller 연결·quote 계약·provider 실패 분류는 보존한다.

### 15.2 구현 단위와 우선순위

| 단계 | 변경 owner | 결과물 | 선행·닫힘 조건 |
| --- | --- | --- | --- |
| PB0 원 시도 재현 | 기존 async/trace 테스트와 위 증거 | 4개 시도의 clock·identity를 축소 fixture로 구성; response clock/worker 완료/Main 소비 구분 | 원 본문 복제·실제 Provider 호출 없이 기존 실패 경로 재현 |
| PB1 완료 결과 우선 소비 | `kiwoom_sniper_v2`, `sniper_state_handlers`, `scanner_async_eval` | 완료 결과를 새 분석 gate보다 먼저 단일 Main owner로 전달 | PB0; 유효 PASS→기존 실행 owner 1회, 무효 결과의 명시 종료 |
| PB2 첫 응답 cold 비용 제거 | `ai_decision_trace`, 기존 기동/준비 owner, `ai_engine_openai` | trace/outcome 인덱스 사전 준비와 증분 재사용, 응답 경로 full scan 제거 | PB0; 첫 요청·자정·재기동, 공유 lock·Main 보호 처리 지연까지 검증 |
| PB3 exact terminal·consumer 연결 | 기존 pipeline/lifecycle writer, `buy_funnel_sentinel`, `submission_bottleneck_monitor` | 원 attempt별 소비 상태와 원인·시각을 작은 기존 전이로 연결 | PB1과 동시 구현; accepted 이후 주문 미진입은 별도 집계, 원 custody 유지 |
| PB4 통합 회귀·배포 인계 | B7·AC6 기존 owner | 불변 release, 호환 handoff, 새 PID·자연 결과 검증 | PB1~PB3 리뷰/반례 종료; 실제 주문 수를 코드 배포 조건으로 두지 않음 |

PB1과 PB3는 한 변경 단위다. PB2는 독립 검증할 수 있으나 첫 응답을 다시 잃는 상태를 남겨 전체 PASS 연결 수리 완료로 표시하지 않는다. 무신호 `kt00011` 반복 조회 축소는 기존 B5a의 별도 P1 후속이며 PB0~PB4 완료를 그 작업이나 B5b의 WS 역사 동등성에 묶지 않는다.

### 15.3 PB1 — 완료 결과의 소유권과 소비 순서

1. **완료 결과 조회에는 유효 claim 생성자를 선행시키지 않는다.** 저장된 원 request ID / generation / cache key / claim token으로 완료 객체부터 찾는다. `FixedWatchGeneration.from_claim()`가 TTL 검사에서 예외를 낸 뒤 결과를 무기록 폐기하는 현재 순서를 바꾼다. 현재 `_scanner_async_entry_cache_key()`는 같은 generation이면 저장된 key를 재사용한다. 이 동작을 보존하고 완료 소비 시 새 trigger/last-AI-time으로 key를 재생성하지 않는다. 원 identity가 없거나 충돌하면 가까운 symbol/시각으로 맞추지 않고 결손으로 기록한다. 결과를 찾았다는 사실은 BUY 권한이 아니다.
2. 일반 scanner와 fixed-watch 결과를 기존 coordinator에서 구분하고, 원 target ID·watch admission·source registration·policy/binding·PID identity에 결속한다. symbol만 같은 후속 target, 다른 claim 또는 다른 session에 결과를 적용하지 않는다. 이전 결과 정리는 이전 request 필드만 대상으로 한다.
3. fast exit/holding/SELL/cancel/체결·계좌 reconciliation의 기존 우선 처리를 보존한 뒤, 신규 평가용 cooldown·모멘텀/거래대금 gate와 신규 source 준비 전에 완료 결과의 disposition을 처리한다. `AI_WATCHING_COOLDOWN`의 새 분석 제한과 commit의 `COOLDOWNS[code]` 주문 제한은 구분하며 후자는 그대로 검증한다. worker/callback은 실행 상태를 변경하거나 주문하지 않는다. 기존 completion event·coordinator 용량을 쓰고 polling·worker·Provider 동시성을 올리지 않는다.
4. Main이 결과 소유권을 받은 뒤 **현재 시각의 원 epoch·monotonic deadline, target/state/manual veto, route/session/item/transport epoch, native branch 생존·정책 철회, canonical quote, 계좌·주문·수량·자본·cooldown**을 기존 경계에서 검증한다. pre-AI gate에 섞인 진짜 source 안전 조건도 없어지면 안 된다. 중복 검사만 분리하고 기존 안전 판단의 참조 입력·거절 의미는 보존한다.
5. 유효 결과는 기존 WATCHING 후속 실행·가격·수량 owner로 한 번 전달한다. async 결과와 inline 결과가 합류하는 **동일 후속 처리**를 사용한다. 원 prepared context·raw/decoded binding·검증 결과·last-AI/provenance 기록·후속 가격/수량 guard를 누락한 별도 BUY 경로를 만들지 않는다. 완료 소비 후 같은 loop에서 새 분석 분기로 다시 들어가거나 수량/주문 계산을 두 번 실행하지 않는다. `Main accepted`는 주문 intent/physical submit/fill과 별개다. AI PASS만으로 `ai_confirmed`, intent 또는 주문 성공 영수증을 합성하지 않는다.
6. **새 source 대기·재시도 기능은 이 수리에서 제외한다.** 현 `validate_scanner_async_commit()`의 `quote_stale_or_missing`, `cooldown_active`, state/route/native 불일치는 최종 거절이다. 이를 fresh quote를 기다리는 재검증으로 바꾸지 않는다. `deferred`는 아직 Main 차례를 기다리는 원 완료 객체의 관측 상태로만 사용한다. Main이 가져오면 기존 검증으로 accepted/rejected를 정하고, 원 deadline 만료는 즉시 expired 처리한다. 새 claim·AI 재호출·TTL 연장·타이머를 만들지 않는다. 기존 scanner recheck의 별도 계약도 fixed-watch에 새로 이식하지 않는다.
7. outer drain의 알림 큐, coordinator `_ready`, handler `take_completed`, orphan 정리가 동일 결과를 중복 소비하거나 먼저 삭제하지 않도록 소유권을 고정한다. `take_completed()`는 pop이므로 가져온 객체의 request/token과 현재 stock의 request/token을 비교한 뒤 **그 요청의 필드만** 정리한다. 후속 claim을 원 객체 대신 ack하거나 지우지 않는다. 별도 무제한 Main pending 저장소를 만들지 않으며 이관 중인 결과도 기존 미처리 용량·동일 요청 재dispatch 금지에 포함한다. 소비/정리 예외와 ready eviction은 원 request로 gap을 기록하고, crash는 `unobservable`로 복구 대사한다. capacity/eviction을 늘려 문제를 숨기지 않는다.
8. 원 **5초** 및 모든 최종 guard는 유지한다. 이미 만료된 과거 PASS를 새 PID에서 주문하거나 새 timestamp로 되살리지 않는다. fixture의 과거 PASS는 경로 검증 자료이고 실제 재전송 대상이 아니다.

### 15.4 PB2 — 필수 저장을 유지하면서 첫 응답의 전체 원장 조회 제거

현재 `prepare_ai_request_capture()`는 payload/prompt/request 인덱스를 준비하지만 `_SEEN_TRACE_IDS`, `_SEEN_OUTCOME_LABEL_IDS`는 첫 응답에서 `_load_seen()`으로 채운다. 아래 작업은 [원장 중복 제거·증분 계획](main-ai-comparison-ledger-dedup-and-incremental-storage-plan-2026-10-07.md)의 live/offline 분리·기존 객체 재사용 계약을 따른다.

- 기존 준비 owner에서 response trace와 outcome index까지 신규 native claim 평가 전에 준비한다. **`prepare_ai_request_capture()`의 index 목록만 늘리는 구현은 불충분하다.** 이 함수는 Main loop 외에도 `capture_ai_request()`의 `_WRITE_LOCK` 안에서 호출된다. 요청/응답 저장의 readiness 확인과 대형 초기 구축을 분리해 fallback 호출이 원 요청 예산 안에서 전체 scan을 시작하지 않게 한다. 장중 모든 요청에서 대형 JSONL을 다시 읽거나 단순히 `seen=set()`으로 시작하지 않는다.
- 현 Main loop의 사전 준비는 완료 수집·Main 보유 처리보다 앞에 있다. fast exit thread가 켜졌다는 사실만으로 모든 보호 처리가 보장됐다고 하지 않는다. 기동·자정·교체 후 구축은 기존 준비 owner의 bounded 작업으로 나누고 Main 완료 소비·보유/체결 처리 기회를 보존한다. 대형 파일을 읽는 동안 `ENTRY_LOCK`이나 공통 trace `_WRITE_LOCK`을 계속 점유하지 않는다. 재진입 가능한 준비를 위해 새 thread/Provider 동시성이나 별도 무한 작업자를 추가하지 않는다. 준비 중 관측된 신호의 실제 발생 시각/5초는 그대로이며 준비 완료 시각으로 새로 찍지 않는다.
- 실행 중 응답 경로에서는 준비된 인덱스와 정상 append 이후 증분만 사용한다. 당일 전체 trace/outcome의 `_load_seen` 호출·전체 JSON decode 수는 **0**이어야 한다. 최초 index 구축이 필요하면 새 entry claim 밖의 기존 준비 단계에서 한 번 수행하며, 초기화 중 이미 보유한 포지션의 보호와 callback을 멈추지 않는다.
- KST 날짜 전환, file replacement/truncate/rotation, 재기동, concurrent append, partial 마지막 행과 lock 경계를 정의한다. index의 source path·date·inode/generation·소비 offset이 맞아야 재사용하고 크기만 같다는 이유로 신뢰하지 않는다. lock 밖에서 읽은 snapshot은 기존 writer의 동기화 경계에서 generation과 append 증분을 다시 대조한 뒤 게시한다. partial tail은 마지막 완결 행의 offset에서 재개한다. 읽기/권한/형식 오류와 확인된 빈 파일을 구분한다. 현 `_load_seen()`의 오류 시 부분 set 반환을 완성 index로 게시하지 않는다. 다음 날 준비 실패를 조용한 empty index나 매 응답 full scan으로 우회하지 않는다.
- 추가 영속 index가 필요한지는 기존 저장 계약을 먼저 대조한다. 필요한 경우 기존 trace 소유 위치의 **재구축 가능한 key/offset index 한 개/일자**로 제한하고 본문·후행 라벨·AI 응답을 복제하지 않는다. offline 비교 ledger나 opportunity outbox를 live trace dedup index로 전용하지 않는다. 배포마다 새 비교 원장을 만들지 않는다.
- 영속 index를 채택하면 trace ID와 outcome label ID의 namespace를 분리하고 **원 행의 정상 append 후에만** index를 전진시킨다. 원 행 저장 후 index 저장 전 crash는 마지막 검증 offset 이후만 복원한다. trace 성공/outcome 실패는 각자의 상태를 보존해 outcome 누락을 완료로 오인하지 않는다. 재시작은 과거 epoch를 참조하되 이전 PID의 monotonic 값을 새 PID deadline으로 사용하지 않는다. 일자별 메모리 cache도 진행 중 요청의 날짜 참조를 보존하면서 만료 일자를 회수하며, 세대별 복제 cache를 계속 쌓지 않는다.
- 현재 필수 request/source 본문, 원 AI 응답, decoder/validator 결과, trace와 outcome seed의 저장·동일 ID 중복 방지·권한/파일 교체 방어를 유지한다. 기록을 생략하거나 미완료 append를 성공으로 표시해 시간을 줄이지 않는다. index/저장 오류의 기존 처리 의미를 보존하고 새 전역 거래 차단을 임의 추가하지 않는다.
- `response_received_epoch`, `validation_started/completed`, `trace_append_completed`, `worker_completed`, `main_take`, `main_disposition`을 구분하여 기존 bounded 성능 계측에 연결한다. trace의 기존 `decision_ts` 의미를 과거와 다르게 재정의하지 않는다. 첫 응답 4.422초 전체를 특정 함수 한 개에 사전 귀속하지 않는다.

PB2의 기능 종료는 첫 응답에도 full-scan 0, 원문/ID 동등성과 cold/warm 경로의 동일 성공·거절 계약이다. 부하 fixture의 정량 결과는 전후 같은 입력/clock/분모로 보고한다. provider 도착 clock·후처리 부하와 모든 기존 guard 통과를 고정한 정상 fixture에서는 후처리·Main 소비까지 원 deadline 안에서 닫힘을 검증한다. 마감 직전 응답을 모두 제출한다는 보장이 아니며 처리 중 원 예산을 넘은 응답도 올바르게 거절되어야 한다. 공유 lock 대기·최대 준비 chunk·Main 보호 처리 간격도 전후 비교하며 비용이 단순히 응답에서 Main 앞부분으로 이동한 결과를 개선으로 인정하지 않는다. 이는 구현 성능 검증이고 새 0.x초 거래 제한이나 정책 진입 gate가 아니다.

### 15.5 PB3 — 종료 영수증·기존 감시 소비 연결

현재 `reversal_operating_outbox`의 `response_received → intent_assigned`는 전송·주문 custody 계약이다. 이 상태 전이를 되감거나 `expired/rejected`를 억지로 추가해 기존 정책 hash·replay·불확실 예약을 변경하지 않는다. **AI 원 응답은 outbox에 보존하고 실행 소비 결과는 기존 ENTRY_PIPELINE/lifecycle 경로의 작은 전이 기록으로 연결**한다. 새 per-attempt 원장 파일·본문 복제·별도 무한 수집기를 만들지 않는다.

영수증은 원 `evaluation_attempt_id`, `decision_trace_id`, `opportunity_key`, native signal/claim/request identity, target/watch generation, PID/start ticks/release, machine/auxiliary hash를 결속한다. 해당 단계에서 아직 생성되지 않은 ID는 null+원인으로 남기고 가짜 ID를 만들지 않는다. **소비/거절 전이의 신원은 꺼낸 immutable 결과가 소유한다.** 현재 stock의 `last_watching_ai_machine_primary_fields`나 새 claim을 기본값으로 합쳐 이전 결과의 원인을 바꾸지 않는다. 현재 guard가 본 원천은 별도 참조로 기록한다. 필드는 기존 pipeline의 문자열/JSON projection 규칙에 맞춰 publisher와 reader를 함께 검증한다. 고정 allowlist의 ID·시각·검사값·이유와 원문 참조/hash만 기록하며, `_log_entry_pipeline`의 기본 enrichment가 전체 WS snapshot·AI payload·보조 binding 본문을 다시 붙이지 않도록 실제 writer 크기를 검사한다.

| 관측 전이 | 기록할 의미 | 금지되는 해석 |
| --- | --- | --- |
| worker 완료 | 응답·의미 검증·필수 기록을 마친 실제 완료 시각과 원 deadline | trace 생성 시각을 worker 완료로 대체 |
| Main accepted | 원 결과를 기존 Main 실행 owner에 한 번 전달 | intent/submit/fill 성공으로 집계 |
| Main deferred | 완료 객체가 Main 차례를 기다리는 상태, 원 소유자·만료시각 | 거절된 quote/source의 새 재검증 또는 새 5초 승인 |
| Main rejected/expired/orphan | 정확한 원 검사 결과·남은 예산·source receipt, 정리한 request | 다른 시도의 최근 source block을 원인으로 붙이기 |
| intent·submit·broker terminal | 기존 주문 owner의 실제 ID·영수증과 연결 | 미호출을 broker 거절로 집계 |

원 request/생산 PID/전이 종류에 결속된 결정적 event ID를 사용한다. worker 완료와 Main disposition은 다른 전이이며, 반복 polling으로 같은 전이를 복제하지 않는다. **주문 실행의 단일 소유권과 진단 행의 중복 제거는 별개**다. 재읽기·재기동 후 같은 진단 행이 재관측되어도 reader가 같은 전이로 합친다. 서로 충돌하는 최종 전이는 최신 시각으로 덮지 않고 해당 attempt의 증빙 결손으로 남긴다. `emit_pipeline_event()`의 `structured_append_succeeded`를 확인하고 raw/companion/summary 실패를 구분한다. 파일 append 반환은 crash 이후 영구 보존이나 broker 완료 증거가 아니다. writer failure·queue full·process crash에서는 기록 성공을 가정하지 않고 bounded 기존 health/오류 counter로 gap을 남긴다. 진단 기록 실패가 이미 허용된 주문을 되돌리거나 주문 재시도를 유발하지 않게 하며, 기존 필수 source/outbox 저장 실패 규칙은 그대로 둔다. 무기록을 피하려고 Main에서 대형 파일 재스캔·새 무제한 동기 I/O를 추가하지 않는다. custody 예약은 해제하지 않으므로 기록 손실이 AI·주문 재전송 권한으로 이어지지 않는다.

소비 연결은 아래 기존 owner에서 닫는다. 새 전이를 모두 주문 stage로 등록하거나 전체 payload를 projection whitelist에 추가하는 방식은 쓰지 않는다.

| 기존 owner | 수정·검증 경계 |
| --- | --- |
| `sniper_state_handlers._log_entry_pipeline` / `_MACHINE_PRIMARY_LINEAGE_PIPELINE_STAGES` | 원 결과의 명시 신원을 보존하는 작은 전이 경로; 현재 stock enrichment와 본문 중복 배제 |
| `scalping/main_lifecycle_journal.PIPELINE_STAGE_MAP` | `scanner_async_result_commit`의 기존 scanner 매핑과 fixed-watch 완료 소비 의미를 대조; 소비를 submit/fill로 매핑하지 않음 |
| `utils/pipeline_event_logger.emit_pipeline_event` / `_project_fields_for_compact_stream` | raw·compact·기존 summary에서 원 event/attempt/clock/상태 참조 보존과 각각의 append 결과 확인 |
| `engine/buy_funnel_sentinel`의 machine funnel·slim cache → `monitoring/submission_bottleneck_monitor.snapshot` | exact PASS 모집단·상호배타적 disposition·accepted 이후 기존 제출 funnel 연결, cache 재읽기 parity |

예산 만료/정상 native 종료는 API 원천 결손과 구분하며, fixed-watch를 scanner promotion 결손으로 다시 분류하지 않는다. 새 알림 채널을 만들지 않고 기존 보고/알림 owner가 exact event를 의미 기반 중복 제거해 소비한다. bounded 읽기 범위·cache 세대가 모집단을 덮지 못하면 coverage를 partial/unobservable로 보고한다. 전체 대형 원장을 다시 읽어 0건을 증명하거나 잘린 tail을 결손 0으로 보고하지 않는다.

판정 분모는 current PID의 exact ENTER_NOW+PASS attempt다. **PASS = accepted + final rejected + pending + unobservable**를 같은 원 attempt·as-of에서 검증한다. 이는 전이 로그 수가 아니라 attempt별 상태 한 개의 합이다. accepted 뒤 최종 수량/가격 guard가 거절해도 소비 집계는 accepted 한 건이며 해당 미진입 사유는 별도 하위 funnel에 둔다. 소비 전 reject/expired/orphan은 final rejected이고, 원 deadline 안에서 실제 미처리 owner가 확인된 경우만 pending이다. deadline 이후 terminal이 없거나 최종 증빙이 충돌/유실된 경우는 unobservable이며 만료됐다는 사실만으로 reject를 합성하지 않는다. timeout/VETO/RECHECK, source-only probe, 과거 PID, 같은 attempt의 반복 로그를 PASS 분모에 섞지 않는다. 관측 창 전후 carry-in/out을 같은 규칙으로 표시하고 raw AI 응답만 있는 사건을 검증된 PASS로 승격하지 않는다.

새 진단 필드는 `metric_role=source_quality_gate`, `decision_authority=report_only`, `window_policy=current_pid_exact_attempt_with_carry_in_out`, `sample_floor=none`, `primary_decision_metric=pass_to_main_disposition_coverage`, `source_quality_gate=exact_identity_and_clock`, `forbidden_uses=policy_or_order_authority,economic_success_inference`를 선언한다. 진단 수치는 정책 채택·주문 권한을 만들지 않는다.

### 15.6 필수 반례와 리뷰 종료 기준

기존 `src/tests/test_scanner_async_entry_bridge.py`, `test_scanner_async_eval.py`, `test_hot_path_ai_dispatcher.py`, `test_ai_decision_trace.py`, `test_fixed_watch_submit_source_repair.py`, `test_submission_bottleneck_monitor.py`와 실제 변경 소비자의 기존 회귀를 확장한다. 새 runtime 모듈이 필요하면 `src/engine/scalping` 또는 기존 monitoring/lifecycle 소유 위치를 먼저 검토하고 engine root를 늘리지 않는다.

| 검증 | 필수 결과 |
| --- | --- |
| 실제 outer drain→일반 WATCHING 두 iteration, native/scanner 혼합 | 실제 소비·guard·WATCHING 후속 합류는 mock으로 대체하지 않음; 유효 ENTER_NOW+PASS는 기존 실행 owner 1회, 중복 callback/두 소비자 경쟁으로 intent 증가 0 |
| 새 분석 cooldown·거래대금/모멘텀 분기가 닫힌 동안 완료 | 완료 결과는 disposition 단계에 도달; 실제 source/quote/native/계좌 안전 위반은 기존 이유로 거절 |
| 잔여 0.739/0.143초, 이미 −0.100초, 첫 검증 4.422초 재현 | trace 시각·실제 완료·Main take를 구분; 원 5초 경계 4.999/5.000/5.001 보존, 늦은 BUY 0 |
| 처리 중 만료·target 제거·claim 교체·last-AI/trigger 변경·manual veto·정책 철회 | 저장된 원 요청으로 조회/ack, 후속 claim 필드·다른 owner 삭제 0; 새 평가 진입·동일 결과 재실행 0 |
| 완료 큐 대기→Main 소비 / stale quote 최종 거절 후 fresh quote | 동일 결과 disposition 1개; 거절된 결과를 되살리는 재검증·Provider 재호출·deadline 갱신 0 |
| cold 416MB 상당 trace, warm 재사용, 자정·restart·rotation·partial tail | 실제 운영 원본을 복제하지 않는 격리 fixture; 응답 경로 full scan 0, 중복/소실/무검증 empty-index 0, 첫 비용 별도 보고 |
| 요청 안의 준비 fallback·준비 중 holding/완료 소비·동시 append·trace 성공/outcome 실패 | 대형 scan의 응답/요청 경로 재유입 0; 공유 lock/보호 처리 간격 측정, 이전 offset·namespace 보존, 부분 index를 ready로 게시하지 않음 |
| 저장/queue 실패·단계별 crash·late callback·ready capacity/eviction | 원 예약/custody 보존, 기록 gap 명시, 존재하지 않는 terminal 성공 합성 0, 자동 재전송 0 |
| v1/v2 wire, 원 확인점 전후 overlay 전환 | 논리 판정·raw/decoded binding·부모·scope 유지; codec/prompt 재연구 없이 영향받은 호출 경로 검증 |
| 새 terminal의 writer→projection/cache→monitor→기존 notification 상태 | accepted 후 guard reject·중복/역순 event·충돌 terminal·tail 누락에도 attempt별 상호배타적 보존식; 정상 만료의 API 오분류·반복 알림 0 |

fake clock/transport와 격리된 data root를 쓰며 실계좌·Provider 호출로 테스트 표본을 만들지 않는다. broad test를 먼저 돌리지 않고 위 변경 owner의 targeted pytest→compile→`git diff --check`를 수행한다. 리뷰→수정→반례 회귀→재리뷰에서 in-scope finding 0 후 배포 후보를 만든다. 수리된 경로는 같은 원 입력과 시간에서 비교하고 단지 주문 수가 늘었다는 이유로 guard 동등성 PASS를 선언하지 않는다.

### 15.7 배포·복구·자연 수용 인계

1. 실행 단계에서 최신 dirty diff·선택 release·PID·기계 128경로/보조 overlay·진행 중 Provider/주문 상태를 다시 고정한다. 새 연구·비교 원장을 생성하거나 현재 정책을 재발행하는 것이 이 코드 수리의 기본 절차가 아니다.
2. PB1~PB3와 영향받은 v1/v2 reader/기동 경로를 함께 검증한 immutable release로 인계한다. 실제 실행 지시와 기존 승인 범위에 따라 배포하며 이번 문서 작성은 배포 실행이 아니다. hard-safety·원 예산을 바꾸는 추가 정책안은 섞지 않는다.
3. graceful drain·실제 물리 작업 terminal/uncertain custody를 보존하고 원 응답/intent를 읽을 수 있는 rollback release만 준비한다. 이전 PASS를 재전송하지 않는다. 프로세스 restart 후 메모리 pending이 사라진 사건은 원 영수증의 unknown/reconciliation 상태로 인계하고 성공/실패를 추정하지 않는다.
4. 최종 코드 hash가 바뀌는 기존 정책 reader/호환 evidence와 장중 handoff를 재검증한다. 현재 checklist와 원 AUTO strict 블록은 유지한다. 실제 영향이 있으면 기존 owner 절차로 필요한 준비만 갱신하고 `strict_checklist_generation_stale`를 과거 PASS 복사·EOD/연구 전수 재생성으로 덮지 않는다. 예정 20:10 장후가 실행 중이면 같은 producer를 중복 실행하거나 중간 release를 섞지 않는다.
5. 새 PID에서 5종목의 session admission, exact machine/auxiliary 소비, 첫 자연 응답의 후처리, 모든 PASS의 disposition·intent/submit을 확인한다. **첫 cold 응답과 warm 응답을 모두 분리 관찰**하고 없으면 해당 항목은 `not_observed`로 남긴다. 삼성과 비삼성, compact-v2 네 scope와 기존 v1 scope를 나눠 표기한다.
6. 자연 종료 기준은 원 claim deadline을 지난 관측 PASS의 Main disposition 누락 0, 중복 execution/Provider 0, 유효 정상 fixture의 기존 제출 경로 연결, 원천·주문 안전 위반 0이다. accepted 이후 주문의 정상 미체결/진행 상태와 Main 결과 소비의 pending을 구분하며 30분 경제 outcome 성숙을 이 코드 수리의 조건으로 두지 않는다. 실제 PASS가 guard에서 정당하게 종료돼 주문 0일 수 있으며 이를 코드 실패 또는 경제성 성공으로 바꾸지 않는다. natural 표본을 만들기 위한 AI 호출·주문은 수행하지 않는다.

결과 보고는 코드 리뷰/배포/PID/자연 accepted·rejected/실제 intent·submit·fill/경제성을 분리한다. 현재 4건의 결손 terminal을 사후 추정값으로 보충하지 않는다. 이 계획은 구현 가능한 수리·검증·배포 순서를 정한 상태이며 PB0~PB4 완료 영수증은 후속 실행에서 작성한다.

### 15.8 후속 계획 리뷰에서 수정한 구현 공백

| 발견한 계획 공백 | 확정한 보완과 닫힘 근거 |
| --- | --- |
| quote/source 거절을 새 대기로 바꿀 여지 | 기존 commit validator의 최종 거절 유지. deferred는 완료 큐 대기의 관측만 하며 stale 거절 후 fresh quote로 재실행하지 않는 회귀 추가 |
| 소비 위치만 옮기면 기존 WATCHING 후속 처리·후속 claim 정리가 달라질 수 있음 | 원 key 재사용, immutable 결과 기준 신원/ack, 공통 후속 합류, token 비교 정리와 단일 용량 소유권을 명시 |
| 준비 함수의 index 목록 확장만으로 요청 안 scan·Main/holding 지연이 재발할 수 있음 | 요청 내 fallback과 준비 owner 분리, bounded 구축·짧은 게시 lock, 완료/보호 처리 간격과 정상 원 예산 fixture 검증 |
| 부분 index·날짜/파일 교체·append 중 crash의 상태가 불명확 | 완결 offset·generation·ID namespace, trace/outcome 개별 성공, 원문 이후 index 전진, 날짜 cache 회수 요건 확정 |
| 새 stage가 현재 stock 신원을 잘못 붙이거나 compact/cache에서 유실될 수 있음 | 원 객체 신원의 작은 전이와 writer→lifecycle/projection→Sentinel→monitor의 실제 owner 명시; append 상태·tail coverage 검증 |
| accepted 후 주문 guard 거절과 소비 전 거절이 중복될 수 있음 | attempt별 상호배타적 소비 상태와 별도 제출 funnel; 중복·역순·충돌·기록 실패 반례 추가 |

이 표는 계획 공백의 보완 기록이다. 실제 4건의 미진입 원인을 추가 확정하거나 PB0~PB4 구현 완료를 뜻하지 않는다. 캐시 key는 현 코드가 같은 generation에서 재사용하고 있음을 확인했으며, 그 자체를 새로 발견한 운영 결함으로 집계하지 않는다.

재리뷰 뒤 두 변경 계획의 로컬 링크/anchor **55개**, print-only parser **22항목·현재 Main owner 1개·경고 0**, `git diff --check`를 검증했다. checklist SHA `4aee28ee1c0fa26d34d8f7f7ecac25432e6680ab226ec805c59b635bb11b48ed`와 현재 handoff의 frozen 입력 경계는 유지했다. 코드 회귀·성능 수용은 PB0~PB4 실행 단계의 미완료 검증이며 문서 검증으로 대체하지 않는다. 이번 작업에서는 문서 두 개만 수정했으며 pytest·AI/broker 호출·배포·재기동·장후 재실행을 수행하지 않았다.

## 16. 비상시감시 no_current_operating_signal 후속 개선계획

[비상시감시 상세계획 NS0~NS5](main-nonfixed-native-signal-observation-and-consumption-remediation-plan-2026-10-08.md)를 기존 Main owner와 통합 R2b에 인계한다. 이번 범위는 상세계획이며 §15의 PASS 이후 수리와 구현·주문 owner를 중복 생성하지 않는다.

PID 381039의 18:49~19:40 비상시감시 37종목·71회는 snapshot 부재로 반환됐다. 보존자료 재현에서는 실제 가격대의 알루코 4건·에스엠벡셀 1건이 조회 시 이미 8.836~16.631초였다. 15~20초 probe 원천 대기 뒤 신호를 한 번 조회하는 경계와 일부 branch의 60/120초 관측 부족을 보완한다. 이는 실제 주문 기회 5건 누락의 확정 증거가 아니며, 전체 71건을 같은 원인으로 분류하지 않는다.

구현은 원천 사전 준비·비소비 machine-only snapshot 조회·Main의 단일 실행 claim 연결을 먼저 닫는다. 장기관측은 5개 probe 상한 안의 공정 배분·기존 60초 watchdog·exact lease 해제/편입과 함께 검증한다. 신호/result/관측 lease의 시계를 구분하여 원 5초 TTL·native 생존·원천/주문 guard를 유지한다. raw-ready의 다른 가격대/backend와 실제 selected-ready를 구분하고 기존 diagnostics/monitor에 원인 영수증을 연결한다.

실제 구현 위치·단계·반례·성능 분모·복구는 NS 상세계획이 소유한다. 현재 checklist 봉인과 동일 stable ID를 유지하며 B0~B7 완료 이력·기존 §15 PB 수리·R4 430봉·compact 연구는 각각의 상태를 보존한다.

후속 계획 리뷰에서 NS의 결과 전달 구간을 보완했다. scanner의 동기 panel REST와 결과 drain을 분리하고 EventBus의 실제 callback thread→Main inbox를 명시한다. 기존 단일 exact lease의 `adopted/removing`·ACK와 관측 interval을 보존하며 expected event의 원자적 claim·원 monotonic deadline을 연결한다. P0에는 이 짧은 lease의 인계 수리까지 포함하고, 60/120초 장기관측 확대만 NS1에 분리한다. pinned 기계 파일 수정은 일반 handoff만으로 해결되지 않으므로 NS §9.1의 loader/code-pin 계약을 따른다. 별도 구현·runtime 변경은 이번 문서 리뷰에 포함하지 않는다.

## 17. PASS 후속 통합 구현 결과

PB1의 완료 결과 우선 소비·요청별 단일 종료, PB2의 원장 사전 인덱스 준비/증분 append, PB3의 기존 compact→Sentinel→monitor 연결을 구현했다. 늦은 결과·삭제/교체된 generation도 원 ID로 꺼내 종료하고 새 요청의 상태를 지우지 않는다. accepted는 기존 실행 경로 인계이며 주문 성공이 아니다. PB4의 작업본 검증과 배포 이후 자연 수용은 분리한다.

검증 수치·수정한 반례·공식 API SHA·배포 보류 경계는 [통합 실행 리뷰](../audits/main-pass-residual-history-nonfixed-implementation-review-2026-10-08.md)에 한 번 기록한다. 실행 owner는 기존 `DirectFamilySourceRepairMainMechanisticEntry`를 유지하며 이번 작업은 checklist 봉인/현행 정책을 재발행하지 않는다.

### 17.1 10/10 배포 상태 대조와 후속 재점검

위 배포 보류는 10/8 구현 당시 기록이다. [10/9 통합 배포](../audits/main-integrated-uncommitted-deployment-review-2026-10-09.md)를 거쳐 현재 선택된 `main-holding-profit-exit-20261009-v4`에는 해당 개선과 mixed-row 후속 수리가 반영돼 있다. 10/10 확인 시 Main은 다음 예약기동 대기이며 `actual_pid_consumed=false`이므로 자연 PASS의 제출 병목 해소는 아직 확인되지 않았다.

[10/10 재점검·보완계획](main-pass-submit-recheck-and-latency-remediation-plan-2026-10-10.md)은 기존 관련 회귀 164건 통과와 별도로 결과 pop 이후 예외 처리, 제출 함수까지의 통합 검증, 전이 간 판정 신원 검증, 동기 진단 기록 지연을 보완한다. 이는 과거 PASS 4건의 직접 원인을 새로 확정한 결과가 아니다. 후속 구현은 이 계획 S1~S4를 따르며 기존 PB의 원 deadline·단일 실행·필수 원천 저장 계약을 유지한다. 10/10 checklist는 없어 과거 owner를 오늘 실행 owner로 대체하지 않고, 봉인된 10/12 checklist도 이번 계획 수정에서는 보존했다.

같은 날 후속 계획 리뷰에서는 결과 인수 context와 모든 폐기 caller, 제출 함수 본문·intent를 통과하는 adapter 경계 검증, 기존 관측 executor의 유한 접수와 raw 저장 성공 구분까지 명시했다. 원 판정 발생/물리 기록 시각과 구버전·자정 관측창을 보존하며 정상 경로 수리를 추가 진단 분류보다 먼저 닫는다. 구체적 구현 경계와 리뷰 보완표는 후속 계획 §3.1/§4.1/§5~§6/§9가 소유한다.
