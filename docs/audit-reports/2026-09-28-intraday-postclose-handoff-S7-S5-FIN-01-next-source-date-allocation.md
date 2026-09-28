# S7 후속 — `S5-FIN-01` 다음 자연 source date allocation 실제 child

실행일: **2026-09-28 KST**. 인계: [직전 S7 차단 보고서](2026-09-28-intraday-postclose-handoff-S7-S5-FIN-01-allocation-actual-child.md), [선행 영수증 S6](2026-09-28-intraday-postclose-handoff-S6-S5-FIN-01-prerequisite-generation.md). **판정: BLOCKER (`source_not_yet_closed`).** 13:56 KST의 다음 자연 source date는 9/28이고 다음 거래일 effective date는 9/29다. 9/28 완료 widget·episode 연구와 장후 native capacity가 아직 없으므로 새 선행 stage와 `research_allocation` 실제 child를 실행하지 않았다. 빠진 원천을 빈 표본·OFF·no-edge로 해석하지 않는다.

## 1. 입력·선택 코드의 읽기 전용 사전 대사

9/28은 KRX 거래일이고 코드의 `_next_krx_trading_day('2026-09-28')`는 `2026-09-29`를 반환했다. 13:56 KST `read_studies(2026-09-28)`는 `missing=['widget','episode']`, 읽은 완료 family **0**이었다. 9/29 정책 세대의 시간 가드 `_publication_update_allowed`는 당시 `True`였지만, 연구·native 원천 부재를 대신하지 못한다.

| 단위 | 13:56 KST 읽기 전용 관측 | S7 분모/판정 |
| --- | --- | --- |
| widget 완료 연구 / stage | `widget_symbol_signal_policy_research_2026-09-28.json`, `widget_policy` terminal, EOD status 모두 없음. | 원본·유효·제외·격리·미관측 symbol 건수 **미관측**; 새 stage 미실행. |
| episode 완료 연구 / stage | `low_price_two_leg_expanded_candidate_research_2026-09-28.json`, `episode_policy` terminal 없음. | profile·symbol 분모 모두 **미관측**; 새 stage 미실행. |
| postclose native capacity / stage | `capacity_source_2026-09-28.json`, native cash·inventory, `research_capacity` terminal 없음. | 원본·유효·격리 native 파일 분모 **미관측**; 새 stage 미실행. |
| 장중 opening capacity | 별도 `opening_capacity/capacity_source_2026-09-28.json` 존재, **1,048 bytes**, SHA `fa14734a760301431c4621fdd4541a9cc510e29459e16566903ba410f1df2911`. | 장중 원천이며 장후 capacity terminal로 승격하지 않음. |
| widget 주문 state | `widget_signal_auto_trade_state.json` 존재, **144,856 bytes**, 관측 시 SHA `af37e65514b0e7225ff469c3a67eccc8209bb4217235c1a215dc9c205f817234`. | 현재일 중 계속 바뀔 수 있어 최종 source-date projection으로 봉인하지 않음. |
| 9/29 정책 세대 | widget·episode 정책 파일과 publication manifest 모두 없음. | 원천 완료 전에 빈 정책/manifest를 만들지 않음. |
| allocation | `research_allocation` terminal·평가 보고서 없음. | 후보 grid·holdout·비용·원본/유효/격리·cold/warm 자원 모두 `unobserved`/`null`; child 미실행. |

선택 포인터 `data/runtime/runtime_release_selection.json`의 byte SHA는 `51c7d4223f031a089d40c97bcadd043addeeee0515f46b28bade846fa02dae6c`이며 commit은 `8e8def53c6a6f66f45c36f2c2cd479c726fe3786`, release root는 `kiwoom-read-cadence-20260928-8e8def53`이다. 작업본 HEAD도 해당 commit이지만 미커밋 변경이 있다. `machine_research_closed_loop_refresh.code_contract()` digest는 **작업본 `c7f05e86782f56412ecc3814aec7ffe7ecac7743d5b2b77d491b3abb69d4cf76`**, **선택 릴리스 `145ba1ce76f741020b8e67a1b80f059fa7f987dacc283f646215aa34b11be4c8`**로 다르다. 예를 들어 `low_price_two_leg_tuning.py` byte SHA도 작업본 `4a3d8918509cbde8fa9ef68f9a0f2af9dc5ab3d62fbf42210e870060163f32f0`, 릴리스 `cacabd048e9143794648ddce4a19a7b1ad1b891508d75a50a43380d9428f35d1`이다. 선택 포인터, 작업본 stage 코드, 실제 PID 소비는 각각 별도 상태이며 이 사전 조사는 PID를 확인하지 않았다.

## 2. 실제 dispatch와 격리 실행 gate

[`postclose_summary_handoff.py`](../../src/engine/automation/postclose_summary_handoff.py)의 9/28 직접 명령을 읽기 전용으로 대사했다. widget·episode recovery는 각각 `machine_research_closed_loop_refresh --source-date 2026-09-28 --family widget|episode --write --source-wait-sec 0`, capacity는 `research_native_capacity_source --source-date 2026-09-28 --write`, allocation은 같은 refresh의 `--family allocation --write --source-wait-sec 0`이다. 각 terminal은 `data/report/postclose_stage_terminal/2026-09-28/` 아래에 쓰이고 allocation 첫 입력은 widget·episode·capacity terminal **3개**다. widget은 EOD status, capacity는 native cash·inventory를 추가 입력으로 검증한다. 연구·policy refresh 및 allocation 보고서, runtime 정책/publication, stage/연구 lock과 임시 파일도 별도 root로 격리해야 한다.

다음 실행의 순서는 아래와 같다. 이번에 단계 1의 원천 부재가 확인돼 단계 2 이후는 진행하지 않았다.

1. **원천 완료 확인:** 9/28 완료 연구 두 파일의 날짜·status·원본 byte SHA·profile/symbol 분모, postclose capacity·cash·inventory·owner와 source-date widget 주문 projection을 고정한다. 누락·late·중복·손상·valid-empty를 각각 분류한다. 9/29 정책/manifest의 기존 세대도 검사한다. 현재일 widget state의 13:56 SHA를 최종 입력으로 재사용하지 않는다.
2. **코드·경로 고정:** 작업본과 선택 릴리스의 실제 code contract, diff, 입력 SHA를 분리한다. 운영 root를 mount하지 않는 **새** 독립 namespace에 같은 절대경로를 만들고 코드 읽기 전용, `data`·lock·tmp 쓰기 격리, socket/provider 차단을 probe로 입증한다. 연구 JSON이 바뀐 직전 `/tmp/kor_s7_allocation_actual_child_20260928`는 clean root로 재사용하지 않는다. 이전 격리 audit hook의 `fdopen` 오탐 수정을 포함하되 guard 자체를 먼저 검증한다.
3. **조건부 stage 실행:** 정책 세대 갱신 창이 열린 동안 완료 원천의 복제본에서 widget·episode·capacity 새 attempt를 각각 실행하고 source date·run ID·코드/입출력 SHA·`stage_receipt_issues=[]`를 검사한다. 세 terminal이 모두 유효할 때에만 allocation 실제 child를 실행한다. 기존 manifest 삭제, 시각/effective date 변조, 옛 성공 receipt 강제 수용은 금지한다.
4. **측정과 결손 인계:** 동일 clean 입력의 별도 root에서 첫 회·반복 회를 비교하고, child 내부 wall·CPU·peak RSS·I/O와 provider budget을 기록한다. cache 재사용과 계산을 분리한다. family별 원본·유효·제외·격리·미관측을 서로 다른 단위로 유지하고 비용 원천이 없으면 경제성은 `null`로 둔다. 데이터·세대·성능 코드 결손이 확인되면 해당 producer/첫 reader owner의 S6 재수리로 돌린다. 원천이 생기기 전에 정책 갱신 창이 닫히면 해당 날짜를 BLOCKER로 남기고 정책을 삭제·재출판하지 않는다.

9/23 운영 capacity 실패·allocation 보류·summary/controller 차단과 직전 9/23 격리 widget 출판 차단은 역사적 상태로 보존한다. 이번 preflight는 전체 15 stage·strict·controller·detector, 선택 릴리스·PREOPEN·PID 또는 자연 비용 조정 수익성 수용이 아니다. `S5-FIN-05`는 새 자연 장후 원천에서 재현할 별도 묶음이다. 정규 장후작업·PREOPEN·배포·실주문·취소, 정책·수량·timeout·서비스·provider·threshold 변경은 실행하지 않았다.

자가 리뷰: 다음 거래일·원천 상태를 실제 경로와 `read_studies` 양쪽에서 확인했고, 장중 opening capacity와 장후 capacity, 현재일 state와 완료 projection, 작업본 코드와 선택 릴리스를 구분했다. repository 코드는 변경하지 않았다. 문서 상대 링크 **3개 유효**, trailing whitespace **0**, print-only checklist parser **PASS(32 task)**, `git diff --check` **PASS**다. 원천 완료 전이라 pytest·Python compile·wrapper `bash -n`·실제 child 성능 측정은 이번 read-only gate에 해당하지 않는다. 외부 Project/Calendar 동기화는 실행하지 않았다.
