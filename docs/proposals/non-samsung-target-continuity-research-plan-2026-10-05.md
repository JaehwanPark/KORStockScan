# 비삼성 목표22건 시간 연결·청산 검증 계획

## 범위·소유

- 사용자 다음 액션 실행에 따라10/2 고정 `pullback_p60_v0` 후보의 봉 목표 선도달22개 원 trace를 유지한다. 이전 날짜·진입·가격·비용·정책을 다시 선정하지 않는다.
- 소유자는10/5 `NonSamsungTargetContinuity1005`. 이전 봉인 코드/산출물은 보존하며 결과는 `tmp/non-samsung-target-continuity-20261005`에 별도 작성한다.
- 새 코드가 필요하면 offline scalping 분석은 `src/engine/scalping`, 회귀는 `src/tests`, 일회 실행/입력 manifest는 위 격리 경로에 둔다. live collector/API/주문/정책/기동은 변경하지 않는다.

## 실행 순서

1. 직전 final report/원 관측/정규화 cache 해시와22개 trace를 고정한다. 원 canonical shard/manifest, 당일 registration receipt·WS snapshot·pipeline/source 이벤트·기존 가격 원천을 목록화한다. 날짜 말 receipt를 장중 상태로 역적용하지 않는다.
2. 각 진입부터 원60분/장 종료까지 item·epoch·순번·관측 시각·연결 전환을 대사한다. 동일 item의 누락된 shard/기존 대체 raw가 발견되면 원 식별자와 producer 계약에 따라 연결한다. 다른 route, 요약 snapshot, 봉을 tick/depth로 합성하지 않는다.
3. 세 가지 결손을 구분한다: 보관 이벤트 사이 무관측, transport/collector epoch 경계, 서로 다른 스트림의 같은 시각 선후 불명. 순번은 collector가 받은 이벤트 번호이며 시장 전체 체결의 연속성 증거로 확대하지 않는다.
4. 정확한 시각/원천 연결이 확보된 경로만 현행 강약 청산을 재생한다. 동일 시각은 receipt로 선후가 입증되거나 모든 가능한 순서의 판정이 같을 때만 확정한다. 연결 불가능이면 복원0도 명시하고 임의의 순서나 가격으로 메우지 않는다.
5. 남은 사례는 기존 봉의 조건부 재생/순서 민감도와 목표·trailing 시작선 차이를 별도 계산한다. 봉 시나리오를 실제 매도 가능 가격/정확한 청산 상하한이라고 주장하지 않는다. 실제 체결·보유/주문 상태·독립 검증 결손은 유지한다.

## 검증·종료

- 원천/산출물 hash, 대상22개 및 삼성 제외, producer 의미, 소스 누락·무순서·충돌·비용 처리, 코드리뷰/보완·표적 pytest/compile, 문서 링크·단일 owner·diff·print-only parser로 닫는다.
- 각 결손의 소유 원천·실제 사유·복원 가능 여부·재생 결과 또는 미입증을 보고한다. 동일한 미복원 원천의 반복 재생은 하지 않는다.
- 기존 성공100%/80% 보존 veto, 신규 수집/API/provider/주문, 운영 정책 선정/발행/배포/재기동은 이 작업에 포함하지 않는다.
