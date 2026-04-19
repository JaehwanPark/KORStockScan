# 아주IB투자 보호 트레일링 음수청산 / 익절 라벨 오표시 감사

작성일: 2026-04-17  
대상: 아주IB투자(027360) `id=2710`, `id=2722`  
범위: `logs/pipeline_event_logger_info.log.1`, `logs/sniper_execution_receipts_info.log`, `logs/bot_history.log`, 관련 청산/체결 코드

---

## 1. 판정

1. `익절 완료` 표시는 **단순 라벨 분기 오류**다.
2. 청산 자체는 단순 계산 오류보다 **이전 포지션의 `trailing_stop_price`가 재진입 후에도 남아 있던 상태(stale protection)** 에서 발생했을 가능성이 높다.
3. 따라서 이번 건은 `손익 계산식` 자체보다 `포지션 상태 초기화`와 `메시지 분기 기준`이 분리되어 꼬인 케이스로 보는 것이 맞다.

---

## 2. 근거

### 2-1. 실제 청산 로그는 음수 손익

`id=2710`

- `2026-04-17 11:47:55` `holding_started`  
  - `buy_price=12490.00`, `buy_qty=1`
- `2026-04-17 11:48:14` `exit_signal`  
  - `exit_rule=protect_trailing_stop`
  - `reason=🔥 보호 트레일링 이탈 (12,607원)`
  - `profit_rate=-0.39`
  - `peak_profit=-0.23`
- `2026-04-17 11:48:15` `sell_completed`  
  - `sell_price=12460`
  - `profit_rate=-0.47`

`id=2722`

- `2026-04-17 12:13:37` `holding_started`  
  - `buy_price=12430.19`, `buy_qty=107`
- `2026-04-17 12:13:39` `exit_signal`  
  - `exit_rule=protect_trailing_stop`
  - `reason=🔥 보호 트레일링 이탈 (12,607원)`
  - `profit_rate=-0.15`
  - `peak_profit=-0.07`
- `2026-04-17 12:13:40` `sell_completed`  
  - `sell_price=12440`
  - `profit_rate=-0.15`

결론:
- 두 건 모두 `protect_trailing_stop`이지만 실제 수익률은 음수다.
- 따라서 `익절 완료`는 실제 체결손익과 불일치한다.

### 2-2. 라벨 오표시는 메시지 분기 기준 문제

메시지 생성 코드는 `sell_reason_type == 'LOSS'`일 때만 `[손절 주문]`을 쓰고, 그 외는 `[익절 주문]`으로 처리한다.

- [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:2783)
- [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:3711)

`protect_trailing_stop`는 `sell_reason_type="TRAILING"`으로 분기되므로, 손익이 음수여도 주문/체결 알림은 `익절` 계열 문구가 된다.

체결 영수증 처리도 `pending_sell_msg`의 기존 `[익절 주문]` 문자열을 `[익절 완료]`로 치환한다.

- [sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py:487)
- [sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py:978)

결론:
- 라벨은 `profit_rate`가 아니라 `sell_reason_type`/기존 `pending_sell_msg`를 따른다.
- 따라서 이번 `익절 완료`는 계산 오류가 아니라 메시지 분기 오류다.

### 2-3. 보호 트레일링 값 `12,607원`은 이전 PYRAMID 보호선과 일치

이전 아주IB투자 포지션에서:

- `2026-04-17 11:27:39` `ADD_SIGNAL type=PYRAMID`
- `2026-04-17 11:27:42` `ADD_EXECUTED`
  - `exec=12,740`
  - `new_avg=12569.5683`
  - `new_qty=139`

관련 로그:
- [sniper_state_handlers_info.log](/home/ubuntu/KORStockScan/logs/sniper_state_handlers_info.log)
- [sniper_execution_receipts_info.log](/home/ubuntu/KORStockScan/logs/sniper_execution_receipts_info.log)

보호선 계산 코드는 `PYRAMID` 추가매수 후:

```text
protect_price = avg_price * 1.003
target_stock['trailing_stop_price'] = max(existing, protect_price)
```

- [sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py:281)
- [sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py:286)

계산:

```text
12569.5683 * 1.003 = 12607.277...
```

즉, 문제의 `12,607원`은 이전 포지션에서 생성된 `PYRAMID 보호 트레일링` 값과 사실상 동일하다.

### 2-4. 재진입/청산 정리 경로에서 보호선 초기화가 보이지 않음

`sell_completed` 및 `revive` 정리 경로에서는 `pending_*`, `entry_*` 일부 메타는 지우지만 `trailing_stop_price`, `hard_stop_price`, `protect_profit_pct`는 제거하지 않는다.

- [sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py:1029)

신규 진입 체결 경로에서도 `trailing_stop_price`를 초기화하는 로직이 보이지 않는다.

- [sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py:676)

결론:
- `12,607원` 보호선은 이전 포지션에서 만들어진 후 청산/재진입 사이에 남아 있었고,
- 새 포지션 `id=2710`, `id=2722`에서 그대로 `protect_trailing_stop` 발동 조건으로 재사용됐을 가능성이 높다.

---

## 3. 다음 액션

1. 계획 반영만 수행한다. 즉시 코드 수정은 하지 않는다.
2. 후속 수정 축은 두 갈래로 분리한다.
   - `메시지`: `protect_trailing_stop`에서도 최종 `profit_rate <= 0`이면 `익절` 대신 `손절/중립 청산`으로 표기
   - `상태 초기화`: `sell_completed/revive/new entry` 경계에서 `trailing_stop_price`, `hard_stop_price`, `protect_profit_pct` 초기화
3. 수정 전에는 동일 케이스를 `계산 오류`로 보지 말고 `stale protection + mislabel` 코호트로 따로 추적한다.

---

## 4. 검증 결과

- 로그 재검증:
  - `id=2710`: `protect_trailing_stop`, `profit_rate=-0.47`
  - `id=2722`: `protect_trailing_stop`, `profit_rate=-0.15`
- 메시지 로직 확인:
  - `sell_reason_type != LOSS`이면 `[익절 주문]`
  - `pending_sell_msg` 기반 체결 알림은 `[익절 완료]`로 치환
- 수치 정합:
  - 이전 `new_avg=12569.5683`
  - 보호선 `12569.5683 * 1.003 ≈ 12607.277`
  - 실제 알림 보호선 `12,607원`
