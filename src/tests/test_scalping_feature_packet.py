import json
from datetime import datetime, timedelta

from src.engine.ai_engine_openai import GPTSniperEngine
from src.engine.scalping_feature_packet import (
    SCALP_FEATURE_PACKET_VERSION,
    build_scalping_feature_audit_fields,
    extract_scalping_feature_packet,
)


def _sample_ws_data():
    return {
        "curr": 10100,
        "v_pw": 132.5,
        "ask_tot": 180000,
        "bid_tot": 150000,
        "net_ask_depth": -4200,
        "ask_depth_ratio": 93.5,
        "orderbook": {
            "asks": [
                {"price": 10110, "volume": 4500},
                {"price": 10120, "volume": 5500},
                {"price": 10130, "volume": 6500},
            ],
            "bids": [
                {"price": 10100, "volume": 3000},
                {"price": 10090, "volume": 4000},
                {"price": 10080, "volume": 5000},
            ],
        },
    }


def _sample_ticks():
    return [
        {"time": "09:00:10", "price": 10100, "volume": 220, "dir": "BUY", "strength": 135.0},
        {"time": "09:00:09", "price": 10100, "volume": 180, "dir": "BUY", "strength": 133.0},
        {"time": "09:00:08", "price": 10100, "volume": 160, "dir": "BUY", "strength": 131.0},
        {"time": "09:00:07", "price": 10095, "volume": 100, "dir": "SELL", "strength": 125.0},
        {"time": "09:00:06", "price": 10095, "volume": 90, "dir": "BUY", "strength": 122.0},
        {"time": "09:00:05", "price": 10090, "volume": 95, "dir": "BUY", "strength": 120.0},
        {"time": "09:00:00", "price": 10090, "volume": 80, "dir": "SELL", "strength": 119.0},
        {"time": "08:59:56", "price": 10085, "volume": 70, "dir": "BUY", "strength": 118.0},
        {"time": "08:59:52", "price": 10085, "volume": 60, "dir": "SELL", "strength": 117.0},
        {"time": "08:59:48", "price": 10080, "volume": 55, "dir": "BUY", "strength": 116.0},
    ]


def _sample_candles():
    return [
        {"체결시간": "08:56:00", "현재가": 10040, "고가": 10060, "저가": 10010, "거래량": 800},
        {"체결시간": "08:57:00", "현재가": 10060, "고가": 10080, "저가": 10030, "거래량": 900},
        {"체결시간": "08:58:00", "현재가": 10080, "고가": 10090, "저가": 10040, "거래량": 1000},
        {"체결시간": "08:59:00", "현재가": 10090, "고가": 10120, "저가": 10070, "거래량": 1200},
        {"체결시간": "09:00:00", "현재가": 10100, "고가": 10130, "저가": 10080, "거래량": 1600},
    ]


def test_extract_scalping_feature_packet_exposes_stage1_supply_fields():
    packet = extract_scalping_feature_packet(
        _sample_ws_data(),
        _sample_ticks(),
        _sample_candles(),
        now=datetime.strptime("09:00:12", "%H:%M:%S"),
    )

    assert packet["packet_version"] == SCALP_FEATURE_PACKET_VERSION
    assert packet["tick_acceleration_ratio"] > 1.0
    assert packet["tick_accel_source"] == "computed_10ticks"
    assert packet["tick_sample_count"] == 10
    assert packet["tick_latest_time"] == "09:00:10"
    assert packet["tick_latest_age_ms"] == 2000
    assert packet["tick_window_span_sec"] == 22
    assert packet["tick_context_stale"] is False
    assert packet["tick_context_quality"] == "fresh_computed"
    assert packet["quote_age_ms"] == "-"
    assert packet["quote_stale"] == "unknown"
    assert packet["same_price_buy_absorption"] >= 3
    assert packet["large_sell_print_detected"] is False
    assert packet["net_aggressive_delta_10t"] > 0
    assert packet["ask_depth_ratio"] == 93.5
    assert packet["net_ask_depth"] == -4200


def test_build_scalping_feature_audit_fields_marks_sent_flags():
    packet = extract_scalping_feature_packet(
        _sample_ws_data(),
        _sample_ticks(),
        _sample_candles(),
        now=datetime.strptime("09:00:12", "%H:%M:%S"),
    )
    fields = build_scalping_feature_audit_fields(packet)

    expected_flags = {
        "scalp_feature_packet_version": SCALP_FEATURE_PACKET_VERSION,
        "tick_acceleration_ratio_sent": True,
        "same_price_buy_absorption_sent": True,
        "large_sell_print_detected_sent": True,
        "ask_depth_ratio_sent": True,
    }
    for key, value in expected_flags.items():
        assert fields[key] == value
    assert fields["tick_source_quality_fields_sent"] is True
    assert fields["tick_sample_count"] == 10
    assert fields["tick_latest_age_ms"] == 2000
    assert fields["tick_accel_source"] == "computed_10ticks"
    assert fields["tick_context_stale"] is False
    assert fields["tick_context_quality"] == "fresh_computed"


def test_extract_scalping_feature_packet_uses_ws_update_timestamp_for_quote_age():
    now = datetime(2026, 5, 15, 9, 0, 12)
    ws_data = {
        **_sample_ws_data(),
        "last_ws_update_ts": (now - timedelta(milliseconds=450)).timestamp(),
    }

    packet = extract_scalping_feature_packet(
        ws_data,
        _sample_ticks(),
        _sample_candles(),
        now=now,
    )
    fields = build_scalping_feature_audit_fields(packet)

    assert packet["quote_age_ms"] == 450
    assert packet["quote_age_source"] == "last_ws_update_ts"
    assert packet["quote_stale"] is False
    assert fields["quote_age_ms"] == 450
    assert fields["quote_age_source"] == "last_ws_update_ts"
    assert fields["quote_stale"] is False


def test_extract_scalping_feature_packet_treats_same_second_ticks_as_burst():
    ticks = [
        {"time": "09:00:10", "price": 10100, "volume": 220, "dir": "BUY", "strength": 135.0},
        {"time": "09:00:10", "price": 10100, "volume": 180, "dir": "BUY", "strength": 133.0},
        {"time": "09:00:10", "price": 10100, "volume": 160, "dir": "BUY", "strength": 131.0},
        {"time": "09:00:10", "price": 10095, "volume": 100, "dir": "SELL", "strength": 125.0},
        {"time": "09:00:10", "price": 10095, "volume": 90, "dir": "BUY", "strength": 122.0},
        {"time": "09:00:07", "price": 10090, "volume": 95, "dir": "BUY", "strength": 120.0},
        {"time": "09:00:05", "price": 10090, "volume": 80, "dir": "SELL", "strength": 119.0},
        {"time": "09:00:03", "price": 10085, "volume": 70, "dir": "BUY", "strength": 118.0},
        {"time": "09:00:01", "price": 10085, "volume": 60, "dir": "SELL", "strength": 117.0},
        {"time": "08:59:59", "price": 10080, "volume": 55, "dir": "BUY", "strength": 116.0},
    ]
    packet = extract_scalping_feature_packet(
        _sample_ws_data(),
        ticks,
        _sample_candles(),
        now=datetime.strptime("09:00:11", "%H:%M:%S"),
    )

    assert packet["recent_5tick_seconds"] == 0
    assert packet["tick_accel_effective_recent_5tick_seconds"] == 1.0
    assert packet["tick_accel_source"] == "same_second_burst_10ticks"
    assert packet["tick_acceleration_ratio"] > 1.0
    assert packet["tick_acceleration_ratio_raw"] == 0.0
    assert packet["tick_context_quality"] == "fresh_computed"


def test_openai_market_packet_includes_quant_feature_section():
    engine = GPTSniperEngine.__new__(GPTSniperEngine)

    packet = engine._format_market_data(_sample_ws_data(), _sample_ticks(), _sample_candles())
    payload = json.loads(packet)

    assert payload["features"]["packet_version"] == SCALP_FEATURE_PACKET_VERSION
    assert "tick_acceleration_ratio" in payload["features"]
    assert "same_price_buy_absorption" in payload["features"]
    assert payload["features"]["ask_depth_ratio"] == 93.5
    assert payload["features"]["net_ask_depth"] == -4200
