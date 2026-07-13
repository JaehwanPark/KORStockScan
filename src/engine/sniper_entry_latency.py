"""Latency-aware entry adapter for the legacy sniper engine."""

from __future__ import annotations

import os
import threading
import time
from datetime import UTC, datetime
from typing import Any

from src.engine.scalping.micro_estimator_state import DEFAULT_STORE as MICRO_ESTIMATOR_STORE
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

_LATENCY_FALSE_NEGATIVE_REMEASURE_AUTHORITY = (
    "source_only_latency_false_negative_bounded_remeasure_enqueue"
)
_LATENCY_FALSE_NEGATIVE_REMEASURE_FORBIDDEN_USES = (
    "standalone_buy,submit_safety_bypass,stale_submit_bypass,broker_guard_bypass,"
    "threshold_mutation,provider_route_change,quantity_or_cap_change,position_cap_release"
)
_LATENCY_TRUE_OFI_DIRECT_CANARY_AUTHORITY = (
    "operator_runtime_override_latency_true_ofi_false_negative_direct_canary"
)
_LATENCY_TRUE_OFI_DIRECT_CANARY_FORBIDDEN_USES = (
    "stale_submit_bypass,broker_guard_bypass,threshold_mutation,provider_route_change,"
    "quantity_or_cap_change,position_cap_release,wide_spread_bypass,explicit_ai_veto_bypass"
)


def _safe_price_int(value: Any) -> int:
    try:
        return int(float(str(value).replace(",", "").strip()))
    except Exception:
        return 0


def _best_ask_bid_from_ws(ws_data: dict[str, Any] | None) -> tuple[int, int]:
    data = ws_data or {}
    orderbook = (ws_data or {}).get("orderbook") or {}
    asks = orderbook.get("asks") or []
    bids = orderbook.get("bids") or []

    best_ask = 0
    best_bid = 0
    if asks:
        best_ask = _safe_price_int((asks[0] or {}).get("price", 0))
    if bids:
        best_bid = _safe_price_int((bids[0] or {}).get("price", 0))
    if best_ask <= 0:
        best_ask = _safe_price_int(data.get("best_ask") or data.get("ask_price") or data.get("ask"))
    if best_bid <= 0:
        best_bid = _safe_price_int(data.get("best_bid") or data.get("bid_price") or data.get("bid"))
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


def _ws_tick_aggressor_pressure_usable(ws_data: dict[str, Any] | None) -> bool:
    ws = ws_data if isinstance(ws_data, dict) else {}
    return _tick_aggressor_pressure_usable_from_fields(ws)


def _tick_aggressor_pressure_usable_from_fields(fields: dict[str, Any] | None) -> bool:
    source = fields if isinstance(fields, dict) else {}
    raw_flag = source.get("tick_aggressor_pressure_usable")
    if isinstance(raw_flag, bool):
        pressure_flag = raw_flag
    else:
        pressure_flag = str(raw_flag or "").strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(
        pressure_flag
        or _to_float(source.get("tick_aggressor_trusted_count"), 0.0) > 0
    )


def _latency_buy_pressure_value(ws_data: dict[str, Any] | None, stock: dict[str, Any] | None) -> float:
    ws = ws_data if isinstance(ws_data, dict) else {}
    item = stock if isinstance(stock, dict) else {}
    if ws.get("buy_pressure_10t") not in (None, "") and _tick_aggressor_pressure_usable_from_fields(ws):
        return _to_float(ws.get("buy_pressure_10t"), 0.0)
    if item.get("buy_pressure_10t") not in (None, "") and _tick_aggressor_pressure_usable_from_fields(item):
        return _to_float(item.get("buy_pressure_10t"), 0.0)
    if ws.get("buy_ratio") not in (None, ""):
        return _to_float(ws.get("buy_ratio"), 0.0)
    return 0.0


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

    pressure_usable = _ws_tick_aggressor_pressure_usable(ws)
    raw_buy_volume = _to_float(ws.get("buy_exec_volume"), 0.0)
    raw_sell_volume = _to_float(ws.get("sell_exec_volume"), 0.0)
    buy_volume = raw_buy_volume if pressure_usable else 0.0
    sell_volume = raw_sell_volume if pressure_usable else 0.0
    total_exec_volume = buy_volume + sell_volume
    buy_ratio = _to_float(ws.get("buy_ratio"), 0.0) if pressure_usable else 50.0
    if total_exec_volume > 0:
        buy_ratio = (buy_volume / total_exec_volume) * 100.0
    net_buy_exec_volume = _to_float(ws.get("net_buy_exec_volume"), buy_volume - sell_volume) if pressure_usable else 0.0

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
    buy_pressure_ok = pressure_usable and net_buy_exec_volume > 0 and buy_ratio >= min_buy_ratio
    ofi_ok = ofi_norm >= min_ofi_norm
    depth_ok = bid_depth > 0 and ask_depth > 0 and bid_ask_ratio >= min_bid_ask_ratio

    return {
        "spread_ticks": spread_ticks,
        "buy_ratio": round(float(buy_ratio), 6),
        "net_buy_exec_volume": int(net_buy_exec_volume),
        "raw_buy_exec_volume": int(raw_buy_volume),
        "raw_sell_exec_volume": int(raw_sell_volume),
        "tick_aggressor_pressure_usable": bool(pressure_usable),
        "tick_aggressor_trusted_count": int(_to_float(ws.get("tick_aggressor_trusted_count"), 0.0)),
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
    operator_enabled = str(
        os.getenv("KORSTOCKSCAN_INTRADAY_ENTRY_PRICE_DISCOVERY_ENABLED") or ""
    ).strip().lower() in {"1", "true", "yes", "y", "on"}
    return operator_enabled or bool(getattr(TRADING_RULES, "SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_ENABLED", False))


def _intraday_entry_price_discovery_enabled() -> bool:
    return str(os.getenv("KORSTOCKSCAN_INTRADAY_ENTRY_PRICE_DISCOVERY_ENABLED") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }


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
    if _dynamic_entry_price_resolver_live_selected() and not _intraday_entry_price_discovery_enabled():
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
        "operator_intraday_entry_price_discovery": _intraday_entry_price_discovery_enabled(),
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
    if _dynamic_entry_price_resolver_live_selected() and not _intraday_entry_price_discovery_enabled():
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
        "operator_intraday_entry_price_discovery": _intraday_entry_price_discovery_enabled(),
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
        "tick_aggressor_pressure_usable": bool(conditional_context.get("tick_aggressor_pressure_usable")),
        "tick_aggressor_trusted_count": int(conditional_context.get("tick_aggressor_trusted_count") or 0),
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


def _clamp_float(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _latency_micro_estimator_all_scalping_enabled() -> bool:
    return _truthy(
        os.getenv("KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_ALL_SCALPING_ENABLED")
    )


def _latency_micro_estimator_allowed_tags() -> set[str]:
    raw_tags = os.getenv("KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_TAGS")
    if raw_tags is None:
        return {
            str(tag).strip().upper()
            for tag in (getattr(TRADING_RULES, "SCALP_LATENCY_SPREAD_RELIEF_TAGS", ()) or ())
            if str(tag).strip()
        }
    return {item.strip().upper() for item in raw_tags.split(",") if item.strip()}


def _score_candidate_from_source(source: dict[str, Any] | None, prefix: str) -> tuple[float | None, str]:
    fields = source if isinstance(source, dict) else {}
    zero_candidate = ""
    for key in (
        "rt_ai_prob",
        "prob",
        "ai_prob",
        "entry_ai_prob",
        "rt_ai_score",
        "ai_score",
        "entry_ai_score",
        "latest_ai_score",
        "prior_ai_score",
        "holding_ai_score",
    ):
        raw_value = fields.get(key)
        if raw_value in (None, "", "None", "-", "not_evaluated"):
            continue
        score = _normalize_signal_score(raw_value)
        if score > 0:
            return score, f"{prefix}.{key}"
        if score == 0:
            zero_candidate = zero_candidate or f"{prefix}.{key}"
    if zero_candidate:
        return 0.0, zero_candidate
    return None, ""


def _latency_explicit_negative_ai_action(
    stock: dict[str, Any] | None,
    ws_data: dict[str, Any] | None,
) -> str:
    """Return an explicit AI veto; unknown or missing action is not a veto."""

    for source in (stock, ws_data):
        fields = source if isinstance(source, dict) else {}
        for key in (
            "rising_missed_entry_ai_action",
            "entry_ai_action",
            "ai_action",
            "action",
            "last_ai_action",
            "current_ai_action",
            "last_watching_ai_action",
            "score_prior_action",
        ):
            action = str(fields.get(key) or "").strip().upper()
            if action in {"DROP", "WAIT"}:
                return action
    return ""


def _latency_micro_estimator_relief_signal_candidate(
    code: str,
    *,
    position_tag: str,
) -> dict[str, Any]:
    """Build a spread-relief signal from fresh, accumulated true OFI only.

    The state is intentionally a supplemental source.  A candidate must have
    multiple best-level deltas from the shared WS store; depth-imbalance proxy
    or REST-only snapshots cannot produce this signal.
    """

    enabled = _truthy(os.getenv("KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_ENABLED"))
    all_scalping_enabled = _latency_micro_estimator_all_scalping_enabled()
    result: dict[str, Any] = {
        "latency_spread_relief_micro_estimator_enabled": enabled,
        "latency_spread_relief_micro_estimator_eligible": False,
        "latency_spread_relief_micro_estimator_reason": "disabled" if not enabled else "not_evaluated",
        "latency_spread_relief_micro_estimator_score": 0.0,
        "latency_spread_relief_micro_estimator_source_state": "not_evaluated",
        "latency_spread_relief_micro_estimator_confidence": 0.0,
        "latency_spread_relief_micro_estimator_true_ofi_ewma": 0.0,
        "latency_spread_relief_micro_estimator_pressure_ewma": 50.0,
        "latency_spread_relief_micro_estimator_top_depth_ratio": 0.0,
        "latency_spread_relief_micro_estimator_true_ofi_sample_count": 0,
        "latency_spread_relief_micro_estimator_ws_age_ms": -1.0,
        "latency_spread_relief_micro_estimator_all_scalping_enabled": all_scalping_enabled,
        "latency_spread_relief_micro_estimator_metric_role": "source_quality_gate",
        "latency_spread_relief_micro_estimator_decision_authority": (
            "supplemental_signal_for_existing_latency_spread_relief_canary"
        ),
        "latency_spread_relief_micro_estimator_window_policy": "fresh_ws_runtime_state",
        "latency_spread_relief_micro_estimator_sample_floor": "true_ofi_samples>=configured_min",
        "latency_spread_relief_micro_estimator_primary_decision_metric": "not_applicable_source_supplement",
        "latency_spread_relief_micro_estimator_source_quality_gate": "fresh_ws_true_ofi_and_depth_contract",
        "latency_spread_relief_micro_estimator_runtime_effect": False,
        "latency_spread_relief_micro_estimator_allowed_runtime_apply": False,
        "latency_spread_relief_micro_estimator_forbidden_uses": (
            "standalone_buy,hard_safety_bypass,broker_guard_bypass,threshold_mutation,"
            "provider_route_change,quantity_or_cap_change"
        ),
    }
    if not enabled or not str(code or "").strip():
        if enabled:
            result["latency_spread_relief_micro_estimator_reason"] = "missing_code"
        return result

    allowed_tags = _latency_micro_estimator_allowed_tags()
    normalized_tag = str(position_tag or "").strip().upper()
    result["latency_spread_relief_micro_estimator_allowed_tags"] = ",".join(sorted(allowed_tags))
    if not all_scalping_enabled and allowed_tags and normalized_tag not in allowed_tags:
        result["latency_spread_relief_micro_estimator_reason"] = "tag_not_allowed"
        return result

    now_ts = time.time()
    try:
        snapshot = MICRO_ESTIMATOR_STORE.snapshot(str(code), now_ts=now_ts)
    except Exception:
        result["latency_spread_relief_micro_estimator_reason"] = "snapshot_unavailable"
        return result
    if not isinstance(snapshot, dict):
        result["latency_spread_relief_micro_estimator_reason"] = "snapshot_unavailable"
        return result

    confidence = _to_float(snapshot.get("confidence"), 0.0)
    true_ofi = _to_float(snapshot.get("true_ofi_ewma"), 0.0)
    pressure = _to_float(snapshot.get("pressure_ewma"), 50.0)
    depth_ratio = _to_float(snapshot.get("top_depth_ratio"), 0.0)
    true_sample_count = int(_to_float(snapshot.get("true_ofi_sample_count"), 0.0))
    last_ws_ts = _to_float(snapshot.get("last_ws_ts"), 0.0)
    ws_age_ms = max(0.0, (now_ts - last_ws_ts) * 1000.0) if last_ws_ts > 0 else -1.0
    result.update(
        {
            "latency_spread_relief_micro_estimator_source_state": str(
                snapshot.get("source_state") or "default_prior"
            ),
            "latency_spread_relief_micro_estimator_confidence": round(confidence, 4),
            "latency_spread_relief_micro_estimator_true_ofi_ewma": round(true_ofi, 4),
            "latency_spread_relief_micro_estimator_pressure_ewma": round(pressure, 3),
            "latency_spread_relief_micro_estimator_top_depth_ratio": round(depth_ratio, 4),
            "latency_spread_relief_micro_estimator_true_ofi_sample_count": true_sample_count,
            "latency_spread_relief_micro_estimator_ws_age_ms": round(ws_age_ms, 3),
        }
    )

    min_confidence = max(
        0.70,
        _to_float(os.getenv("KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_MIN_CONFIDENCE"), 0.70),
    )
    min_true_ofi_samples = max(
        8,
        int(
            _to_float(
                os.getenv("KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_MIN_TRUE_OFI_SAMPLES"),
                8.0,
            )
        ),
    )
    min_true_ofi = max(
        0.20,
        _to_float(
            os.getenv("KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_MIN_TRUE_OFI"),
            0.20,
        ),
    )
    min_pressure = max(
        65.0,
        _to_float(
            os.getenv("KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_MIN_PRESSURE"),
            65.0,
        ),
    )
    min_depth_ratio = max(
        1.05,
        _to_float(
            os.getenv("KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_MIN_TOP_DEPTH_RATIO"),
            1.05,
        ),
    )
    freshness_cap_ms = float(_CONFIG.max_ws_age_ms_for_caution or 700)
    max_ws_age_ms = min(
        freshness_cap_ms,
        max(
            1.0,
            _to_float(
                os.getenv("KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MICRO_ESTIMATOR_MAX_WS_AGE_MS"),
                freshness_cap_ms,
            ),
        ),
    )
    result.update(
        {
            "latency_spread_relief_micro_estimator_min_confidence": round(min_confidence, 4),
            "latency_spread_relief_micro_estimator_min_true_ofi_samples": min_true_ofi_samples,
            "latency_spread_relief_micro_estimator_min_true_ofi": round(min_true_ofi, 4),
            "latency_spread_relief_micro_estimator_min_pressure": round(min_pressure, 3),
            "latency_spread_relief_micro_estimator_min_top_depth_ratio": round(min_depth_ratio, 4),
            "latency_spread_relief_micro_estimator_max_ws_age_ms": round(max_ws_age_ms, 3),
        }
    )
    if ws_age_ms < 0 or ws_age_ms > max_ws_age_ms:
        result["latency_spread_relief_micro_estimator_reason"] = "ws_state_stale_or_missing"
        return result
    if true_sample_count < min_true_ofi_samples:
        result["latency_spread_relief_micro_estimator_reason"] = "true_ofi_samples_below_floor"
        return result
    if confidence < min_confidence:
        result["latency_spread_relief_micro_estimator_reason"] = "confidence_below_floor"
        return result
    if true_ofi < min_true_ofi:
        result["latency_spread_relief_micro_estimator_reason"] = "true_ofi_below_floor"
        return result
    if pressure < min_pressure:
        result["latency_spread_relief_micro_estimator_reason"] = "pressure_below_floor"
        return result
    if depth_ratio < min_depth_ratio:
        result["latency_spread_relief_micro_estimator_reason"] = "top_depth_ratio_below_floor"
        return result

    true_ofi_component = _clamp_float(true_ofi / max(min_true_ofi * 2.0, 0.40), 0.0, 1.0)
    pressure_component = _clamp_float((pressure - 50.0) / 20.0, 0.0, 1.0)
    depth_component = _clamp_float((depth_ratio - 1.0) / 0.25, 0.0, 1.0)
    confidence_component = _clamp_float(confidence, 0.0, 1.0)
    score = _clamp_float(
        50.0
        + (20.0 * true_ofi_component)
        + (15.0 * pressure_component)
        + (10.0 * depth_component)
        + (15.0 * confidence_component),
        0.0,
        100.0,
    )
    result.update(
        {
            "latency_spread_relief_micro_estimator_eligible": True,
            "latency_spread_relief_micro_estimator_reason": "fresh_true_ofi_support",
            "latency_spread_relief_micro_estimator_score": round(score, 3),
        }
    )
    return result


def _latency_micro_relief_signal_candidate(
    stock: dict[str, Any] | None,
    ws_data: dict[str, Any] | None,
) -> tuple[float | None, str, str]:
    for source, prefix in ((ws_data, "ws"), (stock, "stock")):
        fields = source if isinstance(source, dict) else {}
        if not fields:
            continue
        ready = _truthy(fields.get("orderbook_micro_ready")) or str(
            fields.get("orderbook_micro_reason") or ""
        ).strip().lower() == "ready"
        if not ready:
            continue
        healthy_raw = fields.get("orderbook_micro_observer_healthy")
        if healthy_raw not in (None, "", "None") and not _truthy(healthy_raw):
            continue
        snapshot_age_ms = _to_float(
            fields.get("orderbook_micro_snapshot_age_ms"),
            _to_float(fields.get("orderbook_micro_observer_last_quote_age_ms"), 999999.0),
        )
        if snapshot_age_ms > float(_CONFIG.max_ws_age_ms_for_caution or 0):
            continue
        sample_count = int(_to_float(fields.get("orderbook_micro_sample_quote_count"), 0.0))
        min_samples = int(_to_float(fields.get("orderbook_micro_micro_z_min_samples"), 20.0))
        if sample_count < max(3, min_samples):
            continue

        ofi_z = _to_float(fields.get("orderbook_micro_ofi_z"), -999999.0)
        ofi_norm = _to_float(fields.get("orderbook_micro_ofi_norm"), -999999.0)
        bull_threshold = abs(_to_float(fields.get("orderbook_micro_ofi_bull_threshold"), 1.2)) or 1.2
        if ofi_z > -999998.0:
            ofi_component = _clamp_float(ofi_z / bull_threshold, -1.0, 1.0)
        elif ofi_norm > -999998.0:
            ofi_component = _clamp_float(ofi_norm / bull_threshold, -1.0, 1.0)
        else:
            ofi_component = 0.0

        qi_value = _to_float(
            fields.get("orderbook_micro_qi_ewma"),
            _to_float(fields.get("orderbook_micro_qi"), -999999.0),
        )
        qi_component = 0.0
        if qi_value > -999998.0:
            qi_component = _clamp_float((qi_value - 0.50) / 0.20, -1.0, 1.0)

        score = _clamp_float(50.0 + (25.0 * ofi_component) + (25.0 * qi_component), 0.0, 100.0)
        return score, f"{prefix}.orderbook_micro_ofi_qi", ""
    return None, "", "orderbook_micro_not_ready"


def _latency_relief_signal_provenance(
    *,
    code: str,
    signal_strength: Any,
    stock: dict[str, Any] | None,
    ws_data: dict[str, Any] | None,
) -> dict[str, Any]:
    input_score = _normalize_signal_score(signal_strength)
    stock_score, stock_source = _score_candidate_from_source(stock, "stock")
    ws_score, ws_source = _score_candidate_from_source(ws_data, "ws")
    explicit_negative_ai_action = _latency_explicit_negative_ai_action(stock, ws_data)
    stock_fields = stock if isinstance(stock, dict) else {}
    estimator = _latency_micro_estimator_relief_signal_candidate(
        code,
        position_tag=str(
            stock_fields.get("position_tag")
            or stock_fields.get("entry_momentum_tag")
            or stock_fields.get("momentum_tag")
            or ""
        ),
    )
    micro_score, micro_source, micro_gap = _latency_micro_relief_signal_candidate(stock, ws_data)
    candidate_score: float | None = None
    candidate_source = ""
    for score, score_source in ((stock_score, stock_source), (ws_score, ws_source)):
        if score is not None and score > 0:
            candidate_score = score
            candidate_source = score_source
            break
    if candidate_score is None:
        candidate_score = stock_score if stock_score is not None else ws_score
        candidate_source = stock_source or ws_source

    if explicit_negative_ai_action:
        state = "explicit_negative_ai"
        source = f"explicit_ai_{explicit_negative_ai_action.lower()}"
        gap = "explicit_ai_wait_or_drop"
        effective_score = 0.0
    elif input_score > 0:
        state = "fresh"
        source = "input_signal_strength"
        gap = ""
        effective_score = input_score
    elif estimator.get("latency_spread_relief_micro_estimator_eligible"):
        state = "fresh"
        source = "micro_estimator.true_ofi_ewma"
        gap = ""
        effective_score = _to_float(estimator.get("latency_spread_relief_micro_estimator_score"), 0.0)
    elif micro_score is not None:
        state = "fresh"
        source = micro_source
        gap = ""
        effective_score = micro_score
    elif candidate_score is None:
        state = "missing"
        source = "missing"
        gap = "signal_strength_missing"
        effective_score = 0.0
    elif candidate_score > 0:
        state = "source_gap"
        source = "input_signal_strength_zero"
        gap = "prior_ai_available_but_signal_strength_zero"
        effective_score = 0.0
    else:
        state = "unusable"
        source = "input_signal_strength_zero"
        gap = "candidate_ai_score_zero_or_unusable"
        effective_score = 0.0

    return {
        "latency_spread_relief_signal_score": round(float(effective_score), 3),
        "latency_spread_relief_signal_score_source": source,
        "latency_spread_relief_signal_source_quality_state": state,
        "latency_spread_relief_candidate_ai_score": (
            round(float(candidate_score), 3) if candidate_score is not None else 0.0
        ),
        "latency_spread_relief_candidate_ai_score_source": candidate_source,
        "latency_spread_relief_source_quality_gap": gap,
        "latency_spread_relief_explicit_negative_ai_action": explicit_negative_ai_action or "",
        "latency_spread_relief_orderbook_micro_gap": micro_gap,
        **estimator,
    }


def _latency_spread_block_buckets(
    *,
    latency_status,
    latest_price: int,
    best_bid: int,
    best_ask: int,
    signal_source_quality_state: str,
) -> dict[str, Any]:
    spread_ratio = _to_float(getattr(latency_status, "spread_ratio", 0.0), 0.0)
    spread_bps = round(float(spread_ratio) * 10000.0, 3)
    spread_ticks = _compute_spread_ticks(best_ask, best_bid)
    quote_stale = bool(getattr(latency_status, "quote_stale", False))
    ws_age_ms = int(getattr(latency_status, "ws_age_ms", 0) or 0)
    max_ws_age_caution = int(_CONFIG.max_ws_age_ms_for_caution or 0)

    if spread_ratio <= 0:
        price_bucket = "not_spread_block"
    elif quote_stale or (max_ws_age_caution > 0 and ws_age_ms > max_ws_age_caution):
        price_bucket = "stale_mixed_spread"
    elif int(latest_price or best_bid or 0) < 10000 and spread_ticks >= 5:
        price_bucket = "low_price_tick_wide"
    elif spread_ratio >= 0.0100 or spread_ticks >= 8:
        price_bucket = "true_wide_spread"
    elif spread_ratio > _to_float(_CONFIG.max_spread_ratio_for_caution, 0.0):
        price_bucket = "spread_above_caution"
    else:
        price_bucket = "spread_not_above_caution"

    if signal_source_quality_state in {"missing", "unusable", "source_gap", "explicit_negative_ai"}:
        signal_bucket = f"signal_{signal_source_quality_state}"
    else:
        signal_bucket = "signal_fresh"

    block_bucket = price_bucket
    if price_bucket not in {"not_spread_block", "stale_mixed_spread"} and signal_bucket != "signal_fresh":
        block_bucket = f"{price_bucket}|{signal_bucket}"

    return {
        "latency_spread_block_bucket": block_bucket,
        "latency_spread_block_price_bucket": price_bucket,
        "latency_spread_block_signal_context_bucket": signal_bucket,
        "latency_spread_block_spread_bps": spread_bps,
        "latency_spread_block_spread_ticks": spread_ticks,
    }


def _latency_false_negative_remeasure_enabled() -> bool:
    raw = os.getenv("KORSTOCKSCAN_LATENCY_FALSE_NEGATIVE_REMEASURE_ENABLED")
    return True if raw is None else _truthy(raw)


def _latency_false_negative_report_ready(stock: dict[str, Any] | None) -> bool:
    fields = stock if isinstance(stock, dict) else {}
    grade = str(
        fields.get("latency_false_negative_canary_grade")
        or fields.get("latency_false_negative_report_canary_grade")
        or fields.get("latency_false_negative_remeasure_grade")
        or ""
    ).strip()
    return grade == "ready_for_recheck"


def _latency_true_ofi_direct_canary_enabled() -> bool:
    raw = os.getenv("KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_ENABLED")
    return True if raw is None else _truthy(raw)


def _latency_opportunity_price_delta_pct(
    stock: dict[str, Any] | None,
    ws_data: dict[str, Any] | None,
) -> float:
    fields: list[Any] = []
    for source in (stock or {}, ws_data or {}):
        fields.extend(
            [
                source.get("price_delta_since_first_seen_pct"),
                source.get("comparable_flu_delta_since_first_seen"),
                source.get("fluctuation"),
                source.get("fluctuation_rate"),
                source.get("change_rate"),
            ]
        )
    values = [_to_float(value, 0.0) for value in fields if value not in (None, "", "-")]
    return max(values) if values else 0.0


def _latency_rising_missed_lineage(stock: dict[str, Any] | None) -> bool:
    fields = stock if isinstance(stock, dict) else {}
    source_signature = str(fields.get("source_signature") or "").upper()
    promotion_reason = str(fields.get("scanner_promotion_reason") or "").lower()
    forced_reason = str(fields.get("forced_entry_reason") or "").lower()
    lineage = str(fields.get("rising_missed_lineage") or "").strip().lower()
    return (
        _truthy(fields.get("rising_missed_entry_lineage"))
        or _truthy(fields.get("rising_missed_one_share_entry_forced"))
        or _truthy(fields.get("rising_missed_one_share_scout"))
        or bool(lineage)
        or "rising_missed" in promotion_reason
        or "rising_missed" in forced_reason
        or "LOW_REBOUND_RISING_MISSED" in source_signature
    )


def _latency_opportunity_source_support(stock: dict[str, Any] | None, ws_data: dict[str, Any] | None) -> bool:
    markers = {
        "PRICE_JUMP_START",
        "NEW_HIGH_CONFIRMATION",
        "REALTIME_RANK_START",
        "VALUE_TOP",
        "VOLUME_SURGE_POSITIVE",
    }
    for source in (stock or {}, ws_data or {}):
        source_signature = str(source.get("source_signature") or "").upper()
        if any(marker in source_signature for marker in markers):
            return True
    return False


def _first_present_float(*values: Any, default: float = 0.0) -> float:
    for value in values:
        if value not in (None, "", "-"):
            return _to_float(value, default)
    return default


def _first_present_int(*values: Any, default: int = 0) -> int:
    for value in values:
        if value not in (None, "", "-"):
            return int(_to_float(value, float(default)))
    return default


def _signed_trade_side_and_volume_from_tick(tick: Any) -> tuple[str, float]:
    if not isinstance(tick, dict):
        return "UNKNOWN", 0.0
    values = tick.get("values") if isinstance(tick.get("values"), dict) else {}
    raw_signed_qty = (
        tick.get("aggressor_aux_raw_15")
        or tick.get("signed_trade_volume")
        or tick.get("signed_qty")
        or values.get("15")
    )
    raw_text = str(raw_signed_qty or "").replace(",", "").strip()
    if raw_text.startswith("+"):
        return "BUY", abs(_to_float(raw_text, 0.0))
    if raw_text.startswith("-"):
        return "SELL", abs(_to_float(raw_text, 0.0))
    if (
        str(tick.get("aggressor_source") or "") == "kiwoom_rest_ka10084_signed_trade_qty"
        and str(tick.get("aggressor_side") or "").upper() in {"BUY", "SELL"}
        and raw_text
    ):
        return str(tick.get("aggressor_side") or "").upper(), abs(_to_float(raw_text, 0.0))
    return "UNKNOWN", 0.0


def _iter_signed_tape_ticks(*sources: dict[str, Any]) -> list[dict[str, Any]]:
    ticks: list[dict[str, Any]] = []
    for source in sources:
        if not isinstance(source, dict):
            continue
        recent_ticks = source.get("recent_trade_ticks")
        recent_added = False
        if recent_ticks is not None:
            for tick in recent_ticks:
                if isinstance(tick, dict):
                    ticks.append(tick)
                    recent_added = True
        rest_ticks = source.get("rest_signed_trade_ticks")
        if rest_ticks is not None:
            for tick in rest_ticks:
                if isinstance(tick, dict):
                    ticks.append(tick)
                    recent_added = True
        if recent_added:
            continue
        last_tick = source.get("last_trade_tick")
        if isinstance(last_tick, dict):
            ticks.append(last_tick)
    return ticks


def _latency_signed_tape_fields(
    stock: dict[str, Any] | None,
    ws_data: dict[str, Any] | None,
) -> dict[str, Any]:
    item = stock if isinstance(stock, dict) else {}
    ws = ws_data if isinstance(ws_data, dict) else {}
    window = max(
        1,
        int(_to_float(os.getenv("KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_SIGNED_TAPE_WINDOW"), 5.0)),
    )
    min_samples = max(
        1,
        int(_to_float(os.getenv("KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_SIGNED_TAPE_MIN_SAMPLES"), 3.0)),
    )
    max_buy_ratio = max(
        0.0,
        min(
            100.0,
            _to_float(os.getenv("KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_SIGNED_TAPE_MAX_BUY_RATIO"), 45.0),
        ),
    )
    rows: list[tuple[str, float]] = []
    for tick in _iter_signed_tape_ticks(ws, item):
        side, volume = _signed_trade_side_and_volume_from_tick(tick)
        if side in {"BUY", "SELL"} and volume > 0:
            rows.append((side, volume))
        if len(rows) >= window:
            break

    buy_volume = sum(volume for side, volume in rows if side == "BUY")
    sell_volume = sum(volume for side, volume in rows if side == "SELL")
    buy_count = sum(1 for side, _volume in rows if side == "BUY")
    sell_count = sum(1 for side, _volume in rows if side == "SELL")
    sample_count = len(rows)
    total_volume = buy_volume + sell_volume
    buy_ratio = (buy_volume / total_volume * 100.0) if total_volume > 0 else 50.0
    sell_dominated = bool(
        sample_count >= min_samples
        and sell_count > buy_count
        and sell_volume > buy_volume
        and buy_ratio <= max_buy_ratio
    )
    latest_side = rows[0][0] if rows else "UNKNOWN"
    latest_buy_single = _first_present_float(ws.get("buy_exec_single"), item.get("buy_exec_single"), default=0.0)
    latest_sell_single = _first_present_float(ws.get("sell_exec_single"), item.get("sell_exec_single"), default=0.0)
    latest_single_sell_dominated = latest_sell_single > latest_buy_single and latest_sell_single > 0
    return {
        "latency_true_ofi_direct_canary_signed_tape_window": window,
        "latency_true_ofi_direct_canary_signed_tape_min_samples": min_samples,
        "latency_true_ofi_direct_canary_signed_tape_max_buy_ratio": round(max_buy_ratio, 3),
        "latency_true_ofi_direct_canary_signed_tape_sample_count": sample_count,
        "latency_true_ofi_direct_canary_signed_tape_buy_count": buy_count,
        "latency_true_ofi_direct_canary_signed_tape_sell_count": sell_count,
        "latency_true_ofi_direct_canary_signed_tape_buy_volume": int(buy_volume),
        "latency_true_ofi_direct_canary_signed_tape_sell_volume": int(sell_volume),
        "latency_true_ofi_direct_canary_signed_tape_net_buy_volume": int(buy_volume - sell_volume),
        "latency_true_ofi_direct_canary_signed_tape_buy_ratio": round(float(buy_ratio), 3),
        "latency_true_ofi_direct_canary_signed_tape_latest_side": latest_side,
        "latency_true_ofi_direct_canary_signed_tape_sell_dominated": sell_dominated,
        "latency_true_ofi_direct_canary_signed_tape_latest_buy_single": int(latest_buy_single),
        "latency_true_ofi_direct_canary_signed_tape_latest_sell_single": int(latest_sell_single),
        "latency_true_ofi_direct_canary_signed_tape_latest_single_sell_dominated": bool(latest_single_sell_dominated),
    }


def _latency_direct_canary_tape_pressure_fields(
    stock: dict[str, Any] | None,
    ws_data: dict[str, Any] | None,
) -> dict[str, Any]:
    item = stock if isinstance(stock, dict) else {}
    ws = ws_data if isinstance(ws_data, dict) else {}
    min_buy_pressure = max(
        0.0,
        _to_float(os.getenv("KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_MIN_BUY_PRESSURE"), 55.0),
    )
    min_trusted_ticks = max(
        1,
        int(_to_float(os.getenv("KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_MIN_TRUSTED_TICKS"), 3.0)),
    )
    pressure_usable = _tick_aggressor_pressure_usable_from_fields(ws) or _tick_aggressor_pressure_usable_from_fields(item)
    trusted_count = max(
        _first_present_int(ws.get("tick_aggressor_trusted_count"), ws.get("microstructure_reaction_tick_aggressor_trusted_count")),
        _first_present_int(item.get("tick_aggressor_trusted_count"), item.get("microstructure_reaction_tick_aggressor_trusted_count")),
    )
    buy_pressure = _latency_buy_pressure_value(ws, item)
    buy_exec_volume = _first_present_float(ws.get("buy_exec_volume"), item.get("buy_exec_volume"), default=0.0)
    sell_exec_volume = _first_present_float(ws.get("sell_exec_volume"), item.get("sell_exec_volume"), default=0.0)
    net_buy_exec_volume = _first_present_float(
        ws.get("net_buy_exec_volume"),
        item.get("net_buy_exec_volume"),
        default=(buy_exec_volume - sell_exec_volume) if (buy_exec_volume > 0 or sell_exec_volume > 0) else 0.0,
    )
    large_sell = _truthy(ws.get("large_sell_print_detected")) or _truthy(item.get("large_sell_print_detected"))
    signed_tape_fields = _latency_signed_tape_fields(item, ws)
    fields = {
        "latency_true_ofi_direct_canary_min_buy_pressure": round(min_buy_pressure, 3),
        "latency_true_ofi_direct_canary_min_trusted_ticks": min_trusted_ticks,
        "latency_true_ofi_direct_canary_tape_pressure_usable": bool(pressure_usable),
        "latency_true_ofi_direct_canary_tape_trusted_count": trusted_count,
        "latency_true_ofi_direct_canary_tape_buy_pressure": round(float(buy_pressure or 0.0), 3),
        "latency_true_ofi_direct_canary_tape_buy_exec_volume": int(buy_exec_volume),
        "latency_true_ofi_direct_canary_tape_sell_exec_volume": int(sell_exec_volume),
        "latency_true_ofi_direct_canary_tape_net_buy_exec_volume": int(net_buy_exec_volume),
        "latency_true_ofi_direct_canary_large_sell_print_detected": bool(large_sell),
        "latency_true_ofi_direct_canary_tape_support_ok": False,
        "latency_true_ofi_direct_canary_tape_block_reason": "not_evaluated",
        **signed_tape_fields,
    }
    if large_sell:
        fields["latency_true_ofi_direct_canary_tape_block_reason"] = "large_sell_print_detected"
        return fields
    if fields["latency_true_ofi_direct_canary_signed_tape_sell_dominated"]:
        fields["latency_true_ofi_direct_canary_tape_block_reason"] = "signed_tape_sell_dominated"
        return fields
    if not pressure_usable or trusted_count < min_trusted_ticks:
        fields["latency_true_ofi_direct_canary_tape_block_reason"] = "tape_pressure_unavailable"
        return fields
    if (buy_exec_volume > 0 or sell_exec_volume > 0) and net_buy_exec_volume <= 0:
        fields["latency_true_ofi_direct_canary_tape_block_reason"] = "sell_dominated_tape"
        return fields
    if buy_pressure < min_buy_pressure:
        fields["latency_true_ofi_direct_canary_tape_block_reason"] = "buy_pressure_below_floor"
        return fields
    fields["latency_true_ofi_direct_canary_tape_support_ok"] = True
    fields["latency_true_ofi_direct_canary_tape_block_reason"] = "tape_support_ok"
    return fields


def _latency_false_negative_runtime_estimator_context(code: str) -> dict[str, Any]:
    context = {
        "latency_false_negative_remeasure_source_state": "not_evaluated",
        "latency_false_negative_remeasure_true_ofi_ewma": 0.0,
        "latency_false_negative_remeasure_true_ofi_sample_count": 0,
        "latency_false_negative_remeasure_ws_age_ms": -1.0,
        "latency_false_negative_remeasure_estimator_confidence": 0.0,
    }
    if not str(code or "").strip():
        context["latency_false_negative_remeasure_source_state"] = "missing_code"
        return context
    now_ts = time.time()
    try:
        snapshot = MICRO_ESTIMATOR_STORE.snapshot(str(code), now_ts=now_ts)
    except Exception:
        context["latency_false_negative_remeasure_source_state"] = "snapshot_unavailable"
        return context
    if not isinstance(snapshot, dict):
        context["latency_false_negative_remeasure_source_state"] = "snapshot_unavailable"
        return context
    last_ws_ts = _to_float(snapshot.get("last_ws_ts"), 0.0)
    ws_age_ms = max(0.0, (now_ts - last_ws_ts) * 1000.0) if last_ws_ts > 0 else -1.0
    context.update(
        {
            "latency_false_negative_remeasure_source_state": str(
                snapshot.get("source_state") or "default_prior"
            ),
            "latency_false_negative_remeasure_true_ofi_ewma": round(
                _to_float(snapshot.get("true_ofi_ewma"), 0.0), 4
            ),
            "latency_false_negative_remeasure_true_ofi_sample_count": int(
                _to_float(snapshot.get("true_ofi_sample_count"), 0.0)
            ),
            "latency_false_negative_remeasure_ws_age_ms": round(ws_age_ms, 3),
            "latency_false_negative_remeasure_estimator_confidence": round(
                _to_float(snapshot.get("confidence"), 0.0),
                4,
            ),
        }
    )
    return context


def _latency_false_negative_bounded_remeasure_fields(
    *,
    code: str,
    stock: dict[str, Any] | None,
    ws_data: dict[str, Any] | None,
    strategy_id: str,
    policy_decision: EntryDecision,
    effective_decision: EntryDecision,
    latency_status,
    danger_reasons: list[str] | None,
    spread_bps: float,
) -> dict[str, Any]:
    enabled = _latency_false_negative_remeasure_enabled()
    estimator_context = _latency_false_negative_runtime_estimator_context(code) if enabled else {}
    min_review_score_pct = max(
        0.0,
        _to_float(os.getenv("KORSTOCKSCAN_LATENCY_FALSE_NEGATIVE_REMEASURE_MIN_REVIEW_SCORE_PCT"), 2.0),
    )
    min_samples = max(
        1,
        int(_to_float(os.getenv("KORSTOCKSCAN_LATENCY_FALSE_NEGATIVE_REMEASURE_MIN_TRUE_OFI_SAMPLES"), 100.0)),
    )
    max_ws_age_ms = max(
        1.0,
        _to_float(os.getenv("KORSTOCKSCAN_LATENCY_FALSE_NEGATIVE_REMEASURE_MAX_WS_AGE_MS"), 150.0),
    )
    true_ofi_floor = _to_float(
        os.getenv("KORSTOCKSCAN_LATENCY_FALSE_NEGATIVE_REMEASURE_TRUE_OFI_FLOOR"),
        -0.10,
    )
    max_spread_bps = max(
        1.0,
        _to_float(os.getenv("KORSTOCKSCAN_LATENCY_FALSE_NEGATIVE_REMEASURE_MAX_SPREAD_BPS"), 90.0),
    )
    fields: dict[str, Any] = {
        "latency_false_negative_remeasure_enabled": enabled,
        "latency_false_negative_remeasure_candidate": False,
        "latency_false_negative_remeasure_candidate_source": "none",
        "latency_false_negative_remeasure_enqueued": False,
        "latency_false_negative_remeasure_reason": "disabled" if not enabled else "not_evaluated",
        "latency_false_negative_remeasure_cohort": "not_applicable",
        "latency_false_negative_remeasure_grade": "not_applicable",
        "latency_false_negative_remeasure_next_action": "none",
        "latency_false_negative_remeasure_metric_role": "source_only_runtime_remeasure_enqueue",
        "latency_false_negative_remeasure_decision_authority": _LATENCY_FALSE_NEGATIVE_REMEASURE_AUTHORITY,
        "latency_false_negative_remeasure_window_policy": (
            "same_day_ready_for_recheck_report_plus_fresh_runtime_state"
        ),
        "latency_false_negative_remeasure_sample_floor": (
            "report_ready_for_recheck_and_runtime_true_ofi_samples>=floor"
        ),
        "latency_false_negative_remeasure_primary_decision_metric": (
            "ready_for_recheck_grade_with_runtime_spread_true_ofi_freshness"
        ),
        "latency_false_negative_remeasure_source_quality_gate": (
            "fresh_quote_and_fresh_true_ofi_with_bounded_spread_or_bounded_report_spread_only"
        ),
        "latency_false_negative_remeasure_runtime_effect": False,
        "latency_false_negative_remeasure_allowed_runtime_apply": False,
        "latency_false_negative_remeasure_forbidden_uses": _LATENCY_FALSE_NEGATIVE_REMEASURE_FORBIDDEN_USES,
        "latency_false_negative_remeasure_min_review_score_pct": round(min_review_score_pct, 3),
        "latency_false_negative_remeasure_min_true_ofi_samples": min_samples,
        "latency_false_negative_remeasure_max_ws_age_ms": round(max_ws_age_ms, 3),
        "latency_false_negative_remeasure_true_ofi_floor": round(true_ofi_floor, 4),
        "latency_false_negative_remeasure_max_spread_bps": round(max_spread_bps, 3),
        "latency_false_negative_remeasure_spread_bps": round(float(spread_bps or 0.0), 3),
        **estimator_context,
    }
    if not enabled:
        return fields
    if str(strategy_id or "").upper() not in {"SCALPING", "SCALP"}:
        fields["latency_false_negative_remeasure_reason"] = "non_scalping"
        return fields
    if policy_decision != EntryDecision.REJECT_DANGER or effective_decision != EntryDecision.REJECT_DANGER:
        fields["latency_false_negative_remeasure_reason"] = "not_blocked_by_latency_danger"
        return fields
    if bool(getattr(latency_status, "quote_stale", False)):
        fields["latency_false_negative_remeasure_reason"] = "quote_stale"
        return fields
    explicit_negative_ai_action = _latency_explicit_negative_ai_action(stock, ws_data)
    if explicit_negative_ai_action:
        fields["latency_false_negative_remeasure_reason"] = (
            f"explicit_ai_{explicit_negative_ai_action.lower()}_veto"
        )
        return fields

    normalized_reasons = _normalized_reason_set(danger_reasons or _latency_danger_reasons(latency_status))
    spread_reasons = {
        "spread_above_caution_below_guard_cap",
        "spread_above_caution",
        "spread_too_wide",
    }
    if not normalized_reasons or not normalized_reasons.issubset(spread_reasons):
        fields["latency_false_negative_remeasure_reason"] = "non_spread_latency_danger"
        return fields
    if float(spread_bps or 0.0) > max_spread_bps:
        fields["latency_false_negative_remeasure_reason"] = "spread_bps_above_remeasure_cap"
        fields["latency_false_negative_remeasure_grade"] = "observe_wide_spread"
        return fields

    true_ofi = _to_float(fields.get("latency_false_negative_remeasure_true_ofi_ewma"), 0.0)
    sample_count = int(_to_float(fields.get("latency_false_negative_remeasure_true_ofi_sample_count"), 0.0))
    ws_age_ms = _to_float(fields.get("latency_false_negative_remeasure_ws_age_ms"), -1.0)
    true_ofi_ready = (
        sample_count >= min_samples
        and 0.0 <= ws_age_ms <= max_ws_age_ms
        and true_ofi >= true_ofi_floor
    )
    if not _latency_false_negative_report_ready(stock):
        fields["latency_false_negative_remeasure_reason"] = "report_ready_for_recheck_missing"
        return fields
    report_cohort = str(
        (stock or {}).get("latency_false_negative_canary_cohort")
        or (stock or {}).get("latency_false_negative_report_canary_cohort")
        or ""
    )
    if not true_ofi_ready and "spread_only" not in report_cohort:
        fields["latency_false_negative_remeasure_reason"] = "runtime_true_ofi_recheck_not_ready"
        fields["latency_false_negative_remeasure_grade"] = "hold_sample"
        return fields

    fields.update(
        {
            "latency_false_negative_remeasure_candidate": True,
            "latency_false_negative_remeasure_enqueued": True,
            "latency_false_negative_remeasure_candidate_source": "intraday_feedback_report",
            "latency_false_negative_remeasure_reason": (
                "true_ofi_near_zero_or_positive_with_fresh_ws"
                if true_ofi_ready
                else "spread_only_report_ready_with_bounded_spread"
            ),
            "latency_false_negative_remeasure_cohort": (
                "true_ofi_near_zero_false_negative"
                if true_ofi_ready
                else "spread_only_false_negative"
            ),
            "latency_false_negative_remeasure_grade": "ready_for_recheck",
            "latency_false_negative_remeasure_next_action": "bounded_latency_remeasure_enqueue",
        }
    )
    return fields


def _latency_true_ofi_direct_canary_fields(
    *,
    stock: dict[str, Any] | None,
    ws_data: dict[str, Any] | None,
    strategy_id: str,
    policy_decision: EntryDecision,
    effective_decision: EntryDecision,
    latency_status,
    danger_reasons: list[str] | None,
    spread_bps: float,
    signal_score: float,
    micro_estimator_reason: str,
    estimator_context: dict[str, Any],
    danger_relief_forbidden: bool,
) -> dict[str, Any]:
    enabled = _latency_true_ofi_direct_canary_enabled()
    min_samples = max(
        1,
        int(_to_float(os.getenv("KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_MIN_SAMPLES"), 75.0)),
    )
    max_ws_age_ms = max(
        1.0,
        _to_float(os.getenv("KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_MAX_WS_AGE_MS"), 180.0),
    )
    max_spread_bps = max(
        1.0,
        _to_float(os.getenv("KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_MAX_SPREAD_BPS"), 90.0),
    )
    min_true_ofi = _to_float(os.getenv("KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_MIN_TRUE_OFI"), -0.09)
    max_true_ofi = _to_float(os.getenv("KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_MAX_TRUE_OFI"), 0.12)
    min_signal_score = max(
        0.0,
        _to_float(os.getenv("KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_MIN_SIGNAL_SCORE"), 70.0),
    )
    min_delta_pct = max(
        0.0,
        _to_float(os.getenv("KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_MIN_DELTA_PCT"), 3.0),
    )
    true_ofi = _to_float(estimator_context.get("latency_false_negative_remeasure_true_ofi_ewma"), 0.0)
    sample_count = int(_to_float(estimator_context.get("latency_false_negative_remeasure_true_ofi_sample_count"), 0.0))
    ws_age_ms = _to_float(estimator_context.get("latency_false_negative_remeasure_ws_age_ms"), -1.0)
    source_state = str(estimator_context.get("latency_false_negative_remeasure_source_state") or "").strip().lower()
    delta_pct = _latency_opportunity_price_delta_pct(stock, ws_data)
    opportunity_supported = (
        float(signal_score or 0.0) >= min_signal_score
        or delta_pct >= min_delta_pct
        or _latency_opportunity_source_support(stock, ws_data)
    )
    tape_fields = _latency_direct_canary_tape_pressure_fields(stock, ws_data)
    micro_state = str(
        (ws_data or {}).get("orderbook_micro_state")
        or (stock or {}).get("orderbook_micro_state")
        or ""
    ).strip().lower()
    micro_reason = str(micro_estimator_reason or "").strip().lower()
    derived_true_ofi_below_floor = (
        micro_reason == "true_ofi_below_floor"
        or (
            micro_reason in {"", "disabled", "not_evaluated"}
            and true_ofi < 0.20
        )
    )
    fields: dict[str, Any] = {
        "latency_true_ofi_direct_canary_enabled": enabled,
        "latency_true_ofi_direct_canary_applied": False,
        "latency_true_ofi_direct_canary_reason": "disabled" if not enabled else "not_evaluated",
        "latency_true_ofi_direct_canary_decision_authority": _LATENCY_TRUE_OFI_DIRECT_CANARY_AUTHORITY,
        "latency_true_ofi_direct_canary_runtime_effect": False,
        "latency_true_ofi_direct_canary_allowed_runtime_apply": False,
        "latency_true_ofi_direct_canary_forbidden_uses": _LATENCY_TRUE_OFI_DIRECT_CANARY_FORBIDDEN_USES,
        "latency_true_ofi_direct_canary_relief_runtime_enabled": not danger_relief_forbidden,
        "latency_true_ofi_direct_canary_min_samples": min_samples,
        "latency_true_ofi_direct_canary_max_ws_age_ms": round(max_ws_age_ms, 3),
        "latency_true_ofi_direct_canary_max_spread_bps": round(max_spread_bps, 3),
        "latency_true_ofi_direct_canary_min_true_ofi": round(min_true_ofi, 4),
        "latency_true_ofi_direct_canary_max_true_ofi": round(max_true_ofi, 4),
        "latency_true_ofi_direct_canary_min_signal_score": round(min_signal_score, 3),
        "latency_true_ofi_direct_canary_min_delta_pct": round(min_delta_pct, 3),
        "latency_true_ofi_direct_canary_signal_score": round(float(signal_score or 0.0), 3),
        "latency_true_ofi_direct_canary_price_delta_pct": round(delta_pct, 4),
        "latency_true_ofi_direct_canary_spread_bps": round(float(spread_bps or 0.0), 3),
        "latency_true_ofi_direct_canary_true_ofi_ewma": round(true_ofi, 4),
        "latency_true_ofi_direct_canary_true_ofi_sample_count": sample_count,
        "latency_true_ofi_direct_canary_ws_age_ms": round(ws_age_ms, 3),
        "latency_true_ofi_direct_canary_source_state": source_state or "not_evaluated",
        "latency_true_ofi_direct_canary_micro_reason": micro_reason or "not_evaluated",
        "latency_true_ofi_direct_canary_derived_reason": (
            "true_ofi_below_floor" if derived_true_ofi_below_floor else "not_true_ofi_below_floor"
        ),
        "latency_true_ofi_direct_canary_opportunity_supported": bool(opportunity_supported),
        "latency_true_ofi_direct_canary_rising_missed_lineage": _latency_rising_missed_lineage(stock),
        "latency_true_ofi_direct_canary_micro_state": micro_state or "-",
        **tape_fields,
    }
    if not enabled:
        return fields
    if danger_relief_forbidden:
        fields["latency_true_ofi_direct_canary_reason"] = "latency_relief_runtime_disabled"
        return fields
    if str(strategy_id or "").upper() not in {"SCALPING", "SCALP"}:
        fields["latency_true_ofi_direct_canary_reason"] = "non_scalping"
        return fields
    if not fields["latency_true_ofi_direct_canary_rising_missed_lineage"]:
        fields["latency_true_ofi_direct_canary_reason"] = "non_rising_missed_lineage"
        return fields
    if policy_decision != EntryDecision.REJECT_DANGER or effective_decision != EntryDecision.REJECT_DANGER:
        fields["latency_true_ofi_direct_canary_reason"] = "not_blocked_by_latency_danger"
        return fields
    if bool(getattr(latency_status, "quote_stale", False)):
        fields["latency_true_ofi_direct_canary_reason"] = "quote_stale"
        return fields
    explicit_negative_ai_action = _latency_explicit_negative_ai_action(stock, ws_data)
    if explicit_negative_ai_action:
        fields["latency_true_ofi_direct_canary_reason"] = f"explicit_ai_{explicit_negative_ai_action.lower()}_veto"
        return fields
    normalized_reasons = _normalized_reason_set(danger_reasons or _latency_danger_reasons(latency_status))
    spread_reasons = {
        "spread_above_caution_below_guard_cap",
        "spread_above_caution",
        "spread_too_wide",
    }
    if not normalized_reasons or not normalized_reasons.issubset(spread_reasons):
        fields["latency_true_ofi_direct_canary_reason"] = "non_spread_latency_danger"
        return fields
    if not derived_true_ofi_below_floor:
        fields["latency_true_ofi_direct_canary_reason"] = "not_true_ofi_below_floor"
        return fields
    if source_state in {"", "not_evaluated", "missing_code", "snapshot_unavailable"}:
        fields["latency_true_ofi_direct_canary_reason"] = "true_ofi_source_unavailable"
        return fields
    if sample_count < min_samples:
        fields["latency_true_ofi_direct_canary_reason"] = "true_ofi_samples_below_floor"
        return fields
    if not (0.0 <= ws_age_ms <= max_ws_age_ms):
        fields["latency_true_ofi_direct_canary_reason"] = "ws_age_above_direct_canary_cap"
        return fields
    if float(spread_bps or 0.0) > max_spread_bps:
        fields["latency_true_ofi_direct_canary_reason"] = "spread_bps_above_direct_canary_cap"
        return fields
    if not (min_true_ofi <= true_ofi <= max_true_ofi):
        fields["latency_true_ofi_direct_canary_reason"] = "true_ofi_outside_near_zero_band"
        return fields
    if micro_state in {"bearish", "strong_bearish"}:
        fields["latency_true_ofi_direct_canary_reason"] = "bearish_orderbook_micro_state"
        return fields
    if not opportunity_supported:
        fields["latency_true_ofi_direct_canary_reason"] = "opportunity_signal_below_floor"
        return fields
    if not fields["latency_true_ofi_direct_canary_tape_support_ok"]:
        fields["latency_true_ofi_direct_canary_reason"] = str(
            fields.get("latency_true_ofi_direct_canary_tape_block_reason")
            or "tape_pressure_unavailable"
        )
        return fields
    fields.update(
        {
            "latency_true_ofi_direct_canary_applied": True,
            "latency_true_ofi_direct_canary_reason": "direct_canary_true_ofi_false_negative_allow",
            "latency_true_ofi_direct_canary_runtime_effect": True,
            "latency_true_ofi_direct_canary_allowed_runtime_apply": True,
        }
    )
    return fields


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
    spread_ratio = _to_float(getattr(latency_status, "spread_ratio", 0.0), 0.0)
    if spread_ratio > max_spread_ratio:
        reasons.append("spread_too_wide")
    elif not reasons and spread_ratio > _to_float(_CONFIG.max_spread_ratio_for_caution, 0.0):
        reasons.append("spread_above_caution_below_guard_cap")
    if not reasons:
        reasons.append("other_danger")
    return reasons


def _latency_danger_provenance(latency_status) -> dict[str, Any]:
    """Expose the EntryPolicy DANGER basis without changing legacy reason labels."""

    state_value = str(
        getattr(getattr(latency_status, "state", None), "value", getattr(latency_status, "state", ""))
        or ""
    ).upper()
    if state_value != "DANGER":
        return {
            "latency_danger_detail_reason": "not_applicable",
            "latency_danger_source_quality_state": "not_applicable",
            "latency_danger_reason_taxonomy_gap": False,
            "latency_danger_max_ws_age_ms_for_caution": int(_CONFIG.max_ws_age_ms_for_caution or 0),
            "latency_danger_max_ws_jitter_ms_for_caution": int(_CONFIG.max_ws_jitter_ms_for_caution or 0),
            "latency_danger_max_spread_ratio_for_caution": round(
                float(_to_float(_CONFIG.max_spread_ratio_for_caution, 0.0)),
                6,
            ),
            "latency_danger_guard_max_spread_ratio": round(
                float(
                    _to_float(
                        getattr(TRADING_RULES, "SCALP_LATENCY_GUARD_CANARY_MAX_SPREAD_RATIO", 0.0100),
                        0.0100,
                    )
                ),
                6,
            ),
        }

    max_ws_age_caution = int(_CONFIG.max_ws_age_ms_for_caution or 0)
    max_ws_jitter_caution = int(_CONFIG.max_ws_jitter_ms_for_caution or 0)
    max_spread_caution = _to_float(_CONFIG.max_spread_ratio_for_caution, 0.0)
    guard_max_spread = _to_float(
        getattr(TRADING_RULES, "SCALP_LATENCY_GUARD_CANARY_MAX_SPREAD_RATIO", 0.0100),
        0.0100,
    )
    ws_age_ms = int(getattr(latency_status, "ws_age_ms", 0) or 0)
    ws_jitter_ms = int(getattr(latency_status, "ws_jitter_ms", 0) or 0)
    spread_ratio = _to_float(getattr(latency_status, "spread_ratio", 0.0), 0.0)
    order_rtt_avg_ms = int(getattr(latency_status, "order_rtt_avg_ms", 0) or 0)

    detail_reasons: list[str] = []
    if getattr(latency_status, "quote_stale", False):
        detail_reasons.append("quote_stale")
    if max_ws_age_caution > 0 and ws_age_ms > max_ws_age_caution:
        detail_reasons.append("ws_age_above_caution")
    if max_ws_jitter_caution > 0 and ws_jitter_ms > max_ws_jitter_caution:
        detail_reasons.append("ws_jitter_above_caution")
    if order_rtt_avg_ms > int(_CONFIG.max_order_rtt_avg_ms_for_caution or 0):
        detail_reasons.append("order_rtt_avg_above_caution")
    if max_spread_caution > 0 and spread_ratio > max_spread_caution:
        if guard_max_spread > 0 and spread_ratio <= guard_max_spread:
            detail_reasons.append("spread_above_caution_below_guard_cap")
        else:
            detail_reasons.append("spread_above_caution")

    if not detail_reasons:
        detail_reasons.append("unclassified_danger")

    if getattr(latency_status, "quote_stale", False):
        source_quality_state = "stale"
    elif {"ws_age_above_caution", "ws_jitter_above_caution", "order_rtt_avg_above_caution"} & set(
        detail_reasons
    ):
        source_quality_state = "degraded"
    elif any(reason.startswith("spread_above_caution") for reason in detail_reasons):
        source_quality_state = "fresh"
    else:
        source_quality_state = "unknown"

    legacy_reasons = _normalized_reason_set(_latency_danger_reasons(latency_status))
    taxonomy_gap = legacy_reasons == {"other_danger"} and detail_reasons != ["unclassified_danger"]
    return {
        "latency_danger_detail_reason": ",".join(detail_reasons),
        "latency_danger_source_quality_state": source_quality_state,
        "latency_danger_reason_taxonomy_gap": taxonomy_gap,
        "latency_danger_max_ws_age_ms_for_caution": max_ws_age_caution,
        "latency_danger_max_ws_jitter_ms_for_caution": max_ws_jitter_caution,
        "latency_danger_max_spread_ratio_for_caution": round(float(max_spread_caution), 6),
        "latency_danger_guard_max_spread_ratio": round(float(guard_max_spread), 6),
    }


def _danger_latency_relief_runtime_enabled() -> bool:
    return any(
        bool(getattr(TRADING_RULES, attr, False))
        for attr in (
            "SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED",
            "SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED",
            "SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED",
        )
    )


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
    code: str,
    strategy_id: str,
    position_tag: str,
    signal_strength: float,
    latency_status,
    signal_price: int,
    latest_price: int,
    danger_reasons: list[str] | None = None,
    allow_true_ofi_all_scalping_scope: bool = False,
) -> tuple[bool, str]:
    if not bool(getattr(TRADING_RULES, "SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED", False)):
        return False, "disabled"
    if str(strategy_id or "").upper() not in {"SCALPING", "SCALP"}:
        return False, "non_scalping"
    if getattr(latency_status, "quote_stale", False):
        return False, "quote_stale"

    normalized_reasons = _normalized_reason_set(danger_reasons or _latency_danger_reasons(latency_status))
    spread_relief_reasons = {"spread_too_wide", "spread_above_caution_below_guard_cap"}
    if len(normalized_reasons) != 1 or not normalized_reasons.issubset(spread_relief_reasons):
        return False, "spread_only_required"

    allow_tags = {
        str(tag).strip().upper()
        for tag in (getattr(TRADING_RULES, "SCALP_LATENCY_SPREAD_RELIEF_TAGS", ()) or ())
        if str(tag).strip()
    }
    normalized_tag = str(position_tag or "").strip().upper()
    if allow_tags and normalized_tag not in allow_tags and not allow_true_ofi_all_scalping_scope:
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

    if bool(getattr(TRADING_RULES, "SCALP_LATENCY_SPREAD_RELIEF_BLOCK_UNSTABLE_QUOTE", True)):
        stability = ORDERBOOK_STABILITY_OBSERVER.snapshot(code) if code else {}
        if bool(stability.get("unstable_quote_observed")):
            return False, "unstable_quote_observed"
        if "print_quote_alignment" in stability:
            min_alignment = _to_float(
                getattr(TRADING_RULES, "SCALP_LATENCY_SPREAD_RELIEF_MIN_PRINT_QUOTE_ALIGNMENT", 0.90),
                0.90,
            )
            if min_alignment > 0 and _to_float(stability.get("print_quote_alignment"), 1.0) < min_alignment:
                return False, "print_quote_alignment_too_low"

    allowed_slippage = _ENTRY_POLICY._allowed_slippage(
        signal_price=signal_price,
        latest_price=latest_price,
        tick_limit=_CONFIG.normal_allowed_slippage_ticks,
        pct_limit=_CONFIG.normal_allowed_slippage_pct,
    )
    if not _ENTRY_POLICY._slippage_ok(signal_price, latest_price, allowed_slippage, "BUY"):
        return False, "normal_slippage_exceeded"

    return True, "spread_relief_canary_applied"


def _should_apply_latency_wide_spread_passive_requote(
    *,
    code: str,
    strategy_id: str,
    position_tag: str,
    signal_strength: float,
    latest_strength: float,
    buy_pressure_10t: float,
    latency_status,
    signal_price: int,
    latest_price: int,
    best_bid: int,
    best_ask: int,
    ws_data: dict[str, Any] | None,
    danger_reasons: list[str] | None = None,
) -> tuple[bool, str, dict[str, Any]]:
    diagnostics: dict[str, Any] = {}
    if not bool(getattr(TRADING_RULES, "SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_ENABLED", False)):
        return False, "disabled", diagnostics
    if str(strategy_id or "").upper() not in {"SCALPING", "SCALP"}:
        return False, "non_scalping", diagnostics
    if getattr(latency_status, "quote_stale", False):
        return False, "quote_stale", diagnostics

    normalized_reasons = _normalized_reason_set(danger_reasons or _latency_danger_reasons(latency_status))
    if normalized_reasons != {"spread_too_wide"}:
        return False, "spread_only_required", diagnostics

    allow_tags = {
        str(tag).strip().upper()
        for tag in (
            getattr(TRADING_RULES, "SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_TAGS", ()) or ()
        )
        if str(tag).strip()
    }
    normalized_tag = str(position_tag or "").strip().upper()
    if allow_tags and normalized_tag not in allow_tags:
        return False, "tag_not_allowed", diagnostics

    signal_score = _normalize_signal_score(signal_strength)
    min_signal = _to_float(
        getattr(TRADING_RULES, "SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_MIN_SIGNAL_SCORE", 78.0),
        78.0,
    )
    if signal_score < min_signal:
        return False, "low_signal", diagnostics

    min_buy_pressure = _to_float(
        getattr(TRADING_RULES, "SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_MIN_BUY_PRESSURE", 78.0),
        78.0,
    )
    if _to_float(buy_pressure_10t, 0.0) < min_buy_pressure:
        return False, "low_buy_pressure", diagnostics

    min_strength = _to_float(
        getattr(TRADING_RULES, "SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_MIN_STRENGTH", 0.0),
        0.0,
    )
    if min_strength > 0 and _to_float(latest_strength, 0.0) < min_strength:
        return False, "low_strength", diagnostics

    max_ws_age_ms = int(
        getattr(TRADING_RULES, "SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_MAX_WS_AGE_MS", 700)
        or 700
    )
    if int(getattr(latency_status, "ws_age_ms", 0) or 0) > max_ws_age_ms:
        return False, "ws_age_limit_exceeded", diagnostics

    max_ws_jitter_ms = int(
        getattr(TRADING_RULES, "SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_MAX_WS_JITTER_MS", 500)
        or 500
    )
    if int(getattr(latency_status, "ws_jitter_ms", 0) or 0) > max_ws_jitter_ms:
        return False, "ws_jitter_limit_exceeded", diagnostics

    max_spread_ratio = _to_float(
        getattr(TRADING_RULES, "SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_MAX_SPREAD_RATIO", 0.0130),
        0.0130,
    )
    if _to_float(getattr(latency_status, "spread_ratio", 0.0), 0.0) > max_spread_ratio:
        return False, "spread_limit_exceeded", diagnostics

    if int(best_bid or 0) <= 0 or int(best_ask or 0) <= int(best_bid or 0):
        return False, "invalid_quote", diagnostics

    micro_context = _conditional_real_1tick_context(ws_data, best_ask=best_ask, best_bid=best_bid)
    min_ofi = _to_float(
        getattr(TRADING_RULES, "SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_MIN_OFI_NORM", 0.0),
        0.0,
    )
    ofi_norm = micro_context.get("ofi_norm")
    if min_ofi > 0 and (ofi_norm is None or _to_float(ofi_norm, 0.0) < min_ofi):
        return False, "low_ofi", micro_context

    if bool(getattr(TRADING_RULES, "SCALP_LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE_BLOCK_UNSTABLE_QUOTE", True)):
        stability = ORDERBOOK_STABILITY_OBSERVER.snapshot(code) if code else {}
        diagnostics.update(stability)
        if bool(stability.get("unstable_quote_observed")):
            return False, "unstable_quote_observed", diagnostics

    allowed_slippage = _ENTRY_POLICY._allowed_slippage(
        signal_price=signal_price,
        latest_price=latest_price,
        tick_limit=_CONFIG.normal_allowed_slippage_ticks,
        pct_limit=_CONFIG.normal_allowed_slippage_pct,
    )
    if not _ENTRY_POLICY._slippage_ok(signal_price, latest_price, allowed_slippage, "BUY"):
        return False, "normal_slippage_exceeded", diagnostics

    diagnostics.update(micro_context)
    diagnostics.update(
        {
            "signal_score": round(float(signal_score), 3),
            "min_signal_score": round(float(min_signal), 3),
            "buy_pressure": round(float(_to_float(buy_pressure_10t, 0.0)), 3),
            "min_buy_pressure": round(float(min_buy_pressure), 3),
            "max_spread_ratio": round(float(max_spread_ratio), 6),
        }
    )
    return True, "wide_spread_passive_requote_applied", diagnostics


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


REAL_SCALPING_STRATEGY_IDS = {"SCALPING", "SCALP", "KOSPI_ML"}


def _pre_submit_quote_refresh_enabled(strategy_id: str) -> bool:
    if str(strategy_id or "").upper() not in REAL_SCALPING_STRATEGY_IDS:
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
        "pre_submit_quote_refresh_latest_price": int(latest_price or frozen_price or 0),
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
    quote_fresh_reasons = {
        "other_danger",
        "ws_age_too_high",
        "ws_jitter_too_high",
        "spread_too_wide",
        "spread_above_caution_below_guard_cap",
    }
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
    quote_fresh_reasons = {
        "other_danger",
        "ws_age_too_high",
        "ws_jitter_too_high",
        "spread_too_wide",
        "spread_above_caution_below_guard_cap",
    }
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
    quote_fresh_reasons = {
        "other_danger",
        "ws_age_too_high",
        "ws_jitter_too_high",
        "spread_too_wide",
        "spread_above_caution_below_guard_cap",
    }
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
    code: str,
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

    if bool(getattr(TRADING_RULES, "SCALP_LATENCY_OTHER_DANGER_RELIEF_BLOCK_UNSTABLE_QUOTE", True)):
        stability = ORDERBOOK_STABILITY_OBSERVER.snapshot(code) if code else {}
        if bool(stability.get("unstable_quote_observed")):
            return False, "unstable_quote_observed"
        if "print_quote_alignment" in stability:
            min_alignment = _to_float(
                getattr(TRADING_RULES, "SCALP_LATENCY_OTHER_DANGER_RELIEF_MIN_PRINT_QUOTE_ALIGNMENT", 0.90),
                0.90,
            )
            if min_alignment > 0 and _to_float(stability.get("print_quote_alignment"), 1.0) < min_alignment:
                return False, "print_quote_alignment_too_low"

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
    latency_wide_spread_passive_requote_applied = False
    latency_wide_spread_passive_requote_reason = ""
    latency_wide_spread_passive_requote_context: dict[str, Any] = {}
    latency_danger_reasons = ",".join(_latency_danger_reasons(latency))
    latency_danger_provenance = _latency_danger_provenance(latency)
    latency_buy_pressure = _latency_buy_pressure_value(ws_data, stock)
    latency_spread_relief_block_reason = ""
    danger_relief_forbidden = (
        policy.decision == EntryDecision.REJECT_DANGER and not _danger_latency_relief_runtime_enabled()
    )
    if policy.decision == EntryDecision.REJECT_DANGER:
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
            buy_pressure_10t=latency_buy_pressure,
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
                f"buy_pressure={latency_buy_pressure:.1f} "
                f"ws_age_ms={latency.ws_age_ms} ws_jitter_ms={latency.ws_jitter_ms} "
                f"spread_ratio={latency.spread_ratio:.6f} "
                f"danger_reasons={latency_danger_reasons}"
            )
        else:
            if not latency_canary_reason or latency_canary_reason == "disabled":
                latency_canary_reason = signal_quality_reason

    if policy.decision == EntryDecision.REJECT_DANGER and not danger_relief_forbidden and effective_decision == EntryDecision.REJECT_DANGER:
        other_danger_relief_ok, other_danger_relief_reason = _should_apply_latency_other_danger_relief_canary(
            code=code,
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
    spread_relief_signal_provenance = _latency_relief_signal_provenance(
        code=code,
        signal_strength=signal_strength,
        stock=stock,
        ws_data=ws_data,
    )
    spread_relief_signal_score = _to_float(
        spread_relief_signal_provenance.get("latency_spread_relief_signal_score"),
        _normalize_signal_score(signal_strength),
    )
    true_ofi_all_scalping_scope = bool(
        spread_relief_signal_provenance.get("latency_spread_relief_micro_estimator_all_scalping_enabled")
        and spread_relief_signal_provenance.get("latency_spread_relief_micro_estimator_eligible")
        and spread_relief_signal_provenance.get("latency_spread_relief_signal_score_source")
        == "micro_estimator.true_ofi_ewma"
    )
    if policy.decision == EntryDecision.REJECT_DANGER and not danger_relief_forbidden and effective_decision == EntryDecision.REJECT_DANGER:
        spread_relief_ok, spread_relief_reason = _should_apply_latency_spread_relief_canary(
            code=code,
            strategy_id=strategy_id,
            position_tag=spread_relief_tag,
            signal_strength=spread_relief_signal_score,
            latency_status=latency,
            signal_price=frozen_price,
            latest_price=latest_price,
            danger_reasons=latency_danger_reasons.split(","),
            allow_true_ofi_all_scalping_scope=true_ofi_all_scalping_scope,
        )
        if spread_relief_ok:
            latency_canary_applied = True
            latency_canary_reason = spread_relief_reason
            effective_decision = EntryDecision.ALLOW_NORMAL
            effective_reason = "latency_spread_relief_normal_override"
            log_info(
                f"[LATENCY_SPREAD_RELIEF_CANARY] {stock.get('name')}({code}) "
                f"tag={spread_relief_tag} signal_score={spread_relief_signal_score:.1f} "
                f"ws_age_ms={latency.ws_age_ms} ws_jitter_ms={latency.ws_jitter_ms} "
                f"spread_ratio={latency.spread_ratio:.6f} "
                f"danger_reasons={latency_danger_reasons}"
            )
        else:
            latency_spread_relief_block_reason = spread_relief_reason
            if (
                not latency_canary_reason
                or latency_canary_reason == "disabled"
                or (latency_canary_reason == "danger_hard_safety_block" and spread_relief_reason != "disabled")
            ):
                latency_canary_reason = spread_relief_reason

    if policy.decision == EntryDecision.REJECT_DANGER and not danger_relief_forbidden and effective_decision == EntryDecision.REJECT_DANGER:
        passive_requote_ok, passive_requote_reason, passive_requote_context = (
            _should_apply_latency_wide_spread_passive_requote(
                code=code,
                strategy_id=strategy_id,
                position_tag=spread_relief_tag,
                signal_strength=float(signal_strength or 0.0),
                latest_strength=_to_float((ws_data or {}).get("v_pw", stock.get("latest_strength", 0.0)), 0.0),
                buy_pressure_10t=latency_buy_pressure,
                latency_status=latency,
                signal_price=frozen_price,
                latest_price=latest_price,
                best_bid=best_bid,
                best_ask=best_ask,
                ws_data=ws_data,
                danger_reasons=latency_danger_reasons.split(","),
            )
        )
        latency_wide_spread_passive_requote_reason = passive_requote_reason
        latency_wide_spread_passive_requote_context = passive_requote_context
        if passive_requote_ok:
            latency_canary_applied = True
            latency_canary_reason = passive_requote_reason
            latency_wide_spread_passive_requote_applied = True
            effective_decision = EntryDecision.ALLOW_NORMAL
            effective_reason = "latency_wide_spread_passive_requote_normal_override"
            log_info(
                f"[LATENCY_WIDE_SPREAD_PASSIVE_REQUOTE] {stock.get('name')}({code}) "
                f"tag={spread_relief_tag} signal_score={_normalize_signal_score(signal_strength):.1f} "
                f"buy_pressure={latency_buy_pressure:.1f} "
                f"ws_age_ms={latency.ws_age_ms} ws_jitter_ms={latency.ws_jitter_ms} "
                f"spread_ratio={latency.spread_ratio:.6f} best_bid={best_bid} best_ask={best_ask} "
                f"danger_reasons={latency_danger_reasons}"
            )
        else:
            if (
                not latency_canary_reason
                or latency_canary_reason == "disabled"
                or (latency_canary_reason == "danger_hard_safety_block" and passive_requote_reason != "disabled")
            ):
                latency_canary_reason = passive_requote_reason

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
            buy_pressure_10t=latency_buy_pressure,
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
                f"buy_pressure={latency_buy_pressure:.1f} "
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
    spread_block_buckets = _latency_spread_block_buckets(
        latency_status=latency,
        latest_price=latest_price,
        best_bid=best_bid,
        best_ask=best_ask,
        signal_source_quality_state=str(
            spread_relief_signal_provenance.get("latency_spread_relief_signal_source_quality_state") or ""
        ),
    )
    latency_false_negative_remeasure_fields = _latency_false_negative_bounded_remeasure_fields(
        code=code,
        stock=stock,
        ws_data=ws_data,
        strategy_id=strategy_id,
        policy_decision=policy.decision,
        effective_decision=effective_decision,
        latency_status=latency,
        danger_reasons=latency_danger_reasons.split(","),
        spread_bps=_to_float(spread_block_buckets.get("latency_spread_block_spread_bps"), 0.0),
    )
    latency_true_ofi_direct_canary_fields = _latency_true_ofi_direct_canary_fields(
        stock=stock,
        ws_data=ws_data,
        strategy_id=strategy_id,
        policy_decision=policy.decision,
        effective_decision=effective_decision,
        latency_status=latency,
        danger_reasons=latency_danger_reasons.split(","),
        spread_bps=_to_float(spread_block_buckets.get("latency_spread_block_spread_bps"), 0.0),
        signal_score=_normalize_signal_score(signal_strength),
        micro_estimator_reason=str(
            spread_relief_signal_provenance.get("latency_spread_relief_micro_estimator_reason") or ""
        ),
        estimator_context=latency_false_negative_remeasure_fields,
        danger_relief_forbidden=danger_relief_forbidden,
    )
    if latency_true_ofi_direct_canary_fields.get("latency_true_ofi_direct_canary_applied"):
        latency_canary_applied = True
        latency_canary_reason = "latency_true_ofi_direct_canary_applied"
        effective_decision = EntryDecision.ALLOW_NORMAL
        effective_reason = "latency_true_ofi_false_negative_direct_canary_normal_override"
        log_info(
            f"[LATENCY_TRUE_OFI_DIRECT_CANARY] {stock.get('name')}({code}) "
            f"tag={stock.get('position_tag')} signal_score={_normalize_signal_score(signal_strength):.1f} "
            f"delta={latency_true_ofi_direct_canary_fields.get('latency_true_ofi_direct_canary_price_delta_pct')} "
            f"spread_bps={latency_true_ofi_direct_canary_fields.get('latency_true_ofi_direct_canary_spread_bps')} "
            f"true_ofi={latency_true_ofi_direct_canary_fields.get('latency_true_ofi_direct_canary_true_ofi_ewma')} "
            f"samples={latency_true_ofi_direct_canary_fields.get('latency_true_ofi_direct_canary_true_ofi_sample_count')} "
            f"ws_age_ms={latency_true_ofi_direct_canary_fields.get('latency_true_ofi_direct_canary_ws_age_ms')}"
        )
    result = {
        "allowed": False,
        "decision": effective_decision.value,
        "reason": effective_reason,
        "policy_decision": policy.decision.value,
        "policy_reason": policy.reason,
        "effective_decision": effective_decision.value,
        "effective_reason": effective_reason,
        "latency_strategy_id": str(strategy_id or ""),
        "latency_position_tag": str(stock.get("position_tag") or ""),
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
        **latency_danger_provenance,
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
        "latency_spread_relief_configured_min_signal_score": round(spread_relief_configured_min_signal, 3),
        "latency_spread_relief_effective_min_signal_score": round(spread_relief_effective_min_signal, 3),
        "latency_spread_relief_tag": spread_relief_tag,
        "latency_spread_relief_block_reason": latency_spread_relief_block_reason,
        **spread_relief_signal_provenance,
        **spread_block_buckets,
        **latency_false_negative_remeasure_fields,
        **latency_true_ofi_direct_canary_fields,
        "latency_relief_attempted": bool(policy.decision == EntryDecision.REJECT_DANGER and not danger_relief_forbidden),
        "latency_relief_block_reason": (
            latency_canary_reason
            if policy.decision == EntryDecision.REJECT_DANGER
            and effective_decision == EntryDecision.REJECT_DANGER
            and not latency_canary_applied
            else ""
        ),
        "latency_wide_spread_passive_requote_applied": latency_wide_spread_passive_requote_applied,
        "latency_wide_spread_passive_requote_reason": latency_wide_spread_passive_requote_reason,
        "latency_wide_spread_passive_requote_context": latency_wide_spread_passive_requote_context,
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
                entry_price_guard = (
                    "latency_wide_spread_passive_requote_defensive"
                    if latency_wide_spread_passive_requote_applied
                    else "latency_danger_override_defensive"
                )
                applied_bps = 0
                gap_profile.update(
                    profile=(
                        "wide_spread_passive_requote"
                        if latency_wide_spread_passive_requote_applied
                        else "latency_override"
                    ),
                    bps=0,
                    reason=(
                        "wide_spread_passive_requote_keeps_defensive"
                        if latency_wide_spread_passive_requote_applied
                        else "latency_override_keeps_defensive"
                    ),
                )
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
                        "aggressive_entry_price_operator_intraday_discovery": bool(
                            aggressive_override.get("operator_intraday_entry_price_discovery")
                        ),
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
            result["aggressive_entry_price_operator_intraday_discovery"] = bool(
                (gap_profile.get("context") or {}).get("aggressive_entry_price_operator_intraday_discovery", False)
                if isinstance(gap_profile.get("context"), dict)
                else False
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
            "latency_wide_spread_passive_requote_defensive"
            if is_latency_override and latency_wide_spread_passive_requote_applied
            else "latency_danger_override_defensive"
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
