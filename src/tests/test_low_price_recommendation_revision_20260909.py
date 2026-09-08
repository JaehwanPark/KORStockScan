"""Two approved existing-profile revisions; no new machine or custody authority."""

import hashlib
import json
from datetime import date
from pathlib import Path

from src.engine.automation.low_price_two_leg_policy_apply import build_applied_policy
from src.trading.low_price_two_leg.policy_runtime import (
    PROFILE_REVISION_20260909_TRANSITION,
    baseline_policies_for_target_date,
    runtime_profile_exclusions,
    validate_applied,
)
from src.trading.low_price_two_leg.preflight import validate_research_evidence
from src.trading.low_price_two_leg.profiles import get_profile, profiles_for_target_date

DAY = date(2026, 9, 9)
PRIOR = date(2026, 9, 8)
ROOT = Path(__file__).resolve().parents[2]


def test_only_two_approved_policies_change_and_prior_date_is_frozen(tmp_path):
    before = baseline_policies_for_target_date(PRIOR)
    after = baseline_policies_for_target_date(DAY)
    assert len(before) == len(after) == 56
    assert {key for key in after if before[key] != after[key]} == {
        "sk_eternix_late_morning",
        "tym_morning",
    }
    assert runtime_profile_exclusions(DAY) == runtime_profile_exclusions(PRIOR)
    assert len(runtime_profile_exclusions(DAY)) == 3
    assert get_profile("tym_morning", target_date=PRIOR).policy.target_ticks == 2
    assert get_profile("tym_morning", target_date=DAY).policy.target_ticks == 4
    for day in (PRIOR, DAY):
        payload, _ = build_applied_policy(target_date=day, candidate_dir=tmp_path)
        assert validate_applied(payload, target_date=day) == (True, "valid")
        assert not validate_applied(
            payload, target_date=DAY if day == PRIOR else PRIOR
        )[0]


def test_exact_source_evidence_policy_and_quantity_contract():
    p = ROOT / PROFILE_REVISION_20260909_TRANSITION["evidence_path"]
    evidence = json.loads(p.read_text())
    digest = hashlib.sha256(
        json.dumps(evidence, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()
    assert digest == PROFILE_REVISION_20260909_TRANSITION["evidence_canonical_sha256"]
    assert len(evidence["recommendations"]) == 2
    for row in evidence["recommendations"]:
        live = row["profile_id"].removeprefix("logic_")
        profile = get_profile(live, target_date=DAY)
        assert validate_research_evidence(profile, target_date=DAY) == (True, "ready")
        assert profile.policy.quantity == 20
        assert len(profile.policy.entry_legs(20000)) == 2
        assert profile.policy.target_ticks == row["recommended_spot"]["target_ticks"]
        assert row["calibration_first_half_ev_pct"] > 0
        assert row["calibration_second_half_ev_pct"] > 0
    assert set(profiles_for_target_date(DAY)) == set(profiles_for_target_date(PRIOR))


def test_approved_evidence_negative_half_still_fails_with_new_hash(tmp_path):
    evidence = json.loads(
        (ROOT / PROFILE_REVISION_20260909_TRANSITION["evidence_path"]).read_text()
    )
    evidence["recommendations"][0]["calibration_second_half_ev_pct"] = -0.01
    p = tmp_path / "evidence.json"
    p.write_text(json.dumps(evidence))
    digest = hashlib.sha256(
        json.dumps(evidence, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()
    live = evidence["recommendations"][0]["profile_id"].removeprefix("logic_")
    assert not validate_research_evidence(
        get_profile(live), p, expected_sha256=digest, target_date=DAY
    )[0]
