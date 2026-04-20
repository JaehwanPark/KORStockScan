import threading

from src.engine.ai_engine_openai_v2 import GPTSniperEngine
from src.engine.scalping_feature_packet import SCALP_FEATURE_PACKET_VERSION


def _build_engine():
    engine = GPTSniperEngine.__new__(GPTSniperEngine)
    engine.lock = threading.Lock()
    engine.last_call_time = 0.0
    engine.min_interval = 0.0
    engine.fast_model_name = "gpt-fast"
    engine.deep_model_name = "gpt-fast"
    return engine


def _sample_ws_data():
    return {
        "curr": 10100,
        "v_pw": 132.5,
        "fluctuation": 1.2,
        "ask_tot": 180000,
        "bid_tot": 150000,
        "net_ask_depth": -4200,
        "ask_depth_ratio": 93.5,
        "orderbook": {
            "asks": [
                {"price": 10110, "volume": 4500},
                {"price": 10120, "volume": 5500},
            ],
            "bids": [
                {"price": 10100, "volume": 3000},
                {"price": 10090, "volume": 4000},
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
        {"체결시간": "08:56:00", "시가": 10020, "현재가": 10040, "고가": 10060, "저가": 10010, "거래량": 800},
        {"체결시간": "08:57:00", "시가": 10040, "현재가": 10060, "고가": 10080, "저가": 10030, "거래량": 900},
        {"체결시간": "08:58:00", "시가": 10060, "현재가": 10080, "고가": 10090, "저가": 10040, "거래량": 1000},
        {"체결시간": "08:59:00", "시가": 10080, "현재가": 10090, "고가": 10120, "저가": 10070, "거래량": 1200},
        {"체결시간": "09:00:00", "시가": 10090, "현재가": 10100, "고가": 10130, "저가": 10080, "거래량": 1600},
    ]


def test_openai_scalping_analyze_target_returns_feature_audit_fields(monkeypatch):
    engine = _build_engine()

    monkeypatch.setattr(
        engine,
        "_call_openai_safe",
        lambda *args, **kwargs: {"action": "BUY", "score": 84, "reason": "momentum"},
    )
    monkeypatch.setattr(engine, "_should_run_deep_recheck", lambda features, result: False)
    monkeypatch.setattr(engine, "_apply_main_entry_bias_relief", lambda features, result, prompt_type: result)

    result = engine.analyze_target(
        "테스트",
        _sample_ws_data(),
        _sample_ticks(),
        _sample_candles(),
        strategy="SCALPING",
        prompt_profile="watching",
    )

    assert result["action"] == "BUY"
    assert result["ai_prompt_type"] == "scalping_entry"
    assert result["ai_prompt_version"] == "openai_v2_structured_v1"
    assert result["ai_parse_ok"] is True
    assert result["ai_parse_fail"] is False
    assert result["ai_fallback_score_50"] is False
    assert result["ai_response_ms"] >= 0
    assert result["ai_result_source"] == "openai_live"
    assert result["scalp_feature_packet_version"] == SCALP_FEATURE_PACKET_VERSION
    assert result["tick_acceleration_ratio_sent"] is True
    assert result["same_price_buy_absorption_sent"] is True
    assert result["large_sell_print_detected_sent"] is True
    assert result["ask_depth_ratio_sent"] is True


def test_openai_scalping_analyze_target_returns_parse_fallback_meta(monkeypatch):
    engine = _build_engine()

    def _raise(*args, **kwargs):
        raise RuntimeError("json parse failed")

    monkeypatch.setattr(engine, "_call_openai_safe", _raise)
    monkeypatch.setattr(engine, "_should_run_deep_recheck", lambda features, result: False)
    monkeypatch.setattr(engine, "_apply_main_entry_bias_relief", lambda features, result, prompt_type: result)

    result = engine.analyze_target(
        "테스트",
        _sample_ws_data(),
        _sample_ticks(),
        _sample_candles(),
        strategy="SCALPING",
        prompt_profile="watching",
    )

    assert result["action"] == "WAIT"
    assert result["score"] == 50
    assert result["ai_parse_ok"] is False
    assert result["ai_parse_fail"] is True
    assert result["ai_fallback_score_50"] is True
    assert result["ai_response_ms"] >= 0
    assert result["ai_result_source"] == "openai_parse_fallback"
    assert result["scalp_feature_packet_version"] == SCALP_FEATURE_PACKET_VERSION


def test_openai_parse_json_response_text_accepts_code_fence():
    engine = _build_engine()

    parsed = engine._parse_json_response_text(
        """
        ```json
        {"action":"BUY","score":81,"reason":"momentum"}
        ```
        """
    )

    assert parsed["action"] == "BUY"
    assert parsed["score"] == 81


def test_openai_parse_json_response_text_extracts_json_from_wrapped_text():
    engine = _build_engine()

    parsed = engine._parse_json_response_text(
        '분석 결과는 아래와 같습니다. {"action":"WAIT","score":63,"reason":"needs confirmation"} 추가 설명 끝.'
    )

    assert parsed["action"] == "WAIT"
    assert parsed["score"] == 63
