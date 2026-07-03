import threading
from types import SimpleNamespace
from dataclasses import replace

from src.engine import ai_engine_openai as ai_engine_openai_module
from src.engine.ai_prompt_contracts import (
    REALTIME_ANALYSIS_PROMPT_SCALP,
    REALTIME_ANALYSIS_PROMPT_SWING,
    SCALPING_BUY_RECOVERY_CANARY_PROMPT,
    SCALPING_ENTRY_PRICE_PROMPT,
    SCALPING_HOLDING_FLOW_SYSTEM_PROMPT,
    SCALPING_HOLDING_SYSTEM_PROMPT,
    SCALPING_OVERNIGHT_DECISION_PROMPT,
    SCALPING_SYSTEM_PROMPT,
    SCALPING_SYSTEM_PROMPT_75_CANARY,
    SCALPING_WATCHING_SYSTEM_PROMPT,
    SWING_SYSTEM_PROMPT,
)
from src.engine.ai_response_contracts import normalize_ai_reason_language
from src.engine.ai_response_contracts import normalize_gatekeeper_action_key, display_gatekeeper_action_label
from src.engine.ai_engine_openai import GPTSniperEngine


def _build_engine():
    engine = GPTSniperEngine.__new__(GPTSniperEngine)
    engine.lock = threading.Lock()
    engine.cache_lock = threading.RLock()
    engine._analysis_cache = {}
    engine._gatekeeper_cache = {}
    engine._analysis_cache_last_signatures = {}
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


def _has_hangul(text: str) -> bool:
    return any("\uac00" <= char <= "\ud7a3" for char in text)


def _build_provider_engine(engine_cls):
    engine = engine_cls.__new__(engine_cls)
    engine.lock = threading.Lock()
    engine.cache_lock = threading.RLock()
    engine._analysis_cache = {}
    engine._gatekeeper_cache = {}
    engine._analysis_cache_last_signatures = {}
    engine.analysis_cache_ttl = 30.0
    engine.holding_analysis_cache_ttl = 60.0
    engine.gatekeeper_cache_ttl = 30.0
    engine.ai_disabled = False
    engine.last_call_time = 0
    engine.min_interval = 0.0
    engine.consecutive_failures = 0
    engine.max_consecutive_failures = 1
    engine.current_api_key_index = 0
    engine.model_tier1_fast = "tier1-model"
    engine.model_tier2_balanced = "tier2-model"
    engine.model_tier3_deep = "tier3-model"
    engine.current_model_name = engine.model_tier1_fast
    return engine


def test_pullback_wait_prompt_requires_explicit_reentry_condition():
    assert "WAIT is not the default" in SWING_SYSTEM_PROMPT
    assert "If there is no explicit wait condition" in SWING_SYSTEM_PROMPT
    assert "`[눌림 대기]` is not a safe default answer" in REALTIME_ANALYSIS_PROMPT_SCALP
    assert "`[눌림 대기]` is not the default hold answer" in REALTIME_ANALYSIS_PROMPT_SWING
    assert "If the wait condition cannot be derived from the input, choose `[전량 회피]`" in REALTIME_ANALYSIS_PROMPT_SWING


def test_holding_flow_prompt_includes_consistency_rule_and_history_reason():
    engine = _build_engine()

    context = engine._format_scalping_holding_flow_context(
        "테스트",
        "005930",
        {"curr": 10000, "v_pw": 120, "buy_ratio": 55},
        [{"price": 10000, "volume": 10, "side": "BUY"}],
        [{"close": 10000, "high": 10020, "low": 9980, "volume": 1200}],
        {"profit_rate": 0.2, "peak_profit": 0.5, "held_sec": 80, "current_ai_score": 50},
        flow_history=[
            {
                "time": "10:01:02",
                "action": "HOLD",
                "flow_state": "흡수",
                "profit_rate": "+0.20",
                "exit_rule": "soft_stop",
                "reason": "매수 흡수 유지",
            }
        ],
    )

    assert "To reverse the previous flow-review action" in SCALPING_HOLDING_FLOW_SYSTEM_PROMPT
    assert "If a system guard applies" in SCALPING_HOLDING_FLOW_SYSTEM_PROMPT
    assert "state=absorption" in context
    assert "reason=매수 흡수 유지" in context


def test_holding_flow_state_normalizer_accepts_legacy_korean_and_new_english_labels():
    engine = _build_engine()

    assert engine._normalize_flow_state_label("흡수") == "absorption"
    assert engine._normalize_flow_state_label("회복") == "recovery"
    assert engine._normalize_flow_state_label("breakdown") == "breakdown"
    assert engine._normalize_flow_state_label("sideways") == "quiet"

    result = engine._normalize_holding_flow_result(
        {
            "action": "TRIM",
            "score": 67,
            "flow_state": "회복",
            "thesis": "legacy korean label",
            "evidence": ["ok"],
            "reason": "ok",
            "next_review_sec": 44,
        }
    )

    assert result["flow_state"] == "recovery"
    assert result["raw_flow_state"] == "회복"


def test_gatekeeper_action_normalizer_accepts_korean_and_english_labels():
    assert normalize_gatekeeper_action_key("눌림 대기") == "pullback_wait"
    assert normalize_gatekeeper_action_key("눌림|대기") == "pullback_wait"
    assert normalize_gatekeeper_action_key("pullback_wait") == "pullback_wait"
    assert normalize_gatekeeper_action_key("전량 회피") == "full_avoid"
    assert normalize_gatekeeper_action_key("full avoid") == "full_avoid"
    assert normalize_gatekeeper_action_key("즉시 매수") == "immediate_buy"
    assert normalize_gatekeeper_action_key("NOT_EVALUATED_SCORE_VPW_PRIOR") == "not_evaluated_score_vpw_prior"
    assert normalize_gatekeeper_action_key("None") == "unknown"
    assert normalize_gatekeeper_action_key("ambiguous_chase") == "unknown"
    assert display_gatekeeper_action_label("pullback_wait") == "눌림 대기"
    assert display_gatekeeper_action_label("not_evaluated_score_vpw_prior") == "NOT_EVALUATED_SCORE_VPW_PRIOR"


PROVIDER_ENGINES = [
    (GPTSniperEngine, ai_engine_openai_module, "_call_openai_safe"),
]


def _holding_matrix_runtime_context(cache_token: str) -> dict:
    return {
        "applied": True,
        "status": "advisory_prompt_applied",
        "cohort": "candidate",
        "cache_token": cache_token,
        "prompt_context": "[ADM Advisory Context]\n- matrix_version: matrix_v1",
        "fields": {
            "holding_exit_matrix_feature_enabled": True,
            "holding_exit_matrix_applied": True,
            "holding_exit_matrix_status": "advisory_prompt_applied",
            "holding_exit_matrix_cohort": "candidate",
            "holding_exit_matrix_version": "matrix_v1",
            "holding_exit_matrix_source_date": "2026-05-07",
            "holding_exit_matrix_valid_for_date": "next_preopen",
            "holding_exit_matrix_application_mode": "observe_only_until_owner_approval",
            "holding_exit_matrix_loaded_from": "/tmp/matrix.json",
            "holding_exit_matrix_cache_token": cache_token,
            "holding_exit_matrix_price_bucket": "price_10k_30k",
            "holding_exit_matrix_volume_bucket": "volume_500k_2m",
            "holding_exit_matrix_time_bucket": "time_0930_1030",
            "holding_exit_matrix_recommended_biases": "no_clear_edge,no_clear_edge,no_clear_edge",
            "holding_exit_matrix_policy_hints": "candidate_weight_source,candidate_weight_source,candidate_weight_source",
        },
        "matched_entries": [
            {"axis": "price_bucket", "recommended_bias": "no_clear_edge"},
            {"axis": "volume_bucket", "recommended_bias": "no_clear_edge"},
            {"axis": "time_bucket", "recommended_bias": "no_clear_edge"},
        ],
    }


def test_analyze_target_uses_short_ttl_cache(monkeypatch):
    engine = _build_engine()
    call_count = {"value": 0}

    monkeypatch.setattr(engine, "_format_market_data", lambda ws, ticks, candles: "packet")

    def _fake_call(*args, **kwargs):
        call_count["value"] += 1
        return {"action": "BUY", "score": 88, "reason": "strong"}

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)

    ws_data = {"curr": 10000, "fluctuation": 2.1, "orderbook": {"asks": [], "bids": []}}
    recent_ticks = [{"time": "10:00:00", "price": 10000, "volume": 10, "dir": "BUY"}]
    recent_candles = [{"체결시간": "10:00:00", "현재가": 10000, "거래량": 100}]

    first = engine.analyze_target("테스트", ws_data, recent_ticks, recent_candles, strategy="SCALPING")
    second = engine.analyze_target("테스트", ws_data, recent_ticks, recent_candles, strategy="SCALPING")

    assert call_count["value"] == 1
    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert second["action"] == first["action"]
    assert first["ai_model"] == "tier1-model"


def test_holding_cache_provenance_reports_changed_bucket(monkeypatch):
    engine = _build_engine()
    call_count = {"value": 0}

    monkeypatch.setattr(engine, "_format_market_data", lambda ws, ticks, candles: "packet")

    def _fake_call(*args, **kwargs):
        call_count["value"] += 1
        return {"action": "HOLD", "score": 70, "reason": "hold"}

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)

    ws_data = {
        "curr": 10000,
        "fluctuation": 1.0,
        "v_pw": 120,
        "buy_ratio": 55,
        "orderbook": {"asks": [{"price": 10010, "volume": 100}], "bids": [{"price": 10000, "volume": 100}]},
    }
    recent_ticks = [{"time": "10:00:00", "price": 10000, "volume": 100, "dir": "BUY"}]
    recent_candles = [{"체결시간": "10:00:00", "현재가": 10000, "고가": 10020, "저가": 9980, "거래량": 1000}]

    first = engine.analyze_target(
        "테스트",
        ws_data,
        recent_ticks,
        recent_candles,
        strategy="SCALPING",
        cache_profile="holding",
        prompt_profile="holding",
    )
    changed = dict(ws_data)
    changed["curr"] = 10150
    second = engine.analyze_target(
        "테스트",
        changed,
        recent_ticks,
        recent_candles,
        strategy="SCALPING",
        cache_profile="holding",
        prompt_profile="holding",
    )

    assert call_count["value"] == 2
    assert first["cache_hit"] is False
    assert second["cache_hit"] is False
    assert first["ai_prompt_type"] == "scalping_holding"


def test_analyze_target_cache_ignores_transient_market_timestamps(monkeypatch):
    engine = _build_engine()
    call_count = {"value": 0}

    monkeypatch.setattr(engine, "_format_market_data", lambda ws, ticks, candles: "packet")

    def _fake_call(*args, **kwargs):
        call_count["value"] += 1
        return {"action": "WAIT", "score": 61, "reason": "stable"}

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)

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

    def _fake_report_payload(*args, **kwargs):
        call_count["value"] += 1
        return {
            "report": "[즉시 매수]\n수급 양호",
            "selected_mode": "SWING",
            "lock_wait_ms": 0,
            "packet_build_ms": 0,
            "model_call_ms": 0,
            "total_ms": 0,
            "error": "",
        }

    monkeypatch.setattr(engine, "_generate_realtime_report_payload", _fake_report_payload)

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
    assert second["action_key"] == "immediate_buy"


def test_gatekeeper_cache_absorbs_small_context_noise(monkeypatch):
    engine = _build_engine()
    call_count = {"value": 0}

    def _fake_report_payload(*args, **kwargs):
        call_count["value"] += 1
        return {
            "report": "[눌림 대기]\n미세 변동",
            "selected_mode": "SWING",
            "lock_wait_ms": 0,
            "packet_build_ms": 0,
            "model_call_ms": 0,
            "total_ms": 0,
            "error": "",
        }

    monkeypatch.setattr(engine, "_generate_realtime_report_payload", _fake_report_payload)

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
    assert second["action_key"] == "pullback_wait"


def test_holding_cache_profile_absorbs_micro_market_noise(monkeypatch):
    engine = _build_engine()
    call_count = {"value": 0}

    monkeypatch.setattr(engine, "_format_market_data", lambda ws, ticks, candles: "packet")

    def _fake_call(*args, **kwargs):
        call_count["value"] += 1
        return {"action": "WAIT", "score": 58, "reason": "holding-stable"}

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)

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
    assert "75-100 BUY" in SCALPING_SYSTEM_PROMPT_75_CANARY
    assert "50-74 WAIT" in SCALPING_SYSTEM_PROMPT_75_CANARY


def test_scalping_buy_recovery_prompt_mentions_recovery_band():
    assert "WAIT 65-79 candidates" in SCALPING_BUY_RECOVERY_CANARY_PROMPT
    assert "75-100 BUY" in SCALPING_BUY_RECOVERY_CANARY_PROMPT
    assert "50-74 WAIT" in SCALPING_BUY_RECOVERY_CANARY_PROMPT


def test_analyze_target_shadow_prompt_uses_shadow_prompt_type(monkeypatch):
    engine = _build_engine()

    monkeypatch.setattr(engine, "_format_market_data", lambda ws, ticks, candles: "packet")
    monkeypatch.setattr(
        engine,
        "_call_openai_safe",
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


def test_analyze_target_shadow_prompt_skips_when_engine_disabled(monkeypatch):
    engine = _build_engine()
    engine.ai_disabled = True
    called = {"value": False}

    monkeypatch.setattr(engine, "_format_market_data", lambda ws, ticks, candles: "packet")

    def _fake_call(*args, **kwargs):
        called["value"] = True
        return {"action": "BUY", "score": 77, "reason": "should-not-call"}

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)

    result = engine.analyze_target_shadow_prompt(
        "테스트",
        {"curr": 10000, "fluctuation": 2.1, "orderbook": {"asks": [], "bids": []}},
        [{"time": "10:00:00", "price": 10000, "volume": 10, "dir": "BUY"}],
        [{"체결시간": "10:00:00", "현재가": 10000, "거래량": 100}],
        strategy="SCALPING",
    )

    assert called["value"] is False
    assert result["ai_result_source"] == "shadow_engine_disabled"


def test_analyze_target_shadow_prompt_honors_prompt_override(monkeypatch):
    engine = _build_engine()
    used_prompt = {"value": None}

    monkeypatch.setattr(engine, "_format_market_data", lambda ws, ticks, candles: "packet")

    def _fake_call(prompt, *args, **kwargs):
        used_prompt["value"] = prompt
        return {"action": "WAIT", "score": 68, "reason": "recovery-check"}

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)

    engine.analyze_target_shadow_prompt(
        "테스트",
        {"curr": 10000, "fluctuation": 2.1, "orderbook": {"asks": [], "bids": []}},
        [{"time": "10:00:00", "price": 10000, "volume": 10, "dir": "BUY"}],
        [{"체결시간": "10:00:00", "현재가": 10000, "거래량": 100}],
        strategy="SCALPING",
        prompt_override=SCALPING_BUY_RECOVERY_CANARY_PROMPT,
        prompt_type="scalping_buy_recovery_canary",
        cache_profile="watching_buy_recovery_canary",
    )

    assert used_prompt["value"] == SCALPING_BUY_RECOVERY_CANARY_PROMPT


def test_tier2_surfaces_do_not_advance_analyze_target_cooldown(monkeypatch):
    engine = _build_engine()
    engine.last_call_time = 1234.5

    def _fake_call(*args, **kwargs):
        schema_name = kwargs.get("schema_name")
        if schema_name == "entry_price_v1":
            return {
                "action": "USE_REFERENCE",
                "order_price": 10000,
                "confidence": 80,
                "reason": "price ok",
                "max_wait_sec": 10,
            }
        if schema_name == "holding_exit_flow_v1":
            return {
                "action": "HOLD",
                "score": 70,
                "flow_state": "흡수",
                "thesis": "flow ok",
                "evidence": ["buy pressure"],
                "reason": "hold",
                "next_review_sec": 45,
            }
        if schema_name == "overnight_v1":
            return {"action": "SELL_TODAY", "confidence": 60, "reason": "risk", "risk_note": "test"}
        return {"action": "WAIT", "score": 50, "reason": "unexpected"}

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)

    engine.evaluate_scalping_entry_price(
        "테스트",
        "005930",
        {"curr": 10000},
        [{"price": 10000, "volume": 10}],
        [{"close": 10000}],
        {"resolved_order_price": 9900},
    )
    engine.evaluate_scalping_holding_flow(
        "테스트",
        "005930",
        {"curr": 10000, "v_pw": 130, "buy_ratio": 60},
        [{"price": 10000, "volume": 10, "side": "BUY"}],
        [{"close": 10000, "high": 10020, "low": 9980, "volume": 1200}],
        {"profit_rate": 0.2, "peak_profit": 0.5, "held_sec": 80, "current_ai_score": 50},
    )
    engine.evaluate_scalping_overnight_decision(
        "테스트",
        "005930",
        {"curr_price": 10000, "avg_price": 9900, "pnl_pct": 0.7},
    )

    assert engine.last_call_time == 1234.5
    assert engine.consecutive_failures == 0


def test_analyze_target_routes_scalping_and_swing_to_expected_tiers(monkeypatch):
    engine = _build_engine()
    used_models = []

    monkeypatch.setattr(engine, "_format_market_data", lambda ws, ticks, candles: "scalp-packet")
    monkeypatch.setattr(engine, "_format_swing_market_data", lambda ws, candles, qty: "swing-packet")

    def _fake_call(*args, **kwargs):
        used_models.append(kwargs.get("model_override"))
        return {"action": "BUY", "score": 80, "reason": "ok"}

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)
    monkeypatch.setattr(engine, "_apply_remote_entry_guard", lambda result, **kwargs: result)

    ws_data = {"curr": 10000, "fluctuation": 1.0, "orderbook": {"asks": [], "bids": []}}
    recent_ticks = [{"time": "10:00:00", "price": 10000, "volume": 10, "dir": "BUY"}]
    recent_candles = [{"체결시간": "10:00:00", "현재가": 10000, "거래량": 100}]

    engine.analyze_target("스캘프", ws_data, recent_ticks, recent_candles, strategy="SCALPING")
    engine.analyze_target("스윙", ws_data, recent_ticks, recent_candles, strategy="KOSDAQ_ML")

    assert used_models == ["tier1-model", "tier2-model"]


def test_analyze_target_routes_scalping_prompt_profiles(monkeypatch):
    engine = _build_engine()
    used_prompts = []
    used_models = []

    monkeypatch.setattr(engine, "_format_market_data", lambda ws, ticks, candles: "scalp-packet")

    def _fake_call(prompt, *args, **kwargs):
        used_prompts.append(prompt)
        used_models.append(kwargs.get("model_override"))
        return {"action": "WAIT", "score": 61, "reason": "ok"}

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)

    ws_data = {"curr": 10000, "fluctuation": 1.0, "orderbook": {"asks": [], "bids": []}}
    recent_ticks = [{"time": "10:00:00", "price": 10000, "volume": 10, "dir": "BUY"}]
    recent_candles = [{"체결시간": "10:00:00", "현재가": 10000, "거래량": 100}]

    watching = engine.analyze_target(
        "스캘프-감시",
        ws_data,
        recent_ticks,
        recent_candles,
        strategy="SCALPING",
        prompt_profile="watching",
    )
    holding = engine.analyze_target(
        "스캘프-보유",
        ws_data,
        recent_ticks,
        recent_candles,
        strategy="SCALPING",
        cache_profile="holding",
        prompt_profile="holding",
    )
    exiting = engine.analyze_target(
        "스캘프-청산",
        ws_data,
        recent_ticks,
        recent_candles,
        strategy="SCALPING",
        cache_profile="holding",
        prompt_profile="exit",
    )
    shared = engine.analyze_target(
        "스캘프-공용",
        ws_data,
        recent_ticks,
        recent_candles,
        strategy="SCALPING",
        prompt_profile="shared",
    )

    assert used_prompts == [
        SCALPING_WATCHING_SYSTEM_PROMPT,
        SCALPING_HOLDING_SYSTEM_PROMPT,
        SCALPING_HOLDING_SYSTEM_PROMPT,
        SCALPING_SYSTEM_PROMPT,
    ]
    assert used_models == ["tier1-model", "tier1-model", "tier1-model", "tier1-model"]
    assert watching["ai_prompt_type"] == "scalping_entry"
    assert holding["ai_prompt_type"] == "scalping_holding"
    assert exiting["ai_prompt_type"] == "scalping_holding"
    assert shared["ai_prompt_type"] == "scalping_shared"
    assert watching["ai_model"] == "tier1-model"
    assert exiting["ai_model"] == "tier1-model"
    assert watching["ai_prompt_version"] == "split_v2"


def test_analyze_target_holding_exit_action_schema_compat(monkeypatch):
    engine = _build_engine()
    monkeypatch.setattr(engine, "_format_market_data", lambda ws, ticks, candles: "scalp-packet")
    monkeypatch.setattr(
        engine,
        "_call_openai_safe",
        lambda *args, **kwargs: {"action": "EXIT", "score": 31, "reason": "risk"},
    )

    result = engine.analyze_target(
        "스캘프-보유",
        {"curr": 10000, "fluctuation": 1.0, "orderbook": {"asks": [], "bids": []}},
        [{"time": "10:00:00", "price": 10000, "volume": 10, "dir": "BUY"}],
        [{"체결시간": "10:00:00", "현재가": 10000, "거래량": 100}],
        strategy="SCALPING",
        prompt_profile="holding",
    )

    assert result["ai_prompt_type"] == "scalping_holding"
    assert result["action_v2"] == "EXIT"
    assert result["action"] == "DROP"
    assert result["action_schema"] == "holding_exit_v1"
    assert "entry_adm_bucket_token" not in result
    assert "entry_adm_status" not in result


def test_scalping_reason_language_contract_replaces_non_ascii_reason():
    engine = _build_provider_engine(GPTSniperEngine)

    result = engine._normalize_scalping_action_schema(
        {"action": "WAIT", "score": 66, "reason": "ทั้ง curr_vs_ma5_bp positive"},
        prompt_type="scalping_entry",
    )

    assert result["reason"] == "Reason unavailable: non-English output from AI"
    assert result["ai_reason_language_policy"] == "english_ascii_only"
    assert result["ai_reason_language_violation"] is True


def test_scalping_reason_language_contract_keeps_english_reason():
    result = normalize_ai_reason_language("curr_vs_ma5_bp positive but liquidity weak", max_len=120)

    assert result["reason"] == "curr_vs_ma5_bp positive but liquidity weak"
    assert result["ai_reason_language_violation"] is False


def test_scalping_prompts_require_english_ascii_reason():
    for prompt in (
        SCALPING_SYSTEM_PROMPT,
        SCALPING_WATCHING_SYSTEM_PROMPT,
        SCALPING_HOLDING_SYSTEM_PROMPT,
        SCALPING_HOLDING_FLOW_SYSTEM_PROMPT,
        SCALPING_ENTRY_PRICE_PROMPT,
        SCALPING_OVERNIGHT_DECISION_PROMPT,
    ):
        assert "English ASCII only" in prompt


def test_internal_json_classifier_prompts_use_english_instruction_text():
    for prompt in (
        SCALPING_ENTRY_PRICE_PROMPT,
        SCALPING_HOLDING_SYSTEM_PROMPT,
        SCALPING_HOLDING_FLOW_SYSTEM_PROMPT,
        SCALPING_OVERNIGHT_DECISION_PROMPT,
    ):
        assert "Return JSON only" in prompt
        assert "반드시 JSON" not in prompt
        assert "너는" not in prompt
        assert "판정 규칙" not in prompt
        assert not _has_hangul(prompt)

    assert "pre-submit scalping order-price classifier" in SCALPING_ENTRY_PRICE_PROMPT
    assert "low-latency scalping position-state classifier" in SCALPING_HOLDING_SYSTEM_PROMPT
    assert "scalping holding/overnight flow classifier" in SCALPING_HOLDING_FLOW_SYSTEM_PROMPT
    assert "absorption, recovery, distribution, breakdown, quiet" in SCALPING_HOLDING_FLOW_SYSTEM_PROMPT


def test_stage_prompts_keep_decision_scope_separated():
    assert "Do not decide order price, quantity, holding, or exit." in SCALPING_SYSTEM_PROMPT
    assert "Do not decide order price, quantity, holding, or exit." in SCALPING_WATCHING_SYSTEM_PROMPT
    assert "Do not re-decide BUY vs WAIT." in SCALPING_ENTRY_PRICE_PROMPT
    assert "Do not change entry, order price, provider route, quantity, or hard guard policy." in (
        SCALPING_HOLDING_FLOW_SYSTEM_PROMPT
    )


def test_swing_tier2_analyze_target_input_labels_are_english_ascii():
    engine = _build_engine()
    candles = [
        {"체결시간": f"10:{idx:02d}:00", "현재가": 10000 + idx, "거래량": 1000 + idx}
        for idx in range(20)
    ]

    payload = engine._format_swing_market_data(
        {"curr": 10030, "fluctuation": 1.2, "v_pw": 132, "volume": 100000},
        candles,
        program_net_qty=5000,
    )

    assert "[CURRENT_STATE_SWING_VIEW]" in payload
    assert "program_flow: net_buy" in payload
    assert not _has_hangul(payload)


def test_dual_shadow_prompts_use_functional_english_reviewers():
    for prompt in (
        ai_engine_openai_module.DUAL_PERSONA_AGGRESSIVE_PROMPT,
        ai_engine_openai_module.DUAL_PERSONA_CONSERVATIVE_PROMPT,
    ):
        assert "Return JSON only" in prompt
        assert "quantitative reviewer" in prompt
        assert "concise English ASCII only" in prompt
        assert "너는" not in prompt
        assert "반드시 JSON" not in prompt

    assert "opportunity-side quantitative reviewer" in ai_engine_openai_module.DUAL_PERSONA_AGGRESSIVE_PROMPT
    assert "risk-side quantitative reviewer" in ai_engine_openai_module.DUAL_PERSONA_CONSERVATIVE_PROMPT


def test_overnight_prompt_is_internal_english_schema_first_classifier():
    assert "pre-close scalping overnight risk classifier" in SCALPING_OVERNIGHT_DECISION_PROMPT
    assert "Default action is SELL_TODAY" in SCALPING_OVERNIGHT_DECISION_PROMPT
    assert "HOLD_OVERNIGHT is a strict exception" in SCALPING_OVERNIGHT_DECISION_PROMPT
    assert "stale, missing, insufficient, or mixed" in SCALPING_OVERNIGHT_DECISION_PROMPT
    assert "one concise overnight decision rationale" in SCALPING_OVERNIGHT_DECISION_PROMPT
    assert "one concise main risk" in SCALPING_OVERNIGHT_DECISION_PROMPT
    assert "15년" not in SCALPING_OVERNIGHT_DECISION_PROMPT
    assert "베테랑" not in SCALPING_OVERNIGHT_DECISION_PROMPT
    assert "판단 근거" not in SCALPING_OVERNIGHT_DECISION_PROMPT


def test_analyze_target_uses_shared_prompt_when_split_disabled(monkeypatch):
    engine = _build_engine()
    used_prompts = []
    disabled_rules = replace(ai_engine_openai_module.TRADING_RULES, SCALPING_PROMPT_SPLIT_ENABLED=False)
    monkeypatch.setattr(ai_engine_openai_module, "TRADING_RULES", disabled_rules)
    monkeypatch.setattr(engine, "_format_market_data", lambda ws, ticks, candles: "scalp-packet")

    def _fake_call(prompt, *args, **kwargs):
        used_prompts.append(prompt)
        return {"action": "WAIT", "score": 55, "reason": "ok"}

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)

    result = engine.analyze_target(
        "스캘프-보유",
        {"curr": 10000, "fluctuation": 1.0, "orderbook": {"asks": [], "bids": []}},
        [{"time": "10:00:00", "price": 10000, "volume": 10, "dir": "BUY"}],
        [{"체결시간": "10:00:00", "현재가": 10000, "거래량": 100}],
        strategy="SCALPING",
        prompt_profile="holding",
    )

    assert used_prompts == [SCALPING_SYSTEM_PROMPT]
    assert result["ai_prompt_type"] == "scalping_shared"
    assert result["ai_prompt_version"] == "split_disabled_v1"


def test_condition_entry_and_exit_reuse_scalping_routes(monkeypatch):
    engine = _build_engine()
    used_models = []
    used_prompts = []
    used_schemas = []

    monkeypatch.setattr(engine, "_format_market_data", lambda ws, ticks, candles: "condition-packet")

    def _fake_call(prompt, *args, **kwargs):
        used_prompts.append(prompt)
        used_models.append(kwargs.get("model_override"))
        used_schemas.append(kwargs.get("schema_name"))
        if kwargs.get("schema_name") == "entry_v1":
            return {"action": "BUY", "score": 88, "reason": "entry flow"}
        return {"action": "TRIM", "score": 77, "reason": "exit flow"}

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)
    monkeypatch.setattr(engine, "_apply_remote_entry_guard", lambda result, **kwargs: result)

    ws_data = {"curr": 10000, "fluctuation": 1.0, "orderbook": {"asks": [], "bids": []}}
    recent_ticks = [{"time": "10:00:00", "price": 10000, "volume": 10, "dir": "BUY"}]
    recent_candles = [{"체결시간": "10:00:00", "현재가": 10000, "거래량": 100}]
    profile = {"name": "VCP", "strategy": "SCALPING"}

    entry = engine.evaluate_condition_entry("조건주", "000001", ws_data, recent_ticks, recent_candles, profile)
    exit_result = engine.evaluate_condition_exit("조건주", "000001", ws_data, recent_ticks, recent_candles, profile, 1.2, 2.1, 78)

    assert used_models == ["tier1-model", "tier1-model"]
    assert used_prompts == [SCALPING_WATCHING_SYSTEM_PROMPT, SCALPING_HOLDING_SYSTEM_PROMPT]
    assert used_schemas == ["entry_v1", "holding_exit_v1"]
    assert entry["decision"] == "BUY"
    assert entry["confidence"] == 88
    assert exit_result["decision"] == "TRIM"
    assert exit_result["trim_ratio"] == 0.5


def test_provider_cache_profile_separates_non_holding_keys():
    ws_data = {"curr": 10000, "fluctuation": 1.0, "orderbook": {"asks": [], "bids": []}}
    recent_ticks = [{"time": "10:00:00", "price": 10000, "volume": 10, "dir": "BUY"}]
    recent_candles = [{"체결시간": "10:00:00", "현재가": 10000, "거래량": 100}]

    for engine_cls, _, _ in PROVIDER_ENGINES:
        engine = _build_provider_engine(engine_cls)
        default_key = engine._build_analysis_cache_key_with_profile(
            target_name="테스트",
            strategy="SCALPING",
            ws_data=ws_data,
            recent_ticks=recent_ticks,
            recent_candles=recent_candles,
            program_net_qty=0,
            cache_profile="default",
        )
        shadow_key = engine._build_analysis_cache_key_with_profile(
            target_name="테스트",
            strategy="SCALPING",
            ws_data=ws_data,
            recent_ticks=recent_ticks,
            recent_candles=recent_candles,
            program_net_qty=0,
            cache_profile="shadow_profile",
        )

        assert default_key != shadow_key


def test_holding_cache_tick_signature_uses_latest_touch_ticks_and_excludes_heuristic_buy():
    engine = _build_engine()

    compact = engine._compact_holding_ticks_for_cache(
        [
            {
                "time": "10:00:03",
                "price": 10100,
                "volume": 1000,
                "dir": "BUY",
                "aggressor_source": "price_change_heuristic",
            },
            {"time": "10:00:02", "price": 10090, "volume": 450, "best_bid": 10090, "best_ask": 10100},
            {"time": "10:00:01", "price": 10100, "volume": 250, "best_bid": 10090, "best_ask": 10100},
            {"time": "10:00:00", "price": 10080, "volume": 100, "dir": "BUY"},
        ]
    )

    assert compact == [
        {
            "latest_price": 202,
            "buy_volume": 3,
            "sell_volume": 4,
            "net_volume": -1,
            "trade_value": 36,
        }
    ]


def test_provider_cache_set_enforces_max_entries(monkeypatch):
    tiny_rules = SimpleNamespace(AI_RESULT_CACHE_MAX_ENTRIES=3)

    for engine_cls, module, _ in PROVIDER_ENGINES:
        monkeypatch.setattr(module, "TRADING_RULES", tiny_rules)
        engine = _build_provider_engine(engine_cls)

        for index in range(5):
            engine._cache_set("_analysis_cache", f"k{index}", {"value": index}, 30.0)

        assert len(engine._analysis_cache) == 3
        assert "k4" in engine._analysis_cache


def test_provider_holding_matrix_context_appends_prompt_and_tags_result(monkeypatch):
    ws_data = {"curr": 10000, "fluctuation": 1.0, "orderbook": {"asks": [], "bids": []}}
    recent_ticks = [{"time": "10:00:00", "price": 10000, "volume": 10, "dir": "BUY"}]
    recent_candles = [{"체결시간": "10:00:00", "현재가": 10000, "거래량": 100}]

    for engine_cls, module, call_name in PROVIDER_ENGINES:
        engine = _build_provider_engine(engine_cls)
        seen_inputs = []

        monkeypatch.setattr(
            module,
            "build_holding_exit_matrix_runtime_context",
            lambda **kwargs: _holding_matrix_runtime_context(
                "candidate:matrix_v1:price_10k_30k:volume_500k_2m:time_0930_1030"
            ),
        )
        monkeypatch.setattr(engine, "_format_market_data", lambda ws, ticks, candles: "packet")

        def _fake_call(prompt, user_input, *args, **kwargs):
            seen_inputs.append(user_input)
            return {"action": "HOLD", "score": 70, "reason": "hold"}

        monkeypatch.setattr(engine, call_name, _fake_call)

        result = engine.analyze_target(
            "테스트",
            ws_data,
            recent_ticks,
            recent_candles,
            strategy="SCALPING",
            cache_profile="holding",
            prompt_profile="holding",
        )

        assert "[ADM Advisory Context]" in seen_inputs[0]
        assert result["holding_exit_matrix_applied"] is True
        assert result["holding_exit_matrix_version"] == "matrix_v1"
        assert result["holding_exit_matrix_cohort"] == "candidate"
        assert result["holding_exit_matrix_decision_alignment"] == "neutral_no_clear_edge"


def test_openai_analyze_target_waits_min_interval_instead_of_score50_cooldown(monkeypatch):
    engine = _build_provider_engine(GPTSniperEngine)
    engine.last_call_time = 100.0
    engine.min_interval = 0.5
    sleeps = []

    monkeypatch.setattr(ai_engine_openai_module.time, "time", lambda: 100.2)
    monkeypatch.setattr(ai_engine_openai_module.time, "sleep", lambda sec: sleeps.append(sec))
    monkeypatch.setattr(engine, "_format_market_data", lambda ws, ticks, candles: "packet")
    monkeypatch.setattr(engine, "_apply_remote_entry_guard", lambda result, **kwargs: result)

    def _fake_call(*args, **kwargs):
        return {"action": "BUY", "score": 88, "reason": "strong"}

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)

    result = engine.analyze_target(
        "테스트",
        {"curr": 10000, "fluctuation": 1.0, "orderbook": {"asks": [], "bids": []}},
        [{"time": "10:00:00", "price": 10000, "volume": 10, "dir": "BUY"}],
        [{"체결시간": "10:00:00", "현재가": 10000, "거래량": 100}],
        strategy="SCALPING",
    )

    assert len(sleeps) == 1
    assert abs(sleeps[0] - 0.3) < 1e-9
    assert result["action"] == "BUY"
    assert result["score"] == 88
    assert result["ai_result_source"] == "live"
    assert result["ai_fallback_score_50"] is False
    assert result["openai_min_interval_wait_ms"] == 300


def test_provider_holding_matrix_cache_token_separates_cache_variants(monkeypatch):
    ws_data = {"curr": 10000, "fluctuation": 1.0, "orderbook": {"asks": [], "bids": []}}
    recent_ticks = [{"time": "10:00:00", "price": 10000, "volume": 10, "dir": "BUY"}]
    recent_candles = [{"체결시간": "10:00:00", "현재가": 10000, "거래량": 100}]

    for engine_cls, module, call_name in PROVIDER_ENGINES:
        engine = _build_provider_engine(engine_cls)
        call_count = {"value": 0}
        contexts = iter(
            [
                _holding_matrix_runtime_context("candidate:matrix_v1:price_10k_30k:volume_500k_2m:time_0930_1030"),
                _holding_matrix_runtime_context("candidate:matrix_v2:price_10k_30k:volume_500k_2m:time_0930_1030"),
            ]
        )

        monkeypatch.setattr(module, "build_holding_exit_matrix_runtime_context", lambda **kwargs: next(contexts))
        monkeypatch.setattr(engine, "_format_market_data", lambda ws, ticks, candles: "packet")

        def _fake_call(*args, **kwargs):
            call_count["value"] += 1
            return {"action": "HOLD", "score": 61, "reason": "stable"}

        monkeypatch.setattr(engine, call_name, _fake_call)

        first = engine.analyze_target(
            "테스트",
            ws_data,
            recent_ticks,
            recent_candles,
            strategy="SCALPING",
            cache_profile="holding",
            prompt_profile="holding",
        )
        second = engine.analyze_target(
            "테스트",
            ws_data,
            recent_ticks,
            recent_candles,
            strategy="SCALPING",
            cache_profile="holding",
            prompt_profile="holding",
        )

        assert call_count["value"] == 2
        assert first["cache_hit"] is False
        assert second["cache_hit"] is False


def test_provider_overnight_engine_disabled_is_annotated():
    for engine_cls, _, _ in PROVIDER_ENGINES:
        engine = _build_provider_engine(engine_cls)
        engine.ai_disabled = True

        result = engine.evaluate_scalping_overnight_decision(
            "테스트",
            "000001",
            {"position_status": "HOLDING", "curr_price": 10000},
        )

        assert result["action"] == "SELL_TODAY"
        assert result["reason"] == "engine_disabled_sell_today_fallback"
        assert result["risk_note"] == "engine_disabled"
        assert result["ai_prompt_type"] == "scalping_overnight"
        assert result["ai_prompt_version"] == "overnight_v1"
        assert result["ai_result_source"] == "engine_disabled"
        assert result["ai_parse_fail"] is False


def test_provider_overnight_failure_disables_engine(monkeypatch):
    def _raise(*args, **kwargs):
        raise RuntimeError("provider down")

    for engine_cls, _, call_name in PROVIDER_ENGINES:
        engine = _build_provider_engine(engine_cls)
        monkeypatch.setattr(engine, call_name, _raise)

        result = engine.evaluate_scalping_overnight_decision(
            "테스트",
            "000001",
            {"position_status": "HOLDING", "curr_price": 10000},
        )

        assert engine.ai_disabled is True
        assert result["action"] == "SELL_TODAY"
        assert result["reason"] == "ai_failure_sell_today_fallback"
        assert result["risk_note"] == "ai_response_error_or_insufficient_context"
        assert result["ai_result_source"] == "exception"
        assert result["ai_parse_fail"] is True


def test_openai_overnight_uses_batch_timeout_profile(monkeypatch):
    monkeypatch.setattr(
        ai_engine_openai_module,
        "TRADING_RULES",
        replace(
            ai_engine_openai_module.TRADING_RULES,
            OPENAI_RESPONSES_WS_TIMEOUT_MS=700,
            OPENAI_SCANNER_REPORT_TIMEOUT_MS=15000,
            OPENAI_OVERNIGHT_TIMEOUT_MS=12000,
        ),
    )
    engine = _build_provider_engine(GPTSniperEngine)

    assert engine._get_openai_timeout_ms(endpoint_name="overnight", require_json=True) == 12000
    assert engine._get_openai_timeout_ms(endpoint_name="scanner_report", require_json=False) == 15000
    assert engine._get_openai_timeout_ms(endpoint_name="analyze_target", require_json=True) == 700


def test_openai_sim_observation_overnight_failure_does_not_disable_engine(monkeypatch):
    engine = _build_provider_engine(GPTSniperEngine)

    def _raise(*args, **kwargs):
        raise TimeoutError("Request timed out.")

    monkeypatch.setattr(engine, "_call_openai_safe", _raise)

    result = engine.evaluate_scalping_overnight_decision(
        "SIM",
        "000001",
        {
            "position_status": "SIM_HOLDING",
            "simulation_book": "scalp_ai_buy_all",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "decision_authority": "sim_observation_only",
            "curr_price": 10000,
        },
    )

    assert engine.ai_disabled is False
    assert engine.consecutive_failures == 0
    assert result["action"] == "SELL_TODAY"
    assert result["reason"] == "ai_failure_sell_today_fallback"
    assert result["risk_note"] == "ai_response_error_or_insufficient_context"
    assert result["ai_result_source"] == "exception"
    assert result["sim_observation_failure_isolated"] is True


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

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)

    engine.generate_realtime_report("리포트주", "000001", "legacy packet", analysis_mode="SWING")
    engine.evaluate_scalping_overnight_decision("오버나이트주", "000001", {"curr_price": 10000})

    assert used_models == ["tier2-model", "tier2-model"]


def test_scanner_briefing_uses_tier3_model(monkeypatch):
    engine = _build_engine()
    used_models = []

    monkeypatch.setattr(ai_engine_openai_module, "build_scanner_data_input", lambda **kwargs: "scanner-data")

    def _fake_call(*args, **kwargs):
        used_models.append(kwargs.get("model_override"))
        return "브리핑"

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)

    engine.analyze_scanner_results(100, 5, "stats", "macro")

    assert used_models == ["tier3-model"]
