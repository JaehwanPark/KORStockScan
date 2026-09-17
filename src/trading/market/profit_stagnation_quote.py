"""Read existing exact-route WS depth; no subscription or broker request."""

from __future__ import annotations

from datetime import datetime

from src.trading.market.confirmation_window import _normalize
from src.trading.market.micro_confirmation import (
    _live_route_item,
    load_live_dynamic_confirmation_source,
)
from src.trading.order.profit_stagnation import _finite
from src.trading.market.quote_consistency import build_market_data_health, _best_levels


def executable_quote(
    *, symbol: str, route: str, quantity: int, now: datetime, snapshot=None
) -> dict:
    if type(quantity) is not int or quantity <= 0 or now.utcoffset() is None:
        raise ValueError("profit_quote_quantity_or_time_invalid")
    if snapshot is None:
        snapshot, reason = load_live_dynamic_confirmation_source()
        if snapshot is None:
            raise ValueError(reason)
    item = _live_route_item(symbol, route)
    stock = snapshot["stocks"][symbol]
    rows = stock["machine_confirmation_routes"]
    matches = [
        (key, r)
        for key, r in rows.items()
        if r.get("realtime_types", {}).get("0D", {}).get("item") == item
    ]
    if not item or len(matches) != 1:
        raise ValueError("profit_quote_exact_route_missing_or_duplicate")
    key, source = matches[0]
    # Quote-only execution must not require recent trades. Consume the common
    # owner with the existing two-second quote TTL, never cached health or the
    # file publication clock. Current connection epoch remains mandatory.
    health = build_market_data_health(
        stock, now_ts=now.timestamp(), quote_max_age_ms=2000
    )
    facts = health["routes"].get(key, {})
    if facts.get("quote_state") != "fresh":
        raise ValueError("profit_quote_common_health_not_fresh")
    receipt = source["realtime_types"]["0D"]
    candidates = [
        r
        for r in source.get("recent_depth", [])
        if r.get("item") == item
        and r.get("transport_epoch") == receipt.get("transport_epoch")
        and r.get("route_sequence") == receipt.get("route_sequence")
    ]
    if len(candidates) != 1:
        raise ValueError("profit_quote_depth_missing_or_duplicate")
    raw = candidates[0]
    quote = _normalize(raw, depth=True)
    stamp = quote["at_ms"] / 1000
    receipt_bid, receipt_ask = _best_levels(receipt)
    if (
        type(receipt.get("route_sequence")) is not int
        or quote["sequence"] != receipt.get("route_sequence")
        or type(receipt.get("observed_epoch")) not in {int, float}
        or not _finite(receipt["observed_epoch"])
        or abs(receipt["observed_epoch"] * 1000 - quote["at_ms"]) > 1
        or (quote["bid"], quote["ask"]) != (receipt_bid, receipt_ask)
    ):
        raise ValueError("profit_quote_stale_or_endpoint_mismatch")
    levels = raw.get("bid_levels")
    if not isinstance(levels, (list, tuple)) or not levels:
        raise ValueError("profit_quote_depth_missing")
    remaining, total, worst, last = quantity, 0, None, None
    for level in levels:
        if isinstance(level, dict):
            price, qty = level.get("price"), level.get("quantity")
        elif isinstance(level, (tuple, list)) and len(level) == 3:
            _, price, qty = level
        else:
            raise ValueError("profit_quote_invalid_depth")
        if (
            not _finite(price)
            or price <= 0
            or price >= quote["ask"]
            or type(qty) is not int
            or qty <= 0
            or (last is not None and price >= last)
        ):
            raise ValueError("profit_quote_invalid_depth")
        if last is None and price != quote["bid"]:
            raise ValueError("profit_quote_touch_mismatch")
        last, total = price, total + qty
        if remaining:
            remaining = max(0, remaining - qty)
            worst = price
    if remaining:
        raise ValueError("profit_quote_insufficient_depth")
    return dict(
        executable_bid=worst,
        available_quantity=total,
        quote_at=stamp,
        quote_id=f"{item}:{quote['epoch']}:{quote['sequence']}",
        source_epoch=f"{item}:{quote['epoch']}",
        market_data_health=health,
    )
