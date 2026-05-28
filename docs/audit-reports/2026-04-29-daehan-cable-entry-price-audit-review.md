# 대한전선(001440) Submitted-But-Unfilled 진입가 감리 검토 (`2026-04-29`)

> 작성시각: `2026-04-29 KST`
> 검토 대상: `대한전선(001440)` `record_id=4219`, 주문번호 `0049602`
> 검토 목적: `submitted`는 발생했으나 `fill`이 발생하지 않은 스캘핑 진입에서, 미체결 원인이 `진입가 산정`, `유동성`, `latency`, `timeout 정책` 중 어디에 있는지 감리 관점에서 판정한다.
> 검증 범위: runtime `pipeline_events`, `execution_receipts`, `trade_review` snapshot, 진입가 계산 코드

---

## 1. 결론

### 1-1. 1차 판정

`대한전선(001440)` 케이스의 주원인은 `진입가 산정 부적정`이다.

- `latency SAFE`
- `orderbook_stability_observed=False`
- `submitted 성공`
- 그러나 실제 주문가는 `best_bid/best_ask` 대비 지나치게 낮은 `48800`

이 형상은 `유동성 부족으로 어쩔 수 없이 미체결`이 아니라, `체결 가능성이 거의 없는 가격으로 제출`한 케이스에 가깝다.

### 1-2. 보조 판정

`BUY_ORDERED timeout`도 과도하다.

`target_buy_price > 0`인 스캘핑 주문은 `1200초` reserve timeout을 사용하고 있어, 이미 체결 가능성이 낮은 주문이 실전 상태 머신에서 너무 오래 살아남는다. 이는 `entry drought`와는 별개의 기대값 누수다.

---

## 2. 핵심 증적

### 2-1. 제출 당시 호가/안정성 증적

`ENTRY_PIPELINE orderbook_stability_observed`

- `best_bid=50500`
- `best_ask=50900`
- `quote_age_p90_ms=197.552`
- `unstable_quote_observed=False`

근거 로그: [pipeline_events_2026-04-29.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-04-29.jsonl:172796)

해석:

- 호가 신선도나 불안정성 때문에 체결이 막힌 상황으로 보기 어렵다.
- 제출 직전 시장 기준 가격대는 `50500~50900`이었다.

### 2-2. 진입 arm / target cap 증적

`ENTRY_PIPELINE entry_armed`

- `target_buy_price=48800`
- `reason=qualification_passed`
- `dynamic_reason=strong_absolute_override`

근거 로그: [pipeline_events_2026-04-29.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-04-29.jsonl:172794)

해석:

- 실주문가를 강하게 아래로 누르는 상한선이 arm 시점에 이미 설정돼 있었다.

### 2-3. latency guard 계산 증적

`ENTRY_PIPELINE latency_pass`

- `latency=SAFE`
- `decision=ALLOW_NORMAL`
- `entry_price_guard=normal_defensive`
- `normal_defensive_order_price=50400`
- `latency_guarded_order_price=50400`
- `order_price=48800`

근거 로그: [pipeline_events_2026-04-29.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-04-29.jsonl:172798)

해석:

- latency/방어 가격 엔진은 `50400` 수준의 정상 defensive price를 계산했다.
- 그러나 최종 제출가는 다시 `48800`으로 clamp 됐다.
- 따라서 미체결 원인을 `latency guard가 너무 보수적이었다`고 해석하면 틀린다.

### 2-4. 실제 제출 증적

`ENTRY_PIPELINE order_bundle_submitted`

- `requested_qty=2`
- `entry_price_guard=normal_defensive`
- `normal_defensive_order_price=50400`
- `order_price=48800`

근거 로그: [pipeline_events_2026-04-29.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-04-29.jsonl:172802)

해석:

- 제출 자체는 정상적으로 발생했다.
- 문제는 `submitted 여부`가 아니라 `submitted price`다.

### 2-5. 미체결 지속 증적

`sniper_execution_receipts`

- `10:47:25` `type=BUY status=접수 order_no=0049602`
- `11:07:26` `type=BUY status=접수 order_no=0049602`

근거 로그: [sniper_execution_receipts_info.log](/home/ubuntu/KORStockScan/logs/sniper_execution_receipts_info.log:2529), [sniper_execution_receipts_info.log](/home/ubuntu/KORStockScan/logs/sniper_execution_receipts_info.log:2530)

해석:

- 최소 20분 이상 `접수` 상태가 유지됐다.
- 이 역시 `체결 가능한 가격이 아니었다`는 해석과 정합적이다.

---

## 3. 코드 경로 검증

### 3-1. 최종 주문가 clamp 경로

[sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py:823) 부근 로직:

- `normal_defensive_order_price = move_price_by_ticks(latest_price, -1tick)`
- `latency_guarded_order_price = defensive_order.price`
- 이후 `if target_buy_price > 0: order_price = min(order_price, target_cap)`

핵심:

- defensive price가 `50400`으로 계산되어도
- `target_buy_price=48800`이면 최종 주문가는 `48800`으로 내려간다

따라서 이번 케이스는 `defensive order builder`가 아니라 `target cap`이 최종 가격을 결정했다.

### 3-2. target_buy_price 생성 경로

[sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:2435) 에서 `radar.get_smart_target_price()`를 호출해 `final_target_buy_price`를 만든다.

[signal_radar.py](/home/ubuntu/KORStockScan/src/engine/signal_radar.py:200)~[265] 에서:

- AI 점수와 `v_pw`로 기본 drop/tick을 정하고
- 호가 잔량 비율로 조정한 뒤
- `49000 <= final_target <= 49950`이면 `48800`으로 강제 내리는 라운드피겨 회피 로직이 있다

이번 케이스는 이 `48800` 고정 로직과 일치한다.

### 3-3. timeout 경로

[sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:4999)

- `if stock.get('target_buy_price', 0) > 0: timeout_sec = RESERVE_TIMEOUT_SEC`
- 기본 `RESERVE_TIMEOUT_SEC = 1200`

해석:

- 스캘핑 주문이라도 `target_buy_price`가 있으면 `20분 대기` 쪽으로 분기된다
- 체결 가능성이 낮은 deep bid 주문이 실전에서 너무 오래 유지될 수 있다

---

## 4. 왜곡 지점

### 4-1. trade_review snapshot의 `buy_price`

[trade_review_2026-04-29.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/trade_review_2026-04-29.json:60708) 에서는 해당 레코드가

- `status=BUY_ORDERED`
- `buy_price=50500`

으로 보인다.

이는 [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:3198) 에서 `BUY_ORDERED` 장부 업데이트 시 `buy_price=curr_price`를 넣기 때문이다.
실제 주문가는 `48800`인데 장부상 `50500`으로 보일 수 있어, 감리/사후분석 시 `제출가격 vs 당시현재가` 비교가 흐려진다.

즉:

- runtime 제출가격 증적은 `pipeline_events order_price`
- snapshot `buy_price`는 당시 현재가에 가까운 값

으로 해석해야 한다.

---

## 5. 감사인 판단

### 5-1. 확정 가능한 사항

1. 이 케이스는 `latency SAFE`였다.
2. 제출 직전 호가 안정성은 양호했다.
3. defensive price는 `50400`으로 계산됐다.
4. 실제 제출가는 `48800`으로 clamp 됐다.
5. 이 가격은 `best_bid=50500`, `best_ask=50900` 대비 너무 낮았다.
6. `BUY_ORDERED` 상태는 최소 `20분` 지속됐다.

### 5-2. 따라서 닫히는 원인

주원인:

- `radar target cap 과도`

보조원인:

- `target_buy_price > 0 => 1200초 reserve timeout` 스캘핑 부적합

보류원인:

- 순수 유동성 부족
- latency 차단
- orderbook instability

이 셋은 이번 케이스의 1차 원인으로 보기 어렵다.

---

## 6. 후속 권고

### 6-1. 가격 정책

우선 검토 대상:

1. `SCALPING`에서 `target_buy_price`가 `normal_defensive_order_price`보다 과도하게 낮을 때 clamp를 제한할 것인지
2. `round-figure avoidance`의 `48800` 고정 규칙이 breakout/scalping 문맥에서도 유지돼야 하는지
3. `target_buy_price`를 `order cap`이 아니라 `counterfactual/reference`로만 남기고 실주문은 defensive price를 따르게 할지

### 6-2. timeout 정책

우선 검토 대상:

1. `SCALPING + target_buy_price>0` 주문에 `1200초` reserve timeout을 그대로 적용할지
2. breakout/scanner 스캘핑은 별도 짧은 timeout으로 분리할지
3. `best_bid/ask`와의 괴리가 일정 수준 이상이면 early cancel 또는 reprice를 허용할지

### 6-3. 리포트 정합성

감리/사후분석 왜곡 방지를 위해:

1. `BUY_ORDERED buy_price=curr_price`와 `actual_submitted_order_price`를 분리 기록할 필요가 있다
2. `trade_review` 또는 별도 observation 축에서 `submitted_price`, `best_bid_at_submit`, `best_ask_at_submit`를 직접 보이게 할 필요가 있다

---

## 7. 관련 체크리스트

- [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md)
  - `[EntryPriceDaehanCable0429-Postclose] 대한전선(001440) submitted-but-unfilled 진입가 cap/timeout 적정성 판정`

---

## 8. 참고 근거

- [pipeline_events_2026-04-29.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-04-29.jsonl:172794)
- [pipeline_events_2026-04-29.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-04-29.jsonl:172796)
- [pipeline_events_2026-04-29.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-04-29.jsonl:172798)
- [pipeline_events_2026-04-29.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-04-29.jsonl:172802)
- [sniper_execution_receipts_info.log](/home/ubuntu/KORStockScan/logs/sniper_execution_receipts_info.log:2529)
- [sniper_execution_receipts_info.log](/home/ubuntu/KORStockScan/logs/sniper_execution_receipts_info.log:2530)
- [trade_review_2026-04-29.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/trade_review_2026-04-29.json:60708)
- [signal_radar.py](/home/ubuntu/KORStockScan/src/engine/signal_radar.py:200)
- [signal_radar.py](/home/ubuntu/KORStockScan/src/engine/signal_radar.py:260)
- [sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py:823)
- [sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py:827)
- [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:2435)
- [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:2841)
- [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:3198)
- [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:4999)
