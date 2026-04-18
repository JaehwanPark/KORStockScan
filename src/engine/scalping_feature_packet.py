from __future__ import annotations

from datetime import datetime
from statistics import mean


SCALP_FEATURE_PACKET_VERSION = "scalp_feature_packet_v1"


def _safe_hhmmss_to_seconds(value):
    try:
        text = str(value).replace(":", "").zfill(6)
        parsed = datetime.strptime(text, "%H%M%S")
        return parsed.hour * 3600 + parsed.minute * 60 + parsed.second
    except Exception:
        return None


def extract_scalping_feature_packet(ws_data, recent_ticks, recent_candles=None):
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
    same_price_buy_absorption = 0
    large_sell_print_detected = False
    large_buy_print_detected = False

    ticks = recent_ticks[:10] if recent_ticks else []

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
        if len(tick_secs) >= 5 and tick_secs[0] is not None and tick_secs[4] is not None:
            recent_5tick_seconds = tick_secs[0] - tick_secs[4]
            if recent_5tick_seconds < 0:
                recent_5tick_seconds += 86400

        if len(tick_secs) >= 10 and tick_secs[5] is not None and tick_secs[9] is not None:
            prev_5tick_seconds = tick_secs[5] - tick_secs[9]
            if prev_5tick_seconds < 0:
                prev_5tick_seconds += 86400

        if recent_5tick_seconds > 0 and prev_5tick_seconds < 999:
            tick_acceleration_ratio = round(prev_5tick_seconds / recent_5tick_seconds, 3)

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
            from src.engine.signal_radar import SniperRadar

            temp_radar = SniperRadar(token=None)
            indicators = temp_radar.calculate_micro_indicators(recent_candles)

            ma5_value = indicators.get("MA5", 0) or 0
            micro_vwap_value = indicators.get("Micro_VWAP", 0) or 0

            if micro_vwap_value > 0 and curr_price > 0:
                curr_vs_micro_vwap_bp = round(((curr_price - micro_vwap_value) / micro_vwap_value) * 10000, 2)
            if ma5_value > 0 and curr_price > 0:
                curr_vs_ma5_bp = round(((curr_price - ma5_value) / ma5_value) * 10000, 2)
        except Exception:
            pass

    orderbook_total_ratio = round((ask_tot / bid_tot), 3) if bid_tot > 0 else 999.0

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
        "prev_5tick_seconds": round(prev_5tick_seconds, 3) if prev_5tick_seconds < 999 else 999.0,
        "tick_acceleration_ratio": tick_acceleration_ratio,
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
    }


def build_scalping_feature_audit_fields(packet):
    payload = packet or {}
    return {
        "scalp_feature_packet_version": str(payload.get("packet_version", SCALP_FEATURE_PACKET_VERSION)),
        "tick_acceleration_ratio_sent": "tick_acceleration_ratio" in payload,
        "same_price_buy_absorption_sent": "same_price_buy_absorption" in payload,
        "large_sell_print_detected_sent": "large_sell_print_detected" in payload,
        "ask_depth_ratio_sent": "ask_depth_ratio" in payload,
    }
