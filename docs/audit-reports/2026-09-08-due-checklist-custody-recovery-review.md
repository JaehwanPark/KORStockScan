# 9/8 미해결 원장 복구·현시각 체크리스트 실행

실행 시작15:45:52 KST. 사용자 지시: 미해결항목 처리 후 코드리뷰, 현시각 기준 체크리스트 점검 및 실행. [15:00 관찰](./2026-09-08-intraday-monitoring-1500.md)의 당시 미해결 상태는 보존하고 아래 후속 실행으로 대사한다. [원본·preview·적용·소비자 증거](./2026-09-08-due-checklist-custody-recovery-evidence.json)를 함께 보존했다.

## 완료한 복구

| Owner / 원장 거래일 | 검증한 영수증 | 복구 |
| --- | --- | --- |
| 한국전력 오전 /9/8 | 원래 target0021943,10주33900 전량 체결; 다른 target0021477은 이미 완료 | HELD10→COMPLETE0, 이미 완료된 leg 보존 |
| SK텔레콤 오후 /9/3 | 원래 target0051113,10주88000 전량 체결 | HELD10→COMPLETE0, 다른 NO_FILL leg 보존 |
| 제주반도체 오전 /9/3 |9/3 자기 BUY0014749/0014750 각10주,9/4 유일한20주 수동 SELL0013842/71500. 해당 종목 profile은 이 owner 하나이고 다른 날짜 매도 추가 없음 | 기존 whole-owner manual-exit 도구로 HELD20→COMPLETE0. 기존 target 미체결을 target 성공으로 바꾸지 않고 수동 청산 귀속 |
| 팬오션 오전후반 /9/4 | 수동 정정 SELL0050421/0050454 각10주6000, 각각 원래 target0025218/0025279에 `ori_ord`로 결속 | 기존 per-leg manual-exit 도구로 HELD20→COMPLETE0 |
| SamsungE&A 오후 /9/8 | 이미15:12 state에 적용된 수동 SELL0059615,10주49400, `ori_ord=0055228` | state를 다시 수정하지 않고 기존 `register_reconciled_manual_exit`로 공통 owner registry 잔여10→0 |

위4개 HELD service의 MainPID0/inactive와 state mutex 비점유를 확인했다. 거래일·원래 주문번호·기존 leg 수량·attempt_consumed를 보존하고 신규 episode나 주문을 만들지 않았다. 기존 target 체결과 수동 청산을 구분했다.15:57:44→15:59:26 KRX/NXT broker 잔고·미체결이 동일하다. 삼성30주와 삼성중공업10주, 미체결 SELL0062568/0018672는 보존했다. SamsungE&A 공통 원장 후속 보완도 이미 발생한 청산의 귀속이며 새로운 매도가 아니다.

현재 삼성 SELL0062568은 영웅문S# 수동 정정(`ori_ord=0061951`,30주277000)이고 등록된 자동 target0057234와 번호가 다르다. 이를 자동 주문으로 흡수하거나 취소·재제출하지 않았다. 수동 successor 체인의 전체 owner 연결 및 widget 실제 target 추적은 기존 WidgetEpisode acceptance에서 별도 확인한다. 공통 registry의 주문번호 충돌0과 수동 주문의 미등록을 혼동하지 않는다.

## 코드와 최종 리뷰

- 기존 `src/trading/order/manual_episode_exit_reconciliation.py`에 `--original-target` 복구 모드를 추가했다. 새로운 engine-root 모듈·worker·cron은 만들지 않았다. inactive HELD/consumed state,2개 leg·기존1/10주 계약, exact owner schema/owned order/date/symbol/SELL/full fill/양수 체결가와 합산 수량을 검증한다. 완료 leg와 열린 leg 사이 target 재사용도 차단한다.
- 원본 state SHA와 검증 영수증 SHA를 preview confirmation에 결속한다. 실제 서비스 lock 점유, preview 이후 state·영수증 변경, 다른 owner·날짜·종목, partial/missing/duplicate receipt, quantity/aggregate 충돌이면 적용하지 않는다. state의 원래 거래일을 바꾸거나 새 진입을 호출하지 않는다.
- 수동 복구에도 복구 시각을 실제 체결 시각으로 기록하던 문제를 보완했다. dated order receipt만 있으면 `target_filled_at`은 빈 값이며 `target_fill_reconciled_at`과 timestamp unavailable 사유를 남긴다. Samsung report consumer도 이 명시적 결손을 자정 체결시각으로 대체하지 않는다. 과거 이미 작성된 영수증은 덮어쓰지 않는다.
- 복구 command 결과의 `runtime_effect`는 apply 시 true, 범위는 `custody_terminal_only`로 명시했다. 실제 주문 false와 원장 변경을 구분한다. 이번 최초 manual apply 영수증은 이 마지막 metadata 보완 전의 legacy false 필드를 보존하며, 실제 custody state 변경이 있었음을 본 기록과 evidence에 명시한다. 원본 영수증을 사후 수정해 새 실행으로 가장하지 않는다.
- 기존 call-local submit parent 수리도 직접 consumer·drought handoff 회귀에서 재확인했다. 현재 main PID682672는 유지되므로 새 telemetry의 PID 반영·자연 이벤트 확인은 별개다. 다른 세션의 AI/전략/자동화 변경은 보존했고 임의 배포·재기동하지 않았다.

`korstockscan-review-gate`에서 producer→state→low-price/Samsung consumer→owner registry, silent-fail·권한·동시 변경과 historical timestamp 경계를 재리뷰했다. 최종 **531 tests PASS**, compile와 `git diff --check` PASS. 검토한 수정 범위의 미해결 코드 finding0. Python 변경은 위2개 구현 파일과 기존 manual-exit 회귀 테스트이며, 새 CLI가 자동 주기 복구를 설치한 것은 아니다. 향후 HELD와 late-fill의 재발 감시·공통 registry 수동 청산 handoff 확인은 기존 owner를 유지한다.

## 공식 Kiwoom 근거

15:49 전후 현재 upstream `234560d213acd8871ae344b5481aecd2f30287fa`를 조회·검토했다. 이 revision에는 `kiwoom_docs` 디렉터리가 없어 과거 문서가 현재에도 있다고 주장하지 않는다. [공식 spec](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/234560d213acd8871ae344b5481aecd2f30287fa/kiwoom/_data/kiwoom_api_spec.json)의 kt00007/ka10075, `kiwoom/specs.py`, `kiwoom/core/client.py`, Postman을 교차 확인했다. POST `/api/dostk/acnt`, dated `ord_dt`, 전체 거래소 조회, continuation header와 `ord_qty/cntr_qty/cntr_uv/ord_remnq/ori_ord`를 확인했다. 기존 reviewed loader와 shared-read budget을 그대로 사용했고 request/response parser·broker 주문·retry/동시성·token refresh를 변경하지 않았다. 응답 `ord_tm`은 주문시각이므로 체결시각으로 쓰지 않는다.

## 현시각 체크리스트 실행 결과

| 기존 ID / Due | 실행과 판정 | 잔여 |
| --- | --- | --- |
| IntradaySourceQualityGateCheck0908 /14:20~35 |15:48~51 기존 writer-safe 감사 `--write` 실행.212051 events/129 stages; 결손1행 격리·backup/manifest 보존, 재검증 hard gap0, tuning_input_allowed=true | 장중 점검 완료. score_prior_band `neutral_or_unknown`48/307 warning은 장후 source/workorder 기존 owner로 handoff; 전체 날짜 차단 아님 |
| RuntimeEnvIntradayObserve0908 /09:05~20 |15:52 current PID682672 read-only verify PASS, missing/mismatch/finding0. 최신15:20 BUY Funnel AI224/budget588/latency91/submit0 | provenance 관찰 실행. SUBMIT_DROUGHT_CRITICAL과 자연 submit/실현 EV는 OPEN;15:20 이후 Sentinel 다음 설치 슬롯16:00 전 공백을 dead로 오판하지 않음 |
| MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0908 /08:40~45 |15:52 micro trade994521/depth1088273, writer4+4, queue/writer 오류0, disk 약6.93GB, 자동중지 없음 | 현재 수집 정상; NXT 포함 through-close·과거 ingress exclusion/Provider hold 수용은 OPEN |
| WidgetEpisodeRecommendationApplyAcceptance0908 /08:57~14:45 | 원장4개와 SamsungE&A 공통 custody를 위 영수증으로 복구, 현재 보유/수동 주문 분리 |080220 자연 효과·정확한 비용·현재 수동 successor 추적은 OPEN. code/state closure와 실수익 수용 분리 |
| ThresholdDailyEVReport0908 /16:30~45; HumanInterventionSummary0908 /17:00~15 | 예정 전 확인 | `not_yet_due`; 선행 원천·자연 owner를 앞당겨 중복 실행하지 않음 |
| 나머지9/8 POSTCLOSE ID /20:10~21:55 | source/workorder/AI/finalization의 실제 예정창 전 | `not_yet_due`; 장중 수리를 장후 전체 PASS로 바꾸지 않음 |
| OperatorPolicySuccessionAcceptance0908 /9/9; ScannerLookupAttentionCalendarMaintenance1002 /10/2 | 미래 날짜 | `not_yet_due`; 다른 승인 작업의 설계 OPEN을 이번 custody 완료에 합산하지 않음 |

Source-quality 결손은14:18:07 record41204/386380의 minute-window row1개다. `data/source_quality/raw_row_exclusion/2026-09-08_20260908T154858342379+0900/manifest.json`과 gzip 원본 백업에서 전수 격리했다. 감사 후 유입되는 다른 시각·NXT 원천까지 승인한 것은 아니며 장후 preflight는 예정대로 다시 수행한다.

15:15:31 자연 census v4는 `partial_diagnostics_ready/scoped_diagnostics_available`다. KRX raw296=eligible19+excluded277(구간239/master38), eligible19의 첫 미도달은 not-promoted12/late5/unobserved1/fast-gap1이며 provider reach0이다. 구간별 진단 코드 반영은 확인했지만 KRX19는 선언20 floor 미달이고 경제성도 미달이다. NXT premarket35개 구간 진단과 전시장 포착률을 합치지 않는다. 이미 별도 검토에서 닫은 v4 수리를 무표본 때문에 재개하지 않았으며 source/native recommendation→장후 workorder는 기존 예정 owner에서 확인한다.

수리로 새 수익을 만들었다고 주장하지 않는다. 과거 체결과 매도가의 귀속은 복구됐지만 exact fee/tax/체결시각·rolling 경제성은 미검증이며 실현손익 headline은 null을 유지한다. 현재 main의 신규 telemetry 반영을 위해서는 다른 변경까지 검증된 별도 배포/기동 receipt가 필요하다.

최종 종료 확인16:10 KST:16:00:56 자연 Sentinel에서도 main submit0이다. 마지막 보완에서 원래 target보다 낮은 체결가는 original-target 복구로 인정하지 않고 manual/별도 receipt 경계로 차단하는 회귀를 추가했다. 실제 적용한 원본 target 영수증은 이 검사와 consumer contract를 모두 충족한다. 최종 parser에서 source-quality 장중 완료 ID는 OPEN0회, 남은 Runtime/Widget/Micro/Workorder owner는 각각1회다. 외부 Project/Calendar sync는 실행하지 않았다.

필요 시 사용자가 실행할 표준 sync 명령:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
