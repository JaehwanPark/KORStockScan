# 보유 원천 기반 기계·보조 AI 가설 확대 및 정책 재생성 계획 (2026-10-03)

## 요청과 범위

사용자 요청은 원천 수집 확대가 아니라 **보유 원천에서 더 많은 가설을 검증**하는 것이다. 9/29·9/30·10/2의 동결 source만 사용한다. 기존 보완 diff를 보존하고 연구 코드는 격리 offline 모듈에 둔다. live 정책·원천 producer·수집 주기·provider·주문·재기동을 변경하지 않는다. 신규 변경의 배포 대기는 유지한다.

관련 진단: [BLOCK 패턴·탐색 범위](../audits/main-machine-block-pattern-search-diagnosis-2026-10-03.md), [기존 원천 보완](../audits/main-machine-auxiliary-source-remediation-review-2026-10-03.md). 실행 소유자는 오늘 checklist의 `RetainedSourceHypothesisResearch1003`이다. 기존 10/6 자연 수용 항목을 연구 완료로 닫지 않는다.

## 원천·검증 동결

- Main: 기존 machine observation projection 3개 SHA, 2976 KRX/REGULAR 관측. native 기회 적격99행은 정책 재생에 사용하고 나머지는 비승격 유형·차단 진단에 사용한다. fake admission을 만들지 않는다.
- Auxiliary: compact frozen source 3개/59행, 기존 raw response·sanitized input·원래 machine/prompt/soft-policy hash. native watch metadata는 exact trace request/payload/time/stock/bundle/scope에 연결된 기존 원천만 사용한다. archive의 물리 세대 차이는 기록하고 승격 증거로 대체하지 않는다.
- 기존 날짜별 AI outcome label에서 이미 저장된 horizon 경로를 사용한다. 고정 시점 CF는 원래 reference 기준 return minus recorded cost이며 actual exit/stop EV가 아니다. request/stock/time/bundle/scope/label generation을 확인한다. label 결손은 유지한다.
- 학습: 9/29·9/30, 후단 날짜 진단: 10/2. 기존 chronological opportunity purge를 재사용한다. 10/2는 이미 열람한 자료이므로 미사용 독립 holdout이라고 주장하지 않는다. 추가 source 확보를 이번 완료 조건으로 넣지 않는다.
- 후보/조건/budget/평가지표를 학습 전 source hash와 함께 동결한다. 유형·숫자 경계는 predecision 학습 feature로만 만든다. 결과가 좋은 셀을 보고 새 유형을 추가하지 않는다.

## 기계판정 가설

| ID | 가설 | 재생 방법 | 확인 결과 |
|---|---|---|---|
| M1 | 단일 좌표의 최소 변경만으로는 복합 차단이 남는다 | 기존82좌표의 양방향/edge 값과 명시적인 2~여러 좌표 template를 재생 | ENTER 회수·실패 회수·원래 승자 손실·끝까지 남는 차단 |
| M2 | 전역 profile가 유형별 이질성을 평균낸다 | 학습 predecision phase/family/liquidity 및 두 축 그룹 안에서만 동일 profile 적용 | 전역 대 유형별 CF 회수와 분모/종목 편중 |
| M3 | 기존 recovery budget가 숫자 leaf를 탐색하지 않는다 | 학습 tercile selector 각각에 profile 변경을 적용; 기존 canonical tree 표현 가능성 검증 | 새 분기의 효과 및 미지원 범주 dispatch 구분 |
| M4 | 즉시 판정만으로 재확인 기회를 놓친다 | 같은 native 기회 안의 시간순 snapshot에서 최초 non-entry→fresh ENTER 전이를 대조 | 늦은 자연 ENTER 유무; 원래 시점 상승과 후속 진입 경로 분리 |
| M5 | 상승 사례가 동일 종목·retry에 집중돼 있다 | 기회 동일 가중, 날짜별·leave-one-symbol-out 민감도와 overlap 기록 | 반복 횟수를 성공 표본으로 늘리지 않는 검증 |
| M6 | 상승 방향을 예측하는 유형과 현재 ENTER 규칙이 다르다 | 같은 학습 predecision mask로 비용 결속 target-first 예측을 비교 | 패턴 예측과 실제 guard 통과를 분리; 새 진입 허가로 해석하지 않음 |

profile vector는 기존 `mechanistic_entry_policy_decision`으로 계산한다. 조건부 가설은 그 결과를 predecision mask로 선택한다. source-unusable/하드 veto를 보상하거나 풀지 않는다. 범주 dispatch는 offline 연구 표현이며 기존 runtime policy 형식으로 승격 가능한 후보와 구분한다.

budget는 최대240개 고유 machine profile, profile별 전역/학습 숫자 selector/학습 유형 mask, 최대16000개 조건부 가설이다. 작은 셀은 독립 기회5 미만이면 별도 profile를 학습하지 않고 부모를 사용한다. 계산 순서는 predecision/registry에서 정하고 결과별 budget 재배분은 하지 않는다. 전체 공간 최적임을 주장하지 않는다.

Main primary rank는 현재 비용 결속 binary target-first 및 기존 recovery rank를 재사용한다. CF net-path·기존 승자 보존·빈도는 함께 보고한다. train-only research selection 뒤 10/2를 진단하고 기존 publisher gate와 미사용 holdout 부재를 각각 표시한다. 변화 없는 결과도 실제 수행한 가설 수/행동 변화/원인과 함께 닫는다.

## 보조 AI 연구 재설계

| ID | 가설 | 보유 원천에서의 검증 | 권한·한계 |
|---|---|---|---|
| A1 | 기존 stop/path 제외로 응답 연구까지 지나치게 축소됐다 | valid raw response census와 fixed-horizon1/3/5/10m를 분리 | 새 stop·체결·원금/owner EV를 만들지 않음 |
| A2 | evidence count의1~3단일 그리드가 약한 PASS를 구분하지 못한다 | 기존 v1 그리드와 v2 materiality quantile/경계 및 두 soft-risk 축 조합 | 검증된 citation과 현재 hard-risk composition 유지 |
| A3 | soft-risk 중요도는 유형별로 다르다 | phase/liquidity/volatility/tick 및 두 축 leaf; 소표본 부모 fallback | 같은 machine/prompt/soft-policy 세대별로 연구; 미관측 VETO 축은 적격 수리로 주장하지 않음 |
| A4 | 유효한 PASS가 가격 경로상 손실을 충분히 걸러내지 못한다 | false-PASS 경로, positive evidence·adverse fact·materiality와 선택률/승자 손실 대조 | 사후 가격을 AI 입력·조건에 섞지 않음 |
| A5 | prompt 변경이 soft-policy 변경보다 유효하다 | 보유 exact prompt-variant 응답이 있을 때만 paired 비교 | 없는 변형 응답은 unsupported; 기존 응답을 새 prompt 답변으로 재명명하지 않음 |

maximum6000 soft-policy 가설을 생성한다. 기존 validate/repair/evaluate 함수를 재사용하고 응답 원문은 보존한다. semantic/transport INVALID는 PASS/VETO로 바꾸지 않는다. 주요 EV family의 기존 경제성 gate를 승률로 대체하지 않는다. fixed-horizon 진단은 mean CF return·PASS 손실·정상 성공 제외·coverage와 여러 horizon 방향 일관성을 보고한다. canonical 재생 결과와 진단 후보를 별도로 보존한다.

A4는 현행 policy의 evidence-count1~3 범위만 반복하지 않는다. 학습 predecision micro/tail/materiality/정확 숫자 confidence·citation count의 tercile, 유형, 두 조건 조합을 사용한 `PASS→CAUTION` 진단도 최대1000개 수행한다. native 독립 기회5 미만 조건은 부모로 돌아간다. 기존 soft-policy schema 밖의 조건은 `offline_feature_filter_not_registered_policy`로 발행하고 실제 AI의 답변 변경이나 새로운 binding risk로 주장하지 않는다. 변경 없음/후단 손실/승자 손실을 함께 확인한다. 실제 CAUTION 후속 경로가 없어 immediate CF와 최종 non-entry를 동일시하지 않는다.

9/29만으로 조건과 candidate를 다시 선택해 9/30에 대조하는 chronological reselection도 보유 자료 안에서 수행한다. 기존 candidate를 고정한 leave-one-symbol-out 민감도와, 학습 날짜를 바꿔 다시 고른 결과는 다른 검증으로 보고한다. 작은 표본과 여러 가설의 탐색 이력을 숨기지 않는다.

보조 AI prompt의 후속 연구 초안은 다음 영어 지침을 검토한다. 아직 prompt version/schema에 등록하거나 배포한 것이 아니며 기존 답변으로 변화 효과를 입증할 수 없다.

```text
Judge soft-risk materiality from exact predecision facts and their units.
Do not count correlated citations as independent confirmation.
Do not interpret absolute aggressive trade quantity as proportional strength.
Explain conflicts between price response, tick cost and aggressive flow.
Keep machine, source and hard-risk vetoes binding.
```

## 구현·검증·완료 기준

1. 위치: `src/engine/scalping/entry_policy_hypothesis_research.py`. 기존 scalping replay 연구와 같은 offline 역할이며 live loader/publisher/cron의 import는 추가하지 않는다. tests는 `src/tests/test_entry_policy_hypothesis_research.py`다. engine root 새 파일은 없다.
2. 변경 전 manifest/code/input/policy hash, 날짜·scope·sample role을 기록한다. 출력은 전용 `tmp/retained-source-policy-research-20261003/`에 둔다.
3. pure functions에 mask/unknown fallback, train-only 경계, 중복 기회, invalid raw, 정확 horizon binding, type dispatch와 canonical leaf 동등성 회귀를 둔다.
4. self review→수정→재리뷰→pytest/compile/diff PASS 뒤 실제 retained source로 재생성한다. 진행 중 code SHA가 바뀐 결과는 수용하지 않는다.
5. 가설 수·고유 행동 vector·행동 변화·회수/누락·후단 날짜·종목 민감도·CF/actual 구분·wall/RSS를 보고한다. 후보가 없으면 최초 실패 조건을 명시한다. 정책/prompt/가격/주문 안전의 변경을 가설 확대라는 이유로 숨기지 않는다.
6. 결과 audit와 오늘 checklist를 닫고 print-only parser를 실행한다. 거래 정책 배포/재기동은 별도 지시를 기다린다.

연구 metric contract: `metric_role=diagnostic_research`, `decision_authority=offline_only`, `window_policy=frozen_20260929_20261002`, `sample_floor=family_gate_or_explicit_sparse_diagnostic`, `primary_decision_metric=main_cost_bound_target_first_or_auxiliary_cf_diagnostic`, `source_quality_gate=exact_native_frozen_scope_and_response`, `forbidden_uses=live_promotion,actual_profit_claim,hard_safety_relaxation,provider_or_order_authority`.
