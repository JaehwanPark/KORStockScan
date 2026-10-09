# Main 보조판정 프롬프트 연구·장중 적용 계획 — 2026-10-08

## 1. 목적과 이번 승인

기계가 독립 탐지한 유효 진입 기회에서 **실패를 PASS시키는 오판과 승리를 불필요하게 차단하는 오판을 줄인다.** 현행 보조판정과 연구 후보를 같은 확인점에서 실제 호출해 비교하고, 누적 PASS 승률이 개선된 적용 범위만 장중 교체한다. 기계 목록의 초기 등록이나 추가 8개 패턴을 다시 선발하는 연구가 아니다.

- 사용자 요청: 보조 프롬프트 연구를 별도 세션으로 분기하고 추가 연구 호출을 허용하며, 효과 확인 정책을 장중 적용할 예정이므로 연구계획을 수립한다.
- 추가 예산 확정: 사용자 답변 **“추가 200회부터 시작”**. 이번 연구 전체의 신규 provider attempt 200회이며 후보별·원천일별·프로세스별 200회가 아니다. 기존 장후 100회와 구분되는 일회성 추가 연구 예산이다.
- 이번 산출 범위는 계획 작성·리뷰다. 실제 연구 호출, 예산 설정 변경, 코드 구현, 정책 발행, 배포·재기동은 이 문서 작성으로 실행하지 않는다. 추가 연구 호출 승인은 후속 실행에 보존한다.
- 실행 owner는 [오늘 체크리스트](../checklists/2026-10-08-stage2-todo-checklist.md)의 `DirectFamilySourceRepairMainMechanisticEntry` 하나를 사용한다. 분기 연구는 이 owner의 하위 작업이며 새 OPEN을 중복 등록하지 않는다. 현재 봉인된 체크리스트 바이트를 계획 작성 때문에 변경하지 않는다.

의사결정은 오늘 체크리스트와 사용자 지정의 비용 후 이진 승패·누적 승률 계약을 따른다. Rebase의 과거 일반 EV/holdout/최소표본 규칙을 이 연구의 추가 채택 조건으로 가져오지 않는다. 원천·응답·부모 동일성 검사는 성과 문턱이 아니라 비교가 성립하는 조건이다.

## 2. 확인한 출발점과 보완할 구현

다음 수치는 저장된 **08:44 배포 검토 및 당시 비교**의 증거다. 지금의 PID·정책 소비 상태를 대신하지 않으며 연구 착수 시 최신 부모를 다시 확인한다. 문서 작성 중 다른 세션의 scalping 코드 변경도 관찰되어 이 분기에서는 해당 파일을 수정하지 않는다.

| 확인 사항 | 근거와 의미 | 연구 계획에 반영 |
| --- | --- | --- |
| 저장 응답 8쌍, 모두 WIN | [기존 응답 비교](../../data/report/auxiliary-paired-intraday/2026-10-08/existing-response-comparison.json): 두산 3·알테오젠 2·일반 비삼성 2건은 양쪽 모두 비PASS, HPSP 1건은 양쪽 PASS | 7건을 과잉 차단 개발 사례로 사용. 실패 표본이 없어 실패 차단 성능이나 전체 누적 승률을 입증한 자료로 쓰지 않음 |
| 새 문구 후보는 아직 효과 미확인 | [당시 배포 검토](../../data/report/auxiliary-paired-intraday/2026-10-08/deployment.json): 후보 `dd44e565c10205a806554abe0b44051d22f6e4422e1176cea07d565b726833f0`, 신규 호출 0·적용 없음 | `risk_fact_bindings`를 위험의 존재 자체로 오해하는 문제를 첫 가설로 검증 |
| 원천일 10/7 기존 사용량 15,228, 장후 한도 100 | 같은 배포 검토. 현재 튜닝 호출기는 `LIMIT=100` 및 원천일 예산을 검사 | 과거 사용량을 초기화하지 않고 별도 승인된 200회 연구 예산을 구현하여 연결 |
| registry·쌍 비교·장중 보조 overlay 구현 존재 | [기존 구현 검토](../audits/main-auxiliary-paired-tuning-intraday-implementation-review-2026-10-08.md), 아래 코드 연결표 | 기존 공유 원장과 장중 교체 경로 재사용. 분기별 설정/평가 식별은 추가 보완 필요 |
| 실행 cwd에 따른 source 경로 오류가 별도 계획에 존재 | [PRE/AFTER 보완 계획 §2.1](main-pre-after-pattern-registration-and-status-consistency-remediation-plan-2026-10-08.md#21-p0--실제-기계판정-차단의-경로-계약-보완): 당시 기록한 `data/...` 7건은 root에서 SHA 일치, release/src 기준에서는 없음 | PA0/PA13 복구의 최신 완료 증거를 적용 전에 확인. source anchor가 검증된 오프라인 연구는 병행 가능 |

현재 공통 쌍 8건에는 삼성·주성의 완료 쌍이 없다. 이는 해당 소규모 비교의 결손이며 전체 누적 원천에 해당 종목 표본이 없다는 뜻은 아니다.

| 코드 owner | 현재 동작 | 이번 연구 실행 전에 필요한 차이 |
| --- | --- | --- |
| [registry](../../src/engine/scalping/reversal_auxiliary_registry.py) | English ASCII 불변 문구·projector/schema/validator/model binding | 개발 사례·후보 계보를 고정. 과거 후보 정의 덮어쓰기 금지 |
| [tuning](../../src/engine/scalping/reversal_auxiliary_tuning.py) | 공통 쌍·누적 혼동행렬, 전역 `tuning.json` 및 원천일 `latest-campaign.json` | 별도 research config/campaign, 명시 campaign hash로 prepare/calls/evaluate, 추가 예산 소유자 연결 |
| [shared store](../../src/engine/ai/offline_comparison_store.py) | 단일 DB·pack·exact 요청 재사용·durable 예약. 여러 budget key에도 같은 `call_limit` 적용 | 장후 예산과 추가 승인 예산의 명시적 과금 경로 분리. 세션 이름만 바꾼 quota 우회는 허용하지 않음 |
| [intraday publisher/reader](../../src/engine/scalping/reversal_auxiliary_intraday.py) | 부모 CAS·scope별 개선·overlay. 발행 재평가는 날짜의 latest campaign을 다시 읽음 | 선택한 연구 campaign/evaluation 자체를 재검증. 다른 세션의 latest 변경에 따라 평가 대상이 바뀌지 않도록 수정 |
| [typed 입력](../../src/engine/scalping/reversal_operating_auxiliary.py) / [실제 전송](../../src/engine/ai_engine_openai.py) | 복수 signal의 공통 기회 판정, 등록 문구 전송 경로 | 현행의 최종 wire 입력·system 문구·schema·모델 설정과 연구 대조군의 일치 검증 |

위 차이는 계획 단계에서 확인한 실행 선행 구현 요건이다. 코드가 이미 완료됐다고 표시하지 않는다. 실제 착수 시 다른 세션이 먼저 해결한 부분은 재사용한다.

## 3. 연구 원천·정답·분류

### 3.1 모집단과 비교 단위

현행 기계 운용 manifest의 **전체 source-valid 독립 패턴 확인점**을 출발점으로 한다. 과거 AI 호출점·실제 제출점·기존 PASS 지점만 추출하지 않는다. 기계가 유효하게 탐지하지 않은 BLOCK을 보조 AI가 ENTER로 올리는 경로도 만들지 않는다. 같은 기회에 여러 패턴이 맞으면 typed union 한 개와 공통 보조판정 한 개를 사용한다.

현재 승인된 누적 normalized partition manifest를 재사용하고 실제 포함 원천일의 최솟값·최댓값, 종목/세션/route별 census와 제외 이유를 먼저 기록한다. `2026-06-05T00:00:00+09:00` 이전 자료와 archive-only 자료를 복원해 모집단을 늘리지 않는다. 해당 manifest의 더 좁은 원천 적격 경계도 유지하며 원본 파일이 없는데 과거 보고 수치만 있는 구간을 새 평가점으로 만들지 않는다.

각 확인점에는 canonical opportunity key, 원천일, 관측 시각/시퀀스, symbol, market/route/source item, 기계 정의·manifest hash, 확인 ask, 입력 object/hash, outcome source/hash를 연결한다. 동일 확인점은 한 번만 집계하고, 별도 연구 이름이나 다중 패턴 수만큼 증식시키지 않는다.

### 3.2 승패 계약

[기존 라벨 함수](../../src/engine/scalping/continuous_reversal.py)의 실제 확인 ask·비용률 `0.0023`·1800초·비용 후 목표 `+0.4%`·soft stop `−3%`를 유지한다. 가격 `p`에 대한 비용 후 수익률은 기존 식 `p / entry_ask × (1 − 0.0023) − 1`이다. 비용을 한 번만 반영한다.

- `WIN`: soft stop 선도달 없이 진입 후 30분 이내 목표 도달.
- `FAIL_STOP`: 목표보다 soft stop에 먼저 도달.
- `FAIL_TIMEOUT`: 유효한 30분 경로가 완성됐지만 목표 미도달.
- `U`: 필수 ask·순서·경로 결손, 30분 관측 미완료, 봉 내 목표/손절 선후 불명 등. 실패나 정상 차단으로 바꾸지 않는다. 유효한 목표/손절 선도달이 이미 확인되면 30분 전체 경과를 추가로 기다리지 않는다.

30분 이후의 도달은 별도 후행 분석이며 WIN으로 승격하지 않는다. 기존 라벨과 다른 결과가 나오면 비용/경계/원천을 먼저 대조하고 원 라벨 partition을 덮지 않는다. 정정 partition의 기여를 교체하여 중복 집계하지 않는다.

복원 가능한 필수 항목은 기존 검증 원천·저장 응답으로 먼저 보완한다. 외부 원천을 사용하는 후속 실행에서는 정확 종목·venue·시각/단위·원본 provenance를 검증한다. 봉 자료로 tick 순서·호가·매수세를 추정해 넣지 않는다. 보완 불가 row는 이유와 함께 제외하고 나머지 연구를 진행한다.

### 3.3 유형과 적용 범위

| 집계 축 | 연구·보고 단위 | 실제 교체 단위 |
| --- | --- | --- |
| 삼성 | PRE / REGULAR / AFTER 각각 | 기존 삼성 scope와 지원 route |
| 비삼성 | PRE / REGULAR / AFTER × 두산·주성·HPSP·알테오젠·기타 등록 종목 유형 | 기존 symbol type·price band·route scope |
| 패턴 | 하락반전·회복/재접촉·상승지속/돌파 및 동시 충족 조합 | 기계 목록은 고정, 현재 지원 typed union의 보조 binding |

동일 scope 안에서도 개별 종목·원천일·반등 구간 집중도를 공개한다. 불균등하게 추출한 삼성/비삼성·시장별 쌍을 단순 합산해 전 시장 성능으로 주장하지 않는다. 패턴별 진단은 가능하지만 이 연구에서 새 패턴별 보조 실행 owner를 추가하지 않는다.

무표본 PRE/AFTER는 기존 승인 계약대로 동일 유형·지원 route의 REGULAR binding을 승계한다. 독자적으로 관측/검증된 binding을 무표본 취급해 덮지 않는다. REGULAR도 무표본이면 유효한 현행 REGULAR를 유지한다. 상속은 실측 개선과 구분한다.

## 4. 우선 연구할 프롬프트 가설

후보 문구는 연구자가 오류를 분석해 작성·검토하고 불변 registry에 등록한다. 장후작업이 매번 자유롭게 새 문구를 생성하는 기능은 추가하지 않는다. 기계 신호·실제 불리한 사실·provider/model·주문 안전조건을 고정하고 한 번에 한 가설을 비교한다.

| 순서 | 반복 오류 가설 | 후보가 바꿀 해석 | 유지할 반증 |
| --- | --- | --- | --- |
| H1 | 위험 코드에 인용 가능한 사실이 있다는 이유만으로 CAUTION | `risk_fact_bindings`는 허용 인용 목록이며 현재 위험의 자동 증명이 아님 | 확인 시점에 실제 존재하는 불리한 사실과 정확 fact ID |
| H2 | 반전 전 매도 우세·VWAP 미회복을 새 반전의 실패로 해석 | rolling 과거 맥락과 현재 확인 신호를 시간적으로 구분. 기존 창의 회복을 추가 필수 조건으로 만들지 않음 | 확인 때 이미 관측된 새 저점·회복 실패·다른 유효 모순 사실 |
| H3 | 상승지속/돌파에도 하락→저점→FIRST를 요구하거나 한 가지 branch로 전체 기회를 거부 | 모든 supplied signal을 평가하되 없는 하락/저점을 요구하지 않고 공통 진입 기회를 판단 | 공통 기회에 실제 적용되는 불리한 사실. 여러 branch 중 하나만 통과한 것을 공통 PASS로 조작하지 않음 |

H1은 미검증 `dd44...` 후보의 문구·개발 계보부터 확인한다. 기존 프롬프트에도 과거 맥락 구분 지시가 있으므로 단순히 같은 지시를 길게 반복하는 것을 개선으로 간주하지 않는다. 실패 응답의 실제 인용·문구 충돌을 찾아 최소 차이 후보를 만든다. H1/H2를 합치거나 H3로 넘어갈 때에는 새 후보 hash와 근거를 남긴다.

첫 후보에 사용할 수 있는 ASCII 문구 예시는 다음과 같다. 이는 계획의 초안이며 등록·전송된 문구가 아니다.

```text
A risk_fact_bindings entry lists permitted citations; it does not establish
that a blocking risk is active. Distinguish context preceding confirmation
from adverse evidence observed at confirmation. Rolling sell pressure or a
below-VWAP position alone does not invalidate a confirmed signal. Preserve
supplied current adverse evidence. Do not invent missing evidence or require
an additional confirmation that the machine contract does not require.
```

스키마·projector 변경이 필요하면 문구 효과와 입력 효과를 따로 기록한다. PA12의 신규 root 입력이 구현되지 않았다면 임의 필드를 만들어 연구하지 않고 현재 지원 패턴으로 진행한다. 미래 라벨, 목표 도달 시간, 성과 순위, 정답을 암시하는 research ID는 모델 입력에서 제외한다.

## 5. 추가 200회로 진행하는 실제 비교 설계

### 5.1 개발과 효과 확인을 분리

1. **호출 0회로 오류 census:** 기존 exact 응답에서 WIN+비PASS와 FAIL+PASS를 함께 수집한다. 알려진 승리 7건은 개발 사례로 고정한다. 실패인데 PASS인 사례가 없으면 `unobserved`로 표시하고 정상 차단 사례와 혼동하지 않는다.
2. **개발 비교:** 아래 40회 이내에서 우선 H1 한 개를 진단한다. 개발 사례는 label/verdict를 보고 선택할 수 있으나 채택용 성과 분모에서 제외한다. 실패 반례를 포함해 지시를 바꾼 이유와 출력 변화를 확인한다.
3. **후보 동결:** English ASCII 원문, 부모·개발 key 목록, projector/schema/validator/model/생성 설정을 고정한다. 오류 분석으로 읽고 문구 수정에 이용한 사례도 개발 목록에 포함한다.
4. **효과 확인:** 남은 누적 source-valid 확인점에서 label/AI verdict를 보지 않는 고정 seed와 scope별 순환 추출로 비교 명단을 먼저 봉인한다. 같은 확인점의 현행/후보 쌍부터 완성한다. WIN만 골라 성능을 평가하지 않는다.
5. **수정 시 새 실험:** 확인 결과를 보고 문구를 다시 고쳤으면 이전 확인 사례는 새 후보의 개발 사례가 된다. 기존 평가 결과는 보존하고 새 후보는 다른 사전 지정 확인점에서 평가한다. 결과를 본 뒤 유리한 seed로 다시 뽑지 않는다.

정해진 holdout 일수나 최소 표본 수를 추가하지 않는다. 개발에 사용한 정답으로 효과를 재증명하지 않는 분리만 유지한다. 같은 비교 계약의 기존 적격 공통 쌍은 누적으로 합칠 수 있으며 중복·개발 오염·원천 정정을 반영한다.

### 5.2 예산 배분과 호출 순서

| 용도 | 신규 attempt 배정 | 사용 방법 |
| --- | ---: | --- |
| 오판 원인·후보 개발 | 40 | H1 우선, 필요할 때 H2/H3. 기존 응답 우선 활용 |
| 고정 후보의 효과 확인 | 140 | 현행 1개 대 후보 1개, 사전 명단의 쌍 완성 우선 |
| 전달 계약 차이·미완료 쌍 보충 | 20 | 실제 현행 wire 대조, 전송 결과 확인 후 합법적인 보충에 사용 |
| 합계 | **200** | 캐시 조회 0회. failed/uncertain/실제 재시도도 포함 |

배분은 총 200회 안에서 미사용분을 확인 단계로 옮길 수 있다. 다 쓰는 것이 목표는 아니다. 양쪽이 모두 미호출이면 2회, 현행 exact 응답을 재사용하면 후보 1회다. 따라서 총 신규 200회는 최대 100개 전부 신규 쌍 또는 적격 현행 cache가 있을 때 최대 200개 후보 응답에 해당하며, 개발 호출·실패를 제외한 채택용 쌍은 더 적다.

확인 호출은 기본 20 attempt 단위로 진행 상황을 보고한다. 삼성/비삼성, PRE/REGULAR/AFTER 순환 순서와 scope별 추출 확률을 결과를 보기 전에 정한다. 자료가 없는 scope의 예산은 사전 규칙에 따라 다른 적격 scope로 옮기고 표본 결손을 명시한다. 128개 모든 scope에 고르게 한두 번 호출하는 것을 목표로 하지 않으며, 한 묶음 안에서는 같은 scope의 비교 쌍을 완성한다.

각 묶음마다 호출 전후 누적 사용량·정확 cache 재사용·완성/미완료 쌍·scope별 성과·저장량 증가를 기록한다. 같은 현재 binding/후보/관측 계약의 모든 유효 쌍을 누적해 판단한다. 중간 결과로 후보를 고르는 연구이므로 반복 관찰·선택 사실을 공개하며 독립 확증이나 통계적 유의성을 주장하지 않는다.

### 5.3 추가 예산의 구현 계약

추가 연구 허용을 기존 `LIMIT=100` 상수 증가나 날짜 재지정으로 구현하지 않는다. 논리적 예산 식별자는 `aux_prompt_research_20261008_01`, allowance는 **200**으로 고정하고 승인 출처·대상 후보/원천 범위·총량·사용량·종료 상태를 보존한다. 아래 항목은 후속 구현 요건이며 현재 지원 CLI가 있다는 뜻은 아니다.

- 이번 fork 연구의 신규 전송은 이 승인 예산으로 명시적으로 예약한다. 원래 원천일·기존 장후 attempt 15,228 기록은 유지한다. 이미 소진된 장후 100회 예산을 추가 연구 예약의 AND 조건으로 다시 적용하지 않는다.
- 일반 장후 실행은 기존 원천일 100회 정책을 계속 쓴다. 새 연구 예산 ID가 없거나 승인 범위 밖이면 추가 예산을 사용할 수 없다. 세션/후보/세대/자정 변경이나 실패 때문에 200회가 초기화되지 않는다.
- 같은 provider attempt를 여러 origin 참조에 연결해도 연구 사용량은 고유 attempt 한 번이다. 예약과 총량 차감은 원자적으로 수행하여 두 프로세스가 동시에 남은 1회를 초과하지 못하게 한다. 연구 예산을 선택했다는 이유로 같은 요청을 새 request ID로 위장해 중복 호출하지 않는다.
- 실제 전송 결과가 불확실한 예약은 차감·보존하며 새 allowance/후보 이름으로 재시도하지 않는다. 복구·재사용은 기존 durable 응답 reconciliation을 따른다. 200회 소진은 미완료 상태로 종료하고 자동으로 새 allowance를 만들지 않는다.
- 추가 승인 범위는 이번 연구다. 운영 AI 횟수 계약, provider 간격/외부 rate limit, 장후 정기 예산과 독립한다. 다음 장후에 200회가 자동 반복되지 않으며 남은 예산도 새 일자에 자동 부여하지 않는다.

## 6. 전송 일치·분기 격리·원장

### 6.1 무엇을 비교했는지 고정

`confirmation_replay`와 `delivered_live`를 분리한다. 동일 arm 이름이어도 실제 system/user bytes, schema/name, provider/model, endpoint, token/생성 설정이 다르면 같은 대조군으로 간주하지 않는다. 현재 registry 경로는 `gpt-5.4-nano`, 1024 output tokens, reasoning `none`을 고정한다. 기존 비registry 경로와의 전송 동등성은 이름만으로 가정하지 않는다.

착수 시 실제 현행 요청을 저장 trace 또는 provider 호출 없는 전송 fixture로 복원한다. 현행 wire와 연구 재구성 요청이 다르면 다음을 구분한다.

- 동일 생성 설정에서 문구만 바꾼 실험은 **문구 비교**다.
- wrapper/schema/입력/생성 설정까지 바뀌는 실험은 **배포할 보조판정 묶음의 비교**다. 실제 현행 전송 계약을 대조군으로 평가할 adapter가 필요하면 먼저 구현한다. 재구성된 예전 문구의 우월성을 실제 현행 대비 효과로 바꾸어 말하지 않는다.

cache는 exact request·관측 시점·모델 설정·검증 provenance가 맞을 때만 재사용한다. 모델 revision이나 오래된 응답의 비교 가능성을 확인할 수 없는 경우 한계를 표시한다. 실제 response ID와 원 응답을 보존하며 모델이 자기 판단을 평가한 점수나 가상 응답을 실제 쌍으로 사용하지 않는다.

### 6.2 다른 세션·장후와 충돌하지 않는 저장

연구의 제안 저장 위치는 `data/report/reversal_auxiliary_tuning/research/<research_id>/`다. 작은 config, 승인 예산 참조, 불변 campaign/evaluation, 진행 요약만 둔다. 기존 원천일 `latest-campaign.json`, 전역 `auxiliary/tuning.json`, 정기 장후 expected membership을 덮지 않는다.

입력·원 응답은 기존 `data/ai_comparison_store/v1`의 DB/pack/object를 공유한다. 별도 대형 SQLite 복제·normalized 입력 복제·5-arm 전수 큐 재생성을 하지 않는다. 연구 membership/checkpoint에는 research ID·역할(development/evaluation)·후보/현행/원천 계약을 포함하고, exact request/object dedup은 분기 간 유지한다. 실제 선택한 pair만 물질화한다.

단일 writer fence와 기존 lock 순서를 유지하며 다른 writer가 있으면 bounded 대기/재개한다. 기존 장후 작업을 임의 종료하거나 lock을 지우지 않는다. 읽기 전용 census는 새 pack을 만들지 않는다. 저장량 보고는 공통 DB/pack의 이전/이후 크기와 추가 고유 요청 수를 분리한다. 운영/rollback이 참조하는 원 응답·registry·원천은 연구 종료 시 삭제하지 않는다.

`prepare → calls → evaluate → publish`는 **명시한 불변 campaign hash**를 끝까지 전달한다. 발행 시 날짜의 latest를 읽어 다른 세션의 비교로 바뀌는 현재 연결을 고친다. 선택 evaluation과 정확 actual response의 연결을 다시 검증하고, campaign의 부모와 현재 부모가 달라졌다면 조용히 새 hash로 바꾸지 않는다.

## 7. 효과 판정과 채택

공통 유효 실제 응답 쌍에서만 `TP=WIN+PASS`, `FP=FAIL+PASS`, `FN=WIN+비PASS`, `TN=FAIL+비PASS`를 계산한다. VETO·CAUTION의 세부 W/F를 분리하고 이 시점의 대기를 실제 손실로 표현하지 않는다. 입력 결손·무효 응답·미응답·불확실 전송은 TN에 넣지 않는다. 한쪽이 무효면 그 쌍을 양쪽 분모에서 제외하고 제외율을 공개한다.

**채택 기준은 기존 구현의 누적 `PASS 승률=TP/(TP+FP)` 개선이다.** 동일하면 TP가 더 많은 후보를 선택한다. 분수로 비교해 반올림 동률을 만들지 않는다. EV·손익비·고정 최소표본/일수·기존 승리 100%/80% 보존율을 추가하지 않는다.

| 비교 상태 | 처리 |
| --- | --- |
| 양쪽 PASS 분모가 있고 후보 승률이 높음 | 해당 scope의 개선 후보. 늘거나 줄어든 PASS의 W/F를 함께 공개 |
| 양쪽 승률 동률, 후보 TP 증가 | 기회 보존 개선 후보 |
| 후보 열위·동률이며 TP 증가 없음 | 현행 유지, 원인 분석 대상으로 기록 |
| 현행 또는 후보 PASS 분모 0 | 승률은 null. 전부 차단을 100%로 만들거나 현행 0/0을 0%로 가정해 우월성을 선언하지 않음 |
| 유효한 공통 쌍 없음 | 효과 미확인. 모델/schema 오류·원천 결손·예산 부족을 나눠 보고 |

현재 `improves()`도 양쪽 PASS 분모가 있어야 한다. **현행이 계속 전부 막는 scope에서는 이 비교만으로 자동 교체 효과를 판정할 수 있다는 가정을 하지 않는다.** 같은 사전 규칙의 누적 평가를 이어가며 후보가 복원한 W/F와 기계 원 승률을 별도 제시한다. 기계 승률을 몰래 현행 보조 승률의 대체 기준으로 쓰지 않는다. 기존 무표본 REGULAR 상속은 이 후속 우월성 비교와 별도다.

보고에는 기계 원 승률, 현행/후보 PASS 승률, TP/FP/FN/TN, 승리 보존율, 실패 차단율, 추가 PASS와 제거 PASS의 W/F, 전체 census/사전 표본/완료 쌍/미표집/U를 함께 둔다. 성과는 완료된 공통 쌍 조건부 결과이며 실패·미응답의 비대칭을 숨기지 않는다. 기계보다 PASS 승률이 낮은 scope는 보조 관문의 역효과로 표시해 연구 우선순위에 둔다.

128 scope 전부나 과거 5-arm 전수 비교의 완료를 기다리지 않는다. 개선이 확인된 scope부터 인계하고 나머지는 현재 binding을 유지한다. 자연 주문·실현 손익은 별도 사후 관찰이며 프롬프트 연구 성과를 실제 수익으로 보고하지 않는다.

## 8. 효과 확인 직후 장중 적용 절차

1. **최신 운영 부모 확인:** 연구 착수/적용 시점의 정확 당일 bundle, detector manifest, 보조 binding, registry/reader code, release/PID를 기록한다. 다른 세션의 기계 추가·PA0/PA13 코드 복구가 끝났으면 그 결과를 새 기준으로 대조한다. 이전 08:44 영수증을 현재 PASS로 재사용하지 않는다.
2. **실제 실행 경로 검증:** root에서만 성공한 검사로 끝내지 않는다. PA0/PA13의 실제 launch cwd·data anchor·source SHA·loader/cache·code pin 인계가 유효해야 한다. 연구와 P0 복구는 병행하되 잘못된 source loader 위에 overlay만 발행해 적용 완료로 표시하지 않는다. 신규 13개 패턴 전체의 구현 완료가 현재 지원 scope 연구의 선행조건은 아니다.
3. **정확 연구 결과 인계:** 부모/현행 binding과 명시 campaign/evaluation hash를 다시 대조하고 실제 응답으로 재평가한다. code-only 복구의 정책 동등성은 해당 복구 receipt로 확인한다. detector 또는 typed 입력이 바뀐 scope는 새 비교 계약으로 필요한 exact 요청만 보충하며 기존 평가 hash를 최신 부모 값으로 덮지 않는다.
4. **장중 보조 overlay 발행:** 개선 scope·검증된 무표본 상속 범위만 당일 `effective_from`과 함께 CAS 교체한다. 기계 목록·rolling window·신호 타이머·기존 canonical outbox는 유지한다. 사용자가 지정한 기존+8개 초기 정책은 비교 미완료로 철회하지 않는다.
5. **재기동 없이 다음 확인점부터 소비:** 지원되는 문구 artifact 변경은 현재 보조 reader로 읽는다. reader/전송 계약의 코드 변경이 필요한 경우에는 검토된 배포·정식 장중 handoff가 먼저다. 기존 배포 승인은 해당 작업 owner에서 이어받으며 이 계획 작성 중 재기동하지 않는다. 봉인된 checklist/strict를 무효화하거나 검증을 끄지 않는다.
6. **전환 중 요청과 되돌림:** 교체 전 claim은 원 binding과 남은 기존 TTL로만 완료한다. 새 정책으로 과거 VETO/ready를 재발행하거나 중복 intent를 만들지 않는다. 결함 세대는 기존 revocation/CAS rollback 경로로 철회하고 검증된 직전 보조로 복귀한다. broker/보유/청산 소유권은 유지한다.
7. **소비·장후 승계:** `overlay_published`, `PID_binding_loaded`, `first_new_request_observed`를 따로 확인한다. 신호가 없으면 마지막 항목은 미관측이다. 첫 자연 요청의 prompt/input/schema/response hash와 제출 전 검증을 대조한다. 다음 장후는 실제 유효 시간대별 binding과 연구 평가를 참조하고 최신 유효 보조를 다음 날짜 부모로 승계한다. 200회 연구 allowance가 정기 호출 예산으로 전환되지는 않는다.

부모 CAS 충돌은 해당 scope를 재확인할 이유이며 연구 전체 삭제·전체 기계 재선정·장후 전체 재생성의 이유가 아니다. 적용 가능한 다른 scope는 별도 인계한다.

## 9. 실행 순서·리뷰·완료 기준

| 단계 | 작업 | 완료 증거 |
| --- | --- | --- |
| R0 기준 고정 | 현재 부모/원천/실제 전송 계약, 오류 census, 개발 key, 200회 승인 예산 정의 | 작은 연구 manifest와 실제 데이터 범위, P0 선행 상태 |
| R1 실행 경로 보완 | 연구 namespace·추가 예산 예약·명시 campaign 평가/발행 구현 | 반복 리뷰/수정, 아래 반례 검증. 현재 정기 경로 회귀 유지 |
| R2 개발 | H1부터 최대 40회 배정 내 진단, 후보 원문·개발 계보 동결 | 원 응답·인용 fact 분석, immutable registry |
| R3 효과 비교 | 최대 140회와 미사용/보충 예산으로 공통 쌍 누적 평가 | 삼성/비삼성·시장/유형별 혼동행렬, 총량·제외·저장량 기록 |
| R4 장중 인계 | 확인된 scope부터 §8의 정확 부모/overlay 적용 | 발행/loader/PID/자연 요청 상태 분리, rollback 참조 |
| R5 종료·승계 | 총 신규 200회 이하에서 성과/미확인/현행 유지 구분 | 최종 연구 요약·다음 장후 binding 인계·남은 작업 |

R1의 신규 구현은 기존 `src/engine/scalping` 연구/보조 owner와 `src/engine/ai` 저장소에 둔다. 새 Python 모듈이 필요하면 인접 producer/consumer 구조와 location gate를 먼저 확인하며 `src/engine` root에 추가하지 않는다. 기존 [원장 개선 계획](main-ai-comparison-ledger-dedup-and-incremental-storage-plan-2026-10-07.md)과 [독립 운용 계획 §5.3~§5.7](main-operating-policy-independent-detection-and-contribution-evaluation-implementation-plan-2026-10-07.md#53-호출-한도-안에서-보조-관문-튜닝--108-보완-설계)의 공통 저장·관문 목적을 유지한다.

후속 구현의 필수 검증은 다음 반례에 한정해 먼저 수행한다.

- 기존 10/7 장후 예산 초과 상태에서도 명시 연구 allowance만 최대 200회 예약. 일반 장후는 여전히 추가 0회. 동시 남은 1회, 재기동·자정·새 후보·실패/uncertain에서 총량 보존.
- 두 연구와 장후가 같은 원천일을 사용해도 config/latest/checkpoint/평가가 섞이지 않음. 공유 exact cache는 재사용하고 연구 A 발행이 연구 B latest를 읽지 않음.
- 개발 사례가 확인 집합으로 유입되지 않음. outcome/verdict를 바꿔도 사전 표본·AI 입력이 불변. 한쪽 무효·U·미표집·전체 차단 null·동률 TP 증가·source 정정/중복 회계 확인.
- 실제 전송 fixture와 연구 요청의 입력/문구/schema/model 설정 대조. 미래 결과 유입·모순 fact 인용 누락·H3의 가짜 FIRST 요구를 탐지. 코드 테스트는 provider를 호출하지 않음.
- source anchor/PID cwd, 부모/code pin 변경, 관측된 PRE/AFTER 덮어쓰기 금지, 무표본 REGULAR 상속, 교체 중 old claim/TTL, 복귀/재기동 중 intent 중복 방지 확인.
- 새 연구 한 번으로 전체 원장/normalized 입력 복제가 생기지 않음. frozen 연구 결과와 운영/장후 참조를 끝까지 읽을 수 있음.

문서 종료 검증은 링크·단일 owner·권한/예산/날짜 일관성, `git diff --check`, print-only backlog parser다. 문서 검토 때문에 trading suite·실모델 호출·장후 재생성을 실행하지 않는다. 구현 종료, 연구 효과 확인, 장중 소비 완료는 서로 다른 상태로 보고한다.

## 10. 계획 리뷰에서 반영한 보완

| 발견한 위험/누락 | 반영한 결정 |
| --- | --- |
| 추가 연구 허용을 무제한 또는 장후 상수 변경으로 오해 | 사용자 확정 추가 200회, 단일 연구 allowance와 기존 장후 예산 분리 |
| 알려진 WIN 7건만 통과시키고 성공 선언 | 개발 사례 제외, 실패 오판 분석, 사전 고정 공통 쌍·완료 편향 공개 |
| registry의 옛 문구와 실제 현행 전송이 다를 수 있음 | 문구 실험/배포 묶음 실험을 구분하고 실제 wire 대조군 검증 |
| fork가 전역 latest/config를 덮거나 다른 비교를 발행 | 연구 namespace와 명시 불변 campaign의 전 구간 전달 |
| 기존 PASS 0을 0%로 처리하여 허위 개선 | null 유지·복원 W/F 공개, 기계 승률로 몰래 대체하지 않음 |
| P0 source 경로 결함을 새 AI 정책으로 해결했다고 표시 | 별도 PA0/PA13 완료 증거와 실제 launch loader 검증 후 장중 인계 |
| 추가 패턴 구현 때문에 현재 연구를 기다리거나 초기 등록을 재심사 | 현재 지원 scope 연구 병행, 초기 목록과 후속 보조 개선 분리 |
| 장후마다 새 프롬프트·대형 원장을 생성 | 검토한 후보 수동 등록, shared object 재사용, 정기 평가는 등록 후보만 |

현재 상태: **연구계획 수립**. 이 문서는 효과 있는 후보를 이미 찾았거나 200회 allowance가 코드에 반영됐다는 완료 증거가 아니다.

문서 검증: 로컬 링크 14개와 문서 anchor, 공백/diff 검사를 확인했다. print-only parser는 21개 항목을 출력하며 위 실행 owner는 오늘 체크리스트에 1개다. 다른 세션의 코드 변경은 수정하거나 이 문서 검증의 코드 PASS로 포함하지 않았다. 이번 연구의 신규 AI 호출·정책 변경은 0건이다.

## 11. 실행 승인 및 추가 연구 인계 — 2026-10-08

위 §1·§10의 계획 작성만 수행한 상태와 호출 0건은 **계획 작성 당시 기록**이다. 후속 사용자 지시 “연구계획을 실행하라”로 연구 구현·실호출을 진행했으며, “호출한도를 증가시키고 추가연구를 진행하라” 및 답변 **“추가 200회 — 총 400회”**를 추가 실행 승인으로 기록한다.

- 단일 예산 key `research_auxiliary:aux_prompt_research_20261008_01`을 유지한다. 최초 `allowance.json` 200회는 보존하고 `allowance-topup-400.json`으로 **추가 200회, 누적 상한 400회**를 연결한다. 예약·실패·불확실 호출을 포함한 과거 사용량을 초기화하지 않는다. 정기 장후 100회 계약 및 기존 원천일 15,228회 기록은 변경하지 않는다.
- 최초 연구에서 출력 한도 512와 JSON 잘림, 후보/현행의 입력 arm 차이, 날짜순 호출로 시장별 순환 추출 순서가 사라지는 문제가 확인됐다. 응답 무효를 정상 차단으로 집계하지 않고, 현재/후보 입력을 동일 arm으로 맞춘 비교와 실제 native 전송 비교를 구분한다. 고정 표본을 유지하며 연구 호출만 봉인된 scope 순환 순서로 처리한다.
- 09:38 장중 v6 전환 후에는 현재 v6 부모 및 실제 불변 릴리스의 보조 binding을 다시 고정한다. 같은 탐지 정의의 115개 scope는 기존 native 확인점 census를 재사용하고, 변경된 13개 scope는 같은 원 시계열 prefix에서 현행 FSM으로 재탐지한다. 전체 원장 복제 없이 scope별 고정 hash reservoir만 공유 store에 저장한다. 이전 개발/검토 100개 key는 새 후보 평가에서 제외한다.
- 추가 후보는 현행 네 가지 arm 각각에서 **입력 bytes를 고정**하고 문구를 변경한다. 실제 native wire pilot와 양쪽 1,024토큰의 비교를 각각 봉인한다. 생성 설정만 맞춘 비교는 실제 운영 대비 우월성/장중 적용 완료로 표시하지 않는다.
- 연구 namespace의 설정/평가는 정기 장후 latest를 덮지 않는다. 명시 campaign으로 호출·평가·발행을 연결하고, 개발 결과 또는 native 대조가 없는 연구 결과의 직접 발행을 차단한다. 실제 발행에는 현행 부모·현재 binding·전송 계약과 독립 검토된 코드가 계속 필요하다.

코드 owner는 `src/engine/scalping/reversal_auxiliary_research.py`와 `reversal_auxiliary_research_population.py`, 기존 tuning/intraday 모듈이다. 실행 owner는 기존 `DirectFamilySourceRepairMainMechanisticEntry`이며 추가 OPEN을 만들지 않는다. 연구로 기존 봉인 checklist 바이트·장후 결과·운영 정책을 변경하지 않는다. 자세한 실제 호출 수·무효 응답·scope별 성과·배포 여부는 [실행 연구 검토](../audits/main-auxiliary-prompt-research-execution-review-2026-10-08.md)에 기록한다.

2차 중간 결과(종료 아님): 누적 398/400회 차감, 실제 응답 386개(추가 연구 198개), 미응답 예약 12개 보존, 잔여 2회. v6 입력 고정 비교 78점 중 유효 58쌍, 실제 native 및 출력 한도 대조 21점까지 실행했다. 설정을 맞춘 비교의 개선 scope 1개는 실제 native 응답 결손으로 장중 교체 근거를 확정하지 못해 현행을 유지했다. 다음 보완은 512토큰 잘림과 근거 인용 결손이며, 이번 연구가 정책 발행·배포·재기동 완료를 뜻하지 않는다.


## 12. 불완전 비교 보완 계속 승인 — 2026-10-08

사용자 “한도를 추가해도 되니 불완전 연구로 종료하지 마라”에 따라 연구를 계속한다. 우선 추가 200회로 누적 600회를 허용하며, 최초 200/400회 승인 파일과 기존 차감 398회는 보존하고 후속 승인 파일을 연결한다. 미응답/잘림/무효를 정상 BLOCK으로 계산하거나 과거 사용량을 초기화하지 않는다.

- 기존 512토큰 native 비교는 21건 중 16건이 잘렸고, 1,024토큰에서도 근거 ID 오류가 남았다. 먼저 연구용 공통 출력 계약을 보완하여 대조/후보 모두 같은 입력·출력 조건에서 비교를 완성한다.
- scalping 연구 모듈 `reversal_auxiliary_research_wire.py`가 ID를 짧은 별칭으로 전송하고, 신호별 확인과 위험 코드별 근거를 구조화한다. 원 사실·현재 시점·원 응답은 보존하며, 결과를 원래 union validator로 다시 검증한다. 누락된 답을 자동 PASS나 CAUTION으로 채우지 않는다.
- 이미 검토한 모든 178개 확인점은 후속 평가에서 제외한다. 새 표본은 동일 원천에서 scope별 고정 hash 순서로 선택하며 결과 W/F나 AI 답으로 선정하지 않는다. 삼성 PRE/REGULAR/AFTER와 비삼성 시장·종목 유형별 공통 유효 쌍을 보고한다.
- 공통 출력 형식 개선의 효과와 위험 판정 문구의 효과를 분리한다. 연구용 전송 계약은 직접 발행하지 않으며, 실제 운영과 일치하는 계약/reader 검증 없이 장중 적용 완료로 표시하지 않는다. 새 형식의 유효 비교와 결과 해석까지 완료하며 종전 응답 결손만을 이유로 연구를 종료하지 않는다.

## 13. 추가 연구 완료 및 인계 — 2026-10-08

후속 지시의 추가 허용을 사용하여 상한을 600→800회로 확장했다. 기존 사용량을 유지한 최종 차감은 653회, 실제 응답 640개, 미응답 예약 13개, 잔여 147회다. 공통 compact 형식의 문구 비교 60쌍, 판단 본문을 유지한 응답 계약 패키지 비교 65쌍, 추가 AFTER 가격 정체 가설 32쌍을 모두 유효 응답으로 완료했다. 부족한 호출 수나 응답 결손 상태로 종료하지 않았다.

전역 완화와 전체 AFTER 변경은 채택하지 않는다. 연구 조건에서 개선된 후보는 기타 종목 PRE 2만~10만원/NXT(H4), 기타 종목 AFTER 2만~10만원/SOR 및 2만원 미만/SOR, 삼성 AFTER/SOR(H5)의 네 경로다. 승률과 TP/FP/FN/TN, 정확 registry/evaluation hash는 [최종 실행 검토](../audits/main-auxiliary-prompt-research-execution-review-2026-10-08.md)에 인계했다. 운영 소비와 연구의 실제 호출 완료를 구분한다.

이번 후보는 공통 compact 전송 계약에서 평가했다. 장중 교체 전에는 실제 registry/provider 경로가 같은 encoder/schema/decoder와 raw receipt 보존을 지원하도록 연결하고 payload parity를 확인해야 한다. 기존 native 512토큰 계약에 후보 문구만 넣는 교체는 이 연구와 다르므로 실행하지 않는다. 이 fork에서는 정책 발행·배포·재기동을 수행하지 않았으며, 별도 구현 세션의 현재 코드·PID·정책을 덮지 않았다. 같은 실행 owner에 정확한 후보/전송 계약을 인계한다.

후속 [compact 계약 운영 연결·장중 적용 구현계획](main-auxiliary-compact-contract-intraday-adoption-implementation-plan-2026-10-08.md)의 AC0~AC7에 공통 codec·v2 registry·실제 provider/trace 연결, 구형 reader 호환성, 네 경로의 명시 평가 발행, 장후 승계와 배포·재기동 순서를 구체화했다. 비교 대조군은 `incumbent_prompt_under_successor_wire`로 기록하며 기존 native 운영 대비 우월성으로 바꾸어 설명하지 않는다. 이번 후속 작업은 계획 수립·문서 검증이며 코드·정책·운영 변경을 실행하지 않았다.

후속 계획 리뷰에서는 원 논리 신호와 전송 별칭 분리, 실제 SDK 요청 바이트 대조, 기계·보조 동시 발행/CAS 재실행, 현재 세대 위의 scope별 되돌림, 자정 후 해당 거래일 정책 승계와 준비 이후 변경 감지, 구형·신형 혼합 비교를 보완했다. 저장된 실제 응답과 원장 ID는 보존하고, 현행 조건이 달라진 경로만 다시 대조한다. 상세 변경 근거와 검증 반례는 후속 구현계획 §6.1에 둔다.
