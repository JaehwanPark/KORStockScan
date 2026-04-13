import importlib

import pytest

import src.utils.constants as constants


@pytest.fixture(autouse=True)
def reload_constants_module():
    yield
    importlib.reload(constants)


def test_trading_rules_default_latency_canary_thresholds(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_LATENCY_CANARY_PROFILE", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCALP_LATENCY_GUARD_CANARY_MAX_WS_AGE_MS", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCALP_LATENCY_GUARD_CANARY_MAX_SPREAD_RATIO", raising=False)

    reloaded = importlib.reload(constants)

    assert reloaded.TRADING_RULES.SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS == 260
    assert reloaded.TRADING_RULES.SCALP_LATENCY_GUARD_CANARY_MAX_WS_AGE_MS == 450
    assert reloaded.TRADING_RULES.SCALP_LATENCY_GUARD_CANARY_MAX_SPREAD_RATIO == 0.0100


def test_trading_rules_remote_v2_profile_relaxes_latency_canary_jitter(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_LATENCY_CANARY_PROFILE", "remote_v2")
    monkeypatch.delenv("KORSTOCKSCAN_SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS", raising=False)

    reloaded = importlib.reload(constants)

    assert reloaded.TRADING_RULES.SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS == 400
    assert reloaded.TRADING_RULES.SCALP_LATENCY_GUARD_CANARY_MAX_WS_AGE_MS == 450


def test_trading_rules_env_override_wins_over_profile(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_LATENCY_CANARY_PROFILE", "remote_v2")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS", "420")

    reloaded = importlib.reload(constants)

    assert reloaded.TRADING_RULES.SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS == 420


def test_trading_rules_shadow_prompt_env_override(monkeypatch):
    monkeypatch.setenv("AI_WATCHING_75_PROMPT_SHADOW_ENABLED", "true")
    monkeypatch.setenv("AI_WATCHING_75_PROMPT_SHADOW_MIN_SCORE", "74")
    monkeypatch.setenv("AI_WATCHING_75_PROMPT_SHADOW_MAX_SCORE", "81")

    reloaded = importlib.reload(constants)

    assert reloaded.TRADING_RULES.AI_WATCHING_75_PROMPT_SHADOW_ENABLED is True
    assert reloaded.TRADING_RULES.AI_WATCHING_75_PROMPT_SHADOW_MIN_SCORE == 74
    assert reloaded.TRADING_RULES.AI_WATCHING_75_PROMPT_SHADOW_MAX_SCORE == 81
