from __future__ import annotations

from datetime import datetime, timedelta

from src.engine.monitoring.samsung_widget_advisory import MinuteBar
from src.engine.monitoring.samsung_widget_contract import KST
from src.engine.monitoring.widget_symbol_runtime_collector import (
    EpisodeState,
    WidgetSymbolRuntimeCollector,
    _advance_support_break_count,
    _source_quality,
)


def _bar(minute: int, open_: int, high: int, low: int, close: int, volume: int):
    return MinuteBar(
        source_time=f"2026081211{minute:02d}00",
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
    )


def test_entry_candidate_uses_symbol_policy_reclaim_completed_bar_and_fresh_bbo():
    bars = [_bar(index, 10_000, 10_010, 9_990, 10_000, 100) for index in range(30)]
    bars[-5] = _bar(25, 9_920, 9_930, 9_900, 9_910, 100)
    bars[-4] = _bar(26, 9_910, 9_920, 9_890, 9_900, 100)
    bars[-3] = _bar(27, 9_970, 9_980, 9_900, 9_920, 100)
    bars[-2] = _bar(28, 9_920, 9_950, 9_910, 9_940, 100)
    bars[-1] = _bar(29, 9_940, 9_960, 9_930, 9_950, 150)
    policy = {
        "signal_policy": {
            "segment_start_time": "10:30:00",
            "segment_end_time": "13:30:00",
            "lookback_bars": 15,
            "drawdown_pct": 0.5,
            "near_low_pct": 0.5,
            "reclaim_ticks": 1,
            "setup_valid_bars": 5,
            "target_bps": 50,
        }
    }

    candidate = WidgetSymbolRuntimeCollector._entry_candidate(
        bars=bars,
        current_price=9_950,
        bbo={"best_bid": 9_940, "best_ask": 9_950, "age_sec": 1.0},
        policy=policy,
        episode=EpisodeState(trade_date="2026-08-12"),
        observed_at=datetime(2026, 8, 12, 11, 30, tzinfo=KST),
    )

    assert candidate is not None
    assert candidate["state"] == "ENTRY_READY"
    assert candidate["structural_support"] == 9_900
    assert candidate["entry_price_low"] <= candidate["entry_price_high"]


def test_entry_candidate_blocks_stale_or_wide_bbo_and_active_episode():
    bars = [_bar(index, 10_000, 10_010, 9_990, 10_000, 100) for index in range(30)]
    policy = {
        "signal_policy": {
            "segment_start_time": "10:30:00",
            "segment_end_time": "13:30:00",
            "lookback_bars": 15,
            "drawdown_pct": 0.5,
            "near_low_pct": 0.5,
            "reclaim_ticks": 1,
            "setup_valid_bars": 5,
            "target_bps": 50,
        }
    }
    now = datetime(2026, 8, 12, 11, 30, tzinfo=KST)

    assert (
        WidgetSymbolRuntimeCollector._entry_candidate(
            bars=bars,
            current_price=10_000,
            bbo={"best_bid": 9_900, "best_ask": 10_000, "age_sec": 36.0},
            policy=policy,
            episode=EpisodeState(trade_date="2026-08-12"),
            observed_at=now,
        )
        is None
    )
    active = EpisodeState(trade_date="2026-08-12", active=True)
    assert (
        WidgetSymbolRuntimeCollector._entry_candidate(
            bars=bars,
            current_price=10_000,
            bbo={"best_bid": 9_990, "best_ask": 10_000, "age_sec": 1.0},
            policy=policy,
            episode=active,
            observed_at=now + timedelta(seconds=1),
        )
        is None
    )


def test_support_break_confirmation_advances_once_per_completed_bar():
    episode = EpisodeState(trade_date="2026-08-12", active=True, support=10_000)
    first = _bar(28, 9_990, 10_000, 9_980, 9_990, 100)
    second = _bar(29, 9_980, 9_990, 9_970, 9_980, 100)

    _advance_support_break_count(episode, first)
    _advance_support_break_count(episode, first)
    assert episode.support_break_count == 1

    _advance_support_break_count(episode, second)
    assert episode.support_break_count == 2


def test_source_quality_blocks_stale_completed_bar_or_missing_bbo():
    now = datetime(2026, 8, 12, 11, 30, 30, tzinfo=KST)
    fresh = _bar(29, 9_980, 9_990, 9_970, 9_980, 100)

    assert _source_quality(
        latest=fresh,
        bbo={"best_bid": 9_970, "best_ask": 9_980, "age_sec": 0.0},
        observed_at=now,
    ) == ("PASS", ())
    status, reasons = _source_quality(
        latest=_bar(20, 9_980, 9_990, 9_970, 9_980, 100),
        bbo={"best_bid": None, "best_ask": None, "age_sec": 40.0},
        observed_at=now,
    )
    assert status == "BLOCKED"
    assert set(reasons) == {"completed_1m_stale", "bbo_invalid", "bbo_stale"}
