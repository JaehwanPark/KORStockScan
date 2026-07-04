"""WS/REST quote consistency normalization utilities."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Mapping


RUNTIME_FAMILY = "quote_consistency_normalization"


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        text = str(value).strip().replace(",", "")
        if text in {"", "-", "None", "null"}:
            return default
        return int(float(text))
    except Exception:
        return default


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        text = str(value).strip().replace(",", "")
        if text in {"", "-", "None", "null"}:
            return default
        return float(text)
    except Exception:
        return default


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    value = _to_int(os.getenv(name), default)
    return value if value > 0 else default


def _best_levels(data: Mapping[str, Any] | None) -> tuple[int, int]:
    data = data or {}
    best_bid = _to_int(data.get("best_bid"))
    best_ask = _to_int(data.get("best_ask"))
    orderbook = data.get("orderbook") if isinstance(data.get("orderbook"), Mapping) else {}
    if best_bid <= 0:
        bids = orderbook.get("bids") if isinstance(orderbook, Mapping) else None
        if isinstance(bids, list) and bids:
            first = bids[0]
            best_bid = _to_int(first.get("price") if isinstance(first, Mapping) else first)
    if best_ask <= 0:
        asks = orderbook.get("asks") if isinstance(orderbook, Mapping) else None
        if isinstance(asks, list) and asks:
            first = asks[0]
            best_ask = _to_int(first.get("price") if isinstance(first, Mapping) else first)
    return best_bid, best_ask


def _tick_size(price: int) -> int:
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


@dataclass(frozen=True)
class QuoteConsistencyConfig:
    max_ws_age_ms: int = 700
    max_rest_age_ms: int = 1500
    ok_gap_bps: int = 30
    warn_gap_bps: int = 80
    emergency_rest_timeout_ms: int = 400
    block_entry_on_divergence: bool = True

    @classmethod
    def from_env(cls) -> "QuoteConsistencyConfig":
        return cls(
            max_ws_age_ms=_env_int("KORSTOCKSCAN_QUOTE_CONSISTENCY_MAX_WS_AGE_MS", 700),
            max_rest_age_ms=_env_int("KORSTOCKSCAN_QUOTE_CONSISTENCY_MAX_REST_AGE_MS", 1500),
            ok_gap_bps=_env_int("KORSTOCKSCAN_QUOTE_CONSISTENCY_OK_GAP_BPS", 30),
            warn_gap_bps=_env_int("KORSTOCKSCAN_QUOTE_CONSISTENCY_WARN_GAP_BPS", 80),
            emergency_rest_timeout_ms=_env_int(
                "KORSTOCKSCAN_QUOTE_CONSISTENCY_EMERGENCY_REST_TIMEOUT_MS",
                400,
            ),
            block_entry_on_divergence=_env_bool(
                "KORSTOCKSCAN_QUOTE_CONSISTENCY_BLOCK_ENTRY_ON_DIVERGENCE",
                True,
            ),
        )


@dataclass(frozen=True)
class QuoteInput:
    source: str
    mark_price: int = 0
    executable_buy_price: int = 0
    executable_sell_price: int = 0
    passive_buy_price: int = 0
    passive_sell_price: int = 0
    best_bid: int = 0
    best_ask: int = 0
    age_ms: float | None = None
    observed_at: float | None = None
    has_trade_price: bool = False

    @property
    def has_price(self) -> bool:
        return self.mark_price > 0 or self.best_bid > 0 or self.best_ask > 0


@dataclass(frozen=True)
class QuoteConsistencySnapshot:
    canonical_mark_price: int
    executable_buy_price: int
    executable_sell_price: int
    passive_buy_price: int
    passive_sell_price: int
    quality_state: str
    ws_rest_gap_bps: float | None
    age_ms: float | None
    source: str
    runtime_action: str
    reason: str
    normalization_runtime_effect: bool
    safety_exit_allowed: bool
    entry_blocked: bool
    ws_price: int = 0
    rest_mark_price: int = 0
    ws_age_ms: float | None = None
    rest_age_ms: float | None = None
    best_bid: int = 0
    best_ask: int = 0

    def as_event_fields(self, *, prefix: str = "") -> dict[str, Any]:
        return {
            f"{prefix}quote_consistency_family": RUNTIME_FAMILY,
            f"{prefix}quote_consistency_state": self.quality_state,
            f"{prefix}canonical_mark_price": self.canonical_mark_price,
            f"{prefix}executable_buy_price": self.executable_buy_price,
            f"{prefix}executable_sell_price": self.executable_sell_price,
            f"{prefix}passive_buy_price": self.passive_buy_price,
            f"{prefix}passive_sell_price": self.passive_sell_price,
            f"{prefix}ws_rest_gap_bps": (
                None if self.ws_rest_gap_bps is None else round(float(self.ws_rest_gap_bps), 4)
            ),
            f"{prefix}price_source": self.source,
            f"{prefix}normalization_runtime_effect": bool(self.normalization_runtime_effect),
            f"{prefix}quote_consistency_reason": self.reason,
            f"{prefix}quote_consistency_runtime_action": self.runtime_action,
            f"{prefix}quote_consistency_age_ms": None if self.age_ms is None else round(float(self.age_ms), 3),
            f"{prefix}quote_consistency_ws_age_ms": (
                None if self.ws_age_ms is None else round(float(self.ws_age_ms), 3)
            ),
            f"{prefix}quote_consistency_rest_age_ms": (
                None if self.rest_age_ms is None else round(float(self.rest_age_ms), 3)
            ),
            f"{prefix}quote_consistency_safety_exit_allowed": bool(self.safety_exit_allowed),
            f"{prefix}quote_consistency_entry_blocked": bool(self.entry_blocked),
        }


def quote_input_from_ws(data: Mapping[str, Any] | None, *, now_ts: float | None = None) -> QuoteInput:
    now_ts = float(now_ts or time.time())
    data = data or {}
    best_bid, best_ask = _best_levels(data)
    mark = _to_int(data.get("curr")) or _to_int(data.get("last_trade_price"))
    age_ms = data.get("quote_consistency_ws_age_ms")
    if age_ms is None:
        age_ms = data.get("pre_submit_ws_snapshot_refresh_age_ms")
    if age_ms is None:
        ts = _to_float(data.get("last_ws_update_ts"))
        age_ms = None if ts <= 0 else max(0.0, (now_ts - ts) * 1000.0)
    age_ms = None if age_ms is None else max(0.0, _to_float(age_ms))
    buy_price = best_ask or mark or best_bid
    sell_price = best_bid or mark or best_ask
    passive_buy_price = best_bid or mark or best_ask
    passive_sell_price = best_ask or mark or best_bid
    return QuoteInput(
        source="ws",
        mark_price=mark,
        executable_buy_price=buy_price,
        executable_sell_price=sell_price,
        passive_buy_price=passive_buy_price,
        passive_sell_price=passive_sell_price,
        best_bid=best_bid,
        best_ask=best_ask,
        age_ms=age_ms,
        observed_at=now_ts - (age_ms / 1000.0) if age_ms is not None else None,
        has_trade_price=mark > 0,
    )


def quote_input_from_rest_orderbook(
    data: Mapping[str, Any] | None,
    *,
    now_ts: float | None = None,
) -> QuoteInput:
    now_ts = float(now_ts or time.time())
    data = data or {}
    best_bid, best_ask = _best_levels(data)
    rest_current = _to_int(data.get("rest_current_price")) or _to_int(data.get("current_price"))
    midpoint = _to_int(data.get("rest_mid_price"))
    if midpoint <= 0 and best_bid > 0 and best_ask > 0:
        midpoint = int(round((best_bid + best_ask) / 2.0))
    mark = rest_current or midpoint
    received_ts = _to_float(data.get("rest_received_ts") or data.get("received_ts"))
    received_ms = _to_float(data.get("rest_received_ts_ms") or data.get("received_at_ms"))
    if received_ms > 0:
        age_ms = max(0.0, (now_ts * 1000.0) - received_ms)
    elif received_ts > 0:
        age_ms = max(0.0, (now_ts - received_ts) * 1000.0)
    else:
        age_ms = data.get("pre_submit_rest_orderbook_refresh_age_ms")
        is_ka10004_snapshot = str(data.get("source") or "").strip() == "ka10004_rest_orderbook"
        raw_time_authority = str(data.get("bid_req_base_tm_authority") or "").strip()
        if age_ms is None and not is_ka10004_snapshot and raw_time_authority != "raw_not_freshness_input":
            age_ms = data.get("age_ms")
    age_ms = None if age_ms is None else max(0.0, _to_float(age_ms))
    return QuoteInput(
        source="rest",
        mark_price=mark,
        executable_buy_price=best_ask or mark or best_bid,
        executable_sell_price=best_bid or mark or best_ask,
        passive_buy_price=best_bid or mark or best_ask,
        passive_sell_price=best_ask or mark or best_bid,
        best_bid=best_bid,
        best_ask=best_ask,
        age_ms=age_ms,
        observed_at=now_ts - (age_ms / 1000.0) if age_ms is not None else None,
        has_trade_price=rest_current > 0,
    )


def _fresh(source: QuoteInput | None, max_age_ms: int) -> bool:
    if source is None or not source.has_price:
        return False
    return source.age_ms is not None and float(source.age_ms) <= float(max_age_ms)


def _fallback_price(*prices: int) -> int:
    for price in prices:
        value = _to_int(price)
        if value > 0:
            return value
    return 0


def build_quote_consistency_snapshot(
    *,
    ws: QuoteInput | None = None,
    rest: QuoteInput | None = None,
    side: str = "mark",
    safety_exit: bool = False,
    runtime_enabled: bool | None = None,
    config: QuoteConsistencyConfig | None = None,
) -> QuoteConsistencySnapshot:
    config = config or QuoteConsistencyConfig.from_env()
    if runtime_enabled is None:
        runtime_enabled = _env_bool("KORSTOCKSCAN_QUOTE_CONSISTENCY_RUNTIME_ENABLED", False)
    ws_fresh = _fresh(ws, config.max_ws_age_ms)
    rest_fresh = _fresh(rest, config.max_rest_age_ms)
    ws_mark = ws.mark_price if ws else 0
    rest_mark = rest.mark_price if rest else 0
    best_bid = _fallback_price((ws.best_bid if ws else 0), (rest.best_bid if rest else 0))
    best_ask = _fallback_price((ws.best_ask if ws else 0), (rest.best_ask if rest else 0))
    buy_price = _fallback_price(
        (rest.executable_buy_price if rest and rest_fresh else 0),
        (ws.executable_buy_price if ws and ws_fresh else 0),
        best_ask,
        ws_mark,
        rest_mark,
        best_bid,
    )
    sell_price = _fallback_price(
        (rest.executable_sell_price if rest and rest_fresh else 0),
        (ws.executable_sell_price if ws and ws_fresh else 0),
        best_bid,
        ws_mark,
        rest_mark,
        best_ask,
    )
    passive_buy_price = _fallback_price(
        (rest.passive_buy_price if rest and rest_fresh else 0),
        (ws.passive_buy_price if ws and ws_fresh else 0),
        best_bid,
        ws_mark,
        rest_mark,
        best_ask,
    )
    passive_sell_price = _fallback_price(
        (rest.passive_sell_price if rest and rest_fresh else 0),
        (ws.passive_sell_price if ws and ws_fresh else 0),
        best_ask,
        ws_mark,
        rest_mark,
        best_bid,
    )
    gap_bps = None
    state = "missing"
    reason = "quote_missing"
    source = "none"
    canonical = _fallback_price(ws_mark if ws_fresh else 0, rest_mark if rest_fresh else 0, ws_mark, rest_mark)
    runtime_action = "observe_missing"
    entry_blocked = True
    safety_exit_allowed = bool(safety_exit and sell_price > 0)

    if ws_fresh and rest_fresh and ws_mark > 0 and rest_mark > 0:
        mid = max((ws_mark + rest_mark) / 2.0, 1.0)
        gap_bps = abs(ws_mark - rest_mark) / mid * 10000.0
        reference = int(round(mid))
        ok_gap = max(float(config.ok_gap_bps), (2 * _tick_size(reference)) / max(reference, 1) * 10000.0)
        warn_gap = max(float(config.warn_gap_bps), (5 * _tick_size(reference)) / max(reference, 1) * 10000.0)
        canonical = int(round(mid)) if gap_bps <= warn_gap else ws_mark
        source = "ws_rest_mid" if gap_bps <= warn_gap else "ws_primary_rest_diverged"
        if gap_bps <= ok_gap:
            state = "ok"
            reason = "ws_rest_gap_ok"
            runtime_action = "allow"
            entry_blocked = False
        elif gap_bps <= warn_gap:
            state = "warning"
            reason = "ws_rest_gap_warning"
            runtime_action = "allow_with_warning"
            entry_blocked = False
        else:
            state = "diverged"
            reason = "ws_rest_gap_diverged"
            runtime_action = "allow_safety_exit_pessimistic" if safety_exit else "block_entry_reprice_scale_in"
            entry_blocked = bool(config.block_entry_on_divergence and not safety_exit)
    elif ws_fresh and ws_mark > 0:
        state = "single_source"
        reason = "ws_only_fresh"
        source = "ws"
        canonical = ws_mark
        runtime_action = "allow_single_source"
        entry_blocked = False
    elif rest_fresh and rest_mark > 0:
        state = "single_source"
        reason = "rest_only_fresh"
        source = "rest_mid" if not (rest and rest.has_trade_price) else "rest_current"
        canonical = rest_mark
        runtime_action = "allow_single_source"
        entry_blocked = False
    elif (ws and ws.has_price) or (rest and rest.has_price):
        state = "stale"
        reason = "quote_stale"
        source = "stale_cached"
        runtime_action = "allow_safety_exit_cached" if safety_exit and sell_price > 0 else "block_stale_quote"
        entry_blocked = not safety_exit
    age_candidates = [
        float(value)
        for value in [
            ws.age_ms if ws else None,
            rest.age_ms if rest else None,
        ]
        if value is not None
    ]
    age_ms = min(age_candidates) if age_candidates else None
    if safety_exit:
        entry_blocked = False
        safety_exit_allowed = sell_price > 0
    return QuoteConsistencySnapshot(
        canonical_mark_price=canonical,
        executable_buy_price=buy_price,
        executable_sell_price=sell_price,
        passive_buy_price=passive_buy_price,
        passive_sell_price=passive_sell_price,
        quality_state=state,
        ws_rest_gap_bps=gap_bps,
        age_ms=age_ms,
        source=source,
        runtime_action=runtime_action,
        reason=reason,
        normalization_runtime_effect=bool(runtime_enabled),
        safety_exit_allowed=bool(safety_exit_allowed),
        entry_blocked=bool(entry_blocked),
        ws_price=ws_mark,
        rest_mark_price=rest_mark,
        ws_age_ms=ws.age_ms if ws else None,
        rest_age_ms=rest.age_ms if rest else None,
        best_bid=best_bid,
        best_ask=best_ask,
    )
