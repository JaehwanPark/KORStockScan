# Main 보조판정 회로 복구·제출 증빙 연결 상세 보완계획 — 2026-10-12

상태: **10/12 18:30 원 계획의 리뷰 완료 후, 10/13 후속 승인으로 P0-A/B/P1 구현·코드 검증·배포를 실행했다. 최신 장후 인계·복구 최종화07:00:37 종료와 target13 기동 준비 전체 계약을 확인했다. 실제07:35/07:55 수용은 미래 Acceptance다.** 우선 정상 PASS의 제출 증빙 연결을 고치고, 같은 배포에서 AI 회로가 기한 소진으로 영구 중단되는 문제를 보완한다. 원 native 신호의 5초, 기존 정책·프롬프트·주문 안전 조건은 유지한다.

## 2026-10-13 승인 구현의 리뷰 보완

사용자의 후속 구현·등록·배포 승인에 따라 P0-A/B/P1을 구현했다. 본문의 미실행 표시는 원 계획 당시 기록이다. 현재 Main은 10/12 native EOD stop 이후 OFF이며 승인 구현 릴리스가 선택됐다. 실제 릴리스·회귀·장후·13 준비 영수증은 [후속 구현 리뷰](../audits/main-post-readiness-residual-and-pattern-research-review-2026-10-12.md)에 기록한다. 13 준비와 05:35 최종화까지 다시 검증한다.

- P0-A의 비교 정규화는 같은 시장 이름의 대소문자만 허용하고 raw revision/receipt는 유지한다. binder bool 호환 API에 call-local 실패 receipt를 추가하여 실제 submit caller가 첫 결손을 남긴다. ContextVar 밖에서 identity를 합성하지 않는다.
- P0-B는 원 entry deadline의 typed SDK timeout만 entry 회로에 귀속한다. 인증/권한·429·5xx·unknown은 기존 공통 fail-closed 처리에서 빠지지 않는다. allowlisted native/local 종료만 provider 실패에서 분리한다. endpoint circuit은 engine lock 안에서 단일 generation lease를 발급하고 같은 호출만 복구한다. 글로벌 `ai_disabled=False`로 복구하지 않는다.
- 제안 30/60/120/240/300초를 구현 상수로 명시하고 기존 실패 임계값 5·원 5초·provider/key retry·inflight 제한을 유지한다. 지연 응답/만료·cache/다른 endpoint 성공은 entry 회로를 해제하지 않는다. 실제 schema/semantic 검증된 응답만 복구 증거다.
- P1은 기존 bounded runtime receipt에 회로 generation/원인/대기 시각/미평가 횟수를 생산하고 같은 PID/start의 health consumer에 연결한다. detector는 report-only이며 reset·재기동·provider 변경 권한이 없다.
- 기존 완료 owner 전체를 다시 열지 않는다. 현재 13 checklist에는 새 결함 범위와 자연 acceptance만 단일 stable owner로 연결하고 native AUTO seal 밖에 둔다. 등록 정책 변경은 별도 explicit membership receipt로 결속한다.

## 1. 범위와 판단 근거

- [18:30 운영 점검](../../data/report/auxiliary_compact_adoption/2026-10-12/operating-status-1830.json)의 분모는 `native-readiness-20261012-v2`, commit `cf650549e7a07ed470cd95a500af43336d31232c`, PID `1215171`, start ticks `4182334`의 최신 기동부터 18:30까지다. 다른 PID의 결과를 합산하지 않는다.
- 기계 bundle `f7c1454a71b284a25c40a157ea4f42f390ecc5c21f362d76f497c49bf41ec2b1`, 보조 registry 128개 연결, 기계·보조 exact PID 소비와 bootstrap/handoff PASS를 확인했다. 보조 overlay가 null인 것은 base registry 승계이며 보조정책 미로딩을 뜻하지 않는다.
- 실제 AI 호출 69건은 유효 PASS 24, CAUTION 9, VETO 1, 전송 timeout 22, `response_invalid` 13건이다. 마지막 13건은 native 경로 변경 11, 원 기한/신호 변경 1, PASS support 계약 거절 1이다. 모두 AI 오판이나 JSON 불량으로 분류하지 않는다.
- 유효 PASS 24건의 최종 종료는 약한 눌림 보호 9, 수량계획 증빙 결손 9, 원 결과 기한 초과 3, latency guard 3이다. 증권사 주문 API 시작은 0건이다. PASS와 intent·submit·fill은 각각 집계한다.
- [계획 원천·분리 재현 근거](../../data/report/auxiliary_compact_adoption/2026-10-12/auxiliary-circuit-submit-receipt-plan-evidence.json)에 실제 attempt/trace, 제출 parent, source 해시와 재현 범위를 보존했다. 관련 코드 4개는 18:48 대조에서 작업본과 조사 릴리스의 바이트가 같았다. 이후 구현 시작 시 최신 selector/PID/코드를 다시 고정한다.

현재 계획은 [native claim·재검증 보완계획](main-native-signal-claim-and-auxiliary-revalidation-remediation-plan-2026-10-12.md)과 [고정·비고정 readiness 보완계획](main-fixed-nonfixed-signal-readiness-and-latency-remediation-plan-2026-10-12.md)의 후속 결손만 다룬다. 이미 배포된 event wakeup, native lifecycle, append receipt, exact PID 소비 구현을 다시 만드는 작업이 아니다. 별도 [잔여 병목·패턴 연구계획](main-post-readiness-residual-bottleneck-and-unidentified-pattern-research-plan-2026-10-12.md)의 패턴 등록·연구 및 장후 작업 owner를 유지한다.

| 구분 | 이번 기동의 실제 AI 호출 | 보완 적용 범위 |
| --- | ---: | --- |
| 삼성전자 `005930` | 0 | 공통 연결·회로 결함 회귀검증 대상. 자연 AI·제출 개선 실적은 미관측 |
| 주성 `036930` | 62 | 회로 중단과 제출 연결의 주된 관측 사례 |
| 알테오젠 `196170` | 3 | 최종 증빙 결손 PASS 1건을 포함하여 확인 |
| HPSP `403870` | 4 | CAUTION 3·timeout 1. PASS 제출 연결 개선 실적으로 합산하지 않음 |
| 두산 `034020` | 0 | 삼성과 같이 자연 호출 표본이 없으며 동작 부재의 원인은 별도 확인 |

관측 호출은 AFTERMARKET 사례다. 수정은 공통 소비 계약에 적용하되 PRE/REGULAR/AFTER와 고정/비고정을 별도 시험한다. 다른 시장의 미관측 결과를 성공으로 채우지 않는다.

## 2. 우선순위와 변경 소유자

| 순서 | 문제 | 수정 owner | 종료 시험 |
| --- | --- | --- | --- |
| P0-A | PASS의 `machine_action_receipt_absent` | `entry_attempt_identity` 연결과 `sniper_state_handlers` 제출·revision 소비 | 실제 identity 기반 fixture → call-local 연결 → revision 확인 → 기존 수량·분할계획의 정상/거절 경계 |
| P0-B | 원 신호 잔여 기한 timeout 5회 후 영구 AI 중단 | `ai_engine_openai`의 실패 소유권·회로 상태와 기존 transport admission | 원 기한/전송 여부를 구분하고 새 정상 기회에서 1회 복구; 불명 전송·인증 문제는 fail closed |
| P1 | 봇 heartbeat 정상인데 보조판정 중단이 health에서 드러나지 않음 | `runtime_performance` 생산 → `error_detectors/process_health` 소비 | 같은 PID의 circuit 상태·원인·미평가 횟수가 health에 표시되고 무권한 recovery 없음 |
| P2 | `trace_dedup_prepare` OSError 14건·lifecycle 미관측 40건 | 기존 trace/lifecycle 생산·append 관측 owner | exact 오류·구간 확인, identified source gap 분리, 원장 증식 없이 증빙 보강 |
| 별도 연구 | PASS 뒤 약한 눌림/latency 차단의 적절성 | 잔여 병목·패턴 연구계획의 기존 owner | 비용 후 30분 승패를 연결해 과차단 여부 판별; 이번 운영 수리의 등록 조건으로 추가하지 않음 |

P0-A를 먼저 재현·수리하여 회로 복구 후에도 같은 PASS가 다시 증빙 결손으로 막히는 상황을 제거한다. P0-B와 P1은 복구 동작과 그 관측 계약이므로 함께 검증한다. P2의 미확정 원인을 P0 수리의 효과로 계산하지 않는다.

구현 경계는 기존 [연결 함수](../../src/engine/monitoring/entry_attempt_identity.py), [Main 소비·제출](../../src/engine/sniper_state_handlers.py), [capture 생산자](../../src/engine/scalping/ai_decision_trace.py), [수량계획 소비자](../../src/engine/scalping/entry_execution_sizing_plan.py), [AI·transport owner](../../src/engine/ai_engine_openai.py), [성능/회로 관측](../../src/engine/monitoring/runtime_performance.py), [health consumer](../../src/engine/error_detectors/process_health.py)다. helper를 새로 만드는 경우에도 이 역할 경계를 따른다.

## 3. P0-A — 기계 PASS에서 제출 수량계획까지 증빙 연결

### 3.1 확인된 결함과 재현의 한계

1. `ai_decision_trace.capture_machine_observation()`은 원 snapshot의 `session_bucket`을 `market_session_bucket`으로 반환한다. 실제 사례는 `krx_nxt_aftermarket`이다.
2. `_machine_primary_entry_provenance_fields()`는 그 값을 보존한다. 고정 감시 stock의 시장 값은 `KRX_NXT_AFTERMARKET`이다.
3. `bind_submit_attempt_machine_lineage()`는 고정 감시 source와 stock의 시장 문자열에 완전 일치를 요구한다. 같은 의미의 대소문자 차이에도 False이며, 호출자는 연결 실패 이유를 남기지 않는다.
4. `_submit_watching_triggered_entry()`가 연결 반환값을 확인하지 않은 채 진행한다. `submit_attempt_machine_lineage()`가 빈 dict를 반환하면 원자적 수량계획 소비자가 `machine_action_receipt_absent`로 종료한다.
5. [수량계획 projection](../../data/report/auxiliary_compact_adoption/2026-10-12/operating-status-1830-sizing-summary.json)은 13행/10개 고유 attempt다. 최종 종료가 수량계획 차단인 것은 9개/관련 projection 12행이고, 나머지 1개는 최종 `latency_block`이다. 하나의 기회가 반복 점검된 행을 새 주문으로 세지 않는다.

10개 identity를 사용한 분리 binder fixture는 **원 대소문자 10/10 거절 → 같은 표기 10/10 연결**을 재현했다. 이것은 전체 submit 호출의 역사적 stock/runtime를 복원한 replay가 아니다. 실제 실행에서는 원 기한·revision·quote·broker·수량 검증도 남으므로, 9건을 수정 후 주문 또는 승리 9건으로 예측하지 않는다. 예를 들어 `aims-49ef84a3403d73ce5374`의 최종 종료는 원 async 기한을 약 0.15초 넘겼다.

### 3.2 구현 요건

- 원 machine observation, watch admission/generation, 원 session 문자열, bundle/trace/claim 해시는 바꾸지 않는다. 기존 시장 정의에 있는 **같은 명칭의 대소문자 차이만** 비교 시 정규화한다. AFTERMARKET/CLOSE_ONLY/TERMINAL_EXIT, PRE/REGULAR, KRX/NXT/SOR, broker route를 서로 합치는 alias는 허용하지 않는다. unknown/빈 값/충돌은 계속 거절한다.
- 기존 시장 정규화 owner의 사용 가능성을 먼저 확인한다. fixed-watch parent 비교, `_machine_submit_revision_is_current()` 및 sizing 소비가 동일한 의미 계약을 갖게 한다. receipt를 stock 표기로 덮어 native revision key와 새로운 불일치를 만들지 않는다. raw 비교 값과 정규화 결과를 관측 필드로 분리한다.
- call-local 연결은 **검증된 현재 async 결과의 immutable provenance**만 받는다. runtime 우선 선택, stock의 이전 PASS, in-call retry의 새 평가가 섞이지 않는지 통합 시험한다. 필드 보강이 필요하면 exact attempt/trace/source identity에서만 가져온다. AI PASS, 종목·시각 유사성 또는 마지막 stock 값으로 결손 증빙을 합성하지 않는다.
- 고정 감시는 native watch admission/generation을 parent로 사용하고 scanner promotion을 만들지 않는다. 비고정은 검증된 scanner parent를 유지한다. 두 origin이 동시에 있거나 symbol/venue/session/attempt/PID/generation/bundle/revision이 달라지면 fail closed한다.
- binder의 실패 이유와 실제 탈락 항목을 작은 구조화 결과로 노출한다. 기존 bool 호출의 호환성을 유지하되 제출 호출자는 빈 receipt로 계속 진행하기 전에 정확한 실패 terminal을 기록한다. `machine_action_receipt_absent` 일반 문구만 반복하지 않는다. ContextVar 없이 호출된 경로는 telemetry identity를 주문 권한으로 승격시키지 않고 거절한다.
- retry 시작 시 이전 PASS 연결을 지우는 현재 규칙을 유지한다. retry timeout/거절, 중첩 호출, 같은 종목 동시 요청 및 예외 종료 후 다른 호출로 receipt가 새지 않아야 한다.
- sizing owner는 기존 quantity allocator, price resolver, split resolver의 결과만 검증한다. 총수량·leg 수량 합·가격·cap·예약·custody를 동일하게 유지한다. 연결 진단과 sizing action receipt의 경계를 설명하고 observation ID 자체를 주문 허가로 사용하지 않는다.
- Main accepted → submit invocation → receipt bound/rejected → sizing valid/blocked → guard → intent → physical send → broker terminal을 exact attempt로 연결한다. durable dedup 및 불명 broker 응답의 기존 reconciliation을 보존한다.

### 3.3 회귀검증과 완료 기준

- 기존 `test_fixed_watch_submit_source_repair.py`와 `test_entry_execution_sizing_plan.py`를 확장한다. 수동으로 같은 시장 값을 넣는 binder 단위시험만으로 종료하지 않고 **capture 결과 → provenance projection → async Main 소비 → 실제 제출 wrapper → sizing** 경계를 fake clock/quote/account/broker로 시험한다.
- AFTER 대소문자 혼합은 정상 연결; PRE/REGULAR/AFTER와 fixed/scanner 정상 조합도 검증한다. 다른 시장·종목·parent·PID·generation·bundle·revision, captured 실패, PASS false, 기한 만료, quote stale/conflict는 broker send 0으로 종료해야 한다.
- 현재 9개 최종 결손 사례 identity의 재현에서 동일 시장 표기 문제를 제거한다. 이후 다른 guard가 거절하면 정확한 새 terminal로 보존한다. hard guard를 지워 sizing 정상 사례로 만들지 않는다.
- 정상 fixture는 원래 계산된 수량·분할가격과 동일한 계획에 연결되고 단일 실행 owner만 유지한다. 반복된 async result/같은 intent의 재방문은 broker send를 늘리지 않는다.
- 코드 완료는 위 경계의 원인 재현·수리·회귀검증이다. 자연 적용 완료는 새 PID의 정상 사례에서 receipt와 sizing 소비를 확인하는 것이다. 실주문·수익성은 별도 증빙이다.

## 4. P0-B — 영구 AI 중단을 복구 가능한 실패 계약으로 전환

### 4.1 확인된 현재 동작

`ai_engine_openai`는 공통 `consecutive_failures`가 기존 임계값 5에 닿으면 `ai_disabled=True`로 만든다. `_mark_successful_ai_call()`은 횟수만 0으로 바꾸고 disabled를 풀지 않는다. 확인한 코드에서 False 초기화는 engine 생성 시뿐이며, 자동 복구는 관측되지 않았다. entry 외 holding/flow 등의 호출과 transport allowed gate도 같은 상태를 참조하므로 영향 범위를 확인해야 한다.

원 native 무효화와 확인된 미전송 기한 종료는 이미 일부 중립 처리한다. 그러나 SDK 시작 후 원 기한을 소진한 timeout은 일반 실패에 누적된다. 마지막 연속 5회는 아래와 같으며 17:56:28부터 18:30까지 실제 새 AI 호출이 없었다. circuit-disabled 미호출 DROP trace는 36건이다.

| timeout KST | 배정된 provider timeout budget | 관측 provider 시간 |
| --- | ---: | ---: |
| 17:53:03 | 3,007ms | 2,979ms |
| 17:53:09 | 3,176ms | 3,163ms |
| 17:53:48 | 694ms | 681ms |
| 17:56:04 | 1,897ms | 1,881ms |
| 17:56:28 | 3,395ms | 3,375ms |

이 수치는 잔여 기한 소진과 영구 중단의 연결을 보여준다. 공급자 장애가 없었다는 증명은 아니다. `provider_sdk_started=True`도 물리 전송 확정이 아니므로 전송 불명을 미전송으로 바꾸지 않는다.

### 4.2 실패 소유권과 상태 전환

| 실패 소유권 | 처리 계획 | 금지되는 해석/동작 |
| --- | --- | --- |
| 확인된 local/native 종료: 원 기한, 신호 무효화, 미전송 취소, source/registry/계약 오류 | 해당 attempt는 정상 거절/결손 terminal. local 결함은 health/workorder에 남기고 provider 공통 실패와 분리 | local 오류를 정상 PASS로 만들거나 source 결손을 무시하는 것 |
| SDK 시작 후 원 기한 소진, 응답 불명 timeout | entry transport 회로의 실패로 남김. 기존 5회 임계값과 불명 future/예약 추적 유지; entry 범위에서 대기·단일 복구 | 모두 중립으로 지워 건강하다고 선언하거나 전송 불명 요청을 재전송하는 것 |
| 확인된 provider 인증/권한, rate limit, 서버/연결 오류 또는 원인 불명 오류 | 기존 provider fail-closed 범위를 유지. 알려진 상태로 구분하고 복구 가능 오류만 제한 복구; 인증/권한은 정상 재허용 근거 전까지 blocked | 복구 명목의 새 key/provider 변경 경로, 다른 endpoint로 우회, 실패 임계값 상향, blind reset |

구현 시 raw exception/type, 원 deadline, HTTP status의 가용성, adapter/SDK/response 단계, future cancelled/settled, transport·model·endpoint·PID를 함께 연결한다. 전송 계층에서 typed deadline 정보가 소실되면 보존하는 수정부터 한다. local/native **허용 목록 외 오류를 임의로 중립 처리하지 않는다.** 현재 승인된 transport/key retry가 있다면 같은 admission·기한 안의 기존 동작을 보존하며, 이번 회로 복구가 새 retry 권한을 만들지 않는다.

회로 기본안은 `CLOSED → OPEN → HALF_OPEN → CLOSED/OPEN`이다. 상태와 이름은 실패 회로의 의미이며 거래 방향/기계 ENTER 여부를 뜻하지 않는다.

1. 기존 실패 임계값 **5회**를 유지한다. 원 기한과 endpoint 실패를 provider 공통 장애와 혼합하지 않도록 범위를 명시한다. 실제 provider 공통 차단이 있으면 endpoint recovery lease보다 우선한다.
2. OPEN 동안 새 provider 호출을 막고 `not_evaluated_transport`와 circuit 원인을 남긴다. score 0/DROP의 호환 필드가 있더라도 AI VETO나 전략 차단으로 집계하지 않는다. 기존 cache 결과는 별도 current identity·native/TTL/semantic 검증을 통과해야 하고 회로 회복의 증거가 아니다.
3. 복구 가능 오류는 최초 **30초** 대기 후 다음 **새로운 정상 machine ENTER_NOW**를 HALF_OPEN 한 건으로 허용하는 기본안을 사용한다. 이는 제안 값이며 실제 설정값으로 취급하지 않는다. 실패하면 60→120→240→300초, 상한 300초로 대기한다. rate-limit 재시도 시각이 명시되면 더 긴 제한을 따른다. 기회가 없으면 호출하지 않는다.
4. 복구 호출은 기존 admission·동시성·호출한도·lock·provider/모델·원 신호 5초 안에서만 수행한다. 별도 ping/research/warmup 호출을 추가하지 않고 만료 claim을 되살리지 않는다. 남은 기한을 늘리거나 새로운 최소 잔여시간 진입 차단값을 넣지 않는다.
5. same circuit generation에 단일 recovery lease를 발급한다. `ai_disabled=False`를 잠깐 전역 설정해 모든 호출을 여는 구현은 금지한다. transport allowed gate는 그 exact request의 lease와 기존 safety/admission 조건을 모두 확인한다. 동시 요청·success callback은 같은 lock/state generation으로 처리한다.
6. 미정산 provider future가 있으면 기존 inflight/예약 제한을 유지한다. 취소 반환값만으로 SDK 미전송이나 물리 미전송을 추정하지 않는다. 늦은 응답은 현재 circuit generation/lease 및 원 deadline을 대조하며, 이전 응답이 새 회로를 풀거나 entry 권한을 복원하지 못한다.
7. HALF_OPEN의 검증된 정상 응답이 원 기한 내 도착하면 그 회로를 CLOSED로 전환한다. PASS뿐 아니라 정상 CAUTION/VETO도 transport 복구 증거다. 진입 허용은 해당 verdict와 native·submit 검증이 별도로 결정한다. schema/의미 오류, timeout, unknown은 그대로 해당 terminal과 실패 회로에 남긴다.
8. holding/exit와 entry의 failure 소유권을 조사하여 entry 기한 소진만으로 holding AI가 공통 중단되지 않게 한다. 확인된 공통 provider 장애는 분리로 우회할 수 없다. Main 기계 soft/hard/protect/emergency exit와 manual custody는 AI 회로 회복을 기다리지 않으며 기존 경로 그대로 검증한다.

상태·lock·실패 판단은 우선 기존 `ai_engine_openai`와 transport owner에서 보완한다. 별도 구성 요소가 불가피할 때만 `src/engine/ai/`에 둔다. 새 `src/engine` root 모듈, 별도 timer/worker, provider 교체와 연구 호출 증가는 이 계획의 구현 요건이 아니다.

### 4.3 시험과 완료 기준

- 기존 `test_ai_engine_openai_transport.py`와 `test_reversal_auxiliary_wire.py`에 fake clock/future/provider를 사용한다. 실제 API 호출은 필요 없다.
- 마지막 5개의 694~3,395ms budget을 고정해 현행 영구 중단을 재현하고 candidate에서는 entry OPEN 후 새 적격 기회 한 건으로 복구되는지 확인한다. 원 deadline 후 결과는 모두 entry/broker 0이어야 한다.
- SDK 전 미전송 취소, SDK 후 전송 불명, 401/403·429·5xx/unknown, 정상 VETO/CAUTION, schema 불량, 늦은 응답, 병렬 HALF_OPEN 경쟁, lock 경합·engine 종료를 시험한다. 기존 failure threshold·retry/admission·호출한도가 달라지면 실패로 본다.
- stale cache/이전 PASS/다른 endpoint 응답이 회로를 잘못 풀지 않아야 한다. entry timeout의 endpoint 분리는 보호 exit·provider 공통 차단의 회귀시험과 함께 완료한다.
- 구현 결과 보고에서 `circuit repair implemented`, `selected release`, `PID consumed`, `natural HALF_OPEN recovery`, `entry accepted`, `order terminal`을 각각 표시한다. 복구 기회가 없으면 `natural_acceptance_pending`으로 남기며 재기동 성공을 회로 복구 성공으로 대체하지 않는다.

## 5. P1 — 의미적 health와 정확한 종료 연결

- 현재 `runtime_performance.observe_ai_circuit()`는 enabled/disabled, 횟수, 관측 시각만 생산한다. 같은 PID circuit 상태를 기존 health consumer에 연결하고 `scope`, `state`, `opened_at`, `reason`, `failure_owner`, `last_success_at`, `next_recovery_eligible_at`, `half_open_inflight`, `unsettled_provider_requests`, `disabled_noncall_attempt_count`, PID/start ticks를 최소 필드로 기록한다. 민감한 key·prompt·payload는 저장하지 않는다.
- 실제 consumer 연결은 `runtime_performance.log_snapshot()`의 기존 발행 주기에서 PID/start ticks를 포함한 **최대 16KiB 최신 상태 JSON 한 개**를 atomic replace로 발행하고 `process_health`가 현재 PID용 경로만 읽는 안으로 고정한다. 위치는 `data/runtime/ai_circuit_status/<pid>-<start_ticks>.json`이다. endpoint/scope는 고정 허용 목록으로 제한하고 과거 event/history를 상태 파일에 쌓지 않는다. producer 관측 시각이 두 번의 발행 주기를 넘거나 identity가 다르면 stale/unobservable이며, 행 부재를 healthy로 채우지 않는다. status 파일 쓰기 실패는 기존 bounded 관측 실패로 보고하고 주문 실행 결과를 바꾸지 않는다.
- 판정 결손 경보는 exact request → receipt bound/rejected → sizing terminal을 소비한다. `session_spelling_mismatch`, parent/revision/기한 결손을 구조화된 실제 탈락 근거로 표시하며, 지표 수를 늘리는 자체 목적의 분류를 만들지 않는다.
- 현재 PID의 health가 heartbeat 정상만으로 AI 정상이라고 읽히지 않게 한다. 회로 중단은 보조판정 가용성 저하로 표시하고 process 살아 있음, 원천 유효성, AI 호출 가능성, 제출 가능성을 분리한다. 다른 PID/오래된 snapshot이면 `unobservable/stale`다.
- 경보는 동일 PID/scope/generation에 한 번의 발생과 상태 전환·회복만 묶어 반복 폭주를 방지한다. recovery action은 진단 안내이며 detector가 bot restart·circuit reset·key/provider/threshold 변경을 수행하지 않는다.
- 기존 bounded observation queue/append receipt를 재사용한다. per-tick 파일 전체 읽기, hot path 동기 fsync, 별도 거대 원장·response clone·비교용 AI 호출을 만들지 않는다.
- detector/운영 규칙을 실제로 변경하는 후속 구현에는 해당 운영 문서와 candidate checklist도 같은 change set으로 반영하고 targeted detector 시험을 수행한다. 이번 계획 작성으로 운영 규칙을 바꾸지 않는다.

## 6. P2와 보호조건 연구의 제한된 후속

### 6.1 trace/lifecycle 결손

18:29:38 성능 snapshot은 warm loop 4,005회, p95 0.907초, p99 2.307초, max 6.081초, 5초 초과 1회다. append는 완료 1,198 = 확인 1,198이며 관측 envelope 결함 재발은 없었다. selected native lifecycle의 미관측 40건과 `trace_dedup_prepare` OSError 14건은 별도 결손이다.

- OSError는 정확한 errno/path/inode/generation/sidecar/lock 상태를 기존 작은 오류 근거에서 확인한다. disk 증가·권한·파일 교체·index 세대 경쟁 중 어느 원인인지 확인 전 임의 unlink/재생성하지 않는다.
- lifecycle 40건은 exact signal/cell/family/PID/원 기한에 해당하는 생산·종료 receipt를 연결한다. 복원 불가 행은 미관측으로 보존하고 유효 기회의 전달 실패 또는 승리 기회로 세지 않는다.
- 최대 16MiB suffix와 기존 분 단위 partition/index/작은 보고서를 사용한다. 한 사례의 요청·response·대형 원장 복제본을 추가하지 않는다. 완료 산출물은 identity/hash/필수 시계·탈락 조건만 보존한다.
- P0/P1의 targeted checks가 닫히면 정확히 특정된 P2 결손은 기존 원천 owner로 이어간다. 관련 hard source 계약을 완화하거나 P2 해결을 꾸며 P0 배포 PASS로 만들지 않는다.

### 6.2 약한 눌림·latency 차단

PASS 뒤 약한 눌림 9건과 latency 3건은 현행 보호조건의 실제 종료다. 과차단인지 확인하려면 원 decision 시점의 실행 가능한 quote·비용과 30분 경로를 연결한다. **soft stop −3% 선도달 없이 비용 후 +0.4%를 30분 내 도달**한 binary 결과를 삼성/비삼성, PRE/REGULAR/AFTER 및 비삼성 종목 유형별로 집계한다. 30분 이후 도달은 후순위로 분리한다.

원천 결손·비용 불명·경로 시간 순서 불명·관측 종료로 censored된 행은 유효 승패 분모에서 제외하고 제외 수를 별도로 보존한다. 같은 bar 안의 선도달 순서를 알 수 없으면 승리로 채우지 않는다. 외부 원천은 시각·시장·비용 계약이 호환될 때만 보강한다. PnL은 기존 COMPLETED/valid profit_rate 규칙을 따른다. 이번 연결·회로 수리는 이 연구의 EV나 실주문 발생을 코드 완료 요건으로 추가하지 않는다.

보호조건 후보는 별도 기존 연구 owner가 제시한다. 이번 구현에서 weak-pullback·latency·CAUTION micro-confirmation·numeric score·quantity 조건을 동시에 완화하거나 retired score-only 진입 관문을 복원하지 않는다.

## 7. 구현·리뷰·검증 순서

| 단계 | 구체 작업 | 남길 결과 |
| --- | --- | --- |
| R0 | 최신 selector/PID/start ticks·source hash·policy/manifest·현재 owner를 다시 고정 | 오늘 18:30 분모와 새 구현 baseline 구분; unrelated dirty 변경 보호 |
| R1 | P0-A capture/projection/async/submit/sizing 통합 재현과 제한 정규화, 연결 실패 terminal 보강 | before/after fixture, raw/normalized 값, 모든 safety negative send 0 |
| R2 | P0-B 실패 소유권·단일 recovery lease·late future·endpoint/provider 공통 우선순위 구현 | 고정 budget/동시성 시험, 보호 exit 및 provider 차단 비퇴행 |
| R3 | P1 circuit·receipt health consumer 및 transition dedup | 같은 PID의 중단/대기/복구/결손 표시와 detector mutation 0 |
| R4 | producers/consumers·silent failure·source stale·재시도·권한 경계 self review → 수정 → 재리뷰 | 검토 범위의 unresolved defect 0과 targeted validation |
| R5 | 허용된 통합 릴리스 준비·ordered handoff·실제 PID 확인 | 정책/manifest 보존, 정확한 배포·소비 영수증 |
| R6 | 다음 정상 신호의 자연 소비를 확인 | circuit 회복 → PASS/CAUTION/VETO → Main → receipt → sizing → intent/submit/terminal 구분 |

필수 검증은 영향을 받는 위 pytest, 기존 native claim/async 소비·receipt tests, Python compile/import와 `git diff --check`다. wrapper를 수정하면 `bash -n` 및 wrapper contract 시험을 추가한다. 문서/checklist는 링크·단일 owner·권한과 print-only parser로 검증한다.

성능은 동일한 고정 입력·기회 수·요청 수·queue/append 분모와 기존 admission으로 before/after를 비교한다. CLOSED/OPEN/HALF_OPEN 각각의 로컬 처리·provider 대기·Main commit·submit guard를 분리한다. 원 5초를 초과한 결과는 실행 불가다. 작업·호출·관측을 버려 빨라진 결과는 개선으로 인정하지 않으며, binder 단위시험이나 위 운영 snapshot만으로 전체 Main+장후 성능 PASS를 선언하지 않는다.

## 8. owner·배포·재기동·rollback 계약

- [오늘 checklist](../checklists/2026-10-12-stage2-todo-checklist.md)의 기존 OPEN 3개와 16:30~21:40 장후 일정은 유지한다. 문서에 계획을 적은 것은 실행 owner를 OPEN하거나 오늘 장후 산출물의 strict hash를 변경한 것이 아니다.
- 구현 지시 시 P0-A의 새 AFTERMARKET 표기 결함은 완료된 stable ID `MachineAuxiliaryPathRepair1012`의 해당 범위만 명시적으로 reopen한다. P0-B/P1은 `AuxiliaryCircuitRecoveryRepair1012` 하나의 신규 owner에 구현·health·자연 수용 acceptance를 묶는 안이다. 기존 `OrderedIntradayDeploymentRepair1012`는 ordered handoff 계약을 재사용하고, 이미 완료된 다른 native/readiness/auth 작업은 다시 열지 않는다.
- Due/Slot/TimeWindow/Track은 구현 시작 시 실제 KST에 맞춰 candidate checklist에 등록한다. 그날 장중 완료가 불가능하면 원 날짜·이력·남은 자연 acceptance를 보존해 다음 영업일 owner로 전달한다. prose 링크만으로 executable handoff를 대신하지 않는다.
- live checklist·sealed summary/strict/controller 입력은 기동 중 직접 덮어쓰지 않는다. 기존 ordered deployment owner를 통해 candidate bytes와 prerequisite·rollback을 검증한 뒤 authorized stop/publish/start 순서로 전환한다. 소스 문서 변경 때문에 `strict_checklist_generation_stale`이 발생하지 않도록 affected strict/checklist/terminal generation을 실제 마지막 consumer까지 확인한다.
- 후속 구현·배포는 사용자 실행 지시와 현행 승인 범위에 따라 수행한다. 이번 계획 요청 자체로 PID stop/restart, circuit 수동 reset, 운영 env/lock/provider/threshold/order 변경 또는 장후 재실행을 수행하지 않는다.
- 새 릴리스는 기계/보조 bundle·registry·prompt/model·provider route와 기존 원 기한/admission·TTL·수량·cap·custody·manual/hard guards를 보존한다. 정책 변경이 검출되면 P0 수리와 분리하여 해당 owner로 돌린다. 불명 open order/intent는 기존 broker reconciliation owner가 처리하고 새 호출로 재전송하지 않는다.
- restart는 회로를 정상화했다는 자연 증거가 아니다. 선택 릴리스, 실제 PID cwd/start ticks, bootstrap/handoff, 기계·보조 exact PID consumed를 먼저 확인한다. 자연 HALF_OPEN/PASS/제출은 다음 실제 신호로 별도 확인한다. 이후 날짜에는 exact-date PREOPEN·PID 증빙을 새로 확인한다.
- rollback 기준은 잘못된 parent 연결, 다른 시장/native revision 수용, 만료 결과 재사용, 중복 send, 보호 exit 영향, provider/호출한도 우회, unsupported circuit unlock, observation queue 결손 증가 또는 strict handoff 실패다. 마지막 검증 릴리스·정책을 기존 ordered 절차로 되돌린다. 이미 발행된 broker intent/불명 terminal은 삭제하지 않고 exact reconciliation을 유지한다. retired widget/episode가 있는 과거 경로로는 복귀하지 않는다.

## 9. 완료 판정과 결과 보고

1. **계획 완료:** 발생 코드·실제 근거·재현 한계·수정 범위·negative tests·단일 owner/배포 경계가 일치하고 문서 검증이 통과한다.
2. **구현 완료:** P0-A/B/P1의 in-scope review finding 0, targeted tests/compile 통과, 안전 조건·정책·호출한도 보존. 유효 receipt 및 한 건 recovery lease가 실제 consumer까지 전달되는 fixture를 갖춘다.
3. **배포 완료:** 새 선택 릴리스와 실제 PID identity/소비·bootstrap/strict handoff가 같은 세대다. 문서 PASS나 workspace diff를 배포 증거로 사용하지 않는다.
4. **자연 수용:** 새 정상 신호에서 circuit 복구와 receipt→sizing 경로가 관측된다. guard 차단은 exact 원인으로 남긴다. 자연 표본이 없으면 pending이며 주문·수익을 만들어 수용을 채우지 않는다.
5. **효과 검토:** 삼성과 비삼성을 분리하여 호출/미호출, 유효 PASS, Main accepted, receipt bound, sizing valid, intent, physical submit, broker accepted/fill/terminal을 고유 attempt로 비교한다. 기존 9건의 재전송이나 반복 행을 새 기회로 세지 않는다. 승률·순이익/EV는 유효 후행 결과와 기존 비용 계약의 별도 평가다.

이번 계획은 문서만 수정하고 약 7.4KiB의 원천·분리 재현 근거를 추가했다. 계획 self review에서 raw/native key 보존, 반복 행과 최종 terminal의 분모, 단일 recovery lease, 보호 exit 비퇴행, health 실제 consumer·저장 상한, 기존 key retry 보존을 보완했다. 로컬 링크와 print-only parser 검증은 통과했고 오늘 checklist의 OPEN 3개를 유지했다. parser의 나머지 runbook/4월 reference 행은 이 계획의 새 실행 owner나 현행 수리 근거로 채택하지 않는다. 운영 코드·정책·PID·provider·broker·cron·장후 원장은 변경하지 않았다. 코드 시험·배포·자연 수용과 경제성 검증은 이번 문서 작업에서 실행하지 않았다.
