import json
from datetime import datetime, timedelta

from src.engine import ai_engine_openai as openai_module
from src.engine.ai_engine_openai import GPTSniperEngine
from src.engine.scalping_feature_packet import (
    SCALP_FEATURE_PACKET_VERSION,
    SCALP_FEATURE_PACKET_QUOTE_STALE_MS,
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
        {
            "time": "09:00:10",
            "price": 10100,
            "volume": 220,
            "dir": "BUY",
            "aggressor_source": "trusted_declared_side",
            "strength": 135.0,
        },
        {
            "time": "09:00:09",
            "price": 10100,
            "volume": 180,
            "dir": "BUY",
            "aggressor_source": "trusted_declared_side",
            "strength": 133.0,
        },
        {
            "time": "09:00:08",
            "price": 10100,
            "volume": 160,
            "dir": "BUY",
            "aggressor_source": "trusted_declared_side",
            "strength": 131.0,
        },
        {
            "time": "09:00:07",
            "price": 10095,
            "volume": 100,
            "dir": "SELL",
            "aggressor_source": "trusted_declared_side",
            "strength": 125.0,
        },
        {
            "time": "09:00:06",
            "price": 10095,
            "volume": 90,
            "dir": "BUY",
            "aggressor_source": "trusted_declared_side",
            "strength": 122.0,
        },
        {
            "time": "09:00:05",
            "price": 10090,
            "volume": 95,
            "dir": "BUY",
            "aggressor_source": "trusted_declared_side",
            "strength": 120.0,
        },
        {
            "time": "09:00:00",
            "price": 10090,
            "volume": 80,
            "dir": "SELL",
            "aggressor_source": "trusted_declared_side",
            "strength": 119.0,
        },
        {
            "time": "08:59:56",
            "price": 10085,
            "volume": 70,
            "dir": "BUY",
            "aggressor_source": "trusted_declared_side",
            "strength": 118.0,
        },
        {
            "time": "08:59:52",
            "price": 10085,
            "volume": 60,
            "dir": "SELL",
            "aggressor_source": "trusted_declared_side",
            "strength": 117.0,
        },
        {
            "time": "08:59:48",
            "price": 10080,
            "volume": 55,
            "dir": "BUY",
            "aggressor_source": "trusted_declared_side",
            "strength": 116.0,
        },
    ]


def _sample_candles():
    return [
        {
            "체결시간": "08:56:00",
            "현재가": 10040,
            "고가": 10060,
            "저가": 10010,
            "거래량": 800,
        },
        {
            "체결시간": "08:57:00",
            "현재가": 10060,
            "고가": 10080,
            "저가": 10030,
            "거래량": 900,
        },
        {
            "체결시간": "08:58:00",
            "현재가": 10080,
            "고가": 10090,
            "저가": 10040,
            "거래량": 1000,
        },
        {
            "체결시간": "08:59:00",
            "현재가": 10090,
            "고가": 10120,
            "저가": 10070,
            "거래량": 1200,
        },
        {
            "체결시간": "09:00:00",
            "현재가": 10100,
            "고가": 10130,
            "저가": 10080,
            "거래량": 1600,
        },
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
    assert packet["quote_stale"] == "not_available_quote_age"
    assert packet["same_price_buy_absorption"] >= 3
    assert packet["large_sell_print_detected"] is False
    assert packet["net_aggressive_delta_10t"] > 0
    assert packet["ask_depth_ratio"] == 93.5
    assert packet["net_ask_depth"] == -4200
    assert (
        packet["microstructure_reaction_context_version"]
        == "microstructure_reaction_context_v1"
    )
    assert packet["microstructure_reaction_context_status"] == "ok"
    assert packet["microstructure_reaction_tick_aggressor_pressure_usable"] is True
    assert packet["microstructure_reaction_tick_aggressor_trusted_count"] > 0
    assert packet["microstructure_reaction_context_hash"]
    assert packet["microstructure_reaction_vi_proximity_risk"] >= 0
    assert packet["micro_vwap_available"] is True
    assert packet["ma5_available"] is True
    assert packet["minute_candle_context_quality"] == "fresh_bar_window"
    assert packet["minute_candle_latest_age_ms"] == 12000
    assert packet["minute_candle_window_fresh"] is True


def test_extract_scalping_feature_packet_marks_micro_vwap_unavailable_without_candles():
    packet = extract_scalping_feature_packet(
        _sample_ws_data(),
        _sample_ticks(),
        [],
        now=datetime.strptime("09:00:12", "%H:%M:%S"),
    )
    audit = build_scalping_feature_audit_fields(packet)
    engine = GPTSniperEngine.__new__(GPTSniperEngine)
    compact = engine._compact_holding_score_feature_packet(packet, audit)

    assert packet["curr_vs_micro_vwap_bp"] == 0.0
    assert packet["micro_vwap_available"] is False
    assert packet["ma5_available"] is False
    assert packet["minute_candle_context_quality"] == "missing_candles"
    assert audit["micro_vwap_available"] is False
    assert compact["micro_vwap_available"] is False


def test_extract_scalping_feature_packet_blocks_stale_candle_micro_vwap():
    packet = extract_scalping_feature_packet(
        _sample_ws_data(),
        _sample_ticks(),
        _sample_candles(),
        now=datetime.strptime("09:10:00", "%H:%M:%S"),
    )
    audit = build_scalping_feature_audit_fields(packet)

    assert packet["minute_candle_context_quality"] == "stale_bar_window"
    assert packet["minute_candle_latest_age_ms"] == 600000
    assert packet["minute_candle_window_fresh"] is False
    assert packet["micro_vwap_value"] > 0
    assert packet["micro_vwap_available"] is False
    assert packet["ma5_available"] is False
    assert packet["curr_vs_micro_vwap_bp"] == 0.0
    assert audit["minute_candle_context_quality"] == "stale_bar_window"
    assert audit["micro_vwap_available"] is False


def test_extract_scalping_feature_packet_blocks_missing_candle_timestamp_micro_vwap():
    candles = [
        {"현재가": 10100, "고가": 10120, "저가": 10090, "거래량": 1000 + idx}
        for idx in range(5)
    ]

    packet = extract_scalping_feature_packet(
        _sample_ws_data(),
        _sample_ticks(),
        candles,
        now=datetime.strptime("09:00:12", "%H:%M:%S"),
    )

    assert packet["minute_candle_context_quality"] == "missing_candle_time"
    assert packet["minute_candle_latest_age_ms"] == "-"
    assert packet["micro_vwap_value"] > 0
    assert packet["micro_vwap_available"] is False
    assert packet["ma5_available"] is False


def test_extract_scalping_feature_packet_normalizes_tick_side_aliases_for_buy_pressure():
    ticks = [
        {
            "time": "09:00:10",
            "price": 10100,
            "volume": 100,
            "dir": "매수",
            "aggressor_source": "trusted_declared_side",
            "strength": 135.0,
        },
        {
            "time": "09:00:09",
            "price": 10100,
            "volume": 50,
            "dir": "+매수",
            "aggressor_source": "trusted_declared_side",
            "strength": 133.0,
        },
        {
            "time": "09:00:08",
            "price": 10095,
            "volume": 30,
            "dir": "B",
            "aggressor_source": "trusted_declared_side",
            "strength": 131.0,
        },
        {
            "time": "09:00:07",
            "price": 10090,
            "volume": 20,
            "dir": "매도",
            "aggressor_source": "trusted_declared_side",
            "strength": 125.0,
        },
        {
            "time": "09:00:06",
            "price": 10090,
            "volume": 20,
            "dir": "S",
            "aggressor_source": "trusted_declared_side",
            "strength": 122.0,
        },
    ]

    packet = extract_scalping_feature_packet(
        _sample_ws_data(),
        ticks,
        _sample_candles(),
        now=datetime.strptime("09:00:12", "%H:%M:%S"),
    )

    assert packet["buy_pressure_10t"] == 81.82
    assert packet["net_aggressive_delta_10t"] == 140


def test_extract_scalping_feature_packet_keeps_source_less_side_aliases_neutral():
    ticks = [
        {
            "time": "09:00:10",
            "price": 10100,
            "volume": 100,
            "dir": "매수",
            "strength": 135.0,
        },
        {
            "time": "09:00:09",
            "price": 10100,
            "volume": 50,
            "dir": "B",
            "strength": 133.0,
        },
        {
            "time": "09:00:08",
            "price": 10090,
            "volume": 40,
            "side": "SELL",
            "strength": 125.0,
        },
    ]

    packet = extract_scalping_feature_packet(
        _sample_ws_data(),
        ticks,
        _sample_candles(),
        now=datetime.strptime("09:00:12", "%H:%M:%S"),
    )

    assert packet["buy_pressure_10t"] == 50.0
    assert packet["net_aggressive_delta_10t"] == 0
    assert packet["tick_aggressor_trusted_count"] == 0
    assert packet["tick_aggressor_pressure_usable"] is False
    assert packet["tick_aggressor_source_counts"]["declared_tick_side_untrusted"] == 3


def test_extract_scalping_feature_packet_prefers_fresh_ws_orderbook_touch_ticks():
    ws_data = _sample_ws_data()
    ws_data["recent_trade_ticks"] = [
        {
            "time": "09:00:10",
            "price": 10110,
            "volume": 100,
            "best_ask": 10110,
            "best_bid": 10100,
            "aggressor_source": "orderbook_touch",
        },
        {
            "time": "09:00:09",
            "price": 10110,
            "volume": 80,
            "best_ask": 10110,
            "best_bid": 10100,
            "aggressor_source": "orderbook_touch",
        },
        {
            "time": "09:00:08",
            "price": 10100,
            "volume": 40,
            "best_ask": 10110,
            "best_bid": 10100,
            "aggressor_source": "orderbook_touch",
        },
        {
            "time": "09:00:07",
            "price": 10110,
            "volume": 60,
            "best_ask": 10110,
            "best_bid": 10100,
            "aggressor_source": "orderbook_touch",
        },
        {
            "time": "09:00:06",
            "price": 10105,
            "volume": 20,
            "best_ask": 10110,
            "best_bid": 10100,
            "aggressor_source": "orderbook_touch",
        },
    ]
    rest_ticks = [
        {
            "time": "09:00:10",
            "price": 10100,
            "volume": 999,
            "dir": "SELL",
            "strength": 120.0,
        }
        for _ in range(10)
    ]

    packet = extract_scalping_feature_packet(
        ws_data,
        rest_ticks,
        _sample_candles(),
        now=datetime.strptime("09:00:12", "%H:%M:%S"),
    )

    assert packet["buy_pressure_10t"] == 85.71
    assert packet["net_aggressive_delta_10t"] == 200
    assert packet["tick_aggressor_orderbook_touch_count"] == 5
    assert packet["tick_aggressor_price_heuristic_count"] == 0
    assert packet["tick_aggressor_unknown_count"] == 1
    assert packet["tick_aggressor_trusted_count"] == 4
    assert packet["tick_aggressor_pressure_usable"] is True


def test_extract_scalping_feature_packet_prefers_cached_orderbook_touch_ws_ticks():
    ws_data = _sample_ws_data()
    ws_data["recent_trade_ticks"] = [
        {
            "time": "09:00:10",
            "price": 10110,
            "volume": 100,
            "best_ask": 10110,
            "best_bid": 10100,
            "aggressor_source": "cached_orderbook_touch",
            "aggressor_quality": "cached_quote_touch_or_crossed_ask",
            "aggressor_quote_source": "cached_top_of_book_ttl",
        },
        {
            "time": "09:00:09",
            "price": 10110,
            "volume": 80,
            "best_ask": 10110,
            "best_bid": 10100,
            "aggressor_source": "cached_orderbook_touch",
            "aggressor_quote_source": "cached_top_of_book_ttl",
        },
        {
            "time": "09:00:08",
            "price": 10100,
            "volume": 40,
            "best_ask": 10110,
            "best_bid": 10100,
            "aggressor_source": "cached_orderbook_touch",
            "aggressor_quote_source": "cached_top_of_book_ttl",
        },
        {
            "time": "09:00:07",
            "price": 10110,
            "volume": 60,
            "best_ask": 10110,
            "best_bid": 10100,
            "aggressor_source": "cached_orderbook_touch",
            "aggressor_quote_source": "cached_top_of_book_ttl",
        },
        {
            "time": "09:00:06",
            "price": 10105,
            "volume": 20,
            "best_ask": 10110,
            "best_bid": 10100,
            "aggressor_source": "cached_orderbook_touch",
            "aggressor_quote_source": "cached_top_of_book_ttl",
        },
    ]
    rest_ticks = [
        {
            "time": "09:00:10",
            "price": 10100,
            "volume": 999,
            "dir": "SELL",
            "aggressor_source": "price_change_heuristic",
            "strength": 120.0,
        }
        for _ in range(10)
    ]

    packet = extract_scalping_feature_packet(
        ws_data,
        rest_ticks,
        _sample_candles(),
        now=datetime.strptime("09:00:12", "%H:%M:%S"),
    )
    audit = build_scalping_feature_audit_fields(packet)
    engine = GPTSniperEngine.__new__(GPTSniperEngine)
    compact = engine._compact_holding_score_feature_packet(packet)

    assert packet["buy_pressure_10t"] == 85.71
    assert packet["tick_aggressor_orderbook_touch_count"] == 0
    assert packet["tick_aggressor_cached_orderbook_touch_count"] == 5
    assert packet["tick_aggressor_trusted_count"] == 4
    assert audit["tick_aggressor_cached_orderbook_touch_count"] == 5
    assert compact["aggressor_quality"]["cached_orderbook_touch"] == 5


def test_extract_scalping_feature_packet_prefers_signed_0b_ws_ticks_without_touch_count():
    ws_data = _sample_ws_data()
    ws_data.update(
        {
            "kiwoom_0b_aux_observed_count": 7,
            "kiwoom_0b_1313_present_count": 3,
            "kiwoom_0b_1313_missing_count": 4,
            "kiwoom_0b_trade_value_source_counts": {
                "1313": 3,
                "calc_price_x_1030_1031_sum": 4,
            },
            "kiwoom_0b_trade_volume_source_counts": {"1030_1031_sum": 6, "15_abs": 1},
            "kiwoom_0b_1030_1031_vs_15_evaluable_count": 6,
            "kiwoom_0b_1030_1031_vs_15_mismatch_count": 2,
        }
    )
    ws_data["recent_trade_ticks"] = [
        {
            "time": "09:00:10",
            "price": 10110,
            "volume": 100,
            "aggressor_side": "BUY",
            "aggressor_source": "kiwoom_0b_signed_trade_volume",
            "aggressor_quality": "signed_trade_volume_positive",
            "signed_trade_volume": "+100",
            "tick_trade_value_source": "1313",
            "volume_source": "1030_1031_sum",
            "trade_volume_1030_1031_vs_15_mismatch": False,
        },
        {
            "time": "09:00:09",
            "price": 10110,
            "volume": 80,
            "aggressor_side": "BUY",
            "aggressor_source": "kiwoom_0b_signed_trade_volume",
            "aggressor_quality": "signed_trade_volume_positive",
            "signed_trade_volume": "+80",
            "tick_trade_value_source": "calc_price_x_1030_1031_sum",
            "volume_source": "1030_1031_sum",
            "trade_volume_1030_1031_vs_15_mismatch": True,
        },
        {
            "time": "09:00:08",
            "price": 10100,
            "volume": 40,
            "aggressor_side": "SELL",
            "aggressor_source": "kiwoom_0b_signed_trade_volume",
            "aggressor_quality": "signed_trade_volume_negative",
            "signed_trade_volume": "-40",
            "tick_trade_value_source": "1313",
            "volume_source": "15_abs",
            "trade_volume_1030_1031_vs_15_mismatch": False,
        },
        {
            "time": "09:00:07",
            "price": 10110,
            "volume": 60,
            "aggressor_side": "BUY",
            "aggressor_source": "kiwoom_0b_signed_trade_volume",
            "aggressor_quality": "signed_trade_volume_positive",
            "signed_trade_volume": "+60",
            "tick_trade_value_source": "calc_price_x_15_abs",
            "volume_source": "1030_1031_sum",
            "trade_volume_1030_1031_vs_15_mismatch": True,
        },
        {
            "time": "09:00:06",
            "price": 10105,
            "volume": 20,
            "aggressor_side": "BUY",
            "aggressor_source": "kiwoom_0b_signed_trade_volume",
            "aggressor_quality": "signed_trade_volume_positive",
            "signed_trade_volume": "+20",
            "tick_trade_value_source": "calc_price_x_1030_1031_sum",
            "volume_source": "1030_1031_sum",
            "trade_volume_1030_1031_vs_15_mismatch": False,
        },
    ]
    rest_ticks = [
        {
            "time": "09:00:10",
            "price": 10100,
            "volume": 999,
            "dir": "SELL",
            "aggressor_source": "price_change_heuristic",
            "strength": 120.0,
        }
        for _ in range(10)
    ]

    packet = extract_scalping_feature_packet(
        ws_data,
        rest_ticks,
        _sample_candles(),
        now=datetime.strptime("09:00:12", "%H:%M:%S"),
    )

    assert packet["buy_pressure_10t"] == 86.67
    assert packet["net_aggressive_delta_10t"] == 220
    assert packet["tick_aggressor_orderbook_touch_count"] == 0
    assert packet["tick_aggressor_cached_orderbook_touch_count"] == 0
    assert packet["tick_aggressor_source_counts"]["kiwoom_0b_signed_trade_volume"] == 5
    assert packet["tick_aggressor_trusted_count"] == 5
    assert packet["tick_aggressor_pressure_usable"] is True
    assert packet["tick_trade_value_source_counts"] == {
        "1313": 2,
        "calc_price_x_1030_1031_sum": 2,
        "calc_price_x_15_abs": 1,
    }
    assert packet["tick_trade_value_1313_missing_count"] == 3
    assert packet["tick_trade_value_1313_missing_rate_pct"] == 60.0
    assert packet["trade_volume_source_counts"] == {"1030_1031_sum": 4, "15_abs": 1}
    assert packet["trade_volume_1030_1031_vs_15_mismatch_count"] == 2
    assert packet["trade_volume_1030_1031_vs_15_mismatch_rate_pct"] == 40.0
    assert packet["kiwoom_0b_1313_missing_rate_pct"] == 57.143
    assert packet["kiwoom_0b_1030_1031_vs_15_mismatch_rate_pct"] == 33.333


def test_extract_scalping_feature_packet_excludes_price_change_heuristic_from_pressure():
    ticks = [
        {
            "time": "09:00:10",
            "price": 10100,
            "volume": 100,
            "dir": "BUY",
            "aggressor_source": "price_change_heuristic",
            "strength": 135.0,
        },
        {
            "time": "09:00:09",
            "price": 10090,
            "volume": 90,
            "dir": "SELL",
            "aggressor_source": "price_change_heuristic",
            "strength": 130.0,
        },
    ]

    packet = extract_scalping_feature_packet(
        _sample_ws_data(),
        ticks,
        _sample_candles(),
        now=datetime.strptime("09:00:12", "%H:%M:%S"),
    )

    assert packet["buy_pressure_10t"] == 50.0
    assert packet["net_aggressive_delta_10t"] == 0
    assert packet["large_sell_print_detected"] is False
    assert packet["tick_aggressor_price_heuristic_count"] == 2
    assert packet["tick_aggressor_trusted_count"] == 0
    assert packet["tick_aggressor_pressure_usable"] is False


def test_extract_scalping_feature_packet_mixed_pressure_uses_trusted_ticks_only():
    ticks = [
        {
            "time": "09:00:10",
            "price": 10110,
            "volume": 100,
            "best_ask": 10110,
            "best_bid": 10100,
            "aggressor_source": "orderbook_touch",
            "strength": 135.0,
        },
        {
            "time": "09:00:09",
            "price": 10090,
            "volume": 999,
            "dir": "SELL",
            "aggressor_source": "price_change_heuristic",
            "strength": 130.0,
        },
    ]

    packet = extract_scalping_feature_packet(
        _sample_ws_data(),
        ticks,
        _sample_candles(),
        now=datetime.strptime("09:00:12", "%H:%M:%S"),
    )

    assert packet["buy_pressure_10t"] == 100.0
    assert packet["net_aggressive_delta_10t"] == 100
    assert packet["tick_aggressor_orderbook_touch_count"] == 1
    assert packet["tick_aggressor_price_heuristic_count"] == 1
    assert packet["tick_aggressor_trusted_count"] == 1
    assert packet["tick_aggressor_pressure_usable"] is True


def test_extract_scalping_feature_packet_rejects_partial_orderbook_touch_quote():
    ticks = [
        {
            "time": "09:00:10",
            "price": 10110,
            "volume": 100,
            "best_ask": 10110,
            "best_bid": 0,
            "aggressor_source": "orderbook_touch",
            "strength": 135.0,
        },
        {
            "time": "09:00:09",
            "price": 10100,
            "volume": 80,
            "best_ask": 0,
            "best_bid": 10100,
            "aggressor_source": "orderbook_touch",
            "strength": 130.0,
        },
    ]

    packet = extract_scalping_feature_packet(
        _sample_ws_data(),
        ticks,
        _sample_candles(),
        now=datetime.strptime("09:00:12", "%H:%M:%S"),
    )

    assert packet["buy_pressure_10t"] == 50.0
    assert packet["net_aggressive_delta_10t"] == 0
    assert packet["tick_aggressor_orderbook_touch_count"] == 0
    assert packet["tick_aggressor_unknown_count"] == 2
    assert packet["tick_aggressor_trusted_count"] == 0
    assert packet["tick_aggressor_pressure_usable"] is False


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
    assert fields["quote_stale"] == "not_available_quote_age"
    assert fields["entry_liquidity_status"] in {"good", "thin"}
    assert fields["entry_liquidity_score"] >= 50
    assert fields["fillability_score"] >= 40
    assert fields["would_fill_now"] is False
    assert fields["quote_depth_present"] is True
    assert fields["order_flow_pressure_score"] >= 50
    assert fields["entry_order_flow_status"] == "supportive"
    assert fields["entry_momentum_score"] >= 50
    assert fields["entry_momentum_status"] == "accelerating"
    assert fields["entry_context_quality"] in {"partial", "stale", "complete"}
    assert fields["latest_strength"] == packet["latest_strength"]
    assert fields["spread_bp"] == packet["spread_bp"]
    assert fields["top1_depth_ratio"] == packet["top1_depth_ratio"]
    assert fields["top3_depth_ratio"] == packet["top3_depth_ratio"]
    assert fields["orderbook_total_ratio"] == packet["orderbook_total_ratio"]
    assert fields["ask_depth_ratio"] == packet["ask_depth_ratio"]
    assert fields["net_ask_depth"] == packet["net_ask_depth"]
    assert fields["net_aggressive_delta_10t"] == packet["net_aggressive_delta_10t"]
    assert fields["same_price_buy_absorption"] == packet["same_price_buy_absorption"]
    assert fields["large_sell_print_detected"] == packet["large_sell_print_detected"]
    assert fields["large_buy_print_detected"] == packet["large_buy_print_detected"]
    assert fields["distance_from_day_high_pct"] == packet["distance_from_day_high_pct"]
    assert fields["intraday_range_pct"] == packet["intraday_range_pct"]
    assert fields["volume_ratio_pct"] == packet["volume_ratio_pct"]
    assert fields["microstructure_reaction_context_sent"] is True
    assert fields["microstructure_reaction_context_status"] == "ok"
    assert fields["microstructure_reaction_tick_aggressor_pressure_usable"] is True
    assert fields["microstructure_reaction_tick_aggressor_trusted_count"] > 0


def test_entry_context_summary_features_are_complete_when_quote_and_flow_are_fresh():
    now = datetime(2026, 5, 15, 9, 0, 12)
    packet = extract_scalping_feature_packet(
        {
            **_sample_ws_data(),
            "last_ws_update_ts": (now - timedelta(milliseconds=300)).timestamp(),
        },
        _sample_ticks(),
        _sample_candles(),
        now=now,
    )
    fields = build_scalping_feature_audit_fields(packet)

    assert packet["entry_liquidity_status"] == "good"
    assert packet["entry_liquidity_score"] == 84.0
    assert packet["fillability_score"] == 74.0
    assert packet["would_fill_now"] is True
    assert packet["quote_depth_present"] is True
    assert packet["quote_fresh_for_entry"] is True
    assert packet["order_flow_pressure_score"] == 79.5
    assert packet["entry_order_flow_status"] == "supportive"
    assert packet["entry_momentum_score"] == 88.0
    assert packet["entry_momentum_status"] == "accelerating"
    assert packet["entry_context_quality"] == "complete"
    assert packet["entry_context_missing_features"] == ""
    assert fields["entry_liquidity_status"] == "good"
    assert fields["fillability_score"] == 74.0
    assert fields["entry_context_quality"] == "complete"
    assert fields["microstructure_reaction_ask_sweep_score"] >= 0
    assert "tick_trade_value_source_counts" in fields
    assert "trade_volume_source_counts" in fields
    assert "kiwoom_0b_1313_missing_rate_pct" in fields
    assert "kiwoom_0b_1030_1031_vs_15_mismatch_rate_pct" in fields


def test_entry_reason_consistency_flags_position_pass_described_as_fail():
    engine = object.__new__(GPTSniperEngine)
    result = {
        "action": "WAIT",
        "score": 62,
        "reason": (
            "Position advantage not both positive; curr_vs_micro_vwap_bp > 0 and "
            "curr_vs_ma5_bp > 0 are true but BUY is incomplete"
        ),
    }
    feature_packet = {
        "tick_acceleration_ratio": 2.5,
        "buy_pressure_10t": 98.65,
        "curr_vs_micro_vwap_bp": 6.13,
        "curr_vs_ma5_bp": 4.9,
        "micro_vwap_available": True,
        "minute_candle_window_fresh": True,
        "ma5_available": True,
    }

    annotated = engine._annotate_entry_numeric_consistency(
        result,
        prompt_type="scalping_entry",
        feature_packet=feature_packet,
    )

    assert annotated["ai_reason_numeric_inconsistency"] is True
    assert annotated["ai_reason_feature_inconsistency"] is True
    assert annotated["ai_reason_numeric_inconsistency_field"] == "position_advantage"
    assert (
        annotated["ai_reason_numeric_inconsistency_reason"]
        == "position_pass_described_as_fail"
    )


def test_entry_reason_consistency_does_not_flag_position_positive_but_other_gates_weak():
    engine = object.__new__(GPTSniperEngine)
    result = {
        "action": "WAIT",
        "score": 62,
        "reason": (
            "Position advantage present: curr_vs_micro_vwap_bp > 0 and curr_vs_ma5_bp > 0, "
            "but speed and supply-demand are not confirming"
        ),
    }
    feature_packet = {
        "tick_acceleration_ratio": 0.8,
        "buy_pressure_10t": 42.0,
        "curr_vs_micro_vwap_bp": 6.13,
        "curr_vs_ma5_bp": 4.9,
    }

    annotated = engine._annotate_entry_numeric_consistency(
        result,
        prompt_type="scalping_entry",
        feature_packet=feature_packet,
    )

    assert "ai_reason_numeric_inconsistency" not in annotated
    assert "ai_reason_feature_inconsistency" not in annotated


def test_entry_reason_consistency_does_not_flag_not_clearly_positive_when_context_is_mixed():
    engine = object.__new__(GPTSniperEngine)
    result = {
        "action": "WAIT",
        "score": 62,
        "reason": (
            "Position advantage not clearly positive: curr_vs_micro_vwap_bp > 0 "
            "and curr_vs_ma5_bp > 0 both positive, but speed and supply are mixed"
        ),
    }
    feature_packet = {
        "tick_acceleration_ratio": 0.8,
        "buy_pressure_10t": 42.0,
        "curr_vs_micro_vwap_bp": 75.96,
        "curr_vs_ma5_bp": 55.23,
    }

    annotated = engine._annotate_entry_numeric_consistency(
        result,
        prompt_type="scalping_entry",
        feature_packet=feature_packet,
    )

    assert "ai_reason_numeric_inconsistency" not in annotated
    assert "ai_reason_feature_inconsistency" not in annotated


def test_entry_reason_consistency_flags_explicit_wrong_position_sign():
    engine = object.__new__(GPTSniperEngine)
    result = {
        "action": "WAIT",
        "score": 62,
        "reason": "Position disadvantage: curr_vs_micro_vwap_bp <= 0 and curr_vs_ma5_bp <= 0",
    }
    feature_packet = {
        "tick_acceleration_ratio": 0.8,
        "buy_pressure_10t": 42.0,
        "curr_vs_micro_vwap_bp": 6.13,
        "curr_vs_ma5_bp": 4.9,
        "micro_vwap_available": True,
        "minute_candle_window_fresh": True,
        "ma5_available": True,
    }

    annotated = engine._annotate_entry_numeric_consistency(
        result,
        prompt_type="scalping_entry",
        feature_packet=feature_packet,
    )

    assert annotated["ai_reason_numeric_inconsistency"] is True
    assert annotated["ai_reason_numeric_inconsistency_field"] == "position_advantage"
    assert (
        annotated["ai_reason_numeric_inconsistency_reason"]
        == "position_pass_described_as_fail"
    )


def test_entry_reason_consistency_flags_supply_pass_described_as_fail():
    engine = object.__new__(GPTSniperEngine)
    result = {
        "action": "WAIT",
        "score": 62,
        "reason": "insufficient buy pressure: buy_pressure_10t < 68 prevents BUY",
    }
    feature_packet = {
        "tick_acceleration_ratio": 0.9,
        "buy_pressure_10t": 85.2,
        "tick_aggressor_trusted_count": 3,
        "tick_aggressor_pressure_usable": True,
        "curr_vs_micro_vwap_bp": 89.61,
        "curr_vs_ma5_bp": 119.84,
    }

    annotated = engine._annotate_entry_numeric_consistency(
        result,
        prompt_type="scalping_entry",
        feature_packet=feature_packet,
    )

    assert annotated["ai_reason_numeric_inconsistency"] is True
    assert (
        annotated["ai_reason_numeric_inconsistency_field"] == "supply_demand_advantage"
    )
    assert (
        annotated["ai_reason_numeric_inconsistency_reason"]
        == "supply_demand_pass_described_as_fail"
    )


def test_entry_reason_consistency_ignores_untrusted_pressure_pass():
    engine = object.__new__(GPTSniperEngine)
    result = {
        "action": "WAIT",
        "score": 62,
        "reason": "insufficient buy pressure: buy_pressure_10t < 68 prevents BUY",
    }
    feature_packet = {
        "tick_acceleration_ratio": 0.9,
        "buy_pressure_10t": 85.2,
        "net_aggressive_delta_10t": 100,
        "tick_aggressor_trusted_count": 0,
        "tick_aggressor_pressure_usable": False,
        "curr_vs_micro_vwap_bp": 89.61,
        "curr_vs_ma5_bp": 119.84,
    }

    annotated = engine._annotate_entry_numeric_consistency(
        result,
        prompt_type="scalping_entry",
        feature_packet=feature_packet,
    )

    assert "ai_reason_numeric_inconsistency" not in annotated


def test_entry_reason_consistency_flags_three_core_features_pass_no_buy():
    engine = object.__new__(GPTSniperEngine)
    result = {
        "action": "WAIT",
        "score": 74,
        "reason": (
            "Position advantage met and Speed advantage present, but insufficient BUY signals "
            "keep WAIT"
        ),
    }
    feature_packet = {
        "tick_acceleration_ratio": 5.5,
        "buy_pressure_10t": 86.41,
        "tick_aggressor_trusted_count": 3,
        "tick_aggressor_pressure_usable": True,
        "curr_vs_micro_vwap_bp": 56.68,
        "curr_vs_ma5_bp": 58.52,
        "micro_vwap_available": True,
        "minute_candle_window_fresh": True,
        "ma5_available": True,
    }

    annotated = engine._annotate_entry_numeric_consistency(
        result,
        prompt_type="scalping_entry",
        feature_packet=feature_packet,
    )

    assert annotated["ai_reason_numeric_inconsistency"] is True
    assert annotated["ai_reason_numeric_inconsistency_field"] == "entry_feature_bundle"
    assert (
        annotated["ai_reason_numeric_inconsistency_reason"]
        == "three_core_features_pass_described_as_no_buy"
    )


def test_extract_scalping_feature_packet_missing_microstructure_context_is_neutral():
    packet = extract_scalping_feature_packet(
        {"curr": 10100},
        _sample_ticks()[:3],
        _sample_candles(),
        now=datetime.strptime("09:00:12", "%H:%M:%S"),
    )

    assert packet["microstructure_reaction_context_status"] == "source_quality_missing"
    assert packet["microstructure_reaction_ask_sweep_score"] == 50
    assert packet["microstructure_reaction_post_sweep_hold_score"] == 50
    assert packet["microstructure_reaction_bid_replenishment_score"] == 50
    assert (
        packet["microstructure_reaction_entry_reaction_quality"] == "neutral_unusable"
    )


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
    assert fields["quote_stale_threshold_ms"] == 3000
    assert fields["quote_stale"] is False


def test_extract_scalping_feature_packet_uses_pre_ai_quote_freshness_window():
    now = datetime(2026, 5, 15, 9, 0, 12)
    ws_data = {
        **_sample_ws_data(),
        "last_ws_update_ts": (now - timedelta(milliseconds=2500)).timestamp(),
    }

    packet = extract_scalping_feature_packet(
        ws_data,
        _sample_ticks(),
        _sample_candles(),
        now=now,
    )

    assert SCALP_FEATURE_PACKET_QUOTE_STALE_MS == 3000
    assert packet["quote_age_ms"] == 2500
    assert packet["quote_stale_threshold_ms"] == 3000
    assert packet["quote_stale"] is False


def test_extract_scalping_feature_packet_uses_runtime_quote_freshness_window():
    now = datetime(2026, 5, 15, 9, 0, 12)
    ws_data = {
        **_sample_ws_data(),
        "last_ws_update_ts": (now - timedelta(milliseconds=2500)).timestamp(),
        "ai_quote_stale_max_ms": 2000,
    }

    packet = extract_scalping_feature_packet(
        ws_data,
        _sample_ticks(),
        _sample_candles(),
        now=now,
    )

    assert packet["quote_age_ms"] == 2500
    assert packet["quote_stale_threshold_ms"] == 2000
    assert packet["quote_stale"] is True


def test_extract_scalping_feature_packet_clamps_invalid_runtime_quote_window():
    now = datetime(2026, 5, 15, 9, 0, 12)
    ws_data = {
        **_sample_ws_data(),
        "last_ws_update_ts": (now - timedelta(milliseconds=2)).timestamp(),
        "ai_quote_stale_max_ms": -100,
    }

    packet = extract_scalping_feature_packet(
        ws_data,
        _sample_ticks(),
        _sample_candles(),
        now=now,
    )

    assert packet["quote_stale_threshold_ms"] == 1
    assert packet["quote_stale"] is True


def test_extract_scalping_feature_packet_marks_quote_stale_after_pre_ai_window():
    now = datetime(2026, 5, 15, 9, 0, 12)
    ws_data = {
        **_sample_ws_data(),
        "last_ws_update_ts": (now - timedelta(milliseconds=3500)).timestamp(),
    }

    packet = extract_scalping_feature_packet(
        ws_data,
        _sample_ticks(),
        _sample_candles(),
        now=now,
    )

    assert packet["quote_age_ms"] == 3500
    assert packet["quote_stale"] is True


def test_extract_scalping_feature_packet_treats_same_second_ticks_as_burst():
    ticks = [
        {
            "time": "09:00:10",
            "price": 10100,
            "volume": 220,
            "dir": "BUY",
            "strength": 135.0,
        },
        {
            "time": "09:00:10",
            "price": 10100,
            "volume": 180,
            "dir": "BUY",
            "strength": 133.0,
        },
        {
            "time": "09:00:10",
            "price": 10100,
            "volume": 160,
            "dir": "BUY",
            "strength": 131.0,
        },
        {
            "time": "09:00:10",
            "price": 10095,
            "volume": 100,
            "dir": "SELL",
            "strength": 125.0,
        },
        {
            "time": "09:00:10",
            "price": 10095,
            "volume": 90,
            "dir": "BUY",
            "strength": 122.0,
        },
        {
            "time": "09:00:07",
            "price": 10090,
            "volume": 95,
            "dir": "BUY",
            "strength": 120.0,
        },
        {
            "time": "09:00:05",
            "price": 10090,
            "volume": 80,
            "dir": "SELL",
            "strength": 119.0,
        },
        {
            "time": "09:00:03",
            "price": 10085,
            "volume": 70,
            "dir": "BUY",
            "strength": 118.0,
        },
        {
            "time": "09:00:01",
            "price": 10085,
            "volume": 60,
            "dir": "SELL",
            "strength": 117.0,
        },
        {
            "time": "08:59:59",
            "price": 10080,
            "volume": 55,
            "dir": "BUY",
            "strength": 116.0,
        },
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

    fields = build_scalping_feature_audit_fields(packet)
    assert fields["tick_acceleration_ratio"] == packet["tick_acceleration_ratio"]
    assert fields["tick_acceleration_ratio_raw"] == 0.0


def test_openai_market_packet_includes_quant_feature_section():
    engine = GPTSniperEngine.__new__(GPTSniperEngine)

    packet = engine._format_market_data(
        _sample_ws_data(), _sample_ticks(), _sample_candles()
    )
    payload = json.loads(packet)

    assert payload["features"]["packet_version"] == SCALP_FEATURE_PACKET_VERSION
    assert "tick_acceleration_ratio" in payload["features"]
    assert "same_price_buy_absorption" in payload["features"]
    assert payload["features"]["ask_depth_ratio"] == 93.5
    assert payload["features"]["net_ask_depth"] == -4200


def test_openai_market_packet_reuses_precomputed_feature_packet(monkeypatch):
    engine = GPTSniperEngine.__new__(GPTSniperEngine)
    feature_packet = extract_scalping_feature_packet(
        _sample_ws_data(),
        _sample_ticks(),
        _sample_candles(),
        now=datetime.strptime("09:00:12", "%H:%M:%S"),
    )

    def fail_extract(*args, **kwargs):
        raise AssertionError("feature packet should not be recomputed")

    monkeypatch.setattr(openai_module, "extract_scalping_feature_packet", fail_extract)
    payload = engine._format_market_data(
        _sample_ws_data(),
        _sample_ticks(),
        _sample_candles(),
        feature_packet=feature_packet,
    )

    features = json.loads(payload)["features"]
    assert features["microstructure_reaction_context_status"] == "ok"
    assert features["microstructure_reaction_tick_aggressor_pressure_usable"] is True
    assert features["microstructure_reaction_tick_aggressor_trusted_count"] > 0


def test_openai_market_packet_tolerates_missing_orderbook():
    engine = GPTSniperEngine.__new__(GPTSniperEngine)
    ws_data = {**_sample_ws_data(), "orderbook": None}

    payload = engine._format_market_data(ws_data, _sample_ticks(), _sample_candles())
    parsed = json.loads(payload)

    assert parsed["orderbook_top3"] == {"asks": [], "bids": []}
    assert (
        parsed["features"]["microstructure_reaction_context_status"]
        == "source_quality_missing"
    )
