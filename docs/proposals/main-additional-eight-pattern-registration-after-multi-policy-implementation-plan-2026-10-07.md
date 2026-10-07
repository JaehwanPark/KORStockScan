# Main 복수정책 구현 완료 후 추가 8개 패턴 등록 상세 구현계획

후속 방향: [운용 등록 정책 전체 독립 탐지·장후 기여도 평가 계획](main-operating-policy-independent-detection-and-contribution-evaluation-implementation-plan-2026-10-07.md)은 이 문서의 구현 종결 후 별도 사용자 구현 지시에 따라 진행한다. 운용 manifest의 모든 정책을 동등 탐지하고 복합 보조 입력·합집합/기여도 평가로 전환하는 후속 변경이며, 현재 진행 중인 본 계획의 정의·구현 수용 조건을 중간에 변경하지 않는다.

## 1. 목표·선행 작업·권한

사용자 요청은 **다른 세션에서 진행 중인 복수정책 구현 완료 후 추가 패턴을 등록할 수 있는 상세 계획 수립**이다. 이 문서의 작성·리뷰는 후보 등록, 정책 발행, provider 호출, 배포·재기동 실행을 뜻하지 않는다. 진행 중인 소스 작업본과 운영 정책을 변경하지 않는다.

선행 작업은 [전 종목·전 시장 등록 후보 복수정책 계획](main-all-scope-registered-multi-policy-implementation-plan-2026-10-07.md)의 P1~P6 구현 종결과 P7 운영 상태 인계이며 근거는 [v3 실행 감사](../audits/main-registered-multi-policy-v3-implementation-review-2026-10-07.md)에서 받는다. 실행 owner는 [당일 체크리스트](../checklists/2026-10-07-stage2-todo-checklist.md)의 `DirectFamilySourceRepairMainMechanisticEntry` 하나다. 이 계획은 그 owner의 후행 작업이며 별도 구현 세션·중복 OPEN을 만들지 않는다. 실제 착수일이 바뀌면 해당 날짜의 동일 owner로 원 승인·미완료 수용 조건을 인계한다.

목표는 연구에서 선택한 **8개 고정 정의를 기존 정책과 병행 비교할 수 있게 등록하고, 기계·보조 장후와 실시간에 같은 확인 의미로 연결하는 것**이다. 새 가설 탐색은 계속 수동연구가 소유한다. 장후는 등록 정의·명시 조합·장중 실제 적용 정책만 평가한다.

초안 검토 HEAD는 `558359c1`, 이번 재리뷰 HEAD는 `caa234167179c7433343bbfaa1e27d2607a02a94`다. 후자는 선행 장후의 row 원천 결손 분리와 영속 보조 원장 스트리밍 보완을 포함한다. 실행 감사는 여전히 구현 검증 중이므로 이를 완료 commit으로 단정하지 않는다. 선행 세션의 최종 commit/registry/발행 상태를 R0에서 새로 고정한다. 선행 작업의 배포·재기동 승인과 이 문서의 계획 상태를 구분하고 기존 승인을 취소하거나 중복 승인 절차를 만들지 않는다.

후속 사용자 지시로 이 계획의 구현·반복 리뷰·수정보완 및 완료 후 배포·재기동이 승인되었다. 아래 계획 단계는 [구현 검토 기록](../audits/main-additional-eight-pattern-implementation-review-2026-10-07.md)과 동일 current owner에서 실행한다. 이전 문서 작성 시점의 planning-only 상태를 이번 실행 승인으로 대체한다. 새 정의 등록과 실제 선택·PID 소비·자연 주문을 각각 기록한다.

## 2. 최초 등록 목록과 근거

### 2.1 8개로 고정한 범위

근거는 [전 종목 상승지속·경로 연구](../audits/main-continuation-and-path-confirmation-research-review-2026-10-07.md), [이전 FIRST 유형 연구](../audits/main-enter-pass-scarcity-and-opportunity-union-research-review-2026-10-07.md)다. 9/21·22·23·28·29·30, 10/2·6·7의 보유 원천 18개 SOR PRE/REGULAR 파티션을 연구했고, **아래 8개는 모두 SOR REGULAR·정확한 `symbol_AL` item에만 등록**한다. 오늘 REGULAR 연구 접두는 15:20이다. 전 시장 운용 기능과 개별 후보의 연구 적용 범위를 구분한다.

표의 W는 비용을 반영한 목표 선도달, F는 손절 선도달+완전 관측 미도달, U는 원천 경로 부족 등 미확정이다. 수치는 각 후보가 **연구 당시 기준 정책 확인점 밖에서 추가한 점**이다. 다른 신규 후보끼리 중복을 뺀 순차 증가분 또는 독립 거래 수가 아니므로 합산하지 않는다.

| 별칭 | 대상·확인 방식 | 실제 확인점의 유형 조건 | 누적 추가 W/F/U | 오늘 추가 W |
| --- | --- | --- | ---: | ---: |
| SA | 삼성 005930·60초 수익률 +0.1% 상향 전환 | UP·SLOW·FALLING·DD `[0.2,0.4)` | 22/0/1 | 0 |
| SB | 삼성·저점 재시험 후 원 고점 회복, 최대 120초 | NEUTRAL·NEGATIVE·FALLING·DD `[0.4,0.8]`·거래량비≥1 | 53/0/135 | 0 |
| DA | 두산에너빌리티 034020·+0.1% 상향 전환 | NEUTRAL·FAST·MIXED·DD `[0.2,0.4)`·VWAP 이상 | 13/0/10 | 4 |
| HA | HPSP 403870·기존 FIRST 반전 | DOWN·NEGATIVE·FALLING·원 FIRST DD `(0.8,1.2)` | 30/0/15 | 30 |
| HB | HPSP·직전 60초 고점 돌파 전환 | UP·FAST·RISING·DD `<0.2` | 6/0/10 | 6 |
| AA | 알테오젠 196170·저점 재시험 후 원 FIRST 가격 회복, 최대 120초 | DOWN·SLOW·MIXED·DD `(0.8,1.2)` | 20/0/0 | 20 |
| JA | 주성엔지니어링 036930·+0.2% 상향 전환 | UP·FAST·RISING·DD `<0.2` | 44/0/0 | 44 |
| GA | 일반 비삼성 2만~10만원 미만·+0.05% 전환 후 1초 가격 유지 | DOWN·SLOW·MIXED·DD `(0.8,1.2)`·VWAP 이상 | 36/4/43 | 5 |

HA만 원 FIRST 시점 특징·DD를 사용한다. 나머지 7개는 §4의 실제 확인점 특징을 사용한다. GA의 실패 4개는 STOP 1·완전 미도달 3이며 누적 확정 도달률은 36/40=90%다. HB의 단독 전체는 6/0/11이고 기존 확인점과 겹치는 미확정 1개를 뺀 추가 수치가 6/0/10이다.

삼성 SA/SB는 누적 근거로 등록할 가치가 있다. 오늘 두 후보의 추가 확인점은 각각 U 1·4이고 오늘 상승 포착 입증은 없다. 전체 연구에서 선택한 삼성 44개 U와 이 8개 등록안의 삼성 5개 U를 혼동하지 않는다. HPSP·알테오젠·주성의 이점은 오늘에 집중되어 있고 AA의 20점도 독립 거래 20건을 의미하지 않는다. 날짜/목표 시각 집중도와 U는 보고하며 최소 날짜·최소 표본·새 날짜 검증·성공 보존 조건을 추가하지 않는다.

### 2.2 원 정의 식별자

별칭은 문서 표시용이다. 연구 정의를 다시 입력하거나 임계값을 반올림하지 않고 아래 객체를 정확히 추출한다. 정식 포장에 phase/schema가 추가되면 `research_definition_sha256`와 `runtime_definition_sha256`을 구분하고 변환 manifest를 남긴다. 과거 정의 hash를 새 객체의 hash인 것처럼 재사용하지 않는다.

원 연구 객체는 그대로 보존하고 새 실행 phase binding은 외부 등록 envelope에 둔다. 동일 branch ID로 유지하려면 원 정의의 의미·내용을 유지하고 envelope hash만 별도로 계산한다. 조건/확인 의미를 바꿔야 한다면 새 branch ID/version과 원 연구 ID의 대응을 만들고 다시 재생한다. schema 포장을 이유로 수치·시점을 몰래 변경하지 않는다.

| 별칭 | 기존 연구 branch_id | 연구 definition_sha256 |
| --- | --- | --- |
| SA | `manual_path_35c2d4b8fb178441` | `0c606c6f14e9a141a0b6c0eb18fab4bfc82cd530d033b8a18bf600460d7d5cb4` |
| SB | `manual_path_918aff358c3edb8c` | `b7ad047d7078aa6f31f2cda12c946a0fcd0ee9502d28ab5c65e13f1392c6208d` |
| DA | `manual_path_ad9afa2f9f981689` | `11e6c7ac5139956ccb4c5b3c192154cb23d344e78f38a64ac33854214ecc4573` |
| HA | `manual_type_ae4445459dc942c8` | `48e2f9b9a40619d0a31ae36d544196fbeb5fd382ac1fbeb7cbdd13bfb6c26dce` |
| HB | `manual_path_f37911fb56300f77` | `e9959c80f296d01824badaddd0d637be563bc7d38a73a015ea9ebd4d71fc6be5` |
| AA | `manual_path_9e8f22a0a77899e4` | `8a44fe1b4cac82fcc092c25dcded036ac9a61aed3eed0506a0a2a68410a87961` |
| JA | `manual_path_7d9fd5ccc8bfe99b` | `5f0b27afa6703df97120b76c18582461a818d8183e627206196044d3e7f1274b` |
| GA | `manual_path_dca327a873720e53` | `654d2861d52af8505d5fcc4bc17df9178c9fa0cd6795008230b8b2bd905f0c6a` |

원본은 [경로 등록 제안](../../tmp/main-continuation-path-research-20261007/proposed-path-registration-batch.json)의 7개와 [FIRST 등록 제안](../../tmp/main-continuation-path-research-20261007/proposed-type-registration-batch.json)의 HA다. 두 batch의 내부 hash는 각각 `4868f7f9bf7e14d1d9af2e72c55e19562b90683455eb1a08d8caaa69ebcb239c`, `6e34a8a35dfa7ffac2549e3134a7c26153964c33a51d9e45a55659fa7ae3f330`이다. 내부 내용 digest와 파일 bytes SHA를 별도로 검증한다.

223개 FIRST·1,157개 경로 유형 전체, 43개 확인 root 전체는 첫 등록 대상이 아니다. 이번 목록에 없는 `rebound` 필터 alias 보완이나 추가 가설 개발을 8개 등록의 선행 과제로 확대하지 않는다.

## 3. 선행 구현 인계와 버전 호환

### 3.1 R0에서 받을 완료 자료

1. 선행 구현의 최종 commit·변경 파일/검증 결과·미해결 finding, immutable registry manifest/hash, 48셀·실제 지원 route 집합, source/feature/label/auxiliary schema.
2. native loader가 고른 실제 current parent bundle/family와 적용 일자, 장중 실제 적용 버전 census, 기존/등록 후보 목록, 보조 입력·prompt·validator hash. 최초 날짜별 파일이나 연구 당시 기준 정책을 current로 대신하지 않는다.
3. source/publication/effective 날짜, registration custody, reports/ledger/checkpoint 경로, stage/CAS/rollback 계약, 아직 진행 중인 작업과 후행 세션 변경 소유.
4. code 완료·배포·PID 소비는 별도 필드로 받는다. 등록 준비와 격리 검증에 자연 주문·체결·수익 입증을 추가하지 않는다. P1~P6 코드/계약/검증 완료와 변경 소유 인계가 착수 조건이며, P7의 아직 발생하지 않은 자연 신호는 `not_observed`로 이어받는다. 다른 세션이 사용 중인 공유 소스·registry·활성 pointer를 병행 수정하지 않는다.

종결 commit이 변하거나 활성 부모가 바뀌면 해당 diff와 부모만 다시 동결한다. 연구 전체를 무조건 재실행하지 않는다. 필요한 원본을 사용할 수 없으면 정확한 원본/후보 범위의 결손으로 남기고 임의 현재값으로 복원하지 않는다.

### 3.2 확인한 호환 문제와 구현 방향

[v3 validator](../../src/engine/scalping/continuous_reversal_policy_v3.py)는 registry version/hash/manifest를 현재 [catalog](../../src/engine/scalping/reversal_registered_catalog.py)의 전역 상수와 비교한다. source validator는 runtime/catalog/postclose 등 코드 bytes도 고정한다. **동일 catalog에 8개를 append하면 아직 구 정책을 운용 중이어도 구 family 검증이 깨질 수 있다.**

따라서 후속 계획의 기본안은 **새 확인 phase를 가진 `continuous_reversal_policy_v4`와 별도 경로 catalog/runtime/보조 계약을 추가하고 v1/v2/v3 읽기를 보존하는 것**이다. v3와 그 hash 고정 모듈은 완료 인계 bytes를 보존한다. v4는 v3의 검증된 기존 정의를 hash로 참조하며 구 정책의 정의·prompt를 복사해 다른 의미로 만들지 않는다. 공통 순수 계산은 읽기 재사용하고 callback/loader는 family version에 따라 정확히 하나의 상태 소유자를 선택한다.

- 구 family는 그 생성 당시 registry/code 증빙으로 검증한다. 현재 새 catalog와 같아야 한다는 조건으로 옛 family를 거부하지 않는다. 임의 hash 허용이나 source 검증 생략도 하지 않는다.
- 먼저 새 코드를 준비하되 구 family만 로딩하는 호환 검증을 통과한다. 새 registry 등록과 candidate 작성만으로 current pointer·기존 callback dispatch를 바꾸지 않는다.
- v4 이관은 기존 branch 목록·순서·primary tie 순서·보조 binding·지원 route를 모두 보존하고 신규 미선택 상태의 행동 동등성을 입증한다. 이후 별도 누적 비교에서 선택을 바꾼다.
- 인계된 선행 코드가 이미 버전별 catalog/새 phase 확장을 제공한다면 동일 기능을 다시 만들지 않는다. R0에 차이를 기록하고 이 호환 계약을 만족하는 기존 확장점을 사용한다. 그 경우 실제 schema 이름과 코드 소유만 갱신한다.
- 현재 포트폴리오와 사용했던 모든 버전은 새 source에서도 원래 의미로 재생한다. 알 수 없는 버전을 현재 정의로 치환하지 않는다.

### 3.3 새 버전 분기에서 빠뜨리면 안 되는 소비자

현재 [공통 policy compose](../../src/engine/scalping/continuous_reversal_policy.py)는 v2/v3만 새 phase 응답 및 provider 이후 현재 family/claim을 재검증한다. [AI engine](../../src/engine/ai_engine_openai.py)의 claim·arm 선택도 같은 목록을 사용한다. 새 v4가 목록에서 빠지면 v1 snapshot/validator 경로로 흐를 수 있다. 파일명 추가만으로 호환 완료를 선언하지 않는다.

| 호출 경계 | 후속 구현의 필수 변경·실패 조건 |
| --- | --- |
| `load_effective`·stage/activate·direct handoff | v4 schema를 native dispatcher에 명시 등록. 현재/정확일 candidate/승계/소스 검증 모두 같은 버전을 선택하고 알 수 없는 schema는 명시 거부 |
| observation configure·claim·acknowledge | 신규 backend dispatch는 hash 고정 v3 runtime 밖의 adapter가 소유. v3 파일을 새 backend 등록 목적으로 수정하지 않으며, 해당 backend의 configure/observe/claim/validate/acknowledge 전체를 함께 연결 |
| AI 요청 전 | 선택된 family의 snapshot·phase·arm·정확 입력 사용. v4에서 v1 current snapshot 또는 단일 cell arm으로 fallback 금지 |
| AI 응답 후 `compose` | exact phase 응답 검증에 이어 현재 bundle/family 일치·5초 claim·원천 경로·primary 유효성을 다시 검사. 요청 중 정책 교체/소멸이면 BUY 권한 없음 |
| Main bootstrap·장후·의미 감시 | registry/definition/phase/branch/PID receipt를 새 schema로 읽고 구 receipt는 원 schema로 검증. 알 수 없는 버전을 정상 무신호로 처리하지 않음 |

전체 분기 matrix에는 v1/v2/v3/v4/unknown × 요청 전/응답 후/기동/장후/감시를 넣는다. 필요한 의미가 같은 공통 계산은 재사용하되, v3의 고정 코드 bytes를 보존하면서 신규 adapter와 기존 비고정 dispatcher에서 연결한다. 반대로 로컬 소스 보존만으로 과거 source validation이 통과한다고 가정하지 않고 실제 구 bundle의 native load/assess를 검증한다.

## 4. 공유 특징과 확인 상태 구현

### 4.1 특징의 정확한 의미

| 특징 | 고정 계산 계약 |
| --- | --- |
| session | 해당 날짜·종목·market·item의 첫 유효 관측 가격 대비 수익률. UP≥+0.4%, DOWN≤-0.4%, 그 사이는 NEUTRAL. 외부 지수 국면이나 공식 시가가 아니다 |
| ret60 | 확인점 가격 / 연속 경로의 `t-60초 이하 마지막 관측 가격` 변화율. NEGATIVE<0, SLOW `[0,0.2)`, FAST≥0.2; 60초 native history 필요 |
| structure | `[t-30,t]`와 `[t-60,t-30)`의 고점·저점이 모두 엄격 상승이면 RISING, 모두 엄격 하락이면 FALLING, 나머지 유효 계산은 MIXED. 60초 history 결손은 UNKNOWN |
| path DD | `100*(현재 틱 이전 300초 고점/현재 체결가-1)`. 현재 틱 제외, 당시 연속 history 사용. 기존 trough DD와 분리. 별도 300초 warmup을 덧붙이지 않으며 음수를 0으로 자르지 않는다 |
| FIRST DD | HA는 원 FIRST 연구 kernel의 원 저점 기준 DD를 그대로 사용. path DD로 대체하지 않는다 |
| volume ratio | 현재 60초 체결수량 / 직전 60초 체결수량. 120초 연속 history·유효 수량 필요. 분모 0·수량 결손은 UNKNOWN |
| VWAP | 확인점까지 유효 수량으로 계산한 60초 VWAP 대비 가격 변화율; `vwap_min=0`은 이상 포함 |
| 가격대 | 실제 확인 체결가 기준 `<20,000`, `[20,000,100,000)`, `≥100,000`. GA만 중간 가격대; 고정 종목도 native 선택 셀의 가격대와 결속 |

현재 runtime의 spread `100*(ask/bid-1)`와 연구의 `100*(ask-bid)/trade`도 동일 수치로 치환하지 않는다. 첫 8개에는 spread/buy10 필터가 없으므로 이 필드를 새 필수값으로 만들지 않는다. 기존 quote/source guard는 유지한다.

종목/날짜/market/실제 item/epoch/sequence가 상태 소유 키다. 중복된 동일 원본은 한 번 처리하고 충돌 중복·invalid packet·순번 단절·item 변경은 그 영향 구간의 상태를 끊는다. 재기동 때 현재가를 세션 최초가로 재설정하지 않고 검증된 원 anchor를 복원하거나 필요한 branch만 UNKNOWN으로 둔다. 수량·방향 결손을 0/매도로 채우지 않는다. collection stream과 live stream의 seq를 근접 시각으로 강제 동일시하지 않는다.

### 4.2 연속 상승 root: SA·DA·HB·JA·GA

현재 [등록 runtime](../../src/engine/scalping/reversal_registered_runtime.py)은 `legacy.turn`이 새로 생긴 뒤 FIRST/5초 CONFIRMED를 평가한다. 연속 상승 root는 **첫 반전 발생과 무관하게 모든 유효 틱**에서 공통 특징을 읽어야 한다. 종목별 공유 window를 한 번 갱신하고 선택된 root의 상태를 한 번 계산한 뒤 여러 branch 필터가 재사용한다.

- SA/DA: `ret60>=0.1`, JA: `ret60>=0.2`, GA: `ret60>=0.05`가 **known false→known true**로 바뀐 틱이 시작점이다. unknown→true, 재기동 직후 true, 계속 true인 매 틱을 새 신호로 만들지 않는다.
- DA의 root는 +0.1%이고 실제 확인 필터는 FAST≥0.2%다. 관측 한 번에 두 경계를 뛰어넘는 경우를 포함하므로 root를 +0.2%로 바꾸지 않는다.
- HB: 60초 유효 history에서 현재 틱을 제외한 직전 60초 최고가를 엄격 초과하는 false→true 전환이다. 같은 시각의 앞선 sequence는 과거 관측으로 포함한다. 선행 하락·저점·첫 상승을 요구하거나 합성하지 않는다.
- GA: 시작 후 1초 이상이 된 첫 실제 수신 틱에서 확인한다. 그 사이 모든 체결가가 시작 체결가 이상이어야 한다. 동률은 유지, 한 번이라도 하회하면 해당 시도 종료다. 확인 시점의 SLOW/DD/VWAP 필터를 사용하며 +0.05%를 계속 유지해야 한다는 추가 조건은 넣지 않는다.
- 모든 새 확인점의 진입 가격은 **그 시점의 fresh ask**, 라벨 시계도 그 시점부터 다시 1,800초다. 원 시작점의 싼 ask나 미래 고점을 진입가로 사용하지 않는다.

전환은 바로 앞 native 관측과 현재 관측이 모두 known이고 연속일 때만 성립한다. `false→UNKNOWN→true`도 새 crossing이 아니다. 타입 필터 불일치나 호가 결손을 root 조건의 false로 바꿔 다음 틱을 재발화시키지 않는다. root가 지정한 첫 확인점에서 필터/호가를 평가하고 실패하면 해당 시도는 끝난다. 예를 들어 retest의 첫 reclaim에 호가가 없거나 GA의 첫 1초 경과 틱에서 VWAP 필터가 미달이라고, 나중의 더 유리한 틱으로 확인점을 옮기지 않는다. 이는 [연구 확인점 생산 코드](../../tmp/main-continuation-path-research-20261007/research.py)의 root 생성→첫 확인점→quote/type 필터 순서를 보존한다.

GA 연구 정의에는 1초 이후 별도 최대 유예 시간이 없다. source continuity/freshness로 무효인 점은 기존 계약대로 배제하되, 구현 편의로 새 5초/120초 hold 만료를 추가하려면 별도 정의와 재생이 필요하다. claim 유효기간과 hold 대기시간을 혼용하지 않는다.

### 4.3 저점 재시험 root: SB·AA

기존 정책의 통과 여부에 관계없이 모든 native FIRST turn의 원 peak/low/FIRST 가격·index·시간을 동결한다. 상태는 `WAIT_RETOUCH → WAIT_RECLAIM → CONFIRMED/INVALIDATED/EXPIRED`다.

1. 원 FIRST 이후 체결가≤원 low가 처음 관측되면 retouch로 기록한다. old CONFIRMED의 저점 재접촉 즉시 무효 규칙을 재사용하지 않는다.
2. retouch **이후의 틱**에서 SB는 원 peak 이상, AA는 원 FIRST 가격 이상인 첫 틱을 확인점으로 삼는다.
3. 원 FIRST부터 120초 **이하**까지 허용한다. 체결가가 원 low×0.998 **미만**이면 즉시 무효다. 경계와 같은 값은 허용한다. 확인점 이전·확인점에서 발생한 breach를 무시하지 않는다.
4. sequence/epoch/item/원천 유효성이 끊기면 pending을 종료한다. 당시 검증된 접두 없이 재기동 후 pending을 복원하거나 과거 확인점에 새 claim을 만들지 않는다.
5. 같은 root/branch에서 여러 anchor가 같은 틱에 확인되면 모든 anchor lineage를 보존하되 가장 이른 유효 anchor를 대표로 고른다. feature 필터와 ask는 실제 확인점 값이다.

원 peak/low/FIRST 증거는 pending 생성 때 원 native ID·가격·시각으로 동결한다. 기존 `ReversalState.snapshot()`에 가짜 turn을 주입해 새 입력을 만들지 않는다. 새 phase는 별도 prefix projector로 확인점까지의 공통 관측 사실과 동결한 anchor를 결합한다. peak가 rolling buffer 밖으로 나가도 증거를 버리지 않으며 전체 원천 재조회로 callback을 막지 않는다.

### 4.4 실시간 전달·단일 intent

새 claim envelope는 `canonical_opportunity_id`, 원 stream 식별자, source/code/registry/family/definition hash, root kind, signal/anchor/confirmation 시각, branch별 실제 확인 사실과 feature phase를 보존한다. 낮은 가격이나 추가 상승 사실이 없는 유형에 해당 필드를 가짜로 채우지 않는다.

같은 native 확인 틱의 FIRST/CONFIRMED/새 path 신호는 하나의 평가 묶음으로 합친다. 선택된 branch의 누적 성과와 기존 결정적 tie 순서로 primary 하나를 정하고 그 branch의 정확한 phase 입력을 사용한다. 모든 matched branch와 대표 anchor는 기록한다. 한 기회에 intent·운영 보조 요청은 하나이고 VETO 뒤 다른 branch로 재요청하지 않는다. 다른 확인 틱은 별개 기회지만 기존 포지션·진행 주문·cooldown·custody가 후속 진입을 계속 제어한다.

기존 5초 claim 전달 기한은 **실제 confirmation부터** 센다. 120초 retest 대기와 분리한다. 새 phase에 FIRST 전용 '다음 틱에 첫 신호 무효' 규칙을 잘못 적용하지 않고, 기존 phase는 원 동작을 유지한다. source generation/family 변경 시 미소비 claim을 폐기하고 warm history 재사용 여부를 검증한다. 확인→큐 삽입→기계 평가→provider 요청 시각·지연을 남겨 새 경로가 평가 전에 소멸하는지 점검한다.

### 4.5 가격대 이동·재생 큐·정상 소멸

GA는 **확인점 가격대**로 유형을 정한다. 현재 v3 callback은 매 틱의 가격대에서 선택된 branch만 `state.branch_ids`에 넣으므로 그대로 복사하면 19,990원에서 시작하여 20,010원에서 유지 확인된 GA를 놓칠 수 있다. v4는 같은 family·종목군·market·route에서 **어느 가격대에든 실제 선택된 root들의 합집합**만 공유 state로 추적하고, 실제 확인 시점에 해당 가격대의 선택 branch/filter를 적용한다. 모든 등록 후보를 장중에 평가하라는 뜻이 아니다. HA 등 원 FIRST 정의의 anchor 가격대 의미는 바꾸지 않는다. family 전환으로 새로 필요한 root는 검증된 history로 상태를 복구하되 과거 완료 신호를 발행하지 않고, 복원 불가면 warmup/UNKNOWN으로 표시한다.

offline replay는 매 틱의 확인점을 즉시 별도 iterator로 배출한다. 실시간 `MAX_READY=256`, 5초 claim 만료·claim 소비 속도를 과거 확인점 표본 상한으로 사용하지 않는다. 긴 retest의 anchor도 순수 root/FSM에서 완전하게 재생하고, 실시간 pending 저장 한도 `MAX_PENDING=1024`와 overflow는 별도 execution-capacity 계측으로 검증한다. 연구상 완전 모집단과 운영상 처리 가능한 확인점 수를 따로 출력하고 overflow를 조건 미충족/정상 무신호로 숨기지 않는다. 한도 변경 필요성은 부하 근거와 함께 보고하며 이 계획으로 기존 한도를 임의 완화하지 않는다.

새 path 확인은 특정 틱에서 완료된 사실이다. 이후의 일반 가격 변화만으로 '처음부터 신호가 없었다'고 바꾸거나 기존 FIRST 전용 무효화를 적용하지 않는다. 이후 source break·정책 전환·TTL 만료는 현재 claim을 종료하며 live 최신 호가/제출 guard는 계속 별도 검사한다. root별 추가 사후 가격 무효화 조건을 원 연구 정의 없이 만들지 않는다. 완전히 유효한 관측에서 나온 조건 불일치·retest breach/timeout·hold 하회·미소비 TTL은 정상 lifecycle, 필수 원천/특징 결손과 native 불연속은 source 상태, pending/ready 초과는 capacity 상태로 기록한다.

## 5. 보조판정 계약 확장

[기존 보조 phase](../../src/engine/scalping/reversal_auxiliary_phases.py)의 CONFIRMED는 '원 FIRST 이후 5초 이내 추가로 더 높은 체결'과 하락 사실을 요구한다. 이를 120초 retest·상승지속형에 그대로 붙이면 정상 기계 신호가 계약 위반으로 탈락한다.

| 신규 phase | 대상 | 입력/응답 validator가 확인할 실제 사실 |
| --- | --- | --- |
| `MOMENTUM_CROSS` | SA·DA·JA | 관측된 ret60 임계값 전환, 시작·현재 native ID, 확인 시점 context |
| `HIGH_BREAKOUT` | HB | 현재 틱 제외 prior high, strict 초과, 관측 전환 |
| `MOMENTUM_HOLD` | GA | 원 임계값 전환, hold 기준가·기간·중간 하회 없음, 실제 확인점 |
| `RETEST_RECLAIM_PEAK` | SB | 원 peak/low/FIRST, retouch, 허용 저점 하회 경계, peak 회복·120초 기한 |
| `RETEST_RECLAIM_FIRST` | AA | 같은 retest 증빙과 FIRST 가격 회복·120초 기한 |
| 기존 `FIRST_UPTICK` | HA | 기존 FIRST 입력/prompt/응답 validator bytes 유지 |

새 phase의 system/user/schema/fact ID는 English ASCII로 작성한다. 보조 역할은 위험 점검 PASS/VETO이고 기계 BLOCK/RECHECK를 ENTER_NOW로 승격하지 않는다. 선행 하락이 없는 HB 등에 `observed_price_decline`을 필수 fact로 두지 않는다. optional missing과 필수 source 결손을 구분한다. 미래 라벨·목표 시각·성과는 모델 입력에서 제외한다.

새 phase에는 `machine_signal_confirmed`와 `signal_kind`로 실제 확인 사실을 표현한다. 기존 `price_reversal_confirmed`는 원 FIRST/CONFIRMED 계약에서만 원 의미대로 보존한다. [제출병목 감시기](../../src/engine/monitoring/submission_bottleneck_monitor.py)의 기존 event/low/drop 사실 요구와 `reversal_auxiliary_contract`의 reversal assertion을 신규 상승지속형에 적용하지 않도록 버전별 native 재평가·receipt verifier를 연결한다. 반전이 없는 신호를 통과시키려고 `price_reversal_confirmed=true`·가짜 low/drop을 채우지 않는다. 감시 경보를 끄는 것으로 소비자 보완을 대신하지 않는다.

새 문구는 수동으로 정의한 고정 arm 목록을 version/hash로 등록한다. 기존 비교 arm 체계를 재사용하되 새 phase 의미에 맞춘 요청을 고정하며, 장후가 문구를 생성/최적화하지 않는다. 입력/문구/schema/validator가 달라졌으면 과거 유사 문구의 PASS를 재사용하지 않고 정확한 새 bytes의 실제 응답을 비교한다.

- offline 비교 키는 scope/branch/definition/phase/기회/arm이다. provider 요청 키는 **canonical 기회 ID + phase + provider/model 생성 설정·prompt·input·schema의 정확한 bytes hash**로 고정하며 선행 exact ledger와 같은 경계를 사용한다. 여러 비교 소유자가 같은 기회·phase의 완전히 같은 요청을 공유할 수 있지만 다른 native 기회를 비슷한 입력이라는 이유로 합치지 않는다. 라벨/성과/비교 owner는 요청 키와 AI 입력에서 제외하며, source 정정 후 입력이 그대로면 실제 응답을 재사용하되 새 run의 라벨 연결만 검증한다.
- 라벨 연결은 동일 native 확인점·확인 ask·source/hash에 결속한다. branch별 입력을 FIRST/CONFIRMED 배열에서 임의 fallback하지 않고 typed `branch_inputs`에서 직접 찾는다.
- 실제 원 응답·요청/응답 hash·유효성·중복/오류·예약 상태를 ledger/checkpoint에 보존한다. 비교는 전체 eligible 입력을 대상으로 하며 기존 사용자 승인 `quota=None`과 외부 rate limit을 유지한다. 호출 수를 숨기거나 날짜별 임의 표본 상한을 재도입하지 않는다.
- 실행 전 exact cache hit/miss·예상 요청 수·분할 처리량을 출력한다. 메모리는 partition iterator/bounded in-flight로 제한하고 중단 후 영속 checkpoint에서 재개한다. 결과 불명 호출을 성공으로 바꾸거나 무한 재시도하지 않는다.
- 보조 선택은 기존 owner의 **실제 raw PASS 중 WIN/PASS 수** 비교 계약을 유지한다. 같은 성공 100%/80% 보존, 양의 EV, 새 날짜 검증을 탈락 기준으로 추가하지 않는다. 기계 W/(W+F)와 보조 PASS 분모를 혼용하지 않는다.
- 기계 최선 후보가 나와도 해당 보조 비교가 미완료면 `machine_winner`와 `publishable_pair`를 따로 남기고 그 scope의 검증된 기존 기계·보조 쌍을 함께 carry한다. 가격 WIN만으로 PASS를 생성하지 않는다. 이 상태가 등록 실패나 기계 열위로 집계되지 않게 한다.

### 5.1 보조 비교 대상과 완료의 정확한 의미

기계는 모든 등록 후보/조합을 비교한다. 보조 호출 대상은 선행 계획과 같이 **기계 winner 포트폴리오의 실제 primary 경로와 현행/장중 적용 버전의 실제 primary 경로**다. 미선택 후보는 `not_requested_machine_unselected`, 조합 안에서 primary가 된 점이 없는 branch는 `no_primary_points`로 보고한다. 기계 미선택 8개 전부에 provider 호출이 끝나야 등록 완료라는 조건을 추가하지 않는다.

비교 입력의 eligible 집합은 동일 누적 원천에서 라벨이 W/F로 확정되고 실제 확인 입력을 재구성할 수 있는 점이다. 현재 `prepare_inputs`의 U 제외와 일치시키며 `UNRESOLVED`, 필수 입력 결손, quote 결손의 수/ID/사유를 따로 보존한다. 이는 전수 eligible 비교이며 날짜별 샘플 제한이 아니다. 실제 자연 응답이 있더라도 U를 F로 바꿔 PASS 분모에 넣지 않는다. raw PASS 승률의 '전체'는 이 명시한 eligible 집합 안의 실제 raw PASS이며 응답 유효성을 가중치로 조정하지 않는다. 계약 위반 응답 수는 별도 보고하고 운영에서는 validator가 해당 PASS를 계속 거부한다.

예상 비교 소유 집합과 고정 arm 집합을 원장 준비 **전에** manifest로 봉인한다. 원장에 들어온 행의 수만으로 완료를 판단하지 않는다. 각 비교에서 `expected = completed + planned + reserved_uncertain + failed`를 중복 없는 owner/arm ID로 대사하고, 입력 생성 누락·잘못 연결된 응답도 발견할 수 있어야 한다. 같은 eligible 점에 모든 등록 arm의 실제 응답이 있어야 그 점의 비교가 완결된다. 일부 성공 응답만 순위에 반영하여 전체 winner로 발표하지 않는다.

모든 arm이 정상 완료됐지만 PASS가 0인 `completed_no_pass`는 호출 미완료와 다르다. 같은 branch/phase/input 의미의 검증된 이전 binding이 있으면 그 근거를 carry하고, 없으면 `no_comparable_auxiliary_arm`으로 해당 기계·보조 쌍을 carry한다. 등록 자체는 유지한다. `no_primary_points`도 가상의 PASS나 다른 branch의 성과를 복사하여 채우지 않는다. 향후 해당 branch가 primary로 선택될 때 필요한 비교를 생성한다.

## 6. 등록 자료·비교 조합·장후 선택

### 6.1 영속 등록

기존 `data/report/continuous_reversal_registered` custody 구조 안에 batch/8개 정의/변환 manifest/명시 portfolios/원천·연구 코드·결과 SHA/비교 접두를 immutable하게 보존한다. 운영에서 `tmp` Python을 import하거나 임시 경로를 유일한 근거로 참조하지 않는다. 원본을 옮겨 삭제하는 대신 검증된 보존본을 만들고 원 경로·hash→보존 경로·hash 대응을 남긴다. 공유 대형 raw는 보호된 기존 content-addressed source를 참조하고 중복 복사를 피한다.

등록 식별자는 정의 내용으로 고정하고 최초 registration/source date를 보존한다. 후속 날짜 비교가 같은 정의를 재사용할 수 있어야 한다. 원 registration의 날짜를 새 source date로 덮어쓰거나 서로 다른 정의를 같은 ID로 갱신하지 않는다. catalog hash뿐 아니라 개별 definition/root/feature/phase/portfolio hash와 변환 code hash를 연결한다. retention은 active/rollback/비교 consumer가 사용하는 원본을 보호한다.

새 자료의 쓰기 소유는 `data/report/continuous_reversal_registered/v4/<source_date>/<run_sha256>/`와 v4 전용 영속 request ledger로 분리한다. 구 v3의 dated 비교 파일·`actual-*.jsonl.gz`·활성 WAL을 수정/이관하지 않는다. 기존 응답은 hash를 검증한 불변 export에서 exact import하고 동일 요청·응답 충돌은 감추지 않는다. 공통 native 장후 출력과 current pointer를 갱신하는 writer는 기존 owner lock 아래 하나만 실행한다. 비활성 비교 run이 canonical terminal이나 발행 원본을 덮어쓰지 못하도록 `evaluate_only` 출력과 publish 경로를 분리한다.

`run_sha256`는 source/publication/effective 날짜·cutoff, 실제 parent, registry/portfolio/적용 버전 census, 원천·완성 분봉 bytes, feature/root/label/입력 생산 코드와 label 계약을 묶는다. 입력 cache는 준비 함수·typed phase/input version까지, provider reuse는 정확한 요청 생성 설정/bytes까지 결속한다. 뒤늦은 분봉·source 정정은 해당 partition에 새 fingerprint를 만들며 옛 비교·response의 outcome 연결을 덮어쓰지 않는다. 파일 존재나 완료 응답 '개수'가 같다는 이유로 이전 불변 snapshot을 재사용하지 않고 정렬된 내용 digest로 선택한다. write→fsync→atomic publish 후 같은 bytes hash를 확인한다.

후보 상태는 `proposed → registered → compared → selected`로 구분한다. `selected`는 배포/PID 소비/실제 주문 성공을 의미하지 않는다. 등록 후보라도 실시간은 **발행된 해당 scope의 선택 목록만** 실행한다.

### 6.2 조합은 유한 목록으로 고정

R0에서 확정된 이전 registry의 비교 목록과 장중 실제 적용 목록을 유지한다. 아래 신규 목록을 각 적용 가능한 cell/route에 추가한다.

1. 새 8개 각각의 단독 정책.
2. 삼성 `{SA,SB}`, HPSP `{HA,HB}`의 순수 신규 조합; 나머지 group의 신규 조합은 단독과 같으므로 중복 제거.
3. R0에서 동결한 해당 scope의 incumbent + 신규 각 단독, incumbent + 해당 group 신규 전체.
4. 모든 목록의 branch 순서/동률 순서/primary 규칙을 manifest에 고정한다. 신규 batch에서 223/1,157개 powerset, 전체 종목 간 cross-product, 매일 달라지는 가설 grid를 만들지 않는다.

R0 당시 incumbent 기준의 추가 조합 정의는 최초 등록 때 동결한다. 이후 매일 새 조합을 자동 생성하지 않고 해당 등록 조합과 **그날 장중 실제 적용된 전체 버전**을 비교한다. 사용자가 다른 조합을 추가하려면 수동 정의를 새로 등록한다. 선행 catalog 내부의 기존 유한 조합을 이 등록안이 임의 축소하지 않는다.

### 6.3 실제 적용 범위에서 재계산

- 연구의 기존 baseline은 현재 구현 완료 후 정책과 다를 수 있다. §2 숫자를 신규 v3/v4 대비 개선치로 복사하지 않는다. 원 연구 접두에서 후보 단독/확인점/라벨 parity를 먼저 확인하고, 이어서 **실제 incumbent·장중 적용 버전·등록 단독·명시 조합**을 같은 누적 원천/cutoff로 비교한다.
- 비교 소유는 `symbol_group × market × price_band × route`다. 5개 고정 종목 `{005930,034020,403870,196170,036930}`은 GENERAL에서 제외한다. 종목 전체 성과를 다른 가격대 셀로 복사하지 않는다. GA는 확인 가격 `[20,000,100,000)`에만 해당한다.
- canonical 확인점으로 합집합 중복을 한 번 제거한다. 집계 WIN 수를 단순 합산하지 않는다. root/anchor가 달라도 같은 실제 확인 ask/시계이면 한 라벨이며 다른 원천 가격 충돌은 결손으로 드러낸다.
- 기계 자동 선택은 기존 승인 **누적 raw W/(W+F)** 우선이다. F는 STOP+완전 관측 TIMEOUT이고 U는 별도다. U를 0손익/실패/성공으로 바꾸지 않는다. 최소 표본·날짜·holdout·EV·기존 성공 보존율을 추가하지 않는다.
- 동률은 선행 계약대로 현행 우선, 다음 고정 순서로 결정한다. 현행 100%와 신규 100%이면 등록·비교가 성공해도 자동 교체가 없을 수 있다. 더 많은 기회 수는 함께 보고하되 이 계획으로 동률 선택 규칙을 바꾸거나 강제 초기 지정하지 않는다. '후보 가치 있음'과 '자동 선택됨'을 결과 표에서 구분한다.
- 목표 net +0.4%, soft stop -3%, cost rate 0.0023, horizon 1,800초를 유지한다. 10분 이후도 같은 유효 가격 경로/기존 완성 분봉 보조 계약으로 평가하고 미래 가격을 진입 특징에 쓰지 않는다. 정확한 item/시각 경계 결손을 건너뛰어 목표 선도달을 만들지 않는다.
- 등록/새 phase 지원 부족은 구현 결손, 동일 scope의 유효 무신호는 정상 비교 결과, 원본 부족은 source gap, 보조 호출 미완료는 비교 미완료로 각각 기록한다.

**비교 완전성:** expected catalog×적용 scope manifest의 모든 항목에 terminal과 census가 있어야 한다. 일부 root 계산 예외/중단·캐시 불일치를 `valid_empty`로 바꾸고 나머지 후보 중 최고를 선택하지 않는다. 식별 가능한 원천 결손은 해당 row/window/필요 feature branch에만 격리하고, 불완전 비교는 해당 scope를 `evaluation_incomplete`로 carry한다. HA 또는 legacy의 정상 평가까지 SB의 volume 결손으로 막지 않는다. `source_gap_no_eligible_native_item_rows`, `no_observations`, `valid_empty`, `no_resolved_sample`, `evaluated_not_selected`를 구분하며 `caa23416`의 row-exclusion/custody/원장 스트리밍 수리를 후속 코드에서도 유지한다.

선택은 원분수를 사용한다. 0승/양의 분모는 정상 0%, 분모 0은 null이다. 현행만 null이고 새 후보는 유효하면 새 후보 순위를 적용하며 `incumbent_not_comparable`을 남긴다. 모두 null이거나 일부 필수 비교가 미완료이면 검증된 호환 부모/이전 쌍을 원 의미대로 carry하고 성과를 복사하지 않는다. 비교가 완결된 뒤의 raw 승률 선택과 비교 자체의 결손을 분리한다.

신규 8개를 PRE/AFTER/KRX/NXT로 복사하지 않는다. 그 scope의 기존 정책·보조 binding·복수 운용은 보존한다. 향후 같은 후보의 다른 시장 연구는 별도 정의/근거로 등록할 수 있다. 위젯/에피소드 퇴역, owner 신규진입 제외, manual custody/veto를 패턴 등록으로 해제하지 않는다.

## 7. 코드 소유와 소비자 연결

아래 새 파일명은 구현 시 사용할 위치 제안이며 아직 생성하지 않았다. 위치 gate상 live 계산은 `src/engine/scalping`, 테스트는 `src/tests`가 소유한다. `src/engine` 루트에 새 모듈을 만들지 않는다.

| 역할 | 변경/신설 위치 | 닫아야 할 계약 |
| --- | --- | --- |
| 새 정의·manifest | `src/engine/scalping/reversal_path_catalog.py` 신설 | 기존 registry immutable 참조, 정확 8개·유한 조합, scope/개별 hash |
| 공유 path state | `src/engine/scalping/reversal_path_runtime.py` 신설 | all-valid-tick root, retest/hold, causal 특징, typed claim·동일 기회 집계 |
| 새 보조 phase | `src/engine/scalping/reversal_path_auxiliary_contract.py` 신설 | phase/fact/input/prompt/response validator·exact reuse |
| 새 family | `src/engine/scalping/continuous_reversal_policy_v4.py` 신설 | v3 호환 이관·새 schema/source 검증·primary·CAS |
| 장후 | `src/engine/scalping/continuous_reversal_path_postclose.py` 신설, 기존 장후 dispatcher 연결 | registration custody·적용 버전 census·새 root 재생·실제 보조 비교·쌍 발행 |
| Main 소비자 | 기존 비고정 policy dispatcher/native loader/AI engine/Main handlers, 신규 backend adapter | §3.3의 요청 전·응답 후·기동 전체 version matrix, v3 고정 모듈 보존·typed snapshot·주문 guard 유지 |
| 의미 감시/기동 | 기존 policy semantics·postclose handoff·strict/native validator·PREOPEN | 새로운 schema/phase/definition/registry receipt 검증·기존 세대 역사 검증 |
| 회귀 | `src/tests`의 해당 역할 테스트 확장/신설 | §9의 연구 parity·상태 경계·구버전/권한/성능 |

dispatcher/AI/monitor에서 `v1/v2/v3`, `FIRST/CONFIRMED`, `first_signal/confirmed_signals`, registry 전역 hash를 가정한 사용처를 `rg`로 전수 찾고 담당 consumer 표를 만든다. 새 schema를 알 수 없는데 legacy로 fallback하는 경로와 경보만 비활성화하는 수리를 금지한다. 정상 조건 종료를 source gap으로 알리는 경우 실제 invalidation reason과 source validity를 구분한다.

새 callback은 이미 정규화된 WS 원천을 소비하며 파일 읽기·provider·REST·추가 REG를 하지 않는다. 실제 Kiwoom request/parser/FID/REG/recovery를 변경할 필요가 발견될 때에만 AGENTS의 공식 Kiwoom reference gate를 먼저 수행한다. 이번 계획은 API 수집 확대를 요구하지 않는다.

## 8. 실행 순서·산출물·종료 기준

| 단계 | 작업 | 산출물 | 종료 기준 |
| --- | --- | --- | --- |
| R0 | 선행 P1~P6 구현 종결·P7 운영 상태 인계·실제 부모/custody 동결 | handoff manifest·delta/ownership 표 | 완료 commit/registry/소비 계약 특정, 병행 수정 없음, 자연 신호 미관측은 별도 기록 |
| R1 | 원 batch에서 8개 추출·근거 영속화·유한 조합 동결 | registration candidate/변환·source manifest | 정의 SHA 8/8 일치, 연구 재현 read-set 보호, current mutation 없음 |
| R2 | 구버전 호환 reader·새 catalog/family skeleton | migration fixture·schema/source verifier | 새 코드에서 구 family/native loader 정상, tamper 거부, 미선택 행동 parity |
| R3 | 공유 특징·4종 확인 계열 구현 | momentum/breakout/hold/retest state·typed claim | 원 확인 index·ask·feature·native 경계·라벨과 parity, HA 구 FIRST 유지 |
| R4 | 신규 5개 phase 및 원 FIRST 연결 | English ASCII fixed arm·schema·validator·exact key | 거짓 decline/5초 anchor 요구 없음, 다른 요청 응답 혼용 0 |
| R5 | 격리 누적 재생·실제 보조 비교 | 기계 단독/조합/현재 비교·AI ledger·publishable pair | 전체 eligible 회계, W/F/U/겹침/집중도 공개, 미완료 scope 정확 carry |
| R6 | dispatcher/실시간/의미 감시/장후 소비 통합 | 소비자 연결표·stage candidate·rollback 자료 | 48셀/지원 route 보존, 한 intent, strict/native/PREOPEN 계약 일치 |
| R7 | 독립적인 관점의 자기 리뷰→수정→재리뷰·대상 회귀 | review findings·수정/재검증 receipt | 검토 범위 내 미해결 구현 finding 0, 대상 pytest/compile/diff PASS |
| R8 | 기존 owner의 후속 발행·운영 인계 | 선택/미선택/쌍 carry 표·code/정책/배포 소비 receipt | 등록·비교 완료와 실제 선택/배포/자연 소비 각각 확인 |

R1은 정식 registry를 즉시 바꾸는 단계가 아니라 불변 등록 자료 준비다. 실제 등록은 R2~R4 지원과 review가 끝난 뒤 R5의 native 등록 경로에서 수행한다. R3/R4뿐 아니라 R5 producer의 partition/누락 회계/원장/재개/부분 비교·쌍 carry를 소규모 frozen fixture와 가짜 transport로 먼저 검증한다. 미해결 결함이 없고 대상 검증을 통과한 뒤 비싼 전수 재생과 실제 호출을 시작한다. 이미 검증된 과거 연구 source bytes는 읽기 재사용한다.

R5는 §5.1의 실제 primary eligible 대상에 exact AI 비교 checkpoint를 남기며, 외부 서비스 지연으로 미완료여도 해당 결과를 완결로 속이지 않는다. 미선택 branch의 provider 미실행은 미완료 호출에 합산하지 않는다. R7의 code closure와 남은 실제 응답/자연 소비 증거를 분리한다. 완료 조건은 신호가 자연 발생할 때까지 무기한 기다리거나 수익을 보장하는 조건이 아니다.

운영 실행 때는 리뷰된 불변 release에 reader를 먼저 준비하고 검증된 현행 family로 기동 가능한지 확인한 뒤 새 candidate를 parent CAS로 전환한다. 부모가 달라졌으면 해당 parent/비교를 재확인하고 pointer를 강제 덮어쓰지 않는다. 실패 시 보존한 코드·family·registry·보조 쌍으로 돌아갈 수 있어야 한다. 구현 실행 전 기존 owner에 기록된 배포·재기동 지시와 적용 시점을 그대로 확인한다. 이번 문서 작성은 그 절차를 시작하지 않는다.

정기 장후는 별도 병렬 cron을 추가하지 않고 기존 dispatcher/stage에 등록 후보 비교를 연결한다. 자동화 동작이 바뀌는 구현 change set에는 그 operating 문서와 당일 checklist를 함께 반영한다. 마지막 문서/source/release 변경 뒤 필요한 새 strict/controller/PREOPEN 준비를 생성하며 역사 receipt를 현재 준비의 증거로 바꾸지 않는다.

## 9. 대상 검증과 리뷰 기준

### 9.1 필수 회귀

| 영역 | 경계/반례 | 기대 결과 |
| --- | --- | --- |
| 정의 | 8개 원본 SHA, 뜻이 비슷한 VWAP/BUY10 후보, phase 포장 후 SHA | 정확 원본만 등록, 변환 hash 별도, 미지원 정의 명시 거부 |
| causal 특징 | future suffix 변경, 60/120초 warmup, 같은 시각 순번, qty/side 결손, 세션 anchor 복원 | 과거 신호 불변, UNKNOWN 보존, 공식 시가/0값 대체 없음 |
| momentum/breakout | false→true, unknown→true, 계속 true, current tick의 prior high 오염, DA +0.1→+0.2 도약 | 정의대로 1회 발생, 선행 반전 없어도 HB/상승지속 평가 |
| hold | 정확 1초/첫 후속 틱, 동률, 중간 한 번 하회, 늦은 수신·불연속, 확인 때 ret가 +0.05 아래인 SLOW | 원 연구와 동일 확인/탈락, 임의 추가 hold TTL 없음 |
| retest | low 재접촉, low×0.998 동률/미만, 120초 동률/초과, touch와 reclaim 같은 틱, 복수 anchor | strict/inclusive 경계 동일, 같은 틱 reclaim 금지, lineage 전부 보존 |
| source/claim | epoch/item/seq/family 전환, 중복·충돌, 재기동, 확인 후 평가 5초 초과 | 영향 pending/claim만 무효, 과거점 새 신호화 없음, 전달 지연 계측 |
| phase/AI | 하락 없는 HB, 120초 SB, 틀린 supporting fact, hash 다른 cached PASS | 맞는 phase 입력·검증, 기존 FIRST/CONFIRMED bytes 보존, 오응답 재사용 0 |
| 단일 진입 | 한 틱 다중 root/기존 FIRST 동시 성립, primary VETO, 같은/다른 틱 | 1 intent·1 운영 AI 요청, VETO 뒤 다른 branch 우회 없음 |
| scope | 5고정/GENERAL, 19,999/20,000/99,999/100,000, PRE/REGULAR/AFTER·route/item | GA 범위 정확, 고정 종목 중복 배정 0, 지원 기존 scope 소실 0 |
| 선택 | 100%/80% 성공 보존 위반인데 더 높은 raw 승률, 동률, U만 존재, old/new baseline 차이 | 보존율로 탈락 없음, 동률 현행 유지, 무표본 명시, 현재 기준으로 재계산 |
| custody/버전 | v3 로드 뒤 v4 정의 등록, 과거 날짜 등록 재사용, 원본/코드 tamper, parent 변경 | 구 family 정상, 변조 거부, 날짜 덮어쓰기 없음, CAS conflict 명시 |
| 비교/발행 | interrupted ledger, 같은 요청 여러 비교, partial AI, machine winner/aux 불일치 | 이중 호출/허위 PASS 방지, 미완료 회계, 검증된 기계·보조 쌍 carry |
| 권한 | BLOCK/RECHECK, manual/retired owner, 보유/미체결/자본·수량·hard safety | 신규 root가 기존 제출 guard를 우회하지 않음 |
| 확인점 고정 | 첫 root 확인에 quote/유형 미달, 다음 틱은 충족; false→UNKNOWN→true | 뒤의 유리한 점으로 이동/가짜 재발화 없음 |
| 가격대 이동 | GA 시작 19,990→확인 20,010 및 반대, family 중간 교체 | 선택된 root 공유 추적으로 올바른 확인점 평가, 원 가격대 정책 오적용·과거 신호 재발행 없음 |
| 재생/운영 용량 | 5초 안 ready 256 초과, 120초 pending 1,024 초과 | offline 전체 확인점 유지, live overflow 별도 계측, 표본 손실을 정상 무신호로 표시하지 않음 |
| 응답 후 권한 | provider 중 bundle 교체/TTL 만료/path break, unknown schema/backend | 신규 compose에서도 BUY 거부·fallback 없음, v1~v3 호환 유지 |
| source/입력 의미 | 하락 없는 HB, 과거 peak가 buffer 밖, 신규 signal receipt native 재생 | 합성 low/drop/reversal 사실 0, typed 원천 결속·감시 정상 해석 |
| 전수 비교 회계 | 입력 하나가 원장 준비 전에 누락, 5 arm 중 하나 미예약, 전 arm VETO, U만 존재 | expected manifest로 누락 탐지, completed_no_pass/U/미완료 분리, 허위 winner 없음 |
| cache/불변성 | 같은 응답 수·다른 내용, late bar, v3/v4 동일 날짜 run, 중단 후 재개 | content hash별 새 snapshot, 구 family/read-set/원장 불변, 새 run만 발행 |

### 9.2 재생과 성능

원 연구의 `typed-result`/FIRST 결과에서 8개 실제 확인점 집합을 추출해 native 구현의 `(source stream,day,symbol,item,epoch,sequence)`·확인 ask·필터 특징·W/F/U를 대조한다. 기준 정책/8개/명시 합집합을 각각 비교하고 불일치가 있으면 분모부터 원인을 분리한다. 같은 틱 count만 일치하는 것을 parity 완료로 삼지 않는다. 연구 helper의 float 경계 표현과 native 가격/시간 표현 차이도 경계 fixture로 닫는다.

그다음 R0의 실제 적용 버전과 새 조합을 누적 source에서 재생한다. 기존 native label/bar 보조 규약을 사용하며 실현 수익으로 표시하지 않는다. 더 최신 데이터가 추가되면 원 연구 parity source와 최신 비교 source 두 manifest를 분리한다. 새 날짜를 기다려야만 등록 가능하다는 조건은 만들지 않는다.

성능은 같은 frozen tick 집합으로 선행 완료 코드와 새 코드를 비교한다. callback 처리 p50/p95/p99/max, backlog/ready age, 동시 pending, 메모리 최고치와 5초 claim miss를 기록한다. 공유 window/root로 중복 계산을 없애고 source callback에는 I/O가 없음을 검증한다. 기존 source/queue 한도는 임의 완화하지 않으며 overload는 보이게 기록한다. 이를 피하려고 연구 표본/등록 후보를 조용히 잘라내지 않는다. 실제 WS 지연 여부는 배포 후 자연 지연 계측으로 별도 확인한다.

## 10. 계획 리뷰·상태와 다음 인계

| 계획 리뷰에서 확인한 위험 | 반영한 보완 |
| --- | --- |
| registry append가 구 family 전역 hash 검증을 무효화 | §3 별도 successor schema·구버전 immutable reader·선행 bytes 보존 |
| FIRST가 없는 지속 상승과 120초 retest를 기존 5초 CONFIRMED로 표현 | §4 all-valid-tick/root FSM, §5 새 phase·실제 사실 validator |
| 원 FIRST DD와 실제 확인 DD, anchor와 확인점 필터 혼용 | §2/§4 의미·계산·시점을 분리하고 원 정의 SHA 고정 |
| 신규 8개 성과를 더하거나 오래된 baseline을 현재 성과로 제시 | §2 추가/전체 구분, §6 exact union·실제 incumbent 재생 |
| 전 시장 구현을 새 정규장 연구의 전 시장 승격으로 오인 | SOR REGULAR 초기 범위와 기존 PRE/AFTER/route 보존 명시 |
| 1,157개 전부/모든 조합을 등록하여 상태·호출 폭증 | 정확 8개·공유 root·유한 조합·전수 입력 checkpoint |
| 삼성 오늘 U를 새 날짜 대기/등록 탈락으로 사용 | 누적 근거 등록, U 공개, 새 성과 문턱 미추가 |
| 100% 동률인데 추가 패턴이 자동으로 선택될 것으로 기대 | §6 현행 tie 유지와 등록/선택/초기 지정 구분 |
| 다른 세션과 파일·registry·작업 owner 충돌 | R0 완료 인계, 기존 owner 후행 계획, 계획 작성만 수행 |
| P7의 미래 자연 관측까지 기다려야 등록할 수 있다는 해석 | P1~P6 구현 종결·소유 인계로 착수하고 P7 미관측을 별도 인계 |

원 계획 작성 시점의 완료 범위는 8개 식별자·수치/경계·생산자/소비자 조사와 상세 계획 작성·문서 검증이었다. 당시 R0~R8 구현/등록 실행은 아직 시작하지 않았다. 검토 범위 밖의 운영 결함이 없다는 보장은 하지 않는다.

실행 인계 결과에는 후보별 `registered`, native 기계 W/F/U·현재 대비 겹침/추가, 실제 보조 비교 상태, `machine_winner`, `publishable_pair`, `selected`, deployment/PID·자연 판정 상태를 나란히 보고한다. 삼성 두 후보가 선택되지 않더라도 정의 결손·소비 결함·보조 미완료·동률 유지·누적 열위를 각각 실제 근거와 함께 설명할 수 있어야 한다.

문서 closure는 링크·정확 8개 원 정의/수치·단일 OPEN owner·권한 경계·`git diff --check`·print-only backlog parser로 확인한다. 문서 작업에는 거래 pytest, 정책 재생성, provider 호출을 실행하지 않는다.

10/7 문서 검증: 원 정의 digest 8/8·보고 수치 8/8 일치, 본 계획 로컬 링크 11개 유효, print-only parser 29개 작업 중 해당 owner 정확 1개, diff 공백 검사 PASS. 재리뷰에서 위 P7 착수 모호함을 보완했다. 실행 검증 결과는 R7의 별도 receipt로 기록한다.

## 11. 후속 계획 재리뷰 보완 — 10/7

아래는 `caa23416` 코드와 연구 확인점 생산 순서를 다시 대조한 **계획 보완**이다. 현재 구현 결함을 수정/배포했다는 기록이 아니다. 위 §10의 11개 링크 수는 초안 검증 이력이다.

| ID | 확인한 누락/충돌 | 계획 보완·종료 검증 |
| --- | --- | --- |
| PR1 | 최신 원천 격리·원장 성능 수리가 인계 기준에 빠짐 | §1/§6 최신 commit과 수리 계약 기록, R0 최종 commit 재동결 |
| PR2 | v4가 v1 fallback으로 흐르고 provider 후 claim 재검사 누락 가능 | §3.3 전체 version/backend matrix, 요청 중 family/TTL 변경 회귀 |
| PR3 | 구 runtime 동결과 backend 확장 지시가 충돌 | 비고정 dispatcher·신규 adapter 소유, 구 bytes·native loader parity |
| PR4 | 반전 없는 지속형에 old snapshot/`price_reversal_confirmed` 요구 | §4/§5 typed prefix projector·signal kind·감시 native verifier |
| PR5 | 첫 확인의 quote/filter 실패를 늦은 확인으로 바꿀 위험 | §4.2 연구의 root→첫 확인→필터 순서, UNKNOWN 인접 관측 규칙 |
| PR6 | 가격대 이동 전 root 상태를 추적하지 못해 GA 누락 | §4.5 선택된 root를 가격대 간 공유, 확인 셀에서 최종 적용 |
| PR7 | 실시간 5초/ready/pending 용량을 과거 표본 상한으로 적용 | §4.5 완전 offline 배출·live 용량 계측 분리 |
| PR8 | '전수 AI'의 대상·U·전 VETO/무 primary 상태가 불명확 | §5.1 실제 primary eligible 정의·raw PASS 분모·명시 carry 사유 |
| PR9 | 원장에 없는 입력이 비교 완료 집계에서 사라질 수 있음 | expected owner/arm manifest와 준비 전후 회계, 누락 회귀 |
| PR10 | v3 dated 파일·WAL 덮어쓰기와 개수 기반 cache 재사용 위험 | §6.1 v4 namespace·writer lock·단계별 fingerprint·내용 digest |
| PR11 | 일부 기계 후보 미완료인데 나머지를 전수 winner로 발표 가능 | §6.3 전체 expected terminal·branch별 결손 격리·null/0% 구분 |
| PR12 | 비싼 실행 전 producer/원장 검증 시점 불명확 | R5 소규모 fixture/가짜 transport gate 이후 실제 전수 실행 |

8개 후보 정의·수치·승률/동률 기준은 그대로다. 구현 준비 완료 판단은 R0의 인계가 소유하며, 본 리뷰로 추가 자연 체결/수익/새 날짜 조건을 부과하지 않는다.

재리뷰 문서 검증: 8개 원 정의 digest/초기 scope 재대조 PASS, 로컬 링크 15개와 상위 계획·체크리스트 연결 PASS, print-only parser 29개 작업/해당 current owner 1개, tracked diff 및 신규 문서 공백 검사 PASS. 위 PR1~PR12의 계획 보완을 재검토했으며 문서 검토 범위 내 미해결 finding은 없다. 런타임 소스·정책은 변경하지 않았고 문서 작업에 해당하지 않는 거래 pytest·전수 재생·provider·배포·재기동은 실행하지 않았다.


## 12. 승인된 구현 결과

후속 구현 승인을 실행한 결과는 [구현·반복 리뷰 기록](../audits/main-additional-eight-pattern-implementation-review-2026-10-07.md)이 소유한다. v3 고정 모듈 bytes를 유지하고 v4 catalog/root/typed AI/native/장후를 기존 dispatcher에 연결했다. 원 연구의 8개 정의 SHA와 확인점·가격·특징·라벨 parity는 8/8 통과했고 대상 17개 suite 865개가 통과했다. 입력 생성 누락은 population 기반 expected 집합으로 ledger 준비 전에 검사한다.

누적 raw 승률 비교에서 새 8개는 자동 선택되지 않았다. 정의 등록·실행 지원·비교 완료와 실제 선택을 구분하며 동률 규칙을 변경하지 않는다. 실제 primary AI 비교는 전체 eligible 원장에 남기고 미완료 scope는 검증된 기계·보조 쌍을 carry한다. immutable 배포/기동/PID 및 자연 감시 결과는 위 기록의 운영 인계로 확인한다. 후속 독립 탐지 계획은 이번 구현에 추가 적용하지 않았다.
