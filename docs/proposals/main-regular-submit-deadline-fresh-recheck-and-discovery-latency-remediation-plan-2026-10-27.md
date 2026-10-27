# 정규장 제출 시간 소진·fresh 재평가·일반종목 감시 지연 보완계획 — 2026-10-27

## 1. 결정과 실행 기준

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
