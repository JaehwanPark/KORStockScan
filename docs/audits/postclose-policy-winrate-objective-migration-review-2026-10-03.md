# 장후 승률 목적 이행·분모 보완·격리 재생성 리뷰 — 2026-10-03

## 1. 결론

실제 기계·보조 생성기/검증기의 새 후보에서 성공100%·80% 보존 제약을 제거했다. 승률 개선을 학습 순위와 후단 검증에 반영하고 성공 제외·실패 회피·순성과를 별도 보고한다. 전체 장후 정책 조사와 후속 구현 설계는 [W0~W4 계획](../proposals/postclose-policy-winrate-objective-migration-plan-2026-10-03.md)에 정리했다.

**개선 패턴은 발견됐다. 다만 최종 정식 후보 선정은0이다.** 보존80% 제거 직후 등록 생성기는28.73bp 후보를 선택했지만, 추가 리뷰에서 native 기회가 없는 trace를 독립 기회로 집계하는 결함을 확인했다. 이 분모를 보완한 최종 생성기는 기존 정책을 승계한다. 높은 관측 승률을 얻은 연구 결과와 정책 승격에 필요한 독립 기회 증거를 구분한다.

작업본은 미커밋이며 통합 커밋 manifest를 준비했다. canonical 정책 발행·PREOPEN·배포·재기동·provider/broker 호출은 수행하지 않았다. 실제 운영 정책541개 hash는 동일하다.

## 2. 변경과 리뷰 보완

| 발견 | 수정·검증 |
|---|---|
| 등록 VWAP 생성기 학습/후단과 publisher의80% 보존 | 삭제. 30/10 지원수·50% 노출·raw 승률 개선·보정승률5pp 조건 유지. 성공75%만 남기는 개선 후보가 통과하는 생성기/검증기 회귀 |
| 별도 기계 refinement의100% 보존·회수 성공 우선 | `full_population_winrate_priority_v8`: 전체 집단 승률/표본 보정 순위, 학습·후단 raw 승률 개선. 회수 성공0이라는 이유로 순수 실패 회피 후보를 제외하지 않음. 미평가 ENTER 변경·catastrophic guard 유지 |
| 보조 PASS 성공 제외0·EV 우선 | `train_top1_frozen_winrate_improvement_v5`: 학습 동결과 후단 승률 개선. 성공 제외·EV 감소를 진단으로 보고. 비용·원응답·VETO 지원·원천 gate 유지 |
| 목적 변경 뒤 구 frozen 선택 재사용 | 보조 v5 동결 파일/영수증/각 scope에 version 결합. 이전 version 혼합 거부. 기계 selection version으로 기존 checkpoint와 구분. 이전 immutable 발행 계약 읽기는 별도 보존 |
| 등록 경로의 trace→기회 fallback | 10/2 이후 successor는 `opportunity_identity()`의 native scanner/fixed-watch 계보만 소비. 결손을 별도 제외하고 반복 시도를 같은 기회로 묶음. `winrate_native_improvement_without_winner_retention_v3`와 publisher identity 계약 검사 추가 |
| 실제 로그 대조의 naive KST clock·문자열 boolean | 격리 분석 harness에서 producer의 시각/`"False"` 표기를 정규화. 시도 exact match와 앞뒤120초를 분리. 로그 부재로 broker flat을 증명하지 않음 |

producer·publisher·health·동결 선택·재개 경로를 반복 검토했다. v7의 역사적 영수증 검증에 남은 보존 조건은 새 후보 선택 경로가 아니며, 새 v7 후보 발행으로 우회할 수 없다.

## 3. 동일 보유 원천의 실제 생성기 결과

원천: 9/29·9/30·10/2 `machine_observation_projection_*_0_1.json`, KRX 정규7,069행. 세 실행의 파일 SHA가 일치한다. 보조는 기존 full-cost 결합 `reviewed-final/auxiliary-population.json`을 그대로 사용했다. 새 응답이나 label을 생산하지 않았다.

### 3.1 등록 VWAP 생성기: 중간 선택과 최종 보완을 구분

| 단계 | 결과 |
|---|---|
| 변경 전 | 비용/경로 적격2,975시도, 8개 threshold 평가, 승계. 28.73bp는 학습에서80% 성공 보존 조건만 실패 |
| 보존 제약 제거 직후 | 28.73bp 선택. 학습89/109→56/63(81.65→88.89%), 후단14/19→10/11(73.68→90.91%). 학습 성공33·실패13, 후단 성공4·실패4 제외 |
| 추가 source 리뷰 | 위 선택 집단의 실제 native 지원은 학습9기회·후단0기회. 다수 시도가 trace fallback 집계였다. 이 중간 결과를 live 후보로 승인할 수 없음 |
| **최종 native 보완** | 비용/경로 적격 중 계보 없는2,876행 제외,99시도 소비. 등록9개 threshold 평가, 정식 선택0·기존 정책 승계 |

최종 incumbent의 선택 집단은 학습17기회(14승,82.35%), 후단1기회(1승)다. 예를 들어44.71bp 후보는 학습11/11로 개선되지만 최소30기회에 미달한다. **실패 이유는 성공 보존율이 아니다.** 후단1기회의100%는 성능 확증이 아니며10기회 지원수에도 미달한다.

중간28.73bp의 비용 차감 경로 평균은 학습 −0.102528→−0.023930%, 후단 −0.198521→+0.002418%였다. 실제 체결 순이익이 아니며, native 분모 보완 전의 관측 결과다. 10/2는 이미 연구에 재사용했으므로 pristine holdout이라고 부르지 않는다.

### 3.2 별도 기계 refinement

같은7,069행으로 이전89개·수정88개 후보를 평가했다. 목적 version이 탐색 seed/domain에 포함되어 일부 벡터가 달라졌고, 두 실행 모두96개 budget cursor를 완료했다. 같은 후보 집합이라고 가정하지 않았다. native 시간순 split은 학습150·후단25기회이며 binary 성과를 평가할 수 없는 행도 source 진단에 남긴다.

`structural_positive_slopes=2` 후보(`f7fedc8c…58b01`)는 학습 승률82.35→86.67%(기회17→15), 보정승률63.10→66.64%, 경로 평균 −0.088447→−0.039460%로 개선된다. 성공 보존율92.86%는 새 기준에서 탈락 사유가 아니다. 그러나 기존 ENTER 변경4건이 미평가다:

- 9/29 삼화콘덴서 코드 `001820`: 미도달.
- 9/29 삼성전자 `005930`: 늦은 stop 검열1·미도달1.
- 9/30 SK하이닉스 `000660`: 미도달.

정식 생성기는 이 미평가 변경을0손실이나 실패 회피로 대체하지 않아 선택을 보류했다. 이 후보를 후단에서 다시 골라 공식 승격했다고 보고하지 않는다.

### 3.3 실제 보조 stage

| 집단 | 학습/후단 full-cost 비교 | 후보 조합 | 행동 변화 | 결과 |
|---|---:|---:|---:|---|
| KRX 전체 |10/9|12|0|승계|
| 삼성전자 KRX |3/1|6|0|승계|
| 삼성전자 외 KRX |7/8|12|0|승계|

보유 응답으로 등록된 soft policy 조합은 PASS/CAUTION 등 행동을 바꾸지 않았다. 보조의 `auxiliary_stage_net` 고정 경로·full-cost 비교와 앞선10분 연구의 별도 horizon 통계는 같은 승률로 합치지 않는다. 원응답이 없는 prompt 변형을 새로 호출하거나 성공으로 채우지 않았다. 합성 회귀에서는 성공2건을 제외하고 EV가 낮아져도 학습·후단 승률50→100%인 후보가 선택되므로100% 보존 제약 제거 자체는 검증됐다.

## 4. 우선순위3: 두 기계 후보 실행 가능성

### 삼성 조기 확인2건

원본 pipeline2일에서 삼성 이벤트183,576건을 대조했다. exact 평가 시도는9/30 5이벤트·10/2 7이벤트에 연결됐다. 각 후보 앞뒤120초46/63이벤트도 별도 확인했다.

| 후보 시각(KST) | 실제 기록 | 원천/주문 결론 |
|---|---|---|
|9/30 09:06:21, record48997|RECHECK→WAIT/OBSERVE_ONLY, `actual_order_submitted=False`|`exact_broker_capacity_missing`, 세부 `capacity_observation_cache_miss_nonentry`. 당시 exact 용량을 사후 추정할 수 없음|
|10/2 09:43:06, record49036|RECHECK→WAIT/OBSERVE_ONLY, `actual_order_submitted=False`|`unsupported_pre_ai_probe_reservation_scope`. 연구 후보의 실행 재생을 뒷받침할 보유 plan 원천 부족|

`order_owner_registry.jsonl`도 대조했다. 10/2 Widget의 별도 NXT10주 포지션은09:24:37 매도10주 fill과 ORDER_TERMINAL이 있어09:43 후보 시점까지 미청산이었다고 볼 근거는 없다. 이 Widget 이력을 Main의 주문·fill 증거로 전용하지 않는다. 9/30은 해당 일 삼성 Main 주문 binding이 확인되지 않았으며, registry 부재는 계좌 전체가 flat했다는 증명이 아니다. 두 후보 모두 정확한 보조 응답·후단 운영 계획/용량이 없어 **가격 패턴 관측만 유효하고 실행 가능성은 미입증**이다.

### 삼성전자 외 필터

`GE_10BP AND fillability_score <79`의10/2 변경은23건이다. 평가 가능6건은 성공3·실패3이며 **모두 native ID가 없다**. 나머지17건은 미도달12·늦은 stop 검열2·경로 결손3이다. native가 있는5건은 모두 이 미평가 집단이다:

`006400` 미도달, `028050` 경로 결손, `047050` 늦은 stop 검열, `108490` 미도달, `373220` 미도달.

따라서 과거 equal-symbol-day 승률73.53→86.36%를 native 기회 정책의 승률 개선으로 전환할 수 없다. 후속 계획은 **기존 보유 원천에서 exact 시도→scanner/fixed-watch 계보를 복원할 수 있는 행을 먼저 확인**하는 것이다. 복원 불가능한 행에 synthetic ID를 만들거나 미도달을 실패로 바꾸지 않는다. 새 원천 수집은 이번 계획의 요구사항이 아니다.

## 5. publisher·성능·검증

- 실제 publisher를 **복제한 tmp data root**에서 호출했다. trace fallback 기반 중간 v2 보고서는 `winrate_stage_source_invalid`로 거부. 최종 v3 보고서는 `existing_incumbent_preserved`로 처리됐고10/6 기존 정책 hash를 보존했다. canonical 경로의 발행이 아니다.
- 변경 전 등록 생성229.88초, 보존 조건 제거 후214.96초, native 보완 후39.12초. 마지막 실행은 별도 refinement를 생략했으므로 전체 실행시간끼리 비교하지 않는다. 동일 raw SHA에서 불필요한 비native replay를 줄인 단일 관측이며, 병행 작업이 있었으므로 엄밀한 벤치마크가 아니다.
- 통합17개 test module **1,460 PASS**, 후속 native 회귀320 PASS, 최종 영향 회귀 **411 PASS**. 합산해 서로 다른 test 개수로 보고하지 않는다. pandas의 기존 Copy-on-Write deprecation warning1건.
- 변경 작업본 Python34개 compile·`git diff --check`·문서50개 링크 검사·print-only parser PASS. 기존 OPEN23개와10/6 자연 owner가 유지된다. baseline README/runbook/Plan Rebase/prompt/AGENTS는 수정하지 않았고 외부 sync도 실행하지 않았다.
- 기존 source/연구 작업본을 보존하고 이번 수정 경로만 통합 manifest에 표시한다. 운영 정책541개 hash, 세 원천 SHA 및 보조 원천 SHA를 확인한다. 배포·재기동 대기와10/6 자연 수용 owner는 유지한다.

리뷰 범위의 잔여 코드 결함은 확인되지 않았다. 남은 native 계보·미평가 변경·실행 원천·지원수 부족은 보고서에 명시한 정책 선정/실행성 제약이다. 다른 정책군의 계획 항목을 구현 완료로 간주하지 않는다.

## 6. 증거와 남은 구현계획

증거 디렉터리: `tmp/postclose-winrate-selection-migration-20261003/`.

- `before-*`: 실제 이전 생성기 기준선.
- `after-*`: 성공 보존 제약 제거 직후. **등록 중간 선택은 native 결함 보완으로 승격 효력이 없다.** 별도 refinement 결과는 해당 generator 변경 기준으로 유효하다.
- `final-winrate.json`, `final-auxiliary.json`: 최종 원천/목적 계약의 결과.
- `publisher-verification.json`, `promising-machine-diagnostic.json`, `feasibility-compact.json`: 발행 거부/승계, 유망 후보 결손, 실제 시도·주문 owner 대조.
- `tests-integrated.txt`, `tests-final.txt`, `closure-receipt.json`, `commit-preparation.json`: 회귀·불변성·통합 준비.

전체 정책에 대한 후속 구현 범위는 계획의 정책군 표를 따른다. 특히 Entry split의 `min(individual_delta)-error>0`, Initial quantity의 모든 날짜 비음수 조건은 전체 개선 후보를 막는지 별도 검증할 대상으로 남긴다. 이것들은100% 성공 보존율과 동일하지 않으므로 이번에 자동 완화하지 않았다. 공통 비교 증거/version, 기존 자료의 정확한 계보 복원, 분할·수량의 암묵 개별 성과 제약 재설계가 다음 실행 단위다.
