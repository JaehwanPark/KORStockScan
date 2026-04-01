# Scale-In Operations Runbook

## 목적

`KORStockScan`의 추가매수(`AVG_DOWN`, `PYRAMID`) 기능 운영 중

- 현재 상태 확인
- 이상 징후 탐지
- 수동 대사
- 즉시 대응

을 빠르게 수행하기 위한 운영 문서입니다.

---

## 기본 확인 대상

- 테이블: `recommendation_history`
- 테이블: `holding_add_history`
- 로그 태그:
  - `[ADD_ORDER_SENT]`
  - `[ADD_EXECUTED]`
  - `[ADD_CANCELLED]`
  - `[ADD_RECONCILED]`
  - `[ADD_BLOCKED]`

---

## SQL

### 1. 최근 add 이력 확인

```sql
SELECT
  id,
  recommendation_id,
  stock_code,
  stock_name,
  strategy,
  add_type,
  event_type,
  event_time,
  order_no,
  request_qty,
  executed_qty,
  prev_buy_price,
  new_buy_price,
  prev_buy_qty,
  new_buy_qty,
  add_count_after,
  reason
FROM holding_add_history
ORDER BY event_time DESC
LIMIT 50;
```

### 2. 특정 종목 add 흐름 추적

```sql
SELECT
  event_time,
  stock_code,
  stock_name,
  add_type,
  event_type,
  request_qty,
  executed_qty,
  prev_buy_price,
  new_buy_price,
  prev_buy_qty,
  new_buy_qty,
  add_count_after,
  reason,
  note
FROM holding_add_history
WHERE stock_code = '005930'
ORDER BY event_time DESC;
```

### 3. 현재 보유 종목의 add 관련 상태 확인

```sql
SELECT
  id,
  stock_code,
  stock_name,
  status,
  strategy,
  buy_price,
  buy_qty,
  add_count,
  avg_down_count,
  pyramid_count,
  last_add_type,
  last_add_at,
  scale_in_locked,
  hard_stop_price,
  trailing_stop_price
FROM recommendation_history
WHERE status IN ('HOLDING', 'SELL_ORDERED')
ORDER BY last_add_at DESC NULLS LAST, id DESC;
```

### 4. `scale_in_locked` 걸린 종목 확인

```sql
SELECT
  id,
  stock_code,
  stock_name,
  status,
  strategy,
  buy_price,
  buy_qty,
  add_count,
  last_add_type,
  last_add_at,
  scale_in_locked
FROM recommendation_history
WHERE scale_in_locked = true
ORDER BY last_add_at DESC NULLS LAST, id DESC;
```

### 5. 오늘 add 체결 집계

```sql
SELECT
  stock_code,
  stock_name,
  add_type,
  COUNT(*) AS event_count,
  SUM(executed_qty) AS total_executed_qty
FROM holding_add_history
WHERE event_type = 'EXECUTED'
  AND event_time::date = CURRENT_DATE
GROUP BY stock_code, stock_name, add_type
ORDER BY total_executed_qty DESC NULLS LAST;
```

### 6. `ORDER_SENT` 이후 후속 이벤트가 없는 이상 건 확인

```sql
SELECT
  h1.recommendation_id,
  h1.stock_code,
  h1.stock_name,
  h1.order_no,
  h1.event_time AS sent_time,
  h1.add_type,
  h1.request_qty
FROM holding_add_history h1
WHERE h1.event_type = 'ORDER_SENT'
  AND NOT EXISTS (
    SELECT 1
    FROM holding_add_history h2
    WHERE h2.recommendation_id = h1.recommendation_id
      AND h2.event_time >= h1.event_time
      AND h2.event_type IN ('EXECUTED', 'CANCELLED', 'RECONCILED')
      AND (
        h2.order_no = h1.order_no
        OR (h2.event_type = 'RECONCILED' AND h2.order_no IS NULL)
      )
  )
ORDER BY h1.event_time DESC;
```

---

## 로그 체크 명령

### 1. 실시간 add 로그 모니터링

```bash
tail -f logs/bot_history.log | grep --line-buffered -E '\[ADD_ORDER_SENT\]|\[ADD_EXECUTED\]|\[ADD_CANCELLED\]|\[ADD_RECONCILED\]|\[ADD_BLOCKED\]'
```

### 2. 최근 add 로그 요약

```bash
grep -E '\[ADD_ORDER_SENT\]|\[ADD_EXECUTED\]|\[ADD_CANCELLED\]|\[ADD_RECONCILED\]|\[ADD_BLOCKED\]' logs/bot_history.log | tail -n 100
```

### 3. `scale_in_locked` 관련 로그 확인

```bash
grep -E 'scale_in_locked|\[ADD_CANCELLED\]|\[ADD_RECONCILE_PENDING\]|\[ADD_RECONCILED\]' logs/bot_history.log | tail -n 100
```

### 4. 특정 종목 로그 추적

```bash
grep '005930' logs/bot_history.log | tail -n 100
```

---

## 정상 패턴

- `[ADD_ORDER_SENT]` 후 같은 `order_no`로 `[ADD_EXECUTED]` 또는 `[ADD_CANCELLED]`가 이어진다.
- `holding_add_history`에 `ORDER_SENT -> EXECUTED` 또는 `ORDER_SENT -> CANCELLED` 흐름이 남는다.
- `recommendation_history.buy_price`가 add 체결 후 평균단가로 자연스럽게 바뀐다.
- `recommendation_history.buy_qty`가 실제 계좌 수량과 일치한다.
- `scale_in_locked = false` 상태가 유지된다.
- 대사 후 lock이 풀릴 때 `[ADD_RECONCILED]` 로그가 남는다.

---

## 즉시 개입해야 하는 패턴

- `[ADD_BLOCKED] ... reason=pending_add_cancel_failed`
- `[ADD_CANCELLED] ... scale_in_locked=True`
- `ORDER_SENT`는 있는데 `EXECUTED`, `CANCELLED`, `RECONCILED`가 장시간 없다.
- `recommendation_history.scale_in_locked = true` 종목이 누적된다.
- 실제 계좌 수량과 `buy_qty`가 다르다.
- 실제 계좌 평단과 `buy_price`가 다르다.
- 스캘핑 종목에서 `AVG_DOWN` 이벤트가 발생한다.

---

## 운영 첫날 권장 루틴

### 장 시작 후 30분

- add 로그 실시간 모니터링
- `scale_in_locked` 종목 0건인지 확인

### 첫 add 체결 발생 시

- `holding_add_history` 1건 직접 조회
- `buy_price`, `buy_qty`, `add_count`가 기대대로 갱신됐는지 확인

### 장중 1~2회

- orphan `ORDER_SENT` 조회 SQL 실행
- 잠금 종목 조회 SQL 실행

### 장 마감 후

- 오늘 `EXECUTED` 이벤트 종목별 집계 확인
- 실제 계좌 잔고와 `recommendation_history` 대조

---

## 수동 점검 우선순위

- `scale_in_locked = true` 종목
- `ORDER_SENT`만 있고 후속 이벤트가 없는 종목
- 실제 계좌 수량과 `buy_qty`가 다른 종목
- 실제 계좌 평단과 `buy_price`가 다른 종목

---

## 이상 발생 시 대응 절차

1. `logs/bot_history.log`에서 해당 종목의 `[ADD_ORDER_SENT]`, `[ADD_EXECUTED]`, `[ADD_CANCELLED]`, `[ADD_RECONCILED]`, `[ADD_BLOCKED]` 로그를 먼저 확인합니다.
2. `recommendation_history`와 `holding_add_history`를 조회해 `buy_price`, `buy_qty`, `scale_in_locked`, 마지막 add 이벤트를 확인합니다.
3. 실제 계좌에서 해당 종목의 잔고 수량, 평균단가, 미체결 주문 존재 여부를 확인합니다.
4. 계좌와 DB가 불일치하거나 `scale_in_locked = true`이면 원인 정리 전까지 해당 종목 add를 재개하지 말고, 필요하면 전역 `ENABLE_SCALE_IN = False`로 즉시 차단합니다.
5. 계좌 truth가 확정되면 DB/메모리를 대사하고, 미체결 주문 정리까지 끝난 뒤에만 `scale_in_locked`를 해제합니다.

---

## 운영 메모

- 초기 운영 단계에서는 add 체결 직후 `holding_add_history` 기록이 정상적으로 쌓이는지 우선 확인합니다.
- `scale_in_locked`는 자동 해제되더라도, 원인 로그와 계좌 truth를 같이 확인하는 것이 안전합니다.
- 정책 이상이 의심되면 즉시 `ENABLE_SCALE_IN = False`로 전역 차단 후 원인 분석을 진행합니다.
