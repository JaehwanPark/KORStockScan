import hashlib
import json
import threading
from dataclasses import replace
from types import SimpleNamespace

import pytest

from src.engine import ai_engine_openai as openai_module
from src.engine.ai_engine_openai import (
    GPTSniperEngine,
    OPENAI_PROMPT_CONTRACT_MARKER,
    OPENAI_SDK_MAX_RETRIES,
    OpenAIResponseRequest,
    OpenAIResponsesWSPool,
    OpenAIResponsesWSWorker,
    OpenAIResponsesHTTPError,
    OpenAITransportResult,
    OpenAIWSRequestIdMismatchError,
)
from src.engine.ai_prompt_contracts import (
    DECISION_QUALITY_DETAILED_PROMPT_VERSION,
    DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
    DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION,
    DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION,
    DECISION_QUALITY_V2_PROMPT_VERSION,
    SCALPING_HOLDING_FLOW_SYSTEM_PROMPT,
    SCALPING_WATCHING_HOT_SYSTEM_PROMPT,
    decision_quality_v2_detailed_system_prompt,
    decision_quality_v2_13_recovery_confirmation_system_prompt,
    decision_quality_v2_14_setup_risk_adjudicator_system_prompt,
    decision_quality_v2_7_probe_system_prompt,
    decision_quality_v2_system_prompt,
)
from src.engine.ai_response_contracts import build_openai_response_text_format
from src.engine.scalping.entry_ai_gate import evaluate_entry_score_role_gate
from src.engine.scalping.entry_setup_evidence import (
    ENTRY_RISK_ADJUDICATION_SCHEMA,
    build_entry_setup_evidence,
)
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
    engine._annotate_analysis_result = (
        GPTSniperEngine._annotate_analysis_result.__get__(engine, GPTSniperEngine)
    )
    return engine


def test_entry_price_context_uses_frozen_packet_without_rebuild(monkeypatch):
    engine = _build_engine()
    monkeypatch.setattr(
        openai_module,
        "extract_scalping_feature_packet",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("frozen provider input must not be recomputed")
        ),
    )

    features = engine._compact_entry_context_features(
        {"curr": 10_020},
        [],
        [],
        price_ctx={
            "entry_context_features": {
                "entry_context_quality": "complete",
                "entry_context_missing_features": "",
                "quote_age_ms": 2_800,
                "quote_stale": False,
            }
        },
    )

    assert features["entry_context_quality"] == "complete"
    assert features["quote_age_ms"] == 2_800
    assert features["quote_stale"] is False


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


def test_openai_runtime_clients_disable_sdk_retries(monkeypatch):
    created_clients = []

    class _FakeOpenAI:
        def __init__(self, **kwargs):
            created_clients.append(kwargs)
            self.responses = SimpleNamespace(connect=lambda: None)

    monkeypatch.setattr(openai_module, "OpenAI", _FakeOpenAI)

    GPTSniperEngine(["main-key"], announce_startup=False)
    worker = OpenAIResponsesWSWorker(
        worker_id=0, api_key="ws-key", metrics_callback=None
    )
    worker.close()

    assert created_clients
    assert [client["max_retries"] for client in created_clients] == [
        OPENAI_SDK_MAX_RETRIES,
        OPENAI_SDK_MAX_RETRIES,
    ]


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


def _allowed_entry_candle_context():
    return {
        "schema": "entry_candle_context_v1",
        "completed_bar_count": 1,
        "bars": [
            {
                "time": "2026-07-30T09:00:00+09:00",
                "open": 10080,
                "high": 10120,
                "low": 10070,
                "close": 10100,
                "volume": 1200,
                "forming": False,
            }
        ],
        "structure": {
            "returns_pct": {"1": 0.1, "3": 0.2, "5": -0.1, "10": -0.2},
            "slopes_pct_per_bar": {"1": 0.1, "3": 0.1, "5": -0.1, "10": -0.1},
            "forming_bar_excluded": True,
        },
        "source_quality": {"status": "pass"},
        "ai_market_snapshot_v1": {
            "schema": "ai_market_snapshot_v1",
            "snapshot_id": "aims-v27-test",
            "stock_code": "005930",
            "effective_venue": "KRX",
            "session_bucket": "krx_regular",
            "ai_input_preflight_v1": {
                "schema": "ai_input_preflight_v1",
                "allowed": True,
                "source_allowed": True,
                "status": "pass",
                "blockers": [],
                "missing_sources": [],
                "venue_consistent": True,
            },
        },
    }


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
                {
                    "price": best_ask + level * 5,
                    "volume": 1000 + idx + level,
                    "unused": "ask-detail" * 4,
                }
                for level in range(10)
            ],
            "bids": [
                {
                    "price": best_bid - level * 5,
                    "volume": 900 + idx + level,
                    "unused": "bid-detail" * 4,
                }
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
        "irrelevant_price_context": {
            f"ctx_extra_{n}": "ctx-noise" * 5 for n in range(20)
        },
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
    buy_ratio = float(current.get("buy_ratio") or 0.0)
    micro_state = str(micro.get("micro_state") or "insufficient")
    quote_stale = bool(
        price_ctx.get("quote_stale")
        if "quote_stale" in price_ctx
        else latency_guard.get("quote_stale")
    )
    latency_state = str(
        price_ctx.get("latency_state") or latency_guard.get("latency_state") or ""
    )
    defensive_price = int(float(price_ctx.get("defensive_order_price") or 0))
    reference_price = int(float(price_ctx.get("reference_target_price") or 0))
    resolved_price = int(
        float(price_ctx.get("resolved_order_price") or defensive_price or 0)
    )
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
    assert (
        captured["text"]["format"]["schema"]
        == build_openai_response_text_format("condition_entry_v1")["schema"]
    )
    assert OPENAI_PROMPT_CONTRACT_MARKER in captured["instructions"]
    assert "Control language: English" in captured["instructions"]
    assert "Domain glossary for interpretation" in captured["instructions"]
    assert "Preserve all raw enum labels" in captured["instructions"]
    assert not _has_hangul(captured["instructions"])
    assert "PROMPT" in captured["instructions"]


def test_unrelated_endpoint_keeps_json_object_when_global_registry_is_disabled(
    monkeypatch,
):
    engine = _build_engine()
    captured = {}

    def _fake_create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(output_text='{"decision":"WAIT"}')

    engine.client = SimpleNamespace(responses=SimpleNamespace(create=_fake_create))
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_RESPONSE_SCHEMA_REGISTRY_ENABLED=False,
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

    assert result["decision"] == "WAIT"
    assert captured["text"]["format"] == {"type": "json_object"}
    meta = engine._consume_last_transport_meta()
    assert meta["openai_response_schema_registry_used"] is False
    assert meta["openai_response_schema_mode"] == "json_object"
    assert meta["openai_response_schema_application"] == ("provider_json_object_openai")
    assert meta["openai_entry_risk_dynamic_fact_schema_applied"] is False


def test_v2_14_forces_dynamic_strict_schema_when_global_registry_is_disabled(
    monkeypatch,
):
    engine = _build_engine()
    captured = {}

    def _fake_create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            output_text=json.dumps(
                {
                    "schema": ENTRY_RISK_ADJUDICATION_SCHEMA,
                    "risk_verdict": "CAUTION",
                    "risk_codes": ["CONFIRMATION_MISSING"],
                    "supporting_fact_ids": ["structural_edge_floor"],
                    "contradicting_fact_ids": ["trigger_confirmation_missing"],
                    "confidence": 74,
                }
            )
        )

    engine.client = SimpleNamespace(responses=SimpleNamespace(create=_fake_create))
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_RESPONSE_SCHEMA_REGISTRY_ENABLED=False,
            OPENAI_TRANSPORT_MODE="http",
        ),
    )
    user_input = json.dumps(
        {
            "input_schema": "entry_setup_v2_14_live_input",
            "entry_setup_evidence_v1": {
                "positive_facts": ["structural_edge_floor"],
                "contradicting_facts": ["trigger_confirmation_missing"],
                "invalidation_facts": ["hard_blocker:source_unusable"],
            },
        }
    )

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        user_input,
        require_json=True,
        context_name="v2.14-test",
        model_override="gpt-5.4-nano",
        schema_name=ENTRY_RISK_ADJUDICATION_SCHEMA,
        endpoint_name="analyze_target",
        symbol="000001",
    )

    response_format = captured["text"]["format"]
    assert result["confidence"] == 74
    assert response_format["type"] == "json_schema"
    assert response_format["strict"] is True
    assert response_format["schema"]["properties"]["confidence"] == {
        "type": "integer",
        "minimum": 0,
        "maximum": 100,
    }
    assert response_format["schema"]["properties"]["supporting_fact_ids"]["items"][
        "enum"
    ] == ["structural_edge_floor"]
    assert response_format["schema"]["properties"]["contradicting_fact_ids"]["items"][
        "enum"
    ] == [
        "trigger_confirmation_missing",
        "hard_blocker:source_unusable",
    ]
    meta = engine._consume_last_transport_meta()
    assert meta["openai_response_schema_registry_used"] is True
    assert meta["openai_response_schema_mode"] == "strict_dynamic_entry_risk"
    assert meta["openai_response_schema_application"] == ("provider_enforced_openai")
    assert (
        meta["openai_response_schema_sha256"]
        == hashlib.sha256(
            json.dumps(
                response_format["schema"],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            ).encode("utf-8")
        ).hexdigest()
    )
    assert meta["openai_entry_risk_dynamic_fact_schema_applied"] is True
    assert meta["expected_semantic_validator_version"] == (
        openai_module.ENTRY_SETUP_RISK_SEMANTIC_VALIDATOR_VERSION
    )
    assert "semantic_validator_version" not in meta


def test_gpt5_nano_always_uses_openai_after_micro_removal(monkeypatch):
    engine = _build_engine()
    provider_called = {"value": False}

    def _fake_create(**kwargs):
        return SimpleNamespace(
            output_text='{"action":"WAIT","score":61,"reason":"openai"}'
        )

    class Provider:
        def converse(self, **kwargs):
            provider_called["value"] = True
            raise AssertionError("gpt-5-nano must not route to Bedrock")

    engine.client = SimpleNamespace(responses=SimpleNamespace(create=_fake_create))
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE", "off")
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


def test_gpt54_nano_always_uses_openai_after_fast_model_update(monkeypatch):
    engine = _build_engine()
    provider_called = {"value": False}

    def _fake_create(**kwargs):
        return SimpleNamespace(
            output_text='{"action":"WAIT","score":61,"reason":"openai"}'
        )

    class Provider:
        def converse(self, **kwargs):
            provider_called["value"] = True
            raise AssertionError("gpt-5.4-nano must not route to Bedrock")

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
        model_override="gpt-5.4-nano",
        endpoint_name="analyze_target",
    )

    assert result["reason"] == "openai"
    assert provider_called["value"] is False
    meta = engine._consume_last_transport_meta()
    assert meta["openai_transport_mode"] == "http"
    assert "bedrock_primary_used" not in meta


def test_scalping_entry_http_override_bypasses_global_ws_with_full_budget(
    monkeypatch,
):
    engine = _build_engine()
    captured_http = []

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
        "_try_bedrock_primary_provider",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        engine,
        "_call_openai_responses_ws",
        lambda request: (_ for _ in ()).throw(
            AssertionError("scalping entry HTTP override must bypass WS")
        ),
    )

    def _fake_http(request):
        captured_http.append(request)
        return OpenAITransportResult(
            payload={"action": "WAIT", "score": 61, "reason": "http primary"},
            transport_mode="http",
            roundtrip_ms=1200,
        )

    monkeypatch.setattr(engine, "_call_openai_responses_http", _fake_http)

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="scalping_entry_http_primary",
        model_override="gpt-5.4-nano",
        schema_name="entry_v1",
        endpoint_name="analyze_target",
        transport_mode_override="http",
        timeout_ms_override=5000,
    )
    meta = engine._consume_last_transport_meta()

    assert result["action"] == "WAIT"
    assert len(captured_http) == 1
    assert captured_http[0].model_name == "gpt-5.4-nano"
    assert captured_http[0].timeout_ms == 5000
    assert meta["openai_transport_requested_mode"] == "http"
    assert meta["openai_transport_mode"] == "http"
    assert meta["openai_model"] == "gpt-5.4-nano"
    assert meta["openai_timeout_budget_ms"] == 5000


def test_bedrock_primary_routes_gpt54_mini_independently(monkeypatch):
    engine = _build_engine()
    captured = {}
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_PRIMARY_BEDROCK_FALLBACK_ENDPOINTS=(),
        ),
    )

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
    monkeypatch.setenv(
        "KORSTOCKSCAN_BEDROCK_NOVA_LITE_PRIMARY_ENDPOINTS", "entry_price,holding_flow"
    )
    monkeypatch.setattr(bedrock_nova_provider, "runtime_provider", lambda: Provider())
    monkeypatch.setattr(
        bedrock_nova_provider, "write_provider_audit_row", lambda row: None
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

    assert result["action"] == "HOLD"
    assert captured["family"] == "lite"
    meta = engine._consume_last_transport_meta()
    assert meta["provider"] == "bedrock"
    assert meta["bedrock_primary_used"] is True
    assert meta["openai_response_schema_application"] == (
        "local_expected_only_not_sent_to_bedrock"
    )


def test_lite_primary_holding_flow_does_not_call_openai(monkeypatch):
    engine = _build_engine()
    provider_endpoints = []
    openai_called = {"value": False}
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_PRIMARY_BEDROCK_FALLBACK_ENDPOINTS=(),
        ),
    )

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
    monkeypatch.setenv(
        "KORSTOCKSCAN_BEDROCK_NOVA_LITE_PRIMARY_ENDPOINTS", "entry_price,holding_flow"
    )
    monkeypatch.setattr(bedrock_nova_provider, "runtime_provider", lambda: Provider())
    monkeypatch.setattr(
        bedrock_nova_provider, "write_provider_audit_row", lambda row: None
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
            raise AssertionError(
                "OpenAI must not be called for entry_price Qwen primary"
            )

    class Provider:
        def converse(self, *, prompt, user_input, profile):
            captured["family"] = profile.family
            captured["model_id"] = profile.model_id
            return bedrock_nova_provider.BedrockNovaResult(
                payload={
                    "action": "USE_REFERENCE",
                    "order_price": 10100,
                    "confidence": 72,
                    "reason": "qwen",
                },
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
    monkeypatch.setattr(
        bedrock_nova_provider, "write_provider_audit_row", lambda row: None
    )

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


def test_bedrock_lite_primary_endpoint_allowlist_keeps_other_tier2_on_openai(
    monkeypatch,
):
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
    monkeypatch.setenv(
        "KORSTOCKSCAN_BEDROCK_NOVA_LITE_PRIMARY_ENDPOINTS", "entry_price,holding_flow"
    )
    monkeypatch.setattr(bedrock_nova_provider, "runtime_provider", lambda: Provider())
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_TRANSPORT_MODE="http",
            OPENAI_PRIMARY_BEDROCK_FALLBACK_ENDPOINTS=(),
        ),
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
    monkeypatch.setenv(
        "KORSTOCKSCAN_BEDROCK_NOVA_LITE_PRIMARY_ENDPOINTS", "holding_flow"
    )
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_PRIMARY_FAILBACK_TO_OPENAI", "true")
    monkeypatch.setattr(bedrock_nova_provider, "runtime_provider", lambda: Provider())
    monkeypatch.setattr(
        bedrock_nova_provider, "write_provider_audit_row", lambda row: None
    )
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_TRANSPORT_MODE="http",
            OPENAI_PRIMARY_BEDROCK_FALLBACK_ENDPOINTS=(),
        ),
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


def test_openai_primary_success_does_not_call_bedrock_fallback(monkeypatch):
    engine = _build_engine()
    requests = []

    class Provider:
        def converse(self, **kwargs):
            raise AssertionError("Bedrock fallback must not run after OpenAI success")

    def _fake_http(request):
        requests.append(request)
        return OpenAITransportResult(
            payload={"action": "HOLD", "score": 73, "reason": "openai-primary"},
            transport_mode="http",
            roundtrip_ms=321,
        )

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_TRANSPORT_MODE="http",
            OPENAI_HOLDING_FLOW_TIMEOUT_MS=15000,
            OPENAI_PRIMARY_BEDROCK_FALLBACK_ENDPOINTS=("holding_flow",),
            OPENAI_PRIMARY_BEDROCK_FALLBACK_PRIMARY_TIMEOUT_MS=7000,
            OPENAI_PRIMARY_BEDROCK_FALLBACK_TIMEOUT_MS=7000,
        ),
    )
    monkeypatch.setattr(engine, "_call_openai_responses_http", _fake_http)
    monkeypatch.setattr(bedrock_nova_provider, "runtime_provider", lambda: Provider())

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="holding-flow-primary-success",
        model_override="gpt-5.4-mini",
        endpoint_name="holding_flow",
        transport_mode_override="http",
    )
    meta = engine._consume_last_transport_meta()

    assert result["reason"] == "openai-primary"
    assert len(requests) == 1
    assert requests[0].timeout_ms == 7000
    assert meta["openai_transport_mode"] == "http"
    assert meta["openai_primary_provider"] == "openai"
    assert meta["openai_primary_timeout_budget_ms"] == 7000
    assert meta["openai_total_route_timeout_budget_ms"] == 15000
    assert meta["bedrock_fallback_used"] is False


def test_openai_primary_failure_uses_nova_lite_v2_fallback(monkeypatch):
    engine = _build_engine()
    captured = {}
    audit_rows = []

    class Provider:
        def converse(self, *, prompt, user_input, profile, deadline_perf=None):
            captured["family"] = profile.family
            captured["timeout_ms"] = profile.timeout_ms
            captured["deadline_perf"] = deadline_perf
            return bedrock_nova_provider.BedrockNovaResult(
                payload={"action": "HOLD", "score": 66, "reason": "nova-fallback"},
                raw_text='{"action":"HOLD","score":66,"reason":"nova-fallback"}',
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

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_TRANSPORT_MODE="http",
            OPENAI_HOLDING_FLOW_TIMEOUT_MS=15000,
            OPENAI_PRIMARY_BEDROCK_FALLBACK_ENDPOINTS=("holding_flow",),
            OPENAI_PRIMARY_BEDROCK_FALLBACK_FAMILY="lite_v2",
            OPENAI_PRIMARY_BEDROCK_FALLBACK_PRIMARY_TIMEOUT_MS=7000,
            OPENAI_PRIMARY_BEDROCK_FALLBACK_TIMEOUT_MS=7000,
        ),
    )
    monkeypatch.setattr(
        engine,
        "_call_openai_responses_http",
        lambda request: (_ for _ in ()).throw(
            OpenAIResponsesHTTPError("OpenAI primary timed out")
        ),
    )
    monkeypatch.setattr(bedrock_nova_provider, "runtime_provider", lambda: Provider())
    monkeypatch.setattr(
        bedrock_nova_provider, "write_provider_audit_row", audit_rows.append
    )

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="holding-flow-primary-failure",
        model_override="gpt-5.4-mini",
        endpoint_name="holding_flow",
        transport_mode_override="http",
    )
    meta = engine._consume_last_transport_meta()

    assert result["reason"] == "nova-fallback"
    assert captured["family"] == "lite_v2"
    assert 1 <= captured["timeout_ms"] <= 7000
    assert captured["deadline_perf"] is not None
    assert meta["openai_transport_mode"] == "bedrock_fallback"
    assert meta["openai_primary_provider"] == "openai"
    assert meta["openai_primary_error_type"] == "OpenAIResponsesHTTPError"
    assert meta["bedrock_fallback_used"] is True
    assert meta["bedrock_fallback_family"] == "lite_v2"
    assert meta["bedrock_failback_used"] is False
    assert audit_rows[0]["event_type"] == "openai_primary_bedrock_fallback"
    assert audit_rows[0]["primary_provider"] == "openai"
    assert audit_rows[0]["bedrock_fallback_used"] is True


def test_entry_price_openai_primary_route_bypasses_qwen_and_uses_http(monkeypatch):
    engine = _build_engine()
    requests = []

    class Provider:
        def converse(self, **kwargs):
            raise AssertionError(
                "Bedrock must not run after entry-price OpenAI success"
            )

    def _fake_http(request):
        requests.append(request)
        return OpenAITransportResult(
            payload={
                "action": "USE_DEFENSIVE",
                "order_price": 9990,
                "confidence": 80,
                "reason": "openai-entry-price",
            },
            transport_mode="http",
            roundtrip_ms=250,
        )

    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_ROUTE_MODE", "primary")
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_TRANSPORT_MODE="http",
            OPENAI_ENTRY_PRICE_TIMEOUT_MS=15000,
            OPENAI_PRIMARY_BEDROCK_FALLBACK_ENDPOINTS=("entry_price",),
            OPENAI_PRIMARY_BEDROCK_FALLBACK_PRIMARY_TIMEOUT_MS=7000,
            OPENAI_PRIMARY_BEDROCK_FALLBACK_TIMEOUT_MS=7000,
        ),
    )
    monkeypatch.setattr(engine, "_call_openai_responses_http", _fake_http)
    monkeypatch.setattr(bedrock_nova_provider, "runtime_provider", lambda: Provider())

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="entry-price-primary-success",
        model_override="gpt-5.4-mini",
        endpoint_name="entry_price",
        transport_mode_override="http",
    )
    meta = engine._consume_last_transport_meta()

    assert result["reason"] == "openai-entry-price"
    assert len(requests) == 1
    assert requests[0].timeout_ms == 7000
    assert meta["openai_transport_mode"] == "http"
    assert meta["bedrock_fallback_used"] is False


def test_entry_price_openai_failure_uses_only_nova_lite_v2_fallback(monkeypatch):
    engine = _build_engine()
    families = []

    class Provider:
        def converse(self, *, prompt, user_input, profile, deadline_perf=None):
            families.append(profile.family)
            return bedrock_nova_provider.BedrockNovaResult(
                payload={
                    "action": "USE_DEFENSIVE",
                    "order_price": 9980,
                    "confidence": 75,
                    "reason": "nova-entry-price-fallback",
                },
                raw_text="{}",
                parse_ok=True,
                parse_error="",
                model_id=profile.model_id,
                region_name=profile.region_name,
                key_index=0,
                latency_ms=300,
                input_tokens=20,
                output_tokens=8,
                cache_read_input_tokens=0,
                cache_write_input_tokens=0,
                total_input_tokens=20,
                estimated_cost_usd=0.0,
                attempted_key_count=1,
            )

    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_ROUTE_MODE", "primary")
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_TRANSPORT_MODE="http",
            OPENAI_ENTRY_PRICE_TIMEOUT_MS=15000,
            OPENAI_PRIMARY_BEDROCK_FALLBACK_ENDPOINTS=("entry_price",),
            OPENAI_PRIMARY_BEDROCK_FALLBACK_FAMILY="lite_v2",
            OPENAI_PRIMARY_BEDROCK_FALLBACK_PRIMARY_TIMEOUT_MS=7000,
            OPENAI_PRIMARY_BEDROCK_FALLBACK_TIMEOUT_MS=7000,
        ),
    )
    monkeypatch.setattr(
        engine,
        "_call_openai_responses_http",
        lambda request: (_ for _ in ()).throw(
            OpenAIResponsesHTTPError("entry-price OpenAI timeout")
        ),
    )
    monkeypatch.setattr(bedrock_nova_provider, "runtime_provider", lambda: Provider())
    monkeypatch.setattr(
        bedrock_nova_provider, "write_provider_audit_row", lambda row: None
    )

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="entry-price-primary-failure",
        model_override="gpt-5.4-mini",
        endpoint_name="entry_price",
        transport_mode_override="http",
    )
    meta = engine._consume_last_transport_meta()

    assert result["reason"] == "nova-entry-price-fallback"
    assert families == ["lite_v2"]
    assert meta["openai_primary_error_type"] == "OpenAIResponsesHTTPError"
    assert meta["openai_transport_mode"] == "bedrock_fallback"
    assert meta["bedrock_fallback_used"] is True


def test_entry_price_openai_and_nova_failure_closes_with_defensive_price(monkeypatch):
    engine = _build_engine()
    ws_data, ticks, candles, price_ctx = _entry_price_compaction_sample(1)
    families = []

    class Provider:
        def converse(self, *, prompt, user_input, profile, deadline_perf=None):
            families.append(profile.family)
            raise RuntimeError("nova fallback unavailable")

    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_ROUTE_MODE", "primary")
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_TRANSPORT_MODE="http",
            OPENAI_ENTRY_PRICE_TIMEOUT_MS=15000,
            OPENAI_PRIMARY_BEDROCK_FALLBACK_ENDPOINTS=("entry_price",),
            OPENAI_PRIMARY_BEDROCK_FALLBACK_FAMILY="lite_v2",
            OPENAI_PRIMARY_BEDROCK_FALLBACK_PRIMARY_TIMEOUT_MS=7000,
            OPENAI_PRIMARY_BEDROCK_FALLBACK_TIMEOUT_MS=7000,
        ),
    )
    monkeypatch.setattr(
        engine,
        "_call_openai_responses_http",
        lambda request: (_ for _ in ()).throw(
            OpenAIResponsesHTTPError("entry-price OpenAI timeout")
        ),
    )
    monkeypatch.setattr(bedrock_nova_provider, "runtime_provider", lambda: Provider())
    monkeypatch.setattr(
        bedrock_nova_provider, "write_provider_audit_row", lambda row: None
    )

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
    assert result["order_price"] == price_ctx["resolved_order_price"]
    assert result["reason"] == "ai_failure_use_defensive_fallback"
    assert result["ai_parse_fail"] is True
    assert families == ["lite_v2"]


def test_entry_price_evaluate_preserves_bedrock_fallback_provenance(monkeypatch):
    engine = _build_engine()
    ws_data, ticks, candles, price_ctx = _entry_price_compaction_sample(1)
    monkeypatch.setattr(
        engine,
        "_call_openai_safe",
        lambda *args, **kwargs: {
            "action": "USE_DEFENSIVE",
            "order_price": price_ctx["resolved_order_price"],
            "confidence": 75,
            "reason": "nova-entry-price-fallback",
            "provider": "bedrock",
            "bedrock_fallback_used": True,
            "bedrock_fallback_family": "lite_v2",
            "openai_primary_error_type": "OpenAIResponsesHTTPError",
        },
    )

    result = engine.evaluate_scalping_entry_price(
        "테스트",
        "005930",
        ws_data,
        ticks,
        candles,
        price_ctx,
    )

    assert result["provider"] == "bedrock"
    assert result["bedrock_fallback_used"] is True
    assert result["bedrock_fallback_family"] == "lite_v2"
    assert result["openai_primary_error_type"] == "OpenAIResponsesHTTPError"


def test_entry_price_evaluate_preserves_exact_request_trace_fields(monkeypatch):
    engine = _build_engine()
    ws_data, ticks, candles, price_ctx = _entry_price_compaction_sample(1)
    captured_trace = {}
    exact_fields = {
        "ai_decision_trace_id": "entry-price-trace-1",
        "ai_prompt_sha256": "a" * 64,
        "ai_prompt_store_date": "2026-07-24",
        "ai_prompt_redacted": False,
        "ai_prompt_replay_exact": True,
        "ai_input_payload_sha256": "b" * 64,
        "ai_input_payload_store_date": "2026-07-24",
        "ai_input_payload_redacted": False,
        "ai_input_payload_replay_exact": True,
        "ai_request_envelope_sha256": "c" * 64,
        "ai_trace_stock_code": "005930",
        "ai_trace_reference_price_type": "resolved_order_price",
        "ai_trace_reference_price": price_ctx["resolved_order_price"],
        "ai_trace_best_bid": price_ctx["best_bid"],
        "ai_trace_best_ask": price_ctx["best_ask"],
    }

    monkeypatch.setattr(
        engine,
        "_call_openai_safe",
        lambda *args, **kwargs: {
            "action": "USE_DEFENSIVE",
            "order_price": price_ctx["resolved_order_price"],
            "confidence": 75,
            "reason": "defensive entry price",
            "provider": "bedrock",
            "bedrock_primary_used": True,
            "bedrock_model_family": "qwen3_32b",
            **exact_fields,
        },
    )

    def _capture_trace(payload, **kwargs):
        captured_trace.update(payload)
        return {}

    monkeypatch.setattr(openai_module, "record_ai_decision_trace", _capture_trace)

    result = engine.evaluate_scalping_entry_price(
        "테스트",
        "005930",
        ws_data,
        ticks,
        candles,
        price_ctx,
    )

    for key, value in exact_fields.items():
        if key == "ai_input_payload_sha256":
            continue
        assert result[key] == value
        assert captured_trace[key] == value
    assert len(result["ai_input_payload_sha256"]) == 64
    assert (
        captured_trace["ai_input_payload_sha256"] == result["ai_input_payload_sha256"]
    )


def test_entry_price_qwen_parse_failure_falls_back_to_nova_lite_v2(monkeypatch):
    engine = _build_engine()
    families = []
    audit_rows = []
    openai_called = {"value": False}

    class Responses:
        def create(self, **kwargs):
            openai_called["value"] = True
            raise AssertionError(
                "OpenAI must not be called for entry_price Qwen failback"
            )

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
                payload={
                    "action": "USE_DEFENSIVE",
                    "order_price": 9900,
                    "confidence": 80,
                    "reason": "nova",
                },
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
    monkeypatch.setattr(
        bedrock_nova_provider, "write_provider_audit_row", audit_rows.append
    )

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
    assert any(
        row["bedrock_primary_error_type"] == "BedrockNovaProviderError"
        for row in audit_rows
    )
    assert any(
        row["decision_authority"]
        == "runtime_primary_with_bedrock_failback_defensive_close"
        for row in audit_rows
    )
    assert any(row["bedrock_attempted_key_count"] == 2 for row in audit_rows)


def test_entry_price_qwen_and_nova_fail_does_not_fall_back_to_openai(monkeypatch):
    engine = _build_engine()
    families = []
    openai_called = {"value": False}

    class Responses:
        def create(self, **kwargs):
            openai_called["value"] = True
            raise AssertionError(
                "OpenAI must not be called when entry_price Bedrock chain fails"
            )

    class Provider:
        def converse(self, *, prompt, user_input, profile):
            families.append(profile.family)
            raise RuntimeError(f"{profile.family} unavailable")

    engine.client = SimpleNamespace(responses=Responses())
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_ROUTE_MODE", "primary")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_PRIMARY_FAMILY", "qwen3_32b")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_FAILBACK_FAMILY", "lite_v2")
    monkeypatch.setattr(bedrock_nova_provider, "runtime_provider", lambda: Provider())
    monkeypatch.setattr(
        bedrock_nova_provider, "write_provider_audit_row", lambda row: None
    )

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
        raise AssertionError(
            "entry_price Bedrock chain failure must raise to caller fallback"
        )

    assert families == ["qwen3_32b", "lite_v2"]
    assert openai_called["value"] is False


def test_entry_price_provider_init_failure_records_audit_and_does_not_call_openai(
    monkeypatch,
):
    engine = _build_engine()
    audit_rows = []
    openai_called = {"value": False}

    class Responses:
        def create(self, **kwargs):
            openai_called["value"] = True
            raise AssertionError(
                "OpenAI must not be called when entry_price Bedrock provider init fails"
            )

    def _raise_runtime_provider():
        raise RuntimeError("missing bedrock api keys")

    engine.client = SimpleNamespace(responses=Responses())
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_ROUTE_MODE", "primary")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_PRIMARY_FAMILY", "qwen3_32b")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_FAILBACK_FAMILY", "lite_v2")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_FAILBACK_ENABLED", "true")
    monkeypatch.setattr(
        bedrock_nova_provider, "runtime_provider", _raise_runtime_provider
    )
    monkeypatch.setattr(
        bedrock_nova_provider, "write_provider_audit_row", audit_rows.append
    )

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
        raise AssertionError(
            "entry_price provider init failure must raise to caller fallback"
        )

    assert openai_called["value"] is False
    assert any(row["bedrock_primary_family"] == "qwen3_32b" for row in audit_rows)
    assert any(row["bedrock_failback_family"] == "lite_v2" for row in audit_rows)
    assert all(
        row["decision_authority"]
        == "runtime_primary_with_bedrock_failback_defensive_close"
        for row in audit_rows
    )


def test_entry_price_qwen_and_nova_fail_uses_defensive_engine_fallback(monkeypatch):
    engine = _build_engine()
    ws_data, ticks, candles, price_ctx = _entry_price_compaction_sample(1)
    openai_called = {"value": False}

    class Responses:
        def create(self, **kwargs):
            openai_called["value"] = True
            raise AssertionError(
                "OpenAI must not be called when entry_price Bedrock chain fails"
            )

    class Provider:
        def converse(self, *, prompt, user_input, profile):
            raise RuntimeError(f"{profile.family} unavailable")

    engine.client = SimpleNamespace(responses=Responses())
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_ROUTE_MODE", "primary")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_PRIMARY_FAMILY", "qwen3_32b")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_FAILBACK_FAMILY", "lite_v2")
    monkeypatch.setattr(bedrock_nova_provider, "runtime_provider", lambda: Provider())
    monkeypatch.setattr(
        bedrock_nova_provider, "write_provider_audit_row", lambda row: None
    )

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
        engine._set_last_transport_meta(
            {
                "openai_transport_mode": "bedrock_fallback",
                "openai_primary_provider": "openai",
                "openai_primary_error_type": "OpenAIResponsesHTTPError",
                "bedrock_fallback_used": True,
                "bedrock_fallback_family": "lite_v2",
                "provider": "bedrock",
            }
        )
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
        {
            "profit_rate": -0.3,
            "peak_profit": 0.4,
            "held_sec": 75,
            "current_ai_score": 31,
            "worsen_pct": 0.8,
        },
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
    assert result["openai_transport_mode"] == "bedrock_fallback"
    assert result["openai_primary_provider"] == "openai"
    assert result["bedrock_fallback_used"] is True
    assert result["bedrock_fallback_family"] == "lite_v2"
    assert result["provider"] == "bedrock"
    assert result["holding_flow_contract_status"] == "semantic_rejected"
    assert "holding_flow_score_type_invalid" in result["holding_flow_contract_errors"]
    assert result["forensic_semantic_errors"] == result["holding_flow_contract_errors"]
    assert result["semantic_validator_applied"] is True
    assert result["semantic_validation_status"] == "rejected"
    assert result["ai_result_source"] == "live"
    assert result["ai_decision_outcome_eligible"] is False
    assert captured["kwargs"]["schema_name"] == "holding_exit_flow_v1"
    assert captured["kwargs"]["endpoint_name"] == "holding_flow"
    assert captured["kwargs"]["model_override"] == "gpt-5.4-mini"
    assert captured["kwargs"]["transport_mode_override"] == "http"
    assert captured["kwargs"]["metadata_extra"]["sim_record_id"] == "SIM-HOLD-1"
    assert captured["kwargs"]["metadata_extra"]["entry_adm_candidate_id"] == "ADM-1"
    assert captured["kwargs"].get("replay_context") is None
    assert (
        captured["kwargs"]["metadata_extra"][
            "holding_exact_replay_context_capture_status"
        ]
        == "forensic_sidecar_disabled_to_preserve_live_latency"
    )
    assert not captured["user_input"].lstrip().startswith("{")
    assert "To reverse the previous flow-review action" in captured["prompt"]
    assert "If a system guard applies" in SCALPING_HOLDING_FLOW_SYSTEM_PROMPT
    assert (
        "absorption, recovery, distribution, breakdown, or quiet"
        in captured["user_input"]
    )
    assert "state=absorption" in captured["user_input"]
    assert not _has_hangul(captured["prompt"])
    assert "Do not cut by a single score cutoff" in captured["user_input"]
    assert "reason=매수 흡수 유지" in captured["user_input"]


def test_holding_flow_legacy_call_does_not_build_forensic_context(
    monkeypatch,
):
    engine = _build_engine()
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_HOLDING_FLOW_V2_INPUT_ENABLED=False,
        ),
    )
    builder_called = {"value": False}

    def _unexpected_builder(*args, **kwargs):
        builder_called["value"] = True
        raise AssertionError("legacy holding flow must not build a forensic sidecar")

    monkeypatch.setattr(
        engine,
        "_build_scalping_holding_flow_v2_context",
        _unexpected_builder,
    )
    captured = {}

    def _fake_call(prompt, user_input, **kwargs):
        captured["user_input"] = user_input
        captured["kwargs"] = kwargs
        return {
            "action": "HOLD",
            "score": 70,
            "flow_state": "quiet",
            "thesis": "legacy flow remains usable",
            "evidence": ["no material deterioration"],
            "reason": "keep bounded review cadence",
            "next_review_sec": 30,
        }

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)
    result = engine.evaluate_scalping_holding_flow(
        "테스트",
        "005930",
        {"curr": 10_000},
        [],
        [],
        {"profit_rate": 0.1, "held_sec": 10, "current_ai_score": 60},
    )

    assert result["action"] == "HOLD"
    assert builder_called["value"] is False
    assert captured["kwargs"].get("replay_context") is None
    assert (
        captured["kwargs"]["metadata_extra"][
            "holding_exact_replay_context_capture_status"
        ]
        == "forensic_sidecar_disabled_to_preserve_live_latency"
    )
    assert not captured["user_input"].lstrip().startswith("{")


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
    assert result["semantic_validator_version"] == (
        "live_entry_price_v1_schema_semantic_v1"
    )
    assert result["semantic_validator_applied"] is True
    assert result["semantic_validation_status"] == "pass"
    assert result["entry_price_v1_contract_status"] == "pass"
    assert result["entry_price_v1_contract_errors"] == []
    assert not _has_hangul(captured["prompt"])
    assert not _has_hangul(captured["user_input"])
    assert "\\ud14c\\uc2a4\\ud2b8" in captured["user_input"]
    assert "note" not in json.loads(captured["user_input"])["ws_data"]


def test_entry_price_v1_malformed_response_is_quality_rejected_without_live_rewrite(
    monkeypatch,
):
    engine = _build_engine()
    monkeypatch.setattr(
        engine,
        "_call_openai_safe",
        lambda *args, **kwargs: {
            "action": "USE_REFERENCE",
            "order_price": 10000,
            "confidence": "80",
            "reason": "reference price is acceptable",
            "max_wait_sec": 30,
        },
    )

    result = engine.evaluate_scalping_entry_price(
        "test",
        "005930",
        {"curr": 10000},
        [],
        [],
        {"resolved_order_price": 9900},
    )

    assert result["action"] == "USE_REFERENCE"
    assert result["order_price"] == 10000
    assert result["semantic_validator_applied"] is True
    assert result["semantic_validation_status"] == "rejected"
    assert result["entry_price_v1_contract_status"] == "semantic_rejected"
    assert (
        "entry_price_v1_confidence_type_invalid"
        in result["entry_price_v1_contract_errors"]
    )
    assert (
        result["forensic_semantic_errors"] == result["entry_price_v1_contract_errors"]
    )
    assert result["ai_decision_outcome_eligible"] is False


def test_entry_price_v1_semantic_wait_range_matches_live_prompt_contract():
    base = {
        "action": "USE_REFERENCE",
        "order_price": 10000,
        "confidence": 80,
        "reason": "reference price is acceptable",
    }

    assert (
        openai_module._entry_price_v1_response_contract_errors(
            {**base, "max_wait_sec": 5}
        )
        == []
    )
    assert (
        openai_module._entry_price_v1_response_contract_errors(
            {**base, "max_wait_sec": 1200}
        )
        == []
    )
    assert "entry_price_v1_max_wait_sec_out_of_range" in (
        openai_module._entry_price_v1_response_contract_errors(
            {**base, "max_wait_sec": 4}
        )
    )
    assert "entry_price_v1_max_wait_sec_out_of_range" in (
        openai_module._entry_price_v1_response_contract_errors(
            {**base, "max_wait_sec": 1201}
        )
    )


def test_entry_price_v2_5_live_policy_uses_exact_krx_contract_without_route_change(
    monkeypatch,
):
    engine = _build_engine()
    captured = {}
    exact_payload = {
        "stock_code": "005930",
        "price_context": {
            "defensive_order_price": 10000,
            "reference_target_price": 10010,
            "resolved_order_price": 10000,
            "best_bid": 9990,
            "best_ask": 10010,
            "entry_price_guard": {},
        },
        "entry_context_features": {
            "quote_stale": False,
            "quote_fresh_for_entry": True,
            "would_fill_now": True,
            "spread_bp": 20,
        },
        "entry_candle_context": {"risk_flags": []},
        "ai_market_snapshot_v1": {
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "ai_input_preflight_v1": {
                "allowed": True,
                "venue_consistent": True,
                "blockers": [],
            },
        },
    }
    live_version = (
        openai_module.DECISION_QUALITY_ENTRY_PRICE_V2_5_LIVE_KRX_PROMPT_VERSION
    )
    monkeypatch.setattr(
        openai_module,
        "resolve_entry_price_live_policy",
        lambda candle_context: {
            "status": "active_krx_regular_v2_5",
            "selected_prompt_version": live_version,
            "rollback_prompt_version": "entry_price_v1",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "runtime_effect": True,
            "allowed_runtime_apply": True,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "blocking_reasons": [],
            "evidence_sha256": "a" * 64,
        },
    )
    monkeypatch.setattr(
        engine,
        "_build_scalping_entry_price_runtime_input",
        lambda **kwargs: json.dumps(exact_payload),
    )

    def _fake_call(prompt, user_input, **kwargs):
        captured.update(
            {
                "prompt": prompt,
                "user_input": json.loads(user_input),
                "kwargs": kwargs,
            }
        )
        return {
            "edge_state": "EDGE",
            "action": "USE_DEFENSIVE",
            "expected_upside_pct": 1.0,
            "expected_downside_pct": -0.5,
            "confidence": 72,
            "reason_codes": ["edge_positive"],
            "evidence": {
                "trend": "supportive",
                "liquidity": "supportive",
                "tape": "supportive",
                "risk": "low",
                "uncertainty": "low",
                "setup": "continuation",
                "positive_edge": "moderate",
                "adverse_risk": "low",
                "trigger": "confirmed",
            },
            "selected_price": 10000,
            "price_basis": "DEFENSIVE",
            "control_fill_probability_pct": 70.0,
            "selected_fill_probability_pct": 70.0,
            "incremental_fill_probability_pct": 0.0,
            "incremental_chase_cost_pct": 0.0,
            "fill_adjusted_edge_pct": 0.0,
            "provider": "bedrock",
            "bedrock_primary_used": True,
            "bedrock_model_family": "qwen3_32b",
        }

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)

    result = engine.evaluate_scalping_entry_price(
        "test",
        "005930",
        {},
        [],
        [],
        {"resolved_order_price": 10000},
        candle_context=exact_payload["ai_market_snapshot_v1"],
    )

    assert result["action"] == "USE_DEFENSIVE"
    assert result["order_price"] == 10000
    assert result["ai_prompt_version"] == live_version
    assert result["entry_price_v2_5_contract_status"] == "pass"
    assert result["semantic_validator_version"] == (
        openai_module.ENTRY_PRICE_SEMANTIC_VALIDATOR_VERSION
    )
    assert result["semantic_validator_applied"] is True
    assert result["semantic_validation_status"] == "pass"
    assert captured["kwargs"]["schema_name"] == ("entry_price_explicit_fill_value_v1")
    assert captured["kwargs"]["endpoint_name"] == "entry_price"
    assert captured["kwargs"]["model_override"] == engine.model_tier2_balanced
    assert captured["user_input"]["exact_payload"] == exact_payload
    assert "offline" not in captured["prompt"].lower()


def test_entry_price_v2_5_semantic_reject_closes_defensive_without_parse_failure(
    monkeypatch,
):
    engine = _build_engine()
    live_version = (
        openai_module.DECISION_QUALITY_ENTRY_PRICE_V2_5_LIVE_KRX_PROMPT_VERSION
    )
    exact_payload = {
        "price_context": {
            "defensive_order_price": 10000,
            "resolved_order_price": 10000,
            "best_bid": 9990,
            "best_ask": 10010,
        },
        "entry_context_features": {
            "quote_stale": False,
            "quote_fresh_for_entry": True,
        },
        "ai_market_snapshot_v1": {
            "ai_input_preflight_v1": {
                "allowed": True,
                "venue_consistent": True,
                "blockers": [],
            }
        },
    }
    monkeypatch.setattr(
        openai_module,
        "resolve_entry_price_live_policy",
        lambda candle_context: {
            "status": "active_krx_regular_v2_5",
            "selected_prompt_version": live_version,
            "rollback_prompt_version": "entry_price_v1",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "runtime_effect": True,
            "allowed_runtime_apply": True,
            "blocking_reasons": [],
        },
    )
    monkeypatch.setattr(
        engine,
        "_build_scalping_entry_price_runtime_input",
        lambda **kwargs: json.dumps(exact_payload),
    )
    monkeypatch.setattr(
        engine,
        "_call_openai_safe",
        lambda *args, **kwargs: {
            "action": "SKIP",
            "provider": "bedrock",
            "bedrock_primary_used": True,
        },
    )

    result = engine.evaluate_scalping_entry_price(
        "test",
        "005930",
        {},
        [],
        [],
        {"resolved_order_price": 10000},
    )

    assert result["action"] == "USE_DEFENSIVE"
    assert result["order_price"] == 10000
    assert result["ai_result_source"] == "schema_semantic_rejected"
    assert result["ai_parse_ok"] is True
    assert result["ai_parse_fail"] is False
    assert result["entry_price_v2_5_contract_status"] == "rejected"
    assert result["entry_price_v2_5_contract_errors"]
    assert result["semantic_validator_version"] == (
        openai_module.ENTRY_PRICE_SEMANTIC_VALIDATOR_VERSION
    )
    assert result["semantic_validator_applied"] is True
    assert result["semantic_validation_status"] == "rejected"
    assert result["provider_called"] is True
    assert result["ai_decision_outcome_eligible"] is False
    assert (
        result["forensic_semantic_errors"] == result["entry_price_v2_5_contract_errors"]
    )
    assert result["decision_quality_contract_status"] == "semantic_rejected"
    assert (
        result["decision_quality_contract_errors"]
        == result["entry_price_v2_5_contract_errors"]
    )
    assert result["provider"] == "bedrock"


def test_entry_price_live_policy_resolution_error_falls_back_to_v1(monkeypatch):
    engine = _build_engine()
    ws_data, ticks, candles, price_ctx = _entry_price_compaction_sample(1)
    captured = {}

    def _raise_policy_error(candle_context):
        raise ValueError("corrupt policy")

    monkeypatch.setattr(
        openai_module, "resolve_entry_price_live_policy", _raise_policy_error
    )

    def _fake_call(prompt, user_input, **kwargs):
        captured.update(kwargs)
        return {
            "action": "USE_DEFENSIVE",
            "order_price": price_ctx["resolved_order_price"],
            "confidence": 70,
            "reason": "control fallback",
            "max_wait_sec": 30,
        }

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)

    result = engine.evaluate_scalping_entry_price(
        "test",
        "005930",
        ws_data,
        ticks,
        candles,
        price_ctx,
    )

    assert result["ai_prompt_version"] == "entry_price_v1"
    assert result["entry_price_live_policy_status"] == (
        "control_v1_policy_resolution_error"
    )
    assert captured["schema_name"] == "entry_price_v1"


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
        assert (
            parsed["price_context"]["defensive_order_price"]
            == price_ctx["defensive_order_price"]
        )
        assert (
            parsed["price_context"]["reference_target_price"]
            == price_ctx["reference_target_price"]
        )
        assert (
            parsed["price_context"]["resolved_order_price"]
            == price_ctx["resolved_order_price"]
        )
        assert parsed["price_context"]["best_bid"] == price_ctx["best_bid"]
        assert parsed["price_context"]["best_ask"] == price_ctx["best_ask"]
        assert "spread" in parsed["price_context"]
        assert "latency_guard" in parsed["price_context"]
        assert "entry_price_guard" in parsed["price_context"]
        assert (
            parsed["price_context"]["orderbook_micro"]["micro_state"]
            == price_ctx["orderbook_micro"]["micro_state"]
        )
        assert (
            parsed["price_context"]["orderbook_micro"]["ofi"]
            == price_ctx["orderbook_micro"]["ofi_norm"]
        )
        assert (
            parsed["price_context"]["orderbook_micro"]["qi"]
            == price_ctx["orderbook_micro"]["qi"]
        )
        assert (
            parsed["price_context"]["orderbook_micro"]["top_depth_ratio"]
            == price_ctx["orderbook_micro"]["top_depth_ratio"]
        )
        assert (
            parsed["price_context"]["orderbook_micro"]["spread_bp"]
            == price_ctx["orderbook_micro"]["spread_bp"]
        )
        assert (
            parsed["entry_context_features"]["context_role"]
            == "pre_submit_entry_quality_context"
        )
        assert "entry_liquidity_score" in parsed["entry_context_features"]
        assert "fillability_score" in parsed["entry_context_features"]
        assert "order_flow_pressure_score" in parsed["entry_context_features"]
        assert "entry_context_quality" in parsed["entry_context_features"]
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
    assert (
        captured_payload["price_context"]["resolved_order_price"]
        == samples[0][3]["resolved_order_price"]
    )


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
    assert (
        json.loads(compact_runtime_payload)["price_context"]["resolved_order_price"]
        == price_ctx["resolved_order_price"]
    )

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


def test_entry_price_compact_input_preserves_before_after_output_across_large_sample(
    monkeypatch,
):
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
        action_counts[after_output["action"]] = (
            action_counts.get(after_output["action"], 0) + 1
        )

    assert set(action_counts) >= {
        "USE_DEFENSIVE",
        "USE_REFERENCE",
        "IMPROVE_LIMIT",
        "SKIP",
    }

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
        assert (
            entry_price["price_context"]["resolved_order_price"]
            == price_ctx["resolved_order_price"]
        )
        assert (
            entry_price["candidate_prices"]["defensive_order_price"]
            == price_ctx["defensive_order_price"]
        )
        assert (
            entry_price["entry_context_features"]["context_role"]
            == "pre_submit_entry_quality_context"
        )
        assert "entry_liquidity_score" in entry_price["entry_context_features"]
        assert "fillability_score" in entry_price["entry_context_features"]
        assert "order_flow_pressure_score" in entry_price["entry_context_features"]
        assert "entry_context_quality" in entry_price["entry_context_features"]
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
        assert (
            holding_flow["entry_time_context"]["context_role"]
            == "entry_time_provenance_only"
        )
        assert holding_flow["entry_time_context"]["status"] == "not_available"
        assert (
            holding_flow["deterministic_guard_state"][
                "system_guards_remain_authoritative"
            ]
            is True
        )
        assert (
            holding_flow["runtime_advisory_context"]["holding_exit_matrix"]
            == "matrix_context"
        )
        assert (
            holding_flow["runtime_advisory_context"]["lifecycle_ai"]
            == "lifecycle_context"
        )
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
    entry_result = engine.analyze_target(
        "테스트0", ws_data, ticks, candles, prompt_profile="watching"
    )
    entry_price_result = engine.evaluate_scalping_entry_price(
        "테스트0", "000000", ws_data, ticks, candles, price_ctx
    )
    holding_result = engine.evaluate_scalping_holding_flow(
        "테스트0",
        "000000",
        ws_data,
        ticks,
        candles,
        {
            "profit_rate": 0.2,
            "peak_profit": 0.5,
            "held_sec": 60,
            "current_ai_score": 70,
        },
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
    assert captured[0]["kwargs"]["model_override"] == "gpt-5.4-nano"
    assert captured[0]["kwargs"]["transport_mode_override"] == "http"
    assert captured[0]["kwargs"]["timeout_ms_override"] == 5000
    assert captured[1]["kwargs"]["model_override"] == engine.model_tier2_balanced
    assert captured[2]["kwargs"]["model_override"] == "gpt-5.4-mini"
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
        {
            "curr": 10000,
            "orderbook": {
                "asks": [{"price": 10010, "volume": 100}],
                "bids": [{"price": 10000, "volume": 100}],
            },
        },
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


def test_analyze_target_swing_input_contract_stays_plain_text_when_v2_enabled(
    monkeypatch,
):
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

    entry_result = engine.analyze_target(
        "테스트", ws_data, ticks, candles, prompt_profile="watching"
    )
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
        {
            "profit_rate": 0.2,
            "peak_profit": 0.5,
            "held_sec": 60,
            "current_ai_score": 70,
        },
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
            return SimpleNamespace(
                output_text='{"action":"BUY","score":91,"reason":"json"}'
            )
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


def test_openai_usage_meta_includes_provider_response_id_without_usage():
    response = SimpleNamespace(id="resp-forensics-1", usage=None)

    assert openai_module._extract_openai_usage_meta(response) == {
        "openai_response_id": "resp-forensics-1"
    }


def test_openai_reasoning_effort_auto_uses_none_for_gpt54_family(monkeypatch):
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_REASONING_EFFORT="auto",
            OPENAI_TRANSPORT_MODE="http",
        ),
    )

    for model_name in ("gpt-5.4-mini", "gpt-5.4-nano"):
        engine = _build_engine()
        engine.current_model_name = model_name
        calls = []

        def _fake_create(**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                output_text='{"action":"WAIT","score":50,"reason":"ok"}'
            )

        engine.client = SimpleNamespace(responses=SimpleNamespace(create=_fake_create))
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

    payload = engine._format_market_data(
        _sample_ws_data(), _sample_ticks(), _sample_candles()
    )
    parsed = json.loads(payload)

    assert payload.startswith("{")
    assert '"features":' in payload
    assert '"recent_ticks_latest_first":' in payload
    assert "derived" not in parsed
    assert "tick_summary" not in payload
    assert "volume_analysis" not in payload
    assert "orderbook_imbalance" not in payload
    assert "drawdown_from_day_high" not in payload
    assert (
        parsed["current"]["distance_from_day_high_pct"]
        == parsed["features"]["distance_from_day_high_pct"]
    )
    assert "최근 10틱 상세 내역" not in payload


def test_openai_scalping_entry_hot_input_reduces_prompt_payload(monkeypatch):
    engine = _build_engine()
    ws_data = _sample_ws_data()
    ticks = _sample_ticks()
    candles = _sample_candles()

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_SCALPING_COMPACT_INPUT_ENABLED=True,
            OPENAI_ANALYZE_TARGET_HOT_INPUT_ENABLED=True,
            OPENAI_ENTRY_SCREEN_V2_INPUT_ENABLED=False,
        ),
    )

    feature_packet = openai_module.extract_scalping_feature_packet(
        ws_data, ticks, candles
    )
    compact_payload = engine._format_market_data(
        ws_data, ticks, candles, feature_packet=feature_packet
    )
    hot_payload = engine._format_entry_screen_hot_data(
        ws_data,
        ticks,
        candles,
        feature_packet=feature_packet,
        matrix_runtime={
            "status": "excluded",
            "cache_token": "matrix:excluded",
            "prompt_context": "x" * 200,
        },
        entry_adm_runtime={
            "status": "applied",
            "applied": True,
            "cache_token": "entry_adm:bucket",
            "prompt_context": "y" * 200,
            "fields": {
                "entry_adm_bucket_token": "bucket-a",
                "entry_adm_recommended_action": "WAIT",
                "entry_adm_source_quality_adjusted_ev_pct": 0.12,
            },
        },
        lifecycle_ai_runtime={
            "status": "ready",
            "applied": True,
            "cache_token": "lifecycle:ready",
            "prompt_context": "z" * 200,
        },
    )
    parsed = json.loads(hot_payload)

    assert parsed["input_schema"] == "entry_screen_hot_v1"
    assert "recent_ticks_latest_first" not in parsed
    assert "recent_candles_latest_window" not in parsed
    assert "orderbook_top3" not in parsed
    assert "prompt_context" not in hot_payload
    assert (
        parsed["runtime_context"]["entry_adm"]["entry_adm_bucket_token"] == "bucket-a"
    )
    assert parsed["features"]["entry_liquidity_status"] in {"good", "thin"}
    assert "fillability_score" in parsed["features"]
    assert "order_flow_pressure_score" in parsed["features"]
    assert "entry_order_flow_status" in parsed["features"]
    assert "entry_momentum_score" in parsed["features"]
    assert "entry_context_quality" in parsed["features"]
    assert len(hot_payload) < int(len(compact_payload) * 0.6)


def test_entry_hot_payload_refreshes_nested_hash_after_compaction(monkeypatch):
    engine = _build_engine()
    candle_context = _allowed_entry_candle_context()
    candle_context.update(
        {
            "enabled": True,
            "multi_timeframe_ai_input_enabled": True,
            "input_bundle_version": "scalping_multi_timeframe_context_v1",
            "multi_timeframe_context": {
                "schema": "scalping_multi_timeframe_context_v1",
                "multi_timeframe_bars": [],
                "incomplete_multi_timeframe_bars": [],
                "session_bar_vwap": {"status": "pass", "value": 10050.0},
                "payload_hash": "a" * 64,
            },
        }
    )

    parsed = json.loads(
        engine._format_entry_screen_hot_data(
            _sample_ws_data(),
            _sample_ticks(),
            _sample_candles(),
            candle_context=candle_context,
        )
    )
    context = parsed["entry_candle_context"]["multi_timeframe_context"]
    expected = hashlib.sha256(
        json.dumps(
            {key: value for key, value in context.items() if key != "payload_hash"},
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    assert context["source_payload_hash"] == "a" * 64
    assert context["payload_hash"] == expected
    assert "multi_timeframe_bars" not in context


def test_analyze_target_watching_uses_hot_prompt_and_input_schema(monkeypatch):
    engine = _build_engine()
    captured = {}

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_ANALYZE_TARGET_HOT_PROMPT_ENABLED=True,
            OPENAI_ANALYZE_TARGET_HOT_INPUT_ENABLED=True,
            OPENAI_ENTRY_SCREEN_V2_INPUT_ENABLED=False,
            OPENAI_SCALPING_COMPACT_INPUT_ENABLED=True,
        ),
    )

    def _fake_call(prompt, user_input, **kwargs):
        captured["prompt"] = prompt
        captured["payload"] = json.loads(user_input)
        return {"action": "WAIT", "score": 60, "reason": "mixed entry features"}

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)

    result = engine.analyze_target(
        "테스트",
        _sample_ws_data(),
        _sample_ticks(),
        _sample_candles(),
        strategy="SCALPING",
        prompt_profile="watching",
    )

    assert captured["prompt"] == SCALPING_WATCHING_HOT_SYSTEM_PROMPT
    assert captured["payload"]["input_schema"] == "entry_screen_hot_v1"
    assert result["ai_prompt_version"] == "hot_v1"
    assert result["ai_input_schema"] == "entry_screen_hot_v1"
    assert result["ai_input_contract_mode"] == "structured_json"
    assert result["semantic_validator_version"] == (
        "scalping_action_live_normalizer_v1"
    )
    assert result["expected_semantic_validator_version"] == (
        result["semantic_validator_version"]
    )


def test_analyze_target_operator_promotes_decision_quality_v2_7(monkeypatch):
    engine = _build_engine()
    captured = {}
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_ANALYZE_TARGET_PROMPT_VERSION="decision_quality_v2_7",
            OPENAI_ANALYZE_TARGET_HOT_INPUT_ENABLED=False,
            OPENAI_ENTRY_SCREEN_V2_INPUT_ENABLED=True,
        ),
    )

    def _fake_call(prompt, user_input, **kwargs):
        captured["prompt"] = prompt
        captured["payload"] = json.loads(user_input)
        captured["schema_name"] = kwargs.get("schema_name")
        return {
            "edge_state": "NO_EDGE",
            "action": "DROP",
            "expected_upside_pct": 0.5,
            "expected_downside_pct": -1.0,
            "confidence": 80,
            "reason_codes": ["edge_absent", "risk_reward_unfavorable"],
            "evidence": {
                "trend": "adverse",
                "liquidity": "mixed",
                "tape": "mixed",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "no_setup",
                "positive_edge": "none",
                "adverse_risk": "high",
                "trigger": "failed",
            },
        }

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)
    result = engine.analyze_target(
        "테스트",
        _sample_ws_data(),
        _sample_ticks(),
        _sample_candles(),
        strategy="SCALPING",
        prompt_profile="watching",
        candle_context=_allowed_entry_candle_context(),
    )

    assert captured["prompt"] == decision_quality_v2_detailed_system_prompt(
        "entry", live_entry=True
    )
    assert captured["schema_name"] == "decision_quality_v2_7_entry"
    assert captured["payload"]["exact_payload"]["input_schema"] == "entry_screen_hot_v1"
    analysis = captured["payload"]["exact_payload_analysis_v1"]
    assert (
        analysis["observation_contract"]["decision_authority"]
        == "operator_directed_live_entry_prompt_input"
    )
    assert analysis["observation_contract"]["runtime_effect"] is True
    assert result["action"] == "DROP"
    assert result["score"] == 10
    assert result["decision_quality_contract_status"] == "pass"
    assert result["semantic_validator_version"] == (
        openai_module.DECISION_QUALITY_V2_SEMANTIC_VALIDATOR_VERSION
    )
    assert result["expected_semantic_validator_version"] == (
        result["semantic_validator_version"]
    )
    assert result["ai_prompt_version"] == DECISION_QUALITY_DETAILED_PROMPT_VERSION
    assert result["ai_input_schema"] == "decision_quality_v2_7_entry_input"
    assert (
        result["decision_quality_score_semantics"]
        == "confidence_clamped_to_legacy_action_band"
    )


def test_analyze_target_uses_active_v2_14_only_as_krx_bounded_probe(monkeypatch):
    engine = _build_engine()
    captured = {}
    live_policy_kwargs = {}
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_ANALYZE_TARGET_PROMPT_VERSION=(
                DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
            ),
            OPENAI_ANALYZE_TARGET_HOT_INPUT_ENABLED=False,
            OPENAI_ENTRY_SCREEN_V2_INPUT_ENABLED=True,
        ),
    )

    def _resolve_live_policy(**kwargs):
        live_policy_kwargs.update(kwargs)
        return {
            "enabled": True,
            "status": "active_bounded_krx_canary",
            "canary_mode": "performance_bounded",
            "selected_prompt_version": (
                DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
            ),
            "source_date": "2026-08-06",
            "target_date": "2026-08-07",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "activation_artifact_sha256": "activation-sha",
            "candidate_contract_sha256": "candidate-sha",
            "runtime_effect": True,
        }

    monkeypatch.setattr(
        openai_module,
        "resolve_live_prompt_policy",
        _resolve_live_policy,
    )
    setup_evidence = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10100}},
        exact_analysis={
            "schema": "exact_payload_analysis_v1",
            "source_quality": {"status": "pass", "completed_bar_count": 20},
            "executable_liquidity": {"execution_cost_state": "low"},
            "contradictions": [],
            "deterministic_contract_facts": {
                "structural_edge_floor": True,
                "early_session_structural_edge_floor": False,
                "early_session_probe_candidate": False,
                "orderly_pullback_recovery": False,
                "trusted_supportive_trigger": True,
                "adverse_distribution_no_edge": False,
                "blocking_overextension": False,
                "ask_wall_wide_spread": False,
            },
        },
        recovery_analysis={
            "schema": "anticipatory_reversal_analysis_v1",
            "source_mode": "fresh_dual",
            "hard_blockers": [],
            "clean_continuation_probe": {"eligible": True},
            "recovery_confirmation_probe": {"eligible": False},
        },
    )
    monkeypatch.setattr(
        openai_module,
        "build_entry_setup_evidence",
        lambda **_kwargs: setup_evidence,
    )

    def _fake_call(prompt, user_input, **kwargs):
        captured["prompt"] = prompt
        captured["payload"] = json.loads(user_input)
        captured["schema_name"] = kwargs.get("schema_name")
        captured["metadata_extra"] = kwargs.get("metadata_extra")
        captured["replay_context"] = kwargs.get("replay_context")
        # Match the real provider path: transport metadata is recorded in
        # thread-local storage separately from the six-field model response.
        engine._set_last_transport_meta(
            {
                "openai_transport_mode": "http",
                "openai_ws_used": False,
                "openai_request_total_ms": 123,
            }
        )
        return {
            "schema": ENTRY_RISK_ADJUDICATION_SCHEMA,
            "risk_verdict": "PASS",
            "risk_codes": ["NO_BLOCKING_RISK"],
            "supporting_fact_ids": ["structural_edge_floor"],
            "contradicting_fact_ids": [],
            "confidence": 1,
        }

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)
    candle_context = _allowed_entry_candle_context()
    candle_context["venue"] = "KRX"
    candle_context["session"] = "KRX_REGULAR"
    result = engine.analyze_target(
        "테스트",
        _sample_ws_data(),
        _sample_ticks(),
        _sample_candles(),
        strategy="SCALPING",
        prompt_profile="watching",
        metadata_extra={"position_tag": "SCANNER"},
        candle_context=candle_context,
    )

    assert captured["prompt"] == (
        decision_quality_v2_14_setup_risk_adjudicator_system_prompt("entry")
    )
    assert captured["schema_name"] == ENTRY_RISK_ADJUDICATION_SCHEMA
    assert captured["payload"]["input_schema"] == "entry_setup_v2_14_live_input"
    assert captured["payload"]["entry_setup_evidence_v1"] == setup_evidence
    assert captured["payload"]["provider_input_authority"] == (
        "deterministic_setup_ledger_only"
    )
    assert captured["replay_context"]["entry_setup_evidence_v1"] == setup_evidence
    assert captured["replay_context"]["exact_payload"]["input_schema"] == (
        "entry_screen_hot_v1"
    )
    assert len(json.dumps(captured["payload"], default=str)) < len(
        json.dumps(captured["replay_context"], default=str)
    )
    expected_replay_sha256 = hashlib.sha256(
        json.dumps(
            captured["replay_context"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
    assert captured["payload"]["exact_replay_context_sha256"] == (
        expected_replay_sha256
    )
    assert captured["metadata_extra"]["entry_setup_live_policy_status"] == (
        "active_bounded_krx_canary"
    )
    assert live_policy_kwargs["position_tag"] == "SCANNER"
    assert result["ai_prompt_version"] == (
        DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
    )
    assert result["ai_input_schema"] == "entry_setup_v2_14_live_input"
    assert result["action"] == "WAIT"
    assert result["score"] == 70
    assert result["entry_probe_intent"] is True
    assert result["entry_probe_first_required"] is True
    assert result["entry_ai_full_entry_forbidden"] is True
    assert "broker_order_forbidden" not in result
    assert "allowed_runtime_apply" not in result
    assert result["entry_setup_composer_broker_order_forbidden"] is True
    assert result["entry_setup_live_adapter_runtime_effect"] is True
    assert result["entry_setup_live_policy_mode"] == "performance_bounded"
    assert result["decision_quality_contract_status"] == "pass"
    assert result["openai_transport_mode"] == "http"
    assert result["openai_request_total_ms"] == 123
    assert "entry_risk_unexpected_fields" not in result.get(
        "decision_quality_contract_errors", []
    )


def test_decision_quality_v2_6_runtime_override_uses_exact_entry_prompt() -> None:
    engine = _build_engine()

    prompt, prompt_type, prompt_version, profile = engine._resolve_scalping_prompt(
        "watching",
        prompt_version_override=DECISION_QUALITY_V2_PROMPT_VERSION,
    )

    assert prompt == decision_quality_v2_system_prompt("entry")
    assert prompt_type == "scalping_entry"
    assert prompt_version == DECISION_QUALITY_V2_PROMPT_VERSION
    assert profile == "watching"


def test_decision_quality_v2_7_probe_prompt_emits_bounded_wait_intent(monkeypatch):
    engine = _build_engine()
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_ANALYZE_TARGET_PROMPT_VERSION=(
                DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION
            ),
        ),
    )

    prompt, prompt_type, prompt_version, profile = engine._resolve_scalping_prompt(
        "watching"
    )
    assert prompt == decision_quality_v2_7_probe_system_prompt("entry")
    assert "one-share probe intent" in prompt
    assert "completed-bar continuation remains a structural edge" in prompt
    assert "must not by itself erase that edge or produce NO_EDGE/DROP" in prompt
    assert "execution risk only and is never positive evidence" in prompt
    assert prompt_type == "scalping_entry"
    assert prompt_version == DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION
    assert profile == "watching"

    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "EDGE",
            "action": "WAIT",
            "expected_upside_pct": 1.5,
            "expected_downside_pct": -1.0,
            "confidence": 70,
            "reason_codes": ["edge_positive", "recovery_trigger_required"],
            "evidence": {
                "trend": "mixed",
                "liquidity": "adverse",
                "tape": "mixed",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "reversal",
                "positive_edge": "moderate",
                "adverse_risk": "high",
                "trigger": "recovery_required",
            },
        },
        exact_payload={},
        prompt_version=DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION,
    )

    assert result["decision_quality_contract_status"] == "pass"
    assert result["action"] == "WAIT"
    assert result["entry_probe_intent"] is True
    assert result["entry_probe_intent_status"] == "eligible_wait_probe"
    assert result["entry_probe_intent_submit_guard_required"] is True
    assert result["entry_probe_intent_actual_order_submitted"] is False
    assert (
        result["decision_quality_live_adapter"]
        == "decision_quality_v2_7_probe_entry_v8"
    )


def test_decision_quality_v2_13_buy_maps_to_guarded_wait_probe(monkeypatch):
    engine = _build_engine()
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_ANALYZE_TARGET_PROMPT_VERSION=(
                DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
            ),
        ),
    )

    prompt, prompt_type, prompt_version, profile = engine._resolve_scalping_prompt(
        "watching"
    )
    assert prompt == decision_quality_v2_13_recovery_confirmation_system_prompt("entry")
    assert prompt.isascii()
    assert "recovery_confirmation_probe.eligible=true" in prompt
    assert prompt_type == "scalping_entry"
    assert prompt_version == (
        DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
    )
    assert profile == "watching"

    exact_payload = {
        "current": {"price": 10000, "fluctuation_pct": 4.0},
        "features": {
            "quote_fresh_for_entry": True,
            "quote_stale": False,
            "quote_age_ms": 500,
            "quote_depth_present": True,
            "tick_context_stale": False,
            "tick_latest_age_ms": 500,
            "spread_bp": 40,
            "top1_bid_notional": 2_000_000,
            "top1_ask_notional": 2_000_000,
            "same_price_buy_absorption": 1,
            "buy_pressure_10t": 70,
            "net_aggressive_delta_10t": 50,
            "large_sell_print_detected": False,
            "curr_vs_micro_vwap_bp": -10,
            "curr_vs_ma5_bp": 5,
            "price_change_10t_pct": 0.2,
            "entry_order_flow_status": "supportive",
            "order_flow_pressure_source": "trusted_aggressor",
            "entry_momentum_status": "accelerating",
            "tick_aggressor_trusted_count": 12,
            "tick_aggressor_pressure_usable": True,
            "tick_context_quality": "pass",
            "tick_accel_source": "trusted_aggressor",
            "tick_acceleration_ratio": 1.6,
        },
        "entry_candle_context": {
            "completed_bar_count": 20,
            "source_quality": {
                "status": "fresh_consistent",
                "decision_window": {
                    "status": "fresh_consistent",
                    "provider_call_allowed": True,
                    "completed_bar_count": 20,
                },
            },
            "structure": {
                "returns_pct": {
                    "1": 0.6,
                    "3": 0.3,
                    "5": -0.1,
                    "10": 1.2,
                    "20": 1.4,
                    "60": 1.6,
                },
                "slopes_pct_per_bar": {
                    "5": 0.05,
                    "10": 0.1,
                    "20": 0.1,
                    "60": 0.05,
                },
                "peak_drawdown_pct": -1.2,
                "latest_lower_wick_ratio": 0.5,
                "low_rebound_pct": 0.8,
                "high_direction": "up",
                "low_direction": "up_or_flat",
                "volume_ratio": 1.0,
                "volume_direction_alignment": "aligned",
                "regime": "trend",
                "alignment": "supportive",
            },
        },
    }
    model_response = {
        "edge_state": "EDGE",
        "action": "BUY",
        "expected_upside_pct": 1.2,
        "expected_downside_pct": -0.7,
        "confidence": 60,
        "reason_codes": [
            "edge_positive",
            "recovery_trigger_confirmed",
            "risk_reward_favorable",
        ],
        "evidence": {
            "trend": "supportive",
            "liquidity": "mixed",
            "tape": "supportive",
            "risk": "medium",
            "uncertainty": "medium",
            "setup": "reversal",
            "positive_edge": "moderate",
            "adverse_risk": "moderate",
            "trigger": "confirmed",
        },
    }
    result = engine._normalize_decision_quality_entry_result(
        model_response,
        exact_payload=exact_payload,
        prompt_version=DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
    )

    assert result["decision_quality_contract_status"] == "pass"
    assert result["decision_quality_model_action"] == "BUY"
    assert result["action"] == "WAIT"
    assert result["score"] == 64
    assert result["evidence"]["trigger"] == "recovery_required"
    assert "recovery_trigger_required" in result["reason_codes"]
    assert "recovery_trigger_confirmed" not in result["reason_codes"]
    assert result["decision_quality_model_evidence"]["trigger"] == "confirmed"
    assert result["entry_probe_intent"] is True
    assert result["entry_probe_intent_status"] == "eligible_wait_probe"
    assert result["entry_probe_intent_submit_guard_required"] is True
    assert result["entry_probe_intent_actual_order_submitted"] is False
    assert result["decision_quality_runtime_action_mapping"] == (
        "v2_13_buy_to_bounded_wait_probe"
    )
    assert result["decision_quality_live_adapter"] == (
        "decision_quality_v2_13_recovery_confirmation_entry_v1"
    )
    role_gate = evaluate_entry_score_role_gate(
        {**result, "ai_result_source": "live", "ai_parse_ok": True},
        source_stage="analyze_target",
        ai_score=result["score"],
        ai_action=result["action"],
    )
    assert role_gate["entry_score_usable_for_recheck"] is True
    assert role_gate["entry_recheck_probe_intent"] is True
    assert role_gate["entry_recheck_recovery_trigger"] == "recovery_required"

    unconfirmed_payload = json.loads(json.dumps(exact_payload))
    unconfirmed_payload["features"].update(
        {
            "entry_order_flow_status": "mixed",
            "tick_acceleration_ratio": 0.5,
            "net_aggressive_delta_10t": -10,
        }
    )
    rejected = engine._normalize_decision_quality_entry_result(
        model_response,
        exact_payload=unconfirmed_payload,
        prompt_version=DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
    )
    assert rejected["decision_quality_contract_status"] == "semantic_rejected"
    assert rejected["action"] == "DROP"
    assert rejected["score"] == 0
    assert rejected["entry_probe_intent"] is False
    assert "recovery_confirmation_buy_not_eligible" in (
        rejected["decision_quality_contract_errors"]
    )


def test_decision_quality_v2_14_live_adapter_uses_fixed_probe_prior_not_ai_score():
    engine = _build_engine()
    prompt, prompt_type, prompt_version, profile = engine._resolve_scalping_prompt(
        "watching",
        prompt_version_override=(
            DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
        ),
    )
    assert prompt == decision_quality_v2_14_setup_risk_adjudicator_system_prompt(
        "entry"
    )
    assert prompt_type == "scalping_entry"
    assert prompt_version == (
        DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
    )
    assert profile == "watching"

    setup_evidence = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis={
            "schema": "exact_payload_analysis_v1",
            "source_quality": {"status": "pass", "completed_bar_count": 20},
            "executable_liquidity": {"execution_cost_state": "low"},
            "contradictions": [],
            "deterministic_contract_facts": {
                "structural_edge_floor": True,
                "early_session_structural_edge_floor": False,
                "early_session_probe_candidate": False,
                "orderly_pullback_recovery": False,
                "trusted_supportive_trigger": True,
                "adverse_distribution_no_edge": False,
                "blocking_overextension": False,
                "ask_wall_wide_spread": False,
            },
        },
        recovery_analysis={
            "schema": "anticipatory_reversal_analysis_v1",
            "source_mode": "fresh_dual",
            "hard_blockers": [],
            "clean_continuation_probe": {"eligible": True},
            "recovery_confirmation_probe": {"eligible": False},
        },
    )
    risk_response = {
        "schema": ENTRY_RISK_ADJUDICATION_SCHEMA,
        "risk_verdict": "PASS",
        "risk_codes": ["NO_BLOCKING_RISK"],
        "supporting_fact_ids": ["structural_edge_floor"],
        "contradicting_fact_ids": [],
        "confidence": 1,
    }
    live_policy = {
        "enabled": True,
        "status": "active_bounded_krx_canary",
        "canary_mode": "one_share_exploration",
        "maximum_daily_exploration_probes": 3,
        "selected_prompt_version": (
            DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
        ),
        "source_date": "2026-08-06",
        "target_date": "2026-08-07",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "activation_artifact_sha256": "activation-sha",
        "candidate_contract_sha256": "candidate-sha",
        "runtime_effect": True,
    }
    result = engine._normalize_decision_quality_entry_result(
        risk_response,
        exact_payload={"current": {"price": 10000}},
        prompt_version=(DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION),
        entry_setup_evidence=setup_evidence,
        live_policy=live_policy,
    )

    assert result["action"] == "WAIT"
    assert result["score"] == 70
    assert result["decision_quality_score_semantics"] == (
        "fixed_compatibility_prior_not_ai_quality_gate"
    )
    assert result["entry_probe_intent"] is True
    assert result["entry_probe_first_required"] is True
    assert result["entry_ai_full_entry_forbidden"] is True
    assert result["entry_setup_live_policy_mode"] == "one_share_exploration"
    assert result["entry_setup_live_policy_max_daily_exploration_probes"] == 3
    assert "broker_order_forbidden" not in result
    role_gate = evaluate_entry_score_role_gate(
        {**result, "ai_result_source": "live", "ai_parse_ok": True},
        source_stage="analyze_target",
        ai_score=result["score"],
        ai_action=result["action"],
    )
    assert role_gate["entry_score_usable_for_recheck"] is True

    blocked_reentry = engine._normalize_decision_quality_entry_result(
        risk_response,
        exact_payload={
            "current": {"price": 10100},
            "recent_exit_context": {
                "exit_price": 10000,
                "reentry_policy": "fresh_post_exit_confirmation_required",
            },
        },
        prompt_version=(DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION),
        entry_setup_evidence=setup_evidence,
        live_policy=live_policy,
    )
    assert blocked_reentry["action"] == "WAIT"
    assert blocked_reentry["entry_probe_intent"] is False
    assert blocked_reentry["entry_recent_exit_probe_blocked"] is True
    assert blocked_reentry["entry_recent_exit_price_vs_exit_pct"] == 1.0

    rejected = engine._normalize_decision_quality_entry_result(
        {
            **risk_response,
            "action": "BUY",
            "actual_order_submitted": True,
            "broker_order_forbidden": False,
        },
        exact_payload={"current": {"price": 10000}},
        prompt_version=(DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION),
        entry_setup_evidence=setup_evidence,
        live_policy=live_policy,
    )
    assert rejected["decision_quality_contract_status"] == "semantic_rejected"
    assert rejected["entry_setup_family"] == "CLEAN_CONTINUATION"
    assert rejected["entry_setup_state"] == "READY"
    assert rejected["entry_setup_evidence_sha256"] == setup_evidence["evidence_sha256"]
    assert rejected["entry_ai_raw_risk_verdict"] == "PASS"
    assert rejected["action"] == "WAIT"
    assert rejected["score"] == 0
    assert rejected["entry_probe_intent"] is False
    assert rejected["entry_ai_rejected_unexpected_fields"] == [
        "action",
        "actual_order_submitted",
        "broker_order_forbidden",
    ]
    assert "actual_order_submitted" not in rejected
    assert "broker_order_forbidden" not in rejected

    waiting_setup = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis={
            "schema": "exact_payload_analysis_v1",
            "source_quality": {"status": "pass", "completed_bar_count": 20},
            "executable_liquidity": {"execution_cost_state": "low"},
            "contradictions": [],
            "deterministic_contract_facts": {
                "structural_edge_floor": True,
                "early_session_structural_edge_floor": False,
                "early_session_probe_candidate": False,
                "orderly_pullback_recovery": False,
                "trusted_supportive_trigger": False,
                "adverse_distribution_no_edge": False,
                "blocking_overextension": False,
                "ask_wall_wide_spread": False,
            },
        },
        recovery_analysis={
            "schema": "anticipatory_reversal_analysis_v1",
            "source_mode": "fresh_dual",
            "hard_blockers": [],
            "clean_continuation_probe": {"eligible": False},
            "recovery_confirmation_probe": {"eligible": False},
        },
    )
    waiting_rejected = engine._normalize_decision_quality_entry_result(
        {
            "schema": ENTRY_RISK_ADJUDICATION_SCHEMA,
            "risk_verdict": "CAUTION",
            "risk_codes": ["CONFIRMATION_MISSING"],
            "supporting_fact_ids": ["invented_positive_fact"],
            "contradicting_fact_ids": ["trigger_confirmation_missing"],
            "confidence": 0.74,
        },
        exact_payload={"current": {"price": 10000}},
        prompt_version=(DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION),
        entry_setup_evidence=waiting_setup,
        live_policy=live_policy,
    )
    assert waiting_rejected["decision_quality_contract_status"] == ("semantic_rejected")
    assert waiting_rejected["action"] == "WAIT"
    assert waiting_rejected["score"] == 0
    assert waiting_rejected["edge_state"] == "EDGE"
    assert waiting_rejected["entry_probe_intent"] is False
    assert waiting_rejected["entry_ai_raw_risk_verdict"] == "CAUTION"
    assert waiting_rejected["entry_ai_raw_confidence"] == 0.74
    assert waiting_rejected["entry_ai_raw_supporting_fact_ids"] == [
        "invented_positive_fact"
    ]
    assert waiting_rejected["entry_ai_invalid_supporting_fact_ids"] == [
        "invented_positive_fact"
    ]

    malformed_rejected = engine._normalize_decision_quality_entry_result(
        {
            "schema": ENTRY_RISK_ADJUDICATION_SCHEMA,
            "risk_verdict": "CAUTION",
            "risk_codes": 7,
            "supporting_fact_ids": 11,
            "contradicting_fact_ids": 13,
            "confidence": {"normalized": 0.74},
        },
        exact_payload={"current": {"price": 10000}},
        prompt_version=(DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION),
        entry_setup_evidence=setup_evidence,
        live_policy=live_policy,
    )
    assert malformed_rejected["decision_quality_contract_status"] == (
        "semantic_rejected"
    )
    assert malformed_rejected["action"] == "WAIT"
    assert malformed_rejected["entry_probe_intent"] is False
    assert malformed_rejected["entry_ai_raw_risk_codes"] == []
    assert malformed_rejected["entry_ai_raw_supporting_fact_ids"] == []
    assert malformed_rejected["entry_ai_raw_contradicting_fact_ids"] == []
    assert malformed_rejected["entry_ai_raw_confidence"] == "{'normalized': 0.74}"


def test_decision_quality_v2_13_clean_wait_maps_to_guarded_probe(monkeypatch):
    engine = _build_engine()
    monkeypatch.setattr(
        openai_module,
        "build_v2_13_recovery_confirmation_analysis_v1",
        lambda *_args, **_kwargs: {
            "clean_continuation_probe": {"eligible": True},
            "execution_cost": {"conservative_execution_cost_pct": 0.2},
        },
    )
    monkeypatch.setattr(
        openai_module,
        "validate_v2_13_recovery_confirmation_response",
        lambda **_kwargs: [],
    )

    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "EDGE",
            "action": "WAIT",
            "expected_upside_pct": 1.0,
            "expected_downside_pct": -0.8,
            "confidence": 58,
            "reason_codes": ["edge_positive", "recovery_trigger_required"],
            "evidence": {
                "trend": "supportive",
                "liquidity": "adverse",
                "tape": "mixed",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "pullback_recovery",
                "positive_edge": "moderate",
                "adverse_risk": "high",
                "trigger": "recovery_required",
            },
        },
        exact_payload={},
        prompt_version=DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
    )

    assert result["decision_quality_contract_status"] == "pass"
    assert result["action"] == "WAIT"
    assert result["entry_probe_intent"] is True
    assert result["entry_probe_intent_status"] == "eligible_wait_probe"
    assert (
        result["entry_probe_intent_eligibility_path"] == "v2_13_clean_continuation_wait"
    )
    assert result["entry_probe_intent_after_cost_reward_risk"] == pytest.approx(0.8)
    assert result["decision_quality_runtime_action_mapping"] == (
        "v2_13_clean_wait_to_bounded_wait_probe"
    )
    assert result["entry_probe_intent_submit_guard_required"] is True
    assert result["entry_probe_intent_actual_order_submitted"] is False


def test_decision_quality_v2_13_repairs_unusable_non_buy_to_safe_wait():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "NO_EDGE",
            "action": "DROP",
            "expected_upside_pct": 0.2,
            "expected_downside_pct": -1.0,
            "confidence": 80,
            "reason_codes": ["edge_absent"],
            "evidence": {
                "trend": "adverse",
                "liquidity": "adverse",
                "tape": "adverse",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "no_setup",
                "positive_edge": "none",
                "adverse_risk": "high",
                "trigger": "failed",
            },
        },
        exact_payload={},
        prompt_version=DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
    )

    assert result["decision_quality_contract_status"] == "pass"
    assert result["action"] == "WAIT"
    assert result["edge_state"] == "INSUFFICIENT_DATA"
    assert result["entry_probe_intent"] is False
    assert result["decision_quality_contract_repair_codes"] == [
        "unusable_source_fail_closed_wait"
    ]
    assert result["decision_quality_model_action"] == "DROP"


def test_decision_quality_v2_7_repairs_early_session_drop_to_guarded_wait_probe():
    engine = _build_engine()
    exact_payload = {
        "current": {"price": 14900, "fluctuation_pct": 13.91},
        "features": {
            "entry_order_flow_status": "supportive",
            "order_flow_pressure_source": "trusted_aggressor",
            "entry_momentum_status": "flat",
            "buy_pressure_10t": 93.33,
            "net_aggressive_delta_10t": 156,
            "tick_aggressor_trusted_count": 10,
            "tick_aggressor_pressure_usable": True,
            "quote_fresh_for_entry": True,
            "tick_context_stale": False,
            "large_sell_print_detected": False,
            "tick_context_quality": "fresh_computed",
            "tick_accel_source": "same_second_burst_10ticks",
            "spread_bp": 40.27,
            "top1_bid_notional": 536_400,
            "top1_ask_notional": 4_246_500,
            "top3_bid_notional": 14_870_200,
            "top3_ask_notional": 11_145_200,
            "would_fill_now": False,
        },
        "entry_candle_context": {
            "completed_bar_count": 13,
            "structure": {
                "returns_pct": {"1": 1.717, "3": 7.5527, "5": 7.6308, "10": 6.8543},
                "slopes_pct_per_bar": {
                    "1": 1.717,
                    "3": 2.2952,
                    "5": 2.1971,
                    "10": 0.5737,
                },
                "peak_drawdown_pct": -0.2694,
                "high_direction": "up_or_flat",
                "low_direction": "up_or_flat",
                "volume_ratio": 3.937,
                "volume_direction_alignment": "bullish_confirmed",
                "regime": "breakout",
                "alignment": "positive",
            },
        },
    }

    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "NO_EDGE",
            "action": "DROP",
            "expected_upside_pct": 0.0,
            "expected_downside_pct": -1.2,
            "confidence": 78,
            "reason_codes": [
                "edge_absent",
                "liquidity_adverse",
                "setup_invalidated",
            ],
            "evidence": {
                "trend": "supportive",
                "liquidity": "adverse",
                "tape": "supportive",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "no_setup",
                "positive_edge": "none",
                "adverse_risk": "blocking",
                "trigger": "not_applicable",
            },
        },
        exact_payload=exact_payload,
        prompt_version=DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION,
    )

    assert result["decision_quality_contract_status"] == "pass"
    assert result["action"] == "WAIT"
    assert result["edge_state"] == "EDGE"
    assert result["evidence"]["setup"] == "continuation"
    assert result["evidence"]["adverse_risk"] == "high"
    assert result["evidence"]["trigger"] == "recovery_required"
    assert result["entry_probe_intent"] is True
    assert result["entry_probe_intent_submit_guard_required"] is True
    assert result["entry_probe_intent_actual_order_submitted"] is False
    assert "non_buy_early_session_probe_aligned" in (
        result["decision_quality_contract_repair_codes"]
    )
    assert (
        result["decision_quality_live_adapter"]
        == "decision_quality_v2_7_probe_entry_v8"
    )


def test_decision_quality_v2_7_probe_blocks_wait_reentry_above_recent_exit():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "EDGE",
            "action": "WAIT",
            "expected_upside_pct": 1.0,
            "expected_downside_pct": -0.9,
            "confidence": 62,
            "reason_codes": [
                "edge_positive",
                "recovery_trigger_required",
                "liquidity_adverse",
            ],
            "evidence": {
                "trend": "supportive",
                "liquidity": "adverse",
                "tape": "mixed",
                "risk": "medium",
                "uncertainty": "medium",
                "setup": "pullback_recovery",
                "positive_edge": "moderate",
                "adverse_risk": "moderate",
                "trigger": "recovery_required",
            },
        },
        exact_payload={
            "current": {"price": 109900},
            "recent_exit_context": {
                "schema": "recent_scalp_exit_context_v1",
                "exit_price": 109600,
                "reentry_policy": "fresh_post_exit_confirmation_required",
            },
        },
        prompt_version=DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION,
    )

    assert result["decision_quality_contract_status"] == "pass"
    assert result["action"] == "WAIT"
    assert result["entry_probe_intent"] is False
    assert (
        result["entry_probe_intent_status"]
        == "recent_clean_profit_reentry_not_confirmed"
    )
    assert result["entry_recent_exit_context_status"] == "active"
    assert result["entry_recent_exit_probe_blocked"] is True
    assert result["entry_recent_exit_price_vs_exit_pct"] == pytest.approx(0.273723)


def test_hot_entry_payload_preserves_recent_exit_context():
    engine = _build_engine()
    recent_exit = {
        "schema": "recent_scalp_exit_context_v1",
        "age_sec": 10.5,
        "exit_price": 109600,
        "realized_profit_pct": 0.5,
        "reentry_policy": "fresh_post_exit_confirmation_required",
    }

    payload = engine._build_entry_screen_hot_payload(
        {"curr": 109900, "recent_exit_context": recent_exit},
        [],
        [],
        feature_packet={},
    )
    entry_price_payload = json.loads(
        engine._build_scalping_entry_price_user_input(
            stock_name="SK innovation",
            stock_code="096770",
            ws_data={"curr": 109900, "recent_exit_context": recent_exit},
            recent_ticks=[],
            recent_candles=[],
            price_ctx={"resolved_order_price": 109600},
        )
    )

    assert payload["recent_exit_context"] == recent_exit
    assert entry_price_payload["recent_exit_context"] == recent_exit


def test_hot_entry_payload_preserves_explicit_external_market_context():
    engine = _build_engine()
    external = {
        "quality": "fresh",
        "source": "licensed_fixture",
        "risk_state": "RISK_OFF",
        "observed_at": "2026-08-07T09:05:00+09:00",
    }

    payload = engine._build_entry_screen_hot_payload(
        {"curr": 109900, "external_market_context": external},
        [],
        [],
        feature_packet={},
    )

    assert payload["external_market_context"] == external


def test_analyze_target_probe_prompt_keeps_exact_schema_and_version(monkeypatch):
    engine = _build_engine()
    captured = {}
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_ANALYZE_TARGET_PROMPT_VERSION=(
                DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION
            ),
            OPENAI_ANALYZE_TARGET_HOT_INPUT_ENABLED=False,
            OPENAI_ENTRY_SCREEN_V2_INPUT_ENABLED=True,
        ),
    )

    def _fake_call(prompt, user_input, **kwargs):
        captured["prompt"] = prompt
        captured["payload"] = json.loads(user_input)
        captured["schema_name"] = kwargs.get("schema_name")
        return {
            "edge_state": "NO_EDGE",
            "action": "DROP",
            "expected_upside_pct": 0.5,
            "expected_downside_pct": -1.0,
            "confidence": 80,
            "reason_codes": ["edge_absent", "risk_reward_unfavorable"],
            "evidence": {
                "trend": "adverse",
                "liquidity": "mixed",
                "tape": "mixed",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "no_setup",
                "positive_edge": "none",
                "adverse_risk": "high",
                "trigger": "failed",
            },
        }

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)
    result = engine.analyze_target(
        "테스트",
        _sample_ws_data(),
        _sample_ticks(),
        _sample_candles(),
        strategy="SCALPING",
        prompt_profile="watching",
        candle_context=_allowed_entry_candle_context(),
    )

    assert captured["prompt"] == decision_quality_v2_7_probe_system_prompt("entry")
    assert captured["schema_name"] == "decision_quality_v2_7_entry"
    assert captured["payload"]["exact_payload"]["input_schema"] == "entry_screen_hot_v1"
    assert result["ai_prompt_version"] == DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION
    assert result["ai_input_schema"] == "decision_quality_v2_7_entry_input"
    assert result["entry_probe_intent"] is False
    assert result["entry_probe_intent_status"] == "not_eligible"


def test_analyze_target_v2_13_supplies_shared_recovery_analysis(monkeypatch):
    engine = _build_engine()
    captured = {}
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_ANALYZE_TARGET_PROMPT_VERSION=(
                DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
            ),
            OPENAI_ANALYZE_TARGET_HOT_INPUT_ENABLED=False,
            OPENAI_ENTRY_SCREEN_V2_INPUT_ENABLED=True,
        ),
    )

    def _fake_call(prompt, user_input, **kwargs):
        captured["prompt"] = prompt
        captured["payload"] = json.loads(user_input)
        captured["schema_name"] = kwargs.get("schema_name")
        return {
            "edge_state": "NO_EDGE",
            "action": "DROP",
            "expected_upside_pct": 0.5,
            "expected_downside_pct": -1.0,
            "confidence": 80,
            "reason_codes": ["edge_absent", "risk_reward_unfavorable"],
            "evidence": {
                "trend": "adverse",
                "liquidity": "mixed",
                "tape": "mixed",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "no_setup",
                "positive_edge": "none",
                "adverse_risk": "high",
                "trigger": "failed",
            },
        }

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)
    result = engine.analyze_target(
        "테스트",
        _sample_ws_data(),
        _sample_ticks(),
        _sample_candles(),
        strategy="SCALPING",
        prompt_profile="watching",
        candle_context=_allowed_entry_candle_context(),
    )

    assert captured["prompt"] == (
        decision_quality_v2_13_recovery_confirmation_system_prompt("entry")
    )
    assert captured["schema_name"] == "decision_quality_v2_7_entry"
    assert captured["payload"]["exact_payload"]["input_schema"] == (
        "entry_screen_hot_v1"
    )
    shared_analysis = captured["payload"]["anticipatory_reversal_analysis_v1"]
    assert "selective_recovery_probe" in shared_analysis
    assert "recovery_confirmation_probe" in shared_analysis
    assert result["ai_prompt_version"] == (
        DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
    )
    assert result["ai_input_schema"] == "decision_quality_v2_13_entry_input"
    assert result["decision_quality_live_adapter"] == (
        "decision_quality_v2_13_recovery_confirmation_entry_v1"
    )


def test_decision_quality_v2_7_semantic_failure_is_fail_closed(monkeypatch):
    engine = _build_engine()
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_ANALYZE_TARGET_PROMPT_VERSION="decision_quality_v2_7",
        ),
    )
    monkeypatch.setattr(
        engine,
        "_call_openai_safe",
        lambda *args, **kwargs: {
            "edge_state": "EDGE",
            "action": "BUY",
            "expected_upside_pct": 0.5,
            "expected_downside_pct": -1.0,
            "confidence": 95,
            "reason_codes": ["edge_positive"],
            "evidence": {
                "trend": "supportive",
                "liquidity": "supportive",
                "tape": "supportive",
                "risk": "low",
                "uncertainty": "low",
                "setup": "continuation",
                "positive_edge": "strong",
                "adverse_risk": "low",
                "trigger": "confirmed",
            },
        },
    )

    result = engine.analyze_target(
        "테스트",
        _sample_ws_data(),
        _sample_ticks(),
        _sample_candles(),
        strategy="SCALPING",
        prompt_profile="watching",
        candle_context=_allowed_entry_candle_context(),
    )

    assert result["action"] == "DROP"
    assert result["score"] == 0
    assert result["decision_quality_contract_status"] == "semantic_rejected"
    assert (
        result["decision_quality_score_semantics"]
        == "fail_closed_not_model_quality_score"
    )
    assert (
        "entry_buy_reward_risk_below_floor"
        in result["decision_quality_contract_errors"]
    )
    assert result["decision_quality_model_action"] == "BUY"
    assert result["decision_quality_model_edge_state"] == "EDGE"
    assert result["decision_quality_model_expected_upside_pct"] == 0.5
    assert result["decision_quality_model_expected_downside_pct"] == -1.0
    assert result["decision_quality_model_evidence"]["trigger"] == "confirmed"


def test_decision_quality_v2_7_repairs_non_buy_invalid_reason_code_only():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "NO_EDGE",
            "action": "DROP",
            "expected_upside_pct": 0.4,
            "expected_downside_pct": -1.4,
            "confidence": 78,
            "reason_codes": [
                "edge_absent",
                "tape_sample_insufficient",
                "liquidity_adverse",
                "trigger=insufficient_tape_confirmation",
            ],
            "evidence": {
                "trend": "adverse",
                "liquidity": "adverse",
                "tape": "insufficient",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "no_setup",
                "positive_edge": "none",
                "adverse_risk": "blocking",
                "trigger": "insufficient",
            },
        },
        exact_payload={
            "features": {
                "tick_aggressor_trusted_count": 0,
                "tick_context_quality": "fresh_computed",
            }
        },
    )

    assert result["action"] == "DROP"
    assert result["score"] == 11
    assert result["decision_quality_contract_status"] == "pass"
    assert result["reason_codes"] == [
        "edge_absent",
        "tape_sample_insufficient",
        "liquidity_adverse",
    ]
    assert result["decision_quality_contract_repair_applied"] is True
    assert result["decision_quality_contract_repair_codes"] == [
        "non_buy_invalid_reason_codes_removed"
    ]
    assert result["decision_quality_contract_invalid_reason_codes"] == [
        "trigger=insufficient_tape_confirmation"
    ]
    assert result["decision_quality_model_reason_codes"][-1] == (
        "trigger=insufficient_tape_confirmation"
    )


def test_decision_quality_v2_7_repairs_non_buy_exact_ledger_classification():
    engine = _build_engine()
    exact_payload = {
        "current": {"fluctuation_pct": 8.75},
        "features": {
            "entry_order_flow_status": "supportive",
            "order_flow_pressure_source": "trusted_aggressor",
            "entry_momentum_status": "accelerating",
            "buy_pressure_10t": 85.93,
            "net_aggressive_delta_10t": 1251,
            "tick_aggressor_trusted_count": 10,
            "tick_aggressor_pressure_usable": True,
            "quote_fresh_for_entry": True,
            "tick_context_stale": False,
            "large_sell_print_detected": False,
            "tick_context_quality": "fresh_computed",
            "tick_accel_source": "computed_10ticks",
            "curr_vs_micro_vwap_bp": -16.39,
            "curr_vs_ma5_bp": 3.29,
            "spread_bp": 82.1,
            "top1_bid_notional": 47_861_310,
            "top1_ask_notional": 55_163_220,
        },
        "entry_candle_context": {
            "structure": {
                "returns_pct": {
                    "1": 0.2,
                    "3": 0.3,
                    "5": 0.5,
                    "10": 0.7,
                    "20": 0.9,
                    "60": -0.1,
                },
                "slopes_pct_per_bar": {
                    "5": 0.1,
                    "10": 0.1,
                    "20": 0.1,
                    "60": -0.1,
                },
            }
        },
    }
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "NO_EDGE",
            "action": "DROP",
            "expected_upside_pct": 0.4,
            "expected_downside_pct": -1.0,
            "confidence": 64,
            "reason_codes": ["distribution_adverse", "liquidity_adverse"],
            "evidence": {
                "trend": "adverse",
                "liquidity": "adverse",
                "tape": "supportive",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "no_setup",
                "positive_edge": "none",
                "adverse_risk": "blocking",
                "trigger": "failed",
            },
        },
        exact_payload=exact_payload,
    )

    assert result["action"] == "DROP"
    assert result["score"] == 18
    assert result["edge_state"] == "EDGE"
    assert result["evidence"]["positive_edge"] == "moderate"
    assert result["evidence"]["trigger"] == "confirmed"
    assert result["decision_quality_contract_status"] == "pass"
    assert result["decision_quality_contract_repair_applied"] is True
    assert result["decision_quality_contract_original_errors"] == [
        "entry_structural_edge_floor_misclassified",
        "entry_trusted_supportive_trigger_misclassified",
    ]
    assert result["decision_quality_contract_repair_codes"] == [
        "non_buy_deterministic_edge_classification_aligned"
    ]
    assert "edge_positive" in result["reason_codes"]
    assert "edge_absent" not in result["reason_codes"]
    assert "no_positive_edge" not in result["reason_codes"]
    assert result["decision_quality_model_edge_state"] == "NO_EDGE"
    assert result["decision_quality_model_evidence"]["positive_edge"] == "none"


def test_decision_quality_probe_repairs_positive_downside_structural_drop():
    engine = _build_engine()
    exact_payload = {
        "features": {
            "tick_aggressor_trusted_count": 10,
            "tick_context_quality": "fresh_computed",
        },
        "entry_candle_context": {
            "structure": {
                "returns_pct": {
                    "1": 1.06,
                    "3": 1.42,
                    "5": 1.06,
                    "10": 1.24,
                    "20": 0.53,
                    "60": -0.2,
                },
                "slopes_pct_per_bar": {
                    "5": 0.1,
                    "10": 0.1,
                    "20": 0.1,
                    "60": -0.1,
                },
            }
        },
    }
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "NO_EDGE",
            "action": "DROP",
            "expected_upside_pct": 1.0,
            "expected_downside_pct": 1.2,
            "confidence": 70,
            "reason_codes": ["edge_absent", "risk_reward_unfavorable"],
            "evidence": {
                "trend": "supportive",
                "liquidity": "adverse",
                "tape": "mixed",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "pullback_recovery",
                "positive_edge": "moderate",
                "adverse_risk": "blocking",
                "trigger": "failed",
            },
        },
        exact_payload=exact_payload,
        prompt_version=DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION,
    )

    assert result["action"] == "DROP"
    assert result["edge_state"] == "EDGE"
    assert result["expected_downside_pct"] == -1.2
    assert result["decision_quality_contract_status"] == "pass"
    assert result["entry_probe_intent"] is False
    assert result["decision_quality_contract_repair_codes"] == [
        "non_buy_downside_sign_normalized",
        "non_buy_deterministic_edge_classification_aligned",
    ]


def test_decision_quality_probe_aligns_bounded_reversal_to_wait_probe():
    engine = _build_engine()
    exact_payload = {
        "current": {"fluctuation_pct": -18.27},
        "features": {
            "entry_momentum_status": "accelerating",
            "tick_acceleration_ratio": 14.333,
            "quote_fresh_for_entry": True,
            "tick_context_stale": False,
            "tick_aggressor_trusted_count": 10,
            "tick_context_quality": "fresh_computed",
        },
        "entry_candle_context": {
            "structure": {
                "returns_pct": {
                    "1": -0.97,
                    "3": 0.49,
                    "5": 1.16,
                    "10": 2.17,
                    "20": -8.38,
                    "60": -10.0,
                },
                "slopes_pct_per_bar": {
                    "5": 0.1,
                    "10": 0.2,
                    "20": -0.3,
                    "60": -0.2,
                },
            }
        },
    }
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "NO_EDGE",
            "action": "DROP",
            "expected_upside_pct": 1.2,
            "expected_downside_pct": -1.0,
            "confidence": 79,
            "reason_codes": ["edge_absent", "tape_adverse"],
            "evidence": {
                "trend": "adverse",
                "liquidity": "adverse",
                "tape": "adverse",
                "risk": "high",
                "uncertainty": "high",
                "setup": "no_setup",
                "positive_edge": "none",
                "adverse_risk": "high",
                "trigger": "failed",
            },
        },
        exact_payload=exact_payload,
        prompt_version=DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION,
    )

    assert result["action"] == "WAIT"
    assert result["edge_state"] == "EDGE"
    assert result["evidence"]["setup"] == "reversal"
    assert result["evidence"]["trigger"] == "recovery_required"
    assert result["entry_probe_intent"] is True
    assert result["decision_quality_contract_status"] == "pass"
    assert result["decision_quality_contract_repair_codes"] == [
        "non_buy_bounded_reversal_probe_aligned"
    ]


def test_decision_quality_v2_7_repairs_known_tape_trigger_reason_alias():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "NO_EDGE",
            "action": "DROP",
            "expected_upside_pct": 0.4,
            "expected_downside_pct": -1.0,
            "confidence": 70,
            "reason_codes": [
                "edge_absent",
                "tape_sample_insufficient",
                "trigger_state_insufficient_tape_confirmation",
            ],
            "evidence": {
                "trend": "mixed",
                "liquidity": "mixed",
                "tape": "insufficient",
                "risk": "high",
                "uncertainty": "high",
                "setup": "no_setup",
                "positive_edge": "none",
                "adverse_risk": "high",
                "trigger": "insufficient",
            },
        },
        exact_payload={
            "features": {
                "tick_aggressor_trusted_count": 0,
                "tick_context_quality": "fresh_computed",
            }
        },
    )

    assert result["action"] == "DROP"
    assert result["decision_quality_contract_status"] == "pass"
    assert result["decision_quality_contract_repair_applied"] is True
    assert result["decision_quality_contract_repair_codes"] == [
        "non_buy_invalid_reason_codes_removed"
    ]
    assert result["decision_quality_contract_invalid_reason_codes"] == [
        "trigger_state_insufficient_tape_confirmation"
    ]
    assert result["reason_codes"] == ["edge_absent", "tape_sample_insufficient"]


def test_decision_quality_v2_7_repairs_blocking_risk_enum_without_buy_authority():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "NO_EDGE",
            "action": "DROP",
            "expected_upside_pct": 0.4,
            "expected_downside_pct": -1.0,
            "confidence": 72,
            "reason_codes": ["edge_absent", "adverse_risk_high"],
            "evidence": {
                "trend": "adverse",
                "liquidity": "adverse",
                "tape": "adverse",
                "risk": "blocking",
                "uncertainty": "medium",
                "setup": "no_setup",
                "positive_edge": "none",
                "adverse_risk": "blocking",
                "trigger": "failed",
            },
        },
        exact_payload={
            "features": {
                "tick_aggressor_trusted_count": 0,
                "tick_context_quality": "fresh_computed",
            }
        },
    )

    assert result["action"] == "DROP"
    assert result["evidence"]["risk"] == "high"
    assert result["decision_quality_contract_status"] == "pass"
    assert result["decision_quality_contract_repair_codes"] == [
        "non_buy_blocking_risk_enum_aligned"
    ]


def _trusted_supportive_wait_exact_payload(*, ask_wall: bool = False):
    return {
        "features": {
            "curr_vs_micro_vwap_bp": 20,
            "curr_vs_ma5_bp": 15,
            "entry_order_flow_status": "supportive",
            "order_flow_pressure_source": "trusted_aggressor",
            "entry_momentum_status": "accelerating",
            "buy_pressure_10t": 82,
            "net_aggressive_delta_10t": 25,
            "tick_aggressor_pressure_usable": True,
            "tick_aggressor_trusted_count": 10,
            "quote_fresh_for_entry": True,
            "tick_context_stale": False,
            "large_sell_print_detected": False,
            "spread_bp": 60 if ask_wall else 30,
            "top1_bid_notional": 1_000_000,
            "top1_ask_notional": 8_000_000 if ask_wall else 2_000_000,
        },
        "entry_candle_context": {
            "structure": {
                "returns_pct": {
                    "1": 0.2,
                    "3": 0.4,
                    "5": 0.6,
                    "10": 0.8,
                    "20": 1.0,
                    "60": -0.1,
                },
                "slopes_pct_per_bar": {
                    "5": 0.1,
                    "10": 0.1,
                    "20": 0.1,
                    "60": -0.1,
                },
            }
        },
    }


def test_decision_quality_v2_7_repairs_observed_insufficient_wait_evidence():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "INSUFFICIENT_DATA",
            "action": "WAIT",
            "expected_upside_pct": None,
            "expected_downside_pct": None,
            "confidence": 48,
            "reason_codes": [
                "insufficient_core_data",
                "tape_sample_insufficient",
                "completed_bars_missing",
                "source_stale",
            ],
            "evidence": {
                "trend": "insufficient",
                "liquidity": "adverse",
                "tape": "insufficient",
                "risk": "high",
                "uncertainty": "high",
                "setup": "insufficient",
                "positive_edge": "none",
                "adverse_risk": "high",
                "trigger": "insufficient",
            },
        },
        exact_payload={},
        prompt_version=DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION,
    )

    assert result["action"] == "WAIT"
    assert result["decision_quality_contract_status"] == "pass"
    assert result["entry_probe_intent"] is False
    assert result["evidence"]["positive_edge"] == "insufficient"
    assert result["evidence"]["adverse_risk"] == "insufficient"
    assert result["decision_quality_model_evidence"]["positive_edge"] == "none"
    assert result["decision_quality_contract_repair_codes"] == [
        "non_buy_insufficient_evidence_aligned"
    ]


def test_decision_quality_v2_7_repairs_observed_wait_trigger_contradiction():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "EDGE",
            "action": "WAIT",
            "expected_upside_pct": 1.8,
            "expected_downside_pct": -1.0,
            "confidence": 62,
            "reason_codes": [
                "structural_edge_without_trigger",
                "liquidity_adverse",
                "risk_reward_unfavorable",
            ],
            "evidence": {
                "trend": "supportive",
                "liquidity": "adverse",
                "tape": "supportive",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "continuation",
                "positive_edge": "moderate",
                "adverse_risk": "high",
                "trigger": "confirmed",
            },
        },
        exact_payload=_trusted_supportive_wait_exact_payload(),
        prompt_version=DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION,
    )

    assert result["action"] == "WAIT"
    assert result["decision_quality_contract_status"] == "pass"
    assert result["evidence"]["trigger"] == "recovery_required"
    assert "recovery_trigger_required" in result["reason_codes"]
    assert result["entry_probe_intent"] is True
    assert result["decision_quality_contract_repair_codes"] == [
        "non_buy_wait_recovery_trigger_aligned"
    ]


def test_decision_quality_v2_7_keeps_trusted_supportive_wait_probe_candidate():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "EDGE",
            "action": "WAIT",
            "expected_upside_pct": 1.0,
            "expected_downside_pct": -0.9,
            "confidence": 70,
            "reason_codes": [
                "structural_edge_without_trigger",
                "recovery_trigger_required",
                "liquidity_adverse",
            ],
            "evidence": {
                "trend": "supportive",
                "liquidity": "adverse",
                "tape": "supportive",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "continuation",
                "positive_edge": "moderate",
                "adverse_risk": "high",
                "trigger": "recovery_required",
            },
        },
        exact_payload=_trusted_supportive_wait_exact_payload(),
        prompt_version=DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION,
    )

    assert result["action"] == "WAIT"
    assert result["decision_quality_contract_status"] == "pass"
    assert result["entry_probe_intent"] is True
    assert result["entry_probe_intent_status"] == "eligible_wait_probe"
    assert result["entry_probe_intent_actual_order_submitted"] is False
    assert result["entry_probe_intent_submit_guard_required"] is True
    assert result["decision_quality_contract_repair_applied"] is False


def test_decision_quality_v2_7_repairs_trusted_wait_blocking_risk_without_probe():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "EDGE",
            "action": "WAIT",
            "expected_upside_pct": 0.9,
            "expected_downside_pct": -0.8,
            "confidence": 68,
            "reason_codes": [
                "edge_positive",
                "recovery_trigger_required",
                "liquidity_adverse",
                "ask_wall_adverse",
            ],
            "evidence": {
                "trend": "supportive",
                "liquidity": "adverse",
                "tape": "supportive",
                "risk": "blocking",
                "uncertainty": "medium",
                "setup": "continuation",
                "positive_edge": "moderate",
                "adverse_risk": "blocking",
                "trigger": "recovery_required",
            },
        },
        exact_payload=_trusted_supportive_wait_exact_payload(ask_wall=True),
        prompt_version=DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION,
    )

    assert result["action"] == "WAIT"
    assert result["evidence"]["risk"] == "high"
    assert result["decision_quality_contract_status"] == "pass"
    assert result["entry_probe_intent"] is False
    assert result["decision_quality_contract_repair_codes"] == [
        "non_buy_blocking_risk_enum_aligned"
    ]


def test_decision_quality_v2_7_repairs_trusted_wait_positive_downside_sign():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "EDGE",
            "action": "WAIT",
            "expected_upside_pct": 0.9,
            "expected_downside_pct": 0.8,
            "confidence": 68,
            "reason_codes": [
                "structural_edge_without_trigger",
                "recovery_trigger_required",
                "liquidity_adverse",
            ],
            "evidence": {
                "trend": "supportive",
                "liquidity": "adverse",
                "tape": "supportive",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "continuation",
                "positive_edge": "moderate",
                "adverse_risk": "high",
                "trigger": "recovery_required",
            },
        },
        exact_payload=_trusted_supportive_wait_exact_payload(),
        prompt_version=DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION,
    )

    assert result["action"] == "WAIT"
    assert result["expected_downside_pct"] == -0.8
    assert result["decision_quality_contract_status"] == "pass"
    assert result["entry_probe_intent"] is True
    assert result["decision_quality_contract_repair_codes"] == [
        "non_buy_downside_sign_normalized"
    ]


@pytest.mark.parametrize(
    "model_action",
    [
        "STAGE_DROP",
        "STAGE-SPECIFIC ACTION=DROP",
        "STAGE-SPECIFIC DROP",
        "STAGE_DECISION_DROP",
    ],
)
def test_decision_quality_v2_7_repairs_known_stage_drop_aliases(model_action):
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "NO_EDGE",
            "action": model_action,
            "expected_upside_pct": 0.1,
            "expected_downside_pct": -0.8,
            "confidence": 75,
            "reason_codes": ["edge_absent", "tape_adverse"],
            "evidence": {
                "trend": "adverse",
                "liquidity": "adverse",
                "tape": "adverse",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "no_setup",
                "positive_edge": "weak",
                "adverse_risk": "high",
                "trigger": "failed",
            },
        },
        exact_payload={},
    )

    assert result["action"] == "DROP"
    assert result["decision_quality_model_action"] == model_action
    assert result["decision_quality_contract_status"] == "pass"
    assert result["decision_quality_contract_repair_codes"] == [
        "non_buy_stage_drop_action_alias_normalized"
    ]


@pytest.mark.parametrize(
    ("action", "edge_state", "trigger", "reason_codes"),
    [
        (
            "WAIT",
            "EDGE",
            "recovery_required",
            [
                "edge_positive",
                "recovery_trigger_required",
                "trigger_state_unconfirmed",
            ],
        ),
        (
            "DROP",
            "NO_EDGE",
            "not_applicable",
            [
                "no_positive_edge",
                "distribution_adverse",
                "trigger_state_unconfirmed",
            ],
        ),
    ],
)
def test_decision_quality_v2_7_removes_redundant_unconfirmed_trigger_token(
    action, edge_state, trigger, reason_codes
):
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": edge_state,
            "action": action,
            "expected_upside_pct": 0.8 if action == "WAIT" else 0.1,
            "expected_downside_pct": -0.8,
            "confidence": 68,
            "reason_codes": reason_codes,
            "evidence": {
                "trend": "supportive" if action == "WAIT" else "adverse",
                "liquidity": "mixed" if action == "WAIT" else "adverse",
                "tape": "supportive" if action == "WAIT" else "adverse",
                "risk": "medium" if action == "WAIT" else "high",
                "uncertainty": "medium",
                "setup": "reversal" if action == "WAIT" else "no_setup",
                "positive_edge": "moderate" if action == "WAIT" else "none",
                "adverse_risk": "high",
                "trigger": trigger,
            },
        },
        exact_payload=(
            _trusted_supportive_wait_exact_payload() if action == "WAIT" else {}
        ),
    )

    assert result["action"] == action
    assert result["decision_quality_model_action"] == action
    assert result["decision_quality_contract_status"] == "pass"
    assert "trigger_state_unconfirmed" not in result["reason_codes"]
    assert result["decision_quality_contract_repair_codes"] == [
        "non_buy_invalid_reason_codes_removed"
    ]


def test_decision_quality_v2_7_repairs_adverse_distribution_reason_alias():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "NO_EDGE",
            "action": "DROP",
            "expected_upside_pct": 0.0,
            "expected_downside_pct": -1.2,
            "confidence": 80,
            "reason_codes": [
                "adverse_distribution_no_edge",
                "volume_confirmation_missing",
                "liquidity_adverse",
                "tape_adverse",
                "recovery_trigger_failed",
            ],
            "evidence": {
                "trend": "adverse",
                "liquidity": "adverse",
                "tape": "adverse",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "no_setup",
                "positive_edge": "none",
                "adverse_risk": "high",
                "trigger": "failed",
            },
        },
        exact_payload={
            "features": {"tick_aggressor_trusted_count": 10},
            "entry_candle_context": {
                "structure": {
                    "returns_pct": {"5": -0.7, "10": -1.3},
                    "slopes_pct_per_bar": {"5": -0.1, "10": -0.1},
                    "peak_drawdown_pct": -2.5,
                    "high_direction": "down",
                    "volume_ratio": 0.4,
                }
            },
        },
    )

    assert result["action"] == "DROP"
    assert result["decision_quality_contract_status"] == "pass"
    assert "distribution_adverse" in result["reason_codes"]
    assert "adverse_distribution_no_edge" not in result["reason_codes"]
    assert result["decision_quality_model_reason_codes"][0] == (
        "adverse_distribution_no_edge"
    )
    assert result["decision_quality_contract_repair_codes"] == [
        "non_buy_reason_code_aliases_normalized"
    ]


def test_decision_quality_v2_7_does_not_repair_buy_reason_alias():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "EDGE",
            "action": "BUY",
            "expected_upside_pct": 1.5,
            "expected_downside_pct": -0.8,
            "confidence": 82,
            "reason_codes": [
                "adverse_distribution_no_edge",
                "recovery_trigger_confirmed",
            ],
            "evidence": {
                "trend": "supportive",
                "liquidity": "supportive",
                "tape": "supportive",
                "risk": "low",
                "uncertainty": "low",
                "setup": "continuation",
                "positive_edge": "strong",
                "adverse_risk": "low",
                "trigger": "confirmed",
            },
        },
        exact_payload={},
    )

    assert result["action"] == "DROP"
    assert result["score"] == 0
    assert result["decision_quality_model_action"] == "BUY"
    assert result["decision_quality_contract_status"] == "semantic_rejected"
    assert "reason_codes_invalid" in result["decision_quality_contract_errors"]
    assert result["decision_quality_contract_repair_applied"] is False


def test_decision_quality_v2_7_keeps_blocking_wait_observation_only():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "EDGE",
            "action": "WAIT",
            "expected_upside_pct": 0.8,
            "expected_downside_pct": -0.8,
            "confidence": 75,
            "reason_codes": [
                "edge_positive",
                "recovery_trigger_required",
                "ask_wall_adverse",
            ],
            "evidence": {
                "trend": "supportive",
                "liquidity": "adverse",
                "tape": "mixed",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "pullback_recovery",
                "positive_edge": "moderate",
                "adverse_risk": "blocking",
                "trigger": "recovery_required",
            },
        },
        exact_payload={
            "features": {
                "tick_aggressor_trusted_count": 0,
                "tick_context_quality": "fresh_computed",
            }
        },
        prompt_version=DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION,
    )

    assert result["action"] == "WAIT"
    assert result["score"] == 68
    assert result["evidence"]["adverse_risk"] == "blocking"
    assert result["entry_probe_intent"] is False
    assert result["entry_probe_intent_status"] == "not_eligible"
    assert result["decision_quality_contract_status"] == "pass"
    assert result["decision_quality_contract_repair_applied"] is False


def test_decision_quality_v2_7_repairs_no_edge_trigger_reason_conflict_only():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "NO_EDGE",
            "action": "DROP",
            "expected_upside_pct": 0.6,
            "expected_downside_pct": -1.8,
            "confidence": 78,
            "reason_codes": [
                "edge_absent",
                "distribution_adverse",
                "volume_confirmation_missing",
                "liquidity_adverse",
                "tape_sample_insufficient",
                "recovery_trigger_required",
            ],
            "evidence": {
                "trend": "adverse",
                "liquidity": "adverse",
                "tape": "mixed",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "no_setup",
                "positive_edge": "none",
                "adverse_risk": "high",
                "trigger": "insufficient",
            },
        },
        exact_payload={},
        prompt_version=DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION,
    )

    assert result["action"] == "DROP"
    assert result["decision_quality_contract_status"] == "pass"
    assert result["entry_probe_intent"] is False
    assert result["reason_codes"] == [
        "edge_absent",
        "distribution_adverse",
        "volume_confirmation_missing",
        "liquidity_adverse",
        "tape_sample_insufficient",
    ]
    assert result["decision_quality_contract_repair_codes"] == [
        "non_buy_conflicting_trigger_reason_removed"
    ]
    assert result["decision_quality_model_reason_codes"][-1] == (
        "recovery_trigger_required"
    )


def test_decision_quality_v2_7_repairs_non_buy_neutral_tape_enum_only():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "NO_EDGE",
            "action": "DROP",
            "expected_upside_pct": 0.2,
            "expected_downside_pct": -1.0,
            "confidence": 78,
            "reason_codes": [
                "edge_absent",
                "distribution_adverse",
                "liquidity_adverse",
                "tape_adverse",
            ],
            "evidence": {
                "trend": "adverse",
                "liquidity": "adverse",
                "tape": "neutral",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "no_setup",
                "positive_edge": "none",
                "adverse_risk": "high",
                "trigger": "not_applicable",
            },
        },
        exact_payload={},
        prompt_version=DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION,
    )

    assert result["action"] == "DROP"
    assert result["decision_quality_contract_status"] == "pass"
    assert result["entry_probe_intent"] is False
    assert result["evidence"]["tape"] == "adverse"
    assert result["decision_quality_contract_repair_codes"] == [
        "non_buy_neutral_tape_enum_aligned"
    ]
    assert result["decision_quality_model_evidence"]["tape"] == "neutral"


def test_decision_quality_v2_7_repairs_no_edge_setup_without_structural_floor():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "NO_EDGE",
            "action": "DROP",
            "expected_upside_pct": 0.5,
            "expected_downside_pct": -0.8,
            "confidence": 70,
            "reason_codes": ["edge_absent", "recovery_trigger_required"],
            "evidence": {
                "trend": "mixed",
                "liquidity": "mixed",
                "tape": "mixed",
                "risk": "medium",
                "uncertainty": "medium",
                "setup": "pullback_recovery",
                "positive_edge": "none",
                "adverse_risk": "moderate",
                "trigger": "recovery_required",
            },
        },
        exact_payload={},
        prompt_version=DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION,
    )

    assert result["action"] == "DROP"
    assert result["evidence"]["setup"] == "no_setup"
    assert result["decision_quality_contract_status"] == "pass"
    assert result["decision_quality_contract_repair_codes"] == [
        "non_buy_no_edge_setup_aligned"
    ]
    assert result["decision_quality_model_evidence"]["setup"] == "pullback_recovery"


def test_decision_quality_v2_7_does_not_repair_invalid_buy_neutral_tape():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "EDGE",
            "action": "BUY",
            "expected_upside_pct": 1.5,
            "expected_downside_pct": -0.5,
            "confidence": 80,
            "reason_codes": ["edge_positive", "continuation_supported"],
            "evidence": {
                "trend": "supportive",
                "liquidity": "supportive",
                "tape": "neutral",
                "risk": "low",
                "uncertainty": "low",
                "setup": "continuation",
                "positive_edge": "strong",
                "adverse_risk": "low",
                "trigger": "confirmed",
            },
        },
        exact_payload={},
        prompt_version=DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION,
    )

    assert result["action"] == "DROP"
    assert result["score"] == 0
    assert result["decision_quality_contract_status"] == "semantic_rejected"
    assert result["decision_quality_contract_repair_applied"] is False
    assert "evidence_tape_invalid" in result["decision_quality_contract_errors"]


def test_decision_quality_v2_7_never_repairs_invalid_buy_reason_codes():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "EDGE",
            "action": "BUY",
            "expected_upside_pct": 1.5,
            "expected_downside_pct": -0.5,
            "confidence": 90,
            "reason_codes": ["edge_positive", "trigger=confirmed"],
            "evidence": {
                "trend": "supportive",
                "liquidity": "supportive",
                "tape": "supportive",
                "risk": "low",
                "uncertainty": "low",
                "setup": "continuation",
                "positive_edge": "strong",
                "adverse_risk": "low",
                "trigger": "confirmed",
            },
        },
        exact_payload={
            "features": {
                "tick_aggressor_trusted_count": 10,
                "tick_context_quality": "fresh_computed",
                "tick_accel_source": "computed_10ticks",
            }
        },
    )

    assert result["action"] == "DROP"
    assert result["score"] == 0
    assert result["decision_quality_contract_status"] == "semantic_rejected"
    assert result["decision_quality_contract_repair_applied"] is False
    assert result["decision_quality_contract_errors"] == ["reason_codes_invalid"]


def test_decision_quality_v2_7_does_not_hide_unknown_non_buy_reason_code():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "NO_EDGE",
            "action": "DROP",
            "expected_upside_pct": 0.4,
            "expected_downside_pct": -1.4,
            "confidence": 78,
            "reason_codes": [
                "edge_absent",
                "unreviewed_model_reason",
            ],
            "evidence": {
                "trend": "adverse",
                "liquidity": "adverse",
                "tape": "insufficient",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "no_setup",
                "positive_edge": "none",
                "adverse_risk": "blocking",
                "trigger": "insufficient",
            },
        },
        exact_payload={
            "features": {
                "tick_aggressor_trusted_count": 0,
                "tick_context_quality": "fresh_computed",
            }
        },
    )

    assert result["action"] == "DROP"
    assert result["score"] == 0
    assert result["decision_quality_contract_status"] == "semantic_rejected"
    assert result["decision_quality_contract_repair_applied"] is False
    assert result["decision_quality_contract_errors"] == ["reason_codes_invalid"]
    assert result["decision_quality_contract_invalid_reason_codes"] == [
        "unreviewed_model_reason"
    ]


def test_decision_quality_v2_7_repairs_observed_non_buy_scalar_enums():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "NO_EDGE",
            "action": "DROP",
            "expected_upside_pct": -0.2,
            "expected_downside_pct": -1.0,
            "confidence": 80,
            "reason_codes": [
                "edge_absent",
                "liquidity_adverse",
                "blocking_current_entry_risk",
            ],
            "evidence": {
                "trend": "adverse",
                "liquidity": "adverse",
                "tape": "adverse",
                "risk": "blocking",
                "uncertainty": "medium",
                "setup": "no_setup",
                "positive_edge": "none",
                "adverse_risk": "blocking",
                "trigger": "failed",
            },
        },
        exact_payload={},
    )

    assert result["action"] == "DROP"
    assert result["decision_quality_contract_status"] == "pass"
    assert result["expected_upside_pct"] == 0.0
    assert result["evidence"]["risk"] == "high"
    assert "adverse_risk_high" in result["reason_codes"]
    assert "blocking_current_entry_risk" not in result["reason_codes"]
    assert result["decision_quality_contract_repair_codes"] == [
        "non_buy_reason_code_aliases_normalized",
        "non_buy_upside_sign_normalized",
        "non_buy_blocking_risk_enum_aligned",
    ]
    assert result["decision_quality_contract_invalid_reason_codes"] == [
        "blocking_current_entry_risk"
    ]


def test_decision_quality_v2_7_repairs_structural_edge_floor_alias_for_wait():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "EDGE",
            "action": "WAIT",
            "expected_upside_pct": 0.9,
            "expected_downside_pct": -0.8,
            "confidence": 70,
            "reason_codes": [
                "structural_edge_floor",
                "recovery_trigger_required",
                "liquidity_adverse",
            ],
            "evidence": {
                "trend": "supportive",
                "liquidity": "adverse",
                "tape": "mixed",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "continuation",
                "positive_edge": "moderate",
                "adverse_risk": "high",
                "trigger": "recovery_required",
            },
        },
        exact_payload={},
    )

    assert result["action"] == "WAIT"
    assert result["decision_quality_contract_status"] == "pass"
    assert "structural_edge_without_trigger" in result["reason_codes"]
    assert "structural_edge_floor" not in result["reason_codes"]
    assert result["decision_quality_contract_repair_codes"] == [
        "non_buy_reason_code_aliases_normalized"
    ]
    assert result["decision_quality_contract_invalid_reason_codes"] == [
        "structural_edge_floor"
    ]


def test_decision_quality_v2_7_keeps_orderly_pullback_blocking_conflict_rejected():
    engine = _build_engine()
    exact_payload = {
        "features": {
            "curr_vs_micro_vwap_bp": -12.0,
            "curr_vs_ma5_bp": -8.0,
            "entry_order_flow_status": "mixed",
        },
        "entry_candle_context": {
            "structure": {
                "regime": "pullback",
                "alignment": "mixed",
                "returns_pct": {
                    "1": 0.1,
                    "3": 0.2,
                    "5": 0.4,
                    "10": 0.5,
                    "20": 0.6,
                    "60": -0.1,
                },
                "slopes_pct_per_bar": {
                    "5": 0.1,
                    "10": 0.1,
                    "20": -0.1,
                    "60": -0.1,
                },
            }
        },
    }
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "EDGE",
            "action": "WAIT",
            "expected_upside_pct": 0.9,
            "expected_downside_pct": -0.7,
            "confidence": 70,
            "reason_codes": [
                "edge_positive",
                "recovery_trigger_required",
                "liquidity_adverse",
            ],
            "evidence": {
                "trend": "mixed",
                "liquidity": "adverse",
                "tape": "adverse",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "pullback_recovery",
                "positive_edge": "moderate",
                "adverse_risk": "blocking",
                "trigger": "recovery_required",
            },
        },
        exact_payload=exact_payload,
    )

    assert result["action"] == "DROP"
    assert result["score"] == 0
    assert result["decision_quality_contract_status"] == "semantic_rejected"
    assert result["evidence"]["adverse_risk"] == "blocking"
    assert result["decision_quality_contract_repair_applied"] is False
    assert result["decision_quality_contract_errors"] == [
        "entry_orderly_pullback_recovery_misclassified"
    ]


def test_decision_quality_v2_7_completes_adverse_distribution_non_buy_reason():
    engine = _build_engine()
    exact_payload = {
        "entry_candle_context": {
            "structure": {
                "returns_pct": {
                    "5": -0.6,
                    "10": -1.2,
                    "20": -1.8,
                    "60": -2.4,
                },
                "slopes_pct_per_bar": {
                    "5": -0.1,
                    "10": -0.1,
                    "20": -0.1,
                    "60": -0.1,
                },
                "peak_drawdown_pct": -2.5,
                "high_direction": "down",
                "volume_ratio": 0.4,
            }
        }
    }
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "NO_EDGE",
            "action": "DROP",
            "expected_upside_pct": 0.0,
            "expected_downside_pct": -1.2,
            "confidence": 84,
            "reason_codes": [
                "edge_absent",
                "distribution_adverse",
                "liquidity_adverse",
                "tape_sample_insufficient",
                "overextension_chase_risk",
                "adverse_risk_high",
                "optional_source_missing",
                "forming_bar_ignored",
            ],
            "evidence": {
                "trend": "adverse",
                "liquidity": "adverse",
                "tape": "mixed",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "no_setup",
                "positive_edge": "none",
                "adverse_risk": "blocking",
                "trigger": "failed",
            },
        },
        exact_payload=exact_payload,
        prompt_version=DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION,
    )

    assert result["action"] == "DROP"
    assert result["decision_quality_contract_status"] == "pass"
    assert "volume_confirmation_missing" in result["reason_codes"]
    assert "edge_absent" in result["reason_codes"]
    assert "forming_bar_ignored" not in result["reason_codes"]
    assert result["decision_quality_contract_repair_applied"] is True
    assert result["decision_quality_contract_repair_codes"] == [
        "non_buy_adverse_distribution_reason_completed"
    ]
    assert result["decision_quality_contract_original_errors"] == [
        "entry_adverse_distribution_misclassified"
    ]
    assert (
        result["decision_quality_live_adapter"]
        == "decision_quality_v2_7_probe_entry_v8"
    )


def test_decision_quality_v2_7_removes_only_redundant_tape_mixed_reason():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "NO_EDGE",
            "action": "DROP",
            "expected_upside_pct": 0.4,
            "expected_downside_pct": -0.9,
            "confidence": 75,
            "reason_codes": [
                "edge_absent",
                "liquidity_adverse",
                "tape_mixed",
            ],
            "evidence": {
                "trend": "adverse",
                "liquidity": "adverse",
                "tape": "mixed",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "no_setup",
                "positive_edge": "none",
                "adverse_risk": "blocking",
                "trigger": "not_applicable",
            },
        },
        exact_payload={},
    )

    assert result["action"] == "DROP"
    assert result["decision_quality_contract_status"] == "pass"
    assert result["reason_codes"] == ["edge_absent", "liquidity_adverse"]
    assert result["decision_quality_contract_repair_codes"] == [
        "non_buy_redundant_tape_mixed_reason_removed"
    ]
    assert result["decision_quality_contract_invalid_reason_codes"] == ["tape_mixed"]


def test_decision_quality_v2_7_repairs_non_buy_reason_code_conflict():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "NO_EDGE",
            "action": "DROP",
            "expected_upside_pct": 0.0,
            "expected_downside_pct": -0.6,
            "confidence": 72,
            "reason_codes": [
                "edge_absent",
                "no_positive_edge",
                "volume_confirmation_missing",
            ],
            "evidence": {
                "trend": "adverse",
                "liquidity": "mixed",
                "tape": "mixed",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "no_setup",
                "positive_edge": "none",
                "adverse_risk": "high",
                "trigger": "failed",
            },
        },
        exact_payload={},
        prompt_version=DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION,
    )

    assert result["action"] == "DROP"
    assert result["decision_quality_contract_status"] == "pass"
    assert result["reason_codes"] == [
        "no_positive_edge",
        "volume_confirmation_missing",
    ]
    assert result["decision_quality_contract_repair_applied"] is True
    assert result["decision_quality_contract_repair_codes"] == [
        "non_buy_reason_code_conflicts_resolved"
    ]
    assert result["decision_quality_contract_original_errors"] == [
        "reason_codes_conflict"
    ]
    assert (
        result["decision_quality_live_adapter"]
        == "decision_quality_v2_7_probe_entry_v8"
    )


def test_decision_quality_v2_7_repairs_directional_reason_conflicts_from_evidence():
    engine = _build_engine()
    model_reason_codes = [
        "edge_absent",
        "distribution_adverse",
        "liquidity_adverse",
        "liquidity_supportive",
        "tape_supportive",
        "tape_adverse",
    ]
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "NO_EDGE",
            "action": "DROP",
            "expected_upside_pct": 0.0,
            "expected_downside_pct": -0.8,
            "confidence": 76,
            "reason_codes": model_reason_codes,
            "evidence": {
                "trend": "adverse",
                "liquidity": "adverse",
                "tape": "mixed",
                "risk": "high",
                "uncertainty": "medium",
                "setup": "no_setup",
                "positive_edge": "none",
                "adverse_risk": "high",
                "trigger": "not_applicable",
            },
        },
        exact_payload={},
        prompt_version=DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION,
    )

    assert result["action"] == "DROP"
    assert result["decision_quality_contract_status"] == "pass"
    assert result["reason_codes"] == [
        "edge_absent",
        "distribution_adverse",
        "liquidity_adverse",
    ]
    assert result["decision_quality_model_reason_codes"] == model_reason_codes
    assert result["decision_quality_contract_repair_applied"] is True
    assert result["decision_quality_contract_repair_codes"] == [
        "non_buy_reason_code_conflicts_resolved"
    ]
    assert result["decision_quality_contract_original_errors"] == [
        "reason_codes_conflict"
    ]


def test_decision_quality_v2_7_repairs_stage_wait_alias_without_buy_authority():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "EDGE",
            "action": "STAGE_WAIT",
            "expected_upside_pct": 1.0,
            "expected_downside_pct": -0.9,
            "confidence": 62,
            "reason_codes": [
                "edge_positive",
                "structural_trend_supportive",
                "recovery_trigger_required",
            ],
            "evidence": {
                "trend": "supportive",
                "liquidity": "mixed",
                "tape": "mixed",
                "risk": "medium",
                "uncertainty": "medium",
                "setup": "pullback_recovery",
                "positive_edge": "weak",
                "adverse_risk": "high",
                "trigger": "recovery_required",
            },
        },
        exact_payload={},
        prompt_version=DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION,
    )

    assert result["action"] == "WAIT"
    assert result["score"] == 65
    assert result["decision_quality_model_action"] == "STAGE_WAIT"
    assert result["decision_quality_contract_status"] == "pass"
    assert result["evidence"]["positive_edge"] == "moderate"
    assert result["decision_quality_contract_repair_applied"] is True
    assert result["decision_quality_contract_repair_codes"] == [
        "non_buy_stage_wait_action_alias_normalized",
        "non_buy_stage_wait_edge_strength_aligned",
    ]
    assert result["decision_quality_live_adapter"] == (
        "decision_quality_v2_7_probe_entry_v8"
    )


def test_decision_quality_v2_7_does_not_repair_buy_reason_code_conflict():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "EDGE",
            "action": "BUY",
            "expected_upside_pct": 1.5,
            "expected_downside_pct": -0.8,
            "confidence": 80,
            "reason_codes": [
                "edge_positive",
                "edge_absent",
                "recovery_trigger_confirmed",
            ],
            "evidence": {
                "trend": "supportive",
                "liquidity": "supportive",
                "tape": "supportive",
                "risk": "low",
                "uncertainty": "low",
                "setup": "continuation",
                "positive_edge": "strong",
                "adverse_risk": "low",
                "trigger": "confirmed",
            },
        },
        exact_payload={},
    )

    assert result["action"] == "DROP"
    assert result["score"] == 0
    assert result["decision_quality_contract_status"] == "semantic_rejected"
    assert "reason_codes_conflict" in result["decision_quality_contract_errors"]
    assert result["decision_quality_contract_repair_applied"] is False


def test_decision_quality_v2_7_does_not_guess_ambiguous_non_buy_conflict():
    engine = _build_engine()
    result = engine._normalize_decision_quality_entry_result(
        {
            "edge_state": "INSUFFICIENT_DATA",
            "action": "WAIT",
            "expected_upside_pct": None,
            "expected_downside_pct": None,
            "confidence": 35,
            "reason_codes": [
                "risk_reward_favorable",
                "risk_reward_unfavorable",
                "insufficient_core_data",
            ],
            "evidence": {
                "trend": "insufficient",
                "liquidity": "insufficient",
                "tape": "insufficient",
                "risk": "insufficient",
                "uncertainty": "high",
                "setup": "insufficient",
                "positive_edge": "insufficient",
                "adverse_risk": "insufficient",
                "trigger": "insufficient",
            },
        },
        exact_payload={},
        prompt_version=DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION,
    )

    assert result["action"] == "DROP"
    assert result["score"] == 0
    assert result["decision_quality_contract_status"] == "semantic_rejected"
    assert result["decision_quality_contract_errors"] == ["reason_codes_conflict"]
    assert result["decision_quality_contract_repair_applied"] is False


def test_decision_quality_v2_7_requires_exact_preflight_even_if_global_gate_off(
    monkeypatch,
):
    engine = _build_engine()
    called = False
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_ANALYZE_TARGET_PROMPT_VERSION="decision_quality_v2_7",
        ),
    )

    def _unexpected_call(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(engine, "_call_openai_safe", _unexpected_call)
    result = engine.analyze_target(
        "테스트",
        _sample_ws_data(),
        _sample_ticks(),
        _sample_candles(),
        strategy="SCALPING",
        prompt_profile="watching",
    )

    assert called is False
    assert result["action"] == "DROP"
    assert result["score"] == 0
    assert result["ai_result_source"] == "input_preflight_blocked"
    assert result["ai_prompt_version"] == DECISION_QUALITY_DETAILED_PROMPT_VERSION
    assert result["ai_input_preflight_status"] == "blocked"
    assert result["ai_input_preflight_blockers"] == ["ai_market_snapshot_missing"]
    assert result["ai_semantic_evaluation_state"] == "INSUFFICIENT_DATA"
    assert result["decision_evaluation_status"] == (
        "not_evaluated_provider_or_preflight"
    )
    assert result["runtime_fail_closed_action"] == "DROP"
    assert result["ai_decision_outcome_eligible"] is False


def test_hot_entry_keeps_observe_only_snapshot_out_of_model_but_in_trace_metadata(
    monkeypatch,
):
    engine = _build_engine()
    captured = {}
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_ANALYZE_TARGET_HOT_INPUT_ENABLED=True,
            OPENAI_ENTRY_SCREEN_V2_INPUT_ENABLED=False,
            OPENAI_SCALPING_COMPACT_INPUT_ENABLED=True,
        ),
    )

    def _fake_call(_prompt, user_input, **kwargs):
        captured["payload"] = json.loads(user_input)
        captured["metadata"] = kwargs["metadata_extra"]
        return {"action": "WAIT", "score": 60, "reason": "mixed entry features"}

    monkeypatch.setattr(engine, "_call_openai_safe", _fake_call)
    candle_context = {
        "schema": "entry_candle_context_v1",
        "enabled": False,
        "venue": "NXT",
        "session": "nxt_aftermarket",
        "ws_route": "nxt_only",
        "ai_market_snapshot_v1": {
            "schema": "ai_market_snapshot_v1",
            "snapshot_id": "snapshot-nxt-1",
            "stock_code": "005930",
            "effective_venue": "NXT",
            "session_bucket": "nxt_aftermarket",
            "broker_route": "SOR",
            "market_data_route": "nxt_only",
        },
    }

    engine.analyze_target(
        "테스트",
        _sample_ws_data(),
        _sample_ticks(),
        _sample_candles(),
        strategy="SCALPING",
        prompt_profile="watching",
        candle_context=candle_context,
    )

    assert "entry_candle_context" not in captured["payload"]
    assert "ai_market_snapshot_v1" not in captured["payload"]
    assert captured["metadata"]["effective_venue"] == "NXT"
    assert captured["metadata"]["session_bucket"] == "nxt_aftermarket"
    assert captured["metadata"]["broker_route"] == "SOR"


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

    payload = engine._format_market_data(
        _sample_ws_data(), heuristic_ticks, _sample_candles()
    )

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


def test_openai_request_metadata_preserves_exact_market_route_join_keys():
    engine = _build_engine()

    metadata_extra = {
        **{f"extra_{idx:02d}": str(idx) for idx in range(20)},
        "session_bucket": "krx_regular",
        "broker_route": "SOR",
        "market_data_route": "krx_nxt_integrated",
        "snapshot_id": "aims-exact-route",
    }
    request = engine._build_openai_response_request(
        prompt="PROMPT",
        user_input="payload",
        require_json=True,
        context_name="metadata-route-trim",
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
    assert metadata["session_bucket"] == "krx_regular"
    assert metadata["broker_route"] == "SOR"
    assert metadata["market_data_route"] == "krx_nxt_integrated"
    assert metadata["snapshot_id"] == "aims-exact-route"
    assert "extra_19" not in metadata


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

    assert all(
        len(key) <= openai_module.OPENAI_METADATA_KEY_MAX_LENGTH for key in metadata
    )
    normalized_long_keys = [
        key
        for key in metadata
        if key.startswith("early_accel_strong_bundle_recheck_price_delta_since_")
    ]
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
            return OpenAITransportResult(
                payload={"worker_id": self.worker_id},
                transport_mode="responses_ws",
                ws_used=True,
            )

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
    engine.client = SimpleNamespace(
        responses=SimpleNamespace(create=lambda **kwargs: None)
    )
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
        lambda request: (_ for _ in ()).throw(TimeoutError("ws timeout")),
    )
    monkeypatch.setattr(
        openai_module, "log_info", lambda msg, **kwargs: log_info_calls.append(msg)
    )
    monkeypatch.setattr(
        openai_module, "log_error", lambda msg, **kwargs: log_error_calls.append(msg)
    )
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
    assert meta["openai_http_fallback_budget_ms"] > 0
    assert meta["openai_original_timeout_ms"] > 0
    assert meta["openai_ws_elapsed_before_fallback_ms"] >= 0
    assert meta["openai_http_lock_wait_ms"] >= 0
    assert any("[OpenAI WS fallback]" in msg for msg in log_info_calls)
    assert not any("[OpenAI WS fallback]" in msg for msg in log_error_calls)


def test_openai_http_timed_out_text_is_retryable(monkeypatch):
    engine = _build_engine()
    calls = []

    def _create(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise Exception("Request timed out.")
        return SimpleNamespace(
            output_text='{"action":"WAIT","score":61,"reason":"retry success"}'
        )

    engine.client = SimpleNamespace(responses=SimpleNamespace(create=_create))
    monkeypatch.setattr(openai_module.time, "sleep", lambda seconds: None)

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="test_http_timeout_text",
        schema_name="entry_v1",
        endpoint_name="analyze_target",
        symbol="005930",
    )
    meta = engine._consume_last_transport_meta()

    assert result["action"] == "WAIT"
    assert len(calls) == 2
    assert meta["openai_http_attempt_count"] == 2
    assert meta["openai_http_provider_ms"] >= 0
    assert meta["openai_http_provider_total_ms"] >= meta["openai_http_provider_ms"]
    assert meta["openai_http_lock_wait_ms"] >= 0


def test_openai_http_retry_sleep_respects_remaining_timeout(monkeypatch):
    engine = _build_engine()
    sleeps = []

    def _create(**kwargs):
        raise Exception("503 unavailable")

    engine.client = SimpleNamespace(responses=SimpleNamespace(create=_create))
    monkeypatch.setattr(
        openai_module.time, "sleep", lambda seconds: sleeps.append(seconds)
    )
    request = OpenAIResponseRequest(
        prompt="PROMPT",
        user_input="payload",
        require_json=True,
        context_name="test_retry_budget",
        model_name="gpt-fast",
        temperature=0.0,
        schema_name="entry_v1",
        endpoint_name="analyze_target",
        request_id="req-retry-budget",
        symbol="005930",
        cache_key="-",
        submitted_at_perf=openai_module.time.perf_counter(),
        timeout_ms=120,
    )

    try:
        engine._call_openai_responses_http(request)
    except RuntimeError as exc:
        assert "모든 OpenAI API 키 사용 불가" in str(exc)
    else:
        raise AssertionError("expected retry exhaustion")

    assert sleeps
    assert max(sleeps) <= 0.08


def test_openai_http_timeout_budget_exhaustion_does_not_rotate_key(monkeypatch):
    engine = _build_engine()
    rotate_calls = []
    log_info_calls = []
    log_error_calls = []

    def _create(**kwargs):
        raise Exception("Request timed out.")

    engine.client = SimpleNamespace(responses=SimpleNamespace(create=_create))
    engine._rotate_client = lambda: rotate_calls.append("rotated")
    monkeypatch.setattr(
        openai_module, "log_info", lambda msg, **kwargs: log_info_calls.append(msg)
    )
    monkeypatch.setattr(
        openai_module, "log_error", lambda msg, **kwargs: log_error_calls.append(msg)
    )
    request = OpenAIResponseRequest(
        prompt="PROMPT",
        user_input="payload",
        require_json=True,
        context_name="test_timeout_budget",
        model_name="gpt-fast",
        temperature=0.0,
        schema_name="entry_v1",
        endpoint_name="analyze_target",
        request_id="req-timeout-budget-exhausted",
        symbol="005930",
        cache_key="-",
        submitted_at_perf=openai_module.time.perf_counter() - 1.0,
        timeout_ms=100,
    )

    try:
        engine._call_openai_responses_http(request)
    except OpenAIResponsesHTTPError as exc:
        assert "timeout budget exhausted" in str(exc)
        assert exc.timing_meta["openai_http_timeout_budget_exhausted"] is True
        assert exc.timing_meta["openai_http_sdk_max_retries"] == OPENAI_SDK_MAX_RETRIES
    else:
        raise AssertionError("expected timeout budget exhaustion")

    assert not rotate_calls
    assert any("timeout budget exhausted" in msg for msg in log_info_calls)
    assert not any("AI 고갈" in msg for msg in log_error_calls)


def test_openai_http_enforces_wall_clock_deadline_when_sdk_call_runs_late():
    engine = _build_engine()

    def _create(**kwargs):
        openai_module.time.sleep(0.15)
        return SimpleNamespace(output_text='{"action":"WAIT"}', usage=None)

    engine.client = SimpleNamespace(responses=SimpleNamespace(create=_create))
    request = OpenAIResponseRequest(
        prompt="PROMPT",
        user_input="payload",
        require_json=True,
        context_name="test_wall_deadline",
        model_name="gpt-fast",
        temperature=0.0,
        schema_name="entry_v1",
        endpoint_name="analyze_target",
        request_id="req-wall-deadline",
        symbol="005930",
        cache_key="-",
        submitted_at_perf=openai_module.time.perf_counter(),
        timeout_ms=50,
    )

    started = openai_module.time.perf_counter()
    try:
        engine._call_openai_responses_http(request)
    except OpenAIResponsesHTTPError as exc:
        elapsed = openai_module.time.perf_counter() - started
        assert elapsed < 0.13
        assert exc.timing_meta["openai_http_timeout_budget_exhausted"] is True
        assert exc.timing_meta["openai_http_wall_deadline_enforced"] is True
        assert exc.timing_meta["openai_http_wall_deadline_exceeded"] is True
        assert exc.timing_meta["openai_http_provider_future_cancelled"] is False
        assert exc.timing_meta["openai_http_deadline_overshoot_ms"] < 30
    else:
        raise AssertionError("expected wall-clock deadline exhaustion")
    engine._http_deadline_executor.shutdown(wait=True)


def test_openai_http_wall_deadline_cancels_queued_duplicate_provider_call():
    engine = _build_engine()
    provider_calls = []

    def _create(**kwargs):
        provider_calls.append(kwargs)
        openai_module.time.sleep(0.15)
        return SimpleNamespace(output_text='{"action":"WAIT"}', usage=None)

    engine.client = SimpleNamespace(responses=SimpleNamespace(create=_create))

    def _request(request_id: str) -> OpenAIResponseRequest:
        return OpenAIResponseRequest(
            prompt="PROMPT",
            user_input="payload",
            require_json=True,
            context_name="test_wall_deadline_queue",
            model_name="gpt-fast",
            temperature=0.0,
            schema_name="entry_v1",
            endpoint_name="analyze_target",
            request_id=request_id,
            symbol="005930",
            cache_key="-",
            submitted_at_perf=openai_module.time.perf_counter(),
            timeout_ms=30,
        )

    with pytest.raises(OpenAIResponsesHTTPError) as first_error:
        engine._call_openai_responses_http(_request("req-wall-deadline-running"))
    assert (
        first_error.value.timing_meta["openai_http_provider_future_cancelled"]
        is False
    )

    with pytest.raises(OpenAIResponsesHTTPError) as queued_error:
        engine._call_openai_responses_http(_request("req-wall-deadline-queued"))
    assert (
        queued_error.value.timing_meta["openai_http_provider_future_cancelled"]
        is True
    )

    engine._http_deadline_executor.shutdown(wait=True)
    assert len(provider_calls) == 1


def test_openai_ws_attempt_timeout_leaves_http_fallback_budget(monkeypatch):
    engine = _build_engine()
    captured = []

    class _StubPool:
        def submit(self, request, *, use_schema_registry):
            captured.append(request)
            raise TimeoutError("ws attempt timeout")

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_RESPONSES_WS_TIMEOUT_MS=15000,
            OPENAI_RESPONSES_WS_HTTP_FALLBACK_RESERVE_MS=1500,
        ),
    )
    engine._responses_ws_pool = _StubPool()
    request = OpenAIResponseRequest(
        prompt="PROMPT",
        user_input="payload",
        require_json=True,
        context_name="test",
        model_name="gpt-fast",
        temperature=0.0,
        schema_name="entry_v1",
        endpoint_name="analyze_target",
        request_id="req-timeout-budget",
        symbol="005930",
        cache_key="-",
        submitted_at_perf=openai_module.time.perf_counter(),
        timeout_ms=3000,
    )

    try:
        engine._call_openai_responses_ws(request)
    except TimeoutError:
        pass
    else:
        raise AssertionError("expected ws attempt timeout")

    assert captured
    assert captured[0].request_id == request.request_id
    assert 1400 <= captured[0].timeout_ms <= 1600
    assert captured[0].timeout_ms < request.timeout_ms
    assert 1400 <= int(captured[0].metadata["ws_http_fallback_reserve_ms"]) <= 1500


def test_openai_ws_attempt_timeout_can_prefer_http_fallback_budget(monkeypatch):
    engine = _build_engine()
    captured = []

    class _StubPool:
        def submit(self, request, *, use_schema_registry):
            captured.append(request)
            raise TimeoutError("ws attempt timeout")

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_RESPONSES_WS_TIMEOUT_MS=15000,
            OPENAI_RESPONSES_WS_HTTP_FALLBACK_RESERVE_MS=2000,
        ),
    )
    engine._responses_ws_pool = _StubPool()
    request = OpenAIResponseRequest(
        prompt="PROMPT",
        user_input="payload",
        require_json=True,
        context_name="test",
        model_name="gpt-fast",
        temperature=0.0,
        schema_name="entry_v1",
        endpoint_name="analyze_target",
        request_id="req-http-budget-preferred",
        symbol="005930",
        cache_key="-",
        submitted_at_perf=openai_module.time.perf_counter(),
        timeout_ms=3000,
    )

    try:
        engine._call_openai_responses_ws(request)
    except TimeoutError:
        pass
    else:
        raise AssertionError("expected ws attempt timeout")

    assert captured
    assert 900 <= captured[0].timeout_ms <= 1100
    assert 1900 <= int(captured[0].metadata["ws_http_fallback_reserve_ms"]) <= 2000


def test_openai_ws_http_fallback_keeps_executable_timeout_after_ws_elapsed(monkeypatch):
    engine = _build_engine()
    engine.client = SimpleNamespace(
        responses=SimpleNamespace(create=lambda **kwargs: None)
    )
    captured_http = []

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_TRANSPORT_MODE="responses_ws",
            OPENAI_RESPONSES_WS_ENABLED=True,
            OPENAI_ANALYZE_TARGET_TIMEOUT_MS=3000,
            OPENAI_RESPONSES_WS_TIMEOUT_MS=15000,
            OPENAI_RESPONSES_WS_HTTP_FALLBACK_RESERVE_MS=1500,
        ),
    )

    def _fake_ws(request):
        request.submitted_at_perf = openai_module.time.perf_counter() - 1.55
        raise TimeoutError("ws timeout")

    def _fake_http(request):
        captured_http.append(request)
        return OpenAITransportResult(
            payload={"action": "WAIT", "score": 62, "reason": "http fallback"},
            transport_mode="http",
            ws_used=False,
            ws_http_fallback=True,
            roundtrip_ms=15,
        )

    monkeypatch.setattr(engine, "_call_openai_responses_ws", _fake_ws)
    monkeypatch.setattr(engine, "_call_openai_responses_http", _fake_http)

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

    assert result["action"] == "WAIT"
    assert captured_http
    assert 1200 <= captured_http[0].timeout_ms <= 1600
    meta = engine._consume_last_transport_meta()
    assert 1200 <= meta["openai_http_fallback_budget_ms"] <= 1600
    assert meta["openai_ws_elapsed_before_fallback_ms"] >= 1500
    assert meta["openai_http_lock_wait_ms"] >= 0


def test_openai_ws_http_fallback_timeout_fails_closed_for_entry(monkeypatch):
    engine = _build_engine()
    engine.client = SimpleNamespace(
        responses=SimpleNamespace(create=lambda **kwargs: None)
    )
    log_info_calls = []
    log_error_calls = []

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_TRANSPORT_MODE="responses_ws",
            OPENAI_RESPONSES_WS_ENABLED=True,
            OPENAI_ANALYZE_TARGET_TIMEOUT_MS=3000,
        ),
    )
    monkeypatch.setattr(
        engine,
        "_call_openai_responses_ws",
        lambda request: (_ for _ in ()).throw(TimeoutError("ws timeout")),
    )
    monkeypatch.setattr(
        engine,
        "_call_openai_responses_http",
        lambda request: (_ for _ in ()).throw(
            OpenAIResponsesHTTPError(
                "🚨 [AI 고갈] 모든 OpenAI API 키 사용 불가. 마지막 에러: request timed out.",
                timing_meta={
                    "openai_http_provider_ms": 1400,
                    "openai_http_provider_total_ms": 1400,
                    "openai_http_attempt_count": 1,
                    "openai_http_error_type": "TimeoutError",
                },
            )
        ),
    )
    monkeypatch.setattr(
        openai_module, "log_info", lambda msg, **kwargs: log_info_calls.append(msg)
    )
    monkeypatch.setattr(
        openai_module, "log_error", lambda msg, **kwargs: log_error_calls.append(msg)
    )

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="test_entry",
        schema_name="entry_v1",
        endpoint_name="analyze_target",
        symbol="005930",
    )
    meta = engine._consume_last_transport_meta()

    assert result["action"] == "DROP"
    assert result["score"] == 0
    assert result["openai_transport_fail_closed"] is True
    assert meta["openai_ws_http_fallback"] is True
    assert meta["openai_ws_http_fallback_fail_closed"] is True
    assert meta["openai_ws_http_fallback_error_type"] == "OpenAIResponsesHTTPError"
    assert meta["openai_http_provider_ms"] == 1400
    assert meta["openai_http_provider_total_ms"] == 1400
    assert meta["openai_http_attempt_count"] == 1
    assert meta["openai_http_error_type"] == "TimeoutError"
    assert any("HTTP fallback fail-closed" in msg for msg in log_info_calls)
    assert not log_error_calls


def test_openai_ws_http_fallback_timeout_fails_closed_for_holding(monkeypatch):
    engine = _build_engine()
    engine.client = SimpleNamespace(
        responses=SimpleNamespace(create=lambda **kwargs: None)
    )

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_TRANSPORT_MODE="responses_ws",
            OPENAI_RESPONSES_WS_ENABLED=True,
            OPENAI_ANALYZE_TARGET_TIMEOUT_MS=3000,
        ),
    )
    monkeypatch.setattr(
        engine,
        "_call_openai_responses_ws",
        lambda request: (_ for _ in ()).throw(TimeoutError("ws timeout")),
    )
    monkeypatch.setattr(
        engine,
        "_call_openai_responses_http",
        lambda request: (_ for _ in ()).throw(
            RuntimeError("OpenAI Responses HTTP 응답/파싱 실패: Request timed out.")
        ),
    )

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="test_holding",
        schema_name="holding_exit_v1",
        endpoint_name="analyze_target",
        symbol="005930",
    )
    meta = engine._consume_last_transport_meta()

    assert result["action"] == "HOLD"
    assert result["score"] == 0
    assert result["openai_transport_fail_closed"] is True
    assert meta["openai_ws_http_fallback"] is True
    assert meta["openai_ws_http_fallback_fail_closed"] is True


def test_openai_ws_connection_closed_ok_fallback_logs_info_not_error(monkeypatch):
    engine = _build_engine()
    engine.client = SimpleNamespace(
        responses=SimpleNamespace(create=lambda **kwargs: None)
    )
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
    monkeypatch.setattr(
        openai_module, "log_info", lambda msg, **kwargs: log_info_calls.append(msg)
    )
    monkeypatch.setattr(
        openai_module, "log_error", lambda msg, **kwargs: log_error_calls.append(msg)
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

    assert result["action"] == "WAIT"
    assert meta["openai_ws_http_fallback"] is True
    assert meta["openai_ws_error_type"] == "ConnectionClosedOK"
    assert any("[OpenAI WS fallback]" in msg for msg in log_info_calls)
    assert not any("[OpenAI WS fallback]" in msg for msg in log_error_calls)


def test_openai_ws_missing_close_frame_fallback_logs_info_not_error(monkeypatch):
    engine = _build_engine()
    engine.client = SimpleNamespace(
        responses=SimpleNamespace(create=lambda **kwargs: None)
    )
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
        lambda request: (_ for _ in ()).throw(
            RuntimeError("no close frame received or sent")
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
    monkeypatch.setattr(
        openai_module, "log_info", lambda msg, **kwargs: log_info_calls.append(msg)
    )
    monkeypatch.setattr(
        openai_module, "log_error", lambda msg, **kwargs: log_error_calls.append(msg)
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
        return SimpleNamespace(
            output_text='{"action":"WAIT","score":50,"reason":"numeric retry"}'
        )

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
        lambda request: (_ for _ in ()).throw(
            OpenAIWSRequestIdMismatchError("request_id mismatch")
        ),
    )

    def _unexpected_http_fallback(request):
        raise AssertionError(
            "request_id mismatch must not be converted to HTTP fallback"
        )

    monkeypatch.setattr(
        engine, "_call_openai_responses_http", _unexpected_http_fallback
    )

    result = engine.analyze_target(
        "테스트",
        _sample_ws_data(),
        _sample_ticks(),
        _sample_candles(),
        strategy="SCALPING",
        prompt_profile="holding",
    )

    assert result["action"] == "WAIT"
    assert result["score"] == 50
    assert result["ai_parse_fail"] is True
    assert result["openai_transport_mode"] == "responses_ws"
    assert result["openai_ws_used"] is True
    assert result["openai_ws_http_fallback"] is False
    assert result["openai_ws_error_type"] == "OpenAIWSRequestIdMismatchError"


def test_transport_trace_copy_preserves_generic_provider_response_id():
    target = {}

    openai_module.GPTSniperEngine._copy_ai_transport_trace_metadata(
        target,
        {
            "provider": "bedrock",
            "provider_response_id": "aws-request-1",
            "bedrock_response_id": "aws-request-1",
        },
    )

    assert target["provider"] == "bedrock"
    assert target["provider_response_id"] == "aws-request-1"
    assert target["bedrock_response_id"] == "aws-request-1"
