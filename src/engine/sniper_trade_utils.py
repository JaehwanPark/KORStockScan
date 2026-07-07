"""Shared trading utilities for the sniper engine."""

import time

from src.engine import kiwoom_orders
from src.utils import kiwoom_utils


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


def _cancel_response_success(response) -> bool:
    if isinstance(response, dict):
        return str(response.get("return_code", response.get("rt_cd", ""))) == "0"
    return bool(response)


def _cancel_response_message(response) -> str:
    if isinstance(response, dict):
        return str(response.get("return_msg", "") or "")
    return str(response or "")


def _cancel_reject_indicates_sor_exchange_mismatch(message: str) -> bool:
    text = str(message or "")
    return "571412" in text or "원주문이 SOR주문" in text


def _cancel_exchange_from_unfilled_row(row: dict | None) -> str:
    row = row if isinstance(row, dict) else {}
    raw = row.get("raw") if isinstance(row.get("raw"), dict) else {}
    sor_yn = str(row.get("sor_yn") or raw.get("sor_yn") or "").strip().upper()
    if sor_yn == "Y":
        return "SOR"
    stex_tp = str(row.get("stex_tp") or raw.get("stex_tp") or "").strip().upper()
    if stex_tp == "1":
        return "KRX"
    if stex_tp == "2":
        return "NXT"
    stex_text = str(row.get("stex_tp_txt") or raw.get("stex_tp_txt") or "").strip().upper()
    if "NXT" in stex_text:
        return "NXT"
    if "KRX" in stex_text:
        return "KRX"
    return ""


def _resolve_cancel_exchange_from_unfilled_snapshot(code: str, orig_ord_no: str, token: str) -> str:
    try:
        rows = kiwoom_utils.get_unfilled_order_snapshot_ka10075(
            token,
            stk_cd=code,
            stex_tp="0",
        )
    except Exception:
        return ""
    normalized_ord_no = str(orig_ord_no or "").strip()
    for row in rows or []:
        row_ord_no = str((row or {}).get("ord_no") or "").strip()
        if row_ord_no != normalized_ord_no:
            continue
        return _cancel_exchange_from_unfilled_row(row)
    return ""


def send_cancel_order_with_exchange_retry(code, orig_ord_no, token, qty=0, dmst_stex_tp="SOR"):
    cancel_exchange = str(dmst_stex_tp or "SOR").strip().upper()
    if cancel_exchange not in {"KRX", "NXT", "SOR"}:
        cancel_exchange = "SOR"
    res = kiwoom_orders.send_cancel_order(
        code=code,
        orig_ord_no=orig_ord_no,
        token=token,
        qty=qty,
        dmst_stex_tp=cancel_exchange,
    )
    if _cancel_response_success(res) or cancel_exchange != "SOR":
        return res
    if not _cancel_reject_indicates_sor_exchange_mismatch(_cancel_response_message(res)):
        return res

    resolved_exchange = _resolve_cancel_exchange_from_unfilled_snapshot(code, orig_ord_no, token)
    if resolved_exchange not in {"KRX", "NXT"}:
        return res
    return kiwoom_orders.send_cancel_order(
        code=code,
        orig_ord_no=orig_ord_no,
        token=token,
        qty=qty,
        dmst_stex_tp=resolved_exchange,
    )


def confirm_cancel_or_reload_remaining(code, orig_ord_no, token, expected_qty):
    """
    [공통 유틸] 주문 취소 후 실제 계좌 잔고를 재조회하여 팔아야 할 정확한 잔량(rem_qty) 반환
    """
    if orig_ord_no:
        send_cancel_order_with_exchange_retry(
            code=code,
            orig_ord_no=orig_ord_no,
            token=token,
            qty=0,
        )
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
