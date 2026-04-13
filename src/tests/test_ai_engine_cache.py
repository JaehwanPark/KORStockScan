import threading

from src.engine import ai_engine as ai_engine_module
from src.engine.ai_engine import GeminiSniperEngine, SCALPING_SYSTEM_PROMPT_75_CANARY


def _build_engine():
    engine = GeminiSniperEngine.__new__(GeminiSniperEngine)
    engine.lock = threading.Lock()
    engine.cache_lock = threading.RLock()
    engine._analysis_cache = {}
    engine._gatekeeper_cache = {}
    engine.analysis_cache_ttl = 30.0
    engine.holding_analysis_cache_ttl = 60.0
    engine.gatekeeper_cache_ttl = 30.0
    engine.ai_disabled = False
    engine.last_call_time = 0
    engine.min_interval = 0.0
    engine.consecutive_failures = 0
    engine.max_consecutive_failures = 5
    engine.current_api_key_index = 0
    engine.model_tier1_fast = "tier1-model"
    engine.model_tier2_balanced = "tier2-model"
    engine.model_tier3_deep = "tier3-model"
    engine.current_model_name = engine.model_tier1_fast
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


def test_analyze_target_cache_ignores_transient_market_timestamps(monkeypatch):
    engine = _build_engine()
    call_count = {"value": 0}

    monkeypatch.setattr(engine, "_format_market_data", lambda ws, ticks, candles: "packet")

    def _fake_call(*args, **kwargs):
        call_count["value"] += 1
        return {"action": "WAIT", "score": 61, "reason": "stable"}

    monkeypatch.setattr(engine, "_call_gemini_safe", _fake_call)

    ws_base = {
        "curr": 57100,
        "fluctuation": 1.2,
        "v_pw": 210.0,
        "orderbook": {"asks": [], "bids": []},
    }
    ws_1 = dict(ws_base, last_ws_update_ts=1712369400.10)
    ws_2 = dict(ws_base, last_ws_update_ts=1712369400.95)

    ticks_1 = [{"time": "09:11:27", "price": 57100, "volume": 10, "dir": "BUY"}]
    ticks_2 = [{"time": "09:11:28", "price": 57100, "volume": 10, "dir": "BUY"}]
    candles_1 = [{"체결시간": "09:11:00", "현재가": 57100, "거래량": 100}]
    candles_2 = [{"체결시간": "09:11:01", "현재가": 57100, "거래량": 100}]

    first = engine.analyze_target("심텍", ws_1, ticks_1, candles_1, strategy="SCALPING")
    second = engine.analyze_target("심텍", ws_2, ticks_2, candles_2, strategy="SCALPING")

    assert call_count["value"] == 1
    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert second["score"] == 61


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


def test_gatekeeper_cache_absorbs_small_context_noise(monkeypatch):
    engine = _build_engine()
    call_count = {"value": 0}

    def _fake_report(*args, **kwargs):
        call_count["value"] += 1
        return "[눌림 대기]\n미세 변동"

    monkeypatch.setattr(engine, "generate_realtime_report", _fake_report)

    ctx_a = {
        "curr_price": 72500,
        "target_price": 73200,
        "vwap_price": 72100,
        "prev_high": 73000,
        "market_cap": 551000000000,
        "fluctuation": 1.42,
        "score": 66.1,
        "v_pw_now": 118.1,
        "buy_ratio_ws": 62.4,
        "exec_buy_ratio": 61.1,
        "prog_net_qty": 18490,
        "prog_delta_qty": 2210,
        "tick_trade_value": 28500,
        "net_buy_exec_volume": 510,
        "net_bid_depth": 11880,
        "net_ask_depth": -3420,
        "spread_tick": 1,
        "vol_ratio": 146.0,
        "today_vol": 1854321,
        "captured_at": "2026-04-03 10:00:00",
    }
    ctx_b = {
        **ctx_a,
        "curr_price": 72540,
        "target_price": 73240,
        "fluctuation": 1.55,
        "score": 68.9,
        "v_pw_now": 121.8,
        "buy_ratio_ws": 63.8,
        "exec_buy_ratio": 63.5,
        "prog_net_qty": 18999,
        "prog_delta_qty": 2390,
        "tick_trade_value": 30900,
        "net_buy_exec_volume": 690,
        "net_bid_depth": 12940,
        "net_ask_depth": -3010,
        "vol_ratio": 151.0,
        "today_vol": 1888999,
        "captured_at": "2026-04-03 10:00:11",
    }

    first = engine.evaluate_realtime_gatekeeper("테스트", "000001", ctx_a, analysis_mode="SWING")
    second = engine.evaluate_realtime_gatekeeper("테스트", "000001", ctx_b, analysis_mode="SWING")

    assert call_count["value"] == 1
    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert second["allow_entry"] is False


def test_holding_cache_profile_absorbs_micro_market_noise(monkeypatch):
    engine = _build_engine()
    call_count = {"value": 0}

    monkeypatch.setattr(engine, "_format_market_data", lambda ws, ticks, candles: "packet")

    def _fake_call(*args, **kwargs):
        call_count["value"] += 1
        return {"action": "WAIT", "score": 58, "reason": "holding-stable"}

    monkeypatch.setattr(engine, "_call_gemini_safe", _fake_call)

    ws_1 = {
        "curr": 12150,
        "fluctuation": -0.33,
        "v_pw": 102.4,
        "buy_ratio": 51.2,
        "ask_tot": 182000,
        "bid_tot": 176000,
        "net_bid_depth": 8200,
        "net_ask_depth": -6100,
        "buy_exec_volume": 2400,
        "sell_exec_volume": 2100,
        "tick_trade_value": 28100,
        "orderbook": {"asks": [{"price": 12200}], "bids": [{"price": 12150}]},
    }
    ws_2 = {
        **ws_1,
        "curr": 12160,
        "fluctuation": -0.29,
        "v_pw": 103.9,
        "buy_ratio": 52.8,
        "ask_tot": 189000,
        "bid_tot": 181000,
        "tick_trade_value": 29900,
        "orderbook": {"asks": [{"price": 12210}], "bids": [{"price": 12160}]},
    }
    ticks_1 = [
        {"time": "10:45:01", "price": 12150, "volume": 22, "dir": "BUY"},
        {"time": "10:45:02", "price": 12150, "volume": 18, "dir": "SELL"},
    ]
    ticks_2 = [
        {"time": "10:45:11", "price": 12160, "volume": 24, "dir": "BUY"},
        {"time": "10:45:12", "price": 12160, "volume": 16, "dir": "SELL"},
    ]
    candles_1 = [
        {"체결시간": "10:43:00", "현재가": 12140, "고가": 12160, "저가": 12120, "거래량": 8200},
        {"체결시간": "10:44:00", "현재가": 12150, "고가": 12170, "저가": 12130, "거래량": 9100},
        {"체결시간": "10:45:00", "현재가": 12150, "고가": 12180, "저가": 12140, "거래량": 10300},
    ]
    candles_2 = [
        {"체결시간": "10:43:30", "현재가": 12140, "고가": 12160, "저가": 12120, "거래량": 8700},
        {"체결시간": "10:44:30", "현재가": 12160, "고가": 12170, "저가": 12140, "거래량": 9500},
        {"체결시간": "10:45:30", "현재가": 12160, "고가": 12180, "저가": 12140, "거래량": 10800},
    ]

    first = engine.analyze_target(
        "씨아이에스",
        ws_1,
        ticks_1,
        candles_1,
        strategy="SCALPING",
        cache_profile="holding",
    )
    second = engine.analyze_target(
        "씨아이에스",
        ws_2,
        ticks_2,
        candles_2,
        strategy="SCALPING",
        cache_profile="holding",
    )

    assert call_count["value"] == 1
    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert second["score"] == 58


def test_scalping_prompt_75_canary_rewrites_buy_band():
    assert "75~100 (BUY)" in SCALPING_SYSTEM_PROMPT_75_CANARY
    assert "50~74 (WAIT)" in SCALPING_SYSTEM_PROMPT_75_CANARY


def test_analyze_target_shadow_prompt_uses_shadow_prompt_type(monkeypatch):
    engine = _build_engine()

    monkeypatch.setattr(engine, "_format_market_data", lambda ws, ticks, candles: "packet")
    monkeypatch.setattr(
        engine,
        "_call_gemini_safe",
        lambda *args, **kwargs: {"action": "BUY", "score": 77, "reason": "shadow-strong"},
    )

    result = engine.analyze_target_shadow_prompt(
        "테스트",
        {"curr": 10000, "fluctuation": 2.1, "orderbook": {"asks": [], "bids": []}},
        [{"time": "10:00:00", "price": 10000, "volume": 10, "dir": "BUY"}],
        [{"체결시간": "10:00:00", "현재가": 10000, "거래량": 100}],
        strategy="SCALPING",
        prompt_type="scalping_buy75_shadow",
        cache_profile="watching_prompt75_shadow",
    )

    assert result["action"] == "BUY"
    assert result["ai_prompt_type"] == "scalping_buy75_shadow"
    assert result["ai_result_source"] == "shadow_live"
    assert result["cache_hit"] is False


def test_analyze_target_routes_scalping_and_swing_to_expected_tiers(monkeypatch):
    engine = _build_engine()
    used_models = []

    monkeypatch.setattr(engine, "_format_market_data", lambda ws, ticks, candles: "scalp-packet")
    monkeypatch.setattr(engine, "_format_swing_market_data", lambda ws, candles, qty: "swing-packet")

    def _fake_call(*args, **kwargs):
        used_models.append(kwargs.get("model_override"))
        return {"action": "BUY", "score": 80, "reason": "ok"}

    monkeypatch.setattr(engine, "_call_gemini_safe", _fake_call)

    ws_data = {"curr": 10000, "fluctuation": 1.0, "orderbook": {"asks": [], "bids": []}}
    recent_ticks = [{"time": "10:00:00", "price": 10000, "volume": 10, "dir": "BUY"}]
    recent_candles = [{"체결시간": "10:00:00", "현재가": 10000, "거래량": 100}]

    engine.analyze_target("스캘프", ws_data, recent_ticks, recent_candles, strategy="SCALPING")
    engine.analyze_target("스윙", ws_data, recent_ticks, recent_candles, strategy="KOSDAQ_ML")

    assert used_models == ["tier1-model", "tier2-model"]


def test_condition_entry_and_exit_use_tier1_model(monkeypatch):
    engine = _build_engine()
    used_models = []

    monkeypatch.setattr(engine, "_format_market_data", lambda ws, ticks, candles: "condition-packet")

    def _fake_call(*args, **kwargs):
        used_models.append(kwargs.get("model_override"))
        if kwargs.get("context_name", "").startswith("COND_ENTRY"):
            return {
                "decision": "BUY",
                "confidence": 88,
                "order_type": "MARKET",
                "position_size_ratio": 0.3,
                "invalidation_price": 9800,
                "reasons": ["flow"],
                "risks": ["volatility"],
            }
        return {
            "decision": "HOLD",
            "confidence": 77,
            "trim_ratio": 0.0,
            "new_stop_price": 9700,
            "reason_primary": "trend intact",
            "warning": "",
        }

    monkeypatch.setattr(engine, "_call_gemini_safe", _fake_call)

    ws_data = {"curr": 10000, "fluctuation": 1.0, "orderbook": {"asks": [], "bids": []}}
    recent_ticks = [{"time": "10:00:00", "price": 10000, "volume": 10, "dir": "BUY"}]
    recent_candles = [{"체결시간": "10:00:00", "현재가": 10000, "거래량": 100}]
    profile = {"name": "VCP", "strategy": "SCALPING"}

    engine.evaluate_condition_entry("조건주", "000001", ws_data, recent_ticks, recent_candles, profile)
    engine.evaluate_condition_exit("조건주", "000001", ws_data, recent_ticks, recent_candles, profile, 1.2, 2.1, 78)

    assert used_models == ["tier1-model", "tier1-model"]


def test_realtime_report_and_overnight_decision_use_tier2_model(monkeypatch):
    engine = _build_engine()
    used_models = []

    monkeypatch.setattr(engine, "_get_realtime_prompt", lambda mode: f"prompt:{mode}")

    def _fake_call(*args, **kwargs):
        used_models.append(kwargs.get("model_override"))
        if kwargs.get("require_json"):
            return {
                "action": "HOLD_OVERNIGHT",
                "confidence": 81,
                "reason": "trend strong",
                "risk_note": "gap risk",
            }
        return "📍 **[한 줄 결론]**\n🎯 **[실전 행동 지침]**\n[보유 지속]"

    monkeypatch.setattr(engine, "_call_gemini_safe", _fake_call)

    engine.generate_realtime_report("리포트주", "000001", "legacy packet", analysis_mode="SWING")
    engine.evaluate_scalping_overnight_decision("오버나이트주", "000001", {"curr_price": 10000})

    assert used_models == ["tier2-model", "tier2-model"]


def test_scanner_briefing_and_eod_bundle_use_tier3_model(monkeypatch):
    engine = _build_engine()
    used_models = []

    monkeypatch.setattr(ai_engine_module, "build_scanner_data_input", lambda **kwargs: "scanner-data")

    def _fake_call(*args, **kwargs):
        used_models.append(kwargs.get("model_override"))
        if kwargs.get("context_name") == "종가베팅 TOP5 JSON":
            return {
                "market_summary": "시장 요약",
                "one_point_lesson": "원포인트",
                "top5": [
                    {
                        "rank": 1,
                        "stock_name": "테스트",
                        "stock_code": "000001",
                        "close_price": 12345,
                        "reason": "수급 양호",
                        "entry_plan": "눌림",
                        "target_price_guide": "전고점",
                        "stop_price_guide": "전일 저점",
                        "confidence": 0.91,
                    }
                ],
            }
        return "브리핑"

    monkeypatch.setattr(engine, "_call_gemini_safe", _fake_call)

    engine.analyze_scanner_results(100, 5, "stats", "macro")
    bundle = engine.generate_eod_tomorrow_bundle("candidate text")

    assert used_models == ["tier3-model", "tier3-model"]
    assert bundle["top5"][0]["stock_code"] == "000001"
