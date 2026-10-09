# Main 보유청산·익절 원천 계약 구현 리뷰

2026-10-09 초기 회차 기록. [계획](../proposals/main-holding-profit-exit-runtime-and-postclose-remediation-plan-2026-10-09.md)의 HP0–HP5 코드 구현과 반복 리뷰·검증을 완료했다. **이 초기 회차에는 공식 실제 비용 수집 원천 확정·배포·재기동·운영 장후 재생성을 실행하지 않았다.** 이후 사용자 승인으로 수행한 공식 원천 수집·소비 보완과 통합 배포의 현행 결과는 [후속 리뷰](holding-profit-exit-official-cost-source-integration-deployment-review-2026-10-09.md)를 따른다. 아래의 미실행·미커밋·원천 미확정 표시는 초기 시점의 이력이다.

## 기준과 권한

- 작업 시작 HEAD: `23fde69cb6e808e3eb7eab4d5586248449c020c6`. 구현 전 작업본은 clean이었다. 현재 변경은 미커밋 작업본이다.
- 10:02 KST 재확인 selector: `main-integrated-bottlenecks-20261009-v1`, commit `f36b306cbd69ba8fbefdc7bc48f09b10144bdf44`; `actual_pid_consumed=false`, `awaiting_scheduled_main_start_20261012`. 이번 코드는 그 릴리스에 배포되지 않았다.
- 기존 하드스탑·보호·비상·브로커/계좌·주문/수량·시세 freshness·Main/manual 수탁·운영자 lock 및 퇴역 executor 경계는 유지했다. 기존 초기 보유 AI 15셀에 새 경제성 승인 조건을 추가하지 않았다.
- 신규 비용 대사 모듈은 체결 후 자료 검증 역할이므로 `src/engine/lifecycle`에 두었다. 새로운 engine-root 모듈이나 중복 구현 wrapper를 만들지 않았으며 location gate 회귀가 통과했다.
- 오늘 실행 owner는 [10/9 checklist](../checklists/2026-10-09-stage2-todo-checklist.md)의 `HoldingProfitExitSourceContractRepair` 하나다. 미래 10/12 checklist를 오늘 owner로 사용하거나 수정하지 않았다.

## producer에서 consumer까지 구현

| 대상 | 구현과 검증 | 남은 수용 |
|---|---|---|
| F1 / HP1 | 보고서 기본 window와 기계식 cohort가 `policy_refresh_start_date()`의 9/29 forward 경계를 소비한다. 선택기와 bootstrap도 같은 metadata를 검증한다. 명시적 이전 기간은 audit-only다. | 실제 후속 후보의 자연 비교·승격은 이번 코드 검증과 별개다. |
| F2 / HP2 | 정확한 모든 체결 leg 비용 대사 성공/실패 경로, configured/exact 층 분리, 비용 revision→census→sidecar→holding report→manifest 재사용 검증 및 성과 consumer 연결을 구현했다. | 공식 원천의 체결별 비용 배분과 계좌/owner 결속 생산은 미확정이다. 실제 비용 수집 완료가 아니다. |
| F3 / HP3 | live/replay가 순수 유예 허용 함수를 공유한다. 최초 crossing, 동결 AI 판단, 유예 해제와 실제 SELL 허용 시각을 각각 대사한다. 검증된 유예는 정상 incumbent 경로로 인정한다. | 후보별 실제 AI 입력을 재구성할 수 없으면 검열한다. 자연 청산·성능 개선은 미관측이다. |
| F4 / HP4 | 0.4 고정 검사 대신 정책 vector/classifier/hash·시장·날짜·검증 PID를 검사한다. 승인된 합성 0.5는 통과하고 다른 세대는 거부한다. 같은 날 재기동 전 PID의 검증도 보존한다. | 0.5 정책을 실제 발행·적용한 결과는 아니다. |
| F5 / HP4 | v2의 의미 검사, `position_key + buy_fill_identity + signal_id`별 진행, 경제 상태를 분리한다. 제출 전 대기·제출 후 미종결·완료를 구분하고 terminal의 주문/시간/잔량을 검사한다. | 실제 식별자가 없는 역사 row는 source gap이며 완료를 추정하지 않는다. |
| F7 / HP4 | sentinel/semantics가 같은 당일 cutoff와 event generation을 사용한다. 투표 requested/received/persisted와 비용·후행 관측 가용 시각을 함께 제한한다. | 과거 가용 정책/원천을 복원할 수 없으면 unassessed/source gap이다. |
| HP5 | runtime summary가 코드 결함·원천·진행·경제 상태를 구분하며 generator가 식별 결함만 같은 stable owner로 인계한다. wrapper의 비용/봉인 후검사와 handoff code pin을 보완했다. | 운영 재생성·strict/controller/PREOPEN·새 PID의 자연 소비는 실행하지 않았다. |
| F6 / HP6 | 기존 초기 15셀과 provisional/null EV 의미를 유지했다. 자동 후속 최적화를 구현 완료로 표시하지 않는다. | 별도 구현/권한 범위다. |

## 실제 비용 원천 계약과 미확정 사항

공식 [Kiwoom 저장소](https://github.com/Kiwoom-Securities/Kiwoom-REST-API)의 revision `953e5dbff123f437ab4d11a78a95191a685eb51f`를 2026-10-09 09:26:22.778491 KST에 확인했다. inspected paths는 `kiwoom/specs.py`, `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/core/client.py`, `kiwoom/realtime/decoders.py`, `kiwoom/realtime/schemas.py`, `postman/kiwoom-openapi.postman_collection.json`이며 이 revision에는 `kiwoom_docs`가 없다. [필드 확인 근거](../../data/report/holding_profit_exit_implementation/2026-10-09/official-cost-contract-review.json)를 보존했다.

ka10072/73의 일자별 종목 비용, ka10074의 합계, realtime 00의 FID 938/939는 당일 수수료·세금 자료다. kt00007/kt00009에는 이 참조에서 비용 필드가 없다. 이 자료로 포지션의 모든 최초 BUY·ADD·부분 SELL에 체결별 실제 비용을 어떻게 배분하는지는 확정할 수 없다. 일별 누적 비용을 부분 체결마다 합산하거나 수량 비례로 임의 배분하는 adapter를 만들지 않았다. REST/WS 요청·parser·FID mapping·인증·계좌/주문 호출을 변경하거나 호출하지 않았다.

[비용 대사 모듈](../../src/engine/lifecycle/broker_cost_reconciliation.py)은 검증된 producer가 제공할 `data/runtime/holding_actual_costs/{원래 완료일}/{record_id}.json`을 읽는다. 현재 이 비용 경로가 없으므로 자연 원천 상태는 `cost_source_unavailable`이다. schema는 `holding_actual_cost_settlement_v1`이고 필수 결속은 다음과 같다.

- 포지션·종목·Main owner·계좌 scope hash·BUY fill identity·원래 완료일·revision·비용 가용/대사 시각.
- exact-execution statement의 KRW 단위와 raw/hash, 모든 leg의 BUY/SELL·거래일·주문/체결번호·route·수량·가격·수수료·세금. 원시 statement와 정규화 legs가 일치해야 한다.
- 모든 최초 매수·추가매수·부분 매도의 빠짐없는 coverage, 최종 매수/매도 수량 일치, 실현손익의 체결대금·비용 대사. 실제 비용 0과 실현손익 0은 명시된 경우에만 인정한다.

이 self/raw hash는 자료 무결성 계약이며 공식 배분 의미의 증거를 대신하지 않는다. 원천 producer가 계좌 scope와 Main owner를 정확히 결속해야 하며 파일을 임의 작성했다고 공식 비용 증명이 생기지 않는다. 해당 원천 확정이 남은 HP2다. 성공 fixture의 actual +0.95%와 configured +0.8%는 다른 층으로 보존되며 DB configured 값이나 운영 `TRADE_COST_RATE`를 덮어쓰지 않는다.

D일 완료 거래에 D+1 비용이 도착해도 원래 완료일과 train/holdout 소속을 유지한다. cutoff 전에는 pending/unavailable이고 비용 revision이 바뀌면 현재 generation에 맞지 않는 report/census/sidecar/manifest의 재사용을 거부한다. 봉인 manifest는 fsync 후 원자적으로 교체한다. 큰 원본을 무제한 재파싱하는 우회를 추가하지 않았다.

## 반복 리뷰에서 보완한 사항

초기 회귀에서 실제 비용과 configured 비용의 결손을 같이 다뤄 수량 복구까지 막던 경로를 분리했다. exact 비용이 검증된 경우 configured 비용과의 불일치는 원래 값을 보존하면서 exact 층을 인정하고, 수량·체결대금·권한 결손은 그대로 거부한다.

incumbent replay가 정상 AI VETO 유예를 지나치게 이른 기계 매도로 모델링하던 경로를 수정했다. 검증된 실제 허용 시각을 별도 대사하며, 다른 후보 crossing에서 실제 AI 판단·후속 경로를 알 수 없으면 가상의 AI 응답을 만들지 않고 검열한다. live PASS/INSUFFICIENT에 추가 quote 조회를 붙이지 않으며 관측 로그 실패로 기존 보호청산을 막지 않는다.

마지막 재검토에서는 terminal이 같은 signal/buy generation을 갖더라도 다른 주문번호, 제출 전 시각, 불명확한 terminal binding 또는 비영(미확인) 잔량이면 `completed`로 진행시키지 않도록 보완했다. 기존 매도 차단·재평가 stage의 명시 목록을 신호에 연결하고, 더 최근 exit 허용 뒤에는 과거 guard를 현행 대기로 표시하지 않는다. 비용 합산의 숫자 overflow도 실제 손익 검증으로 통과하지 않는다.

동일 PID/manifest를 반복 검증해도 최초 PID 정책 영수증을 유지한다. PID 영수증은 완성된 임시 파일을 fsync한 뒤 기존 첫 영수증을 덮어쓰지 않는 방식으로 원자 발행한다. 발행 실패 시 불완전 영수증과 임시 파일을 남기지 않으며 exact-date 불일치는 거부한다. 비용 입력은 파일당 256 KiB·완료일당 10,000개·총 읽기 32 MiB, PID 영수증 소비는 파일당 32 KiB·당일 최대 256개이고 목록 수집도 그 한도를 넘기지 않는다. 의미 event fingerprint는 행 단위로 해시하며 대형 AI 비교 원장을 복제하지 않는다.

## 검증과 미실행 범위

- 통합 23개 대상 회귀: **1,846 passed / 37.62초**. [최종 통합 로그](../../tmp/holding-profit-exit-validation-20261009/pytest-final.log).
- 마지막 비용 읽기/overflow 보완 후 비용·trade review·snapshot·sentinel·freshness 회귀: **251 passed / 4.04초**. [후속 검증 로그](../../tmp/holding-profit-exit-validation-20261009/pytest-final-cost-consumers.log).
- 마지막 PID 영수증 발행/목록 한도 보완 후 bootstrap·sentinel·PREOPEN·handoff 회귀: **137 passed / 3.34초**. [로그](../../tmp/holding-profit-exit-validation-20261009/pytest-final-pid-handoff.log). 통합/후속 검증 숫자는 중복 사례를 포함하므로 합계 거래 수나 독립 표본 수가 아니다.
- 변경 Python 30개 compile, wrapper `bash -n`, `git diff --check` 통과. print-only parser exit 0, backlog 21개 중 repair owner는 오늘 checklist에 정확히 1개다. [parser 출력](../../tmp/holding-profit-exit-validation-20261009/backlog.log). 로컬 링크 47개와 미래 10/12 checklist의 SHA `6a5428aaa23200c9a7d71ff6ac47286908237d29dfcab6d55d1dd36cb69751b9`를 검증했다.
- 자연 provider/broker 호출 0건, 정책 발행·selector 변경·재기동·운영 보고서 재생성·외부 Project/Calendar sync 0건. 미래 봉인 checklist SHA는 유지한다.

리뷰 범위의 코드 지적은 수정·재검증했다. **HP2 공식 원천 수집, 배포/PID 소비, 자연 latency·체결·비용·후속 경제성은 완료로 선언하지 않는다.** 다음 운영 실행에서는 새 코드의 승인된 배포와 원래 source date의 산출물 세대 재검증을 따로 수행해야 한다.
