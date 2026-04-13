"""Latency-aware entry adapter for the legacy sniper engine."""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from typing import Any

from src.trading.config.entry_config import EntryConfig
from src.trading.entry.entry_policy import EntryPolicy
from src.trading.entry.entry_types import EntryDecision
from src.trading.entry.fallback_strategy import FallbackStrategy
from src.trading.entry.latency_monitor import LatencyMonitor
from src.trading.entry.normal_entry_builder import NormalEntryBuilder
from src.trading.entry.signal_snapshot import build_signal_snapshot
from src.trading.market.market_data_cache import MarketDataCache
from src.utils.constants import TRADING_RULES
from src.utils.logger import log_info


_CONFIG = EntryConfig()
_CACHE = MarketDataCache(stale_after_ms=_CONFIG.max_ws_age_ms_for_caution)
_CACHE_LOCK = threading.RLock()
_LATENCY_MONITOR = LatencyMonitor(_CONFIG)
_ENTRY_POLICY = EntryPolicy(_CONFIG)
_NORMAL_BUILDER = NormalEntryBuilder(_CONFIG)
_FALLBACK_BUILDER = FallbackStrategy(_CONFIG)


def _best_ask_bid_from_ws(ws_data: dict[str, Any] | None) -> tuple[int, int]:
    orderbook = (ws_data or {}).get("orderbook") or {}
    asks = orderbook.get("asks") or []
    bids = orderbook.get("bids") or []

    best_ask = 0
    best_bid = 0
    if asks:
        try:
            best_ask = int(float((asks[0] or {}).get("price", 0) or 0))
        except Exception:
            best_ask = 0
    if bids:
        try:
            best_bid = int(float((bids[0] or {}).get("price", 0) or 0))
        except Exception:
            best_bid = 0
    return best_ask, best_bid


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value).replace(",", "").replace("+", "").strip())
    except Exception:
        return default


def _normalized_reason_set(values: Any) -> set[str]:
    normalized: set[str] = set()
    for value in values or ():
        clean = str(value or "").strip().lower()
        if clean:
            normalized.add(clean)
    return normalized


def _latency_danger_reasons(latency_status) -> list[str]:
    reasons: list[str] = []
    if getattr(latency_status, "quote_stale", False):
        reasons.append("quote_stale")
    max_ws_age_ms = int(getattr(TRADING_RULES, "SCALP_LATENCY_GUARD_CANARY_MAX_WS_AGE_MS", 450) or 450)
    max_ws_jitter_ms = int(getattr(TRADING_RULES, "SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS", 260) or 260)
    max_spread_ratio = _to_float(getattr(TRADING_RULES, "SCALP_LATENCY_GUARD_CANARY_MAX_SPREAD_RATIO", 0.0100), 0.0100)
    if int(getattr(latency_status, "ws_age_ms", 0) or 0) > max_ws_age_ms:
        reasons.append("ws_age_too_high")
    if int(getattr(latency_status, "ws_jitter_ms", 0) or 0) > max_ws_jitter_ms:
        reasons.append("ws_jitter_too_high")
    if _to_float(getattr(latency_status, "spread_ratio", 0.0), 0.0) > max_spread_ratio:
        reasons.append("spread_too_wide")
    if not reasons:
        reasons.append("other_danger")
    return reasons


def _should_apply_latency_guard_canary(
    *,
    strategy_id: str,
    position_tag: str,
    signal_strength: float,
    latency_status,
    signal_price: int,
    latest_price: int,
    danger_reasons: list[str] | None = None,
) -> tuple[bool, str]:
    if not bool(getattr(TRADING_RULES, "SCALP_LATENCY_GUARD_CANARY_ENABLED", False)):
        return False, "disabled"
    if str(strategy_id or "").upper() != "SCALPING":
        return False, "non_scalping"
    if getattr(latency_status, "quote_stale", False):
        return False, "quote_stale"

    reasons = danger_reasons or _latency_danger_reasons(latency_status)
    allowed_danger_reasons = _normalized_reason_set(
        getattr(TRADING_RULES, "SCALP_LATENCY_GUARD_CANARY_ALLOWED_DANGER_REASONS", ())
    )
    if allowed_danger_reasons and not (allowed_danger_reasons & _normalized_reason_set(reasons)):
        return False, "danger_reason_not_allowed"

    allow_tags = {
        str(tag).strip().upper()
        for tag in (getattr(TRADING_RULES, "SCALP_LATENCY_GUARD_CANARY_TAGS", ()) or ())
        if str(tag).strip()
    }
    normalized_tag = str(position_tag or "").strip().upper()
    if allow_tags and normalized_tag not in allow_tags:
        return False, "tag_not_allowed"

    min_signal = _to_float(getattr(TRADING_RULES, "SCALP_LATENCY_GUARD_CANARY_MIN_SIGNAL_SCORE", 85.0), 85.0)
    if _to_float(signal_strength, 0.0) < min_signal:
        return False, "low_signal"

    max_ws_age_ms = int(getattr(TRADING_RULES, "SCALP_LATENCY_GUARD_CANARY_MAX_WS_AGE_MS", 450) or 450)
    max_ws_jitter_ms = int(getattr(TRADING_RULES, "SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS", 260) or 260)
    max_spread_ratio = _to_float(getattr(TRADING_RULES, "SCALP_LATENCY_GUARD_CANARY_MAX_SPREAD_RATIO", 0.0100), 0.0100)
    if int(getattr(latency_status, "ws_age_ms", 0) or 0) > max_ws_age_ms:
        return False, "ws_age_too_high"
    if int(getattr(latency_status, "ws_jitter_ms", 0) or 0) > max_ws_jitter_ms:
        return False, "ws_jitter_too_high"
    if _to_float(getattr(latency_status, "spread_ratio", 0.0), 0.0) > max_spread_ratio:
        return False, "spread_too_wide"

    allowed_slippage = _ENTRY_POLICY._allowed_slippage(
        signal_price=signal_price,
        latest_price=latest_price,
        tick_limit=_CONFIG.fallback_allowed_slippage_ticks,
        pct_limit=_CONFIG.fallback_allowed_slippage_pct,
    )
    if not _ENTRY_POLICY._slippage_ok(signal_price, latest_price, allowed_slippage, "BUY"):
        return False, "fallback_slippage_exceeded"

    return True, "canary_applied"


def freeze_signal_reference(
    stock: dict[str, Any],
    *,
    signal_price: int,
    strategy_id: str,
    signal_time: datetime | None = None,
) -> tuple[int, datetime]:
    """Freeze the first trigger-time reference until the attempt resolves."""

    frozen_price = int(float(stock.get("entry_signal_price", 0) or 0))
    frozen_time = stock.get("entry_signal_time")
    frozen_strategy = str(stock.get("entry_signal_strategy_id", "") or "")

    if frozen_price > 0 and isinstance(frozen_time, datetime) and frozen_strategy == strategy_id:
        return frozen_price, frozen_time

    now = signal_time or datetime.now(UTC)
    stock["entry_signal_price"] = int(signal_price)
    stock["entry_signal_time"] = now
    stock["entry_signal_strategy_id"] = str(strategy_id)
    return int(signal_price), now


def clear_signal_reference(stock: dict[str, Any]) -> None:
    """Clear the frozen trigger-time reference after the attempt finishes."""

    for key in ("entry_signal_price", "entry_signal_time", "entry_signal_strategy_id"):
        stock.pop(key, None)


def evaluate_live_buy_entry(
    *,
    stock: dict[str, Any],
    code: str,
    ws_data: dict[str, Any] | None,
    strategy_id: str,
    planned_qty: int,
    signal_price: int,
    signal_strength: float = 0.0,
    signal_time: datetime | None = None,
    target_buy_price: int = 0,
) -> dict[str, Any]:
    """
    Evaluate whether the legacy live path should still attempt a new BUY.

    Notes:
    - Final truth still comes from the current websocket cache snapshot.
    - CAUTION submits the fallback bundle in the live engine as scout + main
      orders, while delayed receipts are reconciled through shared entry state.
    """

    latest_price = int(float((ws_data or {}).get("curr", 0) or 0))
    if latest_price <= 0 or planned_qty <= 0:
        return {
            "allowed": False,
            "decision": EntryDecision.REJECT_MARKET_CONDITION.value,
            "reason": "invalid_latest_price_or_qty",
            "latency_state": "DANGER",
            "order_price": 0,
        }

    frozen_price, frozen_time = freeze_signal_reference(
        stock,
        signal_price=int(signal_price),
        strategy_id=strategy_id,
        signal_time=signal_time,
    )
    best_ask, best_bid = _best_ask_bid_from_ws(ws_data)
    raw_received_at = (ws_data or {}).get("last_ws_update_ts")
    received_at = None if raw_received_at is None else float(raw_received_at)

    with _CACHE_LOCK:
        _CACHE.update(
            code,
            last_price=latest_price,
            best_ask=best_ask,
            best_bid=best_bid,
            received_at=received_at,
        )
        quote_health = _CACHE.get_quote_health(code)

    latency = _LATENCY_MONITOR.evaluate(
        ws_age_ms=quote_health.ws_age_ms,
        ws_jitter_ms=quote_health.ws_jitter_ms,
        order_rtt_avg_ms=0,
        order_rtt_p95_ms=0,
        quote_stale=quote_health.quote_stale,
        spread_ratio=quote_health.spread_ratio,
    )
    snapshot = build_signal_snapshot(
        symbol=code,
        strategy_id=strategy_id,
        signal_price=frozen_price,
        signal_strength=float(signal_strength),
        planned_qty=int(planned_qty),
        side="BUY",
        signal_time=frozen_time,
        context={
            "stock_name": stock.get("name"),
            "position_tag": stock.get("position_tag"),
        },
    )
    policy = _ENTRY_POLICY.evaluate(
        snapshot=snapshot,
        latency_status=latency,
        latest_price=latest_price,
        now=datetime.now(UTC),
    )

    effective_decision = policy.decision
    effective_reason = policy.reason
    latency_canary_applied = False
    latency_canary_reason = ""
    latency_danger_reasons = ",".join(_latency_danger_reasons(latency))
    if policy.decision == EntryDecision.REJECT_DANGER:
        canary_ok, canary_reason = _should_apply_latency_guard_canary(
            strategy_id=strategy_id,
            position_tag=str(stock.get("position_tag") or ""),
            signal_strength=float(signal_strength or 0.0),
            latency_status=latency,
            signal_price=frozen_price,
            latest_price=latest_price,
            danger_reasons=latency_danger_reasons.split(","),
        )
        if canary_ok:
            latency_canary_applied = True
            latency_canary_reason = canary_reason
            effective_decision = EntryDecision.ALLOW_FALLBACK
            effective_reason = "latency_guard_canary_override"
            log_info(
                f"[LATENCY_GUARD_CANARY] {stock.get('name')}({code}) "
                f"tag={stock.get('position_tag')} signal={float(signal_strength or 0.0):.1f} "
                f"ws_age_ms={latency.ws_age_ms} ws_jitter_ms={latency.ws_jitter_ms} "
                f"spread_ratio={latency.spread_ratio:.6f} "
                f"danger_reasons={latency_danger_reasons}"
            )
        else:
            latency_canary_reason = canary_reason

    computed_allowed_slippage = int(policy.computed_allowed_slippage or 0)
    if latency_canary_applied and computed_allowed_slippage <= 0:
        computed_allowed_slippage = _ENTRY_POLICY._allowed_slippage(
            signal_price=frozen_price,
            latest_price=latest_price,
            tick_limit=_CONFIG.fallback_allowed_slippage_ticks,
            pct_limit=_CONFIG.fallback_allowed_slippage_pct,
        )

    result = {
        "allowed": False,
        "decision": effective_decision.value,
        "reason": effective_reason,
        "latency_state": latency.state.value,
        "latest_price": latest_price,
        "signal_price": frozen_price,
        "signal_time": frozen_time,
        "computed_allowed_slippage": computed_allowed_slippage,
        "ws_age_ms": latency.ws_age_ms,
        "ws_jitter_ms": latency.ws_jitter_ms,
        "spread_ratio": latency.spread_ratio,
        "quote_stale": latency.quote_stale,
        "latency_danger_reasons": latency_danger_reasons,
        "target_buy_price": int(target_buy_price or 0),
        "order_price": 0,
        "latency_canary_applied": latency_canary_applied,
        "latency_canary_reason": latency_canary_reason,
    }

    if effective_decision == EntryDecision.ALLOW_NORMAL:
        defensive_order = _NORMAL_BUILDER.build(snapshot=snapshot, latest_price=latest_price)
        order_price = int(defensive_order.price)
        if int(target_buy_price or 0) > 0:
            order_price = min(order_price, int(target_buy_price))
        result["allowed"] = True
        result["mode"] = "normal"
        result["order_price"] = order_price
        result["orders"] = [
            {
                "tag": "normal",
                "qty": int(snapshot.planned_qty),
                "price": order_price,
                "order_type": defensive_order.order_type,
                "tif": defensive_order.tif,
            }
        ]
        return result

    if effective_decision == EntryDecision.ALLOW_FALLBACK:
        fallback_orders = _FALLBACK_BUILDER.build(
            snapshot=snapshot,
            latest_price=latest_price,
            best_ask=best_ask,
        )
        result["allowed"] = True
        result["mode"] = "fallback"
        result["orders"] = [
            {
                "tag": order.tag,
                "qty": int(order.qty),
                "price": int(order.price),
                "order_type": order.order_type,
                "tif": order.tif,
            }
            for order in fallback_orders
            if int(order.qty) > 0
        ]
        log_info(
            f"[LATENCY_ENTRY_CAUTION] {stock.get('name')}({code}) "
            f"fallback_bundle_ready orders={len(result['orders'])}"
        )
        return result

    result["mode"] = "reject"
    return result
