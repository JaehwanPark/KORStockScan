from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pytest

from src.engine.automation.samsung_machine_entry_policy_apply import (
    build_applied_policy,
    main,
)
from src.trading.order.samsung_entry_policy import (
    APPLIED_SCHEMA,
    BASELINE_POLICIES,
    CANDIDATE_SCHEMA,
    KST,
    OPERATOR_OVERRIDE_RUNTIME_SOURCE,
    atomic_write_json,
    baseline_applied_payload,
    candidate_policies_with_current_baselines,
    load_applied_machine_policy,
    operator_target_override,
    policy_hash,
    policy_mutations_between,
    validate_applied,
    validate_candidate,
    validate_machine_policy,
)


def _candidate(source_date: str) -> dict:
    policies = {machine: dict(policy) for machine, policy in BASELINE_POLICIES.items()}
    policies["midday"].update(
        {
            "rolling_high_drawdown_pct": 1.50,
        }
    )
    return {
        "schema": CANDIDATE_SCHEMA,
        "source_date": source_date,
        "source_report": "samsung_machine_entry_tuning",
        "source_report_schema": "samsung_machine_entry_tuning_report_v2",
        "clean_tuning_baseline_date": "2026-06-05",
        "decision_authority": "postclose_bounded_candidate_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "policy_hash": policy_hash(policies),
        "policy_mutations": policy_mutations_between(BASELINE_POLICIES, policies),
        "machines": {
            machine: {
                "selection_status": "test",
                "selected_axis": None,
                "policy": policy,
                "allowed_runtime_apply": True,
            }
            for machine, policy in policies.items()
        },
    }


def _legacy_two_share_candidate(source_date: str) -> dict:
    payload = _candidate(source_date)
    policies = {
        machine: dict(item["policy"]) for machine, item in payload["machines"].items()
    }
    for policy in policies.values():
        policy["quantity"] = 2
    payload["machines"] = {
        machine: {**payload["machines"][machine], "policy": policy}
        for machine, policy in policies.items()
    }
    payload["policy_hash"] = policy_hash(policies)
    return payload


def test_bounded_policy_rejects_relaxation_and_immutable_changes():
    assert {policy["quantity"] for policy in BASELINE_POLICIES.values()} == {20}
    relaxed = dict(BASELINE_POLICIES["midday"])
    relaxed["rolling_high_drawdown_pct"] = 1.0
    assert validate_machine_policy("midday", relaxed) == (
        False,
        "drawdown_outside_bounded_tightening",
    )

    changed_target = dict(BASELINE_POLICIES["afternoon"])
    changed_target["target_ticks"] = 3
    assert validate_machine_policy("afternoon", changed_target) == (
        False,
        "immutable_target_ticks_mismatch",
    )

    morning = dict(BASELINE_POLICIES["morning"])
    morning["sor_drawdown_pct"] = 1.0
    assert validate_machine_policy("morning", morning) == (
        False,
        "morning_policy_is_baseline_only",
    )


def test_candidate_rejects_more_than_one_same_stage_policy_axis():
    payload = _candidate("2026-08-11")
    payload["machines"]["midday"]["policy"]["rolling_low_proximity_pct"] = 0.10
    policies = {
        machine: item["policy"] for machine, item in payload["machines"].items()
    }
    payload["policy_hash"] = policy_hash(policies)
    payload["policy_mutations"] = policy_mutations_between(BASELINE_POLICIES, policies)

    assert validate_candidate(payload) == (
        False,
        "same_stage_single_axis_contract_invalid",
    )


def test_candidate_accepts_current_and_legacy_tuning_report_schemas():
    legacy = _candidate("2026-08-11")
    assert validate_candidate(legacy) == (True, "valid")

    current = _candidate("2026-08-11")
    for schema in (
        "samsung_machine_entry_tuning_report_v3",
        "samsung_machine_entry_tuning_report_v4",
    ):
        current["source_report_schema"] = schema
        assert validate_candidate(current) == (True, "valid")


def test_legacy_two_share_candidate_is_hash_validated_then_normalized():
    legacy = _legacy_two_share_candidate("2026-08-13")

    assert validate_candidate(legacy) == (True, "valid")
    normalized = candidate_policies_with_current_baselines(legacy)
    assert {policy["quantity"] for policy in normalized.values()} == {20}

    future = _legacy_two_share_candidate("2026-08-14")
    assert validate_candidate(future) == (
        False,
        "candidate_morning_immutable_quantity_mismatch",
    )


def test_preopen_migrates_legacy_candidate_to_current_quantity(tmp_path: Path):
    candidate_dir = tmp_path / "candidates"
    candidate_dir.mkdir()
    legacy = _legacy_two_share_candidate("2026-08-13")
    atomic_write_json(
        candidate_dir / "samsung_machine_entry_policy_candidate_2026-08-13.json",
        legacy,
    )

    applied, status = build_applied_policy(
        target_date=date(2026, 8, 14), candidate_dir=candidate_dir
    )

    assert status == "candidate_applied"
    assert applied["source_candidate_hash"] == legacy["policy_hash"]
    assert {item["policy"]["quantity"] for item in applied["machines"].values()} == {20}
    assert validate_applied(applied, target_date=date(2026, 8, 14)) == (
        True,
        "valid",
    )


def test_legacy_exact_date_applied_policy_remains_audit_compatible():
    target = date(2026, 8, 13)
    payload = baseline_applied_payload(target_date=target, reason="test")
    policies = {}
    for machine, item in payload["machines"].items():
        item["policy"]["quantity"] = 2
        policies[machine] = item["policy"]
    payload["policy_hash"] = policy_hash(policies)

    assert validate_applied(payload, target_date=target) == (True, "valid")
    future = json.loads(json.dumps(payload))
    future["target_date"] = "2026-08-14"
    assert validate_applied(future, target_date=date(2026, 8, 14)) == (
        False,
        "applied_morning_immutable_quantity_mismatch",
    )


def test_missing_candidate_writes_valid_exact_date_baseline(tmp_path: Path):
    target = date(2026, 8, 12)
    payload, status = build_applied_policy(
        target_date=target, candidate_dir=tmp_path / "candidates"
    )
    assert status == "baseline_no_prior_candidate"
    assert payload["schema"] == APPLIED_SCHEMA
    assert validate_applied(payload, target_date=target) == (True, "valid")

    applied_dir = tmp_path / "applied"
    atomic_write_json(
        applied_dir / f"samsung_machine_entry_policy_{target}.json", payload
    )
    policy, applied_hash, reason = load_applied_machine_policy(
        "midday", target_date=target, applied_dir=applied_dir
    )
    assert reason == "ready"
    assert policy == BASELINE_POLICIES["midday"]
    assert applied_hash == payload["policy_hash"]


def test_loader_applies_target3_only_after_operator_override_instant(tmp_path: Path):
    target = date(2026, 8, 14)
    payload = baseline_applied_payload(target_date=target, reason="test")
    applied_dir = tmp_path / "applied"
    atomic_write_json(
        applied_dir / f"samsung_machine_entry_policy_{target}.json", payload
    )

    before, before_hash, before_reason = load_applied_machine_policy(
        "morning",
        target_date=target,
        applied_dir=applied_dir,
        as_of=datetime(2026, 8, 14, 9, 21, 6, tzinfo=KST),
    )
    after, after_hash, after_reason = load_applied_machine_policy(
        "midday",
        target_date=target,
        applied_dir=applied_dir,
        as_of=datetime(2026, 8, 14, 9, 21, 7, tzinfo=KST),
    )

    assert before["target_ticks"] == 2
    assert before_hash == payload["policy_hash"]
    assert before_reason == "ready"
    assert after["target_ticks"] == 3
    assert after_hash != payload["policy_hash"]
    assert after_reason == "ready_operator_override"
    assert OPERATOR_OVERRIDE_RUNTIME_SOURCE.endswith("operator_override")
    override = operator_target_override(
        target_date=target,
        as_of=datetime(2026, 8, 14, 9, 21, 7, tzinfo=KST),
    )
    assert override is not None
    assert "morning_reentry" in override["runtime_scopes"]


def test_latest_valid_prior_candidate_is_applied_without_relaxing_guards(
    tmp_path: Path,
):
    candidate_dir = tmp_path / "candidates"
    candidate_dir.mkdir()
    payload = _candidate("2026-08-11")
    path = candidate_dir / "samsung_machine_entry_policy_candidate_2026-08-11.json"
    atomic_write_json(path, payload)

    applied, status = build_applied_policy(
        target_date=date(2026, 8, 12), candidate_dir=candidate_dir
    )

    assert validate_candidate(payload) == (True, "valid")
    assert status == "candidate_applied"
    assert applied["machines"]["midday"]["policy"]["rolling_high_drawdown_pct"] == 1.50
    assert applied["machines"]["midday"]["policy"]["entry_valid_completed_bars"] == 5
    assert applied["machines"]["midday"]["policy"]["target_ticks"] == 2
    assert applied["machines"]["morning"]["policy"] == BASELINE_POLICIES["morning"]
    assert validate_applied(applied, target_date=date(2026, 8, 12)) == (
        True,
        "valid",
    )


def test_invalid_latest_candidate_fails_closed_instead_of_skipping_to_older(
    tmp_path: Path,
):
    candidate_dir = tmp_path / "candidates"
    candidate_dir.mkdir()
    atomic_write_json(
        candidate_dir / "samsung_machine_entry_policy_candidate_2026-08-10.json",
        _candidate("2026-08-10"),
    )
    invalid = _candidate("2026-08-11")
    invalid["machines"]["midday"]["policy"]["rolling_low_proximity_pct"] = 0.30
    atomic_write_json(
        candidate_dir / "samsung_machine_entry_policy_candidate_2026-08-11.json",
        invalid,
    )

    with pytest.raises(ValueError, match="near_low_outside_bounded_tightening"):
        build_applied_policy(target_date=date(2026, 8, 12), candidate_dir=candidate_dir)


def test_apply_rejects_candidate_with_undeclared_policy_lineage(tmp_path: Path):
    candidate_dir = tmp_path / "candidates"
    candidate_dir.mkdir()
    payload = _candidate("2026-08-11")
    payload["policy_mutations"] = []
    atomic_write_json(
        candidate_dir / "samsung_machine_entry_policy_candidate_2026-08-11.json",
        payload,
    )

    with pytest.raises(ValueError, match="policy_mutation_lineage_mismatch"):
        build_applied_policy(target_date=date(2026, 8, 12), candidate_dir=candidate_dir)


def test_applied_loader_rejects_payload_hash_drift(tmp_path: Path):
    target = date(2026, 8, 12)
    payload, _ = build_applied_policy(
        target_date=target, candidate_dir=tmp_path / "candidates"
    )
    payload["machines"]["midday"]["policy"]["rolling_high_drawdown_pct"] = 1.50
    applied_dir = tmp_path / "applied"
    applied_dir.mkdir()
    path = applied_dir / f"samsung_machine_entry_policy_{target}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    policy, _, reason = load_applied_machine_policy(
        "midday", target_date=target, applied_dir=applied_dir
    )
    assert policy is None
    assert reason == "applied_policy_hash_mismatch"


def test_preopen_apply_reuses_valid_exact_date_policy_without_rewrite(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    candidate_dir = tmp_path / "candidates"
    applied_dir = tmp_path / "applied"
    args = [
        "--target-date",
        "2026-08-12",
        "--candidate-dir",
        str(candidate_dir),
        "--applied-dir",
        str(applied_dir),
        "--write",
    ]

    assert main(args) == 0
    capsys.readouterr()
    path = applied_dir / "samsung_machine_entry_policy_2026-08-12.json"
    first_content = path.read_bytes()
    first_mtime = path.stat().st_mtime_ns

    assert main(args) == 0
    result = json.loads(capsys.readouterr().out)

    assert result["status"] == "exact_date_policy_reused"
    assert path.read_bytes() == first_content
    assert path.stat().st_mtime_ns == first_mtime
