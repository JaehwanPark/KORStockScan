from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from src.engine.monitoring import (
    low_price_two_leg_expanded_candidate_research as expanded,
)
from src.engine.monitoring.low_price_two_leg_entry_spot_research import (
    Bar,
    ResearchError,
    build_day_contexts,
    fetch_sor_history,
)
from src.trading.low_price_two_leg.profiles import PROFILES

LEGACY_TEST_RESEARCH_PROFILES = {
    **expanded.RESEARCH_PROFILES,
    **expanded._new_symbol_profiles({"017670": "SK텔레콤", "007660": "이수페타시스"}),
}


class FakeResponse:
    status_code = 200
    headers = {}

    def __init__(self, rows):
        self._rows = rows

    def json(self):
        return {"return_code": 0, "stk_min_pole_chart_qry": self._rows}


def test_expanded_profiles_separate_new_symbols_and_inactive_existing_sessions():
    assert len(expanded.NEW_SYMBOL_PROFILES) == (
        len(expanded.CANDIDATE_SYMBOLS) * len(expanded.SESSION_WINDOWS)
    )
    assert len(expanded.RESEARCH_PROFILES) == (
        len(expanded.NEW_SYMBOL_PROFILES)
        + len(expanded.EXISTING_SYMBOL_TIME_EXTENSION_PROFILES)
        + len(expanded.EXISTING_SYMBOL_LOGIC_IMPROVEMENT_PROFILES)
    )
    assert set(expanded.CANDIDATE_SYMBOLS).isdisjoint(
        profile.symbol for profile in PROFILES.values()
    )
    assert {
        (profile.symbol, profile.session)
        for profile in expanded.NEW_SYMBOL_PROFILES.values()
    } == {
        (symbol, session)
        for symbol in expanded.CANDIDATE_SYMBOLS
        for session in ("morning", "late_morning", "midday", "afternoon")
    }
    assert len(expanded.EXISTING_SYMBOL_TIME_EXTENSION_PROFILES) == (
        len(expanded.IMPLEMENTED_SYMBOLS) * len(expanded.SESSION_WINDOWS)
        - len(expanded.ACTIVE_SYMBOL_SESSIONS)
    )
    assert len(expanded.EXISTING_SYMBOL_LOGIC_IMPROVEMENT_PROFILES) == len(PROFILES)
    assert set(expanded.EXISTING_SYMBOL_LOGIC_IMPROVEMENT_PROFILES) == {
        f"logic_{profile_id}" for profile_id in PROFILES
    }
    existing_profile = expanded.EXISTING_SYMBOL_TIME_EXTENSION_PROFILES[
        "existing_006800_afternoon"
    ]
    assert existing_profile.discovery_lane == "existing_symbol_time_extension"
    assert (existing_profile.symbol, existing_profile.session) not in (
        expanded.ACTIVE_SYMBOL_SESSIONS
    )


def test_theborn_morning_is_fixed_source_only_operator_observation_candidate():
    profile = expanded.NEW_SYMBOL_PROFILES["candidate_475560_morning"]
    contract = expanded._operator_observation_contract(profile)

    assert expanded.CANDIDATE_SYMBOLS["475560"] == "더본코리아"
    assert profile.fixed_observation is True
    assert profile.policy.scan_start.strftime("%H:%M") == "09:40"
    assert profile.policy.scan_last_bar.strftime("%H:%M") == "09:59"
    assert profile.policy.lookback_bars == 20
    assert profile.policy.rolling_high_drawdown_pct == pytest.approx(0.50)
    assert profile.policy.rolling_low_proximity_pct == pytest.approx(0.35)
    assert profile.policy.entry_offsets_ticks == (0, -1)
    assert profile.policy.entry_valid_completed_bars == 5
    assert profile.policy.target_ticks == 4
    assert contract is not None
    assert contract["status"] == "source_only_keep_collecting"
    assert contract["runtime_effect"] is False
    assert contract["actual_order_submitted"] is False
    assert contract["broker_order_forbidden"] is True
    assert contract["metric_contract"] == {
        "metric_role": "fixed_episode_candidate_holdout_observation",
        "decision_authority": "source_only_observation_no_runtime_authority",
        "window_policy": (
            "clean_baseline_expanding_calibration_latest_16_trading_days_holdout"
        ),
        "sample_floor": {"signal_episodes": 3, "completed_legs": 4},
        "primary_decision_metric": "notional_weighted_ev_pct",
        "source_quality_gate": [
            "official_ka10080_success",
            "requested_start_date_fully_bracketed",
            "valid_unique_completed_sor_regular_ohlc",
            "fixed_policy_identity_match",
            "completed_legs_only_for_ev",
            "active_unrealized_separated_from_completed_ev",
        ],
        "missing_execution_evidence": [
            "prospective_fresh_bbo_spread",
            "passive_fill_feasibility",
            "spread_and_fee_adjusted_target_ev",
        ],
        "forbidden_uses": [
            "daily_policy_reoptimization",
            "automatic_machine_implementation_or_service_start",
            "automatic_runtime_or_preopen_policy_promotion",
            "minute_bar_holdout_pass_as_machine_recommendation_without_bbo_economics",
            "account_or_order_api",
            "real_order_submission",
            "provider_bot_cap_threshold_or_broker_guard_change",
            "stop_loss_or_forced_exit_creation",
            "thin_oos_or_diagnostic_win_rate_as_live_authority",
        ],
    }


def test_fixed_operator_observation_never_enters_implementation_recommendations():
    profile = expanded.NEW_SYMBOL_PROFILES["candidate_475560_morning"]
    profiles = {
        profile.profile_id: {
            "decision": "holdout_pass_source_only_early_candidate",
            "symbol": profile.symbol,
            "name": profile.name,
            "session": profile.session,
            "recommended_spot": expanded.baseline_candidate(profile).public(),
            "selected": {
                "holdout": {
                    "signal_episodes": 10,
                    "completed_legs": 20,
                    "held_legs": 0,
                    "held_leg_rate_per_filled_leg": 0.0,
                    "notional_weighted_ev_pct": 1.0,
                }
            },
            "baseline": {
                "holdout": {
                    "notional_weighted_ev_pct": 1.0,
                }
            },
        }
    }
    source_meta = {
        profile.symbol: {
            "latest_close_price": 30_000,
        }
    }

    assert (
        expanded._recommendation_rows(
            profiles,
            source_meta,
            research_profiles={profile.profile_id: profile},
        )
        == []
    )


def test_fetch_expanded_symbol_requires_explicit_research_allowlist():
    symbol = next(iter(expanded.CANDIDATE_SYMBOLS))
    started = date(2026, 6, 5)
    dates = [started + timedelta(days=index) for index in range(46)]
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

    with pytest.raises(ValueError, match="symbol_not_in_selected_profile_allowlist"):
        fetch_sor_history(
            symbol=symbol,
            token="TOKEN",
            start_date=started,
            end_date=dates[-1],
            post=lambda *args, **kwargs: FakeResponse(rows),
        )

    bars, meta = fetch_sor_history(
        symbol=symbol,
        token="TOKEN",
        start_date=started,
        end_date=dates[-1],
        post=lambda *args, **kwargs: FakeResponse(rows),
        allowed_symbols=frozenset({symbol}),
    )
    assert len(bars) == 46
    assert meta["source_quality_status"] == "PASS"


def test_expanded_report_fails_closed_on_incomplete_source_universe():
    with pytest.raises(
        ResearchError, match="all_research_symbols_source_quality_blocked"
    ):
        expanded.build_report(
            sources={},
            start_date=expanded.CLEAN_BASELINE_DATE,
            end_date=date(2026, 8, 10),
        )


def test_expanded_report_rejects_target_date_profile_policy_drift():
    end_date = date(2026, 8, 21)
    inventory = expanded._target_date_research_inventory(end_date)
    research_profiles = dict(inventory.research_profiles)
    profile_id = sorted(research_profiles)[0]
    profile = research_profiles[profile_id]
    research_profiles[profile_id] = replace(
        profile,
        policy=replace(profile.policy, target_ticks=profile.policy.target_ticks + 1),
    )

    with pytest.raises(
        ResearchError, match="research_profile_target_date_inventory_mismatch"
    ):
        expanded.build_report(
            sources={},
            start_date=expanded.CLEAN_BASELINE_DATE,
            end_date=end_date,
            candidate_symbols=inventory.candidate_symbols,
            research_profiles=research_profiles,
        )


def test_expanded_report_builds_daily_artifact_for_complete_source_universe(
    monkeypatch,
):
    end_date = date(2026, 8, 11)
    target_inventory = expanded._target_date_research_inventory(end_date)
    start_date = expanded.CLEAN_BASELINE_DATE
    trading_dates = list(expanded.clean_baseline_trading_dates(end_date))
    monkeypatch.setattr(
        expanded,
        "build_day_contexts",
        lambda bars: {item: object() for item in trading_dates},
    )
    monkeypatch.setattr(
        expanded,
        "select_profile_spot",
        lambda profile, contexts, **kwargs: {
            "symbol": profile.symbol,
            "name": profile.name,
            "session": profile.session,
            "decision": "no_calibration_candidate",
            "recommended_spot": None,
            "baseline": {
                "holdout": {
                    "signal_episodes": 0,
                    "completed_legs": 0,
                    "held_legs": 0,
                    "notional_weighted_ev_pct": None,
                }
            },
        },
    )
    sources = {
        symbol: (
            [SimpleNamespace(close_price=20_000)],
            {"source_quality_status": "PASS"},
        )
        for symbol in target_inventory.research_symbols
    }

    report = expanded.build_report(
        sources=sources,
        start_date=start_date,
        end_date=end_date,
    )

    assert report["status"] == "no_qualified_candidate"
    assert len(report["profiles"]) == len(target_inventory.research_profiles)
    assert report["trading_date_count"] == 47
    assert report["calibration_trading_day_count"] == 31
    assert report["holdout_trading_day_count"] == 16
    assert report["existing_symbol_time_extension_profile_count"] == len(
        target_inventory.time_extension_profiles
    )
    assert report["existing_symbol_logic_improvement_profile_count"] == len(
        target_inventory.logic_improvement_profiles
    )
    assert report["recommendation_count"] == 0
    assert report["runtime_effect"] is False
    assert report["operator_observation_candidate_count"] == 1
    assert set(report["operator_observation_candidate_inventory"]) == {
        "candidate_475560_morning"
    }


def test_expanded_report_quarantines_one_bad_symbol_without_blocking_others(
    monkeypatch,
):
    end_date = date(2026, 8, 11)
    target_inventory = expanded._target_date_research_inventory(end_date)
    trading_dates = list(expanded.clean_baseline_trading_dates(end_date))
    monkeypatch.setattr(
        expanded,
        "build_day_contexts",
        lambda bars: {item: object() for item in trading_dates},
    )
    monkeypatch.setattr(
        expanded,
        "select_profile_spot",
        lambda profile, contexts, **kwargs: {
            "symbol": profile.symbol,
            "name": profile.name,
            "session": profile.session,
            "decision": "no_calibration_candidate",
            "recommended_spot": None,
            "baseline": {"holdout": {"notional_weighted_ev_pct": None}},
        },
    )
    missing_symbol = sorted(target_inventory.research_symbols)[0]
    sources = {
        symbol: (
            [SimpleNamespace(close_price=20_000)],
            {"source_quality_status": "PASS"},
        )
        for symbol in target_inventory.research_symbols
        if symbol != missing_symbol
    }

    report = expanded.build_report(
        sources=sources,
        start_date=expanded.CLEAN_BASELINE_DATE,
        end_date=end_date,
    )

    assert report["status"] == "partial_source_quality"
    assert report["source_quarantine"] == {missing_symbol: "source_missing"}
    assert (
        report["eligible_source_symbol_count"]
        == len(target_inventory.research_symbols) - 1
    )
    assert all(
        item["decision"] == "source_quality_quarantined_no_evaluation"
        for item in report["profiles"].values()
        if item["symbol"] == missing_symbol
    )


def test_daily_window_expands_from_clean_baseline_and_keeps_latest_16_holdout():
    dates_0810 = expanded.clean_baseline_trading_dates(date(2026, 8, 10))
    dates_0811 = expanded.clean_baseline_trading_dates(date(2026, 8, 11))

    assert len(dates_0810) == 46
    assert len(dates_0811) == 47
    assert dates_0810[0] == dates_0811[0] == date(2026, 6, 5)
    assert dates_0811[-1] == date(2026, 8, 11)
    assert len(dates_0811[: -expanded.HOLDOUT_DAYS]) == 31
    assert len(dates_0811[-expanded.HOLDOUT_DAYS :]) == 16
    with pytest.raises(ValueError, match="target_date_not_krx_trading_day"):
        expanded.clean_baseline_trading_dates(date(2026, 8, 9))


def test_dynamic_universe_adds_ranked_under_100000_symbols_only(tmp_path):
    path = tmp_path / "daily.csv"
    (tmp_path / expanded.DEFAULT_DYNAMIC_UNIVERSE_DIAGNOSTIC_PATH.name).write_text(
        '{"latest_date":"2026-08-11","selected_count":3}', encoding="utf-8"
    )
    path.write_text(
        "date,code,name,close,score_rank\n"
        "2026-08-11,000990,DB하이텍,93200,2\n"
        "2026-08-11,042700,고가종목,213000,1\n"
        "2026-08-11,017670,기존검토종목,86000,3\n",
        encoding="utf-8",
    )

    result = expanded._dynamic_candidate_symbols(date(2026, 8, 11), path=path)

    assert result == {"000990": "DB하이텍"}


def test_dynamic_universe_uses_latest_completed_snapshot_not_after_target(tmp_path):
    path = tmp_path / "daily.csv"
    diagnostic_path = tmp_path / "completion.json"
    diagnostic_path.write_text(
        '{"latest_date":"2026-08-11","selected_count":1}', encoding="utf-8"
    )
    path.write_text(
        "date,code,name,close,score_rank\n2026-08-11,000990,DB하이텍,93200,2\n",
        encoding="utf-8",
    )

    source_date, result = expanded._dynamic_candidate_snapshot(
        date(2026, 8, 12), path=path, diagnostic_path=diagnostic_path
    )

    assert source_date == date(2026, 8, 11)
    assert result == {"000990": "DB하이텍"}

    diagnostic_path.write_text(
        '{"latest_date":"2026-08-13","selected_count":1}', encoding="utf-8"
    )
    assert expanded._dynamic_candidate_snapshot(
        date(2026, 8, 12), path=path, diagnostic_path=diagnostic_path
    ) == (None, {})

    diagnostic_path.write_text(
        '{"latest_date":"2026-08-11","selected_count":2}', encoding="utf-8"
    )
    assert expanded._dynamic_candidate_snapshot(
        date(2026, 8, 12), path=path, diagnostic_path=diagnostic_path
    ) == (None, {})


def test_dynamic_universe_uses_target_date_implemented_symbol_inventory(tmp_path):
    target_date = date(2026, 8, 21)
    target_inventory = expanded._target_date_research_inventory(target_date)
    path = tmp_path / "daily.csv"
    diagnostic_path = tmp_path / "completion.json"
    diagnostic_path.write_text(
        '{"latest_date":"2026-08-21","selected_count":1}', encoding="utf-8"
    )
    path.write_text(
        "date,code,name,close,score_rank\n"
        "2026-08-21,111770,historical-dynamic-candidate,38600,1\n",
        encoding="utf-8",
    )

    assert "111770" in expanded.IMPLEMENTED_SYMBOLS
    assert "111770" not in target_inventory.implemented_symbols
    source_date, symbols = expanded._dynamic_candidate_snapshot(
        target_date,
        path=path,
        diagnostic_path=diagnostic_path,
        implemented_symbols=target_inventory.implemented_symbols,
    )

    assert source_date == target_date
    assert symbols == {"111770": "historical-dynamic-candidate"}


def test_dynamic_universe_report_pins_inventory_for_notifier_validation(monkeypatch):
    end_date = date(2026, 8, 21)
    trading_dates = list(expanded.clean_baseline_trading_dates(end_date))
    base_inventory = expanded._target_date_research_inventory(end_date)
    candidate_symbols = {
        **base_inventory.candidate_symbols,
        "000990": "DB하이텍",
    }
    target_inventory = expanded._target_date_research_inventory(
        end_date,
        candidate_symbols=candidate_symbols,
    )
    research_profiles = target_inventory.research_profiles
    source_symbols = target_inventory.research_symbols
    monkeypatch.setattr(
        expanded,
        "build_day_contexts",
        lambda bars: {item: object() for item in trading_dates},
    )
    monkeypatch.setattr(
        expanded,
        "select_profile_spot",
        lambda profile, contexts, **kwargs: {
            "symbol": profile.symbol,
            "name": profile.name,
            "session": profile.session,
            "decision": "no_calibration_candidate",
            "recommended_spot": None,
            "baseline": {"holdout": {"notional_weighted_ev_pct": None}},
        },
    )

    report = expanded.build_report(
        sources={
            symbol: (
                [SimpleNamespace(close_price=20_000)],
                {"source_quality_status": "PASS"},
            )
            for symbol in source_symbols
        },
        start_date=expanded.CLEAN_BASELINE_DATE,
        end_date=end_date,
        candidate_symbols=candidate_symbols,
        research_profiles=research_profiles,
        dynamic_universe_source_date=end_date,
    )

    assert report["candidate_symbols"]["000990"] == "DB하이텍"
    assert report["dynamic_universe_source_date"] == "2026-08-21"
    assert report["new_symbol_profile_count"] == len(candidate_symbols) * 4
    assert report["existing_symbol_universe_size"] == 13
    assert report["existing_symbol_logic_improvement_profile_count"] == 27
    assert (
        len(expanded.LIVE_PROFILES)
        > report["existing_symbol_logic_improvement_profile_count"]
    )
    assert expanded.CandidateRecommendationNotifier._valid_report(report)

    report["dynamic_universe_source_date"] = "2026-08-24"
    assert not expanded.CandidateRecommendationNotifier._valid_report(report)
    report["dynamic_universe_source_date"] = None
    assert not expanded.CandidateRecommendationNotifier._valid_report(report)


def _profile_result(
    *,
    symbol: str,
    name: str,
    session: str,
    candidate_ev: float,
    baseline_ev: float,
    held_legs: int = 0,
    held_rate: float = 0.0,
    held_mark_pct: float | None = None,
) -> dict:
    return {
        "symbol": symbol,
        "name": name,
        "session": session,
        "baseline_policy_source": "target_date_applied_policy",
        "baseline_policy_hash": "test-applied-policy-hash",
        "decision": "holdout_pass_source_only_early_candidate",
        "recommended_spot": {
            "scan_start": "14:15",
            "scan_end": "14:24",
            "lookback_bars": 15,
            "rolling_high_drawdown_pct": 1.5,
            "rolling_low_proximity_pct": 0.2,
        },
        "selected": {
            "holdout": {
                "signal_episodes": 4,
                "completed_legs": 7,
                "held_legs": held_legs,
                "held_leg_rate_per_filled_leg": held_rate,
                "active_unrealized_notional_weighted_pct": held_mark_pct,
                "worst_filled_max_adverse_excursion_pct": -0.5,
                "realized_net_profit_krw_per_episode": 100.0,
                "notional_weighted_ev_pct": candidate_ev,
            }
        },
        "baseline": {"holdout": {"notional_weighted_ev_pct": baseline_ev}},
    }


def test_recommendations_rank_profiles_and_enforce_daily_price_cap():
    profiles = {
        "existing_080220_afternoon": _profile_result(
            symbol="080220",
            name="제주반도체",
            session="afternoon",
            candidate_ev=0.08,
            baseline_ev=0.01,
        ),
        "candidate_017670_midday": _profile_result(
            symbol="017670",
            name="SK텔레콤",
            session="midday",
            candidate_ev=0.03,
            baseline_ev=0.01,
        ),
        "candidate_007660_afternoon": _profile_result(
            symbol="007660",
            name="이수페타시스",
            session="afternoon",
            candidate_ev=0.50,
            baseline_ev=0.01,
        ),
    }
    source_meta = {
        "080220": {"latest_close_price": 24_000},
        "017670": {"latest_close_price": 65_000},
        "007660": {"latest_close_price": 100_500},
    }

    rows = expanded._recommendation_rows(
        profiles,
        source_meta,
        research_profiles=LEGACY_TEST_RESEARCH_PROFILES,
    )

    assert [row["profile_id"] for row in rows] == [
        "existing_080220_afternoon",
        "candidate_017670_midday",
    ]
    assert rows[0]["price_band"] == "under_50000_krw"
    assert rows[1]["price_band"] == "50000_to_100000_krw"
    assert rows[0]["ev_uplift_pct_point"] == pytest.approx(0.07)
    assert all(row["runtime_effect"] is False for row in rows)


def test_recommendation_accepts_manageable_carry_and_rejects_excess_carry():
    manageable = _profile_result(
        symbol="017670",
        name="SK텔레콤",
        session="midday",
        candidate_ev=0.05,
        baseline_ev=0.01,
        held_legs=1,
        held_rate=0.20,
        held_mark_pct=-2.5,
    )
    excessive = _profile_result(
        symbol="007660",
        name="이수페타시스",
        session="midday",
        candidate_ev=0.20,
        baseline_ev=0.01,
        held_legs=1,
        held_rate=0.30,
        held_mark_pct=-2.5,
    )

    rows = expanded._recommendation_rows(
        {
            "candidate_017670_midday": manageable,
            "candidate_007660_midday": excessive,
        },
        {
            "017670": {"latest_close_price": 65_000},
            "007660": {"latest_close_price": 40_000},
        },
        research_profiles=LEGACY_TEST_RESEARCH_PROFILES,
    )

    assert [row["profile_id"] for row in rows] == ["candidate_017670_midday"]
    assert rows[0]["holdout_held_leg_rate_per_filled_leg"] == pytest.approx(0.20)


def test_target_date_logic_recommendation_requires_cumulative_candidate_and_rebound():
    kst = ZoneInfo("Asia/Seoul")
    target_date = date(2026, 8, 12)
    start = datetime(2026, 8, 12, 12, 52, tzinfo=kst)
    bars = [
        Bar(
            start + timedelta(minutes=index),
            22_000,
            22_100 if index < 30 else 22_000,
            21_950,
            21_950 if index >= 29 else 22_000,
        )
        for index in range(33)
    ]
    bars[31] = Bar(bars[31].timestamp, 21_950, 22_000, 21_950, 22_000)
    bars[32] = Bar(bars[32].timestamp, 22_000, 22_050, 21_950, 22_050)
    contexts = build_day_contexts(bars)
    profile_id = "logic_samsung_heavy_midday"
    profiles = {
        profile_id: {
            "decision": "holdout_pass_source_only_early_candidate",
            "recommended_spot": {
                "scan_start": "13:20",
                "scan_end": "13:29",
                "lookback_bars": 30,
                "rolling_high_drawdown_pct": 0.5,
                "rolling_low_proximity_pct": 0.35,
                "entry_offsets_ticks": [0, -1],
                "entry_valid_completed_bars": 5,
                "target_ticks": 2,
            },
        }
    }

    rows = expanded._target_date_logic_attribution(
        profiles=profiles,
        contexts_by_symbol={"010140": contexts},
        target_date=target_date,
        applied_policy_snapshots={
            "samsung_heavy_midday": {
                "status": "ready",
                "reason": "ready",
                "policy_hash": "test-policy-hash",
                "policy": {
                    "rolling_high_drawdown_pct": 0.75,
                    "rolling_low_proximity_pct": 0.35,
                    "lookback_bars": 30,
                    "entry_valid_completed_bars": 5,
                    "quantity": 2,
                    "target_ticks": 2,
                },
            }
        },
    )
    row = next(item for item in rows if item["profile_id"] == profile_id)

    assert row["decision"] == "recommend_cumulative_logic_candidate_review"
    assert row["applied_policy_status"] == "ready"
    assert row["applied_policy_hash"] == "test-policy-hash"
    assert row["baseline_target_date"]["signal_episodes"] == 0
    assert row["candidate_target_date"]["signal_episodes"] == 1
    assert row["candidate_target_date"]["completed_legs"] == 1
    assert row["candidate_target_date"]["no_fill_legs"] == 1
    assert row["candidate_target_date"]["held_legs"] == 0
    assert row["candidate_target_date"]["notional_weighted_ev_pct"] > 0

    unavailable_rows = expanded._target_date_logic_attribution(
        profiles=profiles,
        contexts_by_symbol={"010140": contexts},
        target_date=target_date,
        applied_policy_snapshots={},
    )
    unavailable = next(
        item for item in unavailable_rows if item["profile_id"] == profile_id
    )
    assert unavailable["decision"] == "not_recommended"
    assert unavailable["reason"] == "target_date_applied_policy_unavailable"


def test_logic_research_inventory_uses_target_date_applied_policy_as_baseline():
    snapshots = {
        "samsung_heavy_midday": {
            "status": "ready",
            "reason": "ready",
            "policy_hash": "applied-hash",
            "policy": {
                "rolling_high_drawdown_pct": 1.0,
                "rolling_low_proximity_pct": 0.25,
                "lookback_bars": 30,
                "entry_valid_completed_bars": 5,
                "quantity": 2,
                "target_ticks": 2,
            },
        }
    }

    _, profiles = expanded._research_inventory(
        expanded.CANDIDATE_SYMBOLS,
        applied_policy_snapshots=snapshots,
    )
    policy = profiles["logic_samsung_heavy_midday"].policy

    assert policy.rolling_high_drawdown_pct == 1.0
    assert policy.rolling_low_proximity_pct == 0.25


def test_existing_symbol_time_extension_recommendation_preserves_active_profile_lineage():
    profiles = {
        "existing_006800_afternoon": _profile_result(
            symbol="006800",
            name="미래에셋증권",
            session="afternoon",
            candidate_ev=0.08,
            baseline_ev=0.01,
        )
    }

    rows = expanded._recommendation_rows(
        profiles, {"006800": {"latest_close_price": 25_000}}
    )

    assert len(rows) == 1
    assert rows[0]["discovery_lane"] == "existing_symbol_time_extension"
    assert rows[0]["active_profile_ids_for_symbol"] == sorted(
        profile_id
        for profile_id, profile in PROFILES.items()
        if profile.symbol == "006800"
    )
    assert (rows[0]["symbol"], rows[0]["session"]) not in (
        expanded.ACTIVE_SYMBOL_SESSIONS
    )


def _notification_report(recommendations: list[dict] | None = None) -> dict:
    target_date = date(2026, 8, 24)
    target_inventory = expanded._target_date_research_inventory(target_date)
    rows = recommendations or []
    new_rows = [row for row in rows if row.get("discovery_lane") == "new_symbol"]
    existing_rows = [
        row
        for row in rows
        if row.get("discovery_lane") == "existing_symbol_time_extension"
    ]
    logic_rows = [
        row
        for row in rows
        if row.get("discovery_lane") == "existing_symbol_logic_improvement"
    ]
    attribution_rows = [
        {
            "profile_id": profile_id,
            "active_profile_id": profile_id.removeprefix("logic_"),
            "symbol": profile.symbol,
            "name": profile.name,
            "session": profile.session,
            "decision": "not_recommended",
            "reason": "cumulative_holdout_candidate_unavailable",
            "runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }
        for profile_id, profile in (target_inventory.logic_improvement_profiles.items())
    ]
    return {
        "schema": expanded.REPORT_SCHEMA,
        "report_type": expanded.REPORT_TYPE,
        "status": "recommendations_ready" if rows else "no_qualified_candidate",
        "authority": expanded.AUTHORITY,
        "target_date": target_date.isoformat(),
        "clean_tuning_baseline_date": "2026-06-05",
        "start_date": "2026-06-05",
        "end_date": "2026-08-24",
        "trading_date_count": 55,
        "calibration_trading_day_count": 39,
        "holdout_trading_day_count": 16,
        "candidate_universe_size": len(target_inventory.candidate_symbols),
        "candidate_symbols": target_inventory.candidate_symbols,
        "existing_symbol_universe_size": len(target_inventory.implemented_symbols),
        "source_symbol_count": len(target_inventory.research_symbols),
        "new_symbol_profile_count": len(target_inventory.new_symbol_profiles),
        "existing_symbol_time_extension_profile_count": len(
            target_inventory.time_extension_profiles
        ),
        "existing_symbol_logic_improvement_profile_count": len(
            target_inventory.logic_improvement_profiles
        ),
        "eligible_source_symbol_count": len(target_inventory.research_symbols),
        "quarantined_source_symbol_count": 0,
        "source_quarantine": {},
        "source_meta": {symbol: {} for symbol in target_inventory.research_symbols},
        "research_profile_inventory": {
            profile_id: {
                "symbol": profile.symbol,
                "name": profile.name,
                "session": profile.session,
                "discovery_lane": profile.discovery_lane,
                "fixed_observation": profile.fixed_observation,
            }
            for profile_id, profile in target_inventory.research_profiles.items()
        },
        "operator_observation_candidate_count": len(
            expanded._operator_observation_inventory(target_inventory.research_profiles)
        ),
        "operator_observation_candidate_inventory": (
            expanded._operator_observation_inventory(target_inventory.research_profiles)
        ),
        "profiles": {
            profile_id: {
                "observation_candidate": expanded._operator_observation_inventory(
                    target_inventory.research_profiles
                ).get(profile_id)
            }
            for profile_id in target_inventory.research_profiles
        },
        "recommendation_count": len(rows),
        "recommendations": rows,
        "new_symbol_recommendations": new_rows,
        "new_symbol_recommendation_count": len(new_rows),
        "existing_symbol_time_extension_recommendations": existing_rows,
        "existing_symbol_time_extension_recommendation_count": len(existing_rows),
        "existing_symbol_logic_improvement_recommendations": logic_rows,
        "existing_symbol_logic_improvement_recommendation_count": len(logic_rows),
        "target_date_logic_attribution": attribution_rows,
        "target_date_logic_attribution_count": len(attribution_rows),
        "postclose_logic_recommendations": [],
        "postclose_logic_recommendation_count": 0,
        "metric_contract": expanded.METRIC_CONTRACT,
        "recommendation_only": True,
        "machine_created": False,
        "service_started": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def test_admin_notifier_retries_sends_once_and_never_creates_machine(tmp_path):
    attempts = []
    sleeps = []

    def sender(token, admin_id, message):
        attempts.append((token, admin_id, message))
        if len(attempts) < 3:
            raise OSError("temporary telegram failure")

    notifier = expanded.CandidateRecommendationNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("token", "admin"),
        sender=sender,
        enabled=True,
        max_attempts=3,
        retry_delay_sec=0.5,
        sleeper=sleeps.append,
    )
    report = _notification_report()

    assert notifier.notify(report) == "sent"
    assert notifier.notify(report) == "duplicate"
    assert len(attempts) == 3
    assert sleeps == [0.5, 0.5]
    assert "자동 기계 구현·기동·실주문 권한 없음" in attempts[-1][2]
    state = (tmp_path / "state.json").read_text(encoding="utf-8")
    assert '"machine_created": false' in state
    assert '"service_started": false' in state


def test_telegram_message_separates_new_symbol_and_existing_time_extension_lanes():
    rows = expanded._recommendation_rows(
        {
            "candidate_017670_midday": _profile_result(
                symbol="017670",
                name="SK텔레콤",
                session="midday",
                candidate_ev=0.08,
                baseline_ev=0.01,
            ),
            "existing_006800_afternoon": _profile_result(
                symbol="006800",
                name="미래에셋증권",
                session="afternoon",
                candidate_ev=0.07,
                baseline_ev=0.01,
            ),
        },
        {
            "017670": {"latest_close_price": 65_000},
            "006800": {"latest_close_price": 25_000},
        },
        research_profiles=LEGACY_TEST_RESEARCH_PROFILES,
    )

    message = expanded.build_telegram_message(_notification_report(rows))

    assert "[신규 종목]" in message
    assert "[기존 종목·신규 시간대]" in message
    assert "SK텔레콤(017670)" in message
    assert "미래에셋증권(006800)" in message


def test_admin_notifier_fails_closed_for_invalid_authority(tmp_path):
    report = _notification_report()
    report["runtime_effect"] = True
    notifier = expanded.CandidateRecommendationNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("token", "admin"),
        sender=lambda *args: pytest.fail("invalid report must not be sent"),
        enabled=True,
    )

    assert notifier.notify(report) == "invalid_report"

    report = _notification_report()
    report["status"] = "recommendations_ready"
    assert notifier.notify(report) == "invalid_report"

    report = _notification_report()
    report["start_date"] = "2026-06-08"
    assert notifier.notify(report) == "invalid_report"

    report = _notification_report()
    report["operator_observation_candidate_inventory"]["candidate_475560_morning"][
        "policy"
    ]["target_ticks"] = 2
    assert notifier.notify(report) == "invalid_report"


def test_admin_notifier_exposes_exhausted_delivery_retries(tmp_path):
    attempts = []

    def sender(*args):
        attempts.append(args)
        raise OSError("telegram unavailable")

    notifier = expanded.CandidateRecommendationNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("token", "admin"),
        sender=sender,
        enabled=True,
        max_attempts=3,
        retry_delay_sec=0,
        sleeper=lambda _: None,
    )

    assert notifier.notify(_notification_report()) == "send_failed"
    assert len(attempts) == 3
    assert not (tmp_path / "state.json").exists()


def test_default_target_date_never_uses_an_incomplete_regular_session():
    assert expanded._default_target_date(
        now=expanded.datetime(2026, 8, 11, 14, 0, tzinfo=expanded.KST)
    ) == date(2026, 8, 10)
    assert expanded._default_target_date(
        now=expanded.datetime(2026, 8, 11, 20, 10, tzinfo=expanded.KST)
    ) == date(2026, 8, 11)


def test_source_quality_blocked_result_is_reported_to_admin_without_recommendation(
    tmp_path,
):
    report = expanded.build_source_quality_blocked_report(
        start_date=date(2026, 6, 5),
        end_date=date(2026, 8, 11),
        reason="015760_source_quality_fail",
    )
    report["telegram_status"] = "not_requested"
    sent = []
    notifier = expanded.CandidateRecommendationNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("token", "admin"),
        sender=lambda token, admin, message: sent.append(message),
        enabled=True,
    )

    assert report["status"] == "source_quality_blocked"
    assert report["recommendations"] == []
    assert notifier.notify(report) == "sent"
    assert "source-quality 문제로 신규 추천을 산출하지 않았습니다" in sent[0]
    assert "015760_source_quality_fail" in sent[0]
    assert "관찰 입력 차단(source-quality)" in sent[0]
    assert "OOS 0/3" not in sent[0]


def test_telegram_transport_requires_explicit_ok_response(monkeypatch):
    class TelegramResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"ok": false, "description": "chat not found"}'

    monkeypatch.setattr(
        expanded.request, "urlopen", lambda request, timeout: TelegramResponse()
    )

    with pytest.raises(RuntimeError, match="telegram_send_not_ok"):
        expanded._send_telegram("token", "admin", "message")


def test_malformed_postclose_logic_recommendation_is_rejected_without_error():
    assert not expanded._valid_postclose_logic_recommendation(
        {
            "applied_policy_status": "ready",
            "applied_policy_reason": "ready",
            "applied_policy_hash": "hash",
            "baseline_target_date": {},
            "candidate_target_date": {"notional_weighted_ev_pct": None},
        }
    )


def test_daily_network_failure_becomes_source_quality_admin_artifact(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        expanded.kiwoom_utils, "get_cached_kiwoom_token", lambda: "TOKEN"
    )

    def fail_fetch(**kwargs):
        raise expanded.requests.ConnectionError("network unavailable")

    monkeypatch.setattr(expanded, "fetch_sor_history", fail_fetch)

    assert (
        expanded.main(
            [
                "--target-date",
                "2026-08-11",
                "--output-dir",
                str(tmp_path),
                "--write",
            ]
        )
        == 0
    )
    report = expanded.json.loads(
        (
            tmp_path / "low_price_two_leg_expanded_candidate_research_2026-08-11.json"
        ).read_text(encoding="utf-8")
    )
    assert report["status"] == "source_quality_blocked"
    assert report["telegram_status"] == "not_requested"
    assert "network unavailable" in report["source_quality_reasons"][0]
