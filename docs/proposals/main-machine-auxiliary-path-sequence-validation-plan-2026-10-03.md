# 기계·보조 AI 결과 분류·관측 순서·장기 경로 검증 계획

기준일: 2026-10-03. 실행 소유자: 오늘 checklist의 `PathSequenceValidation1003`.

## 목적과 경계

사용자가 승인한 우선순위에 따라 기존 [심화 연구](main-machine-auxiliary-deep-retained-research-plan-2026-10-03.md)의 다음 검증을 수행한다. 2026-09-29·09-30·10-02의 보유 원천을 사용한다. 이미 여러 번 관찰한 날짜이므로 미사용 독립 holdout이라고 표현하지 않는다. 전체 관측 7069행을 유지하고 실제 native 기회 수와 혼합하지 않는다.

신규 수집·provider 호출·운영 정책 발행·배포·재기동은 수행하지 않는다. Main의 승인된 binary 순위·hard safety와 실제 holding/exit 계약은 그대로 보존한다. 아래 결과 분류 및 수익 비교는 offline 연구의 대조 방식이며 canonical label 교체가 아니다. 이전 미커밋 작업본을 보존한다.

## 우선순위와 완료 조건

| ID | 작업 | 검증과 완료 조건 |
|---|---|---|
| P1 | 평가 결과 분류 분리 | 원래 label을 보존하고 빠른/늦은 목표, 빠른/늦은 손절, 양쪽 미도달, 같은 봉 순서 불명, 관측/비용 결손으로 대조한다. 3분 이후 이익·손실의 비대칭과 기존 분모 변화를 전수 계수한다. 실제 source gap은 결과로 대체하지 않는다. |
| P2 | 과거 관측의 순서 feature | 같은 날짜·종목·정책·정확 가격 route에서 과거 관측만 연결한다. 각 단계 간격 15~180초, 최대 과거360초, 같은 timestamp의 모호한 관측 제외. 기회/체결 재구성으로 주장하지 않는다. 가격 반전, flow 전환, 가격 확인, spread 축소, 구조 전환을 사전 고정 가설로 비교한다. |
| P3 | 저장된 장기 가격 경로 | 기존 1/3/5/10/20/30/60분의 endpoint, MFE, MAE와 비용을 사용한다. MFE는 체결 가능한 수익으로 해석하지 않는다. 종료 시각이15:30을 넘는 행은 horizon별 session censor로 분리하고 결손·미도달은 보존한다. 공통 관측 집합 비교도 발행한다. |
| P4 | 유형 및 날짜 재현성 | 9/29→9/30, 9/29+30→10/2의 시간순 재선정. 사전 가설과 학습에 존재하는 phase 조건만 선택한다. 10분 간격 관측을 기본으로 사용하고60분 간격·하루 첫 관측·종목별 제외 민감도를 계산한다. 선정은 학습만 사용하며 후단 결과로 가설을 추가하지 않는다. |
| P5 | 보조 AI 오류 검증 | 기존 유효 KRX PASS43개와 이미 확인된 exact pre-AI 연결을 사용한다. flow/가격 불일치, 비용 대비 spread/tick 부담, source 사용 가능성의 중요도를 검증한다. 성공 제외, 남은 PASS 평균, 손실 제거, coverage를 함께 계산한다. 새 프롬프트 응답 효과는 unsupported로 남긴다. |

## 사전 고정 연구 설계

- 기계 순서 가설: 가격 반전; 가격 반전+flow 음수→양수; 가격 상승+동시 micro 가격/flow 양수; 가격 반전+spread 비확대; pullback/rebound/range→recovery/continuation 전환+가격 상승; VWAP 재돌파+flow 양수; flow·micro 가격 동시 개선+가격 상승; 매수 압력 개선+spread 축소+가격 상승. 경계는0이며 결과를 본 뒤 quartile/임계값을 추가하지 않는다.
- static 대조군: 같은 관측 연결 적격 집합에서 현재 flow/가격 양수, VWAP 양수, recovery/continuation 여부를 비교한다. 관측 순서의 증분 효과와 현재 상태 효과를 구분한다.
- 목적함수: 각각 단기3/5/10분, 중기10/20/30분, 장기20/30/60분의 종목·날짜 동일 가중 평균 중 최솟값. 모든 요구 horizon에서 학습 비교 가능10행·5종목 이상, 선택 집합의 경제성 자료 coverage80% 이상을 요구한다. phase 추가 분기는 학습30관측·5종목 이상에만 허용한다. 이 조건은 연구 비교의 적격성일 뿐 운영 승격 기준이 아니다.
- 후단에는 선정 조건을 그대로 적용한다. 평균·종목 동일 가중·하위10%·종목 편중·양의 endpoint 제외 수·추가 비용0.05/0.10%p 민감도를 기록한다. horizon별 분모와 공통 horizon 집합의 분모를 모두 보존한다.
- 순서 연결 및 관측 간격 선택은 사후 label·가격 경로·비용 유무를 보지 않는다. 같은 시각의 미래 결과를 feature로 사용하지 않는다. 필터가 고르는 행 자체에 source gap이 있어도 전체 선택 수에 남긴다.
- 보조 AI 가설은 현재 flow 양수인데 micro 가격 비양수, 큰 매수 비중인데 가격 비양수, spread가 tick보다 큰 상태와 가격 비양수, flow 악화와 spread 확대의 결합이다. 단위가 다른 raw delta 절대값을 공통 강도 기준으로 사용하지 않는다. unknown은 기존 PASS를 유지한다. 학습에서 성공 제외0인 조건을 우선 검토하고 후단에서도 같은 지표를 모두 보고한다.

## 구현 위치와 증거

### 순서 원천 coverage 보완 (분봉 단계 계산 전 고정)

첫 snapshot 단계는 전체7069 중1684행에만 과거 관측을 연결했다. 날짜별로9/29 1498행,9/30 54행,10/2 132행이며 기본 관측 anchor는397/31/47이다. 이 차이는 순서 비교의 원천 범위 제약이다. 이 단계 결과·코드·protocol을 그대로 보존하고, 이미 저장된 동일 route의 완료 분봉으로 과거 가격 순서를 만드는 별도 단계를 추가한다. snapshot 가설의 후단 성과를 보고 경계를 튜닝하지 않는다.

분봉 feature는 판정 시각보다 최소60초 이전 timestamp를 가진 마지막6개 봉을 사용한다. 마지막 봉 timestamp+60초와 판정 사이90초 이내, 인접 봉 간격90초 이내, 날짜·venue/session·정확 request code·completed/source quality 일치를 요구한다. 중복 timestamp는 해당 window를 제외한다. 원래 provider의 봉 시각을 새롭게 해석하지 않고60초를 보수적으로 더해 미완료 OHLC 유입을 막는다. 사후 저장 자료이므로 live 전달/가용성까지 입증하지는 않는다.

추가 가격 가설8개는 가격 반전, 두 봉 연속 회복, 저점 상승+양봉 회복, 직전5봉 고점 돌파,5봉 평균 재돌파, 가격 반전+현재 flow 양수, 고점 돌파+현재 micro 가격/flow 양수,5봉 평균 재돌파+현재 flow 양수다. 숫자 경계 추가 없이 구조적 부호/비교만 사용한다. 학습/후단 날짜·목적함수·source/coverage 기준·비용/종목 민감도는 첫 단계와 동일하다. 두 단계의 표본을 합쳐 독립 기회로 계산하지 않는다.

분봉 단계의 성능 열람 전에 개별3/5/10/20/30/60분 최적 조건 비교도 고정한다. 여러 시간 평균의 최솟값만으로는 늦게 상승하는 가설을 배제할 수 있기 때문이다. 같은 고정 가설 표에서 각 horizon의 학습 평균으로만 조건을 고르고, 후단에 해당 horizon과 조건을 그대로 적용한다. horizon별 후보를 별도로 보고하며 후단에서 가장 좋은 시간만 골라 단일 검증 성공으로 표현하지 않는다. 원천 또는 가설 종류를 추가하지 않는다.

보조 AI의 변경0 조건은 비교 기준으로 남기고 개선 후보로 선정하지 않는다. 변경이 발생한 조건의 성공 제외와 남은 PASS 성능을 별도로 판단한다.

기존 연구 모듈을 검토했고 역할상 `src/engine/scalping/entry_policy_path_sequence_research.py`에 offline 전용 분석을 둔다. `src/engine` root에 파일을 추가하지 않는다. 회귀는 `src/tests/test_entry_policy_path_sequence_research.py`이며 live loader/자동화에는 등록하지 않는다.

산출물은 `tmp/path-sequence-validation-20261003/`에 한정한다. 사전 protocol, 원천/코드 SHA, 기존 정책 파일 hash, 결과 분류 교차표, 원천 projection, 모든 가설/시간순 결과, auxiliary 결과, 최종 리뷰 영수증을 보존한다. 큰 원천은 확장 projection 생성 시 한 번 해석하고 이후 작은 projection을 재사용한다.

## 리뷰와 종료

1. 구현→자체 리뷰→보완→재리뷰→targeted pytest/compile/diff를 닫고 실제 원천 계산을 실행한다.
2. 미래 정보 누출, 잘못된 route/정책 연결, 중복 timestamp, 양수/음수 비대칭, 비용 결손의0 대입, 학습/후단 오염, 겹치는 관측의 독립성 과장, 지원되지 않는 prompt 성능 주장을 검토한다.
3. 모든 P1~P5 결과와 실패·지원 불가를 audit에 기록한다. 연구 가설 유효성과 live policy 승격을 분리한다. 경제성 음수 또는 희소 결과 자체는 분석 구현의 미완료 사유가 아니다.
4. 문서 링크/단일 checklist 소유자와 print-only parser를 확인한다. 외부 Project/Calendar sync는 실행하지 않는다. 기존10/6 자연 수용 소유자는 유지한다.

Metric contract: `metric_role=diagnostic_research`, `decision_authority=offline_only`, `window_policy=frozen_20260929_20261002`, `sample_floor=explicit_research_support`, `primary_decision_metric=cost_bound_path_and_chronological_cf`, `source_quality_gate=exact_retained_source_cost_scope_and_past_only_features`, `forbidden_uses=live_promotion,actual_profit_claim,synthetic_native_identity,provider_or_order_authority,hard_safety_relaxation`.
