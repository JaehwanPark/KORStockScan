from src.engine.sniper_state_handlers import (
    _build_holding_ai_fast_signature,
    _build_holding_ai_fast_snapshot,
    _describe_snapshot_deltas,
)


def test_holding_fast_signature_tolerates_small_micro_moves():
    base = {
        "curr": 57100,
        "fluctuation": 1.24,
        "v_pw": 210.3,
        "buy_ratio": 63.1,
        "ask_tot": 184000,
        "bid_tot": 176500,
        "net_bid_depth": 8400,
        "net_ask_depth": -5200,
        "buy_exec_volume": 7800,
        "sell_exec_volume": 6100,
        "tick_trade_value": 24800,
        "orderbook": {
            "asks": [{"price": 57200, "volume": 3100}],
            "bids": [{"price": 57100, "volume": 2900}],
        },
    }
    micro_shift = {
        **base,
        "curr": 57150,
        "fluctuation": 1.31,
        "v_pw": 211.6,
        "buy_ratio": 64.8,
        "ask_tot": 191000,
        "bid_tot": 181000,
        "net_bid_depth": 9100,
        "net_ask_depth": -4800,
        "buy_exec_volume": 8300,
        "sell_exec_volume": 6400,
        "tick_trade_value": 28900,
        "orderbook": {
            "asks": [{"price": 57250, "volume": 3300}],
            "bids": [{"price": 57150, "volume": 3000}],
        },
    }

    assert _build_holding_ai_fast_signature(base) == _build_holding_ai_fast_signature(micro_shift)


def test_holding_fast_signature_changes_on_meaningful_move():
    base = {
        "curr": 57100,
        "fluctuation": 1.2,
        "v_pw": 210.0,
        "buy_ratio": 63.0,
        "ask_tot": 184000,
        "bid_tot": 176000,
        "net_bid_depth": 8000,
        "net_ask_depth": -5000,
        "buy_exec_volume": 7000,
        "sell_exec_volume": 6000,
        "tick_trade_value": 24000,
        "orderbook": {
            "asks": [{"price": 57200, "volume": 3100}],
            "bids": [{"price": 57100, "volume": 2900}],
        },
    }
    larger_move = {
        **base,
        "curr": 57450,
        "fluctuation": 1.9,
        "v_pw": 226.0,
        "buy_ratio": 71.0,
        "ask_tot": 260000,
        "bid_tot": 210000,
        "net_bid_depth": 21000,
        "net_ask_depth": -12000,
        "buy_exec_volume": 15000,
        "sell_exec_volume": 7000,
        "tick_trade_value": 68000,
        "orderbook": {
            "asks": [{"price": 57500, "volume": 5100}],
            "bids": [{"price": 57400, "volume": 4200}],
        },
    }

    assert _build_holding_ai_fast_signature(base) != _build_holding_ai_fast_signature(larger_move)


def test_holding_fast_snapshot_reports_changed_axes():
    base = {
        "curr": 12150,
        "fluctuation": -0.33,
        "v_pw": 102.4,
        "buy_ratio": 51.2,
        "ask_tot": 182000,
        "bid_tot": 176000,
        "net_bid_depth": 8200,
        "net_ask_depth": -6100,
        "buy_exec_volume": 2400,
        "sell_exec_volume": 2100,
        "tick_trade_value": 28100,
        "orderbook": {
            "asks": [{"price": 12200}],
            "bids": [{"price": 12150}],
        },
    }
    shifted = {
        **base,
        "v_pw": 118.1,
        "ask_tot": 282000,
        "bid_tot": 126000,
    }

    delta_text = _describe_snapshot_deltas(
        _build_holding_ai_fast_snapshot(base),
        _build_holding_ai_fast_snapshot(shifted),
    )

    assert "v_pw:" in delta_text
    assert "ask_bid_balance:" in delta_text
