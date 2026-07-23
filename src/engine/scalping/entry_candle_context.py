"""Session-aware minute-candle source and bounded entry confirmation context.

The neutral source builder may be reused by entry and holding consumers.  The
entry wrapper owns observation and BUY-to-WAIT demotion only; it cannot create
BUY authority, choose an order price/quantity, or bypass broker/safety guards.
"""

from __future__ import annotations

import math
import os
import time
from datetime import datetime, time as dt_time, timezone
from typing import Any
from zoneinfo import ZoneInfo

from src.engine.scalping.ai_market_snapshot import (
    ai_market_snapshot_log_fields,
    build_ai_market_snapshot,
    preferred_ws_route,
    realtime_type_provenance,
)
from src.engine.kiwoom_orders import resolve_order_dmst_stex_tp

SCHEMA = "entry_candle_context_v1"
SOURCE_SCHEMA = "session_candle_source_v1"
KST = ZoneInfo("Asia/Seoul")
ADVERSE_REGIMES = {
    "failed_breakout",
    "lower_high_distribution",
    "downtrend_bounce",
}
OBSERVATION_CONTRACT = {
    "metric_role": "entry_context_feature_bundle",
    "decision_authority": "bounded_entry_confirmation",
    "window_policy": "current_session_3m_5m_10m_20m",
    "sample_floor": "session_aware_0_2_opening_3_9_short_10_plus_full",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": "fresh_venue_consistent_session_bars",
    "forbidden_uses": [
        "standalone_buy_authority",
        "order_price_or_quantity_decision",
        "hard_or_broker_guard_bypass",
        "nxt_evidence_for_krx_only_decision",
        "exit_authority",
    ],
}


def _env_bool(name: str, default: bool = False) -> bool:
    raw = str(os.getenv(name, "true" if default else "false")).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _now_kst(now_ts: Any = None) -> datetime:
    if isinstance(now_ts, datetime):
        if now_ts.tzinfo is None:
            return now_ts.replace(tzinfo=KST)
        return now_ts.astimezone(KST)
    if now_ts is None:
        return datetime.now(KST)
    return datetime.fromtimestamp(float(now_ts), tz=KST)


def _cohort(venue: str, session: str) -> str:
    venue_upper = str(venue or "").upper()
    session_lower = str(session or "").lower()
    if "PREMARKET" in venue_upper or "premarket" in session_lower:
        return "PREMARKET"
    if "NXT" in venue_upper or session_lower.startswith("nxt_"):
        return "NXT"
    return "KRX"


def entry_candle_context_enabled(
    *, venue: str = "", session: str = "", now_ts: Any = None
) -> bool:
    if not _env_bool("KORSTOCKSCAN_ENTRY_CANDLE_CONTEXT_ENABLED", False):
        return False
    active_date = str(
        os.getenv("KORSTOCKSCAN_ENTRY_CANDLE_CONTEXT_ACTIVE_DATE", "")
    ).strip()
    if active_date and _now_kst(now_ts).date().isoformat() != active_date:
        return False
    cohort = _cohort(venue, session)
    return _env_bool(f"KORSTOCKSCAN_ENTRY_CANDLE_CONTEXT_{cohort}_ENABLED", False)


def resolve_entry_candle_session(now_ts: Any = None, session: str | None = None) -> str:
    if session:
        return str(session)
    current = _now_kst(now_ts).time()
    if dt_time(8, 0) <= current < dt_time(9, 0):
        return "premarket_krx_like"
    if dt_time(9, 0) <= current <= dt_time(15, 30):
        return "krx_regular"
    if dt_time(16, 0) <= current <= dt_time(20, 0):
        return "nxt_aftermarket"
    return "off_session"


def _split_code(code: str) -> tuple[str, str]:
    raw = str(code or "").strip().upper().replace(".0", "")
    for suffix in ("_NX", "_AL"):
        if raw.endswith(suffix):
            return raw[:-3], suffix
    if raw.startswith("A") and len(raw) >= 7:
        raw = raw[1:]
    digits = "".join(char for char in raw if char.isdigit())
    return (digits[-6:].zfill(6) if digits else raw), ""


def _ws_route(
    ws_data: dict[str, Any], *, now_ts: float | None = None
) -> tuple[str, str]:
    return preferred_ws_route(ws_data, now_ts=now_ts)


def resolve_entry_candle_venue(
    ws_data: dict[str, Any] | None,
    venue: str | None = None,
    session: str | None = None,
) -> str:
    if venue:
        venue_value = str(venue).upper()
        session_value = str(session or "").lower()
        if venue_value in {"SOR", "INTEGRATED", "KRX_NXT_INTEGRATED"}:
            if "premarket" in session_value:
                return "PREMARKET_KRX_LIKE"
            if "nxt" in session_value:
                return "NXT"
            if "krx" in session_value:
                return "KRX"
        return venue_value
    ws = ws_data if isinstance(ws_data, dict) else {}
    suffix, route = _ws_route(ws)
    session_value = str(session or "").lower()
    if "premarket" in session_value:
        return "PREMARKET_KRX_LIKE"
    if session_value.startswith("nxt_"):
        return "NXT"
    exact_venues = {
        str(row.get("effective_venue") or "").strip().upper()
        for row in realtime_type_provenance(ws).values()
        if row.get("quality") == "fresh"
        and str(row.get("effective_venue") or "").strip().upper() in {"KRX", "NXT"}
    }
    if len(exact_venues) == 1:
        return next(iter(exact_venues))
    if suffix == "_NX" or route == "nxt_only":
        return "NXT"
    if "krx" in session_value:
        return "KRX"
    return "KRX"


def resolve_entry_candle_request_code(
    code: str,
    *,
    venue: str,
    session: str,
    ws_data: dict[str, Any] | None = None,
) -> str:
    base, explicit_suffix = _split_code(code)
    venue_upper = str(venue or "").upper()
    if venue_upper == "NXT":
        return f"{base}_NX"
    if venue_upper == "PREMARKET_KRX_LIKE":
        if explicit_suffix == "_AL":
            return f"{base}_AL"
        return f"{base}_NX"
    if venue_upper in {"SOR", "INTEGRATED", "KRX_NXT_INTEGRATED"}:
        return f"{base}_AL"
    if venue_upper == "KRX":
        ws_suffix, ws_route = _ws_route(ws_data if isinstance(ws_data, dict) else {})
        if ws_suffix == "_AL" and ws_route == "krx_nxt_integrated":
            return f"{base}_AL"
    return base


def _number(value: Any, default: float = 0.0) -> float:
    try:
        result = float(str(value).replace(",", "").replace("+", ""))
        return result if math.isfinite(result) else default
    except (TypeError, ValueError):
        return default


def _integer(value: Any, default: int = 0) -> int:
    return int(round(abs(_number(value, float(default)))))


def _parse_bar_dt(candle: dict[str, Any], now: datetime) -> datetime | None:
    raw = str(candle.get("source_timestamp") or "").strip()
    if len(raw) >= 14 and raw[:14].isdigit():
        try:
            return datetime.strptime(raw[:14], "%Y%m%d%H%M%S").replace(tzinfo=KST)
        except ValueError:
            pass
    raw = str(candle.get("체결시간") or candle.get("time") or "").strip()
    for fmt in ("%H:%M:%S", "%H%M%S", "%H:%M", "%H%M"):
        try:
            parsed = datetime.strptime(raw, fmt).time()
            return datetime.combine(now.date(), parsed, tzinfo=KST)
        except ValueError:
            continue
    return None


def _session_matches(moment: datetime, session: str) -> bool:
    current = moment.time()
    session_lower = str(session or "").lower()
    if "premarket" in session_lower:
        return dt_time(8, 0) <= current < dt_time(9, 0)
    if session_lower.startswith("nxt_regular"):
        return dt_time(9, 0) <= current <= dt_time(15, 30)
    if session_lower.startswith("nxt_") or "aftermarket" in session_lower:
        return dt_time(16, 0) <= current <= dt_time(20, 0)
    if "krx" in session_lower or "regular" in session_lower:
        return dt_time(9, 0) <= current <= dt_time(15, 30)
    return True


def _normalized_bar(candle: dict[str, Any], moment: datetime) -> dict[str, Any]:
    return {
        "dt": moment,
        "t": moment.strftime("%H:%M"),
        "o": _integer(candle.get("시가", candle.get("open"))),
        "h": _integer(candle.get("고가", candle.get("high"))),
        "l": _integer(candle.get("저가", candle.get("low"))),
        "c": _integer(candle.get("현재가", candle.get("close"))),
        "v": _integer(candle.get("거래량", candle.get("volume"))),
        "forming": False,
        "partial_volume": False,
    }


def _nxt_integrated_aftermarket_route_proof(
    *,
    now: datetime,
    venue: str,
    session: str,
    request_suffix: str,
    ws_suffix: str,
    ws_route: str,
) -> dict[str, Any]:
    session_value = str(session or "").strip().lower()
    within_aftermarket_clock = dt_time(16, 0) <= now.time() <= dt_time(20, 0)
    proven = bool(
        str(venue or "").strip().upper() == "NXT"
        and session_value == "nxt_aftermarket"
        and within_aftermarket_clock
        and request_suffix == "_NX"
        and ws_suffix == "_AL"
        and ws_route == "krx_nxt_integrated"
    )
    return {
        "proven": proven,
        "route_equivalence": (
            "nxt_aftermarket_integrated_ws_to_nx_rest" if proven else "not_proven"
        ),
        "krx_regular_closed_by_clock": within_aftermarket_clock,
        "required_session": "nxt_aftermarket",
        "required_rest_suffix": "_NX",
        "required_ws_suffix": "_AL",
        "required_ws_route": "krx_nxt_integrated",
    }


def _route_compatible(
    tick: dict[str, Any],
    *,
    request_suffix: str,
    ws_route: str,
    allow_nxt_integrated_aftermarket: bool = False,
) -> bool:
    tick_suffix = str(tick.get("market_suffix") or "").upper()
    tick_route = str(tick.get("market_route") or "").lower()
    if allow_nxt_integrated_aftermarket:
        return tick_suffix == "_AL" and tick_route == "krx_nxt_integrated"
    if request_suffix and tick_suffix != request_suffix:
        return False
    if not request_suffix and tick_suffix:
        return False
    if ws_route and tick_route != ws_route:
        return False
    return True


def _tick_dt(tick: dict[str, Any], now: datetime) -> datetime | None:
    received = _number(
        tick.get("received_at_ms", tick.get("received_timestamp_ms")), 0.0
    )
    if received > 0:
        return datetime.fromtimestamp(received / 1000.0, tz=timezone.utc).astimezone(
            KST
        )
    raw = str(tick.get("time") or "").strip()
    for fmt in ("%H:%M:%S", "%H%M%S", "%H:%M", "%H%M"):
        try:
            return datetime.combine(
                now.date(), datetime.strptime(raw, fmt).time(), tzinfo=KST
            )
        except ValueError:
            continue
    return None


def _return_pct(bars: list[dict[str, Any]], minutes: int) -> float | None:
    usable = bars[-(minutes + 1) :]
    if len(usable) < 2 or usable[0]["c"] <= 0:
        return None
    return round((usable[-1]["c"] / usable[0]["c"] - 1.0) * 100.0, 4)


def _slope_pct(bars: list[dict[str, Any]], minutes: int) -> float | None:
    usable = bars[-max(2, minutes) :]
    if len(usable) < 2:
        return None
    first = usable[0]["c"]
    if first <= 0:
        return None
    count = len(usable)
    x_mean = (count - 1) / 2.0
    y_mean = sum(bar["c"] for bar in usable) / count
    numerator = sum(
        (index - x_mean) * (bar["c"] - y_mean) for index, bar in enumerate(usable)
    )
    denominator = sum((index - x_mean) ** 2 for index in range(count)) or 1.0
    return round((numerator / denominator) / first * 100.0, 4)


def _range_pct(bars: list[dict[str, Any]], minutes: int) -> float | None:
    usable = bars[-max(1, minutes) :]
    highs = [bar["h"] for bar in usable if bar["h"] > 0]
    lows = [bar["l"] for bar in usable if bar["l"] > 0]
    if not highs or not lows or min(lows) <= 0:
        return None
    return round((max(highs) / min(lows) - 1.0) * 100.0, 4)


def _structure(bars: list[dict[str, Any]]) -> dict[str, Any]:
    completed = [bar for bar in bars if not bar.get("forming")]
    active = bars or completed
    highs = [bar["h"] for bar in active if bar["h"] > 0]
    lows = [bar["l"] for bar in active if bar["l"] > 0]
    latest = active[-1] if active else {}
    peak = max(highs, default=0)
    low = min(lows, default=0)
    latest_close = _integer(latest.get("c"))
    peak_drawdown = (
        round((latest_close / peak - 1.0) * 100.0, 4)
        if peak > 0 and latest_close > 0
        else None
    )
    low_rebound = (
        round((latest_close / low - 1.0) * 100.0, 4)
        if low > 0 and latest_close > 0
        else None
    )
    windows = (1, 3, 5, 10, 20, 60)
    returns = {str(window): _return_pct(active, window) for window in windows}
    slopes = {str(window): _slope_pct(active, window) for window in windows}
    ranges = {str(window): _range_pct(active, window) for window in windows}
    prior = active[:-1]
    prior_high = max((bar["h"] for bar in prior[-10:]), default=0)
    long_slope = slopes["20"] if slopes["20"] is not None else slopes["10"]
    short_return = returns["3"]
    recent_highs = [bar["h"] for bar in active[-6:] if bar["h"] > 0]
    recent_lows = [bar["l"] for bar in active[-6:] if bar["l"] > 0]
    lower_highs = (
        len(recent_highs) >= 4
        and recent_highs[-1] < recent_highs[0]
        and recent_lows[-1] < recent_lows[0]
    )
    latest_range = max(0, _integer(latest.get("h")) - _integer(latest.get("l")))
    upper_wick_ratio = (
        max(0, _integer(latest.get("h")) - max(_integer(latest.get("o")), latest_close))
        / latest_range
        if latest_range > 0
        else 0.0
    )
    body_ratio = (
        abs(latest_close - _integer(latest.get("o"))) / latest_range
        if latest_range > 0
        else 0.0
    )
    lower_wick_ratio = (
        max(
            0,
            min(_integer(latest.get("o")), latest_close) - _integer(latest.get("l")),
        )
        / latest_range
        if latest_range > 0
        else 0.0
    )
    volumes = [bar["v"] for bar in active if bar["v"] >= 0]
    prior_volume = volumes[:-1][-10:]
    volume_ratio = (
        round(volumes[-1] / (sum(prior_volume) / len(prior_volume)), 3)
        if volumes and prior_volume and sum(prior_volume) > 0
        else None
    )
    if volume_ratio is None or short_return is None:
        volume_direction_alignment = "not_available"
    elif volume_ratio >= 1.1 and short_return > 0:
        volume_direction_alignment = "bullish_confirmed"
    elif volume_ratio >= 1.1 and short_return < 0:
        volume_direction_alignment = "bearish_confirmed"
    elif volume_ratio < 0.8 and abs(short_return) >= 0.1:
        volume_direction_alignment = "price_volume_divergence"
    else:
        volume_direction_alignment = "neutral"

    if len(completed) < 3:
        regime = "opening_flow"
    elif (
        len(active) >= 5
        and prior_high > 0
        and max((bar["h"] for bar in active[-3:]), default=0) >= prior_high
        and latest_close < prior_high
        and (upper_wick_ratio >= 0.35 or (peak_drawdown or 0.0) <= -0.25)
    ):
        regime = "failed_breakout"
    elif len(active) >= 10 and lower_highs and (long_slope or 0.0) < 0:
        regime = "lower_high_distribution"
    elif (
        len(active) >= 10 and (long_slope or 0.0) < -0.03 and (short_return or 0.0) > 0
    ):
        regime = "downtrend_bounce"
    elif prior_high > 0 and latest_close > prior_high and (short_return or 0.0) > 0:
        regime = "breakout"
    elif (
        len(active) >= 5
        and (long_slope or slopes["5"] or 0.0) > 0
        and -0.6 <= (short_return or 0.0) <= 0.25
        and (peak_drawdown or 0.0) > -1.2
    ):
        regime = "healthy_pullback"
    else:
        regime = "range"

    alignment = (
        "adverse"
        if regime in ADVERSE_REGIMES
        else ("positive" if regime in {"breakout", "healthy_pullback"} else "neutral")
    )
    return {
        "returns_pct": returns,
        "slopes_pct_per_bar": slopes,
        "ranges_pct": ranges,
        "range_pct": (
            round((peak / low - 1.0) * 100.0, 4) if peak > 0 and low > 0 else None
        ),
        "peak_drawdown_pct": peak_drawdown,
        "low_rebound_pct": low_rebound,
        "latest_upper_wick_ratio": round(upper_wick_ratio, 4),
        "latest_lower_wick_ratio": round(lower_wick_ratio, 4),
        "latest_body_ratio": round(body_ratio, 4),
        "volume_ratio": volume_ratio,
        "volume_direction_alignment": volume_direction_alignment,
        "high_direction": (
            "down"
            if len(recent_highs) >= 2 and recent_highs[-1] < recent_highs[0]
            else "up_or_flat"
        ),
        "low_direction": (
            "down"
            if len(recent_lows) >= 2 and recent_lows[-1] < recent_lows[0]
            else "up_or_flat"
        ),
        "regime": regime,
        "alignment": alignment,
    }


def build_session_candle_source(
    token: str | None,
    code: str,
    ws_data: dict[str, Any] | None,
    venue: str | None,
    session: str | None,
    limit: int = 40,
    model_bar_limit: int = 20,
    now_ts: Any = None,
    *,
    recent_candles: list[dict[str, Any]] | None = None,
    source_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a neutral venue/session candle bundle for bounded consumers."""

    started = time.perf_counter()
    now = _now_kst(now_ts)
    session_value = resolve_entry_candle_session(now, session)
    ws = ws_data if isinstance(ws_data, dict) else {}
    venue_value = resolve_entry_candle_venue(ws, venue, session_value)
    if venue_value == "NXT" and session_value == "krx_regular":
        session_value = "nxt_regular_overlap"
    request_code = resolve_entry_candle_request_code(
        code, venue=venue_value, session=session_value, ws_data=ws
    )
    _, request_suffix = _split_code(request_code)
    ws_suffix, ws_route = _ws_route(ws, now_ts=now.timestamp())
    route_proof = _nxt_integrated_aftermarket_route_proof(
        now=now,
        venue=venue_value,
        session=session_value,
        request_suffix=request_suffix,
        ws_suffix=ws_suffix,
        ws_route=ws_route,
    )
    route_equivalence_proven = bool(route_proof["proven"])
    fetch_ms = 0
    fetch_error = ""
    if recent_candles is None:
        fetch_started = time.perf_counter()
        try:
            from src.utils import kiwoom_utils

            recent_candles, source_meta = (
                kiwoom_utils.get_minute_candles_ka10080_with_meta(
                    token, request_code, limit=max(1, int(limit))
                )
            )
        except Exception as exc:
            recent_candles, source_meta = [], {}
            fetch_error = f"{type(exc).__name__}:{str(exc)[:120]}"
        fetch_ms = int((time.perf_counter() - fetch_started) * 1000)
    candles = [candle for candle in (recent_candles or []) if isinstance(candle, dict)]
    duplicate_count = 0
    duplicate_price_conflict = False
    by_minute: dict[datetime, dict[str, Any]] = {}
    input_order: list[datetime] = []
    for candle in candles:
        moment = _parse_bar_dt(candle, now)
        if moment is None:
            continue
        minute = moment.replace(second=0, microsecond=0)
        input_order.append(minute)
        normalized = _normalized_bar(candle, minute)
        existing = by_minute.get(minute)
        if existing is not None:
            duplicate_count += 1
            if any(existing[key] != normalized[key] for key in ("o", "h", "l", "c")):
                duplicate_price_conflict = True
        by_minute[minute] = normalized
    time_reversal = any(
        input_order[index] < input_order[index - 1]
        for index in range(1, len(input_order))
    )
    parsed = [by_minute[key] for key in sorted(by_minute)][-max(1, int(limit)) :]
    current_session = [
        bar
        for bar in parsed
        if bar["dt"].date() == now.date() and _session_matches(bar["dt"], session_value)
    ]
    previous_session = [bar for bar in parsed if bar not in current_session]

    ticks = [
        tick for tick in (ws.get("recent_trade_ticks") or []) if isinstance(tick, dict)
    ]
    route_conflict_count = 0
    current_minute = now.replace(second=0, microsecond=0)
    if current_session and current_session[-1]["dt"] == current_minute:
        current_session[-1]["forming"] = True
        current_session[-1]["partial_volume"] = True
    minute_ticks: list[tuple[datetime, dict[str, Any]]] = []
    for tick in ticks:
        moment = _tick_dt(tick, now)
        if moment is None or moment.replace(second=0, microsecond=0) != current_minute:
            continue
        if not _route_compatible(
            tick,
            request_suffix=request_suffix,
            ws_route=ws_route,
            allow_nxt_integrated_aftermarket=route_equivalence_proven,
        ):
            route_conflict_count += 1
            continue
        minute_ticks.append((moment, tick))
    if minute_ticks:
        minute_ticks.sort(key=lambda item: item[0])
        prices = [_integer(item[1].get("price")) for item in minute_ticks]
        prices = [price for price in prices if price > 0]
        if prices:
            if current_session and current_session[-1]["dt"] == current_minute:
                forming = dict(current_session[-1])
            else:
                forming = {
                    "dt": current_minute,
                    "t": current_minute.strftime("%H:%M"),
                    "o": prices[0],
                    "h": max(prices),
                    "l": min(prices),
                    "c": prices[-1],
                    "v": 0,
                    "forming": True,
                    "partial_volume": True,
                }
                current_session.append(forming)
            forming.update(
                {
                    "o": forming.get("o") or prices[0],
                    "h": max(_integer(forming.get("h")), max(prices)),
                    "l": min(
                        value
                        for value in (_integer(forming.get("l")), min(prices))
                        if value > 0
                    ),
                    "c": prices[-1],
                    "v": max(
                        _integer(forming.get("v")),
                        sum(_integer(item[1].get("volume")) for item in minute_ticks),
                    ),
                    "forming": True,
                    "partial_volume": True,
                }
            )
            current_session[-1] = forming

    # The forming-bar overlay is an additional live observation. Keep the
    # consumer-visible source window bounded after that overlay as well.
    current_session = current_session[-max(1, int(limit)) :]
    missing_bar_count = 0
    max_consecutive_missing_bar_count = 0
    for left, right in zip(current_session, current_session[1:]):
        gap = int((right["dt"] - left["dt"]).total_seconds() // 60) - 1
        if gap > 0:
            missing_bar_count += gap
            max_consecutive_missing_bar_count = max(
                max_consecutive_missing_bar_count, gap
            )
    latest = current_session[-1] if current_session else None
    latest_age_sec = max(0.0, (now - latest["dt"]).total_seconds()) if latest else None
    venue_conflict = bool(
        route_conflict_count
        or (not route_equivalence_proven and ws_suffix and request_suffix != ws_suffix)
        or (
            venue_value == "KRX"
            and ws_route
            and ws_route not in {"krx_regular", "krx_only", "krx_nxt_integrated"}
        )
        or (
            venue_value == "NXT"
            and ws_route
            and ws_route not in {"nxt_only"}
            and not route_equivalence_proven
        )
    )
    quality_blockers = []
    if fetch_error:
        quality_blockers.append("fetch_error")
    if (
        venue_value == "PREMARKET_KRX_LIKE"
        and request_suffix == "_AL"
        and not (
            ws_route == "krx_nxt_integrated"
            and bool(
                ws.get("krx_market_closed")
                or ws.get("krx_holiday_confirmed")
                or ws.get("krx_regular_session_closed")
            )
        )
    ):
        quality_blockers.append("premarket_al_proof_missing")
    if venue_conflict:
        quality_blockers.append("venue_conflict")
    if time_reversal:
        quality_blockers.append("time_reversal")
    if duplicate_count:
        quality_blockers.append("duplicate_bar")
    if duplicate_price_conflict:
        quality_blockers.append("duplicate_price_conflict")
    if max_consecutive_missing_bar_count >= 2:
        quality_blockers.append("consecutive_bar_gap")
    if not current_session:
        quality_blockers.append("no_current_session_bars")
    if latest_age_sec is not None and latest_age_sec > 180:
        quality_blockers.append("stale_latest_bar")
    quality_status = "blocked" if quality_blockers else "fresh_consistent"
    structure = _structure(current_session)
    completed_count = sum(not bar.get("forming") for bar in current_session)
    sample_mode = (
        "opening_flow_only"
        if completed_count <= 2
        else ("short_structure" if completed_count <= 9 else "full_structure")
    )
    model_bars = current_session[-max(1, int(model_bar_limit)) :]
    model_path = [
        {
            "t": bar["t"],
            "o": bar["o"],
            "h": bar["h"],
            "l": bar["l"],
            "c": bar["c"],
            "v": bar["v"],
            "forming": bool(bar.get("forming")),
            "partial_volume": bool(bar.get("partial_volume")),
        }
        for bar in model_bars
    ]
    build_ms = int((time.perf_counter() - started) * 1000)
    return {
        "schema": SOURCE_SCHEMA,
        "venue": venue_value,
        "session": session_value,
        "request_code": request_code,
        "rest_route": request_suffix or "KRX",
        "ws_route": ws_route or "unknown",
        "ws_suffix": ws_suffix or "",
        "route_equivalence": route_proof["route_equivalence"],
        "route_equivalence_proven": route_equivalence_proven,
        "current_session_bar_count": len(current_session),
        "previous_session_bar_count": len(previous_session),
        "completed_bar_count": completed_count,
        "forming_bar_present": bool(
            current_session and current_session[-1].get("forming")
        ),
        "latest_bar_age_sec": (
            round(latest_age_sec, 3) if latest_age_sec is not None else None
        ),
        "sample_mode": sample_mode,
        "bars": model_path,
        "structure": structure,
        "regime": structure["regime"],
        "alignment": structure["alignment"],
        "risk_flags": sorted(set(quality_blockers)),
        "source_quality": {
            "status": quality_status,
            "blockers": quality_blockers,
            "missing_bar_count": missing_bar_count,
            "max_consecutive_missing_bar_count": max_consecutive_missing_bar_count,
            "duplicate_count": duplicate_count,
            "duplicate_price_conflict": duplicate_price_conflict,
            "time_monotonic": not time_reversal,
            "route_conflict_count": route_conflict_count,
            "route_equivalence_proof": route_proof,
            "source_meta": {
                key: value
                for key, value in (source_meta or {}).items()
                if key
                in {
                    "api_id",
                    "received_count",
                    "requested_limit",
                    "truncated_window",
                    "sort_direction_detected",
                    "latest_source_timestamp",
                }
            },
        },
        "timing": {"fetch_ms": fetch_ms, "build_ms": build_ms},
    }


def build_entry_candle_context(
    token: str | None,
    code: str,
    ws_data: dict[str, Any] | None,
    venue: str | None,
    session: str | None,
    limit: int = 40,
    model_bar_limit: int = 20,
    now_ts: Any = None,
    *,
    recent_candles: list[dict[str, Any]] | None = None,
    source_meta: dict[str, Any] | None = None,
    broker_route: str | None = None,
) -> dict[str, Any]:
    """Build the entry-owned view over the neutral candle source."""

    context = build_session_candle_source(
        token,
        code,
        ws_data,
        venue,
        session,
        limit=limit,
        model_bar_limit=model_bar_limit,
        now_ts=now_ts,
        recent_candles=recent_candles,
        source_meta=source_meta,
    )
    context.update(
        {
            "schema": SCHEMA,
            "enabled": entry_candle_context_enabled(
                venue=str(context.get("venue") or ""),
                session=str(context.get("session") or ""),
                now_ts=now_ts,
            ),
            "observation_contract": OBSERVATION_CONTRACT,
        }
    )
    now_kst = _now_kst(now_ts)
    planned_broker_route = str(
        broker_route or resolve_order_dmst_stex_tp(now=now_kst)
    ).upper()
    context["ai_market_snapshot_v1"] = build_ai_market_snapshot(
        stock_code=code,
        decision_stage="entry_context",
        ws_data=ws_data,
        effective_venue=str(context.get("venue") or ""),
        session_bucket=str(context.get("session") or ""),
        broker_route=planned_broker_route,
        candle_context=context,
        now_ts=now_kst.timestamp(),
    )
    return context


def _best_levels(ws_data: dict[str, Any]) -> tuple[int, int, float, float]:
    orderbook = (
        ws_data.get("orderbook") if isinstance(ws_data.get("orderbook"), dict) else {}
    )
    asks = orderbook.get("asks") if isinstance(orderbook.get("asks"), list) else []
    bids = orderbook.get("bids") if isinstance(orderbook.get("bids"), list) else []
    ask = asks[0] if asks and isinstance(asks[0], dict) else {}
    bid = bids[0] if bids and isinstance(bids[0], dict) else {}
    best_ask = _integer(
        ask.get("price", ws_data.get("best_ask", ws_data.get("ask_price")))
    )
    best_bid = _integer(
        bid.get("price", ws_data.get("best_bid", ws_data.get("bid_price")))
    )
    ask_volume = _number(ask.get("volume", ws_data.get("ask_tot")), 0.0)
    bid_volume = _number(bid.get("volume", ws_data.get("bid_tot")), 0.0)
    return best_bid, best_ask, bid_volume, ask_volume


def apply_entry_candle_hybrid_guard(
    result: dict[str, Any] | None,
    candle_context: dict[str, Any] | None,
    ws_data: dict[str, Any] | None,
    recent_ticks: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Demote unsafe BUY results without ever upgrading an AI action."""

    guarded = dict(result or {})
    context = candle_context if isinstance(candle_context, dict) else {}
    ws = ws_data if isinstance(ws_data, dict) else {}
    action = str(guarded.get("action") or "").upper()
    guard_enabled = bool(context.get("enabled")) and _env_bool(
        "KORSTOCKSCAN_ENTRY_CANDLE_HYBRID_GUARD_ENABLED", False
    )
    guard = {
        "enabled": guard_enabled,
        "evaluated": False,
        "result": "not_applicable",
        "positive_groups": [],
        "negative_groups": [],
        "bbo_fresh_consistent": False,
    }
    if not guard_enabled or action != "BUY":
        guarded["entry_candle_hybrid_guard"] = guard
        return guarded

    guard["evaluated"] = True
    source_quality = (
        context.get("source_quality")
        if isinstance(context.get("source_quality"), dict)
        else {}
    )
    if source_quality.get("status") != "fresh_consistent":
        guarded.update(
            {
                "action": "WAIT",
                "score": min(74, _integer(guarded.get("score"), 0)),
                "reason": "Candle source quality requires fresh venue-consistent recheck",
            }
        )
        guard["result"] = "demote_source_quality"
        guarded["entry_candle_hybrid_guard"] = guard
        return guarded

    regime = str(context.get("regime") or "range")
    if regime not in ADVERSE_REGIMES:
        guard["result"] = "preserve_neutral_or_supportive"
        guarded["entry_candle_hybrid_guard"] = guard
        return guarded

    best_bid, best_ask, bid_volume, ask_volume = _best_levels(ws)
    quote_age_ms = _number(ws.get("quote_age_ms"), 999999.0)
    quote_stale = bool(ws.get("quote_stale", False))
    bbo_fresh = (
        best_bid > 0
        and best_ask >= best_bid
        and not quote_stale
        and quote_age_ms <= 3000
    )
    guard["bbo_fresh_consistent"] = bbo_fresh
    structure = (
        context.get("structure") if isinstance(context.get("structure"), dict) else {}
    )
    returns = (
        structure.get("returns_pct")
        if isinstance(structure.get("returns_pct"), dict)
        else {}
    )
    short_return = _number(returns.get("3"), 0.0)
    current_price = _integer(ws.get("curr", ws.get("price")))
    bars = context.get("bars") if isinstance(context.get("bars"), list) else []
    last_close = _integer(bars[-1].get("c")) if bars else 0
    if short_return > 0.03 and current_price >= last_close > 0:
        guard["positive_groups"].append("price_candle_impulse")
    elif short_return < -0.03 or (last_close > 0 and current_price < last_close):
        guard["negative_groups"].append("price_candle_impulse")

    if bid_volume > ask_volume * 1.05 and bid_volume > 0:
        guard["positive_groups"].append("orderbook")
    elif ask_volume > bid_volume * 1.05 and ask_volume > 0:
        guard["negative_groups"].append("orderbook")

    buy_volume = 0.0
    sell_volume = 0.0
    large_sell = bool(ws.get("large_sell_print_detected", False))
    sell_prints = []
    for tick in (recent_ticks or [])[:20]:
        if not isinstance(tick, dict):
            continue
        side = str(tick.get("aggressor_side", tick.get("dir", ""))).upper()
        volume = abs(_number(tick.get("volume"), 0.0))
        if side == "BUY":
            buy_volume += volume
        elif side == "SELL":
            sell_volume += volume
            sell_prints.append(volume)
    total_tape_volume = buy_volume + sell_volume
    if (
        sell_prints
        and total_tape_volume > 0
        and max(sell_prints) >= total_tape_volume * 0.5
        and sell_volume > buy_volume
    ):
        large_sell = True
    if buy_volume > sell_volume * 1.1 and buy_volume > 0:
        guard["positive_groups"].append("signed_tape")
    elif sell_volume > buy_volume * 1.1 and sell_volume > 0:
        guard["negative_groups"].append("signed_tape")
    if large_sell:
        guard["negative_groups"].append("large_sell_warning")

    if (
        bbo_fresh
        and len(set(guard["positive_groups"])) >= 2
        and not guard["negative_groups"]
    ):
        guard["result"] = "preserve_independent_confirmation"
    else:
        guarded.update(
            {
                "action": "WAIT",
                "score": min(74, _integer(guarded.get("score"), 0)),
                "reason": "Adverse candle structure lacks independent fresh confirmation",
            }
        )
        guard["result"] = "demote_adverse_unconfirmed"
    guarded["entry_candle_hybrid_guard"] = guard
    return guarded


def entry_candle_context_log_fields(
    candle_context: dict[str, Any] | None,
    guard_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = candle_context if isinstance(candle_context, dict) else {}
    source = (
        context.get("source_quality")
        if isinstance(context.get("source_quality"), dict)
        else {}
    )
    timing = context.get("timing") if isinstance(context.get("timing"), dict) else {}
    guard = (
        guard_result
        if isinstance(guard_result, dict)
        else (
            context.get("entry_candle_hybrid_guard")
            if isinstance(context.get("entry_candle_hybrid_guard"), dict)
            else {}
        )
    )
    return {
        "entry_candle_context_schema": context.get("schema", SCHEMA),
        "entry_candle_context_enabled": bool(context.get("enabled", False)),
        "entry_candle_venue": context.get("venue"),
        "entry_candle_session": context.get("session"),
        "entry_candle_rest_route": context.get("rest_route"),
        "entry_candle_ws_route": context.get("ws_route"),
        "entry_candle_route_equivalence": context.get("route_equivalence"),
        "entry_candle_route_equivalence_proven": bool(
            context.get("route_equivalence_proven", False)
        ),
        "entry_candle_current_session_bar_count": context.get(
            "current_session_bar_count", 0
        ),
        "entry_candle_previous_session_bar_count": context.get(
            "previous_session_bar_count", 0
        ),
        "entry_candle_completed_bar_count": context.get("completed_bar_count", 0),
        "entry_candle_forming_bar_present": bool(
            context.get("forming_bar_present", False)
        ),
        "entry_candle_latest_bar_age_sec": context.get("latest_bar_age_sec"),
        "entry_candle_sample_mode": context.get("sample_mode"),
        "entry_candle_regime": context.get("regime"),
        "entry_candle_alignment": context.get("alignment"),
        "entry_candle_risk_flags": context.get("risk_flags", []),
        "entry_candle_source_quality_status": source.get("status"),
        "entry_candle_source_quality_blockers": source.get("blockers", []),
        "entry_candle_hybrid_guard_result": guard.get("result"),
        "entry_candle_context_fetch_ms": timing.get("fetch_ms", 0),
        "entry_candle_context_build_ms": timing.get("build_ms", 0),
        **ai_market_snapshot_log_fields(context),
        **OBSERVATION_CONTRACT,
    }
