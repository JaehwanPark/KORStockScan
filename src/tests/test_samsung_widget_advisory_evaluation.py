from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from src.engine.monitoring import samsung_widget_advisory_evaluation as evaluation

KST = ZoneInfo("Asia/Seoul")


def _row(
    observed_at: datetime,
    price: int,
    *,
    state: str = "WATCH",
    entry_high: int | None = None,
    invalidation: int | None = None,
    high: int | None = None,
    low: int | None = None,
    bar_start: datetime | None = None,
    observation_kind: str = "minute_summary",
    line_number: int = 1,
    market_session: str = "KRX_REGULAR",
    market_venue: str = "KRX",
):
    return {
        "observed_at_kst": observed_at.isoformat(),
        "current_price": price,
        "market_session": market_session,
        "market_venue": market_venue,
        "observation_kind": observation_kind,
        "advisory": {
            "state": state,
            "entry_price_high": entry_high,
            "invalidation_price": invalidation,
        },
        "_observed_at": observed_at,
        "_current_price": price,
        "_bar_start": bar_start,
        "_bar_high": high or price,
        "_bar_low": low or price,
        "_line_number": line_number,
    }


def test_daily_evaluation_records_mfe_mae_and_first_hit_without_real_pnl():
    start = datetime(2026, 8, 3, 9, 10, tzinfo=KST)
    rows = [
        _row(
            start,
            100_000,
            state="ENTRY_READY",
            entry_high=100_000,
            invalidation=99_700,
            observation_kind="state_transition",
        ),
        _row(
            start + timedelta(minutes=1),
            100_200,
            high=100_300,
            low=100_100,
            bar_start=start,
            line_number=2,
        ),
        _row(
            start + timedelta(minutes=2),
            100_600,
            high=100_700,
            low=100_150,
            bar_start=start + timedelta(minutes=1),
            line_number=3,
        ),
        _row(
            start + timedelta(minutes=3),
            99_600,
            high=100_000,
            low=99_500,
            bar_start=start + timedelta(minutes=2),
            line_number=4,
        ),
        _row(start + timedelta(minutes=10), 100_100, line_number=5),
    ]

    report = evaluation.build_daily_evaluation(rows, target_date=date(2026, 8, 3))

    assert report["status"] == "observed"
    assert report["actionable_signal_count"] == 1
    horizon_3 = next(row for row in report["outcomes"] if row["horizon_minutes"] == 3)
    assert horizon_3["mfe_pct"] == 0.7
    assert horizon_3["mae_pct"] == -0.5
    assert horizon_3["first_hit"] == "target_first"
    assert horizon_3["market_venue"] == "KRX"
    assert horizon_3["actual_order_submitted"] is False
    assert report["metric_contract"]["forbidden_uses"]


def test_immature_horizon_is_not_counted():
    start = datetime(2026, 8, 3, 19, 59, tzinfo=KST)
    rows = [
        _row(
            start,
            100_000,
            state="ENTRY_CAUTION",
            entry_high=100_000,
            invalidation=99_700,
            observation_kind="state_transition",
        ),
        _row(start + timedelta(minutes=1), 100_100, line_number=2),
    ]
    report = evaluation.build_daily_evaluation(rows, target_date=date(2026, 8, 3))
    assert {row["horizon_minutes"] for row in report["outcomes"]} == {1}


def test_minute_summary_does_not_duplicate_actionable_signal():
    start = datetime(2026, 8, 3, 9, 10, tzinfo=KST)
    rows = [
        _row(
            start,
            100_000,
            state="ENTRY_READY",
            entry_high=100_000,
            observation_kind="state_transition",
        ),
        _row(
            start + timedelta(minutes=1),
            100_100,
            state="ENTRY_READY",
            entry_high=100_100,
            observation_kind="minute_summary",
            line_number=2,
        ),
        _row(start + timedelta(minutes=2), 100_200, line_number=3),
    ]

    report = evaluation.build_daily_evaluation(rows, target_date=start.date())

    assert report["actionable_signal_count"] == 1


def test_completed_bar_that_started_before_signal_is_not_future_mfe():
    signal = datetime(2026, 8, 3, 9, 10, 5, tzinfo=KST)
    rows = [
        _row(
            signal,
            100_000,
            state="ENTRY_READY",
            entry_high=100_000,
            observation_kind="state_transition",
        ),
        _row(
            signal + timedelta(seconds=55),
            100_100,
            high=101_000,
            low=99_000,
            bar_start=signal.replace(second=0),
            line_number=2,
        ),
        _row(signal + timedelta(minutes=1), 100_200, line_number=3),
    ]

    report = evaluation.build_daily_evaluation(rows, target_date=signal.date())
    horizon_1 = next(row for row in report["outcomes"] if row["horizon_minutes"] == 1)

    assert horizon_1["max_price"] == 100_200
    assert horizon_1["min_price"] == 100_100


def test_evaluation_never_mixes_krx_signal_with_nxt_aftermarket_prices():
    signal = datetime(2026, 8, 3, 15, 29, tzinfo=KST)
    rows = [
        _row(
            signal,
            100_000,
            state="ENTRY_READY",
            entry_high=100_000,
            observation_kind="state_transition",
        ),
        _row(
            datetime(2026, 8, 3, 15, 40, tzinfo=KST),
            101_000,
            market_session="NXT_AFTERMARKET",
            market_venue="NXT",
            line_number=2,
        ),
        _row(
            datetime(2026, 8, 3, 15, 41, tzinfo=KST),
            102_000,
            market_session="NXT_AFTERMARKET",
            market_venue="NXT",
            line_number=3,
        ),
    ]

    report = evaluation.build_daily_evaluation(rows, target_date=signal.date())

    assert report["status"] == "no_mature_actionable_sample"
    assert report["outcomes"] == []


def test_rolling_report_requires_60_daily_artifacts(tmp_path):
    start = date(2026, 5, 1)
    for offset in range(60):
        target = start + timedelta(days=offset)
        payload = {
            "target_date": target.isoformat(),
            "source_row_count": 1,
            "outcomes": [],
            "runtime_effect": False,
        }
        path = (
            tmp_path / f"samsung_widget_advisory_evaluation_{target.isoformat()}.json"
        )
        path.write_text(json.dumps(payload), encoding="utf-8")

    report = evaluation.build_rolling_report(
        tmp_path, as_of_date=start + timedelta(days=59)
    )
    assert report["trading_day_count"] == 60
    assert report["sample_floor_met"] is True
    assert report["runtime_effect"] is False


def test_summary_keeps_legacy_daily_outcome_without_venue_readable():
    summary = evaluation._summarize_outcomes(
        [
            {
                "market_session": "KRX_REGULAR",
                "advisory_state": "ENTRY_READY",
                "horizon_minutes": 1,
                "mfe_pct": 0.2,
                "mae_pct": -0.1,
                "first_hit": "neither",
            }
        ]
    )

    assert summary[0]["market_venue"] == "unknown"
