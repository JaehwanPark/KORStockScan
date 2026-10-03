# 삼성전자·그 외 종목의 기계/보조 정책 연구 재정리 — 2026-10-03

**현재 실행 owner:** [승패 보완·승인된 통합 배포·기동 준비 검증](postclose-outcome-readiness-closure-plan-2026-10-03.md). 최신 사용자 지시로 아래 과거 기록의 배포 대기를 해제했다. 연구 분리와 실제 운영 정책 분리 적용은 별도로 검증한다.

**최신 후속 실행:** [실제 생성기 목적 이행·전체 장후 보완계획](postclose-policy-winrate-objective-migration-plan-2026-10-03.md), [리뷰·재생성 결과](../audits/postclose-policy-winrate-objective-migration-review-2026-10-03.md). 기계·보조100%/80% 보존 제약을 새 후보에서 제거했다. 중간28.73bp 관측 후보는 발견됐으나 native 계보 없는 trace 집계 결함을 보완한 최종 정식 선정은0이다. 삼성 후보의 exact 실행 원천 결손과 그 외17개 미평가 변경을 확인했고 배포 대기를 유지한다.

## 1. 이번 요청의 결정

| 구분 | 결정 | 완료 산출물/다음 실행 |
|---|---|---|
| 삼성전자 기계·보조판정 | 전용 연구를 실행하고 구현계획을 확정했다. | S0~S5 완료. 30조합에서2시도 회수, 정식 gate 미통과. [운영 구현 설계](samsung-fixed-watch-machine-auxiliary-implementation-plan-2026-10-03.md) 확정, live 정책은 보류다. |
| 삼성전자 이외 기계판정 | 현재 확인한 후보에서는 진입 규칙 변경을 뒷받침할 성과가 없다. 운영 정책 개편 계획은 보류한다. | native 분모·기존204개 후보의 종목별 회수·남은 guard를 확인했다. 원천/판정 일치 검증과 기존 결함 보완 검증은 유지한다. |
| 삼성전자 이외 보조판정 | 공통 원천 생산자·장후 소비자 개선을 구현했다. | A0~A5 코드·격리 검증 완료. 비용 scope 연결 결함 수정, 15기회/12조합 행동 변화0. |

최초 재정리 뒤 사용자의 `계획을 실행하라` 지시로 S0~S5 연구와 A0~A5 구현·리뷰·격리 재생성을 실행했다. [실행 리뷰](../audits/samsung-auxiliary-scope-execution-review-2026-10-03.md)에 결과를 기록했다. 이전 작업본과 배포 대기를 유지하며 provider/브로커 호출·새 원천 수집·commit·배포·재기동·운영 정책 활성화는 하지 않았다. 공통 source 수리는 양쪽에 적용하되 학습·선정 결과는 분리했다.

## 2. 직접 재확인한 분모

근거: `tmp/samsung-nonsamsung-policy-scope-replan-20261003/scope-census.json`. 기존 native snapshot, 후보204개의 evidence, 보조 retained projection, 이전4개 보조 위험 규칙을 사용했다. 새 가설을 후단 결과에 맞춰 만들지 않았다.

| 자료 | 삼성전자 | 삼성전자 이외 |
|---|---:|---:|
| 기계 native 시도/기회 | 35/6 | 64/63 |
| 기계9/29 시도/기회 | 4/4 | 47/46 |
| 기계9/30 시도/기회 | 12/1 | 8/8 |
| 기계10/2 시도/기회 | 19/1 | 9/9 |
| 기존 보조 AI KRX PASS 연구 응답 | 9 | 34 |
| 보조 AI 학습/후단 응답 | 8/1 | 26/8 |
| 보조 AI exact pre-AI 연결 | 2 | 12 |

삼성전자 fixed watch는9/30·10/2의31시도/2기회다. 9/29의4시도는 다른 origin 비교군으로 보존한다. 기계 원천의35행과 AI 응답9행은 서로 다른 적격성 분모이므로 날짜/종목만으로 동일 의사결정이라고 join하지 않는다. 반복 관측을 독립 기회로 계산하지 않는다.

후속 전수 검사에서 기존 PASS 집합 밖의 삼성전자 유효 CAUTION1행도 확인했다. 이번 유효 KRX 원응답은 삼성전자10·그 외34이며, fixed-watch로 exact 연결된 것은 PASS2·CAUTION1이다. 새 기계 ENTER2시도에 대응하는 exact AI 응답은0이다.

## 3. 삼성전자 전용 기계·보조판정 연구 및 구현계획 확정 절차

### S0. 대상·원천 고정

- 우선 `005930 + MAIN_FIXED_WATCH + KRX|KRX_REGULAR`를 명시적 연구 대상으로 한다. 삼성전자 다른 origin/세션은 별도 비교군이며 성과를 합산하지 않는다.
- 기존 observation/완료봉/응답/plan/stop/cost/terminal 자료를 native attempt·admission·generation·정책·route·시점·hash로 연결한다. 확보되지 않은 당시 정보는 누락으로 보존한다. 수집 주기나 API/provider 호출을 늘리지 않는다.
- 전체 삼성전자9개 AI 응답 중 fixed-watch 대상에 정확히 연결되는 수와, 새 기계 후보가 회수한2시도에 해당하는 응답 유무를 별도로 계산한다. 같은 날의 PASS를 새 진입 시도에 대입하지 않는다.

### S1. 상시 감시의 반복 관측 구조 확인

- 당시 기록에서 setup 출현→확인 대기→해소/무효화→다음 setup 전이를 찾는다. 모든 구간은 native admission에 역연결한다.
- 날짜·세션·실제 종료/재시작·원천 단절을 보존하고, 미래 상승 여부를 기준으로 episode 경계를 정하지 않는다. 사전 조건이 없는 임의 시간 분할로 지원수를 늘리지 않는다.
- 연구용 episode와 현재 승격용 native 기회 ID를 별도로 저장한다. 현재2개 native 기회를 수십 개의 승격 기회로 교체하지 않는다. 상관된 반복 자료를 같은 fold에 유지한다.
- 보유 원천에서 episode를 식별할 수 없으면 기존 admission 단위로 평가하고 한계를 보고한다.

### S2. 삼성전자 기계 후보 연구

- 대조군은 현재 Main parent다. 첫 가설은 기존 연구의 `DEPTH_SUPPORTED + 현재 유효한 양의 매수 흐름/가격 반응`으로 soft setup 확인을 대체하는 후보다.
- 범위를 삼성전자에 명시하고, 사전에 고정한 phase/시간대/반복 확인 조건만 비교한다. 조건 생성은 학습자료로 한정한다. 종목 자체를 제외하는 검증 대신 날짜·시간대·setup 구간에서 반복성과 민감도를 본다.
- `micro_continuation_unconfirmed`/`no_supported_setup` 대체는 새 의미 규칙이다. 원본 fact를 수정하지 않고 대체 이유를 기록한다. hard/source/liquidity/local-breakout/VWAP 및 주문·계좌·보유 owner를 보존한다.
- 비용 결합 목표-first, 기존 성공 보존, 회수 지원수, 전체 경로 순 EV·최악 손실을 함께 보고한다. 10/2는 이미 사용한 날짜이므로 독립 holdout이라고 부르지 않는다.
- 후보0도 정상 연구 결과다. 현재 정식 gate 기준을 낮추거나 schema를 먼저 등록해 통과시키지 않는다.

### S3. 삼성전자 보조판정 연구

- 실제 존재하는 응답의 같은 입력·prompt·parent·시점에서 deterministic soft 정책을 비교한다. 기존9개 응답은 모두 PASS이며 전용 scope에 포함되는지는 S0에서 확정한다.
- 위험 인용의 중복/관련성/materiality, CAUTION 후 같은 opportunity의 해소·종료, 성공 진입 제외를 분석한다. 기계 후보의 새 ENTER에 exact 응답이 없으면 해당 기계+보조 조합은 `auxiliary_response_not_observed_for_candidate`로 남긴다.
- 기계 성과와 보조 AI 성과, 두 판단을 연결한 성과를 각각 계산한다. 기계2건 목표-first를 보조 판단 개선의 증거로 사용하지 않는다.
- 새 prompt는 정적 설계·schema 검토까지만 가능하다. retained 답변을 새 prompt 응답으로 재사용하지 않으며 provider 비교 실험은 실행하지 않는다.

### S4. 연구 결과로 구현계획 확정

다음 변경 후보는 연구로 필요성이 확인됐을 때 상세 설계한다. 현재 구현된 기능이라고 보지 않는다.

| 구성요소 | 변경 후보 및 검증 |
|---|---|
| 정책 선택 | `entry_strategy_policy`/`mechanistic_entry_runtime_policy`에 symbol·watch origin·exact scope 선택 계약을 설계한다. 현재 수치 feature selector에 종목 가격을 대용 키로 넣지 않는다. |
| parent/child 결속 | parent SHA·대상·유효일·우선순위·미지원 fallback·rollback을 명시한다. 대상 밖의 행동은 parent와 동일해야 한다. |
| 기계 판정 | `entry_setup_evidence`에 검증된 새 확인 근거만 등록하는 방안을 검토한다. hard guard와 원본 fact를 보존한다. |
| 보조판정 | 삼성전자 조건이 검증됐을 때만 별도 soft profile/prompt identity를 둔다. 개선이 입증되지 않으면 공통 보조 정책을 상속하는 결론도 허용한다. |
| 장후 학습/발행 | 삼성전자와 나머지 종목의 source/split/selection manifest를 분리한다. 기회 계약·publisher·loader가 동일 정책 hash와 분모를 검증해야 한다. |
| 실행 소유권 | 기존 Main order/quantity/holding/exit를 유지한다. 별도 삼성전자 주문 프로세스나 retired gateway를 만들지 않는다. |

### S5. 완료 판단

- 연구 결과·후보 JSON·변경 시도·결손/부작용·민감도와 구현 필요/불필요 결론을 만든다.
- 구현계획에는 수정 producer/consumer, schema 변경, 원천 마이그레이션, 회귀/격리 재생성, rollback을 포함한다. 적용 조건을 채우지 못하면 연구/계획 단계에서 종료한다.
- 연구 코드 검증과 실제 정책 선정·PREOPEN·PID 소비·실현 수익은 별도다. 배포는 별도 지시까지 대기한다.

## 4. 삼성전자 이외 기계판정 개선계획 필요성

**현재 결정: 진입 규칙·임계값 변경 계획은 보류. 원천 및 판정 일치 검증은 유지.**

- 삼성전자 제외64시도/63기회, 학습55시도/54기회·후단9시도/9기회다. parent action은 ENTER15, RECHECK43, BLOCK6이다.
- 기존204개 후보의 train/holdout 회수 opportunity ID를 이 집합과 교차 검사했다. 삼성전자 이외를 회수하는 후보는0, 최대 회수 기회도 양쪽0이다. 삼성전자에서 찾은 가설을 공통 정책 변경 근거로 확장하지 않는다.
- 이 결과의 범위는 이번 후보군이다. 삼성전자 이외에 상승 패턴이 전혀 없거나 어떤 개선도 불가능하다는 결론은 아니다.
- 유지할 점검: 미진입 표시 사유와 실제 미해결 risk fact의 일치, 당시 숫자·source freshness·원천 전달 누락, 현재 작업본의 native/cache 수리 회귀. 요약 사유가 포괄적이라는 이유만으로 실제 safety 판단을 오류라고 단정하지 않는다.
- 수정 필요성의 종료 기준은 **특정 producer/consumer 결함 또는 보존된 guard 안에서의 재현 가능한 행동 개선**이다. 결함이면 해당 경계만 수정하고, 정책 가설이면 학습 고정→후단 검증을 수행한다. 확인되지 않으면 정책 변경 없음으로 종료한다.
- 별도 임계값 완화·liquidity/돌파 재확인 해제 과제는 만들지 않는다. 기존10/6 `DirectFamilySourceRepairMainMechanisticEntry`의 자연 수용 owner를 유지한다.

## 5. 삼성전자 이외 보조판정 개선계획 보완

- 기존 계획의 정책 비교 범위를 `stock_code != 005930`으로 명시한다. 공통 producer는 삼성전자 원천도 보존하되 결과를 따로 표시한다.
- 유효 KRX 응답34개, 학습26·후단8, exact pre-AI 연결12를 기준선으로 사용한다. 전체43/14 결과를 삼성전자 제외 성과로 인용하지 않는다.
- 이전4개 규칙을 이 분모로 다시 계산했다. 10/2 fold의 flow/가격 조건은 학습9·후단0 변경, spread/tick 조건은 학습6·후단0 변경이다. 3/5분 성공을 각각1개씩 제외했으며 개선 후보0이다. 과거 flow 악화/spread 확대 조건은 변경0이다.
- 방향은 원천 손실·정합성 개선, 단계별 분모, 응답의 위험 근거 관련성·materiality, CAUTION의 실제 후속 경로다. 이미 실패한 부호/count 규칙을 그대로 강화하지 않는다.
- 비용/stop/운영 plan 결손과 정상 AI 응답·AI-stage 결과를 분리한다. 기존 A0~A5의 상세 순서와 테스트는 [보조 AI 계획](auxiliary-source-producer-postclose-consumer-improvement-plan-2026-10-03.md)을 따른다.

## 6. 소유자·검증·현재 상태

- 이번 재정리: checklist `SamsungPolicyScopeReplan1003` 완료. source hash·대상 교집합/합계·규칙 재집계, 문서 링크/owner/권한·diff·print-only parser를 검증한다.
- 삼성전자 연구·구현계획 확정: `SamsungDedicatedMachineAuxiliaryResearch1003` 완료. 정식 gate·새 ENTER의 보조 응답 결손은 미충족으로 남긴다.
- 삼성전자 제외 보조 producer/consumer 구현·검증: `NonSamsungAuxiliarySourceConsumerImplementation1003` 완료. live 적용은 별도다.
- 기존10/6 자연 수용/PREOPEN 항목을 중복 등록하거나 완료로 바꾸지 않는다.
- 후속 실행에서 scalping source/research 코드와 영향 테스트를 변경했다. 표적 회귀·격리 cold/warm 재생성·문서 parser를 검증했다. 전체 매매 테스트·canonical 장후 재생성·외부 동기화는 실행하지 않았다.

## 7. 후속 심화 연구의 변경된 범위

사용자의 추가 연구 지시로 [연속 관측·집단 분리 연구](partitioned-continuous-pattern-research-plan-2026-10-03.md)를 수행한다. 앞 절의 보류는 당시 후보군에 대한 결론이며 이번 연구의 탐색 중단 조건이 아니다.

- 원본 신원 복원: 삼성전자 전체519관측 중 fixed-watch206행(9/30 46, 10/2 160). 기존31행은 native 비용경로 조건을 통과한 부분집합이다. 9/29의313행은 watch_origin 미기록 비교군으로 구분한다.
- 이전 fixed-watch31행에서60초 내 인접 쌍은0이었다. 따라서 해당 반복2회 후보의 변화0은 `not_evaluable_no_adjacent_exposure`로 정정한다. 전체206행의 간격을 다시 확인한다.
- 그 외 종목은 삼성전자를 제외한6,550관측/702종목으로 조건 생성 이전부터 분리한다. 학습·선택·후단·종목제외 민감도에 삼성전자 데이터가 들어가지 않는다.
- 연구 정책 후보, 실제 기계 guard 안의 행동 변화, auxiliary 연결, 정식 발행·PID·실현수익은 각각 판단한다. 정책 배포 대기와 기존 자연 수용 owner는 유지한다.
- 후속 연구 완료: [집단 분리 심화 리뷰](../audits/partitioned-continuous-pattern-research-review-2026-10-03.md). fixed-watch206행·그 외702종목의 분리 탐색, 시간순·개별 horizon·후보 유지·유형 조합·실제 간격 반복 검증을 수행했다. 양의 후단 성과가 이어지는 신규 정책 후보는 확인되지 않았다. 기존 ENTER 성공 보존을 해치는 유형 필터는 적용하지 않는다.

## 8. 전체 판정 재생과 승률 우선 후속 기준

사용자 후속 지시로 기계·보조 모두 **기존 정책보다 높은 승률 우선**으로 정정했다. 기존 성공100% 보존을 후보 탈락 조건으로 두지 않는다. §7 마지막 문장의 성공 보존에 의한 적용 보류는 당시 기준이며 현재 연구 선정 규칙이 아니다. 성공 제외량·회피 실패량·절대/paired 순손익·미평가 변경은 별도 지표로 남긴다.

- [후속1·2·3번 실행계획](main-machine-decision-cohort-target-first-research-plan-2026-10-03.md)과 [재검증 리뷰](../audits/main-machine-decision-cohort-target-first-research-review-2026-10-03.md): 전체7,069행을 같은 parent로 재생하고 삼성전자/그 외를 실제 남은 guard별로 분리했다.
- 삼성전자 fixed-watch 후보는206행에서 목표-first2·미도달1을 추가했다. 같은 native의 기존 ENTER 이전만 적용하는 후속 시간 가설은 목표-first2를 유지했다. 이는 사후 탐색이며 주문·보유/종료 증거나 독립 후단 검증을 대신하지 않는다.
- 그 외 기계: 승률 우선 관측 필터는10/2에서73.53→86.36%를 보였다. 성공3건도 제외하지만 실패3건을 줄였다. native 선정 후보의 후단 악화, source/censoring, 절대 순경로 평균 음수는 함께 보고하며 운영 정책으로 발행하지 않았다.
- 보조 연구: 성공100% 보존 조건을 제거해 삼성전자9·그 외34의 보유 KRX 응답을 재계산했다. 학습 승률 개선은 후단에서 유지되지 않았다. 원천/생산자 통합을 추가 실행하지 않았으며 [보조 개선계획 A6](auxiliary-source-producer-postclose-consumer-improvement-plan-2026-10-03.md#a6-승률-우선-정책-선정-계약-이행--사용자-후속-기준)에 운영 소비자 목적 이행 대상을 명시했다.
