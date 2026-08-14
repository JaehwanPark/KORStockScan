from __future__ import annotations

from datetime import date, datetime, time, timedelta

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
    assert held["active_unrealized_pct"] == pytest.approx(-2.2)
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


def test_profile_selection_exposes_best_failed_calibration_candidate(monkeypatch):
    candidate = SpotCandidate(13 * 60 + 20, 13 * 60 + 29, 30, 1.50, 0.10)
    monkeypatch.setattr(research, "candidate_grid", lambda profile: (candidate,))
    contexts = _contexts(holdout_candidate_net=0.20)
    for index, context in enumerate(contexts.values()):
        if 15 <= index < 30:
            context.outcome_cache[1]["legs"][0]["net_profit_pct"] = -0.10
            context.outcome_cache[1]["legs"][1]["net_profit_pct"] = -0.10

    result = select_profile_spot(RESEARCH_PROFILES["candidate_007660_midday"], contexts)

    assert result["decision"] == "no_robust_calibration_candidate_do_not_promote"
    assert result["recommended_action"] == "do_not_activate_profile_from_this_evidence"
    assert result["recommended_spot"] is None
    assert result["calibration_ready_candidate_count"] == 0
    assert result["calibration_gate_counts"]["sample_ready"] == 1
    assert result["calibration_gate_counts"]["both_halves_positive_ev"] == 0
    assert result["best_diagnostic_candidate"]["parameters"] == candidate.public()
