"""Shared runtime state for latency-aware entry bundles."""

from __future__ import annotations

import threading
import time
from typing import Any

ENTRY_LOCK = threading.RLock()
# Kiwoom can report a fill several minutes after the local cancel/reconcile path
# has terminalized the entry order. Keep the order-no bridge long enough for that
# delayed broker receipt to update DB/Telegram/holding state.
TERMINAL_ENTRY_GRACE_SECONDS = 900.0
TERMINAL_ENTRY_ORDERS: dict[str, dict[str, Any]] = {}


def prune_terminal_entry_orders(now_ts: float | None = None) -> None:
    """Drop expired terminal entry order mappings."""

    now = float(now_ts if now_ts is not None else time.time())
    expired = [
        ord_no
        for ord_no, payload in TERMINAL_ENTRY_ORDERS.items()
        if float(payload.get("expire_at", 0) or 0) <= now
    ]
    for ord_no in expired:
        TERMINAL_ENTRY_ORDERS.pop(ord_no, None)


def move_orders_to_terminal(
    stock: dict[str, Any],
    *,
    reason: str,
    grace_seconds: float = TERMINAL_ENTRY_GRACE_SECONDS,
    now_ts: float | None = None,
) -> None:
    """Retain recent entry bundle legs briefly so delayed receipts still reconcile."""

    now = float(now_ts if now_ts is not None else time.time())
    prune_terminal_entry_orders(now)

    code = str(stock.get("code", "") or "")[:6]
    bundle_id = str(stock.get("entry_bundle_id", "") or stock.get("odno", "") or "")
    entry_mode = str(stock.get("entry_mode", "") or "unknown")
    stock_name = str(stock.get("name", "") or "")
    strategy = str(stock.get("strategy", "") or "")

    for order in stock.get("pending_entry_orders") or []:
        ord_no = str(order.get("ord_no", "") or "").strip()
        if not ord_no:
            continue
        TERMINAL_ENTRY_ORDERS[ord_no] = {
            "stock_code": code,
            "stock_name": stock_name,
            "bundle_id": bundle_id,
            "leg_type": str(order.get("tag", "") or "unknown"),
            "entry_mode": entry_mode,
            "strategy": strategy,
            "expire_at": now + float(grace_seconds),
            "reason": reason,
        }


def get_terminal_entry_order(
    ord_no: str, *, now_ts: float | None = None
) -> dict[str, Any] | None:
    """Return active terminal mapping for a delayed receipt, if still within grace window."""

    normalized = str(ord_no or "").strip()
    if not normalized:
        return None
    prune_terminal_entry_orders(now_ts)
    payload = TERMINAL_ENTRY_ORDERS.get(normalized)
    if not payload:
        return None
    if float(payload.get("expire_at", 0) or 0) <= float(
        now_ts if now_ts is not None else time.time()
    ):
        TERMINAL_ENTRY_ORDERS.pop(normalized, None)
        return None
    return dict(payload)
