from __future__ import annotations

import json
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


def test_replay_ignores_blocked_price_rows_for_exit_evidence() -> None:
    rows = [
        _row(0, state="ENTRY_READY", previous_state="WATCH"),
        {
            **_row(1, current=102.0, high=102.0),
            "source_quality_status": "BLOCKED",
        },
        _row(2, current=100.1, high=100.2),
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

    assert trades[0]["exit_reason"] == "right_censored"
    assert trades[0]["exit_price"] is None


def test_replay_does_not_use_scale_in_minute_high_after_fill() -> None:
    rows = [
        _row(0, state="ENTRY_READY", previous_state="WATCH"),
        _row(1, current=99.0, high=101.0, bar_minute=0),
        _row(2, current=99.1, high=101.0, bar_minute=1),
        _row(3, current=99.2, high=101.0, bar_minute=2),
    ]
    session = SessionSpec("KRX_REGULAR", "KRX", ("14:30:00",), False, (), False)

    trades = _simulate_day(
        rows,
        session=session,
        add_triggers_bps=(-100,),
        target_bps=100,
        max_entries=1,
        cutoff="14:30:00",
        cooldown_minutes=5,
    )

    assert trades[0]["filled_leg_count"] == 2
    assert trades[0]["exit_at"] == rows[3]["observed_at"].isoformat()
    assert trades[0]["exit_reason"] == "fixed_average_take_profit"


def test_replay_applies_same_episode_source_support_break_before_target() -> None:
    rows = [
        {
            **_row(0, state="ENTRY_READY", previous_state="WATCH"),
            "episode_sequence": 1,
            "entry_event_id": "ENTRY-1",
            "structural_support": 99.0,
        },
        {
            **_row(1, current=98.0, high=102.0),
            "episode_sequence": 1,
            "exit_event_reason": "confirmed_support_break",
            "exit_event_reference_price": 98.0,
            "exit_event_at": datetime(2026, 8, 11, 10, 1, 5, tzinfo=KST),
        },
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
        source_final_exit_action="sell_own_filled_quantity",
    )

    assert trades[0]["exit_reason"] == "confirmed_support_break"
    assert trades[0]["exit_price"] == 98.0
    assert trades[0]["exit_price_provenance"] == ("source_final_exit_reference_price")
    assert trades[0]["gross_return_pct"] == -2.0
    assert trades[0]["net_return_pct"] == -2.2


def test_replay_observe_only_owner_does_not_inherit_source_final_exit() -> None:
    rows = [
        {**_row(0, state="ENTRY_READY", previous_state="WATCH"), "episode_sequence": 1},
        {
            **_row(1, current=101.0, high=101.0),
            "episode_sequence": 1,
            "exit_event_reason": "confirmed_support_break",
            "exit_event_reference_price": 98.0,
        },
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
        source_final_exit_action="observe_only_no_forced_sell",
    )

    assert trades[0]["exit_reason"] == "fixed_average_take_profit"
    assert trades[0]["exit_price"] == 101.0
    assert trades[0]["exit_price_provenance"] == ("fixed_average_take_profit_target")


def test_optional_entry_event_requires_exact_source_only_contract() -> None:
    event = {
        "event_id": "999999:2026-08-11:ENTRY:1:100010",
        "event_type": "ENTRY",
        "episode_sequence": 1,
        "observed_at": "2026-08-11T10:00:10+09:00",
        "state": "ENTRY_READY",
        "entry_price_high": 100.0,
        "target_price": 101.0,
        "structural_support": 99.0,
        "source_quality_status": "PASS",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "runtime_effect": False,
    }

    assert calibration._optional_lifecycle_event_valid(
        event,
        expected_type="ENTRY",
        symbol="999999",
        source_date=date(2026, 8, 11),
        episode_sequence=1,
    )
    assert not calibration._optional_lifecycle_event_valid(
        {**event, "observed_at": "2026-08-10T23:59:59+09:00"},
        expected_type="ENTRY",
        symbol="999999",
        source_date=date(2026, 8, 11),
        episode_sequence=1,
    )
    assert not calibration._optional_lifecycle_event_valid(
        {**event, "structural_support": None},
        expected_type="ENTRY",
        symbol="999999",
        source_date=date(2026, 8, 11),
        episode_sequence=1,
    )


def test_replay_rejects_regressed_source_exit_event_time() -> None:
    rows = [
        {
            **_row(0, state="ENTRY_READY", previous_state="WATCH"),
            "episode_sequence": 1,
        },
        {
            **_row(1, current=98.0, high=102.0),
            "episode_sequence": 1,
            "exit_event_reason": "confirmed_support_break",
            "exit_event_reference_price": 98.0,
            "exit_event_at": datetime(2026, 8, 11, 9, 59, 59, tzinfo=KST),
        },
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
        source_final_exit_action="sell_own_filled_quantity",
    )

    assert trades[0]["exit_reason"] == "fixed_average_take_profit"


def test_daily_entry_caps_compare_one_through_five_and_require_positive_tail_ev() -> (
    None
):
    trades = [
        {
            "trade_date": "2026-08-11",
            "daily_entry_ordinal": cap,
            "net_return_pct": value,
            "exit_reason": "fixed_average_take_profit",
            "filled_leg_count": 1,
        }
        for cap, value in enumerate((0.4, 0.3, 0.2, 0.1, -0.1), 1)
    ]

    comparison = calibration._entry_cap_comparison(trades)

    assert set(comparison) == {"1", "2", "3", "4", "5"}
    assert calibration._incremental_entry_cap_ready(comparison, 4) == (
        True,
        "incremental_entry_cap_ev_positive",
    )
    assert calibration._incremental_entry_cap_ready(comparison, 5) == (
        False,
        "incremental_entry_cap_5_ev_not_positive",
    )
    assert all(spec.max_entries_values == (1, 2, 3, 4, 5) for spec in calibration.SPECS)


def test_summary_excludes_right_censored_rows_from_ev_denominator() -> None:
    summary = _summary(
        [
            {
                "trade_date": "2026-08-11",
                "net_return_pct": 0.6,
                "gross_return_pct": 0.8,
                "exit_reason": "fixed_average_take_profit",
                "filled_leg_count": 1,
                "average_price": 10000,
                "entry_at": "2026-08-11T10:00:00+09:00",
                "exit_at": "2026-08-11T10:02:00+09:00",
            },
            {
                "trade_date": "2026-08-11",
                "net_return_pct": None,
                "exit_reason": "right_censored",
                "filled_leg_count": 1,
                "average_price": 10000,
                "entry_at": "2026-08-11T10:00:00+09:00",
                "exit_at": "2026-08-11T10:10:00+09:00",
            },
        ]
    )

    assert summary["source_quality_adjusted_ev_pct"] == 0.6
    assert summary["right_censored_count"] == 1
    assert summary["target_completion_ratio"] == 0.5
    assert summary["gross_no_slippage_avg_return_pct"] == 0.8
    assert summary["median_resolved_holding_duration_sec"] == 120.0
    assert summary["target_exit_within_180s_ratio"] == 1.0
    assert summary["observed_capital_occupied_krw_seconds"] == 72_000_000.0
    assert summary["cost_aware_realized_return_per_capital_hour"] == 0.03


def test_summary_does_not_fake_exact_capital_occupancy_for_multi_leg_trade() -> None:
    summary = _summary(
        [
            {
                "trade_date": "2026-08-11",
                "net_return_pct": 0.6,
                "gross_return_pct": 0.8,
                "exit_reason": "fixed_average_take_profit",
                "filled_leg_count": 2,
                "average_price": 10000,
                "entry_at": "2026-08-11T10:00:00+09:00",
                "exit_at": "2026-08-11T10:02:00+09:00",
            }
        ]
    )

    assert summary["capital_timing_trade_count"] == 0
    assert summary["capital_occupancy_unavailable_multi_leg_trade_count"] == 1
    assert summary["observed_capital_occupied_krw_seconds"] is None
    assert summary["cost_aware_realized_return_per_capital_hour"] is None


def test_holdout_gates_calibration_selected_high_cap_without_downgrading(
    monkeypatch,
) -> None:
    session = SessionSpec(
        "KRX_REGULAR", "KRX", ("14:30:00",), True, ("15:18:00",), True
    )
    spec = SymbolSpec(
        symbol="005930",
        name="synthetic",
        observation_dir=calibration.DEFAULT_OUTPUT_DIR,
        prefix="synthetic",
        sessions=(session,),
        add_trigger_arms=((),),
        target_bps_values=(50,),
        max_entries_values=calibration.ENTRY_CAP_VALUES,
        minimum_signal_dates=2,
        minimum_trades=2,
        analysis_start_date=date(2026, 6, 5),
        minimum_qualified_observation_dates=0,
    )
    rows = []
    for day in range(1, 6):
        source_date = date(2026, 8, day)
        rows.append(
            {
                **_row(0),
                "trade_date": source_date,
                "observed_at": datetime(2026, 8, day, 10, 0, 10, tzinfo=KST),
                "bar_at": datetime(2026, 8, day, 10, 0, tzinfo=KST),
            }
        )

    def fake_simulate(day_rows, **kwargs):
        maximum = int(kwargs["max_entries"])
        source_date = day_rows[0]["trade_date"]
        calibration_values = (0.5, 0.5, 0.5, 0.1, -0.5)
        holdout_values = (0.5, 0.5, 0.5, -0.2, -0.5)
        values = holdout_values if source_date.day == 5 else calibration_values
        return [
            {
                "trade_date": source_date.isoformat(),
                "daily_entry_ordinal": ordinal,
                "net_return_pct": values[ordinal - 1],
                "exit_reason": (
                    "fixed_average_take_profit"
                    if values[ordinal - 1] > 0
                    else "preclose_market_exit"
                ),
                "filled_leg_count": 1,
            }
            for ordinal in range(1, maximum + 1)
        ]

    monkeypatch.setattr(calibration, "_simulate_day", fake_simulate)

    report = _calibrate_session(spec, session, rows, target_date=date(2026, 8, 5))

    assert report["selected_policy"]["max_completed_entries_per_day"] == 4
    assert report["provisional_candidate_decision"] == (
        "independent_holdout_incremental_entry_cap_ev_not_positive"
    )
    assert report["decision"] == (
        "independent_holdout_incremental_entry_cap_ev_not_positive"
    )


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


def test_verified_non_force_flat_policy_carries_on_inconclusive_holdout() -> None:
    spec = calibration.SPECS[0]
    session = spec.sessions[1]
    rows = []
    for day in (3, 4, 5, 6):
        trade_date = date(2026, 8, day)
        entry = {
            **_row(0, state="ENTRY_READY", previous_state="WATCH"),
            "trade_date": trade_date,
            "observed_at": datetime(2026, 8, day, 10, 0, 10, tzinfo=KST),
            "bar_at": datetime(2026, 8, day, 10, 0, tzinfo=KST),
        }
        terminal_price = 100.0 if day == 6 else 102.0
        terminal = {
            **_row(
                1,
                current=terminal_price,
                low=terminal_price,
                high=terminal_price,
            ),
            "trade_date": trade_date,
            "observed_at": datetime(2026, 8, day, 10, 1, 10, tzinfo=KST),
            "bar_at": datetime(2026, 8, day, 10, 1, tzinfo=KST),
        }
        rows.extend((entry, terminal))
    previous = {
        "policy_id": "verified-prior-policy",
        "new_entry_runtime_eligible": True,
        "add_trigger_bps_from_initial_fill": (),
        "take_profit_bps_from_equal_share_average": 80,
        "max_completed_entries_per_day": 3,
        "reentry_cooldown_minutes": 5,
        "new_entry_cutoff_time": "15:00:00",
        "force_exit_time": None,
    }

    report = _calibrate_session(
        spec,
        session,
        rows,
        target_date=date(2026, 8, 6),
        previous_runtime_policy=previous,
    )

    assert report["provisional_candidate_decision"] == (
        "independent_holdout_target_missing"
    )
    assert report["decision"] == ("carry_forward_previous_verified_policy")
    assert report["carry_forward_previous_policy"] is True
    assert report["carry_forward_candidate_ready"] is True
    assert report["carry_forward_holdout_decision"] == (
        "independent_holdout_target_missing"
    )
    assert report["carry_forward_from_policy_id"] == "verified-prior-policy"
    assert report["runtime_selected_policy"] == {
        "add_trigger_bps_from_initial_fill": [],
        "target_bps": 80,
        "max_completed_entries_per_day": 3,
        "new_entry_cutoff_time": "15:00:00",
        "reentry_cooldown_minutes": 5,
        "force_exit_time": None,
    }

    no_longer_ready = _calibrate_session(
        spec,
        session,
        rows,
        target_date=date(2026, 8, 6),
        previous_runtime_policy={
            **previous,
            "take_profit_bps_from_equal_share_average": 300,
        },
    )
    assert no_longer_ready["carry_forward_candidate_ready"] is False
    assert no_longer_ready["carry_forward_previous_policy"] is False
    assert no_longer_ready["decision"] == "independent_holdout_target_missing"


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


def test_execution_quality_vetoes_broker_submit_failure_without_acceptance(
    tmp_path,
) -> None:
    target_date = date(2026, 8, 24)
    path = tmp_path / "widget_signal_auto_trade_events_20260824.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "symbol": "005930",
                        "event_type": "order_submit_failed",
                        "actual_order_submitted": False,
                        "return_code": "20",
                        "execution_policy_session": "KRX_REGULAR",
                    }
                ),
                json.dumps(
                    {
                        "symbol": "005930",
                        "event_type": "entry_episode_closed_submit_rejected",
                        "actual_order_submitted": False,
                        "execution_policy_session": "KRX_REGULAR",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    quality = _load_execution_quality(
        "005930",
        target_date=target_date,
        event_dir=tmp_path,
        session="KRX_REGULAR",
    )

    assert quality["status"] == "SAFETY_VETO"
    assert quality["accepted_order_count"] == 0
    assert quality["order_submit_failed_count"] == 1
    assert quality["execution_failure_count"] == 1
    assert quality["failure_reason_codes"] == ["broker_order_submit_failed"]
    assert quality["runtime_apply_allowed"] is False


def test_execution_quality_is_attributed_per_widget_session(tmp_path) -> None:
    target_date = date(2026, 8, 11)
    path = tmp_path / "widget_signal_auto_trade_events_20260811.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "symbol": "005930",
                        "event_type": "order_submitted",
                        "actual_order_submitted": True,
                        "execution_policy_session": "KRX_REGULAR",
                    }
                ),
                json.dumps(
                    {
                        "symbol": "005930",
                        "event_type": "take_profit_terminal_failure",
                        "execution_policy_session": "NXT_AFTERMARKET",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    krx = _load_execution_quality(
        "005930",
        target_date=target_date,
        event_dir=tmp_path,
        session="KRX_REGULAR",
    )
    nxt = _load_execution_quality(
        "005930",
        target_date=target_date,
        event_dir=tmp_path,
        session="NXT_AFTERMARKET",
    )

    assert krx["runtime_apply_allowed"] is True
    assert krx["accepted_order_count"] == 1
    assert krx["execution_event_scope"] == "KRX_REGULAR"
    assert nxt["runtime_apply_allowed"] is False
    assert nxt["terminal_execution_failure_count"] == 1


def test_unattributed_terminal_failure_vetoes_every_widget_session(tmp_path) -> None:
    target_date = date(2026, 8, 11)
    path = tmp_path / "widget_signal_auto_trade_events_20260811.jsonl"
    path.write_text(
        '{"symbol":"005930","event_type":"sell_terminal_failure"}\n',
        encoding="utf-8",
    )

    quality = _load_execution_quality(
        "005930",
        target_date=target_date,
        event_dir=tmp_path,
        session="NXT_PREMARKET",
    )

    assert quality["runtime_apply_allowed"] is False
    assert quality["unattributed_terminal_failure_count"] == 1


def test_unattributed_submit_failure_vetoes_every_widget_session(tmp_path) -> None:
    target_date = date(2026, 8, 11)
    path = tmp_path / "widget_signal_auto_trade_events_20260811.jsonl"
    path.write_text(
        '{"symbol":"005930","event_type":"order_submit_failed"}\n',
        encoding="utf-8",
    )

    quality = _load_execution_quality(
        "005930",
        target_date=target_date,
        event_dir=tmp_path,
        session="NXT_PREMARKET",
    )

    assert quality["runtime_apply_allowed"] is False
    assert quality["execution_sample_observed"] is True
    assert quality["unattributed_execution_failure_count"] == 1
    assert quality["failure_reason_codes"] == ["broker_order_submit_failed"]


def test_ambiguous_submit_exception_is_execution_quality_safety_veto(tmp_path) -> None:
    target_date = date(2026, 8, 11)
    path = tmp_path / "widget_signal_auto_trade_events_20260811.jsonl"
    path.write_text(
        json.dumps(
            {
                "symbol": "005930",
                "event_type": "order_submit_ambiguous",
                "execution_policy_session": "KRX_REGULAR",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    quality = _load_execution_quality(
        "005930",
        target_date=target_date,
        event_dir=tmp_path,
        session="KRX_REGULAR",
    )

    assert quality["status"] == "SAFETY_VETO"
    assert quality["runtime_apply_allowed"] is False
    assert quality["order_submit_failed_count"] == 1
    assert quality["order_submit_ambiguous_count"] == 1
    assert quality["failure_reason_codes"] == ["broker_order_submit_ambiguous"]


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
    assert (
        loaded["034020"]["KRX_REGULAR"]["source_final_exit_action"]
        == "sell_own_filled_quantity"
    )
    assert calibration.SOURCE_FINAL_EXIT_ACTION_BY_SYMBOL["005930"] == (
        "observe_only_no_forced_sell"
    )
    assert calibration.SOURCE_FINAL_EXIT_ACTION_BY_SYMBOL["042660"] == (
        "sell_own_filled_quantity"
    )
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


def test_widget_report_consumes_prior_micro_diagnostic_without_policy_effect(
    tmp_path, monkeypatch
) -> None:
    session = SessionSpec("KRX_REGULAR", "KRX", ("14:30:00",), False, (), False)
    spec = SymbolSpec(
        symbol="999999",
        name="synthetic",
        observation_dir=tmp_path / "observations",
        prefix="synthetic",
        sessions=(session,),
        add_trigger_arms=((),),
        target_bps_values=(50,),
        max_entries_values=(1,),
        minimum_signal_dates=2,
        minimum_trades=2,
        analysis_start_date=date(2026, 6, 5),
        minimum_qualified_observation_dates=0,
    )
    monkeypatch.setattr(calibration, "SPECS", (spec,))
    monkeypatch.setattr(
        calibration,
        "_load_rows",
        lambda _spec, *, target_date: ([], [], {"loaded": 0}),
    )
    micro_dir = tmp_path / "machine_micro"
    micro_dir.mkdir()
    (micro_dir / "machine_microstructure_attribution_2026-08-13.json").write_text(
        json.dumps(
            {
                "schema": "machine_microstructure_attribution_v1",
                "target_date": "2026-08-13",
                "status": "warning",
                "authority": {
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                "consumers": {
                    "widget_postclose_tuning": {
                        "symbols": {
                            "999999": {
                                "micro_context_status": "matched",
                                "anchor_results": [
                                    {"anchor_role": "counterfactual_calibration_entry"}
                                ],
                            }
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    loaded = calibration.build_report(
        target_date=date(2026, 8, 14),
        machine_microstructure_report_dir=micro_dir,
    )
    missing = calibration.build_report(
        target_date=date(2026, 8, 14),
        machine_microstructure_report_dir=tmp_path / "missing_micro",
    )

    diagnostic = loaded["symbols"]["999999"][
        "microstructure_prior_trading_day_diagnostic"
    ]
    assert diagnostic["status"] == "loaded"
    assert diagnostic["source_date"] == "2026-08-13"
    assert diagnostic["selection_effect"] is False
    assert diagnostic["payload"]["micro_context_status"] == "matched"
    assert (
        missing["symbols"]["999999"]["microstructure_prior_trading_day_diagnostic"][
            "status"
        ]
        == "missing"
    )
    assert (
        loaded["symbols"]["999999"]["sessions"]
        == missing["symbols"]["999999"]["sessions"]
    )


def test_build_report_blocks_malformed_source_rows_even_with_pass_rows(
    tmp_path, monkeypatch
) -> None:
    session = SessionSpec("KRX_REGULAR", "KRX", ("14:30:00",), False, (), False)
    spec = SymbolSpec(
        symbol="999999",
        name="synthetic",
        observation_dir=tmp_path / "observations",
        prefix="synthetic",
        sessions=(session,),
        add_trigger_arms=((),),
        target_bps_values=(50,),
        max_entries_values=(1,),
        minimum_signal_dates=2,
        minimum_trades=2,
        analysis_start_date=date(2026, 6, 5),
        minimum_qualified_observation_dates=0,
    )
    audit = {
        "raw_line_count": 2,
        "accepted_row_count": 1,
        "invalid_json_or_object_count": 0,
        "required_contract_missing_count": 0,
        "invalid_observed_at_or_date_count": 0,
        "invalid_price_or_bar_time_count": 0,
        "invalid_optional_lifecycle_event_count": 1,
        "expected_source_blocked_without_completed_bar_count": 0,
        "excluded_row_count": 1,
        "raw_row_exclusion_applied": True,
    }
    monkeypatch.setattr(calibration, "SPECS", (spec,))
    monkeypatch.setattr(
        calibration,
        "_load_rows",
        lambda _spec, *, target_date: ([_row(0)], ["synthetic.jsonl"], audit),
    )
    monkeypatch.setattr(
        calibration,
        "_calibrate_session",
        lambda *_args, **_kwargs: {"decision": "insufficient_source"},
    )
    monkeypatch.setattr(
        calibration,
        "_load_execution_quality",
        lambda *_args, **_kwargs: {
            "status": "BLOCKED",
            "runtime_apply_allowed": False,
        },
    )

    report = calibration.build_report(
        target_date=date(2026, 8, 14),
        machine_microstructure_report_dir=tmp_path / "missing_micro",
    )

    symbol = report["symbols"]["999999"]
    assert symbol["source_quality_status"] == "BLOCKED"
    assert symbol["source_contract_valid"] is False
    assert symbol["source_contract_gap_codes"] == [
        "invalid_optional_lifecycle_event_count"
    ]
    assert report["source_quality_status"] == "BLOCKED"
