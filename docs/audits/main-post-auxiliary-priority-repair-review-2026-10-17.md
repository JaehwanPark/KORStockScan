# 보조판정 이후 우선 수리·실패 위험 비교 검토 — 2026-10-17

사용자 "우선순위 진행바람"과 동일50점 비교를 위한 추가100회 승인을 따른다. [앞선 전체 가드 감사](main-post-auxiliary-guards-cumulative-defect-review-2026-10-17.md)의 G171/G174 미전송 상태·분류, 보조 위험 표현, G172/G173 최종 가격·시간, 상시감시/스캐너 제출 분모를 검토한다. 이 문서는 코드·연구 검증 기록이며 운영 배포·PID 소비·실제 매매 성과 기록과 구분한다.

## 작업 기준과 최종 배포본 재확인

10/17 15:26 KST selector와 실제 `/proc`를 재확인했다. 최종 선택 릴리스는 `auxiliary-next-session-20261017-57d4d4664`, 커밋은 `57d4d4664c6ce766bf0e949e6f91a4a1c0618dc7`이다. selector 선택시각은15:01:30이고 다음 영업일은10/19다. Main 봇 PID는 없으며 `actual_pid_consumed=false`다. [해당 배포 검증](main-auxiliary-next-session-deployment-review-2026-10-17.md)의 배포·미래 정책 준비와 실제 다음 영업일 소비를 구분한다.

이번 수정은 위 릴리스에서 분기한 `/home/ubuntu/KORStockScan-worktrees/post-aux-priority-repair-20261017`, 브랜치 `codex/post-aux-priority-repair-20261017`에서 진행한다. 원 작업본의 다른 미커밋 변경과 운영 selector·현재/미래 보조정책을 덮어쓰지 않는다. 이 수리의 배포·재기동은 수행하지 않았다.

코드 커밋은 `d942ba69b`다. 격리 작업본의14개 코드/테스트 파일만 커밋했으며 원 작업본 HEAD·staging·운영 릴리스는 이동하지 않았다.

## 미전송 최초 진입과 최종 전송 가드

- 어댑터가 실제 전송 전에 반환한 결과만 프로세스 내부 증명으로 식별한다. 원격 응답의 `broker_order_attempted=false`나 현재 호출0회만으로 이전 주문 의도를 해제하지 않는다. 기존 owner·미체결·보유·다른 evaluation/trace 충돌은 보존한다.
- 첫 leg의 확실한 미전송은 별도 `TERMINAL_NOT_SENT` 영수증으로 종결하고 뒤 leg는 `NOT_SUBMITTED`로 둔다. 주문·취소·체결 증빙을 만들지 않는다. 같은 PASS에는 미전송 종결 신원을 남겨 재전송을 금지하고, 독립된 다음 신호의 평가를 허용한다.
- 최종 물리 전송과 기존 허용 인증 재시도 직전에 적용 중인 AI 만료시각을 재확인한다. 원 epoch/perf 기준에 결속해 시계 역행이나 토큰 갱신이 수명을 늘리지 못하게 한다. 표시용 반올림으로 실제 유효기간을 바꾸지 않는다.
- G172는 현재 가격 변경을 명시적인 미전송 종료로 처리한다. 가격 일치·원 신호5초·호가·계좌·수량·custody 안전조건을 유지한다. 자동 재가격·추격 진입을 추가하지 않는다.

어댑터 수정 전 [Kiwoom 공식 저장소](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/953e5dbff123f437ab4d11a78a95191a685eb51f)의 현행 SHA `953e5dbff123f437ab4d11a78a95191a685eb51f`, `specs.py`, `core/client.py`, `core/auth.py`, `core/errors.py`, `_data/kiwoom_api_spec.json`, PRD/MOCK Postman의 kt10000를 확인했다. upstream `kiwoom_docs`는 없으며 SDK/Postman 표현 차이를 임의 해석하지 않았다. wire protocol·주문 권한은 변경하지 않는다. 조회 시각·파일 해시는 `tmp/post-aux-priority-repair-20261017/kiwoom-reference.json`에 보존한다.

자체·독립 리뷰에서 이전 owner와 현재 미전송 혼동, intent/outbox 저장 순서의 예외 창, 준비 실패의 가짜 broker 시도1회, 복구 시 불필요 broker 조회, 재시도 tombstone의 provenance/집계 누락을 수정했다. 네트워크 불확실·디스크 저장 실패·registry 충돌은 명시적인 custody gap을 유지한다. 실제 broker 조회·주문을 실행하지 않는 fixture로 검증했다. 이후 배포/복구 코드는 새 `TERMINAL_NOT_SENT` reader를 함께 유지해야 한다. 구 reader는 이를 유효한 주문 상태로 해석하지 못하고 fail closed한다.

## 제출 분모

기존 scanner 전용 지표는 호환성을 유지하면서 범위를 명시하고, 정확한 날짜/evaluation/종목과 native 신원의 상시감시·scanner·미확정 합집합을 별도 표시한다. PASS 반환, 실제 record 연결, Main 명시 인수, 어댑터 호출, 물리전송, broker 접수를 나눈다. 평가 신원 충돌·여러 trace·PID/start 미관측은 인과 연결의 source gap이다. 독립 단계 관측은 남긴다. 물리전송 결손은 null이며0이나 broker 거절로 대체하지 않는다.

원 감사의 보존된14,464행에서 PASS176, 실제 record 연결155, 명시 Main 인수134, broker 접수 증빙15가 확인됐다. 15는 주문번호 수·체결 수·성공 손익 수가 아닌 평가 수다. 10/15에7, 10/16에8이며 고유 주문번호는 원 감사의17개다. 시간 창의 전체 원천이 증명되지 않았으므로 누적 전체 기회를 모두 관찰했다고 주장하지 않는다. 실제 비용/완료 원천의 결손도 그대로 남긴다.

원천 해시 `78ef8e4e650832ecaeb333cb0531e005367cd1c141d52562d21d87c8d3943533`의 frozen projection을 읽기만 했다. 상시감시 PASS175·scanner PASS1 중 scanner1은 PID/start 증빙이 없어 인과 연결 source gap으로 남았다. 평가/종목 신원 결손551행을 제외·집계했고 일자/구분 보존식4종을 확인했다. 전체 단계의 독립 Main 인수1,345를 PASS 인수134로 혼동하지 않는다. 소형 [집계 증빙](../../tmp/post-aux-priority-repair-20261017/main_scoped_census_receipt.json)과 [재현 코드](../../tmp/post-aux-priority-repair-20261017/build_main_scoped_census.py)를 보존했다. 원장 또는 전체 evaluation ledger 복제는 없다.

## 코드 검증

- 미전송·timeout·실제 전송·어댑터·수량 producer/consumer:528 PASS. 마지막 증빙 parent/fill 제약 강화 후 bundle13 PASS를 재검증했다.
- 기존 AI 권한 subset14 PASS, 독립 수정 경계24 PASS. 앞의 검증과 중복하므로 합산하지 않는다.
- 제출 sentinel·병목 monitor: 최종1,051 PASS. 별도 Main 범위 검증에는 PID 결손·trace 혼합·위조0회·다른 호출 미관측·parser 보존·현금 부족 분모를 포함한다.
- 연구 입력·기존 frozen RVP·production input·wire·causal:176 PASS. 임시 runner의 fake transport/재시작/한도/원천 변조8 PASS이며 실제 연구 호출과 분리한다.
- 영향 Python compile·`git diff --check` 통과. [guard 검증 명령·파일 해시](../../tmp/post-aux-priority-repair-20261017/guard-code-review.json)를 별도 보존했다.

검토 범위에서 미해결 코드 결함은 발견하지 못했다. 전체 거래 시스템의 무결함, 자연 제출·체결·PnL 개선을 보증하는 결과는 아니다. 배포·실제 PID·postclose 전체 재생성과 경제성 검증은 이번 코드 종료로 대신하지 않았다.

## 별도 보조 입력 연구

SHA로 고정된 기존 RVP 입력 변환은 수정하지 않고 별도 offline 모듈에서 확인점까지 관측된 가격 진행·반복·체결 방향·실행 거리와 같은 시점의 종목 session/구조를 표현한다. 위험 사실 binding은 인용 어휘이며 자동 veto나 새 수치 기준이 아니다. 원 입력·응답·50점 membership·비용0.23%/30분/net+0.4%/soft−3% 선도달 라벨을 유지한다. 없는 session anchor는 임의 복구하지 않는다.

대조군은 이전 연구의 RVP+후속 문구50응답을 정확 재사용한다. 현재 운영 전체의 공통 incumbent라고 부르지 않는다. 최종 배포에서 해당 조합을 준비한 범위는 두 PRE 경로이며 나머지126개 연결은 승계 상태다. 새 표본이나 독립 holdout은 없다. 50점은 WIN38/STOP3/TIMEOUT9이며, 기존 risk vocabulary가 빈 점은0개다. 빈 어휘 보완의 실제 효과는 이 표본으로 입증할 수 없다.

호출 전 [비교 명세](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/observed-risk-context-20261017/protocol.json) SHA `92bbd8156da3f753c566d757778e6c8e24b71c181b5ff8342c9d81ff42d362d0`를 동결했다. 기존2,047개 attempt ID·행 해시를 보존하고 동일 예산 key의 별도 승인 topup으로2,147회 상한을 연결했다. shared Store 잠금/예약/응답 보존을 사용해 신규 후보50회만 호출했다. 대조50은 정확 응답 재사용이며, 누적2,097/2,147회·미사용50회다. provider 재시도0, 제외/오류0, 공통 유효50쌍이다. 기존 원장 복제나 과거 응답 덮어쓰기는 없다. 원 runner와 검증 코드도 연구 디렉터리에 보존했다.

[실제 비교 결과](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/observed-risk-context-20261017/evaluation.json), SHA `2db2dbc96c41b710d5ceb627b9b197bc23000e5e6fd935ea7bbbcd570521b69d`:

| 관측 | 동결 RVP+문구 대조 | 관측 위험 입력 후보 |
| --- | ---: | ---: |
| 승리 지점 PASS(TP) |32|29|
| 실패 지점 PASS(FP) |12|10|
| 승리 지점 non-PASS(FN) |6|9|
| 실패 지점 non-PASS(TN) |0|2|
| PASS 승률 |72.73%|74.36%|
| 전체 WIN 포착률 |84.21%|76.32%|
| STOP/TIMEOUT 오통과 |3/9|2/8|

사전에 정한 전체50점의 주지표인 PASS 승률은1.63%p 올랐다. 기존 WIN PASS7점을 새로 막고 기존 CAUTION WIN4점을 구해 승리 PASS는 순3건 줄었다. 실패2건의 새 차단은 STOP1/TIMEOUT1이며, non-PASS가 실제 손실 절감이나 주문 방지로 실행됐다는 뜻은 아니다.

새로 놓친 WIN7점 중6점은 기존 spread/VWAP/rebound 사실을,1점은1.105초·10개 관측의 가격 경로를 인용했다. 새로 차단한 STOP1점은 관측 경로와 실행 거리의 복합 사실을 인용했고, TIMEOUT1점은 기존 목표 도달 거리만 인용했다. 응답의 인용은 모델 판정 원인의 인과 증명이 아니다. 특히 공통 목표 거리나 짧은 횡보만으로 실패가 입증되는 것은 아니므로, 어휘 확장만으로 보조 관문의 의미 문제가 해소됐다고 판단하지 않는다.

범위를 합쳐서 운영 우월성을 주장하지 않는다. 10/19에 RVP 조합이 준비된 두 PRE 범위20점은 모두 WIN이고, 두산8→7·알테오젠7→9 PASS로 합계15→16이다. 이 범위는 실패 차단을 측정할 실패 표본이 없다. 다른30점은 승리 PASS17→13, 실패 PASS12→10, PASS 승률58.62%→56.52%로 낮아졌다. 전체 상승을 나머지126개 운영 연결의 개선 근거로 쓸 수 없다. REGULAR·삼성의 효과도 이 표본으로 입증하지 않는다.

provider 입력 합계는225,223→435,484바이트(+93.4%), 실제 총 토큰 중앙값은2,496.5→3,908이다. 새 후보 호출 지연 중앙값은1,210ms다. 대조1,049ms는 이전 시점에 호출한 cache 응답의 기록이므로 동시 비교나 장중 지연 증감의 인과 증거가 아니다. 입력을 그대로 장중에 넣는 성능 수용성을 입증하지 않았다.

실제 총 토큰 합계는133,441→208,315(+56.1%)다. 표본의 실제 관측일은09/29~10/12이며10/07에30점·10/08에13점이 집중돼 있다. report의 `source_date=2026-10-16`은 연구 source/부모 날짜이며50점의 실제 관측일을 뜻하지 않는다. 입력당1회 응답과 과거 대조 cache의 비교여서 모델 변동성이나 독립 일반화 효과를 따로 추정하지 않았다.

독립 검토자는 원응답100건의 bytes/SHA/JSON/codec, 실제 provider 입력 commitment, 원 snapshot/라벨/대조 응답과 기존2,047개 attempt를 읽기 전용으로 대사했다. 집계·변경13건·예산·selector 보존은 일치했다. [독립 검증](../../tmp/post-aux-priority-repair-20261017/risk_context_independent_review.json) SHA `5ea7e2ef4aa59568e724b1cfe1cafb804465393371e3af61c4ab45129e92f737`다. 표본은 PRE40·AFTER10·REGULAR0이며10/15~16 실거래 구간 검증을 포함하지 않는다.

개발 비교는 완료했으며 일괄 운영 적용은 하지 않는다. 후속 검토 대상은 효과가 갈린 알테오젠 PRE의 범위별 확인과 반복되는 입력 사실의 압축이다. 이를 기존 선택본에 적용하려면 별도 입력 구현·동일 provider payload 검증·정확 정책 및 코드 인계가 필요하다. 이 연구는 기존 운영 입력/응답의 원형이나128개 정책 연결을 바꾸지 않았다.

## 이후 승인된 배포의 코드 인계

사용자가 배포·재기동과 다음 영업일 정상가동 점검을 별도로 승인했다. `a008631c5`는 앞선 `d942ba69b`의 수리에 원래 준비 정책의 handler 코드 `669b6109e36f81e9dee263d1c3e31011d55fd612d5641713c6ee109a827a9425` → `b18dab5939fd13ab09c7e24463785b1677324e3957a3efd07e60d82c085fc235`의 정확한 한 쌍만 추가했다. 기존 숫자 정책·호출 권한을 바꾸지 않는다. `intraday_release_handoff`와 prepared-policy 기존 회귀2,363PASS·compile/diff 검사를 통과했다. 실제 배포·준비 결과는 [별도 배포 검증](main-post-auxiliary-deployment-and-next-session-readiness-2026-10-17.md)에서 확인한다.
