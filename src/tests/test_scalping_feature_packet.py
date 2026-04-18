from src.engine.ai_engine import GeminiSniperEngine
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
    packet = extract_scalping_feature_packet(_sample_ws_data(), _sample_ticks(), _sample_candles())

    assert packet["packet_version"] == SCALP_FEATURE_PACKET_VERSION
    assert packet["tick_acceleration_ratio"] > 1.0
    assert packet["same_price_buy_absorption"] >= 3
    assert packet["large_sell_print_detected"] is False
    assert packet["net_aggressive_delta_10t"] > 0
    assert packet["ask_depth_ratio"] == 93.5
    assert packet["net_ask_depth"] == -4200


def test_build_scalping_feature_audit_fields_marks_sent_flags():
    packet = extract_scalping_feature_packet(_sample_ws_data(), _sample_ticks(), _sample_candles())
    fields = build_scalping_feature_audit_fields(packet)

    assert fields == {
        "scalp_feature_packet_version": SCALP_FEATURE_PACKET_VERSION,
        "tick_acceleration_ratio_sent": True,
        "same_price_buy_absorption_sent": True,
        "large_sell_print_detected_sent": True,
        "ask_depth_ratio_sent": True,
    }


def test_gemini_market_packet_includes_quant_feature_section():
    engine = GeminiSniperEngine.__new__(GeminiSniperEngine)

    packet = engine._format_market_data(_sample_ws_data(), _sample_ticks(), _sample_candles())

    assert "[정량형 수급 피처]" in packet
    assert f"packet_version: {SCALP_FEATURE_PACKET_VERSION}" in packet
    assert "- tick_acceleration_ratio:" in packet
    assert "- same_price_buy_absorption:" in packet
    assert "- ask_depth_ratio: 93.5" in packet
    assert "- net_ask_depth: -4200" in packet
