# Main 평가루프 처리 지연 개선계획 — 2026-10-08

## 1. 목표와 실행 경계

신호 확인부터 Main 평가까지의 지연을 줄인다. 우선 정책 조회·검증·구성의 중복을 제거하고, WS 공용 잠금 안에서 수행하는 전체 데이터 복사를 개선한다. 오류 탐지의 반복 원천 읽기는 후속 순위로 다룬다. **5초 claim 유효기간과 매매 조건을 유지한 상태에서 처리 경로를 개선**한다.

이번 요청은 **계획 수립**이다. 이 문서 작성으로 구현·패키지 설치·provider 호출·정책 발행·배포·재기동을 실행하지 않는다. 다른 작업에서 이미 승인된 후속 조치는 해당 범위와 영수증을 그대로 따르며, 이 계획이 추가 승인이나 경제적 적격성 입증을 요구하지 않는다.

실행 소유자는 [오늘 체크리스트](../checklists/2026-10-08-stage2-todo-checklist.md)의 기존 `DirectFamilySourceRepairMainMechanisticEntry`다. `LP0`~`LP12`는 그 항목 내부 단계이며 별도 OPEN owner를 만들지 않는다. **§2~§10은 최초 LP0~LP6 설계·검토, §11은 구현 인계, §12~§17은 자연 목표 미달에 대한 후속 계획·재리뷰**다. 관련 계약은 [독립 탐지·기여도 계획](main-operating-policy-independent-detection-and-contribution-evaluation-implementation-plan-2026-10-07.md), [원장 증분 저장 계획](main-ai-comparison-ledger-dedup-and-incremental-storage-plan-2026-10-07.md), [시간외 등록·상태 보완 계획](main-pre-after-pattern-registration-and-status-consistency-remediation-plan-2026-10-08.md)이다.

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

최초 §2 측정 당시 refresh는 `load_effective → record_pid_consumption(다시 load_effective) → configure_bundle → claim_snapshot`을 수행했다. 캐시 hit도 모든 의존 경로의 `stat/resolve`와 bundle 깊은 복사를 거치며, configure는 같은 세대에서도 family/부모 검증과 복사를 수행했다. 아래는 이 병목의 개선 설계이며, §11의 구현 이후에도 같은 결함이 남았다는 진술이 아니다.

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

최초 측정 코드에서는 refresh가 받은 `now_ts`가 정책 조회·구성 이후 claim 검사에도 전달됐다. 원 신호 확인 시각은 보존하고 실제 claim 검증 시각을 무거운 처리·lock 대기 뒤에 잡아, 낡은 호출 시각이 미래 신호/만료 검사를 왜곡하지 않도록 한다. epoch 기반 신호 나이와 `monotonic/perf_counter` 기반 처리시간을 구분하고 clock rollback·원천 미래시각은 기존 실패 계약으로 처리한다. 기존 등록 영수증·AI 평가·응답 후 검증도 같은 의미로 맞춘다. 이 변경은 TTL 연장이 아니며, 후속 검토는 §11의 구현 결과를 기준으로 한다.

최소 계측은 `loop work`, `policy validate/reuse/configure`, `WS lock wait/hold/snapshot`, `confirmed→claim`, `claim→machine`, `machine→provider response→pre-submit`다. provider 미호출은 0초 성공으로 집계하지 않고 해당 없음으로 남긴다. 미발생 신호, 실제 만료, 원천 결손은 확인 가능한 기존 원인만 기록한다. `no_current_operating_signal`을 모두 만료로 재분류하지 않는다.

계측은 bounded in-memory 집계와 기존 주기적 metrics 출력을 우선 사용한다. 매 tick 동기 파일 쓰기·새로운 full history 복사·high-cardinality 무제한 label을 추가하지 않는다. 판정 trace의 기존 동기 저장은 계측과 별개이며 §14.3의 영수증 계약을 따른다. 새 report 필드는 `metric_role=runtime_performance_diagnostic`, `decision_authority=none`, `window_policy=exact_pid_release_policy_scope_and_load_window`, `sample_floor=none_counts_and_unobservable_explicit`, `primary_decision_metric=latency_distribution_and_contract_parity`, `source_quality_gate=exact_identity_monotonic_duration_and_sample_coverage`, `forbidden_uses=policy_promotion_order_authority_or_economic_claim`을 선언한다. 소비 schema가 이 역할을 모르면 함께 보완한다.

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

최초 문서 검증: 로컬 링크/anchor 19개, 현재 checklist owner 1개, print-only parser 21개 작업 및 diff/공백 검사를 확인했다. 당시 범위는 계획과 기존 checklist owner의 인계 문구였다. 이후 구현·배포는 §11, 자연 목표 미달과 후속 재리뷰는 §12~§17에 기록한다. 이 최초 검증 수를 후속 문서의 재검증 결과로 전용하지 않는다.

## 11. 구현 실행 인계

2026-10-08 후속 사용자가 처리지연 개선 구현, 반복 코드리뷰·보완, 성능 검증 및 배포·재기동을 승인했다. 앞 절의 계획 작성 당시 실행 경계는 이 후속 승인 범위에서 갱신한다. [구현·성능 검토](../audits/main-evaluation-loop-latency-implementation-review-2026-10-08.md)가 실행 증거를 소유한다. 정책 pin/13개 정의 및 보조 프롬프트를 변경하지 않고 기존 호환 호출 경계에서 개선하며, 별도 작업 중인 미완료 보조 연구 파일은 이번 배포에서 제외한다.

## 12. 11:21 KST 자연 실행 재기준

LP0~LP6의 구현·배포 인계 뒤에도 LP6의 자연 수용 목표는 닫히지 않았다. [11:21 PID 기계판정 점검](../../tmp/machine-status-check-20261008-112113/status.json)은 `main-loop-latency-20261008-v5`의 PID `76094`/start ticks `674250`, commit `aed0ffcaf0bbce32fe84fab15a77ea36953f7202`가 v6 bundle `40fb3ec7d5f44e2e34044f2a14e2d0d06dd6ea264f69b5f1481be899f2a4a689`와 기계·보조 각 128 scope를 소비한 상태를 고정한다. 이는 등록 scope 전부에서 자연 신호가 발생했다는 뜻이 아니다. 이 절은 10:40:58~11:21:00 KST의 기록이며 이후 PID나 release의 현재 상태로 전용하지 않는다.

| 관측 | 결과 | 판정 |
| --- | --- | --- |
| 고정감시 평가 | 고유 80회, PID 직접 결속 74회 중 정상 69회·원천 사전 차단 5회 | 나머지 계약 오류 6회는 시간창만 대응하며 PID 직접 영수증 부재 |
| 정상 평가 결과 | `BLOCK` 65회, `ENTER_NOW` 4회 | `no_current_operating_signal`만 발생한 구간이 아님 |
| `ENTER_NOW` 후속 | 알테오젠 1회, 주성엔지니어링 3회가 모두 최종 `WAIT` | 제출 0회; 실제 주문 실패·미체결로 분류하지 않음 |
| AI 경로 | 2회 provider 호출(PASS 1·CAUTION 1), 2회 미호출 로컬 만료 차단 | 호출 2회에도 만료 오류가 기록됐으나 CAUTION은 유효해도 현재 합성 규칙상 WAIT |
| 신호 나이 | 기계 capture 시 약 2.03/3.47/2.22/5.37초, 최종 trace 시 5.51/6.48/6.82/6.91초 | capture/trace 저장 시각의 나이이며 실제 validator·물리 전송 시각과 같지 않음 |
| 사전 차단 | source/required-feature 차단 5회 | 두산·HPSP·알테오젠의 원천 품질 문제는 지연과 별도 |
| claim 계약 | `reversal_signal_path_changed` 5회, `reversal_signal_expired_or_changed` 1회 | 6회 모두 앞의 계약 오류 분모; 앞서 집계한 ENTER_NOW 4회의 후속 오류와 중복 합산 금지 |
| warm Main loop | 1,179회, p95 4.194초, p99 7.967초, max 14.244초, 5초 초과 38회 | episode OFF 전후 혼합 누적 창; 기존 p95≤2초/p99<5초 목표 미달 |
| 최근 약 9분 | 11:11:29.501~11:20:36.095 완료 loop 305회 중 5초 초과 9회 | episode OFF 이후에도 긴 꼬리 관측; 이 창의 p95/p99는 별도 미산출 |

[4개 attempt 후속 요약](../../tmp/machine-status-check-20261008-current/enter-attempt-pipeline-summary.json)의 순서는 알테오젠 `aims-55cce84330bea3d6b183`, 주성 `aims-09aa22661b0740562c60`/`aims-345797ac4cf160508158`/`aims-8629118d9ec8a8e1cae1`다. 이 요약은 읽은 byte bound를 기록한 조사 자료이며 원본 전체의 hash 봉인 증거는 아니다. 네 건 모두 만료 관련 차단이 있으나, 지연 제거만으로 네 건이 BUY/주문이 됐을 것이라고 추론하지 않는다. 특히 CAUTION과 이후 source/submit guard는 독립 조건이다.

보고용 `submission_bottleneck_monitor`는 fixed-watch와 scanner promotion을 분리하며, 후자의 집계에서 fixed-watch를 의도적으로 제외한다. 따라서 `unobservable/no_identified_machine_evaluation`과 위 고정감시 판정은 양립할 수 있다. LP7은 먼저 같은 scope/PID/window/coverage를 대사하고 **실제 소비 누락이 입증된 경로만** 보완한다. fixed-watch를 promotion 분모에 합치거나 기존 unobservable을 임의 PASS로 바꾸지 않는다.

[episode OFF 실행 기록](../audits/episode-permanent-off-lock-release-2026-10-08.md)에 따르면 11:02 이후 구 episode 프로세스 종료·영구 OFF가 적용됐다. 누적 loop 통계를 OFF 이후 성능으로 표시하지 않으며, 직전·직후 짧은 창은 입력 부하가 달라 인과적 절감률을 입증하지 않는다. 잔여분 수동관리·퇴역 조건 해제 지시를 보존하고 episode 자동 청산/복구를 재개하지 않는다. 비용 후 손익·체결 성과는 이 구간에서 확인하지 않았다.

결정은 다음과 같다. LP0~LP6의 정책 검증·WS snapshot·원장 조회 개선은 유지한다. 후속은 TTL 확대가 아니라 **원 신호 epoch부터 응답 후 재검증까지의 critical path**를 줄이는 LP7~LP12로 진행한다. REST/WS 절감 계획의 RW 단계는 실제 critical-path 귀속이 확인된 호출에만 연결한다.

## 13. 후속 설계 원칙

1. claim에 결속된 **신규 진입 평가**의 5초 기준은 native validator가 사용하는 원 `claim.snapshot[0].epoch`다. 이 경로의 deadline은 `min(원 신호 epoch + 5초, 이미 존재하는 더 이른 caller deadline)`으로 제한한다. worker 제출·queue 진입·응답 수신으로 재기산하지 않으며, 보유/청산·주문·분할수량의 다른 deadline을 일괄 5초로 바꾸지 않는다.
2. 기계판정은 Main의 단일 진입 owner를 유지한다. 확정 신호를 일반 WATCHING refresh·discovery probe보다 먼저 준비할 수 있으나 별도 주문 owner나 병렬 broker 제출 경로를 만들지 않는다.
3. AI는 보조 risk screen이다. 기계 `ENTER_NOW`가 AI 지연이나 오류만으로 BUY 권한을 얻지 않으며, 응답 후 활성 정책·보조 binding·exact claim·원천·submit guard를 다시 검증한다.
4. provider timeout은 **현재 상한과 실제 남은 budget 중 작은 값**으로 줄인다. 남은 시간이 기존 timeout 전체보다 짧다는 이유만으로 호출을 막지 않는다. 실행 가능한 budget이 없으면 기존 bounded recheck로 종료한다. quota·retry 권한을 늘리거나 만료 응답을 다음 claim에 재사용하지 않는다.
5. source stale/required-feature 결손, claim path 변화, 처리시간 만료를 별도 상태로 기록한다. `path_changed`나 `SOURCE_INVALID`를 지연으로 합치거나 0 EV·broker 거부로 해석하지 않는다.
6. 현재 v6 정의·추가 13개·보조 binding·manual veto·broker/account/order/수량/자본/cooldown/custody 및 hard safety를 유지한다. 성능 수용을 초기 정책의 경제적 적격성 gate로 사용하지 않는다.

## 14. LP7~LP12 실행 계획

| 단계 | 선행 | 변경·검증 범위 | 종료 증거 |
| --- | --- | --- | --- |
| LP7 attempt 단위 계측 | 실제 release/PID 재고정 | confirmed/claim 이전 누락부터 queue·준비·capture·provider reserve/물리 전송·응답 검증·submit guard까지 연결 | monotonic duration·분모·누락 명시, fixed-watch/scanner의 정확 scope 대사 |
| LP8 확정 신호 우선 처리 | LP7의 queue 귀속 | coordinator 활성 조건·fixed-watch admission·pending 작업 순서·completion wakeup 보완 | 기존 동시성에서 bounded 대기/공정성, 동일 기회의 중복 요청·주문 0 |
| LP9 critical path 외 작업 분리 | LP7의 비용 귀속 | 유효 준비 view 재사용, capacity·capture·report projection의 소비 계약별 비용 절감 | 원 입력/필수 영수증 보존, 관측 coverage 유지, 불필요한 반복 본문 감소 |
| LP10 deadline-aware provider | LP7; LP8/LP9 전체 완료는 불필요 | sync·async·허용 재확인 경로에서 원 deadline 전파, queue/lock/전송/응답 검증의 공통 budget | 실행 가능한 짧은 요청 허용, budget reset·만료 승격·중복 전송 0 |
| LP11 claim path 진단 | LP7; 관련 결함 수리는 독립 | native 검사에서 실패한 실제 predicate와 source receipt를 기록 | 증거 있는 오류만 귀속, 보존 자료로 복원 불가능한 과거 원인은 unknown 유지 |
| LP12 통합 리뷰·배포·자연 수용 | 해당 변경의 LP7·회귀; 비대상 단계는 귀속 근거로 제외 | 구현→리뷰→수정보완→재리뷰→targeted 검증, immutable release와 정확 PID/v6·보조 인계 | 아래 성능·동등성 표, rollback 영수증, 자연 신호/주문/경제성의 별도 상태 |

### 14.1 LP7: 관측 분모와 실제 시각

[runtime performance](../../src/engine/monitoring/runtime_performance.py)의 signal ID 계측은 128-entry bounded 메모리이며 attempt 전체 구간을 결속하지 못한다. release/PID/start ticks·대상일·scope/route·native opportunity/claim/source identity와 `evaluation_attempt_id`/request ID를 연결한다. v6의 여러 matched branch는 같은 canonical opportunity의 참조로 보존하며 각각 별도 요청으로 세지 않는다.

- wall/source clock: 원 signal·receive/event epoch, deadline, 실제 claim 검증 시각. 단계별 소요시간은 같은 프로세스의 monotonic clock으로 기록하며 다른 PID의 monotonic 값을 빼지 않는다.
- 구간: confirmed→claim, queue/worker, source·capacity·policy 준비, machine/capture append, provider 예약·key 대기·물리 전송·응답, 응답 후 검증, Main commit, pre-submit guard 시작/완료, 실제 submit. 현재 `mark_signal(..., 'submit')` 호출 위치는 guard 이전이므로 broker 제출 증거로 사용하지 않는다.
- 분모: native confirmed/ready에서 관측한 기회를 claim 이전부터 센다. claimed/captured만 분모로 삼지 않는다. deferred·queue 만료·source invalid·join 실패·eviction·provider 미호출/불확실을 남기고, `no_current_operating_signal`을 모두 만료로 바꾸지 않는다.

현재 loop의 `over_five_seconds`는 retained deque(최대 4,096개)의 계수다. rolling snapshot 차이를 일반적인 구간 초과 수로 사용하거나 p95/p99를 서로 빼지 않는다. §12의 305/9 차분은 두 시점 모두 reset/eviction 없이 전체 누적 표본이 retained된 구간에 한정한다. 후속은 기존 주기 출력에 구간 histogram/counter와 reset identity를 더해 모든 완료 loop의 분포를 만들고 정상/결손 부하는 별도 층으로 보인다. 매 tick 디스크 쓰기나 무제한 labels를 추가하지 않는다.

monitor는 scanner promotion과 fixed-watch의 각 window·분모·coverage를 표시한다. 동일 scope의 native trace와 식별자가 실제로 누락된 경우만 reader/schema를 수정한다. PID 영수증 부재·부분 window를 성공으로 보충하지 않으며 계측 결손만으로 새 주문 차단 조건을 만들지 않는다.

### 14.2 LP8: 고정감시 admission과 대기 순서

기준 release의 `_resolve_scanner_async_entry_ai`는 coordinator와 `ScannerGeneration`이 모두 있어야 활성화된다. [기존 coordinator](../../src/engine/scalping/scanner_async_eval.py)는 원천 준비 worker 1개와 bounded retained entry를 사용하며 pending priority를 자동 보장하지 않는다. fixed-watch를 scanner promotion으로 위장하지 않고, 실제 고정감시 owner/source identity를 받는 admission과 context를 기존 경로에 보완한다. sync fallback 원인·실제 활성 여부를 먼저 기록한다.

- 아직 실행하지 않은 준비 작업에는 확정 claim의 대기 우선순위를 주되 bounded aging/차례 보장으로 일반 관측이 굶지 않게 한다. 실행 중인 blocking I/O를 선점·재실행한다고 가정하지 않는다. 기존 worker/queue/provider 동시성과 quota를 유지하고, holding/SELL/cancel/late-fill은 기존 우선권을 보존한다.
- sync의 pending claim과 `source_registration_receipt`, frozen 입력·scope 실행 hash·원 deadline을 immutable context로 함께 인계한다. 현재 async caller가 원 claim을 전달하지 않는 차이를 먼저 닫는다. worker가 새 claim을 획득하거나 scanner 세대를 합성하지 않게 한다.
- worker 결과와 callback은 불변 evidence를 반환하고 Main이 현재 stock/claim/quote/manual guard를 확인해 한 번 commit한다. 현재 `entry_economics_observer`처럼 live `stock`을 캡처하는 closure도 점검하여 worker가 stock·주문 상태를 직접 수정하지 않게 한다. live provider 예약은 기존 outbox owner만 수행한다.
- 원천/AI 완료 시 기존 Main 대기를 깨우는 bounded notification을 검토해 다음 polling까지의 지연을 줄인다. busy polling·새 daemon을 만들지 않으며 GIL/CPU 경합은 worker 이동만으로 해결됐다고 보지 않는다.
- 정상 새 tick/sequence라는 이유만으로 유효 claim을 취소하지 않는다. 자기 scope 실행 의미·native/source epoch·claim 생존 여부는 현재 native validator가 결정한다. 다른 scope 변경과 응답 후 허용된 branch 부분집합도 §14.4대로 보존한다.

취소·caller timeout 뒤 물리 요청이 계속 실행되면 완료까지 원 in-flight 슬롯과 예약을 유지한다. 늦은 결과는 원 요청의 증거로 남기되 주문 권한을 얻지 않으며, 다른 token/재기동을 이용한 중복 전송도 막는다.

### 14.3 LP9: 원천·capacity·저장 I/O 분리

확정 신호 전에 준비할 수 있는 시장 view와 계좌 capacity는 기존 trigger·간격·quota·freshness/key 범위에서 재사용한다. 새 주기 호출이나 미리 알 수 없는 가격의 임의 prefetch를 추가하지 않는다. exact price·route·account generation이 달라지면 재사용하지 않으며 일반 BLOCK/RECHECK의 필요한 관측도 보존한다. 최종 pre-submit quote와 capacity 검증은 제거하지 않는다.

기계판정 전 `ka10003`/candle/account preparation은 [REST/WS 계획](main-rest-api-ws-substitution-and-load-reduction-plan-2026-10-08.md)의 RW0 대상 물리 호출과 LP7 timing을 연결한다. WS 전환은 RW0+RW5a→RW2, Main writer/이력 계약→RW3, 계좌 계약→RW4를 따른다. 이미 유효한 view의 동일 평가 재사용·deadline 전달을 전체 46종 API 전환 완료까지 묶어 두지 않는다. 결손이면 기존 bounded fallback/source-invalid를 유지하며 나중에 온 봉/응답으로 과거 입력을 채우지 않는다. 프로토콜 수정이 필요할 때는 §5의 공식 gate를 적용한다.

현재 [판정 trace](../../src/engine/scalping/ai_decision_trace.py)의 machine capture는 동기 append다. `_append_jsonl`은 신규 파일 생성 시 fsync하며 매 행 fsync를 보장하지 않으므로 append 성공과 전원 장애 내구성을 구분한다. 작은 hash envelope를 먼저 성공 처리하고 원 입력 본문을 나중에 저장하는 설계는 채택하지 않는다. provider 이전의 필수 입력·source/prompt/schema binding 및 [live outbox](../../src/engine/scalping/reversal_operating_outbox.py) 예약 순서를 보존한다. 본문 참조 방식이 필요하면 기존 저장 owner에서 원 bytes가 완성·검증된 뒤 참조를 publish하고, 내구성 보장은 해당 owner 계약과 장애 시험으로 확인한다.

필수 입력/예약과 report-only projection을 소비자별로 먼저 구분한다. 새 진단 저장 실패는 report gap이며 신규 전역 매매 gate가 아니다. 기존 필수 예약 실패는 현행 차단 계약대로 처리한다. 안전한 첫 변경은 필수 동기 저장을 유지한 채 반복 직렬화·비필수 projection 비용만 줄이는 것이다.

같은 attempt의 `ai_confirmed_terminal_no_budget` 반복은 [pipeline logger](../../src/utils/pipeline_event_logger.py)와 [summary](../../src/engine/pipeline_event_summary.py), monitor의 현재 compaction/heartbeat 계약부터 조사한다. 재시작을 포함한 event identity와 상태 전이 순서를 보존해 같은 전이의 큰 본문 중복만 줄인다. `A→B→A`는 새 전이이고 원천·blocker 변경, 실제 예약/주문/체결 event는 생략하지 않는다. 반복 관측 수·마지막 관측 시각이 필요한 consumer에는 작은 count/heartbeat를 인계한다. offline 비교 원장의 key를 live 요청 예약이나 pipeline event의 대체 소유자로 쓰지 않으며, 과거 raw와 generation hash를 소급 변경하지 않는다.

### 14.4 LP10~LP11: provider와 claim 재검증

기준 release의 sync `watching_analyze_target`와 두 재확인 caller에는 `entry_input_deadline_epoch` 전달이 빠져 있고, async에는 `submitted_epoch + 5초`가 쓰인다. `_call_openai_safe`에는 보조 provider의 설정 timeout이 전달된다. Main caller→AI wrapper→key/queue 대기→transport의 실제 경로를 한꺼번에 연결해 원 신호 deadline을 잃거나 재설정하지 않게 한다. 진입 claim이 없는 다른 AI 업무까지 일괄 적용하지 않는다.

요청 budget은 `min(기존 provider timeout 상한, min(caller 잔여시간, 원 claim 잔여시간) - 로컬 후처리 reserve)`다. **기존 상한 5초·잔여 3초이고 후처리 reserve를 확보할 수 있다면, 3초보다 작은 유효 budget으로 호출할 수 있어야 한다.** reserve는 LP7에서 측정한 필수 후처리 비용을 근거로 상한과 적용 근거를 기록한다. 추정 provider p95 전체가 들어맞아야 호출한다는 새 gate를 만들지 않는다. age≤2초 목표 역시 운영 cutoff가 아니다.

admission·key/lock 대기·capture·예약·connect/read·이미 허용된 retry/fallback은 하나의 monotonic 잔여 budget을 소비한다. irreversible 예약 전에 검사하고 대기/예약 뒤 물리 전송 직전 다시 검사한다. 매 retry에 timeout을 새로 주거나 최소 timeout clamp(현재 50ms)가 잔여시간을 초과하게 하지 않는다. 유효한 transport budget이 없으면 기존 bounded recheck로 종료한다. 예약 이후 만료되더라도 `transmission_uncertain`을 미호출로 임의 복구하지 않으며, native 증거 없이 재전송하지 않는다.

응답을 받으면 원 요청의 응답/outbox 증거를 보존하면서 schema/semantic·현재 claim 검증을 우선 진행한다. 비필수 projection은 뒤로 옮기되 필수 응답 보존을 뒤집지 않는다. timeout 반환을 transport 취소 완료로 해석하지 않는다. wall clock 역행·미래 source epoch는 현재 실패 계약을 유지하며, monotonic 측정으로 source freshness 검사를 대체하지 않는다.

현재 [합성 규칙](../../src/engine/scalping/continuous_reversal_policy.py)은 유효 `ENTER_NOW + PASS`만 BUY 후보이며 CAUTION은 WAIT, 유효 VETO는 DROP이다. PASS에도 TTL·path·source·policy/binding·submit guard가 필요하다. [v6 active claim 검사](../../src/engine/scalping/continuous_reversal_policy_v6.py)는 응답 후 원 matched refs 중 아직 유효한 부분집합을 허용한다. 이를 전체 집합 동일 강제로 바꾸거나 새 branch를 추가하지 않는다. 호출 전 입력 결속 검사와 응답 후 허용된 생존 검사를 각각 유지한다.

`reversal_signal_path_changed`는 실제 실패한 state/legacy/native epoch/ready membership/generation/snapshot 조건을 기존 source receipt에 더해 기록한다. lock 대기 뒤의 검사 시각과 PID/start ticks도 결속하되 민감한 원문이나 무제한 state dump를 추가하지 않는다. 과거 5건에 당시 내부 상태가 없으면 정확 원인은 unknown으로 남긴다. 합성 fixture의 재현을 실제 과거 원인 입증으로 표시하지 않는다. 유효 claim의 잘못된 제거가 재현된 경우만 native 소유 경로를 수정하고 만료 claim 복원이나 code pin의 비공식 교체를 하지 않는다.

## 15. 후속 수용 기준

| 대상 | 수용 기준 | 실패·미관측 처리 |
| --- | --- | --- |
| 계측 완결성 | confirmed/ready 관측 기회마다 attempt timeline 또는 누락 상태; 실제 단계 순서 일치 | PID/clock/join/eviction 결손은 unknown, 0초 보충 금지 |
| warm Main loop | 모든 완료 warm loop에서 p95 ≤2초, p99 <5초; 정상 원천 부분군도 별도 | 표본 수/max/5초 초과 수·입력률/부하/episode OFF 경계를 공개 |
| 신호→기계 capture | 초기 제안 p95 ≤1.5초, p99 ≤2초 | 미평가/만료/source gap/path change를 전체 관측 분모에 함께 공개 |
| provider dispatch | 실행 적격 호출의 age≤2초를 목표로 준비 대기 감소 | 2초는 새 cutoff 아님; 호출 0/전부 defer를 목표 달성으로 계산하지 않음 |
| 응답 후 claim | 비교 가능한 fresh-source ENTER_NOW의 내부 처리 유발 만료 0을 목표로 측정 | validator 시각/귀속 없으면 원인 unknown; 자연 표본 0은 unobservable |
| WS 잠금 | 기존 p99≤10ms 목표 | wait/hold/snapshot을 따로 보고 |
| terminal 저장 | 동일 전이의 불필요한 본문 증폭 제거, count/heartbeat/새 전이와 live 원장 보존 | 메모리 dedup만으로 재시작 보장 금지; A→B→A는 새 전이 |
| 정상 제출 경로 | mock 정상 경로에서 unexpired PASS와 모든 기존 guard 통과 시 정확히 1개 submit intent; 차단 시 실제 첫 blocker | intent·물리 submit·broker 접수·체결은 별도; 실제 주문 강제 발생 금지 |
| 안전·동등성 | v6/13개/보조·source/hash·manual/order/custody guard parity, 중복 주문 0 | 하나라도 불일치면 배포 수용 실패 |

코드 종료는 결정론적 회귀·안전/입력 동등성·계측 검증으로, 자연 성능 수용은 승인된 인계 뒤 별도로 닫는다. 자연 목표 달성을 배포 전 선행 조건으로 만들어 순환시키지 않는다. 모든 기회를 defer/누락시켜 내부 만료가 0이 된 결과는 지연 개선 PASS가 아니다. 전후 관측 기회·평가·호출·defer·만료의 coverage와 부하 차이를 함께 공개한다. 이는 경제적 적격성이나 기존 제출 수 보존 gate가 아니다. 실제 체결·비용 후 순이익 및 자연 표본 부재는 별도 상태이며 원천 차단 5회도 exact source owner에서 다룬다.

## 16. 배포 순서와 롤백

1. LP7 계측만 먼저 리뷰하고 보존 trace replay로 overhead와 join 정확성을 검증한다.
2. LP10의 deadline 전달과 LP11 진단은 LP7의 관련 계측 뒤 독립 진행할 수 있다. LP8/LP9는 확인한 비용만 작은 변경으로 줄인다. 아래 반례와 frozen 입력 parity를 해당 변경에 맞춰 회귀한다.
3. review gate가 닫힌 뒤 승인 범위가 있는 경우에만 immutable release를 만들고 실제 PID/v6·보조 소비를 확인한다. 기준 release와 treatment release의 자연 window·입력률·신호 수를 각각 기록한다.
4. rollback은 현재 v6/보조를 정상 읽는 검증된 이전 코드 release다. TTL 확대, 이전 v5 정책 복원, episode/widget 재기동, provider/broker guard 완화를 rollback으로 사용하지 않는다.

| 추가 회귀 | 종료 조건 |
| --- | --- |
| 기존 timeout 5초·잔여 3초, key/lock 대기, 50ms 미만 잔여, retry | 짧은 유효 요청 허용; 전체 elapsed budget 상한/물리 전송 전 재검사; timeout reset 0 |
| sync/async/허용 recheck와 source 4.999/5.000/5.001초, clock 역행 | 동일 원 claim·deadline·현재 시각 native 판정 보존; 만료 부활 0 |
| fixed-watch에 ScannerGeneration 부재, queue 포화·장시간 일반 I/O | 가짜 promotion 없이 admission, bounded 대기/공정성, 기존 callback 보호 |
| 준비/AI 완료·cancel·late response·PID 재사용 | Main wakeup/단일 commit, worker의 live stock mutation·중복 요청/주문 0 |
| 원 matched branch 일부 소멸/추가, 다른 scope 변경 | 호출 전 binding과 응답 후 native 부분집합 규칙 보존; 새 branch 승격 0 |
| 필수 본문 저장/예약/전송/응답 저장 각 경계의 crash | 없는 본문의 완료 참조 0; 원 응답/uncertain 보존; 새 token으로 중복 전송 0 |
| report-only append 실패, 반복 terminal A→B→A·재시작 | 기존 필수 custody와 진단 실패 구분; 새 전이/count/last-seen 보존 |
| retained 4,096개 초과/reset, fixed-watch만 있는 monitor 창 | rolling 차분/분위수 오산 0; scope별 unobservable/부분 coverage의 정직한 표시 |
| 모든 attempt defer, CAUTION·VETO·유효 PASS 정상 경로 | 거절만으로 성능 PASS 금지; 원 WAIT/DROP/guard 및 단일 정상 submit intent 검증 |

## 17. 후속 계획 재리뷰 기록

이번 리뷰는 §12의 immutable release 코드와 보존 조사 자료를 기준으로 수행했다. dirty workspace의 별도 퇴역 구현을 해당 PID의 코드로 간주하지 않았다. timeout 전체가 들어맞아야 호출한다는 차단, 고정감시의 scanner admission/claim 누락, envelope 선행 저장, offline/live 원장 혼용, rolling 계수 차분과 monitor scope 오독을 수정했다. CAUTION과 만료의 인과 한계, episode OFF 전후 창, 비선점 queue·callback 소유권, native branch 부분집합, 전부 defer로 지표를 개선하는 오류를 수용 기준에 반영했다.

이번 변경은 이 계획·연결된 REST/WS 계획의 인계 경계와 현재 checklist owner에 한정한다. 로컬 링크/anchor 67개(이 문서 32·REST/WS 16·checklist 19), OPEN owner 1개, print-only parser 21개 작업과 변경 문서의 공백 검사를 통과했다. 전체 workspace 검사는 범위 밖 `test_entry_adverse_flow.py`·`test_policy_research_economics.py`의 EOF 빈 줄 경고를 냈으며 해당 파일은 수정하지 않았다. 코드 구현/거래 테스트·provider/broker 호출·정책 발행·배포·재기동·report 재생성은 실행하지 않았다. 자연 성능 목표 달성과 과거 `path_changed` 5건의 정확 내부 원인은 후속 증거가 필요하다.


## 2026-10-08 승인 구현·리뷰 인계

사용자가 구현·반복 리뷰/보완·배포·재기동을 승인하여 위 계획의 생존 Main 경로를 구현했다. [구현/검증 기록](../audits/main-rest-ws-latency-implementation-review-2026-10-08.md)에 단계별 실제 소비·제외 근거·공식 원천과 성능을 연결한다. 원 5초/native claim·현재 v6/보조·Main-only/cap/quota/최종 주문 보호는 유지한다. WS 분봉은 430봉·전체 prefix가 부족하면 REST를 유지하며, terminal 원문 compaction은 exact attempt 소비 계약 때문에 제외했다. 신규 AI 비교 원장·provider/broker 검증 호출은 생성하지 않았다. 코드 종료와 배포/PID/자연 성능·경제성을 각각 확인한다.

## 2026-10-08 15시 관측 후 상세 수리 인계

[PID 206123 관측](../audits/main-pid-206123-post-warmup-latency-rest-ws-monitoring-2026-10-08.md)에서 워밍업 제외 849회 중 11회가 5초를 넘었고, 실제 fixed-watch Main caller의 coordinator 전달 누락과 native path 변경의 provider 실패 합산으로 14:43:58 Entry AI 비활성화를 확인했다. 앞 절의 구현/리뷰 기록은 당시 증거로 보존하고 이 새 결함은 [상세 개선계획](main-post-warmup-latency-rest-ws-bottleneck-remediation-implementation-plan-2026-10-08.md)의 B0~B7로 보완한다. B1/B2 실제 caller·실패 책임을 먼저 닫고 B3/B4/B6 반복 journal·WS 복사·전역 cache 비용을 개선한다. LP7~LP12의 원 deadline·Main commit·필수 저장·수용 계약과 기존 실행 owner를 유지한다. 이 인계는 계획이며 코드/배포/PID 정상화 완료를 뜻하지 않는다.
