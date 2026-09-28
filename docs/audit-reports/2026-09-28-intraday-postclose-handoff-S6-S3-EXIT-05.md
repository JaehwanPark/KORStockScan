# S6 `S3-EXIT-05` — 전체 완료 census·경제성 분모 인계

실행일: **2026-09-28 KST**. 범위: [S3 `S3-EXIT-05`](2026-09-27-intraday-postclose-handoff-S3.md), [SELL terminal·비용 원천](2026-09-28-intraday-postclose-handoff-S6-S3-EXIT-01.md), [보유 판단→SELL 신호](2026-09-28-intraday-postclose-handoff-S6-S3-EXIT-03.md), [현재 체크리스트](../checklists/2026-09-28-stage2-todo-checklist.md)의 `HoldingExitPositionOutcomeLineageClosure`. **판정: 새 영수증의 완료 ID·투영 SHA·선택 profile과 두 첫 소비자의 경제성 분모를 작업본 fixture에서 결속했다. 실제 broker 과금 원천과 새 자연 완료 표본은 아직 없다.** 선택 릴리스, PID, 자연 장후 소비, 수익성 수용은 이번 판정에 포함하지 않는다.

## 재현 원천·서로 다른 분모

9/23 보존 `trade_review_2026-09-23.json`의 파일 SHA는 `6be7f624889f21384a5c08a2fb8240308477c512d77cf1e1a624f2973977748b`다. 보존된 `pipeline_events_2026-09-23.jsonl.gz`의 기존 해제 논리 SHA는 `4db035e3b3915644ee95fef82d50b54f0dcdfbbf6c69a19dab15594a3d1c758c`([SELL 원천 보고서](2026-09-28-intraday-postclose-handoff-S6-S3-EXIT-01.md)). 두 파일과 과거 장후 산출물은 재작성하지 않았다.

| 범위 | 원본·유효 | 제외·격리·미관측 |
| --- | --- | --- |
| 9/23 첫 trade-review | recent record 10 = 완료 표시 8 + open/censored 2; `sell_completed` 고유 ID 8 | 직접 SELL execution·가격·수량과 **설정 비용률 추정**이 연결된 6, 잔고 화해형 `47531`·`47515` 2의 정확 execution·시각·broker 과금 미관측. 8건의 직접 결속 SELL 판단 0 |
| 9/23 fact sync | fact 10, 완료 표시 8, open 2; 당시 `economics_valid_completed=8` | 8은 `fixed_comparison_cost_model` 분모다. broker 실제 과금 적격 8로 읽지 않는다 |
| 누적 clean-window holding observation | 유효 완료 329, 당시 정의의 비용·체결가격 부분집합 6 | 323 비용 원천 결손, 전체 PnL `null`, 직접 판단·유효 threshold·완전 사후창 각각 0. 329와 9/23의 8은 합산하지 않는다 |
| 새 fixture: 완료 1건 | raw terminal ID 1, projection 1, 유효 profit 표시 1 | broker 실제 과금 strict 0, 비용 제외 1, 중복 격리 0, 미관측 0. 손상 SHA·다른 날짜/profile·중복 ID·추가 raw ID는 각각 별도 격리한다 |

기존 S3의 “strict 6”은 **체결가격 + 설정 비용률**의 당시 평가 정의다. [S6 SELL 보고서](2026-09-28-intraday-postclose-handoff-S6-S3-EXIT-01.md)가 밝힌 대로 그 6건의 broker 실제 과금은 `null`이다. 새 코드의 broker-actual-cost strict와 9/23 보존 지표를 동일 분모라고 주장하지 않는다. 과거 ID·비용·판단 신호를 소급 생성하지 않았다.

## 생산자→첫 소비자 수리와 닫힘 검사

| 경계·수리 owner | 작업본 계약과 fixture 닫힘 |
| --- | --- |
| `sniper_trade_review_report.py` 완료 투영 생산자 | 실제 SELL order·execution·정확 fill clock은 비용과 분리해 보존한다. `main_lifecycle_fees_taxes_krw`는 설정 비용률 추정으로 분류해 `configured_fee_estimate_krw`·`configured_cost_estimated_pnl_krw`에 남긴다. broker 실제 과금이 없으면 strict 제외 사유 `source_gap_broker_actual_cost_missing`, 투영의 실현손익 `null`이다. 상단 `metrics.realized_pnl_krw`는 기존 웹 화면의 숫자 포맷 계약 때문에 **모델 표시값**으로 유지하고 `realized_pnl_krw_basis=legacy_display_configured_cost_model`, `broker_actual_realized_pnl_krw=null`, `modeled_display_pnl_krw`를 함께 낸다. 이 호환 필드는 경제성 소비에 쓰지 않는다. raw terminal ID, 날짜, 선택 입력의 논리 SHA, 출력 SHA, run ID, 행별 SHA·owner/계좌 미관측·attempt/order/execution·route/session·비용/제외 사유를 `completed_census_manifest`에 봉인한다. 입력 SHA는 선택된 DB 행·이벤트의 **논리 투영 hash**이며 독립 broker 원문 검증이라는 뜻이 아니다. 구조화 source receipt가 없으면 `unobserved`로 남긴다. |
| `log_archive_service.py` snapshot 저장 | builder 시점에는 profile이 미정이다. 실제 저장 직전에 부여되는 `snapshot_profile`로 census 영수증과 run ID를 다시 봉인한다. `intraday_light`를 `postclose_exit` 증거로 표시하지 않는다. shell wrapper·스케줄은 변경하지 않았다. |
| `holding_exit_observation_report.py` 첫 평가자 | 9/28 이후 `postclose_exit` profile·원천일·projection SHA·raw terminal ID와 완료 ID·행 날짜를 확인한다. 새 manifest가 없는 과거 projection은 행을 진단용으로 보존하되 `legacy_completion_census_unsealed`로 표시한다. 구세대/손상/다른 profile은 해당 날짜 source gap으로, 날짜 간 중복 완료 ID는 해당 ID 격리로 처리한다. clean-window 원본·유효 profit·strict 비용·제외·격리·미관측, 세대별 입력·출력 SHA를 분리한다. 비용 적격과 **직접 SELL 신호까지 결속된 정책 경제성 적격**을 별도 ID로 기록한다. 직접 신호가 없으면 전체 정책 PnL은 `null`이다. |
| `strategy_position_performance_report.py` 첫 fact 소비자 | 새 세대의 main SCALPING 완료 행은 같은 ID·entry/completion date·symbol·position tag·가격·수량·시각·real owner scope의 투영과 연결한다. 설정 비용률만 있거나 직접 신호가 unbound이면 profit/PnL `null`이며 source-quality 사유를 status 영수증에 남긴다. 기존 비대상 fixed-comparison 집계는 별도 모델 의미를 유지한다. fact status의 census run·출력 SHA를 선택된 trade-review snapshot과 비교해 재작성 뒤 DB 캐시를 현재 세대로 수용하지 않는다. 캐시가 stale이면 읽기 전용 현재 원천 재구성으로 가고 그 사유를 표시하며, trade-review 원천 경고는 차단한다. |

SOR→KRX 사용자 오버라이드는 같은 주문·execution·정확 fill 시각·real terminal을 가진 실제 체결을 장후 **KRX 기준 평가**에 남긴다. broker 과금이 없는 경우에도 사후 가격 관측 자체는 유지하고 손익은 `null`로 둔다. broker 실제 체결 시장 `UNKNOWN`을 KRX 확인으로 바꾸지 않는다.

## 실패 회귀→구현→재검토

첫 실패 실행에서 설정 비용 40원이 실현손익으로 승격되고 census 함수가 없어 **3개 회귀가 실패**했다. 자가 검토 중 추가한 직접 신호 없는 전체 경제성 수용과 구세대 DB fact 수용 회귀도 구현 전 실패를 확인했다. 이후 같은 세대/valid-empty, 출력 변조, raw ID 누락, 날짜 간 중복, 잘못된 profile, visible fact와 sealed row의 가격 불일치, 원천 경고, 비용 없는 직접 체결의 SOR 기준 venue 관측을 검사했다.

자가 검토에서 모델 상단 합계의 출처, 손상 manifest가 sealed 건수에 들어갈 위험, 저장 전 profile 단정, stale DB fact의 무검증 사용, source warning의 빈 결과 전환을 찾아 보완하고 재검토했다. 웹 화면은 기존 숫자 필드를 “실현손익”으로 표시하므로 **그 화면만으로 broker 실제 과금 수익성을 판단할 수 없다**. 서비스 변경은 이번 범위 밖이며 엄격한 장후 소비자는 출처가 분리된 투영·fact를 사용한다. **검토한 S3-EXIT-05 코드 범위의 미해결 결함은 0**이다.

## 검증·잔여 수용

- 영향 pytest: `test_trade_review_report_revival`, `test_holding_exit_observation_report`, `test_strategy_position_performance_report`, `test_log_archive_service`, `test_trade_review_report`, `test_main_lifecycle_receipt_integration`, `test_post_sell_feedback`, `test_live_trade_profit_rate` **321 passed**. 변경 Python·test `py_compile`, 영향 Ruff, `git diff --check` 통과. shell wrapper를 변경하지 않아 `bash -n`과 shell 계약 검사는 비대상이다.
- 다음 자연 source date의 닫힘 검사: 전체 완료 terminal ID ↔ `postclose_exit` census 행 ↔ fact/holding 첫 소비의 동일 source date·profile·run·입출력 SHA, record·position·attempt·order·execution·수량·가격·시각·owner/session을 대사한다. broker 실제 과금의 독립 원천이 확인될 때만 비용 후 손익을 채우고, 직접 SELL 결정·유효 정책/threshold·완전한 1/3/5/10분 창과 독립 holdout을 확인한다. 원천 부재는 `null`·source gap이며 모델 추정치로 닫지 않는다.
- 전체 모집단의 자연 성능·terminal·완전 사후창은 S7, 선택 릴리스·PREOPEN·실제 PID 소비는 S8에 남긴다. `S5-FIN-05`의 새 자연일 조건부 결손과 scale-in의 별도 0-attempt 결손도 유지한다. broker API/parser를 변경하지 않아 공식 Kiwoom reference gate 대상이 아니다. 실주문·취소·정책·수량·timeout·서비스·provider·threshold·배포와 정규 장후작업·PREOPEN은 변경·실행하지 않았다.
