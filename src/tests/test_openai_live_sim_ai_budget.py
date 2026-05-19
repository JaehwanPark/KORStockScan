import os

import pytest

from src.engine import ai_engine_openai as openai_module
from src.engine.ai_engine_openai import GPTSniperEngine
from src.engine.sniper_config import CONF


class _RulesProxy:
    def __init__(self, base, **overrides):
        self._base = base
        self._overrides = overrides

    def __getattr__(self, name):
        if name in self._overrides:
            return self._overrides[name]
        return getattr(self._base, name)


def _api_keys() -> list[str]:
    raw = os.getenv("OPENAI_API_KEYS") or os.getenv("OPENAI_API_KEY") or ""
    keys = [part.strip() for part in raw.split(",") if part.strip()]
    keys.extend(v for k, v in sorted(CONF.items()) if str(k).startswith("OPENAI_API_KEY") and v)
    return keys


def test_live_openai_holding_schema_for_sim_ai_budget(monkeypatch):
    if os.getenv("RUN_OPENAI_LIVE_TESTS") != "1":
        pytest.skip("live OpenAI test disabled; set RUN_OPENAI_LIVE_TESTS=1")
    keys = _api_keys()
    if not keys:
        pytest.fail("RUN_OPENAI_LIVE_TESTS=1 requires OPENAI_API_KEY or OPENAI_API_KEYS")

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        _RulesProxy(
            openai_module.TRADING_RULES,
            GPT_FAST_MODEL=os.getenv("KORSTOCKSCAN_OPENAI_LIVE_TEST_MODEL", "gpt-5-nano"),
            OPENAI_TRANSPORT_MODE="responses_ws",
            OPENAI_RESPONSES_WS_ENABLED=True,
            OPENAI_RESPONSES_WS_POOL_SIZE=1,
            OPENAI_RESPONSES_WS_TIMEOUT_MS=10000,
            OPENAI_RESPONSE_SCHEMA_REGISTRY_ENABLED=False,
            OPENAI_REASONING_EFFORT="auto",
            OPENAI_RESPONSES_MAX_OUTPUT_TOKENS=1024,
        ),
    )
    engine = GPTSniperEngine(keys, announce_startup=False)
    result = engine.analyze_target(
        "SIM_BUDGET_LIVE_TEST",
        {
            "curr": 10000,
            "fluctuation": 0.45,
            "v_pw": 121.0,
            "buy_ratio": 58.0,
            "ask_tot": 80000,
            "bid_tot": 95000,
            "orderbook": {
                "asks": [{"price": 10010, "volume": 3000}, {"price": 10020, "volume": 4500}],
                "bids": [{"price": 10000, "volume": 3800}, {"price": 9990, "volume": 4200}],
            },
        },
        [
            {"time": "10:00:00", "price": 10000, "volume": 120, "dir": "BUY", "strength": 121.0},
            {"time": "09:59:59", "price": 9990, "volume": 80, "dir": "SELL", "strength": 119.0},
            {"time": "09:59:58", "price": 10000, "volume": 150, "dir": "BUY", "strength": 120.5},
        ],
        [
            {"체결시간": "09:58:00", "시가": 9980, "현재가": 9990, "고가": 10010, "저가": 9970, "거래량": 1200},
            {"체결시간": "09:59:00", "시가": 9990, "현재가": 10000, "고가": 10020, "저가": 9980, "거래량": 1400},
        ],
        strategy="SCALPING",
        cache_profile="holding",
        prompt_profile="holding",
    )
    pool = getattr(engine, "_responses_ws_pool", None)
    if pool is not None:
        pool.close()

    assert result["openai_ws_used"] is True
    assert result["openai_endpoint_name"] == "analyze_target"
    assert result["openai_schema_name"] == "holding_exit_v1"
    assert result["ai_parse_ok"] is True
    assert result["action_schema"] == "holding_exit_v1"
    assert result["action_v2"] in {"HOLD", "TRIM", "EXIT"}
