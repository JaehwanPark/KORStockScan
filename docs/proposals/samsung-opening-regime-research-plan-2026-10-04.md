# 삼성전자 개장 초기·장전 기준 분리 연구

Owner: `SamsungPatternCampaign1004`, [현재 checklist](../checklists/2026-10-04-stage2-todo-checklist.md).
선행: [연속 연구계획](samsung-pattern-campaign-plan-2026-10-04.md).

## 사전 고정 범위

연속 연구6,552개 조합 이후 같은 종료 시각 대사에서10/2 09:03:55의 매도 감소 진입은 기준보다500원 낮아+0.1842%p 가격 차이와 추가 목표1개가 있었다.09:28 신호는 종료 전 결손 및 불리한 종료 지점이 있어, 단일 성공을 운영 패턴으로 닫지 않고 개장 초기와 후속 변동을 분리한다. 이미 확인한3일의 추가 탐색이며 pristine holdout이 아니다.

기존 봉인된 정규장 frame·장전 cache·native Main projection만 읽는다. 새 수집·broker API/provider·runtime/정책 발행·배포/재기동은 없다. 기존 성공100%/80% 보존 veto가 없다. 소스와 기존 kernel·정책98개를 보존한다.

## 가설군

- 정규장09:00~09:15 또는09:00~09:30에만 같은12개 가격/flow/잔량 가설을 적용한다.15/30분은 opening impulse와 이후 회복의 경제적 시간 구간이며, 특정 성공 시각만을 남기는 초 단위 최적화를 하지 않는다.
- 장전 기준은 `none`, `below_preopen_close`, `above_preopen_close`, `above_preopen_high`4개다. 기준 close는 장전 마지막 유효 체결 관측, high는 유효 체결의 관측 최고 가격이다. 완전한 공식 OHLC/실제 fill로 부르지 않는다. 기준의 day·source route·hash·마지막 수신 시각을 고정하며 현재 신호보다 과거인 값만 쓴다. 결과 경로는 세션 사이에 연결하지 않는다.
- 기존 과거 창60/180/300·level1/2·600/1200/1800초·비용0.33 stress/0.23 source fee 비교를 유지한다. 전체 조합은12×3×2×2×4×3×2=3,456개다. 선행6,552개를 포함한 누적10,008개 탐색을 공개하며 독립 실험/표본이라고 부르지 않는다.
- phase별 fixed-clock 기준·학습 binary≥3/기준 binary≥3·더 높은 승률→Wilson/support/단순성·9/29→9/30 및9/29~30→10/2 순서를 유지한다. 후단에서 재선정하지 않는다. 기준 표본 부족도 별도 진단하며 성공 보존율·시간 종료 CF 양수 veto로 후보를 제거하지 않는다.

## 안정성·종료

선정 조건의 후단 자체창·같은 절대 종료·250/1000ms 지연·+0.4% arming 가격·현재 native guard/identity와 대응을 확인한다. 장전 기준이 원천 결손으로 없으면 조건 불충족/손실로 대신하지 않는다. 현재 policy reference와 fixed-clock reference를 구분한다.

원천·단계·시간 그룹·가격 거리·flow·3단 잔량·비용 표현·보유창·native 대응과 본 opening 가설을 마친 뒤, 운영 적용 근거가 부족하면 현재 보관3일의 가설군을 소진한 것으로 종료한다. 모든 수학적 가설의 부재나 시장 edge 부재를 주장하지 않는다. 같은3일의 숫자를 계속 잘라 가장 높은 결과를 고르는 추가 탐색은 독립 검증을 추가하지 않으므로 실행하지 않는다. 새로운 날짜 수집 또는 운영 변경을 자동으로 만들지 않는다.

`src/engine/scalping/samsung_opening_regime_research.py`는 독립 오프라인 source consumer다. 기존 kernel은 수정하지 않는다. 구현→리뷰→수정→재리뷰→표적 회귀/compile/diff·prefix 인과성·재실행 일치·source/policy hash·문서 parser를 완료하고 campaign audit에 함께 기록한다.
