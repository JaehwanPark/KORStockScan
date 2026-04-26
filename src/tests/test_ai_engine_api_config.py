import threading
from dataclasses import replace
from types import SimpleNamespace

from src.engine import ai_engine as ai_engine_module
from src.engine import ai_engine_deepseek as ai_engine_deepseek_module
from src.engine.ai_engine import GeminiSniperEngine
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
    engine.api_call_lock = threading.Lock()
    engine.current_model_name = "tier1-model"
    engine.model_tier3_deep = "tier3-model"
    engine.api_keys = ["deepseek-key-a", "deepseek-key-b"]
    engine.current_key = "deepseek-key-a"
    engine.current_api_key_index = 0

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
