from datetime import datetime

from src.engine.scalping.market_data_enrichment import (
    CONFLICTED,
    FRESH_WS,
    REST_ENRICHED,
    SIGNED_TAPE_BUY_DOMINATED,
    SIGNED_TAPE_SELL_DOMINATED,
    build_market_data_enrichment,
)


def _rest_orderbook(price=10000):
    return {
        "source": "ka10004_rest_orderbook",
        "curr": price,
        "best_ask": price + 10,
        "best_bid": price - 10,
        "best_ask_qty": 120,
        "best_bid_qty": 140,
        "rest_received_ts": 1000.0,
        "orderbook": {
            "asks": [{"price": price + 10, "qty": 120}],
            "bids": [{"price": price - 10, "qty": 140}],
        },
    }


def test_market_data_enrichment_uses_fresh_ws_without_rest():
    ws_data = {
        "curr": 10000,
        "best_ask": 10010,
        "best_bid": 9990,
        "last_ws_update_ts": 1000.0,
    }

    enriched, fields = build_market_data_enrichment(ws_data=ws_data, now_ts=1000.2)

    assert fields["market_data_freshness_state"] == FRESH_WS
    assert fields["market_data_enrichment_applied"] is False
    assert fields["market_data_effective_price_source"] == "ws"
    assert enriched["curr"] == 10000


def test_market_data_enrichment_normalizes_nested_ws_best_levels():
    enriched, fields = build_market_data_enrichment(
        ws_data={
            "curr": 10000,
            "last_ws_update_ts": 1000.0,
            "orderbook": {
                "asks": [{"price": 10010, "qty": 120}],
                "bids": [{"price": 9990, "qty": 140}],
            },
        },
        now_ts=1000.1,
    )

    assert fields["market_data_freshness_state"] == FRESH_WS
    assert fields["market_data_effective_quote_level_basis"] == "normalized_ws_orderbook"
    assert fields["market_data_effective_best_ask"] == 10010
    assert fields["market_data_effective_best_bid"] == 9990
    assert enriched["best_ask"] == 10010
    assert enriched["best_bid"] == 9990


def test_market_data_enrichment_promotes_stale_ws_to_rest_enriched_quote():
    ws_data = {
        "curr": 9900,
        "best_ask": 9910,
        "best_bid": 9890,
        "last_ws_update_ts": 990.0,
        "quote_stale": True,
    }

    enriched, fields = build_market_data_enrichment(
        ws_data=ws_data,
        rest_orderbook=_rest_orderbook(10000),
        now_ts=1000.0,
    )

    assert fields["market_data_freshness_state"] == REST_ENRICHED
    assert fields["market_data_orderbook_state"] == REST_ENRICHED
    assert fields["market_data_effective_price_source"] == "ka10004_rest_orderbook"
    assert enriched["curr"] == 10000
    assert enriched["quote_refresh_source"] == "ka10004_rest_orderbook"


def test_market_data_enrichment_promotes_stale_ws_to_rest_when_gap_is_large():
    ws_data = {
        "curr": 9000,
        "best_ask": 9010,
        "best_bid": 8990,
        "last_ws_update_ts": 990.0,
        "quote_stale": True,
    }

    enriched, fields = build_market_data_enrichment(
        ws_data=ws_data,
        rest_orderbook=_rest_orderbook(10000),
        now_ts=1000.0,
        max_ws_rest_gap_bps=100.0,
    )

    assert fields["market_data_freshness_state"] == REST_ENRICHED
    assert fields["market_data_orderbook_state"] == REST_ENRICHED
    assert fields["market_data_ws_rest_gap_bps"] > 100.0
    assert enriched["curr"] == 10000


def test_market_data_enrichment_uses_ka10004_mid_price_when_current_price_missing():
    ws_data = {
        "curr": 9900,
        "best_ask": 9910,
        "best_bid": 9890,
        "last_ws_update_ts": 990.0,
        "quote_stale": True,
    }
    rest_snapshot = _rest_orderbook(10000)
    rest_snapshot["curr"] = 0
    rest_snapshot["rest_mid_price"] = 10000

    enriched, fields = build_market_data_enrichment(
        ws_data=ws_data,
        rest_orderbook=rest_snapshot,
        now_ts=1000.0,
    )

    assert fields["market_data_freshness_state"] == REST_ENRICHED
    assert enriched["curr"] == 10000
    assert enriched["best_ask"] == 10010
    assert enriched["best_bid"] == 9990


def test_market_data_enrichment_marks_large_ws_rest_gap_conflicted():
    ws_data = {
        "curr": 10000,
        "best_ask": 10010,
        "best_bid": 9990,
        "last_ws_update_ts": 1000.0,
    }

    _enriched, fields = build_market_data_enrichment(
        ws_data=ws_data,
        rest_orderbook=_rest_orderbook(11000),
        now_ts=1000.1,
        max_ws_rest_gap_bps=100.0,
    )

    assert fields["market_data_freshness_state"] == CONFLICTED
    assert fields["market_data_orderbook_state"] == CONFLICTED
    assert fields["market_data_effective_price_source"] == "ws_rest_conflicted"


def test_market_data_enrichment_freshest_policy_uses_younger_rest_quote():
    ws_data = {
        "curr": 10000,
        "best_ask": 10010,
        "best_bid": 9990,
        "last_ws_update_ts": 999.2,
    }
    rest_snapshot = _rest_orderbook(10020)
    rest_snapshot["rest_received_ts"] = 999.9

    enriched, fields = build_market_data_enrichment(
        ws_data=ws_data,
        rest_orderbook=rest_snapshot,
        now_ts=1000.0,
        prefer_freshest_source=True,
    )

    assert fields["market_data_freshness_state"] == REST_ENRICHED
    assert fields["market_data_effective_price_source"] == "ka10004_rest_orderbook"
    assert fields["market_data_source_selection_policy"] == "freshest_age"
    assert fields["market_data_ws_quote_age_ms"] == 800.0
    assert fields["market_data_rest_quote_age_ms"] == 100.0
    assert enriched["curr"] == 10020


def test_market_data_enrichment_freshest_policy_keeps_younger_ws_quote():
    ws_data = {
        "curr": 10000,
        "best_ask": 10010,
        "best_bid": 9990,
        "last_ws_update_ts": 999.9,
    }
    rest_snapshot = _rest_orderbook(10020)
    rest_snapshot["rest_received_ts"] = 999.2

    enriched, fields = build_market_data_enrichment(
        ws_data=ws_data,
        rest_orderbook=rest_snapshot,
        now_ts=1000.0,
        prefer_freshest_source=True,
    )

    assert fields["market_data_freshness_state"] == FRESH_WS
    assert fields["market_data_effective_price_source"] == "ws"
    assert fields["market_data_source_selection_policy"] == "freshest_age"
    assert enriched["curr"] == 10000


def test_market_data_enrichment_absolute_ws_timestamp_overrides_constant_reported_age():
    ws_data = {
        "curr": 10000,
        "best_ask": 10010,
        "best_bid": 9990,
        "quote_age_ms": 10.0,
        "last_ws_update_ts": 995.0,
    }
    rest_snapshot = _rest_orderbook(10020)
    rest_snapshot["rest_received_ts"] = 999.9

    enriched, fields = build_market_data_enrichment(
        ws_data=ws_data,
        rest_orderbook=rest_snapshot,
        now_ts=1000.0,
        prefer_freshest_source=True,
    )

    assert fields["market_data_effective_price_source"] == "ka10004_rest_orderbook"
    assert fields["market_data_ws_quote_age_ms"] == 5000.0
    assert fields["market_data_ws_age_basis"] == "absolute_timestamp:last_ws_update_ts"
    assert fields["market_data_rest_age_basis"] == "absolute_timestamp:rest_received_ts"
    assert enriched["curr"] == 10020


def test_market_data_enrichment_reported_ws_age_without_time_basis_is_labeled_unknown():
    _enriched, fields = build_market_data_enrichment(
        ws_data={
            "curr": 10000,
            "best_ask": 10010,
            "best_bid": 9990,
            "quote_age_ms": 10.0,
        },
        now_ts=1000.0,
    )

    assert fields["market_data_freshness_state"] == FRESH_WS
    assert fields["market_data_ws_age_basis"] == "reported_age_no_time_basis:quote_age_ms"


def test_market_data_enrichment_rejects_ka10004_without_receive_timestamp_as_fresh():
    ws_data = {
        "curr": 9900,
        "best_ask": 9910,
        "best_bid": 9890,
        "last_ws_update_ts": 990.0,
        "quote_stale": True,
    }
    rest_snapshot = _rest_orderbook(10000)
    rest_snapshot.pop("rest_received_ts")

    _enriched, fields = build_market_data_enrichment(
        ws_data=ws_data,
        rest_orderbook=rest_snapshot,
        now_ts=1000.0,
    )

    assert fields["market_data_freshness_state"] == "stale"
    assert fields["market_data_orderbook_state"] == "stale"


def test_market_data_enrichment_rejects_ka10004_age_zero_without_receive_timestamp():
    rest_snapshot = _rest_orderbook(10000)
    rest_snapshot.pop("rest_received_ts")
    rest_snapshot["age_ms"] = 0

    _enriched, fields = build_market_data_enrichment(
        ws_data={"curr": 9900, "best_ask": 9910, "best_bid": 9890, "last_ws_update_ts": 990.0},
        rest_orderbook=rest_snapshot,
        now_ts=1000.0,
    )

    assert fields["market_data_rest_quote_age_ms"] == "-"
    assert fields["market_data_rest_age_basis"] == "missing_receive_timestamp"


def test_market_data_signed_tape_sell_dominated_is_negative_veto_provenance_only():
    ticks = [
        {
            "aggressor_side": "SELL",
            "signed_trade_volume": "-100",
            "rest_signed_tape_received_at": 1000.0,
            "source_timestamp": 1000.0,
        },
        {
            "aggressor_side": "SELL",
            "signed_trade_volume": "-90",
            "rest_signed_tape_received_at": 1000.0,
            "source_timestamp": 999.9,
        },
        {
            "aggressor_side": "SELL",
            "signed_trade_volume": "-80",
            "rest_signed_tape_received_at": 1000.0,
            "source_timestamp": 999.8,
        },
        {
            "aggressor_side": "BUY",
            "signed_trade_volume": "+20",
            "rest_signed_tape_received_at": 1000.0,
            "source_timestamp": 999.7,
        },
    ]

    enriched, fields = build_market_data_enrichment(
        ws_data={},
        rest_signed_ticks=ticks,
        now_ts=1000.0,
    )

    assert fields["market_data_signed_tape_state"] == SIGNED_TAPE_SELL_DOMINATED
    assert fields["market_data_signed_tape_fresh_sample_count"] == 4
    assert fields["market_data_rest_signed_tape_pressure_usable"] is False
    assert "buy_pressure_10t" not in enriched


def test_market_data_signed_tape_buy_dominated_does_not_create_buy_pressure():
    ticks = [
        {
            "aggressor_side": "BUY",
            "signed_trade_volume": "+100",
            "rest_signed_tape_received_at": 1000.0,
            "source_timestamp": 1000.0,
        },
        {
            "aggressor_side": "BUY",
            "signed_trade_volume": "+90",
            "rest_signed_tape_received_at": 1000.0,
            "source_timestamp": 999.9,
        },
        {
            "aggressor_side": "BUY",
            "signed_trade_volume": "+80",
            "rest_signed_tape_received_at": 1000.0,
            "source_timestamp": 999.8,
        },
        {
            "aggressor_side": "SELL",
            "signed_trade_volume": "-20",
            "rest_signed_tape_received_at": 1000.0,
            "source_timestamp": 999.7,
        },
    ]

    enriched, fields = build_market_data_enrichment(
        ws_data={},
        rest_signed_ticks=ticks,
        now_ts=1000.0,
    )

    assert fields["market_data_signed_tape_state"] == SIGNED_TAPE_BUY_DOMINATED
    assert fields["market_data_rest_signed_tape_pressure_usable"] is False
    assert "buy_pressure_10t" not in enriched


def test_market_data_signed_tape_stale_rows_cannot_create_negative_veto():
    ticks = [
        {
            "aggressor_side": "SELL",
            "signed_trade_volume": "-100",
            "rest_signed_tape_received_at": 999.0,
            "source_timestamp": 990.0,
        },
        {
            "aggressor_side": "SELL",
            "signed_trade_volume": "-90",
            "rest_signed_tape_received_at": 999.0,
            "source_timestamp": 990.1,
        },
        {
            "aggressor_side": "SELL",
            "signed_trade_volume": "-80",
            "rest_signed_tape_received_at": 999.0,
            "source_timestamp": 990.2,
        },
    ]

    _enriched, fields = build_market_data_enrichment(
        ws_data={},
        rest_signed_ticks=ticks,
        now_ts=1000.0,
    )

    assert fields["market_data_signed_tape_state"] == "stale"
    assert fields["market_data_signed_tape_sample_count"] == 0
    assert fields["market_data_signed_tape_stale_or_unknown_count"] == 3
    assert fields["market_data_tick_context_state"] == "missing"
    assert fields["market_data_rest_signed_tape_pressure_usable"] is False


def test_market_data_signed_tape_accepts_fresh_official_ka10084_time_shape():
    now_ts = datetime(2026, 7, 14, 10, 30, 2).timestamp()
    ticks = [
        {
            "time": value,
            "aggressor_side": "SELL",
            "signed_trade_volume": "-100",
            "rest_signed_tape_received_at": now_ts,
        }
        for value in ("103002", "103001", "103000")
    ]

    _enriched, fields = build_market_data_enrichment(
        ws_data={},
        rest_signed_ticks=ticks,
        now_ts=now_ts,
    )

    assert fields["market_data_signed_tape_state"] == SIGNED_TAPE_SELL_DOMINATED
    assert fields["market_data_signed_tape_sample_count"] == 3
    assert fields["market_data_signed_tape_age_basis"].endswith(
        "source_time:ka10084_tm"
    )
