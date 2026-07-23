import threading
import json
from datetime import datetime
from types import SimpleNamespace
from dataclasses import replace

from src.engine import ai_engine_openai as ai_engine_openai_module
from src.engine.ai_prompt_contracts import (
    REALTIME_ANALYSIS_PROMPT_SCALP,
    REALTIME_ANALYSIS_PROMPT_SWING,
    SCALPING_ENTRY_PRICE_PROMPT,
    SCALPING_HOLDING_FLOW_SYSTEM_PROMPT,
    SCALPING_HOLDING_SCORE_SYSTEM_PROMPT,
    SCALPING_HOLDING_SYSTEM_PROMPT,
    SCALPING_OVERNIGHT_DECISION_PROMPT,
    SCALPING_SYSTEM_PROMPT,
    SCALPING_WATCHING_HOT_SYSTEM_PROMPT,
    SCALPING_WATCHING_SYSTEM_PROMPT,
    SWING_SYSTEM_PROMPT,
)
from src.engine.ai_response_contracts import normalize_ai_reason_language
from src.engine.ai_response_contracts import (
    normalize_gatekeeper_action_key,
    display_gatekeeper_action_label,
)
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


def test_remote_entry_guard_ignores_untrusted_pressure_axes(monkeypatch):
    engine = _build_engine()
    monkeypatch.setattr(
        engine,
        "_extract_scalping_features",
        lambda *_args, **_kwargs: {
            "buy_pressure_10t": 95.0,
            "tick_acceleration_ratio": 1.2,
            "latest_strength": 130.0,
            "curr_vs_micro_vwap_bp": -1.0,
            "micro_vwap_available": True,
            "minute_candle_window_fresh": True,
            "minute_candle_context_quality": "fresh",
            "same_price_buy_absorption": 5,
            "large_sell_print_detected": True,
            "distance_from_day_high_pct": -1.0,
            "top3_depth_ratio": 1.0,
        },
        raising=False,
    )

    result = engine._apply_remote_entry_guard(
        {"action": "BUY", "score": 88, "reason": "raw buy"},
        prompt_type="scalping_entry",
        ws_data={},
        recent_ticks=[],
        recent_candles=[],
    )

    assert result["action"] == "BUY"
    assert result["score"] == 88
    assert "remote_buy_guard" not in result["reason"]


def test_remote_entry_guard_uses_trusted_pressure_axes(monkeypatch):
    engine = _build_engine()
    monkeypatch.setattr(
        engine,
        "_extract_scalping_features",
        lambda *_args, **_kwargs: {
            "buy_pressure_10t": 95.0,
            "tick_acceleration_ratio": 1.2,
            "latest_strength": 130.0,
            "curr_vs_micro_vwap_bp": -1.0,
            "micro_vwap_available": True,
            "minute_candle_window_fresh": True,
            "minute_candle_context_quality": "fresh",
            "same_price_buy_absorption": 5,
            "large_sell_print_detected": True,
            "distance_from_day_high_pct": -1.0,
            "top3_depth_ratio": 1.0,
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 4,
        },
        raising=False,
    )

    result = engine._apply_remote_entry_guard(
        {"action": "BUY", "score": 88, "reason": "raw buy"},
        prompt_type="scalping_entry",
        ws_data={},
        recent_ticks=[],
        recent_candles=[],
    )

    assert result["action"] == "WAIT"
    assert result["score"] == 74
    assert "remote_buy_guard" in result["reason"]


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
    assert (
        "`[눌림 대기]` is not a safe default answer" in REALTIME_ANALYSIS_PROMPT_SCALP
    )
    assert (
        "`[눌림 대기]` is not the default hold answer" in REALTIME_ANALYSIS_PROMPT_SWING
    )
    assert (
        "If the wait condition cannot be derived from the input, choose `[전량 회피]`"
        in REALTIME_ANALYSIS_PROMPT_SWING
    )


def test_holding_flow_prompt_includes_consistency_rule_and_history_reason():
    engine = _build_engine()

    context = engine._format_scalping_holding_flow_context(
        "테스트",
        "005930",
        {"curr": 10000, "v_pw": 120, "buy_ratio": 55},
        [{"price": 10000, "volume": 10, "side": "BUY"}],
        [{"close": 10000, "high": 10020, "low": 9980, "volume": 1200}],
        {
            "profit_rate": 0.2,
            "peak_profit": 0.5,
            "held_sec": 80,
            "current_ai_score": 50,
        },
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

    assert (
        "To reverse the previous flow-review action"
        in SCALPING_HOLDING_FLOW_SYSTEM_PROMPT
    )
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


def test_holding_score_v2_payload_contains_position_pnl_and_source_quality(monkeypatch):
    engine = _build_engine()
    captured = {}

    def _fake_call(prompt, user_input, **kwargs):
        captured["prompt"] = prompt
        captured["user_input"] = user_input
        captured["kwargs"] = kwargs
        engine._set_last_transport_meta(
            {
                "openai_transport_mode": "http",
                "openai_endpoint_name": "holding_score",
                "openai_schema_name": "holding_score_v2",
                "openai_total_tokens": 123,
            }
        )
        return {
            "action": "HOLD",
            "score": 82,
            "confidence": 71,
            "position_state": "continuation",
            "score_basis": "profit and flow remain supportive",
            "risk_factors": ["drawdown controlled"],
            "support_factors": ["fresh orderbook touch flow"],
            "data_quality": "fresh",
            "reason": "Continuation favored with fresh flow",
        }

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)

    ws_data = {
        "curr": 10050,
        "v_pw": 140,
        "buy_ratio": 62,
        "quote_age_ms": 100,
        "orderbook": {
            "asks": [{"price": 10060, "volume": 100}],
            "bids": [{"price": 10050, "volume": 120}],
        },
    }
    ticks = [
        {
            "time": datetime.now().strftime("%H:%M:%S"),
            "price": 10050,
            "volume": 10,
            "side": "BUY",
            "aggressor_source": "orderbook_touch",
        }
    ]
    candles = [{"현재가": 10050, "고가": 10080, "저가": 10000, "거래량": 1000}]

    result = engine.evaluate_scalping_holding_score(
        "테스트",
        "005930",
        ws_data,
        ticks,
        candles,
        {
            "record_id": "REC-1",
            "buy_price": 10000,
            "curr_price": 10050,
            "profit_rate": 0.5,
            "peak_profit": 0.8,
            "drawdown_from_peak_pct": 0.3,
            "held_sec": 75,
            "buy_qty": 1,
            "position_tag": "SCALP",
            "entry_source": "live_buy",
            "entry_time_context": {
                "entry_liquidity_score": 71,
                "fillability_score": 64,
                "order_flow_pressure_score": 58,
                "entry_momentum_score": 55,
                "entry_context_quality": "partial",
                "ai_input_source_quality_status": "evaluated",
            },
            "avg_down_count": 0,
            "pyramid_count": 0,
        },
        metadata_extra={"record_id": "REC-1"},
    )

    payload = json.loads(captured["user_input"])
    assert payload["input_schema"] == "holding_score_v2"
    assert payload["position_context"]["record_id"] == "REC-1"
    assert payload["entry_time_context"]["context_role"] == "entry_time_provenance_only"
    assert payload["entry_time_context"]["current_flow_evidence"] is False
    assert payload["entry_time_context"]["entry_liquidity_score"] == 71
    assert payload["entry_time_context"]["entry_context_quality"] == "partial"
    assert payload["pnl_context"]["drawdown_from_peak_pct"] == 0.3
    assert "market_flow_features" in payload
    assert "compact_features" in payload["market_flow_features"]
    assert "feature_packet" not in payload["market_flow_features"]
    assert "audit_fields" not in payload["market_flow_features"]
    assert "recent_ticks_latest_first" not in payload["market_flow_features"]
    assert "recent_candles_latest_window" not in payload["market_flow_features"]
    assert "source_quality" in payload
    assert payload["hard_guard_context"]["hard_guards_remain_authoritative"] is True
    assert captured["kwargs"]["schema_name"] == "holding_score_v2"
    assert captured["kwargs"]["endpoint_name"] == "holding_score"
    assert captured["kwargs"]["model_override"] == "gpt-5.4-nano"
    assert "position-state score classifier" in captured["prompt"]
    assert "Do not reuse entry logic" in SCALPING_HOLDING_SCORE_SYSTEM_PROMPT
    assert (
        "Runtime role gates decide how the score may be consumed"
        in SCALPING_HOLDING_SCORE_SYSTEM_PROMPT
    )
    assert result["holding_score_input_schema"] == "holding_score_v2"
    assert result["holding_score_data_quality"] in {"fresh", "partial"}
    assert result["holding_score_effective_usable"] is True
    assert result["holding_score_raw_source"] == "live"
    assert result["holding_score_effective_source"] == "live"
    assert result["openai_transport_mode"] == "http"
    assert result["openai_endpoint_name"] == "holding_score"
    assert result["openai_schema_name"] == "holding_score_v2"
    assert result["openai_total_tokens"] == 123
    assert result["ai_prompt_type"] == "scalping_holding_score"


def test_holding_context_is_shared_and_blocks_unsupported_continuation(monkeypatch):
    engine = _build_engine()
    captured = {}
    holding_context = {
        "schema": "holding_decision_context_v1",
        "enabled": True,
        "decision_kind": "holding_score",
        "venue": "KRX",
        "session": "krx_regular",
        "candle": {
            "bars": [{"t": "10:00", "o": 10000, "h": 10020, "l": 9990, "c": 10010}],
            "regime": "range",
            "structure": {},
        },
        "signed_tape": {"state": "missing", "sample_count": 0},
        "microstructure": {"bbo_fresh": False},
        "execution_pnl": {
            "mark_pnl_pct": 0.1,
            "executable_pnl_pct": None,
        },
        "position_lifecycle": {"memory_qty": 1},
        "order_reconciliation": {"order_or_quantity_conflict": True},
        "market_session": {"phase": "krx_regular"},
        "source_quality": {
            "status": "blocked",
            "hold_defer_allowed": False,
            "blockers": ["executable_bbo", "order_or_quantity_conflict"],
        },
        "observation_contract": {
            "metric_role": "holding_context_feature_bundle",
            "decision_authority": "bounded_holding_confirmation",
        },
    }

    def _fake_call(_prompt, user_input, **kwargs):
        captured[kwargs["endpoint_name"]] = user_input
        if kwargs["endpoint_name"] == "holding_score":
            return {
                "action": "HOLD",
                "score": 88,
                "confidence": 90,
                "position_state": "continuation",
                "score_basis": "supportive",
                "risk_factors": [],
                "support_factors": [],
                "data_quality": "fresh",
                "reason": "hold",
            }
        if kwargs["endpoint_name"] == "holding_flow":
            return {
                "action": "HOLD",
                "score": 80,
                "flow_state": "absorption",
                "thesis": "hold",
                "evidence": ["support"],
                "reason": "hold",
                "next_review_sec": 30,
            }
        return {
            "action": "HOLD_OVERNIGHT",
            "confidence": 90,
            "reason": "hold overnight",
            "risk_note": "low",
        }

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)
    ws_data = {
        "curr": 10010,
        "quote_age_ms": 100,
        "orderbook": {
            "asks": [{"price": 10020, "volume": 100}],
            "bids": [{"price": 10010, "volume": 100}],
        },
    }
    ticks = [{"price": 10010, "volume": 10, "side": "BUY"}]
    candles = [{"현재가": 10010, "고가": 10020, "저가": 9990, "거래량": 100}]
    position = {
        "buy_price": 10000,
        "buy_qty": 1,
        "profit_rate": 0.1,
        "peak_profit": 0.2,
    }

    score = engine.evaluate_scalping_holding_score(
        "테스트",
        "005930",
        ws_data,
        ticks,
        candles,
        position,
        holding_context=holding_context,
    )
    flow = engine.evaluate_scalping_holding_flow(
        "테스트",
        "005930",
        ws_data,
        ticks,
        candles,
        position,
        holding_context=holding_context,
    )
    overnight = engine.evaluate_scalping_overnight_decision(
        "테스트",
        "005930",
        {"avg_price": 10000, "curr_price": 10010, "buy_qty": 1},
        holding_context=holding_context,
    )

    assert (
        json.loads(captured["holding_score"])["holding_decision_context"]["schema"]
        == "holding_decision_context_v1"
    )
    assert "holding_decision_context_v1" in captured["holding_flow"]
    assert "holding_decision_context_v1" in captured["overnight"]
    assert score["score"] == 50
    assert score["holding_context_hold_defer_allowed"] is False
    assert flow["action"] == "HOLD"
    assert flow["holding_context_hold_defer_allowed"] is False
    assert overnight["action"] == "SELL_TODAY"
    assert overnight["holding_context_action_clamped"] is True


def test_holding_score_timeout_returns_timeout_source_with_timing_meta(monkeypatch):
    engine = _build_engine()

    def _raise_timeout(*args, **kwargs):
        raise ai_engine_openai_module.OpenAIResponsesHTTPError(
            "OpenAI Responses HTTP timeout budget exhausted: endpoint=holding_score, last_error=request timed out",
            timing_meta={
                "openai_http_provider_ms": 6900,
                "openai_http_provider_total_ms": 6900,
                "openai_http_attempt_count": 1,
                "openai_http_error_type": "TimeoutError",
                "openai_http_timeout_budget_exhausted": True,
            },
        )

    monkeypatch.setattr(engine, "_call_openai_safe", _raise_timeout)

    result = engine.evaluate_scalping_holding_score(
        "테스트",
        "005930",
        {"curr": 10050, "v_pw": 120, "orderbook": {"asks": [], "bids": []}},
        [
            {
                "time": datetime.now().strftime("%H:%M:%S"),
                "price": 10050,
                "volume": 10,
                "side": "BUY",
            }
        ],
        [{"현재가": 10050, "고가": 10080, "저가": 10000, "거래량": 1000}],
        {
            "record_id": "REC-1",
            "buy_price": 10000,
            "profit_rate": 0.5,
            "held_sec": 75,
            "buy_qty": 1,
        },
    )

    assert result["holding_score_source"] == "timeout"
    assert result["holding_score_raw_source"] == "timeout"
    assert result["holding_score_effective_usable"] is False
    assert result["holding_score_excluded_reason"] == "timeout"
    assert result["holding_score_transport_fail_closed"] is True
    assert result["holding_score_timeout_like"] is True
    assert result["openai_http_provider_ms"] == 6900
    assert result["openai_http_timeout_budget_exhausted"] is True
    assert result["ai_result_source"] == "timeout"
    assert result["ai_parse_fail"] is True


def test_holding_score_v2_payload_stays_compact_for_low_latency(monkeypatch):
    engine = _build_engine()
    captured = {}

    def _fake_call(prompt, user_input, **kwargs):
        captured["user_input"] = user_input
        return {
            "action": "HOLD",
            "score": 72,
            "confidence": 60,
            "position_state": "mixed",
            "score_basis": "mixed but stable",
            "risk_factors": ["partial source quality"],
            "support_factors": ["profit still positive"],
            "data_quality": "partial",
            "reason": "Hold neutral",
        }

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)

    ws_data = {
        "curr": 10050,
        "v_pw": 140,
        "buy_ratio": 62,
        "buy_exec_volume": 1200,
        "sell_exec_volume": 900,
        "quote_age_ms": 100,
        "orderbook": {
            "asks": [{"price": 10060, "volume": 100}, {"price": 10070, "volume": 200}],
            "bids": [{"price": 10050, "volume": 120}, {"price": 10040, "volume": 180}],
        },
    }
    ticks = [
        {
            "time": f"09:30:{idx:02d}",
            "price": 10000 + idx * 5,
            "volume": 10 + idx,
            "side": "BUY" if idx % 2 else "SELL",
            "aggressor_source": "orderbook_touch",
            "aggressor_quality": "fresh",
            "strength": 130 + idx,
        }
        for idx in range(10)
    ]
    candles = [
        {
            "time": f"09:{idx:02d}",
            "현재가": 10000 + idx * 8,
            "시가": 9990 + idx * 8,
            "고가": 10030 + idx * 8,
            "저가": 9980 + idx * 8,
            "거래량": 1000 + idx * 30,
        }
        for idx in range(40)
    ]

    engine.evaluate_scalping_holding_score(
        "테스트",
        "005930",
        ws_data,
        ticks,
        candles,
        {
            "record_id": "REC-2",
            "buy_price": 10000,
            "curr_price": 10050,
            "profit_rate": 0.5,
            "peak_profit": 0.8,
            "drawdown_from_peak_pct": 0.3,
            "held_sec": 75,
            "buy_qty": 1,
            "position_tag": "SCALP",
            "entry_source": "live_buy",
            "avg_down_count": 0,
            "pyramid_count": 0,
        },
    )

    payload = json.loads(captured["user_input"])
    assert len(captured["user_input"]) <= 5000
    market_flow = payload["market_flow_features"]
    assert set(market_flow).issuperset(
        {"compact_features", "tick_summary", "candle_summary"}
    )
    assert "feature_packet" not in market_flow
    assert "audit_fields" not in market_flow
    assert "recent_ticks_latest_first" not in market_flow
    assert "recent_candles_latest_window" not in market_flow
    assert "aggressor_quality" in market_flow["compact_features"]
    assert "source_quality_flags" in market_flow["compact_features"]


def test_holding_score_v2_non_dict_response_keeps_transport_meta(monkeypatch):
    engine = _build_engine()

    def _fake_call(prompt, user_input, **kwargs):
        engine._set_last_transport_meta(
            {
                "openai_transport_mode": "http",
                "openai_endpoint_name": "holding_score",
                "openai_schema_name": "holding_score_v2",
            }
        )
        return "not-json"

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)

    result = engine.evaluate_scalping_holding_score(
        "테스트",
        "005930",
        {"curr": 10050, "v_pw": 140, "quote_age_ms": 100},
        [{"time": "09:30:00", "price": 10000, "volume": 10}],
        [
            {
                "time": "09:30",
                "현재가": 10000,
                "고가": 10020,
                "저가": 9990,
                "거래량": 1000,
            }
        ],
        {
            "record_id": "REC-3",
            "buy_price": 10000,
            "curr_price": 10050,
            "profit_rate": 0.5,
            "peak_profit": 0.8,
            "held_sec": 75,
            "buy_qty": 1,
        },
    )

    assert result["ai_result_source"] == "live"
    assert result["holding_score_raw"] == 50
    assert result["openai_transport_mode"] == "http"
    assert result["openai_endpoint_name"] == "holding_score"
    assert result["openai_schema_name"] == "holding_score_v2"


def test_holding_score_v2_source_quality_accepts_fresh_computed_contract():
    engine = _build_engine()

    quality = engine._derive_holding_score_source_quality(
        {
            "tick_context_stale": False,
            "quote_stale": False,
            "tick_context_quality": "fresh_computed",
            "microstructure_reaction_source_quality": "fresh_short_window",
        },
        {},
    )

    assert quality == {
        "data_quality": "fresh",
        "source_quality_reason": "feature_packet_fresh",
    }


def test_holding_score_v2_source_quality_keeps_micro_stale_as_partial():
    engine = _build_engine()

    quality = engine._derive_holding_score_source_quality(
        {
            "tick_context_stale": False,
            "quote_stale": False,
            "tick_context_quality": "fresh_computed",
            "microstructure_reaction_source_quality": "stale_tick_or_quote",
        },
        {},
    )

    assert quality["data_quality"] == "partial"
    assert (
        "microstructure_reaction_source_quality:stale_tick_or_quote"
        in quality["source_quality_reason"]
    )


def test_holding_score_v2_source_quality_explicit_tick_stale_stays_stale():
    engine = _build_engine()

    quality = engine._derive_holding_score_source_quality(
        {
            "tick_context_stale": True,
            "quote_stale": False,
            "tick_context_quality": "fresh_computed",
            "microstructure_reaction_source_quality": "fresh_short_window",
        },
        {},
    )

    assert quality["data_quality"] == "stale"
    assert "tick_context_stale" in quality["source_quality_reason"]


def test_holding_score_v2_source_quality_marks_untrusted_pressure_partial():
    engine = _build_engine()

    quality = engine._derive_holding_score_source_quality(
        {
            "tick_context_stale": False,
            "quote_stale": False,
            "tick_context_quality": "fresh_computed",
            "microstructure_reaction_source_quality": "fresh_short_window",
            "buy_pressure_10t": 91.0,
            "net_aggressive_delta_10t": 120,
            "tick_aggressor_trusted_count": 0,
            "tick_aggressor_pressure_usable": False,
        },
        {},
    )

    assert quality["data_quality"] == "partial"
    assert "tick_aggressor_pressure_unusable" in quality["source_quality_reason"]


def test_holding_score_v2_source_quality_marks_micro_vwap_without_provenance_partial():
    engine = _build_engine()

    quality = engine._derive_holding_score_source_quality(
        {
            "tick_context_stale": False,
            "quote_stale": False,
            "tick_context_quality": "fresh_computed",
            "microstructure_reaction_source_quality": "fresh_short_window",
            "curr_vs_micro_vwap_bp": 12.0,
        },
        {},
    )

    assert quality["data_quality"] == "partial"
    assert "micro_vwap_provenance_missing" in quality["source_quality_reason"]


def test_holding_score_v2_engine_disabled_is_neutral_unusable():
    engine = _build_engine()
    engine.ai_disabled = True

    result = engine.evaluate_scalping_holding_score(
        "테스트",
        "005930",
        {"curr": 10000},
        [],
        [],
        {
            "record_id": "REC-2",
            "profit_rate": -0.5,
            "peak_profit": 0.0,
            "held_sec": 120,
        },
    )

    assert result["action"] == "HOLD"
    assert result["score"] == 50
    assert result["holding_score_data_quality"] == "insufficient"
    assert result["holding_score_effective_usable"] is False
    assert result["holding_score_raw_source"] == "engine_disabled"
    assert result["holding_score_effective_source"] == "engine_disabled"
    assert result["holding_score_effective_from_prior"] is False
    assert result["ai_result_source"] == "engine_disabled"
    assert result["ai_fallback_score_50"] is True


def test_gatekeeper_action_normalizer_accepts_korean_and_english_labels():
    assert normalize_gatekeeper_action_key("눌림 대기") == "pullback_wait"
    assert normalize_gatekeeper_action_key("눌림|대기") == "pullback_wait"
    assert normalize_gatekeeper_action_key("pullback_wait") == "pullback_wait"
    assert normalize_gatekeeper_action_key("전량 회피") == "full_avoid"
    assert normalize_gatekeeper_action_key("full avoid") == "full_avoid"
    assert normalize_gatekeeper_action_key("즉시 매수") == "immediate_buy"
    assert (
        normalize_gatekeeper_action_key("NOT_EVALUATED_SCORE_VPW_PRIOR")
        == "not_evaluated_score_vpw_prior"
    )
    assert normalize_gatekeeper_action_key("None") == "unknown"
    assert normalize_gatekeeper_action_key("ambiguous_chase") == "unknown"
    assert display_gatekeeper_action_label("pullback_wait") == "눌림 대기"
    assert (
        display_gatekeeper_action_label("not_evaluated_score_vpw_prior")
        == "NOT_EVALUATED_SCORE_VPW_PRIOR"
    )


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

    monkeypatch.setattr(
        engine, "_format_market_data", lambda ws, ticks, candles: "packet"
    )

    def _fake_call(*args, **kwargs):
        call_count["value"] += 1
        return {"action": "BUY", "score": 88, "reason": "strong"}

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)

    ws_data = {"curr": 10000, "fluctuation": 2.1, "orderbook": {"asks": [], "bids": []}}
    recent_ticks = [{"time": "10:00:00", "price": 10000, "volume": 10, "dir": "BUY"}]
    recent_candles = [{"체결시간": "10:00:00", "현재가": 10000, "거래량": 100}]

    first = engine.analyze_target(
        "테스트", ws_data, recent_ticks, recent_candles, strategy="SCALPING"
    )
    second = engine.analyze_target(
        "테스트", ws_data, recent_ticks, recent_candles, strategy="SCALPING"
    )

    assert call_count["value"] == 1
    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert second["action"] == first["action"]
    assert first["ai_model"] == "gpt-5.4-nano"


def test_holding_cache_provenance_reports_changed_bucket(monkeypatch):
    engine = _build_engine()
    call_count = {"value": 0}

    monkeypatch.setattr(
        engine, "_format_market_data", lambda ws, ticks, candles: "packet"
    )

    def _fake_call(*args, **kwargs):
        call_count["value"] += 1
        return {"action": "HOLD", "score": 70, "reason": "hold"}

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)

    ws_data = {
        "curr": 10000,
        "fluctuation": 1.0,
        "v_pw": 120,
        "buy_ratio": 55,
        "orderbook": {
            "asks": [{"price": 10010, "volume": 100}],
            "bids": [{"price": 10000, "volume": 100}],
        },
    }
    recent_ticks = [{"time": "10:00:00", "price": 10000, "volume": 100, "dir": "BUY"}]
    recent_candles = [
        {
            "체결시간": "10:00:00",
            "현재가": 10000,
            "고가": 10020,
            "저가": 9980,
            "거래량": 1000,
        }
    ]

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

    monkeypatch.setattr(
        engine, "_format_market_data", lambda ws, ticks, candles: "packet"
    )

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
    second = engine.analyze_target(
        "심텍", ws_2, ticks_2, candles_2, strategy="SCALPING"
    )

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

    monkeypatch.setattr(
        engine, "_generate_realtime_report_payload", _fake_report_payload
    )

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

    first = engine.evaluate_realtime_gatekeeper(
        "테스트", "000001", base_ctx, analysis_mode="SWING"
    )
    second = engine.evaluate_realtime_gatekeeper(
        "테스트", "000001", later_ctx, analysis_mode="SWING"
    )

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

    monkeypatch.setattr(
        engine, "_generate_realtime_report_payload", _fake_report_payload
    )

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

    first = engine.evaluate_realtime_gatekeeper(
        "테스트", "000001", ctx_a, analysis_mode="SWING"
    )
    second = engine.evaluate_realtime_gatekeeper(
        "테스트", "000001", ctx_b, analysis_mode="SWING"
    )

    assert call_count["value"] == 1
    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert second["allow_entry"] is False
    assert second["action_key"] == "pullback_wait"


def test_holding_cache_profile_absorbs_micro_market_noise(monkeypatch):
    engine = _build_engine()
    call_count = {"value": 0}

    monkeypatch.setattr(
        engine, "_format_market_data", lambda ws, ticks, candles: "packet"
    )

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
        {
            "체결시간": "10:43:00",
            "현재가": 12140,
            "고가": 12160,
            "저가": 12120,
            "거래량": 8200,
        },
        {
            "체결시간": "10:44:00",
            "현재가": 12150,
            "고가": 12170,
            "저가": 12130,
            "거래량": 9100,
        },
        {
            "체결시간": "10:45:00",
            "현재가": 12150,
            "고가": 12180,
            "저가": 12140,
            "거래량": 10300,
        },
    ]
    candles_2 = [
        {
            "체결시간": "10:43:30",
            "현재가": 12140,
            "고가": 12160,
            "저가": 12120,
            "거래량": 8700,
        },
        {
            "체결시간": "10:44:30",
            "현재가": 12160,
            "고가": 12170,
            "저가": 12140,
            "거래량": 9500,
        },
        {
            "체결시간": "10:45:30",
            "현재가": 12160,
            "고가": 12180,
            "저가": 12140,
            "거래량": 10800,
        },
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


def test_scalping_entry_prompts_align_default_runtime_buy_band():
    for prompt in (
        SCALPING_SYSTEM_PROMPT,
        SCALPING_WATCHING_HOT_SYSTEM_PROMPT,
        SCALPING_WATCHING_SYSTEM_PROMPT,
    ):
        assert "75-100 BUY" in prompt
        assert "50-74 WAIT" in prompt
        assert "0-49 DROP" in prompt
        assert "70-100 BUY" not in prompt


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
            return {
                "action": "SELL_TODAY",
                "confidence": 60,
                "reason": "risk",
                "risk_note": "test",
            }
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
        {
            "profit_rate": 0.2,
            "peak_profit": 0.5,
            "held_sec": 80,
            "current_ai_score": 50,
        },
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

    monkeypatch.setattr(
        engine, "_format_market_data", lambda ws, ticks, candles: "scalp-packet"
    )
    monkeypatch.setattr(
        engine, "_format_swing_market_data", lambda ws, candles, qty: "swing-packet"
    )

    def _fake_call(*args, **kwargs):
        used_models.append(kwargs.get("model_override"))
        return {"action": "BUY", "score": 80, "reason": "ok"}

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)
    monkeypatch.setattr(
        engine, "_apply_remote_entry_guard", lambda result, **kwargs: result
    )

    ws_data = {"curr": 10000, "fluctuation": 1.0, "orderbook": {"asks": [], "bids": []}}
    recent_ticks = [{"time": "10:00:00", "price": 10000, "volume": 10, "dir": "BUY"}]
    recent_candles = [{"체결시간": "10:00:00", "현재가": 10000, "거래량": 100}]

    engine.analyze_target(
        "스캘프", ws_data, recent_ticks, recent_candles, strategy="SCALPING"
    )
    engine.analyze_target(
        "스윙", ws_data, recent_ticks, recent_candles, strategy="KOSDAQ_ML"
    )

    assert used_models == ["gpt-5.4-nano", "tier2-model"]


def test_analyze_target_routes_scalping_prompt_profiles(monkeypatch):
    engine = _build_engine()
    used_prompts = []
    used_models = []

    monkeypatch.setattr(
        engine, "_format_market_data", lambda ws, ticks, candles: "scalp-packet"
    )

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
        SCALPING_WATCHING_HOT_SYSTEM_PROMPT,
        SCALPING_HOLDING_SYSTEM_PROMPT,
        SCALPING_HOLDING_SYSTEM_PROMPT,
        SCALPING_SYSTEM_PROMPT,
    ]
    assert used_models == [
        "gpt-5.4-nano",
        "tier1-model",
        "tier1-model",
        "gpt-5.4-nano",
    ]
    assert watching["ai_prompt_type"] == "scalping_entry"
    assert holding["ai_prompt_type"] == "scalping_holding"
    assert exiting["ai_prompt_type"] == "scalping_holding"
    assert shared["ai_prompt_type"] == "scalping_shared"
    assert watching["ai_model"] == "gpt-5.4-nano"
    assert exiting["ai_model"] == "tier1-model"
    assert shared["ai_model"] == "gpt-5.4-nano"
    assert watching["ai_prompt_version"] == "hot_v1"


def test_analyze_target_holding_exit_action_schema_compat(monkeypatch):
    engine = _build_engine()
    monkeypatch.setattr(
        engine, "_format_market_data", lambda ws, ticks, candles: "scalp-packet"
    )
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
    result = normalize_ai_reason_language(
        "curr_vs_ma5_bp positive but liquidity weak", max_len=120
    )

    assert result["reason"] == "curr_vs_ma5_bp positive but liquidity weak"
    assert result["ai_reason_language_violation"] is False


def test_scalping_prompts_require_english_ascii_reason():
    for prompt in (
        SCALPING_SYSTEM_PROMPT,
        SCALPING_WATCHING_HOT_SYSTEM_PROMPT,
        SCALPING_WATCHING_SYSTEM_PROMPT,
        SCALPING_HOLDING_SYSTEM_PROMPT,
        SCALPING_HOLDING_FLOW_SYSTEM_PROMPT,
        SCALPING_ENTRY_PRICE_PROMPT,
        SCALPING_OVERNIGHT_DECISION_PROMPT,
    ):
        assert "English ASCII only" in prompt


def test_internal_json_classifier_prompts_use_english_instruction_text():
    for prompt in (
        SCALPING_WATCHING_HOT_SYSTEM_PROMPT,
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
    assert (
        "low-latency scalping position-state classifier"
        in SCALPING_HOLDING_SYSTEM_PROMPT
    )
    assert (
        "scalping holding/overnight flow classifier"
        in SCALPING_HOLDING_FLOW_SYSTEM_PROMPT
    )
    assert (
        "absorption, recovery, distribution, breakdown, quiet"
        in SCALPING_HOLDING_FLOW_SYSTEM_PROMPT
    )


def test_stage_prompts_keep_decision_scope_separated():
    assert (
        "Do not decide order price, quantity, holding, or exit."
        in SCALPING_SYSTEM_PROMPT
    )
    assert (
        "Do not decide order price, quantity, holding, exit, provider route, or hard guard policy."
        in (SCALPING_WATCHING_HOT_SYSTEM_PROMPT)
    )
    assert (
        "Do not decide order price, quantity, holding, or exit."
        in SCALPING_WATCHING_SYSTEM_PROMPT
    )
    assert "Do not re-decide BUY vs WAIT." in SCALPING_ENTRY_PRICE_PROMPT
    assert (
        "Do not change entry, order price, provider route, quantity, or hard guard policy."
        in (SCALPING_HOLDING_FLOW_SYSTEM_PROMPT)
    )


def test_entry_screen_v2_payload_keeps_feature_provenance_in_source_quality():
    engine = _build_engine()

    payload = engine._build_entry_screen_v2_payload(
        {
            "curr": 1000,
            "v_pw": 121,
            "fluctuation": 1.2,
            "latency_state": "fresh",
            "quote_stale": False,
            "quote_age_ms": 80,
            "orderbook": {
                "asks": [{"price": 1001, "volume": 10}],
                "bids": [{"price": 999, "volume": 12}],
            },
        },
        [{"time": "09:00:01", "price": 1000, "volume": 3, "dir": "BUY"}],
        [{"체결시간": "09:00:00", "현재가": 1000, "거래량": 100}],
        feature_packet={
            "tick_context_quality": "fresh_computed",
            "tick_context_stale": False,
            "tick_accel_source": "computed_10ticks",
            "quote_age_ms": 80,
            "quote_stale": False,
            "tick_latest_age_ms": 120,
            "tick_aggressor_pressure_usable": False,
            "tick_aggressor_trusted_count": 0,
            "tick_aggressor_price_heuristic_count": 5,
            "micro_vwap_available": False,
            "ma5_available": True,
            "minute_candle_window_fresh": False,
            "minute_candle_context_quality": "stale_minute_window",
        },
    )

    source_quality = payload["source_quality"]
    assert source_quality["tick_aggressor_pressure_usable"] is False
    assert source_quality["tick_aggressor_trusted_count"] == 0
    assert source_quality["tick_aggressor_price_heuristic_count"] == 5
    assert source_quality["micro_vwap_available"] is False
    assert source_quality["minute_candle_window_fresh"] is False
    assert source_quality["price_change_heuristic_is_not_aggressor"] is True


def test_remote_buy_guard_does_not_count_micro_vwap_without_provenance(monkeypatch):
    engine = _build_engine()
    features = {
        "large_sell_print_detected": False,
        "distance_from_day_high_pct": -1.0,
        "tick_acceleration_ratio": 1.20,
        "curr_vs_micro_vwap_bp": -18.0,
        "top3_depth_ratio": 1.0,
        "tick_aggressor_pressure_usable": True,
        "tick_aggressor_trusted_count": 3,
        "buy_pressure_10t": 74.0,
    }
    monkeypatch.setattr(
        engine, "_extract_scalping_features", lambda *_args, **_kwargs: features
    )

    _, risk_flags = engine._remote_buy_risk_flags({}, [], [])

    assert risk_flags == 0


def test_remote_buy_guard_does_not_downgrade_instant_strength_without_micro_provenance(
    monkeypatch,
):
    engine = _build_engine()
    features = {
        "large_sell_print_detected": False,
        "distance_from_day_high_pct": -1.0,
        "tick_acceleration_ratio": 1.20,
        "curr_vs_micro_vwap_bp": 0.0,
        "top3_depth_ratio": 1.0,
        "tick_aggressor_pressure_usable": True,
        "tick_aggressor_trusted_count": 3,
        "buy_pressure_10t": 74.0,
        "latest_strength": 121.0,
        "same_price_buy_absorption": 0,
    }
    monkeypatch.setattr(
        engine, "_extract_scalping_features", lambda *_args, **_kwargs: features
    )

    result = engine._apply_remote_entry_guard(
        {"action": "BUY", "score": 80, "reason": "strong pressure"},
        prompt_type="scalping_entry",
        ws_data={},
        recent_ticks=[],
        recent_candles=[],
    )

    assert result["action"] == "BUY"
    assert result["score"] == 80


def test_entry_numeric_consistency_ignores_micro_vwap_without_provenance():
    engine = _build_engine()
    result = engine._annotate_entry_numeric_consistency(
        {
            "action": "WAIT",
            "score": 72,
            "reason": "WAIT because curr_vs_micro_vwap_bp <= 0",
        },
        prompt_type="scalping_entry",
        feature_packet={
            "curr_vs_micro_vwap_bp": 14.0,
            "curr_vs_ma5_bp": 0.0,
            "ma5_available": False,
            "tick_acceleration_ratio": 0.5,
            "buy_pressure_10t": 50.0,
            "tick_aggressor_pressure_usable": False,
            "tick_aggressor_trusted_count": 0,
        },
    )

    assert result.get("ai_reason_numeric_inconsistency") is not True


def test_entry_numeric_consistency_uses_micro_vwap_with_fresh_provenance():
    engine = _build_engine()
    result = engine._annotate_entry_numeric_consistency(
        {
            "action": "WAIT",
            "score": 72,
            "reason": "WAIT because curr_vs_micro_vwap_bp <= 0",
        },
        prompt_type="scalping_entry",
        feature_packet={
            "curr_vs_micro_vwap_bp": 14.0,
            "micro_vwap_available": True,
            "minute_candle_window_fresh": True,
            "minute_candle_context_quality": "fresh_bar_window",
            "curr_vs_ma5_bp": 0.0,
            "ma5_available": False,
            "tick_acceleration_ratio": 0.5,
            "buy_pressure_10t": 50.0,
            "tick_aggressor_pressure_usable": False,
            "tick_aggressor_trusted_count": 0,
        },
    )

    assert result["ai_reason_numeric_inconsistency"] is True
    assert result["ai_reason_numeric_inconsistency_field"] == "position_advantage"


def test_scalping_compact_entry_payload_keeps_source_quality_and_freshness(monkeypatch):
    engine = _build_engine()
    monkeypatch.setattr(
        ai_engine_openai_module,
        "TRADING_RULES",
        replace(
            ai_engine_openai_module.TRADING_RULES,
            OPENAI_ENTRY_SCREEN_V2_INPUT_ENABLED=False,
            OPENAI_SCALPING_COMPACT_INPUT_ENABLED=True,
        ),
    )

    payload = json.loads(
        engine._format_market_data(
            {
                "curr": 1000,
                "v_pw": 121,
                "fluctuation": 1.2,
                "latency_state": "fresh",
                "quote_stale": False,
                "quote_age_ms": 90,
                "orderbook": {
                    "asks": [{"price": 1001, "volume": 10}],
                    "bids": [{"price": 999, "volume": 12}],
                },
            },
            [
                {
                    "time": "09:00:01",
                    "price": 1000,
                    "volume": 3,
                    "dir": "BUY",
                    "aggressor_source": "orderbook_touch",
                    "aggressor_quality": "fresh",
                }
            ],
            [
                {
                    "체결시간": "09:00:00",
                    "현재가": 1000,
                    "고가": 1002,
                    "저가": 998,
                    "거래량": 100,
                }
            ],
        )
    )

    assert payload["quote_freshness"]["latency_state"] == "fresh"
    assert payload["quote_freshness"]["quote_stale"] is False
    assert payload["source_quality"]["tick_count"] == 1
    assert payload["source_quality"]["candle_count"] == 1
    assert payload["source_quality"]["orderbook_present"] is True
    assert payload["source_quality"]["tick_aggressor_pressure_usable"] is True
    assert payload["source_quality"]["tick_aggressor_trusted_count"] >= 1
    assert payload["source_quality"]["tick_aggressor_price_heuristic_count"] == 0
    assert payload["source_quality"]["micro_vwap_available"] is False
    assert payload["source_quality"]["minute_candle_window_fresh"] is True
    assert payload["source_quality"]["price_change_heuristic_is_not_aggressor"] is True
    assert (
        payload["recent_ticks_latest_first"][0]["aggressor_source"] == "orderbook_touch"
    )


def test_scalping_legacy_text_entry_payload_includes_feature_provenance(monkeypatch):
    engine = _build_engine()
    monkeypatch.setattr(
        ai_engine_openai_module,
        "TRADING_RULES",
        replace(
            ai_engine_openai_module.TRADING_RULES,
            OPENAI_ENTRY_SCREEN_V2_INPUT_ENABLED=False,
            OPENAI_SCALPING_COMPACT_INPUT_ENABLED=False,
        ),
    )
    feature_packet = {
        "packet_version": "scalp_feature_packet_v1",
        "curr_price": 1000,
        "latest_strength": 121,
        "spread_krw": 2,
        "spread_bp": 20.0,
        "top1_depth_ratio": 1.0,
        "top3_depth_ratio": 1.0,
        "orderbook_total_ratio": 1.0,
        "micro_price": 1000.0,
        "microprice_edge_bp": 0.0,
        "buy_pressure_10t": 50.0,
        "tick_aggressor_pressure_usable": False,
        "tick_aggressor_trusted_count": 0,
        "tick_aggressor_price_heuristic_count": 10,
        "price_change_10t_pct": 0.2,
        "recent_5tick_seconds": 2.0,
        "prev_5tick_seconds": 3.0,
        "distance_from_day_high_pct": -0.5,
        "intraday_range_pct": 1.0,
        "tick_acceleration_ratio": 1.5,
        "tick_accel_source": "computed_10ticks",
        "tick_context_quality": "fresh_computed",
        "tick_context_stale": False,
        "same_price_buy_absorption": 0,
        "large_sell_print_detected": False,
        "large_buy_print_detected": False,
        "net_aggressive_delta_10t": 0,
        "volume_ratio_pct": 0.0,
        "curr_vs_micro_vwap_bp": 0.0,
        "micro_vwap_available": False,
        "minute_candle_window_fresh": False,
        "minute_candle_context_quality": "missing_candles",
        "curr_vs_ma5_bp": 0.0,
        "ma5_available": False,
        "micro_vwap_value": 0.0,
        "ma5_value": 0.0,
        "ask_depth_ratio": 1.0,
        "net_ask_depth": 0,
    }

    text = engine._format_market_data(
        {
            "curr": 1000,
            "v_pw": 121,
            "fluctuation": 1.2,
            "ask_tot": 100,
            "bid_tot": 100,
            "orderbook": {
                "asks": [{"price": 1001, "volume": 10}],
                "bids": [{"price": 999, "volume": 12}],
            },
        },
        [],
        [],
        feature_packet=feature_packet,
    )

    assert "tick_aggressor_pressure_usable: false" in text
    assert "tick_aggressor_trusted_count: 0" in text
    assert "tick_aggressor_price_heuristic_count: 10" in text
    assert "micro_vwap_available: false" in text
    assert "minute_candle_window_fresh: false" in text
    assert "ma5_available: false" in text


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

    assert (
        "opportunity-side quantitative reviewer"
        in ai_engine_openai_module.DUAL_PERSONA_AGGRESSIVE_PROMPT
    )
    assert (
        "risk-side quantitative reviewer"
        in ai_engine_openai_module.DUAL_PERSONA_CONSERVATIVE_PROMPT
    )


def test_overnight_prompt_is_internal_english_schema_first_classifier():
    assert (
        "pre-close scalping overnight risk classifier"
        in SCALPING_OVERNIGHT_DECISION_PROMPT
    )
    assert "Default action is SELL_TODAY" in SCALPING_OVERNIGHT_DECISION_PROMPT
    assert "HOLD_OVERNIGHT is a strict exception" in SCALPING_OVERNIGHT_DECISION_PROMPT
    assert (
        "stale, missing, insufficient, or mixed" in SCALPING_OVERNIGHT_DECISION_PROMPT
    )
    assert (
        "one concise overnight decision rationale" in SCALPING_OVERNIGHT_DECISION_PROMPT
    )
    assert "one concise main risk" in SCALPING_OVERNIGHT_DECISION_PROMPT
    assert "15년" not in SCALPING_OVERNIGHT_DECISION_PROMPT
    assert "베테랑" not in SCALPING_OVERNIGHT_DECISION_PROMPT
    assert "판단 근거" not in SCALPING_OVERNIGHT_DECISION_PROMPT


def test_analyze_target_uses_shared_prompt_when_split_disabled(monkeypatch):
    engine = _build_engine()
    used_prompts = []
    disabled_rules = replace(
        ai_engine_openai_module.TRADING_RULES, SCALPING_PROMPT_SPLIT_ENABLED=False
    )
    monkeypatch.setattr(ai_engine_openai_module, "TRADING_RULES", disabled_rules)
    monkeypatch.setattr(
        engine, "_format_market_data", lambda ws, ticks, candles: "scalp-packet"
    )

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

    monkeypatch.setattr(
        engine, "_format_market_data", lambda ws, ticks, candles: "condition-packet"
    )

    def _fake_call(prompt, *args, **kwargs):
        used_prompts.append(prompt)
        used_models.append(kwargs.get("model_override"))
        used_schemas.append(kwargs.get("schema_name"))
        if kwargs.get("schema_name") == "entry_v1":
            return {"action": "BUY", "score": 88, "reason": "entry flow"}
        return {"action": "TRIM", "score": 77, "reason": "exit flow"}

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)
    monkeypatch.setattr(
        engine, "_apply_remote_entry_guard", lambda result, **kwargs: result
    )

    ws_data = {"curr": 10000, "fluctuation": 1.0, "orderbook": {"asks": [], "bids": []}}
    recent_ticks = [{"time": "10:00:00", "price": 10000, "volume": 10, "dir": "BUY"}]
    recent_candles = [{"체결시간": "10:00:00", "현재가": 10000, "거래량": 100}]
    profile = {"name": "VCP", "strategy": "SCALPING"}

    entry = engine.evaluate_condition_entry(
        "조건주", "000001", ws_data, recent_ticks, recent_candles, profile
    )
    exit_result = engine.evaluate_condition_exit(
        "조건주", "000001", ws_data, recent_ticks, recent_candles, profile, 1.2, 2.1, 78
    )

    assert used_models == ["gpt-5.4-nano", "gpt-5.4-nano"]
    assert used_prompts == [
        SCALPING_WATCHING_HOT_SYSTEM_PROMPT,
        SCALPING_HOLDING_SCORE_SYSTEM_PROMPT,
    ]
    assert used_schemas == ["entry_v1", "holding_score_v2"]
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
            {
                "time": "10:00:02",
                "price": 10090,
                "volume": 450,
                "best_bid": 10090,
                "best_ask": 10100,
                "aggressor_source": "orderbook_touch",
            },
            {
                "time": "10:00:01",
                "price": 10100,
                "volume": 250,
                "best_bid": 10090,
                "best_ask": 10100,
                "aggressor_source": "orderbook_touch",
            },
            {"time": "10:00:00", "price": 10080, "volume": 100, "dir": "BUY"},
        ]
    )

    assert compact == [
        {
            "latest_price": 202,
            "buy_volume": 2,
            "sell_volume": 4,
            "net_volume": -2,
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
        monkeypatch.setattr(
            engine, "_format_market_data", lambda ws, ticks, candles: "packet"
        )

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
        assert (
            result["holding_exit_matrix_decision_alignment"] == "neutral_no_clear_edge"
        )


def test_openai_analyze_target_waits_min_interval_instead_of_score50_cooldown(
    monkeypatch,
):
    engine = _build_provider_engine(GPTSniperEngine)
    engine.last_call_time = 100.0
    engine.min_interval = 0.5
    sleeps = []

    monkeypatch.setattr(ai_engine_openai_module.time, "time", lambda: 100.2)
    monkeypatch.setattr(
        ai_engine_openai_module.time, "sleep", lambda sec: sleeps.append(sec)
    )
    monkeypatch.setattr(
        engine, "_format_market_data", lambda ws, ticks, candles: "packet"
    )
    monkeypatch.setattr(
        engine, "_apply_remote_entry_guard", lambda result, **kwargs: result
    )

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


def test_openai_analyze_target_waits_for_lock_contention_retry(monkeypatch):
    engine = _build_provider_engine(GPTSniperEngine)
    acquire_calls = []

    class ContendedThenAvailableLock:
        def acquire(self, blocking=True, timeout=-1):
            acquire_calls.append((blocking, timeout))
            return timeout and timeout > 0

        def release(self):
            return None

    engine.lock = ContendedThenAvailableLock()
    monkeypatch.setattr(
        engine, "_format_market_data", lambda ws, ticks, candles: "packet"
    )
    monkeypatch.setattr(
        engine, "_apply_remote_entry_guard", lambda result, **kwargs: result
    )
    monkeypatch.setattr(
        engine,
        "_call_openai_safe",
        lambda *args, **kwargs: {"action": "BUY", "score": 88, "reason": "strong"},
    )

    result = engine.analyze_target(
        "LOCK_WAIT_TEST",
        {"curr": 10000, "fluctuation": 1.0, "orderbook": {"asks": [], "bids": []}},
        [{"time": "10:00:00", "price": 10000, "volume": 10, "dir": "BUY"}],
        [{"체결시간": "10:00:00", "현재가": 10000, "거래량": 100}],
        strategy="SCALPING",
        cache_profile="lock_wait_test",
    )

    assert acquire_calls
    assert acquire_calls[0][1] > 0
    assert result["action"] == "BUY"
    assert result["score"] == 88
    assert result["ai_result_source"] == "live"
    assert result["ai_fallback_score_50"] is False


def test_openai_analyze_target_lock_contention_exhaustion_is_not_score50_fallback(
    monkeypatch,
):
    engine = _build_provider_engine(GPTSniperEngine)

    class AlwaysContendedLock:
        def acquire(self, blocking=True, timeout=-1):
            return False

        def release(self):
            raise AssertionError("lock must not be released when acquire failed")

    engine.lock = AlwaysContendedLock()
    monkeypatch.setattr(
        engine,
        "_call_openai_safe",
        lambda *args, **kwargs: {"action": "BUY", "score": 88},
    )

    result = engine.analyze_target(
        "LOCK_FAIL_TEST",
        {"curr": 10000, "fluctuation": 1.0, "orderbook": {"asks": [], "bids": []}},
        [{"time": "10:00:00", "price": 10000, "volume": 10, "dir": "BUY"}],
        [{"체결시간": "10:00:00", "현재가": 10000, "거래량": 100}],
        strategy="SCALPING",
        cache_profile="lock_fail_test",
    )

    assert result["action"] == "DROP"
    assert result["score"] == 0
    assert result["ai_result_source"] == "lock_contention"
    assert result["ai_fallback_score_50"] is False
    assert result["ai_retry_attempted"] is True
    assert result["ai_retry_result"] == "lock_contention_retry_exhausted"


def test_holding_score_lock_contention_waits_before_neutral_score50(monkeypatch):
    engine = _build_provider_engine(GPTSniperEngine)
    acquire_calls = []

    class AlwaysContendedLock:
        def acquire(self, blocking=True, timeout=-1):
            acquire_calls.append((blocking, timeout))
            return False

        def release(self):
            raise AssertionError("lock must not be released when acquire failed")

    engine.lock = AlwaysContendedLock()

    result = engine.evaluate_scalping_holding_score(
        "LOCK_HOLDING_TEST",
        "005930",
        {"curr": 10000},
        [],
        [],
        {
            "profit_rate": 0.2,
            "peak_profit": 0.5,
            "held_sec": 80,
            "current_ai_score": 50,
        },
    )

    assert acquire_calls
    assert acquire_calls[0][1] > 0
    assert result["score"] == 50
    assert result["holding_score_effective_usable"] is False
    assert result["ai_result_source"] == "lock_contention"
    assert result["ai_fallback_score_50"] is True
    assert result["ai_retry_attempted"] is True
    assert result["ai_retry_result"] == "lock_contention_retry_exhausted"


def test_provider_holding_matrix_cache_token_separates_cache_variants(monkeypatch):
    ws_data = {"curr": 10000, "fluctuation": 1.0, "orderbook": {"asks": [], "bids": []}}
    recent_ticks = [{"time": "10:00:00", "price": 10000, "volume": 10, "dir": "BUY"}]
    recent_candles = [{"체결시간": "10:00:00", "현재가": 10000, "거래량": 100}]

    for engine_cls, module, call_name in PROVIDER_ENGINES:
        engine = _build_provider_engine(engine_cls)
        call_count = {"value": 0}
        contexts = iter(
            [
                _holding_matrix_runtime_context(
                    "candidate:matrix_v1:price_10k_30k:volume_500k_2m:time_0930_1030"
                ),
                _holding_matrix_runtime_context(
                    "candidate:matrix_v2:price_10k_30k:volume_500k_2m:time_0930_1030"
                ),
            ]
        )

        monkeypatch.setattr(
            module,
            "build_holding_exit_matrix_runtime_context",
            lambda **kwargs: next(contexts),
        )
        monkeypatch.setattr(
            engine, "_format_market_data", lambda ws, ticks, candles: "packet"
        )

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
            OPENAI_ANALYZE_TARGET_TIMEOUT_MS=3000,
            OPENAI_ENTRY_PRICE_TIMEOUT_MS=7000,
            OPENAI_HOLDING_SCORE_TIMEOUT_MS=7000,
            OPENAI_HOLDING_FLOW_TIMEOUT_MS=15000,
            OPENAI_SCANNER_REPORT_TIMEOUT_MS=15000,
            OPENAI_OVERNIGHT_TIMEOUT_MS=12000,
        ),
    )
    engine = _build_provider_engine(GPTSniperEngine)

    assert (
        engine._get_openai_timeout_ms(endpoint_name="overnight", require_json=True)
        == 12000
    )
    assert (
        engine._get_openai_timeout_ms(
            endpoint_name="scanner_report", require_json=False
        )
        == 15000
    )
    assert (
        engine._get_openai_timeout_ms(endpoint_name="analyze_target", require_json=True)
        == 3000
    )
    assert (
        engine._get_openai_timeout_ms(endpoint_name="entry_price", require_json=True)
        == 7000
    )
    assert (
        engine._get_openai_timeout_ms(endpoint_name="holding_score", require_json=True)
        == 7000
    )
    assert (
        engine._get_openai_timeout_ms(endpoint_name="holding_flow", require_json=True)
        == 15000
    )
    assert (
        engine._get_openai_timeout_ms(endpoint_name="generic_json", require_json=True)
        == 700
    )


def test_analyze_target_timeout_reject_is_not_marked_score50_fallback(monkeypatch):
    engine = _build_engine()
    monkeypatch.setattr(
        ai_engine_openai_module,
        "TRADING_RULES",
        replace(
            ai_engine_openai_module.TRADING_RULES,
            OPENAI_ENTRY_TIMEOUT_REJECT_ENABLED=True,
            OPENAI_SCALPING_COMPACT_INPUT_ENABLED=True,
            OPENAI_ENTRY_SCREEN_V2_INPUT_ENABLED=False,
        ),
    )

    def _raise(*args, **kwargs):
        raise TimeoutError("Request timed out.")

    monkeypatch.setattr(engine, "_call_openai_safe", _raise)

    result = engine.analyze_target(
        "TIMEOUT_TEST",
        {
            "curr": 10000,
            "fluctuation": 0.8,
            "v_pw": 122,
            "quote_stale": False,
            "orderbook": {
                "asks": [{"price": 10010, "volume": 100}],
                "bids": [{"price": 10000, "volume": 120}],
            },
        },
        [{"time": "10:00:00", "price": 10000, "volume": 10, "dir": "BUY"}],
        [
            {
                "체결시간": "10:00:00",
                "현재가": 10000,
                "고가": 10020,
                "저가": 9990,
                "거래량": 1000,
            }
        ],
        strategy="SCALPING",
        cache_profile="timeout_reject_test",
        prompt_profile="shared",
    )

    assert result["action"] == "DROP"
    assert result["score"] == 0
    assert result["ai_result_source"] == "exception"
    assert result["ai_parse_fail"] is True
    assert result["ai_fallback_score_50"] is False


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

    engine.generate_realtime_report(
        "리포트주", "000001", "legacy packet", analysis_mode="SWING"
    )
    engine.evaluate_scalping_overnight_decision(
        "오버나이트주", "000001", {"curr_price": 10000}
    )

    assert used_models == ["tier2-model", "tier2-model"]


def test_scanner_briefing_uses_tier3_model(monkeypatch):
    engine = _build_engine()
    used_models = []

    monkeypatch.setattr(
        ai_engine_openai_module,
        "build_scanner_data_input",
        lambda **kwargs: "scanner-data",
    )

    def _fake_call(*args, **kwargs):
        used_models.append(kwargs.get("model_override"))
        return "브리핑"

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)

    engine.analyze_scanner_results(100, 5, "stats", "macro")

    assert used_models == ["tier3-model"]
