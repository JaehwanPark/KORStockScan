# 기계 후보 평가 함수·원천 효과·고정 진입 청산 검증 계획

작성: 2026-10-04 KST. 사용자 `다음액션 실행`에 따라 앞서 제시한1→2→3을 실행한다. [선행 결과](../audits/samsung-source-recipe-and-non-samsung-horizon-review-2026-10-04.md)의 입력·후보·가격 계약을 유지한다.

## 1. 고정 범위와 코드 위치

- 기계판정 전용, 보유9/29·9/30·10/2 원천만 사용한다. 보조 AI·새 수집·API/provider 호출·정책 발행·배포·재기동·주문은 범위 밖이다.
- 삼성전자외 `pullback_p60_v0`와 삼성전자 `absorption_p60_v10` 조건을 유지한다. 원 ENTER 성공100%/80% 보존 veto를 두지 않는다. 앞선 두 날짜만 연구 선택에 사용하며10/2의 반복 연구 사실을 공개한다.
- 원천·원 native ID·비용·hash·시각·exact venue/session을 보존한다. 결손/불확실을 실패0·경제성0으로 치환하지 않는다.
- 새 순수 오프라인 evaluator는 `src/engine/scalping`의 research 모듈, 회귀는 `src/tests`, 일회성 재생과 결과는 `tmp/machine-candidate-next-actions-20261004`가 소유한다. engine root에 모듈을 추가하지 않는다.

## 2. P1 — 삼성전자외 실제 기계 평가 함수 대사

1. 기존 전체6,550 KRX 정규장 관측을 같은 parent로 재현한다. 고정 조건의 observed filter와 실제 제안 ENTER를 구분한다.
2. 원 기계 core의 위험별 disposition을 보존한다. 가설은 신뢰 수급·VWAP 이하 가격을 별도 pullback setup/trigger로 표현하며, 기존 soft confirmation fact만 명시적으로 상쇄한다. ADVERSE_TAPE·liquidity·hard/source·미지정 fact·선정 micro recipe·situation veto는 유지한다. 원 breakout 사실은 바꾸지 않는다.
3. 기존 ENTER의 조건부 제외를 허용하는 교체형으로 같은 점유 재생을 수행한다. 모든 제외·전환 사유를 기록한다. 원 raw/hash가 잘못되면 해당 행을 분리한다.
4. native 연결0의 원인을 원 capture→projection→기존 pipeline의 exact attempt/snapshot/trace 연결로 대사한다. 종목·시간 근접으로 새 promotion ID를 만들지 않는다. 연결이 복원돼도 관측과 독립 기회를 구분한다.

완료: parent 행동 일치, 제안 ENTER/미전환 위험 원장, 날짜별 승률·선택량·native 결손 원인. source/위험 입력만 받는 순수 함수와 scope/guard/미래결과 차단 회귀를 갖춘다.

## 3. P2 — 삼성전자 원천 수정과 규칙 효과 분리

1. 원 payload·archive·기존 진단 capture에서 완전한 `ws_data/recent_ticks/recent_candles/candle_context/cutoff` 입력이 남아 있는지 census한다. 필수 입력을 추정 생성하지 않는다.
2. 완전 입력에서는 같은 feature 생성 함수를 사용해 기존 원천+기존 규칙 / 수정 원천+기존 규칙 / 기존 원천+새 규칙 / 수정 원천+새 규칙을 비교한다.
3. 완전 입력이 없다면 그 사실과 결손 필드를 행 단위로 확정하고, 실제 원 capture+신규 규칙의 재생과 source selector의 합성 fixture 통합검증을 각각 보고한다.3개 체결값 부분 대체를 전체 원천 효과로 부르지 않는다.

완료: 가능한2×2 비교와 불가능 셀의 구체적 입력 결손, producer→feature→receipt→평가 함수의 결속 및 회귀. 과거 복원 불가능 원천을 반복 탐색하지 않는다.

## 4. P3 — 고정 진입의 청산·비용 분해

1. 기존 및 P1/P2 고정 후보의 비중복60분 기준 진입 ID를 봉인한다. 청산 arm에 따라 더 좋은 진입을 다시 선택하지 않는다.
2. 기본 원 비용+0.1% 목표·gross−0.7% 손절을20/30/60분·같은 세션 종료로 비교한다. 보조 청산 가설은 net 목표0.2%/0.3%이며 손절은 고정한다. 사전에 고정한 arm만 계산한다.
3. 목표 이익·손절 gross 손실·원 비용·시간종료 손익을 분해한다. 같은 진입·양쪽 완전 평가 가능한 집합의 paired 평균과 양수 종료 비율을 낸다. 목표 선도달 승률과 양수 종료 비율은 구분한다.
4. 첫 부분 봉·동일 봉 양 경계·90초 가격 간격·세션 잘림은 불확실로 유지한다. 이후 가격은 미래 label/청산 비교에만 사용한다. 체결 가능성·실현 PnL로 승격하지 않는다.

완료: 음수 평균의 원인별 기여와 고정 진입 청산 비교, 학습과10/2 분리 결과. 청산 가설이 개선되지 않아도 entry 후보를 성공 보존율/평균EV 조건으로 자동 탈락시키지 않는다.

## 5. 리뷰와 기록

- 구현→리뷰→보완→재리뷰→표적 pytest/compile/location/hash/diff/link/print-only parser.
- 결과 문서에 구현 범위와 미입증 범위를 분리한다. 기존 운영 계약/10/6 준비 owner는 변경하지 않는다.
- 실행 owner:10/4 checklist `MachineCandidateEvaluatorSourceExit1004`. 신규 alpha 등록·운영 적용은 이번 완료 조건이 아니다.
