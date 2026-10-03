# 기계·보조 AI 보유 원천 심화 연구 계획 (2026-10-03)

## 목적과 실행 경계

이전 11520개 정책 재생의 회수0과 보조 필터의 음수 CF 결과에서 출발한다. 사용자 요청에 따라 보유 데이터의 활용 범위와 가설 표현을 심화한다. 새 원천 수집이나 provider 호출 없이 9/29·9/30·10/2의 동결 관측·원 응답·가격 경로를 재사용한다. 정책 생성 문법, 시장의 방향 패턴, 확인 시점과 가격의 관계를 검증하고 실행 가능한 후속 연구안을 남긴다. 신규 코드·정책 배포 대기는 유지한다.

소유자는 오늘 checklist의 `DeepRetainedSourceResearch1003`이다. 이전 [연구 결과](../audits/main-machine-auxiliary-retained-source-hypothesis-research-review-2026-10-03.md)는 비교 기준으로 보존한다.

## 사전 고정 가설과 검증

| ID | 연구 질문 | 계산과 판정 |
|---|---|---|
| D1 | 원천 결손과 현재 확인 규칙 중 무엇이 회수0을 만드는가? | native99행에 parent 및 기존 복합 profile를 재생하고 원천, hard/source BLOCK, local breakout, 보상 불가 fact, micro 확인의 잔여 조건을 연결한다. 소스값·risk fact를 임의로 삭제하지 않는다. |
| D2 | 제외된2877행에도 유효한 관측 패턴이 있는가? | 기회 lineage 없이도 hash/cost/가격 관측이 유효한 행을 관측용으로 사용한다. 종목·날짜별 시간 간격을 두고 첫 관측을 선택하고 종목·날짜별 동일 가중도 비교한다. 관측 anchor를 native 기회로 재명명하지 않는다. |
| D3 | 단일 변동성 조건보다 유형·가격 반응·flow 상호작용이 유효한가? | 사전에 정한 숫자 feature의 학습 quartile/중앙값과 유형 조건, 두 조건 AND를 비교한다. 조건 생성은 학습 feature만 사용한다. 행동 vector 중복을 제거하고 동결 budget 안에서 결정론적으로 탐색한다. |
| D4 | 목표-first 비율과 수익의 불일치가 있는가? | 목표/손절의 비용 차감 보상 구조, 손익분기 승률, 고정 시점 CF 경로를 같이 계산한다. Main의 승인된 binary rank를 바꾸지 않으며 actual PnL로 해석하지 않는다. |
| D5 | 확인을 기다리는 시간이 가격상 이득인가? | 기존1/3/5/10분 가격 중 동일 관측 집합에서 즉시와1분/3분 지연의 return-minus-recorded-cost를 비교한다. 지연 시점에 알 수 있는 값만 조건에 사용한다. 재진입·호가·체결·guard 통과는 미입증으로 표시한다. |
| D6 | 보조 AI의 손실 감소가 여러 시간·날짜에서도 유지되는가? | 기존 응답의 PASS를 유지/CAUTION하는 유형·수치·AND 조건을 비교하되, 10분 최대 개선과 3/5/10분 최저 평균 기준의 선택을 따로 한다. 성공 제외·선택률·남은 PASS 평균·동일 모수 CF를 전부 보고한다. |
| D7 | 탐색 과적합과 특정 종목 의존이 큰가? | 9/29만 학습→9/30, 9/29+30→10/2의 시간순 재선정, 종목 제외 재학습, 고정 후보의 종목·날짜 민감도를 계산한다. 가능한 비교에서 label permutation의 최대 탐색 개선과 대조한다. 이미 관찰한 날짜는 독립 미사용 holdout이 아니다. |
| D8 | `evaluable` 행에 한정한 표본 선택이 낮은 변동성의 성과를 부풀리는가? | 리뷰에서 기존 `_0_0` cache의 미도달 제외를 확인했다. 이미 저장된 `_0_1` 전체 관측 cache를 한 번 투영해 기존 조건을 고정 적용하고 전체 선택 수·미도달·가격 결손을 함께 센다. 고정 시점 가격이 있는 미도달 행까지 포함한 학습 전용 재선정을 별도 실행한다. 기존 승률에 미도달을 성공/실패로 임의 대입하지 않는다. |
| D9 | 전체 모수의 지지 기준이 작은 유형의 유효한 가설을 지우는가? | 전체 관측의 predecision 구조 phase별로 별도 학습한다. 학습30관측·5종목 이상인 셀에서 최소 `max(5, ceil(0.1*셀 학습 수))` 지지로 동일 숫자/AND 후보를 비교한다. 10분 및3/5/10분 최저 평균 기준을 적용하고 날짜별 재선정·후단 선택률·성공 제외를 기록한다. 희소 phase는 미지원이며 종목 자체를 조건으로 학습하지 않는다. |

숫자 feature는 원래 결정 시점의 가격·변동성·tick·spread·fillability·flow·VWAP/MA 거리·volume·depth와 유형에 한정한다. 사후 가격, target/stop 결과, 최종 액션, 미래의 source 품질을 feature로 넣지 않는다. micro 사용 불가 및 비유한 값은 unknown으로 남긴다. 새로운 결합 feature는 원값과 단위를 명시한다.

숫자 경계와 유형은 학습에서만 생성한다. 주어진 학습 집합에서 최대8000개 고유 조건 행동 vector, 단일/AND 최대 두 조건, 관측 지지 최소5개를 사용한다. 넓은 관측 집합은 최소10개 및 학습 모수의10% 지지를 요구하며 D9는 명시한 phase 내부 모수를 사용한다. 표본 수 기준은 연구의 안정성 표시이며 기존 family 승격 기준을 교체하지 않는다. 후보는 학습 결과로만 선택하고 후단은 이후 평가한다. 결과를 보고 날짜·조건·budget을 재배분하지 않는다.

보조 AI의 원문/soft-policy 재현은 기존 sealed 연구 자료를 사용한다. 추가 feature는 exact request·symbol·time·policy 세대가 일치하는 기존 원천에만 연결한다. 응답 INVALID와 미관측 prompt 변경은 연구 적격 PASS로 바꾸지 않는다.

## 구현과 완료 기준

1. 역할 위치는 기존 offline 연구 옆 `src/engine/scalping/entry_policy_deep_research.py`, 회귀는 `src/tests/test_entry_policy_deep_research.py`다. live loader/자동화 등록은 없다.
2. 출력은 `tmp/deep-retained-policy-research-20261003/`에 제한한다. 입력 파일·기존 연구·현재 코드/kernel SHA를 동결하고 source/정책 파일 불변을 확인한다. 원천은 한 번 투영하고 이후 작은 연구 cache를 재사용한다.
3. source/hash·시간 간격·first-observation·미지값·미래 label 배제·학습 전용 경계·순차 재학습·비용/지연 수식에 회귀를 둔다.
4. 구현→자체 리뷰→보완→재리뷰→targeted pytest/compile/diff 후 실제 자료에서 실행한다. 결과가 약하거나 모순돼도 동일 기준으로 보고한다.
5. 상세 audit에 가설별 결과·분모·모든 부작용·불가 원인·후속 코드 연구의 구체적인 owner와 확인 조건을 기록한다. 문서 parser만 실행하고 Project/Calendar 외부 동기화는 수행하지 않는다.

metric contract: `metric_role=diagnostic_research`, `decision_authority=offline_only`, `window_policy=frozen_20260929_20261002`, `sample_floor=explicit_research_support`, `primary_decision_metric=cost_bound_direction_and_fixed_horizon_cf`, `source_quality_gate=retained_hash_bound_scope_cost_and_predecision_features`, `forbidden_uses=live_promotion,actual_profit_claim,synthetic_native_identity,hard_safety_relaxation,provider_or_order_authority`.
