"""Exact-date recommendation handoff, economics and custody boundaries."""

import hashlib
import json
from datetime import date
from pathlib import Path

import pytest

from src.engine.automation.low_price_two_leg_policy_apply import build_applied_policy
from src.trading.low_price_two_leg.policy_runtime import (
    PROFILE_REVISION_20260908_TRANSITION,
    runtime_profile_exclusions,
    validate_applied,
)
from src.trading.low_price_two_leg.preflight import (
    RECOMMENDATION_20260907_PROFILE_MAP,
    validate_research_evidence,
)
from src.trading.low_price_two_leg.profiles import (
    PROFILES_20260909_PRIOR as PROFILES,
    PROFILES_20260908_PRIOR,
    get_profile,
)

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / PROFILE_REVISION_20260908_TRANSITION["evidence_path"]
DAY = date(2026, 9, 8)


def test_revision_preserves_prior_date_and_quarantine(tmp_path):
    prior, _ = build_applied_policy(
        target_date=date(2026, 9, 7), candidate_dir=tmp_path
    )
    current, _ = build_applied_policy(target_date=DAY, candidate_dir=tmp_path)
    assert len(prior["profiles"]) == 53
    assert len(current["profiles"]) == 56
    assert set(PROFILES) - set(PROFILES_20260908_PRIOR) == {
        "nhn_midday",
        "tym_morning",
        "sd_biosensor_afternoon",
    }
    assert not {"youngone_late_morning", "doosan_enerbility_midday"} & set(PROFILES)
    assert current["runtime_profile_exclusions"] == prior["runtime_profile_exclusions"]
    assert len(runtime_profile_exclusions(DAY)) == 3
    assert validate_applied(current, target_date=DAY) == (True, "valid")
    assert not validate_applied(current, target_date=date(2026, 9, 7))[0]
    for key in set(PROFILES) - set(PROFILES_20260908_PRIOR):
        with pytest.raises(ValueError):
            get_profile(key, target_date=date(2026, 9, 7))


def test_eleven_policies_exactly_match_approved_recommendations_and_cost_gate():
    evidence = json.loads(EVIDENCE.read_text())
    rows = {row["profile_id"]: row for row in evidence["recommendations"]}
    assert len(rows) == len(RECOMMENDATION_20260907_PROFILE_MAP) == 11
    assert len({r["recommendation_id"] for r in rows.values()}) == 11
    for live_id, source_id in RECOMMENDATION_20260907_PROFILE_MAP.items():
        p = get_profile(live_id, target_date=DAY).policy
        assert rows[source_id]["recommended_spot"] == {
            "scan_start": p.scan_start.strftime("%H:%M"),
            "scan_end": p.scan_last_bar.strftime("%H:%M"),
            "lookback_bars": p.lookback_bars,
            "rolling_high_drawdown_pct": p.rolling_high_drawdown_pct,
            "rolling_low_proximity_pct": p.rolling_low_proximity_pct,
            "entry_offsets_ticks": list(p.entry_offsets_ticks),
            "entry_valid_completed_bars": p.entry_valid_completed_bars,
            "target_ticks": p.target_ticks,
        }
        assert p.quantity == 20
        assert len(p.entry_legs(20000)) == 2
        assert validate_research_evidence(get_profile(live_id), target_date=DAY) == (
            True,
            "ready",
        )
    # Existing held fan-ocean legs remain associated with their original date.
    assert (
        get_profile(
            "fan_ocean_late_morning", target_date=date(2026, 9, 7)
        ).policy.target_ticks
        == 2
    )
    assert (
        get_profile("fan_ocean_late_morning", target_date=DAY).policy.target_ticks == 4
    )


def test_evidence_tampering_and_negative_calibration_half_fail_closed(tmp_path):
    original = json.loads(EVIDENCE.read_text())
    row = next(
        r
        for r in original["recommendations"]
        if r["profile_id"] == "existing_181710_midday"
    )
    row["calibration_first_half_ev_pct"] = -0.001
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(original))
    profile = get_profile("nhn_midday")
    assert not validate_research_evidence(profile, path, target_date=DAY)[0]
    digest = hashlib.sha256(
        json.dumps(original, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()
    # Even a reviewed new digest cannot turn a negative calibration half into approval.
    assert not validate_research_evidence(
        profile, path, expected_sha256=digest, target_date=DAY
    )[0]
