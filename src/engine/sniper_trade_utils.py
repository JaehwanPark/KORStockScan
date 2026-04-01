"""Shared trading utilities for the sniper engine."""

import time

from src.engine import kiwoom_orders


def send_market_exit_now(code, qty, token):
    """정규장 중 즉시 시장가 청산용 공통 래퍼"""
    return kiwoom_orders.send_sell_order_market(
        code=code,
        qty=qty,
        token=token,
        order_type="3",
    )


def send_exit_best_ioc(code, qty, token):
    """[공통 긴급 청산 래퍼] 최유리(IOC, 16) 조건으로 즉각 청산 시도"""
    return kiwoom_orders.send_sell_order_market(
        code=code,
        qty=qty,
        token=token,
        order_type="16",
    )


def confirm_cancel_or_reload_remaining(code, orig_ord_no, token, expected_qty):
    """
    [공통 유틸] 주문 취소 후 실제 계좌 잔고를 재조회하여 팔아야 할 정확한 잔량(rem_qty) 반환
    """
    if orig_ord_no:
        kiwoom_orders.send_cancel_order(code=code, orig_ord_no=orig_ord_no, token=token, qty=0)
        time.sleep(0.5)

    try:
        real_inventory, _ = kiwoom_orders.get_my_inventory(token)
        real_stock = next(
            (item for item in (real_inventory or []) if str(item.get('code', '')).strip()[:6] == code),
            None,
        )
        if real_stock:
            real_qty = int(float(real_stock.get('qty', 0) or 0))
            if real_qty > 0:
                return real_qty
    except Exception:
        pass

    try:
        return max(0, int(expected_qty or 0))
    except Exception:
        return 0


def extract_ord_no(res):
    if isinstance(res, dict):
        return str(res.get('ord_no', '') or res.get('odno', '') or '')
    return ''


def is_ok_response(res):
    if isinstance(res, dict):
        return str(res.get('return_code', res.get('rt_cd', ''))) == '0'
    return bool(res)
