"""September 11 approval preserves dated policy, custody and launch guards."""

import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.tests.test_low_price_recommendation_revision_20260910 import _source_candidate
from src.engine.automation.low_price_two_leg_policy_apply import build_applied_policy
from src.trading.low_price_two_leg.profiles import get_profile, profiles_for_target_date
from src.trading.low_price_two_leg.policy_runtime import (
    PROFILE_REVISION_20260911_TRANSITION,
    PROFILE_REVISION_20260910_TRANSITION,
    PROFILE_REVISION_20260909_TRANSITION,
    baseline_policies_for_target_date,
    candidate_policies_with_current_baselines,
    runtime_profile_exclusions,
    validate_applied,
)
from src.trading.low_price_two_leg.preflight import validate_research_evidence
from src.trading.config.symbol_owner_standing_authority import (
    load_standing_authority,
    SymbolOwnerStandingAuthorityError,
)
from src.trading.order.symbol_owner_policy_auto_apply import (
    expected_machine_symbol_owners,
)

DAY = date(2026, 9, 11)
PRIOR = date(2026, 9, 10)
ROOT = Path(__file__).resolve().parents[2]
APPROVED = {"lotte_chemical_afternoon", "lotte_chemical_midday", "lx_semicon_morning"}


def test_revision_history_and_unapproved_policies(tmp_path):
    before = baseline_policies_for_target_date(PRIOR)
    after = baseline_policies_for_target_date(DAY)
    assert len(before) == 59 and len(after) == 61
    assert set(after) - set(before) == APPROVED - {"lotte_chemical_afternoon"}
    assert {rid for rid in before if before[rid] != after[rid]} == {
        "lotte_chemical_afternoon"
    }
    assert runtime_profile_exclusions(DAY) == runtime_profile_exclusions(PRIOR)
    assert len(runtime_profile_exclusions(DAY)) == 3
    assert (
        get_profile("lotte_chemical_afternoon", target_date=PRIOR).policy.target_ticks
        == 2
    )
    assert (
        get_profile("lotte_chemical_afternoon", target_date=DAY).policy.target_ticks
        == 4
    )
    with pytest.raises(ValueError):
        get_profile("lx_semicon_morning", target_date=PRIOR)
    for day in (PRIOR, DAY):
        payload, _ = build_applied_policy(target_date=day, candidate_dir=tmp_path)
        assert validate_applied(payload, target_date=day) == (True, "valid")
        assert not validate_applied(payload, target_date=PRIOR if day == DAY else DAY)[
            0
        ]


@pytest.mark.parametrize("source_date", [date(2026, 9, 8), date(2026, 9, 9), PRIOR])
def test_candidate_crosses_all_revisions_preserving_actual_unapproved_policy(
    tmp_path, source_date
):
    candidate = _source_candidate(tmp_path, source_date)
    normalized = candidate_policies_with_current_baselines(candidate, target_date=DAY)
    approved = set()
    for transition in [
        PROFILE_REVISION_20260909_TRANSITION,
        PROFILE_REVISION_20260910_TRANSITION,
        PROFILE_REVISION_20260911_TRANSITION,
    ]:
        if source_date < date.fromisoformat(transition["effective_target_date"]) <= DAY:
            approved.update(transition["approved_profile_ids"])
    baseline = baseline_policies_for_target_date(DAY)
    bound = candidate["source_runtime_policy_binding"]["policies"]
    assert len(normalized) == 61
    for rid, policy in normalized.items():
        assert policy == (baseline[rid] if rid in approved else bound[rid])


def test_real_frozen_evidence_and_same_owner_two_legs():
    for rid in APPROVED:
        profile = get_profile(rid, target_date=DAY)
        assert validate_research_evidence(profile, target_date=DAY) == (True, "ready")
        assert profile.policy.quantity == 20
        assert len(profile.policy.entry_legs(20000)) == 2


@pytest.mark.parametrize("mutation", ["negative_half", "changed_spot", "source_hash"])
def test_bad_evidence_cannot_enable_new_entry(tmp_path, mutation):
    transition = PROFILE_REVISION_20260911_TRANSITION
    evidence = json.loads((ROOT / transition["evidence_path"]).read_text())
    row = next(
        r
        for r in evidence["recommendations"]
        if r["profile_id"] == "candidate_108320_morning"
    )
    if mutation == "negative_half":
        row["calibration_second_half_ev_pct"] = -0.01
    elif mutation == "changed_spot":
        row["recommended_spot"]["target_ticks"] = 3
    else:
        evidence["source_report"]["canonical_sha256"] = "0" * 64
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(evidence))
    digest = hashlib.sha256(
        json.dumps(evidence, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()
    assert not validate_research_evidence(
        get_profile("lx_semicon_morning"), path, expected_sha256=digest, target_date=DAY
    )[0]


def test_standing_authority_date_and_exact_scope():
    path = ROOT / "data/config/symbol_owner_policy_standing_authority_2026-09-11.json"
    authority = load_standing_authority(
        path, observed_at=datetime(2026, 9, 11, 7, 32, tzinfo=ZoneInfo("Asia/Seoul"))
    )
    assert {
        k: v["allowed_owners"] for k, v in authority["symbols"].items()
    } == expected_machine_symbol_owners(DAY)
    assert "108320" not in expected_machine_symbol_owners(PRIOR)
    assert expected_machine_symbol_owners(DAY)["108320"] == [
        "episode",
        "main_scalping",
        "manual_operator",
    ]
    with pytest.raises(
        SymbolOwnerStandingAuthorityError, match="outside_effective_range"
    ):
        load_standing_authority(
            path,
            observed_at=datetime(2026, 9, 10, 23, 59, tzinfo=ZoneInfo("Asia/Seoul")),
        )


@pytest.mark.parametrize(
    "rid,hour,minute",
    [
        ("lx_semicon_morning", 9, 45),
        ("lotte_chemical_midday", 13, 15),
        ("lotte_chemical_afternoon", 14, 25),
    ],
)
def test_timer_and_wrapper_reach_exact_profile(rid, hour, minute):
    for pre, offset in [(False, 1), (True, 5)]:
        timer = (
            ROOT
            / "deploy/systemd"
            / (
                "korstockscan-low-price-two-leg-"
                + rid.replace("_", "-")
                + ("-preflight" if pre else "")
                + ".timer"
            )
        )
        clock = hour * 60 + minute - offset
        text = timer.read_text()
        assert f"{clock//60:02d}:{clock%60:02d}:00 Asia/Seoul" in text
        assert f"@{rid}.service" in text
        assert "Persistent=false" in text
    assert rid in (ROOT / "deploy/run_low_price_two_leg_preflight.sh").read_text()
    assert rid in (ROOT / "deploy/run_low_price_two_leg_live.sh").read_text()
