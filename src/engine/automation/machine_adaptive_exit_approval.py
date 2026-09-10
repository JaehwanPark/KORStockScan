"""Initial exit-family bridge for the existing approval ledger and publisher.

No registry installation, default approval, scheduler or broker call.
The caller supplies independently pinned authority AND reviewed execution
readiness. Research candidates cannot supply either. R6 auto-maintenance is
not implemented by this initial-only bridge.
"""

from contextlib import ExitStack, nullcontext
from copy import deepcopy
from collections.abc import Mapping
from pathlib import Path
import json
import argparse

from src.engine.automation import machine_adaptive_exit_policy_apply as publisher
from src.trading.config import machine_adaptive_exit_activation as activation
from src.trading.config.machine_adaptive_exit_policy import (
    AUTHORITY,
    FAMILY,
    canonical_sha256,
)
from src.utils.jsonl_io import json_artifact_generation_lock

CONSUMER = "src.engine.automation.machine_adaptive_exit_approval.publish_preopen"
AXIS = "owned_position_adaptive_exit"
READINESS_FIELDS = {
    "source_sha256",
    "scope_keys",
    "same_stage_owner_conflict_free",
    "owner_services_reviewed",
}


def registry_entry(
    *, envelope, expected_envelope_sha256, runtime_code_sha256, execution_readiness
):
    """Build explicit caller-owned registry data, never register it globally.

    execution_readiness is the caller's independently reviewed execution
    evidence, not a claim read from the candidate/report. No True defaults.
    This API does not itself inspect a running service or authorize deployment.
    """
    activation.validate_envelope(
        envelope,
        expected_sha256=expected_envelope_sha256,
        runtime_code_sha256=runtime_code_sha256,
    )
    # The registry is persisted by the common ledger. Normalize JSON container
    # representation after strict validation, without changing semantic/hash
    # values (e.g. the policy parser accepts a tuple of runner lot IDs).
    envelope = json.loads(json.dumps(envelope, allow_nan=False))
    activation._exact(
        execution_readiness, READINESS_FIELDS, "initial_execution_readiness_required"
    )
    activation._require(
        activation._digest(execution_readiness["source_sha256"])
        and execution_readiness["scope_keys"] == sorted(envelope["scopes"])
        and execution_readiness["same_stage_owner_conflict_free"] is True
        and execution_readiness["owner_services_reviewed"] is True,
        "initial_execution_readiness_not_reviewed",
    )
    return {
        "enabled": True,
        "stage": "exit",
        "axis": AXIS,
        "bounded_contract_sha256": expected_envelope_sha256,
        "preopen_consumer": CONSUMER,
        "apply_receipt_owner": "machine_adaptive_exit_initial_policy_publish",
        "post_apply_attribution_owner": "machine_adaptive_exit_post_apply_attribution",
        "direct_order_authority": False,
        "provider_route_authority": False,
        "quantity_authority": False,
        "hard_safety_authority": False,
        "receipt_content_sha256_required": True,
        "requires_post_apply_attribution_before_auto_chain": True,
        "initial_only": True,
        "initial_approval": {
            "envelope": deepcopy(envelope),
            "expected_envelope_sha256": expected_envelope_sha256,
            "runtime_code_sha256": runtime_code_sha256,
            "execution_readiness": deepcopy(execution_readiness),
        },
    }


def _checked_entry(entry):
    activation._require(isinstance(entry, Mapping), "initial_trusted_registry_missing")
    context = entry.get("initial_approval")
    activation._exact(
        context,
        {
            "envelope",
            "expected_envelope_sha256",
            "runtime_code_sha256",
            "execution_readiness",
        },
        "initial_registry_context_invalid",
    )
    expected = registry_entry(**context)
    activation._require(
        set(entry) == set(expected)
        and canonical_sha256(entry) == canonical_sha256(expected),
        "initial_trusted_registry_mismatch",
    )
    return context["envelope"]


def load_initial_context(path, *, expected_byte_sha256):
    """Read an externally pinned operator context, never a report's registry."""
    receipt = activation.read_plain(Path(path))
    activation._require(
        activation._digest(expected_byte_sha256)
        and receipt.raw_sha256 == expected_byte_sha256,
        "initial_context_byte_hash_mismatch",
    )
    activation._exact(
        receipt.payload,
        {
            "envelope",
            "expected_envelope_sha256",
            "runtime_code_sha256",
            "execution_readiness",
        },
        "initial_context_fields_invalid",
    )
    try:
        return registry_entry(**receipt.payload)
    except (TypeError, KeyError, AttributeError) as exc:
        raise ValueError("initial_context_invalid:" + str(exc)) from exc


def _projection(selection, scope_key, entry):
    from src.engine.automation import machine_microstructure_policy_approval as ledger

    envelope = _checked_entry(entry)
    activation._require(scope_key in envelope["scopes"], "initial_scope_not_approved")
    activation.validate_selection(
        selection,
        scope_key=scope_key,
        approved_scope=envelope["scopes"][scope_key],
        source_date=envelope["source_date"],
    )
    native = selection["candidate"]
    owner, _, _, venue, session = scope_key.split("|")
    candidate = {
        "schema": ledger.CANDIDATE_SCHEMA,
        "candidate_id": native["recommendation_id"],
        "source_date": envelope["source_date"],
        "evidence_valid_through": envelope["target_date"],
        "owner": owner,
        "owner_scope_id": scope_key,
        "first_operator_approval_required": True,
        **AUTHORITY,
        "evidence": {
            "validator": activation.VALIDATOR,
            "selection": deepcopy(selection),
            "parent_byte_sha256": envelope["source_report_sha256"],
            "source_child_sha256": envelope["source_child_sha256"],
        },
        "runtime_design": {
            "runtime_family": FAMILY,
            "stage": "exit",
            "axis": AXIS,
            "mapping_status": "registered",
            "runtime_registry_verified": True,
            "same_stage_owner_conflict_free": True,
            "preopen_consumer": CONSUMER,
            "effective_venue": venue,
            "session_bucket": session,
            "bounded_values": {
                "current": "original_owner_exit_policy",
                "recommended": native["policy"]["policy_hash"],
            },
            "bounded_contract_sha256": entry["bounded_contract_sha256"],
            "rollback": {"action": envelope["lifecycle"]["rollback"]},
            "post_apply_attribution": {
                "owner": entry["post_apply_attribution_owner"],
                "required_for": "auto_maintenance_not_initial_approval",
            },
            "forbidden_uses": [
                "new_buy",
                "other_owner_orders",
                "safety_override",
                "initial_approval_as_auto_maintenance",
            ],
        },
    }
    candidate["candidate_sha256"] = ledger.candidate_sha256(candidate)
    return candidate


def build_candidates(*, source_path, trusted_entry):
    """Project native IDs from the same frozen parent; no source regeneration."""
    envelope = _checked_entry(trusted_entry)
    source = activation.read_plain(Path(source_path))
    activation._require(
        source.raw_sha256 == envelope["source_report_sha256"],
        "parent_byte_hash_mismatch",
    )
    selected = publisher.select_approved_source(source.payload, envelope=envelope)
    return [_projection(selected[key], key, trusted_entry) for key in sorted(selected)]


def candidate_errors(candidate, trusted_entry):
    """Dispatch only by the externally supplied, exact family/initial contract."""
    try:
        _checked_entry(trusted_entry)
        expected = _projection(
            candidate["evidence"]["selection"],
            candidate["owner_scope_id"],
            trusted_entry,
        )
        # Intake may omit its own projection hash. All other metadata, native
        # evidence and authority must exactly match the independently pinned map.
        actual = dict(candidate)
        actual.setdefault("candidate_sha256", expected["candidate_sha256"])
        activation._require(
            set(actual) == set(expected)
            and canonical_sha256(actual) == canonical_sha256(expected),
            "initial_candidate_projection_mismatch",
        )
        return []
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        return ["adaptive_exit_initial_contract:" + str(exc)]


def publish_preopen(
    *,
    queue_path,
    trusted_entry,
    source_path,
    envelope_path,
    output_path,
    now,
    check_only=False,
):
    """Consume every exact scheduled initial handoff before atomic publication.

    No operator decision is manufactured. The current queue and decision files
    must still approve the same native candidates under the same authorization
    ID as the pinned envelope. Publication does not mark a runtime/PID applied.
    """
    from src.engine.automation import machine_microstructure_policy_approval as ledger

    activation._require(type(check_only) is bool, "check_only_must_be_boolean")
    envelope = _checked_entry(trusted_entry)
    current = activation.aware_kst(now)
    activation._require(
        current.date().isoformat() == envelope["target_date"]
        and current.time() < activation.PREOPEN_CUTOFF_KST
        and current < activation.aware_kst(envelope["valid_from"]),
        "initial_preopen_target_or_cutoff_invalid",
    )
    registry = {FAMILY: trusted_entry}
    registry_hash = ledger._registry_entry_sha256(trusted_entry)
    expected = build_candidates(source_path=source_path, trusted_entry=trusted_entry)
    queue_path = Path(queue_path)
    activation.read_plain(queue_path)
    protected_paths = {
        Path(p).resolve() for p in (queue_path, source_path, envelope_path)
    }
    activation._require(
        Path(output_path).resolve() not in protected_paths,
        "policy_output_must_not_overwrite_authority",
    )
    with ExitStack() as stack:
        queue_lease = stack.enter_context(
            nullcontext()
            if check_only
            else json_artifact_generation_lock(
                queue_path, exclusive=False, blocking=False
            )
        )
        queue_read = activation.read_plain(queue_path, generation=queue_lease)
        queue = ledger.load_queue(queue_path, generation=queue_lease)
        reads = [(queue_path, queue_lease, queue_read)]
        provenance = {
            "queue_byte_sha256": queue_read.raw_sha256,
            "native_handoffs": {},
        }
        for candidate in expected:
            matches = [
                r
                for r in queue["candidates"]
                if r.get("candidate_id") == candidate["candidate_id"]
                and r.get("candidate_sha256") == candidate["candidate_sha256"]
            ]
            activation._require(len(matches) == 1, "initial_queue_candidate_missing")
            row = matches[0]
            activation._require(
                row["candidate"] == candidate
                and not ledger._persisted_candidate_errors(row)
                and not ledger.runtime_design_errors(
                    candidate, runtime_registry=registry
                )
                and row["state"] == ledger.STATE_PREOPEN_SCHEDULED
                and row.get("authorization_mode") == "first_explicit_operator_approval"
                and row.get("operator_authorization_id") == envelope["approval_id"]
                and row.get("preopen_target_date") == envelope["target_date"]
                and row.get("operator_registry_entry_sha256") == registry_hash,
                "initial_current_queue_authority_required",
            )
            artifacts = []
            artifact_reads = []
            for field in ("operator_decision_artifact", "preopen_handoff"):
                path = Path(row[field])
                activation._require(
                    path.resolve() != Path(output_path).resolve(),
                    "policy_output_must_not_overwrite_authority",
                )
                activation.read_plain(path)
                lease = stack.enter_context(
                    nullcontext()
                    if check_only
                    else json_artifact_generation_lock(
                        path, exclusive=False, blocking=False
                    )
                )
                read = activation.read_plain(path, generation=lease)
                reads.append((path, lease, read))
                artifact_reads.append(read)
                artifacts.append(read.payload)
            decision, handoff = artifacts
            common = {
                "queue_key": row["queue_key"],
                "candidate_id": candidate["candidate_id"],
                "candidate_sha256": candidate["candidate_sha256"],
                "runtime_family": FAMILY,
                "operator_authorization_id": envelope["approval_id"],
                "runtime_registry_entry_sha256": registry_hash,
                "runtime_effect": False,
                "allowed_runtime_apply": True,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            }
            for artifact in artifacts:
                activation._literal_contract(
                    {k: artifact.get(k) for k in common},
                    common,
                    "initial_handoff_authority_mismatch",
                )
                activation._require(
                    artifact.get("forbidden_uses")
                    == ledger.METRIC_CONTRACT["forbidden_uses"],
                    "initial_handoff_forbidden_uses_mismatch",
                )
            activation._exact(
                decision,
                set(common)
                | {
                    "schema",
                    "source_date",
                    "decision",
                    "decided_at_kst",
                    "operator_instruction",
                    "forbidden_uses",
                },
                "initial_decision_fields_invalid",
            )
            activation._exact(
                handoff,
                set(common)
                | {
                    "schema",
                    "target_date",
                    "created_at_kst",
                    "operator_decision_artifact",
                    "authorization_mode",
                    "family_enrollment",
                    "stage",
                    "axis",
                    "effective_venue",
                    "session_bucket",
                    "bounded_values",
                    "bounded_contract_sha256",
                    "preopen_consumer",
                    "rollback",
                    "post_apply_attribution",
                    "same_stage_owner_conflict_free",
                    "status",
                    "runtime_apply_performed",
                    "forbidden_uses",
                },
                "initial_handoff_fields_invalid",
            )
            activation._require(
                decision.get("schema") == ledger.APPROVAL_SCHEMA
                and decision.get("decision") == "approve"
                and decision.get("source_date") == envelope["source_date"]
                and decision.get("decided_at_kst") == row["operator_decision_at_kst"]
                and bool(str(decision.get("operator_instruction") or "").strip())
                and handoff.get("schema") == ledger.HANDOFF_SCHEMA
                and handoff.get("target_date") == envelope["target_date"]
                and handoff.get("authorization_mode")
                == "first_explicit_operator_approval"
                and handoff.get("operator_decision_artifact")
                == row["operator_decision_artifact"]
                and handoff.get("status") == "preopen_authorization_handoff_ready"
                and handoff.get("runtime_apply_performed") is False
                and handoff.get("same_stage_owner_conflict_free") is True,
                "initial_handoff_or_decision_invalid",
            )
            for field in (
                "stage",
                "axis",
                "effective_venue",
                "session_bucket",
                "bounded_values",
                "bounded_contract_sha256",
                "preopen_consumer",
                "rollback",
                "post_apply_attribution",
            ):
                activation._require(
                    handoff.get(field) == candidate["runtime_design"][field],
                    "initial_handoff_design_mismatch:" + field,
                )
            created = activation.aware_kst(handoff.get("created_at_kst"))
            decided = activation.aware_kst(decision.get("decided_at_kst"))
            activation._require(
                decided <= created <= current
                and created.date() == current.date()
                and created.time() < activation.PREOPEN_CUTOFF_KST,
                "initial_handoff_time_invalid",
            )
            provenance["native_handoffs"][candidate["candidate_id"]] = {
                "candidate_sha256": candidate["candidate_sha256"],
                "decision_byte_sha256": artifact_reads[0].raw_sha256,
                "handoff_byte_sha256": artifact_reads[1].raw_sha256,
            }
        provenance["canonical_sha256"] = canonical_sha256(provenance)
        context = trusted_entry["initial_approval"]
        current_envelope = activation.read_plain(Path(envelope_path)).payload
        activation.validate_envelope(
            current_envelope,
            expected_sha256=context["expected_envelope_sha256"],
            runtime_code_sha256=context["runtime_code_sha256"],
        )
        activation._require(
            activation.read_plain(Path(source_path)).raw_sha256
            == envelope["source_report_sha256"],
            "parent_changed_during_handoff_validation",
        )
        for path, lease, before in reads:
            activation._require(
                activation.read_plain(path, generation=lease) == before,
                "initial_authority_changed_during_validation",
            )
        if check_only:
            return {
                "status": "initial_handoffs_validated_not_published",
                "target_date": envelope["target_date"],
                "selected_scope_count": len(expected),
                "approval_ledger_receipt": provenance,
                **AUTHORITY,
            }
        return publisher._publish_initial_policy(
            source_path=source_path,
            envelope_path=envelope_path,
            output_path=output_path,
            expected_envelope_sha256=context["expected_envelope_sha256"],
            runtime_code_sha256=context["runtime_code_sha256"],
            now=current,
            approval_ledger_receipt=provenance,
        )


def main(argv=None):
    """Default check-only; a separately authorized operator must request publish."""
    from src.engine.automation import machine_microstructure_policy_approval as ledger

    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "context-path",
        "queue-path",
        "source-path",
        "envelope-path",
        "output-path",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--context-sha256", required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--publish", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        entry = load_initial_context(
            args.context_path, expected_byte_sha256=args.context_sha256
        )
        with (
            nullcontext()
            if not args.publish
            else json_artifact_generation_lock(
                args.context_path, exclusive=False, blocking=False
            )
        ):
            activation._require(
                load_initial_context(
                    args.context_path, expected_byte_sha256=args.context_sha256
                )
                == entry,
                "initial_context_changed",
            )
            result = publish_preopen(
                queue_path=args.queue_path,
                trusted_entry=entry,
                source_path=args.source_path,
                envelope_path=args.envelope_path,
                output_path=args.output_path,
                now=ledger._now_kst(),
                check_only=not args.publish,
            )
    except (ValueError, OSError) as exc:
        print(
            json.dumps(
                {"status": "blocked_contract_error", "reason": str(exc), **AUTHORITY},
                sort_keys=True,
            )
        )
        return 2
    print(
        json.dumps(
            {
                "status": result.get("status", "published_not_loaded"),
                "target_date": result["target_date"],
                "check_only": not args.publish,
                **AUTHORITY,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
