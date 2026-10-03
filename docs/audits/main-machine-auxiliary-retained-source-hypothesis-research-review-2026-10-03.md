# 보유 원천 기계·보조 AI 가설 확대 재생성 리뷰 (2026-10-03)

## 판정

**상승 방향을 구분하는 가설과 보조 PASS의 손실을 일부 거르는 가설을 확인했다. 현재 정책 승격은0이다.** 기계의 기존 action grammar 안에서는 가설을 크게 늘려도 비진입→ENTER 회수0이었다. 이를 상승 패턴 부재로 해석하지 않는다. 보조 AI는 기존 soft-policy 그리드의 포화와 feature/유형 조건의 다른 효과를 확인했다.

소유 계획: [상세 연구계획](../proposals/main-machine-auxiliary-retained-source-hypothesis-research-plan-2026-10-03.md). 코드: `src/engine/scalping/entry_policy_hypothesis_research.py`. 실행 산출물: `tmp/retained-source-policy-research-20261003/`. source 수집 확대·provider/broker 호출·canonical 정책 변경·배포·재기동0이다. 기존541개 runtime policy/override/bootstrap SHA도 불변이다.

## 동결 원천과 검증의 역할

- Main 3일 cache KRX2976행, native 적격99행: 학습71시도/59기회, 후단28시도/10기회. 제외행을 가짜 기회로 편입하지 않았다.
- Auxiliary frozen3개/59행. exact retained trace로 watch metadata7행을 진단 복구했고 원문/파일을 바꾸지 않았다. 9/29 압축 archive의 물리 세대 차이를 live 재봉인으로 대체하지 않았다.
- 유효 독립 보조 응답45행: 자연 응답 invalid13, 동일기회 중복1 제외. KRX 학습34/후단9, 통합 AFTER 학습1/후단1은 별도 세대다.
- 9/29·9/30에서 학습하고 10/2를 진단했다. 10/2는 이미 관찰한 자료여서 새 미사용 holdout이 아니다. 별도로9/29 재선정→9/30 및 고정 후보의 leave-one-symbol-out를 확인했다. 신규 원천 확보를 이번 완료 조건으로 요구하지 않는다.
- 비용 결속 target-first, 고정 시점 return-minus-recorded-cost, 기존 fixed target/adverse path는 다른 estimand다. actual fill·실제 stop/holding owner·전체 비용/원금/최종 CAUTION 후속 경로 증거로 교체하지 않는다.

## 1. 기계판정 정책 재생성

| 항목 | 결과 |
|---|---:|
| 고유 profile | 240 |
| 전역/숫자/유형별 조건 | 48 |
| 비교 가설 | **11520** |
| 고유 행동 vector | 209 |
| 학습 행동이 바뀐 가설 | 1124 |
| 비진입→ENTER 회수 기회 최대 | **0** |
| 회수 적격 가설/선정 정책 | **0 / 0** |
| profile 재생 오류 | 0 |

각 profile는 기존 production decision kernel로 계산했고 조건부 vector는 그 결과를 predecision mask로 선택했다. 원래 성공 진입을 잃는 후보는 적격으로 선택하지 않았다. 숫자 분기 대표는 실제 canonical leaf로 재생해 mask와 일치함을 검증했다. 범주 dispatch는 offline 연구 형식으로 남겼다. 대표 canonical 후보는 기존 publisher gate에서도 회수/기존 성공 보존/후단 조건을 통과하지 못했다.

같은 native 기회 중 최초 non-entry인51개를 시간순 대조했지만 후속 parent ENTER 관측은0이다. 이는51개가 실제 영구 non-entry였다는 증거가 아니다. 원천의 해당 기회 안에서 관측하지 못한 상태다.

성공한 학습 비진입38시도의 당시 micro 상태를 서로 겹치지 않게 나누면 `source_usable≠true`9, usable이고 가격 비양수/미확인20, usable·가격 양수이나 delta 비양수/미확인3, usable·가격/delta 모두 양수6이다. 마지막6 중 local-breakout 확인2, MICRO_PRICE_RESPONSE4가 남았다. [기존 BLOCK census](../../tmp/main-machine-auxiliary-source-remediation-20261003/block-pattern-census.json)에서 원값과 복합 risk assessment를 확인할 수 있다. 단일 가격/flow 조건을 만족해도 setup/복합 확인·차단이 남을 수 있다.

## 2. 방향 패턴 가설은 확인됨

같은 predecision 조건47개로 **비용 결속 target-first 방향 예측**을 연구했다. ENTER 권한을 만들지 않는 별도 classifier 진단이다. 학습 보정 score 최대 조건은 `volatility_pct < 0.2665726771056661`이었다.

| 모수 | 독립 기회 | 기회 동일 가중 target-first | 보정 ranking score |
|---|---:|---:|---:|
| 학습 전체 | 59 | 72.4576% | 62.0670 |
| 학습 조건 일치 | 35 | **87.8571%** | 75.9794 |
| 10/2 전체 | 10 | 78.4211% | 52.4447 |
| 10/2 조건 일치 | 8 | **85.5263%** | 56.7123 |

조건 안에는 학습 비진입 성공34시도·10/2 비진입 성공21시도가 남는다. 수치는 retry별 성공률 대신 기회별 시도 binary 평균을 다시 동일 가중한 값이다. 보정 score는 Wilson 모양의 순위 penalty로 통계적 우월성/독립 Bernoulli 신뢰구간이 아니다. 여러 가설 탐색과 작은 후단 모수도 남는다.

따라서 “상승을 구분할 신호가 전혀 없다”는 결론은 반박된다. 현행 guard를 통과하는 실행 정책으로 번역됐다는 뜻은 아니다. 같은 원천에서도 패턴 예측, immediate ENTER grammar, 후속 확인 순서를 구분해 연구해야 한다.

## 3. 보조 AI의 원천 활용과 기존 그리드 포화

기존 fixed-path 비교20행을 재현했다. 저장 label의 request/stock/time/bundle/scope/개별 label hash·horizon 성숙을 검증해 고정 시점 관측을 추가 대조했다.

| 고정 시점 | 유효 독립 응답과 결속된 가격 관측 |
|---|---:|
| 1분 | **42** |
| 3분 | 18 |
| 5분 | 17 |
| 10분 | 20 |

모든 horizon의 비교 수가 늘어난 것은 아니다. 1분에서 기존 fixed10m path 밖의 보유 관측을 더 활용했다. 없는 stop/cost/terminal은 생성하지 않았다. source/세대가 다른 AFTER를 KRX에 섞지 않았다.

기존 v1 evidence-count 및 v2 materiality/유형·두 risk 축의 **438개** soft-policy 가설은 각 세대에서 행동 vector1개, changed0이었다. KRX의 citation 수는3~8개로1~3 PASS 최소값 변화가 모두 포화된다. raw VETO가 없어 VETO 완화축을 검증한 것으로 주장하지 않는다. materiality의 실제 근거와 raw citations에 결속되는 current composer를 우회하지 않았다. exact cached prompt-variant 응답0으로 새 prompt 답변 효과는 미검증이다.

## 4. 보조 feature/유형 필터는 다른 결과

관측용 `PASS→CAUTION` feature/유형/두 조건 조합 **648개**를 학습에서 비교했다. 행동 vector481개, changed635개다. 기존 등록 policy 형식과 구분하며 CAUTION의 후속 재확인/재진입이 replay된 것으로 주장하지 않는다.

10분 학습 기준 연구 선택 조건:

```text
micro:net_aggressive_delta_10t >= 120
AND price_tick_band == GE_10BP
=> diagnostic PASS to CAUTION
```

120은 학습에서 생성한 경계이며 보편적 매수 강도/절대 거래량 threshold가 아니다. 실제 AI 원문은 그대로 두었다.

| 10분 고정 시점 진단 | 학습9/29~30 | 후단10/2 |
|---|---:|---:|
| 비교 기회 | 10 | 9 |
| 기존 PASS / 필터 후 PASS | 10 / 5 | 9 / 6 |
| 손실 PASS | 7→2 | 7→4 |
| 성공 PASS 제외 | 0 | 0 |
| 기존 PASS mean CF net | −0.246255% | −0.127663% |
| 필터 후 PASS mean CF net | −0.062188% | −0.066175% |
| 동일 모수 immediate CF 평균 차이 | +0.215161%p | +0.083546%p |

이는 CF 관측에서 손실 노출을 일부 줄이는 가설이다. **필터 후 평균도 음수**며 실제 기대수익/원금 할당/최종 실행 개선이 아니다. 전 비용 valid0은 유지된다. 후보를 live로 선정하지 않았다.

민감도:

- 학습에서 한 종목씩 제외한 고정 후보의 immediate CF 차이는 +0.182529~+0.239068%p다. 제외 후 후보를 새로 학습한 nested 검증과는 다르다.
- 9/29만으로610개 조건을 다시 탐색했을 때 같은 tick 유형+delta 조합이 선택됐고 경계는105로 바뀌었다. 학습5비교 중 손실2를 CAUTION으로, 9/30의5비교 중 손실3을 CAUTION으로 분류했다. 후단에 남은 PASS2건은 모두 손실이며 평균 −0.500014%다. 작은 표본에서 임계값을 확정할 수 없다.
- 1분 학습에서는 성공 PASS2건을 잃고, 3/5분에는 학습·후단 각각 성공1건을 잃는다. 10분의 성공 보존을 전체 horizon의 성공 보존으로 확대하지 않는다. 3/5분의 후단 PASS 평균은 오히려 더 나빠진다.

보조 AI 연구는 citation 개수의 반복 튜닝보다 **정확한 soft-risk 중요도, tick 비용·flow 크기의 유형별 의미, 손실 PASS와 성공 제외의 horizon 차이**를 비교하는 방향으로 바꾼다. prompt 초안은 계획에 기록했지만 기존 답변으로 새 prompt 성능을 입증하지 않았다.

## 리뷰·보완·검증

처음 auxiliary 고정 시점 hash 비교를 개별 label 대신 report 전체로 수행한 결함을 발견해 수정했다. 이어 horizon 키의 int→JSON string 변환으로 seal hash가 바뀌는 결함을 보완하고 roundtrip 회귀를 추가했다. 가설 budget과 unknown→parent fallback도 검증했다. 결함이 있던 중간 auxiliary 결과는 `intermediate-*`로 보존하며 최종 수용에서 제외한다.

Main phase는 reviewed source snapshot SHA와 3개 cache/parent/kernel에 결속된 실제11520 재생 결과다. auxiliary 후속 보완은 별도 phase code SHA로 재생하고 원 Main source/kernel/hash 일치를 확인했다. 두 phase를 같은 source-code 실행으로 포장하지 않는다. 정확 receipt는 `final-phase-acceptance.json`, 가설 정의/전체 trial/선정/민감도는 해당 JSON에 있다.

실제 Main 포함 최초 실행382.66초, 최대 RSS230048KiB(약225MiB). 최종 보완 auxiliary/classifier phase8.08초다. Main snapshot SHA는 `60b1a96148ea07ed3963f41d9ce137350ea135daa1738a948ec0f74f68526e8f`, 최종 auxiliary code SHA는 `9b9f35111e3917359744f2523d17b8a81491076f5961ef829a44293136c0bb80`이다. 탐색 수와 모수가 다른 기존 계산과 직접 속도 배율을 주장하지 않는다.

신규 source/변환/마스크/invalid/budget/hash 회귀 및 기존 candidate/selector 계약20 PASS(84 deselected), compile/diff/link/print-only parser 확인. live import/publisher 연결0, runtime hash541개 불변, 실제 provider/order/restart/deploy0. 신규 연구 코드는 미커밋·미배포다.

## 완료와 잔여 판정

M1~M6와 A1~A4는 보유 원천 재생·후단·민감도 진단으로 완료한다. A5 새 prompt 비교는 retained exact variant 답변 부재로 unsupported이며 새 수집/AI 호출을 실행하지 않았다. 전체 정책 승격0, actual 경제성 미입증, 기존 정책 유지. 이는 연구 결과0이나 상승 패턴0이 아니다. 자연 수용/PREOPEN의 기존10/6 소유자도 연구 완료로 닫지 않는다.
