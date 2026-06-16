"""Latency-aware entry adapter for the legacy sniper engine."""

from __future__ import annotations

import os
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
from src.trading.order.tick_utils import clamp_price_to_tick
from src.trading.order.tick_utils import get_tick_size
from src.trading.order.tick_utils import move_price_by_ticks
from src.trading.order.tick_utils import move_price_down_by_bps
from src.utils import constants as constants_module
from src.utils.constants import TRADING_RULES
from src.utils.logger import log_info


def _build_entry_config() -> EntryConfig:
    return EntryConfig(
        normal_defensive_ticks=max(
            1,
            int(getattr(TRADING_RULES, "SCALPING_NORMAL_DEFENSIVE_TICKS", 1) or 1),
        ),
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


def _compute_spread_ticks(best_ask: int, best_bid: int) -> int:
    if best_ask <= 0 or best_bid <= 0 or best_ask <= best_bid:
        return 0
    tick_size = get_tick_size(best_bid)
    if tick_size <= 0:
        return 0
    return max(0, int(round((best_ask - best_bid) / tick_size)))


def _conditional_real_1tick_context(ws_data: dict[str, Any] | None, *, best_ask: int, best_bid: int) -> dict[str, Any]:
    ws = ws_data or {}
    orderbook = ws.get("orderbook") or {}
    asks = orderbook.get("asks") or []
    bids = orderbook.get("bids") or []
    ask_depth = _to_float(ws.get("ask_tot"), 0.0)
    bid_depth = _to_float(ws.get("bid_tot"), 0.0)
    if ask_depth <= 0 and asks:
        ask_depth = sum(_to_float((level or {}).get("volume"), 0.0) for level in asks[:3])
    if bid_depth <= 0 and bids:
        bid_depth = sum(_to_float((level or {}).get("volume"), 0.0) for level in bids[:3])

    buy_volume = _to_float(ws.get("buy_exec_volume"), 0.0)
    sell_volume = _to_float(ws.get("sell_exec_volume"), 0.0)
    total_exec_volume = buy_volume + sell_volume
    buy_ratio = _to_float(ws.get("buy_ratio"), 0.0)
    if total_exec_volume > 0:
        buy_ratio = (buy_volume / total_exec_volume) * 100.0
    net_buy_exec_volume = _to_float(ws.get("net_buy_exec_volume"), buy_volume - sell_volume)

    ofi_norm = max(
        _to_float(ws.get("orderbook_micro_ofi_norm"), -999.0),
        _to_float(ws.get("ofi_norm"), -999.0),
        _to_float(ws.get("ofi"), -999.0),
    )
    bid_ask_ratio = (bid_depth / ask_depth) if ask_depth > 0 and bid_depth > 0 else 0.0
    spread_ticks = _compute_spread_ticks(best_ask, best_bid)

    min_buy_ratio = float(getattr(TRADING_RULES, "SCALPING_CONDITIONAL_1TICK_MIN_BUY_RATIO", 60.0) or 60.0)
    min_ofi_norm = float(getattr(TRADING_RULES, "SCALPING_CONDITIONAL_1TICK_MIN_OFI_NORM", 0.45) or 0.45)
    min_bid_ask_ratio = float(
        getattr(TRADING_RULES, "SCALPING_CONDITIONAL_1TICK_MIN_BID_ASK_RATIO", 1.20) or 1.20
    )
    buy_pressure_ok = net_buy_exec_volume > 0 and buy_ratio >= min_buy_ratio
    ofi_ok = ofi_norm >= min_ofi_norm
    depth_ok = bid_depth > 0 and ask_depth > 0 and bid_ask_ratio >= min_bid_ask_ratio

    return {
        "spread_ticks": spread_ticks,
        "buy_ratio": round(float(buy_ratio), 6),
        "net_buy_exec_volume": int(net_buy_exec_volume),
        "ofi_norm": None if ofi_norm == -999.0 else round(float(ofi_norm), 6),
        "bid_ask_depth_ratio": round(float(bid_ask_ratio), 6),
        "buy_pressure_ok": buy_pressure_ok,
        "ofi_ok": ofi_ok,
        "depth_ok": depth_ok,
        "eligible": spread_ticks == 1 and (buy_pressure_ok or ofi_ok or depth_ok),
    }


def _conditional_real_1tick_enabled(strategy_id: str) -> bool:
    if str(strategy_id or "").upper() not in {"SCALPING", "SCALP"}:
        return False
    return bool(getattr(TRADING_RULES, "SCALPING_CONDITIONAL_1TICK_REAL_ENABLED", True))


def _defense_mode_is_percent_bps() -> bool:
    mode = str(getattr(TRADING_RULES, "SCALPING_ENTRY_PRICE_DEFENSE_MODE", "tick") or "").strip().lower()
    return mode == "percent_bps"


def _normal_defensive_bps() -> int:
    return max(1, int(getattr(TRADING_RULES, "SCALPING_NORMAL_DEFENSIVE_BPS", 50) or 50))


def _conditional_strong_defensive_bps() -> int:
    return max(1, int(getattr(TRADING_RULES, "SCALPING_CONDITIONAL_STRONG_DEFENSIVE_BPS", 20) or 20))


def _normal_favorable_defensive_bps() -> int:
    return max(1, int(getattr(TRADING_RULES, "SCALPING_NORMAL_FAVORABLE_DEFENSIVE_BPS", 35) or 35))


def _normal_weak_defensive_bps() -> int:
    return max(1, int(getattr(TRADING_RULES, "SCALPING_NORMAL_WEAK_DEFENSIVE_BPS", 65) or 65))


def _aggressive_entry_price_override_enabled() -> bool:
    return bool(getattr(TRADING_RULES, "SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_ENABLED", False))


def _dynamic_entry_price_resolver_live_selected() -> bool:
    return bool(getattr(TRADING_RULES, "DYNAMIC_ENTRY_PRICE_RESOLVER_LIVE_SELECTED", False)) or bool(
        getattr(TRADING_RULES, "ENTRY_PRICE_LIVE_TUNING_SELECTED", False)
    )


def _aggressive_entry_price_override_types() -> set[str]:
    raw = str(
        getattr(
            TRADING_RULES,
            "SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_TYPES",
            "defensive_missed_upside_v1,reference_target_cap_missed_upside_v1",
        )
        or ""
    )
    return {item.strip() for item in raw.split(",") if item.strip()}


def _micro_state_from_inputs(stock: dict[str, Any] | None, ws_data: dict[str, Any] | None) -> str:
    for source in (stock, ws_data):
        if isinstance(source, dict):
            state = str(source.get("orderbook_micro_state") or source.get("micro_state") or "").strip().lower()
            if state:
                return state
    return "neutral"


def _weak_pullback_like_context(stock: dict[str, Any] | None, positive_signal_count: int) -> bool:
    if positive_signal_count > 0:
        return False
    context = stock.get("scalp_pre_ai_gate_context") if isinstance(stock, dict) else {}
    strength = context.get("strength_momentum") if isinstance(context, dict) else {}
    strength = strength if isinstance(strength, dict) else {}
    state = str(
        strength.get("risk_state")
        or strength.get("state")
        or (stock or {}).get("entry_strength_momentum_risk_state")
        or ""
    ).strip()
    reason = str(strength.get("reason") or (stock or {}).get("entry_strength_momentum_reason") or "").strip()
    return state in {"weak_momentum_context", "below_static_vpw_context"} or reason in {
        "below_buy_ratio",
        "below_window_buy_value",
    }


def _defensive_missed_upside_aggressive_entry_override(
    *,
    stock: dict[str, Any] | None,
    ws_data: dict[str, Any] | None,
    strategy_id: str,
    gap_profile: dict[str, Any],
    applied_bps: int,
    best_bid: int,
    best_ask: int,
    defensive_order_price: int,
    is_latency_override: bool,
    quote_stale: bool,
) -> dict[str, Any]:
    if not _aggressive_entry_price_override_enabled():
        return {"applied": False, "reason": "disabled"}
    if _dynamic_entry_price_resolver_live_selected():
        return {"applied": False, "reason": "dynamic_entry_price_resolver_live_selected"}
    if "defensive_missed_upside_v1" not in _aggressive_entry_price_override_types():
        return {"applied": False, "reason": "type_disabled"}
    if str(strategy_id or "").upper() not in {"SCALPING", "SCALP"}:
        return {"applied": False, "reason": "non_scalping"}
    if is_latency_override:
        return {"applied": False, "reason": "latency_override"}
    if quote_stale:
        return {"applied": False, "reason": "quote_stale"}
    if best_bid <= 0 or defensive_order_price <= 0:
        return {"applied": False, "reason": "missing_bid_or_defensive_price"}

    profile = str(gap_profile.get("profile") or "")
    if profile not in {"normal", "favorable_micro", "favorable_wide_micro", "weak_liquidity_wide_spread"}:
        return {"applied": False, "reason": "profile_not_eligible"}
    min_bps = max(1, int(getattr(TRADING_RULES, "SCALP_DEFENSIVE_MISSED_UPSIDE_MIN_ORIGINAL_BPS", 35) or 35))
    if int(applied_bps or 0) < min_bps:
        return {"applied": False, "reason": "original_bps_below_min"}

    context = gap_profile.get("context") if isinstance(gap_profile.get("context"), dict) else {}
    positive_signal_count = int(context.get("positive_signal_count") or 0)
    micro_state = _micro_state_from_inputs(stock, ws_data)
    if micro_state not in {"neutral", "bullish", "strong_bullish"} and positive_signal_count <= 0:
        return {"applied": False, "reason": "micro_not_eligible"}
    if _weak_pullback_like_context(stock, positive_signal_count):
        return {"applied": False, "reason": "weak_pullback_like_context"}

    target_mode = str(
        getattr(TRADING_RULES, "SCALP_DEFENSIVE_MISSED_UPSIDE_TARGET_MODE", "best_bid_near") or "best_bid_near"
    ).strip()
    bullish = micro_state in {"bullish", "strong_bullish"} or positive_signal_count > 0
    minus_ticks = (
        int(getattr(TRADING_RULES, "SCALP_DEFENSIVE_MISSED_UPSIDE_BULLISH_BID_MINUS_TICKS", 0) or 0)
        if bullish
        else int(getattr(TRADING_RULES, "SCALP_DEFENSIVE_MISSED_UPSIDE_NEUTRAL_BID_MINUS_TICKS", 1) or 1)
    )
    minus_ticks = max(0, minus_ticks)
    target_price = move_price_by_ticks(best_bid, -minus_ticks) if minus_ticks else int(best_bid)
    if best_ask > 0:
        target_price = min(target_price, best_ask)
    if target_price <= defensive_order_price:
        return {"applied": False, "reason": "target_not_more_aggressive"}
    return {
        "applied": True,
        "type": "defensive_missed_upside_v1",
        "reason": "defensive_price_missed_upside_best_bid_near",
        "target_mode": target_mode,
        "target_price": int(target_price),
        "minus_ticks": minus_ticks,
        "micro_state": micro_state,
        "positive_signal_count": positive_signal_count,
        "original_profile": profile,
        "original_bps": int(applied_bps or 0),
    }


def _reference_target_cap_missed_upside_aggressive_entry_override(
    *,
    stock: dict[str, Any] | None,
    ws_data: dict[str, Any] | None,
    strategy_id: str,
    gap_profile: dict[str, Any],
    applied_bps: int,
    best_bid: int,
    best_ask: int,
    defensive_order_price: int,
    target_buy_price: int,
    is_latency_override: bool,
    quote_stale: bool,
) -> dict[str, Any]:
    if not _aggressive_entry_price_override_enabled():
        return {"applied": False, "reason": "disabled"}
    if _dynamic_entry_price_resolver_live_selected():
        return {"applied": False, "reason": "dynamic_entry_price_resolver_live_selected"}
    if "reference_target_cap_missed_upside_v1" not in _aggressive_entry_price_override_types():
        return {"applied": False, "reason": "type_disabled"}
    if str(strategy_id or "").upper() not in {"SCALPING", "SCALP"}:
        return {"applied": False, "reason": "non_scalping"}
    if is_latency_override:
        return {"applied": False, "reason": "latency_override"}
    if quote_stale:
        return {"applied": False, "reason": "quote_stale"}
    if best_bid <= 0 or defensive_order_price <= 0:
        return {"applied": False, "reason": "missing_bid_or_defensive_price"}
    if int(target_buy_price or 0) <= 0:
        return {"applied": False, "reason": "missing_reference_target"}
    if int(target_buy_price) >= best_bid:
        return {"applied": False, "reason": "reference_target_not_below_bid"}

    below_bid_bps = _compute_price_below_bid_bps(int(target_buy_price), int(best_bid))
    min_bps = max(
        1,
        int(getattr(TRADING_RULES, "SCALP_REFERENCE_TARGET_MISSED_UPSIDE_MIN_BELOW_BID_BPS", 20) or 20),
    )
    if below_bid_bps < min_bps:
        return {
            "applied": False,
            "reason": "reference_target_below_bid_bps_below_min",
            "reference_target_price": int(target_buy_price),
            "reference_target_below_bid_bps": int(below_bid_bps),
            "reference_target_missed_upside_min_bps": int(min_bps),
        }

    context = gap_profile.get("context") if isinstance(gap_profile.get("context"), dict) else {}
    positive_signal_count = int(context.get("positive_signal_count") or 0)
    micro_state = _micro_state_from_inputs(stock, ws_data)
    if micro_state not in {"neutral", "bullish", "strong_bullish"} and positive_signal_count <= 0:
        return {"applied": False, "reason": "micro_not_eligible"}
    if _weak_pullback_like_context(stock, positive_signal_count):
        return {"applied": False, "reason": "weak_pullback_like_context"}

    target_mode = str(
        getattr(TRADING_RULES, "SCALP_REFERENCE_TARGET_MISSED_UPSIDE_TARGET_MODE", "best_bid_near")
        or "best_bid_near"
    ).strip()
    bullish = micro_state in {"bullish", "strong_bullish"} or positive_signal_count > 0
    minus_ticks = (
        int(getattr(TRADING_RULES, "SCALP_REFERENCE_TARGET_MISSED_UPSIDE_BULLISH_BID_MINUS_TICKS", 0) or 0)
        if bullish
        else int(getattr(TRADING_RULES, "SCALP_REFERENCE_TARGET_MISSED_UPSIDE_NEUTRAL_BID_MINUS_TICKS", 1) or 1)
    )
    minus_ticks = max(0, minus_ticks)
    target_price = move_price_by_ticks(best_bid, -minus_ticks) if minus_ticks else int(best_bid)
    if best_ask > 0:
        target_price = min(target_price, best_ask)
    if target_price <= max(int(defensive_order_price), int(target_buy_price)):
        return {"applied": False, "reason": "target_not_more_aggressive"}
    return {
        "applied": True,
        "type": "reference_target_cap_missed_upside_v1",
        "reason": "reference_target_cap_missed_upside_best_bid_near",
        "target_mode": target_mode,
        "target_price": int(target_price),
        "minus_ticks": minus_ticks,
        "micro_state": micro_state,
        "positive_signal_count": positive_signal_count,
        "original_profile": str(gap_profile.get("profile") or ""),
        "original_bps": int(applied_bps or 0),
        "reference_target_price": int(target_buy_price),
        "reference_target_below_bid_bps": int(below_bid_bps),
        "reference_target_missed_upside_min_bps": int(min_bps),
    }


def _normal_market_gap_profile(
    conditional_context: dict[str, Any],
    *,
    normal_bps: int,
    strong_bps: int,
    favorable_bps: int,
    weak_bps: int,
    strong_enabled: bool,
    is_latency_override: bool,
) -> dict[str, Any]:
    spread_ticks = int(conditional_context.get("spread_ticks") or 0)
    positive_signals = [
        name
        for name in ("buy_pressure_ok", "ofi_ok", "depth_ok")
        if bool(conditional_context.get(name))
    ]
    positive_signal_count = len(positive_signals)
    profile_context = {
        "spread_ticks": spread_ticks,
        "positive_signal_count": positive_signal_count,
        "positive_signals": ",".join(positive_signals),
        "buy_pressure_ok": bool(conditional_context.get("buy_pressure_ok")),
        "ofi_ok": bool(conditional_context.get("ofi_ok")),
        "depth_ok": bool(conditional_context.get("depth_ok")),
        "conditional_1tick_eligible": bool(conditional_context.get("eligible")),
        "conditional_1tick_enabled": bool(strong_enabled),
        "latency_override": bool(is_latency_override),
    }
    profile = {
        "profile": "normal",
        "bps": normal_bps,
        "reason": "normal_market_default",
        "context": profile_context,
    }
    if is_latency_override:
        profile.update(profile="latency_override", bps=0, reason="latency_override_keeps_defensive")
        return profile
    if not strong_enabled:
        profile["reason"] = "conditional_1tick_disabled"
        return profile
    if bool(conditional_context.get("eligible")):
        profile.update(
            profile="strong_1tick_pressure",
            bps=strong_bps,
            reason="spread_1tick_strong_buy_pressure_percent_bps",
        )
        return profile
    if spread_ticks <= 3 and positive_signal_count >= 1:
        profile.update(
            profile="favorable_micro",
            bps=favorable_bps,
            reason="spread_lte3_positive_micro_percent_bps",
        )
        return profile
    if spread_ticks <= 5 and positive_signal_count >= 2:
        profile.update(
            profile="favorable_wide_micro",
            bps=favorable_bps,
            reason="spread_lte5_two_positive_micro_percent_bps",
        )
        return profile
    if spread_ticks >= 6 or (spread_ticks >= 4 and positive_signal_count == 0):
        profile.update(
            profile="weak_liquidity_wide_spread",
            bps=weak_bps,
            reason="wide_spread_or_no_positive_micro_percent_bps",
        )
        return profile
    return profile


def _normal_defensive_ticks_for_strategy(strategy_id: str) -> int:
    if str(strategy_id or "").upper() in {"SCALPING", "SCALP"}:
        return max(1, int(_CONFIG.normal_defensive_ticks or 1))
    return 1


def _ticks_between(lower: int | float, upper: int | float) -> int:
    """Count how many 1-tick upward moves from lower to reach upper."""
    current = clamp_price_to_tick(int(lower))
    target = int(upper)
    if current >= target:
        return 0
    ticks = 0
    for _ in range(100):
        if current >= target:
            return ticks
        current = move_price_by_ticks(current, 1)
        ticks += 1
    return 0


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


def _should_apply_latency_submit_recovery_canary(
    *,
    strategy_id: str,
    signal_strength: float,
    latency_status,
) -> tuple[bool, str]:
    if not bool(getattr(TRADING_RULES, "SCALP_LATENCY_SUBMIT_RECOVERY_CANARY_ENABLED", False)):
        return False, "disabled"
    if str(strategy_id or "").upper() != "SCALPING":
        return False, "non_scalping"
    if getattr(latency_status, "quote_stale", False):
        return False, "quote_stale"
    if str(getattr(getattr(latency_status, "state", None), "value", "")) != "CAUTION":
        return False, "not_caution"

    normalized_score = _normalize_signal_score(signal_strength)
    min_signal = _to_float(getattr(TRADING_RULES, "SCALP_LATENCY_SUBMIT_RECOVERY_MIN_SIGNAL_SCORE", 75.0), 75.0)
    if normalized_score < min_signal:
        return False, "signal_score_below_floor"

    max_ws_age_ms = int(getattr(TRADING_RULES, "SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_AGE_MS", 1200) or 1200)
    max_ws_jitter_ms = int(
        getattr(TRADING_RULES, "SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_JITTER_MS", 1500) or 1500
    )
    max_spread_ratio = _to_float(
        getattr(TRADING_RULES, "SCALP_LATENCY_SUBMIT_RECOVERY_MAX_SPREAD_RATIO", 0.0100),
        0.0100,
    )
    if int(getattr(latency_status, "ws_age_ms", 0) or 0) > max_ws_age_ms:
        return False, "ws_age_above_recovery_cap"
    if int(getattr(latency_status, "ws_jitter_ms", 0) or 0) > max_ws_jitter_ms:
        return False, "ws_jitter_above_recovery_cap"
    if _to_float(getattr(latency_status, "spread_ratio", 0.0), 0.0) > max_spread_ratio:
        return False, "spread_above_recovery_cap"
    return True, "latency_submit_recovery_normal_override"


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

    configured_min_signal = _to_float(
        getattr(TRADING_RULES, "SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE", 85.0),
        85.0,
    )
    min_signal = max(
        configured_min_signal,
        _to_float(
            getattr(TRADING_RULES, "SCALP_LATENCY_SPREAD_RELIEF_EFFECTIVE_MIN_SIGNAL_SCORE_FLOOR", 85.0),
            85.0,
        ),
    )
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


def _latency_spread_relief_signal_score_floors() -> tuple[float, float]:
    configured_min_signal = _to_float(
        getattr(TRADING_RULES, "SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE", 85.0),
        85.0,
    )
    effective_min_signal = max(
        configured_min_signal,
        _to_float(
            getattr(TRADING_RULES, "SCALP_LATENCY_SPREAD_RELIEF_EFFECTIVE_MIN_SIGNAL_SCORE_FLOOR", 85.0),
            85.0,
        ),
    )
    return configured_min_signal, effective_min_signal


def _pre_submit_quote_refresh_enabled(strategy_id: str) -> bool:
    if str(strategy_id or "").upper() not in {"SCALPING", "SCALP"}:
        return False
    env_value = os.getenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_ENABLED")
    if env_value is not None:
        return str(env_value).strip().lower() in {"1", "true", "yes", "y", "on"}
    runtime_rules = getattr(constants_module, "TRADING_RULES", TRADING_RULES)
    return bool(getattr(runtime_rules, "SCALP_PRE_SUBMIT_QUOTE_REFRESH_ENABLED", False))


def _pre_submit_quote_refresh_max_age_ms() -> int:
    env_value = os.getenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_AGE_MS")
    if env_value is not None:
        try:
            return max(0, int(float(env_value)))
        except Exception:
            pass
    runtime_rules = getattr(constants_module, "TRADING_RULES", TRADING_RULES)
    return int(getattr(runtime_rules, "SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_AGE_MS", 700) or 700)


def _pre_submit_quote_refresh_max_spread_ratio() -> float:
    env_value = os.getenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_SPREAD_RATIO")
    if env_value is not None:
        try:
            return max(0.0, float(env_value))
        except Exception:
            pass
    runtime_rules = getattr(constants_module, "TRADING_RULES", TRADING_RULES)
    return _to_float(
        getattr(runtime_rules, "SCALP_PRE_SUBMIT_QUOTE_REFRESH_MAX_SPREAD_RATIO", 0.015),
        0.015,
    )


def _maybe_refresh_stale_quote_from_observer(
    *,
    code: str,
    strategy_id: str,
    latest_price: int,
    frozen_price: int,
    latency,
) -> tuple[Any, dict[str, Any]]:
    provenance = {
        "pre_submit_quote_refresh_enabled": _pre_submit_quote_refresh_enabled(strategy_id),
        "pre_submit_quote_refresh_applied": False,
        "pre_submit_quote_refresh_reason": "not_attempted",
        "pre_submit_quote_refresh_source": "orderbook_stability_observer",
        "pre_submit_quote_refresh_strategy_id": str(strategy_id or ""),
        "pre_submit_quote_refresh_env_value": os.getenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_ENABLED"),
        "pre_submit_quote_refresh_quote_age_ms": None,
        "pre_submit_quote_refresh_best_bid": 0,
        "pre_submit_quote_refresh_best_ask": 0,
        "pre_submit_quote_refresh_spread_ratio": None,
    }
    if not provenance["pre_submit_quote_refresh_enabled"]:
        provenance["pre_submit_quote_refresh_reason"] = "disabled"
        return latency, provenance
    if not bool(getattr(latency, "quote_stale", False)):
        provenance["pre_submit_quote_refresh_reason"] = "quote_not_stale"
        return latency, provenance

    snapshot = ORDERBOOK_STABILITY_OBSERVER.snapshot(code)
    best_bid = int(snapshot.get("best_bid") or 0)
    best_ask = int(snapshot.get("best_ask") or 0)
    quote_age = snapshot.get("observer_last_quote_age_ms")
    provenance.update(
        {
            "pre_submit_quote_refresh_quote_age_ms": quote_age,
            "pre_submit_quote_refresh_best_bid": best_bid,
            "pre_submit_quote_refresh_best_ask": best_ask,
        }
    )
    if quote_age is None:
        provenance["pre_submit_quote_refresh_reason"] = "observer_quote_missing"
        return latency, provenance
    max_age = _pre_submit_quote_refresh_max_age_ms()
    if float(quote_age) > max_age:
        provenance["pre_submit_quote_refresh_reason"] = "observer_quote_stale"
        return latency, provenance
    if best_bid <= 0 or best_ask <= 0 or best_ask <= best_bid:
        provenance["pre_submit_quote_refresh_reason"] = "observer_best_levels_invalid"
        return latency, provenance

    reference_price = int(latest_price or frozen_price or best_bid)
    if reference_price <= 0:
        provenance["pre_submit_quote_refresh_reason"] = "reference_price_missing"
        return latency, provenance
    spread_ratio = max(0.0, (best_ask - best_bid) / float(reference_price))
    max_spread = _pre_submit_quote_refresh_max_spread_ratio()
    if spread_ratio > max_spread:
        provenance["pre_submit_quote_refresh_reason"] = "observer_spread_too_wide"
        provenance["pre_submit_quote_refresh_spread_ratio"] = round(float(spread_ratio), 6)
        return latency, provenance

    refreshed_latency = _LATENCY_MONITOR.evaluate(
        ws_age_ms=int(round(float(quote_age))),
        ws_jitter_ms=int(getattr(latency, "ws_jitter_ms", 0) or 0),
        order_rtt_avg_ms=int(getattr(latency, "order_rtt_avg_ms", 0) or 0),
        order_rtt_p95_ms=int(getattr(latency, "order_rtt_p95_ms", 0) or 0),
        quote_stale=False,
        spread_ratio=spread_ratio,
    )
    provenance.update(
        {
            "pre_submit_quote_refresh_applied": True,
            "pre_submit_quote_refresh_reason": "observer_quote_fresh",
            "pre_submit_quote_refresh_spread_ratio": round(float(spread_ratio), 6),
        }
    )
    log_info(
        f"[PRE_SUBMIT_QUOTE_REFRESH] {code} source=orderbook_stability_observer "
        f"quote_age_ms={quote_age} best_bid={best_bid} best_ask={best_ask} "
        f"spread_ratio={spread_ratio:.6f}"
    )
    return refreshed_latency, provenance


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
    - CAUTION now follows the normal submit path after the slippage check.
      DANGER/stale/broker safety still blocks before submit.
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
    latency, pre_submit_quote_refresh = _maybe_refresh_stale_quote_from_observer(
        code=code,
        strategy_id=strategy_id,
        latest_price=latest_price,
        frozen_price=frozen_price,
        latency=latency,
    )
    if pre_submit_quote_refresh.get("pre_submit_quote_refresh_applied"):
        refreshed_best_bid = int(pre_submit_quote_refresh.get("pre_submit_quote_refresh_best_bid") or 0)
        refreshed_best_ask = int(pre_submit_quote_refresh.get("pre_submit_quote_refresh_best_ask") or 0)
        if refreshed_best_bid > 0 and refreshed_best_ask > refreshed_best_bid:
            best_bid = refreshed_best_bid
            best_ask = refreshed_best_ask
            latest_price = refreshed_best_bid
            pre_submit_quote_refresh["pre_submit_quote_refresh_latest_price"] = latest_price
            with _CACHE_LOCK:
                _CACHE.update(
                    code,
                    last_price=latest_price,
                    best_ask=best_ask,
                    best_bid=best_bid,
                    received_at=None,
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
    danger_relief_forbidden = policy.decision == EntryDecision.REJECT_DANGER
    if danger_relief_forbidden:
        latency_canary_reason = "danger_hard_safety_block"
    if policy.decision == EntryDecision.REJECT_MARKET_CONDITION and policy.reason == "latency_fallback_deprecated":
        recovery_ok, recovery_reason = _should_apply_latency_submit_recovery_canary(
            strategy_id=strategy_id,
            signal_strength=float(signal_strength or 0.0),
            latency_status=latency,
        )
        if recovery_ok:
            latency_canary_applied = True
            latency_canary_reason = recovery_reason
            effective_decision = EntryDecision.ALLOW_NORMAL
            effective_reason = recovery_reason
            log_info(
                f"[LATENCY_SUBMIT_RECOVERY_CANARY] {stock.get('name')}({code}) "
                f"signal_score={_normalize_signal_score(signal_strength):.1f} "
                f"ws_age_ms={latency.ws_age_ms} ws_jitter_ms={latency.ws_jitter_ms} "
                f"spread_ratio={latency.spread_ratio:.6f}"
            )
        else:
            latency_canary_reason = recovery_reason
    if policy.decision == EntryDecision.REJECT_DANGER and not danger_relief_forbidden:
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

    if policy.decision == EntryDecision.REJECT_DANGER and not danger_relief_forbidden and effective_decision == EntryDecision.REJECT_DANGER:
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

    if policy.decision == EntryDecision.REJECT_DANGER and not danger_relief_forbidden and effective_decision == EntryDecision.REJECT_DANGER:
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

    if policy.decision == EntryDecision.REJECT_DANGER and not danger_relief_forbidden and effective_decision == EntryDecision.REJECT_DANGER:
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

    spread_relief_tag = str(
        stock.get("position_tag")
        or stock.get("entry_momentum_tag")
        or stock.get("momentum_tag")
        or ""
    )
    if policy.decision == EntryDecision.REJECT_DANGER and effective_decision == EntryDecision.REJECT_DANGER:
        spread_relief_ok, spread_relief_reason = _should_apply_latency_spread_relief_canary(
            strategy_id=strategy_id,
            position_tag=spread_relief_tag,
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
                f"tag={spread_relief_tag} signal_score={_normalize_signal_score(signal_strength):.1f} "
                f"ws_age_ms={latency.ws_age_ms} ws_jitter_ms={latency.ws_jitter_ms} "
                f"spread_ratio={latency.spread_ratio:.6f} "
                f"danger_reasons={latency_danger_reasons}"
            )
        else:
            if not latency_canary_reason or latency_canary_reason == "disabled":
                latency_canary_reason = spread_relief_reason

    if policy.decision == EntryDecision.REJECT_DANGER and not danger_relief_forbidden and effective_decision == EntryDecision.REJECT_DANGER:
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

    if policy.decision == EntryDecision.REJECT_DANGER and not danger_relief_forbidden and effective_decision == EntryDecision.REJECT_DANGER:
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

    spread_relief_configured_min_signal, spread_relief_effective_min_signal = (
        _latency_spread_relief_signal_score_floors()
    )
    result = {
        "allowed": False,
        "decision": effective_decision.value,
        "reason": effective_reason,
        "policy_decision": policy.decision.value,
        "policy_reason": policy.reason,
        "effective_decision": effective_decision.value,
        "effective_reason": effective_reason,
        "threshold_family": "latency_classifier_runtime_profile",
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
        "conditional_1tick_real_override_applied": False,
        "conditional_1tick_real_override_reason": "",
        "conditional_1tick_real_override_context": {},
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
        "latency_spread_relief_signal_score": round(_normalize_signal_score(signal_strength), 3),
        "latency_spread_relief_configured_min_signal_score": round(spread_relief_configured_min_signal, 3),
        "latency_spread_relief_effective_min_signal_score": round(spread_relief_effective_min_signal, 3),
        "latency_spread_relief_tag": spread_relief_tag,
        **pre_submit_quote_refresh,
        "orderbook_stability": ORDERBOOK_STABILITY_OBSERVER.snapshot(code),
    }

    if effective_decision == EntryDecision.ALLOW_NORMAL:
        is_latency_override = latency.state.value == "DANGER" and latency_canary_applied
        percent_bps_mode = _defense_mode_is_percent_bps()
        is_scalping = str(strategy_id or "").upper() in {"SCALPING", "SCALP"}

        if percent_bps_mode and is_scalping:
            normal_defensive_bps = _normal_defensive_bps()
            strong_defensive_bps = _conditional_strong_defensive_bps()
            favorable_defensive_bps = _normal_favorable_defensive_bps()
            weak_defensive_bps = _normal_weak_defensive_bps()
            conditional_1tick_context = _conditional_real_1tick_context(
                ws_data,
                best_ask=best_ask,
                best_bid=best_bid,
            )
            conditional_1tick_applied = False
            conditional_1tick_reason = "not_eligible"
            conditional_1tick_enabled = _conditional_real_1tick_enabled(strategy_id)
            gap_profile = _normal_market_gap_profile(
                conditional_1tick_context,
                normal_bps=normal_defensive_bps,
                strong_bps=strong_defensive_bps,
                favorable_bps=favorable_defensive_bps,
                weak_bps=weak_defensive_bps,
                strong_enabled=conditional_1tick_enabled,
                is_latency_override=is_latency_override,
            )
            applied_bps = int(gap_profile.get("bps", normal_defensive_bps) or normal_defensive_bps)
            entry_price_guard = {
                "normal": "normal_defensive_percent_bps",
                "strong_1tick_pressure": "conditional_strong_defensive_percent_bps",
                "favorable_micro": "favorable_micro_percent_bps",
                "favorable_wide_micro": "favorable_wide_micro_percent_bps",
                "weak_liquidity_wide_spread": "weak_liquidity_wide_spread_percent_bps",
                "latency_override": "latency_danger_override_defensive",
            }.get(str(gap_profile.get("profile")), "normal_defensive_percent_bps")

            if str(gap_profile.get("profile")) == "strong_1tick_pressure":
                conditional_1tick_applied = True
                conditional_1tick_reason = str(gap_profile.get("reason"))
            elif not conditional_1tick_enabled:
                conditional_1tick_reason = "disabled_or_non_scalping"
            elif is_latency_override:
                conditional_1tick_reason = "latency_override_keeps_defensive"
            else:
                conditional_1tick_reason = "micro_condition_not_eligible"

            if is_latency_override:
                defensive_ticks = _CONFIG.latency_override_defensive_ticks
                defensive_order = _NORMAL_BUILDER.build(
                    snapshot=snapshot,
                    latest_price=latest_price,
                    defensive_ticks=defensive_ticks,
                )
                order_price = int(defensive_order.price)
                entry_price_guard = "latency_danger_override_defensive"
                applied_bps = 0
                gap_profile.update(profile="latency_override", bps=0, reason="latency_override_keeps_defensive")
            else:
                defensive_price = move_price_down_by_bps(latest_price, applied_bps, floor_ticks=1)
                aggressive_override = _reference_target_cap_missed_upside_aggressive_entry_override(
                    stock=stock,
                    ws_data=ws_data,
                    strategy_id=strategy_id,
                    gap_profile=gap_profile,
                    applied_bps=applied_bps,
                    best_bid=best_bid,
                    best_ask=best_ask,
                    defensive_order_price=defensive_price,
                    target_buy_price=int(target_buy_price or 0),
                    is_latency_override=is_latency_override,
                    quote_stale=bool(latency.quote_stale),
                )
                if not aggressive_override.get("applied"):
                    defensive_override = _defensive_missed_upside_aggressive_entry_override(
                        stock=stock,
                        ws_data=ws_data,
                        strategy_id=strategy_id,
                        gap_profile=gap_profile,
                        applied_bps=applied_bps,
                        best_bid=best_bid,
                        best_ask=best_ask,
                        defensive_order_price=defensive_price,
                        is_latency_override=is_latency_override,
                        quote_stale=bool(latency.quote_stale),
                    )
                    if defensive_override.get("applied") or aggressive_override.get("reason") == "type_disabled":
                        aggressive_override = defensive_override
                if aggressive_override.get("applied"):
                    order_price = int(aggressive_override.get("target_price") or defensive_price)
                    override_type = str(aggressive_override.get("type") or "")
                    gap_profile.update(
                        profile=override_type,
                        bps=int(aggressive_override.get("original_bps") or applied_bps),
                        reason=str(aggressive_override.get("reason")),
                    )
                    gap_profile["context"] = {
                        **(gap_profile.get("context") if isinstance(gap_profile.get("context"), dict) else {}),
                        "aggressive_entry_price_override_applied": True,
                        "aggressive_entry_price_override_type": override_type,
                        "aggressive_entry_price_override_reason": str(aggressive_override.get("reason")),
                        "aggressive_entry_price_original_profile": str(aggressive_override.get("original_profile")),
                        "aggressive_entry_price_original_bps": int(aggressive_override.get("original_bps") or applied_bps),
                        "aggressive_entry_price_target_mode": str(aggressive_override.get("target_mode")),
                        "aggressive_entry_price_order_price": int(order_price),
                        "aggressive_entry_price_minus_ticks": int(aggressive_override.get("minus_ticks") or 0),
                        "aggressive_entry_price_micro_state": str(aggressive_override.get("micro_state") or ""),
                    }
                    if "reference_target_price" in aggressive_override:
                        gap_profile["context"].update(
                            {
                                "reference_target_price": int(aggressive_override.get("reference_target_price") or 0),
                                "reference_target_below_bid_bps": int(
                                    aggressive_override.get("reference_target_below_bid_bps") or 0
                                ),
                                "reference_target_missed_upside_min_bps": int(
                                    aggressive_override.get("reference_target_missed_upside_min_bps") or 0
                                ),
                            }
                        )
                    entry_price_guard = (
                        "reference_target_cap_missed_upside_aggressive_entry"
                        if override_type == "reference_target_cap_missed_upside_v1"
                        else "defensive_missed_upside_aggressive_entry"
                    )
                else:
                    order_price = defensive_price
                    gap_profile["context"] = {
                        **(gap_profile.get("context") if isinstance(gap_profile.get("context"), dict) else {}),
                        "aggressive_entry_price_override_skip_reason": str(
                            aggressive_override.get("reason") or ""
                        ),
                    }
                defensive_ticks = 0
                aggressive_override_applied = bool(aggressive_override.get("applied"))
                reference_target_override_diagnostics = aggressive_override
            if is_latency_override:
                aggressive_override_applied = False
                reference_target_override_diagnostics = {}

            normal_defensive_order_price = move_price_down_by_bps(
                latest_price, normal_defensive_bps, floor_ticks=1
            )
            latency_guarded_order_price = order_price
            counterfactual_order_price_1tick = move_price_by_ticks(latest_price, -1)
            if aggressive_override_applied:
                price_resolution = {
                    "order_price": int(order_price),
                    "price_resolution_reason": "aggressive_entry_price_override",
                    "reference_target_applied": False,
                    "reference_target_rejected_reason": "aggressive_entry_price_override_applied",
                    "reference_target_below_bid_bps": int(
                        reference_target_override_diagnostics.get("reference_target_below_bid_bps")
                        or _compute_price_below_bid_bps(int(target_buy_price or 0), best_bid)
                    ),
                    "reference_target_max_below_bid_bps": int(
                        getattr(TRADING_RULES, "SCALPING_ENTRY_PRICE_RESOLVER_MAX_BELOW_BID_BPS", 80)
                    ),
                    "entry_price_resolver_enabled": bool(
                        getattr(TRADING_RULES, "SCALPING_ENTRY_PRICE_RESOLVER_ENABLED", True)
                    ),
                }
            else:
                price_resolution = _resolve_scalping_order_price(
                    strategy_id=strategy_id,
                    defensive_order_price=order_price,
                    target_buy_price=int(target_buy_price or 0),
                    best_bid=best_bid,
                )
            if int(target_buy_price or 0) > 0 and not aggressive_override_applied:
                target_cap = int(target_buy_price)
                counterfactual_order_price_1tick = min(counterfactual_order_price_1tick, target_cap)
                order_price = int(price_resolution.get("order_price", order_price) or order_price)
            result["allowed"] = True
            result["mode"] = "normal"
            result["order_price"] = order_price
            result["entry_price_guard"] = entry_price_guard
            result["entry_price_defensive_ticks"] = _ticks_between(order_price, latest_price)
            result["entry_price_defense_mode"] = "percent_bps"
            result["entry_price_defensive_bps"] = applied_bps
            result["entry_price_defensive_floor_ticks"] = 1
            result["entry_price_gap_profile"] = str(gap_profile.get("profile"))
            result["entry_price_gap_profile_bps"] = int(gap_profile.get("bps", applied_bps) or applied_bps)
            result["entry_price_gap_profile_reason"] = str(gap_profile.get("reason") or "")
            result["entry_price_gap_profile_context"] = gap_profile.get("context", {})
            result["aggressive_entry_price_override_applied"] = bool(
                (gap_profile.get("context") or {}).get("aggressive_entry_price_override_applied")
                if isinstance(gap_profile.get("context"), dict)
                else False
            )
            result["aggressive_entry_price_override_type"] = str(
                (gap_profile.get("context") or {}).get("aggressive_entry_price_override_type", "")
                if isinstance(gap_profile.get("context"), dict)
                else ""
            )
            result["aggressive_entry_price_override_reason"] = str(
                (gap_profile.get("context") or {}).get("aggressive_entry_price_override_reason", "")
                if isinstance(gap_profile.get("context"), dict)
                else ""
            )
            result["aggressive_entry_price_override_skip_reason"] = str(
                (gap_profile.get("context") or {}).get("aggressive_entry_price_override_skip_reason", "")
                if isinstance(gap_profile.get("context"), dict)
                else ""
            )
            result["aggressive_entry_price_original_profile"] = str(
                (gap_profile.get("context") or {}).get("aggressive_entry_price_original_profile", "")
                if isinstance(gap_profile.get("context"), dict)
                else ""
            )
            result["aggressive_entry_price_original_bps"] = int(
                (gap_profile.get("context") or {}).get("aggressive_entry_price_original_bps", 0)
                if isinstance(gap_profile.get("context"), dict)
                else 0
            )
            result["aggressive_entry_price_target_mode"] = str(
                (gap_profile.get("context") or {}).get("aggressive_entry_price_target_mode", "")
                if isinstance(gap_profile.get("context"), dict)
                else ""
            )
            result["aggressive_entry_price_order_price"] = int(
                (gap_profile.get("context") or {}).get("aggressive_entry_price_order_price", 0)
                if isinstance(gap_profile.get("context"), dict)
                else 0
            )
            result["normal_defensive_order_price"] = int(normal_defensive_order_price)
            result["latency_guarded_order_price"] = int(latency_guarded_order_price)
            result["counterfactual_order_price_1tick"] = int(counterfactual_order_price_1tick)
            result["conditional_1tick_real_override_applied"] = conditional_1tick_applied
            result["conditional_1tick_real_override_reason"] = conditional_1tick_reason
            result["conditional_1tick_real_override_context"] = conditional_1tick_context
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
                    "price": int(order_price),
                    "qty": int(snapshot.planned_qty) if snapshot and snapshot.planned_qty else 0,
                }
            ]
            return result

        # tick-based mode (default, fallback)
        defensive_ticks = (
            _CONFIG.latency_override_defensive_ticks
            if is_latency_override
            else _normal_defensive_ticks_for_strategy(strategy_id)
        )
        entry_price_guard = (
            "latency_danger_override_defensive"
            if is_latency_override
            else "normal_defensive"
        )
        conditional_1tick_context = _conditional_real_1tick_context(
            ws_data,
            best_ask=best_ask,
            best_bid=best_bid,
        )
        conditional_1tick_applied = False
        conditional_1tick_reason = "not_eligible"
        if (
            not is_latency_override
            and defensive_ticks > 1
            and _conditional_real_1tick_enabled(strategy_id)
            and bool(conditional_1tick_context.get("eligible"))
        ):
            defensive_ticks = 1
            entry_price_guard = "conditional_1tick_real_micro_override"
            conditional_1tick_applied = True
            conditional_1tick_reason = "spread_1tick_strong_buy_pressure"
        elif not _conditional_real_1tick_enabled(strategy_id):
            conditional_1tick_reason = "disabled_or_non_scalping"
        elif is_latency_override:
            conditional_1tick_reason = "latency_override_keeps_defensive"
        elif defensive_ticks <= 1:
            conditional_1tick_reason = "already_1tick_or_less"
        defensive_order = _NORMAL_BUILDER.build(
            snapshot=snapshot,
            latest_price=latest_price,
            defensive_ticks=defensive_ticks,
        )
        normal_defensive_order_price = move_price_by_ticks(
            latest_price,
            -_normal_defensive_ticks_for_strategy(strategy_id),
        )
        latency_guarded_order_price = int(defensive_order.price)
        counterfactual_order_price_1tick = move_price_by_ticks(latest_price, -1)
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
        result["entry_price_defense_mode"] = "tick"
        result["normal_defensive_order_price"] = int(normal_defensive_order_price)
        result["latency_guarded_order_price"] = int(latency_guarded_order_price)
        result["counterfactual_order_price_1tick"] = int(counterfactual_order_price_1tick)
        result["conditional_1tick_real_override_applied"] = conditional_1tick_applied
        result["conditional_1tick_real_override_reason"] = conditional_1tick_reason
        result["conditional_1tick_real_override_context"] = conditional_1tick_context
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
                "price": int(order_price),
                "qty": int(snapshot.planned_qty) if snapshot and snapshot.planned_qty else 0,
            }
        ]
        return result

    result["mode"] = "reject"
    return result
