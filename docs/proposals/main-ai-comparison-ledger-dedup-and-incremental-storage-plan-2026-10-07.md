# Main AI 비교 원장 공통 저장·증분 처리 개선계획

## 1. 목표와 실행 경계

최초 요청은 원장 개선계획 수립과 세 정책 계획의 원장 요건 보완이었다. 이후 사용자가 완료된 검증연구의 미사용 복제본 삭제, 이 계획의 구현·반복 리뷰·보완 및 장후작업용 배포를 승인했다. L0~L6 구현 뒤 별도 사용자 지시로 L7 장후 재개도 승인됐다. 10/8 07:26 장후 최종화·정확 일자 준비가 완료됐으며, 이하 과거 중단/무제한 문구는 당시의 이력이다. 이번 후속 보완은 호출 한도에 맞춘 sampled 비교 원장 요구이며 기존 기동 준비를 변경하지 않는다.

목표는 **같은 입력·요청·실제 응답을 한 번 저장하고, 각 정책·버전·평가일은 그 자료를 참조하는 것**이다. 최초 누적 이관 이후 정기 장후는 신규·변경 자료만 준비한다. 누적 승률과 eligible 전수 census는 유지한다. 후속 지시로 **장후 보조비교는 원천일당 누적 100 attempt**이며, 운영 호출 계약은 별개다. 전체 기회 census와 사전 선정한 비교 표본을 분리하고, 표본 선택을 누락이나 전수 완료로 위장하지 않는다. [독립 탐지 계획 §5.3](main-operating-policy-independent-detection-and-contribution-evaluation-implementation-plan-2026-10-07.md)이 튜닝 목적·표본·성과 판단을 소유한다.

[10/7 사용자 중단 기록](../audits/postclose-operator-stop-2026-10-07.md)은 역사적 증빙이며 이후 재개 승인·10/8 완료 상태를 대체하지 않는다. 실행 owner는 [10/8 체크리스트](../checklists/2026-10-08-stage2-todo-checklist.md)의 `DirectFamilySourceRepairMainMechanisticEntry` 하나다. 후속 설계만으로 새로운 provider 실행·배포·정책 교체를 완료했다고 표시하지 않는다.

## 2. 실측 결함과 개선 범위

[20:37 원장 점검](../../tmp/main-additional-eight-implementation-20261007/disk-growth-audit.json)과 이번 계획 작성 중 추가한 읽기 전용 owner 계수의 고정 기준은 다음과 같다. 실행 착수 시 L0에서 다시 동결하며 아래 수를 미래 원장에 강제하지 않는다. 현재 증거의 `tmp` 경로를 무조건 정리 대상으로 삼지 않으며, L0에서 작은 audit/manifest를 기존 보존 계약 아래 인계한 뒤 원 경로를 정리한다.

| 항목 | v3 | v4 |
| --- | ---: | ---: |
| SQLite 할당 bytes | 5,856,215,040 | 5,898,772,480 |
| 고유 요청 | 579,437 | 579,442 |
| 실제 응답 보유 `completed` | 4,626 | 4,626 |
| `planned` | 574,807 | 574,816 |
| `reserved` | 4 | 0 |
| 비교 owner/arm 행 | 580,035 | 580,040 |

두 원장은 579,437개 요청 ID를 공유한다. v4에만 있는 요청 ID는 5개다. 대조한 공통 요청 100개의 저장 본문은 모두 동일했고, 미호출 요청 표본 100개는 평균 7,327.25 bytes였다. ID 전수 교집합과 본문 100개 표본 검사를 구분한다. **이관의 본문 동등성 검증은 표본이 아닌 전수**로 수행한다.

12:41 디스크 정리 직후 대비 사용량은 약 20.8GiB 늘었고, 오늘 생성된 등록 비교 폴더는 약 13.8GiB를 차지했다. 이 중 두 SQLite 원장이 약 10.95GiB다. 나머지 디스크 증가분 전체의 원인을 원장으로 단정하지 않는다.

확인한 구현 결함은 다음과 같다.

- [v3 저장소](../../src/engine/scalping/continuous_reversal_registered_postclose.py)와 [v4 저장소](../../src/engine/scalping/continuous_reversal_path_postclose.py)가 버전별 DB에 같은 요청을 다시 보관한다. 각 버전의 provider lock도 별도다.
- v4의 `prepare_inputs`는 실제 호출 전에 모든 eligible point×5 arm의 전체 입력·prompt·schema를 `requests.request`에 저장한다. 메모리 스트리밍만으로 디스크 중복은 제거되지 않았다.
- generation마다 전체 owner 행과 여러 긴 문자열 index를 복제한다. 응답 본문까지 포함한 covering index도 반복 payload 저장을 만든다.
- 일별/run별 source·입력·응답 export는 별도 보존되며 일부는 hardlink다. 파일 크기 합산을 실제 점유량·회수 가능량으로 사용하면 안 된다.
- **같은 4개 요청이 v3에서는 reserved, v4에서는 planned**다. 현재 자료만으로 전송 여부는 확정할 수 없다. 신규 저장소에서는 대사 전 이를 미호출로 되돌리지 않는다.

호출한도 해제는 실제 호출 가능한 수에 영향을 준다. 위 미호출 본문의 선행 저장·버전별 복제는 별도의 구현 문제다. 호출 제한만으로 저장 복제 문제를 해결했다고 보지 않는다. 후속 100 attempt 한도와 중복 제거·증분 저장은 함께 충족한다.

## 3. 저장 소유와 식별자

### 3.1 공통 저장소와 버전별 산출물

계획 경로는 `data/ai_comparison_store/v1/`이다. 여기서 `v1`은 **저장 형식** 버전이며 정책 v3/v4/후속 v5와 독립이다. 정책 버전이나 평가 날짜가 바뀌었다는 이유만으로 공통 DB와 전체 요청을 복사하지 않는다.

| 자료 | 저장 단위·소유 | 원칙 |
| --- | --- | --- |
| 고정 확인 입력 | 실제 입력 내용 hash | 동일 입력은 한 번; 장후 실행시각·미래 label을 섞지 않음 |
| prompt/schema/생성 설정 | 각각의 내용 hash와 원 계약 버전 | arm별 공통 본문을 요청마다 중복 저장하지 않음 |
| 요청 정의 | canonical opportunity·phase/입력 계약·정확한 요청 binding | 작은 참조만 보관; 호출 직전에 원 요청을 조립 |
| 전송 시도·응답 | request ID + attempt ID + provider response ID | 실제 시도·불확실 상태·원 응답을 보존 |
| 검증 판정 | response 참조 + validator 계약 + validation 결과 hash | transport 완료와 비교/운영 적격을 분리; 재검증은 새 행 |
| 비교 membership | comparison partition hash + 기회/arm/요청 참조 | 날짜·run은 기존 partition 목록을 참조 |
| 결과 라벨 | opportunity + label/source/비용 계약 버전 | W/F/U 변경은 별도 결과; 모델 입력·원 응답을 덮어쓰지 않음 |
| 발행 증빙 | 불변 manifest + response/validation/label 선택 snapshot | mutable DB/WAL 전체 hash나 이후 queue 상태로 과거 결과를 바꾸지 않음 |

`continuous_reversal_registered/<date>/...`, `v4/<date>/<run>/...` 및 후속 정책 namespace에는 각 버전의 비교·발행 manifest와 고유 결과를 보존한다. **결과 namespace 분리와 요청 본문 저장소 분리를 같은 요구로 취급하지 않는다.** 기존 발행 파일과 hash는 소급 변경하지 않는다.

### 3.2 세 가지 key의 분리

1. `opportunity_key`: 원 native stream/date/symbol/session/route/item/epoch/sequence 계약을 보존한다. 다른 native 기회를 가격·시각이 비슷하다는 이유로 합치지 않는다.
2. `request_key`: opportunity, phase/입력 의미, 정확한 input/prompt/schema, provider/model/endpoint·생성 옵션에 결속하는 **전송 요청 ID**다. label·승률·보고 날짜·comparison owner·최종 family hash는 넣지 않는다. 모델에 실제 전달되는 필드라면 임의로 key에서 제거하지 않는다. validator만 달라지고 전송 내용은 같다면 요청 본문/원 응답은 공유할 수 있지만, 별도 validation key로 각 계약의 검증을 수행하고 원 정책이 허용한 재사용 범위 안에서만 비교에 연결한다.
3. `comparison_key`: scope·정의/조합·phase·평가 관측 종류·arm·label 계약에 결속한다. 같은 request를 여러 비교가 참조할 수 있다. 요청 중복 제거가 비교 분모를 줄이는 근거가 되지 않는다.

기존 v3/v4 request ID와 원 bytes는 `legacy_request_alias`와 provenance로 보존한다. 새 정규화가 달라도 같은 ID라고 가정하지 않고, **실제 transport에 사용한 입력·prompt·schema·생성 옵션의 동등성**을 검증해 대응한다. 공통 요청 key에 새 날짜·실행 code commit·정책 버전을 무조건 추가하여 재사용을 무력화하지 않는다. 코드/원천 계약은 별도 provenance와 요청 의미 검증에서 보존한다.

legacy canonical ID에는 stream namespace가 digest 밖의 source receipt에 있을 수 있다. 이관 adapter는 원 ID/hash를 재작성하지 않고 `identity_version + 원 source namespace/receipt + legacy ID → 새 opportunity key`를 대사한다. 다른 collector가 같은 날짜·item·epoch·sequence를 사용해도 명시된 원천 대응 증거 없이 병합하지 않는다. 정책 ID·branch/phase·anchor는 확인점의 lineage이며 opportunity 중복 제거 key에 넣지 않는다. 요청의 phase/내용 구분은 그 다음 request key에서 유지한다.

phase, 복합 `signals[]`, input 의미, prompt/schema/모델 설정이 달라지면 새 요청이다. validator 변경은 기존 각 정책 계획의 엄격한 호환/재검증 규약을 따른다. 저장 공간을 줄이기 위해 구 PASS를 새 계약의 PASS로 재해석하지 않는다. 내용이 같은 객체의 물리적 공유와 응답 재사용 허용은 별개다.

실시간 provider/주문 원장의 영속 중복 방지는 별도 소유다. offline 비교의 arm/pair 예약을 live 1회 AI/1 intent 예약으로 사용하지 않는다. `confirmation_replay`와 `delivered_live`는 관측 종류와 원천 계보를 보존하고, 정확한 실제 요청 대응이 입증된 응답만 기존 정책의 허용 범위에서 참조한다. offline 캐시가 live 주문 권한을 만들지 않는다.

### 3.3 본문 저장과 조회 비용

SQLite metadata에는 request 참조·상태·작은 owner key와 index만 둔다. 입력·prompt/schema·실제 응답은 내용 주소로 저장하고, 큰 입력/응답은 **크기가 제한된 불변 압축 block**에 묶는다. block index가 논리 hash·위치·길이·encoding을 가리키며 읽을 때 원 bytes hash를 검증한다. 요청 수만큼 작은 파일을 만드는 구현도 피한다. 새 압축 패키지 설치를 전제로 하지 않는다.

객체 write/fsync를 완료한 뒤 metadata transaction에서 참조를 commit한다. crash로 남은 미참조 block은 회계에 남기고 검증된 GC 대상이 될 수 있지만, 참조된 미완성 객체를 완료로 발행하지 않는다. 압축/pack 재배치는 논리 요청 ID·원 응답 hash를 바꾸지 않는다.

owner에는 긴 definition/comparison 문자열을 반복하지 않고 dictionary ID/partition 참조를 사용한다. immutable membership partition이 같으면 새 run은 동일 partition을 가리킨다. 같은 기대 집합의 owner 전체를 generation별로 다시 INSERT하지 않는다. 필요한 관계/검색 index만 두고 `result` 등 대형 본문을 covering index에 넣지 않는다. 큐·상태 계수·중복 조회는 작은 metadata의 covering index로 끝나야 한다.

canonical provider journal도 매 호출마다 요청 본문 전체를 반복하지 않는다. 조립 가능한 불변 request 참조와 attempt/response 참조·전송 상태를 durable하게 남긴다. 기존 consumer용 full-body export가 필요한 경우 내용 hash로 한 번 봉인하고 필요한 동안 공유한다. 단순히 모든 구 export에 압축 복사본을 하나 더 붙여 점유량을 늘리지 않는다.

`planned` 참조를 완료한 준비로 인정하기 전에, 본문 재조립에 필요한 입력·arm 설정·serializer 계약·source proof를 보호된 불변 closure로 확보한다. 요청 본문 전체의 선행 복제만 줄이며, 변동하는 최신 raw/현재 prompt를 나중에 다시 읽어 같은 요청이라고 주장하지 않는다. 원 serialized transport bytes로 round-trip 검증한다. 입력 객체가 빠지거나 serializer가 원 bytes를 복원하지 못하면 `request_materialization_missing`으로 해당 대상을 미완료 처리하고 provider 전송 전에 멈춘다.

## 4. 최초 준비와 정기 증분 처리

### 4.1 최초 이관은 한 번

v3/v4 source DB와 응답 export·journal을 읽어 공통 저장소를 구성하는 전체 이관은 최초 한 번 수행한다. 이후 코드 배포나 정책 버전 변경은 새 전체 이관의 이유가 아니다. 이관 ledger version·원 snapshot fingerprint·진행 checkpoint를 통해 재실행이 같은 자료를 중복 INSERT하지 않게 한다.

### 4.2 매일 처리할 차집합

1. source manifest와 기존 partition fingerprint를 대조한다. 새 날짜·새 native 접두, 뒤늦은 분봉/원천 정정, 실제 영향을 받는 feature/정의 변경의 partition만 계산한다.
2. 유효 확인점 전수와 W/F/U·입력 결손 census를 먼저 생성한다. 후속 sampled 비교는 전체 opportunity partition과 선정 표본×현행/후보 pair membership을 분리하며 큰 요청 본문을 전수 생성하지 않는다. 과거 고정 arm 원장은 원 계약으로 보존한다.
3. 신규·변경 요청 참조만 upsert하고 공통 완료 응답·불확실 예약을 조회한다. 같은 입력·같은 계약이면 기존 요청/응답을 재사용한다.
4. 이번 사전 표본의 미호출 차집합만 작은 batch로 읽어 요청을 조립하고 100 attempt 예산 내에서 provider에 전달한다. batch 크기는 메모리·전송 동시성 관리값이며 전체 eligible census를 줄이는 값이 아니다.
5. 새 결과·라벨 수정분을 누적 집계에 반영한다. 기존 partition 집계 + 신규/대체 partition 집계로 누적 승률을 만들며, 라벨 정정은 이전 기여를 제거한 뒤 새 기여를 한 번 반영한다.

전수 평가란 논리적 대상 전수가 census와 결과에 포함된다는 뜻이다. 매일 누적 전체 tick·입력·prompt를 새 파일로 복제하거나 재호출해야 한다는 뜻이 아니다. 정의/입력 의미가 바뀌어 과거 전체가 영향을 받는 경우에는 해당 범위의 재생이 필요할 수 있으며 이를 단순 날짜 증분이라고 축소하지 않는다.

top-level 평가 manifest는 날짜·parent·registry 전체를 결속하되, 하위 source/feature/input/membership cache는 **실제 읽은 의존성**으로 식별한다. 관련 없는 다른 scope 변경이나 publication 날짜만으로 모든 partition을 무효화하지 않는다. 원천·label·feature·prompt 변경 각각의 영향 범위를 분리해 검사한다.

partition은 파일 경계와 같다고 가정하지 않는다. manifest에는 해당 결과가 읽은 이전 session anchor/rolling 구간/root 상태와 이후 최대 30분 label 구간·완성 분봉의 의존성을 기록한다. 경계 부근 source 정정은 이 역참조로 **영향받은 인접 partition까지** 재생하며 input과 label의 영향 범위를 구분한다. append-only 원천은 producer가 봉인한 segment digest/high-water를 사용하고 mtime/크기만 같은 것을 동일 내용 증거로 쓰지 않는다. 이러한 증빙이 없으면 해당 source를 다시 검증하고 그 비용을 보고한다. 이 최적화를 위해 현행 세션/epoch 불연속을 이어 붙이지 않는다.

### 4.3 전수성과 미완료 회계

원장 생성 전 expected membership을 봉인하고 실제 queue/응답과 대사한다. 모든 point×arm의 full JSON이 있어야 expected로 인정하는 규칙은 제거한다. manifest에 없는 행, 사라진 참조, hash 충돌은 별도 결손으로 검출한다.

각 owner/arm의 보존 회계는 `expected = planned + reserved_uncertain + responded + failed + missing`으로 둔다. `missing`은 완료 상태가 아닌 결함이다. `responded` 내부에 유효/무효 응답을 구분하며, 비교 가능한 수는 각 정책의 원 응답·validator·W/F/U 계약으로 계산한다. `completed`라는 구 필드만으로 비교 완료를 추정하지 않는다. 과거 전수 비교는 그 기대 arm 계약을 보존한다. 후속 sampled 비교는 사전 봉인한 현행-후보 쌍만 대사하며, 무관한 제3 arm이나 미선정 전체 기회의 미호출이 해당 비교를 무효화하지 않는다. sampled 결과를 전수 winner로 발행하지 않는다.

이 식은 **봉인 시각의 owner별 비교 상태**이며 attempt 원장의 행 수 합이 아니다. 하나의 request에 응답과 별도 불확실 attempt가 함께 있어도 owner는 한 상태로 세고 미해결 attempt 수는 별도 보존한다. 미전송/실패/재시도 가능 여부는 전송 증거와 원 retry 계약으로 구분한다. provider 응답 ID 부재나 오류 문자열만으로 미전송을 입증하지 않는다. 응답 원본·연결은 있으나 schema 부적격이면 responded의 invalid이며 원천/라벨 결손과 섞지 않는다.

고유 request 수, 비교 owner/arm 수, 실제 attempt 수, 고유 provider response 수는 각각 보고한다. 같은 응답을 참조하는 여러 owner를 여러 AI 호출로 집계하지 않는다. 원장의 동일 요청 통합으로 owner/arm W/F/PASS 분모가 달라지지 않아야 한다.

### 4.3.1 호출 한도와 비교 표본 저장 — 후속 구현 요건

- `eligible_universe`는 기계 기회 전체의 작은 partition/census로 유지하고, `sample_manifest`는 source/기계 목록/관측/현행·후보 binding·추출 seed/규칙/확률·선정 사유·순번을 봉인한다. label은 평가용 별도 binding이며 추출 순서나 provider 입력에 넣지 않는다. 오판 개발 사례와 대표 평가 표본은 용도를 분리한다.
- 전수 eligible×기계 추가 조합×5 arm 요청을 매일 생성하지 않는다. 새 `expected_pairs`의 현행/후보 exact request만 준비한다. 비선정은 `not_sampled_budget`이다. 기존의 전수 미완료/uncertain 원장을 삭제하거나 상태를 바꾸지 않는다. 동일 request는 옛 membership과 새 sampled membership에서 같은 객체를 참조한다.
- 필요한 입력 접두/설정은 봉인해 두고, selected pair가 원 bytes로 조립되는지 검증한다. 전체 원천이 있어야 캐시를 재사용할 수 있다는 가정을 추가하지 않되, exact materialization/provenance는 반드시 검증한다. 이미 완료한 적격 응답은 추가 호출 0회다.
- scheduler는 지정된 표본 순서에서 두 응답의 미호출 차집합을 예약한다. 100 provider attempt 누적, failed/uncertain 차감, crash 후 fence와 불확실 전송 대사는 그대로다. 한쪽 응답만 있는 쌍은 미완료이며 재실행은 남은 합법적 차집합만 처리한다. 한도가 한 번 남았다고 2회가 필요한 새 쌍을 완료할 수 있는 것처럼 표시하지 않는다.
- 같은 표본에서 유효하게 완료된 공통 쌍의 metric partition을 누적하고 뒤늦은 응답은 새 revision으로 봉인한다. 요청 전체 완료와 공통 쌍 평가 가능을 구분하고 식별 가능한 결손 쌍만 양쪽 분모에서 제외한다. candidate/현행/label/관측 계약별로 분리하며, source/label 정정은 해당 partition의 기여를 교체한다. 결과가 마음에 드는 응답만 고르거나 미완료 배치의 완성 부분을 전수 우월성처럼 표시하지 않는다. 완료율·제외 사유와 비응답 편향 한계를 공개하며 미완료 backlog를 일괄적인 튜닝 중단 조건으로 사용하지 않는다.
- 같은 semantic input 의존성의 준비 단계는 새 오판 보고 코드/발행시각만으로 23만 입력을 재투영하지 않는다. source/feature/definition/prompt/serializer 변경 영향과 무관한 집계 코드 변경을 구분하는 cache 계약을 검증한다. 전체 재검증이 불가피하면 소요시간/읽기 bytes/신규 객체 bytes를 보고한다.

### 4.3.2 후보 등록·장중 보조 적용 기록과의 연결 — 10/8 설계

[독립 탐지 계획 §5.5~§5.7](main-operating-policy-independent-detection-and-contribution-evaluation-implementation-plan-2026-10-07.md)은 새 prompt 연구·등록, 예산 내 평가, 당일 보조 binding 교체를 소유한다. 이 절은 그 **미구현 후속 요건**이며 현재 원장에 장중 적용 권한이 있다는 뜻이 아니다.

- 후보 원문/설정/입력·validator 정의를 내용 hash로 한 번 저장하고, registry ID/version·부모·scope·가설/개발 사례는 작은 참조로 연결한다. 장후 evaluator가 자유 문구를 생성해 활성 registry를 덮어쓰는 경로는 없다.
- 개발 사례와 사전 평가 표본의 membership을 분리한다. prompt가 달라지면 새 exact request지만 원천과 원장 DB는 공유한다. 결과/label이 바뀌어도 원 prompt·응답 bytes는 그대로다. 비교에 사용한 실제 response를 고정하고 유리한 반복 응답으로 교체하지 않는다.
- 실행 시 필요한 불변 prompt/schema/binding 객체는 검증된 작은 runtime artifact로 발행한다. live loader가 대형 연구 DB를 조회하거나 offline 예약/worker 상태에 매달리게 하지 않는다. runtime cache invalidation에는 새 보조 pointer와 정확한 객체 의존성을 포함한다.
- 장중 발행 receipt는 기존 기계 기본 bundle·현재 보조 부모·신규 registry·평가 snapshot·scope·유효 세션일을 참조한다. 평가 완료를 PID 소비로 표시하지 않으며, live outbox의 canonical 기회 예약은 보조 버전이 달라도 유지한다. offline 완료가 live 요청/주문 권한을 대신하지 않는다.
- 활성·전환 중 claim·rollback·다음 장후가 참조하는 prompt/응답/평가 객체는 GC에서 보호한다. 다음 날 기본 bundle에 반영되어도 역사적 비교 원본을 재작성하지 않는다. 기존 원장 전체 복사나 날짜별 동일 prompt 복제로 증거를 보존하지 않는다.
- 같은 원천일의 수동 보조 연구·정기 장후·기계 추가안 AI 비교는 공통 100 attempt를 공유한다. 기존 날짜/연구를 새 이름으로 복제해 예산을 리셋하지 않는다. 해당 원천일의 기존 초과 사용량도 차감 상태로 유지한다. 운영 실제 판정 호출의 별도 계약을 연구 호출 우회 경로로 사용하지 않는다.
- 검증: 고유 request/owner/pair/attempt/response 분리, 100회 상한과 resume, 같은 입력 0신규 객체/호출, selected pair materialization, 비선정과 결손 구분, 결과 변경에도 추출 key 불변, 현행 응답 cache 재사용, 일반 보고 변경에 전체 재준비 없음, 과거 원장 불변을 확인한다.

### 4.4 비교 결과 봉인과 실제 응답 선택

공유 원장의 최신 queue 상태와 발행 비교 결과는 분리한다. 비교 snapshot에는 expected membership hash, 응답 수신 cutoff와 ledger commit high-water, owner별 선택한 attempt/response hash, validator/validation hash, label snapshot 및 기계 부모를 결속한다. 늦게 import된 과거 시각의 응답도 봉인한 commit 경계를 소급 통과하지 못한다. 이후 응답 수신·validator/label 정정은 새 비교 revision을 만들며 과거 보고서·active family가 소비한 원 응답을 바꾸지 않는다.

새 revision은 변경된 결과 partition과 기존 불변 partition 참조를 사용한다. 각 응답 도착마다 누적 owner 전체 snapshot을 다시 저장하지 않는다. 미완료 진행률은 작은 queue/checkpoint로 갱신하고, 비교 봉인은 명시된 종료/인계 시점에 수행한다. 독립 재검증에 필요한 closure는 모두 보존한다.

기존 owner의 응답은 기존 frozen export/receipt가 가리킨 것을 유지한다. 신규 owner는 결과 W/F/PASS를 보기 전에 고정한 응답 선택 규약으로 결정한다. 해당 관측 종류·전송/입력 계약에 exact 결속된 실제 응답 중 영속 attempt 순서를 사용하고, legacy 순서를 복구할 수 없으면 source receipt와 response hash의 고정 정렬 규칙을 명시한다. 응답 선택 뒤 validator를 적용하며 validator 합격·PASS 여부로 다른 응답을 골라 끼우지 않는다. 규약으로 해소할 수 없는 ID/내용 충돌은 격리한다. 여러 완료 응답은 모두 보존하며 과거의 서로 다른 owner가 다른 실제 응답을 소비했다면 강제로 하나로 합치지 않는다.

## 5. 예약·응답·중단의 영속 계약

신규 저장소의 writer/예약은 v3/v4/후속 adapter가 공유한다. 기존 두 provider lock은 서로 보호하지 않으므로, cutover 때 구 writer를 모두 중지하고 기존 lock들과 새 공통 writer lease를 정해진 순서로 획득한다. 단지 새 DB에 unique index를 추가한 것만으로 구 writer의 재호출을 막았다고 보지 않는다.

writer는 실제 전송 직전과 응답 commit 때 store generation/fencing token을 다시 검증한다. 구 코드가 새 token을 모르는 경우에는 scheduler/dispatcher/수동 재개 CLI의 실행 진입점에서 해당 writer를 차단하고 검증된 adapter만 허용한다. 구 cron·release 직접 실행 경로가 남아 우회할 수 있으면 cutover 완료가 아니다. 이미 전송됐을 수 있는 old worker의 늦은 응답은 원 attempt에 연결해 보존하고 신규 실행으로 세지 않는다.

요청 상태와 전송 시도를 분리한다. 예약은 transaction/CAS로 하고 attempt ID·worker PID/start identity·fencing token·전송 여부 증거를 기록한다. 원 외부 전송과 DB commit은 원자적이지 않으므로 timeout/crash가 나면 `reserved_uncertain`으로 보존한다. lease 만료, 버전 교체 또는 worker 부재만으로 `planned`로 되돌리지 않는다. 결과 journal/provider ID 대사로 응답이 입증되면 결속하고, 미전송이 입증된 경우에만 기존 허용 retry 규약으로 새 attempt를 준비한다.

이관 충돌은 다음처럼 처리한다.

- 동일 request ID·같은 전달 내용·같은 실제 response ID/bytes: 요청과 응답은 한 번 저장하고 원 owner/provenance를 모두 연결한다.
- 같은 요청에 복수 실제 응답/attempt: 모두 보존하고 기존 비교가 소비한 응답 참조를 유지한다. 더 좋은 PASS를 골라 결과를 바꾸지 않는다.
- `planned`와 `reserved` 충돌: 불확실 예약을 보존한다. 현재 발견한 4건을 대사 전 자동 재호출하지 않는다.
- `completed`와 불확실 예약 충돌: 완료 응답이 **그 attempt**를 닫는지 검증한다. 다른 미해결 attempt를 완료 응답 한 개로 지우지 않는다.
- 같은 ID인데 실제 전달 내용이 다르거나 response ID/bytes가 충돌: 해당 참조를 격리하고 발행/재사용을 막는다. 모든 scope를 일괄 성공·일괄 차단하지 않는다.

응답은 원 bytes/provenance가 durable하게 저장된 뒤 해당 attempt의 수신을 commit한다. 저장 직전 crash, journal fsync 후 DB commit 전 crash, 응답 후 owner 연결 전 crash를 구분해 복구한다. 동일 요청 재개에 새 provider 호출이 필요한지 여부를 자료로 판단한다.

후속 지시에 따라 **장후 보조비교는 원천일당 누적 100 provider attempt**로 제한한다. 이 튜닝의 수동 재실행/연구도 같은 예산을 공유하고 failed/uncertain을 차감한다. 운영 실제 판정 호출은 별도 기존 계약이며 이 저장 개선으로 새 한도를 설정하지 않는다. 기존 외부 rate limit·bounded in-flight·timeout·stage deadline과 사용자 중단은 유지한다. 정상 중단에서는 새 예약을 먼저 막고 전송 중 시도를 drain한다. 강제 중단의 불확실 시도를 보존한다. 저장 부족은 checkpoint와 `resource_deferred` 실행 사유로 기록하며, planned 대상을 없애거나 source_gap/유효 무표본/비교 완료로 바꾸지 않는다.

## 6. 기존 원장 이관·cutover·회수

### 6.1 읽기 준비와 이관

L0에서 selector/현재 family/rollback release, 날짜·source·frozen report·actual response read-set, 구 DB/WAL/journal, 예약 4건, PID/FD/lock과 중단된 예약을 인계한다. 전체 source가 고정되기 전 checksum을 확정하거나 활성 WAL을 무시한 `immutable=1` 읽기를 사용하지 않는다.

구 writer 정지와 lock을 확인한 일관된 SQLite read snapshot을 streaming으로 읽는다. 이관 작업 자체는 provider를 호출하지 않는다. 별도 staging 저장소에 객체·request alias·attempt·response·membership·label을 작성하고 checkpoint를 남긴다. 단순 `ATTACH` 후 전체 request 본문을 반복 random lookup하거나 새 DB를 만들 때마다 원 DB 전체를 복사하는 방식을 피한다.

이관 검증은 원장별 owner/arm 전수와 요청 전수의 key·전달 내용·상태·소비 응답·label 참조를 대조한다. 현재 baseline이면 고유 요청 합집합 579,442개, 원 owner/arm 580,035개와 580,040개의 논리 관계가 보존돼야 한다. 최소 4개 불확실 요청은 대사 결과 없이 planned가 될 수 없다. 이 숫자는 L0 이후 실제 변경이 없을 때만 적용한다.

### 6.2 소비자 전환과 rollback

저장소 manifest는 format/backend·generation·객체 목록 hash·writer epoch를 갖고 별도 store pointer를 CAS 전환한다. mutable SQLite 파일 hash를 실행 policy hash로 사용하지 않는다. 활성 request worker의 dual-write나 old/new 동시 예약을 허용하지 않는다.

구 v3/v4의 고정 module bytes와 과거 family/source hash는 보존한다. storage adapter와 postclose dispatcher의 연결로 소비자를 전환하고, 과거 family는 원 생성 code/native reader로 검증한다. 구현 중 고정 계약 모듈 변경이 실제 필요하면 대응하는 새 code/family 전환 경로를 설계·검증해야 하며 hash 검사를 완화하지 않는다. 저장 형식 v1을 이유로 후속 정책 v5를 강제 활성화하지 않는다.

전환 대상은 prepare/calls/auxiliary 보고뿐 아니라 exact import, 실제 응답 export, native stage/writer, source validator, semantic/strict/PREOPEN, 조사·복구 CLI와 retention consumer까지 포함한다. 발행 증빙은 불변 객체 closure로 검증하고 legacy 소비자는 기존 bytes의 검증된 export/adapter를 읽는다. 이전 active family의 frozen read-set을 이관 때문에 이동·삭제하지 않는다.

rollback도 **새 저장소에 추가된 시도·응답·불확실 예약을 잃지 않아야 한다**. 과거 SQLite 백업을 그대로 되돌리는 rollback은 금지한다. 구 실행 코드가 공통 원장을 읽는 검증된 adapter를 갖거나, writer를 멈춘 상태에서 최신 공통 상태를 구 형식으로 export해 모든 관련 alias/예약을 대사한 뒤에만 구 worker를 허용한다. 이 경로가 없으면 구 ledger의 원 파일을 지우지 않고 rollback 결손으로 남긴다.

### 6.3 삭제 가능 범위와 공간 회수

정리 대상은 검증 후 참조가 사라진 구 SQLite 중복 본문, 미완료 temp/중간 run의 재생성 가능한 파일, 미참조 객체다. DB/WAL/journal을 이름이나 크기만으로 삭제하지 않는다. active/rollback/발행/source/실제 응답/불확실 attempt/재개 checkpoint를 root로 하는 참조 closure를 먼저 계산한다.

회수는 명시적인 dry-run manifest → FD/lock·논리 hash·복원/consumer 검증 → 대상별 삭제 영수증 순서다. hardlink는 device/inode/nlink로 계수하고 마지막 참조가 제거되는 할당 bytes만 회수량으로 계산한다. 미래 GC는 동일 closure를 소비하고 live writer·staging lease와 경쟁하지 않도록 generation 고정과 삭제 전 재검사를 수행한다.

GC root에는 아직 발행하지 않은 expected membership, 모든 planned 요청의 재조립 객체, 미해결 attempt, 봉인한 비교 revision, migration/import cursor도 포함한다. retention 만료와 무참조는 다르며, 아직 필요한 행을 지워 expected를 줄여서는 안 된다. 각 참조 종류의 보존 종료는 해당 consumer 계약으로 판정하고 이번 문서에서 임의 일수 TTL을 신설하지 않는다.

새 저장소를 만들기 전 `현재 할당 + 신규 고유 객체/metadata + WAL/임시 block + 검증/rollback 보존분`의 peak disk를 계산한다. 현재 약 11GiB 원장의 단순 전체 복사본 두 벌을 추가하는 이관은 채택하지 않는다. 압축 보존이 필요한 파일은 round-trip hash/크기/복원 경로를 검증한다. 새 저장소만 줄고 구 원장·export가 그대로 남으면 실제 회수 완료가 아니다.

## 7. 기존 세 계획에 적용할 변경

| 계획·상태 | 유지할 계약 | 원장 보완 |
| --- | --- | --- |
| [전 종목 복수정책](main-all-scope-registered-multi-policy-implementation-plan-2026-10-07.md), 구현 이력 보유 | primary별 비교·원 승률/동률·현재/적용 버전·scope carry | P4/P6에 공통 store adapter·증분 membership·전수 상태 이관·저장/재개 검증 추가 |
| [추가 8개](main-additional-eight-pattern-registration-after-multi-policy-implementation-plan-2026-10-07.md), v4 구현/배포 영수증 보유 | 8개 정의·typed phase·기계 미선택의 provider 비대상·old bytes 보존 | v4 전용 전체 요청 DB 요구를 교체; R5/R6 이후 storage 보완으로 수행, 기존 연구 수용을 소급 변경하지 않음 |
| [운용 독립 탐지·기여도](main-operating-policy-independent-detection-and-contribution-evaluation-implementation-plan-2026-10-07.md), 후속 계획 | 전체 matched 근거·live 1회/1 intent·union/고정 추가안·N0~N8 | successor 전용 대형 DB 금지; N4/N6에서 복합 input 공유·comparison owner 참조·증분 전수성 검증 |

후속 N6의 입력 근거가 달라지는 비교안은 새 실제 요청이 필요할 수 있다. 공유 저장소가 모든 안을 같은 AI 응답으로 처리한다는 뜻은 아니다. 동일 내용의 공통 context/prompt/schema는 공유하고, 바뀐 `signals[]`와 정확한 요청만 새로 보존한다. 부분집합별 결과를 기존 단일 branch PASS의 OR로 합성하지 않는다.

## 8. 코드 소유와 실행 단계

코드 위치는 구조를 확인한 기존 역할 패키지를 사용한다. 공통 offline 저장/예약/객체 계층은 `src/engine/ai/`의 새 `offline_comparison_store` 계열 모듈, Main의 기회·phase·owner·legacy 이관은 `src/engine/scalping/`의 adapter가 소유하는 안이다. 테스트는 `src/tests/`에 둔다. `src/engine` root에 새 모듈을 만들지 않는다. live broker/intent/owner 원장을 이 공통 offline 저장소로 대체하지 않는다.

| 단계 | 수행 내용 | 종료 근거 |
| --- | --- | --- |
| L0 | 중단·현재/rollback·DB/WAL/journal·객체 read-set·공간 동결 | migration source manifest, 예약 충돌 census, peak disk 예산 |
| L1 | 작은 metadata·객체 pack·재조립·원자 예약·legacy alias 구현 | 원 bytes round-trip, 상태/참조/crash 대상 회귀 |
| L2 | v3/v4 일회성 streaming 이관과 전수 대사 | migration checkpoint, 요청/owner/응답/예약/label 누락·변경 0 |
| L3 | prepare/calls/보고·발행/검증·복구·retention adapter 연결 | 구/신 native reader와 rollback의 최신 상태 보존 |
| L4 | 날짜·원천 정정·새 arm/정의·동일 재실행의 증분 시험 | 실제 unique object 증가·전수 분모·provider 재사용·CPU/I/O/메모리 측정 |
| L5 | 리뷰→수정→재리뷰 및 격리 전체 census 검증 | in-scope 미해결 결함 0, targeted pytest/compile/diff와 저장 수용표 |
| L6 | 당시 승인된 배포/cutover 및 검증된 구 중복분 회수 | 단일 writer, store pointer/consumer 증빙, GC manifest와 실제 df |
| L7 | 사용자 별도 지시 뒤 오늘 장후 체인 재개 | 보류한 5개 cron·timer 복원 대조, EOD 재실행 없이 단일 재개 |

L 번호는 작업 ID이며 반드시 표 순서대로 대용량 작업을 실행한다는 뜻은 아니다. **L1과 L3의 adapter/구·신 reader/rollback을 fixture로 구현·리뷰·검증 → L2 일회 이관 → L3 전수 연결 검증 → L4/L5 → L6** 순으로 닫는다. 원 bytes 복원·late response·기존 frozen publication의 round-trip을 소규모 fixture/가짜 transport로 먼저 검증한다. L5에서는 L2의 전수 대사 영수증을 재사용하고 이후 변경에 영향받은 범위만 다시 검증한다. 리뷰를 반복한다는 이유로 매번 전체 원장을 재생성하지 않는다.

장후 재개 시에는 원천일 `2026-10-07`, 당시 publication/effective 영업일, EOD terminal/hash와 미완료 predecessor를 별도로 고정한다. 날짜가 넘어가도 작업의 원천일을 현재 날짜로 바꾸지 않는다. 중단 영수증의 5개 cron·timer만 현재 스케줄과 대조하고 과거 crontab 전체를 덮어쓰지 않는다. **수동 catch-up 또는 예약 실행 중 하나를 재개 owner로 선택**하고, 21:15/05:00 등 놓친 시간의 작업은 자동 실행된 것으로 간주하지 않는다. 예정 슬롯과 겹치거나 다른 원천일이 같은 writer를 쓰면 동일 lock 아래 직렬화한다. 의도적 보류는 held/incomplete이며 DONE/PASS로 위장하지 않는다. 이는 L7의 향후 절차이며 현재 재개 지시가 아니다.

storage 개선과 독립 탐지의 설계/소규모 구현은 역할 경계를 나눌 수 있지만, **대용량 이관·비교를 중복 실행하지 않는다**. N6이나 새 정책 버전의 대형 AI 비교는 L1~L5의 공통 원장 경로를 소비한다. 계획 작성 당시에는 실행 승인이 없었으며, 후속 사용자 지시로 현재 L0~L6 구현·이관·검증된 중복분 삭제·배포를 실행한다. 기존 v3/v4 연구를 다시 호출하지 않으며 L7 재개 권한은 별도다.

실제 provider 예약에는 L6 중 **store pointer·단일 writer/fencing 전환의 완료 영수증**도 필요하다. L2/L4의 staging 비교·회귀는 실제 provider를 호출하지 않으며, 실제 응답은 읽기 재사용하거나 가짜 transport를 사용한다. L6의 구 중복분 삭제는 별도 공간 회수 단계여서 그 완료를 AI 성과 gate로 쓰지 않는다. 정기 장후 재개는 L7이 별도로 소유한다.

## 9. 저장·정합성 수용 기준

| 상황 | 필수 결과 |
| --- | --- |
| 같은 원천·정의·arm을 같은/새 보고일에 준비만 재실행 | 새 고유 입력/요청 객체 0, provider 호출 0; 새 실행 영수증 외 기존 membership 재사용. 별도 허용된 미완료 호출 재개는 새 실제 응답을 추가할 수 있음 |
| 같은 의미의 v3/v4/후속 adapter가 같은 요청을 참조 | 전달 내용 1개·actual attempt 보존; 버전별 full JSON DB 복사 0 |
| 당일 신규 지점 Δ 추가 | 신규·변경 객체만 증가; 누적 전체를 다시 저장하지 않음, expected 전수 유지 |
| label-only 정정 또는 U→W/F | 모델 입력 불변; 기존 응답 재사용/미호출분만 준비; 정정 전 결과도 추적 가능 |
| prompt/model/schema/phase/복합 근거 변경 | 영향 요청만 새 key; 다른 계약의 응답 오용 0 |
| 복수 비교안·복수 policy 귀속 | 고유 request/attempt와 owner 분모 분리; union 거래는 한 번, 각 안의 분모 보존 |
| v3 reserved / v4 planned 4건 | 대사 전 예약 불확실 유지; 자동 재호출 0 |
| 요청·응답 fsync/commit 전후 crash, 두 worker 경쟁 | 참조 결손 탐지·fencing/단일 예약·응답/불확실 시도 소실 0 |
| 저장소 이동·pack 압축·GC | 논리 bytes hash·legacy/native 발행 증빙 동일; active/rollback/미완료 참조 삭제 0 |
| code/family rollback | 최신 실제 응답·예약 상태 유지, 과거 snapshot으로 상태 역행 0 |
| pending 입력의 원 raw 삭제·현재 prompt 변경 | 불변 재조립 closure로 원 bytes 복원 또는 해당 요청의 명시 결손; 바뀐 본문 전송 0 |
| 경계 source 정정·lookback/label 변경 | 의존하는 인접 partition만 무효화, 전체 재생 기준의 신호/라벨/누적 분모와 동일 |
| 봉인 후 늦은 응답·다중 응답·validator 재검증 | 기존 비교/정책 hash 불변, 새 revision만 생성, outcome을 본 뒤 유리한 응답 선택 0 |
| 자정 이후 장후 재개·timer 슬롯 경과·old worker 늦은 응답 | 원천일 보존, 수동/예약 중 한 owner, 전송 상태 역행·중복 실행 0 |
| 원천일당 누적 100 attempt·stage deadline·사용자 중단 | 전체 census/표본 구분, failed/uncertain 차감·재실행 reset 0; 중단을 완료로 표시하지 않음 |
| 새 prompt registry·당일 보조 교체·다음 날 기본 정책 반영 | 동일 원장/불변 객체 참조, live dedup 유지, active/rollback 증거 GC 보호, offline 완료를 PID/주문 권한으로 전용하지 않음 |

용량 보고는 metadata DB/index, 고유 input/prompt/schema, 실제 응답/journal, membership, compatibility export, old-store 보존, WAL/temp를 나눠 **고유 inode 할당량과 peak/steady-state**를 제시한다. 첫 이관의 설계 목표는 기존 두 원장 합계 약 10.95GiB 대비 최종 활성 원장 계층 80% 이상 절감이다. 이는 실측 전 보장이나 경제성 gate가 아니다. 미달하면 payload/index/export 중복 원인을 보완하며 표본·응답·증빙을 버려 목표를 맞추지 않는다.

호출 없는 동일 재실행, 신규 하루 추가, label 정정, prompt 변경, 후속 복합 입력의 다섯 시나리오에서 증가 bytes와 소요 시간을 제출한다. 회수 완료는 새 store 크기만으로 판단하지 않고 남은 rollback/export까지 포함한 실제 디스크 전후 차이로 보고한다. EOD 등 다른 writer의 증가분은 구분한다.

## 10. 계획 리뷰에서 반영한 사항

이번 문서 대조에서 버전별 원장 복제, generation별 owner/index 복제, 불확실 예약의 planned 역행, lazy 준비 시 expected 누락, 공통 입력 캐시와 실제 응답 재사용의 혼동, rollback 시 신규 예약 소실, old export를 남겨두는 명목상 절감, 미래 복합 입력과 live 주문 원장의 혼동을 보완했다. 세 정책 문서의 충돌하는 원장 namespace 문구도 이 공통 계약으로 교체했다. 준비만 재실행하는 경우와 허용된 미완료 실제 호출을 재개하는 경우를 분리해, 정상 새 응답을 중복 저장으로 오인하지 않도록 수용표를 수정했다.

문서 검증은 로컬 링크·단일 실행 owner·상태/승인 경계·세 계획의 요건 대조, `git diff --check`, print-only backlog parser로 닫는다. 소스·DB를 수정하지 않는 계획 작업이므로 거래 pytest·원장 전수 이관·provider 호출·장후 재생성은 수행하지 않는다.

### 10.1 네 계획 통합 재리뷰와 보완

아래 RR은 문서 검토 항목이며 새로운 OPEN owner나 구현 완료 영수증이 아니다.

| ID | 발견한 결함/모호함 | 보완·구현 검증 |
| --- | --- | --- |
| RR1 | 전 종목 계획에 정책/phase를 opportunity ID에 포함한다는 반대 문구 | phase는 request/lineage에만 포함; 동일 틱은 한 기회, namespace/legacy alias 충돌 회귀 |
| RR2 | 공통 원장·미래 successor 규칙이 구 v3/v4 선택/primary에 섞일 위험 | backend별 전략 계약과 저장 형식 전환을 분리; 저장 전후 선택/입력/분모 parity |
| RR3 | validator-only 변경과 전송 요청 변경의 key 경계가 불일치 | 전송 key·validation key·비교 snapshot 분리, 새 계약 재검증/구 응답 보존 |
| RR4 | 원장의 새 응답이 과거 비교/정책을 바꾸거나 유리한 응답으로 교체될 위험 | cutoff·response/validation/label 선택 봉인, outcome과 독립적인 응답 선택, partition 참조 revision |
| RR5 | owner 완료와 복수 attempt 상태를 같은 합계로 취급 | owner는 한 상태, 불확실 attempt 별도 회계; response ID 없음은 미전송 증거 아님 |
| RR6 | 지연 조립 전에 입력/현재 prompt가 바뀌거나 GC로 삭제될 위험 | planned 재조립 closure·serializer round-trip·expected/미완료 참조 보호 |
| RR7 | 파일 partition만 갱신해 인접 특징/label 정정이 누락될 위험 | 앞·뒤 read-set 역참조, producer 내용 증거, 전체 재생 대조 |
| RR8 | 대용량 이관/호출 뒤에야 소비자·rollback 결함을 발견할 순서 | adapter/reader/혼합 scope fixture를 먼저 검증, L6 예약 전환 후 실제 호출 |
| RR9 | successor 혼합 carry가 필수 scope 결손을 정상 bundle로 발행할 위험 | native 전체 coverage 검증·불완전 candidate CAS 거부, 검증된 현행 유지 |
| RR10 | 장후 재개 시 원천일 변경·놓친 timer와 수동 catch-up 중복 | 원천일/발행일/효력일 분리, 실행 owner 하나·동일 lock, 부분 스케줄 복원 |

이 보완은 네 계획의 본문·단계·반례 검증에 함께 반영했다. 구현 시 검증할 요건이며, 문서 검토로 데이터 이관/실제 provider/새 정책의 안전성 검증이 끝났다고 주장하지 않는다.

재리뷰 검증: 네 문서의 로컬 링크 51개와 절 anchor 1개, print-only parser 29개 작업 중 current owner 1개, 공백/충돌 표식 및 `git diff --check`를 통과했다. RR1~RR10의 본문·구현 순서·반례 연결을 재검토했으며 이번 문서 검토 범위의 미해결 finding은 없다. 소스 코드/원장/정책/스케줄 변경과 거래 pytest·provider·장후 실행은 수행하지 않았다. 실제 구현·이관·공간 회수·후속 자연 소비는 각각의 단계 영수증으로 별도 종결한다.

## 11. 구현 및 운영 인계

[구현·이관·배포 검토](../audits/main-ai-comparison-ledger-implementation-review-2026-10-07.md)가 실제 완료 수치와 릴리스 영수증을 소유한다. 이 절은 저장 경로의 운영 계약이다.

- `src/engine/ai/offline_comparison_store.py`: 공통 참조 metadata, 최대 16MiB 압축 pack, 공통+v3+v4 writer lock, 원자 예약, 응답 landing/journal, 불변 비교 snapshot과 validation 참조. 요청·입력·응답의 유효기간 삭제는 추가하지 않는다.
- `src/engine/scalping/continuous_reversal_shared_ledger.py`: 기존 공통 장후 CLI의 v3/v4 prepare/calls/auxiliary 경로를 연결한다. 적격 전수×5 arm, native primary/누적 raw PASS 승률·동률·scope carry를 유지한다. v3는 selected/baseline, v4는 여기에 consumed-version 비교를 추가하는 기존 차이를 보존한다.
- `src/engine/scalping/ai_comparison_ledger_migration.py`: `--mode import`, `verify`, `activate`, `retire-legacy`, `export-legacy`를 제공한다. 이관은 checkpoint부터 재개한다. `activate`만으로 provider 예약을 열지 않으며, 검증된 구 DB 경로를 `RETIRED.json` 디렉터리로 막은 뒤 writer를 허용한다. 구 native CLI의 직접 실행은 그 경로에서 실패하며 구 원장을 다시 만들지 않는다.
- 현재 입력 source에는 더 세밀한 봉인 segment/high-water가 없으므로 source/partition 내용 hash는 재검증한다. 동일 partition은 저장된 입력/요청 참조를 재사용하고, source 정정은 native 전체 session read-set에 결속된 해당 partition을 보수적으로 다시 투영한다. label-only 정정은 별도 membership/validation 집계 revision이며 같은 전송 요청과 실제 응답을 공유한다. CPU 비용까지 0이라고 표시하지 않는다.
- 매 요청별 파일은 만들지 않는다. 응답 landing 파일만 동시 전송 수 범위에서 잠시 존재하며, durable pack/journal commit 뒤 제거한다. full-body 호환 export는 실제 받은 응답에 한해 내용 hash로 공유한다.
- GC는 writer lock 아래 미참조 crash pack만 제거한다. indexed 객체, planned 조립 입력, 미해결 attempt, import checkpoint, 발행/rollback 자료는 유지한다. 장기 retention 종료 규칙을 임의로 만들지 않는다.
- rollback은 `export-legacy --generation ... --output ...`으로 **현재** 공통 원장의 응답·예약을 구 형식으로 출력하고 native reader로 대조한다. 삭제 전의 과거 SQLite를 복원해 호출을 재개하는 절차는 허용하지 않는다.

배포 후에도 10/7 원천일의 EOD 제외 장후 중단(5개 cron·최종 갱신 timer)은 유지한다. 저장 adapter 배포가 장후 완료, 새로운 정책 선택, 실제 AI 재비교 또는 Main PID의 새 정책 소비를 뜻하지 않는다.

실행 결과: L0~L6 구현·전수 이관·최종 253 PASS·배포·구 원장 회수 완료. 579,442개 공통 요청과 reserved 4건을 보존했고, 원장 할당은 10.95→1.32GiB로 감소했다. 자세한 수치와 범위는 위 구현 검토/최종 영수증을 따른다. L7은 계속 보류다.

마지막 호출 경로 보완: 공통 CLI와 직접 `auxiliary_report()` API를 모두 storage adapter로 전달하고, `main_auxiliary_policy`의 코드 fingerprint에 adapter/store 파일을 포함한다. 저장 코드 변경을 구 장후 단계 완료로 재사용하지 않도록 한다.

후속 복수정책/8개 연결 재점검은 [통합 감사](../audits/main-multi-policy-shared-ledger-integration-review-2026-10-07.md)가 소유한다. 공통 CLI의 `--mode prepare-inputs`는 예약/호출 없이 참조만 준비한다. compact 입력 참조 v2에 arm별 request ID를 보존하고 호출/집계 전에 owner·기회·arm·request·label 전부를 원장과 대사한다. v1 참조는 덮어쓰지 않고 재준비하며 같은 고유 요청/실제 응답/예약을 재사용한다. 비교 snapshot과 census receipt는 같은 writer lock에서 봉인한다. 당시 전수 비교는 미완료 scope의 기계·보조 쌍을 carry했다. 최초 지정 목록은 후속 초기 등록 계약을, 이후 sampled 보조 개선은 §4.3.1을 따른다. `--evaluate-only`는 보조 집계 전용이고 다른 mode 조합은 명시 거부한다. 당시 장후 보류/무제한 quota는 역사적 상태이며 현행 보조비교는 §5의 100 attempt 계약이다. 불확실 예약 보호는 계속 유지한다.
