# 🚀 [KORStockScan V15.1] SCALPING 출구 엔진 및 S15 Fail-safe 통합 리팩토링 가이드 (AI API 주입용 수정판)

**대상 파일:** `src/engine/kiwoom_sniper_v2.py`  
**목적:**  
1) 일반 장중 스캘핑(MIDDLE)에만 선제적 지정가 매도 기반 출구 엔진을 적용하고,  
2) VCP/스윙성 스캘프는 기존 보유 AI/트레일링을 유지하며,  
3) S15 Fast-Track은 고아 포지션이 생기지 않도록 fail-safe를 강화한다.

AI 어시스턴트는 아래 Step 0 ~ Step 5를 읽고, **명시된 anchor point 주변만 최소 수정**으로 반영하라.

---

## Step 0: 사전 확인 및 공통 제약

### 0-1. 주문 함수 시그니처 확인
`src/engine/kiwoom_orders.py`의 `send_sell_order_market` (또는 범용 주문 함수)가 `order_type` 파라미터를 받을 수 있는지 확인하라.

이번 리팩토링의 모든 **긴급 청산 기본값**은 다음이다.

- 주문 타입: **최유리(IOC)**
- 주문구분 코드: **`16`**

즉 함수명이 `send_sell_order_market` 이더라도, 실제 동작은 반드시 `order_type="16"` 으로 결정한다.

### 0-2. 절대 지켜야 할 제약
1. 기존 로직을 불필요하게 재작성하지 말고, 명시된 함수와 분기점(anchor point)만 수정하라.
2. 새 출구 엔진은 **일반 SCALPING(MIDDLE)** 에만 적용한다.
3. `VCP_NEXT`, `VCP_SHOOTING`, 스윙성 스캘프(`KOSPI_ML`, `KOSDAQ_ML`)는 기존 보유 AI/트레일링을 유지한다.
4. 일반 SCALPING 새 출구 엔진은 기존 `handle_holding_state()` 의 무거운 AI 스무딩/트레일링 로직과 절대 동시에 돌면 안 된다.
5. 부분체결이 있어도 **+1.5% 지정가 매도 셋업은 1회만 초기화**되어야 한다.
6. 긴급 청산 주문 후에는 중복 주문이 나가지 않도록 필요한 상태값을 저장하라.
7. S15는 익절 지정가 실패 시 절대 `FAILED/EXPIRED` 로 바로 종료하지 말고, 보호 상태를 유지하라.
8. S15는 `finally` 에서 무조건 상태를 지우면 안 된다. 완전 청산 또는 무진입 종료일 때만 cleanup 가능하다.
9. S15 재진입 차단은 **실제 진입이 발생한 경우**에만 적용한다.
10. 현재 파일에 Patch 1/2가 아직 없다면 함께 반영하라.
   - `handle_condition_matched()` 는 `resolve_condition_profile()` 만 사용
   - `analyze_stock_now()` 는 전역 `AI_ENGINE` 재사용

---

## Step 1: 공통 긴급 청산 및 잔량 확인 유틸리티 추가
**[위치]** `kiwoom_sniper_v2.py` 파일 내 전역 변수 선언부 아래, 공통 함수들이 모여있는 곳.

아래의 래퍼 함수 2개를 추가하라.

```python
def _send_exit_best_ioc(code, qty, token):
    """[공통 긴급 청산 래퍼] 최유리(IOC, 16) 조건으로 즉각 청산 시도"""
    from src.engine import kiwoom_orders
    return kiwoom_orders.send_sell_order_market(
        code=code,
        qty=qty,
        token=token,
        order_type="16"  # 최유리(IOC)
    )

def _confirm_cancel_or_reload_remaining(code, orig_ord_no, token, expected_qty):
    """[공통 유틸] 주문 취소 후 실제 계좌 잔고를 재조회하여 팔아야 할 정확한 잔량(rem_qty) 반환"""
    import time
    from src.engine import kiwoom_orders

    # 1) orig_ord_no 가 있을 때만 취소 요청
    if orig_ord_no:
        kiwoom_orders.send_cancel_order(code=code, orig_ord_no=orig_ord_no, token=token, qty=0)
        time.sleep(0.5)  # 키움 서버 반영 대기

    # 2) 계좌 재조회 폴백
    try:
        real_inventory = kiwoom_orders.get_my_inventory(token)
        real_stock = next((item for item in (real_inventory or []) if str(item.get('code', '')).strip()[:6] == code), None)
        if real_stock:
            real_qty = int(float(real_stock.get('qty', 0) or 0))
            if real_qty > 0:
                return real_qty
    except Exception:
        pass

    # 3) 최종 폴백
    try:
        return max(0, int(expected_qty or 0))
    except Exception:
        return 0
```

### 중요 보강사항
- 기존 문서와 달리, `orig_ord_no` 가 없을 때는 취소 주문을 보내지 말고 바로 잔량 재조회로 가야 한다.
- 이 유틸은 일반 SCALPING과 S15가 공통으로 사용한다.

---

## Step 2: 일반 SCALPING(MIDDLE) 매수 체결 직후 상태 초기화 및 선제 지정가 주문
**[위치]** `handle_real_execution(exec_data)` 함수 내부의 `if exec_type == 'BUY':` 블록 안.  
**[목적]** 실제 BUY 체결이 발생하여 메모리를 업데이트하는 시점에, 해당 종목이 일반 SCALPING(MIDDLE) 조건이라면 즉시 +1.5% 지정가 매도를 전송하고 신규 상태 변수들을 주입한다.

### 지시사항
아래 조건에서만 이 로직을 적용하라.

- `raw_strategy in ['SCALPING', 'SCALP']`
- `pos_tag == 'MIDDLE'`

그리고 다음 **방어조건**을 반드시 넣어라.

- `target_stock.get('exit_mode') != 'SCALP_PRESET_TP'`
- 또는 `preset_tp_ord_no` 가 비어 있을 때만 1회 초기화

즉 **부분체결이 여러 번 들어와도 새 출구 엔진 셋업은 한 번만** 수행되어야 한다.

### 삽입 코드 예시
```python
        # 기존 로직: target_stock['status'] = 'HOLDING'

        raw_strategy = (target_stock.get('strategy') or 'KOSPI_ML').upper()
        pos_tag = target_stock.get('position_tag', 'MIDDLE')

        if raw_strategy in ['SCALPING', 'SCALP'] and pos_tag == 'MIDDLE':
            # 부분체결 다중 이벤트 방지: 1회만 셋업
            if target_stock.get('exit_mode') != 'SCALP_PRESET_TP' and not target_stock.get('preset_tp_ord_no'):
                target_stock['exit_mode'] = 'SCALP_PRESET_TP'

                # 가능한 경우 누적 buy_qty / buy_price 기준 사용, 불가하면 exec_price 폴백
                base_buy_price = int(target_stock.get('buy_price') or exec_price or 0)
                if base_buy_price <= 0:
                    base_buy_price = exec_price

                preset_tp_price = kiwoom_utils.get_target_price_up(base_buy_price, 1.5)
                target_stock['preset_tp_price'] = preset_tp_price
                target_stock['hard_stop_pct'] = -0.7
                target_stock['protect_profit_pct'] = None
                target_stock['ai_review_done'] = False
                target_stock['ai_review_score'] = None
                target_stock['ai_review_action'] = None
                target_stock['exit_requested'] = False
                target_stock['exit_order_type'] = None
                target_stock['exit_order_time'] = None

                from src.engine import kiwoom_orders
                sell_qty = int(target_stock.get('buy_qty') or exec_qty or 0)
                sell_res = kiwoom_orders.send_sell_order_limit(
                    code=code, qty=sell_qty, token=KIWOOM_TOKEN, price=preset_tp_price
                )
                target_stock['preset_tp_ord_no'] = sell_res.get('ord_no') if isinstance(sell_res, dict) else ''

                # 지정가 주문 실패 시에도 출구 엔진 자체는 유지
                if not target_stock['preset_tp_ord_no']:
                    print(f"⚠️ [SCALP 출구엔진] {target_stock.get('name')} 지정가 매도 주문번호 미수신. 보유 감시로 보강 필요.")
                else:
                    print(f"🎯 [SCALP 출구엔진 셋업] {target_stock.get('name')} +1.5% 지정가({preset_tp_price:,}원) 1차 매도망 전개 완료.")
```

### 핵심 차이점
- 기존 초안의 `qty=exec_qty` 는 부분체결 환경에서 부정확할 수 있으므로, 가능하면 **현재 보유 수량 기준**으로 처리한다.
- 지정가 주문 실패 시에도 출구 엔진 상태 자체는 남겨서, 이후 보유 감시 로직에서 방어 가능하게 한다.

---

## Step 3: SCALPING 새 출구 엔진 감시 로직 (우회 처리 포함)
**[위치]** `handle_holding_state(...)` 함수의 최상단 부분.  
기존 변수 초기화 직후, 기존 SCALPING AI 감시 로직이 시작되기 전.

### 지시사항
`if stock.get('exit_mode') == 'SCALP_PRESET_TP':` 분기를 만들고 아래 로직을 작성하라.  
이 블록이 실행되면 반드시 `return` 으로 함수를 종료하여 기존의 무거운 AI 스무딩 및 트레일링 로직과 절대 충돌하지 않게 하라.

### 삽입 코드 예시
```python
    # 💡 [V15.1 신규] 일반 SCALPING(MIDDLE) 선제적 출구 엔진 (기존 로직 우회)
    if stock.get('exit_mode') == 'SCALP_PRESET_TP':
        # 중복 청산 방지
        if stock.get('exit_requested'):
            return

        profit_rate = (curr_p - buy_p) / buy_p * 100 if buy_p > 0 else 0.0
        orig_ord_no = stock.get('preset_tp_ord_no', '')
        expected_qty = stock.get('buy_qty', 0)

        # Case B: -0.7% 손절선 도달
        if profit_rate <= stock.get('hard_stop_pct', -0.7):
            print(f"🔪 [SCALP 출구엔진] {stock['name']} 손절선 터치({profit_rate:.2f}%). 즉각 최유리(IOC) 청산!")
            rem_qty = _confirm_cancel_or_reload_remaining(code, orig_ord_no, KIWOOM_TOKEN, expected_qty)
            if rem_qty > 0:
                sell_res = _send_exit_best_ioc(code, rem_qty, KIWOOM_TOKEN)
                stock['exit_requested'] = True
                stock['exit_order_type'] = '16'
                stock['exit_order_time'] = time.time()
                stock['sell_ord_no'] = sell_res.get('ord_no') if isinstance(sell_res, dict) else stock.get('sell_ord_no')
            stock['status'] = 'SELL_ORDERED'
            return

        # Case C: +0.8% 도달 시 AI 1회만 호출
        if profit_rate >= 0.8 and not stock.get('ai_review_done', False):
            print(f"🤖 [SCALP 출구엔진] {stock['name']} +0.8% 도달! AI 1회 검문 실시...")
            stock['ai_review_done'] = True

            if ai_engine:
                try:
                    recent_ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=10)
                    ai_decision = ai_engine.analyze_target(stock['name'], ws_data, recent_ticks, [], strategy="SCALPING")
                    ai_action = ai_decision.get('action', 'WAIT')
                    ai_score = ai_decision.get('score', 50)

                    stock['ai_review_action'] = ai_action
                    stock['ai_review_score'] = ai_score

                    if ai_action in ['SELL', 'DROP']:
                        print(f"🛑 [SCALP 출구엔진 AI] 모멘텀 둔화 감지. 1.5% 포기 후 즉시 최유리(IOC) 청산!")
                        rem_qty = _confirm_cancel_or_reload_remaining(code, orig_ord_no, KIWOOM_TOKEN, expected_qty)
                        if rem_qty > 0:
                            sell_res = _send_exit_best_ioc(code, rem_qty, KIWOOM_TOKEN)
                            stock['exit_requested'] = True
                            stock['exit_order_type'] = '16'
                            stock['exit_order_time'] = time.time()
                            stock['sell_ord_no'] = sell_res.get('ord_no') if isinstance(sell_res, dict) else stock.get('sell_ord_no')
                        stock['status'] = 'SELL_ORDERED'
                        return
                    else:
                        print(f"✅ [SCALP 출구엔진 AI] 돌파 모멘텀 유지(WAIT/BUY). 1.5% 유지, +0.3% 보호선 구축.")
                        stock['protect_profit_pct'] = 0.3

                except Exception as e:
                    print(f"⚠️ [SCALP 출구엔진 AI] 분석 실패: {e}. 기존 지정가 유지.")

        # Case D: +0.3% 보호선 이탈
        protect_pct = stock.get('protect_profit_pct')
        if protect_pct is not None and profit_rate <= protect_pct:
            print(f"🛡️ [SCALP 출구엔진] {stock['name']} +0.3% 보호선 이탈. 최유리(IOC) 약익절!")
            rem_qty = _confirm_cancel_or_reload_remaining(code, orig_ord_no, KIWOOM_TOKEN, expected_qty)
            if rem_qty > 0:
                sell_res = _send_exit_best_ioc(code, rem_qty, KIWOOM_TOKEN)
                stock['exit_requested'] = True
                stock['exit_order_type'] = '16'
                stock['exit_order_time'] = time.time()
                stock['sell_ord_no'] = sell_res.get('ord_no') if isinstance(sell_res, dict) else stock.get('sell_ord_no')
            stock['status'] = 'SELL_ORDERED'
            return

        # 기존 무거운 AI/트레일링과 절대 충돌 금지
        return
```

### 핵심 차이점
- 기존 초안보다 **중복 청산 방지용 상태값(`exit_requested`, `exit_order_time`, `sell_ord_no`)** 저장을 명시했다.
- AI는 +0.8%에서 **정확히 1회만** 호출된다.
- 지정가 취소 후 청산은 항상 `_confirm_cancel_or_reload_remaining()` 를 거친다.
- 이 블록이 실행되면 반드시 `return` 한다.

---

## Step 4: S15 Fast-Track fail-safe 보강
**[위치]** `execute_fast_track_scalp_v2(...)` 함수 내부의 익절 지정가 매도 설정 구간과 `finally` 블록.

### 목표
기존 문서와 가장 크게 다른 부분이다.  
S15는 익절 지정가 매도 실패 시 절대 바로 `FAILED/EXPIRED` 로 끝내면 안 된다.  
실제 계좌에 포지션이 남아 있을 수 있으므로, **보호 상태를 유지한 채 긴급 청산 또는 재시도 루프**로 넘어가야 한다.

### 4-1. 익절 지정가 매도 실패 처리 수정
아래와 같은 흐름으로 바꿔라.

```python
        sell_res = _send_s15_limit_sell(code, real_buy_qty, target_price)

        if not _is_ok_response(sell_res):
            print(f"🚨 [S15 Fail-safe] {name} 익절 지정가 매도 세팅 실패. 보호 상태 유지 후 최유리(IOC) 청산 시도.")
            with state['lock']:
                state['status'] = 'HOLDING_NEEDS_EXIT'
                state['updated_at'] = _now_ts()

            update_s15_shadow_record(
                state.get('shadow_id'),
                status='HOLDING'
            )

            rem_qty = _confirm_s15_cancel_or_reload_remaining(code, state, wait_sec=0.3)
            if rem_qty > 0:
                emergency_res = _send_exit_best_ioc(code, rem_qty, KIWOOM_TOKEN)
                if _is_ok_response(emergency_res):
                    with state['lock']:
                        state['sell_ord_no'] = _extract_ord_no(emergency_res)
                        state['status'] = 'EXIT_RETRY'
                        state['updated_at'] = _now_ts()
                else:
                    print(f"🚨 [S15 Fail-safe] {name} 긴급 청산 주문도 실패. 상태 유지 및 관리자 알림 필요.")
            else:
                print(f"ℹ️ [S15 Fail-safe] {name} 재조회 결과 잔량 없음. 자연 종료 가능.")

            # 여기서 FAILED/EXPIRED/return 로 바로 끝내지 말 것
```

### 4-2. 손절/보호 청산 시 긴급 주문 타입
S15 긴급 청산도 반드시 **최유리(IOC, 16)** 를 사용하라.

- 기존 `_send_s15_market_sell(...)` 를 그대로 두지 말고
- 내부에서 `order_type="16"` 을 쓰는 방향으로 바꾸거나
- `_send_exit_best_ioc(...)` 공통 래퍼를 재사용하라

### 4-3. `finally` 블록 조건부 cleanup
기존 초안과 달리, 아래 정책을 명시적으로 반영하라.

- `cleanup_allowed = False` 기본값
- 완전 청산 완료 또는 무진입 종료일 때만 `cleanup_allowed = True`
- `finally` 에서는 `if cleanup_allowed:` 일 때만 `_pop_fast_state(code)` 실행
- `_block_s15_reentry(code)` 도 실제 진입이 발생한 경우에만 실행

### 삽입 방향 예시
```python
    cleanup_allowed = False
    actual_entry_happened = False

    ...
    if buy_ord_no or state.get('cum_buy_qty', 0) > 0:
        actual_entry_happened = True

    ...
    if real_buy_qty <= 0:
        cleanup_allowed = True
        return

    ...
    if state['status'] == 'DONE':
        cleanup_allowed = True

    finally:
        if actual_entry_happened:
            _block_s15_reentry(code)
        _unarm_s15_candidate(code)
        if cleanup_allowed:
            _pop_fast_state(code)
```

### 핵심 차이점
- 기존 초안의 “finally 에서 무조건 정리”를 금지한다.
- `FAILED/EXPIRED` 로 덮어써서 상태를 날리지 않는다.
- 실제 진입이 없었던 경우에는 재진입 제한을 소모하지 않는다.

---

## Step 5: Patch 1 / Patch 2 누락 시 함께 반영
이 문서는 새 출구 엔진과 S15 fail-safe 중심이지만, 현재 파일에 아직 아래가 없다면 같이 반영하라.

### 5-1. `handle_condition_matched()` 중복 매핑 제거
`resolve_condition_profile()` 를 단일 기준으로 사용하고,  
조건명/시간대/전략/포지션/목표일 계산을 함수 내부에서 다시 하드코딩하지 마라.

### 5-2. `analyze_stock_now()` 전역 AI 엔진 재사용
`GeminiSniperEngine` 을 매 호출마다 새로 만들지 말고,  
전역 `AI_ENGINE` 이 있으면 반드시 재사용하라.  
없을 때만 1회 초기화하라.

---

## 최종 체크리스트

### 일반 SCALPING(MIDDLE)
- [ ] 부분체결이 있어도 +1.5% 지정가 매도 셋업이 1회만 실행되는가
- [ ] -0.7% 도달 시 지정가 취소 → 잔량 재조회 → 최유리(IOC, 16) 청산이 되는가
- [ ] +0.8% 도달 시 AI가 1회만 호출되는가
- [ ] AI가 SELL/DROP이면 즉시 최유리(IOC, 16) 청산되는가
- [ ] AI가 WAIT/BUY이면 +0.3% 보호선이 세팅되는가
- [ ] +0.3% 이탈 시 최유리(IOC, 16) 청산되는가
- [ ] 새 출구 엔진이 기존 SCALPING 보유 AI 루프와 동시에 돌지 않는가
- [ ] 긴급 청산 후 중복 청산 주문이 나가지 않는가

### VCP / 스윙성 스캘프
- [ ] 기존 보유 AI/트레일링 로직이 그대로 유지되는가
- [ ] MIDDLE이 아닌 스캘핑 파생 포지션이 새 출구 엔진에 잘못 들어가지 않는가

### S15
- [ ] 익절 지정가 실패 시 상태가 삭제되지 않는가
- [ ] `HOLDING_NEEDS_EXIT` / `EXIT_RETRY` 등 보호 상태가 남는가
- [ ] 긴급 청산이 최유리(IOC, 16)로 수행되는가
- [ ] 실제 진입 실패 시 재진입 1회 제한이 소모되지 않는가
- [ ] `finally` 에서 cleanup 이 조건부로만 일어나는가
- [ ] 동일 종목 일반 전략/잔고 존재 시 S15 중복 진입이 차단되는가

---

## AI API 주입용 프롬프트
아래 프롬프트를 함께 쓰면 좋다.

```text
다음 markdown 명세를 기준으로 src/engine/kiwoom_sniper_v2.py를 수정하라.

중요 제약:
1) 기존 로직을 불필요하게 재작성하지 말고, 명시된 anchor point 주변만 최소 수정한다.
2) 일반 SCALPING(MIDDLE)에만 새 출구 엔진을 적용하고, VCP_NEXT / VCP_SHOOTING / 스윙성 스캘프는 기존 보유 AI/트레일링을 유지한다.
3) 긴급 청산 기본값은 반드시 최유리(IOC)이며 order_type="16"을 사용한다.
4) send_sell_order_market는 범용 주문 함수로 간주하고, 주문 성격은 order_type으로 결정한다.
5) 일반 SCALPING 새 출구 엔진은 기존 SCALPING 보유 AI 루프와 절대 충돌하면 안 되므로, exit_mode='SCALP_PRESET_TP' 인 경우 handle_holding_state의 기존 무거운 AI/트레일링 로직을 반드시 bypass(return) 처리하라.
6) 일반 SCALPING의 +1.5% 지정가 매도 셋업은 BUY 체결 이벤트마다 반복되면 안 된다. 부분체결이 있어도 1회만 초기화되도록 방어 로직을 넣어라.
7) 긴급 청산 주문을 보낸 뒤에는 중복 주문이 나가지 않도록 exit_requested, exit_order_time, sell_ord_no 등 필요한 상태값을 저장하라.
8) _confirm_cancel_or_reload_remaining는 orig_ord_no가 있을 때만 취소 주문을 보내고, 없으면 바로 잔량 재조회로 가도록 안전하게 구현하라.
9) S15는 익절 지정가 실패 시 절대 FAILED/EXPIRED로 바로 끝내지 말고 HOLDING_NEEDS_EXIT 또는 EXIT_RETRY 보호 상태를 유지하라.
10) S15는 finally에서 무조건 상태를 삭제하면 안 된다. cleanup_allowed 플래그를 두고, 완전 청산 또는 무진입 종료일 때만 FAST_TRADE_STATE 정리를 허용하라.
11) S15 재진입 차단은 실제 진입이 발생한 경우(주문번호 발급 또는 실제 체결) 에만 적용하라.
12) 현재 파일에 Patch 1/2가 아직 없다면 함께 반영하라:
   - handle_condition_matched는 resolve_condition_profile()만 사용
   - analyze_stock_now는 전역 AI_ENGINE 재사용

출력 형식:
- unified diff 형태로만 출력
- diff 바깥의 설명은 최소화
- 변경한 이유가 중요한 곳에는 코드 주석으로 남겨라

검증 목표:
- 일반 SCALPING(MIDDLE)만 새 출구 엔진 적용
- +0.8%에서 AI 1회만 호출
- 긴급 청산은 최유리(IOC, 16)
- VCP/스윙성 스캘프 기존 로직 유지
- S15 익절 지정가 실패 시 고아 포지션이 생기지 않음
```
