from __future__ import annotations

from datetime import datetime
from statistics import mean

from src.engine.scalping.microstructure_reaction_context import build_microstructure_reaction_context


SCALP_FEATURE_PACKET_VERSION = "scalp_feature_packet_v1"


def _safe_number(value, default=0.0):
    try:
        if value in (None, "", "-"):
            return default
        return float(value)
    except Exception:
        return default


def _safe_hhmmss_to_seconds(value):
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


def _age_ms_from_hhmmss(value, *, now=None):
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


def _safe_epoch_ms(value):
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
    except Exception:
        pass
    try:
        text = str(value).strip()
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        return int(datetime.fromisoformat(text).timestamp() * 1000)
    except Exception:
        return None


def _quote_age_ms(ws_data, *, now=None):
    quote_ts_keys = (
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
        raw = (ws_data or {}).get(key)
        epoch_ms = _safe_epoch_ms(raw)
        if epoch_ms is None:
            continue
        return max(0, now_ms - epoch_ms), key
    return None, "missing"


def calculate_scalping_micro_indicator_values(recent_candles):
    candles = recent_candles if isinstance(recent_candles, list) else []
    if len(candles) < 5:
        last_close = _safe_number(candles[-1].get("현재가") if candles and isinstance(candles[-1], dict) else 0, 0.0)
        return {"MA5": int(last_close), "Micro_VWAP": int(last_close)}

    window = [candle for candle in candles[-5:] if isinstance(candle, dict)]
    closes = [_safe_number(candle.get("현재가"), 0.0) for candle in window]
    ma5_value = int(sum(closes) / len(closes)) if closes else 0
    price_vol_sum = 0.0
    volume_sum = 0.0
    for candle in window:
        high = _safe_number(candle.get("고가"), 0.0)
        low = _safe_number(candle.get("저가"), 0.0)
        close = _safe_number(candle.get("현재가"), 0.0)
        volume = _safe_number(candle.get("거래량"), 0.0)
        typical_price = (high + low + close) / 3.0
        price_vol_sum += typical_price * volume
        volume_sum += volume
    micro_vwap_value = int(price_vol_sum / volume_sum) if volume_sum > 0 else int(closes[-1] if closes else 0)
    return {"MA5": ma5_value, "Micro_VWAP": micro_vwap_value}


def extract_scalping_feature_packet(ws_data, recent_ticks, recent_candles=None, *, now=None):
    if recent_candles is None:
        recent_candles = []

    ws_data = ws_data or {}
    curr_price = ws_data.get("curr", 0) or 0
    v_pw = ws_data.get("v_pw", 0) or 0
    ask_tot = ws_data.get("ask_tot", 0) or 0
    bid_tot = ws_data.get("bid_tot", 0) or 0
    net_ask_depth = int(ws_data.get("net_ask_depth", 0) or 0)
    ask_depth_ratio = float(ws_data.get("ask_depth_ratio", 0.0) or 0.0)
    orderbook = ws_data.get("orderbook", {"asks": [], "bids": []}) or {"asks": [], "bids": []}
    asks = orderbook.get("asks", []) or []
    bids = orderbook.get("bids", []) or []

    best_ask = asks[0].get("price", curr_price) if asks else curr_price
    best_bid = bids[0].get("price", curr_price) if bids else curr_price
    best_ask_vol = asks[0].get("volume", 0) if asks else 0
    best_bid_vol = bids[0].get("volume", 0) if bids else 0

    spread_krw = max(0, best_ask - best_bid)
    spread_bp = round((spread_krw / curr_price) * 10000, 2) if curr_price > 0 else 0.0

    top3_ask_vol = sum(level.get("volume", 0) for level in asks[:3])
    top3_bid_vol = sum(level.get("volume", 0) for level in bids[:3])

    top1_depth_ratio = round((best_ask_vol / best_bid_vol), 3) if best_bid_vol > 0 else 999.0
    top3_depth_ratio = round((top3_ask_vol / top3_bid_vol), 3) if top3_bid_vol > 0 else 999.0

    micro_price = curr_price
    denom = best_ask_vol + best_bid_vol
    if denom > 0:
        micro_price = ((best_bid * best_ask_vol) + (best_ask * best_bid_vol)) / denom

    microprice_edge_bp = round(((micro_price - curr_price) / curr_price) * 10000, 2) if curr_price > 0 else 0.0

    high_price = curr_price
    low_price = curr_price
    if recent_candles:
        high_price = max(candle.get("고가", curr_price) for candle in recent_candles)
        low_price = min(candle.get("저가", curr_price) for candle in recent_candles)

    distance_from_day_high_pct = round(((curr_price - high_price) / high_price) * 100, 3) if high_price > 0 else 0.0
    intraday_range_pct = round(((high_price - low_price) / low_price) * 100, 3) if low_price > 0 else 0.0

    buy_vol_10 = 0
    sell_vol_10 = 0
    latest_strength = v_pw
    price_change_10t_pct = 0.0
    net_aggressive_delta_10t = 0
    recent_5tick_seconds = 999.0
    prev_5tick_seconds = 999.0
    tick_acceleration_ratio = 0.0
    tick_acceleration_ratio_raw = 0.0
    tick_accel_effective_recent_5tick_seconds = 999.0
    same_price_buy_absorption = 0
    large_sell_print_detected = False
    large_buy_print_detected = False

    ticks = recent_ticks[:10] if recent_ticks else []
    tick_sample_count = len(ticks)
    tick_latest_time = str(ticks[0].get("time", "") or "") if ticks else ""
    tick_latest_age_ms = _age_ms_from_hhmmss(tick_latest_time, now=now) if tick_latest_time else None
    tick_window_span_sec = None
    tick_accel_source = "no_ticks"

    if ticks:
        buy_vol_10 = sum(tick.get("volume", 0) for tick in ticks if tick.get("dir") == "BUY")
        sell_vol_10 = sum(tick.get("volume", 0) for tick in ticks if tick.get("dir") == "SELL")
        total_vol_10 = buy_vol_10 + sell_vol_10
        buy_pressure_10t = round((buy_vol_10 / total_vol_10) * 100, 2) if total_vol_10 > 0 else 50.0
        net_aggressive_delta_10t = buy_vol_10 - sell_vol_10

        latest_strength = ticks[0].get("strength", v_pw)

        latest_price = ticks[0].get("price", curr_price)
        oldest_price = ticks[-1].get("price", curr_price)
        price_change_10t_pct = round(((latest_price - oldest_price) / oldest_price) * 100, 3) if oldest_price > 0 else 0.0

        tick_secs = [_safe_hhmmss_to_seconds(tick.get("time")) for tick in ticks]
        if len(tick_secs) >= 2 and tick_secs[0] is not None and tick_secs[-1] is not None:
            tick_window_span_sec = tick_secs[0] - tick_secs[-1]
            if tick_window_span_sec < 0:
                tick_window_span_sec += 86400
        tick_accel_source = "insufficient_ticks"
        if len(tick_secs) >= 5 and tick_secs[0] is not None and tick_secs[4] is not None:
            recent_5tick_seconds = tick_secs[0] - tick_secs[4]
            if recent_5tick_seconds < 0:
                recent_5tick_seconds += 86400
        elif len(tick_secs) >= 5:
            tick_accel_source = "invalid_recent_tick_time"

        if len(tick_secs) >= 10 and tick_secs[5] is not None and tick_secs[9] is not None:
            prev_5tick_seconds = tick_secs[5] - tick_secs[9]
            if prev_5tick_seconds < 0:
                prev_5tick_seconds += 86400
        elif len(tick_secs) >= 10:
            tick_accel_source = "invalid_previous_tick_time"

        if recent_5tick_seconds > 0 and prev_5tick_seconds < 999:
            tick_acceleration_ratio_raw = round(prev_5tick_seconds / recent_5tick_seconds, 3)
            tick_acceleration_ratio = tick_acceleration_ratio_raw
            tick_accel_effective_recent_5tick_seconds = recent_5tick_seconds
            tick_accel_source = "computed_10ticks"
        elif recent_5tick_seconds <= 0 and prev_5tick_seconds < 999:
            tick_accel_effective_recent_5tick_seconds = 1.0
            tick_acceleration_ratio_raw = 0.0
            tick_acceleration_ratio = round(prev_5tick_seconds / tick_accel_effective_recent_5tick_seconds, 3)
            tick_accel_source = "same_second_burst_10ticks"
        elif recent_5tick_seconds <= 0:
            tick_accel_source = "same_second_burst_insufficient_previous_window"

        volumes = [tick.get("volume", 0) for tick in ticks if tick.get("volume", 0) > 0]
        avg_tick_vol = mean(volumes) if volumes else 0

        if avg_tick_vol > 0:
            large_sell_print_detected = any(
                tick.get("dir") == "SELL" and tick.get("volume", 0) >= avg_tick_vol * 2.2
                for tick in ticks[:5]
            )
            large_buy_print_detected = any(
                tick.get("dir") == "BUY" and tick.get("volume", 0) >= avg_tick_vol * 2.2
                for tick in ticks[:5]
            )

        price_buy_count = {}
        for tick in ticks[:6]:
            if tick.get("dir") == "BUY":
                price = tick.get("price")
                price_buy_count[price] = price_buy_count.get(price, 0) + 1
        same_price_buy_absorption = max(price_buy_count.values()) if price_buy_count else 0
    else:
        buy_pressure_10t = 50.0

    quote_age_ms, quote_age_source = _quote_age_ms(ws_data, now=now)
    tick_stale = tick_latest_age_ms is not None and tick_latest_age_ms > 5000
    quote_stale = quote_age_ms is not None and quote_age_ms > 1200
    tick_context_quality = "unknown"
    if not ticks:
        tick_context_quality = "missing_ticks"
    elif tick_latest_age_ms is None:
        tick_context_quality = "missing_tick_time"
    elif tick_stale:
        tick_context_quality = "stale_tick"
    elif tick_accel_source not in {"computed_10ticks", "same_second_burst_10ticks"}:
        tick_context_quality = f"accel_{tick_accel_source}"
    else:
        tick_context_quality = "fresh_computed"

    volume_ratio_pct = 0.0
    curr_vs_micro_vwap_bp = 0.0
    curr_vs_ma5_bp = 0.0
    micro_vwap_value = 0.0
    ma5_value = 0.0

    if recent_candles and len(recent_candles) >= 2:
        current_volume = recent_candles[-1].get("거래량", 0)
        prev_volumes = [candle.get("거래량", 0) for candle in recent_candles[:-1] if candle.get("거래량", 0) > 0]
        avg_prev_volume = mean(prev_volumes) if prev_volumes else 0
        if avg_prev_volume > 0:
            volume_ratio_pct = round((current_volume / avg_prev_volume) * 100, 2)

    if recent_candles and len(recent_candles) >= 5:
        try:
            indicators = calculate_scalping_micro_indicator_values(recent_candles)

            ma5_value = indicators.get("MA5", 0) or 0
            micro_vwap_value = indicators.get("Micro_VWAP", 0) or 0

            if micro_vwap_value > 0 and curr_price > 0:
                curr_vs_micro_vwap_bp = round(((curr_price - micro_vwap_value) / micro_vwap_value) * 10000, 2)
            if ma5_value > 0 and curr_price > 0:
                curr_vs_ma5_bp = round(((curr_price - ma5_value) / ma5_value) * 10000, 2)
        except Exception:
            pass

    orderbook_total_ratio = round((ask_tot / bid_tot), 3) if bid_tot > 0 else 999.0
    microstructure_reaction = build_microstructure_reaction_context(
        ws_data,
        recent_ticks,
        recent_candles,
        now=now,
    )

    return {
        "packet_version": SCALP_FEATURE_PACKET_VERSION,
        "curr_price": curr_price,
        "latest_strength": latest_strength,
        "spread_krw": spread_krw,
        "spread_bp": spread_bp,
        "top1_depth_ratio": top1_depth_ratio,
        "top3_depth_ratio": top3_depth_ratio,
        "orderbook_total_ratio": orderbook_total_ratio,
        "micro_price": round(micro_price, 2),
        "microprice_edge_bp": microprice_edge_bp,
        "buy_pressure_10t": buy_pressure_10t,
        "net_aggressive_delta_10t": int(net_aggressive_delta_10t),
        "price_change_10t_pct": price_change_10t_pct,
        "recent_5tick_seconds": round(recent_5tick_seconds, 3),
        "tick_accel_effective_recent_5tick_seconds": round(tick_accel_effective_recent_5tick_seconds, 3)
        if tick_accel_effective_recent_5tick_seconds < 999
        else 999.0,
        "prev_5tick_seconds": round(prev_5tick_seconds, 3) if prev_5tick_seconds < 999 else 999.0,
        "tick_acceleration_ratio": tick_acceleration_ratio,
        "tick_acceleration_ratio_raw": tick_acceleration_ratio_raw,
        "tick_accel_source": tick_accel_source,
        "tick_sample_count": tick_sample_count,
        "tick_window_sample_count": tick_sample_count,
        "tick_latest_time": tick_latest_time or "-",
        "tick_latest_age_ms": tick_latest_age_ms if tick_latest_age_ms is not None else "-",
        "tick_window_span_sec": tick_window_span_sec if tick_window_span_sec is not None else "-",
        "tick_context_stale": bool(tick_stale) if tick_latest_age_ms is not None else "unknown",
        "tick_context_quality": tick_context_quality,
        "quote_age_ms": quote_age_ms if quote_age_ms is not None else "-",
        "quote_age_source": quote_age_source,
        "quote_stale": bool(quote_stale) if quote_age_ms is not None else "unknown",
        "same_price_buy_absorption": same_price_buy_absorption,
        "large_sell_print_detected": large_sell_print_detected,
        "large_buy_print_detected": large_buy_print_detected,
        "distance_from_day_high_pct": distance_from_day_high_pct,
        "intraday_range_pct": intraday_range_pct,
        "volume_ratio_pct": volume_ratio_pct,
        "curr_vs_micro_vwap_bp": curr_vs_micro_vwap_bp,
        "curr_vs_ma5_bp": curr_vs_ma5_bp,
        "micro_vwap_value": round(micro_vwap_value, 2) if micro_vwap_value else 0.0,
        "ma5_value": round(ma5_value, 2) if ma5_value else 0.0,
        "ask_depth_ratio": ask_depth_ratio,
        "net_ask_depth": net_ask_depth,
        **microstructure_reaction,
    }


def build_scalping_feature_audit_fields(packet):
    payload = packet or {}
    return {
        "scalp_feature_packet_version": str(payload.get("packet_version", SCALP_FEATURE_PACKET_VERSION)),
        "tick_acceleration_ratio_sent": "tick_acceleration_ratio" in payload,
        "same_price_buy_absorption_sent": "same_price_buy_absorption" in payload,
        "large_sell_print_detected_sent": "large_sell_print_detected" in payload,
        "ask_depth_ratio_sent": "ask_depth_ratio" in payload,
        "microstructure_reaction_context_sent": "microstructure_reaction_context_version" in payload,
        "tick_source_quality_fields_sent": all(
            field in payload
            for field in (
                "tick_sample_count",
                "tick_latest_age_ms",
                "tick_accel_source",
                "tick_context_quality",
            )
        ),
        "tick_sample_count": payload.get("tick_sample_count", "-"),
        "tick_window_sample_count": payload.get("tick_window_sample_count", "-"),
        "tick_latest_time": payload.get("tick_latest_time", "-"),
        "tick_latest_age_ms": payload.get("tick_latest_age_ms", "-"),
        "tick_window_span_sec": payload.get("tick_window_span_sec", "-"),
        "tick_accel_effective_recent_5tick_seconds": payload.get("tick_accel_effective_recent_5tick_seconds", "-"),
        "tick_acceleration_ratio_raw": payload.get("tick_acceleration_ratio_raw", "-"),
        "tick_accel_source": payload.get("tick_accel_source", "-"),
        "tick_context_stale": payload.get("tick_context_stale", "unknown"),
        "tick_context_quality": payload.get("tick_context_quality", "unknown"),
        "quote_age_ms": payload.get("quote_age_ms", "-"),
        "quote_age_source": payload.get("quote_age_source", "missing"),
        "quote_stale": payload.get("quote_stale", "unknown"),
        "microstructure_reaction_context_version": payload.get("microstructure_reaction_context_version", "-"),
        "microstructure_reaction_context_status": payload.get("microstructure_reaction_context_status", "-"),
        "microstructure_reaction_ask_sweep_score": payload.get("microstructure_reaction_ask_sweep_score", 50),
        "microstructure_reaction_post_sweep_hold_score": payload.get("microstructure_reaction_post_sweep_hold_score", 50),
        "microstructure_reaction_bid_replenishment_score": payload.get("microstructure_reaction_bid_replenishment_score", 50),
        "microstructure_reaction_wall_replenishment_risk_score": payload.get("microstructure_reaction_wall_replenishment_risk_score", 50),
        "microstructure_reaction_vi_proximity_risk": payload.get("microstructure_reaction_vi_proximity_risk", 0),
        "microstructure_reaction_entry_reaction_quality": payload.get("microstructure_reaction_entry_reaction_quality", "-"),
        "microstructure_reaction_source_quality": payload.get("microstructure_reaction_source_quality", "-"),
        "microstructure_reaction_context_hash": payload.get("microstructure_reaction_context_hash", "-"),
    }
