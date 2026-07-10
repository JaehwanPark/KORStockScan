"""Market-data freshness envelope for scalping scanner decisions.

The envelope normalizes WS, REST orderbook, and REST signed-tape freshness.
REST data is provenance/source-quality support only; it must not create BUY
pressure or bypass hard submit safety.
"""

from __future__ import annotations

import time
from typing import Any


FRESH_WS = "fresh_ws"
REST_ENRICHED = "rest_enriched"
MISSING = "missing"
STALE = "stale"
CONFLICTED = "conflicted"

SIGNED_TAPE_SELL_DOMINATED = "sell_dominated"
SIGNED_TAPE_BUY_DOMINATED = "buy_dominated"
SIGNED_TAPE_MIXED = "mixed"
SIGNED_TAPE_INSUFFICIENT = "insufficient"
SIGNED_TAPE_MISSING = "missing"

MARKET_DATA_FORBIDDEN_USES = (
    "buy_support,pressure_math,threshold_mutation,provider_route_change,"
    "order_price_relaxation,quantity_or_cap_change,broker_guard_bypass,"
    "stale_quote_bypass,real_execution_quality_approval"
)


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        if value in (None, "", "-"):
            return default
        return float(str(value).replace(",", ""))
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "", "-"):
            return int(default)
        return int(float(str(value).replace(",", "").replace("+", "")))
    except Exception:
        return int(default)


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    return text in {"1", "true", "yes", "y", "on", "stale"}


def _epoch_ms_to_age_ms(value: Any, now_ts: float) -> float | None:
    parsed = _safe_float(value, None)
    if parsed is None or parsed <= 0:
        return None
    if parsed > 10_000_000_000:
        parsed = parsed / 1000.0
    return max(0.0, (float(now_ts) - float(parsed)) * 1000.0)


def _age_ms_from_keys(source: dict[str, Any], now_ts: float, keys: tuple[str, ...]) -> float | None:
    for key in keys:
        if key not in source:
            continue
        if key.endswith("_age_ms") or key == "age_ms":
            parsed = _safe_float(source.get(key), None)
            if parsed is not None and parsed >= 0:
                return float(parsed)
        age = _epoch_ms_to_age_ms(source.get(key), now_ts)
        if age is not None:
            return age
    return None


def _ws_age_ms(ws_data: dict[str, Any], now_ts: float) -> float | None:
    age = _age_ms_from_keys(
        ws_data,
        now_ts,
        (
            "quote_age_ms",
            "ws_age_ms",
            "pre_submit_effective_quote_age_ms",
            "pre_ai_ws_snapshot_refresh_age_ms",
            "last_ws_update_ts",
            "received_at",
            "received_ts",
            "timestamp",
            "ts",
        ),
    )
    return age


def _rest_age_ms(rest_orderbook: dict[str, Any], now_ts: float) -> float | None:
    if not isinstance(rest_orderbook, dict) or not rest_orderbook:
        return None
    is_ka10004_snapshot = str(rest_orderbook.get("source") or "").strip() == "ka10004_rest_orderbook"
    age_keys = (
        "pre_submit_rest_orderbook_refresh_age_ms",
        "rest_received_age_ms",
        "received_age_ms",
        "rest_received_ts_ms",
        "received_at_ms",
        "rest_received_ts",
        "received_at",
        "received_ts",
        "timestamp",
        "ts",
    )
    if not is_ka10004_snapshot:
        age_keys = ("age_ms", *age_keys)
    age = _age_ms_from_keys(
        rest_orderbook,
        now_ts,
        age_keys,
    )
    if age is not None:
        return age
    if is_ka10004_snapshot:
        return None
    return None


def _orderbook_side(orderbook: Any, side: str) -> dict[str, Any]:
    if not isinstance(orderbook, dict):
        return {}
    rows = orderbook.get(side)
    if isinstance(rows, list) and rows:
        row = rows[0]
        return row if isinstance(row, dict) else {}
    row = orderbook.get(f"best_{side[:-1]}")
    return row if isinstance(row, dict) else {}


def _quote_levels(source: dict[str, Any]) -> dict[str, int]:
    orderbook = source.get("orderbook")
    ask_row = _orderbook_side(orderbook, "asks")
    bid_row = _orderbook_side(orderbook, "bids")
    best_ask = _safe_int(
        source.get("best_ask") or source.get("ask_price") or ask_row.get("price"),
        0,
    )
    best_bid = _safe_int(
        source.get("best_bid") or source.get("bid_price") or bid_row.get("price"),
        0,
    )
    best_ask_qty = _safe_int(
        source.get("best_ask_qty") or source.get("ask_qty") or ask_row.get("qty"),
        0,
    )
    best_bid_qty = _safe_int(
        source.get("best_bid_qty") or source.get("bid_qty") or bid_row.get("qty"),
        0,
    )
    curr = _safe_int(
        source.get("curr")
        or source.get("current_price")
        or source.get("price")
        or source.get("rest_mid_price")
        or source.get("canonical_mark_price")
        or source.get("현재가"),
        0,
    )
    return {
        "curr": abs(curr),
        "best_ask": abs(best_ask),
        "best_bid": abs(best_bid),
        "best_ask_qty": abs(best_ask_qty),
        "best_bid_qty": abs(best_bid_qty),
    }


def _quote_usable(levels: dict[str, int]) -> bool:
    curr = levels.get("curr", 0)
    best_ask = levels.get("best_ask", 0)
    best_bid = levels.get("best_bid", 0)
    return bool(curr > 0 and best_ask > 0 and best_bid > 0 and best_ask >= best_bid)


def _gap_bps(ws_levels: dict[str, int], rest_levels: dict[str, int]) -> float | None:
    ws_price = ws_levels.get("curr", 0) or ws_levels.get("best_ask", 0) or ws_levels.get("best_bid", 0)
    rest_price = rest_levels.get("curr", 0) or rest_levels.get("best_ask", 0) or rest_levels.get("best_bid", 0)
    if ws_price <= 0 or rest_price <= 0:
        return None
    basis = max(ws_price, rest_price)
    if basis <= 0:
        return None
    return abs(float(ws_price) - float(rest_price)) / float(basis) * 10000.0


def _signed_tick_side_and_qty(tick: dict[str, Any]) -> tuple[str, int]:
    side = str(tick.get("aggressor_side") or tick.get("side") or "").strip().upper()
    raw = tick.get("aggressor_aux_raw_15")
    if raw in (None, "", "-"):
        raw = tick.get("signed_trade_volume") or tick.get("signed_volume") or tick.get("체결량")
    text = str(raw or "").strip().replace(",", "")
    qty = abs(_safe_int(text, 0))
    if side not in {"BUY", "SELL"}:
        if text.startswith("-"):
            side = "SELL"
        elif text.startswith("+"):
            side = "BUY"
    return side, qty


def _signed_tape_fields(
    ticks: Any,
    *,
    signed_tape_window: int,
    signed_tape_min_samples: int,
    signed_tape_sell_max_buy_ratio: float,
) -> dict[str, Any]:
    if not isinstance(ticks, list) or not ticks:
        return {
            "market_data_signed_tape_state": SIGNED_TAPE_MISSING,
            "market_data_signed_tape_sample_count": 0,
            "market_data_signed_tape_buy_count": 0,
            "market_data_signed_tape_sell_count": 0,
            "market_data_signed_tape_buy_volume": 0,
            "market_data_signed_tape_sell_volume": 0,
            "market_data_signed_tape_buy_ratio_pct": "-",
            "market_data_rest_signed_tape_pressure_usable": False,
        }
    buy_count = sell_count = buy_volume = sell_volume = 0
    sample = 0
    for tick in ticks[: max(1, int(signed_tape_window))]:
        if not isinstance(tick, dict):
            continue
        side, qty = _signed_tick_side_and_qty(tick)
        if side == "BUY":
            buy_count += 1
            buy_volume += qty
            sample += 1
        elif side == "SELL":
            sell_count += 1
            sell_volume += qty
            sample += 1
    total_volume = buy_volume + sell_volume
    buy_ratio = (float(buy_volume) / float(total_volume) * 100.0) if total_volume > 0 else None
    if sample < max(1, int(signed_tape_min_samples)):
        state = SIGNED_TAPE_INSUFFICIENT
    elif (
        sell_count > buy_count
        and sell_volume > buy_volume
        and buy_ratio is not None
        and buy_ratio <= float(signed_tape_sell_max_buy_ratio)
    ):
        state = SIGNED_TAPE_SELL_DOMINATED
    elif (
        buy_count > sell_count
        and buy_volume > sell_volume
        and buy_ratio is not None
        and buy_ratio >= 100.0 - float(signed_tape_sell_max_buy_ratio)
    ):
        state = SIGNED_TAPE_BUY_DOMINATED
    else:
        state = SIGNED_TAPE_MIXED
    return {
        "market_data_signed_tape_state": state,
        "market_data_signed_tape_sample_count": int(sample),
        "market_data_signed_tape_buy_count": int(buy_count),
        "market_data_signed_tape_sell_count": int(sell_count),
        "market_data_signed_tape_buy_volume": int(buy_volume),
        "market_data_signed_tape_sell_volume": int(sell_volume),
        "market_data_signed_tape_buy_ratio_pct": (
            round(buy_ratio, 3) if buy_ratio is not None else "-"
        ),
        "market_data_rest_signed_tape_pressure_usable": False,
    }


def market_data_enrichment_log_fields(source: dict[str, Any] | None) -> dict[str, Any]:
    source = source if isinstance(source, dict) else {}
    return {key: value for key, value in source.items() if str(key).startswith("market_data_")}


def build_market_data_enrichment(
    *,
    ws_data: dict[str, Any] | None = None,
    rest_orderbook: dict[str, Any] | None = None,
    rest_signed_ticks: list[dict[str, Any]] | None = None,
    candidate_metadata: dict[str, Any] | None = None,
    now_ts: float | None = None,
    max_ws_age_ms: float = 3000.0,
    max_rest_age_ms: float = 1500.0,
    max_ws_rest_gap_bps: float = 120.0,
    signed_tape_window: int = 5,
    signed_tape_min_samples: int = 3,
    signed_tape_sell_max_buy_ratio: float = 45.0,
) -> tuple[dict[str, Any], dict[str, Any]]:
    now_value = time.time() if now_ts is None else float(now_ts)
    base = dict(ws_data or {})
    rest_orderbook = rest_orderbook if isinstance(rest_orderbook, dict) else {}
    metadata = candidate_metadata if isinstance(candidate_metadata, dict) else {}
    ws_levels = _quote_levels(base)
    rest_levels = _quote_levels(rest_orderbook)
    ws_usable = _quote_usable(ws_levels)
    rest_usable = _quote_usable(rest_levels)
    ws_age = _ws_age_ms(base, now_value)
    rest_age = _rest_age_ms(rest_orderbook, now_value)
    ws_explicit_stale = any(
        _boolish(base.get(key))
        for key in ("quote_stale", "stale_quote", "context_stale", "diagnostic_quote_age_stale")
    )
    ws_fresh = bool(ws_usable and not ws_explicit_stale and ws_age is not None and ws_age <= max_ws_age_ms)
    rest_fresh = bool(rest_usable and rest_age is not None and rest_age <= max_rest_age_ms)
    gap = _gap_bps(ws_levels, rest_levels)
    conflicted = bool(ws_usable and rest_usable and gap is not None and gap > max_ws_rest_gap_bps)
    sources = []
    if ws_usable:
        sources.append("ws")
    if rest_orderbook:
        sources.append("ka10004")
    if rest_signed_ticks:
        sources.append("ka10084")
    if conflicted:
        freshness_state = CONFLICTED
        orderbook_state = CONFLICTED
        effective_age = min(value for value in (ws_age, rest_age) if value is not None) if any(
            value is not None for value in (ws_age, rest_age)
        ) else None
        effective_source = "ws_rest_conflicted"
    elif ws_fresh:
        freshness_state = FRESH_WS
        orderbook_state = FRESH_WS
        effective_age = ws_age
        effective_source = "ws"
    elif rest_fresh:
        freshness_state = REST_ENRICHED
        orderbook_state = REST_ENRICHED
        effective_age = rest_age
        effective_source = "ka10004_rest_orderbook"
        base.update(
            {
                "curr": rest_levels["curr"],
                "best_ask": rest_levels["best_ask"],
                "best_bid": rest_levels["best_bid"],
                "best_ask_qty": rest_levels["best_ask_qty"],
                "best_bid_qty": rest_levels["best_bid_qty"],
                "ask_tot": _safe_int(rest_orderbook.get("ask_tot"), _safe_int(base.get("ask_tot"), 0)),
                "bid_tot": _safe_int(rest_orderbook.get("bid_tot"), _safe_int(base.get("bid_tot"), 0)),
                "orderbook": rest_orderbook.get("orderbook") or base.get("orderbook"),
                "quote_stale": False,
                "stale_quote": False,
                "quote_refresh_source": "ka10004_rest_orderbook",
                "ws_snapshot_recovery_source": (
                    base.get("ws_snapshot_recovery_source") or "ka10004_rest_orderbook_enrichment"
                ),
                "quote_age_ms": float(rest_age),
                "last_ws_update_ts": now_value - float(rest_age) / 1000.0,
            }
        )
    elif ws_usable or rest_usable:
        freshness_state = STALE
        orderbook_state = STALE
        effective_age = ws_age if ws_usable else rest_age
        effective_source = "ws" if ws_usable else "ka10004_rest_orderbook"
    else:
        freshness_state = MISSING
        orderbook_state = MISSING
        effective_age = None
        effective_source = "none"

    signed_fields = _signed_tape_fields(
        rest_signed_ticks,
        signed_tape_window=signed_tape_window,
        signed_tape_min_samples=signed_tape_min_samples,
        signed_tape_sell_max_buy_ratio=signed_tape_sell_max_buy_ratio,
    )
    tick_state = (
        "rest_signed_tape"
        if signed_fields["market_data_signed_tape_state"]
        not in {SIGNED_TAPE_MISSING, SIGNED_TAPE_INSUFFICIENT}
        else "missing"
    )
    fields: dict[str, Any] = {
        "market_data_enrichment_applied": bool(rest_orderbook or rest_signed_ticks),
        "market_data_enrichment_sources": ",".join(sources) if sources else "-",
        "market_data_freshness_state": freshness_state,
        "market_data_effective_quote_age_ms": (
            round(float(effective_age), 3) if effective_age is not None else "-"
        ),
        "market_data_effective_price_source": effective_source,
        "market_data_ws_rest_gap_bps": round(float(gap), 3) if gap is not None else "-",
        "market_data_orderbook_state": orderbook_state,
        "market_data_tick_context_state": tick_state,
        "market_data_candidate_source": metadata.get("source_signature") or metadata.get("source") or "-",
        "market_data_forbidden_uses": MARKET_DATA_FORBIDDEN_USES,
        **signed_fields,
    }
    base.update(fields)
    if rest_signed_ticks:
        base["rest_signed_trade_ticks"] = list(rest_signed_ticks)
    return base, fields
