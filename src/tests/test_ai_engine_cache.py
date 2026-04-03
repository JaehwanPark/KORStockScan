import threading

from src.engine.ai_engine import GeminiSniperEngine


def _build_engine():
    engine = GeminiSniperEngine.__new__(GeminiSniperEngine)
    engine.lock = threading.Lock()
    engine.cache_lock = threading.RLock()
    engine._analysis_cache = {}
    engine._gatekeeper_cache = {}
    engine.analysis_cache_ttl = 30.0
    engine.gatekeeper_cache_ttl = 30.0
    engine.ai_disabled = False
    engine.last_call_time = 0
    engine.min_interval = 0.0
    engine.consecutive_failures = 0
    engine.max_consecutive_failures = 5
    engine.current_api_key_index = 0
    engine.current_model_name = "stub-model"
    return engine


def test_analyze_target_uses_short_ttl_cache(monkeypatch):
    engine = _build_engine()
    call_count = {"value": 0}

    monkeypatch.setattr(engine, "_format_market_data", lambda ws, ticks, candles: "packet")

    def _fake_call(*args, **kwargs):
        call_count["value"] += 1
        return {"action": "BUY", "score": 88, "reason": "strong"}

    monkeypatch.setattr(engine, "_call_gemini_safe", _fake_call)

    ws_data = {"curr": 10000, "fluctuation": 2.1, "orderbook": {"asks": [], "bids": []}}
    recent_ticks = [{"time": "10:00:00", "price": 10000, "volume": 10, "dir": "BUY"}]
    recent_candles = [{"체결시간": "10:00:00", "현재가": 10000, "거래량": 100}]

    first = engine.analyze_target("테스트", ws_data, recent_ticks, recent_candles, strategy="SCALPING")
    second = engine.analyze_target("테스트", ws_data, recent_ticks, recent_candles, strategy="SCALPING")

    assert call_count["value"] == 1
    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert second["action"] == "BUY"


def test_gatekeeper_cache_ignores_captured_at(monkeypatch):
    engine = _build_engine()
    call_count = {"value": 0}

    def _fake_report(*args, **kwargs):
        call_count["value"] += 1
        return "[즉시 매수]\n수급 양호"

    monkeypatch.setattr(engine, "generate_realtime_report", _fake_report)

    base_ctx = {
        "curr_price": 10100,
        "market_cap": 500000000000,
        "buy_ratio_ws": 62.0,
        "exec_buy_ratio": 61.0,
        "tick_trade_value": 21000,
        "net_buy_exec_volume": 350,
        "captured_at": "2026-04-03 10:00:00",
    }
    later_ctx = dict(base_ctx)
    later_ctx["captured_at"] = "2026-04-03 10:00:08"

    first = engine.evaluate_realtime_gatekeeper("테스트", "000001", base_ctx, analysis_mode="SWING")
    second = engine.evaluate_realtime_gatekeeper("테스트", "000001", later_ctx, analysis_mode="SWING")

    assert call_count["value"] == 1
    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert second["allow_entry"] is True
