"""Apply the latest prior Samsung entry candidate as an exact-date PREOPEN policy."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.trading.order.samsung_entry_policy import (
    APPLIED_DIR,
    APPLIED_SCHEMA,
    BASELINE_POLICIES,
    CANDIDATE_DIR,
    CANDIDATE_SCHEMA,
    KST,
    LEGACY_CANDIDATE_SCHEMA,
    LEGACY_MUTATING_CANDIDATE_LAST_SOURCE_DATE,
    MAX_CANDIDATE_AGE_DAYS,
    applied_path,
    atomic_write_json,
    baseline_applied_payload,
    candidate_artifact_hash,
    candidate_policies_with_current_baselines,
    canonical_hash,
    file_sha256,
    policy_hash,
    policy_mutations_between,
    validate_applied,
    validate_candidate,
)
from src.utils.constants import DATA_DIR

REPORT_DIR = DATA_DIR / "report" / "samsung_machine_entry_tuning"
SOURCE_QUALITY_DIR = DATA_DIR / "report" / "observation_source_quality_audit"


def _candidate_date(path: Path) -> date | None:
    prefix = "samsung_machine_entry_policy_candidate_"
    if not path.stem.startswith(prefix):
        return None
    try:
        return date.fromisoformat(path.stem.removeprefix(prefix))
    except ValueError:
        return None


def _latest_prior_candidate(candidate_dir: Path, target_date: date) -> Path | None:
    candidates = [
        (candidate_date, path)
        for path in candidate_dir.glob("samsung_machine_entry_policy_candidate_*.json")
        if (candidate_date := _candidate_date(path)) is not None
        and candidate_date < target_date
    ]
    return max(candidates, default=(None, None), key=lambda item: item[0])[1]


def build_applied_policy(
    *,
    target_date: date,
    candidate_dir: Path = CANDIDATE_DIR,
    report_dir: Path = REPORT_DIR,
    source_quality_dir: Path = SOURCE_QUALITY_DIR,
    source_applied_dir: Path = APPLIED_DIR,
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
    if (
        candidate.get("schema") == LEGACY_CANDIDATE_SCHEMA
        and candidate_date > LEGACY_MUTATING_CANDIDATE_LAST_SOURCE_DATE
    ):
        return (
            baseline_applied_payload(
                target_date=target_date,
                reason="baseline_legacy_candidate_without_evidence_binding",
            ),
            "baseline_legacy_candidate_without_evidence_binding",
        )
    source_report: dict[str, Any] | None = None
    if candidate.get("schema") == CANDIDATE_SCHEMA:
        source_report_path = report_dir / (
            f"samsung_machine_entry_tuning_{candidate_date.isoformat()}.json"
        )
        try:
            source_report = json.loads(source_report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"candidate_source_report_unreadable:{type(exc).__name__}"
            ) from exc
        valid, reason = validate_candidate(candidate, source_report=source_report)
        if not valid:
            raise ValueError(reason)
        source_quality_path = source_quality_dir / (
            f"observation_source_quality_audit_{candidate_date.isoformat()}.json"
        )
        preflight = candidate["source_quality_preflight"]
        if preflight.get("source_artifact_present") is False:
            expected_missing_hash = canonical_hash(
                {
                    key: value
                    for key, value in preflight.items()
                    if key != "source_sha256"
                }
            )
            if (
                source_quality_path.exists()
                or preflight.get("source_sha256") != expected_missing_hash
            ):
                raise ValueError("candidate_source_quality_missing_state_changed")
        else:
            try:
                source_quality = json.loads(
                    source_quality_path.read_text(encoding="utf-8")
                )
                source_quality_hash = file_sha256(source_quality_path)
            except (OSError, json.JSONDecodeError) as exc:
                raise ValueError(
                    f"candidate_source_quality_unreadable:{type(exc).__name__}"
                ) from exc
            observed_allowed = bool(
                str(source_quality.get("status") or "").lower() in {"pass", "warning"}
                and (source_quality.get("summary") or {}).get("tuning_input_allowed")
                is True
            )
            if source_quality_hash != preflight[
                "source_sha256"
            ] or observed_allowed != bool(preflight.get("tuning_input_allowed")):
                raise ValueError("candidate_source_quality_artifact_mismatch")
        if candidate.get("policy_mutations") and not preflight.get(
            "tuning_input_allowed"
        ):
            raise ValueError("candidate_source_quality_blocked_for_mutation")
    policies = candidate_policies_with_current_baselines(candidate)
    previous_path = _latest_prior_candidate(candidate_dir, candidate_date)
    previous_policies = {
        machine: dict(policy) for machine, policy in BASELINE_POLICIES.items()
    }
    source_bound_epoch = bool(
        source_report
        and source_report.get("schema") == "samsung_machine_entry_tuning_report_v9"
    )
    if source_bound_epoch:
        from src.engine.monitoring.samsung_machine_entry_tuning import (
            _runtime_policy_binding,
        )

        observed_binding = _runtime_policy_binding(
            candidate_date.isoformat(), source_applied_dir
        )
        if (
            observed_binding.get("status") == "invalid"
            or candidate.get("source_runtime_policy_binding") != observed_binding
            or source_report.get("source_runtime_policy_binding") != observed_binding
        ):
            raise ValueError("candidate_actual_applied_policy_binding_mismatch")
        previous_policies = observed_binding["policies"]
    elif previous_path is not None:
        try:
            previous = json.loads(previous_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"previous_candidate_unreadable:{type(exc).__name__}"
            ) from exc
        valid, reason = validate_candidate(previous)
        if not valid:
            raise ValueError(f"previous_candidate_{reason}")
        previous_policies = candidate_policies_with_current_baselines(previous)
    expected_mutations = policy_mutations_between(
        previous_policies,
        policies,
        include_kind=candidate.get("schema") == CANDIDATE_SCHEMA,
    )
    if candidate.get("policy_mutations") != expected_mutations:
        raise ValueError("candidate_policy_mutation_lineage_mismatch")
    if source_report is not None:
        from src.engine.monitoring.samsung_machine_entry_tuning import (
            build_policy_candidate,
        )

        expected_candidate = build_policy_candidate(
            source_report, prior_policies=previous_policies
        )
        if candidate.get("candidate_hash") != expected_candidate.get(
            "candidate_hash"
        ) or candidate_artifact_hash(candidate) != candidate_artifact_hash(
            expected_candidate
        ):
            raise ValueError("candidate_does_not_match_bound_report_evidence")
    applied_mutations = policy_mutations_between(
        previous_policies, policies, include_kind=True
    )
    payload = {
        "schema": APPLIED_SCHEMA,
        "target_date": target_date.isoformat(),
        "applied_at_kst": datetime.now(tz=KST).isoformat(timespec="seconds"),
        "source_date": candidate_date.isoformat(),
        "source_candidate": str(candidate_path),
        "source_candidate_hash": str(
            candidate.get("candidate_hash") or file_sha256(candidate_path)
        ),
        "source_report_hash": str(
            (candidate.get("source_report_binding") or {}).get("sha256")
            or file_sha256(candidate_path)
        ),
        "source_quality_artifact_hash": str(
            (candidate.get("source_quality_preflight") or {}).get("source_sha256")
            or file_sha256(candidate_path)
        ),
        "selection_status": "candidate_applied",
        "policy_hash": policy_hash(policies),
        "policy_mutations": applied_mutations,
        "machines": {
            machine: {
                "selection_status": str(
                    candidate["machines"][machine].get("selection_status") or ""
                ),
                "selected_axis": candidate["machines"][machine].get("selected_axis"),
                "policy": policy,
            }
            for machine, policy in policies.items()
        },
        "decision_authority": "auto_bounded_live_samsung_entry_policy",
        "runtime_effect": True,
        "allowed_runtime_apply": True,
        "actual_order_submitted": False,
        "rollback": {
            "trigger": (
                "invalid_or_missing_exact_date_applied_policy_or_negative_"
                "post_apply_version_evidence"
            ),
            "action": (
                "block_before_gateway_or_apply_candidate_owned_single_axis_"
                "bounded_rollback"
            ),
            "fallback": "baseline_is_written_only_for_missing_stale_or_unbound_candidate",
        },
        "forbidden_uses": [
            "quantity_target_or_entry_validity_change",
            "threshold_relaxation_beyond_baseline",
            "stop_loss_or_forced_exit_creation",
            "provider_bot_cap_or_broker_guard_change",
        ],
    }
    valid, reason = validate_applied(payload, target_date=target_date)
    if not valid:
        raise ValueError(reason)
    return payload, "candidate_applied"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--candidate-dir", type=Path, default=CANDIDATE_DIR)
    parser.add_argument("--applied-dir", type=Path, default=APPLIED_DIR)
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--source-quality-dir", type=Path, default=SOURCE_QUALITY_DIR)
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
            target_date=target_date,
            candidate_dir=args.candidate_dir,
            report_dir=args.report_dir,
            source_quality_dir=args.source_quality_dir,
            source_applied_dir=args.applied_dir,
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
