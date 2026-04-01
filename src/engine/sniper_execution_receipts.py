"""Order execution receipt handlers for the sniper engine."""

import threading
import time
from datetime import datetime

from src.database.models import RecommendationHistory
from src.utils import kiwoom_utils
from src.utils.logger import log_error
from src.engine.sniper_time import TIME_15_30


KIWOOM_TOKEN = None
DB = None
event_bus = None
ACTIVE_TARGETS = None
highest_prices = None
_get_fast_state = None
_weighted_avg = None
_now_ts = None


def bind_execution_dependencies(
    *,
    kiwoom_token=None,
    db=None,
    event_bus_instance=None,
    active_targets=None,
    highest_prices_map=None,
    get_fast_state=None,
    weighted_avg=None,
    now_ts=None,
):
    global KIWOOM_TOKEN, DB, event_bus, ACTIVE_TARGETS, highest_prices
    global _get_fast_state, _weighted_avg, _now_ts

    if kiwoom_token is not None:
        KIWOOM_TOKEN = kiwoom_token
    if db is not None:
        DB = db
    if event_bus_instance is not None:
        event_bus = event_bus_instance
    if active_targets is not None:
        ACTIVE_TARGETS = active_targets
    if highest_prices_map is not None:
        highest_prices = highest_prices_map
    if get_fast_state is not None:
        _get_fast_state = get_fast_state
    if weighted_avg is not None:
        _weighted_avg = weighted_avg
    if now_ts is not None:
        _now_ts = now_ts

# ==========================================
def _find_execution_target(code, exec_type, order_no):
    normalized_order_no = str(order_no or '').strip()

    if exec_type == 'BUY':
        status_key = 'BUY_ORDERED'
        order_key = 'odno'
    else:
        status_key = 'SELL_ORDERED'
        order_key = 'sell_odno'

    status_candidates = [
        stock for stock in ACTIVE_TARGETS
        if str(stock.get('code', '')).strip()[:6] == code and stock.get('status') == status_key
    ]

    if normalized_order_no:
        exact_match = next(
            (
                stock for stock in status_candidates
                if str(stock.get(order_key, '')).strip() == normalized_order_no
            ),
            None
        )
        if exact_match:
            return exact_match

    if len(status_candidates) == 1:
        return status_candidates[0]

    return None


def _update_db_for_buy(target_id, exec_price, now, target_stock):
    """비동기로 실행되는 BUY 체결 DB 업데이트 및 알림"""
    try:
        with DB.get_session() as session:
            session.query(RecommendationHistory).filter_by(id=target_id).update({
                "buy_price": exec_price,
                "status": "HOLDING",
                "buy_time": now
            })

        print(f"✅ [영수증: ID {target_id}] {target_stock.get('code')} 실제 매수 체결가 {exec_price:,}원 및 시간 반영 완료!")

        pending_msg = target_stock.get('pending_buy_msg')
        audience = target_stock.get('msg_audience', 'ADMIN_ONLY')
        if pending_msg:
            final_msg = pending_msg.replace("그물망 투척!", "그물망 매수 체결!").replace("스나이퍼 포착!", "스나이퍼 매수 체결!")
            final_msg += f"\n✅ **실제 체결가:** `{exec_price:,}원`"
            event_bus.publish('TELEGRAM_BROADCAST', {'message': final_msg, 'audience': audience, 'parse_mode': 'Markdown'})
        else:
            event_bus.publish(
                'TELEGRAM_BROADCAST',
                {'message': f"🛒 **[{target_stock.get('name')}]** 매수 체결 완료!\n체결가: `{exec_price:,}원`", 'audience': audience, 'parse_mode': 'Markdown'}
            )
        # 메모리에서 pending_buy_msg 제거 (스레드에서 제거)
        target_stock.pop('pending_buy_msg', None)
    except Exception as e:
        log_error(f"🚨 [DB 에러] ID {target_id} BUY 처리 중 에러: {e}")


def _update_db_for_sell(target_id, exec_price, now, target_stock, strategy, is_scalp_revive):
    """비동기로 실행되는 SELL 체결 DB 업데이트 및 알림 (스캘핑 부활 제외)"""
    try:
        with DB.get_session() as session:
            record = session.query(RecommendationHistory).filter_by(id=target_id).first()
            if not record:
                return

            safe_buy_price = float(record.buy_price) if record.buy_price is not None else 0.0
            if safe_buy_price > 0:
                profit_rate = round(((exec_price - safe_buy_price) / safe_buy_price) * 100, 2)
            else:
                profit_rate = 0.0
                print(f"⚠️ [수익률 계산 불가] ID {target_id}의 매수가(buy_price)가 누락되어 수익률을 0%로 처리합니다.")

            record.status = 'COMPLETED'
            record.sell_price = exec_price
            record.sell_time = now
            record.profit_rate = profit_rate

            print(f"🎉 [매매 완료: ID {target_id}] {target_stock.get('code')} 실매도가: {exec_price:,}원 / 수익률: {profit_rate}%")

            pending_msg = target_stock.get('pending_sell_msg')
            audience = target_stock.get('msg_audience', 'ADMIN_ONLY')
            if pending_msg:
                final_msg = pending_msg.replace("매도 전송", "매도 체결 완료").replace("[익절 주문]", "[익절 완료]").replace("[손절 주문]", "[손절 완료]")
                final_msg += f"\n✅ **실제 체결가:** `{exec_price:,}원` (확정 수익률: `{profit_rate:+.2f}%`)"
                event_bus.publish('TELEGRAM_BROADCAST', {'message': final_msg, 'audience': audience, 'parse_mode': 'HTML'})
            else:
                sign = "🎊 [익절 완료]" if profit_rate > 0 else "📉 [손절 완료]"
                event_bus.publish(
                    'TELEGRAM_BROADCAST',
                    {'message': f"{sign} **[{target_stock.get('name')}]** 매도 체결!\n체결가: `{exec_price:,}원`\n수익률: `{profit_rate:+.2f}%`", 'audience': audience, 'parse_mode': 'HTML'}
                )
            # 메모리에서 pending_sell_msg 제거
            target_stock.pop('pending_sell_msg', None)
    except Exception as e:
        log_error(f"🚨 [DB 에러] ID {target_id} SELL 처리 중 에러: {e}")


def handle_real_execution(exec_data):
    """
    웹소켓에서 주문 체결(00) 통보가 오면 이 함수가 즉시 실행됩니다.
    고유 ID(id)를 추적하여 해당 매매 건의 실제 체결가를 정확히 기록합니다.
    """
    code = str(exec_data.get('code', '')).strip()[:6]
    exec_type = str(exec_data.get('type', '')).upper()
    order_no = str(exec_data.get('order_no', '') or '').strip()

    try:
        exec_price = int(float(exec_data.get('price', 0) or 0))
    except Exception:
        exec_price = 0

    try:
        exec_qty = int(float(exec_data.get('qty', 0) or 0))
    except Exception:
        exec_qty = 0

    if not code or exec_price <= 0:
        return

    state = _get_fast_state(code)
    if state and exec_qty > 0:
        with state['lock']:
            matched = False

            if exec_type == 'BUY':
                if order_no and order_no == str(state.get('buy_ord_no', '')):
                    state['cum_buy_qty'] += exec_qty
                    state['cum_buy_amount'] += exec_price * exec_qty
                    state['avg_buy_price'] = _weighted_avg(state['cum_buy_amount'], state['cum_buy_qty'])
                    state['updated_at'] = _now_ts()
                    matched = True

            elif exec_type == 'SELL':
                valid_sell_ord_nos = {
                    str(state.get('sell_ord_no', '') or ''),
                    str(state.get('pending_cancel_ord_no', '') or ''),
                }
                if order_no and order_no in valid_sell_ord_nos:
                    state['cum_sell_qty'] += exec_qty
                    state['cum_sell_amount'] += exec_price * exec_qty
                    state['avg_sell_price'] = _weighted_avg(state['cum_sell_amount'], state['cum_sell_qty'])
                    state['updated_at'] = _now_ts()
                    matched = True

        if matched:
            return

    now = datetime.now()
    now_t = now.time()

    target_stock = _find_execution_target(code, exec_type, order_no)
    if not target_stock:
        print(f"[EXEC_IGNORED] no matching active order. code={code}, type={exec_type}, order_no={order_no}")
        return

    target_id = target_stock.get('id')
    if not target_id:
        print(f"🚨 [영수증] 종목 {code}의 고유 ID가 메모리에 없습니다. DB 업데이트가 불가능합니다.")
        return

    new_watch_id = None
    is_scalp_revive = False
    
    # ==========================================
    # 1️⃣ DB 상태 업데이트 (ID 기반 정밀 타격)
    # ==========================================
    if exec_type == 'BUY':
        # 먼저 메모리 업데이트
        target_stock['status'] = 'HOLDING'
        target_stock['buy_price'] = exec_price
        target_stock['buy_time'] = now
        highest_prices[code] = exec_price

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
                sell_res = kiwoom_orders.send_sell_order_market(
                    code=code, qty=sell_qty, token=KIWOOM_TOKEN, order_type="00", price=preset_tp_price
                )
                target_stock['preset_tp_ord_no'] = sell_res.get('ord_no') if isinstance(sell_res, dict) else ''

                # 지정가 주문 실패 시에도 출구 엔진 자체는 유지
                if not target_stock['preset_tp_ord_no']:
                    print(f"⚠️ [SCALP 출구엔진] {target_stock.get('name')} 지정가 매도 주문번호 미수신. 보유 감시로 보강 필요.")
                else:
                    print(f"🎯 [SCALP 출구엔진 셋업] {target_stock.get('name')} +1.5% 지정가({preset_tp_price:,}원) 1차 매도망 전개 완료.")

        # pending_buy_msg는 백그라운드 스레드에서 제거
        # 백그라운드 DB 업데이트 실행
        threading.Thread(
            target=_update_db_for_buy,
            args=(target_id, exec_price, now, target_stock),
            daemon=True
        ).start()
            
    elif exec_type == 'SELL':
        # record 조회 (동기) - 빠른 조회
        try:
            with DB.get_session() as session:
                record = session.query(RecommendationHistory).filter_by(id=target_id).first()
                if not record:
                    return
                safe_buy_price = float(record.buy_price) if record.buy_price is not None else 0.0
                if safe_buy_price > 0:
                    profit_rate = round(((exec_price - safe_buy_price) / safe_buy_price) * 100, 2)
                else:
                    profit_rate = 0.0
                    print(f"⚠️ [수익률 계산 불가] ID {target_id}의 매수가(buy_price)가 누락되어 수익률을 0%로 처리합니다.")
                raw_strategy = (record.strategy or target_stock.get('strategy') or 'KOSPI_ML').upper()
                strategy = 'SCALPING' if raw_strategy in ['SCALPING', 'SCALP'] else raw_strategy
                # ✅ 일관성 통일: 15:30 이전까지만 스캘핑 부활
                is_scalp_revive = (strategy == 'SCALPING') and (now_t < TIME_15_30)
        except Exception as e:
            log_error(f"🚨 [DB 조회 에러] ID {target_id} SELL 처리 중 에러: {e}")
            return

        if is_scalp_revive:
            # 스캘핑 부활: 동기 DB 업데이트 (새 레코드 삽입 필요)
            try:
                with DB.get_session() as session:
                    record = session.query(RecommendationHistory).filter_by(id=target_id).first()
                    if not record:
                        return
                    record.status = 'COMPLETED'
                    record.sell_price = exec_price
                    record.sell_time = now
                    record.profit_rate = profit_rate
                    print(f"🎉 [매매 완료: ID {target_id}] {code} 실매도가: {exec_price:,}원 / 수익률: {profit_rate}%")
                    # 새 레코드 삽입
                    new_record = RecommendationHistory(
                        rec_date=now.date(),
                        stock_code=code,
                        stock_name=record.stock_name,
                        buy_price=0,
                        status='WATCHING',
                        strategy='SCALPING',
                        trade_type='SCALP',
                        position_tag='MIDDLE',
                        prob=record.prob
                    )
                    session.add(new_record)
                    session.flush()
                    new_watch_id = new_record.id
                    # 알림
                    pending_msg = target_stock.get('pending_sell_msg')
                    audience = target_stock.get('msg_audience', 'ADMIN_ONLY')
                    if pending_msg:
                        final_msg = pending_msg.replace("매도 전송", "매도 체결 완료").replace("[익절 주문]", "[익절 완료]").replace("[손절 주문]", "[손절 완료]")
                        final_msg += f"\n✅ **실제 체결가:** `{exec_price:,}원` (확정 수익률: `{profit_rate:+.2f}%`)"
                        event_bus.publish('TELEGRAM_BROADCAST', {'message': final_msg, 'audience': audience, 'parse_mode': 'HTML'})
                    else:
                        sign = "🎊 [익절 완료]" if profit_rate > 0 else "📉 [손절 완료]"
                        event_bus.publish(
                            'TELEGRAM_BROADCAST',
                            {'message': f"{sign} **[{target_stock.get('name')}]** 매도 체결!\n체결가: `{exec_price:,}원`\n수익률: `{profit_rate:+.2f}%`", 'audience': audience, 'parse_mode': 'HTML'}
                        )
            except Exception as e:
                log_error(f"🚨 [DB 에러] ID {target_id} SELL 처리 중 에러: {e}")
                return
            # 메모리 업데이트 (부활)
            highest_prices.pop(code, None)
            target_stock['id'] = new_watch_id
            target_stock['status'] = 'WATCHING'
            target_stock['buy_price'] = 0
            target_stock['buy_qty'] = 0
            target_stock['added_time'] = time.time()
            target_stock['position_tag'] = 'MIDDLE'
            for key in [
                'odno', 'order_time', 'order_price', 'buy_time',
                'target_buy_price', 'pending_buy_msg',
                'pending_sell_msg', 'sell_odno', 'sell_order_time',
                'sell_target_price'
            ]:
                target_stock.pop(key, None)
        else:
            # 일반 SELL: 먼저 메모리 업데이트
            highest_prices.pop(code, None)
            target_stock['status'] = 'COMPLETED'
            target_stock['sell_time'] = now.strftime('%H:%M:%S')
            # pending_sell_msg는 백그라운드에서 제거
            # 백그라운드 DB 업데이트 실행
            threading.Thread(
                target=_update_db_for_sell,
                args=(target_id, exec_price, now, target_stock, strategy, is_scalp_revive),
                daemon=True
            ).start()

    # 메모리 업데이트는 각 조건문 내에서 이미 수행됨

