# 2026-09-10 10:50 종료 장중 모니터링

- 요청: 지시문에 따른 10:50 KST까지 지속 모니터링. 시작 `10:09:07`; 요청 종료 시각10:50 도달 후 `10:50:11` 최종 snapshot/broker 대사를 마쳤다.
- 기준: [장중 지시문](../intraday-monitoring-task-instructions.md), [당일 체크리스트](../checklists/2026-09-10-stage2-todo-checklist.md), Plan Rebase §1~§8, runbook/traceability. main/widget/episode/manual 주문과 수량을 분리한다.
- 원천: `tmp/intraday-monitor-20260910-1050/`. 시각별 broker·collector·machine state·authority 원본 복사/SHA256, pipeline inode/byte range/hash, AI trace를 보존했다. 운영 원장·과거 원천을 합성하거나 테스트 데이터로 복원하지 않았다.

## 1. 실거래와 판단

10:18:08 broker KRX/NXT 전시장 조회는 삼성전자45주·SK텔레콤10주, 미체결 SELL3건이다. 삼성 오전20주는 기존25주와 별도이며 목표 주문0015751/0018662 각10주, SK텔레콤0022607 10주다. 각 미체결의 registry owner가 정확히1개다. 삼성E&A028050은 broker0/registry10의 기존 수동매도 귀속 gap을 유지한다. 잔고0만으로 공통 registry를 수정하지 않았다.

09:00 이후 main 실제1주 BUY bundle은3개이며 모두 매도 완료가 확인됐다. 이는 AI 원문 BUY3건이라는 뜻이 아니다. WAIT 뒤 승인된 기존 bounded 경로의 실제 체결이다.

| 종목 / record | BUY 주문·체결가 | SELL 주문·체결가·시각 | 진입 owner | DB/체결가 기반 비용모델 순손익 |
|---|---|---|---|---:|
| 스트라드비젼475040 /42219 |0018557 /3550|0026594 /3615 /09:53:04|rising-missed submit guard|57원|
| 흥구석유024060 /42193 |0026276 /14920|0029892 /15130 /10:11:01|entry recheck direct|175원|
| 흥아해운003280 /42263 |0026355 /1941|0029586 /1958 /10:09:36|rising-missed submit guard|12원|

합계244원은 동일3거래의 체결가와 현재 로컬 비용모델 대사값이다. `realized_pnl_status=broker_exact_cost_unreconciled`, broker 실제 수수료·세금에 결속한 headline 실현손익은 `null`이다. 실제 매도 venue가 SOR/UNKNOWN인 receipt를 KRX 확정으로 재라벨링하지 않는다. 수리의 인과적 수익 증가량이나 위젯·episode 손익으로 합산하지 않는다.

10:27:43 기준 Entry OpenAI v2.14는 DROP17/WAIT10/BUY0, v2.13 DROP3이다. provider 미호출 DROP은 별도 v2.14 11/v2.13 4건이다. raw `sell_completed`95회는 반복 outbox 로그를 포함하므로95거래가 아니다. AI BUY0과 실제 bundle3을 분리하고, 탐색 recall 정상 또는 AI 경제성 개선을 선언하지 않는다. 당일 탐색 probe cap3의 소비와 이후 신규 진입 제한은 별도 owner 계약이다.

## 2. 발견·수리·검증

### R1. 완료 매도 outbox가 정수/실수 표현 차이로 영구 대기

- 자연 원천: 흥구석유 `42193.json`, SELL0029892/체결번호200196, packet ingress `10:11:01.357421`. pending leg `d64e06983c4e1627c11123f2e0c11987017c80f95ed6b9fbd04230d19c7d9a3c`는 `sell_completed`다.
- 원인: frozen outbox의 `entry_opportunity_recheck_sell_notional_krw=15130`을 terminal attribution이 `15130.0`으로 바꿨다. 모든 durable field의 문자열 정확 일치를 요구하는 정상 ACK 검증에서 이 한 필드가 달라 영구 재시도했다. DB는 이미 COMPLETED이고 broker 잔고도0이다. 재시도 로그를 새 매도나 보유 복구로 세지 않았다.
- 수정: [entry_recheck_economics.py](../../src/engine/scalping/entry_recheck_economics.py)의 finite/수량/원주문 검증 이후, 매도대금·비용률 원본 표현을 보존한다. 계산은 검증된 숫자를 계속 사용하며 ACK 검사·금액·수량·비용·매매 권한은 완화하지 않는다. 기존 원장 재작성/해시 교체는 필요 없다.
- 회귀: 기존 테스트가 실제 ACK validator를 무조건True로 모킹해 결함을 놓쳤다. 실제 validator와 lifecycle identity를 사용하는 int/float/string3종으로 바꿨다. 수정 전2실패/1성공, 수정 후 모두PASS. 금액/수량/체결번호 변조 거절 테스트도 유지한다.
- 보존한 실제 frozen leg의 in-memory emission 검증은 `sell_completed → entry_opportunity_recheck_sell_completed` 모두 성공했다. `offline-outbox-validation.json`은 운영 pipeline에 쓰거나 원장을 ACK한 영수증이 아니다.

### R2. micro 지연 원인의 packet 수신 전/내부 구간 분리가 불가능

- 기존 0B/0D `received_at_ms`는 adapter 정규화 시계다. `_handle_message`가 이미 갖고 있던 신뢰된 packet ingress 시각이 rejection receipt에 전달되지 않아, 10초 초과를 외부 지연으로 단정할 수 없었다.
- 수정: [kiwoom_websocket.py](../../src/engine/kiwoom_websocket.py)는 각 raw row의 observer snapshot에만 packet ingress/source를 붙인다. live target에 저장하거나 기존 tick 시계·freshness 기준을 교체하지 않는다. [forward_collector.py](../../src/engine/scalping/micro_reversion/forward_collector.py)의 bounded64 tail은 `packet_received_at_ms`, `exchange_to_packet_receive_lag_ms`, `packet_to_normalization_ms`, 시각 근거와 trusted/missing 상태를 추가한다. aware ingress 결손·역전이면 null이며 원인 정상화에 사용하지 않는다.
- 정규화→observer 호출까지 지연은 기존 `receive_to_rejection_check_ms`가 소유한다. 이 계측도 OS/TCP 이전 세부 원인을 증명하지 않으며 전체 rejected row를 복원하지 않는다. 원래10초 guard, queue/REST budget, source exclusion, Provider hold, 주문/threshold/cap은 유지한다.
- 공식 gate: `official-reference.json`; `2026-09-10` HEAD 재조회 `234560d213acd8871ae344b5481aecd2f30287fa`, 같은 SHA의08:09:15 취득본 재열람. `kiwoom_docs` 부재를 보존하고 specs/core WS/realtime decoders·packets/packaged spec/Postman을 대조했다. wire/FID/REG·로그인·재연결 정책 변경은 없다.
- 검증: 0B/0D × trusted/missing/untrusted/future 시계와 실제 WS snapshot 경로 테스트. 기존 수신 시계 불변, source-only target 비오염, 원래 stale 거절 유지. 고정 benchmark 원본을 변경하지 않았다. [별도 측정](2026-09-10-micro-packet-diagnostic-latency-validation.json.txt)은 valid0B 5,000×5회 p95 0.026232ms/p99 0.035123ms, rejected0B 5,000회 p95 0.009969ms/p99 0.015438ms, tail64, drop/worker error0. 기존 한도1/2ms 유지.
- compatibility test의 과거 WS pin은 reviewed REG/auction 후속 commit을 반영하지 못했고 storage pin도 `d34bfffe`의 CLI stdout 분리 전이었다. 해당 변경의 기존 리뷰와 직접 diff를 확인한 후 현행 byte/AST pin을 명시 갱신했다. storage 구현·과거 측정·운영 guard는 변경하지 않았다. synthetic callback 검증은 전체 live 부하나 수익성 검증이 아니다.

### R3. 테스트의 운영 sim 상태 파일 쓰기

- 관찰: 운영 `data/runtime/scalp_live_simulator_state.json`이10:29:25 수정됐지만 내부 `updated_at`은 합성 날짜4/3이었다. 직전에는7/7이었다. 동시에 state-handler pytest가 진행 중이었다. 특정 PID의 write syscall까지 귀속한 증거는 없으므로 개별 테스트를 원인으로 단정하지 않는다.
- 코드 경로 확인: 공통 fixture가 pipeline·sell receipt·peak 원장은 격리했으나 `SCALP_SIM_STATE_PATH`/`SWING_INTRADAY_PROBE_STATE_PATH`는 운영 경로였다. [conftest.py](../../src/tests/conftest.py)에 각 테스트 tmp 경로를 적용하고 scalp default-path session 검사를 보존했다. 이후 시작하는 테스트에 유효하며 이미 진행 중인 타 테스트의 fixture를 변경하지 않는다.
- scalp/swing 성과 튜닝이나 과거 상태 복원 작업은 열지 않는다. 오염 가능 상태 파일의 active count는 미확인으로 남기고, 정상 runtime 원천이 새로 영속될 때 기존 `SimProbeIntradayCoverage0910`에서 확인한다. 9/9 보고의 sim21진입/21종료 및 CF38행 전부 비용/source 제외와 현재 상태를 혼합하지 않는다. 이번 창의 확인된 sim24행은 전부 actual_order_submitted=False/broker_order_forbidden=True다.

## 3. 현재 OPEN 전수 분류

모든 날짜는9/10이다. 기존 ID를 재사용하며 이 표는 새 실행 owner를 만들지 않는다.

| 기존 ID | Due window | 10:32 판정·이번 점검 | 남은 acceptance / 다음 시점 |
|---|---|---|---|
|WidgetEpisodeApprovedNextDayExecution0910|08:40~09:00|overdue_unresolved; 삼성/위젯/episode custody·정책·timer 대사|10:34/10:39/10:44 예약 프로세스와 이후 자연 신호·경제성|
|MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0910|08:40~08:45|overdue_unresolved; bounded rejection tail·collector 확인, R2 구현|현재 PID 반영·새 ingress receipt와 through-close 유효 원천|
|RuntimeEnvIntradayObserve0910|09:05~09:20|overdue_unresolved; PID375167 readonly verify PASS, main3완료와 R1 수리|수정 PID 소비·기존 outbox 자연 ACK·실제 비용 대사|
|SimProbeIntradayCoverage0910|09:35~09:50|overdue_unresolved; sim/real 분리 확인, 상태 파일은 blocked_missing_evidence; R3 수리|정상 runtime state의 새 영속과 active/closed 대사; 현재0으로 대체 금지|
|IntradaySourceQualityGateCheck0910|14:20~14:35|not_yet_due; 현재 발견 gap은 선행 기록|예정 당일 source audit|
|ThresholdDailyEVReport0910|16:30~16:45|not_yet_due|9/9 source 조회,9/10 main 조기 생성 금지|
|HumanInterventionSummary0910|17:00~17:15|not_yet_due|9/9 source 개입 분류|
|MainAIQualitySourceGapMainAIMicroExactEconomicIntersectionRepair0910|18:00~18:20|not_yet_due|현재 eligible cohort·Provider/정책/경제성 별도확인|
|CodeImprovementWorkorderReview0910|21:15~21:25|not_yet_due|기존 workorder와 새 gap handoff|
|MachineLifecycleTurnoverObjectiveFollowup0910|21:30~21:40|not_yet_due|별도 adaptive 구현·자연/경제성 owner 보존|
|AutomationTriggerDecisionSummary0910|21:40~21:55|not_yet_due|정상 trigger/run/skip terminal|
|PostcloseSourceQualityGateReview0910|21:40~21:55|not_yet_due|당일 원천 최종 품질/제외·consumer|

OPEN12개 분류, 미분류0. 기존 완료 PREOPEN/Scout2항목의 범위를 보존한다. WS10:05 자연 report는 새 snapshot/evaluated_at 수리를 소비했다. Census 다음12:00 report는 이 요청 종료 후이며 조기 재생성하지 않았다.

## 4. 반영 경계와 종료 증거

- 기존 사용자 재기동 승인은 유지한다. 다만 공유 작업트리에서 별도 adaptive 주문/위젯/registry 수정이 진행 중이며, 현재 PID가 읽을 전체 source의 review closure와 exact-date source provenance를 확인하기 전 단순 restart flag로 일괄 반영하지 않는다. 이 경계는 새 사용자 승인 요구가 아니라 재기동 선행 검증이다.
- R1/R2 코드 수정은 현재 PID375167에 아직 반영되지 않았으며 운영 원장 ACK와 자연 지연 분리는 미확인이다. R3는 새 pytest 프로세스의 테스트 격리 수정이다. code closure, deployment, natural acceptance, economic acceptance를 구분한다.
- 검증: receipt/lifecycle/sim 격리261 PASS·퇴역 ADM/LDM fixture18 SKIP, WS/collector/canary/market contract241 PASS, 합502 PASS. Black/compile/diff 및 print-only parser PASS. 검토한 R1~R3 코드 범위 미해결 finding0이며 deployment/source/economic acceptance는 OPEN이다. 종료 snapshot은 아래에 기록했다.

### 10:45 중간 보완

- NHN10:34:08 PID516640, SD바이오센서10:39:08 PID522730, SK이터닉스10:44:10 PID528752, SK텔레콤10:44:11 PID528785가 각 exact-date authority/preflight 후 기동했다. 10:44:58 네 state의 trade_date는9/10이고 READY/신호 평가·대기다. 단순 PID를 전체 경제성 acceptance로 올리지 않는다.
- 10:43:58 readonly runtime verify는 PASS, PID375167 missing0/mismatch0이다. source code 반영과 env 일치를 구분한다.
- sim 최신10:42:11 영속은 당일187660 active1을 포함한다.09:00 이후 unique sim entry3 /terminal1 /active1 /미대사1(024060)로 보존식이 미완료다. 확인47행은 모두 actual_order_submitted=False/broker_order_forbidden=True다. 현재 날짜 파일로 회복됐다는 이유만으로 test interference의 과거 소실이나 경제성까지 복원됐다고 하지 않는다. `sim-final-provenance.json`/`sim-natural-state.json`을 보존했으며 기존 SimProbe owner는 OPEN이다.

### 10:50 종료

- 최종 계좌 `broker-105012.json`, 조회10:50:11.682931: 삼성00593045주·SK텔레콤01767010주, SELL0022607/0018662/0015751 각잔량10주. 전시장 조회 성공, 각 exact registry owner1개, 이번 창 신규 중복 주문 관측0. 삼성E&A028050 broker0/registry10 과거 귀속 gap은 OPEN이다. raw 주문가능액83,393원과 operator floor 적용3,000,000원을 분리한다.
- main PID375167 유지. 10:43:58 readonly env verify PASS/missing0/mismatch0. 이번에 main 재기동·env/lock/정책/주문 변경은 하지 않았다. 독립 기계는 설치 timer가 자연 기동했으며, 삼성E&A 정상 NO_TRADE 외 네 오전후반 기계는 당일 READY/분봉 무신호다. 위젯10:50:05 cycle은 actual_order_submitted=false다.
- 09:00~10:50:11 main 실제 bundle3, 실제 완료3. raw sell_completed345회는 outbox 재시도 중복을 포함한다. v2.14 OpenAI DROP21/WAIT13/BUY0, v2.13 OpenAI DROP7/BUY0; provider 미호출 DROP24(v2.14 17/v2.13 7)는 별도다. 원문 BUY0을 main 체결0으로 보고하지 않는다.
- collector10:50:01: 0B775,719/0D806,841 callback, 유효 enqueue688,505/708,319; worker도 같은 수까지 진행. queue full·writer error0, writer5+6, free33,589,919,744bytes. 누적 timestamp rejection174,492/진단tail64이며 전체 결손 복원 또는 Provider hold 해제가 아니다. 새 packet 시각 계측은 PID 미반영이다.
- System Error Detector10:50:03은 warning; window에 따라 fail/pass가 바뀌어도 R1 미반영 outbox의 자연 ACK 완료로 보지 않는다. 저장한 원본 leg·in-memory 검증·현재 운영 pending을 구분한다.
- 최초 OPEN12개 전수 점검/분류, 최종 OPEN12개·중복0·미분류0.4개 도래 owner는 부분 점검/수리와 남은 acceptance를 기록했고8개 미래 owner는 not_yet_due다. 다음 정규 작업과 자연 확인은 기존 체크리스트 owner에서 계속한다. 이 요청으로10:50 이후 지속 모니터링을 자동 연장하지 않는다.
- reviewed-source-hashes8개를 저장했고 최종 비교 불일치0, Black/compile/diff/link/print-only parser PASS. 이번 코드 범위502 PASS·퇴역 fixture18 SKIP·미해결 finding0. 공유 작업트리의 별도 Entry/위젯/주문 수정까지 finding0으로 승인한 것은 아니다. 현재 source 변경 전체의 재기동 전 검토가 닫히면 기존 사용자 재기동 권한 아래 broker 대사→graceful handoff→새 PID/env/WS first-data→R1 outbox ACK/R2 새 receipt를 확인한다.

외부 sync는 실행하지 않았다. 필요 시 사용자가 실행할 표준 명령은 다음 하나다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
