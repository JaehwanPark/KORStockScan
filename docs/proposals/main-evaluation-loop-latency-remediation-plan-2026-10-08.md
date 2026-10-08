# Main 평가루프 처리 지연 개선계획 — 2026-10-08

## 1. 목표와 실행 경계

신호 확인부터 Main 평가까지의 지연을 줄인다. 우선 정책 조회·검증·구성의 중복을 제거하고, WS 공용 잠금 안에서 수행하는 전체 데이터 복사를 개선한다. 오류 탐지의 반복 원천 읽기는 후속 순위로 다룬다. **5초 claim 유효기간과 매매 조건을 유지한 상태에서 처리 경로를 개선**한다.

이번 요청은 **계획 수립**이다. 이 문서 작성으로 구현·패키지 설치·provider 호출·정책 발행·배포·재기동을 실행하지 않는다. 다른 작업에서 이미 승인된 후속 조치는 해당 범위와 영수증을 그대로 따르며, 이 계획이 추가 승인이나 경제적 적격성 입증을 요구하지 않는다.

실행 소유자는 [오늘 체크리스트](../checklists/2026-10-08-stage2-todo-checklist.md)의 기존 `DirectFamilySourceRepairMainMechanisticEntry`다. 아래 `LP0`~`LP6`는 그 항목 내부 단계이며 별도 OPEN owner를 만들지 않는다. 관련 계약은 [독립 탐지·기여도 계획](main-operating-policy-independent-detection-and-contribution-evaluation-implementation-plan-2026-10-07.md), [원장 증분 저장 계획](main-ai-comparison-ledger-dedup-and-incremental-storage-plan-2026-10-07.md), [시간외 등록·상태 보완 계획](main-pre-after-pattern-registration-and-status-consistency-remediation-plan-2026-10-08.md)이다.

## 2. 근거와 기준 시점

[읽기 전용 점검 결과](../../tmp/loop-latency-inspection-20261008/findings.md), [측정 영수증](../../tmp/loop-latency-inspection-20261008/findings.json), [실행 스택 표본](../../tmp/loop-latency-inspection-20261008/stacks-24520-second.jsonl)을 근거로 한다. 구현 착수 시 작은 증빙 manifest를 기존 audit 보존 계약에 인계하고, 이 tmp 증거를 임의 정리하지 않는다.

| 구분 | 확인된 사실 | 해석 범위 |
| --- | --- | --- |
| 병목 측정 PID | `24520`, release `pre-after-registration-20261008-v1`, commit `b464f6c81d1a5ac104fc0afd8ef8e499ed9344cf` | 09:32:55.641~09:33:45.808, 약 50초의 표본 |
| Main 정책 경로 | Main 관측 99개 중 loader 53개, configure 6개 | 합계 59/99, 약 59.6%; 정확한 단계별 경과시간·CPU 비율은 아님 |
| PID 소비 확인 | Main 관측 99개 중 35개 | loader 표본과 중첩하므로 합산 금지 |
| WS 전체 복사 | WS 전달 관측 99개 중 39개가 `_snapshot_target` | 별도 10초 관측에서 해당 스레드 CPU 약 3.51초 |
| 보고용 검증 | 오류 탐지 스레드가 별도 10초 동안 논리 읽기 약 70.4 MB | 물리 디스크 병목·cache thrashing은 미확정 |
| 같은 PID의 긴 루프 | 09:31:51 39.8654초, 09:34:06 42.9034초, 09:35:18 21.5496초 | 전체 Main 반복 시간; 다음 polling sleep 제외 |

표본은 target 정지·신호 전송·코드 주입 없이 CPython debug offsets의 함수/파일/행만 읽었다. 원자적 스냅샷은 아니며 100회 관측 전체 스레드에서 87개 프레임 읽기 오류가 있었다. Main/WS의 실제 관측 분모는 각각 99다. 신호 만료 수와 `no_current_operating_signal`의 직접 인과관계는 아직 입증하지 않았다.

**작성 중 09:40 KST 재확인:** 선택 release는 `pre-after-intraday-20261008-v1`, commit `f08405fb063470b17bf3348f84feecb6d3d19e96`, PID receipt는 `34821`/start ticks `299797`로 바뀌었다. current는 v6 bundle `40fb3ec7d5f44e2e34044f2a14e2d0d06dd6ea264f69b5f1481be899f2a4a689`, 효력 시각 `2026-10-08T09:38:51.868863+09:00`이다. 위 v5/PID 24520 수치를 새 PID의 측정값으로 전용하지 않는다. LP0에서 실제 최신 release/PID/v6 소비·보조 binding·시간외 등록 상태를 다시 고정한다. 성능 개선을 위해 승인된 v6/추가 목록을 v5로 되돌리지 않는다.

## 3. 유지할 계약과 제안 목표

- 신호 epoch, 공통 5초 claim TTL, quote/source freshness, route/item/transport epoch, 정책 정의·목록·보조 입력/응답 계약을 보존한다. claim 획득·응답 대기로 TTL을 재기산하지 않는다.
- 현재 승인된 Main 판정 조건, provider 간격/한도·중복 예약, broker/account/order/수량/자본/cooldown/manual veto와 hard/protect/emergency 안전을 보존한다. 새 병렬 주문 owner를 만들지 않는다.
- raw 관측의 무손실 전달과 기존 최신 상태 이벤트의 병합 방식을 각각 보존한다. 이벤트나 이력을 임의 생략해 지연만 낮추지 않는다. 보유/청산·취소·late fill·기존 custody 소비자도 영향 범위에 포함한다.
- 초기 정책 등록에 EV·holdout·최소 거래/표본·체결·수익 조건을 추가하지 않는다. 성능 검증은 구현 종료 기준이며 정책의 신규 적격성 gate가 아니다.

아래는 **이번 계획의 초기 엔지니어링 목표**이며 현행 매매 가드나 이미 달성한 수치가 아니다. LP0에서 입력률·이력 길이·관측 구간을 먼저 고정하고 측정한다. 목표를 바꾸려면 결과와 변경 근거를 남기며 단순 미달을 PASS로 바꾸지 않는다.

| 대상 | 초기 목표 | 별도 공개할 값 |
| --- | --- | --- |
| 정상 원천의 warm Main work loop | p95 ≤ 2초, p99 < 5초 | 표본 수, max, 5초 초과 수, cold start/기동 복원 시간 |
| 신호 확인→실제 claim 평가 시작 | p95 ≤ 1초, p99 ≤ 2초 | 미평가/만료/관측 불가 수; 실제 발생한 확인점만 분모 |
| WS 공용 잠금 점유 | p99 ≤ 10ms | lock 대기/점유 각각의 max, 입력률·queue backlog |
| 동일 frozen 입력·스케줄의 결과 | 정책 정의·입력·중복 소유권 보존, 실제 시각 oracle의 판정과 일치 | 처리 시각 개선에 따른 소비 가능 신호 변화는 별도 |

provider 응답시간과 계좌/주문 대기는 따로 측정한다. 위 목표 충족이 AI 응답 후 제출까지 5초 내 완료나 실제 주문·수익을 보장하지 않는다. 기존 60초 간격 `LOOP_METRICS` 표본만으로 p95/p99를 산출하지 않는다.

## 4. 정책 검증·구성 중복 제거

소유 경로는 [Main refresh](../../src/engine/sniper_state_handlers.py), [정책 loader](../../src/engine/scalping/mechanistic_entry_runtime_policy.py), [PID·보조 소비 기록](../../src/engine/scalping/reversal_auxiliary_intraday.py), [현재 backend dispatch](../../src/engine/scalping/reversal_current_backend.py)다. v5/v6의 configure와 native carry를 함께 조사한다.

현재 refresh는 `load_effective → record_pid_consumption(다시 load_effective) → configure_bundle → claim_snapshot`을 수행한다. 캐시 hit도 모든 의존 경로의 `stat/resolve`와 bundle 깊은 복사를 거치며, configure는 같은 세대에서도 family/부모 검증과 복사를 수행한다.

### 4.1 한 평가에서 검증 결과 한 번 소비

1. 기존 loader를 검증의 단일 소유자로 두고, 검증된 불변 view와 그 검증 식별자를 반환하도록 보완한다. 별도 경쟁 cache나 workspace fallback reader를 만들지 않는다.
2. 식별자는 신뢰된 data root/anchor, KST 대상일, current pointer·bundle/family/schema, 실제 실행 code/contract identity, scope 실행 hash, 보조 overlay/binding·취소 세대, 의존 원천 검증 결과에 결속한다. PID 소비 기록은 PID/start ticks/cwd/release도 포함한다. 소스 출처 없이 외부에서 만든 dict를 검증 완료로 받지 않는다.
3. 같은 평가 안의 PID 영수증·backend 구성·assessment에 그 view를 전달한다. 소비 기록 함수가 같은 policy를 재로딩하거나 128 scope 전체를 매번 재구성하는 중복을 없앤다. 결정/quote/claim 결과를 다음 평가까지 재사용하는 cache는 만들지 않는다.
4. 진입 전·AI 응답 후·제출 직전의 기존 검증 경계와 실패 차단은 유지한다. view를 오래 쥐거나 mutable bundle을 공유해 검증을 우회하지 않는다. 계약상 검사가 필요한 경계에서는 현재 세대와 의존 원천을 재확인한다.

### 4.2 cache 무효화와 읽기 비용

- 처음에는 **동일 평가의 중복 제거와 1회 의존 검사 비용 절감**부터 적용한다. 고정 시간 cache로 원천 변경 감지를 늦추거나 현재 metadata 검사를 배경 작업만으로 대체하지 않는다.
- 각 검사 pass 안에서 공통 상위 경로·anchor 해석과 중복 파일 내용 hash를 공유한다. lexical path/symlink chain identity와 실제 대상 identity는 모두 남긴다. 한 번 resolve한 경로를 영구 고정해 링크 교체를 놓치지 않는다.
- 누락·내용/크기/mtime/ctime/inode 변경·원자 교체·symlink/허용 mount 대상 교체·current CAS·부모/실행 코드/보조 취소 변경을 무효화 입력으로 명시한다. 읽기 전후 identity 대조와 변경 중 재검증 실패를 보존한다. 같은 mtime/크기의 변경도 기존 ctime·inode·hash 계약대로 검출한다.
- 같은 세대 동시 miss는 한 worker가 검증하고 다른 소비자가 동일 결과를 받도록 한다. 검증 중 current가 바뀌면 이전 결과를 새 세대 cache에 publish하지 않는다. 대기에는 측정 가능한 상한을 두고 미완료는 기존 source-invalid/wait 계약으로 반환한다. 불확실한 이전 세대를 정상값으로 반환하지 않는다.
- cache metadata 잠금은 짧게 유지하고 파일 I/O/hash·다른 worker 완료 대기 중에는 해제한다. WS/claim 상태 잠금을 보유한 채 cache miss를 기다리지 않는다. 무거운 준비 뒤 짧은 구성 잠금 안에서 세대를 다시 비교해 publish하며, lock 순서와 실패 시 해제를 동시성 회귀로 검증한다.
- 큰 source hash는 bounded streaming으로 계산하고 실제 working set/메모리를 측정한다. 현재 `maxsize=32`라는 이유만으로 LRU를 무제한 확대하지 않는다. canonical file identity+signature 단위 재사용, byte/entry 상한, eviction·single-flight를 함께 검증한다.

### 4.3 backend 구성과 영수증의 멱등성

같은 대상일·검증 세대·scope 실행 의미·보조 binding·실행 코드가 유지되면 구성과 동일 PID 소비 영수증 생성을 재사용한다. 필요한 현재 identity 확인은 유지하되 파일 전체 검증/직렬화를 중복하지 않는다. 전환 시에는 기존 configure의 scope별 state/claim 유지·무효화 규칙을 그대로 적용한다. 다른 scope의 변경으로 모든 FSM을 초기화하지 않으며, 취소된 보조 세대나 변경된 scope를 계속 소비하지 않는다.

v4/v5/v6 contract pin 목록을 먼저 대조한다. 호환 dispatch에 최적화를 둘 수 있는지 우선 검토한다. pinned module을 수정해야 하면 원 생성 코드 검증과 같은 정책 의미의 정식 successor/인계를 사용한다. 기존 bundle의 code hash를 새 파일 hash로 덮어쓰지 않는다. 부분 초기화 실패는 구성 완료로 cache하지 않고 동시 configure를 직렬화한다.

## 5. WS 잠금 안의 복사 개선

소유자는 [WS manager](../../src/engine/kiwoom_websocket.py), 실제 이벤트 소비자는 [SignalRadar](../../src/engine/signal_radar.py)와 그 통합 점수/Big-Bite/후속 `TRADE_SIGNAL_DETECTED` 소비자다. live getter는 Main 진입과 보유/청산에서도 사용하므로 전체 호출자를 조사한다.

**기존 회귀 `test_raw_observation_is_lossless_while_dispatch_keeps_full_latest_history`는 raw 무손실, 최신 상태, consumer가 중첩 자료를 수정해도 원본이 바뀌지 않는 격리를 요구한다.** `include_history=False`로 일괄 변경하거나 테스트를 약화해 해결하지 않는다.

1. 소비자별 필드·필요 history 길이·순서·타입·중첩 수정 여부와 price/source/health 출처를 표로 고정한다. 현재 값으로 계산한 점수·신호·quote·입력 bytes를 비교 fixture로 남긴다. dashboard의 120행 제한을 live 소비자에 전용하지 않는다.
2. 우선 전체 의미를 유지하는 불변 row/버전별 이력 공유 또는 필요한 필드의 명시 projection을 검토한다. projection은 전수 소비자 계약과 결과 동등성이 확인된 경로에만 적용한다. full-history getter는 기존 계약을 유지하고, 변경된 payload 형식은 versioned adapter와 모든 소비자를 같은 변경으로 인계한다.
3. 잠금 안에서는 같은 item/route/transport epoch/sequence의 작은 일관된 view를 확보한다. 큰 복사를 밖으로 옮기려면 먼저 참조된 중첩 row가 불변임을 보장하거나 버전 확인·bounded retry로 혼합 상태를 거부한다. mutable dict/deque의 얕은 참조만 떼어내는 구현은 금지한다. consumer 수정이 원본이나 다른 consumer에 전파되지 않아야 한다.
4. ingress→pending→snapshot의 lock 순서, raw 0B/0D 각 관측의 보존, 최신 상태 event의 기존 병합 범위와 at-most-once 소비를 보존한다. callback 예외·과부하·버전 충돌은 명시적으로 기록하고 silently drop/duplicate하지 않는다. 동일 이벤트를 구/신 consumer에 이중 발행하지 않는다.
5. SignalRadar의 동기 후속 호출과 market-regime 조회도 측정한다. 실제 병목으로 확인되면 기존 유효 원천 재사용 범위 안에서 개선하고 REST/provider 호출 수·간격·허가를 확대하지 않는다.

실제 Kiwoom 요청·응답 parser/FID·REG/REMOVE/recovery/auth 또는 관련 프로토콜 의미를 수정하는 경우 구현 전에 [Official Kiwoom Reference Gate](../kiwoom-api-data-contract.md#official-kiwoom-reference-gate)에 따라 당시 upstream SHA·경로·조회 시각을 기록한다. 이번 문서 작성은 프로토콜 변경을 실행하지 않는다.

## 6. 보고용 검증과 시각·계측 보완

오류 탐지의 `artifact_freshness → direct_handoff → validate_sources`를 별도 계측한다. 실제 hash working set·hit/miss·읽기량·CPU/GIL 영향과 대형 JSON 직렬화를 확인한 뒤 동일 불변 artifact의 검증 재사용을 우선 적용한다. history와 live 판정이 같은 무거운 validation을 경쟁한다면 기존 report worker/프로세스 경계로 격리하는 안을 검토한다. detector를 끄거나 source gap을 PASS로 바꾸지 않는다. 스케줄·wrapper·automation 변경이 필요하면 해당 운영 문서와 같은 checklist owner를 함께 갱신하며 별도 daemon을 임의 신설하지 않는다.

현재 refresh가 받은 `now_ts`는 정책 조회·구성 이후 claim 검사에도 전달된다. 원 신호 확인 시각은 보존하고 실제 claim 검증 시각을 무거운 처리·lock 대기 뒤에 잡아, 낡은 호출 시각이 미래 신호/만료 검사를 왜곡하지 않도록 한다. epoch 기반 신호 나이와 `monotonic/perf_counter` 기반 처리시간을 구분하고 clock rollback·원천 미래시각은 기존 실패 계약으로 처리한다. 기존 등록 영수증·AI 평가·응답 후 검증도 같은 의미로 맞춘다. 이 변경은 TTL 연장이 아니다.

최소 계측은 `loop work`, `policy validate/reuse/configure`, `WS lock wait/hold/snapshot`, `confirmed→claim`, `claim→machine`, `machine→provider response→pre-submit`다. provider 미호출은 0초 성공으로 집계하지 않고 해당 없음으로 남긴다. 미발생 신호, 실제 만료, 원천 결손은 확인 가능한 기존 원인만 기록한다. `no_current_operating_signal`을 모두 만료로 재분류하지 않는다.

계측은 bounded in-memory 집계와 기존 비동기 writer를 우선 사용한다. 매 tick 동기 파일 쓰기·새로운 full history 복사·high-cardinality 무제한 label을 추가하지 않는다. 새 report 필드는 `metric_role=runtime_performance_diagnostic`, `decision_authority=none`, `window_policy=exact_pid_release_policy_scope_and_load_window`, `sample_floor=none_counts_and_unobservable_explicit`, `primary_decision_metric=latency_distribution_and_contract_parity`, `source_quality_gate=exact_identity_monotonic_duration_and_sample_coverage`, `forbidden_uses=policy_promotion_order_authority_or_economic_claim`을 선언한다. 소비 schema가 이 역할을 모르면 함께 보완한다.

## 7. 구현 단계와 종료 기준

| 단계 | 선행 | 변경·검증 소유 | 종료 증거 |
| --- | --- | --- | --- |
| LP0 기준 고정 | 구현 착수 | 최신 release/PID/v6·보조 binding, 변경 파일/contract pin, 실제 consumer 및 의존 파일 census | 시점별 identity와 재현 fixture, 아직 안 측정한 새 PID를 구 표본과 구분 |
| LP1 중복 제거 | LP0 | policy loader→refresh→PID receipt→backend configure | 동일 평가 이중 load 제거, 동일 세대 configure/receipt 재사용, 모든 invalidation 반례 PASS |
| LP2 검증 비용 절감 | LP1 | dependency signature/hash single-flight·bounded cache | read/hash/resolve 횟수·메모리 감소, 손상/경쟁 시 실패 계약 동일 |
| LP3 WS 복사·잠금 | LP0, 통합은 LP1/LP2 이후 | WS snapshot→SignalRadar→live getters/후속 consumer | 필드/신호 동등성, raw 무손실·consumer 격리·혼합 route/epoch 0, lock·CPU 감소 |
| LP4 보고 부하·시각 | LP1~LP3 계측 | source diagnostics/검증 시각 및 오류 탐지 | 만료 시각 왜곡 제거, 보고 검증 재사용/격리 효과, 새 source gap 0 |
| LP5 통합 review gate | LP1~LP4 | 동시성·실제 launch cwd·v4/v5/v6·code pin 인계 | targeted pytest/compile/diff, frozen 입력 parity, cold/warm/부하 비교 |
| LP6 승인 범위 내 인계·관찰 | LP5 및 해당 실행 권한 | immutable release·정확 정책/보조·현재 PID·보유/주문 custody | 실제 소비 영수증, 구분된 전후 latency·만료·원천·중복 결과, rollback 검증 |

LP4의 대규모 프로세스 분리는 LP1~LP3 뒤에도 유의한 경합이 확인될 때만 구현한다. 측정된 비용이 사라지면 근거와 함께 추가 구조 변경을 생략한다. 어떤 단계에서도 과거 판정을 실제 주문으로 재생하지 않는다.

## 8. 회귀와 성능 비교

기존 [정책 cache/source 테스트](../../src/tests/test_mechanistic_entry_runtime_policy.py), [v5 테스트](../../src/tests/test_reversal_operating_policy.py), [v6 테스트](../../src/tests/test_reversal_extended_policy.py), [WS 테스트](../../src/tests/test_kiwoom_websocket.py), [원천·claim 테스트](../../src/tests/test_fixed_watch_submit_source_repair.py)를 확장한다. 새 Python 파일은 기존 역할 package/`src/tests`에 두며 `src/engine` root에 새 module을 만들지 않는다.

| 반례 | 필수 결과 |
| --- | --- |
| 같은 PID/정책/보조로 반복 평가 | 검증 경계별 1회 확인, configure/소비 영수증 중복 비용 제거; state/claim 소실 0 |
| current 또는 overlay가 읽는 중 교체·취소됨 | 옛 결과를 새 세대에 publish하지 않음; 기존 claim/응답 재검증 |
| 파일 누락/손상·동일 크기와 mtime·inode/ctime 변경·symlink 교체 | 기존 source 무효 감지; verified cache로 숨기지 않음 |
| 동시 miss/검증 예외/cancel/날짜 변경/PID 재사용 | single-flight 해제·bounded 대기, 실패 결과 오염/영구 교착 0 |
| v4 carry/v5/v6/장중 13개 등록·보조 교체 | 자기 계약과 정확 scope 유지; 기존 INITIAL 등록에 추가 gate 0 |
| 다른 scope 변경과 자기 scope 변경 | 영향 범위의 기존 FSM/claim 무효화만 수행 |
| 0B/0D burst·중첩 row 수정·producer/consumer 동시 실행 | raw 순서/개수, full-history 계약, consumer 격리 및 신호 동일 |
| plain/AL/NX, reconnect·transport epoch/sequence 교체 | route 혼합·예전 epoch 재사용·중복 event 0 |
| 복사 중 충돌/queue 포화/느린 callback | bounded 처리와 관측 가능한 실패; 무제한 retry/조용한 생략 0 |
| 4.999/5.000/5.001초 및 lock 대기·wall clock 역행 | 원 확인 epoch 기준 TTL, 갱신된 실제 검증 시각; 만료 신호 부활 0 |
| 보유/취소/SELL/late fill 경로 | snapshot 의미·custody·order callback 보호 동등 |
| detector 반복 실행과 source 변경 | source hash 재사용 가능, 변경된 원천/봉인 손상은 계속 검출 |

동일 frozen source prefix·확인점·정책/보조·consumer 순서에서 처리비용을 먼저 비교한다. clock 개선은 기존 낡은 `now_ts` 결과를 정답으로 삼지 않고 실제 경과시간/원 신호 epoch oracle로 검증한다. 성능 때문에 유효 신호 소비가 달라지는 경우 정의 변경과 구분해 명시한다. provider는 mock/보존 응답으로 검증하며 신규 실호출을 성능 시험에 쓰지 않는다.

최소 비교는 cold/warm, 낮은/높은 실제 관측 입력률, 짧은/긴 history, detector 동시/비동시의 재현 가능한 조합이다. 입력·이력·실행시간·표본 수·누락·CPU/RSS/읽기량을 함께 기록하고 성능 측정 자체의 overhead를 대조한다. 작은 변경마다 무관한 전체 suite나 장후 full replay를 반복하지 않는다.

## 9. 배포·롤백과 최종 확인

구현→리뷰→수정보완→재리뷰→targeted 검증이 닫힌 뒤 이미 승인된 해당 후속 실행 범위를 확인해 진행한다. LP0 때의 최신 정책/보조와 구현 중 다른 작업의 변경을 다시 대조하고, dirty workspace 전체를 배포하거나 과거 측정 release를 복구 정답으로 고정하지 않는다.

실제 `release/src` cwd에서 정책/source validator를 실행하고 code pin/bootstrapping/장중 handoff를 검증한다. 코드만 바뀌어도 계약 hash가 달라지는 범위는 기존 origin와 정식 successor 인계로 닫는다. 정책 목록·등록 scope·기계/보조 의미는 before/after 비교로 보존한다. 문서/checklist 변경으로 무효가 된 strict/PREOPEN 봉인은 기존 owner가 최종 바이트로 재검증·재봉인하며 과거 PASS를 현재 증거로 재사용하지 않는다. 이번 문서 작업에서 보고서 재생성이나 봉인 변경을 실행하지 않는다.

기존 handoff의 in-flight claim/provider 요청/outbox/order intent·보유/취소/SELL 소유권을 인계한다. 불확실 요청을 재전송하거나 종료 안 된 predecessor와 새 Main을 동시에 운용하지 않는다. 실제 PID/start ticks/cwd/release·선택 정책/보조 소비와 자연 처리시간을 별도 증거로 남긴다.

rollback 후보는 **그때의 활성 v6/보조/원천을 정상 읽는 검증된 이전 코드·정책 쌍**이다. 옛 v5 전용 release나 source-anchor 결함 release로 맹목 복귀하지 않는다. 원천/정책 오독, 중복 주문·event, custody/청산 지연, 혼합 snapshot·자료 변조는 기존 안전·rollback 절차로 대응한다. 단순 목표 미달은 추가 개선 상태이며 자동 매매 중단/재기동 규칙을 새로 만들지 않는다.

최종 보고는 코드 검증, 선택 release, 실제 PID/정책 소비, 자연 지연/만료/원천 품질, 실제 주문·비용 후 성과를 구분한다. 미발생 신호나 비교 불가능한 새 정책 window는 `unobservable/not_comparable`로 남기며 성공으로 채우지 않는다.

## 10. 계획 자체의 리뷰

작성 중 다음 사항을 보완했다: 측정 당시 v5/PID 24520과 이후 v6/PID 34821을 구분했고, WS full-history·중첩 수정 격리 회귀를 명시했으며, cache 재사용에 현재 원천 변경 감지를 남겼다. 5초 재기산 금지와 실제 검증 시각 갱신을 함께 적고, v6와 호환되는 rollback·code pin 인계를 요구했다. 재리뷰에서는 낡은 호출 시각을 정답으로 고정하지 않도록 parity 기준을 실제 시각 oracle로 정리하고, single-flight와 WS/claim 잠금 사이의 교착 방지 조건을 추가했다. 문서 검증 완료와 구현·자연 성능 개선 완료는 별도다.

문서 검증: 로컬 링크/anchor 19개, 현재 checklist owner 1개, print-only parser 21개 작업 및 diff/공백 검사를 확인했다. 이번 범위는 계획과 기존 checklist owner의 인계 문구이며 runtime 코드 테스트·provider 호출·정책 발행·배포·재기동은 수행하지 않았다. LP0~LP6 구현 및 자연 성능 목표 달성은 후속 실행 증거로 확인한다.

## 11. 구현 실행 인계

2026-10-08 후속 사용자가 처리지연 개선 구현, 반복 코드리뷰·보완, 성능 검증 및 배포·재기동을 승인했다. 앞 절의 계획 작성 당시 실행 경계는 이 후속 승인 범위에서 갱신한다. [구현·성능 검토](../audits/main-evaluation-loop-latency-implementation-review-2026-10-08.md)가 실행 증거를 소유한다. 정책 pin/13개 정의 및 보조 프롬프트를 변경하지 않고 기존 호환 호출 경계에서 개선하며, 별도 작업 중인 미완료 보조 연구 파일은 이번 배포에서 제외한다.
