import threading
from dataclasses import replace
from types import SimpleNamespace

from src.engine import ai_engine as ai_engine_module
from src.engine import ai_engine_deepseek as ai_engine_deepseek_module
from src.engine.ai_engine import GeminiSniperEngine, GEMINI_RESPONSE_SCHEMA_REGISTRY, SCALPING_HOLDING_FLOW_SYSTEM_PROMPT
from src.engine.ai_engine_deepseek import DeepSeekSniperEngine


def _build_gemini_call_engine():
    engine = GeminiSniperEngine.__new__(GeminiSniperEngine)
    engine.current_model_name = "tier1-model"
    engine.api_keys = ["key-a", "key-b"]
    engine.current_key = "key-a"
    engine.current_api_key_index = 0
    engine._rotate_client = lambda: None
    return engine


def _build_deepseek_call_engine():
    engine = DeepSeekSniperEngine.__new__(DeepSeekSniperEngine)
    engine.lock = threading.Lock()
    engine.api_call_lock = threading.Lock()
    engine.current_model_name = "tier1-model"
    engine.model_tier2_balanced = "tier2-model"
    engine.model_tier3_deep = "tier3-model"
    engine.api_keys = ["deepseek-key-a", "deepseek-key-b"]
    engine.current_key = "deepseek-key-a"
    engine.current_api_key_index = 0
    engine.ai_disabled = False
    engine.consecutive_failures = 0
    engine.last_call_time = 0.0
    engine._annotate_analysis_result = lambda result, **meta: {**dict(result), **{
        "ai_parse_ok": bool(meta.get("parse_ok", False)),
        "ai_parse_fail": bool(meta.get("parse_fail", False)),
    }}

    def _rotate():
        engine.current_key = (
            "deepseek-key-b" if engine.current_key == "deepseek-key-a" else "deepseek-key-a"
        )

    engine._rotate_client = _rotate
    return engine


def test_call_gemini_safe_keeps_legacy_contents_when_system_instruction_flag_off(monkeypatch):
    engine = _build_gemini_call_engine()
    captured = {}

    def _fake_generate_content(*, model, contents, config):
        captured["model"] = model
        captured["contents"] = contents
        captured["config"] = config
        return SimpleNamespace(text='{"action":"BUY","score":88,"reason":"strong"}')

    engine.client = SimpleNamespace(
        models=SimpleNamespace(generate_content=_fake_generate_content)
    )

    monkeypatch.setattr(
        ai_engine_module,
        "TRADING_RULES",
        replace(
            ai_engine_module.TRADING_RULES,
            GEMINI_SYSTEM_INSTRUCTION_JSON_ENABLED=False,
            GEMINI_JSON_DETERMINISTIC_CONFIG_ENABLED=False,
        ),
    )

    result = GeminiSniperEngine._call_gemini_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="test",
    )

    assert result["action"] == "BUY"
    assert captured["contents"] == ["PROMPT", "payload"]
    assert captured["config"].response_mime_type == "application/json"
    assert captured["config"].system_instruction is None


def test_call_gemini_safe_uses_system_instruction_and_deterministic_json_config(monkeypatch):
    engine = _build_gemini_call_engine()
    captured = {}

    def _fake_generate_content(*, model, contents, config):
        captured["model"] = model
        captured["contents"] = contents
        captured["config"] = config
        return SimpleNamespace(text='{"action":"BUY","score":91,"reason":"deterministic"}')

    engine.client = SimpleNamespace(
        models=SimpleNamespace(generate_content=_fake_generate_content)
    )

    monkeypatch.setattr(
        ai_engine_module,
        "TRADING_RULES",
        replace(
            ai_engine_module.TRADING_RULES,
            GEMINI_SYSTEM_INSTRUCTION_JSON_ENABLED=True,
            GEMINI_JSON_DETERMINISTIC_CONFIG_ENABLED=True,
            GEMINI_JSON_TEMPERATURE=0.0,
            GEMINI_JSON_TOP_P=0.2,
            GEMINI_JSON_TOP_K=2,
        ),
    )

    result = GeminiSniperEngine._call_gemini_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="test",
        model_override="tier2-model",
    )

    assert result["action"] == "BUY"
    assert captured["model"] == "tier2-model"
    assert captured["contents"] == ["payload"]
    assert captured["config"].system_instruction == "PROMPT"
    assert captured["config"].temperature == 0.0
    assert captured["config"].top_p == 0.2
    assert captured["config"].top_k == 2


def test_call_gemini_safe_applies_endpoint_response_schema_when_flag_enabled(monkeypatch):
    engine = _build_gemini_call_engine()
    captured = {}

    def _fake_generate_content(*, model, contents, config):
        captured["config"] = config
        return SimpleNamespace(
            text='{"decision":"BUY","confidence":88,"order_type":"LIMIT_TOP","position_size_ratio":0.1,"invalidation_price":1000,"reasons":["ok"],"risks":[]}'
        )

    engine.client = SimpleNamespace(
        models=SimpleNamespace(generate_content=_fake_generate_content)
    )

    monkeypatch.setattr(
        ai_engine_module,
        "TRADING_RULES",
        replace(
            ai_engine_module.TRADING_RULES,
            GEMINI_RESPONSE_SCHEMA_REGISTRY_ENABLED=True,
        ),
    )

    result = GeminiSniperEngine._call_gemini_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="test",
        schema_name="condition_entry_v1",
    )

    assert result["decision"] == "BUY"
    assert captured["config"].response_schema == GEMINI_RESPONSE_SCHEMA_REGISTRY["condition_entry_v1"]


def test_gemini_response_schema_registry_covers_required_endpoints():
    assert set(GEMINI_RESPONSE_SCHEMA_REGISTRY) == {
        "entry_v1",
        "entry_price_v1",
        "holding_exit_v1",
        "holding_exit_flow_v1",
        "overnight_v1",
        "condition_entry_v1",
        "condition_exit_v1",
        "threshold_ai_correction_v1",
        "lifecycle_ai_context_v1",
    }


def test_call_deepseek_safe_parses_plain_json_without_regex_cleanup():
    engine = _build_deepseek_call_engine()
    engine.client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **kwargs: SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(
                                content='{"action":"BUY","score":93,"reason":"fast-path"}'
                            )
                        )
                    ]
                )
            )
        )
    )

    result = DeepSeekSniperEngine._call_deepseek_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="test",
    )

    assert result == {"action": "BUY", "score": 93, "reason": "fast-path"}


def test_deepseek_holding_flow_normalizes_payload_and_caps_review_window(monkeypatch):
    engine = _build_deepseek_call_engine()

    def _fake_call(prompt, user_input, **kwargs):
        assert "직전 action을 뒤집으려면" in prompt
        assert "단일 score cutoff로 자르지 말고" in user_input
        assert "reason=매수 흡수 유지" in user_input
        return {
            "action": "HOLD",
            "score": "23",
            "flow_state": "흡수",
            "thesis": "매도 흡수",
            "evidence": "틱 매수 우위",
            "reason": "아직 붕괴보다 흡수에 가까움",
            "next_review_sec": 120,
        }

    monkeypatch.setattr(engine, "_call_deepseek_safe", _fake_call)

    result = DeepSeekSniperEngine.evaluate_scalping_holding_flow(
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
    )

    assert "시스템 guard" in SCALPING_HOLDING_FLOW_SYSTEM_PROMPT
    assert result["action"] == "HOLD"
    assert result["score"] == 23
    assert result["evidence"] == ["틱 매수 우위"]
    assert result["next_review_sec"] == 90


def test_deepseek_context_aware_backoff_caps_live_and_report_paths(monkeypatch):
    engine = _build_deepseek_call_engine()

    monkeypatch.setattr(
        ai_engine_deepseek_module,
        "TRADING_RULES",
        replace(
            ai_engine_deepseek_module.TRADING_RULES,
            DEEPSEEK_CONTEXT_AWARE_BACKOFF_ENABLED=True,
            DEEPSEEK_RETRY_BASE_SLEEP_SEC=0.4,
            DEEPSEEK_RETRY_JITTER_MAX_SEC=0.0,
            DEEPSEEK_RETRY_LIVE_MAX_SLEEP_SEC=0.8,
            DEEPSEEK_RETRY_REPORT_MAX_SLEEP_SEC=4.0,
        ),
    )
    monkeypatch.setattr(ai_engine_deepseek_module.random, "uniform", lambda a, b: 0.0)

    assert DeepSeekSniperEngine._compute_retry_sleep(engine, 0, live_sensitive=True) == 0.4
    assert DeepSeekSniperEngine._compute_retry_sleep(engine, 3, live_sensitive=True) == 0.8
    assert DeepSeekSniperEngine._compute_retry_sleep(engine, 3, live_sensitive=False) == 3.2


def test_deepseek_retry_acceptance_snapshot_separates_live_and_report_paths(monkeypatch):
    engine = _build_deepseek_call_engine()

    monkeypatch.setattr(
        ai_engine_deepseek_module,
        "TRADING_RULES",
        replace(
            ai_engine_deepseek_module.TRADING_RULES,
            DEEPSEEK_CONTEXT_AWARE_BACKOFF_ENABLED=True,
            DEEPSEEK_RETRY_BASE_SLEEP_SEC=0.4,
            DEEPSEEK_RETRY_JITTER_MAX_SEC=0.1,
            DEEPSEEK_RETRY_LIVE_MAX_SLEEP_SEC=0.8,
            DEEPSEEK_RETRY_REPORT_MAX_SLEEP_SEC=4.0,
        ),
    )

    live = DeepSeekSniperEngine._build_retry_acceptance_snapshot(
        engine,
        context_name="ENTRY:test",
        target_model="tier1-model",
    )
    report = DeepSeekSniperEngine._build_retry_acceptance_snapshot(
        engine,
        context_name="EOD:test",
        target_model="tier3-model",
    )

    assert live["context_aware_backoff_enabled"] is True
    assert live["live_sensitive"] is True
    assert live["max_sleep_sec"] == 0.8
    assert live["lock_scope"] == "api_call_lock"
    assert report["live_sensitive"] is False
    assert report["max_sleep_sec"] == 4.0
