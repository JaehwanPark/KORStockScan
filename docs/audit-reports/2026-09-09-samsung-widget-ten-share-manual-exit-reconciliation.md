# 삼성전자 10주 수동매도와 재생성 목표주문 복구

- 대상일: 2026-09-09 KST. 사용자 승인 범위는 위젯 서비스 중지, 잔존 주문 취소, 이미 체결된 수동매도 귀속 복구, 검증 후 재기동이다. 일반 장후 모니터링이나 새 전략 구현 요청이 아니다.
- 현재 판정: 주문 취소와 원장 복구 검증 완료, 관리자 권한을 통한 위젯 재기동 및 새 PID 검증은 대기 중이다. 재기동 완료나 전체 운영 정상으로 보고하지 않는다.

## Exact receipt와 최초 결손

- 위젯 매수 `0063427`: 17:55:40 주문, NXT 10주 × 271,000원. 원래 목표 주문 `0063429`는 10주 × 273,500원이다.
- 영웅문S# 수동 정정매도 `0064757`, 원주문 `0063429`: 10주 × 267,000원 전량 체결, 잔량 0. `19:13:50`은 주문시각이며 실제 거래소 체결시각으로 사용하지 않는다.
- 기존 위젯은 원목표의 종료를 미체결 취소로 소비하고 수동 successor를 보유 감소에 연결하지 못했다. 19:13:51에 목표 주문 `0064759` 10주 × 273,500원을 다시 제출했다. 수동매도 이후 계좌 25주와 원장의 당일 10주 + 전일 25주가 불일치했다.
- 이번 복구는 이 exact 사건의 원장 정합성을 닫는다. 임의 수동 정정·부분체결의 자동 추적 기능 전체를 수정했다고 주장하지 않는다. 일반 재발방지 구현은 별도 변경 범위이며 기존 위젯 acceptance owner에서 추적한다.

## 중지·잠금·주문 취소

- 일반 `systemctl stop`은 `Interactive authentication required`로 거부됐다. 사용자가 `sudo systemctl stop korstockscan-widget-signal-auto-trader.service`를 실행했다. 이후 `MainPID=0`, `inactive/dead`, `Result=success`를 확인했다.
- 타이머는 변경하지 않았다. 다음 예약은 9/10 07:58이며 복구 작업은 기존 singleton lock을 독점했다. 다른 매매 process나 collector, 정책/env/operator lock은 변경하지 않았다.
- 취소 직전 KRX/NXT 잔고 조회 complete, 삼성전자 25주, `0064759` 체결 0/잔량 10을 재확인했다. 기존 gateway의 NXT `kt10003` 취소를 정확한 원주문/10주로 한 번 실행했다. API 구현이나 호출량 계약은 바꾸지 않았다.
- 취소 접수 `0065312`와 후속 `kt00007`의 원주문 연결·취소확인, `0064759` 체결 0/잔량 0, `ka10075` 미체결 0을 대사했다. 응답 성공만으로 취소 완료를 판정하지 않았다. 취소 후에도 계좌 25주를 유지했다.

## 귀속과 검증

- custody owner: `widget_auto_trade:005930:2026-09-09`, position suffix `005930:2026-09-09:ENTRY:NXT_AFTERMARKET:2026-09-09T17:55:38.645804+09:00`. 수동 execution owner는 `manual_operator`로 별도 보존했다.
- 공통 registry의 기존 native transition으로 취소된 목표만 terminal 처리하고, `register_reconciled_manual_exit`로 영수증 `0064757`을 한 번 반영했다. 새 intent는 `6f97268f93d743adbaabd7b00572d2b6`이며 해당 position은 10→0주다. 다른 삼성전자 registry row는 변경하지 않았다.
- 위젯 원장은 기존 수동 exit 호환 role `MANUAL_OPERATOR_PARTIAL_EXIT`를 사용하되 `manual_exit_scope=full_current_episode_preserve_prior_day_25`로 실제 범위를 기록했다. 해당 episode를 닫고 완료 count를 한 번 반영했다. 자동 target fill count/성공으로 바꾸지 않았고 전일 carry 25주와 다른 종목·history를 보존했다.
- state에 수동 영수증 1건, event journal에 receipt import 2건과 수동 episode 종료 1건을 남겼다. `receipt_imported`, `reconciler_submitted_order=false`, 원주문·정확한 custody·수동 authority를 보존했다. 과거 broker 접수 사실을 기록한 event이지 이번에 새 SELL을 제출한 것이 아니다.
- 사본 staging에서 registry 중복 영수증 거부, position 0, carry 25, 로더 round-trip 불변과 직접 consumer를 검증했다. 초기 staging의 event authority 필드 누락은 live publish 전에 보완해 재검증했다.
- live 재검증: `_widget_actual_execution_inventory`는 `loaded`, contract errors 0, 수동 exit anchor 1건, `manual_exit_realized=true`, `autonomous_target_filled=false`, 당일 residual 0이다. 공통 삼성전자 position 합계와 실제 계좌는 25주, 미체결은 0이다.
- 비용 전 손익은 **-40,000원**. 실제 수수료·세금이 확인되지 않아 확정 순손익은 null이다. 기존 비교비용 consumer의 모델값 -46,147원은 실제 broker 정산값이 아니다.
- 거래소 체결시각은 null로 유지했다. 새 event의 관측시각과 consumer의 confirmation-based duration은 복구 영수증 확인시각/구간이며 실제 holding time·청산 지연이나 timing 정책 효과로 해석하지 않는다.
- `korstockscan-review-gate`: 관련 수동/cancel/state/terminal 테스트 48 passed (258 deselected), 위젯 및 signal-quality 테스트 전체 139 passed. 두 실행은 일부 중복되므로 고유 187 tests로 합산하지 않는다. 이번 exact 원장 복구 범위는 검증됐으며 재발방지 코드 전체/재기동/경제성 acceptance와 구분한다.

## 증거와 남은 확인

- 경로: `data/runtime/manual_close_reconciliation/samsung_widget_20260909_0064757.YC7AO7/`. before/after state·event·registry, broker 원본·metadata, 취소 응답, staging 및 pre-restart 검증을 보존했다. 백업은 감사 증거이며 이미 매도한 10주를 다시 보유로 복원하는 운영 rollback이 아니다.
- `evidence.before.json` SHA256: `91410a713be8dcaf14899d4909fea7d74b0de240f3e0e333f7cc6dc4c99c09d5`.
- 재기동 전 설치 env allowlist·설정·dated policy를 독립 재계산하고 import된 source 85개 hash를 기록했다. 재기동 후 새 PID/startup receipt와 이 기대값, 자연 cycle 및 삼성전자 미체결 0/잔고 25를 확인해야 한다. 재기동 권한과 정책값은 이미 승인된 범위만 사용한다.
- 후속 owner: 당일 checklist의 기존 `WidgetEpisodeRecommendationApplyAcceptance0908`. 전체 장후/추천/경제성 항목은 OPEN을 유지한다. 외부 Project/Calendar sync는 실행하지 않았다.
