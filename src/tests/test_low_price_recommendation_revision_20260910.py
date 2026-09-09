"""Approved 9/10 expansion preserves earlier dates, custody and policy owners."""

import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.engine.automation.low_price_two_leg_policy_apply import build_applied_policy
from src.engine.monitoring.low_price_two_leg_tuning import build_candidate, build_report
from src.trading.low_price_two_leg.policy_runtime import (
    PROFILE_REVISION_20260910_TRANSITION,
    PROFILE_REVISION_20260909_TRANSITION,
    atomic_write_json,
    baseline_policies_for_target_date,
    candidate_policies_with_current_baselines,
    policy_hash,
    runtime_profile_exclusions,
    validate_applied,
)
from src.trading.low_price_two_leg.preflight import validate_research_evidence
from src.trading.low_price_two_leg.profiles import get_profile, profiles_for_target_date

DAY = date(2026, 9, 10)
PRIOR = date(2026, 9, 9)
ROOT = Path(__file__).resolve().parents[2]
APPROVED = set(PROFILE_REVISION_20260910_TRANSITION["approved_profile_ids"])
NEW = {"lotte_chemical_morning", "lotte_chemical_afternoon", "tym_late_morning"}


def _source_candidate(tmp_path, source_date):
    """Build hash-bound fixtures without depending on ignored operating files."""
    applied, _ = build_applied_policy(
        target_date=source_date, candidate_dir=tmp_path / "empty"
    )
    # Preserve a nonbaseline, unapproved axis across the dated revision.
    applied["profiles"]["samsung_heavy_midday"]["policy"][
        "rolling_high_drawdown_pct"
    ] += 0.25
    applied["policy_hash"] = policy_hash(
        {key: row["policy"] for key, row in applied["profiles"].items()}
    )
    atomic_write_json(
        tmp_path / "applied" / f"low_price_two_leg_policy_{source_date}.json",
        applied,
    )
    atomic_write_json(
        tmp_path / "sq" / f"observation_source_quality_audit_{source_date}.json",
        {"status": "pass", "summary": {"tuning_input_allowed": True}},
    )
    report = build_report(
        target_date=str(source_date),
        state_dir=tmp_path / "states",
        output_dir=tmp_path / "reports",
        source_quality_dir=tmp_path / "sq",
        applied_dir=tmp_path / "applied",
        machine_microstructure_report_dir=tmp_path / "micro",
    )
    atomic_write_json(Path(report["artifact_path"]), report)
    candidate = build_candidate(
        report,
        candidate_dir=tmp_path / "candidates",
        samsung_candidate_dir=tmp_path / "samsung",
    )
    atomic_write_json(
        tmp_path
        / "candidates"
        / f"low_price_two_leg_policy_candidate_{source_date}.json",
        candidate,
    )
    return candidate


def test_revision_preserves_prior_date_and_unapproved_baselines(tmp_path):
    before = baseline_policies_for_target_date(PRIOR)
    after = baseline_policies_for_target_date(DAY)
    assert len(before) == 56 and len(after) == 59
    assert set(after) - set(before) == NEW
    # SK Telecom's recommendation reconfirms its existing numeric baseline.
    assert {key for key in before if before[key] != after[key]} == {
        "kepco_late_morning"
    }
    assert runtime_profile_exclusions(DAY) == runtime_profile_exclusions(PRIOR)
    assert len(runtime_profile_exclusions(DAY)) == 3
    assert set(profiles_for_target_date(PRIOR)).isdisjoint(NEW)
    for day in (PRIOR, DAY):
        payload, _ = build_applied_policy(target_date=day, candidate_dir=tmp_path)
        assert validate_applied(payload, target_date=day) == (True, "valid")
        assert not validate_applied(
            payload, target_date=DAY if day == PRIOR else PRIOR
        )[0]


def test_exact_evidence_and_two_ten_share_legs():
    evidence = json.loads(
        (ROOT / PROFILE_REVISION_20260910_TRANSITION["evidence_path"]).read_text()
    )
    digest = hashlib.sha256(
        json.dumps(evidence, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()
    assert digest == PROFILE_REVISION_20260910_TRANSITION["evidence_canonical_sha256"]
    assert len(evidence["recommendations"]) == 5
    assert evidence["approval"]["effective_target_date"] == DAY.isoformat()
    for rid in APPROVED:
        profile = get_profile(rid, target_date=DAY)
        assert validate_research_evidence(profile, target_date=DAY) == (True, "ready")
        assert profile.policy.quantity == 20
        assert len(profile.policy.entry_legs(20000)) == 2


def test_source_hash_and_negative_half_remain_fail_closed(tmp_path):
    evidence = json.loads(
        (ROOT / PROFILE_REVISION_20260910_TRANSITION["evidence_path"]).read_text()
    )
    evidence["recommendations"][0]["calibration_second_half_ev_pct"] = -0.01
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence))
    digest = hashlib.sha256(
        json.dumps(evidence, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()
    assert not validate_research_evidence(
        get_profile("lotte_chemical_morning"),
        path,
        expected_sha256=digest,
        target_date=DAY,
    )[0]


def test_actual_prior_policy_binding_is_preserved_for_unapproved_profiles(tmp_path):
    candidate = _source_candidate(tmp_path, PRIOR)
    payload, status = build_applied_policy(
        target_date=DAY, candidate_dir=tmp_path / "candidates"
    )
    assert status == "candidate_validated_profile_revision_applied"
    assert validate_applied(payload, target_date=DAY) == (True, "valid")
    bound = candidate["source_runtime_policy_binding"]["policies"]
    for rid, row in payload["profiles"].items():
        assert row["policy"] == (
            baseline_policies_for_target_date(DAY)[rid]
            if rid in APPROVED
            else bound[rid]
        )


def test_standing_authority_successor_is_exact_date_and_scope():
    from src.trading.config.symbol_owner_standing_authority import (
        load_standing_authority,
        SymbolOwnerStandingAuthorityError,
    )
    from src.trading.order.symbol_owner_policy_auto_apply import (
        expected_machine_symbol_owners,
    )

    path = ROOT / "data/config/symbol_owner_policy_standing_authority_2026-09-10.json"
    authority = load_standing_authority(
        path, observed_at=datetime(2026, 9, 10, 7, 32, tzinfo=ZoneInfo("Asia/Seoul"))
    )
    assert {
        key: row["allowed_owners"] for key, row in authority["symbols"].items()
    } == expected_machine_symbol_owners(DAY)
    assert "011170" not in expected_machine_symbol_owners(PRIOR)
    with pytest.raises(
        SymbolOwnerStandingAuthorityError, match="outside_effective_range"
    ):
        load_standing_authority(
            path, observed_at=datetime(2026, 9, 9, 23, tzinfo=ZoneInfo("Asia/Seoul"))
        )


def test_older_candidate_crosses_both_approved_revisions_without_losing_binding(
    tmp_path,
):
    candidate = _source_candidate(tmp_path, date(2026, 9, 8))
    normalized = candidate_policies_with_current_baselines(candidate, target_date=DAY)
    approved = APPROVED | set(
        PROFILE_REVISION_20260909_TRANSITION["approved_profile_ids"]
    )
    bound = candidate["source_runtime_policy_binding"]["policies"]
    baselines = baseline_policies_for_target_date(DAY)
    assert len(normalized) == 59
    for rid, policy in normalized.items():
        assert policy == (baselines[rid] if rid in approved else bound[rid])
