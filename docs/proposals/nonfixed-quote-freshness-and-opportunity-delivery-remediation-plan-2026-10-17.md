# 비상시감시 호가 시간정책·기회 전달 상세 점검 및 보완계획 — 2026-10-17

후속 상태: 격리 구현·반복 리뷰·표적 검증 뒤 사용자 명시 배포 지시에 따라 `a41ebc84f`를 다음 정규 기동용으로 배포하고 격리/공유 파일의 정책 read·schema·code 및 전체 준비 검증을 마쳤다. [구현 리뷰](../audits/nonfixed-quote-opportunity-delivery-implementation-review-2026-10-17.md)·§10은 원 구현, [최종 배포 검증](../audits/nonfixed-quote-deployment-and-isolated-policy-review-2026-10-17.md)·§11은 배포를 소유한다. 실제 PID 소비와 자연 성과는 아직 확인하지 않았다. 새 TTL 선정은 배포 선행 조건이 아니다. 아래 §1–§9는 구현 전 점검·계획 당시 기록으로 보존한다.

## 1. 이번 결정

사용자의 “stale 시간기준을 일괄 유지하면 제출병목이 남는다”는 지적에 따라, [앞선 연구 검토 §7](../audits/main-cumulative-opportunity-failure-and-nonfixed-quote-review-2026-10-17.md)의 **현재 시간상한을 일률적으로 유지한다는 전제를 수정**한다. 이전 봉인 보고서는 당시 검토 기록으로 보존한다. 이번 문서가 시간정책과 후속 구현 범위의 상세 보완을 소유한다.

개선은 다음 세 축으로 진행한다.

1. **불필요한 대기·알림 누락을 보완한다.** 실제 선택 코드의 source-wait 경쟁 조건을 재현했고, 호가만 회복될 때의 연결 누락도 확인했다.
2. **시간 허용 정책 자체를 검증한다.** 700ms를 모든 종목에 영구 고정하거나 무조건 늘리지 않는다. 수신·가격·호가 특성에 맞는 조건별 정책을 같은 기회와 원천에서 비교한다.
3. **실제 전송 시점의 유효성을 보장한다.** 앞단에서 같은 시간검사를 중복 누적하는 대신, 입력 유효성·판정 유효성·현재 실행 가격의 역할을 구분하고 최종 전송 직전 검증과 연결한다.

이번은 상세 점검·오프라인 재현·계획 보완이다. production 코드·정책·환경값·구독·주문·provider·배포·재기동은 변경하지 않는다. 원천 정체성 결손이나 실제 무효가 확인된 호가를 더 큰 TTL로 승인하는 예외 경로를 만들지 않는다. 적용된 보조판정의 입력·응답·membership도 보존한다.

## 2. 기준과 증거

선택 릴리스는 `postclose-complete-20261017-7f2552aed`/commit `7f2552aedde8fec6ef904a43105827907e50dfc8`, 기계 bundle은 `8809c82e36bacc6a6e07b44c8bba6ccf15e477b67e11bdfcf4addf15112a4139`다. selector의 다음 운영일은 10/19이고 `actual_pid_consumed=false`다. 이번 검토는 PID 기동 검증이 아니다.

앞선 원천 준비 검토의 핵심 16개 파일 표본 중 workspace와 선택 release가 다른 것은 8개였다. 이번 식별자 계약 점검은 별도의 16개 표본이며 차이10개다(§2.1 및 사전점검 결과). 두 표본을 같은 집합으로 합산하지 않고 실제 선택 코드로 분석했다. [원천 준비 검토](../../tmp/nonfixed-quote-ready-improvement-review-20261017/source-readiness/review.md), [AI 이후 소비 검토](../../tmp/nonfixed-quote-ready-improvement-review-20261017/post-ai/review.md)가 각 경로·행·SHA와 이미 있는 기능을 소유한다. 10/17 체크리스트가 없어 과거 또는 10/19의 OPEN을 오늘 실행 권한으로 대신하지 않았다.

공식 Kiwoom 저장소는 KST `2026-10-17T07:47:11`에 현재 HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`를 확인했다. `kiwoom_docs`는 이 tree에 없다. `kiwoom/specs.py`, `kiwoom/realtime/{decoders,events,schemas,packets,stream}.py`, `kiwoom/_data/kiwoom_api_spec.json`의 0B·0D·kt10000을 확인했다. 0B FID27/28 최우선 호가와 0D FID21/41/51·수량 필드는 별도 원천이다. 확인한 스펙에는 이 프로젝트의 250/700ms 기본값을 호가 유효기간으로 규정한 설명이 없으며, 패킷이 없다는 이유로 호가가 무기한 유효하다고 보증한 것으로 해석하지 않는다. [상류 snapshot](../../tmp/nonfixed-quote-ready-improvement-review-20261017/official/upstream.json)과 [공식 packaged spec](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/953e5dbff123f437ab4d11a78a95191a685eb51f/kiwoom/_data/kiwoom_api_spec.json)을 보존했다. 실제 Kiwoom/API·auth·계좌·주문 호출은 없었다.

### 2.1 구현 전 식별자·필드 계약 확인

[사전점검 결과](../audits/nonfixed-quote-remediation-contract-preflight-review-2026-10-17.md)에 생산자→소비자 21개 경계와 실제 정책·schema·필드·함수 인자·타입·단위·대소문자를 고정했다. 현재 선택 bundle의 native validator·digest, 기존 원천 테스트 31개, 정책/설정/경로 순수 fixture 60개와 handoff fixture 17개를 확인했다. 문법/미정의 이름 검사는 선택 생산 코드 25개에서 통과했다. 지원되는 session alias·nullable·호환 backend를 임의의 새 탈락 조건으로 바꾸지 않는다.

**설정 조회 이름 불일치 1건을 추가 재현했다.** `constants.py:2157`은 `KORSTOCKSCAN_SCALP_PRE_AI_MAX_WS_AGE_SEC`를 읽지만 `_scanner_ws_stale_backoff_recovered:15852`는 접두사가 없는 이름을 `_env_float`에 전달한다. 이 helper는 prefix를 추가하지 않는다. 정식 설정이 1초/5초인 fixture에서 backoff는 각각 기본 3초로 남았다. 기본 3초에서는 드러나지 않는다. 시간정책 비교 전에 기존 canonical 설정 owner와 이 회복 판단의 이름·단위·기본값·clamp를 일치시킨다. 실제 설정값·자연 제출 영향은 이번에 측정하지 않았다.

구현 기준 코드도 고정한다. 정책 측 검사 49개 중 workspace와 선택본 차이21개는 내용 차이17개·workspace 부재4개다. 원천 측 별도 표본에는 workspace에 없는 `native_source_continuity.py`도 있다. 후속 구현은 선택 커밋과 필수 모듈을 갖춘 격리 작업본에서 시작하고 동시 작업을 덮어쓰지 않는다. 사전점검 전 문서와 원 완료 영수증은 별도 원본으로 보존했다.

## 3. 확인된 결함과 기존 구현

### 3.1 P1: 원천 준비 알림을 놓치는 경쟁 조건

선택 `zero_base_probe.py:391–446`은 source snapshot을 검사한 다음 알림 순번을 읽는다. 검사 직후 source가 갱신되면 갱신된 순번으로 대기하여 이미 준비된 원천을 재확인하지 못하고 최대 1초 더 잠들 수 있다.

[실제 함수의 결정적 재현](../../tmp/nonfixed-quote-ready-improvement-review-20261017/source-readiness/source-wait-race.json): `snapshot missing → source ready+notify(version1) → version1 읽기 → wait predicate false`에서 `source_already_ready=true`, `wait_ms=1000`이었다. clock/source만 mock했고 선택 production 함수는 변경하지 않았다. 운영에서의 실제 발생 빈도는 미측정이다.

**보완:** loop 시작에서 알림 version을 먼저 캡처하고 source snapshot을 확인한 다음, 같은 version으로 대기한다. 이미 올바른 native wait의 `:886/888/905` 순서와 맞춘다. 타이머를 짧게 하거나 busy loop를 추가하지 않는다.

**완료 검사:** 검사와 wait 사이 갱신·wait 중 갱신·가짜 깨움·정상 timeout·transport/policy 교체·원 deadline 만료. 준비된 source가 있으면 추가 1초 대기가 없어야 한다.

### 3.2 P2: 0D만 준비돼도 source 대기를 깨우지 않음

선택 `kiwoom_websocket.py:4669–4679`는 0B 처리 후 `notify_observation(item)`를 호출하지만 0D는 같은 condition을 깨우지 않는다. `REALTIME_TICK_ARRIVED`와 fast exit wake는 해당 source 대기의 대체 경로가 아니다. 마지막 부족 입력이 0D라면 최대 1초 재확인 주기를 기다리는 연결 누락이다. 실제 누락 건수는 별도다.

**보완:** exact item·epoch의 0D를 정상 수신하여 공용 snapshot에 반영한 뒤 기존 source condition을 깨운다. 원천이 아직 반영되지 않은 시점에 notify하지 않는다. 0D로 가격 FSM을 진행하거나 가짜 0B를 생성하지 않는다. 대기 중인 exact source에 한정해 전달하고 coalescing하여 전체 Main 재평가 폭주를 방지한다. 3.1 수정과 함께 적용한다.

**완료 검사:** 0D-only 회복 즉시 재검사, 다른 item/route/epoch 무효, price FSM signal 수 불변, 잘못된 source로 깨어나도 승격 없음, 고빈도 0D에서 bounded CPU/단일 intent 유지.

### 3.3 이미 있으므로 다시 구현하지 않는 기능

- durable discovery claim, Main consumer readiness, exact 0B/0D lease 및 source continuity.
- 새 native 0B 신호의 Main event wake, 독립 등록 정책 탐지.
- 신호 전 무조건 430봉 REST를 생략하고 신호 뒤 reduced WS 완료봉을 우선 재사용하는 경로.
- native event+5초의 wall/perf 공통 deadline, generation/state/custody/claim 재검증.
- AI 직전 준비 입력 갱신, 기존 PASS의 정확한 binding 검증, ack·outbox·중복 전송 및 불확실 전송 보호.

따라서 “이벤트 처리·재조회·PASS 검증을 새로 만든다”는 넓은 구현계획은 중복이다. 실제 누락된 호출 연결과 시각을 고친다.

## 4. 시간기준은 한 가지가 아니다

아래는 **선택 코드의 기본값과 적용 경로**다. 실제 다음 PID의 유효 설정은 별도 장전/기동 증거다.

| 검사 | 기본값·원천 시계 | 역할·활성 경계 |
|---|---|---|
| 연구 `good_quote` | age 미기록 또는 5,000ms | 과거 가격 패턴 연구 조건. 실시간 실행 허가가 아님 |
| exact probe·native source continuity | 0B/0D 기본 3초 | 같은 item/route/epoch·등록 후 원천 및 준비 조건 |
| AI 입력 전 canonical quote | 3,000ms | 실제 채택한 0D 또는 정확한 inline 0B 최우선 호가의 수신 시각 |
| 비상시 async snapshot 추가 검사 | transport age 2초 | canonical 검사 이후 비상시에 추가. fixed watch는 이 추가 한도 생략 |
| latency 분류와 관련 cache | SAFE250 / CAUTION700ms | 다른 jitter/spread/RTT 조건과 함께 분류. 두 상태 모두 정상 제출 가능 |
| quote consistency | WS700 / REST1,500ms | runtime flag가 켜지고 `entry_blocked`일 때 실행 차단. 기본 flag=False |
| local 최신 WS snapshot 재조회 | 기본 채택 700ms | 명시적 env False가 아니면 사용; 호출 owner가 별도 한도를 줄 수 있음 |
| observer quote refresh | 기본 채택 700ms | 기본 disabled. 켜져도 채택 후 latency 재분류가 별도로 존재 |
| submit revalidation | transport snapshot2초 / context8초 | `quote_age_at_submit_ms`라는 출력명과 달리 현재 age 계산은 `last_ws_update_ts` 기반이다. canonical 호가 원천 나이와 별도로 구분 |
| native 기회 lifetime | 원 event+5초 | quote age와 별개의 원 신호·claim·AI·Main lifetime. 재조회로 연장 안 됨 |

quote consistency와 observer refresh는 과거 10/16 준비 env에서 활성 기록이 있었지만 이를 다음 PID 적용으로 전용하지 않았다. post-sell·퇴역 opening rotation·진단 버킷에서 발견된 1초 값은 일반 Main 진입 한도로 합치지 않았다. entry policy의 별도 trigger-clock1,200ms도 machine→AI 총예산으로 부르지 않는다.

**700ms 한 곳만 늘리면 다른 활성 700ms에서 다시 막힐 수 있다.** 반대로 숫자 전체의 최솟값을 만능 TTL로 삼는 것도 틀리다. 검사 시각·대상 원천·역할이 다르고 중간에 새로운 호가가 도착하기 때문이다. 각 검사에서 같은 source receipt를 현재 시각으로 다시 계산하는 흐름으로 대조해야 한다.

## 5. 시간 허용 정책의 수정 방향

### 5.1 나이 정책과 정체성 결손을 분리

- 허용시간을 늘려도 해결되지 않는 항목: item/route/epoch 불일치, 원천 미기록·미래 시각, 수신 단절·유실 증빙, 유효하지 않은 bid/ask·수량, 원 신호 취소·만료, custody·수량·broker 차단.
- 검증할 항목: 알려진 수신시각을 가진 동일 원천의 age가 700ms를 넘었다는 이유만으로 차단하는 범위를 종목·세션·관측 상태별로 달리할 수 있는가.
- 실제 무효화: 새 quote·trade가 원 가격/호가와 충돌하거나 spread·슬리피지·정책 조건을 벗어나면 재가격·재판정한다. 단순히 업데이트가 없었다는 이유로 “변화 없음”을 확정하지 않는다.

다른 단계의 age 검사를 우회하는 예외 lane을 추가하지 않는다. 승인된 시간정책 버전·적용 이유·source clock을 모든 해당 소비자가 명시적으로 소비하도록 설계한다. 그 정책에서도 무효인 stale·UNKNOWN은 차단한다.

### 5.2 종목 이름 대신 진입 시점 특성을 사용

비상시라는 이유만으로 긴 시간을 주지 않는다. 다음 유형을 **판정 이전 prefix**로 구분한다.

1. 체결·호가가 빈번하고 변동이 큰 상태: 실행 가격 변화와 depth 변화를 짧은 주기로 확인한다.
2. 체결은 간헐적이나 동일 item의 0D 수신·구독·연속성이 검증된 상태: 0D-only 회복과 조건별 age 후보를 비교한다.
3. 편입 직후 또는 cadence/연속성 증빙 부족: ‘조용한 종목’으로 추정하지 않고 기존 준비 경로로 원천을 확인한다.

스프레드·depth·관측 가격 변동·0B/0D 간격은 진단과 후보 조건의 입력이다. 미래 업데이트 빈도로 과거 유형을 정하지 않는다. 저유동성 자체를 낮은 위험으로 취급하지 않는다. 서로 다른 type의 시계를 임의로 갱신하지 않는다. 기존 inline 0B가 현재 BBO와 정확히 같고 epoch가 일치할 때 최우선 호가 시각을 채택하는 기능은 재사용하되 depth 전체를 갱신했다고 표시하지 않는다.

### 5.3 단계별 중복 검사와 최종 검증을 함께 정리

입력 준비 검사는 특징·원천을 판단하고, AI binding 검사는 원 판정의 유효성을 판단하며, 전송 검사는 현재 실행 가능 가격을 판단한다. 오래된 최초 snapshot의 age만 보고 중간 단계에서 종료했지만 manager에 더 최신 exact 0D가 이미 있는 경우를 먼저 확인한다.

`_pre_submit_refresh_real_ws_snapshot`은 전달된 snapshot이 해당 한도에서 fresh면 manager 조회를 생략할 수 있다. 상위가 항상 최신 frame을 제공하는지 재현해 영향이 있을 때만 최신 source 선택을 보완한다. 재조회가 원 AI 요청/응답을 다시 쓰는 권한이 되지 않게 한다.

비상시만 추가하는 transport snapshot2초 검사도 같은 묶음에서 검증한다. 유효 native claim·동일 원천 증거가 같은데 상시 여부만으로 다른 결과가 생기는지, 더 최신 exact 호가를 조회하기 전에 옛 snapshot의 추가 상한으로 종료하는지 비교한다. 새 정책의 적용은 종목 이름보다 현재 proof·원천 상태로 결정한다. native proof가 없거나 generic scanner의 상태가 불명확한 경우까지 검사 생략을 넓히지 않는다. 2초만 없애고 다른 700ms에 그대로 막히는 보완은 완료로 보지 않는다.

선택 코드의 submit quote 검사는 `sniper_state_handlers.py:68037`이고, 이후 자금·수량 준비, auxiliary 재검증, 원 deadline 검사를 거쳐 `:71480`에서 send를 호출한다. 추가로 읽은 `kiwoom_orders.py:2034–2298` 및 `_post_kiwoom_with_auth_retry:757`에는 같은 intent의 quote receipt·age를 전달받는 인자나 전송 직전 재검사 hook이 없다. 물리 POST는 `:782`, auth retry 전송은 `:861`이다. **검사 후 실제 전송까지 age가 늘어날 수 있는 경계**이며, 실제 stale 주문이 있었다는 증거는 아니다.

후속 구현은 준비·intent 영속화·token 준비 뒤 실제 전송 직전에 같은 quote policy의 유효성을 확인하는 경계를 만든다. 더 이른 단계의 같은 목적 중복 차단도 함께 정리한다. auth 거절 후 허용되는 재전송은 실제 각 전송 직전에 원 deadline/source/수량/intent를 재검증하고 원 기한을 새로 만들지 않는다. 이미 전송한 주문이 응답·체결을 기다리는 상태는 entry TTL 경과만으로 실패·미전송 처리하지 않는다. 불확실 전송을 다시 보낼 수 있게 바꾸지 않는다.

공용 transport를 수정할 때 새 guard context는 **Main 신규진입 `ENTRY_BUY`의 원 intent**에만 명시적으로 바인딩한다. 그 context를 가진 해당 매수 API의 물리 전송·정확한 auth retry에만 적용한다. SELL·보호/긴급 청산·CANCEL·계좌 조회·대사·다른 owner로 entry 5초/quote 의무가 전파되지 않아야 한다. thread/context 상속만으로 적용 대상을 추정하지 않고 side/API/owner/intent를 확인한다.

여기서 `ENTRY_BUY`는 논리적인 최초 진입 범위다. 기존 `OwnerOrderContext`의 필드는 `owner_type`, `owner_id`, `position_id`, `client_intent_id` 네 개이며 `action` 필드는 없다. 일반 최초 진입은 helper의 `action="ENTRY_BUY"` 인자로 intent 문자열을 만들지만 초기 분할 leg0는 `initial_quantity:…:leg0` 형식을 사용한다. 따라서 없는 `context.action`을 읽거나 intent에 `ENTRY_BUY` 문자열이 포함되는지로 guard를 선택하지 않는다. 새 operation context는 새 계약임을 명시하고 기존 네 필드와 원 intent를 결속한다. 일반 최초 진입과 초기 분할 leg0의 첫 전송·같은 intent의 허용된 auth retry에 명시 전달한다. leg1 이후·기존 bundle 재개·AVG_DOWN에는 Main owner/BUY라는 이유만으로 최초 신호의 5초 기한을 전파하지 않는다. 후속 leg는 기존 bundle slot·원 주문 시작 시각·최대 1,200초 계약을 유지한다.

실제 환경변수명도 코드 helper 인자와 구분한다. `_env_or_rule_int("SCALPING_ENTRY_SUBMIT_REVALIDATION_MAX_QUOTE_AGE_MS", …)`가 읽는 env는 `KORSTOCKSCAN_SCALPING_ENTRY_SUBMIT_REVALIDATION_MAX_QUOTE_AGE_MS`다. 짧은 helper 인자를 env 이름으로 복사하면 설정이 반영되지 않는다. 새 검증에서 현재 `quote_age_at_submit_ms`를 canonical 호가 나이로 재사용하지 않고 기존 `ws_quote_source_receipt`·`ws_quote_receive_age_ms`의 실제 source clock을 사용한다. 과거 telemetry와 원 receipt bytes는 이름 변경으로 덮어쓰지 않는다.

새 context의 생산자는 Main 실행 owner다. `submit_attempt_machine_lineage()`는 작은 telemetry allowlist만 반환하므로 전체 assessment·nested effective verdict·quote·AI trace를 그 dict에서 추측해 꺼내지 않는다. 원 비동기 결과와 검증된 Main provenance에서 각 필드를 가져오고 call-local 평가 ID·원 client intent와 일치시킨다. `entry_ai_screen_status="pass"`, 대문자 effective verdict `PASS`, 실제 bool인 `entry_ai_screen_pass`도 구분한다. 같은 `machine_component_sha256`라는 이름이더라도 assessment와 `runtime_consumption`의 해시 owner가 다르므로 전체 경로별로 검증한다. 현재 지원 backend/version별 검증 결과를 사용하고 UNION 전용 필드를 모든 호환 정책에 일괄 필수화하지 않는다.

## 6. 0D-only 원천 회복의 별도 계약

사전 계약 점검에서 정책·데이터·broker의 route 역할도 구분했다. `assessment.route`와 native event의 `venue`는 정책/시장데이터 scope의 `SOR`·`NXT` 등이고, WS `market_route`는 `krx_nxt_integrated`·`nxt_only`, broker body의 `dmst_stex_tp`는 최종 실행 route다. 이 세 문자열을 직접 동등 비교하거나 일괄 대문자화하지 않는다. 기존 route resolver와 각 원천 증빙을 따라 결속한다. `ws_quote_source_receipt`의 타입 key는 `source_type`이며 `realtime_type`으로 추측하지 않는다. `transport_epoch`는 연결 세대를 식별하는 정수이므로 timestamp처럼 나누거나 변환하지 않는다.

현재 `entry_machine_source_recovery.py:120–186`는 원 결손이 호가뿐이어도 새 0B를 요구한다. 기존 `test_only_new_exact_tape_schedules_fresh_calculation`이 이 계약을 고정하므로 코드 버그로 단정하지 않는다. 0D wakeup을 추가해도 이 정책은 그대로 남는다.

후속 후보는 다음 조건을 모두 만족하는 원천 회복에 한정한다.

- 원 평가가 미평가·provider 미호출 상태이며 결손 필드가 0D가 생산하는 BBO/depth로 특정된다.
- 새 exact 0D의 시각·sequence·item/epoch·lease가 증명된다. 최초 실패 뒤 실제 수신된 packet이어야 한다.
- live 0D의 `received_at_ms`는 depth builder의 로컬 생성 시각이며 snapshot `observed_epoch`는 이 값/1,000이다. 이는 별도 `packet_received_epoch`와 다르다. 최초 실패 뒤 실제 packet 수신이라는 조건은 `observed_epoch`만으로 증명하지 않는다. 기존 latency 원천의 packet 시각을 같은 item/epoch/type sequence와 대조하고 증빙이 없으면 미입증으로 남긴다. 원천 생성 시각을 packet 수신 시각으로 대체하지 않는다.
- 기존 0B는 새 검사 시점의 해당 source 정책에서도 유효하고 원 신호는 취소되지 않았으며 원래 5초 내다.
- snapshot을 새 source receipt로 새로 계산하고 현재 특징/ask를 사용한다. 원 관측 bytes·판정 ID를 덮어쓰지 않는다.
- 같은 원 기회에 bounded machine 재계산 1개만 허용한다. 이미 provider가 실행된 verdict/PASS, 체결·봉·거래량 결손, epoch/route 불일치에는 일반화하지 않는다.
- 기존 native proof가 root event ask와 계산 ask를 함께 표현하지 못하면 버전 있는 proof 계약부터 보완한다. 현재 quote를 과거 native event에 삽입하지 않는다.

원래 signal identity와 새 evaluation identity의 관계, 필드 owner, source 변경·expiry 중 경합, ack/outbox 및 Main/manual 경계를 회귀로 확인한다. 완료 기준은 새 0B를 합성하지 않고 적격 0D-only 회복이 기존 경로의 새 기계계산에 도달하는 것이다.

**깨워야 하는 소비자는 둘이다.** §3.2의 source condition은 probe worker를 깨운다. 이미 WATCHING인 종목의 source recovery는 `sniper_state_handlers.py:_resolve_watching_state_change_refresh`에서 Main loop가 수행하므로 별도 pending-target 전달이 필요하다. 같은 원 signal이 살아 있고 위 조건에 맞는 pending target만 기존 coordinator wake에 연결해 coalescing한다. native FSM을 진행하거나 native-ready·새 기회 통계를 늘리지 않는다. probe의 0D-only 회복과 WATCHING pending source의 0D-only 회복을 별도로 검사한다.

## 7. 저장 원천으로 검증하는 방법

기존 0B-prefix 진단만으로 TTL을 선택하지 않는다. 같은 opportunity·각 단계 실제 시각·직전 수신 source를 고정하여 다음을 비교한다.

1. current 코드와 현재 시간정책.
2. 시간정책은 current인 채 lost wakeup·0D 통지·불필요한 준비 지연만 보완.
3. 전달 경로는 current인 채 조건별 age 후보만 변경한 오프라인 진단.
4. 지연 보완과 조건별 age 정책을 함께 사용한 재생.

진단 age 후보는 250/700/1,000/1,500/2,000/3,000/5,000ms다. 이는 확정 운영값이나 모든 단계의 공통 한도가 아니다. source·quote·feature·원 신호 lifetime의 검사 시각을 각각 재현한다. 불명확하거나 부적격인 epoch는 제외하고 결과는 null/결손으로 남긴다.

필수 자료는 기존 저장 0B·0D, exact 구독/transport epoch·원천 quality, original claim·deadline, 기계/AI 입력·응답·Main 소비·기존 terminal이다. 별도 수집 확대는 하지 않는다. `market_depth_stream` 저장 자료도 확인했으므로 0B만 보던 연구보다 직접 검증을 보완할 여지가 있다. 파일 존재만으로 과거 epoch·필수 clock이 적격이라고 승인하지 않는다.

같은 시점의 허용 결과만 비교하지 않고, 현재 ask 이동·spread·호가 잔량·가격 상충·원 신호 무효화·지정가/슬리피지·비용 후 30분 목표/손절을 함께 계산한다. actual PnL은 기존 COMPLETED+유효 비용 계약의 자료만 사용한다. 체결·가격 모델이 없으면 실제 전송·체결·수익 증가를 추정하지 않는다.

패턴 품질은 기존 Main 누적 비용 후 승률 계약을 쓰고, source-age 정책의 안전성은 같은 표본에서 원천 무효·실행 가격 위험을 분리해 검증한다. age 정책을 장후 패턴 자동 탐색이나 누적 승률 후보의 별도 주문 권한으로 만들지 않는다.

### 7.1 시간상한 민감도: 실제로 진단한 범위

현재 CF 비상시 166개(기존150·신규16)를 각 확인점+0/1/2/3초로 이동시켜 보존 0B-prefix만으로 검사했다. 이전150의 250/700ms 결과를 전부 재대조했으며 18개 원천을 한 번씩 읽었다. [진단 결과](../../tmp/nonfixed-quote-ready-improvement-review-20261017/research-contract/age-sensitivity.json)를 보존했다.

| 확인 후 시간 | 700ms 이내 증빙 | 1,000ms | 1,500ms | 2,000ms | 3,000ms | UNKNOWN |
|---|---:|---:|---:|---:|---:|---:|
| 1초 | 71 | 157 | 157 | 157 | 157 | 9 |
| 2초 | 62 | 75 | 86 | 156 | 156 | 10 |
| 3초 | 53 | 58 | 70 | 83 | 154 | 12 |

700→3,000ms로 늘리면 3초 시점의 알려진 age 범위 통과는 53→154개다. **오래된 호가를 더 오래 인정한 민감도**이며 새 0D가 왔거나 실제 주문이 늘어난 결과가 아니다. 이 수치만으로 운영 상한을 3초로 선정하지 않는다. 기존 0B만 보던 진단의 한계와 실제 0D 수신을 함께 검증해야 한다.

### 7.2 저장 0D를 단일 소형 범위로 확인한 결과

수집 확대 없이 10/15 SOR AFTER의 비상시 CF16개·7item·2native epoch를 대상으로 기존 depth gzip 한 파일을 한 번 읽었다. 물리 10,611,626B, 논리 211,277,711B·165,526행을 1.99초에 확인했고 대상 시각 주변 278행만 추출했다. 512MiB/60초 예산 안에서 끝났으며 원천은 수정하지 않았다. [0D prefix 대조](../../tmp/nonfixed-quote-ready-improvement-review-20261017/research-contract/depth-prefix-probe.json)에 원 행 hash·논리 offset과 한계를 기록했다.

- 확인점+0/1/2/3초에 같은 item·native epoch의 과거 0D를 찾은 수는 12/16/16/16개다. 0초에는 같은 timestamp의 수신 순서 미확정1개, 주변 구간에 없는3개가 있다.
- 그 시각 저장 원천의 관측 clock 기준 age≤700ms인 0D는 각각 9/11/5/8개다. 별도의 실제 packet ingress 시각을 입증한 수가 아니다.
- 보존 0B의 quote 증빙은 700ms를 넘었지만 새 0D가 700ms 내에 왔고 **그 뒤 새 0B가 없었던 사례**가 1/2/3초 시점에 각각 5/2/5개 있었다. 서로 독립 사례의 단순 합으로 세지 않는다.
- 예: `046970_AL` 확인 시각 `1792052613.700`에서 1초 후, 0B 증빙 age는 1,000ms다. 같은 native epoch의 0D(sequence2201)는 저장 원천 관측 시각이 `1792052614.304`여서 age396ms였다. socket 수신 시각과의 차이는 별도 검증 대상이다.

최초 추출은 전체 depth 배열·authority 필드를 생략하여 원천 owner의 전체 행 검증을 실행할 수 없었다. 첫 시도와 영수증을 보존하고, 같은 278행만 원본 bytes로 회수하는 제한된 추가 읽기를 1회 수행했다. 0.53초에 끝났고 원 행 hash·논리 offset 278개가 전부 일치했다. 선택 릴리스의 `_validate_depth_row`는 **278/278행 PASS**, 당시 Main의 정상 종료된 수집 epoch 증빙도 **278/278행 적격**이었다. [원본 전체 행 검증](../../tmp/nonfixed-quote-ready-improvement-review-20261017/research-contract/attempt2/full-depth-validation.json)에 원본·validator·epoch 해시를 결속했다. 같은 16개 기회를 0/1/2/3초에서 반복 평가한 **과거 수신 기준 관측 60개**가 이 원천 계약을 통과했다. 이는 고유 기회 수나 고유 0D 행 수가 아니다. 0초의 수신 순서 미확정1개·관측 없음3개는 UNKNOWN으로 보존했다. `native_receive_session=null`은 owner 계약에서 허용하는 nullable 필드이므로 새 탈락 조건으로 만들지 않았다.

따라서 **더 최신의 적격 저장 원천이 이미 있었는데 0B만 본 분석에서는 보이지 않는 경우**를 확인했다. 실시간 lease·필수 기계 입력 전체·실제 snapshot 채택·Main 소비·PASS·주문은 별도다. 이 원천 검증만으로 16개가 모두 실행 적격이었다거나 실제 제출이 증가한다고 승인하지 않는다.

후속 연구는 **신선한 0D가 있는 경우의 전달 개선**과 **새 수신 없이 알려진 호가만 오래된 경우의 시간정책 검증**을 각각 계산한다. 이전 0B-only 진단을 실제 stale 거절률로 바꾸지 않는다.

## 8. 구현 순서·완료 검사

| 순서 | 작업 | 소유 경계 | 완료 검사 |
|---|---|---|---|
| 0 | 선택 커밋 기반 격리 작업본·실명 계약·설정 조회 일치 | 기존 코드/정책 loader·canonical config owner | 21개 source 경계·schema/case/clock 검증, prefixed1/5/default3초가 backoff와 일치, 동시 변경 보존 |
| 1 | source-wait version-before-check | `zero_base_probe`·기존 condition | 현재 재현의 1초 불필요 대기 제거, timeout/원 deadline 보존 |
| 2 | exact 0D source wake | WS 수신→공용 source condition | 0D-only source-ready 즉시 확인, 다른 item 무효, 가격 FSM 불변·event storm 없음 |
| 3 | quote-only source 재계산·Main pending wake 계약 | 기존 source recovery·native proof·coordinator | probe 및 WATCHING pending 각각 즉시 전달, 미평가·호가-only 결손의 bounded 새 계산, 0B 합성·기한 갱신·중복 AI·native-ready 통계 증가 없음 |
| 4 | 현재 시간 owner·활성 설정 한 묶음 | entry latency·quote consistency·refresh·Main 소비 | 기본/OFF/ON/원천 시계 차이를 선언하고 설정 하나만 바꿔 다른 한도에 막히는 누락 제거 |
| 5 | 조건별 age 후보 재생 | 저장 raw·기존 source quality·오프라인 연구 | past-only 0B/0D join, same opportunity 비교, invalid/UNKNOWN 및 위험 증가 공개 |
| 6 | 승인된 시간정책의 단일 영수증 | 준비→AI→Main→가격→실제 전송 | 적용 scope·policy/version·source 시각·검사 시각·현재 가격·원 deadline 일치; OFF는 observe-only |
| 7 | 최종 전송 직전 유효성 | 해당 Main ENTRY_BUY intent/transport owner | 자금 지연·auth retry·clock/quote 변경 주입 시 각 해당 전송의 계약 유지, 미전송/불확실 구분; SELL·긴급/보호청산·CANCEL·조회 영향 없음 |
| 8 | 자연 인과 확인 | 기존 evaluation/intent/terminal | 같은 비상시 기회의 source-ready→machine→PASS→Main→정상 submit 호출 비교; broker/체결/경제성은 별도 |

새 영구 Python 구현은 `src/engine/scalping`, 기존 WS 수신·trading/entry·market·order owner를 사용한다. engine root에 새 모듈을 만들지 않는다. 현재 연결과 기존 regression을 확장하며 새로운 비교용 실행 경로·퇴역 widget/episode worker를 만들지 않는다. 프로토콜·계좌·order call을 변경하는 구현 전에는 그때의 공식 upstream revision을 다시 확인한다.

이번 점검으로 새 상한을 선정하거나 운영 예외를 승인하지 않았다. 향후 적용 시에는 관련 모든 시간 owner의 exact 설정·code handoff·원 source policy와 함께 적용해야 한다. 다음 PID/자연 제출/체결 검증은 준비 코드 검증과 분리한다.

## 9. 이번 점검의 검증과 남은 한계

- 선택 코드 source-wait의 실제 함수에서 lost wakeup을 결정적으로 재현했다. 기존 관련 표적 검사 7개 PASS이며 production 수정은 없다.
- 앞선 전체 패턴 재생·32개 연구 검사를 반복하지 않았다. 새 age 민감도와 저장 0D의 작은 범위 검증은 [검토 결과 디렉터리](../../tmp/nonfixed-quote-ready-improvement-review-20261017/)의 별도 receipt로 보존한다.
- 문서 링크·역할/권한·공백 및 print-only backlog parser를 검증한다. 외부 Project/Calendar sync는 실행하지 않는다.
- 실제 지연 발생률·실제 stale 거절률, 조건별 적정 상한, 자연 제출 증가와 실현 수익 증가는 아직 입증하지 않았다. 과거/현재 설정과 PID 소비를 혼동하지 않고 현재 데이터로 입증되는 범위만 판단한다.

## 10. 구현 결과와 남은 수용 경계

10/17 사용자 구현·반복 코드리뷰 지시로 선택 commit `7f2552aedde8fec6ef904a43105827907e50dfc8` 기준 격리 작업본에 반영했다. [구현 리뷰](../audits/nonfixed-quote-opportunity-delivery-implementation-review-2026-10-17.md)가 원천 알림 경합·Main 및 probe의 bounded 0D-only 회복·현재 ask/스프레드·실제 POST 직전 검증·미전송 집계와 반복 리뷰를 소유한다. [현재 체크리스트](../checklists/2026-10-17-stage2-todo-checklist.md)의 `NonfixedQuoteOpportunityDelivery1017`이 코드 완료 owner다.

통합 표적 pytest는 1,610 PASS다. 기존 보고서 census 테스트 1건은 원 선택 릴리스에서도 같은 assertion으로 실패함을 직접 재현하여 변경 검증에서 제외하고 별도 영수증을 보존했다. Python21개 compile·미정의 이름 검사와 문서·parser·diff 검증을 완료했다.

0B/0D 저장 원천의 고정·조건부 age 후보는 비교했으나 새 운영 상한을 선정/발행하지 않았다. 이는 기존 700ms의 영구 고정도 승인된 완화도 아니다. 실제 경로의 시각·원천·현재 quote 검증과 조건별 정책 적용 계약이 후속 판단 근거다.

운영 정책 포인터·환경·선택 릴리스·배포·재기동·provider·주문은 변경/실행하지 않았다. V5/V6의 계산/검증 dependency에 회복 모듈을 포함했으므로 실제 전환 전에는 깨끗한 후보 commit에 대해 exact active-policy code handoff와 native parity를 새로 검증해야 한다. 기존 다음 세션 준비나 이번 테스트를 그 영수증·PID 소비·자연 제출·실현 손익으로 재사용하지 않는다.


## 11. 승인된 배포의 prepared 정책 코드 인계

2026-10-17 사용자가 배포 및 격리 정책 읽기·스키마·코드 호환성 검증을 명시했다. 기존 next-session 정책 수치/멤버십과 actual-PID 승인 경계를 유지한다. 새 시간상한 선정은 배포 선행 조건이 아니다.

`automation.prepared_policy_code_handoff`는 기존 완전 검증된 원 prepared manifest/env/verification과 당시 controller/summary/Main 정책 영수증을 내용 해시로 원본 보존한다. 같은 target의 기존 delay 및 incumbent-carry holding/stop 정책만 exact 원 정책 해시·원 코드 inventory·검토된 원/후속 코드 해시 쌍으로 인계한다. 현재 정책 파일은 별도로 불변 검증하고 숫자 successor·다른 날짜·변경 코드/증거·재선정은 거부한다. 과거 closure 보존은 현재 closure나 PID 소비가 아니다.

발행은 Main 부재와 release-set/selector 잠금 아래 수행하며, 네트워크 및 쓰기 경계가 있는 격리 namespace에서 native reader와 bootstrap을 실행한다. 실제 선택 전에 원 정책 의미 불변과 native 신호 parity를 확인한다. 변경 capability generation은 기존 독립 fixture producer로 새 검증을 발행한다. 기존 당일 PREOPEN/PID 기동 검증은 유지한다. 세부 결과는 [배포 검증 기록](../audits/nonfixed-quote-deployment-and-isolated-policy-review-2026-10-17.md)에 남긴다.
