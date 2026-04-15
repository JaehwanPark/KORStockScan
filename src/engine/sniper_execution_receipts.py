"""Order execution receipt handlers for the sniper engine."""

import threading
import time
from datetime import datetime

from src.database.models import RecommendationHistory
from src.engine.sniper_entry_state import (
    ENTRY_LOCK,
    get_terminal_entry_order,
    move_orders_to_terminal,
)
from src.engine.sniper_scale_in_utils import record_add_history_event
from src.engine.sniper_position_tags import (
    default_position_tag_for_strategy,
    is_default_position_tag,
    normalize_position_tag,
    normalize_strategy,
)
from src.engine.trade_profit import calculate_net_profit_rate
from src.utils.constants import TRADING_RULES
from src.utils import kiwoom_utils
from src.utils.logger import log_error, log_info
from src.utils.pipeline_event_logger import emit_pipeline_event
from src.engine.sniper_time import TIME_15_30
from src.engine.sniper_post_sell_feedback import record_post_sell_candidate


KIWOOM_TOKEN = None
DB = None
event_bus = None
ACTIVE_TARGETS = None
highest_prices = None
_get_fast_state = None
_weighted_avg = None
_now_ts = None
RECEIPT_LOCK = ENTRY_LOCK


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
    state_machine=None,
    **_unused_kwargs,
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


def _log_holding_pipeline(name, code, target_id, stage, **fields):
    emit_pipeline_event(
        "HOLDING_PIPELINE",
        name,
        code,
        stage,
        record_id=target_id,
        fields=fields,
    )


# ==========================================
def _find_execution_target(code, exec_type, order_no):
    normalized_order_no = str(order_no or '').strip()

    if exec_type == 'BUY':
        if normalized_order_no:
            bundle_match = next(
                (
                    stock for stock in ACTIVE_TARGETS
                    if str(stock.get('code', '')).strip()[:6] == code
                    and any(
                        str(order.get('ord_no', '') or '').strip() == normalized_order_no
                        for order in (stock.get('pending_entry_orders') or [])
                    )
                ),
                None,
            )
            if bundle_match:
                return bundle_match

            terminal_match = get_terminal_entry_order(normalized_order_no)
            if terminal_match:
                stock_code = str(terminal_match.get('stock_code', '') or '').strip()[:6]
                target = next(
                    (
                        stock for stock in ACTIVE_TARGETS
                        if str(stock.get('code', '')).strip()[:6] == stock_code
                    ),
                    None,
                )
                if target:
                    return target

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

        # HOLDING 상태의 추가매수 주문 매칭
        if exec_type == 'BUY':
            add_match = next(
                (
                    stock for stock in ACTIVE_TARGETS
                    if str(stock.get('code', '')).strip()[:6] == code
                    and bool(stock.get('pending_add_order'))
                    and str(stock.get('pending_add_ord_no', '')).strip() == normalized_order_no
                ),
                None
            )
            if add_match:
                return add_match

    if exec_type == 'BUY':
        pending_add_candidates = [
            stock for stock in ACTIVE_TARGETS
            if str(stock.get('code', '')).strip()[:6] == code
            and bool(stock.get('pending_add_order'))
            and stock.get('status') == 'HOLDING'
        ]
        if len(pending_add_candidates) == 1:
            return pending_add_candidates[0]

    if len(status_candidates) == 1:
        return status_candidates[0]

    return None


def _find_order_notice_target(code, exec_type, order_no):
    target = _find_execution_target(code, exec_type, order_no)
    if target:
        return target

    status_key = 'BUY_ORDERED' if exec_type == 'BUY' else 'SELL_ORDERED'
    status_candidates = [
        stock for stock in ACTIVE_TARGETS
        if str(stock.get('code', '')).strip()[:6] == code and stock.get('status') == status_key
    ]
    if len(status_candidates) == 1:
        return status_candidates[0]
    return None


def _apply_order_notice_to_target(target_stock, *, code, exec_type, order_no, status):
    changed = False

    if exec_type == 'BUY':
        pending_orders = target_stock.get('pending_entry_orders') or []
        exact_match = None
        blank_match = None

        for order in pending_orders:
            existing_ord_no = str(order.get('ord_no', '') or '').strip()
            if existing_ord_no == order_no:
                exact_match = order
                break
            if not existing_ord_no and blank_match is None:
                blank_match = order

        target_order = exact_match or blank_match
        if target_order:
            if not str(target_order.get('ord_no', '') or '').strip():
                target_order['ord_no'] = order_no
                changed = True
            target_order['notice_status'] = status
            target_order['notice_at'] = time.time()
            changed = True

        if order_no and not str(target_stock.get('odno', '') or '').strip():
            target_stock['odno'] = order_no
            changed = True

    elif exec_type == 'SELL':
        if order_no and not str(target_stock.get('sell_odno', '') or '').strip():
            target_stock['sell_odno'] = order_no
            changed = True

    if changed:
        log_info(
            f"[ORDER_NOTICE_BOUND] {target_stock.get('name')}({code}) "
            f"type={exec_type} status={status} order_no={order_no}"
        )


def handle_order_notice(notice_data):
    code = str(notice_data.get('code', '') or '').strip()[:6]
    exec_type = str(notice_data.get('type', '') or '').upper()
    order_no = str(notice_data.get('order_no', '') or '').strip()
    status = str(notice_data.get('status', '') or '').strip()

    if not code or not exec_type or not order_no:
        return

    with RECEIPT_LOCK:
        target_stock = _find_order_notice_target(code, exec_type, order_no)
        if not target_stock:
            return
        _apply_order_notice_to_target(
            target_stock,
            code=code,
            exec_type=exec_type,
            order_no=order_no,
            status=status,
        )


def weighted_avg_price(old_price, old_qty, exec_price, exec_qty):
    total_qty = old_qty + exec_qty
    if total_qty <= 0:
        return exec_price
    return round(((old_price * old_qty) + (exec_price * exec_qty)) / total_qty, 4)


def _clear_pending_add_meta(target_stock):
    for key in [
        'pending_add_order',
        'pending_add_type',
        'pending_add_qty',
        'pending_add_ord_no',
        'pending_add_requested_at',
        'pending_add_counted',
        'pending_add_filled_qty',
        'add_order_time',
        'add_odno',
    ]:
        target_stock.pop(key, None)


def _apply_scale_in_protection(target_stock, add_type):
    """추가매수 체결 후 보호선 보정(1차 단순 버전)."""
    try:
        raw_strategy = (target_stock.get('strategy') or 'KOSPI_ML').upper()
        strategy = 'SCALPING' if raw_strategy in ['SCALPING', 'SCALP'] else raw_strategy
        avg_price = float(target_stock.get('buy_price') or 0)
        if avg_price <= 0:
            return False

        if add_type == 'PYRAMID':
            if strategy == 'SCALPING':
                protect_price = avg_price * 1.003
            else:
                protect_price = avg_price * 1.01

            existing = float(target_stock.get('trailing_stop_price') or 0)
            target_stock['trailing_stop_price'] = max(existing, protect_price)
        elif add_type == 'AVG_DOWN':
            # 1차: 기존 손절선 유지(필요 시 완화 가능)
            pass
        return True
    except Exception as e:
        log_error(f"⚠️ [ADD_PROTECT] 보호선 보정 실패: {e}")
        return False


def _is_ok_response(res):
    if not isinstance(res, dict):
        return bool(res)
    return str(res.get('return_code', res.get('rt_cd', ''))) == '0'


def _refresh_scalp_preset_exit_order(target_stock, code, total_qty):
    """
    스캘핑 보유 수량이 바뀌면 preset TP 주문을 새 수량 기준으로 다시 맞춥니다.
    """
    from src.engine import kiwoom_orders

    preset_ord_no = str(target_stock.get('preset_tp_ord_no', '') or '').strip()
    preset_tp_price = int(target_stock.get('preset_tp_price') or 0)

    if preset_ord_no:
        cancel_res = kiwoom_orders.send_cancel_order(code=code, orig_ord_no=preset_ord_no, token=KIWOOM_TOKEN, qty=0)
        if not _is_ok_response(cancel_res):
            log_error(
                f"⚠️ [ADD_PROTECT] {target_stock.get('name')}({code}) 기존 preset TP 취소 실패. "
                "added shares may remain partially unprotected."
            )
            return False

    if preset_tp_price <= 0 or total_qty <= 0:
        if total_qty <= 0:
            target_stock['preset_tp_qty'] = 0
        return True

    sell_res = kiwoom_orders.send_sell_order_market(
        code=code,
        qty=total_qty,
        token=KIWOOM_TOKEN,
        order_type="00",
        price=preset_tp_price,
    )
    new_ord_no = sell_res.get('ord_no') if isinstance(sell_res, dict) else ''
    target_stock['preset_tp_ord_no'] = new_ord_no
    target_stock['preset_tp_qty'] = int(total_qty or 0)
    if not new_ord_no:
        log_error(
            f"⚠️ [ADD_PROTECT] {target_stock.get('name')}({code}) refreshed preset TP order number missing."
        )
        return False
    log_info(
        f"[ENTRY_TP_REFRESH] {target_stock.get('name')}({code}) qty={total_qty} "
        f"tp_price={preset_tp_price} ord_no={new_ord_no}"
    )
    return True


def _update_db_for_buy(target_id, exec_price, now, target_stock):
    """비동기로 실행되는 BUY 체결 DB 업데이트 및 알림"""
    try:
        buy_qty = int(target_stock.get('buy_qty') or 0)
        avg_buy_price = float(target_stock.get('buy_price') or exec_price or 0)
        with DB.get_session() as session:
            session.query(RecommendationHistory).filter_by(id=target_id).update({
                "buy_price": avg_buy_price,
                "buy_qty": buy_qty,
                "status": "HOLDING",
                "buy_time": now
            })

        print(f"✅ [영수증: ID {target_id}] {target_stock.get('code')} 실제 매수 체결 반영 완료! avg={avg_buy_price:,} qty={buy_qty}")

        if not target_stock.get('buy_execution_notified'):
            pending_msg = target_stock.get('pending_buy_msg')
            audience = target_stock.get('msg_audience', 'ADMIN_ONLY')
            if pending_msg:
                final_msg = pending_msg.replace("그물망 투척!", "그물망 매수 체결!").replace("스나이퍼 포착!", "스나이퍼 매수 체결!")
                final_msg += f"\n✅ **평균 체결가:** `{avg_buy_price:,.0f}원` / **체결수량:** `{buy_qty}주`"
                event_bus.publish('TELEGRAM_BROADCAST', {'message': final_msg, 'audience': audience, 'parse_mode': 'Markdown'})
            else:
                event_bus.publish(
                    'TELEGRAM_BROADCAST',
                    {
                        'message': f"🛒 **[{target_stock.get('name')}]** 매수 체결 완료!\n평균 체결가: `{avg_buy_price:,.0f}원`\n체결수량: `{buy_qty}주`",
                        'audience': audience,
                        'parse_mode': 'Markdown',
                    }
                )
            target_stock['buy_execution_notified'] = True
            target_stock.pop('pending_buy_msg', None)
    except Exception as e:
        log_error(f"🚨 [DB 에러] ID {target_id} BUY 처리 중 에러: {e}")


def _update_db_for_add(target_id, exec_price, exec_qty, now, target_stock, add_type, count_increment):
    """비동기로 실행되는 추가매수 체결 DB 업데이트"""
    try:
        add_count_after = int(target_stock.get('add_count') or 0)
        with DB.get_session() as session:
            record = session.query(RecommendationHistory).filter_by(id=target_id).first()
            if not record:
                return

            old_price = float(record.buy_price) if record.buy_price is not None else 0.0
            old_qty = int(record.buy_qty or 0)
            new_avg = float(target_stock.get('buy_price') or exec_price or 0)
            new_qty = int(target_stock.get('buy_qty') or 0)

            record.buy_price = new_avg
            record.buy_qty = new_qty
            record.add_count = int(target_stock.get('add_count', record.add_count or 0) or 0)
            record.avg_down_count = int(target_stock.get('avg_down_count', record.avg_down_count or 0) or 0)
            record.pyramid_count = int(target_stock.get('pyramid_count', record.pyramid_count or 0) or 0)
            record.last_add_type = add_type
            record.last_add_at = now
            record.scale_in_locked = bool(target_stock.get('scale_in_locked', False))
            add_count_after = int(record.add_count or 0)

            # 보호선 보정값을 DB에도 반영 (있을 때만)
            if target_stock.get('trailing_stop_price') is not None:
                record.trailing_stop_price = float(target_stock.get('trailing_stop_price') or 0)
            if target_stock.get('hard_stop_price') is not None:
                record.hard_stop_price = float(target_stock.get('hard_stop_price') or 0)

        print(
            f"✅ [영수증: ID {target_id}] {target_stock.get('code')} 추가매수 체결 반영 "
            f"(avg={new_avg}, qty={new_qty}, type={add_type})"
        )

        if event_bus and count_increment:
            msg = (
                f"[ADD_EXECUTED] {target_stock.get('name')}({target_stock.get('code')})\n"
                f"strategy={target_stock.get('strategy')}\n"
                f"type={add_type}\n"
                f"old_avg={old_price:.2f} exec={exec_price:,}\n"
                f"new_avg={new_avg:.2f} total_qty={new_qty}\n"
                f"add_count={add_count_after}"
            )
            event_bus.publish('TELEGRAM_BROADCAST', {
                'message': msg,
                'audience': target_stock.get('msg_audience', 'ADMIN_ONLY'),
                'parse_mode': 'Markdown'
            })
    except Exception as e:
        log_error(f"🚨 [DB 에러] ID {target_id} ADD 처리 중 에러: {e}")


def _update_db_for_sell(target_id, exec_price, now, target_stock, strategy, is_scalp_revive):
    """비동기로 실행되는 SELL 체결 DB 업데이트 및 알림 (스캘핑 부활 제외)"""
    try:
        with DB.get_session() as session:
            record = session.query(RecommendationHistory).filter_by(id=target_id).first()
            if not record:
                return

            safe_buy_price = float(record.buy_price) if record.buy_price is not None else 0.0
            if safe_buy_price > 0:
                profit_rate = calculate_net_profit_rate(safe_buy_price, exec_price)
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
            _log_holding_pipeline(
                target_stock.get('name'),
                str(target_stock.get('code', '')).strip()[:6],
                target_id,
                'sell_completed',
                sell_price=int(exec_price or 0),
                profit_rate=f"{profit_rate:+.2f}",
                exit_rule=target_stock.get('last_exit_rule') or '-',
                revive=bool(is_scalp_revive),
                strategy=strategy,
            )
            try:
                record_post_sell_candidate(
                    recommendation_id=target_id,
                    stock=target_stock,
                    code=str(target_stock.get('code', '')).strip()[:6],
                    sell_time=now,
                    buy_price=safe_buy_price,
                    sell_price=exec_price,
                    profit_rate=profit_rate,
                    buy_qty=int(float(getattr(record, 'buy_qty', 0) or target_stock.get('buy_qty', 0) or 0)),
                    exit_rule=target_stock.get('last_exit_rule') or '-',
                    strategy=strategy,
                    revive=bool(is_scalp_revive),
                )
            except Exception as exc:
                log_error(f"[POST_SELL] candidate record failed (id={target_id}): {exc}")
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

    with RECEIPT_LOCK:
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
            pending_add = bool(target_stock.get('pending_add_order'))
            pending_ord_no = str(target_stock.get('pending_add_ord_no', '') or '').strip()
            is_add_fill = pending_add and (not order_no or order_no == pending_ord_no)

            if is_add_fill:
                add_type = (target_stock.get('pending_add_type') or '').upper()
                old_price = float(target_stock.get('buy_price') or 0)
                old_qty = int(target_stock.get('buy_qty') or 0)
                request_qty = int(target_stock.get('pending_add_qty', 0) or 0)
                history_order_no = pending_ord_no or order_no
                new_qty = old_qty + exec_qty
                new_avg = weighted_avg_price(old_price, old_qty, exec_price, exec_qty)

                target_stock['status'] = 'HOLDING'
                target_stock['buy_price'] = new_avg
                target_stock['buy_qty'] = new_qty
                target_stock['last_add_type'] = add_type
                target_stock['last_add_at'] = now
                target_stock['last_add_time'] = time.time()
                if not target_stock.get('holding_started_at'):
                    target_stock['holding_started_at'] = now
                highest_prices[code] = max(highest_prices.get(code, 0), exec_price)

                count_increment = False
                if not target_stock.get('pending_add_counted'):
                    target_stock['add_count'] = int(target_stock.get('add_count', 0) or 0) + 1
                    if add_type == 'AVG_DOWN':
                        target_stock['avg_down_count'] = int(target_stock.get('avg_down_count', 0) or 0) + 1
                    elif add_type == 'PYRAMID':
                        target_stock['pyramid_count'] = int(target_stock.get('pyramid_count', 0) or 0) + 1
                    target_stock['pending_add_counted'] = True
                    count_increment = True

                filled = int(target_stock.get('pending_add_filled_qty', 0) or 0) + exec_qty
                target_stock['pending_add_filled_qty'] = filled
                pending_qty = int(target_stock.get('pending_add_qty', 0) or 0)

                protection_ok = _apply_scale_in_protection(target_stock, add_type)
                strategy = normalize_strategy(target_stock.get('strategy'))
                pos_tag = normalize_position_tag(strategy, target_stock.get('position_tag'))
                if strategy == 'SCALPING' and is_default_position_tag(strategy, pos_tag):
                    base_buy_price = int(target_stock.get('buy_price') or exec_price or 0)
                    target_stock['preset_tp_price'] = kiwoom_utils.get_target_price_up(base_buy_price, 1.5)
                    protection_ok = _refresh_scalp_preset_exit_order(target_stock, code, new_qty) and protection_ok

                if not protection_ok:
                    target_stock['scale_in_locked'] = True
                    log_error(
                        f"⚠️ [ADD_PROTECT] {target_stock.get('name')}({code}) 보호선 재설정 실패로 "
                        "scale_in_locked=True"
                    )

                _update_db_for_add(
                    target_id,
                    exec_price,
                    exec_qty,
                    now,
                    target_stock,
                    add_type,
                    count_increment,
                )
                record_add_history_event(
                    DB,
                    recommendation_id=target_id,
                    stock_code=code,
                    stock_name=target_stock.get('name'),
                    strategy=target_stock.get('strategy'),
                    add_type=add_type,
                    event_type='EXECUTED',
                    order_no=history_order_no,
                    request_qty=request_qty or pending_qty or exec_qty,
                    executed_qty=exec_qty,
                    executed_price=exec_price,
                    prev_buy_price=old_price,
                    new_buy_price=new_avg,
                    prev_buy_qty=old_qty,
                    new_buy_qty=new_qty,
                    add_count_after=target_stock.get('add_count', 0),
                    reason='receipt_confirmed',
                )
                if pending_qty > 0 and filled >= pending_qty:
                    _clear_pending_add_meta(target_stock)
                log_info(
                    "[ADD_EXECUTED] "
                    f"{target_stock.get('name')}({code}) "
                    f"type={add_type} exec={exec_price:,} "
                    f"new_avg={new_avg} new_qty={new_qty} add_count={target_stock.get('add_count')}"
                )
                _log_holding_pipeline(
                    target_stock.get('name'),
                    code,
                    target_id,
                    'scale_in_executed',
                    add_type=add_type,
                    fill_price=int(exec_price or 0),
                    fill_qty=int(exec_qty or 0),
                    new_avg_price=f"{float(new_avg or 0):.2f}",
                    new_buy_qty=int(new_qty or 0),
                    add_count=int(target_stock.get('add_count', 0) or 0),
                )
            else:
                # 신규 진입 체결: 단일 주문/복수 fallback 주문 공통 누적 처리
                old_qty = int(target_stock.get('buy_qty') or 0)
                old_price = float(target_stock.get('buy_price') or 0)
                new_qty = old_qty + exec_qty
                new_avg = weighted_avg_price(old_price, old_qty, exec_price, exec_qty) if old_qty > 0 else exec_price
                entry_mode = str(target_stock.get('entry_mode', 'normal') or 'normal')

                pending_entry_orders = target_stock.get('pending_entry_orders') or []
                if pending_entry_orders and order_no:
                    for pending_order in pending_entry_orders:
                        if str(pending_order.get('ord_no', '') or '').strip() != order_no:
                            continue
                        pending_order['filled_qty'] = int(pending_order.get('filled_qty', 0) or 0) + exec_qty
                        requested_qty = int(pending_order.get('qty', 0) or 0)
                        if requested_qty > 0 and pending_order['filled_qty'] >= requested_qty:
                            pending_order['status'] = 'FILLED'
                        else:
                            pending_order['status'] = 'PARTIAL'
                        pending_order['last_fill_price'] = exec_price
                        pending_order['last_fill_at'] = time.time()
                        log_info(
                            f"[ENTRY_FILL] {target_stock.get('name')}({code}) "
                            f"tag={pending_order.get('tag')} ord_no={order_no} "
                            f"fill_qty={exec_qty} filled={pending_order.get('filled_qty')}/{requested_qty} "
                            f"fill_price={exec_price}"
                        )
                        break

                target_stock['status'] = 'HOLDING'
                target_stock['buy_price'] = new_avg
                target_stock['buy_qty'] = new_qty
                target_stock['entry_filled_qty'] = int(target_stock.get('entry_filled_qty', 0) or 0) + exec_qty
                target_stock['entry_fill_amount'] = int(target_stock.get('entry_fill_amount', 0) or 0) + (exec_price * exec_qty)
                target_stock['buy_time'] = now
                if not target_stock.get('holding_started_at'):
                    target_stock['holding_started_at'] = now
                highest_prices[code] = max(highest_prices.get(code, 0), exec_price)

                requested_entry_qty = int(target_stock.get('entry_requested_qty', target_stock.get('requested_buy_qty', 0)) or 0)
                cum_filled_qty = int(target_stock.get('entry_filled_qty', 0) or 0)
                remaining_qty = max(0, requested_entry_qty - cum_filled_qty) if requested_entry_qty > 0 else 0
                fill_quality = (
                    "FULL_FILL"
                    if requested_entry_qty > 0 and cum_filled_qty >= requested_entry_qty
                    else ("PARTIAL_FILL" if requested_entry_qty > 0 else "UNKNOWN")
                )
                target_stock['entry_fill_quality'] = fill_quality

                preset_tp_price = int(target_stock.get('preset_tp_price') or 0)
                preset_tp_ord_no_before = str(target_stock.get('preset_tp_ord_no', '') or '').strip()
                preset_tp_ord_no_after = preset_tp_ord_no_before
                preset_sync_status = "NOT_APPLICABLE"
                preset_sync_reason = "non_scalping_or_non_default_tag"
                if requested_entry_qty > 0 and new_qty >= requested_entry_qty:
                    log_info(
                        f"[ENTRY_BUNDLE_FILLED] {target_stock.get('name')}({code}) "
                        f"mode={target_stock.get('entry_mode', 'normal')} "
                        f"filled_qty={new_qty}/{requested_entry_qty} avg_buy={new_avg}"
                    )
                    move_orders_to_terminal(target_stock, reason='entry_bundle_filled')
                    target_stock.pop('pending_entry_orders', None)
                    target_stock.pop('entry_requested_qty', None)
                    target_stock.pop('requested_buy_qty', None)
                    target_stock.pop('entry_filled_qty', None)
                    target_stock.pop('entry_fill_amount', None)
                    target_stock.pop('entry_bundle_id', None)

                strategy = normalize_strategy(target_stock.get('strategy'))
                pos_tag = normalize_position_tag(strategy, target_stock.get('position_tag'))
                target_stock['position_tag'] = pos_tag

                if strategy == 'SCALPING' and is_default_position_tag(strategy, pos_tag):
                    target_stock['exit_mode'] = 'SCALP_PRESET_TP'

                    # 가능한 경우 누적 buy_qty / buy_price 기준 사용, 불가하면 exec_price 폴백
                    base_buy_price = int(target_stock.get('buy_price') or exec_price or 0)
                    if base_buy_price <= 0:
                        base_buy_price = exec_price

                    preset_tp_price = kiwoom_utils.get_target_price_up(base_buy_price, 1.5)
                    target_stock['preset_tp_price'] = preset_tp_price
                    preset_tp_ord_no_before = str(target_stock.get('preset_tp_ord_no', '') or '').strip()
                    preset_hard_stop_pct = float(getattr(TRADING_RULES, 'SCALP_PRESET_HARD_STOP_PCT', -0.7) or -0.7)
                    preset_hard_stop_grace_sec = int(getattr(TRADING_RULES, 'SCALP_PRESET_HARD_STOP_GRACE_SEC', 0) or 0)
                    preset_hard_stop_emergency_pct = float(
                        getattr(
                            TRADING_RULES,
                            'SCALP_PRESET_HARD_STOP_EMERGENCY_PCT',
                            min(preset_hard_stop_pct - 0.5, -1.2),
                        )
                        or min(preset_hard_stop_pct - 0.5, -1.2)
                    )
                    if str(target_stock.get('entry_mode', '')).strip().lower() == 'fallback':
                        preset_hard_stop_pct = float(
                            getattr(
                                TRADING_RULES,
                                'SCALP_PRESET_HARD_STOP_FALLBACK_BASE_PCT',
                                preset_hard_stop_pct,
                            )
                            or preset_hard_stop_pct
                        )
                        preset_hard_stop_grace_sec = int(
                            getattr(
                                TRADING_RULES,
                                'SCALP_PRESET_HARD_STOP_FALLBACK_BASE_GRACE_SEC',
                                preset_hard_stop_grace_sec,
                            )
                            or preset_hard_stop_grace_sec
                        )
                        preset_hard_stop_emergency_pct = float(
                            getattr(
                                TRADING_RULES,
                                'SCALP_PRESET_HARD_STOP_FALLBACK_BASE_EMERGENCY_PCT',
                                preset_hard_stop_emergency_pct,
                            )
                            or preset_hard_stop_emergency_pct
                        )
                    target_stock['hard_stop_pct'] = preset_hard_stop_pct
                    target_stock['hard_stop_grace_sec'] = preset_hard_stop_grace_sec
                    target_stock['hard_stop_emergency_pct'] = preset_hard_stop_emergency_pct
                    target_stock['protect_profit_pct'] = None
                    target_stock['ai_review_done'] = False
                    target_stock['ai_review_score'] = None
                    target_stock['ai_review_action'] = None
                    target_stock['ai_low_score_loss_hits'] = 0
                    target_stock['last_ai_reviewed_at'] = None
                    target_stock['exit_requested'] = False
                    target_stock['exit_order_type'] = None
                    target_stock['exit_order_time'] = None

                    sell_qty = int(target_stock.get('buy_qty') or exec_qty or 0)
                    refreshed = _refresh_scalp_preset_exit_order(target_stock, code, sell_qty)
                    preset_tp_ord_no_after = str(target_stock.get('preset_tp_ord_no', '') or '').strip()
                    preset_tp_qty = int(target_stock.get('preset_tp_qty', 0) or 0)

                    if not refreshed:
                        preset_sync_status = "REFRESH_FAILED"
                        preset_sync_reason = "refresh_failed"
                    elif not preset_tp_ord_no_after:
                        preset_sync_status = "MISSING_ORD_NO"
                        preset_sync_reason = "missing_ord_no"
                    elif preset_tp_qty != sell_qty:
                        preset_sync_status = "QTY_MISMATCH"
                        preset_sync_reason = f"preset_tp_qty={preset_tp_qty},sell_qty={sell_qty}"
                    else:
                        preset_sync_status = "OK"
                        preset_sync_reason = "-"

                    # 지정가 주문 실패 시에도 출구 엔진 자체는 유지
                    if not refreshed or not target_stock.get('preset_tp_ord_no'):
                        print(f"⚠️ [SCALP 출구엔진] {target_stock.get('name')} 지정가 매도 주문번호 미수신. 보유 감시로 보강 필요.")
                    else:
                        print(
                            f"🎯 [SCALP 출구엔진 셋업] {target_stock.get('name')} "
                            f"+1.5% 지정가({preset_tp_price:,}원) {sell_qty}주 매도망 전개 완료."
                        )
                        _log_holding_pipeline(
                            target_stock.get('name'),
                            code,
                            target_id,
                            'preset_exit_setup',
                            preset_tp_price=int(preset_tp_price or 0),
                            qty=int(sell_qty or 0),
                            ord_no=str(target_stock.get('preset_tp_ord_no', '') or '-'),
                        )
                _log_holding_pipeline(
                    target_stock.get('name'),
                    code,
                    target_id,
                    'position_rebased_after_fill',
                    fill_qty=int(exec_qty or 0),
                    cum_filled_qty=int(cum_filled_qty or 0),
                    requested_qty=int(requested_entry_qty or 0),
                    remaining_qty=int(remaining_qty or 0),
                    avg_buy_price=f"{float(new_avg or 0):.2f}",
                    entry_mode=entry_mode,
                    fill_quality=fill_quality,
                    preset_tp_price=int(preset_tp_price or 0),
                    preset_tp_ord_no_before=preset_tp_ord_no_before or "-",
                    preset_tp_ord_no_after=preset_tp_ord_no_after or "-",
                    sync_status=preset_sync_status,
                )
                if strategy == 'SCALPING' and is_default_position_tag(strategy, pos_tag):
                    sync_stage = 'preset_exit_sync_ok' if preset_sync_status == "OK" else 'preset_exit_sync_mismatch'
                    _log_holding_pipeline(
                        target_stock.get('name'),
                        code,
                        target_id,
                        sync_stage,
                        entry_mode=entry_mode,
                        fill_quality=fill_quality,
                        requested_qty=int(requested_entry_qty or 0),
                        buy_qty=int(new_qty or 0),
                        preset_tp_qty=int(target_stock.get('preset_tp_qty', 0) or 0),
                        preset_tp_price=int(preset_tp_price or 0),
                        preset_tp_ord_no_before=preset_tp_ord_no_before or "-",
                        preset_tp_ord_no_after=preset_tp_ord_no_after or "-",
                        sync_status=preset_sync_status,
                        sync_reason=preset_sync_reason,
                    )

                _log_holding_pipeline(
                    target_stock.get('name'),
                    code,
                    target_id,
                    'holding_started',
                    strategy=target_stock.get('strategy'),
                    position_tag=target_stock.get('position_tag'),
                    buy_price=f"{float(new_avg or 0):.2f}",
                    buy_qty=int(new_qty or 0),
                    fill_price=int(exec_price or 0),
                    fill_qty=int(exec_qty or 0),
                    entry_mode=entry_mode,
                )

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
                        profit_rate = calculate_net_profit_rate(safe_buy_price, exec_price)
                    else:
                        profit_rate = 0.0
                        print(f"⚠️ [수익률 계산 불가] ID {target_id}의 매수가(buy_price)가 누락되어 수익률을 0%로 처리합니다.")
                    strategy = normalize_strategy(record.strategy or target_stock.get('strategy') or 'KOSPI_ML')
                    # ✅ 일관성 통일: 15:30 이전까지만 스캘핑 부활
                    is_scalp_revive = (strategy == 'SCALPING') and (now_t < TIME_15_30)
            except Exception as e:
                log_error(f"🚨 [DB 조회 에러] ID {target_id} SELL 처리 중 에러: {e}")
                return

            if is_scalp_revive:
            # 스캘핑 부활: 동기 DB 업데이트 (새 레코드 삽입 필요)
                revived_position_tag = normalize_position_tag(
                    'SCALPING',
                    target_stock.get('position_tag') or default_position_tag_for_strategy('SCALPING'),
                )
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
                            position_tag=revived_position_tag,
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
                        _log_holding_pipeline(
                            target_stock.get('name'),
                            code,
                            target_id,
                            'sell_completed',
                            sell_price=int(exec_price or 0),
                            profit_rate=f"{profit_rate:+.2f}",
                            exit_rule=target_stock.get('last_exit_rule') or '-',
                            revive=True,
                            new_watch_id=int(new_watch_id or 0),
                        )
                        try:
                            record_post_sell_candidate(
                                recommendation_id=target_id,
                                stock=target_stock,
                                code=code,
                                sell_time=now,
                                buy_price=safe_buy_price,
                                sell_price=exec_price,
                                profit_rate=profit_rate,
                                buy_qty=int(float(getattr(record, 'buy_qty', 0) or target_stock.get('buy_qty', 0) or 0)),
                                exit_rule=target_stock.get('last_exit_rule') or '-',
                                strategy=strategy,
                                revive=True,
                            )
                        except Exception as exc:
                            log_error(f"[POST_SELL] candidate record failed (id={target_id}): {exc}")
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
                target_stock['position_tag'] = revived_position_tag
                move_orders_to_terminal(target_stock, reason='sell_revive_cleanup')
                for key in [
                    'odno', 'order_time', 'order_price', 'buy_time',
                    'target_buy_price', 'pending_buy_msg',
                    'pending_sell_msg', 'sell_odno', 'sell_order_time',
                    'sell_target_price', 'pending_entry_orders', 'entry_mode',
                    'entry_requested_qty', 'entry_filled_qty', 'entry_fill_amount',
                    'entry_bundle_id', 'requested_buy_qty', 'buy_execution_notified'
                ]:
                    target_stock.pop(key, None)
            else:
            # 일반 SELL: 먼저 메모리 업데이트
                highest_prices.pop(code, None)
                target_stock['status'] = 'COMPLETED'
                target_stock['sell_time'] = now.strftime('%H:%M:%S')
                move_orders_to_terminal(target_stock, reason='sell_completed_cleanup')
                for key in [
                    'pending_entry_orders', 'entry_mode', 'entry_requested_qty',
                    'entry_filled_qty', 'entry_fill_amount', 'entry_bundle_id', 'requested_buy_qty',
                    'buy_execution_notified'
                ]:
                    target_stock.pop(key, None)
                # pending_sell_msg는 백그라운드에서 제거
                # 백그라운드 DB 업데이트 실행
                threading.Thread(
                    target=_update_db_for_sell,
                    args=(target_id, exec_price, now, target_stock, strategy, is_scalp_revive),
                    daemon=True
                ).start()

    # 메모리 업데이트는 각 조건문 내에서 이미 수행됨
