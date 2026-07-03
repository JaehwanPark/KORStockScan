from __future__ import annotations

from src.trading.market.quote_consistency import (
    QuoteConsistencyConfig,
    build_quote_consistency_snapshot,
    quote_input_from_rest_orderbook,
    quote_input_from_ws,
)


def _ws(price: int, *, age_ms: int = 100, best_bid: int | None = None, best_ask: int | None = None):
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

    ok = build_quote_consistency_snapshot(ws=_ws(10000), rest=_rest(9980, 10020), config=_config())
    assert ok.quality_state == "ok"
    assert ok.entry_blocked is False
    assert ok.executable_buy_price == 10020
    assert ok.passive_buy_price == 9980

    warning = build_quote_consistency_snapshot(ws=_ws(10000), rest=_rest(9920, 9960), config=_config())
    assert warning.quality_state == "warning"
    assert warning.entry_blocked is False

    diverged = build_quote_consistency_snapshot(ws=_ws(10000), rest=_rest(9700, 9740), config=_config())
    assert diverged.quality_state == "diverged"
    assert diverged.entry_blocked is True
    assert diverged.runtime_action == "block_entry_reprice_scale_in"


def test_quote_consistency_stale_missing_and_single_source(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_QUOTE_CONSISTENCY_RUNTIME_ENABLED", "true")

    ws_only = build_quote_consistency_snapshot(ws=_ws(10000), config=_config())
    assert ws_only.quality_state == "single_source"
    assert ws_only.canonical_mark_price == 10000

    stale = build_quote_consistency_snapshot(ws=_ws(10000, age_ms=2000), rest=_rest(9980, 10020, age_ms=4000), config=_config())
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
            "rest_received_ts_ms": 1_000_000,
        },
        now_ts=1002.0,
    )

    assert rest.age_ms == 2000.0


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
