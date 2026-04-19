# 2026-04-17 코미팜(041960) 보유 이후 감시 누락 점검

작성시각: 2026-04-17 07:47 KST

## 1) 판정

1. `id=2602` 보유 포지션 기준으로 **감시 누락 없음**.
2. 실계좌 불일치의 직접 원인은 **감시 누락이 아니라 매도거절 메시지 해석 버그**.
3. 다만 `id=1664`에 대해 `hard_time_stop_shadow` 로그가 잔존해 **종료 후 유령 shadow 이벤트 가능성**은 별도 점검 필요.

## 2) 근거

1. 보유 시작과 감시 로그가 연속적으로 확인됨 (`id=2602`).
   - `09:18:39` `holding_started` (partial/full fill 반영 후 보유 진입)
   - `09:18:42` `ai_holding_review`
   - `09:18:49`, `09:18:55`, `09:19:01`, `09:19:10`, `09:19:22`, `09:19:28`, `09:19:49` `AI 보유감시` 지속
   - 로그 출처: `logs/pipeline_event_logger_info.log`, `logs/bot_history.log`
2. 종료 직전 감시/판정 체인이 끊기지 않음 (`id=2602`).
   - `09:19:49` `ai_holding_review -> loss_fallback_probe -> exit_signal -> sell_order_failed(new_status=COMPLETED)`
   - 동일 시각 `bot_history.log`에 `잔고 0주(이미 매도됨). COMPLETED로 강제 전환` 기록
3. 보유 누락과 별개 이슈:
   - `id=1664`, `position_tag=OPEN_RECLAIM`로 `09:23:05/09:25:02/09:27:02` `hard_time_stop_shadow`가 추가로 발생.
   - `id=2602` 종료 이후 발생하므로 동일 보유 체인의 누락이라기보다, 별도/잔존 포지션 객체 이벤트 가능성이 높음.
4. 실계좌 잔고 불일치 원인(코드):
   - `send_smart_sell_order` 거절 시 `return_msg`에 `매도가능수량` 문자열이 포함되면 기존 로직이 무조건 `COMPLETED`로 전환했다.
   - `"[2000](800033:... 125주 매도가능)"`도 `0주`처럼 처리돼 장부상 완료 오판정이 발생할 수 있었다.
   - 수정 후 로직:
     - `0주 매도가능`일 때만 `COMPLETED`
     - `N주(N>0) 매도가능`이면 `HOLDING` 유지 + `buy_qty=N` 보정 후 재시도

## 3) 다음 액션

1. `id=1664` 포지션 객체 수명 점검:
   - `COMPLETED` 전환 시 `hard_time_stop_shadow_logged` 및 관련 상태 초기화 여부 확인.
2. 재발 방지 가드:
   - `qty<=0` 또는 `status in {COMPLETED, SOLD}`인 포지션에서 `_emit_scalp_hard_time_stop_shadow()` 호출 차단 검토.
3. 내일 PREOPEN 검증:
   - `코미팜` 또는 동일 패턴 종목에서 `COMPLETED` 이후 `hard_time_stop_shadow` 재발 여부 재확인.

## 5) 적용/검증 결과

1. 로컬 코드 반영:
   - `src/engine/sniper_state_handlers.py` 매도거절 분기 보정
2. 테스트:
   - `pytest -q src/tests/test_sniper_scale_in.py -k "sell_reject_with_positive_sellable_qty_keeps_holding or sell_reject_with_zero_sellable_qty_marks_completed or holding_exit_signal_logs_exit_rule"`
   - 결과: `3 passed`
3. 원격 반영:
   - `songstockscan` 동일 파일 반영 완료
   - 원격 `py_compile src/engine/sniper_state_handlers.py` 통과
   - `bot_main.py` 재기동 완료(신규 PID 확인)

## 4) 검증 명령

```bash
rg -n "id=2602|코미팜\\(041960\\)|holding_started|ai_holding_review|exit_signal|sell_order_failed" logs/pipeline_event_logger_info.log -S
rg -n "코미팜|041960|AI 보유감시|잔고 0주\\(이미 매도됨\\)" logs/bot_history.log -S
rg -n "id=1664|hard_time_stop_shadow" logs/pipeline_event_logger_info.log -S
```
