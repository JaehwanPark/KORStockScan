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
from src.engine.ai_prompt_contracts import SCALPING_HOLDING_FLOW_SYSTEM_PROMPT
from src.engine.ai_response_contracts import build_openai_response_text_format
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
    engine._annotate_analysis_result = GPTSniperEngine._annotate_analysis_result.__get__(engine, GPTSniperEngine)
    return engine


def _has_hangul(text: str) -> bool:
    return any("\uac00" <= char <= "\ud7a3" for char in text)


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


def _entry_price_compaction_sample(idx):
    base = 10000 + (idx % 37) * 120
    best_bid = base - (idx % 3) * 5
    best_ask = best_bid + 5 + (idx % 4) * 5
    ws_data = {
        "curr": base,
        "current_price": base,
        "v_pw": 95.0 + (idx % 80),
        "buy_ratio": 35.0 + (idx % 60),
        "fluctuation": round(((idx % 21) - 10) / 10, 2),
        "ask_tot": 100000 + idx * 73,
        "bid_tot": 90000 + idx * 67,
        "net_ask_depth": -5000 + idx,
        "ask_depth_ratio": 80 + (idx % 40),
        "memo": "수급 확인 " * 10,
        "unused_snapshot": {f"extra_{n}": f"value-{idx}-{n}" for n in range(20)},
        "orderbook": {
            "asks": [
                {"price": best_ask + level * 5, "volume": 1000 + idx + level, "unused": "ask-detail" * 4}
                for level in range(10)
            ],
            "bids": [
                {"price": best_bid - level * 5, "volume": 900 + idx + level, "unused": "bid-detail" * 4}
                for level in range(10)
            ],
        },
    }
    ticks = [
        {
            "time": f"09:{(idx + n) % 60:02d}:{n % 60:02d}",
            "price": base + ((n % 5) - 2) * 5,
            "volume": 100 + idx + n,
            "dir": "BUY" if (idx + n) % 3 else "SELL",
            "strength": 100 + ((idx + n) % 70),
            "unused_tick_blob": "tick-noise" * 8,
        }
        for n in range(20)
    ]
    candles = [
        {
            "체결시간": f"09:{n % 60:02d}:00",
            "시가": base - 20 + n,
            "현재가": base - 10 + n,
            "고가": base + 30 + n,
            "저가": base - 40 + n,
            "거래량": 1000 + idx * 3 + n * 10,
            "unused_candle_blob": "candle-noise" * 8,
        }
        for n in range(20)
    ]
    price_ctx = {
        "strategy": "SCALPING",
        "position_tag": "main",
        "current_price": base,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "reference_target_price": best_bid,
        "defensive_order_price": best_bid - 5,
        "normal_defensive_order_price": best_bid - 10,
        "resolved_order_price": best_bid - 5,
        "resolution_reason": "latency_guarded_defensive",
        "price_below_bid_bps": 4,
        "reference_target_below_bid_bps": 0,
        "latency_state": "SAFE" if idx % 5 else "CAUTION",
        "ws_age_ms": 120 + idx,
        "ws_jitter_ms": idx % 40,
        "spread_ratio": round((best_ask - best_bid) / max(best_bid, 1), 6),
        "quote_stale": False,
        "signal_score": 65 + (idx % 30),
        "irrelevant_price_context": {f"ctx_extra_{n}": "ctx-noise" * 5 for n in range(20)},
        "orderbook_micro": {
            "ready": True,
            "reason": "ok",
            "micro_state": ["bullish", "neutral", "bearish", "insufficient"][idx % 4],
            "qi": round(((idx % 20) - 10) / 10, 3),
            "ofi_norm": round(((idx % 30) - 15) / 10, 3),
            "ofi_z": round(((idx % 25) - 12) / 10, 3),
            "top_depth_ratio": round(0.8 + (idx % 20) / 20, 3),
            "spread_bp": 5 + (idx % 15),
            "spread_ticks": 1 + (idx % 3),
            "sample_quote_count": 20 + idx,
            "ofi_threshold_source": "bucket",
            "ofi_threshold_bucket_key": f"spread={idx % 4}|price={idx % 5}",
            "ofi_calibration_warning": "",
            **{f"micro_extra_{n}": "micro-noise" * 5 for n in range(25)},
        },
    }
    return ws_data, ticks, candles, price_ctx


def _entry_price_fake_model_output(user_input):
    payload = json.loads(user_input)
    if "ws_data" in payload:
        current = payload.get("ws_data") or {}
        price_ctx = payload.get("price_context") or {}
    else:
        current = payload.get("current") or {}
        price_ctx = payload.get("price_context") or {}

    micro = price_ctx.get("orderbook_micro") or {}
    latency_guard = price_ctx.get("latency_guard") or {}
    entry_guard = price_ctx.get("entry_price_guard") or {}

    buy_ratio = float(current.get("buy_ratio") or 0.0)
    micro_state = str(micro.get("micro_state") or "insufficient")
    quote_stale = bool(price_ctx.get("quote_stale") if "quote_stale" in price_ctx else latency_guard.get("quote_stale"))
    latency_state = str(price_ctx.get("latency_state") or latency_guard.get("latency_state") or "")
    defensive_price = int(float(price_ctx.get("defensive_order_price") or 0))
    reference_price = int(float(price_ctx.get("reference_target_price") or 0))
    resolved_price = int(float(price_ctx.get("resolved_order_price") or defensive_price or 0))
    spread = int(float(price_ctx.get("spread") or 0))
    if spread <= 0:
        best_ask = int(float(price_ctx.get("best_ask") or 0))
        best_bid = int(float(price_ctx.get("best_bid") or 0))
        spread = max(0, best_ask - best_bid)

    if quote_stale or (micro_state == "bearish" and latency_state == "CAUTION"):
        return {
            "action": "SKIP",
            "order_price": 0,
            "confidence": 88,
            "reason": "stale or bearish micro context",
            "max_wait_sec": 30,
        }
    if micro_state == "bullish" and buy_ratio >= 55 and reference_price > 0:
        return {
            "action": "USE_REFERENCE",
            "order_price": reference_price,
            "confidence": 82,
            "reason": "bullish micro context supports reference",
            "max_wait_sec": 45,
        }
    if spread >= 15 and resolved_price > 0:
        return {
            "action": "IMPROVE_LIMIT",
            "order_price": resolved_price,
            "confidence": 76,
            "reason": "wide spread supports improved limit",
            "max_wait_sec": 60,
        }
    return {
        "action": "USE_DEFENSIVE",
        "order_price": defensive_price or resolved_price,
        "confidence": 90,
        "reason": "defensive price is suitable",
        "max_wait_sec": 30,
    }


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
    assert captured["text"]["format"]["schema"] == build_openai_response_text_format("condition_entry_v1")[
        "schema"
    ]
    assert OPENAI_PROMPT_CONTRACT_MARKER in captured["instructions"]
    assert "Control language: English" in captured["instructions"]
    assert "Domain glossary for interpretation" in captured["instructions"]
    assert "Preserve all raw enum labels" in captured["instructions"]
    assert not _has_hangul(captured["instructions"])
    assert "PROMPT" in captured["instructions"]


def test_gpt5_nano_always_uses_openai_after_micro_removal(monkeypatch):
    engine = _build_engine()
    provider_called = {"value": False}

    def _fake_create(**kwargs):
        return SimpleNamespace(output_text='{"action":"WAIT","score":61,"reason":"openai"}')

    class Provider:
        def converse(self, **kwargs):
            provider_called["value"] = True
            raise AssertionError("gpt-5-nano must not route to Bedrock")

    engine.client = SimpleNamespace(responses=SimpleNamespace(create=_fake_create))
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE", "shadow")
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
        model_override="gpt-5-nano",
        endpoint_name="analyze_target",
    )

    assert result["action"] == "WAIT"
    assert result["reason"] == "openai"
    assert provider_called["value"] is False
    meta = engine._consume_last_transport_meta()
    assert meta["openai_transport_mode"] == "http"
    assert "bedrock_primary_used" not in meta


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


def test_lite_primary_holding_flow_does_not_call_openai(monkeypatch):
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
    assert result["reason"] == "lite-primary"
    meta = engine._consume_last_transport_meta()
    assert meta["provider"] == "bedrock"
    assert meta["openai_transport_mode"] == "bedrock_primary"
    assert meta["bedrock_primary_used"] is True
    assert meta["bedrock_failback_used"] is False

    assert provider_endpoints == ["lite"]
    assert openai_called["value"] is False


def test_entry_price_qwen_primary_does_not_call_openai(monkeypatch):
    engine = _build_engine()
    captured = {}
    openai_called = {"value": False}

    class Responses:
        def create(self, **kwargs):
            openai_called["value"] = True
            raise AssertionError("OpenAI must not be called for entry_price Qwen primary")

    class Provider:
        def converse(self, *, prompt, user_input, profile):
            captured["family"] = profile.family
            captured["model_id"] = profile.model_id
            return bedrock_nova_provider.BedrockNovaResult(
                payload={"action": "USE_REFERENCE", "order_price": 10100, "confidence": 72, "reason": "qwen"},
                raw_text='{"action":"USE_REFERENCE","order_price":10100,"confidence":72,"reason":"qwen"}',
                parse_ok=True,
                parse_error="",
                model_id=profile.model_id,
                region_name=profile.region_name,
                key_index=0,
                latency_ms=111,
                input_tokens=20,
                output_tokens=8,
                cache_read_input_tokens=0,
                cache_write_input_tokens=0,
                total_input_tokens=20,
                estimated_cost_usd=0.0,
                attempted_key_count=1,
            )

    engine.client = SimpleNamespace(responses=Responses())
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_ROUTE_MODE", "primary")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_PRIMARY_FAMILY", "qwen3_32b")
    monkeypatch.setattr(bedrock_nova_provider, "runtime_provider", lambda: Provider())
    monkeypatch.setattr(bedrock_nova_provider, "write_provider_audit_row", lambda row: None)

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="test",
        model_override="gpt-5.4-mini",
        endpoint_name="entry_price",
    )

    assert result["reason"] == "qwen"
    assert captured["family"] == "qwen3_32b"
    meta = engine._consume_last_transport_meta()
    assert meta["openai_transport_mode"] == "bedrock_primary"
    assert meta["bedrock_model_family"] == "qwen3_32b"
    assert meta["bedrock_primary_family"] == "qwen3_32b"
    assert meta["bedrock_primary_used"] is True
    assert meta["bedrock_failback_used"] is False
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
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE", "primary")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_PRIMARY_ENDPOINTS", "holding_flow")
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
        model_override="gpt-5.4-mini",
        endpoint_name="holding_flow",
    )

    assert result["action"] == "BUY"
    meta = engine._consume_last_transport_meta()
    assert meta["bedrock_failback_used"] is True
    assert meta["openai_transport_mode"] == "http"


def test_entry_price_qwen_parse_failure_falls_back_to_nova_lite_v2(monkeypatch):
    engine = _build_engine()
    families = []
    audit_rows = []
    openai_called = {"value": False}

    class Responses:
        def create(self, **kwargs):
            openai_called["value"] = True
            raise AssertionError("OpenAI must not be called for entry_price Qwen failback")

    class Provider:
        def converse(self, *, prompt, user_input, profile):
            families.append(profile.family)
            if profile.family == "qwen3_32b":
                return bedrock_nova_provider.BedrockNovaResult(
                    payload={},
                    raw_text='{"action":"USE_REFERENCE",',
                    parse_ok=False,
                    parse_error="JSONDecodeError",
                    model_id=profile.model_id,
                    region_name=profile.region_name,
                    key_index=1,
                    latency_ms=100,
                    input_tokens=20,
                    output_tokens=8,
                    cache_read_input_tokens=0,
                    cache_write_input_tokens=0,
                    total_input_tokens=20,
                    estimated_cost_usd=0.0,
                    attempted_key_count=2,
                )
            return bedrock_nova_provider.BedrockNovaResult(
                payload={"action": "USE_DEFENSIVE", "order_price": 9900, "confidence": 80, "reason": "nova"},
                raw_text='{"action":"USE_DEFENSIVE","order_price":9900,"confidence":80,"reason":"nova"}',
                parse_ok=True,
                parse_error="",
                model_id=profile.model_id,
                region_name=profile.region_name,
                key_index=0,
                latency_ms=120,
                input_tokens=22,
                output_tokens=8,
                cache_read_input_tokens=0,
                cache_write_input_tokens=0,
                total_input_tokens=22,
                estimated_cost_usd=0.0,
                attempted_key_count=1,
            )

    engine.client = SimpleNamespace(responses=Responses())
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_ROUTE_MODE", "primary")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_PRIMARY_FAMILY", "qwen3_32b")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_FAILBACK_FAMILY", "lite_v2")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_FAILBACK_ENABLED", "true")
    monkeypatch.setattr(bedrock_nova_provider, "runtime_provider", lambda: Provider())
    monkeypatch.setattr(bedrock_nova_provider, "write_provider_audit_row", audit_rows.append)

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="test",
        model_override="gpt-5.4-mini",
        endpoint_name="entry_price",
    )

    assert result["reason"] == "nova"
    assert families == ["qwen3_32b", "lite_v2"]
    meta = engine._consume_last_transport_meta()
    assert meta["bedrock_primary_used"] is False
    assert meta["bedrock_failback_used"] is True
    assert meta["bedrock_primary_family"] == "qwen3_32b"
    assert meta["bedrock_failback_family"] == "lite_v2"
    assert meta["bedrock_model_family"] == "lite_v2"
    assert openai_called["value"] is False
    assert any(row["bedrock_primary_error_type"] == "BedrockNovaProviderError" for row in audit_rows)
    assert any(
        row["decision_authority"] == "runtime_primary_with_bedrock_failback_defensive_close" for row in audit_rows
    )
    assert any(row["bedrock_attempted_key_count"] == 2 for row in audit_rows)


def test_entry_price_qwen_and_nova_fail_does_not_fall_back_to_openai(monkeypatch):
    engine = _build_engine()
    families = []
    openai_called = {"value": False}

    class Responses:
        def create(self, **kwargs):
            openai_called["value"] = True
            raise AssertionError("OpenAI must not be called when entry_price Bedrock chain fails")

    class Provider:
        def converse(self, *, prompt, user_input, profile):
            families.append(profile.family)
            raise RuntimeError(f"{profile.family} unavailable")

    engine.client = SimpleNamespace(responses=Responses())
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_ROUTE_MODE", "primary")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_PRIMARY_FAMILY", "qwen3_32b")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_FAILBACK_FAMILY", "lite_v2")
    monkeypatch.setattr(bedrock_nova_provider, "runtime_provider", lambda: Provider())
    monkeypatch.setattr(bedrock_nova_provider, "write_provider_audit_row", lambda row: None)

    try:
        GPTSniperEngine._call_openai_safe(
            engine,
            "PROMPT",
            "payload",
            require_json=True,
            context_name="test",
            model_override="gpt-5.4-mini",
            endpoint_name="entry_price",
        )
    except RuntimeError as exc:
        assert "lite_v2 unavailable" in str(exc)
    else:
        raise AssertionError("entry_price Bedrock chain failure must raise to caller fallback")

    assert families == ["qwen3_32b", "lite_v2"]
    assert openai_called["value"] is False


def test_entry_price_provider_init_failure_records_audit_and_does_not_call_openai(monkeypatch):
    engine = _build_engine()
    audit_rows = []
    openai_called = {"value": False}

    class Responses:
        def create(self, **kwargs):
            openai_called["value"] = True
            raise AssertionError("OpenAI must not be called when entry_price Bedrock provider init fails")

    def _raise_runtime_provider():
        raise RuntimeError("missing bedrock api keys")

    engine.client = SimpleNamespace(responses=Responses())
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_ROUTE_MODE", "primary")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_PRIMARY_FAMILY", "qwen3_32b")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_FAILBACK_FAMILY", "lite_v2")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_FAILBACK_ENABLED", "true")
    monkeypatch.setattr(bedrock_nova_provider, "runtime_provider", _raise_runtime_provider)
    monkeypatch.setattr(bedrock_nova_provider, "write_provider_audit_row", audit_rows.append)

    try:
        GPTSniperEngine._call_openai_safe(
            engine,
            "PROMPT",
            "payload",
            require_json=True,
            context_name="test",
            model_override="gpt-5.4-mini",
            endpoint_name="entry_price",
        )
    except RuntimeError as exc:
        assert "missing bedrock api keys" in str(exc)
    else:
        raise AssertionError("entry_price provider init failure must raise to caller fallback")

    assert openai_called["value"] is False
    assert any(row["bedrock_primary_family"] == "qwen3_32b" for row in audit_rows)
    assert any(row["bedrock_failback_family"] == "lite_v2" for row in audit_rows)
    assert all(row["decision_authority"] == "runtime_primary_with_bedrock_failback_defensive_close" for row in audit_rows)


def test_entry_price_qwen_and_nova_fail_uses_defensive_engine_fallback(monkeypatch):
    engine = _build_engine()
    ws_data, ticks, candles, price_ctx = _entry_price_compaction_sample(1)
    openai_called = {"value": False}

    class Responses:
        def create(self, **kwargs):
            openai_called["value"] = True
            raise AssertionError("OpenAI must not be called when entry_price Bedrock chain fails")

    class Provider:
        def converse(self, *, prompt, user_input, profile):
            raise RuntimeError(f"{profile.family} unavailable")

    engine.client = SimpleNamespace(responses=Responses())
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_ROUTE_MODE", "primary")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_PRIMARY_FAMILY", "qwen3_32b")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_FAILBACK_FAMILY", "lite_v2")
    monkeypatch.setattr(bedrock_nova_provider, "runtime_provider", lambda: Provider())
    monkeypatch.setattr(bedrock_nova_provider, "write_provider_audit_row", lambda row: None)

    result = GPTSniperEngine.evaluate_scalping_entry_price(
        engine,
        "테스트",
        "005930",
        ws_data,
        ticks,
        candles,
        price_ctx,
    )

    assert result["action"] == "USE_DEFENSIVE"
    assert result["reason"] == "ai_failure_use_defensive_fallback"
    assert result["order_price"] == price_ctx["resolved_order_price"]
    assert result["ai_parse_fail"] is True
    assert openai_called["value"] is False


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
    assert result["flow_state"] == "recovery"
    assert result["raw_flow_state"] == "회복"
    assert result["next_review_sec"] == 44
    assert captured["kwargs"]["schema_name"] == "holding_exit_flow_v1"
    assert captured["kwargs"]["endpoint_name"] == "holding_flow"
    assert captured["kwargs"]["metadata_extra"]["sim_record_id"] == "SIM-HOLD-1"
    assert captured["kwargs"]["metadata_extra"]["entry_adm_candidate_id"] == "ADM-1"
    assert "To reverse the previous flow-review action" in captured["prompt"]
    assert "If a system guard applies" in SCALPING_HOLDING_FLOW_SYSTEM_PROMPT
    assert "absorption, recovery, distribution, breakdown, or quiet" in captured["user_input"]
    assert "state=absorption" in captured["user_input"]
    assert not _has_hangul(captured["prompt"])
    assert "Do not cut by a single score cutoff" in captured["user_input"]
    assert "reason=매수 흡수 유지" in captured["user_input"]


def test_openai_entry_price_tier2_input_escapes_non_english_payload(monkeypatch):
    engine = _build_engine()
    captured = {}

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_ENTRY_PRICE_COMPACT_INPUT_ENABLED=True,
        ),
    )

    def _fake_call(prompt, user_input, **kwargs):
        captured["prompt"] = prompt
        captured["user_input"] = user_input
        captured["kwargs"] = kwargs
        return {
            "action": "USE_REFERENCE",
            "order_price": 10000,
            "confidence": 80,
            "reason": "reference price is acceptable",
            "max_wait_sec": 30,
        }

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)

    result = GPTSniperEngine.evaluate_scalping_entry_price(
        engine,
        "테스트",
        "005930",
        {"curr": 10000, "note": "수급 확인"},
        [{"price": 10000, "volume": 10, "side": "BUY"}],
        [{"close": 10000, "high": 10020, "low": 9980, "volume": 1200}],
        {"resolved_order_price": 9900},
    )

    assert result["action"] == "USE_REFERENCE"
    assert captured["kwargs"]["schema_name"] == "entry_price_v1"
    assert captured["kwargs"]["endpoint_name"] == "entry_price"
    assert not _has_hangul(captured["prompt"])
    assert not _has_hangul(captured["user_input"])
    assert "\\ud14c\\uc2a4\\ud2b8" in captured["user_input"]
    assert "note" not in json.loads(captured["user_input"])["ws_data"]


def test_entry_price_compact_input_reduces_payload_across_large_sample(monkeypatch):
    engine = _build_engine()
    samples = [_entry_price_compaction_sample(idx) for idx in range(200)]
    raw_lengths = []
    compact_lengths = []

    for idx, (ws_data, ticks, candles, price_ctx) in enumerate(samples):
        raw_payload = engine._build_scalping_entry_price_raw_input(
            stock_name=f"테스트{idx}",
            stock_code=f"{idx:06d}",
            ws_data=ws_data,
            recent_ticks=ticks,
            recent_candles=candles,
            price_ctx=price_ctx,
        )
        compact_payload = engine._build_scalping_entry_price_user_input(
            stock_name=f"테스트{idx}",
            stock_code=f"{idx:06d}",
            ws_data=ws_data,
            recent_ticks=ticks,
            recent_candles=candles,
            price_ctx=price_ctx,
        )
        parsed = json.loads(compact_payload)
        raw_lengths.append(len(raw_payload))
        compact_lengths.append(len(compact_payload))

        assert parsed["stock_name"] == f"테스트{idx}"
        assert parsed["stock_code"] == f"{idx:06d}"
        assert parsed["ws_data"]["curr"] == ws_data["curr"]
        assert parsed["ws_data"]["v_pw"] == ws_data["v_pw"]
        assert parsed["ws_data"]["buy_ratio"] == ws_data["buy_ratio"]
        assert parsed["ws_data"]["ask_tot"] == ws_data["ask_tot"]
        assert parsed["ws_data"]["bid_tot"] == ws_data["bid_tot"]
        assert len(parsed["ws_data"]["orderbook"]["asks"]) <= 10
        assert len(parsed["ws_data"]["orderbook"]["bids"]) <= 10
        assert parsed["price_context"]["defensive_order_price"] == price_ctx["defensive_order_price"]
        assert parsed["price_context"]["reference_target_price"] == price_ctx["reference_target_price"]
        assert parsed["price_context"]["resolved_order_price"] == price_ctx["resolved_order_price"]
        assert parsed["price_context"]["best_bid"] == price_ctx["best_bid"]
        assert parsed["price_context"]["best_ask"] == price_ctx["best_ask"]
        assert "spread" in parsed["price_context"]
        assert "latency_guard" in parsed["price_context"]
        assert "entry_price_guard" in parsed["price_context"]
        assert parsed["price_context"]["orderbook_micro"]["micro_state"] == price_ctx["orderbook_micro"]["micro_state"]
        assert parsed["price_context"]["orderbook_micro"]["ofi"] == price_ctx["orderbook_micro"]["ofi_norm"]
        assert parsed["price_context"]["orderbook_micro"]["qi"] == price_ctx["orderbook_micro"]["qi"]
        assert parsed["price_context"]["orderbook_micro"]["top_depth_ratio"] == price_ctx["orderbook_micro"]["top_depth_ratio"]
        assert parsed["price_context"]["orderbook_micro"]["spread_bp"] == price_ctx["orderbook_micro"]["spread_bp"]
        assert len(parsed["recent_ticks"]) <= 20
        assert len(parsed["recent_candles"]) <= 20
        assert "unused_snapshot" not in compact_payload
        assert "unused_tick_blob" not in compact_payload
        assert "unused_candle_blob" not in compact_payload

    raw_avg = sum(raw_lengths) / len(raw_lengths)
    compact_avg = sum(compact_lengths) / len(compact_lengths)
    raw_p95 = sorted(raw_lengths)[int(len(raw_lengths) * 0.95) - 1]
    compact_p95 = sorted(compact_lengths)[int(len(compact_lengths) * 0.95) - 1]

    assert compact_avg <= raw_avg * 0.5
    assert compact_p95 <= raw_p95 * 0.6

    captured = {}

    def _fake_call(prompt, user_input, **kwargs):
        captured["prompt"] = prompt
        captured["user_input"] = user_input
        captured["kwargs"] = kwargs
        return {
            "action": "USE_DEFENSIVE",
            "order_price": samples[0][3]["resolved_order_price"],
            "confidence": 90,
            "reason": "defensive price is suitable",
            "max_wait_sec": 30,
        }

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_ENTRY_PRICE_COMPACT_INPUT_ENABLED=True,
        ),
    )
    result = GPTSniperEngine.evaluate_scalping_entry_price(
        engine,
        "테스트0",
        "000000",
        samples[0][0],
        samples[0][1],
        samples[0][2],
        samples[0][3],
    )

    captured_payload = json.loads(captured["user_input"])
    assert result["action"] == "USE_DEFENSIVE"
    assert captured["kwargs"]["schema_name"] == "entry_price_v1"
    assert captured["kwargs"]["endpoint_name"] == "entry_price"
    assert captured["kwargs"]["model_override"] == engine.model_tier2_balanced
    assert captured_payload["price_context"]["resolved_order_price"] == samples[0][3]["resolved_order_price"]


def test_entry_price_runtime_input_defaults_to_compact_and_can_be_disabled(monkeypatch):
    engine = _build_engine()
    ws_data, ticks, candles, price_ctx = _entry_price_compaction_sample(3)

    compact_runtime_payload = engine._build_scalping_entry_price_runtime_input(
        stock_name="테스트3",
        stock_code="000003",
        ws_data=ws_data,
        recent_ticks=ticks,
        recent_candles=candles,
        price_ctx=price_ctx,
    )
    assert "unused_snapshot" not in compact_runtime_payload
    assert json.loads(compact_runtime_payload)["price_context"]["resolved_order_price"] == price_ctx[
        "resolved_order_price"
    ]

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_ENTRY_PRICE_COMPACT_INPUT_ENABLED=False,
        ),
    )
    raw_runtime_payload = engine._build_scalping_entry_price_runtime_input(
        stock_name="테스트3",
        stock_code="000003",
        ws_data=ws_data,
        recent_ticks=ticks,
        recent_candles=candles,
        price_ctx=price_ctx,
    )
    assert "unused_snapshot" in raw_runtime_payload


def test_entry_price_compact_input_preserves_before_after_output_across_large_sample(monkeypatch):
    engine = _build_engine()
    samples = [_entry_price_compaction_sample(idx) for idx in range(200)]
    action_counts = {}

    for idx, (ws_data, ticks, candles, price_ctx) in enumerate(samples):
        raw_payload = engine._build_scalping_entry_price_raw_input(
            stock_name=f"테스트{idx}",
            stock_code=f"{idx:06d}",
            ws_data=ws_data,
            recent_ticks=ticks,
            recent_candles=candles,
            price_ctx=price_ctx,
        )
        compact_payload = engine._build_scalping_entry_price_user_input(
            stock_name=f"테스트{idx}",
            stock_code=f"{idx:06d}",
            ws_data=ws_data,
            recent_ticks=ticks,
            recent_candles=candles,
            price_ctx=price_ctx,
        )
        before_output = _entry_price_fake_model_output(raw_payload)
        after_output = _entry_price_fake_model_output(compact_payload)

        assert after_output == before_output
        action_counts[after_output["action"]] = action_counts.get(after_output["action"], 0) + 1

    assert set(action_counts) >= {"USE_DEFENSIVE", "USE_REFERENCE", "IMPROVE_LIMIT", "SKIP"}

    captured_outputs = {}

    def _fake_call(prompt, user_input, **kwargs):
        output = _entry_price_fake_model_output(user_input)
        captured_outputs["after"] = output
        return output

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_ENTRY_PRICE_COMPACT_INPUT_ENABLED=True,
        ),
    )
    ws_data, ticks, candles, price_ctx = samples[17]
    before_payload = engine._build_scalping_entry_price_raw_input(
        stock_name="테스트17",
        stock_code="000017",
        ws_data=ws_data,
        recent_ticks=ticks,
        recent_candles=candles,
        price_ctx=price_ctx,
    )
    before_output = _entry_price_fake_model_output(before_payload)
    result = GPTSniperEngine.evaluate_scalping_entry_price(
        engine,
        "테스트17",
        "000017",
        ws_data,
        ticks,
        candles,
        price_ctx,
    )

    assert captured_outputs["after"] == before_output
    assert result["action"] == before_output["action"]
    assert result["order_price"] == before_output["order_price"]
    assert result["confidence"] == before_output["confidence"]
    assert result["max_wait_sec"] == before_output["max_wait_sec"]


def test_ai_hot_path_v2_inputs_are_structured_json_across_large_sample(monkeypatch):
    engine = _build_engine()
    samples = [_entry_price_compaction_sample(idx) for idx in range(500)]
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_ENTRY_SCREEN_V2_INPUT_ENABLED=True,
            OPENAI_ENTRY_PRICE_COMPACT_INPUT_ENABLED=True,
            OPENAI_ENTRY_PRICE_V2_INPUT_ENABLED=True,
            OPENAI_HOLDING_FLOW_V2_INPUT_ENABLED=True,
        ),
    )

    for idx, (ws_data, ticks, candles, price_ctx) in enumerate(samples):
        entry_screen = engine._build_entry_screen_v2_payload(ws_data, ticks, candles)
        entry_price = json.loads(
            engine._build_scalping_entry_price_v2_input(
                stock_name=f"테스트{idx}",
                stock_code=f"{idx:06d}",
                ws_data=ws_data,
                recent_ticks=ticks,
                recent_candles=candles,
                price_ctx=price_ctx,
            )
        )
        holding_flow = json.loads(
            engine._build_scalping_holding_flow_v2_context(
                f"테스트{idx}",
                f"{idx:06d}",
                ws_data,
                ticks,
                candles,
                {
                    "exit_rule": "soft_stop",
                    "sell_reason_type": "PROFIT",
                    "buy_price": price_ctx["resolved_order_price"],
                    "curr_price": ws_data["curr"],
                    "profit_rate": ((idx % 11) - 5) / 10,
                    "peak_profit": 1.2 + (idx % 5) / 10,
                    "drawdown": 0.3 + (idx % 3) / 10,
                    "held_sec": 30 + idx,
                    "current_ai_score": 55 + (idx % 40),
                    "worsen_pct": 0.8,
                    "orderbook_micro": price_ctx["orderbook_micro"],
                },
                flow_history=[
                    {
                        "time": "10:00:00",
                        "action": "HOLD",
                        "flow_state": "absorption",
                        "profit_rate": "+0.10",
                        "exit_rule": "soft_stop",
                        "reason": "prior absorption",
                    }
                ],
                decision_kind="intraday_exit",
                matrix_runtime={"prompt_context": "matrix_context"},
                lifecycle_ai_runtime={"prompt_context": "lifecycle_context"},
            )
        )

        assert entry_screen["input_schema"] == "entry_screen_v2"
        assert entry_screen["features"]["packet_version"]
        assert len(entry_screen["recent_ticks_latest_first"]) <= 5
        assert len(entry_screen["recent_candles_latest_window"]) <= 5
        assert "tick_summary" in entry_screen
        assert "candle_summary" in entry_screen
        assert "recent_ticks" not in entry_screen
        assert "recent_candles" not in entry_screen

        assert entry_price["input_schema"] == "entry_price_v2"
        assert entry_price["price_context"]["resolved_order_price"] == price_ctx["resolved_order_price"]
        assert entry_price["candidate_prices"]["defensive_order_price"] == price_ctx["defensive_order_price"]
        assert "quote_change" in entry_price
        assert "fill_probability_hints" in entry_price
        assert len(entry_price["recent_ticks_latest_first"]) <= 5
        assert len(entry_price["recent_candles_latest_window"]) <= 5
        assert "recent_ticks" not in entry_price
        assert "recent_candles" not in entry_price
        assert "unused_snapshot" not in json.dumps(entry_price)
        assert "unused_tick_blob" not in json.dumps(entry_price)
        assert "unused_candle_blob" not in json.dumps(entry_price)

        assert holding_flow["input_schema"] == "holding_flow_v2"
        assert holding_flow["position"]["current_price"] == ws_data["curr"]
        assert holding_flow["deterministic_guard_state"]["system_guards_remain_authoritative"] is True
        assert holding_flow["runtime_advisory_context"]["holding_exit_matrix"] == "matrix_context"
        assert holding_flow["runtime_advisory_context"]["lifecycle_ai"] == "lifecycle_context"
        assert len(holding_flow["recent_ticks_latest_first"]) <= 5
        assert len(holding_flow["recent_candles_latest_window"]) <= 5

    captured = []

    def _fake_call(prompt, user_input, **kwargs):
        captured.append({"prompt": prompt, "user_input": user_input, "kwargs": kwargs})
        if kwargs["schema_name"] == "entry_price_v1":
            return {
                "action": "USE_DEFENSIVE",
                "order_price": samples[0][3]["resolved_order_price"],
                "confidence": 90,
                "reason": "defensive price is suitable",
                "max_wait_sec": 30,
            }
        if kwargs["schema_name"] == "holding_exit_flow_v1":
            return {
                "action": "HOLD",
                "score": 80,
                "flow_state": "absorption",
                "thesis": "absorption remains valid",
                "evidence": ["buy pressure stable"],
                "reason": "flow remains supportive",
                "next_review_sec": 45,
            }
        return {"action": "WAIT", "score": 65, "reason": "mixed entry features"}

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)
    ws_data, ticks, candles, price_ctx = samples[0]
    entry_result = engine.analyze_target("테스트0", ws_data, ticks, candles, prompt_profile="watching")
    entry_price_result = engine.evaluate_scalping_entry_price("테스트0", "000000", ws_data, ticks, candles, price_ctx)
    holding_result = engine.evaluate_scalping_holding_flow(
        "테스트0",
        "000000",
        ws_data,
        ticks,
        candles,
        {"profit_rate": 0.2, "peak_profit": 0.5, "held_sec": 60, "current_ai_score": 70},
    )

    assert [item["kwargs"]["endpoint_name"] for item in captured] == [
        "analyze_target",
        "entry_price",
        "holding_flow",
    ]
    assert [item["kwargs"]["schema_name"] for item in captured] == [
        "entry_v1",
        "entry_price_v1",
        "holding_exit_flow_v1",
    ]
    assert captured[0]["kwargs"]["model_override"] == engine.model_tier1_fast
    assert captured[1]["kwargs"]["model_override"] == engine.model_tier2_balanced
    assert captured[2]["kwargs"]["model_override"] == engine.model_tier2_balanced
    assert json.loads(captured[0]["user_input"])["input_schema"] == "entry_screen_v2"
    assert json.loads(captured[1]["user_input"])["input_schema"] == "entry_price_v2"
    assert json.loads(captured[2]["user_input"])["input_schema"] == "holding_flow_v2"
    assert entry_result["ai_input_schema"] == "entry_screen_v2"
    assert entry_result["ai_input_contract_mode"] == "structured_json"
    assert entry_price_result["ai_input_schema"] == "entry_price_v2"
    assert entry_price_result["ai_input_contract_mode"] == "structured_json"
    assert holding_result["ai_input_schema"] == "holding_flow_v2"
    assert holding_result["ai_input_contract_mode"] == "structured_json"


def test_analyze_target_v2_input_fallback_uses_legacy_context_contract(monkeypatch):
    engine = _build_engine()
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(openai_module.TRADING_RULES, OPENAI_ENTRY_SCREEN_V2_INPUT_ENABLED=True),
    )
    monkeypatch.setattr(
        engine,
        "_format_market_data",
        lambda ws_data, recent_ticks, recent_candles, feature_packet=None: "legacy text payload",
    )

    captured = {}

    def _fake_call(prompt, user_input, **kwargs):
        captured["user_input"] = user_input
        return {"action": "WAIT", "score": 60, "reason": "mixed entry features"}

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)
    result = engine.analyze_target(
        "테스트",
        {"curr": 10000, "orderbook": {"asks": [{"price": 10010, "volume": 100}], "bids": [{"price": 10000, "volume": 100}]}},
        [{"price": 10000, "volume": 10, "side": "BUY"}],
        [{"close": 10000, "high": 10010, "low": 9990, "volume": 100}],
        prompt_profile="watching",
    )

    payload = json.loads(captured["user_input"])
    assert payload["input_schema"] == "entry_screen_v2"
    assert payload["input_build_fallback"] == "legacy_text_payload"
    assert payload["legacy_context"] == "legacy text payload"
    assert "legacy_payload" not in payload
    assert result["ai_input_schema"] == "entry_screen_v2"
    assert result["ai_input_contract_mode"] == "structured_json"
    assert result["ai_input_build_fallback"] == "legacy_text_payload"


def test_analyze_target_swing_input_contract_stays_plain_text_when_v2_enabled(monkeypatch):
    engine = _build_engine()
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(openai_module.TRADING_RULES, OPENAI_ENTRY_SCREEN_V2_INPUT_ENABLED=True),
    )

    captured = {}

    def _fake_call(prompt, user_input, **kwargs):
        captured["user_input"] = user_input
        return {"action": "WAIT", "score": 62, "reason": "swing setup incomplete"}

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)
    result = engine.analyze_target(
        "스윙",
        {"curr": 10000, "fluctuation": 0.4, "v_pw": 110},
        [],
        [{"체결시간": "10:00:00", "현재가": 10000, "거래량": 1000}],
        strategy="KOSPI_ML",
    )

    assert not captured["user_input"].lstrip().startswith("{")
    assert result["ai_input_schema"] == "swing_market_text_v1"
    assert result["ai_input_contract_mode"] == "plain_text"


def test_hot_path_exception_results_keep_input_contract_metadata(monkeypatch):
    engine = _build_engine()
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_ENTRY_SCREEN_V2_INPUT_ENABLED=True,
            OPENAI_ENTRY_PRICE_COMPACT_INPUT_ENABLED=True,
            OPENAI_ENTRY_PRICE_V2_INPUT_ENABLED=True,
            OPENAI_HOLDING_FLOW_V2_INPUT_ENABLED=True,
        ),
    )
    ws_data, ticks, candles, price_ctx = _entry_price_compaction_sample(0)

    def _raise_call(*args, **kwargs):
        raise RuntimeError("transport failed")

    monkeypatch.setattr(engine, "_call_openai_safe", _raise_call)

    entry_result = engine.analyze_target("테스트", ws_data, ticks, candles, prompt_profile="watching")
    entry_price_result = engine.evaluate_scalping_entry_price(
        "테스트",
        "000000",
        ws_data,
        ticks,
        candles,
        price_ctx,
    )
    holding_result = engine.evaluate_scalping_holding_flow(
        "테스트",
        "000000",
        ws_data,
        ticks,
        candles,
        {"profit_rate": 0.2, "peak_profit": 0.5, "held_sec": 60, "current_ai_score": 70},
    )

    assert entry_result["ai_parse_fail"] is True
    assert entry_result["ai_input_schema"] == "entry_screen_v2"
    assert entry_result["ai_input_contract_mode"] == "structured_json"
    assert entry_price_result["ai_parse_fail"] is True
    assert entry_price_result["ai_input_schema"] == "entry_price_v2"
    assert entry_price_result["ai_input_contract_mode"] == "structured_json"
    assert holding_result["ai_parse_fail"] is True
    assert holding_result["ai_input_schema"] == "holding_flow_v2"
    assert holding_result["ai_input_contract_mode"] == "structured_json"


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


def test_openai_legacy_market_data_excludes_price_change_heuristic_ticks(monkeypatch):
    engine = _build_engine()
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_SCALPING_COMPACT_INPUT_ENABLED=False,
            OPENAI_ENTRY_SCREEN_V2_INPUT_ENABLED=False,
        ),
    )
    heuristic_ticks = [
        {
            "time": "09:00:10",
            "price": 10110,
            "volume": 120,
            "dir": "BUY",
            "aggressor_side": "BUY",
            "aggressor_source": "price_change_heuristic",
            "strength": 135.0,
        },
        {
            "time": "09:00:09",
            "price": 10100,
            "volume": 80,
            "dir": "SELL",
            "aggressor_side": "SELL",
            "aggressor_source": "price_change_heuristic",
            "strength": 130.0,
        },
    ]

    payload = engine._format_market_data(_sample_ws_data(), heuristic_ticks, _sample_candles())

    assert "매수 압도율(Buy Pressure): 50.0%" in payload
    assert "매수 0주 vs 매도 0주" in payload
    assert "aggressor source: {'price_change_heuristic': 2}" in payload


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


def test_openai_request_metadata_is_trimmed_to_provider_limit():
    engine = _build_engine()

    metadata_extra = {f"extra_{idx:02d}": str(idx) for idx in range(20)}
    request = engine._build_openai_response_request(
        prompt="PROMPT",
        user_input="payload",
        require_json=True,
        context_name="metadata-trim",
        model_name="gpt-fast",
        temperature=0.0,
        schema_name="entry_v1",
        endpoint_name="analyze_target",
        symbol="005930",
        cache_key="abc",
        metadata_extra=metadata_extra,
    )
    metadata = request.build_provider_payload(use_schema_registry=False)["metadata"]

    assert len(metadata) == openai_module.OPENAI_METADATA_MAX_PROPERTIES
    assert metadata["request_id"] == request.request_id
    assert metadata["endpoint_name"] == "analyze_target"
    assert metadata["schema_name"] == "entry_v1"
    assert metadata["symbol"] == "005930"
    assert metadata["cache_key"] == "abc"
    assert "extra_00" in metadata
    assert "extra_10" in metadata
    assert "extra_11" not in metadata


def test_openai_request_metadata_normalizes_long_property_names():
    engine = _build_engine()

    metadata_extra = {
        "early_accel_strong_bundle_recheck_price_delta_since_first_seen_pct": "0.52",
    }
    request = engine._build_openai_response_request(
        prompt="PROMPT",
        user_input="payload",
        require_json=True,
        context_name="metadata-long-key",
        model_name="gpt-fast",
        temperature=0.0,
        schema_name="entry_v1",
        endpoint_name="analyze_target",
        symbol="005930",
        cache_key="abc",
        metadata_extra=metadata_extra,
    )
    metadata = request.build_provider_payload(use_schema_registry=False)["metadata"]

    assert all(len(key) <= openai_module.OPENAI_METADATA_KEY_MAX_LENGTH for key in metadata)
    normalized_long_keys = [key for key in metadata if key.startswith("early_accel_strong_bundle_recheck_price_delta_since_")]
    assert len(normalized_long_keys) == 1
    assert metadata[normalized_long_keys[0]] == "0.52"


def test_early_accel_strong_bundle_recheck_metadata_context_is_in_prompt_payload():
    engine = _build_engine()

    formatted = engine._append_early_accel_strong_bundle_recheck_context(
        '{"input_schema":"entry_screen_compact_v1","features":{"buy_pressure_10t":71.2}}',
        metadata_extra={
            "early_accel_strong_bundle_recheck": "true",
            "early_accel_strong_bundle_recheck_original_action": "WAIT",
            "early_accel_strong_bundle_recheck_original_score": "72.0",
            "early_accel_strong_bundle_recheck_original_reason_excerpt": "momentum confirmation missing",
            "early_accel_strong_bundle_recheck_scanner_promotion_reason": "strong_bundle",
            "early_accel_strong_bundle_recheck_source_signature": "sig-a",
            "early_accel_strong_bundle_recheck_price_delta_since_first_seen_pct": "0.52",
            "early_accel_strong_bundle_recheck_comparable_flu_delta_since_first_seen": "1.40",
            "early_accel_strong_bundle_recheck_cntr_str_available": "true",
            "early_accel_strong_bundle_recheck_cntr_str": "131.5",
            "early_accel_strong_bundle_recheck_tick_acceleration_ratio": "2.3",
            "early_accel_strong_bundle_recheck_curr_vs_micro_vwap_bp": "8.1",
            "early_accel_strong_bundle_recheck_micro_vwap_available": "true",
            "early_accel_strong_bundle_recheck_minute_candle_context_quality": "fresh_bar_window",
            "early_accel_strong_bundle_recheck_minute_candle_window_fresh": "true",
            "early_accel_strong_bundle_recheck_minute_candle_latest_age_ms": "12000",
            "early_accel_strong_bundle_recheck_buy_pressure_10t": "73.4",
        },
    )
    payload = json.loads(formatted)
    context = payload["early_accel_strong_bundle_recheck_context"]

    assert context["original_action"] == "WAIT"
    assert context["original_score"] == "72.0"
    assert context["price_delta_since_first_seen_pct"] == "0.52"
    assert context["tick_acceleration_ratio"] == "2.3"
    assert context["micro_vwap_available"] == "true"
    assert context["minute_candle_context_quality"] == "fresh_bar_window"
    assert context["minute_candle_window_fresh"] == "true"
    assert context["minute_candle_latest_age_ms"] == "12000"
    assert context["buy_pressure_10t"] == "73.4"


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
