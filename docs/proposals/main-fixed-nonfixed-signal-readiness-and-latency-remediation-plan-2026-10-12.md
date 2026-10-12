# Main 상시·비상시감시 신호 전달·입력 준비 상세 보완계획 — 2026-10-12

상태: **계획 리뷰·보완, 작업본 구현·코드리뷰·수정 반복 완료. 최종 통합 회귀 1,462건 통과. 후속 재리뷰·추가 수리 후 16:46 통합 배포·재기동 완료, PID 1171338 소비 검증 PASS.** 목표는 현재 등록 정책으로 평가할 수 있는 신호가 준비·전달 결함 때문에 사라지는 경로를 보완하고, 정상 패턴 부재와 실제 원천 결손을 정확히 구분하는 것이다. ENTER_NOW·PASS·주문 건수 증가 자체를 수리 완료 조건으로 사용하지 않는다.

## 1. 적용 범위와 기존 계획의 관계

- [점검 보고서](../audits/main-machine-signal-lifetime-and-nonfixed-readiness-review-2026-10-12.md)의 상시감시와 비상시감시 발견을 함께 처리한다. 삼성·두산·주성·알테오젠·HPSP와 일반 탐색을 구분하며, PRE/REGULAR/AFTER와 exact item/route/session별 원천을 합산하지 않는다.
- [Main native 신호·보조 재검증 계획](main-native-signal-claim-and-auxiliary-revalidation-remediation-plan-2026-10-12.md)의 **S0·S1·S2·S3·S4·N0·N1 ID를 재사용**한다. Main 신호 수명·최종 재검증·관측 저장·후행 평가의 상세 계약은 해당 계획이 소유한다. 이 문서는 비상시 **N0·N1을 구체화하고 N2 원천 진단 및 전체 통합 수용**을 정한다. 같은 기능의 별도 구현·원장·자동 실행 owner를 만들지 않는다.
- [비상시 native 관측·Main 인계 계획](main-nonfixed-native-signal-observation-and-consumption-remediation-plan-2026-10-08.md)의 NS0~NS5와 [잔여 병목 통합계획](main-residual-capacity-budget-pass-history-bottleneck-implementation-plan-2026-10-08.md)의 완료 구현을 출발점으로 삼는다. source refresh, 비소비 probe, Main inbox/completion wakeup, scanner panel worker, exact WS lease 및 기존 cleanup을 다시 설계하지 않는다.
- 현재 [일일 체크리스트](../checklists/2026-10-12-stage2-todo-checklist.md)의 완료 ID `MachineAuxiliarySignalDeliveryRepair1012`, `NonfixedDispatchReadinessReview1012`는 과거 코드 수용 증거다. 이번 새 결함을 후속 구현 범위로 연결하며 완료 증거를 지우지 않는다. 현재 PID에 봉인된 체크리스트는 계획 작성 중 변경하지 않는다. 실제 실행 항목·시간창·Acceptance는 구현 착수 때 현행 owner에 결속한다.
- Main-only, 퇴역 widget/episode·역사 custody·manual veto를 보존한다. 원 5초 신호 예산, source/quote freshness, 계좌·주문·수량·cap·cooldown·hard safety, provider/model 및 요청 한도는 이번 보완의 변경 축이 아니다.

착수 시 [선행 구현 리뷰](../audits/main-native-signal-claim-implementation-review-2026-10-12.md)의 S0/S1/S3 및 기본 N0/N1 구현을 대조해 재사용했다. 이번에는 준비 세대의 callback/worker 재검증, 실제 가격대의 branch descriptor, 0B/0D 시계, 최초 eligible wakeup, probe execution projection을 보완한다. §2는 조사 당시 릴리스 기준이며 진행 중 작업본 전체의 최신 코드 상태를 주장하지 않는다.

## 2. 근거와 해결할 결함

조사 PID는 `981118` / start ticks `3253591`, 릴리스 `deployment-detector-20261012-v1`이다. Main 사례는 14:38의 네 attempt, 비상시 census는 **14:33:30~14:52:48**이다. 조사 중 새 PID `1020707` / `auxiliary-consumption-attestation-20261012-v1`로 전환됐음을 14:59:23에 확인했다. 아래 수는 조사 PID 실적이다. 구현 시작 시 selector·실제 PID/start/cwd·정책/코드 해시를 다시 고정한다.

| 발견 | 직접 근거 | 보완의 성격 |
|---|---|---|
| selected native 34 = claimed 4 + 시간 경과 표시 30 | `expired_before_claim`은 epoch+5초로 계산하며 실제 ready 제거 사유를 보존하지 않음 | S0: 수명 증빙과 정확한 분모 |
| ENTER_NOW·AI PASS 1건이 Main에서 거절 | `aims-9695ea7e635b1469a30b`, 신호 후 4.648초에 path changed, 원 예산 약 0.353초 잔여 | S1: 실패 predicate·원 receipt 보존. 만료나 주문 실패로 재분류하지 않음 |
| 짧은 신호가 Main까지 늦게 도착할 여지 | native→claim 최대 2.596초, fixed native-ready와 Main completion wait 직접 연결 없음 | S2: 정확한 eligible 구간을 기준으로 전달 지연 보완 |
| 비상시 고유 예약 126 = 종료 121 + 진행 5 | 기계 completed ENTER/RECHECK/BLOCK 0 | N0·N1·N2: 계산 전 준비 경로 수리 |
| 기동 직후 `runtime_dependency_missing` 5 | subscriber만 확인한 scanner와 WS_MANAGER·AI_ENGINE·token을 요구하는 probe의 차이 | N0: 실제 의존성 준비 확인. 결손 객체는 아직 미확정 |
| residence 종료 50 = 정상 FALSE 40 + UNKNOWN 10 | UNKNOWN 9건은 60초 이력·known FALSE→TRUE·1초 hold branch, 연속 관측 18.56~58.64초 | N1: 기존 60/150초 슬롯 배정과 필수 입력 준비 연결 |
| source 종료 66 | route snapshot 없음 21, 0B 없음 22, 0B age 초과 19, 준비 경계 age 초과 4 | N2: lease·수신·native publish·quiet 구간 증거 연결 |
| RECHECK의 tape stale | 0B 3,253.47ms / 기존 한도 3,000ms, 0D 335.13ms | N2: 체결·호가 시계 분리. 새 호가로 체결 freshness를 대신하지 않음 |
| 응답 로컬 비용의 원인 미분해 | PASS transport 1.427초, response_validate .721초, 준비 .809초, 캡처 append 최대 .183초 | S2·S3: 비중첩 시계 후 확인된 중복 작업만 축소 |

정상 FALSE 40건은 기존 `_probe_verified_no_match`로 검증됐다. 실행 기회·기계 BLOCK·AI 실패 분모로 바꾸지 않는다. source 종료 66건도 체결 희소·경로 문제·실제 수신 지연을 대조하기 전에는 API 장애로 확정하지 않는다. Main 네 건의 원 시계와 probe lease 분모를 합쳐 손실 기회 수를 만들지 않는다.

## 3. 구현 순서와 산출물

| 순서 | 단계 | 변경과 산출물 | 완료 기준 |
|---|---|---|---|
| 0 | 공통 기준 고정 | exact 현재 코드/정책/신원, 네 attempt 및 121 terminal의 작은 fixture, 영향 caller 목록 | 과거·현재 PID와 원천 범위 분리, 정책/guard baseline 고정 |
| 1 | S0·S1 + 필요한 S3 | 신호 생성·종료·Main 방문과 최종 native 실패 receipt를 기존 projection에 연결 | 동일 신호/attempt의 생성→처리→종료 대사, 상세 미관측 명시 |
| 2 | N0 | queue claim 전 effective readiness와 실제 callback 재확인 | 준비 전 물리 미실행 예약 소모 0, 경합·cleanup 단일 소유 |
| 3 | N1 | branch별 입력 준비 descriptor, 기존 긴 슬롯 배정·대기 | 60초+확인 유형의 구조적 단기 배정 문제 해소, 한도·공정성 유지 |
| 4 | N2 | exact lease의 source 시계·sequence·first-data·quiet 연결 | 0B/0D/route 결손의 첫 단절과 미입증 원인 구분 |
| 5 | S2 | 유효 native-ready wakeup, 확인된 준비/검증 중복 비용 축소 | 같은 유효 신호 도달 시간 개선, 기존 판정/대상/저장 보존 |
| 6 | 통합 리뷰·검증 | fixed/nonfixed·복수 branch·서로 다른 시장·재기동/경합 fixture | 실제 caller의 원 예산·단일 소비·cleanup·guard parity 통과 |
| 7 | 후속 적용·자연 확인 | 기존 ordered 배포·PID 소비 및 bounded 자연 창의 별도 영수증 | 코드/로드/자연 경로를 각각 판정. 현재 계획 실행과 구분 |
| 8 | S4 연구 인계 | 충분한 입력으로 정상 불일치한 유형과 정상 FIRST 무효화 사례 | 누적 기존 원천으로 후보 비교. 이번 source 수리 완료와 독립 |

S0·S1·N0는 우선 구현한다. N1은 N0와 source 연속성 계약을 닫은 뒤 적용한다. S2의 scheduler 변경은 S0로 실제 유효 시간과 Main 방문 지연을 확인한 경로에 적용한다. 정상 FALSE 40건을 ENTER로 만드는 목표는 S4의 수동연구 과제이며 이 구현에 임계값 완화로 넣지 않는다.

## 4. 공통 신원·시계·저장 계약

### 4.1 신원과 시간 경계

1. 원천 기준 key는 `date/PID/start_ticks/release/bundle/family/scope_hash/symbol/item/route/session/native_epoch/signal_id`다. branch membership은 같은 opportunity 안에 보존한다. probe는 추가로 discovery `source_sha256/claim_count/physical_probe_lease_id/interval_generation`을 결속하고 observer→Main live attempt 관계를 명시한다.
2. `source_received/native_ready/main_visit/claim/prepare/input_freeze/http_start/http_end/worker_done/main_revalidation/terminal`은 wall clock과 같은 PID monotonic을 구분한다. wall clock 역행·worker 전달·context 재생성으로 원 deadline을 늘리지 않는다. source provider clock, receive clock, Main read clock을 서로 대체하지 않는다.
3. 신호의 5초 deadline과 probe의 60/150초 residence는 별도다. 장기 관측 안에서 신호가 생겨도 실행에는 **그 신호의 원 5초**가 적용된다. 결과 생성·inbox 도착·재구독 시각을 새 신호 epoch로 쓰지 않는다.
4. FIRST 유효성 변화의 정확 시각이 없으면 마지막 valid~첫 invalid 구간과 관측 coverage를 남긴다. age 증가만으로 `valid_until_deadline`을 합성하지 않는다. 과거 30건과 이전 PID를 현재 state로 성공/실패 보충하지 않는다.

### 4.2 저장·consumer

- 기존 `runtime_performance`의 유한 ring과 분 단위 execution/pipeline projection을 사용한다. event/lease의 준비·전이·종료에만 작은 capsule을 저장하고 매 tick 전체 stock/claim/AI payload를 append하지 않는다. 현재 4,096개 selected ring의 상한을 확대하지 않는다.
- callback→writer→append receipt→reader allowlist→monitor 요약을 하나의 계약으로 검증한다. callback 반환이 `None`이면 필수 append가 확인됐다는 의미를 부여하지 않는다. 정상 skip·실패·확인 불가를 S3 정의에 맞춰 구분한다.
- 중복 관측은 key와 phase/sequence로 coalesce한다. overflow·eviction·partial tail·회전·write 실패는 coverage/미관측으로 대사한다. 원 mandatory append/outbox 실패의 기존 차단 의미는 유지하고 선택적 진단 실패를 새 주문 veto·retry로 사용하지 않는다.
- native lock에서는 작은 immutable 필드만 복사한다. disk·hash·full JSON·provider 작업은 lock 밖에서 한다. callback·Main·scanner·diagnostic lock의 실제 순서를 caller별로 표로 고정하고 역순·대기 중 I/O를 회귀로 검사한다.
- diagnostic 필드는 `decision_authority=none/report_only`, 원 source quality·미관측 의미를 유지한다. 표시용 상태가 queue slot 해제, native claim, AI PASS, 주문 권한을 갖지 않는다.

## 5. S0·S1 — 신호 수명과 Main 최종 거부 증빙

상세 상태 계약은 [기존 계획 §4~§5](main-native-signal-claim-and-auxiliary-revalidation-remediation-plan-2026-10-12.md#4-s0--미claim-분류-보완)를 따른다. 이번 통합 구현에서는 다음 연결을 실제 caller에서 닫는다.

| 생산 경계 | 보존할 사실 | 소비 경계 |
|---|---|---|
| native ingress/선택 관측 | raw ready와 실제 eligible 구분, event/branch/scope·sequence·원 deadline | performance의 같은 opportunity |
| turn 종료·교체·source interval 종료 | 마지막 eligible~첫 invalid 시각, surviving branch, 실제 확인된 원인 | claim 전 종료 capsule. hook 부재면 미관측 |
| Main 첫 방문·claim 시도 | visited/claimed/거부/원 예산, 선택한 exact event | 같은 native opportunity의 disposition |
| `validate_claim_with_receipt` 실패 | 이미 예외에 붙은 `reversal_source_receipt`, 검증 시각·failed predicate | `_resolve_scanner_async_entry_ai`의 최종 disposition writer |
| writer→monitor | 상세 receipt의 작은 hash/ref·failed fields, accepted/rejected/deferred/미관측 | exact attempt terminal. 반복 sentinel 행 중복 집계 금지 |

Main에서 `str(exc)`만 남기는 경로에 allowlist projection을 연결한다. 원 claim registration과 현재 검증 상태는 별도 시점이다. 현재 ready 소멸을 claim 생성 당시 source 결손으로 소급하지 않는다. v6 envelope와 carried backend generation을 구분하고 다른 branch가 살아 있는 경우 실제 native 선택/재검증 계약을 대조한다.

영수증 저장만으로 native 결정은 변경되지 않는다. 중복 result 수거·request 교체·late callback·ack 실패에서도 원 terminal을 덮거나 새 claim을 실행하지 않는다. `worker_completed`, Main 결과 수거, `first_ai_wait`, intent, physical submit은 별도 단계로 남긴다.

정확 cohort의 보존식은 **고유 observed opportunity = claimed + 확인된 claim 전 terminal + as-of pending + 미관측**이다. expired·invalidated·replaced 등 상세 원인은 S0 정의를 사용하고 같은 사건을 여러 terminal에 더하지 않는다. 원 30건의 상세 자료가 없으면 역사 미해결로 남긴다.

## 6. N0 — 실제 준비된 consumer에서만 새 probe 시작

### 6.1 소유 코드와 readiness receipt

- [discovery runtime](../../src/scanners/zero_base_discovery_runtime.py)의 `dispatch_due_probes`가 admission을 소유한다.
- [Main](../../src/engine/kiwoom_sniper_v2.py)의 현재 probe subscriber·WS/AI 초기화·종료 경계가 읽기 전용 readiness 정보를 생산한다. scanner가 다른 module의 전역을 임의 추측하거나 계좌/인증 API로 readiness를 확인하지 않는다.
- [probe](../../src/engine/scalping/zero_base_probe.py)의 실제 시작 경계가 동일 의존성을 재확인한다. machine-only probe의 현재 의존성은 유지하고 AI 객체 존재를 provider 호출 권한으로 해석하지 않는다.

필드: `schema/PID/start/date/runtime_generation/route/session/observed_epoch`, `subscriber_present`, `consumer_open`, `ws_manager_present`, 기존 WS 연결·epoch 준비, `ai_engine_present`, `token_present`, 기존 REST/WS 설정의 인증 환경 일치(토큰 발급 증명과 구별), `machine_policy_ready`, `first_missing_dependency`. token·계좌·키의 값은 기록하지 않는다. 정책 확인은 기존 preload/검증 결과를 재사용하고 dispatch마다 전체 정책 graph/hash를 새로 만들지 않는다.

receipt의 freshness와 invalidate 범위는 현재 초기화·reconnect·정책/날짜 변경·close 경계로 결속한다. elapsed만으로 건강을 추정하지 않는다. **새 후보 item의 0B/0D 수신은 probe 시작 readiness에 요구하지 않는다.** 실제 lease를 얻기 전에 해당 원천을 요구하는 순환 대기를 만들지 않는다.

### 6.2 admission과 경합 처리

1. 현재 subscriber 확인에 effective readiness를 함께 적용한다. 미준비면 신규 dispatch를 defer하고 원 candidate를 보존한다. probe `claim_count/in_flight/residence_deadline`을 새로 소비하지 않는다. source discovery의 freshness·next_due와 기존 순환 정책은 그대로 적용한다. readiness 실패는 신규 admission에만 적용하며 기존 result/ACK 수거·만료 대사·cleanup·필수 persistence는 계속한다. 미준비 때문에 물리 슬롯 정리를 멈추지 않는다.
2. readiness PASS 뒤 queue claim과 durable persist가 완료된 다음에만 현재 EventBus 전달을 실행한다. persistence 실패의 기존 rollback·단일 queue writer 계약을 유지한다.
3. publish와 실제 callback 사이의 reconnect/close/token/AI 초기화 변화는 원 readiness generation과 consumer 재확인으로 대사한다. 미실행이 입증된 요청만 기존 미전송 해제 경로로 정리한다. 등록 전 실패·등록 전송·ACK 불명·cleanup pending을 혼동하지 않는다.
4. 실제 REG 요청 가능성이 있거나 cleanup 미완료인 lease는 기존 physical ACK가 슬롯 반환을 소유한다. 빠른 재시도를 위해 슬롯·claim generation을 임의 초기화하지 않는다. late result/ACK가 successor lease를 해제하지 않도록 exact lease/generation을 검사한다.
5. readiness가 회복됐을 때 기존 scanner wakeup을 사용한다. 새 busy polling·추가 worker·토큰 refresh 강제 호출을 만들지 않는다. 날짜/close 뒤 남은 receipt를 새 scanner에 승계하지 않는다.

종료 기준: 초기 의존성 각각 누락·모두 준비·확인 직후 변화·subscriber 소실·중복 callback·persist 실패에서 **전송 전 무의미한 예약 소비 0, uncertain 슬롯 조기 반환 0, 중복 probe 0**. 자연 기동 5건과 steady-state 결손을 분리한다. 실제 실패 dependency는 새 증거로 확인하고 과거 5건에 추정 필드를 채우지 않는다.

## 7. N1 — 필요한 이력과 기존 관측 슬롯을 연결

### 7.1 입력 준비 descriptor

[현재 registry](../../src/engine/scalping/reversal_path_catalog.py)와 선택 payload의 활성 branch에서 기존 root/feature 계약을 읽는다. `manual_path_dca327a873720e53`은 60초 return, known FALSE→TRUE 전환과 1초 hold가 필요하다. 알려진 history만으로 미래 전환·신호 발생을 보장할 수 없음을 명시한다.

branch별 필드: `branch_id/definition_sha/policy_scope`, 필수 backward window, predecessor/표본·side/qty 요구, transition/hold, 현재 연속 유효 구간의 시작·끝·coverage, detector의 TRUE/FALSE/UNKNOWN, root 현재 조건과 feature 가용성, 현재 부족한 입력, 남은 residence. 이 descriptor는 전략 조건이나 별도 정책 파일이 아니며 실제 detector 정의와 hash를 대조한다. 설명 문자열을 파싱해 새로운 임계값을 만들지 않는다.

배정 전 discovery 가격은 tentative 가격대 판단에만 사용한다. 실제 first-data의 가격대·선택 scope가 다르면 descriptor를 재검증하고 원 deadline 안에서 입력 부족을 기록한다. 이전 가격대로 정책을 고정하거나 새 가격을 이유로 기한을 연장하지 않는다.

### 7.2 60/150초 배정 규칙

기존 **전체 물리 슬롯 5개, 150초 긴 슬롯 최대 2개, 나머지 60초**를 유지한다. 진행·handoff/cleanup pending은 현재 물리 한도에 포함한다. residence는 원 queue claim부터 시작한다.

| 후보의 실제 입력 상태 | 배정/처리 | 남길 근거 |
|---|---|---|
| 검증된 동일 interval 이력이 있고 짧은 슬롯에서 평가 가능 | 기존 순환 순서에 따라 짧은 슬롯 가능 | 재사용 prefix·필수 coverage·remaining budget |
| 새 관측 구간에서 60초 이력 및 추가 확인을 요구 | 기존 긴 슬롯을 우선 배정 | 필요한 이력·준비 상태·긴 슬롯 선택 사유 |
| 긴 슬롯이 모두 사용 중이고 짧은 슬롯으로 필요한 평가가 불가능 | 긴 슬롯 대기. claim 전 candidate 상태 유지 | 대기 시작·기존 next_due/신선도·현재 슬롯 점유 |
| 한 branch는 충분히 평가 가능하고 다른 branch는 미성숙 | 원 native union을 계속 평가; 유효 branch hit가 있으면 기존 경로 진행 | 모든 활성 branch membership과 각각의 준비 상태 |
| 이력 결손·미지원 descriptor·scope 변화로 판단 불가 | 미관측/입력 부족 보존, 원 admission/guard 적용 | 알 수 없는 입력·변경 scope·동일 원 deadline |

배정의 목적은 판단 불가능한 짧은 lease를 반복하는 것을 줄이는 것이다. 긴 슬롯 대기 때문에 일부 짧은 슬롯이 비는 경우 처리량·대기와 확보된 branch coverage를 함께 보고한다. 단순 lease 완료 건수만 높이려고 동일 부족을 반복하지 않는다. 짧은 lease에 들어간 활성 branch를 조용히 제외하거나 일부 branch 평가만으로 전체 정책을 검사했다고 표시하지 않는다.

prefix 재사용을 추가할 경우 같은 route/item/transport epoch 및 검증된 **연속 구독 interval**의 retained prefix만 허용한다. 이번 구현의 admission은 `history_reuse=none_without_exact_lease_interval`로 보수적으로 배정한다. 현재 native 구간은 first-data/terminal descriptor에만 투영하며, 입증되지 않은 prefix로 짧은 슬롯을 허용하지 않는다. 검증된 shared-owner prefix의 admission 최적화는 후속 범위로 분리한다. shared Main owner가 실제 수집을 계속한 경우의 prefix와 마지막 owner REMOVE 후 미관측 구간을 구분한다. REST 가격·다른 route·archive 가격으로 native tick 연속성·known FALSE→TRUE를 합성하지 않는다.

### 7.3 fairness와 종료 의미

1. 현재 cohort·activity:gainers 비율·last_claim·first_seen 순환 규칙을 유지한다. 준비 가능성은 슬롯 종류 배정에 사용하며 종목의 매매 우선순위나 가격 범위를 새로 최적화하지 않는다. 긴 슬롯 대기와 단기 슬롯에서 평가 가능한 후보를 명시적으로 구분하여, 대기 중인 선두 후보가 모든 단기 dispatch를 막지 않게 한다. 실제 dispatch에 적용된 cohort 순환과 defer 사유를 함께 대사한다.
2. 긴 슬롯 대기 candidate는 대기 원 시각과 기존 freshness를 보존한다. slot 경쟁에서 starvation을 계측하고 종료/ACK 뒤 순환하도록 한다. old claim을 반복 갱신하거나 새 발견 hint로 관측 예산을 연장하지 않는다.
3. 현재 descriptor와 남은 시간으로 해당 branch의 평가가 불가능해져도 활성 정책 membership을 숨기지 않는다. 기존 lease를 자동 연장하지 않고 부족 원인·현재 other branch coverage를 남긴다. 전략 조건을 줄이는 대안은 별도 수동연구다.
4. source reset·first-data 지연·정상 무신호는 각각 남긴다. 150초 내 필요한 history가 완성돼도 미래 transition이 없으면 정상 FALSE일 수 있다. UNKNOWN을 FALSE/BLOCK으로 바꾸거나 매수 기회였다고 추정하지 않는다.
5. 원 결과·최종화·lease 정리는 현재 worker→scanner→Main ACK 경로로 닫는다. queue deadline만 늘리고 worker/native wait/physical watchdog은 그대로 두는 불일치 구현을 금지한다. 이번 규칙에서는 원 60/150초를 늘리지 않는다.

필수 window/hold는 평가 가능성의 하한이며 미래 transition 대기 시간의 상한이 아니다. 고정된 임의 여유 시간을 추가해 정책 gate를 만들거나 150초 관측이면 반드시 판정/진입한다는 수용 조건을 두지 않는다. 실제 source 준비 비용·연속 구간·remaining budget과 branch별 coverage를 근거로 배정 효과를 판정한다.

종료 기준: 60초 history+1초 hold에 빈 prefix를 준 fixture가 긴 슬롯 또는 명시적 긴 슬롯 대기로 분류되고, long 2·physical 5 한도가 유지된다. 이미 짧은 이력으로 평가 가능한 branch를 가진 fixture와 일부 TRUE/일부 UNKNOWN union은 기존 정상 경로를 보존한다. 긴 슬롯 대기 시간은 candidate의 최초 대기 시각에서 계산하고 claim 뒤 초기화하며, 새 discovery hint로 리셋하지 않는다. 여러 round의 cohort 공정성·최대 대기·native 평가 branch coverage를 함께 검증한다. 과거 UNKNOWN 10건이 실제 성공 거래로 바뀌었다고 주장하지 않는다.

## 8. N2 — 0B/0D 원천의 첫 단절과 quiet 구간 대사

### 8.1 계측할 경계

기존 exact lease·raw packet·normalized snapshot·native observation receipt에서 아래 참조를 연결한다. 새 Kiwoom field 의미를 추정하지 않는다.

```text
claim -> exact REG 요청/확인 -> interval/epoch
      -> 0B first/provider/receive/callback/native ingest/Main read
      -> 0D first/provider/receive/snapshot publish/Main read
      -> source-ready 또는 missing/stale -> result -> exact cleanup/ACK
```

- 같은 lease의 item/route/realtime type·sequence·원 provider/수신/조회 시각·첫 0B/0D·현재 데이터 age를 구분한다. raw 전체 복제 대신 기존 journal 참조와 필요한 작은 scalar를 사용한다. 원 journal 참조가 없는 normalized snapshot은 없는 참조를 합성하지 않는다. `first_*`는 retained interval 내 최초 행으로 한정하고 실제 첫 packet이라고 단정하지 않는다.
- registry·first packet·normalized publish·native ingest 중 최초로 증거가 끊긴 곳을 남긴다. global connection 정상이나 fresh 0D만으로 해당 item 0B 정상 판정을 만들지 않는다.
- 기존 normalized envelope에 결속된 packet/dispatch/normalization 시각과 native 호출 반환 시각을 투영한다. native 호출 반환 자체는 수용 증거가 아니며 native epoch/sequence와 별도로 대사한다. 0D provider 시각이 정의되지 않은 경우 null을 유지한다. WS 원 packet 수신은 있으나 native publish가 없는 사례와 원 packet 자체가 없는 사례를 분리한다. 후자는 quiet/구독/transport 원인이 미입증이면 미관측이다. 다른 종목의 활발한 체결을 같은 종목의 체결 발생 증거로 대체하지 않는다.
- receipt 조회 범위는 원 실패 lease/신호의 bounded prefix와 기존 작은 execution partition으로 고정한다. 전체 진행 중 일일 원장을 반복 읽거나 가격 API를 늘리지 않는다.

### 8.2 원인별 처리

| 증거 상태 | 다음 보완 | 종료 검사 |
|---|---|---|
| REG 미전송/거절·ACK 불명 | 기존 exact acquire/cleanup 및 readiness 경합 검사 | 요청·확인·물리 해제의 원 신원 일치 |
| exact packet은 있으나 snapshot/native 단계가 누락·지연 | 같은 route/sequence의 실제 parser/callback/lock/배치 경로 수리 | 수신된 원 사건을 한 번 반영, 순서·sign/time·source 품질 보존 |
| 0D만 수신, 0B 발생은 미입증 | quiet/미관측 증거 유지 | 추가 provider 조회·fake tick·freshness 덮어쓰기 0 |
| 실제 원천 경로/구독 결함이 확인됨 | 이미 허용된 bounded recovery 적용 범위에서 수리 | 원 lease·cleanup·reconnect 검증, 이전 신호 부활 0 |
| normalized 시계가 서로 다른 event로 덮임 | 기존 source provenance projection 수정 | 0B/0D 각각의 원 clock/sequence와 Main age 일치 |

Kiwoom request/parser/FID mapping·REG/REMOVE/recovery를 실제 수정하기 전 [Official Kiwoom Reference Gate](../kiwoom-api-data-contract.md)의 **현행 upstream commit SHA·조회 시각·관련 kiwoom_docs와 SDK/core/realtime/Postman 경로**를 기록한다. 과거 다른 수리의 SHA를 이번 수정의 최신 검증으로 재사용하지 않는다. undefined/충돌 protocol 의미는 raw provenance·source gap으로 남긴다. 문서 계획에는 신규 요청·wire 변경을 실행하지 않는다.

## 9. S2·S3 — 유효 신호의 Main 도달과 로컬 비용 감소

### 9.1 native-ready→Main wakeup

이미 구현된 fixed 우선 배치·async completion/inbox wakeup을 유지한다. ready 통지는 유효한 선택 scope의 새로운 signal 또는 eligible 변화만 기존 Main 알림 경로에 전달한다. WS callback은 bounded identity/sequence 게시·notify만 수행한다.

- 기존 S0가 최초 eligible로 관측한 key만 기존 coordinator Event에 통지한다. root 현재 조건 TRUE를 전환 완료로 해석하지 않는다. 동일 key coalesce, callback 게시와 Main wait/clear 경합, pending batch, close/PID/정책/route 전환을 검증한다. Main이 실제 native 상태를 다시 검사하며 힌트는 claim·주문 권한이 없다.
- 현재 Main thread가 claim·DB·결정·주문 처리를 소유한다. FAST/holding/exit·실보유·COMMIT 우선순위와 기존 전체 watch 대상 수를 유지한다. 알림 때문에 동일 유효 신호를 반복 준비하거나 모든 tick에서 scanner/account를 다시 실행하지 않는다.
- Main이 동기 작업 중이면 wakeup만으로 즉시 처리되지 않는다. S0 시계로 확인된 작업 사이에 기존 cursor/bounded batch의 양보 지점을 보완한다. 진행 중 HTTP/physical 요청을 강제 취소하거나 새 thread·API quota로 지연을 감추지 않는다.
- pinned native 코드 수정 필요 여부를 구현 전 확인한다. adapter만으로 사실을 얻을 수 없으면 필요한 최소 hook과 code-pin 영향·동일 정책 호환을 먼저 검토한다. 상태를 추정하는 이중 detector/wrapper를 만들지 않는다.

### 9.2 준비·응답·저장 비용

`prepare_wait/service`, policy resolve/validation, exact source refresh, payload/복사/해시, HTTP, 응답 의미검증, trace/index/pending, 필수 append, worker 반환, Main 소비를 **비중첩 stage**로 계측한다. worker elapsed와 transport 차이를 그대로 제거 가능한 비용으로 계산하지 않는다.

기존 최종 WS refresh, trace/outcome index prewarm, candle 공유/cache를 재사용한다. 동일 입력의 중복 복사·graph/hash·schema 또는 비필수 저장이 실제 병목으로 확인된 부분만 해당 owner 안에서 줄인다. cache는 source cutoff·policy/registry/schema/validator/route/generation 변경에 무효화하고 반환 envelope를 다른 attempt가 수정하지 못하게 한다.

필수 capture·outbox·action append는 보존한다. 비필수 저장의 이관은 기존 bounded queue와 원 append→reader·crash 계약이 확인된 경우만 수행한다. `_load_seen` 등 특정 함수가 .721초 전체를 사용했다고 추정하지 않는다. 기록 drop으로 빨라진 candidate는 채택하지 않는다.

## 10. 소유 위치와 표적 회귀

새 engine-root 모듈·새 대형 원장·중복 queue를 만들지 않는다. 아래 기존 역할 package/caller에 구현하고 helper 추가 필요 시 같은 package의 책임을 먼저 확정한다.

| 변경 | 기존 코드 owner | 우선 확장할 테스트 |
|---|---|---|
| S0·S1 receipt 및 terminal | [runtime_performance](../../src/engine/monitoring/runtime_performance.py), [source diagnostics](../../src/engine/scalping/reversal_source_diagnostics.py), [Main handler](../../src/engine/sniper_state_handlers.py) | [fixed source](../../src/tests/test_fixed_watch_submit_source_repair.py), [latency](../../src/tests/test_main_rest_ws_latency.py), [async bridge](../../src/tests/test_scanner_async_entry_bridge.py), [monitor](../../src/tests/test_submission_bottleneck_monitor.py) |
| N0 준비·dispatch 경합 | discovery runtime, Main 초기화/요청 callback, zero_base_probe | [discovery runtime](../../src/tests/test_zero_base_discovery_runtime.py), [probe](../../src/tests/test_zero_base_probe.py), [Main attach](../../src/tests/test_zero_base_main_attach.py) |
| N1 슬롯/입력 준비 | [discovery queue](../../src/scanners/zero_base_discovery_queue.py), probe/native 관측 adapter | [queue](../../src/tests/test_zero_base_discovery_queue.py), [path policy](../../src/tests/test_reversal_path_policy.py), [operating policy](../../src/tests/test_reversal_operating_policy.py), probe/runtime |
| N2 원천 lifecycle | [WS](../../src/engine/kiwoom_websocket.py), probe/source diagnostics | [WS tests](../../src/tests/test_kiwoom_websocket.py), [continuous state](../../src/tests/test_continuous_reversal.py), probe/monitor |
| S2 Main 알림·준비 | kiwoom_sniper_v2, 기존 async coordinator/AI caller | [fixed watch](../../src/tests/test_main_fixed_watch.py), [async eval](../../src/tests/test_scanner_async_eval.py), latency/bridge |
| S3 저장 projection | [pipeline logger](../../src/utils/pipeline_event_logger.py), 실제 callback와 reader | [logger](../../src/tests/test_pipeline_event_logger.py), [summary](../../src/tests/test_pipeline_event_summary.py), monitor |
| 적용 호환/인계 | 기존 native loader·bootstrap·ordered deploy | [bootstrap](../../src/tests/test_runtime_policy_bootstrap.py), [ordered deploy](../../src/tests/test_ordered_intraday_deploy.py), operating policy |

필수 통합 반례:

1. 최초 eligible 아님, .85초 안에 저점 재시험, FIRST 교체, 일부 branch만 무효, 완전 source interval 종료, original 4.999/5.001초, ring eviction·미관측.
2. subscriber 있음/AI·WS·token 각각 없음, 준비 후 close, publish 뒤 late callback, REG timeout·cleanup pending, persist 실패, duplicate ACK가 successor를 해제하려는 경합.
3. 빈 prefix의 60초+1초 hold, 연속 prefix 충분, 59/60초 및 실제 transition/hold 경계, source gap/reconnect/shared owner/마지막 REMOVE, price-band 변경, 긴 슬롯 2개 만석, 반복 cohort 경쟁.
4. probe observer ENTER→durable result→Main inbox/adoption→원 exact live claim→live machine→auxiliary stub→기존 Main guard의 **실제 caller 통합**. 충분한 유효 신호를 준 fixture는 단일 소비하고 정상 거부 fixture는 같은 원 신원으로 종료한다. probe의 provider/order 호출은 0, 중복 live provider/intent는 0.
5. native hint와 completion 동시 도착, clear 직전 게시, heavy panel/계좌 작업, COMMIT/exit 경쟁, batch 잔여, policy/PID/date 교체. 통지 손실·busy loop·새 예산·누락 대상 0.
6. append 미확인·실패·회전/partial tail·동시 append·crash, 이전 schema reader·혼합일·receipt allowlist·sanitizer. 진단 성공으로 필수 저장 미완료를 덮지 않는다.

구현→self review→보완→재리뷰→표적 pytest·수정 Python compile·`git diff --check`를 반복한다. wrapper/배포 규칙 변경 시 `bash -n`과 해당 운영문서·checklist 인계를 같은 변경 집합에 포함한다. 문서 계획 검증은 로컬 link/owner/authority 및 print-only parser로 한정하며 trading suite·provider 호출·장후 재생성을 수행하지 않는다.

## 11. 성능·자원 검증과 수용 기준

### 11.1 비교 입력과 부하

baseline/candidate는 같은 정책·source prefix·event/lease 시계·작업 수로 고정한다. 실제 네 Main 실패 회귀는 원 시계를 유지하고, 합성된 충분한 원천의 정상 인계 fixture와 별도 표시한다. baseline/candidate **교대 3회**에 다음 부하를 포함한다.

- 상시감시 5개와 비상시 5슬롯(긴 2개 포함), 동일 source panel·준비 작업 수.
- 위 부하에 기존 COMMIT/holding/exit·정상 계좌 작업·필수 append가 겹치는 경우.
- 같은 5슬롯 안의 cleanup pending·source reset·늦은 결과 및 후보 대기 경쟁. 슬롯 밖 추가 작업을 만들어 처리량을 부풀리지 않는다.

wall/CPU·process-tree RSS·thread/worker 수, lock hold/wait, loop tail·ready→Main/claim/capture·응답 후처리, physical REST 수·WS callback/구독 churn, queue wait·lease-time·branch coverage·필수 저장 수를 같이 기록한다. 자연 한 PASS의 transport 시간을 일반 p95로 사용하지 않는다. 이전 PID의 더 늦은 snapshot에는 5초 초과 loop가 있으므로 앞선 짧은 창의 0건을 전체 warm 성능으로 일반화하지 않는다.

### 11.2 목표와 실패 조건

[기존 NS5/R2b 목표](main-nonfixed-native-signal-observation-and-consumption-remediation-plan-2026-10-08.md#82-성능과-자연-수용)를 재사용한다: `native-ready→Main claim p95 ≤250ms`, `signal→live machine capture p95 ≤1초`, `coordinator ready→Main guard p95 ≤100ms / p99 ≤250ms`. 성능 목표이며 새 매매 veto·TTL·승인 gate가 아니다. probe capture와 Main live capture를 합쳐 처리량을 세지 않는다.

코드 수용 조건:

- exact cohort의 opportunity/lease/attempt 보존식과 실제 writer→reader 연결이 닫힌다. 결손은 미관측·입력 부족으로 남고 false 성공을 만들지 않는다.
- 기존 5슬롯/긴 2개·60/150초·원 신호 5초·source/quote·policy/guard·custody가 유지된다. 동일 입력에 대해 전략 결정 parity, 유효 fixture의 단일 실행 인계, 정상 거부의 단일 종료를 확인한다.
- 준비 완료 전 물리 미실행 요청 소모가 없고, 구조적으로 부족한 단기 배정을 명시적 대기/기존 장기 배정으로 처리한다. 일부 정책 생략·대상/필수 저장 drop·unknown→FALSE 변환으로 얻은 속도 개선은 실패다.
- 같은 부하의 유효 신호 전달/로컬 비용이 개선되고 COMMIT/holding/exit·source coverage·물리 quota에 검증된 회귀가 없다. 변동이 커서 결론이 나지 않으면 개선 확정으로 표시하지 않는다.

### 11.3 자연 관측

새 PID의 초기 bootstrap/객체 준비·첫 준비 작업은 warmup 표로 분리한다. 반복 probe 이력 준비·비상시 lease residence·응답 후처리는 실제 운영 비용이며 warmup으로 제거하지 않는다. PRE/REGULAR/AFTER, fixed/nonfixed, source-at-event 준비 상태별 표본 수·as-of pending/미관측·분포를 표시한다.

표본이 작으면 개별 시계와 N을 제시하고 p99를 일반화하지 않는다. 실제 유효 신호가 없으면 코드/로드 PASS와 자연 전달 미관측을 분리한다. 테스트용 실주문·강제 Provider 호출·신호 부활을 만들지 않는다. 자연 표본 결손 때문에 코드 수리를 무기한 반복하거나 경제성/실현수익을 추가 수용 gate로 요구하지 않는다.

## 12. 정책 호환·배포·복구 인계

1. 구현 시작 시 실제 selected release/PID·정책 source hash와 code pin을 재확인한다. unpinned adapter 우선이며 pinned file을 바꾸면 현재 family의 loader/native 검증 영향과 unchanged-policy 호환을 먼저 닫는다. code-only successor가 필요한 경우 부모/CAS·원 경제 조건·target date·auxiliary 결속을 보존한다.
2. 실제 배포는 리뷰/표적 검증 완료와 해당 변경의 승인 범위 확인 뒤 기존 `OrderedIntradayDeploymentRepair1012` 경로를 사용한다. 후보 preflight·정책 호환 검증은 Main 종료 전에 끝낸다. 현행 drain→selector/checklist 게시→handoff/bootstrap→exact PID/start/cwd와 기계·보조 소비→selector 안정성의 순서를 유지한다.
3. 계획 작성으로 cron·현재 sealed checklist·정책 source bytes를 바꾸지 않는다. 후속 자동화 변경은 당시 운영문서와 동일 stable owner의 실행 항목을 함께 준비하고 외부 sync는 사용자 표준 명령에 맡긴다.
4. rollback/보완 중단 조건은 중복 claim/Provider/intent, 원 예산 연장, source·guard 누락, owner/custody 침범, 물리 한도 위반, append/대상 손실, crash 및 검증된 보호 처리·원천 부하 회귀다. 퇴역 consumer를 복원하는 릴리스는 rollback 후보에서 제외한다.
5. 코드 수용·배포 완료·PID 소비·자연 신호 terminal·경제성은 각각 별도 영수증이다. Main 이후의 정상 자금·수량·주문 guard와 broker terminal 문제는 증거를 보존해 해당 owner로 인계하며 이 source/latency 작업의 강제 주문 조건으로 넣지 않는다.

## 13. 정상 패턴 부재의 후속 연구

수리 후 충분한 입력의 native FALSE가 많으면 상시와 비상시·시장·종목/가격대별 등록 branch coverage를 [S4 후행 평가](main-native-signal-claim-and-auxiliary-revalidation-remediation-plan-2026-10-12.md#8-s4--과차단타점-연구의-source-계약)와 수동연구에 인계한다. 새로운 유형·특징·조건·확인 방식은 기존 사용자 방침대로 수동연구에서 만든다. 장후 owner가 자동으로 새 패턴을 발명하지 않는다.

- 정상 FIRST 저점 재시험·짧은 유효 수명과 confirmed/지속형 후보의 입력·소비 가능 시간을 비교한다. ENTER/PASS 여부와 후행 목표·손절/비용 결과를 별도 결속한다.
- 원 event 당시의 실행 가능 호가·target/stop/cost와 후행 경로가 없으면 pending/검열/source gap을 유지한다. 미도달 후 자료의 보조 평가도 기존 라벨 계약과 분리한다. 실제 PnL은 `COMPLETED + valid profit_rate`만 사용한다.
- 같은 canonical opportunity에 복수 패턴이 맞아도 한 기회로 비교하고 branch 기여·추가 기회를 별도 기록한다. UNKNOWN/미관측 10건을 정상 음성 학습으로 쓰지 않는다.
- 기존 누적 원천·clean source 계약으로 비교하며 수집/API를 확대하지 않는다. 기존 성공 100%/80% 보존을 새 후보 탈락 조건으로 복원하지 않는다. 정책 채택은 현재 해당 owner의 지정/비교·안전 계약을 따른다.

누적 분석의 시작일은 현행 family의 policy-refresh/source 계약을 사용한다. 현재 Plan Rebase의 revised postclose 정책 비교는 2026-09-29부터이며, 일반 clean-data 하한만으로 그 이전 자료를 successor 학습/선택에 섞지 않는다. 역사 receipt/custody/audit의 보존 의미는 별도다.

이번 실행은 선행 S0·S1·S3를 재사용하고 **N0 세대 경합, N1 descriptor·대기, N2 시계·저장, S2 최초 eligible 알림**까지 연결한다. 추가 batch 양보·정책 graph cache 변경은 실제 병목 원인이 입증될 때 진행한다. 문서 계획 완료, 코드 결함 수리 완료, 자연 경로 미관측, 정책 연구 대기는 각각 명시적으로 구분한다.

## 14. 구현 리뷰 보완 사항과 인계

1. 준비 receipt를 `PID/start/date/session/route/transport/family/runtime_generation`에 묶고 admission→callback→worker에서 재확인한다. 토큰/계좌/키 값과 digest는 출력하지 않는다. 확인 후 변경은 물리 REG 전에 종료하며, 실제 REG 가능성 이후에는 원 exact cleanup/ACK가 슬롯을 소유한다.
2. 패턴 정의의 history/hold를 캐시하되 registry hash와 branch ID로 구분하고 호출자에는 복사본을 반환한다. native lock 안에서 전체 definition/hash를 계산하지 않는다. actual native 가격의 scope와 원 discovery scope를 함께 기록하며 원 residence를 연장하지 않는다.
3. 오래된 마지막 tick의 FALSE를 현재의 정상 FALSE로 투영하지 않는다. 실제 detector snapshot·원 source clock과 freshness가 관측된 경우만 사용한다. root condition, 신호 전환/확인, feature 가용성을 서로 대체하지 않는다.
4. 0B/0D의 원 시계/sequence를 각각 유지한다. earliest-retained와 first packet, call-return와 native acceptance를 구별한다. 상세 진단은 기존 lossless 원본/분 partition에서 읽으며 텍스트에 중복 출력하지 않는다.
5. `zero_base_probe_result`의 원본→기존 `entry_mechanical_momentum` execution partition 누락을 수리한다. 원본과 projection은 동일 execution identity로 대사하며 주문 건수로 계산하지 않는다. 큰 신규 원장/일별 복제본은 만들지 않는다.
6. Main이 대기 중인 상황의 native-ready 통지 손실은 기존 completion Event로 보완한다. callback에서 claim/주문/DB를 수행하지 않으며 반복 tick마다 깨우지 않는다. 동기 작업 중 실행 지연의 개선은 이 변경만으로 확정하지 않는다.

성능은 두 수준으로 판정한다. 같은 입력 5 fixed+5 nonfixed stream과 실제 coordinator wait를 쓰는 component replay는 wakeup 효과/작업량을 검증한다. COMMIT/holding/exit/account는 이 replay에서 로컬 대역이므로 §11의 실제 전체 Main·물리 lease·보호 처리 동시 부하 완료로 표시하지 않는다. 전체 성능 및 자연 신호→claim→capture p95는 배포 후 별도 관측이다.

최종 테스트·공식 참조·lock 순서·원천 해시·남은 자연 관측은 [구현 리뷰](../audits/main-fixed-nonfixed-readiness-implementation-review-2026-10-12.md)와 [완료 영수증](../../tmp/fixed-nonfixed-readiness-20261012/completion.json)에 기록한다. 현행 sealed checklist를 변경하지 않고, 선행 native/auth 수리를 보존한 후보 checklist에 동일 stable owner로 인계한다. 배포/재기동·운영 장후 재생성·외부 sync는 이번 실행에서 하지 않는다.

## 15. 승인 후 통합 배포

사용자의 재리뷰·배포·재기동 승인에 따라 실패 AI 시계·trace writer·cache 시계 격리를 추가 보완하고 exact code-custody pair를 검증했다. 추가 1,027회귀와 269인계 회귀 PASS. `native-readiness-20261012-v1`/commit `fda9f640aadc14c3987075c9e9dc25358c03a28c`, PID `1171338`/start `4055127`의 bootstrap·exact consumption·prepared·auxiliary 128경로를 검증했다. 현재 sealed checklist는 배포기가 이전 PID 종료 후 게시했으며 그 후 byte 변경은 없다. 원 정책·PREOPEN 보호 파일은 동일하다. 자연 감시에서 세대 오류·신규 오류는 없고 기존 야간 recovered_late warning은 보존한다. 새 PID의 실제 AI 표본이 없으므로 시간초과 개선은 미검증이다. [배포 리뷰](../audits/main-native-readiness-deployment-review-2026-10-12.md)와 [완료 증빙](../../tmp/native-readiness-deploy-20261012/completion.json)을 확인한다.
