from __future__ import annotations

from datetime import date, datetime, time, timedelta
from types import SimpleNamespace

import pytest

from src.engine.monitoring import low_price_two_leg_entry_spot_research as research
from src.engine.monitoring.low_price_two_leg_expanded_candidate_research import (
    RESEARCH_PROFILES,
)
from src.engine.monitoring.low_price_two_leg_entry_spot_research import (
    Bar,
    DayContext,
    SignalFeature,
    SpotCandidate,
    _leg_outcome,
    candidate_grid,
    fetch_sor_history,
    select_profile_spot,
)
from src.trading.low_price_two_leg.profiles import PROFILES
from src.trading.order.regular_two_leg_machine import KST


class FakeResponse:
    def __init__(self, body, *, headers=None):
        self.status_code = 200
        self._body = body
        self.headers = headers or {}

    def json(self):
        return self._body


def _bar(timestamp: datetime, *, low=20_000, high=20_000) -> Bar:
    return Bar(timestamp, 20_000, high, low, 20_000)


def test_candidate_grid_stays_inside_each_profile_base_window():
    for profile in PROFILES.values():
        lower = profile.policy.scan_start.hour * 60 + profile.policy.scan_start.minute
        upper = (
            profile.policy.scan_last_bar.hour * 60 + profile.policy.scan_last_bar.minute
        )
        grid = candidate_grid(profile)
        assert grid
        assert all(lower <= item.scan_start_minute for item in grid)
        assert all(item.scan_end_minute <= upper for item in grid)
        assert all(
            item.scan_end_minute - item.scan_start_minute + 1 >= 10 for item in grid
        )


def test_logic_improvement_grid_expands_execution_plan_without_live_authority():
    profile = RESEARCH_PROFILES["logic_mirae_asset_morning"]
    plans = {
        (
            item.entry_offsets_ticks,
            item.entry_valid_completed_bars,
            item.target_ticks,
        )
        for item in candidate_grid(profile)
    }

    assert ((-1, -2), 5, 4) in plans
    assert ((0, -1), 3, 4) in plans
    assert all(len(item.entry_offsets_ticks) == 2 for item in candidate_grid(profile))


def test_fixed_operator_observation_grid_never_reoptimizes_the_policy():
    profile = RESEARCH_PROFILES["candidate_475560_morning"]
    grid = candidate_grid(profile)

    assert len(grid) == 1
    assert grid[0].public() == {
        "scan_start": "09:40",
        "scan_end": "09:59",
        "lookback_bars": 20,
        "rolling_high_drawdown_pct": 0.5,
        "rolling_low_proximity_pct": 0.35,
        "entry_offsets_ticks": [0, -1],
        "entry_valid_completed_bars": 5,
        "target_ticks": 4,
    }


def test_target_cannot_complete_on_the_same_bar_as_fill():
    started = datetime(2026, 8, 10, 13, 16, tzinfo=KST)
    fill = _bar(started, low=19_900, high=20_100)
    later_below = _bar(started + timedelta(minutes=1), low=20_000, high=20_050)
    held = _leg_outcome(
        entry_price=20_000,
        fill_bars=(fill, later_below),
        target_bars=(fill, later_below),
    )
    assert held["status"] == "HELD"

    later_target = _bar(started + timedelta(minutes=2), low=20_000, high=20_100)
    complete = _leg_outcome(
        entry_price=20_000,
        fill_bars=(fill,),
        target_bars=(fill, later_target),
    )
    assert complete["status"] == "COMPLETE"


def test_held_leg_exposes_mark_to_market_mae_and_manageable_carry_budget():
    started = datetime(2026, 8, 10, 13, 16, tzinfo=KST)
    fill = Bar(started, 20_000, 20_000, 19_950, 20_000)
    later = Bar(started + timedelta(minutes=1), 19_800, 19_850, 19_500, 19_600)
    held = _leg_outcome(
        entry_price=20_000,
        fill_bars=(fill,),
        target_bars=(fill, later),
    )

    assert held["status"] == "HELD"
    assert held["active_unrealized_pct"] == pytest.approx(-2.23)
    assert held["max_adverse_excursion_pct"] == pytest.approx(-2.5)
    assert research._manageable_carry(
        {
            "held_leg_rate_per_filled_leg": 0.25,
            "worst_held_active_unrealized_pct": -2.2,
        }
    )
    assert not research._manageable_carry(
        {
            "held_leg_rate_per_filled_leg": 0.26,
            "worst_held_active_unrealized_pct": -2.2,
        }
    )


def test_fetch_uses_integrated_sor_and_cached_token_without_other_api_calls():
    start = date(2026, 6, 5)
    dates = [start + timedelta(days=index) for index in range(46)]
    rows = [
        {
            "cntr_tm": f"{item.strftime('%Y%m%d')}131500",
            "open_pric": "20000",
            "high_pric": "20100",
            "low_pric": "19900",
            "cur_prc": "20000",
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
        }
    )
    calls = []

    def post(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse({"return_code": 0, "stk_min_pole_chart_qry": rows})

    bars, meta = fetch_sor_history(
        symbol="010140",
        token="CACHED",
        start_date=start,
        end_date=dates[-1],
        post=post,
        page_delay_sec=0,
    )

    assert len(calls) == 1
    assert calls[0][1]["headers"]["api-id"] == "ka10080"
    assert calls[0][1]["json"] == {
        "stk_cd": "010140_AL",
        "tic_scope": "1",
        "upd_stkpc_tp": "1",
    }
    assert len(bars) == 46
    assert meta["source_quality_status"] == "PASS"


def test_fetch_uses_shared_source_only_read_capacity(monkeypatch):
    start = date(2026, 6, 5)
    dates = [start + timedelta(days=index) for index in range(46)]
    rows = [
        {
            "cntr_tm": f"{item.strftime('%Y%m%d')}131500",
            "open_pric": "20000",
            "high_pric": "20100",
            "low_pric": "19900",
            "cur_prc": "20000",
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
        }
    )
    admissions = []

    def acquire(**kwargs):
        admissions.append(kwargs)
        return SimpleNamespace(admitted=True, reason="shared_read_rate_admitted")

    monkeypatch.setattr(research.kiwoom_utils, "acquire_kiwoom_read_capacity", acquire)

    fetch_sor_history(
        symbol="010140",
        token="CACHED",
        start_date=start,
        end_date=dates[-1],
        post=lambda *args, **kwargs: FakeResponse(
            {"return_code": 0, "stk_min_pole_chart_qry": rows}
        ),
        page_delay_sec=0,
        shared_read_control_enabled=True,
    )

    assert len(admissions) == 1
    assert admissions[0]["request_owner"] == ("low_price_two_leg_entry_spot_research")
    assert admissions[0]["request_class"] == "source_only"
    assert admissions[0]["request_code"] == "010140_AL"


def test_fetch_waits_and_retries_the_same_continuation_page_on_shared_defer(
    monkeypatch,
):
    start = date(2026, 6, 5)
    dates = [start + timedelta(days=index) for index in range(46)]
    rows = [
        {
            "cntr_tm": f"{item.strftime('%Y%m%d')}131500",
            "open_pric": "20000",
            "high_pric": "20100",
            "low_pric": "19900",
            "cur_prc": "20000",
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
        }
    )
    admissions = iter(
        [
            SimpleNamespace(admitted=False, reason="source_only_reserve"),
            SimpleNamespace(admitted=False, reason="source_only_reserve"),
            SimpleNamespace(admitted=True, reason="shared_read_rate_admitted"),
        ]
    )
    sleeps = []
    post_calls = []
    monkeypatch.setattr(
        research.kiwoom_utils,
        "acquire_kiwoom_read_capacity",
        lambda **_kwargs: next(admissions),
    )

    bars, meta = fetch_sor_history(
        symbol="010140",
        token="CACHED",
        start_date=start,
        end_date=dates[-1],
        post=lambda *args, **kwargs: (
            post_calls.append((args, kwargs))
            or FakeResponse({"return_code": 0, "stk_min_pole_chart_qry": rows})
        ),
        page_delay_sec=0,
        shared_read_control_enabled=True,
        shared_defer_max_attempts=2,
        shared_defer_delay_sec=0.5,
        sleeper=sleeps.append,
    )

    assert len(bars) == 46
    assert len(post_calls) == 1
    assert sleeps == [0.5, 0.5]
    assert meta["shared_read_deferred_count"] == 2
    assert meta["shared_read_deferred_wait_sec"] == 1.0


def test_fetch_accepts_expanding_clean_baseline_trading_day_count():
    start = date(2026, 6, 5)
    dates = [start + timedelta(days=index) for index in range(47)]
    rows = [
        {
            "cntr_tm": f"{item.strftime('%Y%m%d')}131500",
            "open_pric": "20000",
            "high_pric": "20100",
            "low_pric": "19900",
            "cur_prc": "20000",
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
        }
    )

    bars, meta = fetch_sor_history(
        symbol="010140",
        token="CACHED",
        start_date=start,
        end_date=dates[-1],
        post=lambda *args, **kwargs: FakeResponse(
            {"return_code": 0, "stk_min_pole_chart_qry": rows}
        ),
        page_delay_sec=0,
        expected_trading_day_count=47,
    )

    assert len(bars) == 47
    assert meta["expected_trading_date_count"] == 47
    assert meta["source_quality_status"] == "PASS"


def _episode(day: date, signal_minute: int, *, net_profit_pct: float) -> dict:
    timestamp = datetime.combine(day, time(13, signal_minute), tzinfo=KST)
    return {
        "date": day.isoformat(),
        "signal_at": timestamp.isoformat(),
        "signal_close": 20_000,
        "observed_drawdown_pct": 2.0,
        "observed_near_low_pct": 0.05,
        "legs": [
            {
                "status": "COMPLETE",
                "entry_price": 20_000,
                "target_price": 20_100,
                "net_profit_pct": net_profit_pct,
            },
            {
                "status": "COMPLETE",
                "entry_price": 19_950,
                "target_price": 20_050,
                "net_profit_pct": net_profit_pct,
            },
        ],
    }


def _contexts(
    *,
    holdout_candidate_net: float,
    baseline_net: float = -0.10,
    total_days: int = 46,
    calibration_days: int = 30,
) -> dict[date, DayContext]:
    started = date(2026, 6, 5)
    result = {}
    for index in range(total_days):
        day = started + timedelta(days=index)
        first = SignalFeature(
            0,
            datetime.combine(day, time(13, 15), tzinfo=KST),
            20_000,
            1.25,
            0.20,
        )
        second = SignalFeature(
            1,
            datetime.combine(day, time(13, 20), tzinfo=KST),
            20_000,
            2.0,
            0.05,
        )
        candidate_net = 0.20 if index < calibration_days else holdout_candidate_net
        result[day] = DayContext(
            day,
            (),
            {30: (first, second)},
            {
                0: _episode(day, 15, net_profit_pct=baseline_net),
                1: _episode(day, 20, net_profit_pct=candidate_net),
            },
        )
    return result


def test_profile_selection_uses_calibration_then_requires_untouched_holdout(
    monkeypatch,
):
    candidate = SpotCandidate(13 * 60 + 20, 13 * 60 + 29, 30, 1.50, 0.10)
    monkeypatch.setattr(research, "candidate_grid", lambda profile: (candidate,))
    profile = RESEARCH_PROFILES["candidate_007660_midday"]

    passed = select_profile_spot(profile, _contexts(holdout_candidate_net=0.20))
    assert passed["calibration_winner"]["parameters"] == candidate.public()
    assert passed["decision"] == "holdout_pass_source_only_early_candidate"
    assert passed["selected"]["parameters"] == candidate.public()

    failed = select_profile_spot(profile, _contexts(holdout_candidate_net=-0.20))
    assert failed["calibration_winner"]["parameters"] == candidate.public()
    assert failed["decision"] == "holdout_failed_keep_baseline"
    assert failed["selected"]["parameters"] != candidate.public()


def test_profile_selection_expands_calibration_and_keeps_16_day_holdout(
    monkeypatch,
):
    candidate = SpotCandidate(13 * 60 + 20, 13 * 60 + 29, 30, 1.50, 0.10)
    monkeypatch.setattr(research, "candidate_grid", lambda profile: (candidate,))

    result = select_profile_spot(
        RESEARCH_PROFILES["candidate_007660_midday"],
        _contexts(
            holdout_candidate_net=0.20,
            total_days=47,
            calibration_days=31,
        ),
        calibration_days=31,
        holdout_days=16,
    )

    assert result["date_split"]["calibration_trading_day_count"] == 31
    assert result["date_split"]["holdout_trading_day_count"] == 16
    assert result["decision"] == "holdout_pass_source_only_early_candidate"


def test_profile_selection_requires_strict_holdout_improvement(monkeypatch):
    candidate = SpotCandidate(13 * 60 + 20, 13 * 60 + 29, 30, 1.50, 0.10)
    monkeypatch.setattr(research, "candidate_grid", lambda profile: (candidate,))

    result = select_profile_spot(
        RESEARCH_PROFILES["candidate_007660_midday"],
        _contexts(holdout_candidate_net=0.10, baseline_net=0.10),
    )

    assert result["decision"] == "holdout_positive_not_better_keep_baseline"
    assert result["recommended_action"] == "retain_existing_baseline"
    assert result["selected"]["parameters"] != candidate.public()


def test_calibration_half_negative_is_diagnostic_when_overall_and_holdout_positive(
    monkeypatch,
):
    candidate = SpotCandidate(13 * 60 + 20, 13 * 60 + 29, 30, 1.50, 0.10)
    monkeypatch.setattr(research, "candidate_grid", lambda profile: (candidate,))
    contexts = _contexts(holdout_candidate_net=0.20)
    for index, context in enumerate(contexts.values()):
        if 15 <= index < 30:
            context.outcome_cache[1]["legs"][0]["net_profit_pct"] = -0.10
            context.outcome_cache[1]["legs"][1]["net_profit_pct"] = -0.10

    result = select_profile_spot(RESEARCH_PROFILES["candidate_007660_midday"], contexts)

    assert result["decision"] == "holdout_pass_source_only_early_candidate"
    assert result["runtime_effect"] is False
    assert result["calibration_half_diagnostics"]["second_half_positive_ev"] is False
    assert result["calibration_ready_candidate_count"] == 1
    assert result["calibration_gate_counts"]["sample_ready"] == 1
    assert result["calibration_gate_counts"]["both_halves_positive_ev"] == 0
    assert result["best_diagnostic_candidate"]["parameters"] == candidate.public()


def test_higher_trade_ev_with_lower_same_window_profit_is_not_recommended(monkeypatch):
    candidate = SpotCandidate(800, 809, 30, 1.50, 0.10)
    monkeypatch.setattr(research, "candidate_grid", lambda profile: (candidate,))
    contexts = _contexts(holdout_candidate_net=0.20, baseline_net=0.10)
    for index, context in enumerate(contexts.values()):
        if index % 3 != 0:
            context.features[30] = context.features[30][:1]
    result = select_profile_spot(RESEARCH_PROFILES["candidate_007660_midday"], contexts)
    assert (
        result["calibration_winner"]["holdout"]["notional_weighted_ev_pct"]
        > result["baseline"]["holdout"]["notional_weighted_ev_pct"]
    )
    assert result["paired_economics"]["net_profit_uplift_krw_per_observation_day"] < 0
    assert result["decision"] == "holdout_positive_not_better_keep_baseline"
    assert "episodes" in result["baseline"]["full"]


def test_held_inventory_blocks_following_days_and_holdout_without_mutating_cache():
    contexts = _contexts(holdout_candidate_net=0.2)
    dates = sorted(contexts)
    first = contexts[dates[0]].outcome_cache[1]
    first["legs"][0].update(status="HELD", active_unrealized_pct=-0.1)
    first["legs"][0].pop("net_profit_pct")
    candidate = SpotCandidate(800, 809, 30, 1.5, 0.10)
    full = research.evaluate_candidate(
        candidate, contexts, dates, include_episodes=True
    )
    holdout = research.evaluate_candidate(candidate, contexts, dates[-16:])
    assert full["signal_episodes"] == 1
    assert len(full["custody_blocked_dates"]) == 45
    assert holdout["signal_episodes"] == 0
    assert holdout["carry_in_held_legs"] == 1
    assert holdout["custody_resolution_required"] is True
    assert "holding_completed_bars" not in first["legs"][0]
    assert full["runtime_effect"] is False


def test_existing_axis_replay_finds_later_signal_with_execution_fields_unchanged():
    contexts = _contexts(holdout_candidate_net=0.2, baseline_net=0.05)
    for context in contexts.values():
        first, second = context.features[30]
        first = research.replace(
            first, timestamp=first.timestamp.replace(minute=20), drawdown_pct=0.8
        )
        second = research.replace(
            second, timestamp=second.timestamp.replace(minute=25), drawdown_pct=1.0
        )
        context.features[30] = (first, second)
        context.outcome_cache[0]["signal_at"] = first.timestamp.isoformat()
        context.outcome_cache[1]["signal_at"] = second.timestamp.isoformat()
    from src.trading.low_price_two_leg.profiles import get_profile

    profile = get_profile("samsung_heavy_midday", target_date=max(contexts))
    replay = research.existing_axis_economic_replay(profile, contexts)
    drawdown = next(
        item
        for item in replay["alternatives"]
        if item["axis"] == "rolling_high_drawdown_pct"
    )
    assert drawdown["comparison"]["net_profit_improved"] is True
    assert (
        drawdown["outcome"]["episodes"][0]["signal_at"]
        != replay["current_outcome"]["episodes"][0]["signal_at"]
    )
    for key in (
        "entry_offsets_ticks",
        "entry_valid_completed_bars",
        "target_ticks",
        "lookback_bars",
    ):
        assert drawdown["parameters"][key] == replay["current_parameters"][key]
    assert replay["allowed_runtime_apply"] is False
    assert research.valid_existing_axis_economic_replay(replay)
    drawdown["parameters"]["target_ticks"] += 1
    assert not research.valid_existing_axis_economic_replay(replay)


def test_paired_economics_rejects_different_windows_and_costs():
    contexts = _contexts(holdout_candidate_net=0.2)
    candidate = SpotCandidate(800, 809, 30, 1.5, 0.1)
    dates = sorted(contexts)
    current = research.evaluate_candidate(candidate, contexts, dates[:16])
    different = research.evaluate_candidate(candidate, contexts, dates[-16:])
    assert (
        research.paired_economics(current, different)["comparable_observation_window"]
        is False
    )
    assert (
        research.paired_economics(current, dict(current, cost_pct=0.2))[
            "comparable_observation_window"
        ]
        is False
    )


def test_cached_fill_outcomes_do_not_reuse_another_lookback_signal_features():
    contexts = _contexts(holdout_candidate_net=0.2)
    context = contexts[min(contexts)]
    signal = context.features[30][0]
    candidate = SpotCandidate(795, 809, 30, 0.75, 0.35)
    first = research._episode(context, signal, candidate)
    changed_signal = research.replace(signal, drawdown_pct=0.91, near_low_pct=0.07)
    second = research._episode(context, changed_signal, candidate)
    assert first["observed_drawdown_pct"] == 1.25
    assert second["observed_drawdown_pct"] == 0.91
    assert second["observed_near_low_pct"] == 0.07
    assert first["legs"] == second["legs"]
    assert context.outcome_cache[0]["observed_drawdown_pct"] == 2.0
