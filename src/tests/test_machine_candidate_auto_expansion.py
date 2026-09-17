from __future__ import annotations

import csv
import json
import pytest
from datetime import date
from pathlib import Path

from src.engine.automation import low_price_two_leg_auto_expansion_policy as expansion
from src.engine.monitoring.machine_candidate_lifecycle import (
    completed_daily_recommendation_symbols,
)
from src.engine.monitoring.machine_recommendation_identity import bind_recommendation
from src.trading.low_price_two_leg.auto_expansion_service import _profile


def test_completed_daily_recommendations_have_no_cardinality_cap(tmp_path):
    rows = [
        {
            "date": "2026-09-15",
            "code": str(index).zfill(6),
            "name": f"symbol-{index}",
            "close": "10000",
            "score_rank": str(index),
        }
        for index in range(1, 22)
    ]
    csv_path = tmp_path / "recommendations.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    diagnostics = tmp_path / "diagnostics.json"
    diagnostics.write_text(
        json.dumps({"latest_date": "2026-09-15", "selected_count": len(rows)}),
        encoding="utf-8",
    )

    source_date, symbols = completed_daily_recommendation_symbols(
        date(2026, 9, 16),
        csv_path=csv_path,
        diagnostics_path=diagnostics,
    )

    assert source_date == date(2026, 9, 15)
    assert len(symbols) == 21


def _report() -> dict:
    spot = {
        "scan_start": "10:05",
        "scan_end": "10:59",
        "lookback_bars": 20,
        "rolling_high_drawdown_pct": 0.5,
        "rolling_low_proximity_pct": 0.2,
        "entry_offsets_ticks": [0, -1],
        "entry_valid_completed_bars": 5,
        "target_ticks": 2,
    }
    row = {
        "profile_id": "existing_111770_late_morning",
        "symbol": "111770",
        "name": "영원무역",
        "session": "late_morning",
        "discovery_lane": "existing_symbol_time_extension",
        "recommended_spot": spot,
        "implementation_status": "source_only_requires_review_and_user_approval",
        "notional_weighted_ev_pct": 0.03,
        "holdout_signal_episodes": 3,
        "holdout_completed_legs": 4,
        "holdout_held_legs": 0,
        "holdout_held_leg_rate_per_filled_leg": 0.0,
        "holdout_realized_net_profit_krw_per_episode": 10.0,
        "paired_economics": {
            "comparable_observation_window": True,
            "net_profit_improved": True,
            "runtime_effect": False,
        },
        "runtime_effect": False,
    }
    bind_recommendation(
        row,
        producer="low_price_two_leg_expanded_candidate_research",
        scope="111770/late_morning/existing_111770_late_morning",
        axis="profile_policy",
        proposal=spot,
        consumer="low_price_two_leg_policy_apply",
        acceptance="test exact-date bridge",
    )
    return {
        "schema": expansion.REPORT_SCHEMA,
        "target_date": "2026-09-15",
        "status": "recommendations_ready",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "recommendations": [row],
        "postclose_logic_recommendations": [],
    }


def test_episode_recommendation_promotes_without_user_approval_and_round_trips(
    tmp_path,
):
    report_dir = tmp_path / "reports"
    policy_dir = tmp_path / "policies"
    report_dir.mkdir()
    report_path = (
        report_dir / "low_price_two_leg_expanded_candidate_research_2026-09-15.json"
    )
    report_path.write_text(json.dumps(_report()), encoding="utf-8")

    payload = expansion.build_policy(
        source_date=date(2026, 9, 15),
        report_dir=report_dir,
        policy_dir=policy_dir,
    )
    output = expansion.policy_path(date(2026, 9, 16), policy_dir=policy_dir)
    policy_dir.mkdir()
    output.write_text(json.dumps(payload), encoding="utf-8")

    loaded = expansion.load_policy(date(2026, 9, 16), policy_dir=policy_dir)
    profile = _profile(
        loaded["profiles"]["auto_111770_late_morning"],
        authority_hash=loaded["policy_hash"],
    )

    assert loaded["cardinality_cap"] is None
    assert loaded["newly_promoted_profile_ids"] == ["auto_111770_late_morning"]
    assert profile.policy.dynamic_authority_hash == loaded["policy_hash"]
    assert profile.policy.scan_last_bar.isoformat() == "10:59:00"


def test_auto_expansion_systemd_preflight_does_not_depend_on_private_tmux_socket():
    unit = Path(
        "deploy/systemd/korstockscan-low-price-two-leg-auto-expansion.service"
    ).read_text(encoding="utf-8")

    assert "PrivateTmp=true" in unit
    assert "ExecCondition=/usr/bin/tmux" not in unit
    assert "auto_expansion_service --check-active" in unit


def test_episode_policy_accepts_complete_source_above_legacy_32mib_bound(tmp_path):
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    source = report_dir / "low_price_two_leg_expanded_candidate_research_2026-09-15.json"
    report = _report()
    report["diagnostic_population"] = "x" * (32 * 1024 * 1024)
    source.write_text(json.dumps(report), encoding="utf-8")
    payload = expansion.build_policy(
        source_date=date(2026, 9, 15), report_dir=report_dir,
        policy_dir=tmp_path / "policies",
    )
    assert payload["newly_promoted_profile_ids"] == ["auto_111770_late_morning"]
    assert payload["actual_order_submitted"] is False
    assert payload["hard_safety_preserved"] is True


@pytest.mark.parametrize("kind", ["oversize", "symlink", "order_authority"])
def test_episode_policy_preserves_source_and_authority_rejection(
    monkeypatch, tmp_path, kind
):
    from src.engine.monitoring import low_price_two_leg_expanded_candidate_research as producer

    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    source = report_dir / "low_price_two_leg_expanded_candidate_research_2026-09-15.json"
    report = _report()
    if kind == "order_authority":
        report["actual_order_submitted"] = True
    if kind == "symlink":
        actual = tmp_path / "actual.json"
        actual.write_text(json.dumps(report))
        source.symlink_to(actual)
    else:
        source.write_text(json.dumps(report))
    if kind == "oversize":
        monkeypatch.setattr(producer, "REPORT_CACHE_MAX_BYTES", 8)
    with pytest.raises(ValueError, match="episode_auto_expansion_source_"):
        expansion.build_policy(
            source_date=date(2026, 9, 15), report_dir=report_dir,
            policy_dir=tmp_path / "policies",
        )
    assert not (tmp_path / "policies").exists()


def test_integrated_aftermarket_episode_profile_is_runtime_compilable():
    row = {
        "profile_id": "auto_111770_integrated_aftermarket",
        "symbol": "111770",
        "name": "영원무역",
        "session": "integrated_aftermarket",
        "policy": {
            "scan_start": "16:30",
            "scan_end": "19:20",
            "lookback_bars": 20,
            "rolling_high_drawdown_pct": 0.5,
            "rolling_low_proximity_pct": 0.2,
            "entry_offsets_ticks": [0, -1],
            "entry_valid_completed_bars": 5,
            "target_ticks": 2,
        },
    }

    profile = _profile(row, authority_hash="a" * 64)

    assert profile.session == "integrated_aftermarket"
    assert profile.policy.scan_start.isoformat() == "16:30:00"
    assert profile.policy.scan_last_bar.isoformat() == "19:20:00"
