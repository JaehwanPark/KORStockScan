"""Fail-closed standing-authorization bridge for the first AI-quality candidate.

The artifact produced here records a reviewed, one-shot operator intent.  It is
not an operator decision artifact and is deliberately incompatible with the
PREOPEN handoff consumer.  A future R3 source-only candidate can be bound to
that intent only when every declared identity matches.  Even after a match,
the result remains ``awaiting_runtime_design`` until the candidate is converted
to the existing machine policy promotion contract and passes that contract's
evidence and runtime-design gates.

This module never registers a runtime family, mutates runtime state, emits an
apply-authorizing handoff, calls a provider, or submits an order.

The authorization expiry applies to the first-candidate decision only. A
caller may bypass that time check for a later candidate only after the trusted
approval consumer has independently validated a guarded-apply plus post-apply
attribution enrollment for the exact same bounded family.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from src.engine.automation import machine_microstructure_policy_approval as approval

KST = ZoneInfo("Asia/Seoul")
STANDING_AUTHORIZATION_SCHEMA = (
    "main_ai_quality_first_candidate_standing_authorization_v1"
)
RESOLUTION_SCHEMA = "main_ai_quality_standing_authorization_resolution_v1"
R3_SCHEMA = "main_ai_quality_source_only_candidate_manifest_v1"
SOURCE_CANDIDATE_FAMILY = "main_ai_quality_prompt_contract"
TUNING_AXIS = "prompt_contract_effect"
# The first 20-clean-trading-day candidate can slip when any source day is
# excluded.  Keep the one-shot exact hash binding long enough to avoid manual
# renewal while still bounding the reviewed intent to one calendar quarter.
MAX_AUTHORIZATION_LIFETIME = timedelta(days=62)
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

SOURCE_ONLY_AUTHORITY: dict[str, Any] = {
    "decision_authority": "source_only_standing_intent_matching",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "runtime_apply_performed": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
}

FORBIDDEN_USES = [
    "use_as_machine_microstructure_operator_decision",
    "use_as_preopen_apply_handoff",
    "register_runtime_family_from_source_candidate",
    "approve_unknown_or_unreviewed_prompt_contract",
    "approve_multiple_or_tied_candidates",
    "bypass_previous_post_apply_attribution",
    "change_order_quantity_provider_bot_threshold_or_hard_safety",
]


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _content_sha256(value: Mapping[str, Any], field: str) -> str:
    return _sha256({key: item for key, item in value.items() if key != field})


def _aware_kst(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise ValueError("standing_authorization_datetime_invalid") from exc
    if parsed.tzinfo is None:
        raise ValueError("standing_authorization_datetime_must_be_aware")
    return parsed.astimezone(KST)


def _exact_sha(value: Any) -> str:
    text = str(value or "").strip()
    if not SHA256_PATTERN.fullmatch(text):
        raise ValueError("standing_authorization_sha256_invalid")
    return text


def _exact_nonempty(value: Any, error: str) -> str:
    text = str(value or "").strip()
    if not text or "*" in text:
        raise ValueError(error)
    return text


def build_standing_authorization(
    *,
    operator_authorization_id: str,
    operator_instruction: str,
    reviewed_at_kst: str,
    expires_at_kst: str,
    runtime_family: str,
    stage: str,
    axis: str,
    bounded_values: Mapping[str, Any],
    bounded_contract_sha256: str,
    evidence_contract: Mapping[str, Any],
    expected_runtime_registry_entry_sha256: str,
    expected_preopen_consumer: str,
    effective_venue: str,
    session_bucket: str,
    source_candidate_family: str = SOURCE_CANDIDATE_FAMILY,
) -> dict[str, Any]:
    """Build an immutable one-shot intent without granting apply authority."""

    reviewed = _aware_kst(reviewed_at_kst)
    expires = _aware_kst(expires_at_kst)
    if expires <= reviewed or expires - reviewed > MAX_AUTHORIZATION_LIFETIME:
        raise ValueError("standing_authorization_expiry_out_of_bounds")
    family = _exact_nonempty(runtime_family, "runtime_family_not_exact")
    stage_value = _exact_nonempty(stage, "runtime_stage_not_exact")
    if stage_value not in approval.VALID_STAGES:
        raise ValueError("runtime_stage_invalid")
    axis_value = _exact_nonempty(axis, "runtime_axis_not_exact")
    source_family = _exact_nonempty(
        source_candidate_family, "source_candidate_family_not_exact"
    )
    consumer = _exact_nonempty(expected_preopen_consumer, "preopen_consumer_not_exact")
    venue = _exact_nonempty(effective_venue, "effective_venue_not_exact")
    session = _exact_nonempty(session_bucket, "session_bucket_not_exact")
    if not isinstance(bounded_values, Mapping) or set(bounded_values) != {
        "current",
        "recommended",
    }:
        raise ValueError("bounded_values_must_be_exact_current_and_recommended")
    current = _exact_sha(bounded_values.get("current"))
    recommended = _exact_sha(bounded_values.get("recommended"))
    if current == recommended:
        raise ValueError("bounded_values_no_change")
    if not isinstance(evidence_contract, Mapping) or not evidence_contract:
        raise ValueError("evidence_contract_missing")
    authorization_id = _exact_nonempty(
        operator_authorization_id, "operator_authorization_id_missing"
    )
    instruction = _exact_nonempty(operator_instruction, "operator_instruction_missing")
    body = {
        "schema": STANDING_AUTHORIZATION_SCHEMA,
        "operator_authorization_id": authorization_id,
        "operator_instruction": instruction,
        "reviewed_at_kst": reviewed.isoformat(timespec="seconds"),
        "expires_at_kst": expires.isoformat(timespec="seconds"),
        "one_shot": True,
        "consumed_candidate_sha256": None,
        "source_candidate_family": source_family,
        "runtime_family": family,
        "stage": stage_value,
        "axis": axis_value,
        "effective_venue": venue,
        "session_bucket": session,
        "bounded_values": {"current": current, "recommended": recommended},
        "bounded_contract_sha256": _exact_sha(bounded_contract_sha256),
        "evidence_contract": dict(evidence_contract),
        "evidence_contract_sha256": _sha256(evidence_contract),
        "expected_runtime_registry_entry_sha256": _exact_sha(
            expected_runtime_registry_entry_sha256
        ),
        "expected_preopen_consumer": consumer,
        "status": "standing_intent_reviewed_source_only",
        "forbidden_uses": list(FORBIDDEN_USES),
        **SOURCE_ONLY_AUTHORITY,
    }
    return {**body, "artifact_content_sha256": _sha256(body)}


def _authorization_errors(value: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if value.get("schema") != STANDING_AUTHORIZATION_SCHEMA:
        errors.append("standing_authorization_schema_invalid")
    if value.get("artifact_content_sha256") != _content_sha256(
        value, "artifact_content_sha256"
    ):
        errors.append("standing_authorization_hash_mismatch")
    if value.get("one_shot") is not True:
        errors.append("standing_authorization_not_one_shot")
    if value.get("status") != "standing_intent_reviewed_source_only":
        errors.append("standing_authorization_status_invalid")
    if value.get("consumed_candidate_sha256") is not None:
        errors.append("standing_authorization_already_consumed")
    for field, expected in SOURCE_ONLY_AUTHORITY.items():
        if value.get(field) != expected:
            errors.append(f"standing_authorization_authority_invalid:{field}")
    if value.get("forbidden_uses") != FORBIDDEN_USES:
        errors.append("standing_authorization_forbidden_uses_invalid")
    try:
        build_standing_authorization(
            operator_authorization_id=str(value.get("operator_authorization_id") or ""),
            operator_instruction=str(value.get("operator_instruction") or ""),
            reviewed_at_kst=str(value.get("reviewed_at_kst") or ""),
            expires_at_kst=str(value.get("expires_at_kst") or ""),
            runtime_family=str(value.get("runtime_family") or ""),
            stage=str(value.get("stage") or ""),
            axis=str(value.get("axis") or ""),
            bounded_values=(
                value.get("bounded_values")
                if isinstance(value.get("bounded_values"), Mapping)
                else {}
            ),
            bounded_contract_sha256=str(value.get("bounded_contract_sha256") or ""),
            evidence_contract=(
                value.get("evidence_contract")
                if isinstance(value.get("evidence_contract"), Mapping)
                else {}
            ),
            expected_runtime_registry_entry_sha256=str(
                value.get("expected_runtime_registry_entry_sha256") or ""
            ),
            expected_preopen_consumer=str(value.get("expected_preopen_consumer") or ""),
            effective_venue=str(value.get("effective_venue") or ""),
            session_bucket=str(value.get("session_bucket") or ""),
            source_candidate_family=str(value.get("source_candidate_family") or ""),
        )
    except ValueError as exc:
        errors.append(str(exc))
    if value.get("evidence_contract_sha256") != _sha256(value.get("evidence_contract")):
        errors.append("standing_evidence_contract_hash_mismatch")
    return sorted(set(errors))


def _manifest_errors(value: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if value.get("schema") != R3_SCHEMA:
        errors.append("r3_manifest_schema_invalid")
    if value.get("artifact_content_sha256") != _content_sha256(
        value, "artifact_content_sha256"
    ):
        errors.append("r3_manifest_hash_mismatch")
    candidates = value.get("candidates")
    if not isinstance(candidates, list):
        return [*errors, "r3_candidates_invalid"]
    candidate_count = value.get("candidate_count")
    if (
        isinstance(candidate_count, bool)
        or not isinstance(candidate_count, int)
        or candidate_count != len(candidates)
    ):
        errors.append("r3_candidate_count_mismatch")
    if value.get("status") != "source_only_candidates_ready":
        errors.append("r3_manifest_not_candidate_ready")
    if value.get("first_runtime_candidate_auto_apply_performed") is not False:
        errors.append("r3_manifest_prior_auto_apply_state_invalid")
    ids = [
        str(row.get("candidate_id") or "")
        for row in candidates
        if isinstance(row, Mapping)
    ]
    hashes = [
        str(row.get("candidate_sha256") or "")
        for row in candidates
        if isinstance(row, Mapping)
    ]
    if len(ids) != len(candidates) or len(set(ids)) != len(ids):
        errors.append("r3_candidate_ids_not_unique")
    if len(hashes) != len(candidates) or len(set(hashes)) != len(hashes):
        errors.append("r3_candidate_hashes_not_unique")
    for field in ("runtime_effect", "allowed_runtime_apply", "actual_order_submitted"):
        if value.get(field) is not False:
            errors.append(f"r3_manifest_authority_invalid:{field}")
    if value.get("broker_order_forbidden") is not True:
        errors.append("r3_manifest_authority_invalid:broker_order_forbidden")
    return errors


def _candidate_errors(candidate: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if not str(candidate.get("candidate_id") or "").strip():
        errors.append("r3_candidate_id_missing")
    candidate_content = {
        key: value
        for key, value in candidate.items()
        if key not in {"candidate_id", "candidate_sha256"}
    }
    if candidate.get("candidate_sha256") != _sha256(candidate_content):
        errors.append("r3_candidate_hash_mismatch")
    for field in ("runtime_effect", "allowed_runtime_apply", "actual_order_submitted"):
        if candidate.get(field) is not False:
            errors.append(f"r3_candidate_authority_invalid:{field}")
    if candidate.get("broker_order_forbidden") is not True:
        errors.append("r3_candidate_authority_invalid:broker_order_forbidden")
    if candidate.get("runtime_design_status") != (
        "design_required_no_registered_consumer"
    ):
        errors.append("r3_candidate_runtime_design_status_unknown")
    if candidate.get("first_exact_candidate_approval_required") is not True:
        errors.append("r3_candidate_first_exact_approval_contract_invalid")
    if candidate.get("continuous_auto_chain_eligible") is not False:
        errors.append("r3_candidate_auto_chain_contract_invalid")
    if candidate.get("provider_or_order_authority") is not False:
        errors.append("r3_candidate_provider_or_order_authority_invalid")
    for field in ("current_prompt_sha256", "recommended_prompt_sha256"):
        try:
            _exact_sha(candidate.get(field))
        except ValueError:
            errors.append(f"r3_candidate_{field}_invalid")
    try:
        _exact_sha(candidate.get("latest_symbol_master_artifact_sha256"))
    except ValueError:
        errors.append("r3_candidate_latest_symbol_master_sha256_invalid")
    try:
        datetime.strptime(
            str(candidate.get("latest_symbol_master_source_date") or ""), "%Y-%m-%d"
        )
    except ValueError:
        errors.append("r3_candidate_latest_symbol_master_source_date_invalid")
    return errors


def _registry_entry_sha256(value: Mapping[str, Any] | None) -> str | None:
    return approval._registry_entry_sha256(value)


def _prior_family_gate_errors(
    queue: Mapping[str, Any], *, runtime_family: str
) -> list[str]:
    errors: list[str] = []
    candidates = queue.get("candidates", [])
    if not isinstance(candidates, list):
        return ["approval_queue_candidates_invalid"]
    prior = []
    for entry in candidates:
        candidate = entry.get("candidate") if isinstance(entry, Mapping) else None
        design = (
            candidate.get("runtime_design") if isinstance(candidate, Mapping) else None
        )
        if (
            isinstance(design, Mapping)
            and design.get("runtime_family") == runtime_family
        ):
            prior.append(entry)
    if prior and any(
        entry.get("state") != approval.STATE_POST_APPLY_ATTRIBUTED for entry in prior
    ):
        errors.append("prior_family_candidate_not_post_apply_attributed")
    return errors


def resolve_standing_authorization(
    authorization: Mapping[str, Any],
    r3_manifest: Mapping[str, Any],
    *,
    approval_queue: Mapping[str, Any],
    runtime_registry: Mapping[str, Mapping[str, Any]] | None = None,
    now: datetime | None = None,
    enrolled_continuation: bool = False,
) -> dict[str, Any]:
    """Bind at most one exact R3 candidate, while retaining source-only authority."""

    checked_at = now or datetime.now(KST)
    if checked_at.tzinfo is None:
        raise ValueError("resolution_now_must_be_timezone_aware")
    checked_at = checked_at.astimezone(KST)
    authorization_errors = _authorization_errors(authorization)
    manifest_errors = _manifest_errors(r3_manifest)
    blocker_codes = [*authorization_errors, *manifest_errors]
    try:
        reviewed = _aware_kst(str(authorization.get("reviewed_at_kst") or ""))
        expires = _aware_kst(str(authorization.get("expires_at_kst") or ""))
    except ValueError:
        reviewed = checked_at + timedelta(microseconds=1)
        expires = checked_at
    # Expiry bounds the operator's first-candidate authorization. Once the
    # exact family has completed guarded apply and post-apply attribution, its
    # independently validated enrollment owns later same-contract candidates.
    if checked_at >= expires and not enrolled_continuation:
        blocker_codes.append("standing_authorization_expired")
    if checked_at < reviewed and not enrolled_continuation:
        blocker_codes.append("standing_authorization_not_yet_reviewed")

    family = str(authorization.get("runtime_family") or "")
    registry = (
        approval.TRUSTED_RUNTIME_FAMILY_REGISTRY
        if runtime_registry is None
        else runtime_registry
    )
    registry_entry = registry.get(family) if isinstance(registry, Mapping) else None
    if not isinstance(registry_entry, Mapping):
        blocker_codes.append("runtime_family_not_in_trusted_registry")
    else:
        registry_digest = _registry_entry_sha256(registry_entry)
        if registry_digest != authorization.get(
            "expected_runtime_registry_entry_sha256"
        ):
            blocker_codes.append("runtime_registry_entry_sha256_drift")
        if (
            registry_entry.get("enabled") is not True
            or registry_entry.get("stage") != authorization.get("stage")
            or registry_entry.get("axis") != authorization.get("axis")
            or registry_entry.get("bounded_contract_sha256")
            != authorization.get("bounded_contract_sha256")
            or registry_entry.get("preopen_consumer")
            != authorization.get("expected_preopen_consumer")
            or not str(registry_entry.get("apply_receipt_owner") or "").strip()
            or not str(registry_entry.get("post_apply_attribution_owner") or "").strip()
        ):
            blocker_codes.append("runtime_registry_contract_mismatch")
    blocker_codes.extend(
        _prior_family_gate_errors(approval_queue, runtime_family=family)
    )
    pre_match_control_errors = list(blocker_codes)

    candidates = r3_manifest.get("candidates")
    exact_matches: list[Mapping[str, Any]] = []
    candidate_validation_errors: list[str] = []
    if isinstance(candidates, list):
        for candidate in candidates:
            if not isinstance(candidate, Mapping):
                continue
            candidate_errors = _candidate_errors(candidate)
            if candidate_errors:
                blocker_codes.extend(candidate_errors)
                candidate_validation_errors.extend(candidate_errors)
                continue
            if (
                candidate.get("candidate_family")
                == authorization.get("source_candidate_family")
                and candidate.get("decision_stage") == authorization.get("stage")
                and candidate.get("tuning_axis") == TUNING_AXIS
                and candidate.get("effective_venue")
                == authorization.get("effective_venue")
                and candidate.get("session_bucket")
                == authorization.get("session_bucket")
                and candidate.get("current_prompt_sha256")
                == (authorization.get("bounded_values") or {}).get("current")
                and candidate.get("recommended_prompt_sha256")
                == (authorization.get("bounded_values") or {}).get("recommended")
                and _sha256(candidate.get("evidence_contract"))
                == authorization.get("evidence_contract_sha256")
                and candidate.get("evidence_contract")
                == authorization.get("evidence_contract")
            ):
                exact_matches.append(candidate)
            elif candidate.get("current_prompt_sha256") != (
                authorization.get("bounded_values") or {}
            ).get("current") or candidate.get("recommended_prompt_sha256") != (
                authorization.get("bounded_values") or {}
            ).get(
                "recommended"
            ):
                blocker_codes.append("unreviewed_prompt_contract")
    control_gates_pass = (
        not pre_match_control_errors and not candidate_validation_errors
    )
    if len(exact_matches) != 1 or not control_gates_pass:
        blocker_codes.append(
            "r3_exact_candidate_missing"
            if not exact_matches
            else (
                "r3_exact_candidate_multiple"
                if len(exact_matches) > 1
                else "r3_exact_candidate_binding_blocked_by_control_gate"
            )
        )

    binding = None
    if len(exact_matches) == 1 and control_gates_pass:
        match = exact_matches[0]
        binding = {
            "candidate_id": match.get("candidate_id"),
            "candidate_sha256": match.get("candidate_sha256"),
            "r3_manifest_sha256": r3_manifest.get("artifact_content_sha256"),
            "standing_authorization_sha256": authorization.get(
                "artifact_content_sha256"
            ),
            "runtime_family": family,
            "stage": authorization.get("stage"),
            "axis": authorization.get("axis"),
            "bounded_contract_sha256": authorization.get("bounded_contract_sha256"),
        }
        # The R3 schema intentionally carries only source-only aggregate gates.
        # It cannot satisfy evidence_readiness_errors/runtime_design_errors and
        # therefore must not be converted into APPROVAL_SCHEMA here.
        blocker_codes.extend(
            [
                "promotion_candidate_contract_not_materialized",
                "existing_evidence_readiness_gate_not_executable",
            ]
        )

    blocker_codes = sorted(set(blocker_codes))
    status = (
        "candidate_bound_awaiting_runtime_design"
        if binding is not None
        else "awaiting_runtime_design"
    )
    body = {
        "schema": RESOLUTION_SCHEMA,
        "checked_at_kst": checked_at.isoformat(timespec="seconds"),
        "status": status,
        "candidate_binding": binding,
        "blocker_codes": blocker_codes,
        "exact_candidate_bound_operator_decision_created": False,
        "preopen_handoff_created": False,
        "next_required_gate": (
            "register_and_review_the_exact_family_consumer_then_materialize_the_"
            "candidate_into_machine_microstructure_policy_promotion_candidate_v1_"
            "and_pass_evidence_readiness_errors_and_runtime_design_errors"
        ),
        "forbidden_uses": list(FORBIDDEN_USES),
        **SOURCE_ONLY_AUTHORITY,
    }
    return {**body, "artifact_content_sha256": _sha256(body)}


def write_artifact(path: Path, payload: Mapping[str, Any]) -> None:
    """Persist one immutable artifact without permitting replacement."""

    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    created = False
    try:
        fd = os.open(path, flags, 0o640)
        created = True
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        if created:
            path.unlink(missing_ok=True)
        raise
