from datetime import datetime, timedelta

from src.engine.panic_buying_state_detector import (
    PanicBuyingCandle,
    PanicBuyingDetectorConfig,
    PanicBuyingOrderbookMicro,
    PanicBuyingStateDetector,
    PanicBuyingTradeFlow,
    summarize_microstructure_detector_from_events,
)


BASE = datetime.fromisoformat("2026-05-13T10:00:00")


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
    return PanicBuyingCandle(
        ts=BASE + timedelta(minutes=offset),
        open=open_value,
        high=max(high if high is not None else close, open_value, close),
        low=min(low if low is not None else close, open_value, close),
        close=close,
        volume=volume,
    )


def _trade(offset: int, *, buy: float, sell: float):
    return PanicBuyingTradeFlow(ts=BASE + timedelta(minutes=offset), buy_volume=buy, sell_volume=sell)


def _book(
    offset: int,
    *,
    bid_depth: float = 1000.0,
    ask_depth: float = 1000.0,
    spread_ratio: float = 1.0,
    ofi_z: float = 0.0,
    ask_drop: float | None = None,
    ask_refill: float | None = None,
    bid_support: float | None = None,
    state: str = "neutral",
):
    return PanicBuyingOrderbookMicro(
        ts=BASE + timedelta(minutes=offset),
        best_bid=9900,
        best_ask=10000,
        bid_depth_l5=bid_depth,
        ask_depth_l5=ask_depth,
        spread_ratio=spread_ratio,
        ask_depth_drop_ratio=ask_drop,
        ask_depth_refill_ratio=ask_refill,
        bid_depth_support_ratio=bid_support,
        ofi_z=ofi_z,
        qi_ewma=0.55,
        micro_state=state,
        ready=True,
        observer_healthy=True,
    )


def _config(**overrides):
    values = {
        "min_bars_required": 3,
        "short_window_bars": 1,
        "mid_window_bars": 2,
        "panic_buy_confirm_bars": 2,
        "panic_buy_confirm_window": 3,
        "exhaustion_confirm_bars": 2,
        "exhaustion_confirm_window": 4,
    }
    values.update(overrides)
    return PanicBuyingDetectorConfig(**values)


def _warm(detector: PanicBuyingStateDetector):
    detector.update(_candle(0, 100.0), _trade(0, buy=52, sell=48), _book(0))
    detector.update(_candle(1, 100.0), _trade(1, buy=52, sell=48), _book(1))


def _enter_panic_buy(detector: PanicBuyingStateDetector):
    _warm(detector)
    detector.update(
        _candle(2, 102.6, open_=100.0, high=102.8, low=99.9, volume=430),
        _trade(2, buy=76, sell=24),
        _book(2, bid_depth=1300, ask_depth=520, spread_ratio=2.0, ofi_z=3.0, ask_drop=0.48, state="bullish"),
    )
    return detector.update(
        _candle(3, 103.2, open_=102.5, high=103.4, low=102.4, volume=440),
        _trade(3, buy=75, sell=25),
        _book(3, bid_depth=1350, ask_depth=500, spread_ratio=2.1, ofi_z=3.1, ask_drop=0.50, state="bullish"),
    )


def test_price_rise_alone_does_not_confirm_panic_buying():
    detector = PanicBuyingStateDetector(_config(panic_buy_confirm_bars=1))
    _warm(detector)

    signal = detector.update(
        _candle(2, 102.0, open_=100.0, high=102.1, low=99.9, volume=100),
        _trade(2, buy=53, sell=47),
        _book(2, spread_ratio=1.0, ofi_z=0.0, ask_drop=0.0),
    )

    assert signal.state == "NORMAL"
    assert signal.allow_tp_override is False
    assert signal.allow_runner is False


def test_composite_panic_buying_sets_report_only_runner_flags():
    detector = PanicBuyingStateDetector(_config())

    signal = _enter_panic_buy(detector)

    assert signal.state == "PANIC_BUY"
    assert signal.internal_state == "PANIC_BUY_ACTIVE"
    assert signal.panic_buy_entered is True
    assert signal.allow_tp_override is True
    assert signal.allow_runner is True
    assert "buy_ratio_high" in signal.reasons
    assert "ofi_buy_pressure" in signal.reasons


def test_missing_orderbook_is_degraded_not_silent():
    detector = PanicBuyingStateDetector(_config(panic_buy_confirm_bars=1))
    _warm(detector)

    signal = detector.update(
        _candle(2, 102.6, open_=100.0, high=102.8, low=99.9, volume=430),
        _trade(2, buy=76, sell=24),
        None,
    )

    assert "orderbook_missing_degraded" in signal.reasons
    assert signal.confidence < 1.0
    assert signal.metrics["orderbook_missing"] is True
    assert signal.panic_buy_score <= 0.82


def test_ofi_cusum_is_report_only_metric_not_required_for_state():
    detector = PanicBuyingStateDetector(_config(panic_buy_confirm_bars=1))
    detector.update(_candle(0, 100.0), _trade(0, buy=52, sell=48), _book(0, ofi_z=0.0))
    detector.update(_candle(1, 100.0), _trade(1, buy=52, sell=48), _book(1, ofi_z=0.0))
    detector.update(_candle(2, 100.1), _trade(2, buy=53, sell=47), _book(2, ofi_z=-0.1))

    signal = detector.update(
        _candle(3, 100.2, volume=105),
        _trade(3, buy=54, sell=46),
        _book(3, spread_ratio=1.0, ofi_z=3.2, ask_drop=0.0, bid_support=1.0),
    )

    assert signal.state == "NORMAL"
    assert signal.metrics["ofi_cusum_direction"] == "positive"
    assert signal.metrics["ofi_cusum_triggered"] is True
    assert signal.metrics["micro_consensus_pass"] is False


def test_microstructure_summary_exposes_static_threshold_contract():
    events = []
    for offset, close in enumerate([100.0, 100.1, 100.2]):
        events.append(
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "orderbook_stability_observed",
                "stock_code": "000001",
                "stock_name": "테스트종목",
                "record_id": 1,
                "emitted_at": (BASE + timedelta(minutes=offset)).isoformat(timespec="seconds"),
                "fields": {
                    "curr_price": close,
                    "volume": 100,
                    "buy_exec_volume": 52,
                    "sell_exec_volume": 48,
                    "best_bid": 9900,
                    "best_ask": 10000,
                },
            }
        )

    summary = summarize_microstructure_detector_from_events(events, as_of=BASE + timedelta(minutes=3))

    assert summary["threshold_mode"] == "static_fallback"
    assert summary["threshold_contract"]["decision_authority"] == "source_quality_only"
    assert summary["threshold_contract"]["runtime_effect"] == "report_only_no_mutation"
    assert "panic_buy_entry_score_threshold" in summary["threshold_contract"]["static_fallback_values"]
    assert "runtime_threshold_apply" in summary["threshold_contract"]["forbidden_uses"]


def test_microstructure_summary_carries_input_provenance_diagnostics():
    summary = summarize_microstructure_detector_from_events(
        [],
        as_of=BASE + timedelta(minutes=3),
        input_provenance={
            "input_universe": "entry_observation_only",
            "excluded_holding_row_count": 2,
            "excluded_exit_sell_row_count": 1,
        },
    )

    assert summary["evaluated_symbol_count"] == 0
    assert summary["input_provenance"]["input_universe"] == "entry_observation_only"
    assert summary["input_provenance"]["excluded_holding_row_count"] == 2
    assert summary["input_provenance"]["excluded_exit_sell_row_count"] == 1


def test_single_small_red_bar_does_not_confirm_exhaustion_when_buy_flow_stays_strong():
    detector = PanicBuyingStateDetector(_config())
    _enter_panic_buy(detector)

    signal = detector.update(
        _candle(4, 103.0, open_=103.2, high=103.5, low=102.9, volume=390),
        _trade(4, buy=72, sell=28),
        _book(4, bid_depth=1400, ask_depth=460, spread_ratio=1.7, ofi_z=2.5, ask_drop=0.42, state="bullish"),
    )

    assert signal.exhaustion_confirmed is False
    assert signal.state == "PANIC_BUY"
    assert signal.allow_runner is True


def test_exhaustion_requires_persistent_m_of_n_confirmation():
    detector = PanicBuyingStateDetector(_config())
    _enter_panic_buy(detector)

    watch = detector.update(
        _candle(4, 102.7, open_=103.3, high=103.35, low=102.4, volume=430),
        _trade(4, buy=57, sell=43),
        _book(4, bid_depth=1100, ask_depth=900, spread_ratio=1.25, ofi_z=0.2, ask_refill=0.80, state="neutral"),
    )
    exhausted = detector.update(
        _candle(5, 102.4, open_=102.9, high=103.1, low=102.1, volume=420),
        _trade(5, buy=55, sell=45),
        _book(5, bid_depth=1050, ask_depth=950, spread_ratio=1.20, ofi_z=0.0, ask_refill=0.85, state="neutral"),
    )

    assert watch.state == "EXHAUSTION_WATCH"
    assert watch.tighten_trailing_stop is True
    assert exhausted.state == "BUYING_EXHAUSTED"
    assert exhausted.force_exit_runner is True


def test_exhaustion_candidate_returns_to_active_on_rebreak():
    detector = PanicBuyingStateDetector(_config(exhaustion_confirm_bars=3))
    _enter_panic_buy(detector)
    watch = detector.update(
        _candle(4, 102.7, open_=103.3, high=103.35, low=102.4, volume=430),
        _trade(4, buy=57, sell=43),
        _book(4, bid_depth=1100, ask_depth=900, spread_ratio=1.25, ofi_z=0.2, ask_refill=0.80, state="neutral"),
    )
    resumed = detector.update(
        _candle(5, 104.0, open_=103.0, high=104.3, low=102.9, volume=450),
        _trade(5, buy=76, sell=24),
        _book(5, bid_depth=1400, ask_depth=480, spread_ratio=2.0, ofi_z=3.2, ask_drop=0.50, state="bullish"),
    )

    assert watch.state == "EXHAUSTION_WATCH"
    assert resumed.state == "PANIC_BUY"
    assert resumed.allow_tp_override is True
