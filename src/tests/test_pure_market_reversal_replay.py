from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from src.engine.monitoring import pure_market_reversal_replay as replay


def test_operator_selected_research_floor_is_46_unique_trading_dates():
    dates = [date(2026, 1, 1) + timedelta(days=index) for index in range(46)]

    assert replay.MIN_QUALIFIED_TRADING_DAYS == 46
    assert replay.has_research_sample_floor(dates)
    assert replay.has_research_sample_floor(dates + [dates[-1]])
    assert not replay.has_research_sample_floor(dates[:-1])


def _bar(
    minute: int,
    *,
    open_: int,
    high: int,
    low: int,
    close: int,
    volume: int = 100,
    day: date = date(2026, 8, 3),
    venue: str = "KRX",
    session: str = "KRX_REGULAR",
) -> replay.Bar:
    return replay.Bar(
        symbol="005930",
        venue=venue,
        session=session,
        timestamp=datetime.combine(day, datetime.min.time()).replace(hour=9)
        + timedelta(minutes=minute),
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
        source="test",
    )


def _policy(**overrides) -> replay.Policy:
    values = {
        "lookback_bars": 3,
        "drawdown_pct": 1.0,
        "stabilization_bars": 1,
        "reclaim_pct": 0.1,
        "max_chase_pct": 1.0,
        "rebound_volume_ratio": 0.5,
        "target_pct": 0.5,
        "stop_pct": 1.0,
        "trailing_arm_pct": 10.0,
        "trailing_drawdown_pct": 1.0,
        "max_hold_bars": 5,
    }
    values.update(overrides)
    return replay.Policy(**values)


def _entry_setup(*, ambiguous_exit: bool = False) -> list[replay.Bar]:
    exit_low = 9_700 if ambiguous_exit else 9_820
    return [
        _bar(0, open_=10_000, high=10_020, low=9_990, close=10_000),
        _bar(1, open_=9_980, high=9_990, low=9_940, close=9_950),
        _bar(2, open_=9_940, high=9_950, low=9_890, close=9_900),
        _bar(3, open_=9_900, high=9_910, low=9_800, close=9_800),
        _bar(4, open_=9_810, high=9_850, low=9_810, close=9_840, volume=120),
        _bar(5, open_=9_840, high=9_900, low=exit_low, close=9_880, volume=120),
    ]


def test_simulation_enters_only_at_next_bar_open_and_uses_completed_signal_bar():
    trades = replay.simulate_policy(_entry_setup(), _policy(), cost_pct=0.2)

    assert len(trades) == 1
    assert trades[0]["entry_signal_at"].endswith("09:04:00")
    assert trades[0]["entry_at"].endswith("09:05:00")
    assert trades[0]["entry_price"] == 9_840
    assert trades[0]["exit_reason"] == "target_limit"
    assert trades[0]["mfe_pct"] > 0


def test_same_bar_target_and_stop_is_resolved_adverse_first():
    trades = replay.simulate_policy(
        _entry_setup(ambiguous_exit=True),
        _policy(),
        cost_pct=0.2,
    )

    assert len(trades) == 1
    assert trades[0]["exit_reason"] == "stop_ambiguous_first"
    assert trades[0]["gross_profit_pct"] < 0
    assert trades[0]["mae_pct"] <= -1.0


def test_data_gap_exits_at_next_observed_open_not_prior_close():
    bars = _entry_setup()
    bars.append(
        _bar(
            10,
            open_=9_700,
            high=9_710,
            low=9_680,
            close=9_690,
        )
    )
    trades = replay.simulate_policy(
        bars,
        _policy(target_pct=10.0, stop_pct=10.0, max_hold_bars=20),
        cost_pct=0.2,
    )

    assert len(trades) == 1
    assert trades[0]["exit_reason"] == "data_gap_next_open"
    assert trades[0]["exit_at"].endswith("09:10:00")
    assert trades[0]["exit_price"] == 9_700


def test_widget_loader_consumes_market_bar_only_and_excludes_conflict(tmp_path):
    observation_dir = tmp_path / "observations"
    observation_dir.mkdir()
    row = {
        "market_venue": "KRX",
        "market_session": "KRX_REGULAR",
        "advisory": {"state": "ENTRY_READY", "entry_price_low": 1},
        "exit_advisory": {"state": "EXIT_READY"},
        "latest_completed_bar": {
            "source_time": "20260803090000",
            "open": 100,
            "high": 102,
            "low": 99,
            "close": 101,
            "volume": 50,
        },
    }
    (observation_dir / "samsung_widget_advisory_2026-08-03.jsonl").write_text(
        json.dumps(row) + "\n", encoding="utf-8"
    )

    bars, quality = replay.load_market_bars(
        widget_observation_dir=observation_dir,
        start_date=date(2026, 8, 3),
    )

    assert len(bars) == 1
    assert bars[0].close == 101
    assert quality["signal_fields_consumed"] is False
    assert quality["policy_fields_consumed"] is False


def test_conflicting_duplicate_market_bar_is_excluded(tmp_path):
    market_path = tmp_path / "market.jsonl"
    rows = []
    for close in (101, 102):
        rows.append(
            {
                "schema": "pure_market_minute_bar_v1",
                "symbol": "005930",
                "venue": "KRX",
                "session": "KRX_REGULAR",
                "source_timestamp": "20260803090000",
                "open": 100,
                "high": 103,
                "low": 99,
                "close": close,
                "volume": 50,
            }
        )
    market_path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )

    bars, quality = replay.load_market_bars(
        market_paths=[market_path],
        widget_observation_dir=None,
        start_date=date(2026, 8, 3),
    )

    assert bars == []
    assert quality["status"] == "FAIL"
    assert quality["conflict_count"] == 1


def test_opportunity_labels_are_ex_post_and_match_near_trough_entry():
    bars = []
    for minute in range(45):
        if minute < 20:
            close = 10_000 - minute * 10
        else:
            close = 9_800 + (minute - 20) * 12
        low = close - (20 if minute == 20 else 5)
        bars.append(
            _bar(
                minute,
                open_=close,
                high=close + 10,
                low=low,
                close=close,
            )
        )
    labels = replay.label_reversal_opportunities(bars)
    trough = min(labels, key=lambda row: row["trough_price"])
    trade = {
        "trade_date": trough["trade_date"],
        "venue": "KRX",
        "session": "KRX_REGULAR",
        "entry_at": (
            datetime.fromisoformat(trough["trough_at"]) + timedelta(minutes=1)
        ).isoformat(),
        "entry_price": trough["trough_price"] + 10,
        "exit_at": (
            datetime.fromisoformat(trough["trough_at"]) + timedelta(minutes=10)
        ).isoformat(),
        "exit_price": trough["forward_rebound_peak"] - 10,
        "exit_reason": "target_limit",
        "net_profit_pct": 0.2,
    }
    summary = replay.summarize_opportunity_capture([trough], [trade])

    assert summary["captured_count"] == 1
    assert summary["diagnostic_opportunity_capture_rate_pct"] == 100.0
    assert summary["avg_entry_timing_vs_trough_min"] == 1.0


def test_coverage_requires_each_expected_venue_session():
    day = date(2026, 8, 3)
    krx = [
        _bar(
            minute,
            open_=100,
            high=101,
            low=99,
            close=100,
            day=day,
        )
        for minute in range(300)
    ]
    nxt_pre_only = [
        _bar(
            minute,
            open_=100,
            high=101,
            low=99,
            close=100,
            day=day,
            venue="NXT",
            session="NXT_PREMARKET",
        )
        for minute in range(30)
    ]
    coverage = replay.assess_date_coverage(krx + nxt_pre_only)

    assert coverage["qualified_dates_by_venue"]["KRX"] == ["2026-08-03"]
    assert coverage["qualified_dates_by_venue"]["NXT"] == []
    assert coverage["excluded_dates_by_venue"]["NXT"][0]["sessions"]


def test_report_keeps_krx_nxt_separate_and_has_no_runtime_authority():
    bars = []
    for offset in range(61):
        day = date(2026, 6, 5) + timedelta(days=offset)
        for venue, session in (("KRX", "KRX_REGULAR"), ("NXT", "NXT_REGULAR")):
            bars.append(
                _bar(
                    0,
                    open_=100,
                    high=101,
                    low=99,
                    close=100,
                    day=day,
                    venue=venue,
                    session=session,
                )
            )
    report = replay.build_walk_forward_report(
        bars,
        source_quality={"status": "PASS"},
        policies=[_policy()],
        training_days=1,
        min_train_trades=1,
        min_train_dates=1,
        enforce_coverage=False,
    )

    assert set(report["cohorts"]) == {"KRX", "NXT"}
    assert report["runtime_effect"] is False
    assert report["broker_order_forbidden"] is True
    assert report["decision"] == "insufficient_for_strategy_or_runtime_judgment"
    assert report["cohorts"]["KRX"]["decision"] == "no_out_of_sample_trade_evidence"
