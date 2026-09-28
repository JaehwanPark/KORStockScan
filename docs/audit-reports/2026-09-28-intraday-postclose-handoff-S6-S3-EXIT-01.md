# S6 `S3-EXIT-01` — SELL terminal·비용 원천 인계

실행일: **2026-09-28 KST**. 범위: [S3 `S3-EXIT-01`](2026-09-27-intraday-postclose-handoff-S3.md), [BUY parent→보유 인계](2026-09-28-intraday-postclose-handoff-S6-S2-ENT-03-S3-EXIT-02.md), [순차 첫 BUY](2026-09-28-intraday-postclose-handoff-S6-S2-ENT-05.md). **판정: 새 원천의 생산자→첫 장후 reader 계약을 작업본에서 수리했다. 9/23 두 SELL의 실제 execution ID·체결시각·broker 과금은 복원되지 않아 여전히 `unknown`·`null`이다.** 선택 릴리스·PID·자연 소비는 이 작업의 수용 범위가 아니다.

## 원천 재현과 영향 분모

9/23 원천은 `data/pipeline_events/pipeline_events_2026-09-23.jsonl.gz`이며 archive receipt의 해제 논리 SHA는 `4db035e3b3915644ee95fef82d50b54f0dcdfbbf6c69a19dab15594a3d1c758c`이다. 압축 파일 SHA는 `471c327ab369d195d5374f3f2e4860966303c7d963ffe3cc1e69b26a79851e18`, 보존된 `trade_review_2026-09-23.json` 파일 SHA는 `6be7f624889f21384a5c08a2fb8240308477c512d77cf1e1a624f2973977748b`이다. 원본 산출물은 재작성하지 않았다.

| 범위 | 원본 | 유효·직접 | 격리·미관측 |
| --- | ---: | ---: | --- |
| 9/23 완료 표시 projection | 8 record | 직접 broker SELL fill·설정 비용률 투영 6 | `47531`·`47515` 2는 balance+`kt00007` 주문·가격·수량 화해만 확인; 실제 execution 번호·시각·broker 과금·엄격 원가 미관측. 9/23 projection에는 현행 `strict_completion_status` 필드 없음 |
| `47531` / SELL `0012375` | `sell_order_sent` 1, `sell_cancel_reconciliation_deferred` 1, 잔고 화해형 `sell_completed` 1 | 제출 attempt `SCANPROM-010060-1790120286324`, lifecycle `mlc-393510f2…`, route `SOR`, 정규장 기준 session과 주문번호 연결 | 직접 SELL execution 0; `sell_qty=1`은 화해 수량이며 leg execution 증명이 아님. 모델 +5,438원은 실현손익에서 제외 |
| `47515` / SELL `0011689` | `sell_order_sent` 1, `sell_cancel_reconciliation_deferred` 1, 잔고 화해형 `sell_completed` 1 | 제출 attempt `SCANPROM-058610-1790118882111`, lifecycle `mlc-c59def4c…`, route `SOR`, 정규장 기준 session과 주문번호 연결 | 직접 SELL execution 0; 모델 +462원은 실현손익에서 제외. `exit_signal` 8 event는 별도 판단 분모 |

두 record의 `sell_completed.decision_authority=broker_balance_reconciliation_only`와 `execution_match_reason=unique_owner_cycle_kt00007_terminal_sell_execution`은 잔고 부재 및 단일 주문 화해를 가리킨다. `sell_time_precision=order_second_not_fill_second`이며 원문 execution ID·실제 체결시각·실제 과금은 없다. 취소 **대기 event 1씩**을 취소 종결이나 체결 leg로 세지 않는다. 9/23 BUY parent 10건은 앞선 S6 보고서대로 미분류이며 SELL 주문번호가 같다는 이유로 BUY custody를 소급 연결하지 않는다.

## 생산자→직접 reader 수리

| 경계 | 수리·닫힘 검사 |
| --- | --- |
| 직접 SELL fill 생산자 `sniper_execution_receipts.py` | 기존 broker 체결가격과 `get_trade_cost_rate()`로 계산한 `main_lifecycle_fees_taxes_krw`를 명시적인 **설정 비용 추정치** `main_lifecycle_configured_fee_estimate_krw`·`main_lifecycle_cost_basis_source=configured_trade_cost_rate`와 함께 낸다. broker 실제 과금은 별도 `main_lifecycle_broker_actual_fees_taxes_krw=null`이다. 주문·취소·체결·DB 상태 변경은 없다. |
| 잔고·`kt00007` 화해 생산자 `sniper_sync.py` | 실제 두 건을 만든 경로다. 정규화된 날짜·record·code·order·order time·submitted/filled/remaining qty·가격·route/SOR·BUY 시각·snapshot 시각을 한 논리 contract와 SHA로 보존한다. execution 번호와 broker 실제 과금은 `null`, 설정 비용률 추정치만 별도 필드다. 영속 DB 완료는 기존 흐름대로 두고 관측 필드만 보강한다. 원천 snapshot 실패는 기존 `sell_completion_reconciliation_gap`로 남긴다. 새 API 요청·parser 변경은 없다. |
| 첫 장후 reader `sniper_trade_review_report.py` | 직접 fill과 balance-only terminal을 분리하고, `sell_completion_reconciliation_gap`·`sell_cancel_reconciliation_deferred`를 구조화 projection에 포함한다. 화해 contract의 SHA·source date·record/code·주문·가격·수량·BUY→주문→snapshot 시간, 제출 stage의 주문·attempt·lifecycle·route·authority 및 중복 상충을 대사한다. 옛 9/23 영수증은 `legacy_unbound`로 남기고 새 세대를 소급하지 않는다. 자정 뒤 기록돼도 원래 source date를 보존한다. 설정 비용 추정치는 동세대 제출과 화해가 모두 결속된 행에만 내며 실제 broker 과금·순손익은 `null`이다. 취소 대기는 건수만 보존하고 종결로 승격하지 않는다. |

직접 체결 6건의 기존 `broker_fill_prices_fee_aware` 필드명은 가격 영수증+설정 비용률의 기존 호환 계약이다. 새 `configured_fee_estimate_krw`와 `broker_actual_fees_taxes_krw=null`이 두 비용 원천을 명시적으로 나눈다. 실제 과금 검증 0/8을 설정 추정 6/8에 합치지 않는다. SOR→KRX 사용자 오버라이드는 장후 **평가 기준 venue**에만 해당하며 broker 실제 체결 시장은 계속 `UNKNOWN`이다.

## 실패 회귀·자가 리뷰·인계

1. 수리 전 회귀에서 잔고 화해의 source status·비용 분리·정규화 세대 field와 직접 fill의 비용 출처가 없어 **4개 실패**를 확인했다. 동일 주문 ACK, 화해 원천 부재, 부분·취소 대기, 중복·다른 주문·route, 다른 날짜/SHA·가격·수량, 자정 이후 영수증, 재기동·late SELL receipt의 기존 fixture를 함께 검사한다.
2. 자가 리뷰에서 장후 reader가 `sell_completion_reconciliation_gap`·취소 대기 stage를 투영하지 않는 점, normalized SHA를 전달만 하고 재검증하지 않는 점, 같은 주문번호의 상충 제출 로그·route 또는 DB와 다른 수량·가격을 수용할 위험을 확인해 보완했다. 보존된 9/23 projection의 두 record를 새 reader로 읽으면 제출 attempt는 주문번호에만 `matched_source_only`, 화해 세대는 `legacy_unbound`, 실현손익은 `null`이다. 원천이 없는 fee·execution·fill time·account를 만들지 않는다. **검토 범위 내 미해결 코드 결함은 0**이다.
3. 수리 owner는 `src/engine/sniper_execution_receipts.py` 직접 fill, `src/engine/sniper_sync.py` 잔고 화해, `src/engine/sniper_trade_review_report.py` 첫 소비자다. 새 자연 source date의 원본 broker execution·cancel/terminal·account/fee 원천과 동일 record/attempt/order/execution·날짜/SHA를 양방향 대사해야 **두 record의 역사적 빈 칸과 별개인** 새 표본의 닫힘을 선언할 수 있다. 실제 broker 과금 원천이 없으면 계속 null이고, 설정 비용률 추정은 별도 분모다.

`S3-EXIT-03/05`의 보유 판단·전체 경제성, `S5-FIN-05`의 새 자연일 조건부 결손은 별도 인계다. 전체 데이터·성능과 자연 terminal은 S7, 릴리스·PREOPEN·PID 소비는 S8에 남긴다. 앞선 S6 작업본과 9/23 BUY parent 미분류 10건을 보존했다. 실주문·취소·정책·수량·timeout·서비스·provider·threshold·배포 및 정규 장후작업·PREOPEN은 변경·실행하지 않았다. Broker API/parser는 변경하지 않아 공식 Kiwoom reference gate 대상이 아니다.

## 검증

- 영향 pytest: `test_trade_review_report_revival`, `test_main_lifecycle_receipt_integration`, `test_live_trade_profit_rate`, `test_holding_exit_observation_report`, `test_post_sell_feedback` **274 passed**. 실패 재현 4개→수리 후 producer→reader 동세대 연결·구세대 격리, 중복·다른 주문/route·수량/가격·자정 이후 원천일, partial/cancel/restart 경로를 검증했다.
- 변경 Python·test `py_compile`, `git diff --check`, 문서 링크 3개, current-owner print-only backlog parser(`count=31`) 통과. Shell wrapper를 변경하지 않아 `bash -n`/wrapper 계약 검사는 비대상이다. Ruff는 영향 파일에서 기존 미사용 import 3건(`sniper_execution_receipts.py`의 기존 10·83·84행)으로 전체 파일 검사가 실패했으며 이번 변경 줄의 지적은 없다.
- 남은 위험: 9/23 직접 execution·실제 과금 원천이 없어 두 건의 비용 후 실현손익·체결시장별 성과는 미식별이다. 최신 코드 fixture와 과거 `sell_completed` 표시를 자연 terminal·실제 PID 소비로 승격하지 않는다.
