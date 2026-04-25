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


def test_trading_rules_dynamic_strength_relief_env_override(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_RELIEF_ENABLED", "false")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_RELIEF_TAGS", "SCANNER")
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_RELIEF_ALLOWED_REASONS",
        "below_window_buy_value,below_buy_ratio",
    )
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_RELIEF_MIN_BUY_VALUE_RATIO", "0.90")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_RELIEF_BUY_RATIO_TOL", "0.02")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_RELIEF_EXEC_BUY_RATIO_TOL", "0.01")

    reloaded = importlib.reload(constants)

    assert reloaded.TRADING_RULES.SCALP_DYNAMIC_STRENGTH_RELIEF_ENABLED is False
    assert reloaded.TRADING_RULES.SCALP_DYNAMIC_STRENGTH_RELIEF_TAGS == ("SCANNER",)
    assert reloaded.TRADING_RULES.SCALP_DYNAMIC_STRENGTH_RELIEF_ALLOWED_REASONS == (
        "below_window_buy_value",
        "below_buy_ratio",
    )
    assert reloaded.TRADING_RULES.SCALP_DYNAMIC_STRENGTH_RELIEF_MIN_BUY_VALUE_RATIO == 0.90
    assert reloaded.TRADING_RULES.SCALP_DYNAMIC_STRENGTH_RELIEF_BUY_RATIO_TOL == 0.02
    assert reloaded.TRADING_RULES.SCALP_DYNAMIC_STRENGTH_RELIEF_EXEC_BUY_RATIO_TOL == 0.01
