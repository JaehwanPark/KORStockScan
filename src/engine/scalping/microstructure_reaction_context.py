from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

from src.utils.constants import DATA_DIR


CONTEXT_VERSION = "microstructure_reaction_context_v1"
REPORT_DIR = DATA_DIR / "report" / "microstructure_reaction_context"
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"

CONTEXT_KEYS = (
    "microstructure_reaction_context_version",
    "microstructure_reaction_context_status",
    "microstructure_reaction_tick_aggressor_pressure_usable",
    "microstructure_reaction_tick_aggressor_trusted_count",
    "microstructure_reaction_ask_sweep_score",
    "microstructure_reaction_post_sweep_hold_score",
    "microstructure_reaction_bid_replenishment_score",
    "microstructure_reaction_wall_replenishment_risk_score",
    "microstructure_reaction_vi_proximity_risk",
    "microstructure_reaction_entry_reaction_quality",
    "microstructure_reaction_source_quality",
    "microstructure_reaction_context_hash",
    "tick_trade_value_source_counts",
    "tick_trade_value_1313_count",
    "tick_trade_value_1313_missing_count",
    "tick_trade_value_1313_missing_rate_pct",
    "trade_volume_source_counts",
    "trade_volume_1030_1031_vs_15_evaluable_count",
    "trade_volume_1030_1031_vs_15_mismatch_count",
    "trade_volume_1030_1031_vs_15_mismatch_rate_pct",
    "tick_aggressor_source_counts",
    "kiwoom_0b_aux_observed_count",
    "kiwoom_0b_1313_present_count",
    "kiwoom_0b_1313_missing_count",
    "kiwoom_0b_1313_missing_rate_pct",
    "kiwoom_0b_trade_value_source_counts",
    "kiwoom_0b_trade_volume_source_counts",
    "kiwoom_0b_1030_1031_vs_15_evaluable_count",
    "kiwoom_0b_1030_1031_vs_15_mismatch_count",
    "kiwoom_0b_1030_1031_vs_15_mismatch_rate_pct",
    "ka10003_buy_dominance_observation",
    "ka10003_buy_dominance_observation_source_counts",
    "ka10003_buy_dominance_observation_trade_value_source_counts",
    "ka10003_buy_dominance_observation_inside_spread_count",
    "ka10003_buy_dominance_observation_split_vs_15_evaluable_count",
    "ka10003_buy_dominance_observation_split_vs_15_mismatch_count",
    "v_pw_now",
    "v_pw_source",
    "v_pw_runtime_support_usable",
    "v_pw_ws_value",
    "v_pw_rest_value",
    "ka10046_strength_source",
    "ka10046_strength_decision_authority",
    "ka10046_strength_runtime_effect",
    "ka10046_strength_rest_received_ts_ms",
    "market_data_signed_tape_state",
    "market_data_signed_tape_sample_count",
    "market_data_signed_tape_buy_count",
    "market_data_signed_tape_sell_count",
    "market_data_signed_tape_buy_volume",
    "market_data_signed_tape_sell_volume",
    "market_data_signed_tape_buy_ratio_pct",
    "market_data_rest_signed_tape_pressure_usable",
    "rest_signed_trade_ticks",
    "latency_true_ofi_direct_canary_signed_tape_window",
    "latency_true_ofi_direct_canary_signed_tape_min_samples",
    "latency_true_ofi_direct_canary_signed_tape_max_buy_ratio",
    "latency_true_ofi_direct_canary_signed_tape_sample_count",
    "latency_true_ofi_direct_canary_signed_tape_buy_count",
    "latency_true_ofi_direct_canary_signed_tape_sell_count",
    "latency_true_ofi_direct_canary_signed_tape_buy_volume",
    "latency_true_ofi_direct_canary_signed_tape_sell_volume",
    "latency_true_ofi_direct_canary_signed_tape_net_buy_volume",
    "latency_true_ofi_direct_canary_signed_tape_buy_ratio",
    "latency_true_ofi_direct_canary_signed_tape_latest_side",
    "latency_true_ofi_direct_canary_signed_tape_sell_dominated",
    "latency_true_ofi_direct_canary_signed_tape_latest_buy_single",
    "latency_true_ofi_direct_canary_signed_tape_latest_sell_single",
    "latency_true_ofi_direct_canary_signed_tape_latest_single_sell_dominated",
    "latency_true_ofi_direct_canary_tape_block_reason",
    "latency_true_ofi_direct_canary_tape_support_ok",
    "quote_stale",
    "quote_age_ms",
    "quote_age_at_submit_ms",
    "ws_age_ms",
    "market_data_freshness_state",
)

GENERIC_FRESHNESS_CONTEXT_KEYS = {
    "quote_stale",
    "quote_age_ms",
    "quote_age_at_submit_ms",
    "ws_age_ms",
    "market_data_freshness_state",
}

FORBIDDEN_USES = [
    "standalone_buy",
    "broker_guard_bypass",
    "threshold_mutation",
    "provider_route_change",
    "bot_restart",
    "cap_release",
]

WORKORDER_FORBIDDEN_USES = [
    "standalone_buy",
    "submit_permission",
    "pressure_math",
    "broker_guard_bypass",
    "stale_quote_guard_bypass",
    "order_guard_relaxation",
    "threshold_mutation",
    "provider_route_change",
    "bot_restart",
    "cap_release",
    "real_execution_quality_approval",
]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "", "-"):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    return default


def _clamp_score(value: float) -> int:
    return int(max(0, min(100, round(value))))


def _rate_pct(numerator: int, denominator: int) -> float:
    return round((numerator / denominator) * 100.0, 3) if denominator > 0 else 0.0


def _dict_counter(value: Any) -> Counter:
    if isinstance(value, dict):
        return Counter({str(key): int(_safe_float(count, 0.0)) for key, count in value.items()})
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("{") and text.endswith("}"):
            try:
                parsed = ast.literal_eval(text)
            except (SyntaxError, ValueError):
                parsed = None
            if isinstance(parsed, dict):
                return Counter({str(key): int(_safe_float(count, 0.0)) for key, count in parsed.items()})
    return Counter()


def _list_value(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = ast.literal_eval(text)
            except (SyntaxError, ValueError):
                parsed = None
            if isinstance(parsed, list):
                return parsed
    return []


def _safe_hhmmss_to_seconds(value: Any) -> int | None:
    try:
        text = str(value or "").replace(":", "").strip()
        if not text:
            return None
        if not text.isdigit():
            return None
        text = text.zfill(6)
        hour = int(text[0:2])
        minute = int(text[2:4])
        second = int(text[4:6])
        if hour > 23 or minute > 59 or second > 59:
            return None
        return (hour * 3600) + (minute * 60) + second
    except Exception:
        return None


def _normalize_tick_side(value: Any) -> str:
    raw = str(value or "").strip().upper()
    compact = raw.replace("+", "").replace("-", "").replace(" ", "")
    if raw in {"BUY", "B", "2"} or "매수" in compact:
        return "BUY"
    if raw in {"SELL", "S", "1"} or "매도" in compact:
        return "SELL"
    return raw


def _tick_price(tick: dict[str, Any]) -> float:
    return _safe_float(
        tick.get("price")
        or tick.get("trade_price")
        or tick.get("cur_prc")
        or tick.get("현재가")
        or tick.get("체결가"),
        0.0,
    )


def _tick_best_ask(tick: dict[str, Any]) -> float:
    return _safe_float(
        tick.get("best_ask")
        or tick.get("ask_price")
        or tick.get("ask")
        or tick.get("27"),
        0.0,
    )


def _tick_best_bid(tick: dict[str, Any]) -> float:
    return _safe_float(
        tick.get("best_bid")
        or tick.get("bid_price")
        or tick.get("bid")
        or tick.get("28"),
        0.0,
    )


TRUSTED_AGGRESSOR_SOURCES = {
    "orderbook_touch",
    "cached_orderbook_touch",
    "kiwoom_0b_signed_trade_volume",
    "provider_declared_side",
    "exchange_declared_side",
    "trusted_declared_side",
    "declared_aggressor_side",
}

ORDERBOOK_TOUCH_SOURCES = {
    "orderbook_touch",
    "cached_orderbook_touch",
}

ORDERBOOK_TOUCH_QUOTE_SOURCES = {
    "0B_inline_best_quote",
    "cached_top_of_book_ttl",
}


def infer_tick_aggressor_side(tick: dict[str, Any] | None) -> dict[str, Any]:
    tick = tick if isinstance(tick, dict) else {}
    declared_source = str(tick.get("aggressor_source") or tick.get("dir_source") or "").strip()
    declared_quality = str(tick.get("aggressor_quality") or "").strip()
    quote_source = str(tick.get("aggressor_quote_source") or "").strip()
    touch_source = (
        "cached_orderbook_touch"
        if declared_source == "cached_orderbook_touch" or quote_source == "cached_top_of_book_ttl"
        else "orderbook_touch"
    )

    def _touch_quality(default: str) -> str:
        if declared_quality and (
            declared_source in {"orderbook_touch", "cached_orderbook_touch"} or quote_source
        ):
            return declared_quality
        return default
    explicit = _normalize_tick_side(
        tick.get("aggressor_side")
        or tick.get("trade_aggressor_side")
        or tick.get("dir")
        or tick.get("side")
    )
    trade_price = _tick_price(tick)
    best_ask = _tick_best_ask(tick)
    best_bid = _tick_best_bid(tick)
    if explicit in {"BUY", "SELL"} and declared_source == "kiwoom_0b_signed_trade_volume":
        return {
            "side": explicit,
            "source": declared_source,
            "quality": declared_quality or "signed_trade_volume",
            "declared_side": explicit,
            "trade_price": trade_price,
            "best_ask": best_ask,
            "best_bid": best_bid,
            "touch_side": str(tick.get("aggressor_touch_side") or "UNKNOWN"),
            "touch_source": str(tick.get("aggressor_touch_source") or ""),
            "touch_quality": str(tick.get("aggressor_touch_quality") or ""),
            "touch_confirms_signed": tick.get("aggressor_touch_confirms_signed"),
        }
    if trade_price > 0 and (best_ask > 0 or best_bid > 0):
        raw_inline_quote = not declared_source and not quote_source and ("27" in tick or "28" in tick)
        trusted_touch_source = (
            declared_source in ORDERBOOK_TOUCH_SOURCES
            or quote_source in ORDERBOOK_TOUCH_QUOTE_SOURCES
            or raw_inline_quote
        )
        if not trusted_touch_source:
            return {
                "side": "UNKNOWN",
                "source": declared_source or "untrusted_orderbook_touch_source",
                "quality": "quote_with_untrusted_aggressor_source",
                "declared_side": explicit if explicit in {"BUY", "SELL"} else "UNKNOWN",
                "trade_price": trade_price,
                "best_ask": best_ask,
                "best_bid": best_bid,
            }
        if best_ask <= 0 or best_bid <= 0:
            return {
                "side": "UNKNOWN",
                "source": "missing_best_quote",
                "quality": "partial_orderbook_touch_quote",
                "trade_price": trade_price,
                "best_ask": best_ask,
                "best_bid": best_bid,
            }
        if best_ask > 0 and trade_price >= best_ask:
            return {
                "side": "BUY",
                "source": touch_source,
                "quality": _touch_quality("touch_or_crossed_ask"),
                "trade_price": trade_price,
                "best_ask": best_ask,
                "best_bid": best_bid,
            }
        if best_bid > 0 and trade_price <= best_bid:
            return {
                "side": "SELL",
                "source": touch_source,
                "quality": _touch_quality("touch_or_crossed_bid"),
                "trade_price": trade_price,
                "best_ask": best_ask,
                "best_bid": best_bid,
            }
        return {
            "side": "UNKNOWN",
            "source": touch_source,
            "quality": _touch_quality("inside_spread_or_uncertain"),
            "trade_price": trade_price,
            "best_ask": best_ask,
            "best_bid": best_bid,
        }
    if explicit in {"BUY", "SELL"} and declared_source in TRUSTED_AGGRESSOR_SOURCES:
        return {
            "side": explicit,
            "source": declared_source,
            "quality": str(tick.get("aggressor_quality") or "side_without_orderbook_touch"),
            "trade_price": trade_price,
            "best_ask": best_ask,
            "best_bid": best_bid,
        }
    if explicit in {"BUY", "SELL"}:
        return {
            "side": "UNKNOWN",
            "source": declared_source or "declared_tick_side_untrusted",
            "quality": "side_without_trusted_source",
            "declared_side": explicit,
            "trade_price": trade_price,
            "best_ask": best_ask,
            "best_bid": best_bid,
        }
    return {
        "side": "UNKNOWN",
        "source": "missing_aggressor_side",
        "quality": "missing_orderbook_touch_and_side",
        "trade_price": trade_price,
        "best_ask": best_ask,
        "best_bid": best_bid,
    }


def _aggressor_pressure_usable(inferred: dict[str, Any] | None) -> bool:
    inferred = inferred if isinstance(inferred, dict) else {}
    if inferred.get("side") not in {"BUY", "SELL"}:
        return False
    return str(inferred.get("source") or "").strip() in TRUSTED_AGGRESSOR_SOURCES


def _age_ms_from_hhmmss(value: Any, *, now: datetime | None = None) -> int | None:
    tick_sec = _safe_hhmmss_to_seconds(value)
    if tick_sec is None:
        return None
    now_dt = now or datetime.now()
    now_sec = now_dt.hour * 3600 + now_dt.minute * 60 + now_dt.second
    age_sec = now_sec - tick_sec
    if age_sec < -43200:
        age_sec += 86400
    elif age_sec > 43200:
        age_sec -= 86400
    return max(0, int(age_sec * 1000))


def _safe_epoch_ms(value: Any) -> int | None:
    if value in (None, "", "-"):
        return None
    try:
        numeric = float(value)
        if numeric <= 0:
            return None
        if numeric > 1_000_000_000_000:
            return int(numeric)
        if numeric > 1_000_000_000:
            return int(numeric * 1000)
    except (TypeError, ValueError):
        pass
    try:
        text = str(value).strip()
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        return int(datetime.fromisoformat(text).timestamp() * 1000)
    except Exception:
        return None


def _quote_age_ms(ws_data: dict[str, Any], *, now: datetime | None = None) -> tuple[int | None, str]:
    quote_ts_keys = (
        "quote_age_ms",
        "ws_age_ms",
        "ws_received_at_ms",
        "quote_received_at_ms",
        "received_at_ms",
        "last_ws_update_ts",
        "last_update_ms",
        "updated_at_ms",
        "captured_at_ms",
        "timestamp_ms",
        "ts_ms",
        "updated_at",
        "timestamp",
    )
    now_ms = int((now or datetime.now()).timestamp() * 1000)
    for key in quote_ts_keys:
        raw = ws_data.get(key)
        if key in {"quote_age_ms", "ws_age_ms"}:
            age_value = _safe_float(raw, -1.0)
            if age_value >= 0:
                return int(age_value), key
            continue
        epoch_ms = _safe_epoch_ms(raw)
        if epoch_ms is None:
            continue
        return max(0, now_ms - epoch_ms), key
    return None, "missing"


def precompute_microstructure_reaction_inputs(
    ws_data: dict[str, Any] | None,
    recent_ticks: list[dict[str, Any]] | None,
    recent_candles: list[dict[str, Any]] | None = None,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    ws_data = ws_data if isinstance(ws_data, dict) else {}
    recent_ticks = recent_ticks if isinstance(recent_ticks, list) else []
    recent_candles = recent_candles if isinstance(recent_candles, list) else []
    orderbook = ws_data.get("orderbook") if isinstance(ws_data.get("orderbook"), dict) else {}
    asks = [level for level in (orderbook.get("asks") if isinstance(orderbook.get("asks"), list) else []) if isinstance(level, dict)]
    bids = [level for level in (orderbook.get("bids") if isinstance(orderbook.get("bids"), list) else []) if isinstance(level, dict)]
    curr_price = _safe_float(ws_data.get("curr") or ws_data.get("curr_price"), 0.0)
    best_ask = _safe_float(asks[0].get("price") if asks else 0, curr_price)
    best_bid = _safe_float(bids[0].get("price") if bids else 0, curr_price)
    best_ask_vol = _safe_float(asks[0].get("volume") if asks else 0, 0.0)
    best_bid_vol = _safe_float(bids[0].get("volume") if bids else 0, 0.0)
    top3_ask_vol = sum(_safe_float(level.get("volume"), 0.0) for level in asks[:3])
    top3_bid_vol = sum(_safe_float(level.get("volume"), 0.0) for level in bids[:3])
    ticks = [tick for tick in recent_ticks[:10] if isinstance(tick, dict)]
    tick_latest_time = str(ticks[0].get("time") or "") if ticks else ""
    tick_age_ms = _age_ms_from_hhmmss(tick_latest_time, now=now) if tick_latest_time else None
    tick_secs = [_safe_hhmmss_to_seconds(tick.get("time")) for tick in ticks]
    aggressor_rows = [infer_tick_aggressor_side(tick) for tick in ticks]
    tick_trade_value_source_counts = Counter(
        str(tick.get("tick_trade_value_source") or "unknown")
        for tick in ticks
        if "tick_trade_value_source" in tick
    )
    tick_trade_value_observed_count = sum(tick_trade_value_source_counts.values())
    tick_trade_value_1313_count = tick_trade_value_source_counts.get("1313", 0)
    tick_trade_value_1313_missing_count = max(
        0,
        tick_trade_value_observed_count - tick_trade_value_1313_count,
    )
    trade_volume_source_counts = Counter(
        str(tick.get("volume_source") or tick.get("trade_volume_source") or "unknown")
        for tick in ticks
        if "volume_source" in tick or "trade_volume_source" in tick
    )
    trade_volume_mismatch_rows = [
        tick
        for tick in ticks
        if "trade_volume_1030_1031_vs_15_mismatch" in tick
    ]
    trade_volume_mismatch_count = sum(
        1
        for tick in trade_volume_mismatch_rows
        if _safe_bool(tick.get("trade_volume_1030_1031_vs_15_mismatch"), False)
    )
    pressure_rows = [
        (tick, inferred)
        for tick, inferred in zip(ticks, aggressor_rows)
        if _aggressor_pressure_usable(inferred)
    ]
    buy_vol = sum(
        _safe_float(tick.get("volume"), 0.0)
        for tick, inferred in pressure_rows
        if inferred.get("side") == "BUY"
    )
    sell_vol = sum(
        _safe_float(tick.get("volume"), 0.0)
        for tick, inferred in pressure_rows
        if inferred.get("side") == "SELL"
    )
    total_vol = buy_vol + sell_vol
    buy_pressure_pct = (buy_vol / total_vol * 100.0) if total_vol > 0 else 50.0
    prices: list[float] = []
    volumes: list[float] = []
    pressure_volumes: list[float] = []
    for tick in ticks:
        price_value = _safe_float(tick.get("price"), 0.0)
        if price_value > 0:
            prices.append(price_value)
        volume_value = _safe_float(tick.get("volume"), 0.0)
        if volume_value > 0:
            volumes.append(volume_value)
    for tick, _inferred in pressure_rows:
        volume_value = _safe_float(tick.get("volume"), 0.0)
        if volume_value > 0:
            pressure_volumes.append(volume_value)
    latest_price = prices[0] if prices else curr_price
    oldest_price = prices[-1] if prices else curr_price
    price_change_pct = ((latest_price - oldest_price) / oldest_price * 100.0) if oldest_price > 0 else 0.0
    avg_tick_volume = mean(volumes) if volumes else 0.0
    avg_pressure_tick_volume = mean(pressure_volumes) if pressure_volumes else 0.0
    buy_at_or_above_ask_vol = sum(
        _safe_float(tick.get("volume"), 0.0)
        for tick, inferred in pressure_rows
        if inferred.get("side") == "BUY" and _safe_float(tick.get("price"), 0.0) >= best_ask
    )
    large_buy_print_detected = any(
        _aggressor_pressure_usable(inferred)
        and inferred.get("side") == "BUY"
        and _safe_float(tick.get("volume"), 0.0) >= avg_pressure_tick_volume * 2.2
        for tick, inferred in zip(ticks[:5], aggressor_rows[:5])
    ) if avg_pressure_tick_volume > 0 else False
    large_sell_print_detected = any(
        _aggressor_pressure_usable(inferred)
        and inferred.get("side") == "SELL"
        and _safe_float(tick.get("volume"), 0.0) >= avg_pressure_tick_volume * 2.2
        for tick, inferred in zip(ticks[:5], aggressor_rows[:5])
    ) if avg_pressure_tick_volume > 0 else False
    price_buy_count: dict[float, int] = {}
    for tick, inferred in zip(ticks[:6], aggressor_rows[:6]):
        if not _aggressor_pressure_usable(inferred):
            continue
        if inferred.get("side") != "BUY":
            continue
        price_key = _safe_float(tick.get("price"), 0.0)
        price_buy_count[price_key] = price_buy_count.get(price_key, 0) + 1
    same_price_buy_absorption = max(price_buy_count.values()) if price_buy_count else 0
    candle_highs: list[float] = []
    candle_lows: list[float] = []
    for candle in recent_candles:
        if not isinstance(candle, dict):
            continue
        high_value = _safe_float(candle.get("고가"), 0.0)
        if high_value > 0:
            candle_highs.append(high_value)
        low_value = _safe_float(candle.get("저가"), 0.0)
        if low_value > 0:
            candle_lows.append(low_value)
    quote_age_ms, quote_age_source = _quote_age_ms(ws_data, now=now)
    return {
        "ws_data": ws_data,
        "recent_ticks": recent_ticks,
        "recent_candles": recent_candles,
        "asks": asks,
        "bids": bids,
        "curr_price": curr_price,
        "best_ask": best_ask,
        "best_bid": best_bid,
        "best_ask_vol": best_ask_vol,
        "best_bid_vol": best_bid_vol,
        "top3_ask_vol": top3_ask_vol,
        "top3_bid_vol": top3_bid_vol,
        "ticks": ticks,
        "tick_aggressor_rows": aggressor_rows,
        "tick_aggressor_source_counts": dict(Counter(str(row.get("source") or "unknown") for row in aggressor_rows)),
        "tick_aggressor_quality_counts": dict(Counter(str(row.get("quality") or "unknown") for row in aggressor_rows)),
        "tick_trade_value_source_counts": dict(sorted(tick_trade_value_source_counts.items())),
        "tick_trade_value_1313_count": int(tick_trade_value_1313_count),
        "tick_trade_value_1313_missing_count": int(tick_trade_value_1313_missing_count),
        "tick_trade_value_1313_missing_rate_pct": _rate_pct(
            tick_trade_value_1313_missing_count,
            tick_trade_value_observed_count,
        ),
        "trade_volume_source_counts": dict(sorted(trade_volume_source_counts.items())),
        "trade_volume_1030_1031_vs_15_evaluable_count": len(trade_volume_mismatch_rows),
        "trade_volume_1030_1031_vs_15_mismatch_count": int(trade_volume_mismatch_count),
        "trade_volume_1030_1031_vs_15_mismatch_rate_pct": _rate_pct(
            trade_volume_mismatch_count,
            len(trade_volume_mismatch_rows),
        ),
        "tick_aggressor_unknown_count": sum(1 for row in aggressor_rows if row.get("side") not in {"BUY", "SELL"}),
        "tick_aggressor_orderbook_touch_count": sum(1 for row in aggressor_rows if row.get("source") == "orderbook_touch"),
        "tick_aggressor_cached_orderbook_touch_count": sum(
            1 for row in aggressor_rows if row.get("source") == "cached_orderbook_touch"
        ),
        "tick_aggressor_price_heuristic_count": sum(
            1 for row in aggressor_rows if row.get("source") == "price_change_heuristic"
        ),
        "tick_aggressor_trusted_count": len(pressure_rows),
        "tick_aggressor_pressure_usable": bool(pressure_rows),
        "tick_sample_count": len(ticks),
        "tick_latest_time": tick_latest_time,
        "tick_age_ms": tick_age_ms,
        "tick_secs": tick_secs,
        "buy_vol": buy_vol,
        "sell_vol": sell_vol,
        "total_vol": total_vol,
        "buy_pressure_pct": buy_pressure_pct,
        "latest_price": latest_price,
        "oldest_price": oldest_price,
        "price_change_pct": price_change_pct,
        "avg_tick_volume": avg_tick_volume,
        "buy_at_or_above_ask_vol": buy_at_or_above_ask_vol,
        "large_buy_print_detected": large_buy_print_detected,
        "large_sell_print_detected": large_sell_print_detected,
        "same_price_buy_absorption": same_price_buy_absorption,
        "quote_age_ms": quote_age_ms,
        "quote_age_source": quote_age_source,
        "candle_highs": candle_highs,
        "candle_lows": candle_lows,
        "session_high": max(candle_highs or [curr_price]),
        "session_low": min(candle_lows or [curr_price]),
    }


def _context_hash(payload: dict[str, Any]) -> str:
    compact = {
        key: payload.get(key)
        for key in CONTEXT_KEYS
        if key != "microstructure_reaction_context_hash"
    }
    raw = json.dumps(compact, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def neutral_microstructure_reaction_context(status: str, reason: str) -> dict[str, Any]:
    payload = {
        "microstructure_reaction_context_version": CONTEXT_VERSION,
        "microstructure_reaction_context_status": status,
        "microstructure_reaction_tick_aggressor_pressure_usable": False,
        "microstructure_reaction_tick_aggressor_trusted_count": 0,
        "microstructure_reaction_ask_sweep_score": 50,
        "microstructure_reaction_post_sweep_hold_score": 50,
        "microstructure_reaction_bid_replenishment_score": 50,
        "microstructure_reaction_wall_replenishment_risk_score": 50,
        "microstructure_reaction_vi_proximity_risk": 0,
        "microstructure_reaction_entry_reaction_quality": "neutral_unusable",
        "microstructure_reaction_source_quality": reason,
    }
    payload["microstructure_reaction_context_hash"] = _context_hash(payload)
    return payload


def build_microstructure_reaction_context(
    ws_data: dict[str, Any] | None,
    recent_ticks: list[dict[str, Any]] | None,
    recent_candles: list[dict[str, Any]] | None = None,
    *,
    now: datetime | None = None,
    precomputed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    snapshot = precomputed if isinstance(precomputed, dict) else precompute_microstructure_reaction_inputs(
        ws_data,
        recent_ticks,
        recent_candles,
        now=now,
    )
    ws_data = snapshot.get("ws_data") if isinstance(snapshot.get("ws_data"), dict) else {}
    recent_candles = snapshot.get("recent_candles") if isinstance(snapshot.get("recent_candles"), list) else []
    asks = snapshot.get("asks") if isinstance(snapshot.get("asks"), list) else []
    bids = snapshot.get("bids") if isinstance(snapshot.get("bids"), list) else []
    if not asks or not bids:
        return neutral_microstructure_reaction_context("source_quality_missing", "missing_orderbook")
    if int(snapshot.get("tick_sample_count") or 0) < 5:
        return neutral_microstructure_reaction_context("insufficient_window", "tick_sample_lt5")

    tick_age_ms = snapshot.get("tick_age_ms")
    quote_age_ms = snapshot.get("quote_age_ms")
    if (tick_age_ms is not None and tick_age_ms > 5000) or (quote_age_ms is not None and quote_age_ms > 1200):
        return neutral_microstructure_reaction_context("stale", "stale_tick_or_quote")
    curr_price = _safe_float(snapshot.get("curr_price"), 0.0)
    best_ask = _safe_float(snapshot.get("best_ask"), curr_price)
    best_bid = _safe_float(snapshot.get("best_bid"), curr_price)
    top3_ask_vol = _safe_float(snapshot.get("top3_ask_vol"), 0.0)
    top3_bid_vol = _safe_float(snapshot.get("top3_bid_vol"), 0.0)
    top3_depth_ratio = top3_ask_vol / top3_bid_vol if top3_bid_vol > 0 else 9.99

    ticks = snapshot.get("ticks") if isinstance(snapshot.get("ticks"), list) else []
    buy_vol = _safe_float(snapshot.get("buy_vol"), 0.0)
    sell_vol = _safe_float(snapshot.get("sell_vol"), 0.0)
    total_vol = _safe_float(snapshot.get("total_vol"), 0.0)
    pressure_usable = _safe_bool(snapshot.get("tick_aggressor_pressure_usable"), False) and total_vol > 0
    pressure_trusted_count = _safe_int(snapshot.get("tick_aggressor_trusted_count"), 0)
    if not pressure_usable:
        payload = neutral_microstructure_reaction_context(
            "source_quality_partial",
            "tick_aggressor_pressure_unusable",
        )
        payload["microstructure_reaction_tick_aggressor_trusted_count"] = pressure_trusted_count
        payload["microstructure_reaction_context_hash"] = _context_hash(payload)
        return payload
    buy_pressure = _safe_float(snapshot.get("buy_pressure_pct"), 50.0)
    latest_price = _safe_float(snapshot.get("latest_price"), curr_price)
    price_change_pct = _safe_float(snapshot.get("price_change_pct"), 0.0)
    buy_at_or_above_ask = _safe_float(snapshot.get("buy_at_or_above_ask_vol"), 0.0)
    ask_sweep_share = buy_at_or_above_ask / total_vol if total_vol > 0 else 0.0
    avg_vol = _safe_float(snapshot.get("avg_tick_volume"), 0.0)
    large_buy = bool(snapshot.get("large_buy_print_detected")) if avg_vol > 0 else False
    large_sell = bool(snapshot.get("large_sell_print_detected")) if avg_vol > 0 else False

    ask_sweep_score = _clamp_score(35 + (buy_pressure - 50) * 0.7 + ask_sweep_share * 35 + (12 if price_change_pct > 0 else 0) + (8 if large_buy else 0))
    post_sweep_hold_score = _clamp_score(50 + min(25, max(-25, price_change_pct * 45)) + (12 if latest_price >= best_ask else 0) - (15 if latest_price < best_bid else 0))
    bid_ratio = top3_bid_vol / top3_ask_vol if top3_ask_vol > 0 else 2.0
    bid_replenishment_score = _clamp_score(45 + min(30, bid_ratio * 14) + (10 if sell_vol > 0 and price_change_pct >= -0.05 else 0) - (10 if latest_price < best_bid else 0))
    wall_replenishment_risk_score = _clamp_score(25 + max(0, top3_depth_ratio - 1.0) * 28 + (16 if large_sell else 0) + (10 if buy_pressure < 55 else 0))

    fluctuation = _safe_float(ws_data.get("fluctuation"), 0.0)
    high = _safe_float(snapshot.get("session_high"), curr_price)
    low = _safe_float(snapshot.get("session_low"), curr_price)
    distance_from_high = ((curr_price - high) / high * 100.0) if high > 0 and curr_price > 0 else -99.0
    intraday_range = ((high - low) / low * 100.0) if high >= low and low > 0 else 0.0
    vi_proximity_risk = _clamp_score(max(0, fluctuation - 20) * 6 + (20 if distance_from_high >= -0.25 and intraday_range >= 12 else 0))

    if wall_replenishment_risk_score >= 70 or vi_proximity_risk >= 70:
        quality = "risk_context_only"
    elif ask_sweep_score >= 65 and post_sweep_hold_score >= 60 and bid_replenishment_score >= 55:
        quality = "favorable_reaction"
    elif ask_sweep_score <= 40 or post_sweep_hold_score <= 40:
        quality = "weak_reaction"
    else:
        quality = "mixed_reaction"

    payload = {
        "microstructure_reaction_context_version": CONTEXT_VERSION,
        "microstructure_reaction_context_status": "ok",
        "microstructure_reaction_tick_aggressor_pressure_usable": bool(pressure_usable),
        "microstructure_reaction_tick_aggressor_trusted_count": pressure_trusted_count,
        "microstructure_reaction_ask_sweep_score": ask_sweep_score,
        "microstructure_reaction_post_sweep_hold_score": post_sweep_hold_score,
        "microstructure_reaction_bid_replenishment_score": bid_replenishment_score,
        "microstructure_reaction_wall_replenishment_risk_score": wall_replenishment_risk_score,
        "microstructure_reaction_vi_proximity_risk": vi_proximity_risk,
        "microstructure_reaction_entry_reaction_quality": quality,
        "microstructure_reaction_source_quality": "fresh_short_window",
    }
    payload["microstructure_reaction_context_hash"] = _context_hash(payload)
    return payload


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"microstructure_reaction_context_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _event_path(target_date: str) -> Path:
    path = PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"
    if path.exists():
        return path
    gz_path = Path(f"{path}.gz")
    return gz_path


def _iter_jsonl(path: Path):
    if not path.exists():
        return
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def _has_context(fields: dict[str, Any]) -> bool:
    return any(key in fields for key in CONTEXT_KEYS if key not in GENERIC_FRESHNESS_CONTEXT_KEYS)


def _row_from_event(event: dict[str, Any]) -> dict[str, Any] | None:
    fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
    if not _has_context(fields):
        return None
    row = {
        "stock_code": str(event.get("stock_code") or fields.get("stock_code") or "").lstrip("A"),
        "stock_name": event.get("stock_name"),
        "event_time": event.get("emitted_at") or fields.get("event_time") or fields.get("event_ts"),
        "event_ts": fields.get("event_ts") or event.get("emitted_at"),
        "record_id": event.get("record_id") or fields.get("record_id"),
        "sim_record_id": fields.get("sim_record_id"),
        "sim_parent_record_id": fields.get("sim_parent_record_id"),
        "source_event_stage": fields.get("source_event_stage") or event.get("stage"),
        "stage": event.get("stage"),
        "actual_order_submitted": _safe_bool(fields.get("actual_order_submitted"), False),
        "broker_order_forbidden": (
            _safe_bool(fields.get("broker_order_forbidden"), False)
            if "broker_order_forbidden" in fields
            else None
        ),
    }
    row.update({key: fields.get(key) for key in CONTEXT_KEYS})
    observation = fields.get("ka10003_buy_dominance_observation")
    if isinstance(observation, dict):
        row["ka10003_buy_dominance_observation_source_counts"] = (
            row.get("ka10003_buy_dominance_observation_source_counts")
            or observation.get("source_counts")
            or {}
        )
        row["ka10003_buy_dominance_observation_trade_value_source_counts"] = (
            row.get("ka10003_buy_dominance_observation_trade_value_source_counts")
            or observation.get("trade_value_source_counts")
            or {}
        )
        row["ka10003_buy_dominance_observation_inside_spread_count"] = (
            row.get("ka10003_buy_dominance_observation_inside_spread_count")
            if row.get("ka10003_buy_dominance_observation_inside_spread_count") not in (None, "")
            else observation.get("inside_spread_count")
        )
        row["ka10003_buy_dominance_observation_split_vs_15_evaluable_count"] = (
            row.get("ka10003_buy_dominance_observation_split_vs_15_evaluable_count")
            if row.get("ka10003_buy_dominance_observation_split_vs_15_evaluable_count") not in (None, "")
            else observation.get("split_vs_15_evaluable_count")
        )
        row["ka10003_buy_dominance_observation_split_vs_15_mismatch_count"] = (
            row.get("ka10003_buy_dominance_observation_split_vs_15_mismatch_count")
            if row.get("ka10003_buy_dominance_observation_split_vs_15_mismatch_count") not in (None, "")
            else observation.get("split_vs_15_mismatch_count")
        )
    return row


def _sum_int(rows: list[dict[str, Any]], key: str) -> int:
    return sum(_safe_int(row.get(key), 0) for row in rows)


def _sum_counter_rows(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter: Counter = Counter()
    for row in rows:
        counter.update(_dict_counter(row.get(key)))
    return dict(sorted(counter.items()))


def _field_counter(rows: list[dict[str, Any]], key: str, *, default: str = "missing") -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key) or default) for row in rows).items()))


def _rest_signed_trade_tick_count(rows: list[dict[str, Any]]) -> int:
    return sum(len(_list_value(row.get("rest_signed_trade_ticks"))) for row in rows)


def _rest_signed_trade_tick_source_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter = Counter()
    for row in rows:
        for tick in _list_value(row.get("rest_signed_trade_ticks")):
            if not isinstance(tick, dict):
                counter["unparsed"] += 1
                continue
            source = (
                tick.get("rest_signed_tape_source")
                or tick.get("aggressor_source")
                or tick.get("source")
                or "unknown"
            )
            counter[str(source)] += 1
    return dict(sorted(counter.items()))


def _quote_freshness_state(row: dict[str, Any]) -> str:
    raw_state = str(row.get("market_data_freshness_state") or "").strip().lower()
    if raw_state in {"fresh", "stale", "missing", "unknown"}:
        return raw_state
    if "quote_stale" in row:
        if _safe_bool(row.get("quote_stale"), False):
            return "stale"
        return "fresh"
    age_candidates = (
        row.get("quote_age_ms"),
        row.get("quote_age_at_submit_ms"),
        row.get("ws_age_ms"),
    )
    ages = [_safe_float(value, -1.0) for value in age_candidates]
    ages = [age for age in ages if age >= 0]
    if not ages:
        return "unknown"
    return "stale" if min(ages) > 1200.0 else "fresh"


def _strength_diff_rows(rows: list[dict[str, Any]]) -> list[float]:
    diffs: list[float] = []
    for row in rows:
        ws_value = _safe_float(row.get("v_pw_ws_value"), 0.0)
        rest_value = _safe_float(row.get("v_pw_rest_value"), 0.0)
        if ws_value <= 0 or rest_value <= 0:
            continue
        diffs.append(abs(ws_value - rest_value))
    return diffs


def _microstructure_code_improvement_orders(summary: dict[str, Any], report_path: Path) -> list[dict[str, Any]]:
    orders: list[dict[str, Any]] = []

    def base_order(order_id: str, title: str, *, route: str, improvement_type: str, evidence: list[str]) -> dict[str, Any]:
        order = {
            "order_id": order_id,
            "title": title,
            "source_report_type": "microstructure_reaction_context",
            "target_subsystem": "runtime_instrumentation",
            "lifecycle_stage": "entry_source_quality",
            "route": route,
            "threshold_family": "microstructure_reaction_context",
            "improvement_type": improvement_type,
            "priority": 2,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "decision_authority": "entry_confidence_modifier_source_only",
            "metric_role": "source_quality_gate",
            "primary_decision_metric": "source_quality_adjusted_ev_pct",
            "source_quality_gate": "microstructure source contract and forbidden-use counters",
            "forbidden_uses": list(WORKORDER_FORBIDDEN_USES),
            "evidence": [
                *evidence,
                "runtime_effect=false",
                "allowed_runtime_apply=false",
                "actual_order_submitted=false",
                "broker_order_forbidden=true",
            ],
            "expected_ev_effect": (
                "Close market-data provenance gaps before any later bounded runtime family can consume "
                "microstructure evidence."
            ),
            "files_likely_touched": [
                "src/engine/scalping/microstructure_reaction_context.py",
                "src/engine/scalping/market_data_enrichment.py",
                "src/utils/pipeline_event_logger.py",
                "src/engine/build_code_improvement_workorder.py",
            ],
            "acceptance_tests": [
                "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_microstructure_reaction_context_report.py src/tests/test_market_data_enrichment.py src/tests/test_pipeline_event_logger.py src/tests/test_build_code_improvement_workorder.py",
                "regenerated microstructure_reaction_context keeps runtime_effect=false and allowed_runtime_apply=false",
                "postclose code_improvement_workorder includes or explicitly closes this source-only order",
            ],
            "source_paths": [str(report_path)],
            "implementation_provenance": {
                "implementation_type": "microstructure_source_quality_workorder_handoff",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "requires_separate_runtime_apply_candidate": True,
            },
        }
        if route == "auto_family_candidate":
            order["candidate_family"] = "microstructure_signed_tape_runtime_candidate"
        else:
            order["mapped_family"] = "microstructure_reaction_context"
        return order

    if _safe_int(summary.get("market_data_rest_signed_tape_pressure_usable_true_count"), 0) > 0:
        orders.append(
            base_order(
                "order_microstructure_rest_signed_tape_pressure_authority_violation",
                "REST signed tape pressure authority violation",
                route="instrumentation_order",
                improvement_type="source_quality_forbidden_use_violation",
                evidence=[
                    "market_data_rest_signed_tape_pressure_usable_true_count="
                    f"{summary.get('market_data_rest_signed_tape_pressure_usable_true_count')}",
                    "REST signed tape must remain negative-veto/source-quality provenance only",
                ],
            )
        )

    if _safe_int(summary.get("ka10046_strength_runtime_effect_true_count"), 0) > 0:
        orders.append(
            base_order(
                "order_microstructure_ka10046_runtime_effect_violation",
                "ka10046 REST strength runtime-effect violation",
                route="instrumentation_order",
                improvement_type="source_quality_forbidden_use_violation",
                evidence=[
                    f"ka10046_strength_runtime_effect_true_count={summary.get('ka10046_strength_runtime_effect_true_count')}",
                    "ka10046 REST strength fallback must not create runtime support by itself",
                ],
            )
        )

    if _safe_int(summary.get("ka10046_strength_missing_received_ts_count"), 0) > 0:
        orders.append(
            base_order(
                "order_microstructure_ka10046_received_timestamp_gap",
                "ka10046 REST strength received timestamp gap",
                route="instrumentation_order",
                improvement_type="source_quality_timestamp_provenance_gap",
                evidence=[
                    f"ka10046_strength_missing_received_ts_count={summary.get('ka10046_strength_missing_received_ts_count')}",
                    "REST aggregate row time cannot substitute for client receive timestamp",
                ],
            )
        )

    if _safe_int(summary.get("row_count"), 0) > 0 and _safe_int(summary.get("rest_signed_trade_ticks_row_count"), 0) > 0:
        orders.append(
            base_order(
                "order_microstructure_signed_tape_runtime_candidate_review",
                "signed tape runtime candidate review from source-quality observation",
                route="auto_family_candidate",
                improvement_type="runtime_candidate_design_review",
                evidence=[
                    f"rest_signed_trade_ticks_row_count={summary.get('rest_signed_trade_ticks_row_count')}",
                    f"market_data_signed_tape_state_counts={summary.get('market_data_signed_tape_state_counts') or {}}",
                    "candidate review only; no runtime apply until separate PREOPEN guard and family contract",
                ],
            )
        )

    if _safe_int(summary.get("ka10003_buy_dominance_observation_split_vs_15_evaluable_count"), 0) > 0:
        orders.append(
            base_order(
                "order_microstructure_ka10003_split_vs_15_observation_review",
                "ka10003 split-vs-15 observation review",
                route="instrumentation_order",
                improvement_type="source_quality_observation_review",
                evidence=[
                    "ka10003_buy_dominance_observation_split_vs_15_evaluable_count="
                    f"{summary.get('ka10003_buy_dominance_observation_split_vs_15_evaluable_count')}",
                    "ka10003_buy_dominance_observation_split_vs_15_mismatch_rate_pct="
                    f"{summary.get('ka10003_buy_dominance_observation_split_vs_15_mismatch_rate_pct')}",
                    "ka10003 remains observation-only and must not fill trusted pressure fields",
                ],
            )
        )

    return orders


def _latest_rows_by_stock(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        stock_code = str(row.get("stock_code") or "").strip()
        if not stock_code:
            continue
        latest[stock_code] = row
    return list(latest.values())


def build_microstructure_reaction_context_report(target_date: str) -> dict[str, Any]:
    target_date = str(target_date).strip()
    path = _event_path(target_date)
    rows = [row for event in (_iter_jsonl(path) or []) if (row := _row_from_event(event))]
    status_counts = Counter(str(row.get("microstructure_reaction_context_status") or "missing") for row in rows)
    quality_counts = Counter(str(row.get("microstructure_reaction_entry_reaction_quality") or "-") for row in rows)
    source_quality_counts = Counter(str(row.get("microstructure_reaction_source_quality") or "-") for row in rows)
    stage_counts = Counter(str(row.get("stage") or "-") for row in rows)
    real_rows = [row for row in rows if row.get("actual_order_submitted") is True]
    latest_stock_rows = _latest_rows_by_stock(rows)
    v_pw_source_counts = _field_counter(rows, "v_pw_source")
    ka10046_fallback_rows = [row for row in rows if str(row.get("v_pw_source") or "") == "ka10046_rest_fallback"]
    ka10046_fallback_quote_freshness_counts = dict(
        sorted(Counter(_quote_freshness_state(row) for row in ka10046_fallback_rows).items())
    )
    strength_diffs = _strength_diff_rows(rows)
    strength_divergence20_count = sum(1 for value in strength_diffs if value >= 20.0)
    window_trade_value_1313_count = _sum_int(rows, "tick_trade_value_1313_count")
    window_trade_value_1313_missing_count = _sum_int(rows, "tick_trade_value_1313_missing_count")
    window_trade_volume_mismatch_evaluable_count = _sum_int(
        rows,
        "trade_volume_1030_1031_vs_15_evaluable_count",
    )
    window_trade_volume_mismatch_count = _sum_int(
        rows,
        "trade_volume_1030_1031_vs_15_mismatch_count",
    )
    cumulative_0b_count = _sum_int(latest_stock_rows, "kiwoom_0b_aux_observed_count")
    cumulative_1313_missing_count = _sum_int(latest_stock_rows, "kiwoom_0b_1313_missing_count")
    cumulative_mismatch_evaluable_count = _sum_int(
        latest_stock_rows,
        "kiwoom_0b_1030_1031_vs_15_evaluable_count",
    )
    cumulative_mismatch_count = _sum_int(
        latest_stock_rows,
        "kiwoom_0b_1030_1031_vs_15_mismatch_count",
    )
    ka10003_split_vs_15_evaluable_count = _sum_int(
        rows,
        "ka10003_buy_dominance_observation_split_vs_15_evaluable_count",
    )
    ka10003_split_vs_15_mismatch_count = _sum_int(
        rows,
        "ka10003_buy_dominance_observation_split_vs_15_mismatch_count",
    )
    summary = {
        "available": bool(rows),
        "row_count": len(rows),
        "ok_count": status_counts.get("ok", 0),
        "missing_or_unusable_count": len(rows) - status_counts.get("ok", 0),
        "status_counts": dict(sorted(status_counts.items())),
        "entry_reaction_quality_counts": dict(sorted(quality_counts.items())),
        "source_quality_counts": dict(sorted(source_quality_counts.items())),
        "stage_counts": dict(sorted(stage_counts.items())),
        "real_submitted_count": len(real_rows),
        "v_pw_source_counts": v_pw_source_counts,
        "v_pw_rest_fallback_count": v_pw_source_counts.get("ka10046_rest_fallback", 0),
        "v_pw_ws_0b_count": v_pw_source_counts.get("ws_0b", 0),
        "v_pw_missing_count": v_pw_source_counts.get("missing", 0),
        "v_pw_rest_fallback_rate_pct": _rate_pct(
            v_pw_source_counts.get("ka10046_rest_fallback", 0),
            len(rows),
        ),
        "v_pw_runtime_support_unusable_count": sum(
            1
            for row in rows
            if "v_pw_runtime_support_usable" in row
            and not _safe_bool(row.get("v_pw_runtime_support_usable"), False)
        ),
        "ka10046_rest_fallback_quote_freshness_counts": ka10046_fallback_quote_freshness_counts,
        "ka10046_rest_fallback_with_fresh_quote_count": ka10046_fallback_quote_freshness_counts.get("fresh", 0),
        "ka10046_rest_fallback_with_stale_quote_count": ka10046_fallback_quote_freshness_counts.get("stale", 0),
        "ka10046_strength_runtime_effect_true_count": sum(
            1 for row in rows if _safe_bool(row.get("ka10046_strength_runtime_effect"), False)
        ),
        "ka10046_strength_missing_received_ts_count": sum(
            1
            for row in rows
            if str(row.get("ka10046_strength_source") or "") == "ka10046_rest_strength_trend"
            and _safe_int(row.get("ka10046_strength_rest_received_ts_ms"), 0) <= 0
        ),
        "ka10046_0b_strength_compare_evaluable_count": len(strength_diffs),
        "ka10046_0b_strength_abs_diff_avg": round(sum(strength_diffs) / len(strength_diffs), 3)
        if strength_diffs
        else 0.0,
        "ka10046_0b_strength_abs_diff_max": round(max(strength_diffs), 3) if strength_diffs else 0.0,
        "ka10046_0b_strength_divergence20_count": strength_divergence20_count,
        "ka10046_0b_strength_divergence20_rate_pct": _rate_pct(
            strength_divergence20_count,
            len(strength_diffs),
        ),
        "market_data_signed_tape_state_counts": _field_counter(rows, "market_data_signed_tape_state"),
        "market_data_signed_tape_sample_count_total": _sum_int(rows, "market_data_signed_tape_sample_count"),
        "market_data_signed_tape_buy_count_total": _sum_int(rows, "market_data_signed_tape_buy_count"),
        "market_data_signed_tape_sell_count_total": _sum_int(rows, "market_data_signed_tape_sell_count"),
        "market_data_signed_tape_buy_volume_total": _sum_int(rows, "market_data_signed_tape_buy_volume"),
        "market_data_signed_tape_sell_volume_total": _sum_int(rows, "market_data_signed_tape_sell_volume"),
        "market_data_rest_signed_tape_pressure_usable_true_count": sum(
            1 for row in rows if _safe_bool(row.get("market_data_rest_signed_tape_pressure_usable"), False)
        ),
        "rest_signed_trade_ticks_row_count": _rest_signed_trade_tick_count(rows),
        "rest_signed_trade_ticks_source_counts": _rest_signed_trade_tick_source_counts(rows),
        "latency_true_ofi_direct_canary_signed_tape_sample_count_total": _sum_int(
            rows,
            "latency_true_ofi_direct_canary_signed_tape_sample_count",
        ),
        "latency_true_ofi_direct_canary_signed_tape_buy_count_total": _sum_int(
            rows,
            "latency_true_ofi_direct_canary_signed_tape_buy_count",
        ),
        "latency_true_ofi_direct_canary_signed_tape_sell_count_total": _sum_int(
            rows,
            "latency_true_ofi_direct_canary_signed_tape_sell_count",
        ),
        "latency_true_ofi_direct_canary_signed_tape_net_buy_volume_sum": _sum_int(
            rows,
            "latency_true_ofi_direct_canary_signed_tape_net_buy_volume",
        ),
        "latency_true_ofi_direct_canary_signed_tape_latest_side_counts": _field_counter(
            rows,
            "latency_true_ofi_direct_canary_signed_tape_latest_side",
        ),
        "latency_true_ofi_direct_canary_signed_tape_sell_dominated_count": sum(
            1
            for row in rows
            if _safe_bool(row.get("latency_true_ofi_direct_canary_signed_tape_sell_dominated"), False)
        ),
        "latency_true_ofi_direct_canary_signed_tape_latest_single_sell_dominated_count": sum(
            1
            for row in rows
            if _safe_bool(
                row.get("latency_true_ofi_direct_canary_signed_tape_latest_single_sell_dominated"),
                False,
            )
        ),
        "latency_true_ofi_direct_canary_tape_block_reason_counts": _field_counter(
            rows,
            "latency_true_ofi_direct_canary_tape_block_reason",
        ),
        "tick_aggressor_source_counts": _sum_counter_rows(rows, "tick_aggressor_source_counts"),
        "tick_trade_value_source_counts": _sum_counter_rows(rows, "tick_trade_value_source_counts"),
        "tick_trade_value_1313_count": window_trade_value_1313_count,
        "tick_trade_value_1313_missing_count": window_trade_value_1313_missing_count,
        "tick_trade_value_1313_missing_rate_pct": _rate_pct(
            window_trade_value_1313_missing_count,
            window_trade_value_1313_count + window_trade_value_1313_missing_count,
        ),
        "trade_volume_source_counts": _sum_counter_rows(rows, "trade_volume_source_counts"),
        "trade_volume_1030_1031_vs_15_evaluable_count": window_trade_volume_mismatch_evaluable_count,
        "trade_volume_1030_1031_vs_15_mismatch_count": window_trade_volume_mismatch_count,
        "trade_volume_1030_1031_vs_15_mismatch_rate_pct": _rate_pct(
            window_trade_volume_mismatch_count,
            window_trade_volume_mismatch_evaluable_count,
        ),
        "kiwoom_0b_latest_stock_count": len(latest_stock_rows),
        "kiwoom_0b_aux_observed_count": cumulative_0b_count,
        "kiwoom_0b_1313_present_count": _sum_int(latest_stock_rows, "kiwoom_0b_1313_present_count"),
        "kiwoom_0b_1313_missing_count": cumulative_1313_missing_count,
        "kiwoom_0b_1313_missing_rate_pct": _rate_pct(cumulative_1313_missing_count, cumulative_0b_count),
        "kiwoom_0b_trade_value_source_counts": _sum_counter_rows(
            latest_stock_rows,
            "kiwoom_0b_trade_value_source_counts",
        ),
        "kiwoom_0b_trade_volume_source_counts": _sum_counter_rows(
            latest_stock_rows,
            "kiwoom_0b_trade_volume_source_counts",
        ),
        "kiwoom_0b_1030_1031_vs_15_evaluable_count": cumulative_mismatch_evaluable_count,
        "kiwoom_0b_1030_1031_vs_15_mismatch_count": cumulative_mismatch_count,
        "kiwoom_0b_1030_1031_vs_15_mismatch_rate_pct": _rate_pct(
            cumulative_mismatch_count,
            cumulative_mismatch_evaluable_count,
        ),
        "ka10003_buy_dominance_observation_source_counts": _sum_counter_rows(
            rows,
            "ka10003_buy_dominance_observation_source_counts",
        ),
        "ka10003_buy_dominance_observation_trade_value_source_counts": _sum_counter_rows(
            rows,
            "ka10003_buy_dominance_observation_trade_value_source_counts",
        ),
        "ka10003_buy_dominance_observation_inside_spread_count": _sum_int(
            rows,
            "ka10003_buy_dominance_observation_inside_spread_count",
        ),
        "ka10003_buy_dominance_observation_split_vs_15_evaluable_count": ka10003_split_vs_15_evaluable_count,
        "ka10003_buy_dominance_observation_split_vs_15_mismatch_count": ka10003_split_vs_15_mismatch_count,
        "ka10003_buy_dominance_observation_split_vs_15_mismatch_rate_pct": _rate_pct(
            ka10003_split_vs_15_mismatch_count,
            ka10003_split_vs_15_evaluable_count,
        ),
        "avg_ask_sweep_score": _avg_score(rows, "microstructure_reaction_ask_sweep_score"),
        "avg_post_sweep_hold_score": _avg_score(rows, "microstructure_reaction_post_sweep_hold_score"),
        "avg_bid_replenishment_score": _avg_score(rows, "microstructure_reaction_bid_replenishment_score"),
        "max_vi_proximity_risk": max(
            [_safe_int(row.get("microstructure_reaction_vi_proximity_risk"), 0) for row in rows] or [0]
        ),
    }
    json_path, md_path = report_paths(target_date)
    code_improvement_orders = _microstructure_code_improvement_orders(summary, json_path)
    summary["code_improvement_order_count"] = len(code_improvement_orders)
    summary["top_code_improvement_orders"] = [
        {
            "order_id": order.get("order_id"),
            "title": order.get("title"),
            "route": order.get("route"),
            "improvement_type": order.get("improvement_type"),
        }
        for order in code_improvement_orders[:5]
    ]
    report = {
        "schema_version": 1,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": "microstructure_reaction_context",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": "entry_confidence_modifier_source_only",
        "metric_role": "feature_context",
        "window_policy": "same_day_short_window_runtime_events_plus_postclose_source_summary",
        "sample_floor": "none_for_v1_source_only",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "context_status ok and connection keys present",
        "forbidden_uses": FORBIDDEN_USES,
        "sources": {"pipeline_events": str(path) if path.exists() else None},
        "summary": summary,
        "rows": rows[:500],
        "code_improvement_orders": code_improvement_orders,
        "warnings": [
            message
            for message in [
                "pipeline_events_missing" if not path.exists() else "",
                "microstructure_reaction_context_missing" if not rows else "",
            ]
            if message
        ],
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_microstructure_reaction_context_markdown(report), encoding="utf-8")
    return report


def _avg_score(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [_safe_float(row.get(key), -1.0) for row in rows]
    values = [value for value in values if value >= 0]
    return round(sum(values) / len(values), 3) if values else None


def render_microstructure_reaction_context_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# Microstructure Reaction Context - {report.get('date')}",
        "",
        "- runtime_effect: `False`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- forbidden_uses: `{report.get('forbidden_uses') or []}`",
        "",
        "## Summary",
        f"- available: `{summary.get('available')}`",
        f"- row_count: `{summary.get('row_count')}`",
        f"- ok/missing_or_unusable: `{summary.get('ok_count')}` / `{summary.get('missing_or_unusable_count')}`",
        f"- real_submitted_count: `{summary.get('real_submitted_count')}`",
        f"- status_counts: `{summary.get('status_counts') or {}}`",
        f"- entry_reaction_quality_counts: `{summary.get('entry_reaction_quality_counts') or {}}`",
        f"- source_quality_counts: `{summary.get('source_quality_counts') or {}}`",
        f"- stage_counts: `{summary.get('stage_counts') or {}}`",
        f"- v_pw_source_counts: `{summary.get('v_pw_source_counts') or {}}`",
        f"- v_pw_rest_fallback_rate_pct: `{summary.get('v_pw_rest_fallback_rate_pct')}`",
        f"- v_pw_runtime_support_unusable_count: `{summary.get('v_pw_runtime_support_unusable_count')}`",
        f"- ka10046_rest_fallback_quote_freshness_counts: `{summary.get('ka10046_rest_fallback_quote_freshness_counts') or {}}`",
        f"- ka10046_strength_runtime_effect_true_count: `{summary.get('ka10046_strength_runtime_effect_true_count')}`",
        f"- ka10046_strength_missing_received_ts_count: `{summary.get('ka10046_strength_missing_received_ts_count')}`",
        "- ka10046_0b_strength_diff: "
        f"avg=`{summary.get('ka10046_0b_strength_abs_diff_avg')}` "
        f"max=`{summary.get('ka10046_0b_strength_abs_diff_max')}` "
        f"divergence20=`{summary.get('ka10046_0b_strength_divergence20_count')}` / "
        f"`{summary.get('ka10046_0b_strength_compare_evaluable_count')}` "
        f"(`{summary.get('ka10046_0b_strength_divergence20_rate_pct')}`%)",
        f"- market_data_signed_tape_state_counts: `{summary.get('market_data_signed_tape_state_counts') or {}}`",
        f"- market_data_signed_tape_sample_count_total: `{summary.get('market_data_signed_tape_sample_count_total')}`",
        f"- market_data_rest_signed_tape_pressure_usable_true_count: `{summary.get('market_data_rest_signed_tape_pressure_usable_true_count')}`",
        f"- rest_signed_trade_ticks_row_count: `{summary.get('rest_signed_trade_ticks_row_count')}`",
        f"- rest_signed_trade_ticks_source_counts: `{summary.get('rest_signed_trade_ticks_source_counts') or {}}`",
        "- latency_true_ofi_direct_canary_signed_tape: "
        f"sample_total=`{summary.get('latency_true_ofi_direct_canary_signed_tape_sample_count_total')}` "
        f"net_buy_volume_sum=`{summary.get('latency_true_ofi_direct_canary_signed_tape_net_buy_volume_sum')}` "
        f"sell_dominated=`{summary.get('latency_true_ofi_direct_canary_signed_tape_sell_dominated_count')}` "
        f"latest_single_sell_dominated=`{summary.get('latency_true_ofi_direct_canary_signed_tape_latest_single_sell_dominated_count')}`",
        f"- latency_true_ofi_direct_canary_signed_tape_latest_side_counts: `{summary.get('latency_true_ofi_direct_canary_signed_tape_latest_side_counts') or {}}`",
        f"- latency_true_ofi_direct_canary_tape_block_reason_counts: `{summary.get('latency_true_ofi_direct_canary_tape_block_reason_counts') or {}}`",
        f"- tick_aggressor_source_counts: `{summary.get('tick_aggressor_source_counts') or {}}`",
        f"- tick_trade_value_source_counts: `{summary.get('tick_trade_value_source_counts') or {}}`",
        f"- tick_trade_value_1313_missing_rate_pct: `{summary.get('tick_trade_value_1313_missing_rate_pct')}`",
        f"- trade_volume_source_counts: `{summary.get('trade_volume_source_counts') or {}}`",
        "- trade_volume_1030_1031_vs_15_mismatch: "
        f"`{summary.get('trade_volume_1030_1031_vs_15_mismatch_count')}` / "
        f"`{summary.get('trade_volume_1030_1031_vs_15_evaluable_count')}` "
        f"(`{summary.get('trade_volume_1030_1031_vs_15_mismatch_rate_pct')}`%)",
        f"- kiwoom_0b_latest_stock_count: `{summary.get('kiwoom_0b_latest_stock_count')}`",
        f"- kiwoom_0b_trade_value_source_counts: `{summary.get('kiwoom_0b_trade_value_source_counts') or {}}`",
        f"- kiwoom_0b_1313_missing_rate_pct: `{summary.get('kiwoom_0b_1313_missing_rate_pct')}`",
        f"- kiwoom_0b_trade_volume_source_counts: `{summary.get('kiwoom_0b_trade_volume_source_counts') or {}}`",
        "- kiwoom_0b_1030_1031_vs_15_mismatch: "
        f"`{summary.get('kiwoom_0b_1030_1031_vs_15_mismatch_count')}` / "
        f"`{summary.get('kiwoom_0b_1030_1031_vs_15_evaluable_count')}` "
        f"(`{summary.get('kiwoom_0b_1030_1031_vs_15_mismatch_rate_pct')}`%)",
        f"- ka10003_buy_dominance_observation_source_counts: `{summary.get('ka10003_buy_dominance_observation_source_counts') or {}}`",
        f"- ka10003_buy_dominance_observation_trade_value_source_counts: `{summary.get('ka10003_buy_dominance_observation_trade_value_source_counts') or {}}`",
        f"- ka10003_buy_dominance_observation_inside_spread_count: `{summary.get('ka10003_buy_dominance_observation_inside_spread_count')}`",
        "- ka10003_buy_dominance_observation_split_vs_15_mismatch: "
        f"`{summary.get('ka10003_buy_dominance_observation_split_vs_15_mismatch_count')}` / "
        f"`{summary.get('ka10003_buy_dominance_observation_split_vs_15_evaluable_count')}` "
        f"(`{summary.get('ka10003_buy_dominance_observation_split_vs_15_mismatch_rate_pct')}`%)",
        f"- avg_ask_sweep_score: `{summary.get('avg_ask_sweep_score')}`",
        f"- avg_post_sweep_hold_score: `{summary.get('avg_post_sweep_hold_score')}`",
        f"- avg_bid_replenishment_score: `{summary.get('avg_bid_replenishment_score')}`",
        f"- max_vi_proximity_risk: `{summary.get('max_vi_proximity_risk')}`",
        f"- warnings: `{report.get('warnings') or []}`",
        f"- code_improvement_order_count: `{summary.get('code_improvement_order_count')}`",
        f"- top_code_improvement_orders: `{summary.get('top_code_improvement_orders') or []}`",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build source-only microstructure reaction context artifact.")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    args = parser.parse_args(argv)
    report = build_microstructure_reaction_context_report(args.date)
    print(json.dumps({"date": report.get("date"), "summary": report.get("summary"), "warnings": report.get("warnings")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
