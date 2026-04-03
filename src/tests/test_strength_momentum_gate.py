from src.engine.sniper_strength_momentum import evaluate_scalping_strength_momentum


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
