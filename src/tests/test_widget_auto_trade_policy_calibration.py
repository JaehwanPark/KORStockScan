from __future__ import annotations

from datetime import date, datetime

from src.engine.monitoring.samsung_widget_contract import KST
from src.engine.monitoring.widget_auto_trade_policy_calibration import (
    SessionSpec,
    SymbolSpec,
    _calibrate_session,
    _load_execution_quality,
    _research_accumulation,
    _simulate_day,
    _summary,
    build_policy,
    write_outputs,
)
from src.engine.monitoring import widget_auto_trade_policy_calibration as calibration
from src.trading.widget_auto_trade.policy import WidgetAutoTradePolicyLoader
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


def test_non_force_flat_candidate_keeps_unresolved_as_diagnostic_not_hard_block() -> (
    None
):
    spec = calibration.SPECS[0]
    session = spec.sessions[1]
    summary = {
        "distinct_signal_date_count": 5,
        "signal_trade_count": 5,
        "target_exit_count": 2,
        "target_completion_ratio": 0.4,
        "source_quality_adjusted_ev_pct": 0.12,
        "equal_weight_avg_net_return_pct": 0.3,
        "worst_net_return_pct": 0.3,
        "resolved_trade_count": 2,
    }

    ready, reason = calibration._candidate_ready(spec, session, summary)

    assert ready is True
    assert reason == "bounded_cumulative_candidate_ready"


def test_policy_selection_uses_chronological_holdout_not_selection_rows(
    tmp_path,
) -> None:
    session = SessionSpec(
        "KRX_REGULAR", "KRX", ("14:30:00",), True, ("15:18:00",), True
    )
    spec = SymbolSpec(
        symbol="999999",
        name="테스트",
        observation_dir=tmp_path,
        prefix="test",
        sessions=(session,),
        add_trigger_arms=((),),
        target_bps_values=(100,),
        max_entries_values=(2,),
        minimum_signal_dates=2,
        minimum_trades=2,
        analysis_start_date=date(2026, 8, 3),
        minimum_qualified_observation_dates=0,
    )
    rows = []
    for day in (3, 4, 5, 6):
        trade_date = date(2026, 8, day)
        entry = {
            **_row(0, state="ENTRY_READY", previous_state="WATCH"),
            "trade_date": trade_date,
            "observed_at": datetime(2026, 8, day, 10, 0, 10, tzinfo=KST),
            "bar_at": datetime(2026, 8, day, 10, 0, tzinfo=KST),
        }
        terminal_price = 99.0 if day == 6 else 102.0
        terminal = {
            **_row(1, current=terminal_price, low=terminal_price, high=terminal_price),
            "trade_date": trade_date,
            "observed_at": datetime(2026, 8, day, 15, 18, 1, tzinfo=KST),
            "bar_at": datetime(2026, 8, day, 15, 17, tzinfo=KST),
        }
        rows.extend((entry, terminal))

    report = _calibrate_session(spec, session, rows, target_date=date(2026, 8, 6))

    assert report["calibration_dates"] == [
        "2026-08-03",
        "2026-08-04",
        "2026-08-05",
    ]
    assert report["holdout_dates"] == ["2026-08-06"]
    assert report["selected_summary"]["source_quality_adjusted_ev_pct"] > 0
    assert report["independent_holdout_summary"]["source_quality_adjusted_ev_pct"] < 0
    assert report["decision"] == "independent_holdout_ev_or_tail_failed"


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


def test_execution_quality_surfaces_terminal_sell_failure_as_safety_veto(
    tmp_path,
) -> None:
    target_date = date(2026, 8, 11)
    path = tmp_path / "widget_signal_auto_trade_events_20260811.jsonl"
    path.write_text(
        "\n".join(
            [
                '{"symbol":"999999","event_type":"order_submitted",'
                '"actual_order_submitted":true}',
                '{"symbol":"999999","event_type":"take_profit_terminal_failure"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    quality = _load_execution_quality(
        "999999", target_date=target_date, event_dir=tmp_path
    )

    assert quality["status"] == "SAFETY_VETO"
    assert quality["accepted_order_count"] == 1
    assert quality["terminal_sell_failure_count"] == 1
    assert quality["runtime_apply_allowed"] is False


def test_execution_quality_counts_actual_engine_terminal_failure_names(
    tmp_path,
) -> None:
    target_date = date(2026, 8, 11)
    path = tmp_path / "widget_signal_auto_trade_events_20260811.jsonl"
    path.write_text(
        "\n".join(
            [
                '{"symbol":"999999","event_type":"sell_terminal_failure"}',
                '{"symbol":"999999","event_type":"buy_cancel_terminal_failure"}',
                '{"symbol":"999999","event_type":"take_profit_cancel_terminal_failure"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    quality = _load_execution_quality(
        "999999", target_date=target_date, event_dir=tmp_path
    )

    assert quality["status"] == "SAFETY_VETO"
    assert quality["terminal_sell_failure_count"] == 3


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
        "source_quality_status": "BLOCKED",
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
    loaded = WidgetAutoTradePolicyLoader(
        tmp_path / "policies", include_symbol_expansion=False
    ).resolve_all(observed_date=date(2026, 8, 12))
    assert set(loaded["005930"]) == {
        "NXT_PREMARKET",
        "KRX_REGULAR",
        "NXT_AFTERMARKET",
    }
    assert all(
        policy["new_entry_runtime_eligible"] is False
        for policy in loaded["005930"].values()
    )
    assert (
        loaded["034020"]["KRX_REGULAR"]["new_entry_runtime_block_reason"]
        == "source_quality_blocked"
    )
    assert (
        loaded["034020"]["KRX_REGULAR"]["research_accumulation_gate_status"]
        == "missing"
    )
    assert loaded["042660"]["KRX_REGULAR"]["new_entry_runtime_eligible"] is False


def test_verified_low_symbol_policy_auto_promotes_on_effective_date(tmp_path) -> None:
    qualified_dates: list[str] = []
    candidate = date(2026, 8, 12)
    while len(qualified_dates) < 40:
        if is_krx_trading_day(candidate):
            qualified_dates.append(candidate.isoformat())
        candidate = date.fromordinal(candidate.toordinal() + 1)
    target_date = date.fromisoformat(qualified_dates[-1])
    effective_date = calibration._next_krx_trading_date(target_date)
    accumulation = {
        "status": "ready",
        "start_date": "2026-08-12",
        "minimum_qualified_observation_dates": 40,
        "qualified_observation_date_count": 40,
        "qualified_observation_dates": qualified_dates,
        "excluded_observation_dates": {},
        "qualification_contract": calibration.CUMULATIVE_RESEARCH_QUALIFICATION_CONTRACT,
        "runtime_eligible": True,
    }
    symbols = {}
    for spec in calibration.SPECS:
        source = {
            "name": spec.name,
            "source_quality_status": "PASS",
            "actual_evidence_start_date": spec.analysis_start_date.isoformat(),
            "execution_quality": {
                "status": "PASS",
                "runtime_apply_allowed": spec.symbol == "034020",
            },
            "sessions": {},
        }
        for session in spec.sessions:
            if spec.symbol == "034020":
                source["sessions"][session.session] = {
                    "decision": "widget_auto_trade_policy_candidate_ready",
                    "selected_policy": {
                        "add_trigger_bps_from_initial_fill": [-50, -100],
                        "target_bps": 80,
                        "max_completed_entries_per_day": 2,
                        "new_entry_cutoff_time": "14:30:00",
                        "reentry_cooldown_minutes": 10,
                        "force_exit_time": "15:18:00",
                    },
                    "policy_tier": "bounded_chronological_holdout",
                    "rollback_condition": "postclose_holdout_or_source_quality_failure",
                    "research_accumulation": accumulation,
                }
            else:
                source["sessions"][session.session] = {
                    "decision": "execution_quality_safety_veto",
                    "selected_policy": None,
                    "research_accumulation": {
                        "status": "not_required",
                        "runtime_eligible": spec.symbol == "005930",
                    },
                }
        symbols[spec.symbol] = source
    report = {
        "schema": "widget_auto_trade_policy_calibration_report_v1",
        "status": "complete",
        "target_date": target_date.isoformat(),
        "effective_date": effective_date.isoformat(),
        "source_quality_status": "PASS",
        "symbols": symbols,
        "metric_contract": calibration.METRIC_CONTRACT,
    }
    policy = build_policy(report)

    _, _, verification = write_outputs(
        report,
        policy,
        output_dir=tmp_path / "reports",
        policy_dir=tmp_path / "policies",
    )
    loaded = WidgetAutoTradePolicyLoader(
        tmp_path / "policies", include_symbol_expansion=False
    ).resolve_all(observed_date=effective_date)

    assert verification["status"] == "pass"
    assert verification["runtime_eligible_session_count"] == 1
    assert loaded["034020"]["KRX_REGULAR"]["new_entry_runtime_eligible"] is True
    assert loaded["034020"]["KRX_REGULAR"]["leg_quantity_each"] == 10
    assert loaded["042660"]["KRX_REGULAR"]["new_entry_runtime_eligible"] is False


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
