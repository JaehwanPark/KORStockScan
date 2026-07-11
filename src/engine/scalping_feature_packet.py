from __future__ import annotations

import time
from datetime import datetime
from statistics import mean

from src.engine.scalping.microstructure_reaction_context import (
    build_microstructure_reaction_context,
    precompute_microstructure_reaction_inputs,
)


SCALP_FEATURE_PACKET_VERSION = "scalp_feature_packet_v1"
SCALP_FEATURE_PACKET_QUOTE_STALE_MS = 3000
SCALP_FEATURE_PACKET_MINUTE_CANDLE_STALE_MS = 180_000


def _safe_number(value, default=0.0):
    try:
        if value in (None, "", "-"):
            return default
        return float(value)
    except Exception:
        return default


def _rate_pct(numerator, denominator):
    denominator = int(_safe_number(denominator, 0))
    numerator = int(_safe_number(numerator, 0))
    return round((numerator / denominator) * 100.0, 3) if denominator > 0 else 0.0


def _time_to_seconds(value) -> int | None:
    text = str(value or "").strip()
    if not text:
        return None
    compact = text.replace(":", "").strip()
    if len(compact) >= 14 and compact[:14].isdigit():
        compact = compact[8:14]
    elif len(compact) > 6 and compact[-6:].isdigit():
        compact = compact[-6:]
    if len(compact) != 6 or not compact.isdigit():
        return None
    hour = int(compact[:2])
    minute = int(compact[2:4])
    second = int(compact[4:6])
    if hour > 23 or minute > 59 or second > 59:
        return None
    return hour * 3600 + minute * 60 + second


def _reference_seconds_of_day(ws_data, ticks, now=None) -> tuple[int, str]:
    if isinstance(now, datetime):
        return now.hour * 3600 + now.minute * 60 + now.second, "explicit_now"
    if isinstance(now, (int, float)) and now > 0:
        ref = datetime.fromtimestamp(float(now))
        return ref.hour * 3600 + ref.minute * 60 + ref.second, "explicit_epoch"
    try:
        ts = float((ws_data or {}).get("last_ws_update_ts") or 0)
        if ts > 0:
            ref = datetime.fromtimestamp(ts)
            return ref.hour * 3600 + ref.minute * 60 + ref.second, "ws_last_update_ts"
    except Exception:
        pass
    for tick in ticks or []:
        if not isinstance(tick, dict):
            continue
        sec = _time_to_seconds(tick.get("time") or tick.get("체결시간") or tick.get("20"))
        if sec is not None:
            return sec, "latest_tick_time"
    ref = datetime.fromtimestamp(time.time())
    return ref.hour * 3600 + ref.minute * 60 + ref.second, "system_clock"


def _minute_candle_time_quality(recent_candles, ws_data, ticks, *, now=None) -> dict:
    candles = recent_candles if isinstance(recent_candles, list) else []
    base = {
        "minute_candle_latest_time": "-",
        "minute_candle_latest_age_ms": "-",
        "minute_candle_context_quality": "missing_candles" if not candles else "missing_candle_time",
        "minute_candle_reference_source": "-",
        "minute_candle_source_time_basis": "-",
        "minute_candle_window_fresh": False,
    }
    if not candles:
        return base
    latest = candles[-1] if isinstance(candles[-1], dict) else {}
    raw_time = (
        latest.get("source_timestamp")
        or latest.get("source_timestamp_kst")
        or latest.get("cntr_tm")
        or latest.get("체결시간")
    )
    sec = _time_to_seconds(raw_time)
    base["minute_candle_latest_time"] = str(raw_time or "-")
    base["minute_candle_source_time_basis"] = str(
        latest.get("source_time_basis") or "ka10080_cntr_tm_bar_timestamp"
    )
    if sec is None:
        return base
    ref_sec, ref_source = _reference_seconds_of_day(ws_data, ticks, now=now)
    age_sec = ref_sec - sec
    if age_sec < 0:
        age_sec += 24 * 3600
    age_ms = max(0, int(age_sec * 1000))
    fresh = age_ms <= SCALP_FEATURE_PACKET_MINUTE_CANDLE_STALE_MS
    base.update(
        {
            "minute_candle_latest_age_ms": age_ms,
            "minute_candle_context_quality": "fresh_bar_window" if fresh else "stale_bar_window",
            "minute_candle_reference_source": ref_source,
            "minute_candle_window_fresh": fresh,
        }
    )
    return base


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
    recent_ticks = _select_recent_ticks_for_feature_packet(ws_data, recent_ticks, now=now)
    snapshot = precompute_microstructure_reaction_inputs(
        ws_data,
        recent_ticks,
        recent_candles,
        now=now,
    )
    if "ai_quote_stale_max_ms" in ws_data:
        snapshot["ai_quote_stale_max_ms"] = ws_data.get("ai_quote_stale_max_ms")
    curr_price = snapshot.get("curr_price", 0) or 0
    v_pw = ws_data.get("v_pw", 0) or 0
    ask_tot = ws_data.get("ask_tot", 0) or 0
    bid_tot = ws_data.get("bid_tot", 0) or 0
    net_ask_depth = int(ws_data.get("net_ask_depth", 0) or 0)
    ask_depth_ratio = float(ws_data.get("ask_depth_ratio", 0.0) or 0.0)
    asks = snapshot.get("asks") if isinstance(snapshot.get("asks"), list) else []
    bids = snapshot.get("bids") if isinstance(snapshot.get("bids"), list) else []

    best_ask = snapshot.get("best_ask", curr_price) if asks else curr_price
    best_bid = snapshot.get("best_bid", curr_price) if bids else curr_price
    best_ask_vol = snapshot.get("best_ask_vol", 0) if asks else 0
    best_bid_vol = snapshot.get("best_bid_vol", 0) if bids else 0

    spread_krw = max(0, best_ask - best_bid)
    spread_bp = round((spread_krw / curr_price) * 10000, 2) if curr_price > 0 else 0.0

    top3_ask_vol = snapshot.get("top3_ask_vol", 0)
    top3_bid_vol = snapshot.get("top3_bid_vol", 0)

    top1_depth_ratio = round((best_ask_vol / best_bid_vol), 3) if best_bid_vol > 0 else 999.0
    top3_depth_ratio = round((top3_ask_vol / top3_bid_vol), 3) if top3_bid_vol > 0 else 999.0

    micro_price = curr_price
    denom = best_ask_vol + best_bid_vol
    if denom > 0:
        micro_price = ((best_bid * best_ask_vol) + (best_ask * best_bid_vol)) / denom

    microprice_edge_bp = round(((micro_price - curr_price) / curr_price) * 10000, 2) if curr_price > 0 else 0.0

    high_price = snapshot.get("session_high", curr_price) if recent_candles else curr_price
    low_price = snapshot.get("session_low", curr_price) if recent_candles else curr_price

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

    ticks = snapshot.get("ticks") if isinstance(snapshot.get("ticks"), list) else []
    tick_sample_count = int(snapshot.get("tick_sample_count") or 0)
    tick_latest_time = str(snapshot.get("tick_latest_time") or "") if ticks else ""
    tick_latest_age_ms = snapshot.get("tick_age_ms")
    tick_aggressor_source_counts = snapshot.get("tick_aggressor_source_counts") or {}
    tick_aggressor_quality_counts = snapshot.get("tick_aggressor_quality_counts") or {}
    tick_trade_value_source_counts = snapshot.get("tick_trade_value_source_counts") or {}
    trade_volume_source_counts = snapshot.get("trade_volume_source_counts") or {}
    tick_aggressor_orderbook_touch_count = int(snapshot.get("tick_aggressor_orderbook_touch_count") or 0)
    tick_aggressor_cached_orderbook_touch_count = int(
        snapshot.get("tick_aggressor_cached_orderbook_touch_count") or 0
    )
    tick_aggressor_price_heuristic_count = int(snapshot.get("tick_aggressor_price_heuristic_count") or 0)
    tick_aggressor_unknown_count = int(snapshot.get("tick_aggressor_unknown_count") or 0)
    tick_aggressor_trusted_count = int(snapshot.get("tick_aggressor_trusted_count") or 0)
    tick_aggressor_pressure_usable = bool(snapshot.get("tick_aggressor_pressure_usable", False))
    kiwoom_0b_aux_observed_count = int(ws_data.get("kiwoom_0b_aux_observed_count") or 0)
    kiwoom_0b_1313_missing_count = int(ws_data.get("kiwoom_0b_1313_missing_count") or 0)
    kiwoom_0b_1030_1031_vs_15_evaluable_count = int(
        ws_data.get("kiwoom_0b_1030_1031_vs_15_evaluable_count") or 0
    )
    kiwoom_0b_1030_1031_vs_15_mismatch_count = int(
        ws_data.get("kiwoom_0b_1030_1031_vs_15_mismatch_count") or 0
    )
    tick_window_span_sec = None
    tick_accel_source = "no_ticks"

    if ticks:
        buy_vol_10 = snapshot.get("buy_vol", 0)
        sell_vol_10 = snapshot.get("sell_vol", 0)
        total_vol_10 = buy_vol_10 + sell_vol_10
        buy_pressure_10t = round(snapshot.get("buy_pressure_pct", 50.0), 2) if total_vol_10 > 0 else 50.0
        net_aggressive_delta_10t = buy_vol_10 - sell_vol_10

        latest_strength = ticks[0].get("strength", v_pw)

        latest_price = snapshot.get("latest_price", curr_price)
        oldest_price = snapshot.get("oldest_price", curr_price)
        price_change_10t_pct = round(((latest_price - oldest_price) / oldest_price) * 100, 3) if oldest_price > 0 else 0.0

        tick_secs = snapshot.get("tick_secs") if isinstance(snapshot.get("tick_secs"), list) else []
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

        large_sell_print_detected = bool(snapshot.get("large_sell_print_detected"))
        large_buy_print_detected = bool(snapshot.get("large_buy_print_detected"))
        same_price_buy_absorption = int(snapshot.get("same_price_buy_absorption") or 0)
    else:
        buy_pressure_10t = 50.0

    quote_age_ms = snapshot.get("quote_age_ms")
    quote_age_source = snapshot.get("quote_age_source", "missing")
    quote_stale_threshold_ms = max(
        1,
        int(
            _safe_number(snapshot.get("ai_quote_stale_max_ms"), SCALP_FEATURE_PACKET_QUOTE_STALE_MS)
            or SCALP_FEATURE_PACKET_QUOTE_STALE_MS
        ),
    )
    tick_stale = tick_latest_age_ms is not None and tick_latest_age_ms > 5000
    quote_stale = quote_age_ms is not None and quote_age_ms > quote_stale_threshold_ms
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
    micro_vwap_available = False
    ma5_available = False
    minute_candle_quality = _minute_candle_time_quality(recent_candles, ws_data, ticks, now=now)
    minute_candle_window_fresh = bool(minute_candle_quality.get("minute_candle_window_fresh"))

    if minute_candle_window_fresh and recent_candles and len(recent_candles) >= 2:
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

            if minute_candle_window_fresh and micro_vwap_value > 0 and curr_price > 0:
                curr_vs_micro_vwap_bp = round(((curr_price - micro_vwap_value) / micro_vwap_value) * 10000, 2)
                micro_vwap_available = True
            if minute_candle_window_fresh and ma5_value > 0 and curr_price > 0:
                curr_vs_ma5_bp = round(((curr_price - ma5_value) / ma5_value) * 10000, 2)
                ma5_available = True
        except Exception:
            pass

    orderbook_total_ratio = round((ask_tot / bid_tot), 3) if bid_tot > 0 else 999.0
    microstructure_reaction = build_microstructure_reaction_context(
        ws_data,
        recent_ticks,
        recent_candles,
        now=now,
        precomputed=snapshot,
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
        "tick_aggressor_source_counts": tick_aggressor_source_counts,
        "tick_aggressor_quality_counts": tick_aggressor_quality_counts,
        "tick_trade_value_source_counts": tick_trade_value_source_counts,
        "tick_trade_value_1313_count": int(snapshot.get("tick_trade_value_1313_count") or 0),
        "tick_trade_value_1313_missing_count": int(snapshot.get("tick_trade_value_1313_missing_count") or 0),
        "tick_trade_value_1313_missing_rate_pct": snapshot.get("tick_trade_value_1313_missing_rate_pct", 0.0),
        "trade_volume_source_counts": trade_volume_source_counts,
        "trade_volume_1030_1031_vs_15_evaluable_count": int(
            snapshot.get("trade_volume_1030_1031_vs_15_evaluable_count") or 0
        ),
        "trade_volume_1030_1031_vs_15_mismatch_count": int(
            snapshot.get("trade_volume_1030_1031_vs_15_mismatch_count") or 0
        ),
        "trade_volume_1030_1031_vs_15_mismatch_rate_pct": snapshot.get(
            "trade_volume_1030_1031_vs_15_mismatch_rate_pct",
            0.0,
        ),
        "kiwoom_0b_aux_observed_count": kiwoom_0b_aux_observed_count,
        "kiwoom_0b_1313_present_count": int(ws_data.get("kiwoom_0b_1313_present_count") or 0),
        "kiwoom_0b_1313_missing_count": kiwoom_0b_1313_missing_count,
        "kiwoom_0b_1313_missing_rate_pct": _rate_pct(
            kiwoom_0b_1313_missing_count,
            kiwoom_0b_aux_observed_count,
        ),
        "kiwoom_0b_trade_value_source_counts": ws_data.get("kiwoom_0b_trade_value_source_counts") or {},
        "kiwoom_0b_trade_volume_source_counts": ws_data.get("kiwoom_0b_trade_volume_source_counts") or {},
        "kiwoom_0b_1030_1031_vs_15_evaluable_count": kiwoom_0b_1030_1031_vs_15_evaluable_count,
        "kiwoom_0b_1030_1031_vs_15_mismatch_count": kiwoom_0b_1030_1031_vs_15_mismatch_count,
        "kiwoom_0b_1030_1031_vs_15_mismatch_rate_pct": _rate_pct(
            kiwoom_0b_1030_1031_vs_15_mismatch_count,
            kiwoom_0b_1030_1031_vs_15_evaluable_count,
        ),
        "tick_aggressor_orderbook_touch_count": tick_aggressor_orderbook_touch_count,
        "tick_aggressor_cached_orderbook_touch_count": tick_aggressor_cached_orderbook_touch_count,
        "tick_aggressor_price_heuristic_count": tick_aggressor_price_heuristic_count,
        "tick_aggressor_unknown_count": tick_aggressor_unknown_count,
        "tick_aggressor_trusted_count": tick_aggressor_trusted_count,
        "tick_aggressor_pressure_usable": tick_aggressor_pressure_usable,
        "tick_latest_time": tick_latest_time or "-",
        "tick_latest_age_ms": tick_latest_age_ms if tick_latest_age_ms is not None else "-",
        "tick_window_span_sec": tick_window_span_sec if tick_window_span_sec is not None else "-",
        "tick_context_stale": (
            bool(tick_stale) if tick_latest_age_ms is not None else "not_available_tick_latest_age"
        ),
        "tick_context_quality": tick_context_quality,
        "quote_age_ms": quote_age_ms if quote_age_ms is not None else "-",
        "quote_age_source": quote_age_source,
        "quote_stale_threshold_ms": quote_stale_threshold_ms,
        "quote_stale": bool(quote_stale) if quote_age_ms is not None else "not_available_quote_age",
        "same_price_buy_absorption": same_price_buy_absorption,
        "large_sell_print_detected": large_sell_print_detected,
        "large_buy_print_detected": large_buy_print_detected,
        "distance_from_day_high_pct": distance_from_day_high_pct,
        "intraday_range_pct": intraday_range_pct,
        "volume_ratio_pct": volume_ratio_pct,
        "curr_vs_micro_vwap_bp": curr_vs_micro_vwap_bp,
        "micro_vwap_available": micro_vwap_available,
        "curr_vs_ma5_bp": curr_vs_ma5_bp,
        "ma5_available": ma5_available,
        "micro_vwap_value": round(micro_vwap_value, 2) if micro_vwap_value else 0.0,
        "ma5_value": round(ma5_value, 2) if ma5_value else 0.0,
        **minute_candle_quality,
        "minute_candle_stale_threshold_ms": SCALP_FEATURE_PACKET_MINUTE_CANDLE_STALE_MS,
        "ask_depth_ratio": ask_depth_ratio,
        "net_ask_depth": net_ask_depth,
        **microstructure_reaction,
    }


def _select_recent_ticks_for_feature_packet(ws_data, recent_ticks, *, now=None):
    rest_ticks = recent_ticks if isinstance(recent_ticks, list) else []
    ws_ticks = ws_data.get("recent_trade_ticks") if isinstance(ws_data, dict) else None
    if not isinstance(ws_ticks, list) or len(ws_ticks) < 5:
        return rest_ticks
    snapshot = precompute_microstructure_reaction_inputs(
        ws_data,
        ws_ticks,
        [],
        now=now,
    )
    age_ms = snapshot.get("tick_age_ms")
    touch_count = int(snapshot.get("tick_aggressor_orderbook_touch_count") or 0) + int(
        snapshot.get("tick_aggressor_cached_orderbook_touch_count") or 0
    )
    trusted_count = int(snapshot.get("tick_aggressor_trusted_count") or 0)
    if age_ms is None or age_ms > 5000 or (touch_count <= 0 and trusted_count <= 0):
        return rest_ticks
    return ws_ticks


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
        "tick_aggressor_source_counts": payload.get("tick_aggressor_source_counts", {}),
        "tick_aggressor_quality_counts": payload.get("tick_aggressor_quality_counts", {}),
        "tick_trade_value_source_counts": payload.get("tick_trade_value_source_counts", {}),
        "tick_trade_value_1313_count": payload.get("tick_trade_value_1313_count", 0),
        "tick_trade_value_1313_missing_count": payload.get("tick_trade_value_1313_missing_count", 0),
        "tick_trade_value_1313_missing_rate_pct": payload.get("tick_trade_value_1313_missing_rate_pct", 0.0),
        "trade_volume_source_counts": payload.get("trade_volume_source_counts", {}),
        "trade_volume_1030_1031_vs_15_evaluable_count": payload.get(
            "trade_volume_1030_1031_vs_15_evaluable_count",
            0,
        ),
        "trade_volume_1030_1031_vs_15_mismatch_count": payload.get(
            "trade_volume_1030_1031_vs_15_mismatch_count",
            0,
        ),
        "trade_volume_1030_1031_vs_15_mismatch_rate_pct": payload.get(
            "trade_volume_1030_1031_vs_15_mismatch_rate_pct",
            0.0,
        ),
        "kiwoom_0b_aux_observed_count": payload.get("kiwoom_0b_aux_observed_count", 0),
        "kiwoom_0b_1313_present_count": payload.get("kiwoom_0b_1313_present_count", 0),
        "kiwoom_0b_1313_missing_count": payload.get("kiwoom_0b_1313_missing_count", 0),
        "kiwoom_0b_1313_missing_rate_pct": payload.get("kiwoom_0b_1313_missing_rate_pct", 0.0),
        "kiwoom_0b_trade_value_source_counts": payload.get("kiwoom_0b_trade_value_source_counts", {}),
        "kiwoom_0b_trade_volume_source_counts": payload.get("kiwoom_0b_trade_volume_source_counts", {}),
        "kiwoom_0b_1030_1031_vs_15_evaluable_count": payload.get(
            "kiwoom_0b_1030_1031_vs_15_evaluable_count",
            0,
        ),
        "kiwoom_0b_1030_1031_vs_15_mismatch_count": payload.get(
            "kiwoom_0b_1030_1031_vs_15_mismatch_count",
            0,
        ),
        "kiwoom_0b_1030_1031_vs_15_mismatch_rate_pct": payload.get(
            "kiwoom_0b_1030_1031_vs_15_mismatch_rate_pct",
            0.0,
        ),
        "tick_aggressor_orderbook_touch_count": payload.get("tick_aggressor_orderbook_touch_count", 0),
        "tick_aggressor_cached_orderbook_touch_count": payload.get(
            "tick_aggressor_cached_orderbook_touch_count", 0
        ),
        "tick_aggressor_price_heuristic_count": payload.get("tick_aggressor_price_heuristic_count", 0),
        "tick_aggressor_unknown_count": payload.get("tick_aggressor_unknown_count", 0),
        "tick_aggressor_trusted_count": payload.get("tick_aggressor_trusted_count", 0),
        "tick_aggressor_pressure_usable": payload.get("tick_aggressor_pressure_usable", False),
        "tick_latest_time": payload.get("tick_latest_time", "-"),
        "tick_latest_age_ms": payload.get("tick_latest_age_ms", "-"),
        "tick_window_span_sec": payload.get("tick_window_span_sec", "-"),
        "tick_accel_effective_recent_5tick_seconds": payload.get("tick_accel_effective_recent_5tick_seconds", "-"),
        "tick_acceleration_ratio_raw": payload.get("tick_acceleration_ratio_raw", "-"),
        "tick_accel_source": payload.get("tick_accel_source", "-"),
        "tick_context_stale": payload.get("tick_context_stale", "not_available_tick_latest_age"),
        "tick_context_quality": payload.get("tick_context_quality", "unknown"),
        "quote_age_ms": payload.get("quote_age_ms", "-"),
        "quote_age_source": payload.get("quote_age_source", "missing"),
        "quote_stale_threshold_ms": payload.get("quote_stale_threshold_ms", SCALP_FEATURE_PACKET_QUOTE_STALE_MS),
        "quote_stale": payload.get("quote_stale", "not_available_quote_age"),
        "recent_5tick_seconds": payload.get("recent_5tick_seconds", "-"),
        "prev_5tick_seconds": payload.get("prev_5tick_seconds", "-"),
        "tick_acceleration_ratio": payload.get("tick_acceleration_ratio", "-"),
        "buy_pressure_10t": payload.get("buy_pressure_10t", "-"),
        "curr_vs_micro_vwap_bp": payload.get("curr_vs_micro_vwap_bp", "-"),
        "micro_vwap_available": payload.get("micro_vwap_available", False),
        "curr_vs_ma5_bp": payload.get("curr_vs_ma5_bp", "-"),
        "ma5_available": payload.get("ma5_available", False),
        "minute_candle_latest_time": payload.get("minute_candle_latest_time", "-"),
        "minute_candle_latest_age_ms": payload.get("minute_candle_latest_age_ms", "-"),
        "minute_candle_context_quality": payload.get("minute_candle_context_quality", "unknown"),
        "minute_candle_reference_source": payload.get("minute_candle_reference_source", "-"),
        "minute_candle_source_time_basis": payload.get("minute_candle_source_time_basis", "-"),
        "minute_candle_window_fresh": payload.get("minute_candle_window_fresh", False),
        "minute_candle_stale_threshold_ms": payload.get(
            "minute_candle_stale_threshold_ms",
            SCALP_FEATURE_PACKET_MINUTE_CANDLE_STALE_MS,
        ),
        "microstructure_reaction_context_version": payload.get("microstructure_reaction_context_version", "-"),
        "microstructure_reaction_context_status": payload.get("microstructure_reaction_context_status", "-"),
        "microstructure_reaction_tick_aggressor_pressure_usable": payload.get(
            "microstructure_reaction_tick_aggressor_pressure_usable", False
        ),
        "microstructure_reaction_tick_aggressor_trusted_count": payload.get(
            "microstructure_reaction_tick_aggressor_trusted_count", 0
        ),
        "microstructure_reaction_ask_sweep_score": payload.get("microstructure_reaction_ask_sweep_score", 50),
        "microstructure_reaction_post_sweep_hold_score": payload.get("microstructure_reaction_post_sweep_hold_score", 50),
        "microstructure_reaction_bid_replenishment_score": payload.get("microstructure_reaction_bid_replenishment_score", 50),
        "microstructure_reaction_wall_replenishment_risk_score": payload.get("microstructure_reaction_wall_replenishment_risk_score", 50),
        "microstructure_reaction_vi_proximity_risk": payload.get("microstructure_reaction_vi_proximity_risk", 0),
        "microstructure_reaction_entry_reaction_quality": payload.get("microstructure_reaction_entry_reaction_quality", "-"),
        "microstructure_reaction_source_quality": payload.get("microstructure_reaction_source_quality", "-"),
        "microstructure_reaction_context_hash": payload.get("microstructure_reaction_context_hash", "-"),
    }
