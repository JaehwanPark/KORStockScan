"""Scheduled current-axis candidate / PREOPEN / delivery handoff.

Registration and operator authorization are externally reviewed inputs. This
command never creates consent, changes an env, restarts a bot or calls AI.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path

from src.engine.scalping import main_ai_current_axis as policy
from src.engine.scalping import main_ai_current_axis_runtime as runtime
from src.engine.scalping.micro_reversion import ai_quality_cycle as cycle
from src.utils.jsonl_io import (
    iter_jsonl_objects_strict,
    json_artifact_generation_lock,
    write_json_object_generation_safe,
)


def owner_conflicts(target_date: str) -> list[str]:
    from src.engine.scalping import entry_setup_live_policy as entry_owner

    path = entry_owner.activation_path(target_date)
    if not runtime._present(path):
        # This producer runs AFTER the Entry Setup PREOPEN selection.
        return ["entry_setup_preopen_owner_state_missing"]
    try:
        activation = policy.read(path)
    except (OSError, ValueError, EOFError):
        return ["entry_setup_preopen_owner_state_invalid"]
    if activation.get(
        "schema"
    ) != entry_owner.PREOPEN_ACTIVATION_SCHEMA or activation.get(
        "artifact_sha256"
    ) != entry_owner._canonical_sha256(
        {key: value for key, value in activation.items() if key != "artifact_sha256"}
    ):
        return ["entry_setup_preopen_owner_state_invalid"]
    if activation.get("target_date") != target_date:
        return ["entry_setup_preopen_owner_wrong_date"]
    if (
        activation.get("runtime_effect") is not False
        or activation.get("allowed_runtime_apply") is not False
        or activation.get("status") != "inactive_fallback_v2_13"
    ):
        return ["entry_setup_live_policy"]
    return []


def postclose(target_date: str, *, root: Path, write: bool) -> dict:
    registration_path = root / "registration.json"
    if not runtime._present(registration_path):
        return {"status": "registration_missing_disabled", **policy.SOURCE_ONLY}
    registration = policy.read(registration_path)
    policy.check(registration, "main_ai_current_axis_registration_v1")
    if registration.get("contract_sha256") != policy.sha(policy.CONTRACT):
        raise ValueError("registration_contract_mismatch")
    scope = registration.get("scope", {})
    if (
        not isinstance(scope, dict)
        or set(scope) - {"selected_cost_profile_id"}
        or any(
            not isinstance(value, str) or not value.strip() for value in scope.values()
        )
    ):
        raise ValueError("registration_scope_invalid")
    rolling = policy.read(cycle.rolling_report_path(target_date))
    manifest = policy.read(cycle.r3_manifest_path(target_date))
    cycle.validate_r3_source_only_manifest(manifest, source_rolling_artifact=rolling)
    policy.validate_terminal_cycle(rolling, manifest)
    if (
        rolling.get("target_date") != target_date
        or manifest.get("target_date") != target_date
    ):
        raise ValueError("exact_postclose_source_date_required")
    choices = [
        row
        for row in manifest["candidates"]
        if row.get("tuning_axis") == policy.AXIS
        and row.get("current_contract_sha256")
        == registration.get("control", {}).get("contract_sha256")
        and row.get("recommended_contract_sha256")
        == registration.get("recommended", {}).get("contract_sha256")
        and row.get("decision_stage") == "entry"
        and row.get("effective_venue") == "KRX"
        and row.get("session_bucket") == "KRX_REGULAR"
        and all(row.get(key) == value for key, value in scope.items())
    ]
    if not choices:
        return {
            "status": "no_eligible_registered_candidate",
            "source_manifest_sha256": manifest[policy.HASH_FIELD],
            **policy.SOURCE_ONLY,
        }
    if len(choices) != 1:
        raise ValueError("multiple_current_axis_candidates_require_scope_selection")
    reference_date = choices[0]["latest_symbol_master_source_date"]
    paths = cycle._default_paths(reference_date)
    from src.engine.scalping.micro_reversion.ai_quality_bridge import (
        _verified_cost_config_from_path,
    )

    input_reference = {
        "bridge_config": asdict(
            _verified_cost_config_from_path(
                paths["cost_profile"],
                target_date=datetime.fromisoformat(reference_date).date(),
            )
        ),
        "symbol_master": policy.read(paths["symbol_master"]),
    }
    candidate = policy.build_candidate(
        rolling=rolling,
        manifest=manifest,
        candidate_id=choices[0]["candidate_id"],
        control=registration["control"],
        recommended=registration["recommended"],
        input_reference=input_reference,
    )
    if write:
        write_json_object_generation_safe(
            root / f"candidate_{candidate['target_date']}.json", candidate
        )
    return {
        "status": "candidate_ready_separate_authorization_required",
        "candidate_sha256": candidate[policy.HASH_FIELD],
        "candidate_id": candidate["candidate_id"],
        **policy.SOURCE_ONLY,
    }


def preopen(target_date: str, *, root: Path, write: bool, now: datetime) -> dict:
    if not policy.enabled():
        return {"status": "disabled", **policy.SOURCE_ONLY}
    if runtime._present(root / "rollback.json"):
        return {"status": "rolled_back", **policy.SOURCE_ONLY}
    if not runtime._present(root / "operator_authorization.json"):
        return {"status": "exact_operator_authorization_missing", **policy.SOURCE_ONLY}
    candidate = policy.read(root / f"candidate_{target_date}.json")
    if candidate.get("target_date") != target_date:
        raise ValueError("candidate_preopen_target_argument_mismatch")
    policy.validate_postclose_handoff(candidate, root=root)
    source_date = candidate["source_date"]
    rolling = policy.read(cycle.rolling_report_path(source_date))
    manifest = policy.read(cycle.r3_manifest_path(source_date))
    policy.validate_terminal_cycle(rolling, manifest)
    authorization = policy.read(root / "operator_authorization.json")
    first = None
    if authorization.get("first_candidate_sha256") != candidate[policy.HASH_FIELD]:
        # Renewal needs a committed first application. An exact first grant
        # can recover receipt-only writes after a crash before activation.
        first = policy.read(root / "enrollment_receipt.json")
        first_activation = policy.read(root / f"activation_{first['target_date']}.json")
        if first != policy.apply_receipt(first_activation):
            raise ValueError("enrollment_activation_receipt_not_committed")
    activation = policy.build_activation(
        candidate=candidate,
        rolling=rolling,
        manifest=manifest,
        authorization=authorization,
        now=now,
        owner_conflicts=owner_conflicts(target_date),
        first_receipt=first,
    )
    activation_path = root / f"activation_{target_date}.json"
    receipt_path = root / f"apply_receipt_{target_date}.json"
    if write:
        # Activation is the commit marker. A partial write is unusable by the
        # live consumer; reruns cannot overwrite an applied day's generation.
        with json_artifact_generation_lock(activation_path) as lease:
            if runtime._present(activation_path):
                prior = policy.read(activation_path)
                if (
                    prior.get("candidate_sha256") != activation["candidate_sha256"]
                    or prior.get("authorization_sha256")
                    != activation["authorization_sha256"]
                    or policy.read(receipt_path) != policy.apply_receipt(prior)
                ):
                    raise ValueError("immutable_preopen_generation_conflict")
                activation = prior
            else:
                receipt = policy.apply_receipt(activation)
                write_json_object_generation_safe(receipt_path, receipt)
                if (
                    authorization["first_candidate_sha256"]
                    == candidate[policy.HASH_FIELD]
                ):
                    write_json_object_generation_safe(
                        root / "enrollment_receipt.json", receipt
                    )
                write_json_object_generation_safe(
                    activation_path, activation, generation=lease
                )
    return {
        "status": "applied_preopen" if write else "preopen_dry_run_ready",
        "activation_sha256": activation[policy.HASH_FIELD],
        "runtime_apply_performed": write,
        "actual_order_submitted": False,
    }


def post_apply(target_date: str, *, root: Path, trace_path: Path) -> dict:
    activation_path = root / f"activation_{target_date}.json"
    activation = (
        policy.read(activation_path) if runtime._present(activation_path) else None
    )
    if activation is not None:
        receipt = policy.apply_receipt(activation)
        policy.validate_candidate(activation["candidate"])
        if (
            activation.get("target_date") != target_date
            or activation.get("candidate_sha256")
            != activation["candidate"][policy.HASH_FIELD]
            or policy.read(root / f"apply_receipt_{target_date}.json") != receipt
        ):
            raise ValueError("post_apply_activation_commit_invalid")
    if activation is None and not policy.enabled():
        rows = []
    elif not trace_path.exists() and not trace_path.with_suffix(".jsonl.gz").exists():
        if activation is not None:
            raise ValueError("active_family_trace_source_missing")
        rows = []
    else:
        rows = list(iter_jsonl_objects_strict(trace_path))
    return runtime.attribution(rows, target_date=target_date, activation=activation)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase", choices=("postclose", "preopen", "rollback"), required=True
    )
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--reason")
    args = parser.parse_args(argv)
    root = policy.RUNTIME_ROOT
    current = datetime.now(policy.KST)
    try:
        if args.phase == "postclose":
            try:
                result = postclose(args.target_date, root=root, write=args.write)
            except (OSError, EOFError, KeyError, TypeError, ValueError) as exc:
                # A failed next-session candidate must not suppress today's
                # exact-request delivery/revocation accounting.
                result = {
                    "status": "blocked_contract",
                    "reason": str(exc),
                    **policy.SOURCE_ONLY,
                }
            result["post_apply_attribution"] = post_apply(
                args.target_date,
                root=root,
                trace_path=policy.ROOT
                / "data/ai_decision_trace"
                / f"ai_decision_trace_{args.target_date}.jsonl",
            )
            if result["post_apply_attribution"]["source_quality_errors"]:
                result["status"] = "blocked_contract"
                result["reason"] = "post_apply_delivery_contract_gap"
        elif args.phase == "preopen":
            result = preopen(args.target_date, root=root, write=args.write, now=current)
        else:
            if not args.reason or args.target_date != current.date().isoformat():
                raise ValueError("rollback_requires_exact_current_date_and_reason")
            result = policy.seal(
                {
                    "schema": "main_ai_current_axis_rollback_v1",
                    "target_date": args.target_date,
                    "reason": args.reason,
                    "recorded_at_kst": current.isoformat(),
                    "status": "rolled_back",
                    **policy.SOURCE_ONLY,
                }
            )
            if args.write:
                write_json_object_generation_safe(root / "rollback.json", result)
    except (OSError, EOFError, KeyError, TypeError, ValueError) as exc:
        result = {
            "status": "blocked_contract",
            "reason": str(exc),
            **policy.SOURCE_ONLY,
        }
    result = policy.seal(
        {
            **result,
            "schema": "main_ai_current_axis_cycle_v1",
            "phase": args.phase,
            "target_date": args.target_date,
            "provider_call_performed": False,
        }
    )
    if args.write:
        write_json_object_generation_safe(
            root / f"{args.phase}_status_{args.target_date}.json", result
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 1 if result["status"] == "blocked_contract" else 0


if __name__ == "__main__":
    raise SystemExit(main())
