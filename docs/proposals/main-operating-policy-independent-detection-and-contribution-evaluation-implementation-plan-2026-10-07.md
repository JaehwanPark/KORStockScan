# Main 운용 등록 정책 전체 독립 탐지·장후 기여도 평가 구현계획

## 1. 목적·선행조건·이번 작업 범위

2026-10-07 후속 실행 승인: 사용자가 이 계획의 구현·반복 코드리뷰·보완·배포와, 배포 완료 후 중단한 EOD 제외 장후 재개·모니터링·10/8 정상 기동 준비를 명시했다. 아래의 계획 작성 당시 보류/미승인 문구는 역사적 범위이며 이번 실행 승인 이후에는 적용하지 않는다. 원천일은 자정 이후에도 10/7로 보존한다. 현재 실행 owner는 `DirectFamilySourceRepairMainMechanisticEntry`이며 [구현·장후 인계 기록](../audits/main-operating-policy-implementation-and-postclose-review-2026-10-07.md)에 코드/배포/실제 비교/정책 준비/기동을 구분한다.

사용자 요청은 **다른 세션의 Main 복수정책·추가 8개 패턴 구현이 끝난 뒤 실행할 후속 구현계획 수립**이다. 이 문서는 계획이며 소스 구현·등록·실제 AI 호출·정책 발행·배포·재기동을 시작하지 않는다. 사용자가 선행 구현 완료 후 구현을 지시할 예정이다.

선행 문서는 [전 종목 복수정책 계획](main-all-scope-registered-multi-policy-implementation-plan-2026-10-07.md)과 [추가 8개 패턴 등록 계획](main-additional-eight-pattern-registration-after-multi-policy-implementation-plan-2026-10-07.md)이다. 10/7 선행 코드 `15f1ccd40e71c4bfeed2aa7979562fd3ab0f51f0`의 구현·배포 인계는 [추가 8개 구현 기록](../audits/main-additional-eight-pattern-implementation-review-2026-10-07.md)에 기록됐다. 8개 등록/정의 parity와 대상 865개 검증은 완료됐으며, 신규 8개 자동 선택은 0개였다. 장후 기동 시 native v4 정책 PID 소비 미관측과 코드 기동 확인을 구분한다. 실제 착수 때 최신 코드·부모·적용 상태를 N0에서 다시 인계받는다.

초기 재리뷰는 당시 작성 중이던 v4의 `configure`/`validate_claim`/`acknowledge`/`prepare_inputs`를 대조한 이력이다. 이번 원장 보완은 [공통 저장·증분 처리 계획](main-ai-comparison-ledger-dedup-and-incremental-storage-plan-2026-10-07.md)을 N4~N6의 선행 요건으로 연결한다. 아래는 후속 구현의 수용 조건이며 소스를 수정한 결과가 아니다. EOD 제외 장후 중단은 유지하고, 이번 계획 보완을 이관·실제 호출·배포 또는 장후 재개 지시로 해석하지 않는다.

계약 우선순위: 구 v3/v4 scope는 원 native 선택/primary/동률 현행 유지 계약을 유지한다. successor로 전환한 scope만 운용 목록 전체 탐지·복합 보조·이 문서의 권고 규칙을 사용한다. 공통 저장소는 두 계약의 자료를 함께 보존하지만 전략 의미를 선택하지 않는다. 원장 전환과 successor 전환은 서로 다른 변경 영수증으로 검증한다.

목표는 다음 네 가지다.

1. **운용 등록된 모든 정책**을 해당 종목·시장·route에서 독립 탐지한다. 성과 순위나 다른 정책의 반전 발생 여부로 평가 기회를 제한하지 않는다.
2. 같은 확인점의 다중 성립 근거를 보조판정에 함께 전달하고, 공통 보조판정·주문 의도는 각각 한 번만 만든다.
3. 장후는 개별 정책, 전체 합집합, 정책별 추가 기여도와 실제 보조판정 성과를 평가한다. 일별 순위로 운용 정책을 자동 탈락시키지 않는다.
4. 수동연구가 새 유형·특징·조건·확인 방식과 변경 버전을 정의한다. 장후는 고정 정의와 적용 버전을 평가하고 등록·교체·퇴역 권고를 만든다.

실행 owner는 [10/7 체크리스트](../checklists/2026-10-07-stage2-todo-checklist.md)의 `DirectFamilySourceRepairMainMechanisticEntry` 하나다. 별도 중복 OPEN을 만들지 않으며 착수일이 바뀌면 동일 owner에 미완료 조건을 인계한다. 선행 코드/계약/대상 검증 종결과 변경 소유 인계, **이 후속 계획에 대한 사용자 구현 지시**가 착수 조건이다. 미래 자연 신호·체결·수익·새 날짜를 기다리는 조건은 추가하지 않는다. 선행 세션의 기존 실행 승인은 그대로 유지한다.

## 2. 선행 구현에서 이어받을 것과 바뀔 것

| 항목 | 선행 8개 계획 | 이 후속 구현의 목표 |
| --- | --- | --- |
| 패턴 정의·root·확인점 | FIRST, momentum, breakout, hold, retest의 고정 의미 | 그대로 재사용; 수치·시점·라벨을 새로 탐색하지 않음 |
| 실시간 대상 | 장후 선택 portfolio의 branch 목록 | 명시적인 운용 등록 manifest의 모든 해당 branch |
| 중첩 신호 보조 입력 | 성과 순위로 정한 primary의 typed 입력 | 같은 확인점에 성립한 모든 정책의 typed 근거를 포함한 공통 입력 |
| 기계 장후 출력 | 비교한 조합 중 winner와 carry | 운용 목록 유지 + 개별/합집합/기여도 보고 + 수동 등록 권고 |
| 등록 권고의 동률 | 현행 조합 유지 | 같은 누적 승률이면 추가 확정 기회를 제공하는 후보를 우선 권고 |
| 보조 문구 평가 | branch/primary별 실제 요청 비교 | 합집합 확인점의 실제 복합 입력으로 고정 arm을 비교 |
| 정책 변경 | 선택 결과로 목록 변경 | 명시된 등록/교체/퇴역 변경으로 목록 변경; 평가 보고서 갱신과 분리 |

위 표는 **후속 구현에서 변경할 계약**이다. 완료한 8개 구현의 수용 증거를 소급 변경하지 않는다. 선행 구현에서 이미 충족한 기능은 다시 만들지 않고 인계 시 대응표로 확인한다. 순위에 따른 primary 귀속은 역사 자료를 읽기 위한 필드로 남을 수 있지만 신규 탐지·보조 입력·주문 권한을 결정하지 않는다.

## 3. 운용 등록 계약과 최초 전환 목록

### 3.1 연구 정의와 운용 등록의 분리

정의 catalog에 존재하는 것과 운용하는 것은 별도 상태다. catalog에는 연구 비교용 `ALL` 및 다수의 미선택 후보도 들어 있으므로 catalog 전체를 켜면 안 된다. 신규 상태는 다음처럼 구분한다.

| 상태 | 의미 | 실시간 탐지 |
| --- | --- | --- |
| `research_registered` | 수동연구 정의·원본·범위가 등록됨 | 없음; 격리 비교 대상 |
| `operating_pending` | 구체적인 운용 추가/교체안이 있으나 실행 계약/발행 준비 중 | 기존 유효 운용 목록 유지 |
| `operating_registered` | 검증된 실행 manifest에 포함되어 적용 대상임 | scope에 맞는 모든 정책 독립 탐지 |
| `paused` / `retired` | 명시적인 운용 중지·퇴역 기록 | 새 진입 탐지 없음; 과거 증빙 보존 |

개별 원천 결손·지표 하락은 등록 상태를 자동 삭제하지 않는다. 해당 원천으로 계산할 수 없는 정책/확인점만 결손 상태를 기록한다. source/계약 검증은 실행 의미를 보장하며 추가 경제성 적격 심사가 아니다.

`operating_manifest`의 최소 계약은 다음과 같다.

- manifest version·parent hash·effective date·변경 receipt와 ADD/REPLACE/RETIRE 대상.
- 정확한 symbol/group·market·session·price band·route/item 범위.
- policy ID/version·연구 정의 hash·실행 정의 hash·root/feature/phase 계약 hash.
- 공통 보조 입력/validator/arm binding과 비용·라벨 계약 hash.
- 변경 전후 목록 diff 및 불변 정의·원천 custody 참조. 동일 ID/version의 의미 변경은 거부한다.

서로 다른 조건이 겹치는 정책은 허용한다. 동일 정의의 중복 등록은 alias로 연결해 계산·호출을 중복시키지 않는다. 같은 패턴의 복수 버전도 명시적으로 병행 등록할 수 있으며, REPLACE는 기존 버전 제거와 새 버전 추가를 원자적으로 기록한다. 보고용 `pattern_family`가 같은 정책끼리 한 개만 선택하는 암묵적 제한은 두지 않는다.

### 3.2 최초 전환안

최초 목표 목록은 **N0에서 확인한 실제 운용 정책 + 선행 계획의 SA/SB/DA/HA/HB/AA/JA/GA 8개**다. 이미 운용 중인 항목은 한 번만 포함한다. 8개의 ID·정의 hash·경계·초기 scope는 [선행 계획 §2](main-additional-eight-pattern-registration-after-multi-policy-implementation-plan-2026-10-07.md#2-최초-등록-목록과-근거)를 그대로 사용한다. 이 문서에서는 중복 전사하지 않는다.

8개 신규 적용 범위는 연구된 **SOR REGULAR·정확한 `symbol_AL`**이다. 운용 구조는 전 종목·전 시장을 지원하되 PRE/AFTER나 다른 route로 8개 정의를 자동 복제하지 않는다. 기존 지원 scope·운용 정책은 보존한다. catalog의 나머지 비교 후보를 모두 운용 대상으로 확대하지 않는다. 추가 운용 요청은 정확한 목록 diff로 기록한다.

N0에서 원 정의·등록 상태가 다른 항목이 발견되면 그 차이를 표시하고 해당 항목의 인계를 해결한다. 현재 값으로 정의를 복원하거나 성과 순위가 낮다는 이유로 계획한 8개를 조용히 제외하지 않는다. 사용자 지정 초기 운용에 새 날짜·최소 표본·양의 EV·100%/80% 성공 보존 조건을 붙이지 않는다.

### 3.3 실행 세대와 성과 보고서의 분리

`execution_manifest_hash`는 정의·운용 목록·scope·root/phase·보조 binding 등 실행 의미에만 결속한다. `evaluation_report_hash`는 평가 source cutoff·W/F/U·권고 결과에 결속한다. 같은 정책의 보고 수치만 달라진 장후에는 실행 세대를 교체하거나 pending FSM/claim을 초기화하지 않는다.

정의·목록·보조 binding이 실제 바뀌면 parent CAS로 새 실행 세대를 적용하고 기존 세대의 pending/claim 처리 규약을 따른다. report hash를 실행 hash에서 분리해도 입력·코드·응답 provenance 검증을 생략하지 않는다. effective/date와 평가 as-of 날짜를 별도로 검증한다.

순환 hash를 만들지 않도록 `detector_manifest_hash`(정의·목록·scope) → exact 보조 요청/arm·응답 증빙 → 최종 실행 manifest 순으로 결속한다. 비교 요청이 아직 생성되지 않은 최종 선택 family hash를 요구하지 않게 한다. 일자별 source/readiness receipt는 별도 envelope로 묶고, 기존 세션 전환·epoch reset은 그대로 수행한다. 평가 파일의 날짜 변경과 실제 실행 의미 변경을 혼동하지 않는다.

publication 전체 hash와 별도로 각 scope의 `scope_execution_hash`를 둔다. 다른 종목/시장만 변경된 발행은 현재 scope의 동일 실행 계약을 무효화하지 않는다. 다만 활성 manifest의 무결성과 현재 scope가 가리키는 정의·code/보조 binding·source/guard 계약의 동등성을 검증한 경우에만 상태를 유지한다. 자기 scope 또는 공유 계산 코드가 바뀌면 영향을 받는 상태/claim을 무효화한다. 현재 v4의 family 전체 hash 검사를 생략하는 방식으로 구현하지 않는다.

hash의 정규화 필드 목록을 schema로 고정한다. 실행 의미 hash에는 성과 수치·평가 cutoff·증빙 파일 경로/mtime·매일 늘어나는 응답 원장 hash를 넣지 않는다. 증빙은 날짜/유효기간·현재 정책 적용 권한과 함께 publication/activation envelope에 결속하고 현재 envelope를 요청 전후 검증한다. 같은 arm의 새 평가 증빙만 생겼다고 FSM을 초기화하지 않지만, 만료되거나 무효인 현재 envelope를 실행 hash가 같다는 이유로 허용하지 않는다.

## 4. 모든 운용 정책의 동등한 독립 탐지

### 4.1 root와 특징 소비

- 유효한 동일 원천 이벤트를 해당 운용 정책 전체에 전달한다. FIRST가 없거나 다른 정책이 RECHECK/BLOCK이어도 momentum/breakout/hold/retest가 자체 조건을 평가한다.
- 공통 가격창·수량창·고저점 계산은 공유하되 anchor·pending·확인·소멸 상태는 정책/root 계약별로 유지한다. 동일 root를 공유해도 각 정책의 필터와 성립 여부는 별도로 남긴다.
- 원천 접두만 사용한다. 선행 계획의 첫 확인점, UNKNOWN 전이, 가격대 이동 추적, 실제 확인 시 scope 적용, 세션 anchor와 native epoch/sequence 규약을 보존한다.
- 정책 A의 전용 volume 특징 결손은 A에만 영향을 준다. 공통 quote/path/route가 무효이면 영향을 받는 모든 정책을 차단한다. 결손을 false/0으로 치환하지 않는다.
- 적용 범위 밖, warmup 부족, 조건 불충족, pending, confirmed, expired, source invalid를 구분해 기록한다. 다른 branch의 미성립을 공통 BLOCK 사유로 합치지 않는다.

현재 성과와 목록 순서를 바꿔도 같은 원천에서 정책별 확인점 집합은 같아야 한다. 첫 성공에서 평가를 중단하는 `break`, 성과순 top-K, primary-only 필터를 신규 운용 backend에 두지 않는다.

새 root는 검증된 동일 원천의 과거 접두로 warmup할 수 있지만 활성 시점 이전 확인점을 실시간 ready로 재발행하지 않는다. 복원된 anchor/window의 source identity와 원 정의를 검증하며, 접두가 부족하면 필요한 branch만 warmup/UNKNOWN으로 남긴다. 현재가로 세션 anchor를 새로 만들거나 UNKNOWN→TRUE를 임의 신규 전환으로 처리하지 않는다.

### 4.2 확인점 합집합·중복 제어

canonical opportunity key는 선행 native 규약의 `(stream_namespace, source_date, symbol, market/session, route, item, epoch, sequence)`로 고정한다. 정책 ID나 phase는 key에 넣지 않고 그 확인점의 근거 목록에 둔다. 같은 시각이어도 순번이 다르면 별도 확인점이며, stream 간에는 입증된 exact mapping 없이 시각 근접으로 합치지 않는다.

기존 v3/v4 digest의 namespace가 외부 source receipt에 있으면 원 ID를 고쳐 쓰지 않고 alias manifest로 새 key에 연결한다. 이 대응은 stream 간 시세를 합치는 추정 mapping이 아니다. 같은 native 확인점에 다른 phase가 있는 경우 기회는 하나여도 exact 요청은 서로 다를 수 있으며, 구 phase 응답을 새 union 응답으로 간주하지 않는다.

한 원천 이벤트의 모든 정책 평가가 끝난 뒤 `matched_policy_refs[]`와 `signals[]`를 봉인한다. 정책별 처리 순서에 따라 먼저 발견한 근거만 AI에 보내지 않는다. 동일한 source proof/특징의 alias는 근거를 한 번 담고 관련 정책 참조를 모두 보존한다. 같은 canonical key의 quote/가격/계보가 충돌하면 그 확인점의 계약 오류로 분리한다.

유효한 성립 정책이 하나 이상이면 기계 ENTER_NOW를 만들 수 있다. 이후 공통 보조판정과 정상 제출 경로의 intent는 각각 최대 한 번이다. 보조 VETO 뒤 다른 겹친 정책으로 재호출하지 않는다. registry 교체·재시도·재기동으로 같은 소비 완료 확인점이 새 주문 기회가 되지 않도록 아래 영속 계약을 연결한다. 다른 확인점도 기존 보유/미체결/수량/자본/cooldown/owner/manual veto/hard safety를 통과해야 한다.

현재 v4의 `_CLAIMS`/`ready.claimed`/`acknowledge`는 메모리 상태다. 이것만으로 재기동 중복 방지 완료를 주장하지 않는다. N0에서 기존 provider 원장·주문 의도 registry의 영속 보장 범위를 확인하고, 확인점과 기존 영속 소비자를 연결하는 최소 outbox/예약 기록을 보완한다.

이 실시간 예약/outbox는 오프라인 공통 비교 원장의 worker 예약과 별도 소유다. 정확한 원 요청·응답을 장후에 참조할 수 있어도 offline `responded`가 live claim/TTL/intent 완료나 주문 권한을 대신하지 않는다. 저장 공유를 위해 실시간 source/계정/주문 guard를 변경하지 않는다.

- consumer가 외부 호출 전에 canonical key를 원자적으로 예약하고 request hash·scope 실행 hash·상태를 결속한다. key에는 policy/arm/family 세대를 넣어 중복을 허용하지 않는다. callback은 이 저장 I/O를 직접 하지 않는다.
- 예약, 전송 여부 불확실, 응답 수신, intent 할당, 제출 진행/대사 완료를 구분하고 기존 provider/주문 원장 ID에 연결한다. 외부 전송과 로컬 저장은 하나의 트랜잭션이 아니므로 exactly-once 전송을 보장한다고 표현하지 않는다.
- 응답·주문 접수 여부가 불확실한 crash 구간은 기존 native 대사로 해결한다. 중복 정책·새 실행 세대·재기동을 이유로 자동 재전송하지 않는다. 미전송이 입증된 경우만 기존 허용 retry 계약 안에서 같은 논리 요청을 재개한다.
- 구 버전의 미해결 요청/intent를 새 버전 handoff에서 보존한다. exact source identity를 복구할 수 없는 과거 접두는 live 신호로 재발행하지 않고 warmup 용도로만 소비한다. 실제 새 transport epoch의 새 이벤트를 시각 근접만으로 과거 주문과 동일시하지 않는다.

신규 provenance는 `matched_policy_refs`·`still_valid_policy_refs`·`signal_set_hash`·`opportunity_key`를 판정→계획→intent→체결/완료까지 전달한다. 단일 `primary_branch`를 요구하는 후단은 union 참조를 읽도록 연결하며 임의 한 branch를 원인으로 기록하지 않는다. 실제 한 거래의 손익은 한 번 집계하고 관련 정책별 연결 통계는 합산 불가로 표시한다. 정책 중지/교체가 기존 보유 포지션의 custody·청산 계획을 삭제하지 않는다.

### 4.3 성능과 과부하

callback에서는 provider/REST/파일 I/O를 수행하지 않는다. 공유 window와 root 계산으로 비용을 줄이며, live pending/ready 한도와 offline 전수 재생을 구분한다. live 초과는 누락·지연 상태를 계측하고 성과순으로 정책을 잘라 정상 무신호로 표시하지 않는다. provider 대기 중 새 확인점은 자체 TTL을 지키며 모든 신호에 호출·제출을 보장한다고 주장하지 않는다.

선행 완료 코드와 같은 frozen tick 집합에서 callback p50/p95/p99/max, backlog·확인→평가 지연, claim 만료, pending 최고치·메모리를 비교한다. 기존 5초 claim 등 시간 계약을 늘려 성능 문제를 숨기지 않는다.

## 5. 다중 근거 보조판정 계약

### 5.1 입력·응답

새 보조 입력은 `common_context` 한 개와 `signals[]`로 구성한다. 공통 context에는 정확한 확인점·ask/quote·scope·평가시각·공통 목표/비용 조건을 넣는다. 각 signal에는 policy 참조, typed phase, 원 anchor/확인점, 당시 특징과 source proof를 넣는다. 하락 없는 breakout에 합성 저점·낙폭을 만들지 않는다.

입력 순서는 성과와 무관한 고정 식별자 순서로 정규화한다. 과거 승률을 특정 신호의 우선권으로 prompt에 넣지 않는다. 공통 사실과 동일 근거의 중복을 줄여 전체 성립 근거를 담고, token 한도 초과를 top-K 생략으로 해결하지 않는다. 용량을 넘으면 명시적인 입력 용량 결손으로 기록해 지원 계약을 보완한다.

보조판정은 **해당 공통 진입 기회의 위험을 PASS/VETO/CAUTION으로 평가**한다. 특정 branch를 winner로 다시 뽑지 않는다. 최종 English ASCII prompt/schema/validator를 고정하고 실제 요청 hash·응답 ID·근거 coverage를 검증한다. 응답에 선언된 signal 참조 집합 및 인용 사실이 봉인된 입력과 일치해야 한다. 이 검사는 참조 계약의 충족을 확인하며 모델 내부의 주의·추론을 입증하는 것으로 표현하지 않는다. 모델의 자유 해설만으로 coverage 완료를 인정하지 않는다.

구 primary 입력의 PASS들을 OR로 합쳐 새 복합 입력의 PASS를 만들 수 없다. 입력 구성·prompt·schema 등 실제 전송 내용이 달라지면 그 요청의 실제 응답으로 비교한다. validator만 변경됐다면 전송 key와 원 응답은 유지할 수 있으나 새 validation 결과를 별도로 만들고 계약상 재사용 가능한 경우에만 비교한다. validation 변경을 원 입력 변경으로 숨기거나 옛 유효성 결과를 복사하지 않는다. 과거 AI 자료는 원 계약 아래 보존한다.

### 5.2 응답 후 유효성

요청 전에 각 branch와 공통 quote/path/claim을 검증하고 `matched_at_request`를 고정한다. 응답 뒤에는 현재 실행 manifest, 공통 source/route/quote/TTL, 원래 포함된 branch들의 현재 claim을 다시 검사한다.

확인 시점의 `confirmed_set`, 요청 직전의 `matched_at_request`, 응답 직후의 `still_valid_at_response`와 각 탈락 이유/시각을 구분한다. 같은 확인점에서 새 성립 branch를 뒤늦게 덧붙이지 않으며, 요청 전 무효화된 근거를 AI 입력에 정상 근거로 남기지 않는다.

- 새 계약에서 보조 PASS는 봉인한 시점의 모든 사실을 바탕으로 한 **공통 위험 판정**이다. 유효한 기계 근거는 응답 시점에 원래 집합 중 적어도 하나가 남아 있어야 한다.
- **공통 5초 이내에서 FIRST의 최신 반전 상태만 무효화**됐고 같은 확인점의 독립 breakout 근거는 유효한 경우를 branch별로 재검증한다. 공통 시각을 가진 FIRST만 시간 만료되고 breakout의 5초가 새로 시작하는 것으로 해석하지 않는다. `matched_at_request`와 `still_valid_at_response`를 모두 남긴다.
- 공통 claim 시간이 만료되거나 공통 hard/source 계약이 깨지면 모든 근거의 진행을 막는다. branch별 TTL을 재기산하지 않는다. 원 입력의 모든 branch가 무효화돼도 진행하지 않는다. 요청에 없던 branch·확인점을 사후에 끼워 넣지 않는다. 발행 세대가 바뀐 경우에는 §3.3의 현재 scope 실행 계약 동등성을 검증하며 다른 내용의 scope로 응답을 전용하지 않는다.
- 구 primary PASS에는 이 규칙을 소급 적용하지 않는다. 공통 위험 판정 의미와 응답 후 branch별 검증이 구현·검증된 신규 계약에서만 사용한다.

응답 schema에는 공통 위험 판정이라는 역할을 명시한다. 특정 branch의 존속을 PASS 전제조건으로 거는 응답을 그대로 다른 branch의 허가로 해석하지 않는다. 인용 사실 변조·공통 위험 근거의 소멸·역할 위반은 기존 invalid response/source 경로로 처리한다. 새로운 전송 없이 원 응답을 부분집합 입력에 대한 새 응답인 것처럼 재작성하지 않는다.

### 5.3 장후 보조 비교

고정된 arm 목록을 정확한 scope의 **합집합 기계 적격 확인점**에서 동일 복합 입력으로 비교한다. 기존 arm을 재사용해도 최종 문구/input/schema가 바뀌면 새 버전으로 고정한다. 조합별로 새 prompt 가설을 자동 생성하지 않는다. 입력 projector는 미래 label/도달 시각·실현 결과·연구 승률을 읽지 않는 allowlist 방식으로 만들고, label은 별도 평가 테이블에서 exact 확인점에 결합한다.

입력 모집단과 실제 비교 호출 모집단을 명시적으로 분리한다. 입력 manifest는 유효한 기계 확인점 전체를 W/F/U 구분과 함께 계수한다. 초기 장후 성과 비교용 신규 호출은 입력 계약이 유효하고 라벨이 확정된 W/F 확인점×고정 arm 전체를 대상으로 하며, ENTER/PASS 로그·성과 순위·W만으로 좁히지 않는다. U는 `outcome_unresolved_no_comparison_request`로 별도 계수하고, 그 때문에 무기한 전수 호출 대기를 만들지 않는다. 장중 자연 응답은 U라도 보존하고 후속 유효 라벨 확정 때 같은 요청의 응답을 재사용할 수 있다.

이때 전송 request key는 고정 확인 입력·phase 의미·prompt/schema·provider/model/endpoint·생성 설정에 결속하며 미래 label/보고서 hash는 포함하지 않는다. validator 계약과 검증 결과는 별도 validation key로 결속해 응답 재사용 적격을 판단한다. 모델 입력에 시간 필드가 있다면 확인 당시 고정값을 사용하고 장후 실행 시각으로 바꾸지 않는다. 새 label snapshot은 같은 응답을 다시 평가할 수 있지만, 변경된 입력의 응답을 재사용할 수는 없다. input census는 row 제거 전에 만들고 `전체 = 비교 요청 대상 + U 보류 + 입력 결손/충돌`의 원인별 회계를 닫는다.

공통 저장에서는 **객체 공유와 응답 재사용을 구분**한다. 여러 안에서 같은 시장 context·prompt/schema는 한 번 저장할 수 있지만, matched 근거·phase·관측 의미·최종 요청 bytes가 달라지면 별도 request와 실제 응답이 필요하다. raw 응답을 공통 보존해도 validator가 바뀐 비교는 그 계약으로 다시 검증하며, 원 비교의 유효성/분모를 소급 바꾸지 않는다. 사전에 봉인한 expected membership에서 작은 request 참조/상태를 준비하고 호출 직전에 본문을 조립한다. `expected = planned + reserved_uncertain + responded + failed + missing`을 대사하며 `missing`을 valid-empty로 처리하지 않는다.

expected owner의 비교 상태와 request의 복수 attempt 상태는 별도로 센다. 완료 응답이 있다고 다른 불확실 attempt가 사라지지 않으며 response ID가 없다고 미전송인 것도 아니다. 각 안은 응답 수신 cutoff·실제 선택한 응답/validation·label을 불변 snapshot으로 봉인한다. 뒤늦은 응답·정정은 새 revision이며 유리한 PASS만 골라 원 결과를 갱신하지 않는다. 비교 가능 표본은 기대 집합의 같은 확인점×전체 고정 arm으로 대사하고, 부분 응답 표는 진단으로만 내보낸다.

입력의 source proof는 실제 소비한 접두/quote·계약에 결속한다. 미래 관측이 추가된 전체 컨테이너 hash는 외부 source manifest에 남기고 과거 모델 입력에 미래 정보로 넣지 않는다. 새 manifest에서도 동일 입력 접두가 입증돼야 캐시를 재사용할 수 있다. 응답이 terminal 실패/무효 schema인 것은 정상 비교 응답이 아니며, 원장 종료와 성과 비교 가능 상태를 구분한다. 일부 arm의 실패 표본만 빼서 비교 분모를 유리하게 만들지 않는다.

준비한 요청의 context·signals·arm·serializer 참조를 불변 객체로 보호해 호출 시 원 bytes를 재조립한다. 현재 자료로 다시 투영하지 않는다. source 정정은 앞의 rolling/root/session anchor와 뒤의 30분 label 의존성을 따라 인접 partition까지 갱신한다. raw 보존 종료 여부와 planned/expected 객체의 보존 종료 여부를 따로 검증하며 입력 객체가 없으면 해당 요청의 materialization 결손을 명시한다.

원천 재생의 확인 즉시 평가와 실제 전달 지연 후의 입력은 다른 관측이다. 확인 즉시 복합 입력 결과는 `confirmation_replay`로, 실제 요청 당시 근거 집합/지연/quote가 보존된 결과는 `delivered_live`로 표시한다. 실제 요청 원본 없이 지연 후 AI PASS를 재현했다고 주장하지 않는다. 같은 composer를 사용해도 두 입력의 내용 hash가 다르면 응답을 혼용하지 않는다.

실제 응답이 있는 공통 비교 모집단에서 `PASS 후 W / PASS 후 확정 결과`를 계산하고 PASS 수·미확정·VETO/CAUTION이 제외한 W/F를 함께 표시한다. 같은 승률의 보조 arm은 추가 확정 성공을 제공하는 더 많은 확정 PASS 기회를 우선 비교하고, 개선이 없으면 현행 binding을 유지한다. 0% 동률에서 실패 PASS만 증가한 arm을 기회 확대라고 권고하지 않는다. 완료한 arm끼리만 비교해 전수 winner인 것처럼 발표하지 않으며 expected input×arm census와 actual terminal을 대조한다.

모든 유효 응답이 VETO/CAUTION으로 확정 PASS가 0인 `completed_no_pass`, 보존한 자연 PASS 결과가 모두 U인 `completed_unresolved`, 유효 source를 읽었으나 해당 확인점이 0인 `valid_empty`, source 읽기/계약 실패 `source_gap`, 예상 응답 누락 `incomplete`를 구분한다. 빈 파일이나 읽기 실패만으로 valid-empty를 선언하지 않는다. 앞의 세 상태에 임의 0%/100% winner를 만들지 않는다. arm 간 승률 비교도 정수 분자/분모를 사용한다.

단일 union 응답을 각 정책이 별도로 받은 응답처럼 합산하지 않는다. 정책별 관련 응답은 연결 분석으로 표시한다. 정책을 뺐을 때 AI 결과가 바뀌는 효과는 그 변경된 입력의 실제 응답이 있어야 계산할 수 있다. 기계 leave-one-out 계산만으로 AI 인과 효과를 주장하지 않는다.

무표본 scope는 0%로 만들지 않는다. 기존에 허용된 동일 유형 정규장 승계가 있으면 새 복합 입력 계약을 지원하는 binding만 그 규칙에 따라 승계하고 출처를 표시한다. 새 날짜를 기다리는 수익성 gate를 만들지 않으며, 호환 binding 자체가 없으면 해당 scope의 실행 계약 결손으로 인계한다. 미완료 비교는 검증된 기계·보조 쌍을 carry하고, 준비한 신규 운용 목록을 적용 완료로 표시하지 않는다.

### 5.4 등록안과 기계·보조 결합 성과

운용 목록을 바꾸면 새 기회뿐 아니라 기존 중첩 확인점의 AI 입력도 바뀔 수 있다. N6 비교 대상은 **실제 현행 운용안·동일 목록의 successor 복합판정안·8개 각각 추가안·8개 일괄 추가안·명시된 교체안**으로 고정한다. 실제 현행안은 원 native 탐지/primary/보조 binding으로 재생하고, 나머지는 새 복합 입력으로 비교한다. 이전 요청 bytes와 응답을 보존하며 새 입력으로 계산한 값을 실제 현행 보조 성과라고 부르지 않는다. 이렇게 탐지 목록 효과와 보조 계약 전환 효과를 나눠 보고한다.

각 안의 전체 union 확인점을 집계하고 §5.3의 W/F 요청 대상에서 실제 응답을 비교한다. identical 요청은 provider 한 번으로 공유하되 비교안별 owner 연결을 보존한다. 원천/정의/입력/모델/validator가 다른 안의 cache를 섞지 않고 2^N 부분집합 탐색을 추가하지 않는다.

동일 날짜를 신규 schema로 비교한다는 이유로 v5 전용 전체 요청 DB를 만들거나 v3/v4 원장을 통째로 복제하지 않는다. 공통 저장소에 없는 exact 요청과 변경된 membership/label partition만 추가하고, 나머지는 불변 참조로 재사용한다. 같은 기회라도 추가/제외 정책 때문에 복합 입력이 바뀌면 새 실제 호출 대상이다. 옛 개별 PASS를 OR하여 새 복합 PASS로 대체하지 않는다. quota=None과 전체 eligible 비교는 유지하며 고유 요청·owner·attempt·응답·저장량 증가분을 각각 공개한다.

장후 호출 순서는 명시적 운용 추가(`add_all − successor_same`)가 있는 scope의 일괄안·개별안·현행 대조군을 우선한다. 나머지 exact expected 요청도 같은 큐에 유지하며 제외하거나 완료 처리하지 않는다. 이는 최초 전환의 비교가 대규모 현행 모집단 뒤에서 발행창을 소진하지 않도록 하는 스케줄 순서이며 승률·결과·표본 크기로 대상을 선별하는 규칙이 아니다. 실제 전송 identity·원 응답·uncertain 중복 방지·quota=None·동시성/시간 보호는 유지하고 우선 비교 ID를 호출 종료 영수증에 기록한다.

보고서는 각 안에 대해 기계 union W/F/U·승률, 실제 AI PASS W/F/U·승률, 새로 확보/제외된 PASS의 W/F, 미비교 응답을 나란히 보여준다. 특히 기계 확인점이 같아도 근거 구성이 바뀌어 PASS가 줄어드는 경우를 탐지한다. 기존 기계 승률 개선 권고와 보조 후 성과가 반대이면 `machine_auxiliary_tradeoff`로 표시하고 종합 우월이라고 요약하지 않는다. 최초 사용자 지정 목록을 새 경제성 gate로 자동 거부하지 않으며, 추가/교체 권고에 실제 비교의 적용 범위와 미완료를 표시한다.

## 6. 장후 성과를 평가할 기준

### 6.1 공통 모집단과 라벨

평가는 유효 clean baseline 이후 **보유 누적 원천**으로 한다. 소실 자료를 복원했다고 간주하거나 새 수집을 선행 요구하지 않는다. frozen source manifest·제외 row/window·native mapping·code/definition/label hash·cutoff를 고정하고 비교 대상 모두 같은 원천으로 재생한다.

기계 평가는 당시 기계·AI의 통과 로그에 한정하지 않는다. 등록된 각 고정 정책을 유효 연속 원천에 재생하여 그 정책의 확인점 집합을 구한다. 연구 때 추가점 수치나 옛 baseline 결과를 현재 전체 성과로 재사용하지 않는다.

목표 계약은 선행 family의 **실제 확인 ask 기준, 1,800초, 비용률 0.0023, 비용 후 목표 +0.4%·soft 손절 -3% 선도달**을 그대로 사용한다. 정확한 비용/도달/분봉 보조 계산은 native label producer를 재사용한다. 10분 미도달을 즉시 실패로 종료하지 않고 계약상 30분 경로와 유효한 후속 가격 보조를 소비한다.

| 기호 | 집계 |
| --- | --- |
| W | 유효 관측에서 목표 선도달 |
| F_stop | 손절 선도달 |
| F_timeout | 계약상 전체 구간이 유효하게 관측됐지만 목표 미도달 |
| U | 경로·quote·계보 결손, 검열, 순서 불명 등 미확정; 이유별 별도 |
| 누적 raw 승률 | `W / (W + F_stop + F_timeout)`; 분모 0이면 null |

이 값은 확인점의 가격 경로 성과다. 실제 거래 승률·실현 수익률로 표시하지 않는다. U/결손은 F나 0%로 바꾸지 않는다. 동일 확인점에서 정책별 라벨이 다르면 합집합 계산 전에 계약 충돌을 해결한다. 한 날·한 종목·동일 목표 도달 시각에 집중된 점들은 별도 집중도/episode 수로 보여주며 독립 거래 수로 표현하지 않는다.

**탐지 결손과 결과 U도 분리한다.** 각 정책의 적용 가능한 원천 접두에서 판정은 TRUE/FALSE/UNKNOWN이다. 기계 OR는 하나라도 TRUE면 TRUE, TRUE 없이 UNKNOWN이 있으면 UNKNOWN, 모두 정상 FALSE일 때만 FALSE다. UNKNOWN인 정책을 미성립으로 처리하면 기존 정책의 독점 기회와 신규 추가 기회를 과장할 수 있다. `confirmed_opportunity_unresolved_outcome`과 `detection_unknown_window`를 다른 필드로 남긴다.

정책 p의 독점 기회는 p가 TRUE이고 다른 해당 정책이 모두 정상 FALSE임을 확인한 점에만 확정한다. 다른 정책에 UNKNOWN이 있으면 `exclusive_unproven`이다. baseline/변경안 비교는 양쪽 판정이 가능한 동일 row/window 범위를 식별해 재계산하고, 원래 baseline 전체 수치·비교 범위 수치·제외된 baseline W/F/U를 함께 제시한다. 제외 불가능한 source 계약 실패는 그 scope의 비교 불가로 표시한다. 특정 후보만 결손 행을 빼서 좋아진 승률을 전체 성과 개선으로 발표하지 않는다. 이 격리는 새 표본/날짜/성공 보존 문턱이 아니다.

확인점별 근거와 source 구간 mask/제외 원인·계수를 불변 manifest로 보존해 이 회계를 재현한다. 전체 틱×정책의 FALSE/UNKNOWN을 모두 개별 JSON으로 쌓는 방식은 요구하지 않는다. 구간 압축/스트리밍 집계 후 원천 수·정책별 평가 가능 수·확인점 수가 대조돼야 한다.

### 6.2 개별·합집합·기여도

동일 비교 범위 D에서 정책 p의 유효 확인점 집합을 `S_p(D)`, 전체 운용 집합을 `U_all = union(S_p)`로 정의한다. 위 표의 미확정 U와 집합 이름 `U_all`을 보고서 필드에서 혼동하지 않는다.

| 평가 | 계산·의미 |
| --- | --- |
| 개별 정책 | 각 `S_p`의 W/F/U·승률·오늘/누적 확인점; 겹침을 포함한 단독 패턴 성과 |
| 전체 운용 | `U_all`의 canonical 중복 제거 W/F/U·승률; 현재 제공한 전체 기회 |
| 정책의 독점 기회 | 비교 가능한 범위에서 `S_p - union(S_q, q!=p)`; 다른 정책의 UNKNOWN은 독점 미입증으로 별도 |
| 제외 전후 차이 | 전체와 p를 뺀 합집합의 승률·확정 기회 수 차이; 기계 기여도 |
| 신규 추가 효과 | 기존 `U_all`, 후보 `S_new`, `U_all union S_new`와 교집합/추가 W/F/U |
| 교체 효과 | 명시된 제거·추가 목록을 반영한 집합과 기존 집합을 같은 원천에서 비교 |

중복이 큰 정책은 개별 성과가 좋아도 독점 기회가 0일 수 있다. 그 값으로 자동 퇴역시키지 않는다. 개별 독점 기여도만으로 여러 정책을 한꺼번에 제거하면 공유 기회가 사라질 수 있으므로 명시된 변경 묶음의 합집합도 계산한다. 8개 각각·8개 전체 추가안·실제 운용안 등 정해진 비교만 수행하고 모든 부분집합 탐색으로 새 정책을 자동 만들지 않는다.

표는 삼성·4개 고정 종목·일반 비삼성 유형, market/session·가격대·route별로 분리한다. 전체 pooled 수치는 진단 요약이며 서로 다른 scope의 증감을 한 승률로 상쇄해 등록 권고하지 않는다. 보고 기간은 당일, 누적, 연구에 사용한 기간, 등록 이후를 구분한다. 등록 이후에도 원천 재생 결과와 실제 PID 적용 기간 관측 결과를 별도로 보여준다.

### 6.3 수동 등록·교체 권고 규칙

1. 현재 운용 목록을 부모로 고정하고 기존안과 변경안을 동일 누적 source/라벨에서 비교한다.
2. 누적 raw 승률이 더 높은 안을 우선 권고한다. 정확한 정수 분자/분모로 비교하며 표시용 반올림 때문에 동률로 만들지 않는다.
3. 승률이 정확히 같으면 **추가 확정 성공을 포함해 확정 확인점이 증가하는 안**을 우선 권고한다. 미확정만 증가하거나 0% 동률에서 실패만 증가한 경우는 성과 개선으로 권고하지 않는다. 승률·확정 기회가 모두 같으면 현행 유지 권고다. 이는 동률 정렬의 실패 증가 방지 규칙이며 별도 최소 표본/일수 기준을 만들지 않는다.
4. 교체로 기존 W 일부가 사라져도 새 승률이 높으면 100%/80% 보존율 때문에 탈락시키지 않는다. 잃은 W와 새 W/F/U는 공개한다.
5. 분모가 없는 비교는 `not_comparable`로 남기고 0% baseline으로 순위를 만들지 않는다. 사용자 지정 운용은 별도 명시된 목록으로 처리하며 최소 표본·일수·holdout·양의 EV를 추가하지 않는다.

설명용 예: 기존 80W/20F일 때 새로운 **겹치지 않는 확정점**이 9W/1F면 89/110=80.91%, 8W/2F면 88/110=80%, 7W/3F면 87/110=79.09%다. 첫째는 승률 개선, 둘째는 동률 기회 확대 권고이며 셋째는 단순 추가 권고 대상이 아니다. 이 예는 현재 데이터의 계산 결과가 아니다.

이 규칙은 수동연구 후보의 등록/교체 권고와 고정 보조 arm 비교를 구체화한 후속 제안이다. **이미 운용 등록된 정책을 장후가 매일 순위로 자동 제외하는 규칙이 아니다.** 순위 하락은 검토할 근거를 만들며 실제 운용 목록 변경은 명시된 변경 receipt를 따른다.

### 6.4 실행 성과와의 연결

동일 기회에 대해 기계 탐지→보조 실제 응답→제출→체결→완료를 연결하되 분모와 원인을 구분한다. 기계 미탐지, 전달 지연, 보조 VETO, broker/자본/보유/미체결 제약을 같은 정책 실패로 합치지 않는다.

실현 PnL은 `COMPLETED + valid profit_rate` 및 정확한 비용/수량/owner 증빙으로만 집계한다. 가격 경로 W를 비용 증빙이 있는 실현 수익으로 대신하지 않는다. 복수 정책 추가로 실제 주문 순서·보유·자본 점유가 달라질 수 있으므로 기계 합집합의 W 보존이 실제 수익 보존을 뜻하지 않는다. 제출 이후 기계 결함이 아닌 개선 연구는 별도 과제로 인계한다.

## 7. 수동연구·장후·실시간의 역할과 생산물

| 단계 | 수행 작업 | 고정·보존할 자료 |
| --- | --- | --- |
| 수동연구 | 새 root/유형/조건/확인 방식·변경 가설 탐색 | 정의 원본·연구 기간·source/code hash·discovery 결과 |
| 등록 준비 | 고정 정의의 native 지원·현재 합집합 대비 추가/교체 비교 | 원 정의↔실행 정의 대응·scope·비교 W/F/U·등록 제안 |
| 운용 등록 | 명시된 목록 변경과 보조 binding을 원자적으로 발행 | execution manifest·parent CAS·effective date·change receipt |
| 실시간 | scope에 맞는 운용 정책 전부 탐지·복합 근거 1회 AI·1 intent | 원천→모든 성립 policy→입력/응답→유효 claim→실행 계보 |
| 정기 장후 | 고정 정책/장중 적용 버전 재생·성과/기여도·고정 arm 비교 | 평가 snapshot·actual response ledger·권고·실제 적용 census |

정기 장후는 새로운 threshold/grid/feature 조합을 탐색하지 않는다. 조건 변경이 필요하면 수동연구의 새 ID/version으로 돌아간다. 연구 기간을 쓰고 등록 이후 성과를 분리하는 것은 과적합을 드러내기 위한 보고이며 새 날짜를 기다리는 채택 gate가 아니다.

장후 산출물에는 다음이 필요하다.

- `operating_membership`: 기존 목록·명시 변경·실제 발행 목록·pending 차이.
- `policy_metrics`, `union_metrics`, `contribution_metrics`: W/F_stop/F_timeout/U·분모·겹침·집중도·scope.
- `candidate_comparisons`: 고정 parent 대비 추가/교체 효과와 권고 근거; 자동 membership 변경 없음.
- `auxiliary_comparison`: exact 복합 input×arm expected census·실제 응답·PASS 성과·carry 사유.
- `combined_comparison`: 현행/각 추가/일괄 추가/교체안의 기계 성과와 실제 AI 후 성과·교환관계.
- `applied_version_census`: 날짜·시간별 실제 적용 manifest·정책/보조 버전; 소급 적용으로 표시하지 않음.
- `coverage_and_delivery`: source 결손, 정책별 평가 가능 수, 확인→평가 지연, 누락/초과/미관측.

기계 목록이 같고 보조 binding도 같으면 보고서만 갱신한다. 고정 arm의 실제 비교에 따라 binding이 변경되는 경우에는 새 실행 세대를 발행한다. 등록되지 않은 정책을 장후의 성과 순위만으로 활성화하지 않는다.

## 8. 구현 위치·버전·자동화 인계

N0에서 최종 v4의 module pin과 dispatcher를 다시 조사한다. 기본안은 실행 manifest와 복합 보조 의미를 구분하는 **successor schema(v5 예정)**다. 최종 선행 schema가 다르면 이름만 대응시키고 새로운 의미를 기존 불변 family에 덮어쓰지 않는다.

| 소유 경계 | 현재 확인한 연결 지점 | 후속 작업 |
| --- | --- | --- |
| 정의·manifest·검증 | `src/engine/scalping/continuous_reversal_policy_v4.py`, `reversal_path_catalog.py` | 신규 실행 manifest/운용 목록 validator, 구 family 원 생성 증빙 검증 |
| 실시간 | `reversal_path_runtime.py`, `reversal_policy_backend.py` | 전 운용 branch·공유 root·완결된 matched 집합·scope 세대·기존 영속 소비자와 claim/ack 연결 |
| 보조 | `reversal_path_auxiliary.py`, `src/engine/ai_engine_openai.py` | 복합 schema/prompt/validator·정확 cache·응답 후 branch별 재검증 |
| 장후 | `continuous_reversal_path_postclose.py`, `continuous_reversal_postclose.py` | winner→운용 목록/기여도 보고 분리, UNKNOWN 비교 범위·고정 후보의 결합 AI 비교 |
| Main 소비 | `continuous_reversal_policy.py`, `mechanistic_entry_runtime_policy.py`, `src/engine/sniper_state_handlers.py` | 새 schema compose·freshness·정상 submit path·durable dedup |
| 기동·발행·감시 | `src/engine/automation/postclose_summary_handoff.py`, `intraday_release_handoff.py`, `src/engine/error_detectors/artifact_freshness.py`, `src/engine/monitoring/submission_bottleneck_monitor.py` | 실행 목록/평가 보고/복합 phase와 원천 경고를 구분해 native 검증 |

위 파일은 구현 중 조사한 연결점이며 최종 완료 파일/함수 목록은 N0가 소유한다. 새 live/계약/장후 코드는 역할에 맞는 기존 `src/engine/scalping` 패키지를 우선 사용하고 테스트는 `src/tests`에 둔다. `src/engine` root에 새 모듈을 만들지 않는다. 선행 hash 고정 파일을 변경해야 하면 새 모듈과 버전 adapter 또는 입증된 역사 reader 경계를 사용하고 임의 hash 허용을 하지 않는다.

새 report/custody와 논리적 비교 membership은 successor namespace에 두고 v4 결과를 덮어쓰지 않는다. **물리적 요청·응답 저장소는 정책 schema와 독립된 공통 저장소**를 사용하며, 버전 변경마다 대형 ledger/공통 context/index를 복제하지 않는다. 같은 날짜라도 definition·membership·source·prompt·response 내용 hash가 다르면 새 비교 snapshot이지만 기존 내용 객체는 참조한다. provider 실행은 공통 영속 예약·writer/lease·exact cache·증분 checkpoint를 사용한다. 기존 v3/v4의 별도 lock을 전역 lock으로 간주하지 않으며 cutover 시 모두 차단·대사한다. timeout/불확실 예약을 완료나 미호출로 간주해 중복 호출하지 않는다. 원장 준비 전 expected census를 만들어 누락을 검출한다. 원천 결손은 특정 row/window/scope에 격리한다.

공통 offline 저장 구현은 기존 `src/engine/ai/` 역할 패키지, Main 비교 adapter는 `src/engine/scalping/`, 검증은 `src/tests`가 소유한다. 실제 위치는 L0/N0의 인접 소비자 조사 후 확정하며 engine root를 늘리지 않는다. 과거 모듈 pin·불변 exports는 보존하고, 새 adapter로 prepare/calls/report/export/native validator/strict/PREOPEN/retention까지 연결한다. rollback에도 새 저장소에서 발생한 예약/응답을 보존해야 하므로 오래된 DB 사본만 복원하는 절차는 금지한다. 상세 이관·보존·GC는 공통 원장 계획 §6을 따른다.

별도 경쟁 cron/장후 writer를 추가하지 않는다. 기존 stage dispatcher에 신규 소비를 연결하고 같은 change set에서 해당 operating 문서와 실행일 checklist를 갱신한다. 구현 시점 자동화 변경에 해당하는 문서만 수정한다. 이 계획 작성으로 baseline README/Rebase/AGENTS를 갱신하지 않는다.

### 8.1 일부 scope carry와 혼합 버전 소비

현재 v4는 family 단위 schema와 branch별 보조 payload를 검증한다. 신규 복합 입력과 호환되지 않는 옛 payload를 v5 payload인 것처럼 포장해 carry하지 않는다. successor 발행 envelope는 scope마다 native schema/backend·불변 parent family·scope payload hash를 참조할 수 있어야 한다.

| scope 상태 | 실제 실행 대상 | 보고 상태 |
| --- | --- | --- |
| 신규 기계·복합 보조 준비 완료 | successor 운용 목록과 같은 계약의 보조 binding | `operating_union_active` |
| 신규 비교/실행 계약 미완료, 검증된 구 쌍 존재 | 원 native reader로 검증한 구 기계·보조 쌍 | `legacy_pair_carried`, 계획한 신규 목록은 pending |
| 검증 가능한 신·구 쌍 모두 없음 | 해당 scope의 신규 진입 권한 없음 | 정확한 계약 결손; 다른 scope를 정상으로 위장하거나 함께 실패시키지 않음 |

한 확인 scope에는 권한 backend가 하나다. 가격대 간 root warmup을 공유해도 같은 이벤트를 신·구 backend가 각각 주문 권한으로 claim하지 못하게 한다. 두 native 계약의 검증/dispatch/응답 후 재검증과 공통 canonical 예약을 함께 연결한다. 이전 schema의 원 source/code 검증은 유지한다.

필수 지원 scope에 신·구 유효 쌍이 모두 없으면 그 사실을 보고하되 **불완전 새 bundle을 활성화하지 않는다.** native coverage validator가 요구하는 전체 범위를 채운 candidate만 parent CAS로 전환한다. 그동안 기존 유효 bundle은 자체 계약 범위에서 유지한다. 특정 source 결손을 다른 정상 scope의 기계 실패로 확장하지 않는 것과, 발행 bundle의 필수 coverage를 생략하는 것은 별개다.

승계는 검증된 parent를 참조하고 명시 중지·퇴역된 정책을 되살리지 않는다. 신규 목록을 검증 없이 부분 적용하지 않으며, 어떤 scope가 carry인지 runtime/bootstrap/장후/감시에서 동일하게 표시한다. 최종 인계는 `계획 scope 수 / 신규 준비 수 / 실제 신규 소비 수 / 구 쌍 carry 수 / 계약 결손 수`를 제시한다. code 완료와 전 scope 새 방식 운용 완료를 같은 상태로 표시하지 않는다.

## 9. 실행 순서와 완료 기준

| 단계 | 작업·산출물 | 종료 기준 |
| --- | --- | --- |
| N0 | 선행 최종 commit/검증·정의 registry·48셀/실제 지원 route·현재 및 적용 이력·writer/영속 원장 소유 인계 | 8개 구현과 충돌 없는 기준 고정; 선행 미완료/자연 미관측·메모리/영속 계약 차이 및 L0 원장 상태 충돌·consumer 인계 |
| N1 | 운용 목록/평가 분리 schema·최초 active+8 diff·등록/교체/퇴역 계약 | catalog 전체 활성화 없음; 정확 scope·원 정의·parent 대조 |
| N2 | 독립 탐지·matched 집합·공통 확인점·durable dedup | 순서/승률 불변성, 모든 등록 branch 소비, FIRST 없는 지속형 검증 |
| N3 | 복합 보조 입력/arm/validator·응답 후 재검증 | 합성 사실·구 PASS 재사용·VETO 뒤 우회 호출 없음 |
| N4 | 개별/합집합/기여도·권고·고정 비교안의 복합 AI producer·공통 원장 adapter | UNKNOWN·공통 비교 범위·수작업 집합 fixture 일치, expected census·지연 본문·partition 증분·부분 carry·hash 검증 |
| N5 | 자기 리뷰→보완→재리뷰·대상 pytest/compile/diff | N7의 소비자/발행/혼합 scope 연결까지 fixture 검증 후 in-scope finding 0; 공통 원장 L1~L5·중단/재개·실시간 소유 분리 검증; 비싼 실행 전 gate |
| N6 | frozen 누적 원천 replay·현행/각 추가/일괄 추가안의 exact 복합 AI 실제 비교 | 실제 호출은 L6의 공통 writer 전환 영수증 이후 차집합만 실행, expected 회계·기계/보조 W/F/U/차이·디스크 증가분 보고; incomplete를 성공 처리하지 않음 |
| N7 | stage/loader/장후/감시·정상 기동 준비 통합 검증 | 소비자 구현/가짜 transport 검증은 N5 전에 완료; N6 이후 실제 생성 artifact로 구 family·혼합 scope carry·필수 coverage·새 manifest/쌍·rollback 최종 검증 |
| N8 | 당시 승인된 발행/배포/기동 후속 인계 | code·선택/등록·배포·PID·자연 신호·실현 성과를 별도 보고; 사용자 장후 중단 override를 별도 재개 지시 전 유지 |

N6의 원천 재생은 N5와 공통 원장 L1~L5 검증 후 진행한다. N6의 실제 provider 예약은 추가로 L6의 store pointer·단일 writer/fencing 전환이 확인된 공통 원장만 사용하며 별도 staging 원장에서 호출하지 않는다. 구 원장 회수 완료는 호출의 추가 성과 gate가 아니다. 같은 원장 이관을 N4와 별도 세션에서 중복 실행하지 않는다. 기존 정확한 source 재생/AI 응답은 내용 hash가 일치할 때만 재사용한다. provider 미완료 시 그 scope와 남은 expected 요청을 인계하고 같은 작업을 무작정 처음부터 반복하지 않는다. 이번 문서 요청은 N0~N8 실행 승인이 아니다. 후속 실행 지시에서 허용된 범위를 따르며 이미 허용된 동일 후속 조치를 중복 확인하지 않는다. 현재 보류된 정기 장후는 원장 개선 완료만으로 자동 재개하지 않는다.

발행 시 새 reader로 기존 family를 먼저 검증하고, parent CAS로 준비된 신규 기계·보조 쌍을 전환한다. 실패하면 보존한 code/family/등록 manifest/보조 binding으로 복귀한다. parent가 바뀌면 무조건 덮어쓰지 않고 변경된 부분의 비교·인계만 재확인한다. 최종 코드/정책/source/checklist 변경 이후 필요한 strict/controller/PREOPEN 준비를 다시 봉인한다. 자연 신호나 실제 주문 발생을 코드 종료 기준으로 요구하지 않는다.

## 10. 필수 검증·계획 리뷰

| 반례/경계 | 기대 결과 |
| --- | --- |
| 정책 순서 역전·성과 순위 역전 | 기계 확인점/성립 목록/정규화 AI 입력 동일; 성과순 우선권 없음 |
| FIRST 없음·FIRST WAIT·독립 HB 성립 | HB 정상 탐지; 반전 선행 조건 없음 |
| 한 정책 volume 결손·다른 정책 조건 유효 | 결손 정책만 제외; 공통 source 유효 여부는 별도 검사 |
| 동일 확인점 HA/HB 동시·동일 증거 alias | 모든 근거 참조 보존·AI 1회·intent 1회·union 1점 |
| 공통 5초 이내 FIRST 상태 무효·HB 유효 / 공통 5초 만료 | 전자는 신규 공통 위험 계약과 HB 재검증, 후자는 전부 차단; TTL 재기산 없음 |
| AI VETO·다른 정책 PASS cache 존재 | 새 복합 input의 VETO 유지; 정책별 우회 재호출 없음 |
| 같은 시각 다른 seq·다른 stream·quote 충돌 | 정확 key만 결합, 충돌 격리, 근접 시각 임의 결합 없음 |
| 80/100 baseline의 9W1F·8W2F·7W3F 추가 | 승률 개선·동률 추가 기회·열위 권고 구분; 반올림 동률 없음 |
| 기존 W 일부 손실을 포함한 승률 개선 교체 | 성공 100%/80% 보존으로 탈락시키지 않음 |
| 완전 미도달·경로 검열·확정 분모 0 | F_timeout/U/null 분리; 10분에서 조기 실패 처리 없음 |
| 개별 기여 0인 두 중복 정책 동시 제거 | 변경 묶음 비교로 공유 기회 소실 검출; 자동 퇴역 없음 |
| 추가안 기계 replay·원래 union AI 응답 재사용 | 변경 input의 AI 인과 성과로 사용 금지; exact 요청만 재사용 |
| 평가 수치만 갱신 / 실제 membership·AI binding 변경 | 전자는 FSM 유지, 후자는 새 실행 hash·CAS·claim 세대 검증 |
| 최종 family hash가 아직 없음·일자별 평가 갱신·세션 전환 | 비순환 증빙 결속, 보고 갱신만으로 상태 초기화 없음, 기존 세션 reset 보존 |
| catalog의 비교용 ALL·미선택 수백 후보 | 운용 manifest에 없는 정의의 자동 탐지·주문 권한 없음 |
| 일부 scope AI incomplete·원장 준비 전 입력 누락 | 누락 검출·해당 쌍 carry; 전수 완료·새 목록 적용 허위 표시 없음 |
| 전 arm VETO·PASS 전부 U·valid-empty | 완료 상태/분모 null 구분; 임의 승률·winner 없음 |
| 0% 동률에서 실패 확인점/PASS만 증가 | 기회 개선 권고 없음; 기존 성공 보존율 gate는 추가하지 않음 |
| 후보 volume UNKNOWN·baseline TRUE / 둘 다 UNKNOWN | 전자는 union TRUE이나 독점 미입증, 후자는 탐지 결손; U 라벨과 구분 |
| 후보 결손 구간에 baseline 실패 집중 | 공통 범위 baseline도 재계산·제외 수치 공개; 분모 차이를 승률 개선으로 왜곡하지 않음 |
| 현행/추가안 동일 기계 점·다른 복합 입력 | 각 입력 실제 AI 비교·PASS 목표 도달 성과 차이 공개; 구 응답 대용 금지 |
| label의 W/F/U·future suffix·장후 실행시각 변경 | 고정 확인 입력과 요청 key 불변, label 결합만 갱신; 미래 정보 유입 없음 |
| 다른 scope 발행 / 자기 scope·공유 code 변경 | 전자는 계약 동등성 검증 후 유지, 후자는 영향 state/claim 무효화 |
| provider 전후·intent 할당 전후 crash·버전 교체 | 영속 예약/기존 원장 대사·중복 호출/intent 방지, 불확실 전송 자동 재시도 없음 |
| 동일 입력/다른 보고서 버전·새 날짜·label만 정정 | 공통 본문/응답 복제 0, 변경 partition/참조만 추가, 누적 집계 parity·expected owner 보존 |
| 복합 근거 추가/제외·validator 변경 | 공통 context는 공유하되 달라진 요청은 새 실제 응답, validator별 결과 분리, 옛 PASS OR 대체 0 |
| 구 reserved/신 planned 충돌·저장 cutover/rollback | 불확실 예약 전수 대사, 최신 attempt 보존, 재개 시 중복 전송 방지, offline 응답으로 live intent 승인 불가 |
| legacy ID namespace 충돌·늦은 응답·인접 partition 정정 | 원 ID 보존/입증된 alias만 연결, 봉인 비교 불변, full replay와 증분 결과 parity |
| 신·구 쌍 모두 없는 필수 scope·소비자 연결 누락 | incomplete candidate 보존·CAS 거부, 기존 유효 bundle 검증, 가짜 transport로 N5 이전 검출 |
| 두 정책 관련 1회 체결·그중 한 정책 퇴역 | 실현 손익 1회, 정책 연결 통계 합산 불가, 잔여 custody/exit 계획 보존 |
| 현행 v4 primary와 동일 목록 v5 복합판정 | 별도 비교안/요청 bytes·실제 응답 사용; 계약 전환 효과 분리 |
| 특정 scope v4 carry·다른 scope v5 / 가격대 이동 | scope별 native 검증·권한 backend 하나·canonical 예약 공유; carry를 신규 적용으로 표시하지 않음 |
| 동일 실행 의미·새 증빙 / envelope 만료·무효 | 증빙 갱신만으로 FSM reset 없음; 무효 envelope는 차단 |
| 신규 정책 등록 직전 접두에서 이미 확인된 신호 | warmup만 수행; 과거 확인점의 live ready/intent 재발행 없음 |
| 확인 즉시 두 branch·실제 요청 전 한 branch 상태 무효 | confirmation replay/live 입력을 구분·정확 요청 hash만 재사용·지연 손실 별도 |
| token/ready/pending 한도·외부 provider 지연 | 과부하와 claim 만료 공개; top-K 생략·offline 표본 절단 없음 |
| 구 v1~v4/신규/unknown × 로드·요청 전후·기동·감시 | 원 계약 검증·신규 정확 dispatch·unknown 명시 거부 |
| retired/manual owner·보유·미체결·broker/자본/수량 guard | 독립 신호 증가가 기존 실행 제한을 우회하지 않음 |

실제 모델 응답의 재현성을 가짜로 보장하지 않는다. 순서 불변성 단위 검증은 요청 bytes와 고정 transport fixture로 확인하고, 성과 비교는 보존한 실제 응답을 사용한다. 선행 8개의 native 확인점·특징·라벨 parity와 최신 누적 비교를 분리한다.

### 10.1 계획 자기 리뷰에서 반영한 보완

| 위험 | 보완 |
| --- | --- |
| 등록 전체를 catalog 전체로 해석 | §3 운용 manifest와 연구 catalog 분리, 최초 active+8 diff 고정 |
| 동등 탐지인데 primary만 AI에 전달 | §4 이벤트 평가 완료 후 봉인, §5 전체 typed 근거·공통 위험 계약 |
| FIRST 상태 무효와 공통 claim 만료 혼동 | §5.2 원 입력 집합의 branch별 상태 재검증·공통 5초 만료 시 전부 차단 |
| 장후 순위가 매일 운용 정책을 다시 줄임 | §2/§6 목록 변경 receipt와 평가 권고 분리 |
| 보고 수치 갱신마다 신호 상태 초기화 | §3.3 실행 manifest와 평가 hash 분리 |
| 보조 비교가 최종 family hash를 선행 요구하는 순환 의존 | §3.3 detector manifest→실제 비교→실행 manifest의 결속 순서 |
| 개별 성공 수를 더해 union 성과 과장 | §6 canonical 집합·독점/묶음 기여·기계/AI 인과 차이 명시 |
| 자동 가설 탐색·새 holdout/성공 보존 gate 재도입 | §6/§7 고정 정의 평가·누적 승률·동률 기회·수동연구 경계 |
| 다른 세션 구현 중 변경 또는 옛 배포 승인을 후속 실행으로 확대 | §1/N0 소유 인계와 이후 구현 지시, 현재 계획 작성만 수행 |

문서 closure는 링크·단일 OPEN owner·권한/선행 계약·공백·print-only backlog parser로 확인한다. 코드 pytest·전수 재생·provider·정책 발행·배포·재기동은 구현 단계 검증이며 이 문서 작성에서는 실행하지 않는다.

10/7 문서 검증: 새 계획의 로컬 링크 4개·선행 계획/체크리스트의 후속 링크, print-only parser 29개 작업 중 current owner 1개, tracked diff와 신규 문서 공백 검사를 확인했다. 재리뷰에서 비순환 hash·세션 reset·전 VETO/미확정/빈 모집단 구분을 보완했다. 문서 검토 범위 내 미해결 finding은 없으며 구현·성능·실제 응답 검증 완료를 뜻하지 않는다.

### 10.2 후속 재리뷰 — 구현 중 v4와의 대조

위 4개 링크 수와 검증은 초안 이력이다. 이번 보완은 다음 항목을 소유하며, 구현 중 v4의 수정·완료를 의미하지 않는다.

| ID | 발견한 계획 결함/모호함 | 보완과 구현 종료 검증 |
| --- | --- | --- |
| IR1 | 같은 확인점인데 FIRST만 시간 만료된다는 잘못된 예 | §5.2 상태 무효와 공통 5초 만료 분리; 공통 만료 시 전부 차단 |
| IR2 | 메모리 claim을 영속 dedup으로 가정 | §4.2 실제 provider/intent registry 연결·원자 예약·불확실 전송 대사; crash 회귀 |
| IR3 | 타 scope/새 평가 증빙이 모든 탐지 상태를 초기화할 위험 | §3.3 scope 실행 의미와 publication 증빙 분리; 현재 envelope 유효성은 계속 검사 |
| IR4 | 탐지 UNKNOWN을 미성립으로 취급해 독점 기회·승률 과장 | §6.1 TRUE/FALSE/UNKNOWN·독점 미입증·동일 비교 범위·baseline 제외 수치 |
| IR5 | AI 전수 입력/호출 분모 불명확·미래 label 유입 가능 | §5.3 사전 input census·W/F 호출·U 별도 회계·allowlist projector·미래값 불변성 |
| IR6 | label 확정 때 정상 과거 응답을 무효화하거나 다른 입력에 재사용 | §5.3 요청 key와 label snapshot 분리·exact bytes/model/validator 재사용 |
| IR7 | 기계 증가만 보고 복합 AI의 기존 PASS 감소를 누락 | §5.4 현행 native/동일 목록 successor/각 추가/일괄 비교·교환관계 보고 |
| IR8 | 0% 동률에서 실패만 늘어도 기회 확대 권고 | §5.3/§6.3 동률 추가 성공 확인; 실패 증가만으로 권고하지 않음 |
| IR9 | 구 branch별 보조를 신규 복합 schema에 복사해 부분 carry | §8.1 native parent 참조·scope별 단일 backend·실제 carry 표시 |
| IR10 | 다중 정책 성과 귀속이 후단 단일 primary/중복 PnL로 되돌아감 | §4.2 다중 근거 계보를 intent/완료까지 보존·실현 손익 한 번 집계 |
| IR11 | 새 등록 warmup의 과거 확인점을 신규 기회로 재발행 | §4.1 활성 경계/원천 접두 복원·warmup과 live ready 분리 |
| IR12 | 확인 즉시 연구 응답을 실제 전달 후 응답으로 간주 | §5.2/§5.3 확인/요청/응답 시점 집합·지연·입력 hash를 구분 |

재리뷰 검증: 로컬 링크 5개와 절 anchor, print-only parser 29개 작업 중 current owner 1개, tracked diff·신규 문서 공백 검사 PASS. IR1~IR12의 본문/실행 단계/반례 검증 연결을 다시 확인했다. 이번 문서 검토 범위 내 미해결 finding은 없으며, 런타임 소스·정책·실제 provider·배포·재기동과 코드 테스트는 실행하지 않았다. 구현 종료 여부는 N0~N8의 실제 결과로 별도 판단한다.
