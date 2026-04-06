from src.engine.sniper_state_handlers import (
    _build_gatekeeper_fast_signature,
    _build_holding_ai_fast_signature,
    _resolve_gatekeeper_fast_reuse_sec,
    _resolve_holding_ai_fast_reuse_sec,
)


def test_gatekeeper_fast_signature_absorbs_small_noise():
    stock = {"position_tag": "MIDDLE"}
    ws_a = {
        "curr": 12570,
        "fluctuation": 3.42,
        "volume": 1854321,
        "v_pw": 118.1,
        "buy_ratio": 62.4,
        "prog_net_qty": 18490,
        "prog_delta_qty": 2210,
        "ask_tot": 184200,
        "bid_tot": 218700,
        "net_bid_depth": 11880,
        "net_ask_depth": -3420,
        "orderbook": {
            "asks": [{"price": 12590}, {"price": 12580}],
            "bids": [{"price": 12570}, {"price": 12560}],
        },
    }
    ws_b = dict(ws_a)
    ws_b.update({
        "volume": 1858999,
        "v_pw": 118.8,
        "buy_ratio": 63.1,
        "prog_net_qty": 18999,
        "ask_tot": 188999,
    })

    sig_a = _build_gatekeeper_fast_signature(stock, ws_a, "KOSPI_ML", 81.0)
    sig_b = _build_gatekeeper_fast_signature(stock, ws_b, "KOSPI_ML", 81.4)

    assert sig_a == sig_b


def test_holding_ai_fast_signature_changes_on_meaningful_orderbook_shift():
    ws_a = {
        "curr": 10000,
        "fluctuation": 1.5,
        "v_pw": 122.0,
        "buy_ratio": 61.0,
        "ask_tot": 90000,
        "bid_tot": 120000,
        "net_bid_depth": 7000,
        "net_ask_depth": -2000,
        "buy_exec_volume": 4000,
        "sell_exec_volume": 2000,
        "tick_trade_value": 26000,
        "orderbook": {
            "asks": [{"price": 10020}, {"price": 10010}],
            "bids": [{"price": 10000}, {"price": 9990}],
        },
    }
    ws_b = dict(ws_a)
    ws_b.update({
        "curr": 10120,
        "buy_ratio": 74.0,
        "ask_tot": 150000,
        "bid_tot": 80000,
    })
    ws_b["orderbook"] = {
        "asks": [{"price": 10140}, {"price": 10130}],
        "bids": [{"price": 10120}, {"price": 10110}],
    }

    sig_a = _build_holding_ai_fast_signature(ws_a)
    sig_b = _build_holding_ai_fast_signature(ws_b)

    assert sig_a != sig_b


def test_holding_ai_fast_reuse_sec_tracks_review_window():
    assert _resolve_holding_ai_fast_reuse_sec(True, 10) == 12.0
    assert _resolve_holding_ai_fast_reuse_sec(False, 50) == 52.0


def test_gatekeeper_fast_reuse_sec_has_minimum_window():
    assert _resolve_gatekeeper_fast_reuse_sec() >= 20.0
