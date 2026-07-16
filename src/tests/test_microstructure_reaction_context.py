from datetime import datetime

from src.engine.scalping.microstructure_reaction_context import (
    build_microstructure_reaction_context,
    infer_tick_aggressor_side,
    precompute_microstructure_reaction_inputs,
)


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
        {
            "time": "09:00:10",
            "price": 10120,
            "volume": 500,
            "dir": "BUY",
            "aggressor_source": "trusted_declared_side",
        },
        {
            "time": "09:00:09",
            "price": 10120,
            "volume": 420,
            "dir": "BUY",
            "aggressor_source": "trusted_declared_side",
        },
        {
            "time": "09:00:08",
            "price": 10110,
            "volume": 360,
            "dir": "BUY",
            "aggressor_source": "trusted_declared_side",
        },
        {
            "time": "09:00:07",
            "price": 10110,
            "volume": 180,
            "dir": "SELL",
            "aggressor_source": "trusted_declared_side",
        },
        {
            "time": "09:00:06",
            "price": 10100,
            "volume": 220,
            "dir": "BUY",
            "aggressor_source": "trusted_declared_side",
        },
        {
            "time": "09:00:05",
            "price": 10090,
            "volume": 140,
            "dir": "SELL",
            "aggressor_source": "trusted_declared_side",
        },
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
    assert (
        context["microstructure_reaction_entry_reaction_quality"]
        == "favorable_reaction"
    )


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
    assert (
        context["microstructure_reaction_entry_reaction_quality"] == "risk_context_only"
    )


def test_bid_replenishment_score_reflects_bid_depth_after_sell_prints():
    ticks = [
        {
            "time": "09:00:10",
            "price": 10100,
            "volume": 220,
            "dir": "SELL",
            "aggressor_source": "trusted_declared_side",
        },
        {
            "time": "09:00:09",
            "price": 10110,
            "volume": 500,
            "dir": "BUY",
            "aggressor_source": "trusted_declared_side",
        },
        {
            "time": "09:00:08",
            "price": 10100,
            "volume": 180,
            "dir": "SELL",
            "aggressor_source": "trusted_declared_side",
        },
        {
            "time": "09:00:07",
            "price": 10100,
            "volume": 300,
            "dir": "BUY",
            "aggressor_source": "trusted_declared_side",
        },
        {
            "time": "09:00:06",
            "price": 10100,
            "volume": 140,
            "dir": "SELL",
            "aggressor_source": "trusted_declared_side",
        },
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
    assert (
        insufficient["microstructure_reaction_context_status"] == "insufficient_window"
    )
    assert insufficient["microstructure_reaction_post_sweep_hold_score"] == 50


def test_vi_proximity_is_risk_provenance_not_buy_trigger():
    context = build_microstructure_reaction_context(
        _ws_data(curr=11200, fluctuation=29.0),
        _ticks(),
        [{"고가": 11200, "저가": 10000}],
        now=datetime.strptime("09:00:12", "%H:%M:%S"),
    )

    assert context["microstructure_reaction_vi_proximity_risk"] >= 70
    assert (
        context["microstructure_reaction_entry_reaction_quality"] == "risk_context_only"
    )


def test_precomputed_snapshot_preserves_context_result():
    now = datetime.strptime("09:00:12", "%H:%M:%S")
    snapshot = precompute_microstructure_reaction_inputs(
        _ws_data(),
        _ticks(),
        [{"고가": 10130, "저가": 10080}],
        now=now,
    )

    direct = build_microstructure_reaction_context(
        _ws_data(),
        _ticks(),
        [{"고가": 10130, "저가": 10080}],
        now=now,
    )
    reused = build_microstructure_reaction_context(
        _ws_data(),
        _ticks(),
        [{"고가": 10130, "저가": 10080}],
        now=now,
        precomputed=snapshot,
    )

    assert reused == direct


def test_context_with_only_untrusted_declared_side_is_neutral_partial():
    ticks = [
        {"time": "09:00:10", "price": 10120, "volume": 500, "dir": "BUY"},
        {"time": "09:00:09", "price": 10120, "volume": 420, "dir": "BUY"},
        {"time": "09:00:08", "price": 10110, "volume": 360, "dir": "BUY"},
        {"time": "09:00:07", "price": 10110, "volume": 180, "dir": "SELL"},
        {"time": "09:00:06", "price": 10100, "volume": 220, "dir": "BUY"},
    ]

    context = build_microstructure_reaction_context(
        _ws_data(),
        ticks,
        [{"고가": 10130, "저가": 10080}],
        now=datetime.strptime("09:00:12", "%H:%M:%S"),
    )

    assert context["microstructure_reaction_context_status"] == "source_quality_partial"
    assert (
        context["microstructure_reaction_source_quality"]
        == "tick_aggressor_pressure_unusable"
    )
    assert (
        context["microstructure_reaction_entry_reaction_quality"] == "neutral_unusable"
    )
    assert context["microstructure_reaction_ask_sweep_score"] == 50
    assert context["microstructure_reaction_wall_replenishment_risk_score"] == 50
    assert context["microstructure_reaction_tick_aggressor_pressure_usable"] is False
    assert context["microstructure_reaction_tick_aggressor_trusted_count"] == 0


def test_cached_orderbook_touch_source_is_preserved():
    inferred = infer_tick_aggressor_side(
        {
            "time": "09:00:10",
            "price": 10110,
            "volume": 100,
            "best_ask": 10110,
            "best_bid": 10100,
            "aggressor_source": "cached_orderbook_touch",
            "aggressor_quality": "cached_quote_touch_or_crossed_ask",
            "aggressor_quote_source": "cached_top_of_book_ttl",
        }
    )

    assert inferred["side"] == "BUY"
    assert inferred["source"] == "cached_orderbook_touch"
    assert inferred["quality"] == "cached_quote_touch_or_crossed_ask"


def test_kiwoom_0b_signed_trade_volume_source_is_trusted_before_touch_fallback():
    inferred = infer_tick_aggressor_side(
        {
            "time": "09:00:10",
            "price": 10100,
            "volume": 100,
            "best_ask": 10110,
            "best_bid": 10100,
            "aggressor_side": "BUY",
            "aggressor_source": "kiwoom_0b_signed_trade_volume",
            "aggressor_quality": "signed_trade_volume_positive",
            "aggressor_quote_source": "0B_inline_best_quote",
            "aggressor_touch_side": "SELL",
            "aggressor_touch_source": "orderbook_touch",
            "aggressor_touch_quality": "touch_or_crossed_bid",
            "aggressor_touch_confirms_signed": False,
        }
    )

    assert inferred["side"] == "BUY"
    assert inferred["source"] == "kiwoom_0b_signed_trade_volume"
    assert inferred["quality"] == "signed_trade_volume_positive"
    assert inferred["touch_side"] == "SELL"
    assert inferred["touch_confirms_signed"] is False


def test_source_less_declared_side_is_not_pressure_usable():
    snapshot = precompute_microstructure_reaction_inputs(
        _ws_data(),
        [
            {"time": "09:00:10", "price": 10110, "volume": 100, "dir": "BUY"},
            {"time": "09:00:09", "price": 10100, "volume": 80, "side": "SELL"},
        ],
        now=datetime.strptime("09:00:12", "%H:%M:%S"),
    )

    assert snapshot["buy_pressure_pct"] == 50.0
    assert snapshot["buy_vol"] == 0
    assert snapshot["sell_vol"] == 0
    assert snapshot["tick_aggressor_trusted_count"] == 0
    assert snapshot["tick_aggressor_pressure_usable"] is False
    assert snapshot["tick_aggressor_source_counts"]["declared_tick_side_untrusted"] == 2


def test_price_change_heuristic_with_quote_is_not_promoted_to_orderbook_touch():
    inferred = infer_tick_aggressor_side(
        {
            "time": "09:00:10",
            "price": 10110,
            "volume": 100,
            "best_ask": 10110,
            "best_bid": 10100,
            "dir": "BUY",
            "aggressor_source": "price_change_heuristic",
        }
    )

    assert inferred["side"] == "UNKNOWN"
    assert inferred["source"] == "price_change_heuristic"
    assert inferred["quality"] == "quote_with_untrusted_aggressor_source"


def test_source_less_best_quote_is_not_promoted_to_orderbook_touch():
    inferred = infer_tick_aggressor_side(
        {
            "time": "09:00:10",
            "price": 10110,
            "volume": 100,
            "best_ask": 10110,
            "best_bid": 10100,
            "dir": "BUY",
        }
    )

    assert inferred["side"] == "UNKNOWN"
    assert inferred["source"] == "untrusted_orderbook_touch_source"
    assert inferred["quality"] == "quote_with_untrusted_aggressor_source"


def test_raw_0b_quote_fields_without_normalized_source_still_allow_touch_inference():
    inferred = infer_tick_aggressor_side(
        {
            "time": "09:00:10",
            "price": 10110,
            "volume": 100,
            "10": 10110,
            "27": 10110,
            "28": 10100,
        }
    )

    assert inferred["side"] == "BUY"
    assert inferred["source"] == "orderbook_touch"
    assert inferred["quality"] == "touch_or_crossed_ask"


def test_precomputed_snapshot_counts_cached_orderbook_touch_separately():
    snapshot = precompute_microstructure_reaction_inputs(
        _ws_data(),
        [
            {
                "time": "09:00:10",
                "price": 10110,
                "volume": 100,
                "best_ask": 10110,
                "best_bid": 10100,
                "aggressor_source": "cached_orderbook_touch",
                "aggressor_quote_source": "cached_top_of_book_ttl",
            }
        ],
        now=datetime.strptime("09:00:12", "%H:%M:%S"),
    )

    assert snapshot["tick_aggressor_cached_orderbook_touch_count"] == 1
    assert snapshot["tick_aggressor_orderbook_touch_count"] == 0
    assert snapshot["tick_aggressor_trusted_count"] == 1
    assert snapshot["buy_pressure_pct"] == 100.0
