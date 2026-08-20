"""Apply the latest lower-price candidate as an exact-date PREOPEN policy."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.trading.low_price_two_leg.policy_runtime import (
    APPLIED_DIR,
    APPLIED_SCHEMA,
    CANDIDATE_DIR,
    KST,
    MAX_CANDIDATE_AGE_DAYS,
    apply_operator_policy_transitions,
    applied_path,
    atomic_write_json,
    baseline_policies_for_target_date,
    baseline_applied_payload,
    candidate_policies_with_current_baselines,
    operator_policy_transitions,
    policy_hash,
    policy_mutations_between,
    profile_revision_transition,
    validate_applied,
    validate_candidate,
)


def _candidate_date(path: Path) -> date | None:
    prefix = "low_price_two_leg_policy_candidate_"
    if not path.stem.startswith(prefix):
        return None
    try:
        return date.fromisoformat(path.stem.removeprefix(prefix))
    except ValueError:
        return None


def _latest_prior_candidate(candidate_dir: Path, target_date: date) -> Path | None:
    candidates = [
        (candidate_date, path)
        for path in candidate_dir.glob("low_price_two_leg_policy_candidate_*.json")
        if (candidate_date := _candidate_date(path)) is not None
        and candidate_date < target_date
    ]
    return max(candidates, default=(None, None), key=lambda item: item[0])[1]


def _candidate_policies(
    payload: dict[str, Any], *, target_date: date
) -> dict[str, dict[str, Any]]:
    return candidate_policies_with_current_baselines(payload, target_date=target_date)


def _applied_profile_selection_status(
    *,
    profile_id: str,
    policy: dict[str, Any],
    candidate: dict[str, Any],
    profile_revision_applied: bool,
    profile_revision: dict[str, Any] | None,
) -> str:
    candidate_item = (candidate.get("profiles") or {}).get(profile_id) or {}
    if profile_revision_applied:
        approved_profile_ids = (profile_revision or {}).get("approved_profile_ids")
        if approved_profile_ids is None and candidate_item.get("policy") != policy:
            return "user_approved_profile_revision_baseline"
        if profile_id in set(approved_profile_ids or []):
            return "user_approved_profile_revision_baseline"
        if candidate_item.get("policy") != policy:
            return "profile_revision_same_stage_mutation_not_applied"
    return str(
        candidate_item.get("selection_status")
        or "baseline_added_during_profile_universe_expansion"
    )


def build_applied_policy(
    *, target_date: date, candidate_dir: Path = CANDIDATE_DIR
) -> tuple[dict[str, Any], str]:
    candidate_path = _latest_prior_candidate(candidate_dir, target_date)
    if candidate_path is None:
        return (
            baseline_applied_payload(
                target_date=target_date, reason="baseline_no_prior_candidate"
            ),
            "baseline_no_prior_candidate",
        )
    candidate_date = _candidate_date(candidate_path)
    if candidate_date is None:
        raise ValueError("candidate_filename_date_invalid")
    if (target_date - candidate_date).days > MAX_CANDIDATE_AGE_DAYS:
        return (
            baseline_applied_payload(
                target_date=target_date, reason="baseline_candidate_stale"
            ),
            "baseline_candidate_stale",
        )
    try:
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"candidate_unreadable:{type(exc).__name__}") from exc
    valid, reason = validate_candidate(candidate)
    if not valid:
        raise ValueError(reason)
    if candidate.get("source_date") != candidate_date.isoformat():
        raise ValueError("candidate_filename_payload_date_mismatch")
    candidate_source_policies = _candidate_policies(
        candidate, target_date=candidate_date
    )
    candidate_policies = _candidate_policies(candidate, target_date=target_date)
    previous_path = _latest_prior_candidate(candidate_dir, candidate_date)
    previous_source_policies = {
        profile_id: dict(policy)
        for profile_id, policy in baseline_policies_for_target_date(
            candidate_date
        ).items()
    }
    previous_target_policies = {
        profile_id: dict(policy)
        for profile_id, policy in baseline_policies_for_target_date(target_date).items()
    }
    if previous_path is not None:
        try:
            previous = json.loads(previous_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"previous_candidate_unreadable:{type(exc).__name__}"
            ) from exc
        valid, reason = validate_candidate(previous)
        if not valid:
            raise ValueError(f"previous_candidate_{reason}")
        previous_source_policies = _candidate_policies(
            previous, target_date=candidate_date
        )
        previous_target_policies = _candidate_policies(
            previous, target_date=target_date
        )
    source_expected_mutations = policy_mutations_between(
        previous_source_policies, candidate_source_policies
    )
    if candidate.get("policy_mutations") != source_expected_mutations:
        raise ValueError("candidate_policy_mutation_lineage_mismatch")
    applied_mutations = policy_mutations_between(
        previous_target_policies, candidate_policies
    )
    policies = apply_operator_policy_transitions(
        candidate_policies, target_date=target_date
    )
    revision = profile_revision_transition(target_date)
    profile_revision_applied = bool(
        revision
        and candidate_date < date.fromisoformat(str(revision["effective_target_date"]))
    )
    selection_status = (
        "candidate_validated_profile_revision_applied"
        if profile_revision_applied
        else "candidate_applied"
    )
    payload = {
        "schema": APPLIED_SCHEMA,
        "target_date": target_date.isoformat(),
        "applied_at_kst": datetime.now(tz=KST).isoformat(timespec="seconds"),
        "source_date": candidate_date.isoformat(),
        "source_candidate": str(candidate_path),
        "source_candidate_hash": str(candidate["policy_hash"]),
        "selection_status": selection_status,
        "policy_hash": policy_hash(policies),
        "policy_mutations": applied_mutations,
        "profiles": {
            profile_id: {
                "selection_status": _applied_profile_selection_status(
                    profile_id=profile_id,
                    policy=policy,
                    candidate=candidate,
                    profile_revision_applied=profile_revision_applied,
                    profile_revision=revision,
                ),
                "selected_axis": (candidate.get("profiles") or {})
                .get(profile_id, {})
                .get("selected_axis"),
                "policy": policy,
            }
            for profile_id, policy in policies.items()
        },
        "decision_authority": "auto_bounded_live_low_price_two_leg_policy",
        "runtime_effect": True,
        "allowed_runtime_apply": True,
        "actual_order_submitted": False,
        "rollback": {
            "trigger": "invalid_or_missing_exact_date_applied_policy_at_service_start",
            "action": "block_that_profile_before_broker_gateway_construction",
            "fallback": "baseline_written_only_for_missing_or_stale_candidate",
        },
        "forbidden_uses": [
            "candidate_quantity_target_or_entry_validity_change",
            "target_change_outside_recorded_operator_policy_transition",
            "threshold_relaxation_below_baseline",
            "stop_loss_or_forced_exit_creation",
            "provider_bot_cap_or_broker_guard_change",
        ],
    }
    transitions = operator_policy_transitions(target_date)
    if transitions:
        payload["operator_policy_transitions"] = transitions
    if revision:
        payload["profile_revision_transition"] = revision
    valid, reason = validate_applied(payload, target_date=target_date)
    if not valid:
        raise ValueError(reason)
    return payload, selection_status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--candidate-dir", type=Path, default=CANDIDATE_DIR)
    parser.add_argument("--applied-dir", type=Path, default=APPLIED_DIR)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    target_date = date.fromisoformat(args.target_date)
    output_path = applied_path(target_date, applied_dir=args.applied_dir)
    if output_path.exists():
        try:
            existing = json.loads(output_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(
                json.dumps(
                    {
                        "status": "blocked_invalid_exact_date_policy",
                        "target_date": target_date.isoformat(),
                        "reason": f"applied_policy_unreadable:{type(exc).__name__}",
                        "runtime_effect": False,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            return 3
        valid, reason = validate_applied(existing, target_date=target_date)
        if not valid:
            print(
                json.dumps(
                    {
                        "status": "blocked_invalid_exact_date_policy",
                        "target_date": target_date.isoformat(),
                        "reason": reason,
                        "runtime_effect": False,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            return 3
        print(
            json.dumps(
                {
                    "status": "exact_date_policy_reused",
                    "target_date": target_date.isoformat(),
                    "output_path": str(output_path),
                    "policy_hash": existing["policy_hash"],
                    "written": False,
                    "runtime_effect": True,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    try:
        payload, status = build_applied_policy(
            target_date=target_date, candidate_dir=args.candidate_dir
        )
    except ValueError as exc:
        print(
            json.dumps(
                {
                    "status": "blocked_invalid_candidate",
                    "target_date": target_date.isoformat(),
                    "reason": str(exc),
                    "runtime_effect": False,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 2
    if args.write:
        atomic_write_json(output_path, payload)
    print(
        json.dumps(
            {
                "status": status,
                "target_date": target_date.isoformat(),
                "output_path": str(output_path),
                "policy_hash": payload["policy_hash"],
                "written": bool(args.write),
                "runtime_effect": bool(args.write),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
