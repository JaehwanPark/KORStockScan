# AI API 입력용 설계 + 소단위 unified diff 3종 세트

대상 파일: `src/engine/kiwoom_sniper_v2.py`

이 문서는 **AI API에 그대로 넣기 좋은 형태**로 정리한 실행 문서다.  
설계 목적, 적용 순서, 기능별 소단위 diff, 검증 체크리스트를 한 번에 담았다.

---

## 적용 순서

반드시 아래 순서로 적용한다.

1. **Patch 1** — `handle_condition_matched()` 중복 매핑 제거
2. **Patch 2** — `analyze_stock_now()`의 AI 엔진 재생성 제거
3. **Patch 3** — S15 Fast-Track Safe Mode 도입  
   - `RecommendationHistory`에 shadow record 유지
   - 익절 지정가 취소 후 시장가 전환은 **취소 확인 또는 잔량 재조회 후 실행**
   - S15는 **종목당 당일 1회 진입**

---

## 공통 설계 원칙

- `resolve_condition_profile()`를 **조건식 해석의 단일 진실원(single source of truth)** 으로 사용한다.
- `analyze_stock_now()`는 전역 `AI_ENGINE`을 재사용한다.
- S15는 일반 상태머신을 **완전 대체**하지 않고, **Fast-Track + Shadow record** 구조로 도입한다.
- S15 체결 반영은 **종목코드(code)** 만 보지 않고 **주문번호(order_no)** 를 우선 매칭한다.
- 부분체결 평균단가는 **누적 체결금액 / 누적 체결수량** 으로 계산한다.
- S15는 **종목당 당일 1회 진입**만 허용한다.
- 익절 지정가 취소 후 시장가 전환은 **취소 확인 또는 잔량 재조회 후** 실행한다.

---

## Patch 1 — `handle_condition_matched()` 중복 매핑 제거

### 목적

현재 파일은 이미 `resolve_condition_profile()`와 `get_condition_target_date()`를 갖고 있지만,  
`handle_condition_matched()`는 내부에서 조건명을 다시 파싱하고 있다.  
이 구조는 시간대/전략/포지션/목표일 기준이 **두 군데** 존재하게 만들어 S15, VCP, 스윙 예약 로직이 쉽게 꼬인다.

이 패치는 `handle_condition_matched()`가 **반드시 `resolve_condition_profile()` 결과만 사용**하도록 바꾼다.

### unified diff

```diff
--- a/src/engine/kiwoom_sniper_v2.py
+++ b/src/engine/kiwoom_sniper_v2.py
@@
 def handle_condition_matched(payload):
     """실시간 조건검색(Push)으로 날아온 종목을 즉각 감시망(WATCHING)에 올립니다."""
     global KIWOOM_TOKEN, DB, ACTIVE_TARGETS, event_bus
     code = str(payload.get('code', '')).strip()[:6]
     cnd_name = str(payload.get('condition_name', '') or '')
     if not code:
         return

     now_t = datetime.now().time()
-
-    target_strategy = 'SCALPING'
-    target_trade_type = 'SCALP'
-    is_next_day_target = False
-    target_position_tag = 'MIDDLE'
-
-    # =========================================================
-    # ⏰ 시간대별 검색식 필터링
-    # =========================================================
-    if "scalp_candid_aggressive_01" in cnd_name or "scalp_candid_normal_01" in cnd_name:
-        if not _in_time_window(now_t, dt_time(9, 0), dt_time(9, 30)):
-            return
-
-    elif "scalp_strong_01" in cnd_name:
-        if not _in_time_window(now_t, dt_time(9, 20), dt_time(11, 0)):
-            return
-
-    elif "scalp_underpress_01" in cnd_name:
-        if not _in_time_window(now_t, dt_time(9, 40), dt_time(13, 0)):
-            return
-
-    elif "scalp_shooting_01" in cnd_name:
-        if not _in_time_window(now_t, dt_time(9, 40), dt_time(13, 30)):
-            return
-
-    elif "scalp_afternoon_01" in cnd_name:
-        if not _in_time_window(now_t, dt_time(13, 0), dt_time(15, 20)):
-            return
-
-    elif "kospi_short_swing_01" in cnd_name or "kospi_midterm_swing_01" in cnd_name:
-        if not _in_time_window(now_t, dt_time(14, 30), dt_time(15, 30)):
-            return
-        target_strategy = 'KOSPI_ML'
-        target_trade_type = 'MAIN'
-        is_next_day_target = True
-
-    elif "vcp_candid_01" in cnd_name:
-        # ✅ overnight 구간 보정: 15:30 ~ 23:59 or 00:00 ~ 07:00
-        if not _in_time_window(now_t, dt_time(15, 30), dt_time(7, 0)):
-            return
-        target_strategy = 'SCALPING'
-        target_trade_type = 'SCALP'
-        is_next_day_target = True
-        target_position_tag = 'VCP_CANDID'
-
-    elif "vcp_shooting_01" in cnd_name:
-        if not _in_time_window(now_t, dt_time(9, 0), dt_time(15, 0)):
-            return
-        target_position_tag = 'VCP_SHOOTING'
-
-    elif "vcp_shooting_next_01" in cnd_name:
-        if not _in_time_window(now_t, dt_time(15, 30), dt_time(23, 59, 59)):
-            return
-        target_strategy = 'SCALPING'
-        target_trade_type = 'SCALP'
-        is_next_day_target = True
-        target_position_tag = 'VCP_NEXT'
-    
-    elif "s15_scan_base" in cnd_name:
-        if not _in_time_window(now_t, dt_time(9, 2), dt_time(10, 30)):
-            return
-        target_strategy = 'SCALPING'
-        target_trade_type = 'SCALP'
-        target_position_tag = 'S15_CANDID'
-
-    elif "s15_trigger_break" in cnd_name:
-        if not _in_time_window(now_t, dt_time(9, 5), dt_time(11, 00)):
-            return
-        target_strategy = 'SCALPING'
-        target_trade_type = 'SCALP'
-        target_position_tag = 'S15_SHOOTING'
-
-    else:
+    profile = resolve_condition_profile(cnd_name)
+    if not profile:
         return
-    # =========================================================
+
+    if not _in_time_window(now_t, profile['start'], profile['end']):
+        return
+
+    target_strategy = profile['strategy']
+    target_trade_type = profile['trade_type']
+    is_next_day_target = profile['is_next_day_target']
+    target_position_tag = profile['position_tag']

     # 당일 감시망에 이미 있으면 일반 케이스는 스킵
     # 단, VCP_SHOOTING은 기존 CANDID -> SHOOTING 승격이 있으므로 통과
     if any(str(t.get('code', '')).strip()[:6] == code for t in ACTIVE_TARGETS):
         if not is_next_day_target and target_position_tag != 'VCP_SHOOTING':
             return

     try:
-        import holidays
-
         basic_info = kiwoom_utils.get_basic_info_ka10001(KIWOOM_TOKEN, code)
         name = basic_info.get('Name', code)
-
-        if is_next_day_target:
-            kr_hols = holidays.KR(years=[datetime.now().year, datetime.now().year + 1])
-            hol_dates = np.array([np.datetime64(d) for d in kr_hols.keys()], dtype='datetime64[D]')
-            today_np = np.datetime64(datetime.now().date())
-            next_bday_np = np.busday_offset(today_np, 1, holidays=hol_dates)
-            target_date = pd.to_datetime(next_bday_np).date()
-        else:
-            target_date = datetime.now().date()
+        target_date = get_condition_target_date(is_next_day_target)

         print(f"🦅 [V3 헌터] 조건검색 0.1초 포착! {name}({code}) 감시망 편입 준비 (목표일: {target_date})")
```

### 적용 후 기대 효과

- 조건명 해석 기준이 한 곳으로 모인다.
- `handle_condition_unmatched()`와 목표일 계산 기준이 맞춰진다.
- S15/VCP/스윙 예약 로직이 이후 패치와 충돌할 여지가 줄어든다.

---

## Patch 2 — `analyze_stock_now()`의 AI 엔진 재생성 제거

### 목적

현재 `analyze_stock_now()`는 호출할 때마다 `GeminiSniperEngine`을 새로 만든다.  
하지만 엔진은 이미 전역 `AI_ENGINE`을 쓰는 구조가 있고, 다른 실시간 경로도 이 방향에 맞춰져 있다.

이 패치는 **전역 `AI_ENGINE`이 있으면 재사용하고**, 없을 때만 1회 초기화하도록 통일한다.

### unified diff

```diff
--- a/src/engine/kiwoom_sniper_v2.py
+++ b/src/engine/kiwoom_sniper_v2.py
@@
     # =========================================================
     # 💡 Gemini 3.0 Flash 호출
     # =========================================================
     ai_report = "⚠️ AI 리포트 생성 실패"
     api_keys = [v for k, v in CONF.items() if k.startswith("GEMINI_API_KEY")]
-    
-    if api_keys:
-        try:
-            from src.engine.ai_engine import GeminiSniperEngine
-            ai_engine = GeminiSniperEngine(api_keys=api_keys)
-            ai_report = ai_engine.generate_realtime_report(stock_name, code, quant_data_text)
-        except Exception as e:
-            ai_report = f"⚠️ AI 리포트 생성 중 오류: {e}"
-    else:
+
+    if AI_ENGINE is None and api_keys:
+        try:
+            from src.engine.ai_engine import GeminiSniperEngine
+            AI_ENGINE = GeminiSniperEngine(api_keys=api_keys)
+        except Exception as e:
+            ai_report = f"⚠️ AI 엔진 초기화 중 오류: {e}"
+
+    if AI_ENGINE is not None:
+        try:
+            ai_report = AI_ENGINE.generate_realtime_report(stock_name, code, quant_data_text)
+        except Exception as e:
+            ai_report = f"⚠️ AI 리포트 생성 중 오류: {e}"
+    else:
         ai_report = "⚠️ GEMINI_API_KEY 미설정으로 AI 리포트를 생성할 수 없습니다."
```

### 적용 후 기대 효과

- 텔레그램/관리자 수동 분석 호출이 많아도 엔진 재초기화 비용이 줄어든다.
- API 키 로테이션/세션/레이트리밋 관리가 안정된다.
- 전체 엔진의 AI 사용 패턴이 일관된다.

---

## Patch 3 — S15 Fast-Track Safe Mode 도입

### 목적

이 패치는 S15를 아래 구조로 도입한다.

- `s15_scan_base` → **arm(화이트리스트 진입)**
- `s15_trigger_break` → **Fast-Track 실행**
- `RecommendationHistory` → **shadow record만 유지**
- 체결 반영 → **order_no 기준**
- 익절 지정가 취소 후 시장가 전환 → **취소 확인 또는 잔량 재조회 후 실행**
- 재진입 → **종목당 당일 1회만 허용**

### 구현 메모

- 이 패치는 **Patch 1**이 먼저 적용된 상태를 기준으로 한다.
- `kiwoom_orders`의 로컬 래퍼 이름이 환경마다 다를 수 있으므로,  
  S15 전용 주문 어댑터 `_send_s15_limit_buy`, `_send_s15_limit_sell`, `_send_s15_market_sell` 를 추가한다.
- 이 어댑터만 로컬 환경에 맞게 연결하면 나머지 로직은 거의 그대로 사용할 수 있다.

### unified diff

```diff
--- a/src/engine/kiwoom_sniper_v2.py
+++ b/src/engine/kiwoom_sniper_v2.py
@@
 global ACTIVE_TARGETS
 ACTIVE_TARGETS = []
 LAST_AI_CALL_TIMES = {}
+
+# ==========================================
+# ⚡ [S15 v2] Fast-Track 상태 관리
+# ==========================================
+FAST_SCALP_POOL = {}
+FAST_TRADE_STATE = {}
+FAST_REENTRY_BLOCK = {}
+FAST_LOCK = threading.RLock()
@@
 def _in_time_window(now_value, start, end):
     return (start <= now_value <= end) if start <= end else (now_value >= start or now_value <= end)
+
+def _now_ts():
+    return time.time()
+
+def _arm_s15_candidate(code, name, cnd_name, ttl_sec=180):
+    now = _now_ts()
+    with FAST_LOCK:
+        FAST_SCALP_POOL[code] = {
+            'name': name or code,
+            'armed_at': now,
+            'last_seen': now,
+            'base_condition': cnd_name,
+            'expires_at': now + ttl_sec,
+        }
+
+def _unarm_s15_candidate(code):
+    with FAST_LOCK:
+        FAST_SCALP_POOL.pop(code, None)
+
+def _is_s15_armed(code):
+    now = _now_ts()
+    with FAST_LOCK:
+        item = FAST_SCALP_POOL.get(code)
+        if not item:
+            return False
+        if item.get('expires_at', 0) < now:
+            FAST_SCALP_POOL.pop(code, None)
+            return False
+        return True
+
+def _is_s15_reentry_blocked(code):
+    return FAST_REENTRY_BLOCK.get(code, 0) > _now_ts()
+
+def _block_s15_reentry(code, seconds=60*60*6):
+    FAST_REENTRY_BLOCK[code] = _now_ts() + seconds
+
+def _get_fast_state(code):
+    with FAST_LOCK:
+        return FAST_TRADE_STATE.get(code)
+
+def _set_fast_state(code, state):
+    with FAST_LOCK:
+        FAST_TRADE_STATE[code] = state
+
+def _pop_fast_state(code):
+    with FAST_LOCK:
+        return FAST_TRADE_STATE.pop(code, None)
+
+def _get_tick_size_for_price(price):
+    if hasattr(kiwoom_utils, 'get_tick_size'):
+        return int(kiwoom_utils.get_tick_size(price))
+    if price < 2000:
+        return 1
+    if price < 5000:
+        return 5
+    if price < 20000:
+        return 10
+    if price < 50000:
+        return 50
+    if price < 200000:
+        return 100
+    if price < 500000:
+        return 500
+    return 1000
+
+def _price_ticks_up(curr_price, ticks=2):
+    price = int(curr_price)
+    for _ in range(ticks):
+        price += _get_tick_size_for_price(price)
+    return int(price)
+
+def _target_price_pct_up(avg_buy_price, pct=1.8):
+    ideal = avg_buy_price * (1 + (pct / 100.0))
+    price = int(avg_buy_price)
+    while price < ideal:
+        price += _get_tick_size_for_price(price)
+    return int(price)
+
+def _weighted_avg(amount, qty):
+    if qty <= 0:
+        return 0
+    return int(amount / qty)
+
+def create_s15_shadow_record(code, name):
+    global DB
+    try:
+        with DB.get_session() as session:
+            record = RecommendationHistory(
+                rec_date=datetime.now().date(),
+                stock_code=code,
+                stock_name=name,
+                buy_price=0,
+                trade_type='SCALP',
+                strategy='S15_FAST',
+                status='WATCHING',
+                position_tag='S15_FAST'
+            )
+            session.add(record)
+            session.flush()
+            return record.id
+    except Exception as e:
+        log_error(f"🚨 S15 shadow record 생성 실패 ({code}): {e}")
+        return None
+
+def update_s15_shadow_record(shadow_id, **kwargs):
+    global DB
+    if not shadow_id:
+        return
+    try:
+        with DB.get_session() as session:
+            record = session.query(RecommendationHistory).filter_by(id=shadow_id).first()
+            if not record:
+                return
+            for k, v in kwargs.items():
+                if hasattr(record, k):
+                    setattr(record, k, v)
+    except Exception as e:
+        log_error(f"🚨 S15 shadow record 갱신 실패 ({shadow_id}): {e}")
+
+def _send_s15_limit_buy(code, qty, price):
+    return kiwoom_orders.send_buy_order_market(
+        code=code,
+        qty=qty,
+        token=KIWOOM_TOKEN,
+        order_type="00",
+        price=int(price)
+    )
+
+def _send_s15_limit_sell(code, qty, price):
+    if hasattr(kiwoom_orders, 'send_sell_order_limit'):
+        return kiwoom_orders.send_sell_order_limit(
+            code=code,
+            qty=qty,
+            token=KIWOOM_TOKEN,
+            price=int(price)
+        )
+    raise NotImplementedError("kiwoom_orders.send_sell_order_limit 래퍼를 연결하세요.")
+
+def _send_s15_market_sell(code, qty):
+    if hasattr(kiwoom_orders, 'send_sell_order_market'):
+        return kiwoom_orders.send_sell_order_market(
+            code=code,
+            qty=qty,
+            token=KIWOOM_TOKEN
+        )
+    raise NotImplementedError("kiwoom_orders.send_sell_order_market 래퍼를 연결하세요.")
+
+def _extract_ord_no(res):
+    if isinstance(res, dict):
+        return str(res.get('ord_no', '') or res.get('odno', '') or '')
+    return ''
+
+def _is_ok_response(res):
+    if isinstance(res, dict):
+        return str(res.get('return_code', res.get('rt_cd', ''))) == '0'
+    return bool(res)
+
+def _confirm_s15_cancel_or_reload_remaining(code, state, wait_sec=0.5):
+    until = _now_ts() + wait_sec
+    while _now_ts() < until:
+        with state['lock']:
+            rem_qty = max(0, state['cum_buy_qty'] - state['cum_sell_qty'])
+        if rem_qty == 0:
+            return 0
+        time.sleep(0.05)
+    try:
+        inventory = kiwoom_orders.get_my_inventory(KIWOOM_TOKEN)
+        real_stock = next((item for item in (inventory or []) if str(item.get('code', '')).strip()[:6] == code), None)
+        if real_stock:
+            return int(float(real_stock.get('qty', 0) or 0))
+    except Exception as e:
+        log_error(f"⚠️ S15 잔량 재조회 실패 ({code}): {e}")
+    with state['lock']:
+        return max(0, state['cum_buy_qty'] - state['cum_sell_qty'])
+
+def execute_fast_track_scalp_v2(code, name, trigger_price, ratio=0.10):
+    state = _get_fast_state(code)
+    if not state:
+        return
+    try:
+        rt_data = WS_MANAGER.get_latest_data(code) if WS_MANAGER else {}
+        curr_price = int(float((rt_data or {}).get('curr', 0) or 0))
+        if curr_price <= 0:
+            curr_price = int(trigger_price or 0)
+        if curr_price <= 0:
+            state['status'] = 'FAILED'
+            update_s15_shadow_record(state.get('shadow_id'), status='EXPIRED')
+            return
+
+        if AI_ENGINE is None:
+            state['status'] = 'FAILED'
+            log_error(f"🚨 S15 AI_ENGINE 미초기화 ({code})")
+            update_s15_shadow_record(state.get('shadow_id'), status='EXPIRED')
+            return
+
+        ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=10)
+        ai_res = AI_ENGINE.analyze_target(
+            name,
+            rt_data or {'curr': curr_price, 'orderbook': {'asks': [], 'bids': []}},
+            ticks,
+            recent_candles=[],
+            strategy="SCALPING"
+        )
+
+        if ai_res.get('action') != 'BUY' or ai_res.get('score', 0) < 80:
+            state['status'] = 'FAILED'
+            update_s15_shadow_record(state.get('shadow_id'), status='EXPIRED')
+            return
+
+        buy_price = _price_ticks_up(curr_price, 2)
+        deposit = kiwoom_orders.get_deposit(KIWOOM_TOKEN)
+        req_qty = kiwoom_orders.calc_buy_qty(buy_price, deposit, ratio=ratio)
+        if req_qty <= 0:
+            state['status'] = 'FAILED'
+            update_s15_shadow_record(state.get('shadow_id'), status='EXPIRED')
+            return
+
+        buy_res = _send_s15_limit_buy(code, req_qty, buy_price)
+        if not _is_ok_response(buy_res):
+            state['status'] = 'FAILED'
+            update_s15_shadow_record(state.get('shadow_id'), status='EXPIRED')
+            return
+
+        with state['lock']:
+            state['status'] = 'BUY_SENT'
+            state['buy_ord_no'] = _extract_ord_no(buy_res)
+            state['req_buy_qty'] = req_qty
+            state['updated_at'] = _now_ts()
+        update_s15_shadow_record(state.get('shadow_id'), status='BUY_ORDERED')
+
+        expire_at = _now_ts() + 20.0
+        while _now_ts() < expire_at:
+            with state['lock']:
+                if state['cum_buy_qty'] >= req_qty:
+                    break
+            time.sleep(0.1)
+
+        with state['lock']:
+            real_buy_qty = state['cum_buy_qty']
+            avg_buy_price = state['avg_buy_price']
+            buy_ord_no = state.get('buy_ord_no', '')
+
+        if real_buy_qty <= 0:
+            if buy_ord_no:
+                kiwoom_orders.send_cancel_order(code=code, orig_ord_no=buy_ord_no, token=KIWOOM_TOKEN, qty=0)
+            state['status'] = 'CANCELLED'
+            update_s15_shadow_record(state.get('shadow_id'), status='EXPIRED')
+            return
+
+        if real_buy_qty < req_qty and buy_ord_no:
+            kiwoom_orders.send_cancel_order(code=code, orig_ord_no=buy_ord_no, token=KIWOOM_TOKEN, qty=0)
+
+        if avg_buy_price <= 0:
+            avg_buy_price = buy_price
+
+        target_price = _target_price_pct_up(avg_buy_price, 1.8)
+        stop_price = int(avg_buy_price * (1 - 0.007))
+
+        with state['lock']:
+            state['status'] = 'HOLDING'
+            state['target_price'] = target_price
+            state['stop_price'] = stop_price
+            state['updated_at'] = _now_ts()
+        update_s15_shadow_record(
+            state.get('shadow_id'),
+            status='HOLDING',
+            buy_price=avg_buy_price,
+            buy_qty=real_buy_qty
+        )
+
+        sell_res = _send_s15_limit_sell(code, real_buy_qty, target_price)
+        if not _is_ok_response(sell_res):
+            state['status'] = 'FAILED'
+            update_s15_shadow_record(state.get('shadow_id'), status='EXPIRED')
+            return
+
+        with state['lock']:
+            state['sell_ord_no'] = _extract_ord_no(sell_res)
+            state['status'] = 'EXIT_SENT'
+            state['updated_at'] = _now_ts()
+
+        while True:
+            time.sleep(0.1)
+
+            with state['lock']:
+                if state['cum_sell_qty'] >= state['cum_buy_qty'] > 0:
+                    state['status'] = 'DONE'
+                    break
+
+            rt = WS_MANAGER.get_latest_data(code) if WS_MANAGER else {}
+            curr_p = int(float((rt or {}).get('curr', 0) or 0))
+            if curr_p <= 0 or avg_buy_price <= 0:
+                continue
+
+            profit_rate = ((curr_p - avg_buy_price) / avg_buy_price) * 100
+            if profit_rate <= -0.7:
+                with state['lock']:
+                    sell_ord_no = state.get('sell_ord_no', '')
+
+                if sell_ord_no:
+                    cancel_res = kiwoom_orders.send_cancel_order(
+                        code=code, orig_ord_no=sell_ord_no, token=KIWOOM_TOKEN, qty=0
+                    )
+                    if _is_ok_response(cancel_res):
+                        with state['lock']:
+                            state['pending_cancel_ord_no'] = sell_ord_no
+
+                rem_qty = _confirm_s15_cancel_or_reload_remaining(code, state, wait_sec=0.5)
+                if rem_qty > 0:
+                    market_res = _send_s15_market_sell(code, rem_qty)
+                    if _is_ok_response(market_res):
+                        with state['lock']:
+                            state['sell_ord_no'] = _extract_ord_no(market_res) or state.get('sell_ord_no', '')
+                            state['updated_at'] = _now_ts()
+                break
+
+        with state['lock']:
+            final_buy = state['avg_buy_price']
+            final_sell = state['avg_sell_price']
+            final_qty = state['cum_buy_qty']
+
+        final_profit_rate = 0.0
+        if final_buy > 0 and final_sell > 0:
+            final_profit_rate = round(((final_sell - final_buy) / final_buy) * 100, 2)
+
+        update_s15_shadow_record(
+            state.get('shadow_id'),
+            status='COMPLETED',
+            sell_price=final_sell or state.get('target_price', 0),
+            sell_time=datetime.now(),
+            profit_rate=final_profit_rate,
+            buy_price=final_buy,
+            buy_qty=final_qty
+        )
+    except Exception as e:
+        log_error(f"🚨 S15 Fast-Track 에러 ({code}): {e}")
+        update_s15_shadow_record(state.get('shadow_id'), status='EXPIRED')
+    finally:
+        _block_s15_reentry(code)
+        _unarm_s15_candidate(code)
+        _pop_fast_state(code)
```

```diff
--- a/src/engine/kiwoom_sniper_v2.py
+++ b/src/engine/kiwoom_sniper_v2.py
@@
 def handle_condition_matched(payload):
@@
     try:
         basic_info = kiwoom_utils.get_basic_info_ka10001(KIWOOM_TOKEN, code)
         name = basic_info.get('Name', code)
         target_date = get_condition_target_date(is_next_day_target)
+
+        # =========================================================
+        # ⚡ [S15 v2] Fast-Track 하이패스
+        # =========================================================
+        if target_position_tag == 'S15_CANDID':
+            _arm_s15_candidate(code, name, cnd_name, ttl_sec=180)
+            return
+
+        if target_position_tag == 'S15_SHOOTING':
+            if not _is_s15_armed(code):
+                return
+            if _is_s15_reentry_blocked(code):
+                return
+            if _get_fast_state(code):
+                return
+
+            shadow_id = create_s15_shadow_record(code, name)
+            state = {
+                'lock': threading.RLock(),
+                'name': name,
+                'status': 'ARMED',
+                'buy_ord_no': '',
+                'sell_ord_no': '',
+                'pending_cancel_ord_no': '',
+                'req_buy_qty': 0,
+                'cum_buy_qty': 0,
+                'cum_buy_amount': 0,
+                'avg_buy_price': 0,
+                'cum_sell_qty': 0,
+                'cum_sell_amount': 0,
+                'avg_sell_price': 0,
+                'created_at': _now_ts(),
+                'updated_at': _now_ts(),
+                'target_price': 0,
+                'stop_price': 0,
+                'shadow_id': shadow_id,
+                'trigger_price': 0,
+            }
+            _set_fast_state(code, state)
+
+            rt = WS_MANAGER.get_latest_data(code) if WS_MANAGER else {}
+            trigger_price = int(float((rt or {}).get('curr', 0) or 0))
+            state['trigger_price'] = trigger_price
+
+            threading.Thread(
+                target=execute_fast_track_scalp_v2,
+                args=(code, name, trigger_price, 0.10),
+                daemon=False
+            ).start()
+            return
+        # =========================================================

         print(f"🦅 [V3 헌터] 조건검색 0.1초 포착! {name}({code}) 감시망 편입 준비 (목표일: {target_date})")
```

```diff
--- a/src/engine/kiwoom_sniper_v2.py
+++ b/src/engine/kiwoom_sniper_v2.py
@@
 def handle_condition_unmatched(payload):
@@
     profile = resolve_condition_profile(cnd_name)
     if not profile:
         return
+
+    if profile['position_tag'] == 'S15_CANDID':
+        _unarm_s15_candidate(code)
+        return
+
+    if profile['position_tag'] == 'S15_SHOOTING':
+        return

     target_date = get_condition_target_date(profile['is_next_day_target'])
```

```diff
--- a/src/engine/kiwoom_sniper_v2.py
+++ b/src/engine/kiwoom_sniper_v2.py
@@
 def handle_real_execution(exec_data):
@@
     try:
         exec_price = int(float(exec_data.get('price', 0) or 0))
     except Exception:
         exec_price = 0
+
+    try:
+        exec_qty = int(float(exec_data.get('qty', 0) or 0))
+    except Exception:
+        exec_qty = 0

     if not code or exec_price <= 0:
         return
+
+    state = _get_fast_state(code)
+    if state and exec_qty > 0:
+        with state['lock']:
+            matched = False
+
+            if exec_type == 'BUY':
+                if order_no and order_no == str(state.get('buy_ord_no', '')):
+                    state['cum_buy_qty'] += exec_qty
+                    state['cum_buy_amount'] += exec_price * exec_qty
+                    state['avg_buy_price'] = _weighted_avg(state['cum_buy_amount'], state['cum_buy_qty'])
+                    state['updated_at'] = _now_ts()
+                    matched = True
+
+            elif exec_type == 'SELL':
+                valid_sell_ord_nos = {
+                    str(state.get('sell_ord_no', '') or ''),
+                    str(state.get('pending_cancel_ord_no', '') or ''),
+                }
+                if order_no and order_no in valid_sell_ord_nos:
+                    state['cum_sell_qty'] += exec_qty
+                    state['cum_sell_amount'] += exec_price * exec_qty
+                    state['avg_sell_price'] = _weighted_avg(state['cum_sell_amount'], state['cum_sell_qty'])
+                    state['updated_at'] = _now_ts()
+                    matched = True
+
+        if matched:
+            return

     now = datetime.now()
     now_t = now.time()
```

### 적용 후 기대 효과

- `s15_scan_base`는 arm만 하고 일반 감시망을 오염시키지 않는다.
- `s15_trigger_break`는 arm 상태일 때만 실행된다.
- S15가 장애 복구 가능성을 완전히 잃지 않는다.
- 부분체결 평균단가와 잔량 처리가 정확해진다.
- 익절 지정가 취소 후 시장가 전환 시 이중매도 위험을 낮춘다.

---

## 검증 체크리스트

### Patch 1
- [ ] `handle_condition_matched()`가 `resolve_condition_profile()`만 사용한다.
- [ ] `get_condition_target_date()`를 직접 재호출한다.
- [ ] 함수 내부에서 `import holidays`와 수동 목표일 계산이 제거됐다.

### Patch 2
- [ ] `analyze_stock_now()`가 `AI_ENGINE`을 재생성하지 않는다.
- [ ] `AI_ENGINE is None`일 때만 1회 초기화한다.

### Patch 3
- [ ] `s15_scan_base`는 `FAST_SCALP_POOL`만 arm한다.
- [ ] `s15_trigger_break`는 arm 상태일 때만 Fast-Track 스레드를 시작한다.
- [ ] `RecommendationHistory`에 `strategy='S15_FAST'`, `position_tag='S15_FAST'` shadow record가 남는다.
- [ ] S15 체결 반영이 `order_no` 기준으로 이뤄진다.
- [ ] 부분체결 평균단가가 누적 금액/수량으로 계산된다.
- [ ] 익절 지정가 취소 후 시장가 전환 전에 취소 확인 또는 잔량 재조회가 들어간다.
- [ ] `FAST_REENTRY_BLOCK`로 종목당 당일 1회 진입이 유지된다.
- [ ] S15 전용 주문 어댑터 함수가 로컬 `kiwoom_orders` 래퍼에 맞게 연결됐다.

---

## AI API 프롬프트에 같이 넣으면 좋은 한 줄

> 아래 설계와 diff를 순서대로 적용하라. Patch 1 → Patch 2 → Patch 3 순서로 반영하고, Patch 3의 S15 주문 어댑터는 현재 프로젝트의 `kiwoom_orders` 함수명에 맞게 연결하라. 기존 로직을 임의로 재작성하지 말고, diff 범위 밖의 코드는 유지하라.
