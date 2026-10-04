# 삼성전자 프로그램 연속 변화·효력 소멸 연구 보완계획

Owner: `SamsungEnvironmentConditionedResearch1004`, [현재 checklist](../checklists/2026-10-04-stage2-todo-checklist.md).
선행: [환경·수급 계획](samsung-environment-conditioned-pattern-research-plan-2026-10-04.md).

사용자의 가설 확대·중단 없는 연구 지시를 이어서 실행한다. 환경 부호 연구의 학습 개선1건이 후단에서 실패한 뒤, 마지막 구별되는 가설군으로 **프로그램의 실제 과거 연속 변화와 신호 효력 소멸**을 검증한다. 기존 accepted 환경 연구의 kernel/plan/source는 수정하지 않는다. 이미 탐색한3일을 재사용하며 독립 holdout으로 표시하지 않는다.

- 기존519 normalized snapshot만 사용한다. 같은 날짜·epoch·route의 서로 다른 관측 clock에서 연속 간격60초 이내일 때만 net_qty 변화 부호를 계산한다. 서로 다른3관측이면 시간 차이를 나눠 buy/sell/net rate와 감속/가속·양수 전환을 계산한다. 동일 snapshot 재사용을 변화로 세지 않고, 같은clock 다른값·counter 감소·clock 역전·gap/epoch 단절이면 history를 초기화한다. 당시 fresh/availability/expiry 계약은 유지한다.
- 무조건 baseline1 및 조건13: net 변화3부호, 매도 감속/매수 가속/net 가속/양수 전환4개, 감속/가속×종목300초 방향4개, net 변화up×VWAPbelow/누적netdown2개. 기존6상태×300/900초×confirm5초12신호에 barrier/state_failure2종료를 고정해336개 가격 조건을 계산한다.
- 리뷰 보완: 60초 모델에서는9/30·10/2의 서로 다른 과거 endpoints가 연결되지 않았다. 최신 source expiry60초와 과거 endpoint 비교 간격을 구분해60/180/300/900초의4모델을 검증한다. coarse 모델은 관측 endpoint 간 구간평균이며 연속 sub-minute 흐름·보간값이 아니다. 가격 조건은baseline24+13조건×4모델×12신호×2종료=1,272개다. 원source의각시점fresh·availability·sameepoch를 유지하고 최신expiry를 늘리지 않는다. 초안60초 결과를 먼저 확인한 탐색 보완이며 후단 독립성을 주장하지 않는다.
- state_failure는 기존 순수 연구 exit를 그대로 사용한다. bid가신호 시점보다500원 하락하거나 net 목표+0.1% 또는gross stop−0.7%에 먼저 도달하면 종료, 최대1200초/비용0.23%/cooldown60초다. live exit 소유자/임계값은 바꾸지 않는다.
- 학습 선정은 선행과 동일하게 양일 지원·확정≥3·동일 무조건 baseline 대비 terminal 승률 개선·평균netCF양수다. 원Main binary/native·환경 단독 veto도 별도 비교한다. 성공 보존 veto는 없다. 원source/정책/인계hash를 보존한다.
- 실제 관측/교집합 지원이 없으면 `not_observable`이며 효과 없음으로 치환하지 않는다. 후보가 생기면 고정 후단 결과를 검증하고, 미충족이면 이 가설군 종료를 보고한다. 외부intraday 지수/업종은 미실행으로 유지한다.
- 오프라인 생산자는 기존scalping 연구package,회귀는src/tests,결과는동일tmp의`sequence-cold/sequence-warm/`. 구현→리뷰→보완→회귀/compile/diff→격리재실행→문서parser로 마친다. 주문/API/provider/원천확대/정책발행/배포/재기동은 없다.
