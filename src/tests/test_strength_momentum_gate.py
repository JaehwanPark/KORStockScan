from dataclasses import replace

import src.engine.sniper_strength_momentum as strength_momentum_module
from src.engine.sniper_strength_momentum import evaluate_scalping_strength_momentum
from src.utils.constants import TRADING_RULES as CONFIG


def _build_history(entries):
    return [
        {
            "ts": ts,
            "v_pw": v_pw,
            "tick_value": tick_value,
            "buy_tick_value": buy_value,
            "sell_tick_value": sell_value,
            "buy_qty": buy_qty,
            "sell_qty": sell_qty,
            "buy_ratio": buy_ratio,
        }
        for ts, v_pw, tick_value, buy_value, sell_value, buy_qty, sell_qty, buy_ratio in entries
    ]


def test_strength_momentum_allows_when_buy_pressure_is_strong():
    ws_data = {
        "v_pw": 103.0,
        "strength_momentum_history": _build_history([
            (100.0, 96.0, 8_000, 6_000, 2_000, 420, 180, 63.0),
            (104.0, 100.0, 15_000, 12_000, 3_000, 760, 240, 72.0),
            (108.0, 103.0, 20_000, 18_000, 2_000, 980, 220, 81.0),
        ]),
    }

    result = evaluate_scalping_strength_momentum(ws_data, now_ts=108.0)

    assert result["allowed"] is True
    assert result["reason"] in {"momentum_ok", "buy_value_override", "strong_absolute_override"}
    assert result["window_buy_value"] >= 20_000
    assert result["window_exec_buy_ratio"] >= 0.56


def test_strength_momentum_blocks_when_exec_buy_pressure_is_weak():
    ws_data = {
        "v_pw": 102.0,
        "strength_momentum_history": _build_history([
            (200.0, 97.0, 10_000, 7_000, 3_000, 260, 240, 52.0),
            (204.0, 100.0, 12_000, 8_000, 4_000, 310, 290, 51.0),
            (208.0, 102.0, 14_000, 9_000, 5_000, 360, 340, 51.0),
        ]),
    }

    result = evaluate_scalping_strength_momentum(ws_data, now_ts=208.0)

    assert result["allowed"] is False
    assert result["reason"] in {"below_exec_buy_ratio", "below_net_buy_qty", "below_buy_ratio"}


def test_strength_momentum_relaxed_profile_allows_open_reclaim_borderline_case():
    ws_data = {
        "v_pw": 94.0,
        "_position_tag": "OPEN_RECLAIM",
        "strength_momentum_history": _build_history([
            (300.0, 93.0, 8_000, 6_000, 2_000, 1_000, 900, 75.0),
            (304.0, 94.0, 8_000, 6_000, 2_000, 1_280, 1_140, 75.0),
            (308.0, 94.0, 8_000, 6_000, 2_000, 1_540, 1_360, 75.0),
        ]),
    }

    result = evaluate_scalping_strength_momentum(ws_data, now_ts=308.0)

    assert result["allowed"] is True
    assert result["threshold_profile"] == "relaxed"
    assert result["position_tag"] == "OPEN_RECLAIM"
    assert result["window_buy_value"] == 18_000
    assert result["window_exec_buy_ratio"] == 0.54


def test_strength_momentum_keeps_default_profile_for_scanner():
    ws_data = {
        "v_pw": 94.0,
        "_position_tag": "SCANNER",
        "strength_momentum_history": _build_history([
            (400.0, 93.0, 8_000, 6_000, 2_000, 1_000, 900, 75.0),
            (404.0, 94.0, 8_000, 6_000, 2_000, 1_280, 1_140, 75.0),
            (408.0, 94.0, 8_000, 6_000, 2_000, 1_540, 1_360, 75.0),
        ]),
    }

    result = evaluate_scalping_strength_momentum(ws_data, now_ts=408.0)

    assert result["allowed"] is False
    assert result["threshold_profile"] == "default"
    assert result["position_tag"] == "SCANNER"
    assert result["reason"] == "below_strength_base"


def test_strength_momentum_canary_relaxes_exec_buy_ratio_for_scanner(monkeypatch):
    monkeypatch.setattr(
        strength_momentum_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_DYNAMIC_STRENGTH_CANARY_ENABLED=True,
            SCALP_DYNAMIC_STRENGTH_CANARY_TAGS=("SCANNER",),
            SCALP_DYNAMIC_STRENGTH_CANARY_ALLOWED_REASONS=("below_exec_buy_ratio",),
            SCALP_DYNAMIC_STRENGTH_CANARY_MIN_BUY_VALUE_RATIO=0.85,
            SCALP_DYNAMIC_STRENGTH_CANARY_BUY_RATIO_TOL=0.03,
            SCALP_DYNAMIC_STRENGTH_CANARY_EXEC_BUY_RATIO_TOL=0.03,
        ),
    )

    ws_data = {
        "v_pw": 102.0,
        "_position_tag": "SCANNER",
        "strength_momentum_history": _build_history([
            (500.0, 99.0, 10_000, 8_000, 2_000, 500, 460, 80.0),
            (504.0, 101.0, 10_000, 8_000, 2_000, 650, 590, 80.0),
            (508.0, 102.0, 10_000, 8_000, 2_000, 820, 740, 80.0),
        ]),
    }

    result = evaluate_scalping_strength_momentum(ws_data, now_ts=508.0)

    assert result["canary_applied"] is True
    assert result["allowed"] is True
    assert result["reason"] == "canary_relaxed_below_exec_buy_ratio"
    assert result["canary_origin_reason"] == "below_exec_buy_ratio"


def test_strength_momentum_canary_not_applied_for_non_allowed_tag(monkeypatch):
    monkeypatch.setattr(
        strength_momentum_module,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALP_DYNAMIC_STRENGTH_CANARY_ENABLED=True,
            SCALP_DYNAMIC_STRENGTH_CANARY_TAGS=("SCANNER",),
            SCALP_DYNAMIC_STRENGTH_CANARY_ALLOWED_REASONS=("below_exec_buy_ratio",),
            SCALP_DYNAMIC_STRENGTH_CANARY_MIN_BUY_VALUE_RATIO=0.85,
            SCALP_DYNAMIC_STRENGTH_CANARY_BUY_RATIO_TOL=0.03,
            SCALP_DYNAMIC_STRENGTH_CANARY_EXEC_BUY_RATIO_TOL=0.03,
        ),
    )

    ws_data = {
        "v_pw": 102.0,
        "_position_tag": "MIDDLE",
        "strength_momentum_history": _build_history([
            (600.0, 99.0, 10_000, 8_000, 2_000, 500, 460, 80.0),
            (604.0, 101.0, 10_000, 8_000, 2_000, 650, 590, 80.0),
            (608.0, 102.0, 10_000, 8_000, 2_000, 820, 740, 80.0),
        ]),
    }

    result = evaluate_scalping_strength_momentum(ws_data, now_ts=608.0)

    assert result["canary_applied"] is False
    assert result["allowed"] is False
    assert result["reason"] == "below_exec_buy_ratio"
