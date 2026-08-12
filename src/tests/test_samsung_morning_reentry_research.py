from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta

import pytest

from src.engine.monitoring import samsung_morning_reentry_research as research
from src.engine.monitoring.pure_market_reversal_replay import Bar


def _bar(
    timestamp: datetime,
    *,
    open_price: int = 100_000,
    high: int = 100_000,
    low: int = 100_000,
    close: int = 100_000,
    venue: str = "KRX",
    session: str = "KRX_REGULAR",
) -> Bar:
    return Bar(
        symbol="005930",
        venue=venue,
        session=session,
        timestamp=timestamp,
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=1_000,
        source="test",
    )


def test_target_cannot_complete_on_fill_bar():
    started = datetime(2026, 8, 10, 9, 10)
    fill = _bar(started, high=100_200, low=100_000)
    held = research._leg_outcome(
        entry_price=100_000,
        fill_bars=(fill,),
        target_bars=(fill,),
    )
    assert held["status"] == "HELD"

    later = _bar(started + timedelta(minutes=1), high=100_200, low=100_100)
    completed = research._leg_outcome(
        entry_price=100_000,
        fill_bars=(fill,),
        target_bars=(fill, later),
    )
    assert completed["status"] == "COMPLETE"
    assert completed["target_at"] == later.timestamp.isoformat()


def test_source_validation_fails_closed_when_session_coverage_is_incomplete(
    tmp_path, monkeypatch
):
    input_path = tmp_path / "minute.jsonl"
    input_path.write_bytes(b"source")
    manifest_path = tmp_path / "minute.manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema": "pure_market_minute_backfill_manifest_v1",
                "source_quality_status": "PASS",
                "start_date": "2026-06-05",
                "end_date": "2026-08-10",
                "symbol": "005930",
                "data_sha256": hashlib.sha256(b"source").hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        research,
        "load_market_bars",
        lambda **kwargs: ([], {"status": "PASS"}),
    )
    monkeypatch.setattr(
        research,
        "assess_date_coverage",
        lambda bars: {"qualified_dates_by_venue": {"KRX": ["date"] * 46, "NXT": []}},
    )

    with pytest.raises(
        research.ResearchError, match="market_data_session_coverage_not_pass"
    ):
        research.validate_source(input_path, manifest_path)


def test_first_episode_falls_back_only_the_unfilled_nxt_leg():
    day = date(2026, 8, 10)
    nxt = [
        _bar(
            datetime.combine(day, datetime.min.time()) + timedelta(hours=8, minutes=i),
            open_price=100_000,
            high=97_100,
            low=97_100,
            close=97_100,
            venue="NXT",
            session="NXT_PREMARKET",
        )
        for i in range(50)
    ]
    nxt[1] = _bar(
        nxt[1].timestamp,
        open_price=97_100,
        high=97_300,
        low=97_100,
        close=97_300,
        venue="NXT",
        session="NXT_PREMARKET",
    )
    krx = [
        _bar(
            datetime.combine(day, datetime.min.time()) + timedelta(hours=9, minutes=i),
            open_price=100_000,
            high=99_200,
            low=99_200,
            close=99_200,
        )
        for i in range(3)
    ]
    krx[1] = _bar(
        krx[1].timestamp,
        open_price=99_200,
        high=99_400,
        low=99_200,
        close=99_400,
    )

    result = research.reconstruct_first_episode(nxt, krx)

    assert result["status"] == "COMPLETE"
    assert [leg["route"] for leg in result["legs"]] == ["NXT", "SOR"]
    assert all(leg["status"] == "COMPLETE" for leg in result["legs"])


def test_candidate_grid_keeps_price_families_and_morning_limit_separate():
    grid = research.candidate_grid()
    families = {candidate.family for candidate in grid}
    assert families == {
        "direct_low_proximity",
        "low_hold_reclaim_close_split",
        "low_hold_reclaim_passive_split",
    }
    assert all(candidate.scan_end_minute <= 600 for candidate in grid)
    assert all(
        candidate.entry_offset_ticks == 0
        for candidate in grid
        if candidate.family == "low_hold_reclaim_close_split"
    )
    assert all(
        candidate.entry_offset_ticks == -1
        for candidate in grid
        if candidate.family == "low_hold_reclaim_passive_split"
    )


def test_low_hold_reclaim_requires_low_hold_and_reclaim():
    started = datetime(2026, 8, 10, 9, 10)
    bars = tuple(
        _bar(
            started + timedelta(minutes=index),
            open_price=100_000,
            high=100_000 + index * 100,
            low=99_500,
            close=99_500 + index * 100,
        )
        for index in range(5)
    )
    setup = research.SignalFeature(
        index=0,
        timestamp=bars[0].timestamp,
        close_price=99_500,
        drawdown_pct=0.75,
        near_low_pct=0.0,
    )
    context = research.DayContext(
        trade_date=date(2026, 8, 10),
        krx_bars=bars,
        first_episode={"status": "COMPLETE", "completed_at": started.isoformat()},
        features={lookback: (setup,) for lookback in research.LOOKBACK_GRID},
    )
    candidate = research.Candidate(
        family="low_hold_reclaim_passive_split",
        lookback_bars=3,
        drawdown_pct=0.5,
        near_low_pct=0.1,
        scan_end_minute=600,
        entry_valid_completed_bars=3,
        entry_offset_ticks=-1,
        confirmation_bars=2,
        reclaim_ticks=1,
        entry_anchor="confirmation_close",
    )

    resolved = research._resolve_signal(context, candidate)

    assert resolved is not None
    assert resolved.entry_index == 2
    assert resolved.entry_anchor_price == bars[2].close


def test_metric_contract_and_report_authority_are_source_only(monkeypatch):
    monkeypatch.setattr(
        research,
        "validate_source",
        lambda *args, **kwargs: {
            "manifest": {"source_quality_status": "PASS"},
            "bars": [],
        },
    )
    monkeypatch.setattr(research, "build_contexts", lambda bars: {})
    monkeypatch.setattr(
        research,
        "select_candidate",
        lambda contexts: {
            "candidate": None,
            "decision": "no_robust_calibration_candidate",
            "recommended_action": "do_not_change_live_machine",
        },
    )

    report = research.build_report()

    assert report["runtime_effect"] is False
    assert report["allowed_runtime_apply"] is False
    assert report["actual_order_submitted"] is False
    assert report["broker_order_forbidden"] is True
    assert (
        report["metric_contract"]["decision_authority"]
        == "source_only_no_runtime_or_order_authority"
    )


def test_family_iteration_selects_first_calibration_winner_that_passes_holdout(
    monkeypatch,
):
    dates = [date(2026, 6, 5) + timedelta(days=index) for index in range(44)]
    contexts = {trade_date: object() for trade_date in dates}
    candidates = tuple(
        research.Candidate(
            family=family,
            lookback_bars=3,
            drawdown_pct=0.5,
            near_low_pct=0.2,
            scan_end_minute=600,
            entry_valid_completed_bars=3,
            entry_offset_ticks=offset,
            confirmation_bars=0 if family == "direct_low_proximity" else 1,
            reclaim_ticks=0 if family == "direct_low_proximity" else 1,
            entry_anchor="signal_close",
        )
        for family, offset in (
            ("direct_low_proximity", 0),
            ("low_hold_reclaim_close_split", 0),
            ("low_hold_reclaim_passive_split", -1),
        )
    )
    monkeypatch.setattr(research, "candidate_grid", lambda: candidates)

    def fake_evaluate(candidate, unused_contexts, selected_dates, **kwargs):
        selected_dates = list(selected_dates)
        is_holdout = selected_dates == dates[-16:]
        is_full = len(selected_dates) == 44
        held = int(
            (is_holdout or is_full)
            and candidate.family != "low_hold_reclaim_passive_split"
        )
        result = {
            "signal_episodes": max(3, len(selected_dates) // 2),
            "attempted_legs": max(8, len(selected_dates)),
            "completed_legs": max(6, len(selected_dates) - held),
            "no_fill_legs": 0,
            "held_legs": held,
            "notional_weighted_ev_pct": 0.1,
        }
        if kwargs.get("include_episodes"):
            result["episodes"] = []
        return result

    monkeypatch.setattr(research, "evaluate_candidate", fake_evaluate)

    selection = research.select_candidate(contexts)

    assert selection["decision"] == "holdout_pass_source_only_reentry_candidate"
    assert (
        selection["candidate"]["parameters"]["family"]
        == "low_hold_reclaim_passive_split"
    )
    assert (
        selection["family_results"]["direct_low_proximity"]["decision"]
        == "holdout_failed_do_not_change_live_machine"
    )
