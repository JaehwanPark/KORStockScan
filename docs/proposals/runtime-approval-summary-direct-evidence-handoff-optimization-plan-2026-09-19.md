# Runtime approval summary 직접 증거 인계 및 family 경제성 최적화 상세계획

작성일: 2026-09-19 KST

구현 기준: `origin/main` `bb6b955e3b37cb027973a3fdf5874349245841e8`

실행 owner: [2026-09-21 Stage2 checklist](../checklists/2026-09-21-stage2-todo-checklist.md)의 기존 `CodeImprovementWorkorderReview0918`

연계 계획: [Daily threshold-cycle 공통 튜닝 퇴역 계획](./daily-threshold-cycle-tuning-retirement-and-runtime-owner-separation-plan-2026-09-19.md), [구조결손·EV 증거 우선순위 계획](./code-improvement-workorder-structural-closure-and-ev-evidence-prioritization-plan-2026-09-19.md)

## 1. 결론

`runtime_approval_summary`는 제거하지 않는다. 다만 독립 튜너·경제성 승인기·정책 선택기로 확장하지 않고 **family별 직접 증거와 다음 소비 상태를 확인하는 최소 장후 인계 영수증**으로 고정한다.

EV 최적화는 이 요약기 안에서 수행하지 않는다. 각 family의 기존 evaluator가 동일 자본·비용 차감·독립 holdout 계약으로 경제성을 계산하고, 기존 publisher가 승인된 후보만 발행하며, `runtime_policy_bootstrap`이 검증된 직접 receipt만 다음 PREOPEN 환경으로 합성한다. 요약기는 그 결과를 재계산하지 않고 정확히 투영한다.

최적화 목표는 다음 네 가지다.

1. 파일 존재를 경제성 승인으로 오인하지 못하게 한다.
2. `source_gap`, `pending_maturity`, `measured_no_edge`, `validated_edge`를 분리한다.
3. 검증된 family 후보만 정책·PREOPEN·장중 소비로 연결됐는지 추적한다.
4. 구형 Daily/EV 집계와 대형 누적 산출물을 안전하게 제거한다.

## 2. 현재 상태와 문제

### 2.1 현재 역할

현재 schema v2는 다음 9개 direct owner의 보고서 존재·날짜·SHA를 확인한다.

- observation source quality
- entry cancel wait
- entry split order
- scale-in split order
- Samsung machine entry
- low-price two-leg
- low-price expansion
- intraday WS freshness
- AI action outcome

출력 권한은 이미 다음처럼 제한돼 있다.

- `decision_authority=family_owned_direct_evidence_summary_only`
- `common_tuning_candidate_created=false`
- `runtime_effect=false`
- `allowed_runtime_apply=false`
- `actual_order_submitted=false`
- Daily/EV 공통 후보 생성은 retired

### 2.2 최신 구형 결과

2026-09-17 대상 최신 구형 산출물은 family 17개, paired comparable 0개, validated improvement 0개, 다음 PREOPEN 후보 0개, actual net-profit improvement null이었다. 이 결과는 현재 축소 schema의 자연 실행 증거가 아니다.

### 2.3 구조적 결함

| 결함 | 현재 영향 | 판정 |
| --- | --- | --- |
| `status=pass`가 파일 존재·날짜·해시만 의미 | 경제성·정책 승인으로 오독 가능 | 소비자 의미 계약 수리 필요 |
| required owner가 코드 고정 집합 | OFF·retired·선택적 family와 실제 active owner가 어긋날 수 있음 | 기존 직접 receipt owner에서 파생 필요 |
| 64MiB 초과 JSON은 hash-only | 보고서가 있어도 semantic status·경제성 확인 불가 | compact companion/manifest 계약 필요 |
| source status를 전달하지만 판정하지 않음 | `source_gap`도 available source로 집계 | completeness와 eligibility 분리 필요 |
| policy/bootstrap receipt는 optional | source complete와 다음 장전 소비 준비를 혼동할 수 있음 | 별도 handoff 상태 필요 |
| 최신 산출물이 퇴역 전 대형 schema | 현재 코드의 자연 producer/consumer 증거 부재 | 다음 정상 장후 acceptance 필요 |
| 구형 traceability 설명 잔존 | 운영자가 summary를 승인기로 오인 가능 | owning 문서 정합화 필요 |

이 결함은 summary에 새 EV 계산기를 넣어 해결하지 않는다. 의미와 인계 계약만 보완한다.

## 3. 목표 구조

```text
family raw/source/terminal
          │
          ▼
family-owned evaluator
  ├─ source/comparison 상태
  ├─ 비용 차감 paired EV·순익·tail·노출
  ├─ model/candidate holdout
  └─ first blocker·closure test
          │
          ├──────── no-edge/gap/pending ──────── incumbent 유지
          │
          ▼ validated edge only
family-owned dated publisher
          │
          ▼
runtime_policy_bootstrap → PREOPEN → 장중 owner → R6 actual outcome
          │
          └──────── receipt/status ─────────────┐
                                               ▼
                                runtime_approval_summary
                                (직접 증거 인계 요약만)
                                               │
                           controller/tower/checklist/verifier
```

`runtime_approval_summary`는 위 흐름의 의사결정자가 아니다. producer와 마지막 소비자의 계약 단절을 한 화면에서 보여 주는 terminal handoff다.

## 4. RA0 — 기준선과 소비자 동결

구현 시작 시 다음을 읽기 전용으로 기록한다.

1. 선택 release와 source commit
2. 실제 실행 중 postclose/PREOPEN PID와 cwd가 있으면 그 release
3. 최신 summary의 date·schema·size·SHA·generated-at
4. 9개 direct owner의 exact-date path·size·mtime·SHA·status
5. controller, tower, summary handoff, checklist, strict verifier의 소비 필드
6. runtime bootstrap이 summary를 소비하지 않고 direct receipt를 읽는다는 증거
7. active/OFF/retired family와 현재 직접 publisher 목록

64MiB 초과 또는 growing artifact는 materialize하지 않는다. stat 후 existing compact summary/manifest 또는 bounded header만 사용한다.

Closure: 현재 producer→summary→diagnostic consumer와 publisher→bootstrap→runtime 경로가 서로 섞이지 않은 한 장의 inventory로 재현된다.

## 5. RA1 — 상태 의미 분리

기존 최상위 `status=pass`를 경제성 승인처럼 쓰지 못하도록 다음 최소 상태를 도입한다. 확인된 모든 repository consumer를 같은 변경에서 전환하고 `status`도 `direct_evidence_complete` 또는 `direct_evidence_incomplete`로 원자적으로 바꾼다. repository 밖의 실제 소비자가 확인된 경우에만 한 migration window 동안 의미가 명시된 compatibility alias를 유지한다.

| 필드 | 허용 값 | 의미 |
| --- | --- | --- |
| `direct_evidence_state` | `complete`, `incomplete` | required direct owner의 exact-date artifact·hash·schema 완결 |
| `economic_state` | `validated_edge`, `measured_no_edge`, `identical_policy`, `pending_maturity`, `source_gap`, `not_applicable`, `mixed` | family evaluator 결과의 투영. summary가 계산하지 않음 |
| `policy_handoff_state` | `candidate_published`, `incumbent_preserved`, `blocked`, `not_applicable` | dated publisher 결과 |
| `preopen_consumption_state` | `verified`, `pending`, `rejected`, `not_due`, `not_applicable` | bootstrap receipt 상태 |
| `natural_acceptance_state` | `verified`, `pending`, `not_due`, `not_applicable` | 실제 적용 버전·완료 손익 증거 상태 |
| `resolution_mode` | `producer_repair`, `consumer_rebind`, `natural_maturity`, `historical_unrecoverable`, `measured_no_edge`, `retired_or_not_applicable` | 다음 조치 분류 |

규칙:

- `direct_evidence_state=complete`는 경제성·정책·PID·실제 이익을 승인하지 않는다.
- 경제성 필드가 없으면 null과 exact reason을 유지한다.
- `source_gap`을 `measured_no_edge`로 바꾸지 않는다.
- `pending_maturity`는 미래 입력 생성 경로가 구현·검증된 경우에만 허용한다.
- retired/OFF family는 missing이 아니라 `not_applicable`이다.
- current runtime lock·incumbent carry는 신규 validated edge와 분리한다.

## 6. RA2 — active owner와 required 계약 정합화

별도 registry·DB·service를 만들지 않는다. 다음 기존 원천을 우선순위대로 사용해 required 여부를 결정한다.

1. 명시적 retirement/OFF envelope
2. current checklist와 운영 설정의 active owner
3. postclose wrapper에서 해당 날짜에 실행하도록 설정된 producer
4. runtime bootstrap의 기존 direct receipt source 계약

family publisher가 실제 발행한 receipt는 required 여부의 선언 원천으로 사용하지 않는다. receipt가 없다는 이유로 required owner 자체가 목록에서 사라지는 순환 판정을 막고, expected owner와 observed receipt를 분리한다. 위 원천이 서로 충돌하면 자동으로 하나를 고르지 않고 `owner_contract_drift`로 인계를 차단한다.

코드 고정 목록은 fallback inventory로만 유지한다. owner별로 다음을 선언한다.

- family·stage·scope·venue/session
- producer path와 report type/schema
- required/optional/not-applicable 근거
- evaluator path와 comparison contract
- publisher/policy path
- PREOPEN/runtime consumer
- first blocker owner와 closure test

같은 family의 report와 policy가 모두 required인 척 중복 집계하지 않는다. source evidence와 apply receipt의 역할을 분리한다.

Closure tests:

- active producer 누락은 `incomplete`
- retired/OFF producer 부재는 `not_applicable`
- optional policy의 target-date mismatch는 경고가 아니라 해당 handoff만 `rejected`
- 한 malformed family가 무관한 family의 증거를 승인하지 않음

## 7. RA3 — family 경제성 계약 투영

summary는 계산하지 않고 각 evaluator가 이미 검증한 최소 projection만 복사한다.

### 7.1 필수 projection

- `comparison_status`
- incumbent/candidate policy identity와 실제 차이
- paired comparable sample·source day·holdout day
- 비용 차감 baseline/candidate EV와 paired delta
- 일별 baseline/candidate 순익과 delta
- tail/downside, capital/reserve/exposure, fill participation
- cost/model/stress provenance와 보수적 delta 하한
- source-quality gate
- model-validation holdout와 candidate-selection holdout
- actual completed profit 여부
- evidence artifact path·schema·semantic SHA
- first blocker·owner·closure test

값이 없는 경우 null을 유지한다. summary가 비용, tolerance, stop, exit, fill 또는 profit을 보간하지 않는다.

### 7.2 후보0 분류

후보가 없으면 다음 중 하나로 정확히 분리한다.

- `source_gap`: 필수 원천·identity·cost·terminal 결손
- `unsupported_scope`: evaluator가 검증하지 않은 owner/route/session
- `pending_maturity`: future producer 계약은 완성됐으나 표본 floor/holdout 미성숙
- `insufficient_sample`: 현재 comparison은 유효하나 표본 수 부족
- `identical_policy`: challenger가 실제 결정을 바꾸지 않음
- `measured_no_edge`: 비교는 유효하지만 비용 후 개선이 양수가 아님
- `validated_edge`: 독립 holdout과 위험 gate를 통과한 양수 개선

후보0 집계가 새 workorder를 무조건 만들지 않는다. 구조결손만 기존 workorder로 보내고, maturity는 기존 family 자연 owner, no-edge는 incumbent 보존으로 보낸다.

## 8. RA4 — 대형 artifact의 bounded semantic contract

low-price와 expansion처럼 64MiB를 넘는 보고서는 전체 JSON을 summary가 다시 읽지 않는다.

1. 기존 producer가 이미 만드는 compact summary/manifest가 있으면 그것을 소비한다.
2. 없다면 해당 family producer의 기존 출력에 작은 terminal companion을 추가한다.
3. companion에는 source artifact SHA·size·schema·target date·terminal status·economic projection SHA만 둔다.
4. companion과 원 artifact hash가 불일치하면 `semantic_unverified_large_source`로 차단한다.
5. 단순 파일명 날짜와 stream hash만으로 economic state를 만들지 않는다.

새 collector, raw projection DB, 전수 스캐너를 만들지 않는다. 큰 원천을 테스트 fixture로 복제하지 않는다.

## 9. RA5 — 정책·PREOPEN·장중 소비 분리

summary와 runtime 적용의 권한 경계를 회귀로 고정한다.

### 9.1 후보 선정

- 후보 선정은 family evaluator/publisher만 수행한다.
- 동일 frozen 수량·예산·후행 guard 비교가 없는 후보는 publish 금지다.
- validated edge라도 family의 기존 promotion floor·rollback·same-stage conflict guard를 통과해야 한다.
- no-edge/source-gap/pending이면 incumbent·operator lock·명시적 OFF를 보존한다.

### 9.2 bootstrap

`runtime_policy_bootstrap`은 summary가 아니라 다음을 직접 검증한다.

- dated family receipt와 policy artifact hash
- effective date·scope·stage·owner
- `allowed_runtime_apply=true`
- retirement/OFF scrub
- owner conflict·operator lock·rollback

summary는 bootstrap 결과를 읽기 전용으로 투영할 뿐 env를 만들거나 수정하지 않는다.

### 9.3 실제 적용 성과

R6는 적용 policy version별 episode dedup 후 다음을 family evaluator로 돌려준다.

- rolling/cumulative 비용 차감 EV와 순익
- tail/downside와 노출/reserve
- fill participation
- 모델 예측 delta와 실제 완료 이익의 분리
- source/policy/PREOPEN/PID/runtime/terminal identity

summary는 R6 존재·버전 결속·상태만 보여 준다.

## 10. RA6 — consumer 의미 계약 수리

### 10.1 controller

- `direct_evidence_state=complete`와 strict verifier PASS만 장후 인계 완료로 본다.
- 이를 경제성 완료나 다음 정책 적용 완료로 표시하지 않는다.

### 10.2 control tower·summary handoff

- summary 전체 파일 hash와 generation/date/schema를 확인한다.
- family별 economic evidence artifact/hash가 바뀌면 stale을 검출한다.
- 큰 원천의 terminal companion 불일치를 허용하지 않는다.

### 10.3 checklist·workorder

- structural blocker만 구현 후보로 만든다.
- natural maturity는 기존 family acceptance owner로 남긴다.
- measured no-edge는 구현 주문을 만들지 않는다.
- validated edge는 기존 publisher/PREOPEN owner로 인계한다.
- 같은 blocker를 새 ID로 반복 생성하지 않는다.
- `DirectFamily*` 항목은 현재 `runtime_approval_summary`에서 다시 투영하는 builder 소유 작업이다. 다음 summary가 해당 family를 terminal/not-applicable로 판정하면 이전 자동 블록의 해당 항목은 제거하고, 무관한 수동 작업은 보존한다.

### 10.4 strict verifier

최소한 다음을 검사한다.

- Daily/EV retired flag
- exact target/source/effective date
- required/not-applicable owner census
- artifact·semantic hash
- summary 권한 false
- policy candidate와 bootstrap receipt의 family/hash 일치
- source-gap인데 apply된 상태 차단
- validated receipt 없이 candidate가 선택된 상태 차단
- final generation 이후 mandatory source 변경 차단

## 11. RA7 — 구형 산출물과 문서 정리

삭제는 새 schema의 자연 생성과 consumer 검증 뒤에 수행한다.

### 11.1 선행 조건

1. 정상 영업일 장후에 새 summary가 자연 생성됨
2. controller/tower/handoff/checklist/strict가 동일 generation/hash를 소비함
3. 다음 정상 PREOPEN bootstrap이 direct family receipt를 소비함
4. runtime이 summary를 정책 입력으로 읽지 않음을 재확인함
5. rollback·감사 보존 대상 목록이 확정됨

### 11.2 삭제 대상

- 퇴역 Daily/EV family row를 포함한 반복 대형 JSON/Markdown
- reuse contract가 끝난 중간 generation
- retired ADM/LDM·pattern-lab·swing 승인 흔적만 복제한 summary
- current consumer가 참조하지 않는 오래된 Markdown
- 구형 schema 전용 테스트 fixture와 문서 설명

### 11.3 보존 대상

- 전환 직전 마지막 산출물 1세트와 SHA receipt
- 첫 자연 새-schema 산출물
- selected release·bootstrap·PREOPEN·PID·rollback 증거
- source-quality, order/fill/terminal, custody, 비용 손익 원장
- 정책 적용 버전별 실제 성과 증거

정리는 active process·lock·consumer 참조·current-day source를 확인한 뒤 regenerable artifact에만 수행한다.

## 12. 구현 순서

| 단계 | 변경 | 검증 |
| --- | --- | --- |
| T0 | 현재 release·artifact·consumer 기준선 동결 | bounded read-only inventory |
| T1 | 상태 의미와 owner applicability 보완 | missing/OFF/retired/date/schema 회귀 |
| T2 | family economic projection과 first blocker 전달 | null/no-edge/identical/maturity/source-gap 회귀 |
| T3 | large-artifact terminal companion 결속 | hash mismatch·oversize·stale 회귀 |
| T4 | controller/tower/checklist/verifier 의미 수리 | false PASS·stale generation·authority leak 회귀 |
| T5 | bootstrap 독립성·policy handoff 검증 | validated/rejected/incumbent/OFF 회귀 |
| T6 | self review→보완→재리뷰 | 영향 producer/consumer finding 0 |
| T7 | targeted validation | pytest, compile, wrapper `bash -n`, diff check, print-only parser |
| T8 | 승인된 경우 immutable release | source test·selected release·실제 PID 별도 보고 |
| T9 | 다음 정상 장후/PREOPEN 자연 acceptance | generation/hash·policy/PID·R6 분리 확인 |
| T10 | acceptance 뒤 구형 산출물 정리 | protected evidence 불변·consumer reference 0 |

## 13. 필수 회귀 시나리오

1. required source 누락 → direct evidence incomplete
2. retired/OFF source 누락 → not applicable, 전체 실패 아님
3. source exists + `source_gap` → completeness와 economic block 동시 표현
4. identical incumbent/candidate → improvement 0이 아니라 identical policy
5. 유효 음수 paired delta → measured no-edge, incumbent 유지
6. 표본 floor 미달 + future path 검증 → pending maturity
7. future path 미구현 → source gap, maturity로 위장 금지
8. large artifact companion/hash 불일치 → semantic verification 차단
9. validated edge + independent holdout → family candidate publish 가능
10. candidate hash/date/scope mismatch → bootstrap reject
11. 한 family reject → 무관 family receipt 승인 상태 불변
12. summary를 삭제·변조해도 runtime이 임의 후보를 적용하지 않음
13. summary PASS만으로 checklist가 경제성 완료를 표시하지 않음
14. 적용 버전이 다른 episode를 합산하지 않음
15. 모델 delta와 actual completed profit을 별도 필드로 유지

## 14. 성능 및 코드 범위 제한

- 새 서비스·daemon·DB·collector·generic evaluator를 만들지 않는다.
- `src/engine` root에 새 Python 모듈을 만들지 않는다.
- 기존 `runtime_approval_summary.py`, family terminal companion, 현재 consumers만 최소 수정한다.
- raw 전수 재스캔과 대형 보고서 반복 materialization을 하지 않는다.
- 양수 EV를 만들기 위한 threshold·표본 floor·비용·stress·holdout 완화는 금지한다.
- broker/account/order/quantity/cooldown/cap/custody/operator lock/hard safety를 보존한다.
- 합성 fixture 통과를 자연 표본·정책 적용·경제성 개선으로 보고하지 않는다.

## 15. 자연 검증 시점

현재 선택 배포본은 실제 PID 소비 전이며 축소 schema의 자연 산출물도 없다. 구현 여부와 무관하게 자연 acceptance는 다음 단계로 분리한다.

- 2026-09-21 정상 장후: source date 9/21의 direct owner·새 summary 자연 생성
- 다음 정상 PREOPEN: family receipt→bootstrap→env/hash 검증
- 장중: 실제 loader/PID consumption 확인
- position/episode 완료 뒤: 비용 차감 rolling/cumulative 성과 평가

시간 경과만으로 source gap이 해결되지는 않는다. producer·consumer 계약이 구현된 family의 표본 부족만 자연 maturity로 닫는다.

## 16. 완료 기준

구현 완료는 다음을 모두 만족해야 한다.

1. summary가 direct evidence completeness를 경제성 승인과 분리한다.
2. active/OFF/retired owner census가 실제 wrapper·publisher·bootstrap과 일치한다.
3. family 경제성 결과는 재계산 없이 exact artifact/hash로 투영된다.
4. 후보0이 source gap·unsupported·pending·insufficient·identical·no-edge로 구분된다.
5. validated edge만 family publisher→bootstrap으로 진행한다.
6. controller/tower/checklist/verifier가 `pass`를 경제성 완료로 해석하지 않는다.
7. large artifact는 bounded terminal contract로 semantic 검증된다.
8. summary가 없어도 runtime이 임의 후보를 만들지 않으며, summary가 있어도 runtime mutation 권한이 없다.
9. 자연 생성·PREOPEN·PID·실제 완료 손익은 별도 acceptance로 남는다.
10. 첫 자연 새-schema 인계 검증 뒤 불필요한 구형 산출물과 문서가 정리된다.

## 17. 최종 판정 원칙

이 개선의 성공은 summary가 양수 후보를 만드는 것이 아니다. 성공 기준은 다음과 같다.

- 실제 EV를 계산하는 family owner가 분명함
- 경제성 판단을 막는 최초 구조결손이 정확히 노출됨
- 유효 no-edge는 incumbent 보존으로 종결됨
- 검증된 edge만 다음 PREOPEN 정책으로 이동함
- 정책 적용과 실제 순익이 같은 버전·episode로 추적됨
- summary 자체는 작고 빠른 읽기 전용 인계 영수증으로 유지됨

## 16. 구현 상태 (2026-09-19)

- RA0–RA6: 구현·회귀 검증 대상. schema v3에서 직접 완결, 경제 상태, dated policy 인계, 다음 effective-date PREOPEN, 자연 acceptance를 분리한다.
- RA7: 코드 삭제가 아니라 첫 정상 영업일의 새 schema 자연 생성과 동일 generation consumer acceptance 후 실행하는 조건부 정리다. 보호 대상과 전환 직전 1세트는 유지한다.
- RA8: 지원 입력의 계산은 family evaluator가 소유하고 summary는 null을 보간하지 않는다. 양수 후보가 없으면 incumbent를 유지한다.
- RA9: 다음 정상 PREOPEN/PID와 적용 버전별 완료 손익은 자연 OPEN이다. 구현 완료나 배포 receipt로 대체하지 않는다.
