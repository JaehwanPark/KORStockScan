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
        "metric_contract": {"decision_authority": "widget_advisory_only"},
        "advisory": {
            "state": state,
            "session": market_session,
            "entry_price_low": entry_high,
            "entry_price_high": entry_high,
            "invalidation_price": invalidation,
            "observed_at": observed_at.isoformat(),
            "valid_until": (observed_at + timedelta(seconds=60)).isoformat(),
            "source_quality": {"status": "PASS", "issues": []},
            "provenance": {
                "market_venue": market_venue,
                "quote_request_code": (
                    "005930_NX" if market_venue == "NXT" else "005930"
                ),
            },
            "authority": "widget_advisory_only",
            "runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
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
    signal = _row(
        start,
        100_000,
        state="ENTRY_READY",
        entry_high=100_000,
        invalidation=99_700,
        observation_kind="state_transition",
    )
    signal["advisory"]["required_actionable_confirmations"] = 3
    signal["advisory"]["calibration_policy"] = {
        "policy_version": "widget_advisory_policy_2026-08-03",
        "effective_date": "2026-08-03",
    }
    rows = [
        signal,
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
    assert horizon_3["widget_policy_version"] == ("widget_advisory_policy_2026-08-03")
    assert horizon_3["required_actionable_confirmations"] == 3
    assert horizon_3["market_venue"] == "KRX"
    assert horizon_3["actual_order_submitted"] is False
    assert report["metric_contract"]["forbidden_uses"]


def test_mfe_clock_starts_only_after_exact_entry_touch():
    start = datetime(2026, 8, 3, 9, 10, tzinfo=KST)
    rows = [
        _row(
            start,
            100_500,
            state="ENTRY_READY",
            entry_high=100_000,
            observation_kind="state_transition",
        ),
        _row(start + timedelta(minutes=1), 100_400, line_number=2),
        _row(start + timedelta(minutes=2), 100_000, line_number=3),
        _row(start + timedelta(minutes=3), 100_300, line_number=4),
        _row(start + timedelta(minutes=4), 100_600, line_number=5),
    ]

    report = evaluation.build_daily_evaluation(rows, target_date=start.date())
    horizon_1 = next(row for row in report["outcomes"] if row["horizon_minutes"] == 1)

    assert horizon_1["entry_touch_status"] == "ENTRY_TOUCHED"
    assert (
        horizon_1["entry_touched_at_kst"] == (start + timedelta(minutes=2)).isoformat()
    )
    assert horizon_1["mfe_pct"] == 0.3


def test_completed_bar_only_entry_overlap_is_ambiguous_and_excluded():
    start = datetime(2026, 8, 3, 9, 10, tzinfo=KST)
    rows = [
        _row(
            start,
            100_500,
            state="ENTRY_READY",
            entry_high=100_000,
            observation_kind="state_transition",
        ),
        _row(
            start + timedelta(minutes=1),
            100_400,
            high=100_600,
            low=99_900,
            bar_start=start,
            line_number=2,
        ),
        _row(start + timedelta(minutes=2), 100_300, line_number=3),
    ]

    report = evaluation.build_daily_evaluation(rows, target_date=start.date())
    horizon_1 = next(row for row in report["outcomes"] if row["horizon_minutes"] == 1)

    assert horizon_1["entry_touch_status"] == "ENTRY_AMBIGUOUS"
    assert horizon_1["evaluation_eligible"] is False
    assert horizon_1["mfe_pct"] is None


def test_sparse_post_touch_window_is_excluded_for_coverage():
    start = datetime(2026, 8, 3, 9, 10, tzinfo=KST)
    rows = [
        _row(
            start,
            100_000,
            state="ENTRY_READY",
            entry_high=100_000,
            observation_kind="state_transition",
        ),
        _row(start + timedelta(minutes=1), 100_100, line_number=2),
        _row(start + timedelta(minutes=5), 100_500, line_number=3),
    ]

    report = evaluation.build_daily_evaluation(rows, target_date=start.date())
    horizon_5 = next(row for row in report["outcomes"] if row["horizon_minutes"] == 5)

    assert horizon_5["evaluation_status"] == "INSUFFICIENT_COVERAGE"
    assert horizon_5["coverage_ratio"] < 0.8
    assert horizon_5["evaluation_eligible"] is False


def test_session_coverage_counts_only_source_quality_passed_minutes():
    observed_at = datetime(2026, 8, 3, 9, 10, tzinfo=KST)
    passed = _row(observed_at, 100_000)
    blocked = _row(observed_at + timedelta(minutes=1), 100_100)
    blocked["advisory"]["source_quality"] = {
        "status": "BLOCKED",
        "issues": ["quote_stale"],
    }

    krx = next(
        item
        for item in evaluation._session_coverage([passed, blocked])
        if item["market_session"] == "KRX_REGULAR"
    )

    assert krx["total_observed_minute_count"] == 2
    assert krx["observed_minute_count"] == 1


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


def test_signal_with_invalid_widget_authority_is_excluded_from_evaluation():
    start = datetime(2026, 8, 3, 9, 10, tzinfo=KST)
    signal = _row(
        start,
        100_000,
        state="ENTRY_READY",
        entry_high=100_000,
        observation_kind="state_transition",
    )
    signal["advisory"]["runtime_effect"] = True
    rows = [signal, _row(start + timedelta(minutes=2), 100_500, line_number=2)]

    report = evaluation.build_daily_evaluation(rows, target_date=start.date())

    assert report["candidate_signal_count"] == 1
    assert report["actionable_signal_count"] == 0
    assert report["source_quality_excluded_signal_count"] == 1
    assert report["source_quality_excluded_signal_reasons"] == {
        "advisory_authority_contract_mismatch": 1
    }


def test_signal_without_state_transition_provenance_is_excluded():
    start = datetime(2026, 8, 3, 9, 10, tzinfo=KST)
    signal = _row(
        start,
        100_000,
        state="ENTRY_READY",
        entry_high=100_000,
        observation_kind="",
    )
    rows = [signal, _row(start + timedelta(minutes=2), 100_500, line_number=2)]

    report = evaluation.build_daily_evaluation(rows, target_date=start.date())

    assert report["candidate_signal_count"] == 1
    assert report["source_quality_excluded_signal_reasons"] == {
        "observation_kind_missing_or_invalid": 1
    }


def test_default_target_date_uses_completed_trading_date_for_persistent_timer():
    before_close = evaluation._resolve_default_target_date(
        now=datetime(2026, 8, 3, 8, 0, tzinfo=KST),
    )
    after_close = evaluation._resolve_default_target_date(
        now=datetime(2026, 8, 3, 20, 10, tzinfo=KST),
    )

    assert before_close == date(2026, 7, 31)
    assert after_close == date(2026, 8, 3)


def test_backfill_discovers_every_missing_observation_date(tmp_path):
    observation_dir = tmp_path / "observations"
    output_dir = tmp_path / "reports"
    observation_dir.mkdir()
    output_dir.mkdir()
    for day_key in ("20260730", "20260731", "20260803"):
        (observation_dir / f"samsung_widget_advisory_{day_key}.jsonl").touch()
    (output_dir / "samsung_widget_advisory_evaluation_2026-07-31.json").touch()

    result = evaluation._discover_backfill_dates(
        observation_dir, output_dir, through_date=date(2026, 8, 3)
    )

    assert result == [date(2026, 7, 30), date(2026, 8, 3)]


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


def test_same_support_state_transitions_within_two_minutes_are_one_episode():
    start = datetime(2026, 8, 3, 15, 3, tzinfo=KST)
    rows = [
        _row(
            start,
            100_000,
            state="ENTRY_CAUTION",
            entry_high=100_000,
            invalidation=99_500,
            observation_kind="state_transition",
        ),
        _row(start + timedelta(seconds=30), 99_900, line_number=2),
        _row(
            start + timedelta(minutes=1),
            100_000,
            state="ENTRY_CAUTION",
            entry_high=100_000,
            invalidation=99_500,
            observation_kind="state_transition",
            line_number=3,
        ),
        _row(start + timedelta(minutes=3), 100_600, line_number=4),
    ]

    report = evaluation.build_daily_evaluation(rows, target_date=start.date())

    assert report["candidate_signal_count"] == 2
    assert report["actionable_signal_count"] == 1
    assert report["episode_duplicate_signal_count"] == 1


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
    start = evaluation.CLEAN_BASELINE_DATE
    targets = []
    target = start
    while len(targets) < 60:
        if evaluation.is_krx_trading_day(target):
            targets.append(target)
        target += timedelta(days=1)
    for target in targets:
        payload = {
            "schema_version": 2,
            "symbol": "005930",
            "status": "no_mature_actionable_sample",
            "target_date": target.isoformat(),
            "source_row_count": 1,
            "qualified_trading_day": True,
            "outcomes": [],
            "target_return_pct": 0.5,
            "fallback_adverse_pct": -0.3,
            "metric_contract": {
                "decision_authority": "widget_advisory_evaluation_only"
            },
            "runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }
        path = (
            tmp_path / f"samsung_widget_advisory_evaluation_{target.isoformat()}.json"
        )
        path.write_text(json.dumps(payload), encoding="utf-8")

    report = evaluation.build_rolling_report(tmp_path, as_of_date=targets[-1])
    assert report["trading_day_count"] == 60
    assert report["sample_floor_met"] is True
    assert report["runtime_effect"] is False


def test_rolling_report_excludes_wrong_symbol_and_authority(tmp_path):
    target = date(2026, 8, 6)
    base = {
        "schema_version": 2,
        "symbol": "034020",
        "status": "observed",
        "target_date": target.isoformat(),
        "source_row_count": 1,
        "qualified_trading_day": True,
        "outcomes": [],
        "target_return_pct": 1.0,
        "fallback_adverse_pct": -0.3,
        "metric_contract": {"decision_authority": "widget_advisory_evaluation_only"},
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    wrong_symbol = {**base, "symbol": "999999"}
    wrong_authority = {
        **base,
        "target_date": "2026-08-05",
        "metric_contract": {"decision_authority": "wrong"},
    }
    malformed_count = {
        **base,
        "target_date": "2026-08-04",
        "source_row_count": "not-an-int",
    }
    (tmp_path / "doosan_eval_2026-08-06.json").write_text(
        json.dumps(wrong_symbol), encoding="utf-8"
    )
    (tmp_path / "doosan_eval_2026-08-05.json").write_text(
        json.dumps(wrong_authority), encoding="utf-8"
    )
    (tmp_path / "doosan_eval_2026-08-04.json").write_text(
        json.dumps(malformed_count), encoding="utf-8"
    )

    report = evaluation.build_rolling_report(
        tmp_path,
        as_of_date=target,
        report_prefix="doosan_eval",
        symbol_code="034020",
        target_return_pct=1.0,
    )

    assert report["calendar_artifact_count"] == 0
    assert report["daily_source_paths"] == []


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


def test_daily_evaluation_accepts_explicit_non_samsung_symbol_provenance():
    start = datetime(2026, 8, 6, 12, 10, tzinfo=KST)
    signal = _row(
        start,
        80_000,
        state="ENTRY_CAUTION",
        entry_high=80_000,
        invalidation=79_700,
        observation_kind="state_transition",
    )
    signal["advisory"]["provenance"]["quote_request_code"] = "034020"
    rows = [
        signal,
        _row(start + timedelta(minutes=1), 80_100, line_number=2),
        _row(start + timedelta(minutes=10), 80_500, line_number=3),
    ]

    report = evaluation.build_daily_evaluation(
        rows,
        target_date=start.date(),
        symbol_code="034020",
        expected_sessions={"KRX_REGULAR": 390},
        target_return_pct=1.0,
    )

    assert report["symbol"] == "034020"
    assert report["source_quality_excluded_signal_count"] == 0
    assert report["actionable_signal_count"] == 1
    assert report["outcomes"][0]["target_price"] == 80_800
    assert report["target_return_pct"] == 1.0
    assert "entry_scenario" not in report["outcomes"][0]
    assert report["scenario_cohort_summary"] == []
    assert report["episode_exit_policy_comparisons"] == []
    assert "capacity_constrained_exit_policy_replay" not in report
    assert (
        report["metric_contract"]["episode_exit_policy_comparison"]
        == "not_applicable_non_samsung_widget"
    )


def test_episode_policy_comparison_uses_exact_episode_exit_and_two_fixed_targets():
    start = datetime(2026, 8, 11, 10, 0, tzinfo=KST)
    episode_id = "2026-08-11:KRX_REGULAR:20260811100000"
    signal = _row(
        start,
        100_000,
        state="ENTRY_CAUTION",
        entry_high=100_000,
        invalidation=99_500,
        observation_kind="state_transition",
    )
    signal["advisory"]["derived"] = {
        "retest_held": True,
        "retest_rebound_confirmed": True,
    }
    signal["exit_advisory"] = {
        "state": "EXIT_WATCH",
        "continuity": {"entry_episode_id": episode_id},
    }
    unrelated_exit = _row(
        start + timedelta(minutes=2),
        99_900,
        line_number=3,
        observation_kind="exit_state_transition",
    )
    unrelated_exit["exit_advisory"] = _valid_exit_advisory(
        start + timedelta(minutes=2),
        episode_id="another-episode",
        reference_exit_price=99_900,
    )
    matched_exit = _row(
        start + timedelta(minutes=4),
        100_800,
        line_number=5,
        observation_kind="exit_state_transition",
    )
    matched_exit["exit_advisory"] = _valid_exit_advisory(
        start + timedelta(minutes=4),
        episode_id=episode_id,
        reference_exit_price=100_800,
    )
    rows = [
        signal,
        _row(start + timedelta(minutes=1), 100_600, line_number=2),
        unrelated_exit,
        _row(start + timedelta(minutes=3), 101_100, line_number=4),
        matched_exit,
    ]

    report = evaluation.build_daily_evaluation(rows, target_date=start.date())
    comparison = report["episode_exit_policy_comparisons"][0]

    assert comparison["entry_scenario"] == "support_retest_reversal"
    assert comparison["comparison_eligible"] is True
    assert [item["status"] for item in comparison["fixed_target_results"]] == [
        "TARGET_HIT",
        "TARGET_HIT",
    ]
    assert (
        comparison["fixed_target_results"][0]["hit_at_kst"]
        == (start + timedelta(minutes=1)).isoformat()
    )
    assert (
        comparison["fixed_target_results"][1]["hit_at_kst"]
        == (start + timedelta(minutes=3)).isoformat()
    )
    assert comparison["structural_exit_result"]["status"] == ("EXIT_READY_ATTRIBUTED")
    assert comparison["structural_exit_result"]["reference_exit_price"] == 100_800
    assert comparison["structural_exit_result"]["gross_return_pct"] == 0.8
    assert report["episode_exit_policy_summary"][0]["fixed_target_hit_counts"] == {
        "fixed_0.5pct": 1,
        "fixed_1pct": 1,
    }


def test_structural_exit_is_not_guessed_when_episode_provenance_is_missing():
    start = datetime(2026, 8, 11, 10, 0, tzinfo=KST)
    signal = _row(
        start,
        100_000,
        state="ENTRY_READY",
        entry_high=100_000,
        observation_kind="state_transition",
    )
    exit_row = _row(
        start + timedelta(minutes=1),
        99_500,
        line_number=2,
        observation_kind="exit_state_transition",
    )
    exit_row["exit_advisory"] = _valid_exit_advisory(
        start + timedelta(minutes=1),
        episode_id="different-or-unknown",
        reference_exit_price=99_500,
    )

    report = evaluation.build_daily_evaluation(
        [signal, exit_row],
        target_date=start.date(),
    )
    comparison = report["episode_exit_policy_comparisons"][0]

    assert comparison["structural_exit_result"]["status"] == (
        "UNATTRIBUTABLE_MISSING_EPISODE_ID"
    )


def test_episode_policy_uses_ratio_coverage_and_keeps_long_gap_diagnostic():
    start = datetime(2026, 8, 11, 10, 0, tzinfo=KST)
    signal = _row(
        start,
        100_000,
        state="ENTRY_READY",
        entry_high=100_000,
        observation_kind="state_transition",
    )
    rows = [signal]
    rows.extend(
        _row(start + timedelta(minutes=minute), 100_100, line_number=minute + 1)
        for minute in (*range(1, 8), 10)
    )

    report = evaluation.build_daily_evaluation(rows, target_date=start.date())
    comparison = report["episode_exit_policy_comparisons"][0]

    assert comparison["comparison_coverage"]["coverage_ratio"] == 0.8
    assert comparison["comparison_coverage"]["max_gap_sec"] == 180.0
    assert comparison["comparison_coverage"]["coverage_passed"] is False
    assert comparison["comparison_coverage"]["episode_policy_coverage_passed"] is True
    assert comparison["comparison_eligible"] is True


def test_capacity_replay_removes_overlaps_and_keeps_unresolved_slot_occupied():
    start = datetime(2026, 8, 11, 9, 0, tzinfo=KST)
    comparisons = [
        _capacity_comparison(
            start,
            line=1,
            fixed_half_exit=start + timedelta(minutes=2),
            fixed_one_exit=start + timedelta(minutes=4),
            structural_exit=start + timedelta(minutes=3),
        ),
        _capacity_comparison(
            start + timedelta(minutes=1),
            line=2,
            fixed_half_exit=start + timedelta(minutes=2),
            fixed_one_exit=start + timedelta(minutes=3),
            structural_exit=start + timedelta(minutes=2),
        ),
        _capacity_comparison(
            start + timedelta(minutes=3),
            line=3,
            fixed_half_exit=start + timedelta(minutes=4),
            fixed_one_exit=start + timedelta(minutes=5),
            structural_exit=start + timedelta(minutes=4),
        ),
        _capacity_comparison(
            start + timedelta(minutes=5),
            line=4,
        ),
        _capacity_comparison(
            start + timedelta(minutes=6),
            line=5,
            touch_within_validity=False,
        ),
    ]

    replay = evaluation._build_capacity_constrained_replay(comparisons)
    arms = {arm["policy"]: arm for arm in replay["arms"]}

    half = arms["fixed_0.5pct"]
    assert half["selected_entry_count"] == 3
    assert half["overlap_skipped_count"] == 1
    assert half["invalid_or_insufficient_candidate_count"] == 1
    assert half["completed_trade_count"] == 2
    assert half["unresolved_position_count"] == 1
    assert half["decision_evidence_complete"] is False

    one = arms["fixed_1pct"]
    assert one["selected_entry_count"] == 2
    assert one["overlap_skipped_count"] == 2
    assert one["completed_trade_count"] == 1
    assert one["unresolved_position_count"] == 1

    structural = arms["observed_exact_episode_structural_exit_ready"]
    assert structural["selected_entry_count"] == 2
    assert structural["overlap_skipped_count"] == 2
    assert structural["completed_trade_count"] == 1
    assert structural["unresolved_position_count"] == 1


def test_rolling_capacity_replay_aggregates_days_without_cross_day_slot_state():
    start = datetime(2026, 8, 10, 9, 0, tzinfo=KST)
    first = evaluation._build_capacity_constrained_replay(
        [
            _capacity_comparison(
                start,
                line=1,
                fixed_half_exit=start + timedelta(minutes=2),
                fixed_one_exit=start + timedelta(minutes=4),
                structural_exit=start + timedelta(minutes=3),
            )
        ]
    )
    second_start = start + timedelta(days=1)
    second = evaluation._build_capacity_constrained_replay(
        [
            _capacity_comparison(
                second_start,
                line=1,
                fixed_half_exit=second_start + timedelta(minutes=2),
                fixed_one_exit=second_start + timedelta(minutes=4),
                structural_exit=second_start + timedelta(minutes=3),
            )
        ]
    )

    rolling = evaluation._build_rolling_capacity_replay(
        [
            {
                "target_date": "2026-08-10",
                "capacity_constrained_exit_policy_replay": first,
            },
            {
                "target_date": "2026-08-11",
                "capacity_constrained_exit_policy_replay": second,
            },
        ]
    )
    half = next(arm for arm in rolling["arms"] if arm["policy"] == "fixed_0.5pct")

    assert half["source_trading_day_count"] == 2
    assert half["selected_entry_count"] == 2
    assert half["completed_trade_count"] == 2
    assert {trade["source_target_date"] for trade in half["trades"]} == {
        "2026-08-10",
        "2026-08-11",
    }


def test_rolling_capacity_replay_rejects_bad_authority_and_malformed_arm():
    start = datetime(2026, 8, 11, 9, 0, tzinfo=KST)
    replay = evaluation._build_capacity_constrained_replay(
        [
            _capacity_comparison(
                start,
                line=1,
                fixed_half_exit=start + timedelta(minutes=2),
                fixed_one_exit=start + timedelta(minutes=4),
                structural_exit=start + timedelta(minutes=3),
            )
        ]
    )
    bad_authority = json.loads(json.dumps(replay))
    bad_authority["metric_contract"]["decision_authority"] = "real_order"
    malformed_arm = json.loads(json.dumps(replay))
    malformed_arm["arms"][0]["selected_entry_count"] = "not-an-int"

    rolling = evaluation._build_rolling_capacity_replay(
        [
            {
                "target_date": "2026-08-11",
                "capacity_constrained_exit_policy_replay": bad_authority,
            },
            {
                "target_date": "2026-08-11",
                "capacity_constrained_exit_policy_replay": malformed_arm,
            },
        ]
    )

    assert rolling["source_daily_report_count"] == 1
    assert all(arm["policy"] != "fixed_0.5pct" for arm in rolling["arms"])


def test_rolling_capacity_replay_rejects_tampered_completed_profit():
    start = datetime(2026, 8, 11, 9, 0, tzinfo=KST)
    replay = evaluation._build_capacity_constrained_replay(
        [
            _capacity_comparison(
                start,
                line=1,
                fixed_half_exit=start + timedelta(minutes=2),
                fixed_one_exit=start + timedelta(minutes=4),
                structural_exit=start + timedelta(minutes=3),
            )
        ]
    )
    replay["arms"][0]["trades"][0]["net_return_pct"] = 999.0

    rolling = evaluation._build_rolling_capacity_replay(
        [
            {
                "target_date": "2026-08-11",
                "capacity_constrained_exit_policy_replay": replay,
            }
        ]
    )

    assert all(arm["policy"] != "fixed_0.5pct" for arm in rolling["arms"])


def test_rolling_capacity_replay_rejects_tampered_unresolved_terminal_mark():
    start = datetime(2026, 8, 11, 9, 0, tzinfo=KST)
    replay = evaluation._build_capacity_constrained_replay(
        [_capacity_comparison(start, line=1)]
    )
    replay["arms"][0]["trades"][0]["unresolved_terminal_mark_return_pct"] = 999.0

    rolling = evaluation._build_rolling_capacity_replay(
        [
            {
                "target_date": "2026-08-11",
                "capacity_constrained_exit_policy_replay": replay,
            }
        ]
    )

    assert all(arm["policy"] != "fixed_0.5pct" for arm in rolling["arms"])


def _valid_exit_advisory(
    observed_at: datetime,
    *,
    episode_id: str,
    reference_exit_price: int,
) -> dict:
    return {
        "state": "EXIT_READY",
        "session": "KRX_REGULAR",
        "observed_at": observed_at.isoformat(),
        "valid_until": (observed_at + timedelta(seconds=60)).isoformat(),
        "reference_exit_price": reference_exit_price,
        "continuity": {"entry_episode_id": episode_id},
        "source_quality": {"status": "PASS", "issues": []},
        "authority": "widget_advisory_only",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "holding_independent": True,
    }


def _capacity_comparison(
    entry_at: datetime,
    *,
    line: int,
    fixed_half_exit: datetime | None = None,
    fixed_one_exit: datetime | None = None,
    structural_exit: datetime | None = None,
    touch_within_validity: bool = True,
) -> dict:
    def fixed_result(policy: str, target: int, exit_at: datetime | None) -> dict:
        return {
            "policy": policy,
            "status": (
                "TARGET_HIT"
                if exit_at is not None
                else "NOT_HIT_WITHIN_OBSERVED_SESSION_WINDOW"
            ),
            "target_price": target,
            "hit_at_kst": exit_at.isoformat() if exit_at else None,
        }

    structural = {
        "status": (
            "EXIT_READY_ATTRIBUTED"
            if structural_exit is not None
            else "NO_EXIT_READY_WITHIN_OBSERVED_SESSION_WINDOW"
        ),
        "exit_at_kst": structural_exit.isoformat() if structural_exit else None,
        "reference_exit_price": 100_800 if structural_exit else None,
    }
    return {
        "signal_observed_at_kst": entry_at.isoformat(),
        "signal_valid_until_kst": (entry_at + timedelta(minutes=1)).isoformat(),
        "source_line_number": line,
        "entry_episode_id": f"episode-{line}",
        "entry_scenario": "support_retest_reversal",
        "market_session": "KRX_REGULAR",
        "market_venue": "KRX",
        "entry_reference_price": 100_000,
        "entry_touched_at_kst": entry_at.isoformat(),
        "entry_touch_within_signal_validity": touch_within_validity,
        "comparison_eligible": True,
        "fixed_target_results": [
            fixed_result("fixed_0.5pct", 100_500, fixed_half_exit),
            fixed_result("fixed_1pct", 101_000, fixed_one_exit),
        ],
        "structural_exit_result": structural,
        "observed_window_end_at_kst": (entry_at + timedelta(hours=6)).isoformat(),
        "observed_window_end_price": 99_500,
    }
