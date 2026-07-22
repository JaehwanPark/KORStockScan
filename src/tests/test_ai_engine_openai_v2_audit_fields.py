import threading

from src.engine.ai_engine_openai import GPTSniperEngine
from src.engine.scalping_feature_packet import SCALP_FEATURE_PACKET_VERSION


def _build_engine():
    engine = GPTSniperEngine.__new__(GPTSniperEngine)
    engine.lock = threading.Lock()
    engine.cache_lock = threading.RLock()
    engine._analysis_cache = {}
    engine._gatekeeper_cache = {}
    engine.analysis_cache_ttl = 30.0
    engine.holding_analysis_cache_ttl = 60.0
    engine.gatekeeper_cache_ttl = 30.0
    engine.ai_disabled = False
    engine.consecutive_failures = 0
    engine.max_consecutive_failures = 5
    engine.current_api_key_index = 0
    engine.last_call_time = 0.0
    engine.min_interval = 0.0
    engine.model_tier1_fast = "gpt-fast"
    engine.model_tier2_balanced = "gpt-report"
    engine.model_tier3_deep = "gpt-deep"
    engine.current_model_name = engine.model_tier1_fast
    engine.fast_model_name = engine.model_tier1_fast
    engine.report_model_name = engine.model_tier2_balanced
    engine.deep_model_name = engine.model_tier3_deep
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
        {
            "time": "09:00:10",
            "price": 10100,
            "volume": 220,
            "dir": "BUY",
            "strength": 135.0,
        },
        {
            "time": "09:00:09",
            "price": 10100,
            "volume": 180,
            "dir": "BUY",
            "strength": 133.0,
        },
        {
            "time": "09:00:08",
            "price": 10100,
            "volume": 160,
            "dir": "BUY",
            "strength": 131.0,
        },
        {
            "time": "09:00:07",
            "price": 10095,
            "volume": 100,
            "dir": "SELL",
            "strength": 125.0,
        },
        {
            "time": "09:00:06",
            "price": 10095,
            "volume": 90,
            "dir": "BUY",
            "strength": 122.0,
        },
        {
            "time": "09:00:05",
            "price": 10090,
            "volume": 95,
            "dir": "BUY",
            "strength": 120.0,
        },
        {
            "time": "09:00:00",
            "price": 10090,
            "volume": 80,
            "dir": "SELL",
            "strength": 119.0,
        },
        {
            "time": "08:59:56",
            "price": 10085,
            "volume": 70,
            "dir": "BUY",
            "strength": 118.0,
        },
        {
            "time": "08:59:52",
            "price": 10085,
            "volume": 60,
            "dir": "SELL",
            "strength": 117.0,
        },
        {
            "time": "08:59:48",
            "price": 10080,
            "volume": 55,
            "dir": "BUY",
            "strength": 116.0,
        },
    ]


def _sample_candles():
    return [
        {
            "체결시간": "08:56:00",
            "시가": 10020,
            "현재가": 10040,
            "고가": 10060,
            "저가": 10010,
            "거래량": 800,
        },
        {
            "체결시간": "08:57:00",
            "시가": 10040,
            "현재가": 10060,
            "고가": 10080,
            "저가": 10030,
            "거래량": 900,
        },
        {
            "체결시간": "08:58:00",
            "시가": 10060,
            "현재가": 10080,
            "고가": 10090,
            "저가": 10040,
            "거래량": 1000,
        },
        {
            "체결시간": "08:59:00",
            "시가": 10080,
            "현재가": 10090,
            "고가": 10120,
            "저가": 10070,
            "거래량": 1200,
        },
        {
            "체결시간": "09:00:00",
            "시가": 10090,
            "현재가": 10100,
            "고가": 10130,
            "저가": 10080,
            "거래량": 1600,
        },
    ]


def test_openai_scalping_analyze_target_returns_feature_audit_fields(monkeypatch):
    engine = _build_engine()
    used_models = []

    def _fake_call(*args, **kwargs):
        used_models.append(kwargs.get("model_override"))
        return {"action": "BUY", "score": 84, "reason": "momentum"}

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)
    monkeypatch.setattr(
        engine,
        "_apply_remote_entry_guard",
        lambda result, **kwargs: result,
    )
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
    assert result["ai_prompt_version"] == "hot_v1"
    assert result["ai_input_schema"] == "entry_screen_hot_v1"
    assert result["ai_model"] == "gpt-5.4-nano"
    assert used_models == ["gpt-5.4-nano"]
    assert result["ai_parse_ok"] is True
    assert result["ai_parse_fail"] is False
    assert result["ai_fallback_score_50"] is False
    assert result["ai_response_ms"] >= 0
    assert result["ai_result_source"] == "live"
    assert result["scalp_feature_packet_version"] == SCALP_FEATURE_PACKET_VERSION
    assert result["tick_acceleration_ratio_sent"] is True
    assert result["same_price_buy_absorption_sent"] is True
    assert result["large_sell_print_detected_sent"] is True
    assert result["ask_depth_ratio_sent"] is True
    assert result["tick_source_quality_fields_sent"] is True
    assert result["tick_sample_count"] == 10
    assert result["tick_accel_source"] == "computed_10ticks"
    assert result["tick_context_quality"] in {"fresh_computed", "stale_tick"}


def test_openai_scalping_analyze_target_returns_parse_fallback_meta(monkeypatch):
    engine = _build_engine()

    def _raise(*args, **kwargs):
        raise RuntimeError("json parse failed")

    monkeypatch.setattr(engine, "_call_openai_safe", _raise)
    result = engine.analyze_target(
        "테스트",
        _sample_ws_data(),
        _sample_ticks(),
        _sample_candles(),
        strategy="SCALPING",
        prompt_profile="watching",
    )

    assert result["action"] == "DROP"
    assert result["score"] == 0
    assert result["ai_parse_ok"] is False
    assert result["ai_parse_fail"] is True
    assert result["ai_fallback_score_50"] is False
    assert result["ai_response_ms"] >= 0
    assert result["ai_result_source"] == "exception"


def test_openai_parse_json_response_text_accepts_code_fence():
    engine = _build_engine()

    parsed = engine._parse_json_response_text("""
        ```json
        {"action":"BUY","score":81,"reason":"momentum"}
        ```
        """)

    assert parsed["action"] == "BUY"
    assert parsed["score"] == 81


def test_openai_parse_json_response_text_extracts_json_from_wrapped_text():
    engine = _build_engine()

    parsed = engine._parse_json_response_text(
        '분석 결과는 아래와 같습니다. {"action":"WAIT","score":63,"reason":"needs confirmation"} 추가 설명 끝.'
    )

    assert parsed["action"] == "WAIT"
    assert parsed["score"] == 63
