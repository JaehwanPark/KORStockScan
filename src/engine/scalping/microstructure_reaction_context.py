from __future__ import annotations

import argparse
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
    "microstructure_reaction_ask_sweep_score",
    "microstructure_reaction_post_sweep_hold_score",
    "microstructure_reaction_bid_replenishment_score",
    "microstructure_reaction_wall_replenishment_risk_score",
    "microstructure_reaction_vi_proximity_risk",
    "microstructure_reaction_entry_reaction_quality",
    "microstructure_reaction_source_quality",
    "microstructure_reaction_context_hash",
)

FORBIDDEN_USES = [
    "standalone_buy",
    "broker_guard_bypass",
    "threshold_mutation",
    "provider_route_change",
    "bot_restart",
    "cap_release",
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


def infer_tick_aggressor_side(tick: dict[str, Any] | None) -> dict[str, Any]:
    tick = tick if isinstance(tick, dict) else {}
    explicit = _normalize_tick_side(
        tick.get("aggressor_side")
        or tick.get("trade_aggressor_side")
        or tick.get("dir")
        or tick.get("side")
    )
    trade_price = _tick_price(tick)
    best_ask = _tick_best_ask(tick)
    best_bid = _tick_best_bid(tick)
    if trade_price > 0 and (best_ask > 0 or best_bid > 0):
        if best_ask > 0 and trade_price >= best_ask:
            return {
                "side": "BUY",
                "source": "orderbook_touch",
                "quality": "touch_or_crossed_ask",
                "trade_price": trade_price,
                "best_ask": best_ask,
                "best_bid": best_bid,
            }
        if best_bid > 0 and trade_price <= best_bid:
            return {
                "side": "SELL",
                "source": "orderbook_touch",
                "quality": "touch_or_crossed_bid",
                "trade_price": trade_price,
                "best_ask": best_ask,
                "best_bid": best_bid,
            }
        return {
            "side": "UNKNOWN",
            "source": "orderbook_touch",
            "quality": "inside_spread_or_uncertain",
            "trade_price": trade_price,
            "best_ask": best_ask,
            "best_bid": best_bid,
        }
    if explicit in {"BUY", "SELL"}:
        return {
            "side": explicit,
            "source": str(tick.get("aggressor_source") or tick.get("dir_source") or "declared_tick_side"),
            "quality": str(tick.get("aggressor_quality") or "side_without_orderbook_touch"),
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
    return str(inferred.get("source") or "").strip() != "price_change_heuristic"


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
        "tick_aggressor_unknown_count": sum(1 for row in aggressor_rows if row.get("side") not in {"BUY", "SELL"}),
        "tick_aggressor_orderbook_touch_count": sum(1 for row in aggressor_rows if row.get("source") == "orderbook_touch"),
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
    return any(key in fields for key in CONTEXT_KEYS)


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
    return row


def build_microstructure_reaction_context_report(target_date: str) -> dict[str, Any]:
    target_date = str(target_date).strip()
    path = _event_path(target_date)
    rows = [row for event in (_iter_jsonl(path) or []) if (row := _row_from_event(event))]
    status_counts = Counter(str(row.get("microstructure_reaction_context_status") or "missing") for row in rows)
    quality_counts = Counter(str(row.get("microstructure_reaction_entry_reaction_quality") or "-") for row in rows)
    source_quality_counts = Counter(str(row.get("microstructure_reaction_source_quality") or "-") for row in rows)
    stage_counts = Counter(str(row.get("stage") or "-") for row in rows)
    real_rows = [row for row in rows if row.get("actual_order_submitted") is True]
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
        "avg_ask_sweep_score": _avg_score(rows, "microstructure_reaction_ask_sweep_score"),
        "avg_post_sweep_hold_score": _avg_score(rows, "microstructure_reaction_post_sweep_hold_score"),
        "avg_bid_replenishment_score": _avg_score(rows, "microstructure_reaction_bid_replenishment_score"),
        "max_vi_proximity_risk": max(
            [_safe_int(row.get("microstructure_reaction_vi_proximity_risk"), 0) for row in rows] or [0]
        ),
    }
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
    json_path, md_path = report_paths(target_date)
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
        f"- avg_ask_sweep_score: `{summary.get('avg_ask_sweep_score')}`",
        f"- avg_post_sweep_hold_score: `{summary.get('avg_post_sweep_hold_score')}`",
        f"- avg_bid_replenishment_score: `{summary.get('avg_bid_replenishment_score')}`",
        f"- max_vi_proximity_risk: `{summary.get('max_vi_proximity_risk')}`",
        f"- warnings: `{report.get('warnings') or []}`",
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
