"""Internal initial policy publisher; no CLI, schedule or broker calls.

Inputs/outputs are explicit paths. Calling this function is an operational
publication and needs separate authority; importing it never publishes. The
operational entrypoint is machine_adaptive_exit_approval.publish_preopen, which
requires the common ledger handoffs. Tests exercise this primitive with temporary
files. There is no default approval file or numeric envelope.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path

from src.trading.config.machine_adaptive_exit_activation import (
    APPLIED_SCHEMA,
    PREOPEN_CUTOFF_KST,
    RECEIPT_SCHEMA,
    VALIDATOR,
    _literal_contract,
    _require,
    _signed,
    aware_kst,
    read_plain,
    validate_applied,
    validate_envelope,
)
from src.trading.config.machine_adaptive_exit_policy import AUTHORITY, canonical_sha256
from src.utils.jsonl_io import (
    json_artifact_generation_lock,
    write_json_object_generation_safe,
)


def select_approved_source(parent, *, envelope):
    """Consume the existing attribution child, never invent native IDs."""
    _require(
        isinstance(parent, dict)
        and parent.get("target_date") == envelope["source_date"],
        "parent_source_date_mismatch",
    )
    child = parent.get("rolling_policy_research_v2")
    _signed(child, "machine_adaptive_exit_source_census_v1")
    _literal_contract(child.get("authority"), AUTHORITY, "child_source_only_required")
    _require(
        child.get("target_date") == envelope["source_date"]
        and child["canonical_sha256"] == envelope["source_child_sha256"],
        "source_child_binding_mismatch",
    )
    study = child.get("all_scope_study")
    _signed(study, "machine_adaptive_exit_study_v1")
    _literal_contract(study.get("authority"), AUTHORITY, "study_source_only_required")
    _require(
        study.get("target_date") == envelope["source_date"]
        and study.get("status") == "study_evaluated",
        "study_not_evaluated",
    )
    candidates, evidence, rows = (
        study.get("policy_promotion_candidates"),
        study.get("evidence"),
        study.get("scopes"),
    )
    _require(
        all(isinstance(v, list) for v in (candidates, evidence, rows)),
        "study_lists_required",
    )
    selected = {}
    for key, approved in envelope["scopes"].items():
        scope_rows = [
            r for r in rows if isinstance(r, dict) and r.get("scope_key") == key
        ]
        _require(
            len(scope_rows) == 1
            and scope_rows[0].get("status") == "study_evaluated"
            and scope_rows[0].get("owner_census_valid") is True
            and scope_rows[0].get("execution_scope") is True,
            "approved_scope_source_not_ready",
        )
        matches = [
            c
            for c in candidates
            if isinstance(c, dict)
            and c.get("canonical_sha256") == approved["candidate_sha256"]
        ]
        _require(len(matches) == 1, "approved_candidate_missing_or_duplicate")
        candidate = matches[0]
        _require(
            sum(
                isinstance(c, dict)
                and c.get("recommendation_id") == candidate.get("recommendation_id")
                for c in candidates
            )
            == 1,
            "native_id_conflict",
        )
        selection = {"candidate": deepcopy(candidate)}
        for output, field in (
            ("base_evidence", "evidence_hash"),
            ("stress_evidence", "stress_evidence_hash"),
        ):
            matches = [
                e
                for e in evidence
                if isinstance(e, dict)
                and e.get("canonical_sha256") == candidate.get(field)
            ]
            _require(len(matches) == 1, "approved_evidence_missing_or_duplicate")
            selection[output] = deepcopy(matches[0])
        selected[key] = selection
    # A bad unselected scope remains a reported source gap, not a blanket veto.
    return selected


def _publish_initial_policy(
    *,
    source_path: Path,
    envelope_path: Path,
    output_path: Path,
    expected_envelope_sha256: str,
    runtime_code_sha256: str,
    now: datetime,
    approval_ledger_receipt: dict | None = None,
):
    """Validate first; atomically publish one immutable exact-date generation.

    Frozen candidate/evidence bytes survive later canonical report refreshes.
    The current envelope is still required at load time for revocation. A new
    target-date envelope cannot silently overwrite an already issued policy.
    Publication receipt and selected payload are one atomic file, not two
    independently successful artifacts.
    """
    paths = [Path(p).absolute() for p in (source_path, envelope_path, output_path)]
    _require(
        len(set(paths)) == 3 and len({p.resolve() for p in paths}) == 3,
        "publisher_paths_must_be_distinct",
    )
    source_path, envelope_path, output_path = paths
    # Read before taking a lease so a missing approval cannot create a parent.
    read_plain(envelope_path)
    with json_artifact_generation_lock(
        envelope_path, exclusive=False, blocking=False
    ) as approval_lease:
        approval_read = read_plain(envelope_path, generation=approval_lease)
        envelope = approval_read.payload
        validate_envelope(
            envelope,
            expected_sha256=expected_envelope_sha256,
            runtime_code_sha256=runtime_code_sha256,
        )
        current = aware_kst(now)
        _require(
            current.date().isoformat() == envelope["target_date"]
            and current.time() < PREOPEN_CUTOFF_KST
            and current < aware_kst(envelope["valid_from"]),
            "exact_date_preopen_publication_required",
        )
        source = read_plain(source_path)
        _require(
            source.raw_sha256 == envelope["source_report_sha256"],
            "parent_byte_hash_mismatch",
        )
        selections = select_approved_source(source.payload, envelope=envelope)
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "validator": VALIDATOR,
            "envelope_sha256": expected_envelope_sha256,
            "selection_sha256": canonical_sha256(selections),
            "published_at": current.isoformat(),
            "authority": dict(AUTHORITY),
            "status": "published_not_loaded",
        }
        if approval_ledger_receipt is not None:
            receipt["approval_ledger_receipt"] = deepcopy(approval_ledger_receipt)
        receipt["canonical_sha256"] = canonical_sha256(receipt)
        payload = {
            "schema": APPLIED_SCHEMA,
            "envelope_sha256": expected_envelope_sha256,
            **{
                k: envelope[k]
                for k in (
                    "family",
                    "source_date",
                    "target_date",
                    "source_report_sha256",
                    "source_child_sha256",
                )
            },
            "selections": selections,
            "publication_receipt": receipt,
        }
        payload["canonical_sha256"] = canonical_sha256(payload)
        kwargs = dict(
            envelope=envelope,
            expected_sha256=expected_envelope_sha256,
            runtime_code_sha256=runtime_code_sha256,
        )
        validate_applied(payload, **kwargs)
        with json_artifact_generation_lock(output_path, blocking=False) as output_lease:
            _require(
                read_plain(envelope_path, generation=approval_lease) == approval_read,
                "approval_changed_before_publish",
            )
            if (
                output_lease.stat_name(output_path.name) is not None
                or output_lease.stat_name(output_path.name + ".gz") is not None
            ):
                existing = read_plain(output_path, generation=output_lease).payload
                validate_applied(existing, **kwargs)
                _require(
                    existing["selections"] == selections,
                    "existing_policy_generation_conflict",
                )
                if approval_ledger_receipt is not None:
                    original_handoff = existing["publication_receipt"].get(
                        "approval_ledger_receipt"
                    )
                    _require(
                        isinstance(original_handoff, dict)
                        and original_handoff.get("native_handoffs")
                        == approval_ledger_receipt["native_handoffs"],
                        "existing_policy_approval_handoff_conflict",
                    )
                _require(
                    read_plain(envelope_path, generation=approval_lease)
                    == approval_read,
                    "approval_changed_during_publish",
                )
                return existing
            write_json_object_generation_safe(
                output_path, payload, sort_keys=True, generation=output_lease
            )
            installed = read_plain(output_path, generation=output_lease).payload
            _require(installed == payload, "policy_publish_readback_mismatch")
            _require(
                read_plain(envelope_path, generation=approval_lease) == approval_read,
                "approval_changed_during_publish",
            )
            return installed
