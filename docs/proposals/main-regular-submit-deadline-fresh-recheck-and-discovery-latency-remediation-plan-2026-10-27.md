# 정규장 제출 시간 소진·fresh 재평가·일반종목 감시 지연 보완계획 — 2026-10-27

> **10/28 후속 설계 기준:** 사용자가 5초 고정 전제를 해제한 근본 개선안과 실제 만료 대안 비교를 요청했다. 신규 설계·구현 우선순위는 [§10 기한·신호 유효성 재설계](#entry-validity-redesign-20261028)를 따른다. 아래 §1~§9의 원5초 유지 문구는 당시 구현/운영 계약의 기록이며 새 설계값을 제한하지 않는다. 이번 계획 수립은 운영 기한 변경·배포 승인이 아니다.

## 1. 결정과 실행 기준

10/28 PRE 후속은 [프리마켓 전달·제출 지연 상세계획](main-premarket-opportunity-delivery-submit-latency-and-auxiliary-input-remediation-plan-2026-10-28.md)이 소유한다. 아래 완료된 공통 수리/원 정규장 Acceptance는 유지하며 PRE의 적격 최초·재관찰 배분과 원5초/별도1,200ms reference 대사를 같은 기존 owner에서 추가한다. PRE 관측을 REGULAR/SOR/_AL 수용으로 대체하거나 기존 기능을 다시 구현하지 않는다.

**기존 수리를 유지한 채 P0 잔여 처리비용, P1 가격 변경 후 새 판정 연결, P2 일반종목의 적시 감시를 순서대로 보완한다.** 계측·코드 반영·자연 경로 수용을 구분하고, 이미 구현된 기능을 미구현으로 되돌려 다시 만들지 않는다. 이번 구현은 최신 선택f14f42989 위에서 P0·P1·G1/G2를 기존 owner에 반영한다. AI 호출·정책 변경·배포·재기동은 실행하지 않는다.

사용자의 후속 범위 지정에 따라 **구현 세션은 검증된 후보와 인계자료를 제시하고, 다른 세션이 최신 배포본에 통합하여 배포·재기동한다.** 아래 S4가 구현 세션의 종료 경계다. 코드·회귀·native 후보 준비의 실제 결과와 후보 commit/릴리스는 [구현 인계자료](../../tmp/submit-fresh-latency-implementation-20261027/handoff.md)를 따른다. 후보는 운영 선택/기동과 구분한다.

- 기준 시각:2026-10-27 16:47:15 KST. 선택 `3178d65e0a0b39f63a8eb666a9bcb4b132a590f4`, release `/home/ubuntu/KORStockScan-runtime-releases/nonfixed-final-20261027-3178d65e0`, Main1580293/start73079256/cwd 해당 release의`src`. native 정책 소비 검증 PASS이며16:31 기동으로 정규장 수용 표본은 없다.
- [현재 선택·실제 PID·18개 source SHA·원 문서 기준](../../tmp/regular-submit-remediation-plan-20261027/baseline.json)을 고정했다.18개 중14개가 기본 작업 디렉터리와 다르다. **후속 구현은 착수 시 재확인한 최신 선택 릴리스에서 분기하고, 무관한 dirty 변경을 덮어쓰거나 전체 복사하지 않는다.** source가 다르다는 사실만으로 미반영/결함을 판정하지 않는다.
- 운영 bundle은 원 정규장 evidence의 `6b93eb6a16efc2a7a349fcdbd347146200830034d5697564a6500e3ed2472f92`이며 정확 소비는 위 native receipt를 따른다. 새 Wilson 선택 계약은 현재 선택 코드에 없고, [별도 선택계획](main-regular-nonfixed-small-sample-selection-remediation-plan-2026-10-27.md)의 연구·격리 구현을 운영 반영으로 세지 않는다.
- 대상은 Main 정규 session / KRX 정책 cohort / `<symbol>_AL`, `krx_nxt_integrated` 자료 / 요청SOR다. 실제 체결 거래소는 native execution receipt가 없으면 UNKNOWN이다. PRE/AFTER 또는 개별 KRX/NXT census 가격으로 이 경로의 수용을 대신하지 않는다.
- 원 실행 owner는 오늘 checklist의 `MainEntrySourceTerminalRepair1022`와 `MachinePatternOpportunityResearch1023`다. 별도 OPEN ID·스케줄·worker·원장·일반화된 validator를 만들지 않는다. 다음 native 거래일은10/28이며 실제 실행 전에 달력·선택본을 재확인한다.

근거는 [정규장 전체 판정·최초 종료·상승 경로 대사](../audits/main-machine-pattern-dual-track-research-review-2026-10-21.md#regular-pre-submit-guards-and-rising-opportunities--2026-10-27), [일반종목 원천·배포 공백·식별자 수리](../audits/main-regular-nonfixed-opportunity-and-auxiliary-adequacy-review-2026-10-27.md#8-식별자혼합-제외-수리와-원인-추적--1027)다. 과거 시행착오·원 FAIL·수신 결손·UNKNOWN은 보존한다.

## 2. 이미 반영된 개선과 남은 상태

|항목|현재3178에 있는 구현|남은 상태·이번 계획의 처리|
|---|---|---|
|정책 hash 조회·복사|`mechanistic_entry_runtime_policy.validate_attempt_generation`의 immutable loader 사용, `verified_family_evaluation`의 loader 발급 family 구조증명 재사용|재구현하지 않는다. 독립 경계의 현재 pointer/dependency·native claim 검사는 계속 수행하며 잔여 중복비용만 실측한다|
|원 기한·완료 전달|`entry_deadline`의 원 event+5초와 wall/perf 최소 기한, 기존 async 완료·Main 소비·원 결과 단일 종료|구현됨. 오전 실패의 과거 clock을 보존하고 새 정규 PASS의 전달 지연/만료 감소는 미검증으로 둔다|
|claim 전 지연·회로 해석|원 packet epoch/수신·dispatch 시각, blocked/continued preclaim 방문, CLOSED 회로에서 local 기한 소진을 회로 OPEN으로 오인하지 않는 분기|진단·해석 수리다. receive 공백·시간 소진 자체가 해소됐다는 증명이 아니다|
|제출 최초 종료 집계|`call_local_terminal_v1`·call 최초 관측/종료를 읽고 종료 후 watch gate를 이전 call에 섞지 않음|구현됨. 새 blocker 분류기를 추가하지 않고 기존 정확 attempt/terminal을 재사용한다|
|최종 가격/미송신 custody|`PhysicalEntrySendContext.check`의 가격 변경 거부, verified local NOT_SENT의 bundle 종료·WATCHING 복귀·원 PASS 재사용 방지|안전 종료는 구현됨. 초기 계획의 공백 판정은 구현 대조 후 정정한다. 완료 wrapper→native successor wake→fresh claim의 공통 연결은 이미 있다. 이번 수리는 scanner 세대/AI clock이 같을 때 새 claim이 옛 cache key와 충돌하는 지점과 부모/새 판정 증빙이다|
|기존 fresh successor|승인된 `pre_submit_delay_policy_v2`의 due→새 평가·단일 successor, `expired_after_response`의 fresh snapshot recheck 예약|특정 분기의 기능이다. 일반 가격 변경·Main에서 만료한 모든 PASS에 자동 적용되는 것으로 해석하지 않는다|
|일반종목 코드·원천 적격|검증된 master에 따른 영문 포함6자리 코드 보존, WS→queue→probe→Main/order identity 수리, 정확 혼합 제외 epoch reader|구현·배포됨. 새 같은 경로의 자연 표본과 원 무수신 원인은 별도이며 과거 틱을 복원한 것이 아니다|
|일반종목 admission·배분|`DiscoveryQueue.claim`의 실제 fresh/due/active/product 판단·관측 대기시간·기존 순환/age 배분, runtime의 종목별 변경분 기록과 실제 append 성공 확인·census 소비|이미 있다. 슬롯 확대나 새로운 fairness queue를 먼저 만들지 않는다. 실제 대기/재관찰·저장 비용을 이 owner에서 보완한다|
|기계 선택 확장·보조 prompt|소표본 고착 보완/유형별 추가 패턴·프롬프트는 별도 연구|현재3178 반영으로 세지 않는다. 이번 처리시간·전달 수리에 새 정책 채택을 끼워 넣지 않는다|

분류도 구분한다. P0의 원 수명 소진은 **역사적으로 확정된 병목/새 코드 효과 미검증**, P1은 **기존 successor 연결의 신호별 request 신원과 부모 증빙 결손**, 일반종목은 **운영 공백·입력 미가용·늦은 관찰의 확인 및 일부 원인 미확정**이다. 물리 가격 변경 거부, stale/UNKNOWN 거부, 종료 중 실행 차단 자체를 결함으로 제거하지 않는다.

## 3. 원 실패와 비교 표본

정규장 ENTER53→PASS7(삼성3/주성3/HPSP1)→budget/SAFE5→전송0이다. PASS 최초 종료는 수명 소진5확정/1추정·가격 변경1이다. 반복 watch 방문·probe 횟수를 고유 매매 기회로 계산하지 않는다.

|우선 표본|확인된 증거|후속 사용|
|---|---|---|
|09:47 주성 `aims-16f59f1a0244d5ece2f0`|auxiliary 종료·수명 소진 추정, 입력 ask182,400→23분 뒤 census184,800|P0 원 처리비용·원 결속 재생과 놓친 상승 후보. 모델 비용 후+1.086%지만 executable bid 전체 경로/stop-first는 미확정|
|10:09 주성·10:20 삼성|물리 검사 전 monotonic 잔여53/34ms, native 검사 시 원 신호5.364/5.480초|P0 준비/기록/최종검사 누적과 5초 경계 재생|
|10:36 주성 `aims-d4593848a6191aaed9ca`|원 수명 내·quote age140ms, 가격 변경으로 verified local NOT_SENT|P1 음성 원본+새 유효 신호를 붙인 양성 fixture. 당시 후행 상승이 입증됐다고 보지 않음|
|10:00 삼성·10:29 HPSP·11:15 삼성|Main 만료2, auxiliary 검사 시5.553초 만료1|Main 소비·필수 저장·binding/clock 경계 및 정상 만료 음성 검사|
|13:36 삼성 `aims-b5d5a87f778e63b28405`|guard 통과까지3.291초, 입력 준비 뒤1,251ms 잔여·응답1,398ms;28분24.5초 뒤 모델 호가 상승+0.447%|P0 claim 전 비용 비교. locked 진입·수량/체결 미검증이며 AI PASS 표본이 아님|
|멜콘·글로벌테크놀로지·알트·에코앤드림|늦은 lease/관찰, executor unavailable, 오후 새 종료 미관측|P2 실제 source SHA/lease 시각으로 비교. 사후 최대 상승이나 오전 FALSE를 미래 정책 입력/차단 정당화로 쓰지 않음|

[기존 원본·exact join](../../tmp/regular-presubmit-opportunity-review-20261027/findings.json)을 재사용한다. 이미 확인한 가격 상승과 실행 가능한 WIN을 구분한다. 추후 정책 연구 라벨은 native 비용·30분 내+0.4%·소프트손절−3% 선도달 없음이며, 실제 fill/손익을 대신하지 않는다. 미확정은 U/null, 식별 가능한 결손행은 제외하며 전체 날짜를 임의로 실패 처리하지 않는다.

## 4. P0 — 원5초 안의 잔여 시간 소진

**목표:** 기한을 늘리지 않고 유효 결과가 Main과 최종 제출 검사에 도달할 시간을 회복한다. “만료를 더 일찍 출력”하거나 진단 비용을 다른 큐로 옮긴 것만으로 성능 개선을 선언하지 않는다.

1. **원본 대조를 먼저 고정한다.** 선택3178과 후보를 같은7개 PASS 및13:36 입력, 같은 정책·가짜 provider/계좌 응답·격리 저장 root·wall/perf clock으로 비교한다. 원 신호, 준비 시작/종료, provider 시작/응답, 필수 trace 저장, 완료 게시/Main 소비, submit 각 경계, 실제 guard 시각을 기존 timing 필드로 연결한다. 서로 중첩된 child/total은 합하지 않고 부재 구간은 null로 둔다.14:16 연구 자원경합 구간은 자연 개선효과 표본에서 제외한다.
2. **immutable policy의 이미 있는 재사용 범위를 보존한다.** 현재 `verified_evaluation`의 짧은 동기 경계 안에서 동일 발급 객체의 구조/hash 반복 계산만 통합한다. 다음 AI/Main/전송 경계에서는 현재 dependency/pointer를 다시 확인한다. native 신호·quote·계좌·수량 유효성을 캐시하거나 AI 대기/주문 I/O까지 context를 연장하지 않는다. 실측 중복이 없으면 이 부분은 변경하지 않는다.
3. **Main 전달·필수/진단 기록 비용을 줄인다.** 기존 async coordinator의 완료 수집을 먼저 소비하고 무관한 준비/진단 batch로 지연시키는 caller를 재현해 수정한다. report-only 직렬화·중복 emit은 기존 유한 관측 executor/writer로 통합할 수 있으나 request/response/trace·outbox·주문 intent 필수 저장은 완료 전 성공 처리하지 않는다. enqueue와 append 성공, 포화/쓰기 실패를 구분하고 Main 동기 fallback이나 새 worker를 만들지 않는다.
4. **최종 검사 비용을 역할별로 정리한다.** `PhysicalEntrySendContext.check`는 binding/snapshot reader 뒤에 실제 clock을 검사한다. 먼저 저비용 원 기한 검사로 이미 만료한 작업의 불필요한 읽기를 막고, 읽기 뒤와 전송 직전 원 deadline/현재 source/price 검사를 유지한다. 이것은 만료 작업의 낭비 축소이며 유효 PASS 개선은 별도로 측정한다. 동일 정책의 정적 검증을 합치더라도 최신 native eligibility/quote 검사를 제거하지 않는다.
5. **전체 경로를 검증한다.** outer completion→실제 resolver→submit 함수 내부→가격/자금/수량/intent→order adapter까지 연결한다. adapter만 no-network spy로 대체하며 submit 함수를 성공 stub으로 바꾸지 않는다. 새 정규 PASS의 자연 측정 전에는 ‘현재 지연 해소’라고 표기하지 않는다.

산출물은 원/후보의 소요시간·실제 잔여기한·guard 결과·provider/adapter 호출 수·저장 bytes/실패/queue lag를 담은 작은 비교표다. 동일 환경에서 cold/warm을 구분해 반복하고 clock 위조·미집계 실패·지연 전가를 확인한다. 임의 p99·최소 참여율·거래 수를 새 차단선으로 추가하지 않는다. **원 기한 내 정상 통합 경로, 만료 뒤 전송0, 보호조건 회귀0, 반복되는 불필요 local time 감소**가 코드 완료 기준이다. provider 자체가 원 예산을 넘으면 정당한 만료로 보존한다.

## 5. P1 — 가격 변경 후 fresh 재평가의 실제 연결

**목표:** 원 PASS를 안전하게 종료한 뒤 현재 자료를 다시 기계판정하는 기회를 기존 Main 경로에 전달한다. 가격만 바꾸어 같은 PASS를 다시 제출하는 기능은 아니다.

### 기존 owner의 연결과 이번 보완

구현 확인: `handle_watching_state`의 completed-unsent arm 정리와 `rearm_native_watch_after_completion`은 기존 기능이다. 새 신호가 없는 가격 변경은 새 provider/제출을 열지 않는다. 이미 pending인 request는 유지하고, 소유권 정리 후 새 claim의 token을 새 cache key에 포함한다. 원 NOT_SENT의 request/evaluation/trace와 같은 source item/native venue/market/epoch/generation인 다음 신호만 진단상 부모로 연결한다. 부모 링크는 재시도 권한이 아니며 기존 claim/기한·coordinator·기계/AI/주문 검사를 대신하지 않는다. 추가 scheduler·TTL·재가격 loop는 만들지 않았다. 아래 순서는 기존 소비 경로의 검증 계약이다.

1. **허용된 시작점:** exact `execution_price_changed_reprice_required`와 broker adapter가 발급한 verified local no-call 증거, physical attempts0, 해당 bundle/owner의 미전송 종료를 모두 확인한 경우다. 일반 False·auth retry·응답 불확실·기존 주문/부분체결·수동 veto·custody 충돌은 접수 대상이 아니다.
2. **원 사건은 먼저 종결한다.** `_initial_entry_known_not_sent`의 원 attempt/trace/가격/수량/원 기한·bundle 종료와 nonexecution tombstone을 유지한다. 보존/종료가 실패하면 새 평가/주문을 열지 않고 기존 custody 복구로 넘긴다. 동일 원 PASS 재사용 차단은 제거하지 않는다.
3. **기존 scheduler에 한 번만 재평가 의도를 넘긴다.** handler는 새 AI/주문을 직접 부르지 않는다. 기존 WATCHING·async coordinator·fresh 입력 준비를 사용하고, 부모 attempt/native opportunity와 접수 generation을 연결한다. 같은 부모의 중복 이벤트는 합치고 successor는 최대1개, 이미 pending/종료한 접수는 재호출하지 않는다. 자연적으로 생긴 별도 신규 신호의 정상 평가까지 막는 영구 종목 락은 만들지 않는다.
4. **현재 원천부터 다시 판정한다.** exact item/route/epoch·quote·native 신호·현재 정책과 target 상태를 새로 읽는다. 기계 BLOCK/RECHECK이면 AI 호출 없이 해당 결과를 보존한다. ENTER_NOW만 승인된 예산과 기존 provider 경로로 보조판정한다. 새 request/evaluation/trace는 부모와 연결하지만 부모의 AI verdict/prompt/cost/quote를 새 결과로 복사하지 않는다.
5. **기한은 native 신호가 정한다.** 같은 옛 신호를 다시 읽으면 남은 원 기한과 현재 native 적격성을 모두 적용한다. 이미 소비·무효화/종결한 claim/outbox를 재개하지 않는다. native owner가 별도 새 유효 신호/claim을 발급한 때만 그 신호의 원 기한을 사용한다. `now+5`·재평가 접수시각·완료시각으로 옛 신호의 수명을 갱신하지 않는다. 유효한 정식 claim이나 남은 기한이 없으면 AI/제출을 중지한다.
6. **새 가격으로 전체 제출 준비를 다시 한다.** 보조판정과 상태가 현재 경계에서 유효하면 숫자 가격 owner→해당 가격의 계좌 자금·수량/분할→새 intent→최종 물리 guard를 거친다. 물리 guard는 기존대로 현재 가격 변경을 거부한다. 재평가 중 추가 가격 변화가 생겨도 같은 부모의 무한 재가격/AI loop로 돌리지 않는다.
7. **consumer와 terminal까지 남긴다.** 부모 미전송→successor 접수/기계 결과/보조 결과→제출 또는 직접 종료를 기존 async/outbox/submit 영수증으로 연결한다. 접수 실패·기한 소진·generation/PID 교체는 정확히 종료하고 restart 때 원 PASS/종료한 successor를 재실행하지 않는다. 필요한 최소 링크만 기존 schema/reader에 추가하며 별도 전용 원장은 만들지 않는다.

`pre_submit_delay_policy_v2`의 단일 successor 계약은 재사용 가능한 공통 소유권/신원 처리만 통합한다. 가격 변경 사건을 가짜 양수 지연 intent나 퇴역 opening-rotation request로 만들지 않는다. 기존 `expired_after_response` recheck는 유지하고, 여러 경로가 같은 원천을 중복 접수하지 않는지 확인한다.

수정 owner는 기존 `sniper_state_handlers._submit_watching_triggered_entry`, `_initial_entry_known_not_sent`, `_resolve_scanner_async_entry_ai`와 기존 async coordinator/신호·outbox다. 물리 guard/주문 adapter는 현재 no-call 증거와 가격 거부를 유지한다. 기존 공통 successor caller를 유지하며 새 중복 분기를 만들지 않는다. 신원 및 진단 링크를 기존 결과/disposition에 반영한다.

완료 기준: 원10:36 가격 변경은 그대로 미송신 종료, 유효 정식 claim/기계 ENTER가 없으면 신규 provider/adapter0, 유효 successor fixture는 기존 guard 전체를 거쳐 단일 initial leg adapter1회다. manual/custody·stale/conflict·다른 정책/route/epoch·중복 completion·동시 새 신호·restart/쓰기 실패·응답 불확실은 재전송0을 검증한다. 실제 재평가 결과가 BLOCK인 경우도 올바른 연결 수용이며 실제 체결/양의 수익을 코드 수리 조건으로 요구하지 않는다.

## 6. P2 — 일반종목의 감시 진입·재관찰 지연

10/28 REGULAR에서 새로 확인한 매도 우세의 source 오분류·미배정/재관찰·저가 상승지속 후보 선택은 [정규장 후속 계획](main-regular-preclaim-and-discovery-allocation-remediation-plan-2026-10-28.md)이 소유한다. 아래 G1/G2와 기존 P0/P1의 완료 구현·원 안전/clock은 유지하고, Q1/Q2 준비본은 실제 배포와 구분해 필요한 차이만 통합한다. 새 계획은 RFHIC 최종 배포본 기반에서 진행하며 그 복구 owner의 전환·원장을 조작하지 않는다.

**원칙:** 기존5슬롯·동시성/구독·residence·신호 기한·상품/active/manual 제외를 유지하고, 놓친 구간이 어느 단계에서 발생했는지 기존 admission 증거로 보완한다. 상승 종목만 사후 우선 배정하거나 전체 패턴을 활성화하지 않는다.

|순서|보완 범위|구체 구현/측정·완료 기준|
|---|---|---|
|G1: 종료/접수 경계|`_zero_base_consumer_readiness`, native drain, `handle_zero_base_probe_requested`|현 코드는 consumer readiness에 probe CLOSING 상태가 직접 연결되지 않고 callback은 CLOSING 또는 executor.submit RuntimeError를 모두 executor_unavailable로 종료한다. 정상 종료 순서/진행 중 callback 경합을 먼저 재현해 신규 claim의 잘못된 접수가 가능한지 증명한다. 확인된 경우 기존 ready generation/admission close 순서를 수리한다. callback 최종 차단·진행 중 lease의 정당한 drain은 유지한다. 원45건을 worker5슬롯 포화로 바꾸지 않는다|
|G2: dispatch 자체의 비용|`ZeroBaseDiscoveryRuntime.dispatch_due_probes/_persist`, `DiscoveryQueue.claim`|현재 dispatch마다 queue deepcopy와 snapshot JSON/fsync가 수행되는 비용을 원 크기의 격리 큐로 측정한다. 변경 없는 dispatch와 실제 abandoned/claim/result/source 변경을 구분해 **내구 상태 불변이 검증된 경우에만** 복사·동일 snapshot 쓰기를 생략/재사용한다. 실제 claim은 persist 성공 후 worker에 전달하고 실패 시 정확 rollback한다. 기존 저장 owner를 사용하며 DB/새 journal을 추가하지 않는다|
|G3: 적격 대기·반복 관찰 연결|`DiscoveryQueue.observe/claim/resolve`와 기존 종목별 admission delta|기존 fresh/due/active/product 판단·activity/gainer 순환·age turn을 먼저 그대로 재생한다. 최신 발견 정보가 들어오면 queued/assessed가 재접수될 수 있는 구현은 이미 있으므로, 실제 `last_result/next_due/source_sha` 전이와 오후 재관찰 부재를 대조한다. 낡은 cache key·종결/active 플래그·lost wake 등 확인된 전이 결함만 수정한다. 정책적인 재관찰 주기/배분 변경이 필요하면 별도 변경안으로 분리하고 이번 성능 수리에 숨기지 않는다|
|G4: 입력 도달과 후행 비교|기존 wire→normalize→native receipt 및 scanner census|도착 전 미관측, 도착 후 정규화/계산 손실, source stale, 정상 조건 FALSE를 원 lease/PID로 분리한다. 같은 item의 새0B/0D와 정상화 sequence·quote/currentness·선택 branch를 연결한다. source gap을 API 결함/정상 무체결로 단정하지 않는다|

G1의 source 계약 재현은 P0 시작 시 함께 고정하고, 실제 성능 수리는 P0/P1 공통 경로를 안정시킨 뒤 G2/G3으로 이어간다. admission 진단은 현재 `per_symbol_admission_delta_v1`·append 확인·census 소비를 유지한다. `dispatch_samples_only` 대기를 연속 감시 이력으로 바꾸지 않고, capped pending·emit failure·저장 성장/읽은 bytes도 기존 관측에서 확인한다.

회귀에는 같은 master·일반숫자/검증된 영문 코드·unknown 상품, cold start·정상 close·callback 경합·restore·stale 갱신·in-flight source 갱신·장기 residence·short-slot 예약/borrow·공정 배분·writer failure를 포함한다. 단순 총 대기열1,500개나 global full-slot 기록만으로 개별 종목이 적격 대기했다고 세지 않는다. 원53구간 중12개 운영 공백/41개 개별 적격 역사 결손은 보존한다.

산출물은 기존 census의 발견→당시 적격→claim/REG→첫 수신→필수 native 창→기계 결과 시각과 원 사유, fresh 적격 대기의 지연/성숙 전 이탈·일반종목 판정 도달 변화다. 정책 비교는 현행을 고정한다. 다른 날 입력 차이를 제거하지 못하면 처리량 증가를 수리 효과로 확정하지 않는다. 실제 source27/새 날짜 목표-first 결과를 붙이는 별도 패턴·보조 연구는 기존 연구계획이 소유한다.

## 7. 구현·리뷰·통합 및 남길 경계

1. **S0 현재 기준 고정은 완료했다.** 실제 release/PID·native 소비,18개 코드 SHA와 workspace 차이, 원7 PASS/선택 상승구간을 고정했다. 이후 selector가 바뀌면 재확인하고 기존 이력을 지우지 않는다.
2. **S1 P0:** 원 실패/정상 no-network 통합 fixture→잔여 비용 계측→확인된 비용 수리→자체리뷰/보완/재리뷰. G1 종료/admission 반례도 이 단계에 고정한다. 결과는 실제 변경 함수와 절약·잔여 시간으로 남긴다.
3. **S2 P1:** 기존 local NOT_SENT·fresh/async ownership을 연결하고 정상/반복/경계/uncertain 실패를 함께 검증한다. 새 provider 호출 실험 대신 가짜 transport와 원 evidence를 우선 사용한다.
4. **S3 G1~G4:** 확인된 lifecycle/source/큐 비용·전이 결함만 기존 owner에서 수리하고 동일 입력의 도달/대기·persist/rollback·resource 회귀를 확인한다. 단순 capacity 부족이면 정상 제한으로 기록하고 별도 정책/자원 변경과 구분한다.
5. **S4 영향 검증·후보 인계:** 기존 `test_entry_shared_deadline_latency`, `test_runtime_policy_evaluation`, `test_scanner_async_entry_bridge`, `test_main_integrated_bottlenecks`, `test_entry_physical_send_guard`, `test_zero_base_discovery_queue/runtime/source`, `test_zero_base_probe/main_attach`에서 실제 변경 범위를 검사한다. 관련 caller·writer/index/reader·중복/owner·clock·missing/stale/conflict·신규 generation·실패 unwind를 재리뷰하고 compile·`git diff --check`를 실행한다. 예전 모든 인계 조합이나 무관한 전 거래 테스트를 전수 반복하지 않는다. candidate 생성 전 native retention/inventory·여유 용량을 확인하고, 최신 검증 parent 위의 clean immutable 후보를 준비한다. 이 세션은 selector/hold/drain/start를 수행하지 않고 아래 인계 manifest를 제시한 뒤 종료한다.
6. **S5 다른 세션의 통합·배포·재기동:** 인수 세션은 실제 착수 시 incumbent/PID/start/cwd·활성 정책과 후보 parent를 재확인한다. 중간 변경이 있으면 필요한 commit만 통합·재리뷰하고 변경으로 무효화된 검증을 다시 수행한다. 원 후보 P5를 새 통합본의 증거로 복사하지 않는다. 현재 활성 정책과 독립 preparation reader/P5·완전한 직전 generation·ordered transition/CAS/실패 unwind를 검증하고 drain 전에 후보를 완성한다. 사용자 지정 범위에서 selector/prepare/start를 실행한 뒤 exact PID 소비·현재 observer/health를 확인한다. 정책 내용이 같으면 신호/AI 연구 원장과 완료 EOD/장후 전체를 다시 만들지 않으며 코드세대로 무효화된 직접 소비자만 native 절차로 갱신한다.
7. **S6 다른 세션의 자연 수용:** 기존 owner의 다음 정규 창10/28 09:30~10:00에 그때 실제 배포된 PID의 SOR/_AL·정책·원 신호로 P0 잔여기한/정상 terminal, P1 새 successor 소비, P2 실제 적격→감시/판정 도달을 확인한다. 그때 미구현/미배포이면 incumbent 관측과 계획 상태로 남긴다. PRE/AFTER 수용으로 REGULAR를 닫지 않고 표본 부재는 같은 owner OPEN으로 유지한다. 새 예약이나 주문/구독을 만들어 수용을 제조하지 않는다.

P0/P1 실행 owner는 `MainEntrySourceTerminalRepair1022`, 일반종목 전달 수리도 그 owner와 기존 `MachinePatternOpportunityResearch1023`의 범위를 따른다. source27 20:05~23:59는 이미 있는 연구 입력/라벨 확인 창이며 이번 문서가 장후 실행을 지시하지 않는다.

### 다른 세션에 제시할 후보 인계자료

- 정확한 baseline parent/관측 selector SHA와 clean 후보 commit·릴리스 경로·Git 상태, 통합해야 할 commit 순서 및 파일별 원/후 SHA.
- 다른 세션의 병행 후보·승인된 정책 변경과 겹치는 코드/contract 목록. 현재 별도 A09 선택 후보 준비가 같은 연구 owner에 기록됐으나3178의 채택으로 세지 않는다. 후속 통합에 포함하면 그 owner의 선택·부모/code/source 인계 증거를 따로 유지하며 이번 성능 검증으로 대신하지 않는다. 이 수리 자체의 정책 불변과 별도로 승인된 정책 변경을 구분한다.
- P0/P1/G1~G4의 구현/리뷰 완료 여부, 실제 교체·제거/유지 범위, 원 실패 반례·정상/음성 검증·동일 입력 성능 비교와 남은 결함/미확정.
- native active-parent/policy parity·독립 preparation/P5 등 **실제로 완료한** receipt의 path/SHA·대상 generation. 미완료 항목은 그대로 남기며 코드 회귀 PASS를 배포 준비 PASS로 대신하지 않음.
- 원 정책·원5초·가격/수량/custody/guard가 바뀌지 않은 범위와 필요한 직접 consumer 갱신, 원 실패·진단 원천 보존 위치 및 rollback 조건.
- 아직 selector 미변경/미기동임을 명시하고, 인수 세션의 최신 parent 대조→충돌 통합→영향 검증→native 전환→새 PID/observer→10/28 정규 수용 순서를 기록. 후보 parent가 달라지면 원 CAS/기동 증거를 재사용하지 않음.

## 8. 교체·보존과 계획 검증

- `retained`: immutable loader·원5초/clock·async coordinator·outbox/미송신 tombstone·숫자 가격/자금·수량/주문 owner·물리 guard·원 admission/큐·source master·기존 bounded pipeline/census. 기존 미수신/경제성 null과 퇴역 owner 경계를 유지한다.
- `consolidated` 대상: 실측으로 확인한 같은 경계의 정책 구조/직렬화 반복, 검증된 불변 dispatch의 copy/persist, 기존 fresh successor 신원/단일 접수 처리. 각각 실제 caller 전환과 원 의미 동등성을 확인한 뒤 기존 중복 분기를 제거한다.
- `removed` 대상: 후속 구현이 대체한 중복 호출/이중 접수 분기. 아직 구현하지 않았으므로 제거 완료로 표시하지 않는다. 새 wrapper로 옛 구현을 영구 존치하지 않는다.
- `deferred`: 원천 유실 복원 불가 구간의 경제성, 별도 기계 선택·프롬프트 채택, capacity/TTL/배분 정책 변경. 기존 연구 owner와 정확한 source/채택 계약이 충족될 때만 해당 후속을 연다.

이번 구현에는 신규 runtime 모듈/worker/dispatch/registry/원장0이다. 실제 source/test/doc 증가·삭제는 인계자료의 baseline 대비 accounting을 따른다. 대형 raw 재스캔·복제·AI 호출은 없고 기존 bounded evidence를 재사용했다. 계획 재리뷰는 ‘현재 이미 있음/구조 공백/인과 미확정/정상 안전 종료’를 분리하고 P1의 옛 신호 기한 갱신·불확실 주문 재전송·재평가 loop를 방지하는 기준을 보완한다. 문서 link/anchor·기존 owner 각1개·print-only parser·diff 검증과 실제 selector/PID 재확인은 [계획 검증 기록](../../tmp/regular-submit-remediation-plan-20261027/validation.json)에 남긴다. 문서 작업으로 trading pytest/실측 성능 개선/운영 정상화를 주장하지 않는다.


## 9. 구현 리뷰와 후보 인계 — 10/27

- P0: 물리 검사 진입 전 원 wall/perf 기한을 확인하고 읽기 뒤 검사를 유지했다. Main physical binding 준비에서 필요한 machine/candle 필드만 private copy로 투영하며 무관한 AI replay/feature 전체 순회를 제거했다. 원5초·현재 source/price·수량/custody 검사는 유지한다.
- P1: 기존 common successor wake를 재사용한다. 새 native token을 request key에 넣어 같은 scanner 세대/AI clock의 완료 결과 충돌을 방지하고, 원 price-change NOT_SENT→새 request/trace를 기존 disposition에 연결한다. native SOR와 정책 KRX를 구분해 원 snapshot의 item/venue/market/epoch를 보존한다. malformed·다른 source·custody/outbox gap에는 부모 링크를 만들지 않는다.
- G1/G2: CLOSING을 실제 consumer readiness에 연결했다. scalar Candidate의 checkpoint/snapshot 복사를 단순화하고 동일 payload와 동일 file generation이 모두 확인된 성공 저장만 재사용한다. source/claim/result 변경은 여전히 fsync 완료 후 worker에 전달한다. 파일 교체·삭제·쓰기/fsync 실패·rollback을 검증했다.
- G3/G4: 현재 observe/claim/resolve·retry cadence·age 배분과 wire 정규화 owner를 유지한다. 새 정책/슬롯/구독/재시도 변경의 근거가 없어 변경하지 않았다. 원 41구간 admission 결손·미수신과 경제성 null은 보존한다.
- 동일 입력 격리 비교: 1,500행 checkpoint warm median 49.82→10.34ms, snapshot+JSON14.98→11.35ms. 같은1.04MB snapshot의 강제 저장22.03ms 대비 검증된 불변 저장11.84ms. 중첩 불필요 context를 포함한 binding 투영91.01→0.0035ms는 합성 부품 비교이며 실제7 PASS 전체 소요시간 개선량/실거래 성공으로 확대하지 않는다.
- 리뷰 보완: 저장 후 generation 부재가 cache에 들어갈 수 있는 반례를 재현해 제거했다. native 인계에서는 실제59a922 정책 원본·선택3a989의 물리 SHA와 기존 formatting owner의 정규 SHA를 각각 고정한다. 모르는 endpoint나 혼합 세대를 허용하지 않는다.
- 교체/제거: `removed` 전체 AI/prepared payload thaw2곳과 Candidate 전체 asdict 경로의 반복 스칼라 복사. `consolidated` 기존 persist 성공 cache/스냅샷. `retained` 원 deadline/최종 재검사, 단일 successor scheduler, active/manual/custody·계좌/수량/주문 owner, retry/age·5슬롯·native 원천. 별도 wrapper/옛 대체 구현을 남기지 않았다. historical reader/profile은 원 계약/봉인 receipt 소비 때문에 유지한다.
- 코드 검증과 native 준비는 [인계자료](../../tmp/submit-fresh-latency-implementation-20261027/handoff.md)의 실제 receipt/path/SHA로만 완료를 표시한다. 이 세션 selector/hold/drain/start0, actual PID 소비/자연 수용은 미실행이다. 다른 세션이 통합 후 다음10/28 09:30~10:00 REGULAR/SOR/_AL 창을 기존 owner에서 확인한다.


### 최종 기반 갱신: f14f42989

다른 세션이17:37 기동한 `f14f4298907806aa568bec65a764e2f38e2e0530`/Main1993963/start73475785를 실제 최신 기반으로 다시 통합했다. 초기3178→3a와 중간ebbf 후보의 인계/시험/보고서 증거는 원 시점대로 보존하며 최종 후보의 운영 인계·P5에 재사용하지 않는다. 최신 기반의 시장가 wire-price 증빙 수리, quote collection JSON 결속과 WS local-session/raw-state 분리는 그대로 유지했다. 시장가 증빙은 추가28개 정상 경계 반례와 실제 adapter·가짜 POST 연결로 재확인했으며 route/type/quantity·원 기한/현재 가격 guard는 바꾸지 않았다. 공식 HEAD/API spec·core·Postman 검토는 [검토 증거](../../tmp/submit-fresh-latency-implementation-20261027/official-reference-market-context.json)를 따른다. 새로운 API/AI/주문 호출은 없다.

최종 기반 영향 검사는 runtime1,241 PASS이며 새 native/독립 preparation/fixture reader와 후보 준비는 [최종 인계](../../tmp/submit-fresh-latency-implementation-20261027/handoff.md)의 receipt 및 SHA를 따른다. 중간 보고서 재검증 중 외부 selector 전환으로 보호조건이 실패한 이력은 보존한다. 원 holding/report/manifest·정책은 그대로이며 외부 selector 전환을 이 세션의 배포로 세지 않는다.

<a id="entry-validity-redesign-20261028"></a>
## 10. 기한·신호 유효성·처리 경로의 근본 재설계 — 2026-10-28

### 10.1 결정·권한·현재 기준

**5초는 비교 기준이며 설계의 고정 전제가 아니다. 신호 수명과 처리 예산의 정책 적합성을 처리 단축과 동시에 검증한다.** 기존 §4의 “먼저 원5초 안에서 줄이고 이후 검토” 순서는 이번 신규 설계에서 대체한다. 과거 수리의 원5초 보존, 당시 회귀와 운영 증거는 그대로 보존한다. 이번 권한은 개선안 수립과 기존 실제 사례의 오프라인 비교다. 실행 코드/기한·provider·API·슬롯/자원·주문·배포/재기동 변경은 없다.

- 15:00 기준 최신 운영본 `f4cdac80647b71aae8f7d8ef5114ff5879c463cf`, PID197518/start81121238, 실제cwd와 native policy consumption `ready` 확인. [기준·문서 원본](../../tmp/entry-validity-redesign-20261028/baseline.json). 구현 시작 때 다시 핀하고 이미 반영된 cache/완료 우선 처리/wake/의미 분리를 재구현하지 않는다.
- 실제 사고는 각각 원래 PID/릴리스·정책으로 해석한다. 10/27 REGULAR/SOR,10/28 PRE/NXT,10/28 REGULAR/SOR는 별개 모집단이다. 수치가 다른 당시 정책을 새 정책으로 소급하지 않는다. 138/PID4183243의13:57:58~14:45:52 동결을 새197518 성과로 바꾸지 않는다.
- 공통 기한·전달은 `MainEntrySourceTerminalRepair1022`, 비상시 관찰 배분/선택은 `MachinePatternOpportunityResearch1023`가 계속 소유한다. 새 OPEN ID·cron·상시 진단기·정책 자동 승격기를 추가하지 않는다. 현재 일정/다음 자연 창은 [10/28 checklist](../checklists/2026-10-28-stage2-todo-checklist.md)의 같은 두 owner를 따른다.
- 유지되는 안전과 연구 가능한 기한을 구분한다. 현재 승인된 실행 정책은 새 정책 선택·인계 전까지 그대로 적용되지만, 그 숫자를 개선안의 성공 조건으로 고정하지 않는다. 기한 연장은 정책 의미를 바꾸므로 동일정책 code handoff만으로 운영 승인할 수 없다.

검토 중 추가된 [동일 최신 PID의15:06 동결](../../tmp/regular-delivery-integrated-20261028/natural-acceptance-through-1506.json)도 확인했다. 상시 claim11건 중5건이 신호 후2초를 넘었고,036930의 `aims-7bf521db52d3b5c36625`는 첫 큐 방문0.141초→claim4.638초로 잔여0.362초에서 시작해 AI 전 만료됐다. 같은 PID의 구간 합계는 target 처리3.618초·idle1.000초이며 세부 구간은 일부 잘려 단일 함수의 원인으로 단정하지 않는다. 별도 호출 후 timeout5건의 transport 예산은447~1146ms였다. 이 관측은 아래 사전 지정9건 분모에 사후 추가하지 않고, **claim 전 대기와 provider 예산도 P0에 포함해야 하는 현재 증거**로 사용한다. 비상시 배정34건(최초23/재관찰11)은 정식 기계 승인·제출34건이 아니다.

### 10.2 실제 사례로 수행한 대안 비교

[재현 가능한 비교 코드](../../tmp/entry-validity-redesign-20261028/compare.py)와 [입력 hash·결과](../../tmp/entry-validity-redesign-20261028/comparison.json)를 남겼다. 원 capsule의 내용 SHA, native Main/physical 시각, request/evaluation/PID를 연결했다. 10/27 원 payload8.8MiB와 작은 기존 동결본만 읽었고 전체 pipeline/일별 원천을 재스캔하거나 provider를 재호출하지 않았다.

**정확한 만료 시각을 가진 사전 지정9건**을 비교한다. 만료 사례로 선정한 표본이므로 전체 기회·승률·정상 제출률의 분모가 아니다. `decision_ts`나 로그 출력 시각을 실제 검사 시각으로 바꾸지 않았다.

| 원 사례 | 실제 차단 경계 | 원 신호 이후 시간 | 당시 AI |
| --- | --- | ---: | --- |
| 10/28 삼성 `aims-cffc16d81c6749fec266` | 입력 최종 동결 | 5.123초 | 미호출 |
| 10/28 삼성 `aims-ad7553e6c2ed5c6dddec` | 입력 최종 동결 | 5.049초 | 미호출 |
| 10/28 삼성 `aims-84bef36c8b1f6dfd88fc` | 입력 최종 동결 | 5.321초 | 미호출 |
| 10/27 삼성 `aims-4e553d575a726719402f` | Main 종료 판정 | 5.171초 | PASS |
| 10/27 주성 `aims-34e13653a782f358d16e` | 물리 전송 직전 native 검사 | 5.364초 | PASS |
| 10/27 삼성 `aims-c8cab60bb3dfad2f1b66` | 물리 전송 직전 native 검사 | 5.480초 | PASS |
| 10/27 HPSP `aims-dbabc38bc3b3fb87ecb6` | Main 종료 판정 | 5.470초 | PASS |
| 10/28 삼성 `aims-b0dd134e5473a3e6335a` | 응답 처리 후 Main 검사 | 5.203초 | PASS |
| 10/28 알테오젠 PRE `aims-7f20a47ca8d7fd6e4339` | Main commit 검사 | 5.010초 | PASS |

| 대안 | 현재 자료의 검증 결과 | 판단 |
| --- | --- | --- |
| A: 현행5초+처리 단축 | 같은 경계에서0.25초 단축을 **가정**하면5/9,0.5초면9/9가 시간상 기한 안에 들어옴 | 실측 절감량이 아니다. 최적화만으로 근본 수명 설계가 맞다고 결론낼 수 없음 |
| B: 일괄 고정6초/8초 | 같은 기록된 검사 시점에서는 각각9/9가 시간 조건을 통과 | 6·8은 연구용 민감도 값이며 채택값 아님. 미호출3건의 이후 AI·최종검사 시간은 미관측이고 후단 가격/계좌·주문 검사가 모두 끝난 것도 아님 |
| C: 의미적 무효화+유한 수명 상한+독립 quote/AI/주문 검사 | PRE 알테오젠1건은 같은 Main 시점의 age 이외 native predicate가 모두 참. 삼성14:12는 branch/원천/호가가 참이지만 ready membership이 이미 없어 보존·만료 원인 분리가 필요. 나머지7건은 해당 비교 경계의 완전한 비시간 predicate 부족 | **우선 구현할 설계 후보.** 현재 증거로 신규 주문 허용을 입증한 건수0. 결손을 true로 채우지 않고 같은 원천으로 최종 consumer까지 재생할 것 |
| D: 만료 후 새 신호로 fresh 재평가 | 기존 신호를 되살릴 수 없으며 새 신호/claim/input/request/AI와 새 시각이 필요 | 보완 경로다. 원 만료 경로를 고치는 것과 별개이며 무한 재요청/기존 PASS 재사용 금지 |
| E: claim 또는 AI 호출 때부터 다시5초 | 최신036930은 claim4.638초 후 기한을 다시5초 주면 원 신호의 총 수명이9.638초가 됨. 반면 첫 가격 유지선 이탈은0.100초에도 발생 | 시작점 이동만으로는 신호 안전성을 설명하지 못함. 총 신호 수명 상한·연속 유효성 없이 이 방식을 채택하지 않음 |

현재 native `EntryDeadline.create`에 호출자8초를 넣어도 claim의 원5초와 min을 취해5초가 유지되는 것을 실제 helper로 확인했다. **한 timeout 인자만 바꾸는 방식은 대안B/C 구현이 아니다.** 전체 주문 경로 재생·가상 체결은 수행하지 않았으며 실제/모형 손익은 null이다. 부분 시계만 있는10/27 09:47·11:15,10/28 08:05 및 다른 사전 AI4건은 이9건 수치에서 제외하고 원 증거를 보존했다.

안전 대조군도 분리했다.

- 10/27 주성 `aims-d4593848a6191aaed9ca`: 원신호+4.644초·quote age140ms에도 `execution_price_changed_reprice_required`. 기한을 바꿔도 원 주문을 보내면 안 된다.
- 10/28 심텍 원 signal `...:92`·`...:150`: 각1.487초/0.100초에 `first_price_hold_breached`. 가격이 회복돼도 원 신호 무효화를 취소하면 안 된다. 새 신호는 별도 발급한다.
- 10/28 알테오젠08:06: native 검사+3.336초로 원 수명 안이었지만 별도 `latency_block`. 5초 변경으로 이 결과를 자동 해제하지 않는다. 원 signal reference의 신원/clock 결함 여부와 승인된 DANGER/stale/가격 안전은 별도로 검사한다.
- 정상 비상시 PRE RFHIC49558·안랩49559의 BUY receipt 원 SHA를 확인해 회귀 입력으로 지정했다. 과거 주문/체결을 새 대안의 주문 성공이나 수익으로 합산하지 않는다.

### 10.3 한 숫자에 섞인 역할을 분리하는 설계

| 계약/시계 | 의미 | 새 설계의 소유·처리 |
| --- | --- | --- |
| 패턴 확인 창 | FIRST/CONFIRMED/HOLD 등 정의가 성립하는 관측 시간 | 기존 branch 정의·최초 기준·필수 관측량 유지. 같은 숫자5라고 실행 수명과 함께 변경하지 않음 |
| 신호 최대 수명 | 원 confirmation에서 얼마 동안 동일 신호를 실행 후보로 인정할지 | 기존 native family/claim owner가 버전·scope·발급시각·절대기한을 한 번 발급. 5/6/8 등 후보를 비교하되 적용값은 미선정 |
| 의미적 유효성 | 원 유지선/저점 이탈·branch 소멸·epoch/세대 변경·원천 연속성 손실 | 첫 무효화를 종료까지 보존. 현재가 회복·재조회로 reset하지 않음. unknown은 실행 불가 |
| 실제 처리 예산 | admission/준비/AI/후처리/Main/submit이 사용할 남은 시간 | 발급된 절대기한과 wall/perf의 보수적인 min을 모든 consumer가 전달. 단계마다 now+TTL 발급 금지 |
| AI 결과 권한 | 정확한 input/정책/claim에 대한 특정 응답의 사용 가능 범위 | 현행 AI authority 만료와 request/input hash/변경 민감 fact를 독립 검증. 신호 수명 연장만으로 AI 권한 연장 금지 |
| 실행 원천·호가 현재성 | 해당 item/route/epoch의 최신 체결·BBO·가격 유효성 | 기존 quote-time/source contract와 물리 검사 유지. 신호의 나이가 늘어도 stale quote 허용하지 않음 |
| latency reference | 별도 signal reference의 나이·가격/slippage 판정 | 기존 source identity·시각 결속 유지. stale/DANGER·원 가격/계좌·주문 보호는 우회하지 않음 |

후보C의 실행 조건은 **유한 signal deadline 안 + 원 신호의 연속 유효성 + 유효 AI 권한 + 최신 실행 원천/가격 + 기존 모든 주문 안전**이다. 상한 없는 “계속 유효하니 계속 기다림”도, 기한 초과 결과를 조용히 새 신호에 붙이는 것도 허용하지 않는다. KRX/NXT/SOR·PRE/REGULAR/AFTER·상시/비상시를 시계로 추측하지 않고 실제 session/정책 cohort/data item·route/broker 요청/체결 venue를 분리한다.

신호 수명 후보는 기존 family가 정의한 최초 confirmation을 `T0`로 고정하고 `T_signal_end = T0 + L(scope, policy_version)`로 발급한다. 처리 시작점은 별도로 기록하며 준비·AI·후처리의 예산을 남은 수명 안에서 배분한다. L은 원 가격 경로의 유효성·실행 품질과 비용을 비교해 선택하며 **현재 큐가 밀렸다는 이유로 자동 증가시키지 않는다.** 실행 기한을 claim/응답 시점으로 옮기는 대안도 총 신호 나이를 함께 비교한다. 새 확인을 시작점으로 쓰려면 이전 신호를 종료하고 실제 새 관측으로 확인된 신호를 발급해야 한다. 최종 AI PASS를 다른 신호에 재사용하지 않으며, 미리 계산할 수 있는 것은 불변 정책/정적 입력 준비와 허용된 문맥뿐이다.

발급 계약은 기존 claim/등록 영수증과 family 정책에 필요한 lifetime policy version, scope, confirmation 시각, 절대기한, 최초 무효화 identity, input/정책 hash를 연결한다. 새 독립 정책 엔진이나 주문 원장을 만들지 않는다. historical5초 claim은 당시 버전으로만 읽고 새 수명으로 소급하지 않는다. 실행 중 발급한 claim의 기한은 변경 불가다. 세대 전환은 새 claim부터 적용하며 이전 in-flight claim은 기존 기한·권한으로 종료한다. 선후 관계를 증명하지 못하는 중간 세대·PID 재사용은 차단한다.

현재 `response_reserve()`는 관측 없으면0, 최근 `response_validate` p95를 최대0.25초로 제한한다. 삼성14:12 실제 `response_reserve_ms=0`, 로컬 후처리1.132초였다. 이 함수의 예측 범위가 필수 후단 전체를 대표하는지 검증해야 한다. **reserve를 크게 만드는 것만으로는 AI 호출 전 탈락을 앞당길 수 있어 개선이 아니다.** 준비 단축·후단 비용·전체 신호 수명과 함께 비교하고 냉기동/정상/혼잡·상시/비상시 분모를 유지한다. 충분한 예측 자료가 없으면 unknown으로 기록하며 provider 지연을 0이나 임의 p95로 가정하지 않는다.

### 10.4 구현 우선순위와 기존 owner의 변경 범위

| 우선순위 | 구현 범위·기존 소유 위치 | 산출물과 완료 판정 |
| --- | --- | --- |
| P0-A / 공통 | `entry_deadline`, `reversal_extended_runtime/state`, 현재 상속되는 `reversal_registered_runtime`·`reversal_path_runtime`, `reversal_source_diagnostics`의 발급/보존/claim/검증/종료 연결 | lifetime 정책·절대기한의 단일 발급 계약과 typed 종료 원인. 단계별 hard-coded5 중 실행 수명만 이관. confirmation/source-clock5는 유지. 원9건+무효화/세대/clock 음성을 실제 caller로 재생 |
| P0-B / 상시 및 공통 후단 | `ai_engine_openai`·`mechanistic_entry_runtime_policy`·`reversal_auxiliary_intraday`·`continuous_reversal_policy`·기존 outbox/writer | 신호 전 immutable 준비, 응답 뒤 mandatory 검증/저장/변환의 CPU/I/O/lock 비용 분해와 중복 제거. 단일 evaluation 안의 불변 검증만 재사용; provider 대기 뒤 mutable 검사는 새 경계에서 수행 |
| P0-C / 상시와 비상시 신호 인수·async 직접 소비 | `sniper_state_handlers`·`scanner_async_eval`의 기존 coordinator/완료 소비·`physical_send_guard` | native-ready→claim 대기와 응답→Main 대기를 함께 수리. 기존 loop의 ready/완료 우선 인수·기한순 처리·idle wake를 비교하되 한 종목 독점/다른 안전 작업 기아를 방지. issued contract를 Main→submit→가격/수량/intent→adapter 직전까지 전달. 기존 completion-first/wake를 재작성하거나 별도 무제한 worker를 추가하지 않음 |
| P1-A / 비상시 병행 | `zero_base_probe`, 기존 DiscoveryQueue/dispatch와 등록·첫 수신 owner | Q0/current와 구현된 Q1/Q2를 같은 적격/source/슬롯/체류/due로 비교. 최초/재관찰의 admission→first receive→필수창→선택까지 대사. 수신0은 exact item/lease/epoch의 local send/connection response/wire/normalize로 분리; Kiwoom 코드 변경 전 공식 reference gate |
| P1-B / 비상시 병행 | 기존 machine candidate registry·누적 비교/선택 owner | 선택 신호0을 기한 문제와 분리. 기존 G4/G1/G2·등록 상승지속 후보의 실제 price-band/branch·현재성·누적/미사용 결과 비교. 기한 연구에 패턴 완화를 섞지 않고 이미 실패한 후보를 새 이름으로 재등록하지 않음 |
| P2 / 정책 선택·적용 준비 | 현재 native family 선택/등록·policy handoff·release routing owner | 대안A/B/C의 완전한 비교 후 한 scope의 lifetime 후보를 명시 선택. 최대 수명 변경을 동일정책 parity로 위장하지 않음. 기존 선택·canary/override 계약·rollback과 source consumer inventory로 승격하며 자동 승인하지 않음 |

P0-A의 계약 설계와 P0-B/C의 실제 비용 검증은 함께 착수한다. P1-A/B도 이 결과를 기다리지 않는다. 순서가 “최적화를 모두 끝낸 뒤 TTL 연구”로 돌아가면 계획 위반이다. 현재 일부 공유 파일의 dirty 작업·다른 세션의 보유/SELL/수량 수리는 원 scope에 남겨 두고 구현 시 최신 선택본에서 필요한 hunk만 통합한다.

비상시 근거는138/PID4183243의 종료106lease/97종목: 패턴 불일치39·확정대기2·유효 이력 후 현재 stale35·route 미수신18·0B age9·0B없음1·필수호가/feature2, 선택 TRUE0이다. 당일 최초85/재관찰21, 적격대기422·활성5·관측된 최대대기47.3분이다. 반복 평가/관찰과 독립 기회·연속 적격 대기를 구분한다. 기한만 변경해 이106건이 진입 신호로 바뀐다고 가정하지 않는다. [원 분석](../../tmp/submit-cause-latest-20261028-1447/144552/analysis.json).

### 10.5 제거·통합 및 유지할 안전장치

| 기존 경로 | 후속 처리 | 확인할 caller/consumer |
| --- | --- | --- |
| active 신호의 `epoch+5`, ready pop/claim/validate 각자 수명 계산 | `consolidated` 예정: 단일 발급 계약 소비 후 중복 실행 수명 산식 제거 | native state→claim→EntryDeadline→AI→async→Main→physical→observer 전부; 동적 backend dispatch 포함 |
| 중간 `now+5`·별도 caller 상한 | `retained` 또는 `removed`를 실제 claim 존재/legacy 역할별 확정 | non-claim legacy를 신규 승인 우회로 사용하지 않음; original caller보다 기한 확대하지 않음 |
| confirmation timeout·exchange/source clock 허용5·quote freshness | `retained` | 별도 의미의 현행 source/branch 계약. 숫자 일괄 치환 금지 |
| 원/구 버전 claim·봉인 code reader | `retained` | 과거 재생·인계/rollback consumer, 현행 실행으로 퇴역 기능 복원 금지 |
| 동일 immutable 경계의 중복 검증/보고용 복제 | 측정 후 `consolidated`/`removed` | 기존 cache/writer의 실제 direct caller·실패 저장·queue 포화 확인. 필수 outbox/intent durable 저장은 retained |
| 기존 Q1/Q2·fresh successor·완료 wake | `retained` | 이미 구현된 경로를 확장. 새 queue·worker·validator 추가 없음 |

보호 조건은 다음 전체를 유지한다: DANGER·stale/conflict, current price/executable BBO·spread/slippage·depth, exact route/item/epoch/시계·세대, 최초 무효화·등록된 claim, 기계 ENTER와 동일 input에 대한 유효 AI PASS, 수동관리/operator lock·보유 custody·퇴역 owner 경계, 계좌/현금·수량·cap·미체결/중복·cooldown, hard/protect/emergency와 기존 청산 권한. 미확정 전송 재시도·만료 PASS 재사용·인수 성공을 필수 저장 성공으로 대체하지 않는다. 최대 수명·결과 권한·현재 원천 중 하나라도 만료/unknown이면 실행 불가다. 승인되지 않은 live 수명 연장은 없다.

### 10.6 비교 실험과 완료 기준

**이번에 완료한 것은 원 사고 비교와 계획 검토다.** 구현·새 기한 선택·전체 제출 재생·배포·자연 제출·경제성은 아직 완료하지 않았다. 아래 검증으로 계획을 실행하며 단순 테스트 개수/기동 성공을 성능 수용으로 바꾸지 않는다.

1. **동결 재현:** 위9건+가격변경1+유지선 이탈2+독립 latency1+정상 비상시 PRE2를 각 원 code/source reader로 baseline 재현한다. 회복/악화 가능성을 보기 위해 만료만 뽑은9건에 정상·실패·새 원천 결손을 더한 전체 적격 cohort를 별도로 고정한다. closed loop를 임의 성공 stub으로 바꾸지 않는다. 원천 부재는 U/null이며 새 자료를 과거 predicate로 채우지 않는다.
2. **실제 경로 비교:** A/B/C는 같은 immutable inputs·동일 provider 응답 bytes·정확한 시각/최초 무효화 stream·비용과 actor provenance를 사용한다. 원 provider 미호출3건에는 새 응답을 꾸며 넣지 않고 `post_provider_unknown`을 유지한다. replay에서는 네트워크·broker adapter만 no-send spy로 막고 Main→submit→수량/intent→physical predicate는 실제 owner를 실행한다. 미래 정보가 당시 선택·예산을 바꾸면 실패다.
3. **기한/경계 회귀:** confirmation 직전/직후, 수명 상한 직전/같은 시각/직후, wall clock 역행/전진, monotonic 소진, 세대/PID/route/epoch 변경, ready evict/첫 무효화 후 가격 회복, provider late/unsettled·중복 완료, lock/writer 포화·부분 append·중단/재기동을 검증한다. 현재 native `<=5`와 budget/physical `>=deadline`의 경계 차이도 한 계약으로 명시한다. 기존 MAX_READY/queue/storage 경계를 넘겨 자료를 보존하지 않으며 결손은 실행 불가로 남긴다.
4. **코드 완료:** 원 계약 차단/가격변경/최초무효화/unknown 음성의 adapter 호출0, 정상 입력은 단일 intent/정상 initial adapter 도달, mixed generation 거부, 필요한 기록의 원 SHA/custody 보존, 이전 active consumer의 중복 수명 산식 제거를 확인한다. TTL-only로 보이는 사례는 비시간 guard와 실제 처리 소요를 함께 증명한 경우에만 복원으로 센다. 실제 원가/체결 부재는 진단 코드 수리의 실패 조건으로 추가하지 않는다.
5. **지연·처리량 완료:** cohort별 signal→claim→provider→response→Main→physical/adapter의 비중첩 시간, cold/warm/혼잡 p50/p95/p99, 잔여기한, CPU/I/O/lock, writer lag·누락·호출/자원수를 baseline과 비교한다. 선택한 유한 cap 안에 정상 경로의 측정 p99와 계측 불확실성이 들어오지 않으면 성능 수용을 닫지 않는다. 표본 부족으로 p99를 추정한 경우 그대로 미확정이다. 사전 AI 탈락만 늘려 만료율을 낮춘 후보는 채택하지 않는다. 상시/비상시의 유효 기계→AI PASS→정상 제출 도달률·정당한 비진입을 각각 보고한다.
6. **정책 적합성·경제성:** lifetime 변경은 전 사례에서 추가로 허용/차단한 exact 기회와 가격 불리, native 비용 후 target/stop/timeout/U, rolling/cumulative·미사용 날짜를 owning family 지표로 비교한다. Main machine selection의 현행 win-rate 예외를 다른 가족에 확대하지 않고, provider/기한 수리의 코드 완료에 새 EV gate를 임의 추가하지 않는다. 비용/후행 경로/실제 venue가 없으면 손익 null, 다른 venue census 최고가로 이익을 주장하지 않는다. 9/9 시간 통과만으로6초를 선택하지 않는다.
7. **배포·자연 수용:** 별도 승인된 후보에 현재 정책 또는 새로 명시 선택된 정책의 정확한 handoff·consumer census·격리P5·rollback을 준비한다. 실제 selected generation/PID 소비와 observer/health를 확인하고 기존 checklist의 PRE/NXT/_NX, REGULAR/SOR/_AL 창에서 branch별 자연 결과를 검증한다. AFTER 적용을 포함하면 해당 실제 session/route에 새 창을 같은 owner에 명시하며 REGULAR로 대체하지 않는다. 해당 표본이 없으면 자연 수용 OPEN이고 이미 완료한 코드 수리를 반복하지 않는다. 새 source/price/권한 결손·중복 전송·안전 실패가 나타나면 기존 native rollback owner로 되돌리고 실패 영수증을 보존한다.

**선택 방향은 C의 단일 발급·연속 유효성·유한 상한 구조와 B/C 간 실제 정책 비교, 그리고 공통 처리 단축이다.** 5초 고정도, 무조건 연장도 이번 결론이 아니다. 현재 9건의 경계 비교에서 추가 수명 여지는 보이지만 안전한 신규 제출·순익은 아직 입증되지 않았다는 경계를 유지한다.


### 10.7 구현·리뷰 인계 — 10/28

사용자는 P0-A/B/C와 비상시 P1의 병행 구현 및 리뷰 후 배포·재기동을 승인했다. 기준은 선택본 `f4cdac80647b71aae8f7d8ef5114ff5879c463cf`이며 격리 작업본은 `/home/ubuntu/KORStockScan-worktrees/entry-validity-20261028`이다. 다른 세션의 보유·청산·저장소 작업은 이 변경에 혼합하지 않는다.

- **P0-A:** 기존 `entry_deadline`이 confirmation에 결속된 유한 lifetime을 발급하고 ready/claim/AI/Main/physical 및 관측기가 동일 기한을 소비한다. 새 family 필드는 scope hash와 동일 정책 판정에 포함되며 장후·누적·joint/extended 등록 생산자가 보존한다. live 발급에는 PID·wall/monotonic 쌍을 결속한다. 재발급·다른 PID·회귀 시계로 기한을 연장하지 않는다. 별도 lifetime이 없는 봉인/현 정책은 원5초 계약으로 읽는다. **이번에 새 live 수명 숫자를 선택하지 않는다.** 6/8/12초는 격리 검증 값이다.
- **P0-B:** provider 직전 검증한 immutable 요청 definition을 그 응답의 decode에서 재사용하여 동일 registry의 후단 재로딩을 제거했다. 현재 revocation·정책·claim·원천/가격 검증과 raw/decoded durable 저장은 유지한다. decode·decoded 저장·normalization 및 응답 CPU 구간을 기존 로컬 계측에 추가하여 미확정 응답 후처리 지연을 추적한다. 실제 응답의 해당 decode 경계 51회 측정은 median3.866→0.807ms, p953.922→0.822ms다. 이 측정은 전체1.132초 원인이나 전체 제출 경로 속도 개선의 증거가 아니다.
- **P0-C:** 동일 bounded 힌트/selected stream·raw→selected projection에서 원 발급 기한을 소비하며 새 큐/worker/슬롯을 추가하지 않았다. 리뷰 중 추가한 pending 방문 토큰 보존은 기존 완료 후 rearm owner와 중복되어 제거했다. 실제 pending→완료→후속 claim 및 invalid/owner 변경 회귀로 기존 완료 우선 소비·rearm·Main 재검증·physical 이중 시계를 유지한다.
- **P1:** 이미 선택본에 있는 Q0/Q1/Q2 및 최초/재관찰 경로를 재사용하고 probe·제한된 원천 복구 예산을 발급 기한에 연결했다. 선택된 배분은 `current`, 장기슬롯/구독/패턴/모델은 변경하지 않았다. 같은 owner의 진행 중 source28 봉인·다음 PRE/REG 관찰을 중복 실행하지 않는다. 기존 동결 비교는 실제 점유5에서 추가배정0이며 가상 빈 슬롯 비교도 승패 U다. 코드 준비와 배분/패턴의 자연 성능 수용을 구분한다.

**재생의 범위:** 원 SHA를 인증한 만료9건, 원 provider 응답6건의 decode, 미호출3건의 실제 `analyze_target`→preflight→trace 종료를 재생한다. 9개 실제 경계 시각을 사용한 전체 physical adapter 회귀는 별도 격리 continuation fixture다. 당시 claim/수량/계좌/Main quote가 없는 구간을 성공 stub으로 채우지 않는다. 따라서 역사적 전체 경로 재생·복원 제출 건수·경제성은 미확정이며 수명 정책 선택 P2의 근거로 승격하지 않는다. [입력·계측·검증](../../tmp/entry-validity-implementation-20261028/).

**교체·제거:** 실행 수명의 분산 `epoch+5`는 기존 `entry_deadline`으로 `consolidated`; provider 후단 동일 definition 재로딩은 live v5/v6에서 `removed`, 원 historical/non-native reader는 named caller를 위해 `retained`; 원5초 confirmation/source clock·quote freshness·MAX_READY·outbox·첫 무효화 이력·manual/계좌/주문/수량/cooldown·hard safety는 `retained`. 새 모듈/worker/producer/CLI는 없다. 기존 준비 reader의 전체 source profile과 독립 reader 쌍을 갱신하고 원 발급 predecessor는 유지한다.

**운영 순서:** 최종 source/소비자 census 고정 → 원 active-parent native parity/인계 → 변경된 capability·trailing derived generation만 재생성 → 완전한 후보/독립 준비/P5 → native ordered 전환 → selected 준비/P5 → 실제 PID 정책 소비 → 현재 observer → full health. 실패하면 원 incumbent·정책·실패 기록을 보존하며 먼저 중지해 증거를 만들지 않는다. 현재 startup/health는 아직 이 절차를 실행하기 전이며 배포 완료를 뜻하지 않는다. PRE/NXT/_NX, REGULAR/SOR/_AL 자연 수용과 충분한 p99·비용 후 성능은 다음 창의 같은 checklist owner에 OPEN이다.
