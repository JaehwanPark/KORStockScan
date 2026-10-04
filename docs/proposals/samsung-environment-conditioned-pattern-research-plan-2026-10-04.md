# 삼성전자 환경·수급 조건부 패턴 연구 실행계획

Owner: `SamsungEnvironmentConditionedResearch1004`, [현재 checklist](../checklists/2026-10-04-stage2-todo-checklist.md).

## 1. 목적과 범위

사용자의 환경별 가설 확대 및 연구계획 실행 지시에 따라 보유 9/29·9/30·10/2 원천으로 새 조건부 가설을 검증한다. 앞선 회복·흡수 연구의 소진 판정은 당시 탐색한 가설군에 한정한다. 종목 자체의 방향과 외부 시장·업종의 방향을 별도 변수로 취급한다. 새 수집, API/provider 호출, 주문, 정책 발행, 배포·재기동은 이번 연구 범위에 없다. 성공 100%/80% 보존 veto는 사용하지 않는다.

## 2. 원천·위치·계약

- 기존 봉인 regular source의 체결·호가·51,604 frame, Main 판정 519건과 원래 binary/비용/native identity를 보존한다. 원 capture의 path·physical hash·행·canonical trace를 대사한 뒤 프로그램·투자자 normalized snapshot을 추가 소비한다.
- 새 생산자는 오프라인 연구 package `src/engine/scalping/samsung_environment_conditioned_research.py`, 회귀는 `src/tests`, 결과는 `tmp/samsung-environment-conditioned-research-20261004/`에 둔다. 기존 live producer, 프로토콜 parser, sealed 연구 kernel을 수정하지 않는다.
- 수급은 관측 시각이 capture 이전이며 같은 날짜·종목·scope·원 snapshot route를 만족하는 값만 인정한다. snapshot의 fresh 표기만 믿지 않고 timestamp·유효기간을 재검증한다. Frame에 붙일 때 capture 이후에만 사용할 수 있고 원 source expiry와 stream epoch를 지킨다. 미래 snapshot, stale carry, 날짜·epoch 간 carry를 금지한다. `_AL` 통합 수급은 해당 capture의 문맥으로 표시하며 KRX 단독 수급으로 바꾸지 않는다.
- 외부 지수·업종은 보관된 당시 intraday 자료만 사용한다. 장후 cache, stock master, 이전 기간 지수, 일봉 종가를 장중 상태로 치환하지 않는다. 현재 원천에서 확인되지 않으면 `source_unavailable`로 남기며 종목 상태를 시장 상태라고 부르지 않는다.
- 별도로 **당시 이미 발행된 이전 일일 report의 우량주 pool 20일선 breadth**를 소비한다. 원 publication 시각과 quote_date를 보존하며 quote 종가 기준72시간 이내만 인정한다. 현재장 상태/전체시장 breadth와 다르고, 같은 날 장후 report를 오전에 소급하지 않는다. 원 생산자의 <40% 하락·40~60% 중립·≥60% 상승 분류를 사용한다.

## 3. 계산 전에 고정할 가설

1. **종목 방향**: 연결된 과거 300/900초의 bid 수익률로 상승·중립·하락을 구분한다. 경계는 각각 ±0.2%/±0.3%. 과거 VWAP 위/아래와 비용+목표 0.33% 이상의 과거 range도 구분한다.
2. **프로그램 수급**: 누적 net_qty 및 최신 delta_qty의 양수·0·음수, 누적 매도 중 순매수 전환/누적 매수 중 순매도 전환을 구분한다. 종목 900초 방향 × 프로그램 delta 방향의 9개 셀도 시험한다. 최신 delta는 직전 API 응답 차이로 재해석하지 않는다.
3. **투자자 수급**: 당시 foreign_net·inst_net·smart_money_net의 부호를 시험한다. 0으로만 채워진 값은 별도 무정보 판정이며 결손과 다르게 공개한다. 프로그램 양수 delta × smart_money 양수도 시험한다.
   - 이전 발행 pool breadth 3상태 및 breadth × 종목900초 방향9셀을 더해 총51조건을 고정한다. 이 분류의 날짜별 변화가 없으면 환경 효과를 식별할 수 없다고 보고한다.
4. 앞선 6개 causal state × 300/900초 × 확인 5/15초의 24개 신호 정의에 각 조건을 적용한다. 조건에 미달한 최초 신호를 뒤의 성공 신호로 바꾸지 않는다. 누적된 상태 신호를 당시 조건으로 필터한 효과를 측정한다.
5. 동일 ask 진입/bid 종료로 barrier·600초·1200초 종료를 비교한다. 비용 0.23%, net 목표 +0.1%, gross stop −0.7%, terminal 이후 cooldown 60초를 고정한다. 불명 terminal 뒤의 추가 진입은 금지한다. 선정 규칙의 비용 0.33%·1초 지연 민감도를 별도로 계산한다.

## 4. 비교·선정·중단

- 9/29·9/30에서만 선택하고 10/2에서 고정 재생한다. 이미 탐색한 10/2는 독립 pristine holdout이 아니다. 선택 기준은 같은 신호·종료 모델의 무조건 baseline 대비 확정 terminal 승률 개선, 학습 확정 결과 ≥3건과 두 학습일 지원, 양수 평균 net CF이다. 이는 연구 shortlist이며 Main 원 binary 승률이나 실현 PnL의 대체물이 아니다. 성공 보존율을 탈락 조건으로 두지 않는다.
- 각 셀의 전체 시도·확정·검열·목표/stop·승률·CF·날짜별 지원과 분류 결손을 공개한다. 셀별 좋은 승률과 조건부 전략 전체 승률을 구분한다. 조건을 통과한 서로 다른 신호군을 독립 수익으로 합산하지 않는다.
- Main 519건에는 같은 당시 조건과 guard-compatible state bridge를 적용해 veto/soft_add/replace_soft를 별도 비교한다. 결손 조건은 기존 parent로 승계한다. 원 binary와 원 비용을 바꾸지 않고 원 native group과 trace 분모를 함께 보고한다. 해당 publisher의 30/10 native floor는 공식 적격성에만 적용하며 가격 연구 중단 조건으로 쓰지 않는다.
- 리뷰 보완: 기존 신호 정의의 제약과 환경 조건 자체의 효과를 분리하기 위해51개 **parent ENTER 환경 단독 veto**도 계산한다. unknown은 parent 승계이고 BLOCK/RECHECK 승격은 없다. 첫 가격 재생의 학습 선정1건·후단 손실을 이미 확인한 후 추가한 비교이므로 별도 탐색 보완으로 표시한다. 계산한 초기 kernel/plan은 격리 snapshot에 보존하고, 보완 이후 accepted cold/warm으로 최종 증거를 새로 봉인한다.
- 외부 시장·업종 자료가 없으면 그 가설은 미실행으로 명시한다. 실행한 고정 가설이 모두 재검증에서 미충족이면 그 가설군에 한정해 종료하고, 전체 접근법 소진이나 시장 조건 효과 부재라고 주장하지 않는다.

## 5. 검토·검증

구현→self review→수정→재리뷰→표적 pytest/compile/diff를 마친 뒤 격리 cold/warm 재생한다. 미래값·expiry·route·epoch·원 trace 불일치, 0/결손 구분, 과거 return continuity, train-only 선택, 검열 뒤 재진입, winner-preservation 부재, source/정책 hash 불변성을 검증한다. 학습 고정 조건만 후단과 민감도에서 평가한다. 최종 source census·선정·실패 원인·다음 가설과 운영 후보 적격성을 별도 audit에 남기고 local link/owner 및 print-only parser를 검증한다. 기존 10/6 기동 owner는 유지한다.
