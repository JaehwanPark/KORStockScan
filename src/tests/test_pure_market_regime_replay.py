from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta

import pytest

from src.engine.monitoring import pure_market_regime_replay as regime
from src.engine.monitoring import pure_market_reversal_replay as base


def _bar(
    minute: int,
    close: int,
    *,
    venue: str = "KRX",
    session: str = "KRX_REGULAR",
    symbol: str = "005930",
) -> base.Bar:
    timestamp = datetime(2026, 8, 11, 9, 0) + timedelta(minutes=minute)
    return base.Bar(
        symbol=symbol,
        venue=venue,
        session=session,
        timestamp=timestamp,
        open=close,
        high=close + 10,
        low=close - 10,
        close=close,
        volume=100,
        source="test",
    )


def _policy() -> base.Policy:
    return base.Policy(
        lookback_bars=3,
        drawdown_pct=1.0,
        stabilization_bars=1,
        reclaim_pct=0.1,
        max_chase_pct=1.0,
        rebound_volume_ratio=0.5,
        target_pct=0.5,
        stop_pct=1.0,
        trailing_arm_pct=10.0,
        trailing_drawdown_pct=1.0,
        max_hold_bars=5,
    )


def test_observed_1009_inflection_is_bullish_transition_not_strong_trend():
    state = regime._raw_regime(
        {
            "stock_return_3m_pct": 0.2169,
            "stock_return_5m_pct": 0.2169,
            "stock_return_15m_pct": -0.2160,
            "kospi_return_3m_pct": 0.0423,
            "kospi_return_5m_pct": -0.0155,
            "kospi_return_15m_pct": -0.5769,
            "relative_return_3m_pct_point": 0.1746,
            "stock_vs_session_vwap_bp": -5.0,
        }
    )

    assert state == "BULLISH_TRANSITION"


def test_early_joint_decline_is_weak_downtrend():
    state = regime._raw_regime(
        {
            "stock_return_3m_pct": -1.08,
            "stock_return_5m_pct": -0.87,
            "stock_return_15m_pct": None,
            "kospi_return_3m_pct": -0.83,
            "kospi_return_5m_pct": -0.34,
            "kospi_return_15m_pct": None,
            "relative_return_3m_pct_point": -0.25,
            "stock_vs_session_vwap_bp": -25.0,
        }
    )

    assert state == "WEAK_DOWNTREND"


def test_regime_assignment_is_unchanged_by_future_bars():
    stock = [_bar(i, 10_000 - i * 10) for i in range(21)]
    kospi = [_bar(i, 300_000 - i * 100, symbol="KOSPI") for i in range(21)]
    before = regime.classify_causal_regimes(stock, kospi)
    key = ("KRX", "KRX_REGULAR", stock[18].timestamp)

    stock.extend(_bar(i, 11_000 + i * 100) for i in range(21, 26))
    kospi.extend(_bar(i, 310_000 + i * 100, symbol="KOSPI") for i in range(21, 26))
    after = regime.classify_causal_regimes(stock, kospi)

    assert before[key] == after[key]


def test_window_return_requires_exact_elapsed_minute_boundary():
    current = _bar(5, 10_100)
    with_gap = {_bar(1, 10_000).timestamp: _bar(1, 10_000)}

    assert regime._window_return(current, with_gap, 3) is None

    exact_prior = _bar(2, 10_000)
    with_gap[exact_prior.timestamp] = exact_prior
    assert regime._window_return(current, with_gap, 3) == pytest.approx(1.0)


def test_same_timestamp_krx_and_nxt_regimes_have_distinct_keys():
    krx = [_bar(i, 10_000 - i * 10) for i in range(20)]
    nxt = [
        _bar(
            i,
            10_000 + i * 10,
            venue="NXT",
            session="NXT_REGULAR",
        )
        for i in range(20)
    ]
    kospi = [_bar(i, 300_000 - i * 100, symbol="KOSPI") for i in range(20)]
    classified = regime.classify_causal_regimes(krx + nxt, kospi)
    timestamp = krx[-1].timestamp

    assert ("KRX", "KRX_REGULAR", timestamp) in classified
    assert ("NXT", "NXT_REGULAR", timestamp) in classified
    assert (
        classified[("KRX", "KRX_REGULAR", timestamp)]
        != classified[("NXT", "NXT_REGULAR", timestamp)]
    )


def test_entry_mode_is_routed_by_signal_time_regime():
    bars = [
        base.Bar(
            symbol="005930",
            venue="KRX",
            session="KRX_REGULAR",
            timestamp=datetime(2026, 8, 11, 9, minute),
            open=open_,
            high=high,
            low=low,
            close=close,
            volume=volume,
            source="test",
        )
        for minute, open_, high, low, close, volume in [
            (0, 10_000, 10_020, 9_990, 10_000, 100),
            (1, 9_980, 9_990, 9_940, 9_950, 100),
            (2, 9_940, 9_950, 9_890, 9_900, 100),
            (3, 9_900, 9_910, 9_800, 9_800, 100),
            (4, 9_810, 9_850, 9_810, 9_840, 110),
            (5, 9_840, 9_900, 9_820, 9_880, 120),
        ]
    ]
    weak = {bar.timestamp: "WEAK_DOWNTREND" for bar in bars}

    blocked = base.simulate_policy(
        bars,
        _policy(),
        cost_pct=0.2,
        regime_by_timestamp=weak,
        allowed_entry_regimes={"BULLISH_TRANSITION", "STRONG_UPTREND"},
        strategy_mode="confirmed_recovery",
    )
    admitted = base.simulate_policy(
        bars,
        _policy(),
        cost_pct=0.2,
        regime_by_timestamp=weak,
        allowed_entry_regimes={"WEAK_DOWNTREND"},
        strategy_mode="capitulation_probe",
    )

    assert blocked == []
    assert len(admitted) == 1
    assert admitted[0]["entry_regime"] == "WEAK_DOWNTREND"
    assert admitted[0]["strategy_mode"] == "capitulation_probe"


def test_controller_rejects_overlapping_mode_positions():
    common = {
        "trade_date": date(2026, 8, 11).isoformat(),
        "venue": "KRX",
        "session": "KRX_REGULAR",
        "exit_at": datetime(2026, 8, 11, 9, 10).isoformat(),
    }
    trades = [
        {
            **common,
            "entry_at": datetime(2026, 8, 11, 9, 5).isoformat(),
            "strategy_mode": "confirmed_recovery",
        },
        {
            **common,
            "entry_at": datetime(2026, 8, 11, 9, 7).isoformat(),
            "strategy_mode": "capitulation_probe",
        },
    ]

    accepted = regime._merge_non_overlapping(trades)

    assert len(accepted) == 1


def test_confirmed_recovery_exits_next_open_after_bearish_transition():
    bars = [
        base.Bar(
            symbol="005930",
            venue="KRX",
            session="KRX_REGULAR",
            timestamp=datetime(2026, 8, 11, 9, minute),
            open=open_,
            high=high,
            low=low,
            close=close,
            volume=100,
            source="test",
        )
        for minute, open_, high, low, close in [
            (0, 10_000, 10_020, 9_990, 10_000),
            (1, 9_980, 9_990, 9_940, 9_950),
            (2, 9_940, 9_950, 9_890, 9_900),
            (3, 9_900, 9_910, 9_800, 9_800),
            (4, 9_810, 9_850, 9_810, 9_840),
            (5, 9_840, 9_900, 9_820, 9_880),
            (6, 9_880, 10_000, 9_870, 9_980),
            (7, 9_970, 9_980, 9_900, 9_910),
            (8, 9_905, 9_920, 9_880, 9_890),
            (9, 9_885, 9_900, 9_860, 9_870),
        ]
    ]
    regimes = {bar.timestamp: "BULLISH_TRANSITION" for bar in bars}
    regimes[bars[7].timestamp] = "BEARISH_TRANSITION"
    regimes[bars[8].timestamp] = "BEARISH_TRANSITION"

    trades = base.simulate_policy(
        bars,
        replace(_policy(), target_pct=10.0, max_hold_bars=20),
        cost_pct=0.2,
        regime_by_timestamp=regimes,
        allowed_entry_regimes={"BULLISH_TRANSITION"},
        exit_regimes={"BEARISH_TRANSITION"},
        exit_regime_confirmations=2,
        strategy_mode="confirmed_recovery",
    )

    assert len(trades) == 1
    assert trades[0]["exit_reason"] == "regime_transition_next_open"
    assert trades[0]["exit_at"] == bars[9].timestamp.isoformat()
    assert trades[0]["exit_price"] == float(bars[9].open)
