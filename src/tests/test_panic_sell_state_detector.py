from datetime import datetime, timedelta

from src.engine.panic_sell_state_detector import (
    PanicCandle,
    PanicOrderbookMicro,
    PanicSellDetectorConfig,
    PanicSellStateDetector,
    PanicTradeFlow,
)

BASE = datetime.fromisoformat("2026-05-12T10:00:00")


def _candle(
    offset: int,
    close: float,
    *,
    open_: float | None = None,
    high: float | None = None,
    low: float | None = None,
    volume: float = 100.0,
):
    open_value = close if open_ is None else open_
    return PanicCandle(
        ts=BASE + timedelta(minutes=offset),
        open=open_value,
        high=max(high if high is not None else close, open_value, close),
        low=min(low if low is not None else close, open_value, close),
        close=close,
        volume=volume,
    )


def _trade(offset: int, *, buy: float, sell: float):
    return PanicTradeFlow(
        ts=BASE + timedelta(minutes=offset), buy_volume=buy, sell_volume=sell
    )


def _book(
    offset: int,
    *,
    bid_depth: float = 1000.0,
    ask_depth: float = 1000.0,
    spread_ratio: float = 1.0,
    ofi_z: float = 0.0,
    state: str = "neutral",
):
    return PanicOrderbookMicro(
        ts=BASE + timedelta(minutes=offset),
        best_bid=9900,
        best_ask=10000,
        bid_depth_l5=bid_depth,
        ask_depth_l5=ask_depth,
        spread_ratio=spread_ratio,
        ofi_z=ofi_z,
        qi_ewma=0.50,
        micro_state=state,
        ready=True,
        observer_healthy=True,
    )


def _config(**overrides):
    values = {
        "min_bars_required": 3,
        "short_window_bars": 1,
        "mid_window_bars": 2,
        "panic_entry_confirm_bars": 2,
        "panic_entry_confirm_window": 3,
        "recovery_confirm_bars": 2,
        "recovery_confirm_window": 4,
    }
    values.update(overrides)
    return PanicSellDetectorConfig(**values)


def _warm(detector: PanicSellStateDetector):
    detector.update(_candle(0, 100.0), _trade(0, buy=52, sell=48), _book(0))
    detector.update(_candle(1, 100.0), _trade(1, buy=52, sell=48), _book(1))


def test_price_drop_alone_does_not_confirm_panic():
    detector = PanicSellStateDetector(_config(panic_entry_confirm_bars=1))
    _warm(detector)

    signal = detector.update(
        _candle(2, 97.8, open_=100.0, high=100.1, low=97.7, volume=100),
        _trade(2, buy=52, sell=48),
        _book(2, bid_depth=1000, ask_depth=1000, spread_ratio=1.0, ofi_z=0.0),
    )

    assert signal.state == "NORMAL"
    assert signal.risk_off_advisory is False
    assert signal.allow_new_long_advisory is True


def test_composite_panic_sets_report_only_risk_off_advisory():
    detector = PanicSellStateDetector(_config())
    _warm(detector)

    first = detector.update(
        _candle(2, 97.5, open_=100.0, high=100.1, low=97.45, volume=420),
        _trade(2, buy=28, sell=72),
        _book(
            2,
            bid_depth=540,
            ask_depth=1400,
            spread_ratio=2.0,
            ofi_z=-2.7,
            state="bearish",
        ),
    )
    second = detector.update(
        _candle(3, 97.0, open_=97.6, high=97.7, low=96.9, volume=430),
        _trade(3, buy=27, sell=73),
        _book(
            3,
            bid_depth=500,
            ask_depth=1500,
            spread_ratio=2.1,
            ofi_z=-2.8,
            state="bearish",
        ),
    )

    assert first.state == "PANIC_SELL"
    assert second.internal_state == "PANIC_ACTIVE"
    assert second.risk_off_advisory is True
    assert second.allow_new_long_advisory is False
    assert second.panic_entered is True
    assert "sell_ratio_high" in second.reasons
    assert "ofi_panic" in second.reasons


def test_missing_orderbook_is_degraded_not_silent():
    detector = PanicSellStateDetector(_config(panic_entry_confirm_bars=1))
    _warm(detector)

    signal = detector.update(
        _candle(2, 97.3, open_=100.0, high=100.1, low=97.25, volume=500),
        _trade(2, buy=24, sell=76),
        None,
    )

    assert "orderbook_missing_degraded" in signal.reasons
    assert signal.confidence < 1.0
    assert signal.metrics["orderbook_missing"] is True


def test_ofi_cusum_is_report_only_metric_not_required_for_state():
    detector = PanicSellStateDetector(_config(panic_entry_confirm_bars=1))
    detector.update(_candle(0, 100.0), _trade(0, buy=52, sell=48), _book(0, ofi_z=0.0))
    detector.update(_candle(1, 100.0), _trade(1, buy=52, sell=48), _book(1, ofi_z=0.0))
    detector.update(_candle(2, 99.9), _trade(2, buy=51, sell=49), _book(2, ofi_z=0.1))

    signal = detector.update(
        _candle(3, 99.8, volume=105),
        _trade(3, buy=50, sell=50),
        _book(3, spread_ratio=1.0, ofi_z=-3.2),
    )

    assert signal.state == "NORMAL"
    assert signal.metrics["ofi_cusum_direction"] == "negative"
    assert signal.metrics["ofi_cusum_triggered"] is True
    assert signal.metrics["micro_consensus_pass"] is False


def test_single_green_rebound_does_not_confirm_recovery_when_sell_flow_stays_bad():
    detector = PanicSellStateDetector(_config())
    _warm(detector)
    detector.update(
        _candle(2, 97.5, open_=100.0, high=100.1, low=97.45, volume=420),
        _trade(2, buy=28, sell=72),
        _book(
            2,
            bid_depth=540,
            ask_depth=1400,
            spread_ratio=2.0,
            ofi_z=-2.7,
            state="bearish",
        ),
    )
    detector.update(
        _candle(3, 97.0, open_=97.6, high=97.7, low=96.9, volume=430),
        _trade(3, buy=27, sell=73),
        _book(
            3,
            bid_depth=500,
            ask_depth=1500,
            spread_ratio=2.1,
            ofi_z=-2.8,
            state="bearish",
        ),
    )

    signal = detector.update(
        _candle(4, 97.6, open_=97.0, high=97.7, low=97.0, volume=300),
        _trade(4, buy=30, sell=70),
        _book(
            4,
            bid_depth=430,
            ask_depth=1550,
            spread_ratio=2.0,
            ofi_z=-1.8,
            state="bearish",
        ),
    )

    assert signal.recovery_confirmed is False
    assert signal.state == "PANIC_SELL"
    assert signal.risk_off_advisory is True


def test_recovery_requires_persistent_microstructure_improvement_and_remains_advisory():
    detector = PanicSellStateDetector(_config())
    _warm(detector)
    detector.update(
        _candle(2, 97.5, open_=100.0, high=100.1, low=97.45, volume=420),
        _trade(2, buy=28, sell=72),
        _book(
            2,
            bid_depth=540,
            ask_depth=1400,
            spread_ratio=2.0,
            ofi_z=-2.7,
            state="bearish",
        ),
    )
    detector.update(
        _candle(3, 97.0, open_=97.6, high=97.7, low=96.9, volume=430),
        _trade(3, buy=27, sell=73),
        _book(
            3,
            bid_depth=500,
            ask_depth=1500,
            spread_ratio=2.1,
            ofi_z=-2.8,
            state="bearish",
        ),
    )

    watch = detector.update(
        _candle(4, 98.2, open_=97.2, high=98.4, low=97.05, volume=380),
        _trade(4, buy=45, sell=55),
        _book(
            4,
            bid_depth=760,
            ask_depth=950,
            spread_ratio=1.20,
            ofi_z=-0.2,
            state="neutral",
        ),
    )
    confirmed = detector.update(
        _candle(5, 98.6, open_=98.1, high=98.8, low=97.2, volume=390),
        _trade(5, buy=48, sell=52),
        _book(
            5,
            bid_depth=820,
            ask_depth=900,
            spread_ratio=1.15,
            ofi_z=0.1,
            state="bullish",
        ),
    )

    assert watch.state == "RECOVERY_WATCH"
    assert watch.allow_new_long_advisory is False
    assert confirmed.state == "RECOVERY_CONFIRMED"
    assert confirmed.recovery_confirmed is True
    assert confirmed.risk_off_advisory is False
    assert confirmed.allow_new_long_advisory is True
