from __future__ import annotations

from datetime import date, datetime

from src.engine.monitoring.samsung_widget_contract import KST
from src.engine.monitoring.widget_auto_trade_policy_calibration import (
    SessionSpec,
    _research_accumulation,
    _simulate_day,
    _summary,
    build_policy,
    write_outputs,
)
from src.engine.monitoring import widget_auto_trade_policy_calibration as calibration
from src.utils.market_day import is_krx_trading_day


def _row(
    minute: int,
    *,
    state: str = "WATCH",
    previous_state: str = "WATCH",
    current: float = 100.0,
    low: float = 100.0,
    high: float = 100.0,
    bar_minute: int | None = None,
):
    observed_at = datetime(2026, 8, 11, 10, minute, 10, tzinfo=KST)
    return {
        "trade_date": date(2026, 8, 11),
        "observed_at": observed_at,
        "session": "KRX_REGULAR",
        "venue": "KRX",
        "state": state,
        "previous_state": previous_state,
        "current_price": current,
        "low": low,
        "high": high,
        "bar_at": datetime(
            2026, 8, 11, 10, minute if bar_minute is None else bar_minute, tzinfo=KST
        ),
        "source_quality_status": "PASS",
        "source_path": "synthetic.jsonl",
        "source_line_number": minute + 1,
    }


def test_replay_does_not_use_pre_entry_high_from_same_completed_bar() -> None:
    rows = [
        _row(0, state="ENTRY_READY", previous_state="WATCH"),
        _row(1, current=100.1, high=102.0, bar_minute=0),
        _row(2, current=100.2, high=101.1, bar_minute=1),
    ]
    session = SessionSpec("KRX_REGULAR", "KRX", ("14:30:00",), False, (), False)

    trades = _simulate_day(
        rows,
        session=session,
        add_triggers_bps=(),
        target_bps=100,
        max_entries=1,
        cutoff="14:30:00",
        cooldown_minutes=5,
    )

    assert trades[0]["exit_at"] == rows[2]["observed_at"].isoformat()
    assert trades[0]["exit_reason"] == "fixed_average_take_profit"


def test_replay_force_flat_resolves_unhit_target_at_preclose() -> None:
    rows = [
        _row(0, state="ENTRY_CAUTION", previous_state="WATCH"),
        {
            **_row(1, current=99.5, low=99.5, high=100.0),
            "observed_at": datetime(2026, 8, 11, 15, 18, 1, tzinfo=KST),
            "bar_at": datetime(2026, 8, 11, 15, 17, tzinfo=KST),
        },
    ]
    session = SessionSpec(
        "KRX_REGULAR", "KRX", ("14:30:00",), True, ("15:18:00",), True
    )

    trades = _simulate_day(
        rows,
        session=session,
        add_triggers_bps=(),
        target_bps=100,
        max_entries=1,
        cutoff="14:30:00",
        cooldown_minutes=5,
        force_exit_time="15:18:00",
    )
    summary = _summary(trades)

    assert trades[0]["exit_reason"] == "preclose_market_exit"
    assert summary["resolved_trade_count"] == 1
    assert summary["right_censored_count"] == 0


def test_default_target_uses_completed_current_date_only_after_postclose(
    monkeypatch,
) -> None:
    class BeforeClose(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 8, 12, 19, 59, tzinfo=KST)

    class AfterClose(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 8, 12, 20, 10, tzinfo=KST)

    monkeypatch.setattr(calibration, "datetime", BeforeClose)
    assert calibration._resolve_default_target_date() == date(2026, 8, 11)

    monkeypatch.setattr(calibration, "datetime", AfterClose)
    assert calibration._resolve_default_target_date() == date(2026, 8, 12)


def test_write_outputs_requires_report_before_policy_can_load(tmp_path) -> None:
    session_reports = {}
    for spec in calibration.SPECS:
        session_reports[spec.symbol] = {
            "name": spec.name,
            "sessions": {
                session.session: {
                    "decision": "insufficient_non_overlapping_trades",
                    "selected_policy": None,
                }
                for session in spec.sessions
            },
        }
    report = {
        "schema": "widget_auto_trade_policy_calibration_report_v1",
        "status": "complete",
        "target_date": "2026-08-11",
        "effective_date": "2026-08-12",
        "source_quality_status": "PASS",
        "symbols": session_reports,
        "metric_contract": calibration.METRIC_CONTRACT,
    }
    policy = build_policy(report)

    report_path, policy_path, verification = write_outputs(
        report,
        policy,
        output_dir=tmp_path / "reports",
        policy_dir=tmp_path / "policies",
    )

    assert report_path.exists()
    assert policy_path.exists()
    assert verification["status"] == "pass"


def test_low_symbol_research_gate_requires_40_full_krx_dates() -> None:
    spec = calibration.SPECS[1]
    session = spec.sessions[0]
    rows = []
    trade_dates = []
    candidate = date(2026, 8, 12)
    while len(trade_dates) < 39:
        if is_krx_trading_day(candidate):
            trade_dates.append(candidate)
        candidate = date.fromordinal(candidate.toordinal() + 1)
    for trade_date in trade_dates:
        for index in range(300):
            minute = round(index * 389 / 299)
            observed_at = datetime.combine(
                trade_date,
                datetime.min.time(),
                tzinfo=KST,
            ).replace(hour=9) + calibration.timedelta(minutes=minute)
            rows.append(
                {
                    "trade_date": trade_date,
                    "observed_at": observed_at,
                    "session": session.session,
                    "venue": session.venue,
                    "source_quality_status": "PASS",
                }
            )

    accumulation = _research_accumulation(spec, session, rows)

    assert accumulation["status"] == "accumulating"
    assert accumulation["qualified_observation_date_count"] == 39
    assert accumulation["runtime_eligible"] is False

    fortieth_date = candidate
    while not is_krx_trading_day(fortieth_date):
        fortieth_date = date.fromordinal(fortieth_date.toordinal() + 1)
    for index in range(300):
        minute = round(index * 389 / 299)
        observed_at = datetime.combine(
            fortieth_date,
            datetime.min.time(),
            tzinfo=KST,
        ).replace(hour=9) + calibration.timedelta(minutes=minute)
        rows.append(
            {
                "trade_date": fortieth_date,
                "observed_at": observed_at,
                "session": session.session,
                "venue": session.venue,
                "source_quality_status": "PASS",
            }
        )

    ready = _research_accumulation(spec, session, rows)

    assert ready["status"] == "ready"
    assert ready["qualified_observation_date_count"] == 40
    assert ready["runtime_eligible"] is True


def test_low_symbol_research_gate_records_fully_missing_trading_dates() -> None:
    spec = calibration.SPECS[1]
    session = spec.sessions[0]

    accumulation = _research_accumulation(
        spec,
        session,
        [],
        target_date=date(2026, 8, 12),
    )

    assert accumulation["qualified_observation_date_count"] == 0
    assert (
        "no_valid_krx_regular_rows"
        in accumulation["excluded_observation_dates"]["2026-08-12"]
    )
