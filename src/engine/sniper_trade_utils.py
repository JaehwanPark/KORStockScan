"""Shared trading utilities for the sniper engine."""

import re
import time

from src.engine import kiwoom_orders
from src.utils import kiwoom_utils


class BrokerRemainingQty(int):
    """Integer-compatible broker quantity with tri-state confirmation provenance."""

    def __new__(
        cls,
        value,
        *,
        confirmation_state: str,
        source: str,
        successful_exchanges=(),
    ):
        instance = int.__new__(cls, max(0, int(value or 0)))
        instance.confirmation_state = str(confirmation_state)
        instance.source = str(source)
        instance.successful_exchanges = tuple(
            sorted(
                {
                    str(exchange or "").strip().upper()
                    for exchange in (successful_exchanges or ())
                    if str(exchange or "").strip()
                }
            )
        )
        return instance


def _remaining_qty_result(
    value: int,
    *,
    confirmation_state: str,
    source: str,
    successful_exchanges=(),
) -> BrokerRemainingQty:
    return BrokerRemainingQty(
        value,
        confirmation_state=confirmation_state,
        source=source,
        successful_exchanges=successful_exchanges,
    )


def _strict_nonnegative_int(value):
    """Parse broker quantities without accepting float/scientific coercion."""

    if isinstance(value, bool):
        return None
    normalized = str(value if value is not None else "").strip()
    if not re.fullmatch(r"[+]?(?:\d{1,3}(?:,\d{3})+|\d+)", normalized):
        return None
    try:
        parsed = int(normalized.replace(",", ""))
    except ValueError:
        return None
    return parsed if parsed >= 0 else None


def send_market_exit_now(code, qty, token):
    """정규장 중 즉시 시장가 청산용 공통 래퍼"""
    return kiwoom_orders.send_sell_order_market(
        code=code,
        qty=qty,
        token=token,
        order_type="3",
    )


def send_exit_best_ioc(
    code,
    qty,
    token,
    *,
    dmst_stex_tp=None,
    reason_type=None,
    strategy=None,
    bypass_open_time_block=False,
):
    """[공통 긴급 청산 래퍼] 최유리(IOC, 16) 조건으로 즉각 청산 시도"""
    kwargs = {
        "code": code,
        "qty": qty,
        "token": token,
        "order_type": "16",
        "dmst_stex_tp": dmst_stex_tp,
        "reason_type": reason_type,
        "strategy": strategy,
    }
    if bypass_open_time_block:
        kwargs["bypass_open_time_block"] = True
    return kiwoom_orders.send_sell_order_market(**kwargs)


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
    stex_text = (
        str(row.get("stex_tp_txt") or raw.get("stex_tp_txt") or "").strip().upper()
    )
    if "NXT" in stex_text:
        return "NXT"
    if "KRX" in stex_text:
        return "KRX"
    return ""


def _resolve_cancel_exchange_from_unfilled_snapshot(
    code: str, orig_ord_no: str, token: str
) -> str:
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


def send_cancel_order_with_exchange_retry(
    code, orig_ord_no, token, qty=0, dmst_stex_tp="SOR"
):
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
    if not _cancel_reject_indicates_sor_exchange_mismatch(
        _cancel_response_message(res)
    ):
        return res

    resolved_exchange = _resolve_cancel_exchange_from_unfilled_snapshot(
        code, orig_ord_no, token
    )
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
    Return a broker-confirmed remaining position after an acknowledged cancel.

    ``expected_qty`` is intentionally not a fallback.  Reusing the pre-cancel
    quantity after an unknown cancel/inventory result can duplicate a partially
    filled SELL, so every ambiguous path fails closed with zero.
    """
    if orig_ord_no:
        cancel_result = send_cancel_order_with_exchange_retry(
            code=code,
            orig_ord_no=orig_ord_no,
            token=token,
            qty=0,
        )
        if not _cancel_response_success(cancel_result):
            return _remaining_qty_result(
                0,
                confirmation_state="unknown",
                source="cancel_unconfirmed",
            )
        time.sleep(0.5)

    try:
        real_inventory, successful_exchanges = kiwoom_orders.get_my_inventory(token)
        successful = {
            str(exchange or "").strip().upper()
            for exchange in (successful_exchanges or ())
        }
        matching_rows = [
            item
            for item in (real_inventory or [])
            if str(item.get("code", "")).strip()[:6] == code
        ]
        if matching_rows:
            if not {"KRX", "NXT"}.issubset(successful):
                return _remaining_qty_result(
                    0,
                    confirmation_state="unknown",
                    source="kt00018_partial_venue_confirmation",
                    successful_exchanges=successful,
                )
            parsed_quantities = [
                _strict_nonnegative_int(item.get("qty")) for item in matching_rows
            ]
            if any(quantity is None for quantity in parsed_quantities):
                return _remaining_qty_result(
                    0,
                    confirmation_state="unknown",
                    source="kt00018_inventory_quantity_malformed",
                    successful_exchanges=successful,
                )
            quantity = sum(parsed_quantities)
            if quantity > 0:
                return _remaining_qty_result(
                    quantity,
                    confirmation_state="confirmed_positive",
                    source="kt00018_position_found",
                    successful_exchanges=successful,
                )
            if {"KRX", "NXT"}.issubset(successful):
                return _remaining_qty_result(
                    0,
                    confirmation_state="verified_zero",
                    source="kt00018_all_venues_zero_row",
                    successful_exchanges=successful,
                )
    except Exception:
        return _remaining_qty_result(
            0,
            confirmation_state="unknown",
            source="inventory_lookup_failed",
        )
    if {"KRX", "NXT"}.issubset(successful):
        return _remaining_qty_result(
            0,
            confirmation_state="verified_zero",
            source="kt00018_all_venues_position_absent",
            successful_exchanges=successful,
        )
    return _remaining_qty_result(
        0,
        confirmation_state="unknown",
        source="kt00018_partial_venue_confirmation",
        successful_exchanges=successful,
    )


def extract_ord_no(res):
    if isinstance(res, dict):
        return str(res.get("ord_no", "") or res.get("odno", "") or "")
    return ""


def is_ok_response(res):
    if isinstance(res, dict):
        return str(res.get("return_code", res.get("rt_cd", ""))) == "0"
    return bool(res)
