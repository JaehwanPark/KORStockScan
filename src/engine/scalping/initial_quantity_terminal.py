"""Exact BUY leg terminal evidence for a sequential initial-entry bundle.

This module does not submit, cancel, or query an order.  A broker ACK is an
identity for a cancel child, never proof that the original BUY has ended.

Official reference checked 2026-09-27 10:37 KST: Kiwoom-REST-API main
953e5dbff123f437ab4d11a78a95191a685eb51f, packaged kt00007/ka10075/
kt10000/kt10003 specs, kiwoom/specs.py, kiwoom/core/client.py and Postman.
The checkout has no kiwoom_docs directory. No request envelope is changed.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
    ).encode("ascii")).hexdigest()


def _qty(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return None
    value = str(value).strip()
    if not re.fullmatch(r"\+?[0-9]+", value):
        return None
    return int(value)


def _order_no(value: Any) -> str | None:
    value = str(value or "").strip()
    return value if re.fullmatch(r"[0-9]{7}", value) and int(value) > 0 else None


def _one_row(rows: list[dict[str, Any]], order_no: str) -> dict[str, Any] | None:
    matching = [row for row in rows if row.get("ord_no") == order_no]
    if not matching or any(row != matching[0] for row in matching):
        return None
    return matching[0]


def _row_route(row: dict[str, Any]) -> str | None:
    # The broker history reports exchange as 1/2, even when the submitted
    # request used KRX/NXT. SOR is identified by its explicit router flag.
    raw = row.get("raw")
    raw = raw if isinstance(raw, dict) else {}
    sor = str(row.get("sor_yn") or raw.get("sor_yn") or "").upper()
    exchange = str(row.get("stex_tp") or "").upper()
    if sor == "Y":
        return "SOR"
    if sor not in {"", "N"}:
        return None
    return {"1": "KRX", "KRX": "KRX", "2": "NXT", "NXT": "NXT"}.get(exchange)


def prove_initial_buy_leg_terminal(
    *, order_date: str, stock_code: str, route: str, order_no: str,
    ordered_qty: int, cancel_order_no: str | None,
    dated_rows: list[dict[str, Any]], dated_meta: dict[str, Any],
    current_rows: list[dict[str, Any]], current_meta: dict[str, Any],
    observed_at_epoch: float, now_epoch: float,
) -> dict[str, Any] | None:
    """Prove Q=F+C and current absence for one exact BUY order.

    ``kt00007`` supplies the original BUY and, when cancelled, its separate
    positive-confirmation cancel child. ``ka10075`` proves both are absent from
    the complete current unfilled census.  Owner and inventory custody must
    still be checked by the caller before releasing a successor BUY.
    """
    try:
        day = date.fromisoformat(order_date)
    except (TypeError, ValueError):
        return None
    if (day.isoformat() != order_date
            or not re.fullmatch(r"[0-9]{6}", str(stock_code or ""))
            or route not in {"KRX", "NXT", "SOR"}
            or _order_no(order_no) is None
            or (cancel_order_no is not None
                and (_order_no(cancel_order_no) is None
                     or cancel_order_no == order_no))
            or type(ordered_qty) is not int or ordered_qty <= 0
            or not isinstance(dated_rows, list) or not isinstance(current_rows, list)
            or any(not isinstance(row, dict) for row in dated_rows + current_rows)
            or any(not isinstance(meta, dict)
                   or meta.get("request_succeeded") is not True
                   or meta.get("normalization_contract_complete") is not True
                   for meta in (dated_meta, current_meta))
            or isinstance(observed_at_epoch, bool)
            or isinstance(now_epoch, bool)
            or not all(isinstance(value, (float, int)) and math.isfinite(value)
                       for value in (observed_at_epoch, now_epoch))
            or not 0 <= observed_at_epoch <= now_epoch < 4102444800
            or not 0 <= now_epoch - observed_at_epoch <= 2
            or datetime.fromtimestamp(now_epoch, KST).date() != day):
        return None
    related = {order_no, cancel_order_no} - {None}
    if any(row.get("ord_no") in related for row in current_rows):
        return None
    root = _one_row(dated_rows, order_no)
    if root is None:
        return None
    def identity(row: dict[str, Any]) -> bool:
        return bool(row.get("source_api") == "kt00007"
                    and row.get("trade_date") == day.strftime("%Y%m%d")
                    and row.get("trade_date_contract_valid") is True
                    and row.get("code") == stock_code
                    and row.get("code_contract_valid") is True
                    and row.get("order_no_contract_valid") is True
                    and row.get("side") == "매수"
                    and row.get("side_contract_valid") is True
                    and row.get("route_contract_valid") is True
                    and _row_route(row) == route)
    if not identity(root):
        return None
    raw_root = root.get("raw")
    if not isinstance(raw_root, dict):
        return None
    filled = _qty(raw_root.get("cntr_qty"))
    remaining = _qty(raw_root.get("ord_remnq"))
    if (_qty(raw_root.get("ord_qty")) != ordered_qty
            or filled is None or remaining != 0 or filled > ordered_qty):
        return None
    cancelled = 0
    child = None
    if cancel_order_no is not None:
        child = _one_row(dated_rows, cancel_order_no)
        if child is None or not identity(child) or child.get("orig_ord_no") != order_no:
            return None
        raw_child = child.get("raw")
        if not isinstance(raw_child, dict):
            return None
        cancelled = _qty(raw_child.get("cnfm_qty"))
        child_qty = _qty(raw_child.get("ord_qty"))
        child_filled = _qty(raw_child.get("cntr_qty"))
        child_remaining = _qty(raw_child.get("ord_remnq"))
        confirm_at = str(raw_child.get("cnfm_tm") or "").replace(":", "")
        # kt00007 calls cnfm_qty a generic confirmation quantity. A change
        # child can confirm quantity too, so the raw cancel operation must be
        # explicit before those shares may count as cancelled.
        cancel_kind = str(raw_child.get("mdfy_cncl") or "").strip()
        order_kind = str(raw_child.get("io_tp_nm") or "").strip()
        if (cancelled is None or cancelled <= 0
                or child_qty is None or not cancelled <= child_qty <= ordered_qty
                or child_filled != 0 or child_remaining != 0
                or not re.fullmatch(r"[0-9]{6}", confirm_at)
                or cancel_kind != "취소" or "매수취소" not in order_kind):
            return None
    if filled + cancelled != ordered_qty:
        return None
    if any(row.get("orig_ord_no") in related and row.get("ord_no") not in related
           for row in dated_rows + current_rows):
        return None
    try:
        body = {"schema": "initial_quantity_buy_leg_terminal_v1",
                "order_date": order_date, "stock_code": stock_code,
                "route": route, "order_no": order_no,
                "cancel_order_no": cancel_order_no, "ordered_qty": ordered_qty,
                "filled_qty": filled, "cancelled_qty": cancelled,
                "broker_unfilled_qty": 0, "observed_at_epoch": observed_at_epoch,
                "dated_source_sha256": _digest({"rows": dated_rows, "meta": dated_meta}),
                "current_source_sha256": _digest({"rows": current_rows,
                                                  "meta": current_meta})}
        return {**body, "proof_sha256": _digest(body)}
    except (TypeError, ValueError, OverflowError):
        return None


def read_initial_buy_leg_terminal(
    *, token: str, order_date: str, stock_code: str, route: str,
    order_no: str, ordered_qty: int, cancel_order_no: str | None,
    client: Any = None, clock: Any = time.time,
) -> tuple[dict[str, Any] | None, str]:
    """Read dated BUY and current unfilled through existing bounded clients.

    The returned proof covers broker quantity only. The caller must still
    verify the exact Main owner registry and account position before another
    BUY can be submitted. No write or retry is performed here.
    """
    if not token or not order_date or not stock_code or not order_no:
        return None, "read_identity_missing"
    if client is None:
        from src.utils import kiwoom_utils
        client = kiwoom_utils
    started = clock()
    try:
        dated, dated_meta = client.get_order_reference_snapshot_kt00007_with_meta(
            token, ord_dt=order_date.replace("-", ""), qry_tp="1",
            stk_bond_tp="1", sell_tp="2", stk_cd=stock_code,
            fr_ord_no="", dmst_stex_tp="%")
        current, current_meta = client.get_unfilled_order_snapshot_ka10075_with_meta(
            token, stk_cd=stock_code, all_stk_tp="1",
            trde_tp="2", stex_tp="0")
    except Exception as exc:
        return None, "broker_read_failed:" + type(exc).__name__
    observed = clock()
    if (type(started) not in (int, float) or type(observed) not in (int, float)
            or not math.isfinite(started) or not math.isfinite(observed)
            or not 0 <= observed - started <= 10):
        return None, "broker_read_window_invalid"
    proof = prove_initial_buy_leg_terminal(
        order_date=order_date, stock_code=stock_code, route=route,
        order_no=order_no, ordered_qty=ordered_qty,
        cancel_order_no=cancel_order_no,
        dated_rows=dated, dated_meta=dated_meta,
        current_rows=current, current_meta=current_meta,
        observed_at_epoch=observed, now_epoch=clock())
    return (proof, "broker_terminal_proved" if proof else
            "broker_terminal_unproved")
