import json
import threading
from dataclasses import replace
from types import SimpleNamespace

from src.engine import ai_engine_openai as openai_module
from src.engine.ai_engine_openai import (
    GPTSniperEngine,
    OPENAI_PROMPT_CONTRACT_MARKER,
    OPENAI_RESPONSE_SCHEMA_REGISTRY,
    OpenAIResponseRequest,
    OpenAIResponsesWSPool,
    OpenAITransportResult,
    OpenAIWSRequestIdMismatchError,
)
from src.engine.ai_engine import SCALPING_HOLDING_FLOW_SYSTEM_PROMPT
from src.engine import bedrock_nova_provider


def _build_engine():
    engine = GPTSniperEngine.__new__(GPTSniperEngine)
    engine.api_call_lock = threading.Lock()
    engine.current_model_name = "gpt-fast"
    engine.model_tier1_fast = "gpt-fast"
    engine.model_tier2_balanced = "gpt-report"
    engine.model_tier3_deep = "gpt-deep"
    engine.fast_model_name = "gpt-fast"
    engine.report_model_name = "gpt-report"
    engine.deep_model_name = "gpt-deep"
    engine.api_keys = ["key-a", "key-b"]
    engine.current_key = "key-a"
    engine.current_api_key_index = 0
    engine._rotate_client = lambda: None
    engine._transport_local = threading.local()
    engine._ws_metrics_lock = threading.Lock()
    engine._ws_metrics = {
        "openai_ws_requests": 0,
        "openai_ws_completed": 0,
        "openai_ws_timeout_reject": 0,
        "openai_ws_late_discard": 0,
        "openai_ws_parse_fail": 0,
        "openai_ws_reconnects": 0,
        "openai_ws_http_fallback": 0,
        "openai_ws_request_id_mismatch": 0,
        "openai_ws_queue_wait_ms_values": [],
        "openai_ws_roundtrip_ms_values": [],
    }
    engine._responses_ws_pool = None
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
    engine.last_call_time = 0.0
    engine.min_interval = 0.0
    engine._annotate_analysis_result = lambda result, **meta: {**dict(result), **{
        "ai_parse_ok": bool(meta.get("parse_ok", False)),
        "ai_parse_fail": bool(meta.get("parse_fail", False)),
    }}
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


def test_openai_engine_default_model_routing_uses_requested_tiers():
    engine = GPTSniperEngine(["test-key"], announce_startup=False)

    assert engine.fast_model_name == "gpt-5-nano"
    assert engine.report_model_name == "gpt-5.4-mini"
    assert engine.deep_model_name == "gpt-5.4"


def test_openai_call_applies_endpoint_response_schema_when_flag_enabled(monkeypatch):
    engine = _build_engine()
    captured = {}

    def _fake_create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            output_text='{"decision":"BUY","confidence":88,"order_type":"LIMIT_TOP","position_size_ratio":0.1,"invalidation_price":1000,"reasons":["ok"],"risks":[]}'
        )

    engine.client = SimpleNamespace(responses=SimpleNamespace(create=_fake_create))

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_RESPONSE_SCHEMA_REGISTRY_ENABLED=True,
            OPENAI_TRANSPORT_MODE="http",
        ),
    )

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="test",
        schema_name="condition_entry_v1",
        endpoint_name="condition_entry",
        symbol="000001",
    )

    assert result["decision"] == "BUY"
    assert captured["text"]["format"]["type"] == "json_schema"
    assert captured["text"]["format"]["name"] == "condition_entry_v1"
    assert captured["text"]["format"]["schema"] == OPENAI_RESPONSE_SCHEMA_REGISTRY["condition_entry_v1"]
    assert OPENAI_PROMPT_CONTRACT_MARKER in captured["instructions"]
    assert "Control language: English" in captured["instructions"]
    assert "Korean domain glossary" in captured["instructions"]
    assert "Preserve all raw enum labels" in captured["instructions"]
    assert "PROMPT" in captured["instructions"]


def test_bedrock_primary_only_routes_gpt5_nano_json(monkeypatch):
    engine = _build_engine()
    openai_called = {"value": False}

    engine.client = SimpleNamespace(
        responses=SimpleNamespace(
            create=lambda **kwargs: openai_called.__setitem__("value", True)
        )
    )

    class Provider:
        def converse(self, *, prompt, user_input, profile):
            return bedrock_nova_provider.BedrockNovaResult(
                payload={"action": "WAIT", "score": 61, "reason": "bedrock"},
                raw_text='{"action":"WAIT","score":61,"reason":"bedrock"}',
                parse_ok=True,
                parse_error="",
                model_id=profile.model_id,
                region_name=profile.region_name,
                key_index=0,
                latency_ms=123,
                input_tokens=10,
                output_tokens=5,
                cache_read_input_tokens=0,
                cache_write_input_tokens=0,
                total_input_tokens=10,
                estimated_cost_usd=0.1,
                attempted_key_count=1,
            )

    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_MICRO_ROUTE_MODE", "primary")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE", "shadow")
    monkeypatch.setattr(bedrock_nova_provider, "runtime_provider", lambda: Provider())
    monkeypatch.setattr(bedrock_nova_provider, "write_provider_audit_row", lambda row: None)

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="test",
        model_override="gpt-5-nano",
        endpoint_name="analyze_target",
    )

    assert result["action"] == "WAIT"
    assert openai_called["value"] is False
    meta = engine._consume_last_transport_meta()
    assert meta["provider"] == "bedrock"
    assert meta["bedrock_primary_used"] is True
    assert meta["bedrock_failback_used"] is False


def test_bedrock_primary_routes_gpt54_mini_independently(monkeypatch):
    engine = _build_engine()
    captured = {}

    class Provider:
        def converse(self, *, prompt, user_input, profile):
            captured["model_id"] = profile.model_id
            captured["family"] = profile.family
            return bedrock_nova_provider.BedrockNovaResult(
                payload={"action": "HOLD", "score": 64, "reason": "lite"},
                raw_text='{"action":"HOLD","score":64,"reason":"lite"}',
                parse_ok=True,
                parse_error="",
                model_id=profile.model_id,
                region_name=profile.region_name,
                key_index=0,
                latency_ms=456,
                input_tokens=20,
                output_tokens=8,
                cache_read_input_tokens=0,
                cache_write_input_tokens=0,
                total_input_tokens=20,
                estimated_cost_usd=0.2,
                attempted_key_count=1,
            )

    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_MICRO_ROUTE_MODE", "shadow")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE", "primary")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_PRIMARY_ENDPOINTS", "entry_price,holding_flow")
    monkeypatch.setattr(bedrock_nova_provider, "runtime_provider", lambda: Provider())
    monkeypatch.setattr(bedrock_nova_provider, "write_provider_audit_row", lambda row: None)

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="test",
        model_override="gpt-5.4-mini",
        endpoint_name="holding_flow",
    )

    assert result["action"] == "HOLD"
    assert captured["family"] == "lite"
    meta = engine._consume_last_transport_meta()
    assert meta["provider"] == "bedrock"
    assert meta["bedrock_primary_used"] is True


def test_lite_primary_entry_price_and_holding_flow_do_not_call_openai(monkeypatch):
    engine = _build_engine()
    provider_endpoints = []
    openai_called = {"value": False}

    class Responses:
        def create(self, **kwargs):
            openai_called["value"] = True
            raise AssertionError("OpenAI must not be called for Lite primary endpoints")

    class Provider:
        def converse(self, *, prompt, user_input, profile):
            provider_endpoints.append(profile.family)
            return bedrock_nova_provider.BedrockNovaResult(
                payload={"action": "HOLD", "score": 64, "reason": "lite-primary"},
                raw_text='{"action":"HOLD","score":64,"reason":"lite-primary"}',
                parse_ok=True,
                parse_error="",
                model_id=profile.model_id,
                region_name=profile.region_name,
                key_index=0,
                latency_ms=123,
                input_tokens=20,
                output_tokens=8,
                cache_read_input_tokens=0,
                cache_write_input_tokens=0,
                total_input_tokens=20,
                estimated_cost_usd=0.2,
                attempted_key_count=1,
            )

    engine.client = SimpleNamespace(responses=Responses())
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE", "primary")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_PRIMARY_ENDPOINTS", "entry_price,holding_flow")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_V2_SHADOW_ENABLED", "false")
    monkeypatch.setattr(bedrock_nova_provider, "runtime_provider", lambda: Provider())
    monkeypatch.setattr(bedrock_nova_provider, "write_provider_audit_row", lambda row: None)

    for endpoint_name in ("entry_price", "holding_flow"):
        result = GPTSniperEngine._call_openai_safe(
            engine,
            "PROMPT",
            "payload",
            require_json=True,
            context_name="test",
            model_override="gpt-5.4-mini",
            endpoint_name=endpoint_name,
        )
        assert result["reason"] == "lite-primary"
        meta = engine._consume_last_transport_meta()
        assert meta["provider"] == "bedrock"
        assert meta["openai_transport_mode"] == "bedrock_primary"
        assert meta["bedrock_primary_used"] is True
        assert meta["bedrock_failback_used"] is False

    assert provider_endpoints == ["lite", "lite"]
    assert openai_called["value"] is False


def test_bedrock_lite_primary_endpoint_allowlist_keeps_other_tier2_on_openai(monkeypatch):
    engine = _build_engine()
    provider_called = {"value": False}

    def _fake_create(**kwargs):
        return SimpleNamespace(output_text='{"action":"WAIT","score":50}')

    class Provider:
        def converse(self, **kwargs):
            provider_called["value"] = True
            raise AssertionError("should not route non-allowlisted endpoint")

    engine.client = SimpleNamespace(responses=SimpleNamespace(create=_fake_create))
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE", "primary")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_PRIMARY_ENDPOINTS", "entry_price,holding_flow")
    monkeypatch.setattr(bedrock_nova_provider, "runtime_provider", lambda: Provider())
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(openai_module.TRADING_RULES, OPENAI_TRANSPORT_MODE="http"),
    )

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="test",
        model_override="gpt-5.4-mini",
        endpoint_name="other_tier2",
    )

    assert result["action"] == "WAIT"
    assert provider_called["value"] is False


def test_bedrock_lite_primary_enqueues_lite_v2_shadow(monkeypatch):
    engine = _build_engine()
    captured = {}

    class Provider:
        def converse(self, *, prompt, user_input, profile):
            return bedrock_nova_provider.BedrockNovaResult(
                payload={"action": "HOLD", "score": 70, "reason": "lite-v1"},
                raw_text='{"action":"HOLD","score":70,"reason":"lite-v1"}',
                parse_ok=True,
                parse_error="",
                model_id=profile.model_id,
                region_name=profile.region_name,
                key_index=0,
                latency_ms=100,
                input_tokens=20,
                output_tokens=8,
                cache_read_input_tokens=0,
                cache_write_input_tokens=0,
                total_input_tokens=20,
                estimated_cost_usd=0.2,
                attempted_key_count=1,
            )

    def _capture_shadow(**kwargs):
        captured.update(kwargs)
        return True

    from src.engine import bedrock_nova_lite_v2_shadow

    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE", "primary")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_PRIMARY_ENDPOINTS", "holding_flow")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_V2_SHADOW_ENABLED", "true")
    monkeypatch.setattr(bedrock_nova_provider, "runtime_provider", lambda: Provider())
    monkeypatch.setattr(bedrock_nova_provider, "write_provider_audit_row", lambda row: None)
    monkeypatch.setattr(bedrock_nova_lite_v2_shadow, "enqueue_runtime_shadow", _capture_shadow)

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="test",
        model_override="gpt-5.4-mini",
        endpoint_name="holding_flow",
    )

    assert result["action"] == "HOLD"
    assert captured["baseline_payload"]["action"] == "HOLD"
    assert captured["request_meta"]["baseline_bedrock_model_id"] == "apac.amazon.nova-lite-v1:0"


def test_bedrock_primary_does_not_route_other_models(monkeypatch):
    engine = _build_engine()
    captured = {}
    provider_called = {"value": False}

    def _fake_create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(output_text='{"action":"WAIT","score":50}')

    class Provider:
        def converse(self, **kwargs):
            provider_called["value"] = True
            raise AssertionError("should not route")

    engine.client = SimpleNamespace(responses=SimpleNamespace(create=_fake_create))
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_MICRO_ROUTE_MODE", "primary")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE", "primary")
    monkeypatch.setattr(bedrock_nova_provider, "runtime_provider", lambda: Provider())
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(openai_module.TRADING_RULES, OPENAI_TRANSPORT_MODE="http"),
    )

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="test",
        model_override="gpt-5.4",
        endpoint_name="scanner_report",
    )

    assert result["action"] == "WAIT"
    assert provider_called["value"] is False
    assert captured["model"] == "gpt-5.4"


def test_bedrock_primary_failure_falls_back_to_openai(monkeypatch):
    engine = _build_engine()

    def _fake_create(**kwargs):
        return SimpleNamespace(output_text='{"action":"BUY","score":77}')

    class Provider:
        def converse(self, **kwargs):
            raise RuntimeError("429 throttling")

    engine.client = SimpleNamespace(responses=SimpleNamespace(create=_fake_create))
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_MICRO_ROUTE_MODE", "primary")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_PRIMARY_FAILBACK_TO_OPENAI", "true")
    monkeypatch.setattr(bedrock_nova_provider, "runtime_provider", lambda: Provider())
    monkeypatch.setattr(bedrock_nova_provider, "write_provider_audit_row", lambda row: None)
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(openai_module.TRADING_RULES, OPENAI_TRANSPORT_MODE="http"),
    )

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="test",
        model_override="gpt-5-nano",
        endpoint_name="analyze_target",
    )

    assert result["action"] == "BUY"
    meta = engine._consume_last_transport_meta()
    assert meta["bedrock_failback_used"] is True
    assert meta["openai_transport_mode"] == "http"


def test_bedrock_primary_mode_suppresses_same_model_shadow_enqueue(monkeypatch):
    engine = _build_engine()
    request = OpenAIResponseRequest(
        prompt="PROMPT",
        user_input="payload",
        require_json=True,
        context_name="test",
        model_name="gpt-5-nano",
        temperature=None,
        max_output_tokens=128,
        reasoning_effort=None,
        schema_name=None,
        endpoint_name="analyze_target",
        request_id="req-1",
        symbol="000001",
        cache_key="-",
        submitted_at_perf=0.0,
        timeout_ms=1000,
        metadata={},
    )

    from src.engine import bedrock_nova_micro_shadow

    def _raise_if_called(**kwargs):
        raise AssertionError("shadow should not run in primary route mode")

    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_MICRO_SHADOW_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_MICRO_ROUTE_MODE", "primary")
    monkeypatch.setattr(bedrock_nova_micro_shadow, "enqueue_runtime_shadow", _raise_if_called)

    GPTSniperEngine._enqueue_bedrock_nova_micro_runtime_shadow(
        engine,
        request=request,
        openai_payload={"action": "WAIT", "score": 50},
        transport_meta={"openai_request_id": "req-1"},
        roundtrip_ms=100,
    )


def test_openai_holding_flow_uses_flow_schema_and_normalizes_payload(monkeypatch):
    engine = _build_engine()
    captured = {}

    def _fake_call(prompt, user_input, **kwargs):
        captured["prompt"] = prompt
        captured["user_input"] = user_input
        captured["kwargs"] = kwargs
        return {
            "action": "TRIM",
            "score": "67",
            "flow_state": "회복",
            "thesis": "눌림 흡수 중",
            "evidence": ["틱 매수 우위", "분봉 회복"],
            "reason": "단일 순간 약세보다 회복 흐름 우세",
            "next_review_sec": "44",
        }

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)

    result = GPTSniperEngine.evaluate_scalping_holding_flow(
        engine,
        "테스트",
        "005930",
        {"curr": 10000, "v_pw": 130, "buy_ratio": 60, "ask_tot": 1000, "bid_tot": 1200},
        [{"price": 10000, "volume": 10, "side": "BUY"}],
        [
            {"close": 9900, "high": 10020, "low": 9890, "volume": 1000},
            {"close": 10000, "high": 10040, "low": 9950, "volume": 1200},
        ],
        {"profit_rate": -0.3, "peak_profit": 0.4, "held_sec": 75, "current_ai_score": 31, "worsen_pct": 0.8},
        flow_history=[
            {
                "time": "10:00:00",
                "action": "HOLD",
                "flow_state": "흡수",
                "profit_rate": "+0.10",
                "exit_rule": "soft",
                "reason": "매수 흡수 유지",
            }
        ],
        decision_kind="intraday_exit",
        metadata_extra={
            "sim_record_id": "SIM-HOLD-1",
            "sim_parent_record_id": "PARENT-1",
            "entry_adm_candidate_id": "ADM-1",
            "source_event_stage": "holding_flow",
        },
    )

    assert result["action"] == "TRIM"
    assert result["score"] == 67
    assert result["next_review_sec"] == 44
    assert captured["kwargs"]["schema_name"] == "holding_exit_flow_v1"
    assert captured["kwargs"]["endpoint_name"] == "holding_flow"
    assert captured["kwargs"]["metadata_extra"]["sim_record_id"] == "SIM-HOLD-1"
    assert captured["kwargs"]["metadata_extra"]["entry_adm_candidate_id"] == "ADM-1"
    assert "직전 action을 뒤집으려면" in captured["prompt"]
    assert "시스템 guard" in SCALPING_HOLDING_FLOW_SYSTEM_PROMPT
    assert "단일 score cutoff로 자르지 말고" in captured["user_input"]
    assert "reason=매수 흡수 유지" in captured["user_input"]


def test_openai_deterministic_config_is_limited_to_json_path(monkeypatch):
    engine = _build_engine()
    calls = []

    def _fake_create(**kwargs):
        calls.append(kwargs)
        if "text" in kwargs:
            return SimpleNamespace(output_text='{"action":"BUY","score":91,"reason":"json"}')
        return SimpleNamespace(output_text="plain text report")

    engine.client = SimpleNamespace(responses=SimpleNamespace(create=_fake_create))

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_JSON_DETERMINISTIC_CONFIG_ENABLED=True,
            OPENAI_TRANSPORT_MODE="http",
        ),
    )

    GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="json",
        endpoint_name="analyze_target",
        symbol="000001",
    )
    GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=False,
        context_name="text",
        endpoint_name="realtime_report",
        symbol="000001",
    )

    assert calls[0]["temperature"] == 0.0
    assert "text" in calls[0]
    assert calls[1]["temperature"] == 0.7
    assert "text" not in calls[1]


def test_openai_gpt5_models_omit_temperature(monkeypatch):
    engine = _build_engine()
    engine.current_model_name = "gpt-5-nano"
    calls = []

    def _fake_create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(output_text='{"action":"WAIT","score":50,"reason":"ok"}')

    engine.client = SimpleNamespace(responses=SimpleNamespace(create=_fake_create))

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_JSON_DETERMINISTIC_CONFIG_ENABLED=True,
            OPENAI_TRANSPORT_MODE="http",
        ),
    )

    GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="json",
        endpoint_name="analyze_target",
        symbol="000001",
    )

    assert calls[0]["model"] == "gpt-5-nano"
    assert "temperature" not in calls[0]
    assert "json" in calls[0]["input"].lower()
    assert calls[0]["max_output_tokens"] == 512
    assert calls[0]["reasoning"] == {"effort": "minimal"}


def test_openai_usage_meta_is_exposed_for_pipeline_events(monkeypatch):
    engine = _build_engine()

    def _fake_create(**kwargs):
        return SimpleNamespace(
            output_text='{"action":"WAIT","score":50,"reason":"ok"}',
            usage=SimpleNamespace(
                input_tokens=1234,
                output_tokens=56,
                total_tokens=1290,
                input_tokens_details=SimpleNamespace(cached_tokens=120),
                output_tokens_details=SimpleNamespace(reasoning_tokens=8),
            ),
        )

    engine.client = SimpleNamespace(responses=SimpleNamespace(create=_fake_create))

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_TRANSPORT_MODE="http",
        ),
    )

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="json",
        endpoint_name="analyze_target",
        symbol="000001",
    )
    result = engine._merge_last_transport_meta(result)

    assert result["action"] == "WAIT"
    assert result["openai_input_tokens"] == 1234
    assert result["openai_output_tokens"] == 56
    assert result["openai_total_tokens"] == 1290
    assert result["openai_cached_input_tokens"] == 120
    assert result["openai_reasoning_tokens"] == 8


def test_openai_reasoning_effort_auto_uses_none_for_gpt54_mini(monkeypatch):
    engine = _build_engine()
    engine.current_model_name = "gpt-5.4-mini"
    calls = []

    def _fake_create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(output_text='{"action":"WAIT","score":50,"reason":"ok"}')

    engine.client = SimpleNamespace(responses=SimpleNamespace(create=_fake_create))

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_REASONING_EFFORT="auto",
            OPENAI_TRANSPORT_MODE="http",
        ),
    )

    GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="json",
        endpoint_name="analyze_target",
        symbol="000001",
    )

    assert calls[0]["reasoning"] == {"effort": "none"}


def test_openai_scalping_market_data_uses_compact_json_payload(monkeypatch):
    engine = _build_engine()

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_SCALPING_COMPACT_INPUT_ENABLED=True,
        ),
    )

    payload = engine._format_market_data(_sample_ws_data(), _sample_ticks(), _sample_candles())
    parsed = json.loads(payload)

    assert payload.startswith("{")
    assert '"features":' in payload
    assert '"recent_ticks_latest_first":' in payload
    assert "derived" not in parsed
    assert "tick_summary" not in payload
    assert "volume_analysis" not in payload
    assert "orderbook_imbalance" not in payload
    assert "drawdown_from_day_high" not in payload
    assert parsed["current"]["distance_from_day_high_pct"] == parsed["features"]["distance_from_day_high_pct"]
    assert "최근 10틱 상세 내역" not in payload


def test_openai_request_payload_omits_previous_response_id_by_default():
    engine = _build_engine()

    request = engine._build_openai_response_request(
        prompt="PROMPT",
        user_input="payload",
        require_json=True,
        context_name="ctx",
        model_name="gpt-fast",
        temperature=0.0,
        schema_name="entry_v1",
        endpoint_name="analyze_target",
        symbol="005930",
        cache_key="abc",
    )
    payload = request.build_provider_payload(use_schema_registry=False)

    assert "previous_response_id" not in payload
    assert payload["metadata"]["request_id"] == request.request_id


def test_openai_analyze_target_timeout_rejects_buy_side_when_enabled(monkeypatch):
    engine = _build_engine()

    def _raise(*args, **kwargs):
        raise TimeoutError("ws timeout")

    monkeypatch.setattr(engine, "_call_openai_safe", _raise)
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(openai_module.TRADING_RULES, OPENAI_ENTRY_TIMEOUT_REJECT_ENABLED=True),
    )

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
    assert result["ai_parse_fail"] is True


def test_openai_responses_ws_pool_uses_round_robin_workers(monkeypatch):
    calls = []

    class _StubWorker:
        def __init__(self, *, worker_id, api_key, metrics_callback):
            self.worker_id = worker_id
            self.jobs = []
            calls.append(self)

        def submit(self, job):
            self.jobs.append(job.request.request_id)
            return OpenAITransportResult(payload={"worker_id": self.worker_id}, transport_mode="responses_ws", ws_used=True)

        def close(self):
            return None

    monkeypatch.setattr(openai_module, "OpenAIResponsesWSWorker", _StubWorker)

    pool = OpenAIResponsesWSPool(api_keys=["key-a"], pool_size=2, metrics_callback=None)

    for idx in range(3):
        request = OpenAIResponseRequest(
            prompt="PROMPT",
            user_input="payload",
            require_json=True,
            context_name="ctx",
            model_name="gpt-fast",
            temperature=0.0,
            schema_name="entry_v1",
            endpoint_name="analyze_target",
            request_id=f"req-{idx}",
            symbol="005930",
            cache_key="-",
            submitted_at_perf=0.0,
            timeout_ms=700,
        )
        pool.submit(request, use_schema_registry=False)

    assert len(calls[0].jobs) == 2
    assert len(calls[1].jobs) == 1


def test_openai_call_falls_back_from_ws_to_http(monkeypatch):
    engine = _build_engine()
    engine.client = SimpleNamespace(responses=SimpleNamespace(create=lambda **kwargs: None))

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_TRANSPORT_MODE="responses_ws",
            OPENAI_RESPONSES_WS_ENABLED=True,
        ),
    )
    monkeypatch.setattr(engine, "_call_openai_responses_ws", lambda request: (_ for _ in ()).throw(TimeoutError("ws timeout")))
    monkeypatch.setattr(
        engine,
        "_call_openai_responses_http",
        lambda request: OpenAITransportResult(
            payload={"action": "BUY", "score": 88, "reason": "http fallback"},
            transport_mode="http",
            ws_used=False,
            ws_http_fallback=True,
            roundtrip_ms=15,
        ),
    )

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="test",
        schema_name="entry_v1",
        endpoint_name="analyze_target",
        symbol="005930",
    )
    meta = engine._consume_last_transport_meta()

    assert result["action"] == "BUY"
    assert meta["openai_ws_http_fallback"] is True
    assert meta["openai_transport_mode"] == "http"


def test_openai_ws_connection_closed_ok_fallback_logs_info_not_error(monkeypatch):
    engine = _build_engine()
    engine.client = SimpleNamespace(responses=SimpleNamespace(create=lambda **kwargs: None))
    log_info_calls = []
    log_error_calls = []

    class ConnectionClosedOK(Exception):
        pass

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_TRANSPORT_MODE="responses_ws",
            OPENAI_RESPONSES_WS_ENABLED=True,
        ),
    )
    monkeypatch.setattr(
        engine,
        "_call_openai_responses_ws",
        lambda request: (_ for _ in ()).throw(
            ConnectionClosedOK("received 1000 (OK); then sent 1000 (OK)")
        ),
    )
    monkeypatch.setattr(
        engine,
        "_call_openai_responses_http",
        lambda request: OpenAITransportResult(
            payload={"action": "WAIT", "score": 62, "reason": "http fallback"},
            transport_mode="http",
            ws_used=False,
            ws_http_fallback=True,
            roundtrip_ms=15,
        ),
    )
    monkeypatch.setattr(openai_module, "log_info", lambda msg, **kwargs: log_info_calls.append(msg))
    monkeypatch.setattr(openai_module, "log_error", lambda msg, **kwargs: log_error_calls.append(msg))

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="test",
        schema_name="entry_v1",
        endpoint_name="analyze_target",
        symbol="005930",
    )
    meta = engine._consume_last_transport_meta()

    assert result["action"] == "WAIT"
    assert meta["openai_ws_http_fallback"] is True
    assert meta["openai_ws_error_type"] == "ConnectionClosedOK"
    assert any("[OpenAI WS fallback]" in msg for msg in log_info_calls)
    assert not any("[OpenAI WS fallback]" in msg for msg in log_error_calls)


def test_openai_ws_missing_close_frame_fallback_logs_info_not_error(monkeypatch):
    engine = _build_engine()
    engine.client = SimpleNamespace(responses=SimpleNamespace(create=lambda **kwargs: None))
    log_info_calls = []
    log_error_calls = []

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_TRANSPORT_MODE="responses_ws",
            OPENAI_RESPONSES_WS_ENABLED=True,
        ),
    )
    monkeypatch.setattr(
        engine,
        "_call_openai_responses_ws",
        lambda request: (_ for _ in ()).throw(RuntimeError("no close frame received or sent")),
    )
    monkeypatch.setattr(
        engine,
        "_call_openai_responses_http",
        lambda request: OpenAITransportResult(
            payload={"action": "WAIT", "score": 62, "reason": "http fallback"},
            transport_mode="http",
            ws_used=False,
            ws_http_fallback=True,
            roundtrip_ms=15,
        ),
    )
    monkeypatch.setattr(openai_module, "log_info", lambda msg, **kwargs: log_info_calls.append(msg))
    monkeypatch.setattr(openai_module, "log_error", lambda msg, **kwargs: log_error_calls.append(msg))

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="test",
        schema_name="entry_v1",
        endpoint_name="analyze_target",
        symbol="005930",
    )
    meta = engine._consume_last_transport_meta()

    assert result["action"] == "WAIT"
    assert meta["openai_ws_http_fallback"] is True
    assert meta["openai_ws_error_type"] == "RuntimeError"
    assert any("[OpenAI WS fallback]" in msg for msg in log_info_calls)
    assert not any("[OpenAI WS fallback]" in msg for msg in log_error_calls)


def test_openai_ws_hot_path_does_not_take_http_api_lock(monkeypatch):
    engine = _build_engine()

    class FailingLock:
        def __enter__(self):
            raise AssertionError("WS hot path must not take the HTTP API lock")

        def __exit__(self, exc_type, exc, tb):
            return False

    engine.api_call_lock = FailingLock()
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_TRANSPORT_MODE="responses_ws",
            OPENAI_RESPONSES_WS_ENABLED=True,
        ),
    )
    monkeypatch.setattr(
        engine,
        "_call_openai_responses_ws",
        lambda request: OpenAITransportResult(
            payload={"action": "BUY", "score": 91, "reason": "ws path"},
            transport_mode="responses_ws",
            ws_used=True,
            ws_http_fallback=False,
            queue_wait_ms=3,
            roundtrip_ms=120,
        ),
    )

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="test",
        schema_name="entry_v1",
        endpoint_name="analyze_target",
        symbol="005930",
    )
    meta = engine._consume_last_transport_meta()

    assert result["action"] == "BUY"
    assert meta["openai_transport_mode"] == "responses_ws"
    assert meta["openai_ws_used"] is True
    assert meta["openai_ws_roundtrip_ms"] == 120


def test_openai_ws_entry_price_endpoint_uses_ws_transport(monkeypatch):
    engine = _build_engine()
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_TRANSPORT_MODE="responses_ws",
            OPENAI_RESPONSES_WS_ENABLED=True,
        ),
    )
    monkeypatch.setattr(
        engine,
        "_call_openai_responses_ws",
        lambda request: OpenAITransportResult(
            payload={"action": "USE_DEFENSIVE", "confidence": 0.7, "price": 70000},
            transport_mode="responses_ws",
            ws_used=True,
            ws_http_fallback=False,
            roundtrip_ms=95,
        ),
    )

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="test_entry_price",
        schema_name="entry_price_v1",
        endpoint_name="entry_price",
        symbol="005930",
    )
    meta = engine._consume_last_transport_meta()

    assert result["action"] == "USE_DEFENSIVE"
    assert meta["openai_transport_mode"] == "responses_ws"
    assert meta["openai_ws_used"] is True
    assert meta["openai_ws_http_fallback"] is False


def test_openai_invalid_prompt_retries_with_minimal_numeric_prompt(monkeypatch):
    engine = _build_engine()
    calls = []

    def _create(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise Exception(
                "Error code: 400 - {'error': {'code': 'invalid_prompt', 'message': 'Invalid prompt'}}"
            )
        return SimpleNamespace(output_text='{"action":"WAIT","score":50,"reason":"numeric retry"}')

    engine.client = SimpleNamespace(responses=SimpleNamespace(create=_create))

    result = engine._call_openai_safe(
        "원본 프롬프트",
        '{"features":{"buy_pressure_10t":55.0}}',
        require_json=True,
        context_name="삼성물산(SCALPING:scalping_entry)",
        schema_name="entry_v1",
        endpoint_name="analyze_target",
        symbol="028260",
    )

    assert result["action"] == "WAIT"
    assert len(calls) == 2
    assert calls[1]["metadata"]["invalid_prompt_retry"] == "true"
    assert "Use only the numeric fields" in calls[1]["instructions"]
    assert "원본 프롬프트" not in calls[1]["instructions"]


def test_openai_ws_request_id_mismatch_fails_closed_without_http_fallback(monkeypatch):
    engine = _build_engine()

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_TRANSPORT_MODE="responses_ws",
            OPENAI_RESPONSES_WS_ENABLED=True,
            OPENAI_ENTRY_TIMEOUT_REJECT_ENABLED=True,
        ),
    )
    monkeypatch.setattr(
        engine,
        "_call_openai_responses_ws",
        lambda request: (_ for _ in ()).throw(OpenAIWSRequestIdMismatchError("request_id mismatch")),
    )

    def _unexpected_http_fallback(request):
        raise AssertionError("request_id mismatch must not be converted to HTTP fallback")

    monkeypatch.setattr(engine, "_call_openai_responses_http", _unexpected_http_fallback)

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
    assert result["ai_parse_fail"] is True
    assert result["openai_transport_mode"] == "responses_ws"
    assert result["openai_ws_used"] is True
    assert result["openai_ws_http_fallback"] is False
    assert result["openai_ws_error_type"] == "OpenAIWSRequestIdMismatchError"
