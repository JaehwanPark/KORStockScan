from datetime import datetime

from src.engine.scalping.microstructure_reaction_context import build_microstructure_reaction_context


def _ws_data(**overrides):
    data = {
        "curr": 10120,
        "quote_age_ms": 200,
        "fluctuation": 8.0,
        "orderbook": {
            "asks": [
                {"price": 10110, "volume": 1200},
                {"price": 10120, "volume": 1300},
                {"price": 10130, "volume": 1400},
            ],
            "bids": [
                {"price": 10100, "volume": 4200},
                {"price": 10090, "volume": 3800},
                {"price": 10080, "volume": 3600},
            ],
        },
    }
    data.update(overrides)
    return data


def _ticks():
    return [
        {"time": "09:00:10", "price": 10120, "volume": 500, "dir": "BUY"},
        {"time": "09:00:09", "price": 10120, "volume": 420, "dir": "BUY"},
        {"time": "09:00:08", "price": 10110, "volume": 360, "dir": "BUY"},
        {"time": "09:00:07", "price": 10110, "volume": 180, "dir": "SELL"},
        {"time": "09:00:06", "price": 10100, "volume": 220, "dir": "BUY"},
        {"time": "09:00:05", "price": 10090, "volume": 140, "dir": "SELL"},
    ]


def test_ask_sweep_and_price_hold_surface_favorable_reaction():
    context = build_microstructure_reaction_context(
        _ws_data(),
        _ticks(),
        [{"고가": 10130, "저가": 10080}],
        now=datetime.strptime("09:00:12", "%H:%M:%S"),
    )

    assert context["microstructure_reaction_context_status"] == "ok"
    assert context["microstructure_reaction_ask_sweep_score"] >= 60
    assert context["microstructure_reaction_post_sweep_hold_score"] >= 60
    assert context["microstructure_reaction_bid_replenishment_score"] >= 55
    assert context["microstructure_reaction_entry_reaction_quality"] == "favorable_reaction"


def test_wall_replenishment_overrides_to_risk_context_only():
    context = build_microstructure_reaction_context(
        _ws_data(
            orderbook={
                "asks": [
                    {"price": 10110, "volume": 9000},
                    {"price": 10120, "volume": 8500},
                    {"price": 10130, "volume": 8000},
                ],
                "bids": [
                    {"price": 10100, "volume": 1000},
                    {"price": 10090, "volume": 900},
                    {"price": 10080, "volume": 800},
                ],
            }
        ),
        _ticks(),
        [{"고가": 10130, "저가": 10080}],
        now=datetime.strptime("09:00:12", "%H:%M:%S"),
    )

    assert context["microstructure_reaction_context_status"] == "ok"
    assert context["microstructure_reaction_wall_replenishment_risk_score"] >= 70
    assert context["microstructure_reaction_entry_reaction_quality"] == "risk_context_only"


def test_bid_replenishment_score_reflects_bid_depth_after_sell_prints():
    ticks = [
        {"time": "09:00:10", "price": 10100, "volume": 220, "dir": "SELL"},
        {"time": "09:00:09", "price": 10110, "volume": 500, "dir": "BUY"},
        {"time": "09:00:08", "price": 10100, "volume": 180, "dir": "SELL"},
        {"time": "09:00:07", "price": 10100, "volume": 300, "dir": "BUY"},
        {"time": "09:00:06", "price": 10100, "volume": 140, "dir": "SELL"},
    ]

    context = build_microstructure_reaction_context(
        _ws_data(),
        ticks,
        [{"고가": 10130, "저가": 10080}],
        now=datetime.strptime("09:00:12", "%H:%M:%S"),
    )

    assert context["microstructure_reaction_context_status"] == "ok"
    assert context["microstructure_reaction_bid_replenishment_score"] >= 60


def test_stale_and_insufficient_windows_return_neutral_context():
    stale = build_microstructure_reaction_context(
        _ws_data(quote_age_ms=1600),
        _ticks(),
        now=datetime.strptime("09:00:12", "%H:%M:%S"),
    )
    insufficient = build_microstructure_reaction_context(
        _ws_data(),
        _ticks()[:4],
        now=datetime.strptime("09:00:12", "%H:%M:%S"),
    )

    assert stale["microstructure_reaction_context_status"] == "stale"
    assert stale["microstructure_reaction_ask_sweep_score"] == 50
    assert insufficient["microstructure_reaction_context_status"] == "insufficient_window"
    assert insufficient["microstructure_reaction_post_sweep_hold_score"] == 50


def test_vi_proximity_is_risk_provenance_not_buy_trigger():
    context = build_microstructure_reaction_context(
        _ws_data(curr=11200, fluctuation=29.0),
        _ticks(),
        [{"고가": 11200, "저가": 10000}],
        now=datetime.strptime("09:00:12", "%H:%M:%S"),
    )

    assert context["microstructure_reaction_vi_proximity_risk"] >= 70
    assert context["microstructure_reaction_entry_reaction_quality"] == "risk_context_only"
