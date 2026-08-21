from __future__ import annotations

from datetime import date, datetime, time, timedelta

import pytest

from src.engine.monitoring import widget_symbol_signal_policy_research as research
from src.engine.monitoring.widget_symbol_signal_policy_research import (
    Bar,
    KST,
    ResearchError,
    SignalPolicy,
)


class FakeResponse:
    status_code = 200
    headers = {}

    def __init__(self, rows):
        self._rows = rows

    def json(self):
        return {"return_code": 0, "stk_min_pole_chart_qry": self._rows}


class RateLimitResponse:
    status_code = 429
    headers = {"Retry-After": "0"}

    def json(self):
        return {}


def test_completed_research_date_uses_previous_session_before_krx_close():
    observed = datetime(2026, 8, 18, 7, 10, tzinfo=KST)

    assert research.resolve_completed_research_end_date(observed) == date(2026, 8, 14)


def test_completed_research_date_uses_current_session_after_krx_close():
    observed = datetime(2026, 8, 18, 15, 31, tzinfo=KST)

    assert research.resolve_completed_research_end_date(observed) == date(2026, 8, 18)


def _bars(
    values: list[tuple[int, int, int, int, int]],
    *,
    started: time = time(9, 0),
) -> tuple[Bar, ...]:
    base = datetime.combine(date(2026, 8, 11), started, tzinfo=KST)
    return tuple(
        Bar(base + timedelta(minutes=index), open_, high, low, close, volume)
        for index, (open_, high, low, close, volume) in enumerate(values)
    )


def _policy() -> SignalPolicy:
    return SignalPolicy(
        segment="morning",
        lookback_bars=3,
        drawdown_pct=0.5,
        near_low_pct=0.5,
        reclaim_ticks=1,
        target_bps=50,
    )


def test_widget_source_is_independent_read_only_ohlcv_contract():
    started = date(2026, 6, 5)
    dates = [started + timedelta(days=index) for index in range(17)]
    rows = [
        {
            "cntr_tm": f"{item.strftime('%Y%m%d')}131500",
            "open_pric": "20000",
            "high_pric": "20100",
            "low_pric": "19900",
            "cur_prc": "20000",
            "trde_qty": str(100 + index),
        }
        for index, item in enumerate(dates)
    ]
    rows.append(
        {
            "cntr_tm": "20260604131500",
            "open_pric": "20000",
            "high_pric": "20100",
            "low_pric": "19900",
            "cur_prc": "20000",
            "trde_qty": "99",
        }
    )
    calls = []

    def post(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse(rows)

    bars, meta = research.fetch_krx_history(
        symbol="006800",
        token="CACHED",
        start_date=started,
        end_date=dates[-1],
        expected_trading_day_count=len(dates),
        page_delay_sec=0,
        post=post,
    )

    assert len(calls) == 1
    assert calls[0][1]["headers"]["api-id"] == "ka10080"
    assert calls[0][1]["json"] == {
        "stk_cd": "006800",
        "tic_scope": "1",
        "upd_stkpc_tp": "1",
    }
    assert bars[0].volume == 100
    assert meta["source_quality_status"] == "PASS"
    assert meta["market"] == "KRX_regular"


def test_widget_source_retries_429_without_auth_or_owner_fallback(monkeypatch):
    started = date(2026, 6, 5)
    dates = [started + timedelta(days=index) for index in range(17)]
    rows = [
        {
            "cntr_tm": f"{item.strftime('%Y%m%d')}131500",
            "open_pric": "20000",
            "high_pric": "20100",
            "low_pric": "19900",
            "cur_prc": "20000",
            "trde_qty": "100",
        }
        for item in dates
    ]
    rows.append(
        {
            "cntr_tm": "20260604131500",
            "open_pric": "20000",
            "high_pric": "20100",
            "low_pric": "19900",
            "cur_prc": "20000",
            "trde_qty": "100",
        }
    )
    responses = [RateLimitResponse(), FakeResponse(rows)]
    sleeps = []
    monkeypatch.setattr(research.time_module, "sleep", sleeps.append)

    bars, meta = research.fetch_krx_history(
        symbol="006800",
        token="CACHED",
        start_date=started,
        end_date=dates[-1],
        expected_trading_day_count=len(dates),
        page_delay_sec=0,
        post=lambda *args, **kwargs: responses.pop(0),
    )

    assert len(bars) == len(dates)
    assert sleeps == [0.2]
    assert meta["request_count"] == 2
    assert meta["rate_limit_retry_count"] == 1


def test_entry_uses_next_completed_bar_open_and_not_signal_bar_price():
    rows = _bars(
        [
            (10_000, 10_000, 9_990, 10_000, 100),
            (10_000, 10_000, 9_990, 10_000, 100),
            (10_000, 10_000, 9_990, 10_000, 100),
            (10_000, 10_000, 9_990, 10_000, 100),
            (10_000, 10_000, 9_990, 10_000, 100),
            (10_000, 10_000, 9_990, 10_000, 100),
            (10_000, 10_010, 10_000, 10_010, 120),
            (10_020, 10_030, 10_010, 10_020, 100),
        ]
    )

    found = research._find_entry(rows, 5, _policy(), segment_end=time(10, 30))

    assert found is not None
    entry_index, entry_price, state, volume_ratio = found
    assert entry_index == 7
    assert entry_price == 10_020
    assert state == "ENTRY_READY"
    assert volume_ratio == pytest.approx(1.2)


def test_setup_feature_supports_calibrated_early_history_and_session_anchor():
    rows = _bars(
        [
            (10_000, 10_100, 9_990, 10_000, 100),
            (10_000, 10_000, 9_950, 9_980, 100),
            (9_980, 9_990, 9_900, 9_910, 100),
            (9_910, 9_950, 9_900, 9_930, 100),
            (9_930, 9_970, 9_920, 9_960, 100),
        ]
    )

    feature = research._setup_feature(
        rows,
        4,
        15,
        anchor_mode="session",
        minimum_history_bars=5,
    )

    assert feature is not None
    drawdown, near_low = feature
    assert drawdown == pytest.approx((10_100 - 9_960) / 10_100 * 100)
    assert near_low == pytest.approx((9_960 - 9_900) / 9_900 * 100)


def test_policy_grid_bounds_expansion_and_widens_chase_only_in_morning():
    policies = list(research.policy_grid())

    assert len(policies) == 1_536
    assert any(
        policy.segment == "morning" and policy.max_reclaim_chase_ticks == 6
        for policy in policies
    )
    assert all(
        policy.segment == "morning"
        for policy in policies
        if policy.max_reclaim_chase_ticks == 6
    )


def test_subset_evaluation_reuses_full_simulation_without_metric_drift():
    first_date = date(2026, 8, 10)
    second_date = date(2026, 8, 11)
    episodes = [
        {
            "trade_date": first_date.isoformat(),
            "daily_entry_ordinal": 1,
            "entry_price": 10_000,
            "net_return_pct": 0.3,
            "exit_reason": "target",
            "entry_state": "ENTRY_READY",
            "peak_return_pct": 0.5,
        },
        {
            "trade_date": second_date.isoformat(),
            "daily_entry_ordinal": 1,
            "entry_price": 20_000,
            "net_return_pct": -0.2,
            "exit_reason": "confirmed_support_break",
            "entry_state": "ENTRY_CAUTION",
            "peak_return_pct": 0.1,
        },
    ]

    subset = research._subset_evaluation({"episodes": episodes}, [first_date])

    assert subset["episode_count"] == 1
    assert subset["target_count"] == 1
    assert subset["notional_weighted_ev_pct"] == pytest.approx(0.3)
    assert subset["entry_cap_comparison"]["1"]["cumulative"]["episode_count"] == 1
    assert subset["episodes"] == [episodes[0]]


def test_entry_replay_enforces_the_same_calibrated_reclaim_chase_band():
    rows = _bars(
        [
            (10_000, 10_000, 9_990, 10_000, 100),
            (10_000, 10_000, 9_990, 10_000, 100),
            (10_000, 10_000, 9_990, 10_000, 100),
            (10_000, 10_000, 9_990, 10_000, 100),
            (10_000, 10_000, 9_990, 10_000, 100),
            (10_000, 10_000, 9_900, 9_900, 100),
            (9_900, 9_950, 9_900, 9_950, 120),
            (9_940, 9_970, 9_930, 9_960, 100),
        ]
    )
    narrow = SignalPolicy("morning", 3, 0.5, 0.5, 1, 50, max_reclaim_chase_ticks=2)
    wider = SignalPolicy("morning", 3, 0.5, 0.5, 1, 50, max_reclaim_chase_ticks=6)

    assert research._find_entry(rows, 5, narrow, segment_end=time(10, 30)) is None
    assert research._find_entry(rows, 5, wider, segment_end=time(10, 30)) is not None


def test_daily_source_coverage_requires_open_close_and_volume():
    trade_date = date(2026, 8, 11)
    rows = _bars([(10_000, 10_000, 10_000, 10_000, 100)] * 381)

    passed = research._daily_source_coverage({trade_date: rows}, [trade_date])
    failed = research._daily_source_coverage({trade_date: rows[:299]}, [trade_date])

    assert passed["status"] == "PASS"
    assert failed["status"] == "FAIL"
    assert failed["qualified_date_count"] == 0
    assert failed["failed_dates"][0]["reasons"] == [
        "bar_count_below_300",
        "regular_close_not_covered",
    ]


def test_daily_source_coverage_excludes_one_partial_day_when_sample_remains():
    started = date(2026, 6, 5)
    dates = [started + timedelta(days=index) for index in range(26)]
    grouped = {}
    for trade_date in dates:
        base = datetime.combine(trade_date, time(9, 0), tzinfo=KST)
        count = 378 if trade_date == dates[5] else 381
        grouped[trade_date] = tuple(
            Bar(
                base + timedelta(minutes=index),
                10_000,
                10_000,
                10_000,
                10_000,
                100,
            )
            for index in range(count)
        )

    result = research._daily_source_coverage(grouped, dates)

    assert result["status"] == "PASS_WITH_DATE_EXCLUSIONS"
    assert result["failed_date_count"] == 1
    assert result["qualified_date_count"] == 25
    assert dates[5].isoformat() not in result["qualified_dates"]


def test_entry_does_not_cross_segment_end_or_broken_support_gap():
    near_end = _bars(
        [
            (10_000, 10_000, 9_990, 10_000, 100),
            (10_000, 10_000, 9_990, 10_000, 100),
            (10_000, 10_000, 9_990, 10_000, 100),
            (10_000, 10_000, 9_990, 10_000, 100),
            (10_000, 10_000, 9_990, 10_000, 100),
            (10_000, 10_000, 9_990, 10_000, 100),
            (10_000, 10_010, 10_000, 10_010, 120),
            (10_010, 10_020, 10_000, 10_010, 100),
        ],
        started=time(10, 23),
    )
    assert (
        research._find_entry(
            near_end,
            5,
            _policy(),
            segment_end=time(10, 30),
        )
        is None
    )

    broken_support = list(near_end)
    broken_support[7] = Bar(
        broken_support[7].timestamp,
        9_980,
        10_000,
        9_970,
        9_990,
        100,
    )
    assert (
        research._find_entry(
            tuple(broken_support),
            5,
            _policy(),
            segment_end=time(10, 31),
        )
        is None
    )


def test_same_bar_target_and_confirmed_adverse_resolves_adverse():
    rows = _bars(
        [
            (10_000, 10_000, 10_000, 10_000, 100),
            (10_000, 10_000, 9_980, 9_980, 100),
            (9_980, 10_100, 9_970, 9_970, 100),
            (9_970, 9_980, 9_960, 9_960, 100),
            (9_960, 9_970, 9_950, 9_950, 100),
        ]
    )

    result = research._exit_episode(
        rows,
        entry_index=1,
        entry_price=10_000,
        support=9_990,
        target_bps=50,
    )

    assert result["exit_reason"] == "same_bar_conflict_adverse"
    assert result["exit_price"] == 9_970


def test_final_completed_regular_bar_is_force_flat_boundary():
    rows = _bars(
        [
            (10_000, 10_000, 10_000, 10_000, 100),
            (10_000, 10_010, 9_990, 10_000, 100),
        ],
        started=time(15, 18),
    )

    result = research._exit_episode(
        rows,
        entry_index=0,
        entry_price=10_000,
        support=9_900,
        target_bps=100,
    )

    assert result["exit_at"].endswith("15:19:00+09:00")
    assert result["exit_reason"] == "force_flat"


def test_entry_cap_comparison_requires_positive_fourth_and_fifth_episode_ev():
    episodes = [
        {
            "trade_date": "2026-08-11",
            "daily_entry_ordinal": cap,
            "entry_price": 10_000,
            "net_return_pct": value,
            "exit_reason": "target" if value > 0 else "force_flat",
            "entry_state": "ENTRY_READY",
            "peak_return_pct": max(value, 0.0),
        }
        for cap, value in enumerate((0.4, 0.3, 0.2, 0.1, -0.1), 1)
    ]

    comparison = research._entry_cap_comparison(episodes)

    assert set(comparison) == {"1", "2", "3", "4", "5"}
    assert research._incremental_entry_cap_ready(comparison, 4) is True
    assert research._incremental_entry_cap_ready(comparison, 5) is False


def test_discovery_selects_on_calibration_and_can_fail_untouched_holdout(
    monkeypatch,
):
    selected = _policy()
    expected_dates = [date(2026, 6, 5) + timedelta(days=index) for index in range(26)]
    grouped = {
        item: _bars([(10_000, 10_000, 10_000, 10_000, 1)]) for item in expected_dates
    }
    monkeypatch.setattr(research, "_group_bars", lambda bars: grouped)
    monkeypatch.setattr(research, "policy_grid", lambda: (selected,))
    evaluated_windows: list[tuple[date, ...]] = []

    def fake_evaluate(grouped_arg, dates, policy, *, include_episodes=False):
        del grouped_arg, policy
        evaluated_windows.append(tuple(dates))
        is_holdout = dates == expected_dates[-research.HOLDOUT_DAYS :]
        net_return = -0.1 if is_holdout else 0.2
        episodes = [
            {
                "trade_date": trade_date.isoformat(),
                "daily_entry_ordinal": cap,
                "entry_price": 10_000,
                "net_return_pct": net_return,
                "exit_reason": "target" if net_return > 0 else "force_flat",
                "entry_state": "ENTRY_READY",
                "peak_return_pct": max(net_return, 0.0),
            }
            for trade_date in dates
            for cap in research.ENTRY_CAP_VALUES
        ]
        result = research._summarize_episodes(episodes)
        result["entry_cap_comparison"] = research._entry_cap_comparison(episodes)
        if include_episodes:
            result["episodes"] = episodes
        return result

    monkeypatch.setattr(research, "evaluate_policy", fake_evaluate)

    result = research.discover_symbol_policy([], expected_dates=expected_dates)

    assert result["selected_policy"] == {
        **research.asdict(selected),
        "max_completed_entries_per_day": 5,
    }
    assert result["decision"] == "holdout_failed_no_widget_runtime_promotion"
    assert result["allowed_runtime_apply"] is False
    calibration_dates = tuple(expected_dates[: -research.HOLDOUT_DAYS])
    split = len(calibration_dates) // 2
    assert evaluated_windows.count(calibration_dates) == 1
    assert tuple(calibration_dates[:split]) not in evaluated_windows
    assert tuple(calibration_dates[split:]) not in evaluated_windows
    assert len(evaluated_windows) == 2


def test_discovery_auto_expands_to_positive_fourth_episode_without_chasing_cap_ev(
    monkeypatch,
):
    selected = _policy()
    expected_dates = [date(2026, 6, 5) + timedelta(days=index) for index in range(26)]
    grouped = {
        item: _bars([(10_000, 10_000, 10_000, 10_000, 1)]) for item in expected_dates
    }
    monkeypatch.setattr(research, "_group_bars", lambda bars: grouped)
    monkeypatch.setattr(research, "policy_grid", lambda: (selected,))

    def fake_evaluate(grouped_arg, dates, policy, *, include_episodes=False):
        del grouped_arg, policy
        incremental_ev = {1: 0.5, 2: 0.3, 3: 0.15, 4: 0.05, 5: -0.1}
        episodes = [
            {
                "trade_date": trade_date.isoformat(),
                "daily_entry_ordinal": cap,
                "entry_price": 10_000,
                "net_return_pct": incremental_ev[cap],
                "exit_reason": "target" if incremental_ev[cap] > 0 else "force_flat",
                "entry_state": "ENTRY_READY",
                "peak_return_pct": max(incremental_ev[cap], 0.0),
            }
            for trade_date in dates
            for cap in research.ENTRY_CAP_VALUES
        ]
        result = research._summarize_episodes(episodes)
        result["entry_cap_comparison"] = research._entry_cap_comparison(episodes)
        if include_episodes:
            result["episodes"] = episodes
        return result

    monkeypatch.setattr(research, "evaluate_policy", fake_evaluate)

    result = research.discover_symbol_policy([], expected_dates=expected_dates)

    assert result["decision"] == "holdout_pass_widget_signal_policy_candidate"
    assert result["selected_policy"]["max_completed_entries_per_day"] == 4
    assert result["calibration"]["notional_weighted_ev_pct"] == 0.25


def test_report_requires_exact_sources_and_declares_cross_owner_prohibition():
    with pytest.raises(ResearchError, match="widget_symbol_source_set_mismatch"):
        research.build_report(sources={}, end_date=date(2026, 8, 11))

    assert research.OWNER_CONTRACT["owner"] == "widget_symbol_auto_trade"
    assert (
        "sell_other_owner_quantity"
        in research.OWNER_CONTRACT["forbidden_cross_owner_actions"]
    )
    assert "mutate_low_price_two_leg_profile_policy_or_service" in (
        research.OWNER_CONTRACT["forbidden_cross_owner_actions"]
    )
