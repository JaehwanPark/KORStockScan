"""S15 fast-track scalping helpers and state."""

import threading
import time
from datetime import datetime

from src.engine import kiwoom_orders
from src.database.models import RecommendationHistory
from src.utils import kiwoom_utils
from src.utils.logger import log_error


KIWOOM_TOKEN = None
WS_MANAGER = None
AI_ENGINE = None
DB = None


def bind_s15_dependencies(kiwoom_token=None, ws_manager=None, ai_engine=None, db=None):
    global KIWOOM_TOKEN, WS_MANAGER, AI_ENGINE, DB
    if kiwoom_token is not None:
        KIWOOM_TOKEN = kiwoom_token
    if ws_manager is not None:
        WS_MANAGER = ws_manager
    if ai_engine is not None:
        AI_ENGINE = ai_engine
    if db is not None:
        DB = db


# ==========================================
# ⚡ [S15 v2] Fast-Track 상태 관리
# ==========================================
FAST_SCALP_POOL = {}
FAST_TRADE_STATE = {}
FAST_REENTRY_BLOCK = {}
FAST_LOCK = threading.RLock()


def _now_ts():
    return time.time()


def _get_tick_size_for_price(price):
    if hasattr(kiwoom_utils, 'get_tick_size'):
        return int(kiwoom_utils.get_tick_size(price))
    if price < 2000:
        return 1
    if price < 5000:
        return 5
    if price < 20000:
        return 10
    if price < 50000:
        return 50
    if price < 200000:
        return 100
    if price < 500000:
        return 500
    return 1000


def _price_ticks_up(curr_price, ticks=2):
    price = int(curr_price)
    for _ in range(ticks):
        price += _get_tick_size_for_price(price)
    return int(price)


def _target_price_pct_up(avg_buy_price, pct=1.8):
    ideal = avg_buy_price * (1 + (pct / 100.0))
    price = int(avg_buy_price)
    while price < ideal:
        price += _get_tick_size_for_price(price)
    return int(price)


def _weighted_avg(amount, qty):
    if qty <= 0:
        return 0
    return int(amount / qty)


def _arm_s15_candidate(code, name, cnd_name, ttl_sec=180):
    now = _now_ts()
    with FAST_LOCK:
        FAST_SCALP_POOL[code] = {
            'name': name or code,
            'armed_at': now,
            'last_seen': now,
            'base_condition': cnd_name,
            'expires_at': now + ttl_sec,
        }
    try:
        _save_armed_candidate_to_db(code, name, cnd_name, now, now + ttl_sec)
    except Exception as exc:
        log_error(f"🚨 S15 armed candidate DB 저장 실패 ({code}): {exc}")


def _unarm_s15_candidate(code):
    with FAST_LOCK:
        FAST_SCALP_POOL.pop(code, None)
    _delete_armed_candidate_from_db(code)


def _save_armed_candidate_to_db(code, name, cnd_name, armed_at, expires_at):
    today = datetime.now().date()
    if DB is None:
        return
    with DB.get_session() as session:
        record = session.query(RecommendationHistory).filter_by(
            rec_date=today,
            stock_code=code,
            strategy='S15_CANDID'
        ).first()
        if record:
            record.stock_name = name
            record.position_tag = 'S15_CANDID:' + cnd_name
            record.nxt = armed_at
            record.profit_rate = expires_at
        else:
            record = RecommendationHistory(
                rec_date=today,
                stock_code=code,
                stock_name=name,
                trade_type='SCALP',
                strategy='S15_CANDID',
                status='WATCHING',
                position_tag='S15_CANDID:' + cnd_name,
                prob=0.0,
                nxt=armed_at,
                profit_rate=expires_at,
                buy_price=0,
                buy_qty=0
            )
            session.add(record)


def _delete_armed_candidate_from_db(code):
    today = datetime.now().date()
    if DB is None:
        return
    with DB.get_session() as session:
        session.query(RecommendationHistory).filter_by(
            rec_date=today,
            stock_code=code,
            strategy='S15_CANDID'
        ).delete()


def _restore_armed_candidates_from_db():
    """봇 재시작 시 DB에 저장된 S15_CANDID 후보들을 FAST_SCALP_POOL에 복원합니다."""
    today = datetime.now().date()
    now = _now_ts()
    if DB is None:
        return
    with DB.get_session() as session:
        records = session.query(RecommendationHistory).filter_by(
            rec_date=today,
            strategy='S15_CANDID',
            status='WATCHING'
        ).all()
        for rec in records:
            code = rec.stock_code
            name = rec.stock_name
            cnd_name = rec.position_tag.replace('S15_CANDID:', '') if rec.position_tag else ''
            armed_at = rec.nxt if rec.nxt else 0.0
            expires_at = rec.profit_rate if rec.profit_rate else 0.0
            if expires_at < now:
                session.query(RecommendationHistory).filter_by(
                    rec_date=today,
                    stock_code=code,
                    strategy='S15_CANDID'
                ).delete()
                continue
            with FAST_LOCK:
                FAST_SCALP_POOL[code] = {
                    'name': name or code,
                    'cnd_name': cnd_name,
                    'armed_at': armed_at,
                    'expires_at': expires_at
                }
        session.commit()


def _is_s15_armed(code):
    now = _now_ts()
    need_unarm = False
    with FAST_LOCK:
        item = FAST_SCALP_POOL.get(code)
        if not item:
            return False
        if item.get('expires_at', 0) < now:
            FAST_SCALP_POOL.pop(code, None)
            need_unarm = True
        else:
            return True
    if need_unarm:
        _unarm_s15_candidate(code)
    return False


def _is_s15_reentry_blocked(code):
    return FAST_REENTRY_BLOCK.get(code, 0) > _now_ts()


def _block_s15_reentry(code, seconds=60 * 60 * 6):
    FAST_REENTRY_BLOCK[code] = _now_ts() + seconds


def _get_fast_state(code):
    with FAST_LOCK:
        return FAST_TRADE_STATE.get(code)


def _set_fast_state(code, state):
    with FAST_LOCK:
        FAST_TRADE_STATE[code] = state


def _pop_fast_state(code):
    with FAST_LOCK:
        return FAST_TRADE_STATE.pop(code, None)


def create_s15_shadow_record(code, name):
    if DB is None:
        return None
    try:
        with DB.get_session() as session:
            record = RecommendationHistory(
                rec_date=datetime.now().date(),
                stock_code=code,
                stock_name=name,
                buy_price=0,
                trade_type='SCALP',
                strategy='S15_FAST',
                status='WATCHING',
                position_tag='S15_FAST'
            )
            session.add(record)
            session.flush()
            return record.id
    except Exception as exc:
        log_error(f"🚨 S15 shadow record 생성 실패 ({code}): {exc}")
        return None


def update_s15_shadow_record(shadow_id, **kwargs):
    if DB is None:
        return
    if not shadow_id:
        return
    try:
        with DB.get_session() as session:
            record = session.query(RecommendationHistory).filter_by(id=shadow_id).first()
            if not record:
                return
            for key, value in kwargs.items():
                if hasattr(record, key):
                    setattr(record, key, value)
    except Exception as exc:
        log_error(f"🚨 S15 shadow record 갱신 실패 ({shadow_id}): {exc}")


def _send_s15_limit_buy(code, qty, price):
    return kiwoom_orders.send_buy_order_market(
        code=code,
        qty=qty,
        token=KIWOOM_TOKEN,
        order_type="00",
        price=int(price)
    )


def _send_s15_limit_sell(code, qty, price):
    return kiwoom_orders.send_sell_order_market(
        code=code,
        qty=qty,
        token=KIWOOM_TOKEN,
        order_type="00",
        price=int(price)
    )


def _send_s15_market_sell(code, qty):
    return kiwoom_orders.send_sell_order_market(
        code=code,
        qty=qty,
        token=KIWOOM_TOKEN,
        order_type="3"
    )


def _send_exit_best_ioc(code, qty, token):
    """[공통 긴급 청산 래퍼] 최유리(IOC, 16) 조건으로 즉각 청산 시도"""
    return kiwoom_orders.send_sell_order_market(
        code=code,
        qty=qty,
        token=token,
        order_type="16"
    )


def _extract_ord_no(res):
    if isinstance(res, dict):
        return str(res.get('ord_no', '') or res.get('odno', '') or '')
    return ''


def _is_ok_response(res):
    if isinstance(res, dict):
        return str(res.get('return_code', res.get('rt_cd', ''))) == '0'
    return bool(res)


def _confirm_s15_cancel_or_reload_remaining(code, state, wait_sec=0.5):
    until = _now_ts() + wait_sec
    while _now_ts() < until:
        with state['lock']:
            rem_qty = max(0, state['cum_buy_qty'] - state['cum_sell_qty'])
        if rem_qty == 0:
            return 0
        time.sleep(0.05)
    try:
        inventory, _ = kiwoom_orders.get_my_inventory(KIWOOM_TOKEN)
        real_stock = next((item for item in (inventory or []) if str(item.get('code', '')).strip()[:6] == code), None)
        if real_stock:
            return int(float(real_stock.get('qty', 0) or 0))
    except Exception as exc:
        log_error(f"⚠️ S15 잔량 재조회 실패 ({code}): {exc}")
    with state['lock']:
        return max(0, state['cum_buy_qty'] - state['cum_sell_qty'])


def execute_fast_track_scalp_v2(code, name, trigger_price, ratio=0.10):
    state = _get_fast_state(code)
    if not state:
        return
    try:
        cleanup_allowed = False
        actual_entry_happened = False
        rt_data = WS_MANAGER.get_latest_data(code) if WS_MANAGER else {}
        curr_price = int(float((rt_data or {}).get('curr', 0) or 0))
        if curr_price <= 0:
            curr_price = int(trigger_price or 0)
        if curr_price <= 0:
            state['status'] = 'FAILED'
            update_s15_shadow_record(state.get('shadow_id'), status='EXPIRED')
            return

        if AI_ENGINE is None:
            state['status'] = 'FAILED'
            log_error(f"🚨 S15 AI_ENGINE 미초기화 ({code})")
            update_s15_shadow_record(state.get('shadow_id'), status='EXPIRED')
            return

        ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=10)
        ai_res = AI_ENGINE.analyze_target(
            name,
            rt_data or {'curr': curr_price, 'orderbook': {'asks': [], 'bids': []}},
            ticks,
            recent_candles=[],
            strategy="SCALPING"
        )

        if ai_res.get('action') != 'BUY' or ai_res.get('score', 0) < 80:
            state['status'] = 'FAILED'
            update_s15_shadow_record(state.get('shadow_id'), status='EXPIRED')
            return

        buy_price = _price_ticks_up(curr_price, 2)
        deposit = kiwoom_orders.get_deposit(KIWOOM_TOKEN)
        req_qty = kiwoom_orders.calc_buy_qty(buy_price, deposit, ratio=ratio)
        if req_qty <= 0:
            state['status'] = 'FAILED'
            update_s15_shadow_record(state.get('shadow_id'), status='EXPIRED')
            return

        buy_res = _send_s15_limit_buy(code, req_qty, buy_price)
        if not _is_ok_response(buy_res):
            state['status'] = 'FAILED'
            update_s15_shadow_record(state.get('shadow_id'), status='EXPIRED')
            return

        with state['lock']:
            state['status'] = 'BUY_SENT'
            state['buy_ord_no'] = _extract_ord_no(buy_res)
            state['req_buy_qty'] = req_qty
            state['updated_at'] = _now_ts()
        update_s15_shadow_record(state.get('shadow_id'), status='BUY_ORDERED')

        expire_at = _now_ts() + 20.0
        while _now_ts() < expire_at:
            with state['lock']:
                if state['cum_buy_qty'] >= req_qty:
                    break
            time.sleep(0.1)

        with state['lock']:
            real_buy_qty = state['cum_buy_qty']
            avg_buy_price = state['avg_buy_price']
            buy_ord_no = state.get('buy_ord_no', '')
        if real_buy_qty > 0:
            actual_entry_happened = True

        if real_buy_qty <= 0:
            cleanup_allowed = True
            if buy_ord_no:
                kiwoom_orders.send_cancel_order(code=code, orig_ord_no=buy_ord_no, token=KIWOOM_TOKEN, qty=0)
            state['status'] = 'CANCELLED'
            update_s15_shadow_record(state.get('shadow_id'), status='EXPIRED')
            return

        if real_buy_qty < req_qty and buy_ord_no:
            kiwoom_orders.send_cancel_order(code=code, orig_ord_no=buy_ord_no, token=KIWOOM_TOKEN, qty=0)

        if avg_buy_price <= 0:
            avg_buy_price = buy_price

        target_price = _target_price_pct_up(avg_buy_price, 1.8)
        stop_price = int(avg_buy_price * (1 - 0.007))

        with state['lock']:
            state['status'] = 'HOLDING'
            state['target_price'] = target_price
            state['stop_price'] = stop_price
            state['updated_at'] = _now_ts()
        update_s15_shadow_record(
            state.get('shadow_id'),
            status='HOLDING',
            buy_price=avg_buy_price,
            buy_qty=real_buy_qty
        )

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

        with state['lock']:
            state['sell_ord_no'] = _extract_ord_no(sell_res)
            state['status'] = 'EXIT_SENT'
            state['updated_at'] = _now_ts()

        while True:
            time.sleep(0.1)

            with state['lock']:
                if state['cum_sell_qty'] >= state['cum_buy_qty'] > 0:
                    state['status'] = 'DONE'
                    cleanup_allowed = True
                    break

            rt = WS_MANAGER.get_latest_data(code) if WS_MANAGER else {}
            curr_p = int(float((rt or {}).get('curr', 0) or 0))
            if curr_p <= 0 or avg_buy_price <= 0:
                continue

            profit_rate = ((curr_p - avg_buy_price) / avg_buy_price) * 100
            if profit_rate <= -0.7:
                with state['lock']:
                    sell_ord_no = state.get('sell_ord_no', '')

                if sell_ord_no:
                    cancel_res = kiwoom_orders.send_cancel_order(
                        code=code, orig_ord_no=sell_ord_no, token=KIWOOM_TOKEN, qty=0
                    )
                    if _is_ok_response(cancel_res):
                        with state['lock']:
                            state['pending_cancel_ord_no'] = sell_ord_no

                rem_qty = _confirm_s15_cancel_or_reload_remaining(code, state, wait_sec=0.5)
                if rem_qty > 0:
                    market_res = _send_exit_best_ioc(code, rem_qty, KIWOOM_TOKEN)
                    if _is_ok_response(market_res):
                        with state['lock']:
                            state['sell_ord_no'] = _extract_ord_no(market_res) or state.get('sell_ord_no', '')
                            state['updated_at'] = _now_ts()
                break

        with state['lock']:
            final_buy = state['avg_buy_price']
            final_sell = state['avg_sell_price']
            final_qty = state['cum_buy_qty']

        final_profit_rate = 0.0
        if final_buy > 0 and final_sell > 0:
            final_profit_rate = round(((final_sell - final_buy) / final_buy) * 100, 2)

        update_s15_shadow_record(
            state.get('shadow_id'),
            status='COMPLETED',
            sell_price=final_sell or state.get('target_price', 0),
            sell_time=datetime.now(),
            profit_rate=final_profit_rate,
            buy_price=final_buy,
            buy_qty=final_qty
        )
    except Exception as exc:
        log_error(f"🚨 S15 Fast-Track 에러 ({code}): {exc}")
        update_s15_shadow_record(state.get('shadow_id'), status='EXPIRED')
    finally:
        if actual_entry_happened:
            _block_s15_reentry(code)
        _unarm_s15_candidate(code)
        if cleanup_allowed:
            _pop_fast_state(code)
