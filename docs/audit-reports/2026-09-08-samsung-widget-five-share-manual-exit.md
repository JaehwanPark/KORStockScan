# 삼성전자 5주 수동 부분청산 대사

- 판정: 요청된 5주 영수증·원장 대사 완료. 이후 별도 사용자 확인·승인으로 과거 이월 표식 40→0 정정과 위젯 재기동도 완료했다. 현재 실보유는 25주이며, 과거 40주의 매도 이력 복원 및 전체 경제성 검증은 별도다.
- 대상일: `2026-09-08 KST`; source commit `2c9731fe02227c38e430dd0d30850b9e15926718`. 거래 코드·정책·env·unit은 수정하지 않았다.
- 사용자 권한: 이미 실행한 삼성전자 부분청산의 원장 처리, 위젯만 잠시 중지 후 재기동. 이번 대사기는 broker 주문·취소·정정을 호출하지 않았다.

## 체결과 owner

- `kt00007` 영수증 `0066896`: 삼성전자 `005930`, NXT 매도 요청 5주/체결 5주/미체결 0주, 평균 271,500원. 원주문 없음, HTS 수동 주문이다.
- 주문시각 18:53:44와 실제 체결 관측시각 19:00:00을 분리했다. 후자는 `logs/bot_history.log:20008`의 WS 체결 수신 근거이며 미제공 broker 원시 체결시각을 추정하지 않았다.
- 귀속 owner: `widget_auto_trade:005930:2026-09-08`, 11:17:11.739361 KRX_REGULAR entry episode. 매수 `0038061/0052179/0057233` 총 30주, 원가 합계 8,240,000원. 다른 삼성전자 episode position의 registry 순보유는 0주다.
- 기존 target `0057234 → 0061951 → 0062568 → 0064889`는 체결 0/잔량 0으로 종료됐으며 새 매도나 목표 주문을 만들지 않았다.

## 반영과 검증

- 위젯 `orders`에 `MANUAL_OPERATOR_PARTIAL_EXIT` 1건, 대응 event 2건을 exact 주문번호로 기록했다. `receipt_imported/imported_at`, 실제 수동 execution owner와 `reconciler_submitted_order=false`를 보존하여 역사적 주문 관측과 이번 회계 수리를 구분했다.
- 공통 registry의 기존 `register_reconciled_manual_exit`를 사용했다. intent `2176b88d224c4ef38a94364a5cd0dac2`, 기존 정확한 owner position 30→25주. main/episode owner로 이동하지 않았다.
- 위젯 당일 순보유 30→25주, `entry_episode_open=true` 유지. 다른 원장 항목·주문은 JSON 구조 비교로 불변 확인했다.
- 실제 consumer `_widget_actual_execution_inventory`: `status=loaded`, contract errors 0, `quantity=5`, `right_censored_residual_quantity=25`, `manual_exit_realized=true`, `realized_loss=true`, `autonomous_target_filled=false` 확인. 장후 전체 report를 수동 재생성하거나 자연 실행 완료로 표기하지 않았다.
- 해당 episode 가중평균 원가 기준 세전 손익은 약 **-15,833.33원**. 기존 비교비용 계약 적용 비용 3,124.625원/모델 순손익 **-18,957.958333원**. `modeled_costs_broker_receipt_exact=false`; 실제 증권사 수수료·세금이 없는 값을 0 또는 확정 순손익으로 기록하지 않았다.
- 부분청산 회귀: `test_actual_widget_manual_partial_exit_is_realized_loss_with_residual_custody` 통과. 격리된 registry 사본에서 31주 과다 배정 거부, 5주 반영, 동일 주문 중복 반영 거부를 검증했다. 실데이터 staging 및 live consumer 재검증, 로더 round-trip 25주, `git diff --check` 통과. 코드 신규 구현은 없었다.

## 중지/재기동과 보존

- 19:33:46 위젯 정상 중지, `MainPID=0/Result=success`; 대사 process PID1185156이 기존 singleton lock을 독점했다. 기존 lock을 삭제하거나 다른 매매 process를 중지하지 않았다.
- 중지 중 원본 state/events/registry bytes를 보존하고 staging 검증 후 exact registry append와 state/event 반영을 수행했다. 원장 두 파일이 맞고 loader/consumer 검증을 통과하기 전에는 위젯을 시작하지 않았다. 원본 30주 bytes는 감사용이며, 체결 후의 정상 운영 rollback 값이 아니다.
- 19:36:55 위젯 재기동, 새 PID **1188026**, `active/running`, `Result=success`, `NRestarts=0`, 해당 PID singleton lock 확인.
- 설치 unit env와 exact-date policy에서 독립 재계산한 기대값으로 startup receipt 검증: `verified_requested_startup_fields`, findings/mismatch 0. 이는 시작 설정 확인이며 모든 자연 policy 호출이나 전략 효과 승인이 아니다. 새 결정적 policy hash는 이전 07:58 receipt와 동일하다고 가정하지 않았다.
- 19:37:35 broker 재조회: 삼성전자 25주, 미체결 0주; 새 PID 원장도 25주, 수동 영수증 1건 보존. 다른 widget 주문 변화 0. 19:38:00 cycle 진행 확인.
- 감사 경로: `data/runtime/manual_close_reconciliation/samsung_widget_20260908_0066896.sb2Kjp/`의 evidence, preflight/staging, before/after bytes, final order/events, registry applied receipt, startup receipt와 검증을 보존했다.

| 파일 | 적용 직후 SHA-256 |
| --- | --- |
| evidence.json | `410ed0b66cd52271839b6e0f6bd4242721ba15454872ca4fb5a24cc78e98fe71` |
| state.after.json | `7f63510cacb2f4ec779f88ce616bd715cfd55016bd51dd871f7be1bdebe77c66` |
| events.after.jsonl | `470ae5c5293032d95a450ee9f3acdee037a51c61efd8a782636f73f94491f935` |
| registry.after.jsonl | `91f3e994a2683cce96e464ca73f78451e04686e8342967cbd0c79558b9bae042` |

## 최초 부분청산 대사 당시 잔여 범위

- 기존 `prior_day_unmanaged_qty=40` 표식은 이번 부분청산 이전부터 존재했다. 이번 5주를 이 과거 표식에서 임의 차감하거나 이를 현재 실재하는 추가 40주로 확정하지 않았다. 당일 widget/registry 25주 대사와 과거 이월 필드의 정합성은 분리한다.
- 최초 대사에서는 과거 이월 표식을 임의 변경하지 않았다. 당시 잔여 확인은 기존 `PostcloseRecoverySourceAcceptance0908`에 남겼으며, 아래 별도 사용자 승인 정정이 현재 표식의 후속 근거다. 과거 매도·손익 근거를 합성하지 않는 원칙은 그대로다.

## 별도 승인: 실재하지 않는 이월 40주 표식 정정

- 사용자 진술 `이월 40주는 현재 보유하고 있지 않아`와 40→0 정정·위젯만 중지/재기동에 대한 명시적 승인을 근거로 수행했다. 과거 40주 매도 주문이나 체결·비용·실현손익을 새로 만들지 않았다.
- 20:03:47 broker KRX/NXT 잔고 계약 complete, 삼성전자 25주·미체결 0주. 당일 widget 순보유 25주 및 정확한 현재 owner position 25주와 일치했고, 다른 삼성전자 registry position은 모두 0주였다. 따라서 추가 legacy carry는 현재 수량 보존식상 0주다.
- 20:05:06 위젯만 정상 중지 후 PID1211711이 기존 singleton lock을 독점했다. 원본 state/events/registry/startup receipt를 백업했다. main/episode process와 timer·policy·env는 변경하지 않았다.
- `symbols.005930`의 세 필드만 정정: `prior_day_unmanaged_qty: 40→0`, `prior_day_unmanaged_qty_broker_reconciled: false→true`, source는 `explicit_operator_current_inventory_reconciliation_20260908`. 이 true는 현재 잔고 대사 완료이지 과거 40주의 체결 이력 복원 완료가 아니다.
- 정확한 JSON diff로 다른 모든 필드·history·orders 불변, events/registry bytes 불변을 확인했다. 로더는 현재 25주와 carry 0주를 유지했고, 주문0066896의 5주 부분 실현손실 및 잔여 right-censored 25주를 소비하는 경로도 contract error 0이었다.
- `_unmanaged_overnight_qty`는 추가 체결이 없을 때 기존 65주 대신 25주를 산출한다. 다음 날 수량 0으로 리셋하거나 현재 25주를 청산 완료 처리하지 않았다. 실제 다음 날짜 전이는 아직 자연 관측 전이다.
- `korstockscan-review-gate`로 owner·동시 쓰기·rollover·부분청산 consumer를 재검토했다. 관련 pytest **4 passed / 180 deselected**, 로더·실데이터 비교 및 `git diff --check` 통과, 이번 정정 범위 미해결 finding 0. 거래 코드 수정이나 비싼 보고서 재생성은 없었다.
- 20:06:48 위젯 재기동: PID **1212987**, `active/running`, `Result=success`, `NRestarts=0`; singleton lock inode1333750의 실제 보유 PID 일치. 20:07:38 설치 env 8개와 독립 재계산 config/policy의 startup receipt 검증 통과, mismatch/finding 0. policy/config hash는 19:36 기동과 동일했다. startup 검증을 전체 자연 policy 소비·경제성 승인으로 확대하지 않는다.
- 재기동 후 broker 재조회도 25주·미체결 0주, 원장25주/carry0 및 모든 주문·history·events·registry 보존 확인. 대사기는 주문·취소·정정을 실행하지 않았다.
- 감사 경로: `data/runtime/manual_close_reconciliation/samsung_widget_carry_20260908.dMzQl3/`의 `evidence.json`, before/after state, 이전 events/registry bytes, before/after startup receipt 및 `restart-verification.json`. state 적용 전 SHA256 `60c855a169d068d9418f878648f9bc33049de474b5930f4ef2e205ac25ecec1f`, 적용 직후 `e6498bda347ea11df52381258177dbc305be6da37a8b85c7c12f5578e5cce3c5`. 백업은 감사 근거이며 실재하지 않는 40주를 복원하는 운영 rollback 권한이 아니다.
- 남은 자연 장후 소비는 기존 `PostcloseRecoverySourceAcceptance0908`에서 추적한다. rollover 계산 검증과 미래 실제 전이는 별도이며, 이번 정정을 닫기 위해 미래 전이를 강제 실행하지 않는다. 정확한 과거 매도 영수증·실비용 미확인을 0손익이나 완료 거래로 보간하지 않으며, 현재 표식 정정 완료를 취소하는 조건으로도 삼지 않는다.
