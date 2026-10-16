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

## 첫 배포 후 발견한 잔여 읽기와 추가 보완

`8d1fb29fda99c3ac867f84f5f876ea034695a0db`는 원 `35beec0f`를 ancestor로 포함하고 11:33:03 native ordered 배포를 완료했다. Main PID3314987/start18181121의 정책 소비를 확인했다. 이 배포 완료가 읽기 개선의 최종 수용은 아니다.

11:35의 /proc 관측에서 Main은 7,394,107,688-byte 10/13 pipeline을 열고 있었다. 별도 holding-exit sentinel은 당일 pipeline/166MB 이벤트 cache, buy-funnel sentinel은 89MB SQLite를 읽고 있었고 monitor snapshot도 독립 실행 중이었다. 이 관측은 파일 metadata와 프로세스 I/O 카운터만 사용했다.

raw open 직전 중단하는 read-only audit로 `artifact_freshness → historical_checklist_for_observer → verify_bootstrap → _observer_delay_generation → verify_source → family_source_ledger_issues → byte_generation(pipeline)` 경로를 확인했다. 지연 정책의 기동 준비도 같은 검증 함수를 사용한다. 기존 반복 읽기 제거에서 이 ledger 내부 경로가 누락되었으므로 재개한 결함이다. 10/12 원장 open 직전 스택은 [원 증거](/home/ubuntu/KORStockScan/tmp/sor-krx-pipeline-validation-deploy-20261016-1100/raw-open-first-stack.json)를 보존한다.

추가 구현은 지연 정책 bootstrap/prepare 및 수량 terminal 소비에서 pipeline 참조만 검증한다. 봉인 ledger, compact source bytes, 정확한 overlap, 보고서/정책/코드 결속은 유지하고 연구 producer의 기본 full 원천 검증은 보존한다. canonical plain/gzip/late 참조를 같은 계약으로 처리한다. 실제 10/15 발행 지연 보고서의 수정 consumer 검증은 원장 open 0, 0.207초에 통과했다. 이는 해당 consumer 한 회 측정이며 전체 기동 시간은 후속 배포에서 별도로 측정한다.

observer digest의 role 공통 잠금이 전체 검증 동안 유지되어 다른 observer가 2초 후 `ValidationDeferred`로 중단되는 문제도 확인했다. generation 잠금으로 검증을 분리하고 role 잠금은 발행/retention에만 사용한다. 같은 generation 경합 시 artifact 관측을 명시적으로 deferred/불완전으로 남기고 독립 health 검사는 계속한다. cache 발행 실패로 semantic 결과를 PASS로 바꾸거나 원장 전체 읽기로 재시도하지 않는다.
