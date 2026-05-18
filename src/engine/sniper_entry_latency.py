"""Latency-aware entry adapter for the legacy sniper engine."""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from typing import Any

from src.trading.config.entry_config import EntryConfig
from src.trading.entry.entry_policy import EntryPolicy
from src.trading.entry.entry_types import EntryDecision
from src.trading.entry.latency_monitor import LatencyMonitor
from src.trading.entry.normal_entry_builder import NormalEntryBuilder
from src.trading.entry.orderbook_stability_observer import ORDERBOOK_STABILITY_OBSERVER
from src.trading.entry.signal_snapshot import build_signal_snapshot
from src.trading.market.market_data_cache import MarketDataCache
from src.trading.order.tick_utils import move_price_by_ticks
from src.utils.constants import TRADING_RULES
from src.utils.logger import log_info


def _build_entry_config() -> EntryConfig:
    return EntryConfig(
        max_ws_age_ms_for_caution=int(
            getattr(TRADING_RULES, "SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION", 700) or 700
        ),
        max_ws_jitter_ms_for_caution=int(
            getattr(TRADING_RULES, "SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION", 300) or 300
        ),
        max_spread_ratio_for_caution=float(
            getattr(TRADING_RULES, "SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION", 0.005) or 0.005
        ),
    )


_CONFIG = _build_entry_config()
_CACHE = MarketDataCache(stale_after_ms=_CONFIG.max_ws_age_ms_for_caution)
_CACHE_LOCK = threading.RLock()
_LATENCY_MONITOR = LatencyMonitor(_CONFIG)
_ENTRY_POLICY = EntryPolicy(_CONFIG)
_NORMAL_BUILDER = NormalEntryBuilder(_CONFIG)


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


def _compute_price_below_bid_bps(price: int, best_bid: int) -> int:
    try:
        normalized_price = int(price or 0)
        normalized_best_bid = int(best_bid or 0)
    except Exception:
        return 0
    if normalized_price <= 0 or normalized_best_bid <= 0 or normalized_price >= normalized_best_bid:
        return 0
    return int(round(((normalized_best_bid - normalized_price) / normalized_best_bid) * 10000))


def _can_apply_target_buy_price_cap(*, target_buy_price: int, best_bid: int) -> bool:
    if target_buy_price <= 0:
        return False
    if not bool(getattr(TRADING_RULES, "SCALPING_PRE_SUBMIT_PRICE_GUARD_ENABLED", True)):
        return True
    max_below_bid_bps = int(
        getattr(TRADING_RULES, "SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS", 80) or 80
    )
    return _compute_price_below_bid_bps(target_buy_price, best_bid) <= max_below_bid_bps


def _resolve_scalping_order_price(
    *,
    strategy_id: str,
    defensive_order_price: int,
    target_buy_price: int,
    best_bid: int,
) -> dict[str, Any]:
    target_price = int(target_buy_price or 0)
    defensive_price = int(defensive_order_price or 0)
    below_bid_bps = _compute_price_below_bid_bps(target_price, best_bid)
    resolver_enabled = bool(
        getattr(TRADING_RULES, "SCALPING_ENTRY_PRICE_RESOLVER_ENABLED", True)
    ) and str(strategy_id or "").upper() in {"SCALPING", "SCALP"}
    max_below_bid_bps = int(
        getattr(
            TRADING_RULES,
            "SCALPING_ENTRY_PRICE_RESOLVER_MAX_BELOW_BID_BPS",
            getattr(TRADING_RULES, "SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS", 80),
        )
        or 80
    )

    resolved = {
        "order_price": defensive_price,
        "price_resolution_reason": "defensive_order_price",
        "reference_target_applied": False,
        "reference_target_rejected_reason": "",
        "reference_target_below_bid_bps": below_bid_bps,
        "reference_target_max_below_bid_bps": max_below_bid_bps,
        "entry_price_resolver_enabled": resolver_enabled,
    }
    if target_price <= 0 or defensive_price <= 0:
        return resolved
    if target_price >= defensive_price:
        resolved["reference_target_rejected_reason"] = "not_better_than_defensive"
        return resolved

    if not resolver_enabled:
        if _can_apply_target_buy_price_cap(target_buy_price=target_price, best_bid=best_bid):
            resolved.update(
                order_price=target_price,
                price_resolution_reason="reference_target_cap",
                reference_target_applied=True,
            )
        else:
            resolved["reference_target_rejected_reason"] = "pre_submit_guard_bps_exceeded"
        return resolved

    if below_bid_bps <= max_below_bid_bps:
        resolved.update(
            order_price=target_price,
            price_resolution_reason="reference_target_cap",
            reference_target_applied=True,
        )
        return resolved

    resolved.update(
        price_resolution_reason="scalping_reference_rejected_defensive",
        reference_target_rejected_reason="target_below_bid_bps_exceeded",
    )
    return resolved


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value).replace(",", "").replace("+", "").strip())
    except Exception:
        return default


def _normalize_signal_score(signal_strength: Any) -> float:
    score = _to_float(signal_strength, 0.0)
    if 0.0 <= score <= 1.0:
        return score * 100.0
    return score


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
    if not bool(getattr(TRADING_RULES, "SCALP_LATENCY_FALLBACK_ENABLED", False)):
        return False, "latency_fallback_disabled"
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
    signal_score = _normalize_signal_score(signal_strength)
    if signal_score < min_signal:
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


def _should_apply_latency_spread_relief_canary(
    *,
    strategy_id: str,
    position_tag: str,
    signal_strength: float,
    latency_status,
    signal_price: int,
    latest_price: int,
    danger_reasons: list[str] | None = None,
) -> tuple[bool, str]:
    if not bool(getattr(TRADING_RULES, "SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED", False)):
        return False, "disabled"
    if str(strategy_id or "").upper() != "SCALPING":
        return False, "non_scalping"
    if getattr(latency_status, "quote_stale", False):
        return False, "quote_stale"

    normalized_reasons = _normalized_reason_set(danger_reasons or _latency_danger_reasons(latency_status))
    if normalized_reasons != {"spread_too_wide"}:
        return False, "spread_only_required"

    allow_tags = {
        str(tag).strip().upper()
        for tag in (getattr(TRADING_RULES, "SCALP_LATENCY_SPREAD_RELIEF_TAGS", ()) or ())
        if str(tag).strip()
    }
    normalized_tag = str(position_tag or "").strip().upper()
    if allow_tags and normalized_tag not in allow_tags:
        return False, "tag_not_allowed"

    min_signal = _to_float(getattr(TRADING_RULES, "SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE", 85.0), 85.0)
    signal_score = _normalize_signal_score(signal_strength)
    if signal_score < min_signal:
        return False, "low_signal"

    max_spread_ratio = _to_float(
        getattr(TRADING_RULES, "SCALP_LATENCY_SPREAD_RELIEF_MAX_SPREAD_RATIO", 0.0120),
        0.0120,
    )
    if _to_float(getattr(latency_status, "spread_ratio", 0.0), 0.0) > max_spread_ratio:
        return False, "spread_relief_limit_exceeded"

    allowed_slippage = _ENTRY_POLICY._allowed_slippage(
        signal_price=signal_price,
        latest_price=latest_price,
        tick_limit=_CONFIG.normal_allowed_slippage_ticks,
        pct_limit=_CONFIG.normal_allowed_slippage_pct,
    )
    if not _ENTRY_POLICY._slippage_ok(signal_price, latest_price, allowed_slippage, "BUY"):
        return False, "normal_slippage_exceeded"

    return True, "spread_relief_canary_applied"


def _should_apply_latency_quote_fresh_composite_canary(
    *,
    strategy_id: str,
    position_tag: str,
    signal_strength: float,
    latency_status,
    signal_price: int,
    latest_price: int,
    danger_reasons: list[str] | None = None,
) -> tuple[bool, str]:
    if not bool(getattr(TRADING_RULES, "SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED", False)):
        return False, "disabled"
    if str(strategy_id or "").upper() != "SCALPING":
        return False, "non_scalping"
    if getattr(latency_status, "quote_stale", False):
        return False, "quote_stale"

    normalized_reasons = _normalized_reason_set(danger_reasons or _latency_danger_reasons(latency_status))
    quote_fresh_reasons = {"other_danger", "ws_age_too_high", "ws_jitter_too_high", "spread_too_wide"}
    if not normalized_reasons or not normalized_reasons.issubset(quote_fresh_reasons):
        return False, "quote_fresh_family_required"

    allow_tags = {
        str(tag).strip().upper()
        for tag in (getattr(TRADING_RULES, "SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_TAGS", ()) or ())
        if str(tag).strip()
    }
    normalized_tag = str(position_tag or "").strip().upper()
    if allow_tags and normalized_tag not in allow_tags:
        return False, "tag_not_allowed"

    min_signal = _to_float(
        getattr(TRADING_RULES, "SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_MIN_SIGNAL_SCORE", 88.0),
        88.0,
    )
    signal_score = _normalize_signal_score(signal_strength)
    if signal_score < min_signal:
        return False, "low_signal"

    max_ws_age_ms = int(getattr(TRADING_RULES, "SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_MAX_WS_AGE_MS", 950) or 950)
    if int(getattr(latency_status, "ws_age_ms", 0) or 0) > max_ws_age_ms:
        return False, "ws_age_composite_limit_exceeded"

    max_ws_jitter_ms = int(
        getattr(TRADING_RULES, "SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_MAX_WS_JITTER_MS", 450) or 450
    )
    if int(getattr(latency_status, "ws_jitter_ms", 0) or 0) > max_ws_jitter_ms:
        return False, "ws_jitter_composite_limit_exceeded"

    max_spread_ratio = _to_float(
        getattr(TRADING_RULES, "SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_MAX_SPREAD_RATIO", 0.0075),
        0.0075,
    )
    if _to_float(getattr(latency_status, "spread_ratio", 0.0), 0.0) > max_spread_ratio:
        return False, "spread_composite_limit_exceeded"

    allowed_slippage = _ENTRY_POLICY._allowed_slippage(
        signal_price=signal_price,
        latest_price=latest_price,
        tick_limit=_CONFIG.normal_allowed_slippage_ticks,
        pct_limit=_CONFIG.normal_allowed_slippage_pct,
    )
    if not _ENTRY_POLICY._slippage_ok(signal_price, latest_price, allowed_slippage, "BUY"):
        return False, "normal_slippage_exceeded"

    return True, "quote_fresh_composite_canary_applied"


def _should_apply_latency_signal_quality_quote_composite_canary(
    *,
    strategy_id: str,
    position_tag: str,
    signal_strength: float,
    latest_strength: float,
    buy_pressure_10t: float,
    latency_status,
    signal_price: int,
    latest_price: int,
    danger_reasons: list[str] | None = None,
) -> tuple[bool, str]:
    if not bool(
        getattr(TRADING_RULES, "SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED", False)
    ):
        return False, "disabled"
    if str(strategy_id or "").upper() != "SCALPING":
        return False, "non_scalping"
    if getattr(latency_status, "quote_stale", False):
        return False, "quote_stale"

    normalized_reasons = _normalized_reason_set(danger_reasons or _latency_danger_reasons(latency_status))
    quote_fresh_reasons = {"other_danger", "ws_age_too_high", "ws_jitter_too_high", "spread_too_wide"}
    if not normalized_reasons or not normalized_reasons.issubset(quote_fresh_reasons):
        return False, "quote_fresh_family_required"

    allow_tags = {
        str(tag).strip().upper()
        for tag in (
            getattr(TRADING_RULES, "SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_TAGS", ()) or ()
        )
        if str(tag).strip()
    }
    normalized_tag = str(position_tag or "").strip().upper()
    if allow_tags and normalized_tag not in allow_tags:
        return False, "tag_not_allowed"

    min_signal = _to_float(
        getattr(TRADING_RULES, "SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_MIN_SIGNAL_SCORE", 90.0),
        90.0,
    )
    signal_score = _normalize_signal_score(signal_strength)
    if signal_score < min_signal:
        return False, "low_signal"

    min_strength = _to_float(
        getattr(TRADING_RULES, "SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_MIN_STRENGTH", 110.0),
        110.0,
    )
    if _to_float(latest_strength, 0.0) < min_strength:
        return False, "low_strength"

    min_buy_pressure = _to_float(
        getattr(TRADING_RULES, "SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_MIN_BUY_PRESSURE", 65.0),
        65.0,
    )
    if _to_float(buy_pressure_10t, 0.0) < min_buy_pressure:
        return False, "low_buy_pressure"

    max_ws_age_ms = int(
        getattr(TRADING_RULES, "SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_MAX_WS_AGE_MS", 1200)
        or 1200
    )
    if int(getattr(latency_status, "ws_age_ms", 0) or 0) > max_ws_age_ms:
        return False, "ws_age_signal_quality_limit_exceeded"

    max_ws_jitter_ms = int(
        getattr(TRADING_RULES, "SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_MAX_WS_JITTER_MS", 500)
        or 500
    )
    if int(getattr(latency_status, "ws_jitter_ms", 0) or 0) > max_ws_jitter_ms:
        return False, "ws_jitter_signal_quality_limit_exceeded"

    max_spread_ratio = _to_float(
        getattr(TRADING_RULES, "SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_MAX_SPREAD_RATIO", 0.0085),
        0.0085,
    )
    if _to_float(getattr(latency_status, "spread_ratio", 0.0), 0.0) > max_spread_ratio:
        return False, "spread_signal_quality_limit_exceeded"

    allowed_slippage = _ENTRY_POLICY._allowed_slippage(
        signal_price=signal_price,
        latest_price=latest_price,
        tick_limit=_CONFIG.normal_allowed_slippage_ticks,
        pct_limit=_CONFIG.normal_allowed_slippage_pct,
    )
    if not _ENTRY_POLICY._slippage_ok(signal_price, latest_price, allowed_slippage, "BUY"):
        return False, "normal_slippage_exceeded"

    return True, "signal_quality_quote_composite_canary_applied"


def _should_apply_latency_mechanical_momentum_relief_canary(
    *,
    strategy_id: str,
    position_tag: str,
    signal_strength: float,
    latest_strength: float,
    buy_pressure_10t: float,
    latency_status,
    signal_price: int,
    latest_price: int,
    danger_reasons: list[str] | None = None,
) -> tuple[bool, str]:
    if not bool(
        getattr(TRADING_RULES, "SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED", False)
    ):
        return False, "disabled"
    if str(strategy_id or "").upper() != "SCALPING":
        return False, "non_scalping"
    if getattr(latency_status, "quote_stale", False):
        return False, "quote_stale"

    normalized_reasons = _normalized_reason_set(danger_reasons or _latency_danger_reasons(latency_status))
    quote_fresh_reasons = {"other_danger", "ws_age_too_high", "ws_jitter_too_high", "spread_too_wide"}
    if not normalized_reasons or not normalized_reasons.issubset(quote_fresh_reasons):
        return False, "quote_fresh_family_required"

    allow_tags = {
        str(tag).strip().upper()
        for tag in (getattr(TRADING_RULES, "SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_TAGS", ()) or ())
        if str(tag).strip()
    }
    normalized_tag = str(position_tag or "").strip().upper()
    if allow_tags and normalized_tag not in allow_tags:
        return False, "tag_not_allowed"

    max_signal = _to_float(
        getattr(TRADING_RULES, "SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_SIGNAL_SCORE", 75.0),
        75.0,
    )
    signal_score = _normalize_signal_score(signal_strength)
    if signal_score > max_signal:
        return False, "signal_not_mechanical"

    min_strength = _to_float(
        getattr(TRADING_RULES, "SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MIN_STRENGTH", 110.0),
        110.0,
    )
    if _to_float(latest_strength, 0.0) < min_strength:
        return False, "low_strength"

    min_buy_pressure = _to_float(
        getattr(TRADING_RULES, "SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MIN_BUY_PRESSURE", 50.0),
        50.0,
    )
    if _to_float(buy_pressure_10t, 0.0) < min_buy_pressure:
        return False, "low_buy_pressure"

    max_ws_age_ms = int(
        getattr(TRADING_RULES, "SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_WS_AGE_MS", 1200) or 1200
    )
    if int(getattr(latency_status, "ws_age_ms", 0) or 0) > max_ws_age_ms:
        return False, "ws_age_mechanical_momentum_limit_exceeded"

    max_ws_jitter_ms = int(
        getattr(TRADING_RULES, "SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_WS_JITTER_MS", 500) or 500
    )
    if int(getattr(latency_status, "ws_jitter_ms", 0) or 0) > max_ws_jitter_ms:
        return False, "ws_jitter_mechanical_momentum_limit_exceeded"

    max_spread_ratio = _to_float(
        getattr(TRADING_RULES, "SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_SPREAD_RATIO", 0.0085),
        0.0085,
    )
    if _to_float(getattr(latency_status, "spread_ratio", 0.0), 0.0) > max_spread_ratio:
        return False, "spread_mechanical_momentum_limit_exceeded"

    allowed_slippage = _ENTRY_POLICY._allowed_slippage(
        signal_price=signal_price,
        latest_price=latest_price,
        tick_limit=_CONFIG.normal_allowed_slippage_ticks,
        pct_limit=_CONFIG.normal_allowed_slippage_pct,
    )
    if not _ENTRY_POLICY._slippage_ok(signal_price, latest_price, allowed_slippage, "BUY"):
        return False, "normal_slippage_exceeded"

    return True, "mechanical_momentum_relief_canary_applied"


def _should_apply_latency_ws_jitter_relief_canary(
    *,
    strategy_id: str,
    position_tag: str,
    signal_strength: float,
    latency_status,
    signal_price: int,
    latest_price: int,
    danger_reasons: list[str] | None = None,
) -> tuple[bool, str]:
    if not bool(getattr(TRADING_RULES, "SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED", False)):
        return False, "disabled"
    if str(strategy_id or "").upper() != "SCALPING":
        return False, "non_scalping"
    if getattr(latency_status, "quote_stale", False):
        return False, "quote_stale"

    normalized_reasons = _normalized_reason_set(danger_reasons or _latency_danger_reasons(latency_status))
    if normalized_reasons != {"ws_jitter_too_high"}:
        return False, "ws_jitter_only_required"

    allow_tags = {
        str(tag).strip().upper()
        for tag in (getattr(TRADING_RULES, "SCALP_LATENCY_WS_JITTER_RELIEF_TAGS", ()) or ())
        if str(tag).strip()
    }
    normalized_tag = str(position_tag or "").strip().upper()
    if allow_tags and normalized_tag not in allow_tags:
        return False, "tag_not_allowed"

    min_signal = _to_float(getattr(TRADING_RULES, "SCALP_LATENCY_WS_JITTER_RELIEF_MIN_SIGNAL_SCORE", 85.0), 85.0)
    signal_score = _normalize_signal_score(signal_strength)
    if signal_score < min_signal:
        return False, "low_signal"

    max_ws_age_ms = int(getattr(TRADING_RULES, "SCALP_LATENCY_WS_JITTER_RELIEF_MAX_WS_AGE_MS", 450) or 450)
    if int(getattr(latency_status, "ws_age_ms", 0) or 0) > max_ws_age_ms:
        return False, "ws_age_limit_exceeded"

    max_ws_jitter_ms = int(getattr(TRADING_RULES, "SCALP_LATENCY_WS_JITTER_RELIEF_MAX_WS_JITTER_MS", 360) or 360)
    if int(getattr(latency_status, "ws_jitter_ms", 0) or 0) > max_ws_jitter_ms:
        return False, "ws_jitter_relief_limit_exceeded"

    max_spread_ratio = _to_float(
        getattr(TRADING_RULES, "SCALP_LATENCY_WS_JITTER_RELIEF_MAX_SPREAD_RATIO", 0.0050),
        0.0050,
    )
    if _to_float(getattr(latency_status, "spread_ratio", 0.0), 0.0) > max_spread_ratio:
        return False, "spread_limit_exceeded"

    allowed_slippage = _ENTRY_POLICY._allowed_slippage(
        signal_price=signal_price,
        latest_price=latest_price,
        tick_limit=_CONFIG.normal_allowed_slippage_ticks,
        pct_limit=_CONFIG.normal_allowed_slippage_pct,
    )
    if not _ENTRY_POLICY._slippage_ok(signal_price, latest_price, allowed_slippage, "BUY"):
        return False, "normal_slippage_exceeded"

    return True, "ws_jitter_relief_canary_applied"


def _should_apply_latency_other_danger_relief_canary(
    *,
    strategy_id: str,
    position_tag: str,
    signal_strength: float,
    latency_status,
    signal_price: int,
    latest_price: int,
    danger_reasons: list[str] | None = None,
) -> tuple[bool, str]:
    if not bool(getattr(TRADING_RULES, "SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED", False)):
        return False, "disabled"
    if str(strategy_id or "").upper() != "SCALPING":
        return False, "non_scalping"
    if getattr(latency_status, "quote_stale", False):
        return False, "quote_stale"

    normalized_reasons = _normalized_reason_set(danger_reasons or _latency_danger_reasons(latency_status))
    if normalized_reasons != {"other_danger"}:
        return False, "other_danger_only_required"

    allow_tags = {
        str(tag).strip().upper()
        for tag in (getattr(TRADING_RULES, "SCALP_LATENCY_OTHER_DANGER_RELIEF_TAGS", ()) or ())
        if str(tag).strip()
    }
    normalized_tag = str(position_tag or "").strip().upper()
    if allow_tags and normalized_tag not in allow_tags:
        return False, "tag_not_allowed"

    min_signal = _to_float(getattr(TRADING_RULES, "SCALP_LATENCY_OTHER_DANGER_RELIEF_MIN_SIGNAL_SCORE", 90.0), 90.0)
    signal_score = _normalize_signal_score(signal_strength)
    if signal_score < min_signal:
        return False, "low_signal"

    max_ws_age_ms = int(getattr(TRADING_RULES, "SCALP_LATENCY_OTHER_DANGER_RELIEF_MAX_WS_AGE_MS", 400) or 400)
    if int(getattr(latency_status, "ws_age_ms", 0) or 0) > max_ws_age_ms:
        return False, "ws_age_limit_exceeded"

    max_ws_jitter_ms = int(
        getattr(TRADING_RULES, "SCALP_LATENCY_OTHER_DANGER_RELIEF_MAX_WS_JITTER_MS", 80) or 80
    )
    if int(getattr(latency_status, "ws_jitter_ms", 0) or 0) > max_ws_jitter_ms:
        return False, "ws_jitter_limit_exceeded"

    max_spread_ratio = _to_float(
        getattr(TRADING_RULES, "SCALP_LATENCY_OTHER_DANGER_RELIEF_MAX_SPREAD_RATIO", 0.0080),
        0.0080,
    )
    if _to_float(getattr(latency_status, "spread_ratio", 0.0), 0.0) > max_spread_ratio:
        return False, "spread_limit_exceeded"

    allowed_slippage = _ENTRY_POLICY._allowed_slippage(
        signal_price=signal_price,
        latest_price=latest_price,
        tick_limit=_CONFIG.normal_allowed_slippage_ticks,
        pct_limit=_CONFIG.normal_allowed_slippage_pct,
    )
    if not _ENTRY_POLICY._slippage_ok(signal_price, latest_price, allowed_slippage, "BUY"):
        return False, "normal_slippage_exceeded"

    return True, "other_danger_relief_canary_applied"


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
        quote_fresh_composite_ok, quote_fresh_composite_reason = _should_apply_latency_quote_fresh_composite_canary(
            strategy_id=strategy_id,
            position_tag=str(stock.get("position_tag") or ""),
            signal_strength=float(signal_strength or 0.0),
            latency_status=latency,
            signal_price=frozen_price,
            latest_price=latest_price,
            danger_reasons=latency_danger_reasons.split(","),
        )
        if quote_fresh_composite_ok:
            latency_canary_applied = True
            latency_canary_reason = quote_fresh_composite_reason
            effective_decision = EntryDecision.ALLOW_NORMAL
            effective_reason = "latency_quote_fresh_composite_normal_override"
            log_info(
                f"[LATENCY_QUOTE_FRESH_COMPOSITE_CANARY] {stock.get('name')}({code}) "
                f"tag={stock.get('position_tag')} signal_score={_normalize_signal_score(signal_strength):.1f} "
                f"ws_age_ms={latency.ws_age_ms} ws_jitter_ms={latency.ws_jitter_ms} "
                f"spread_ratio={latency.spread_ratio:.6f} "
                f"danger_reasons={latency_danger_reasons}"
            )
        else:
            latency_canary_reason = quote_fresh_composite_reason

    if policy.decision == EntryDecision.REJECT_DANGER and effective_decision == EntryDecision.REJECT_DANGER:
        signal_quality_ok, signal_quality_reason = _should_apply_latency_signal_quality_quote_composite_canary(
            strategy_id=strategy_id,
            position_tag=str(stock.get("position_tag") or ""),
            signal_strength=float(signal_strength or 0.0),
            latest_strength=_to_float((ws_data or {}).get("v_pw", stock.get("latest_strength", 0.0)), 0.0),
            buy_pressure_10t=_to_float((ws_data or {}).get("buy_ratio", stock.get("buy_pressure_10t", 0.0)), 0.0),
            latency_status=latency,
            signal_price=frozen_price,
            latest_price=latest_price,
            danger_reasons=latency_danger_reasons.split(","),
        )
        if signal_quality_ok:
            latency_canary_applied = True
            latency_canary_reason = signal_quality_reason
            effective_decision = EntryDecision.ALLOW_NORMAL
            effective_reason = "latency_signal_quality_quote_composite_normal_override"
            log_info(
                f"[LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY] {stock.get('name')}({code}) "
                f"tag={stock.get('position_tag')} signal_score={_normalize_signal_score(signal_strength):.1f} "
                f"strength={_to_float((ws_data or {}).get('v_pw', stock.get('latest_strength', 0.0)), 0.0):.1f} "
                f"buy_pressure={_to_float((ws_data or {}).get('buy_ratio', stock.get('buy_pressure_10t', 0.0)), 0.0):.1f} "
                f"ws_age_ms={latency.ws_age_ms} ws_jitter_ms={latency.ws_jitter_ms} "
                f"spread_ratio={latency.spread_ratio:.6f} "
                f"danger_reasons={latency_danger_reasons}"
            )
        else:
            if not latency_canary_reason or latency_canary_reason == "disabled":
                latency_canary_reason = signal_quality_reason

    if policy.decision == EntryDecision.REJECT_DANGER and effective_decision == EntryDecision.REJECT_DANGER:
        other_danger_relief_ok, other_danger_relief_reason = _should_apply_latency_other_danger_relief_canary(
            strategy_id=strategy_id,
            position_tag=str(stock.get("position_tag") or ""),
            signal_strength=float(signal_strength or 0.0),
            latency_status=latency,
            signal_price=frozen_price,
            latest_price=latest_price,
            danger_reasons=latency_danger_reasons.split(","),
        )
        if other_danger_relief_ok:
            latency_canary_applied = True
            latency_canary_reason = other_danger_relief_reason
            effective_decision = EntryDecision.ALLOW_NORMAL
            effective_reason = "latency_other_danger_relief_normal_override"
            log_info(
                f"[LATENCY_OTHER_DANGER_RELIEF_CANARY] {stock.get('name')}({code}) "
                f"tag={stock.get('position_tag')} signal_score={_normalize_signal_score(signal_strength):.1f} "
                f"ws_age_ms={latency.ws_age_ms} ws_jitter_ms={latency.ws_jitter_ms} "
                f"spread_ratio={latency.spread_ratio:.6f} "
                f"danger_reasons={latency_danger_reasons}"
            )
        else:
            if not latency_canary_reason or latency_canary_reason == "disabled":
                latency_canary_reason = other_danger_relief_reason

    if policy.decision == EntryDecision.REJECT_DANGER and effective_decision == EntryDecision.REJECT_DANGER:
        ws_jitter_relief_ok, ws_jitter_relief_reason = _should_apply_latency_ws_jitter_relief_canary(
            strategy_id=strategy_id,
            position_tag=str(stock.get("position_tag") or ""),
            signal_strength=float(signal_strength or 0.0),
            latency_status=latency,
            signal_price=frozen_price,
            latest_price=latest_price,
            danger_reasons=latency_danger_reasons.split(","),
        )
        if ws_jitter_relief_ok:
            latency_canary_applied = True
            latency_canary_reason = ws_jitter_relief_reason
            effective_decision = EntryDecision.ALLOW_NORMAL
            effective_reason = "latency_ws_jitter_relief_normal_override"
            log_info(
                f"[LATENCY_WS_JITTER_RELIEF_CANARY] {stock.get('name')}({code}) "
                f"tag={stock.get('position_tag')} signal_score={_normalize_signal_score(signal_strength):.1f} "
                f"ws_age_ms={latency.ws_age_ms} ws_jitter_ms={latency.ws_jitter_ms} "
                f"spread_ratio={latency.spread_ratio:.6f} "
                f"danger_reasons={latency_danger_reasons}"
            )
        else:
            if not latency_canary_reason or latency_canary_reason == "disabled":
                latency_canary_reason = ws_jitter_relief_reason

    if policy.decision == EntryDecision.REJECT_DANGER and effective_decision == EntryDecision.REJECT_DANGER:
        spread_relief_ok, spread_relief_reason = _should_apply_latency_spread_relief_canary(
            strategy_id=strategy_id,
            position_tag=str(stock.get("position_tag") or ""),
            signal_strength=float(signal_strength or 0.0),
            latency_status=latency,
            signal_price=frozen_price,
            latest_price=latest_price,
            danger_reasons=latency_danger_reasons.split(","),
        )
        if spread_relief_ok:
            latency_canary_applied = True
            latency_canary_reason = spread_relief_reason
            effective_decision = EntryDecision.ALLOW_NORMAL
            effective_reason = "latency_spread_relief_normal_override"
            log_info(
                f"[LATENCY_SPREAD_RELIEF_CANARY] {stock.get('name')}({code}) "
                f"tag={stock.get('position_tag')} signal_score={_normalize_signal_score(signal_strength):.1f} "
                f"ws_age_ms={latency.ws_age_ms} ws_jitter_ms={latency.ws_jitter_ms} "
                f"spread_ratio={latency.spread_ratio:.6f} "
                f"danger_reasons={latency_danger_reasons}"
            )
        else:
            if not latency_canary_reason or latency_canary_reason == "disabled":
                latency_canary_reason = spread_relief_reason

    if policy.decision == EntryDecision.REJECT_DANGER and effective_decision == EntryDecision.REJECT_DANGER:
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
            effective_decision = EntryDecision.REJECT_MARKET_CONDITION
            effective_reason = "latency_fallback_deprecated"
            log_info(
                f"[LATENCY_GUARD_CANARY] {stock.get('name')}({code}) "
                f"tag={stock.get('position_tag')} signal_score={_normalize_signal_score(signal_strength):.1f} "
                f"ws_age_ms={latency.ws_age_ms} ws_jitter_ms={latency.ws_jitter_ms} "
                f"spread_ratio={latency.spread_ratio:.6f} "
                f"danger_reasons={latency_danger_reasons}"
            )
        else:
            if not latency_canary_reason or latency_canary_reason == "disabled":
                latency_canary_reason = canary_reason

    if policy.decision == EntryDecision.REJECT_DANGER and effective_decision == EntryDecision.REJECT_DANGER:
        mechanical_momentum_ok, mechanical_momentum_reason = _should_apply_latency_mechanical_momentum_relief_canary(
            strategy_id=strategy_id,
            position_tag=str(stock.get("position_tag") or ""),
            signal_strength=float(signal_strength or 0.0),
            latest_strength=_to_float((ws_data or {}).get("v_pw", stock.get("latest_strength", 0.0)), 0.0),
            buy_pressure_10t=_to_float((ws_data or {}).get("buy_ratio", stock.get("buy_pressure_10t", 0.0)), 0.0),
            latency_status=latency,
            signal_price=frozen_price,
            latest_price=latest_price,
            danger_reasons=latency_danger_reasons.split(","),
        )
        if mechanical_momentum_ok:
            latency_canary_applied = True
            latency_canary_reason = mechanical_momentum_reason
            effective_decision = EntryDecision.ALLOW_NORMAL
            effective_reason = "latency_mechanical_momentum_relief_normal_override"
            log_info(
                f"[LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY] {stock.get('name')}({code}) "
                f"tag={stock.get('position_tag')} signal_score={_normalize_signal_score(signal_strength):.1f} "
                f"strength={_to_float((ws_data or {}).get('v_pw', stock.get('latest_strength', 0.0)), 0.0):.1f} "
                f"buy_pressure={_to_float((ws_data or {}).get('buy_ratio', stock.get('buy_pressure_10t', 0.0)), 0.0):.1f} "
                f"ws_age_ms={latency.ws_age_ms} ws_jitter_ms={latency.ws_jitter_ms} "
                f"spread_ratio={latency.spread_ratio:.6f} "
                f"danger_reasons={latency_danger_reasons}"
            )
        else:
            if not latency_canary_reason or latency_canary_reason in {"disabled", "latency_fallback_disabled"}:
                latency_canary_reason = mechanical_momentum_reason

    computed_allowed_slippage = int(policy.computed_allowed_slippage or 0)
    if latency_canary_applied and computed_allowed_slippage <= 0:
        tick_limit = _CONFIG.fallback_allowed_slippage_ticks
        pct_limit = _CONFIG.fallback_allowed_slippage_pct
        if effective_decision == EntryDecision.ALLOW_NORMAL:
            tick_limit = _CONFIG.normal_allowed_slippage_ticks
            pct_limit = _CONFIG.normal_allowed_slippage_pct
        computed_allowed_slippage = _ENTRY_POLICY._allowed_slippage(
            signal_price=frozen_price,
            latest_price=latest_price,
            tick_limit=tick_limit,
            pct_limit=pct_limit,
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
        "entry_price_guard": "none",
        "entry_price_defensive_ticks": 0,
        "normal_defensive_order_price": 0,
        "latency_guarded_order_price": 0,
        "counterfactual_order_price_1tick": 0,
        "price_resolution_reason": "none",
        "reference_target_applied": False,
        "reference_target_rejected_reason": "",
        "reference_target_below_bid_bps": 0,
        "reference_target_max_below_bid_bps": int(
            getattr(
                TRADING_RULES,
                "SCALPING_ENTRY_PRICE_RESOLVER_MAX_BELOW_BID_BPS",
                getattr(TRADING_RULES, "SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS", 80),
            )
            or 80
        ),
        "entry_price_resolver_enabled": bool(
            getattr(TRADING_RULES, "SCALPING_ENTRY_PRICE_RESOLVER_ENABLED", True)
        ),
        "latency_canary_applied": latency_canary_applied,
        "latency_canary_reason": latency_canary_reason,
        "orderbook_stability": ORDERBOOK_STABILITY_OBSERVER.snapshot(code),
    }

    if effective_decision == EntryDecision.ALLOW_NORMAL:
        is_latency_override = latency.state.value == "DANGER" and latency_canary_applied
        defensive_ticks = (
            _CONFIG.latency_override_defensive_ticks
            if is_latency_override
            else _CONFIG.normal_defensive_ticks
        )
        entry_price_guard = (
            "latency_danger_override_defensive"
            if is_latency_override
            else "normal_defensive"
        )
        defensive_order = _NORMAL_BUILDER.build(
            snapshot=snapshot,
            latest_price=latest_price,
            defensive_ticks=defensive_ticks,
        )
        normal_defensive_order_price = move_price_by_ticks(latest_price, -_CONFIG.normal_defensive_ticks)
        latency_guarded_order_price = int(defensive_order.price)
        counterfactual_order_price_1tick = normal_defensive_order_price
        order_price = int(defensive_order.price)
        price_resolution = _resolve_scalping_order_price(
            strategy_id=strategy_id,
            defensive_order_price=order_price,
            target_buy_price=int(target_buy_price or 0),
            best_bid=best_bid,
        )
        if int(target_buy_price or 0) > 0:
            target_cap = int(target_buy_price)
            counterfactual_order_price_1tick = min(counterfactual_order_price_1tick, target_cap)
            order_price = int(price_resolution.get("order_price", order_price) or order_price)
        result["allowed"] = True
        result["mode"] = "normal"
        result["order_price"] = order_price
        result["entry_price_guard"] = entry_price_guard
        result["entry_price_defensive_ticks"] = int(defensive_ticks)
        result["normal_defensive_order_price"] = int(normal_defensive_order_price)
        result["latency_guarded_order_price"] = int(latency_guarded_order_price)
        result["counterfactual_order_price_1tick"] = int(counterfactual_order_price_1tick)
        result["price_resolution_reason"] = price_resolution.get("price_resolution_reason", "defensive_order_price")
        result["reference_target_applied"] = bool(price_resolution.get("reference_target_applied"))
        result["reference_target_rejected_reason"] = price_resolution.get("reference_target_rejected_reason", "")
        result["reference_target_below_bid_bps"] = int(price_resolution.get("reference_target_below_bid_bps", 0) or 0)
        result["reference_target_max_below_bid_bps"] = int(
            price_resolution.get("reference_target_max_below_bid_bps", 0) or 0
        )
        result["entry_price_resolver_enabled"] = bool(price_resolution.get("entry_price_resolver_enabled"))
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

    result["mode"] = "reject"
    return result
