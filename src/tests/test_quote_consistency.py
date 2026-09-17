from __future__ import annotations

import pytest

from src.trading.market.quote_consistency import (
    ws_quote_receive_age_ms,
    build_market_data_health,
    QuoteConsistencyConfig,
    build_quote_consistency_snapshot,
    quote_input_from_rest_orderbook,
    quote_input_from_ws,
)


@pytest.mark.parametrize(
    "stamp,expected",
    [(100000, 500), (101000, -500), (True, None), ("bad", None), (float("nan"), None)],
)
def test_rest_clock_and_common_health_have_identical_age_without_future_clamp(
    stamp, expected
):
    payload = {
        "source": "ka10004_rest_orderbook",
        "stock_code": "005930",
        "request_code": "005930_NX",
        "rest_freshness_basis": "response_received_epoch_ms",
        "rest_received_ts_ms": stamp,
        "best_bid": 9990,
        "best_ask": 10010,
        "age_ms": 0,
    }
    quote = quote_input_from_rest_orderbook(payload, now_ts=100.5)
    health = build_market_data_health(payload, now_ts=100.5)
    rest = health["rest_quote"]
    assert quote.age_ms == rest["quote_receive_age_ms"] == expected
    assert rest["market_data_scope"] == "NXT"
    assert rest["trade_activity_state"] == "OBSERVATION_UNPROVEN"
    if expected is None or expected < 0:
        assert rest["quote_state"] != "fresh"
        assert not build_quote_consistency_snapshot(
            rest=quote, config=_config()
        ).safety_exit_allowed


def test_program_packet_cannot_refresh_executable_ws_book():
    ws = quote_input_from_ws(
        {
            "curr": 10000,
            "best_bid": 9990,
            "best_ask": 10010,
            "last_ws_update_ts": 100.0,
            "last_realtime_type_ts": {"0D": 90.0, "0w": 100.0},
        },
        now_ts=100.0,
    )
    assert ws.age_ms == 10000
    assert build_quote_consistency_snapshot(ws=ws, config=_config()).entry_blocked


def test_missing_depth_provenance_cannot_use_transport_timestamp():
    ws = quote_input_from_ws(
        {
            "curr": 10000,
            "last_ws_update_ts": 100.0,
            "last_realtime_type_ts": {"0w": 100.0},
        },
        now_ts=100.0,
    )
    assert ws.age_ms is None


def test_market_data_health_keeps_missing_and_cross_epoch_unproven():
    frame = {
        "last_ws_update_ts": 100.0,
        "market_data_transport_epoch": 2,
        "realtime_type_snapshots_by_route": {
            "KRX|krx": {
                "0D": {
                    "item": "005930",
                    "observed_epoch": 100.0,
                    "transport_epoch": 2,
                    "effective_venue": "KRX",
                    "market_route": "krx",
                    "orderbook": {
                        "bids": [{"price": 9990}],
                        "asks": [{"price": 10010}],
                    },
                },
                "0B": {
                    "item": "005930",
                    "observed_epoch": 85.0,
                    "transport_epoch": 1,
                    "effective_venue": "KRX",
                    "market_route": "krx",
                },
            }
        },
    }
    health = build_market_data_health(frame, now_ts=100.0)
    route = health["routes"]["KRX|krx"]
    assert route["quote_state"] == "fresh"
    assert route["trade_activity_state"] == "OBSERVATION_UNPROVEN"
    assert route["quiet_episode_count"] is None
    assert health["transport_receive_age_ms"] == 0
    assert health["decision_authority"] is False


@pytest.mark.parametrize("bad_value", [True, "2", 2.0, -1, 4, None])
def test_serialized_quiet_episode_count_requires_exact_bounded_integer(bad_value):
    from src.trading.market.quote_consistency import build_market_data_health

    quote = {
        "item": "005930",
        "market_route": "krx",
        "effective_venue": "KRX",
        "transport_epoch": 2,
        "observed_epoch": 100.0,
        "orderbook": {"bids": [{"price": 9990}], "asks": [{"price": 10010}]},
    }
    health = build_market_data_health(
        {
            "market_data_transport_epoch": 2,
            "realtime_type_snapshots_by_route": {
                "KRX|krx": {
                    "0D": quote,
                    "0B": {**quote, "observed_epoch": 70.0},
                    "quiet_tape_observation": {
                        "last_quote": 100.0,
                        "last_trade": 70.0,
                        "closed_episodes": bad_value,
                    },
                }
            },
        },
        now_ts=100.0,
    )
    route = health["routes"]["KRX|krx"]
    assert route["quote_state"] == "fresh"
    assert route["trade_activity_state"] == "OBSERVATION_UNPROVEN"
    assert route["quiet_episode_count"] is None


@pytest.mark.parametrize("field", ["0B", "0D"])
def test_boolean_route_epoch_is_not_current_transport_proof(field):
    from src.trading.market.quote_consistency import build_market_data_health

    quote = {
        "item": "005930",
        "market_route": "krx",
        "effective_venue": "KRX",
        "transport_epoch": 1,
        "observed_epoch": 100.0,
        "orderbook": {"bids": [{"price": 9990}], "asks": [{"price": 10010}]},
    }
    records = {
        "0D": dict(quote),
        "0B": {**quote, "observed_epoch": 95.0},
        "quiet_tape_observation": {
            "last_quote": 100.0,
            "last_trade": 95.0,
            "closed_episodes": 0,
        },
    }
    records[field]["transport_epoch"] = True
    health = build_market_data_health(
        {
            "market_data_transport_epoch": 1,
            "realtime_type_snapshots_by_route": {"KRX|krx": records},
        },
        now_ts=100.0,
    )
    assert health["routes"]["KRX|krx"]["trade_activity_state"] == "OBSERVATION_UNPROVEN"
    if field == "0D":
        assert health["routes"]["KRX|krx"]["quote_state"] == "unproven"
        assert health["executable_quote_receive_age_ms"] is None


def test_market_data_health_future_quote_is_not_fresh():
    health = build_market_data_health(
        {
            "market_data_transport_epoch": 2,
            "realtime_type_snapshots_by_route": {
                "KRX|krx": {"0D": {"observed_epoch": 101.0, "transport_epoch": 2}}
            },
        },
        now_ts=100.0,
    )
    assert health["routes"]["KRX|krx"]["quote_state"] == "future"


def test_future_depth_timestamp_cannot_pass_quote_consistency():
    ws = quote_input_from_ws(
        {
            "curr": 10000,
            "best_bid": 9990,
            "best_ask": 10010,
            "last_realtime_type_ts": {"0D": 101.0},
        },
        now_ts=100.0,
    )
    assert ws.age_ms == -1000
    assert build_quote_consistency_snapshot(ws=ws, config=_config()).entry_blocked


def test_exact_inline_trade_quote_remains_usable_without_fresh_depth():
    frame = {
        "best_bid": 9990,
        "best_ask": 10010,
        "last_realtime_type_ts": {"0B": 100.0},
        "last_realtime_type_item": {"0B": "005930"},
        "market_data_transport_epoch": 2,
        "realtime_type_snapshots_by_route": {
            "KRX|krx": {
                "0B": {
                    "item": "005930",
                    "observed_epoch": 100.0,
                    "transport_epoch": 2,
                    "inline_best_bid": 9990,
                    "inline_best_ask": 10010,
                }
            }
        },
    }
    assert ws_quote_receive_age_ms(frame, now_ts=100.1) < 101
    frame["realtime_type_snapshots_by_route"]["KRX|krx"]["0B"]["inline_best_bid"] = 9980
    assert ws_quote_receive_age_ms(frame, now_ts=100.1) is None


def test_serialized_quiet_observation_keeps_pure_counter_and_expiry():
    record = {
        "item": "005930",
        "market_route": "krx",
        "effective_venue": "KRX",
        "transport_epoch": 2,
        "observed_epoch": 110.0,
        "orderbook": {"bids": [{"price": 9990}], "asks": [{"price": 10010}]},
    }
    frame = {
        "market_data_transport_epoch": 2,
        "realtime_type_snapshots_by_route": {
            "KRX|krx": {
                "0D": record,
                "0B": {**record, "observed_epoch": 100.0},
                "quiet_tape_observation": {
                    "last_quote": 110.0,
                    "last_trade": 100.0,
                    "closed_episodes": 0,
                },
            }
        },
    }
    for _ in range(100):
        route = build_market_data_health(frame, now_ts=110.0)["routes"]["KRX|krx"]
        assert route["quiet_episode_count"] == 1
    expired = build_market_data_health(frame, now_ts=114.0)["routes"]["KRX|krx"]
    assert expired["trade_activity_state"] == "OBSERVATION_UNPROVEN"


@pytest.mark.parametrize(
    "route,item,venue,proven",
    [
        ("krx_nxt_integrated", "005930_AL", "UNKNOWN", True),
        ("krx_only", "005930", "UNKNOWN", False),
        ("krx_nxt_integrated", "005930", "UNKNOWN", False),
        ("krx_only", "005930", "KRX", True),
    ],
)
def test_activity_scope_is_not_underlying_integrated_exchange(
    route, item, venue, proven
):
    record = {
        "item": item,
        "market_route": route,
        "effective_venue": venue,
        "transport_epoch": 2,
        "observed_epoch": 110.0,
        "orderbook": {"bids": [{"price": 9990}], "asks": [{"price": 10010}]},
    }
    records = {
        "0D": record,
        "0B": {**record, "observed_epoch": 105.0},
        "quiet_tape_observation": {
            "last_quote": 110.0,
            "last_trade": 105.0,
            "closed_episodes": 0,
        },
    }
    frame = {
        "market_data_transport_epoch": 2,
        "realtime_type_snapshots_by_route": {"scope": records},
    }
    facts = build_market_data_health(frame, now_ts=110.0)["routes"]["scope"]
    assert facts["observation_continuity_proven"] is proven
    assert facts["effective_venue"] == venue
    assert facts["underlying_event_venue_proven"] is (proven and venue == "KRX")
    assert facts["trade_activity_state"] == (
        "RECENT_TRADE" if proven else "OBSERVATION_UNPROVEN"
    )
    # Neither companion timestamps nor cross-epoch records can prove activity.
    records["quiet_tape_observation"]["last_trade"] = 109.0
    assert (
        build_market_data_health(frame, now_ts=110.0)["routes"]["scope"][
            "observation_continuity_proven"
        ]
        is False
    )
    records["quiet_tape_observation"]["last_trade"] = 105.0
    records["0B"]["transport_epoch"] = 1
    assert (
        build_market_data_health(frame, now_ts=110.0)["routes"]["scope"][
            "observation_continuity_proven"
        ]
        is False
    )


def _ws(
    price: int,
    *,
    age_ms: int = 100,
    best_bid: int | None = None,
    best_ask: int | None = None,
):
    best_bid = best_bid if best_bid is not None else price - 10
    best_ask = best_ask if best_ask is not None else price + 10
    return quote_input_from_ws(
        {
            "curr": price,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "quote_consistency_ws_age_ms": age_ms,
        }
    )


def _rest(best_bid: int, best_ask: int, *, age_ms: int = 200, current_price: int = 0):
    return quote_input_from_rest_orderbook(
        {
            "best_bid": best_bid,
            "best_ask": best_ask,
            "rest_current_price": current_price,
            "rest_mid_price": int(round((best_bid + best_ask) / 2.0)),
            "age_ms": age_ms,
        }
    )


def _config() -> QuoteConsistencyConfig:
    return QuoteConsistencyConfig(
        max_ws_age_ms=700,
        max_rest_age_ms=1500,
        ok_gap_bps=30,
        warn_gap_bps=80,
        emergency_rest_timeout_ms=400,
        block_entry_on_divergence=True,
    )


def test_quote_consistency_ok_warning_and_diverged(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_QUOTE_CONSISTENCY_RUNTIME_ENABLED", "true")

    ok = build_quote_consistency_snapshot(
        ws=_ws(10000), rest=_rest(9980, 10020), config=_config()
    )
    assert ok.quality_state == "ok"
    assert ok.entry_blocked is False
    assert ok.executable_buy_price == 10020
    assert ok.passive_buy_price == 9980

    warning = build_quote_consistency_snapshot(
        ws=_ws(10000), rest=_rest(9920, 9960), config=_config()
    )
    assert warning.quality_state == "warning"
    assert warning.entry_blocked is False

    diverged = build_quote_consistency_snapshot(
        ws=_ws(10000), rest=_rest(9700, 9740), config=_config()
    )
    assert diverged.quality_state == "diverged"
    assert diverged.entry_blocked is True
    assert diverged.runtime_action == "block_entry_reprice_scale_in"


def test_quote_consistency_stale_missing_and_single_source(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_QUOTE_CONSISTENCY_RUNTIME_ENABLED", "true")

    ws_only = build_quote_consistency_snapshot(ws=_ws(10000), config=_config())
    assert ws_only.quality_state == "single_source"
    assert ws_only.canonical_mark_price == 10000

    stale = build_quote_consistency_snapshot(
        ws=_ws(10000, age_ms=2000),
        rest=_rest(9980, 10020, age_ms=4000),
        config=_config(),
    )
    assert stale.quality_state == "stale"
    assert stale.entry_blocked is True

    missing = build_quote_consistency_snapshot(config=_config())
    assert missing.quality_state == "missing"
    assert missing.entry_blocked is True


def test_rest_orderbook_age_prefers_received_timestamp_over_static_age_ms():
    rest = quote_input_from_rest_orderbook(
        {
            "best_bid": 9980,
            "best_ask": 10020,
            "rest_mid_price": 10000,
            "age_ms": 0,
            "bid_req_base_tm": "093001",
            "rest_received_ts_ms": 1_000_000,
        },
        now_ts=1002.0,
    )

    assert rest.age_ms == 2000.0


def test_ka10004_rest_orderbook_does_not_trust_static_age_without_received_timestamp():
    rest = quote_input_from_rest_orderbook(
        {
            "source": "ka10004_rest_orderbook",
            "best_bid": 9980,
            "best_ask": 10020,
            "rest_mid_price": 10000,
            "age_ms": 0,
            "bid_req_base_tm": "093001",
            "bid_req_base_tm_authority": "raw_not_freshness_input",
        },
        now_ts=1002.0,
    )

    assert rest.age_ms is None

    snapshot = build_quote_consistency_snapshot(rest=rest, config=_config())
    assert snapshot.quality_state == "stale"
    assert snapshot.entry_blocked is True
    assert snapshot.reason == "quote_stale"


def test_safety_exit_does_not_block_on_divergence_or_late_rest(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_QUOTE_CONSISTENCY_RUNTIME_ENABLED", "true")

    diverged = build_quote_consistency_snapshot(
        ws=_ws(10000),
        rest=_rest(9400, 9440),
        safety_exit=True,
        side="sell",
        config=_config(),
    )
    assert diverged.quality_state == "diverged"
    assert diverged.entry_blocked is False
    assert diverged.safety_exit_allowed is True
    assert diverged.executable_sell_price == 9400

    stale_rest = build_quote_consistency_snapshot(
        ws=_ws(10000),
        rest=_rest(9400, 9440, age_ms=5000),
        safety_exit=True,
        side="sell",
        config=_config(),
    )
    assert stale_rest.quality_state == "single_source"
    assert stale_rest.entry_blocked is False
    assert stale_rest.safety_exit_allowed is True
    assert stale_rest.executable_sell_price > 0
