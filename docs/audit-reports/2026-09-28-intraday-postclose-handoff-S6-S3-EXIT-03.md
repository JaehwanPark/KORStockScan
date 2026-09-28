# S6 `S3-EXIT-03` — 보유 판단→SELL 직접 신호 인계

실행일: **2026-09-28 KST**. 범위: [S3 `S3-EXIT-03`](2026-09-27-intraday-postclose-handoff-S3.md), [SELL terminal·비용 원천](2026-09-28-intraday-postclose-handoff-S6-S3-EXIT-01.md), [현재 체크리스트](../checklists/2026-09-28-stage2-todo-checklist.md)의 `[HoldingProfitExitSemanticClosure0928]`·`[HoldingExitPositionOutcomeLineageClosure]`. **판정: 새 원천의 결정→첫 SELL ACK→첫 장후 reader→보유 평가 인계를 작업본 fixture에서 수리했다. 9/23의 직접 판단·정확 비용·완전한 사후창과 새 자연일 소비는 여전히 미관측이다.** 선택 릴리스·PID·정규 장후작업·PREOPEN은 이번 수용 범위가 아니다.

## 재현·분모·영향

| 범위 | 원본 | 직접 유효 | 격리·미관측 |
| --- | ---: | ---: | --- |
| 보존된 9/23 raw 감사의 `exit_signal` | 이벤트 53 | 같은 주문·BUY 세대에 결속된 완료 판단을 당시 산출물에서 증명한 건수 0 | 53은 후보/반복 신호 이벤트 분모다. 완료 8과의 차이 45를 유실·격리 거래로 계산하지 않는다. 53개의 행별 격리 수는 과거 영수증에서 미산출이다. |
| 보존된 9/23 완료 trade-review | record 8, SELL 제출 8, 완료 표시 8 | 명시적 결속 `0/8` | `exit_signal.inferred=true` 8/8, effective threshold 직접 영수증 0/8. SELL 2건 `47531`·`47515`의 정확 execution·broker 실제 비용은 앞선 S6대로 `unknown`·`null`이다. |
| 보존된 9/23 후행 SELL | 진단 평가 후보 6 | 완전한 1/3/5/10분 창 0 | `partial_window` 6. 나머지 완료 2건은 정확 fill 시각이 없다. 이 분모를 판단 신호 53과 합치지 않는다. |
| 새 fixture의 같은 주문 세대 | 결정 1→ACK 1→terminal 1 | 직접 신호 1 | 구세대·다른 주문·SHA/날짜/수량/호가 변조·sim scope·상충 중복은 격리 상태, 결정 또는 제출 원천 부재는 미관측 상태로 남긴다. 재시도 동일 중복은 주문 1개로 본다. |

9/23 근거는 S3 감사와 보존된 [SELL 수리 보고서](2026-09-28-intraday-postclose-handoff-S6-S3-EXIT-01.md)의 원천 인계다. 압축 `pipeline_events_2026-09-23.jsonl.gz`의 기존 해제 논리 SHA는 `4db035e3b3915644ee95fef82d50b54f0dcdfbbf6c69a19dab15594a3d1c758c`, 보존된 `trade_review_2026-09-23.json` SHA는 `6be7f624889f21384a5c08a2fb8240308477c512d77cf1e1a624f2973977748b`다. 437MB 압축 원천이나 과거 장후 산출물을 재작성·재실행하지 않았다. 과거 영수증에 새 결정 ID를 소급 기입하지 않는다.

실패 재현 회귀를 먼저 추가했다. 최초 실행에서 명시적 `exit_signal`이 제출 세대·주문번호 없이도 직접 판단으로 채택되는 회귀와 신형 계약을 인식하지 못하는 회귀가 실패했다. 첫 evaluator 테스트의 fixture 준비 오류는 수정했다. 이후 정상 영수증, 구세대, 상충 중복, 다른 주문·BUY 세대·날짜·route, 손상된 context SHA, 수량·호가 변조, 부분체결·취소 대기, 결정 없는 재기동을 분리해 검증했다.

## 생산자→원천→첫 소비자

| 경계·수리 owner | 수리와 닫힘 검사 |
| --- | --- |
| 장중 `sniper_state_handlers.py`의 main real SCALPING 보유 판단 | 기존 `exit_signal` 판단·주문 로직은 그대로 두고 record·position key·검증된 BUY fill identity·source date·결정 시각·rule·보유/호가/arm/강약 입력·유효 threshold·관측 policy SHA·session을 담은 `holding_exit_signal_receipt_v1`과 논리 SHA를 기록한다. BUY 세대가 없으면 결정 ID를 만들지 않고 source gap으로 남긴다. sim/probe는 결속 대상에서 제외한다. 캡처 예외는 관측 gap으로 남기고 기존 주문 경로를 막지 않는다. |
| 같은 생산자의 `sell_order_sent` 첫 ACK | 이미 영속화된 SELL submit generation/context의 원문과 SHA를 같은 position·BUY identity·rule에만 붙인다. broker 요청 route와 실제 응답 route를 별도 보존한다. 응답 불확실·취소 대기를 성공 ACK/terminal로 바꾸지 않는다. 중단 뒤 결정 영수증이 없으면 새 ID를 추정하지 않는다. |
| 구조화 `HOLDING_PIPELINE` → `sniper_trade_review_report.py` 첫 reader | 결정 contract SHA, 제출 context SHA, record/code/position/BUY identity, 결정→제출→terminal 시각, 동일 주문번호·수량·route/session, main real scope와 DB strategy/position tag를 검증한다. 정상은 `binding_status=same_order_generation`; legacy·누락·손상·상충은 `inferred=true`와 명시적 source-quality 사유로 유지한다. 제출 중복의 동일 영수증은 한 주문이며 상충 중복은 격리한다. 완료 projection의 `exit_signal_binding_counts`와 제출 ID/owner/account/route/session 필드를 보존한다. owner·account 원천이 없는 필드는 `null`이다. |
| `holding_exit_observation_report.py` 첫 evaluator | 직접 결속 상태인 행만 `exit_rule_provenance=observed`와 threshold 입력으로 소비한다. 상태·원천일·결정 SHA·제출 영수증을 outcome과 `exit_signal_binding_status_counts`에 전달한다. 기존 9/23처럼 추론된 행은 유효 threshold 0이나 no-edge로 바꾸지 않는다. 구조화 event 원천 SHA와 trailing policy manifest의 결속·PID 증명은 별도 필드/단계다. |

결정→주문 결속과 정책 출처는 별도 상태다. trailing 정책 SHA가 있어도 bootstrap hash가 맞는지에 따라 `observed_sha_bootstrap_unverified` 또는 `bootstrap_hash_matched_no_pid_proof`로 기록하며, SHA 자체가 없으면 `source_gap_policy_sha_missing`이다. 직접 SELL 판단 분류만으로 선택 정책·PID 소비를 증명하지 않는다.

결정 원천의 `holding_context_venue=KRX`는 판단 기준이며 SOR 응답의 **실제 체결 시장**을 확인하지 않는다. 기존 SOR→KRX 사용자 오버라이드는 장후 기준 venue에만 작용하고 이 수리에서 변경하지 않았다. 한 주문의 부분체결·취소 대기는 판단 영수증이 있어도 완료 경제성이 아니다. `sell_completed`의 execution·수량·비용과 BUY 보유 인계는 기존 별도 ledger가 검증하며, 비용 원천 없는 실현손익은 계속 `null`이다.

## 자가 리뷰·검증·잔여 위험

자가 리뷰에서 정상 영수증의 마이크로초 결정 시각과 reader의 초 단위 event 시각이 달라지는 문제, submit context의 정규 세션과 보고용 소문자 세션의 차이, SOR 요청 후 다른 broker 응답 route, 동일 ID의 상충 중복, 평가 input 변조, 캡처 예외가 주문 경로에 전파될 위험을 찾아 보완하고 재검토했다. 검토 범위 내 미해결 코드 결함은 **0**이다.

- 영향 pytest: `test_trade_review_report_revival`, `test_holding_exit_observation_report`, `test_main_lifecycle_receipt_integration`, `test_post_sell_feedback`, `test_live_trade_profit_rate`, `test_scalp_exit_safety_monitor`, `test_sniper_loop_metrics`에서 **382 passed, 1 deselected**. 전체 동일 실행에서 1건은 수정하지 않은 `kiwoom_sniper_v2.run_sniper`의 호출문이 `while True` 이후 첫 500자 안에 있어야 한다는 기존 소스 위치 가정으로 실패했다. 해당 파일은 diff가 없고 이번 청산 영수증 경계와 무관하다. 이 실패를 이번 수리의 PASS로 숨기지 않는다.
- 변경 Python·test의 `py_compile` 통과, `git diff --check` 통과. wrapper를 변경하지 않아 `bash -n`/wrapper 계약 검사는 비대상이다. Ruff 영향 파일 검사에는 `sniper_state_handlers.py`의 기존 F401/F841/F821 총 14건이 남아 있으며 이번 변경 줄의 지적은 0건이다.
- 남은 수용: 새 자연 source date에서 직접 신호→정확 주문·execution/terminal→원천 SHA·정책 manifest→첫 장후 evaluator의 같은 record/BUY 세대·decision/submit SHA를 확인한다. `S3-EXIT-05`의 전체 비용 census·완전 사후창·독립 holdout과 체크리스트 두 항목의 운영 닫힘은 별도다. 9/23 SELL 2건의 broker 실제 과금과 BUY parent 미분류 10건도 소급 해결하지 않았다. 다른 자연일로 넘어간 결정/제출의 reader coverage와 전체 데이터·성능/자연 terminal은 S7에서 확인하고, 릴리스·PREOPEN·PID 소비는 S8에서 확인한다. `S5-FIN-05`는 새 자연일 재현이 필요한 별도 인계다.

기존 S6 미커밋 작업본은 보존했다. 실주문·취소·정책·수량·timeout·서비스·provider·threshold·배포를 변경하거나 정규 장후작업·PREOPEN을 실행하지 않았다. Broker API·parser도 변경하지 않아 공식 Kiwoom reference gate 대상이 아니다.
