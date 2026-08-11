from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from src.engine.monitoring.samsung_like_machine_candidate_scan import (
    _leg_outcome,
    build_report,
)

KST = ZoneInfo("Asia/Seoul")


def _row(at: datetime, *, open_: int, high: int, low: int, close: int) -> dict:
    return {
        "source_timestamp": at.strftime("%Y%m%d%H%M%S"),
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
    }


def _candidate_source(day_count: int = 20) -> dict:
    sor: list[dict] = []
    nxt: list[dict] = []
    start = date(2026, 6, 5)
    for offset in range(day_count):
        day = start + timedelta(days=offset)
        regular_start = datetime.combine(day, time(12, 46), tzinfo=KST)
        for minute in range(30):
            at = regular_start + timedelta(minutes=minute)
            if minute == 0:
                sor.append(_row(at, open_=100000, high=100000, low=99900, close=99900))
            elif minute == 29:
                sor.append(_row(at, open_=98600, high=98700, low=98400, close=98500))
            else:
                sor.append(_row(at, open_=99500, high=99600, low=99400, close=99500))
        sor.append(
            _row(
                regular_start + timedelta(minutes=30),
                open_=98500,
                high=98500,
                low=98300,
                close=98400,
            )
        )
        sor.append(
            _row(
                regular_start + timedelta(minutes=31),
                open_=98500,
                high=98800,
                low=98500,
                close=98700,
            )
        )
        nxt_start = datetime.combine(day, time(8, 0), tzinfo=KST)
        nxt.append(_row(nxt_start, open_=100000, high=100000, low=97000, close=97000))
        nxt.append(
            _row(
                nxt_start + timedelta(minutes=1),
                open_=97100,
                high=97400,
                low=97100,
                close=97300,
            )
        )
        sor_open = datetime.combine(day, time(9, 0), tzinfo=KST)
        sor.append(_row(sor_open, open_=100000, high=100000, low=99900, close=99900))
    return {
        "name": "테스트",
        "sor_bars": sor,
        "nxt_bars": nxt,
        "source_meta": {
            "SOR": {"source_quality_status": "PASS"},
            "NXT": {"source_quality_status": "PASS"},
        },
    }


def test_source_only_scan_finds_completed_morning_and_midday_candidate():
    report = build_report(
        symbols={"000001": _candidate_source()},
        start_date="2026-06-05",
        end_date="2026-06-24",
    )

    morning = report["symbols"]["000001"]["machines"]["morning"]
    midday = report["symbols"]["000001"]["machines"]["midday"]
    assert morning["status"] == "implementation_candidate_source_only"
    assert morning["completed_legs"] == 40
    assert morning["held_legs"] == 0
    assert midday["status"] == "implementation_candidate_source_only"
    assert midday["completed_legs"] == 40
    assert report["runtime_effect"] is False
    assert report["broker_order_forbidden"] is True


def test_same_bar_fill_and_target_is_conservatively_held():
    at = datetime(2026, 8, 10, 14, 1, tzinfo=KST)
    bar = _row(at, open_=100000, high=100300, low=99900, close=100100)

    outcome = _leg_outcome(
        entry_price=100000,
        entry_bars=[{**bar, "timestamp": at}],
        target_bars=[{**bar, "timestamp": at}],
        cost_pct=0.20,
    )

    assert outcome["status"] == "HELD"


def test_source_quality_failure_blocks_candidate_even_with_price_pattern():
    source = _candidate_source()
    source["source_meta"]["SOR"]["source_quality_status"] = "PARTIAL"

    report = build_report(
        symbols={"000001": source},
        start_date="2026-06-05",
        end_date="2026-06-24",
    )

    machines = report["symbols"]["000001"]["machines"]
    assert machines["midday"]["status"] == "source_quality_blocked"
    assert machines["morning"]["status"] == "source_quality_blocked"
