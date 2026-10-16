# SOR KRX 지정과 pipeline 검증 경계 수리 — 2026-10-16

## 승인과 변경 범위

사용자는 통합 SOR 체결의 소비 시장을 KRX로 고정하고, 정책 발행·기동·감시가 과거 pipeline 원장을 반복해서 읽는 경로를 제거하도록 지시했다. 모든 보완 후 `35beec0fd584d0b01cbd7b965f1c271161fd46bf`를 통합해 배포·재기동하는 권한도 명시했다. 지정 커밋은 충돌 없이 cherry-pick `be1108609`로 통합했다. 이는 배포/PID 소비 영수증이 아니다.

## 구현과 재리뷰

- 시장 귀속은 `src/trading/market/execution_venue.py`의 순수 계약으로 소유한다. 10/16 이후 aware 체결 시각, broker venue UNKNOWN 및 원본 `0/SOR 또는 통합/Y`에서만 KRX를 지정하고 `user_2026_10_16_sor_execution_venue_krx`를 기록한다. 명시적 KRX/NXT·충돌·원본 누락·이전 날짜에는 적용하지 않는다. 주문·시세 route를 변경하지 않는다.
- 원 FID·broker UNKNOWN·provenance false·비용 결손과 기존 9/27 참고시장 승인을 보존한다. 체결 축→snapshot/ACK→매도 후 관측→완료 투영→장후 결합에 지정 근거와 verified=false를 전달한다. native venue-specific promotion을 합성하지 않는다.
- revive 후보는 같은 완료 leg의 frozen snapshot을 우선해 주문·체결번호를 전달한다. `unknown` 예정 시세 경로는 세션 계약에서 선택하고 실제 BBO는 원 exact item/session/freshness 검증을 유지한다. 과거 놓친 관측창을 소급 복구하지 않는다.
- 공식 체결 시각은 수량 보존·정확한 주문/체결번호·체결 authority로 독립 결속한다. 비용 미상 때문에 시각을 지우지 않으며 strict 경제성과 손익 결손은 유지한다.
- 정책 v2–v6와 active-code handoff는 canonical 일별 pipeline의 봉인된 참조 형식/날짜/해시를 검증하고 raw bytes를 재해시하지 않는다. 원천의 현재 내용/존재를 검증했다는 주장이 아니다. 발행 보고서·정책·코드·다른 원천과 연구 producer의 검증은 유지한다.
- full/artifact detector는 기존 observer digest session을 연결한다. 파일 identity 변경 시 다시 읽고 모든 semantic check는 매번 실행한다. `validation_io`에 실제 전체/재사용 바이트를 기록하며 verdict는 캐시하지 않는다.
- PREOPEN 원 commit→검토 코드의 정확한 source hash pair를 결속한다. 정책·임계치·수량·provider·custody·수동 제외와 기존 timeout은 유지한다.

## 검증과 운영 수용

관련 619개, 영향 경로 1,989개, 집중 계약 27개와 최종 receipt/report/detector/handoff 회귀 2,473개가 통과했다. native 동일 workload는 현재 선택본과 수정본 모두 128 scope·76,800행·594 hit·동일 signal SHA이며 provider/주문 호출 0이다. [native 비교](/home/ubuntu/KORStockScan/tmp/sor-krx-pipeline-validation-deploy-20261016-1100/native-policy-parity.json).

pipeline archived 참조의 raw open 0, 잘못된 해시/clean-baseline 이전 거부, 다른 보고서 변경 탐지, detector의 실행 간 재사용·의미 재평가·변경 재읽기, SOR 원본 불변·NXT 보존·잘못된 authority 거부·비용 null을 검증했다.

기존 `DirectFamilyPreopenPolicyHandoff`/`HoldingProfitExitSourceContractRepair`가 실제 배포·PID·정규 후속 수용을 소유한다. 리뷰 후 immutable release/code handoff와 ordered 정지→선택→준비→시작→독립 PID 검증을 진행한다. 원 실패·source/economic OPEN을 보존하며 역사적 journal/DB를 일괄 수정하거나 관측을 합성하지 않는다.
