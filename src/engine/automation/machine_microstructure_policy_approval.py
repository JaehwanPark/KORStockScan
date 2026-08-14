"""Persist and surface first-approval gates for machine microstructure policy.

This module is a control-plane ledger.  It never mutates a runtime env or
submits an order.  Evidence-ready candidates remain visible until they are
designed, explicitly approved, rejected, or expired.  A PREOPEN run can emit
an exact-date authorization handoff only for a registered bounded family; the
family-owned consumer remains responsible for the actual guarded apply and
its apply/attribution receipts.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import tempfile
from collections import Counter
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping, Sequence
from urllib import parse, request
from zoneinfo import ZoneInfo

from src.engine.scalping.micro_reversion.contracts import CLEAN_BASELINE_DATE
from src.utils.constants import CONFIG_PATH, DATA_DIR, DEV_PATH

KST = ZoneInfo("Asia/Seoul")
QUEUE_SCHEMA = "machine_microstructure_policy_approval_queue_v1"
REPORT_SCHEMA = "machine_microstructure_policy_approval_status_v1"
CANDIDATE_SCHEMA = "machine_microstructure_policy_promotion_candidate_v1"
APPROVAL_SCHEMA = "machine_microstructure_policy_operator_decision_v1"
HANDOFF_SCHEMA = "machine_microstructure_policy_preopen_handoff_v1"
APPLY_RECEIPT_SCHEMA = "machine_microstructure_policy_family_apply_receipt_v1"

SOURCE_REPORT_DIR = DATA_DIR / "report" / "machine_microstructure_attribution"
QUEUE_DIR = DATA_DIR / "runtime" / "machine_microstructure_policy_approval"
DEFAULT_QUEUE_PATH = QUEUE_DIR / "queue.json"
REPORT_DIR = DATA_DIR / "report" / "machine_microstructure_policy_approval"
APPROVAL_DIR = (
    DATA_DIR / "threshold_cycle" / "approvals" / ("machine_microstructure_policy")
)
HANDOFF_DIR = (
    DATA_DIR
    / "threshold_cycle"
    / "machine_microstructure_policy"
    / ("preopen_handoffs")
)
APPLY_RECEIPT_DIR = (
    DATA_DIR / "threshold_cycle" / ("machine_microstructure_policy") / "apply_receipts"
)

STATE_DESIGN_REQUIRED = "DESIGN_REQUIRED"
STATE_REVIEW_READY = "REVIEW_READY"
STATE_USER_APPROVED = "USER_APPROVED"
STATE_PREOPEN_SCHEDULED = "PREOPEN_SCHEDULED"
STATE_APPLIED = "APPLIED"
STATE_POST_APPLY_ATTRIBUTED = "POST_APPLY_ATTRIBUTED"
STATE_AUTO_CHAIN_ELIGIBLE = "AUTO_CHAIN_ELIGIBLE"
STATE_HOLD = "HOLD"
STATE_REJECTED = "REJECTED"
STATE_EXPIRED = "EXPIRED"

REMINDER_STATES = {
    STATE_DESIGN_REQUIRED,
    STATE_REVIEW_READY,
    STATE_USER_APPROVED,
    STATE_PREOPEN_SCHEDULED,
    STATE_APPLIED,
    STATE_HOLD,
}
TERMINAL_STATES = {
    STATE_POST_APPLY_ATTRIBUTED,
    STATE_REJECTED,
    STATE_EXPIRED,
}
EXPIRABLE_STATES = {
    STATE_DESIGN_REQUIRED,
    STATE_REVIEW_READY,
    STATE_USER_APPROVED,
    STATE_PREOPEN_SCHEDULED,
    STATE_AUTO_CHAIN_ELIGIBLE,
    STATE_HOLD,
}
VALID_DECISIONS = {"approve", "hold", "reject"}
VALID_PHASES = {"postclose", "preopen"}
VALID_STAGES = {"entry", "submit", "holding", "scale_in", "exit"}
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

# Candidate producers cannot grant runtime authority to their own output.
# Families enter this source-owned registry only together with a real PREOPEN
# consumer, rollback/receipt implementation, and tests.  It is deliberately
# empty while this module remains an observation/approval control plane.
TRUSTED_RUNTIME_FAMILY_REGISTRY: Mapping[str, Mapping[str, Any]] = {}

METRIC_CONTRACT = {
    "metric_role": "operator_approval_control_plane",
    "decision_authority": "approval_reminder_and_preopen_handoff_only",
    "window_policy": "persistent_until_decision_expiry_or_post_apply_attribution",
    "sample_floor": (
        "five_observed_trading_days_twenty_matched_anchors_with_paired_"
        "cost_adjusted_positive_5d_10d_20d_ev"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": (
        "clean_baseline_exact_owner_symbol_session_bbo_depth_and_zero_invalid_rows"
    ),
    "forbidden_uses": [
        "runtime_env_mutation",
        "broker_order_submission",
        "threshold_or_provider_or_bot_or_cap_change",
        "approval_reuse_after_candidate_hash_change",
        "unregistered_family_preopen_scheduling",
        "same_stage_multi_axis_apply",
        "hard_safety_or_broker_guard_bypass",
    ],
}

Sender = Callable[[str, str, str], None]
ConfigLoader = Callable[[], tuple[str, str]]


def _now_kst(now: datetime | None = None) -> datetime:
    value = now or datetime.now(tz=KST)
    if value.tzinfo is None:
        value = value.replace(tzinfo=KST)
    return value.astimezone(KST)


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def candidate_sha256(candidate: Mapping[str, Any]) -> str:
    payload = dict(candidate)
    payload.pop("candidate_sha256", None)
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def _finite_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed != parsed or parsed in {float("inf"), float("-inf")}:
        return None
    return parsed


def _nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not numeric.is_integer():
        return None
    parsed = int(numeric)
    return parsed if parsed >= 0 else None


def _nonempty_mapping(value: Any) -> bool:
    return isinstance(value, Mapping) and bool(value)


def evidence_readiness_errors(candidate: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if candidate.get("schema") != CANDIDATE_SCHEMA:
        errors.append("candidate_schema_invalid")
    candidate_id = str(candidate.get("candidate_id") or "").strip()
    if not candidate_id:
        errors.append("candidate_id_missing")
    if candidate.get("first_operator_approval_required") not in {True, False}:
        errors.append("first_operator_approval_required_not_boolean")
    try:
        source_date = date.fromisoformat(str(candidate.get("source_date") or ""))
        valid_through = date.fromisoformat(
            str(candidate.get("evidence_valid_through") or "")
        )
        if valid_through < source_date:
            errors.append("evidence_valid_through_before_source_date")
        if source_date < CLEAN_BASELINE_DATE:
            errors.append("source_date_before_clean_baseline")
    except ValueError:
        errors.append("source_or_valid_through_date_invalid")

    if candidate.get("runtime_effect") is not False:
        errors.append("candidate_runtime_effect_must_be_false")
    if candidate.get("allowed_runtime_apply") is not False:
        errors.append("candidate_allowed_runtime_apply_must_be_false")
    if candidate.get("actual_order_submitted") is not False:
        errors.append("candidate_actual_order_submitted_must_be_false")
    if candidate.get("broker_order_forbidden") is not True:
        errors.append("candidate_broker_order_forbidden_must_be_true")

    evidence = candidate.get("evidence")
    if not isinstance(evidence, Mapping):
        return [*errors, "evidence_missing"]
    observed_days = _nonnegative_int(evidence.get("observed_trading_days"))
    matched_anchors = _nonnegative_int(evidence.get("matched_entry_anchors"))
    invalid_rows = _nonnegative_int(evidence.get("invalid_contract_row_count"))
    bbo_rate = _finite_float(evidence.get("bbo_complete_rate_pct"))
    depth_rate = _finite_float(evidence.get("depth_window_coverage_pct"))
    relative_uplift = _finite_float(evidence.get("relative_primary_ev_uplift_pct"))
    net_profit = _finite_float(evidence.get("primary_20d_net_profit"))
    rolling = evidence.get("rolling_source_quality_adjusted_ev_pct")
    if observed_days is None or observed_days < 5:
        errors.append("observed_trading_days_below_5")
    if matched_anchors is None or matched_anchors < 20:
        errors.append("matched_entry_anchors_below_20")
    if bbo_rate is None or bbo_rate < 95.0:
        errors.append("bbo_complete_rate_below_95pct")
    if depth_rate is None or depth_rate < 90.0:
        errors.append("depth_window_coverage_below_90pct")
    if invalid_rows != 0:
        errors.append("invalid_contract_rows_present")
    if not isinstance(rolling, Mapping) or any(
        (_finite_float(rolling.get(window)) or 0.0) <= 0.0
        for window in ("5d", "10d", "20d")
    ):
        errors.append("rolling_5d_10d_20d_ev_not_all_positive")
    if relative_uplift is None or relative_uplift < 1.0:
        errors.append("relative_primary_ev_uplift_below_1pct")
    if net_profit is None or net_profit <= 0.0:
        errors.append("primary_20d_net_profit_not_positive")
    for field in (
        "costs_included",
        "source_quality_pass",
        "paired_p10_not_worse",
        "held_unresolved_not_increased",
    ):
        if evidence.get(field) is not True:
            errors.append(f"{field}_not_true")
    return errors


def _trusted_registry_entry(
    family: str,
    runtime_registry: Mapping[str, Mapping[str, Any]] | None,
) -> Mapping[str, Any] | None:
    registry = (
        TRUSTED_RUNTIME_FAMILY_REGISTRY
        if runtime_registry is None
        else runtime_registry
    )
    entry = registry.get(family)
    return entry if isinstance(entry, Mapping) else None


def _registry_entry_sha256(entry: Mapping[str, Any] | None) -> str | None:
    return hashlib.sha256(_canonical_json(entry)).hexdigest() if entry else None


def runtime_design_errors(
    candidate: Mapping[str, Any],
    *,
    runtime_registry: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[str]:
    design = candidate.get("runtime_design")
    if not isinstance(design, Mapping):
        return ["runtime_design_missing"]
    errors: list[str] = []
    family = str(design.get("runtime_family") or "").strip()
    stage = str(design.get("stage") or "").strip()
    axis = str(design.get("axis") or "").strip()
    if not family:
        errors.append("runtime_family_missing")
    if stage not in VALID_STAGES:
        errors.append("runtime_stage_invalid")
    if not axis:
        errors.append("runtime_axis_missing")
    if design.get("mapping_status") != "registered":
        errors.append("runtime_family_mapping_not_registered")
    if design.get("runtime_registry_verified") is not True:
        errors.append("runtime_registry_not_verified")
    if design.get("same_stage_owner_conflict_free") is not True:
        errors.append("same_stage_owner_conflict_not_closed")
    if not str(design.get("preopen_consumer") or "").strip():
        errors.append("preopen_consumer_missing")
    bounded_values = design.get("bounded_values")
    if not _nonempty_mapping(bounded_values) or any(
        key not in bounded_values for key in ("current", "recommended")
    ):
        errors.append("bounded_values_missing")
    elif _canonical_json(bounded_values.get("current")) == _canonical_json(
        bounded_values.get("recommended")
    ):
        errors.append("bounded_values_no_change")
    if not SHA256_PATTERN.fullmatch(str(design.get("bounded_contract_sha256") or "")):
        errors.append("bounded_contract_sha256_invalid")
    if not _nonempty_mapping(design.get("rollback")):
        errors.append("rollback_missing")
    if not _nonempty_mapping(design.get("post_apply_attribution")):
        errors.append("post_apply_attribution_missing")
    forbidden = design.get("forbidden_uses")
    if not isinstance(forbidden, list) or not forbidden:
        errors.append("runtime_design_forbidden_uses_missing")
    registry_entry = _trusted_registry_entry(family, runtime_registry)
    if registry_entry is None:
        errors.append("runtime_family_not_in_trusted_registry")
    elif (
        registry_entry.get("enabled") is not True
        or registry_entry.get("stage") != stage
        or registry_entry.get("axis") != axis
        or registry_entry.get("bounded_contract_sha256")
        != design.get("bounded_contract_sha256")
        or registry_entry.get("preopen_consumer") != design.get("preopen_consumer")
        or not str(registry_entry.get("apply_receipt_owner") or "").strip()
    ):
        errors.append("runtime_family_trusted_registry_mismatch")
    return errors


def _empty_queue(*, now: datetime) -> dict[str, Any]:
    return {
        "schema": QUEUE_SCHEMA,
        "updated_at_kst": now.isoformat(timespec="seconds"),
        "metric_contract": METRIC_CONTRACT,
        "authority": {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
        "candidates": [],
        "family_enrollments": {},
    }


def load_queue(
    path: Path = DEFAULT_QUEUE_PATH, *, now: datetime | None = None
) -> dict[str, Any]:
    payload = _load_json(path)
    if payload is None:
        if path.exists():
            raise ValueError("approval_queue_unreadable")
        return _empty_queue(now=_now_kst(now))
    if (
        payload.get("schema") != QUEUE_SCHEMA
        or payload.get("metric_contract") != METRIC_CONTRACT
        or not isinstance(payload.get("candidates"), list)
        or not isinstance(payload.get("family_enrollments"), dict)
    ):
        raise ValueError("approval_queue_contract_invalid")
    return payload


def _queue_key(candidate_id: str, digest: str) -> str:
    return f"{candidate_id}:{digest[:16]}"


def _candidate_runtime_family(candidate: Mapping[str, Any]) -> str:
    design = candidate.get("runtime_design")
    return (
        str(design.get("runtime_family") or "").strip()
        if isinstance(design, Mapping)
        else ""
    )


def _entry_expired(entry: Mapping[str, Any], *, as_of_date: date) -> bool:
    try:
        return (
            date.fromisoformat(str(entry.get("evidence_valid_through") or ""))
            < as_of_date
        )
    except ValueError:
        return True


def _approval_artifacts(approval_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(approval_dir.glob("*.json")):
        payload = _load_json(path)
        if payload is not None:
            rows.append({**payload, "_artifact_path": str(path)})
    return rows


def _apply_operator_decisions(
    entries: list[dict[str, Any]],
    artifacts: Sequence[Mapping[str, Any]],
    *,
    runtime_registry: Mapping[str, Mapping[str, Any]] | None = None,
) -> None:
    by_key = {str(entry.get("queue_key") or ""): entry for entry in entries}
    for artifact in artifacts:
        if artifact.get("schema") != APPROVAL_SCHEMA:
            continue
        if (
            not str(artifact.get("operator_authorization_id") or "").strip()
            or not str(artifact.get("operator_instruction") or "").strip()
        ):
            continue
        key = str(artifact.get("queue_key") or "")
        entry = by_key.get(key)
        if entry is None:
            continue
        if str(artifact.get("candidate_sha256") or "") != str(
            entry.get("candidate_sha256") or ""
        ):
            continue
        decision = str(artifact.get("decision") or "")
        if decision not in VALID_DECISIONS:
            continue
        candidate = entry.get("candidate") or {}
        family = _candidate_runtime_family(candidate)
        registry_digest = _registry_entry_sha256(
            _trusted_registry_entry(family, runtime_registry)
        )
        if (
            str(artifact.get("candidate_id") or "")
            != str(entry.get("candidate_id") or "")
            or str(artifact.get("source_date") or "")
            != str(entry.get("source_date") or "")
            or str(artifact.get("runtime_family") or "") != family
            or str(artifact.get("runtime_registry_entry_sha256") or "")
            != str(registry_digest or "")
            or artifact.get("runtime_effect") is not False
            or artifact.get("allowed_runtime_apply") is not (decision == "approve")
            or artifact.get("actual_order_submitted") is not False
            or artifact.get("broker_order_forbidden") is not True
        ):
            continue
        entry["operator_decision_artifact"] = str(artifact.get("_artifact_path") or "")
        entry["operator_decision_at_kst"] = artifact.get("decided_at_kst")
        entry["operator_authorization_id"] = artifact.get("operator_authorization_id")
        entry["operator_registry_entry_sha256"] = registry_digest
        if decision == "approve" and entry.get("state") in {
            STATE_REVIEW_READY,
            STATE_HOLD,
        }:
            if runtime_design_errors(candidate, runtime_registry=runtime_registry):
                entry["state"] = STATE_DESIGN_REQUIRED
                entry["state_reason"] = "approval_ignored_runtime_design_not_ready"
            else:
                entry["state"] = STATE_USER_APPROVED
                entry["state_reason"] = "explicit_operator_approval_recorded"
        elif decision == "hold" and entry.get("state") in {
            STATE_DESIGN_REQUIRED,
            STATE_REVIEW_READY,
            STATE_USER_APPROVED,
        }:
            entry["state"] = STATE_HOLD
            entry["state_reason"] = "explicit_operator_hold_recorded"
        elif decision == "reject" and entry.get("state") in {
            STATE_DESIGN_REQUIRED,
            STATE_REVIEW_READY,
            STATE_USER_APPROVED,
            STATE_HOLD,
        }:
            entry["state"] = STATE_REJECTED
            entry["state_reason"] = "explicit_operator_rejection_recorded"


def _handoff_matches_entry(
    entry: Mapping[str, Any],
    design: Mapping[str, Any],
    *,
    registry_digest: str | None,
) -> bool:
    handoff_path = Path(str(entry.get("preopen_handoff") or ""))
    handoff = _load_json(handoff_path)
    return bool(
        handoff
        and handoff.get("schema") == HANDOFF_SCHEMA
        and handoff.get("target_date") == entry.get("preopen_target_date")
        and handoff.get("queue_key") == entry.get("queue_key")
        and handoff.get("candidate_sha256") == entry.get("candidate_sha256")
        and handoff.get("runtime_family") == design.get("runtime_family")
        and handoff.get("stage") == design.get("stage")
        and handoff.get("axis") == design.get("axis")
        and handoff.get("bounded_contract_sha256")
        == design.get("bounded_contract_sha256")
        and handoff.get("runtime_registry_entry_sha256") == registry_digest
        and handoff.get("status") == "preopen_authorization_handoff_ready"
        and handoff.get("runtime_effect") is False
        and handoff.get("runtime_apply_performed") is False
        and handoff.get("allowed_runtime_apply") is True
        and handoff.get("actual_order_submitted") is False
        and handoff.get("broker_order_forbidden") is True
    )


def _apply_family_receipts(
    entries: list[dict[str, Any]],
    receipt_dir: Path,
    *,
    runtime_registry: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    enrollments: dict[str, dict[str, Any]] = {}
    by_key = {str(entry.get("queue_key") or ""): entry for entry in entries}
    receipts: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(receipt_dir.glob("*.json")):
        receipt = _load_json(path)
        if receipt is None or receipt.get("schema") != APPLY_RECEIPT_SCHEMA:
            continue
        receipts.append((path, receipt))
    receipts.sort(
        key=lambda item: (
            0 if item[1].get("status") == "applied_guard_passed" else 1,
            str(item[0]),
        )
    )
    for path, receipt in receipts:
        entry = by_key.get(str(receipt.get("queue_key") or ""))
        if entry is None:
            continue
        candidate = entry.get("candidate") or {}
        design = candidate.get("runtime_design") or {}
        registry_digest = _registry_entry_sha256(
            _trusted_registry_entry(
                str(design.get("runtime_family") or ""), runtime_registry
            )
        )
        if (
            str(receipt.get("candidate_sha256") or "")
            != str(entry.get("candidate_sha256") or "")
            or str(receipt.get("runtime_family") or "")
            != str(design.get("runtime_family") or "")
            or str(receipt.get("stage") or "") != str(design.get("stage") or "")
            or str(receipt.get("runtime_registry_entry_sha256") or "")
            != str(registry_digest or "")
            or receipt.get("same_stage_owner_conflict_free") is not True
            or receipt.get("hard_safety_and_broker_guards_preserved") is not True
        ):
            continue
        status = str(receipt.get("status") or "")
        if status not in {"applied_guard_passed", "post_apply_attribution_complete"}:
            continue
        expected_state = (
            STATE_PREOPEN_SCHEDULED
            if status == "applied_guard_passed"
            else STATE_APPLIED
        )
        if entry.get("state") != expected_state:
            continue
        if status == "applied_guard_passed" and runtime_design_errors(
            candidate, runtime_registry=runtime_registry
        ):
            continue
        if status == "applied_guard_passed" and not _handoff_matches_entry(
            entry,
            design,
            registry_digest=registry_digest,
        ):
            continue
        if (
            str(receipt.get("axis") or "") != str(design.get("axis") or "")
            or str(receipt.get("bounded_contract_sha256") or "")
            != str(design.get("bounded_contract_sha256") or "")
            or str(receipt.get("preopen_handoff") or "")
            != str(entry.get("preopen_handoff") or "")
            or str(receipt.get("target_date") or "")
            != str(entry.get("preopen_target_date") or "")
        ):
            continue
        if status == "applied_guard_passed":
            if (
                receipt.get("runtime_effect") is not True
                or receipt.get("runtime_apply_performed") is not True
                or receipt.get("actual_order_submitted") is not False
            ):
                continue
            entry["family_apply_receipt"] = str(path)
            entry["state"] = STATE_APPLIED
        else:
            if (
                receipt.get("runtime_effect") is not False
                or receipt.get("runtime_apply_performed") is not False
                or receipt.get("actual_order_submitted") is not False
                or receipt.get("post_apply_attribution_complete") is not True
                or str(receipt.get("source_apply_receipt") or "")
                != str(entry.get("family_apply_receipt") or "")
            ):
                continue
            entry["post_apply_attribution_receipt"] = str(path)
            entry["state"] = STATE_POST_APPLY_ATTRIBUTED
        entry["state_reason"] = status
        family = str(design.get("runtime_family") or "")
        if family and status == "applied_guard_passed":
            enrollments[family] = {
                "runtime_family": family,
                "stage": design.get("stage"),
                "axis": design.get("axis"),
                "bounded_contract_sha256": design.get("bounded_contract_sha256"),
                "runtime_registry_entry_sha256": registry_digest,
                "first_approved_queue_key": entry.get("queue_key"),
                "first_apply_receipt": str(path),
                "enrolled_after_guarded_apply": True,
            }
    return enrollments


def _validated_existing_enrollments(
    raw_enrollments: Mapping[str, Any],
    entries: Sequence[Mapping[str, Any]],
    *,
    receipt_dir: Path,
    runtime_registry: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    by_key = {str(entry.get("queue_key") or ""): entry for entry in entries}
    validated: dict[str, dict[str, Any]] = {}
    receipt_root = receipt_dir.resolve()
    for family, raw in raw_enrollments.items():
        if (
            not isinstance(raw, Mapping)
            or raw.get("enrolled_after_guarded_apply") is not True
        ):
            continue
        entry = by_key.get(str(raw.get("first_approved_queue_key") or ""))
        if entry is None or entry.get("state") not in {
            STATE_APPLIED,
            STATE_POST_APPLY_ATTRIBUTED,
        }:
            continue
        candidate = entry.get("candidate") or {}
        design = candidate.get("runtime_design") or {}
        registry_digest = _registry_entry_sha256(
            _trusted_registry_entry(str(family), runtime_registry)
        )
        if (
            str(design.get("runtime_family") or "") != str(family)
            or runtime_design_errors(candidate, runtime_registry=runtime_registry)
            or raw.get("stage") != design.get("stage")
            or raw.get("axis") != design.get("axis")
            or raw.get("bounded_contract_sha256")
            != design.get("bounded_contract_sha256")
            or raw.get("runtime_registry_entry_sha256") != registry_digest
        ):
            continue
        receipt_path = Path(str(raw.get("first_apply_receipt") or ""))
        try:
            receipt_path.resolve().relative_to(receipt_root)
        except (OSError, ValueError):
            continue
        receipt = _load_json(receipt_path)
        if (
            not receipt
            or receipt.get("schema") != APPLY_RECEIPT_SCHEMA
            or receipt.get("status") != "applied_guard_passed"
            or receipt.get("queue_key") != entry.get("queue_key")
            or receipt.get("candidate_sha256") != entry.get("candidate_sha256")
            or receipt.get("runtime_family") != family
            or receipt.get("stage") != design.get("stage")
            or receipt.get("axis") != design.get("axis")
            or receipt.get("bounded_contract_sha256")
            != design.get("bounded_contract_sha256")
            or receipt.get("runtime_registry_entry_sha256") != registry_digest
            or receipt.get("preopen_handoff") != entry.get("preopen_handoff")
            or receipt.get("target_date") != entry.get("preopen_target_date")
            or receipt.get("runtime_effect") is not True
            or receipt.get("runtime_apply_performed") is not True
            or receipt.get("actual_order_submitted") is not False
            or receipt.get("same_stage_owner_conflict_free") is not True
            or receipt.get("hard_safety_and_broker_guards_preserved") is not True
        ):
            continue
        validated[str(family)] = dict(raw)
    return validated


def sync_queue(
    queue: Mapping[str, Any],
    *,
    source_candidates: Sequence[Mapping[str, Any]],
    source_path: Path | None,
    as_of_date: date,
    source_status: str = "not_provided",
    now: datetime | None = None,
    approval_artifacts: Sequence[Mapping[str, Any]] = (),
    apply_receipt_dir: Path = APPLY_RECEIPT_DIR,
    runtime_registry: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    generated = _now_kst(now)
    entries = [
        dict(row) for row in queue.get("candidates", []) if isinstance(row, dict)
    ]
    by_key = {str(entry.get("queue_key") or ""): entry for entry in entries}
    intake_rejections: list[dict[str, Any]] = []
    for raw_candidate in source_candidates:
        candidate = dict(raw_candidate)
        errors = evidence_readiness_errors(candidate)
        if str(candidate.get("source_date") or "") != as_of_date.isoformat():
            errors.append("candidate_source_date_not_as_of_date")
        if errors:
            intake_rejections.append(
                {
                    "candidate_id": candidate.get("candidate_id"),
                    "errors": errors,
                }
            )
            continue
        digest = candidate_sha256(candidate)
        declared_digest = str(candidate.get("candidate_sha256") or "")
        if declared_digest and declared_digest != digest:
            intake_rejections.append(
                {
                    "candidate_id": candidate.get("candidate_id"),
                    "errors": ["candidate_sha256_mismatch"],
                }
            )
            continue
        candidate_id = str(candidate["candidate_id"])
        key = _queue_key(candidate_id, digest)
        for previous in entries:
            if (
                previous.get("candidate_id") == candidate_id
                and previous.get("queue_key") != key
                and previous.get("state") in EXPIRABLE_STATES
            ):
                previous["state"] = STATE_EXPIRED
                previous["state_reason"] = "superseded_by_changed_candidate_hash"
                previous["superseded_by_queue_key"] = key
        design_errors = runtime_design_errors(
            candidate, runtime_registry=runtime_registry
        )
        registry_digest = _registry_entry_sha256(
            _trusted_registry_entry(
                _candidate_runtime_family(candidate), runtime_registry
            )
        )
        if key in by_key:
            entry = by_key[key]
            entry["last_seen_at_kst"] = generated.isoformat(timespec="seconds")
            entry["source_path"] = str(source_path) if source_path else None
            entry["candidate"] = candidate
            entry["runtime_design_errors"] = design_errors
            entry["runtime_registry_entry_sha256"] = registry_digest
            if entry.get("state") == STATE_DESIGN_REQUIRED and not design_errors:
                entry["state"] = STATE_REVIEW_READY
                entry["state_reason"] = "runtime_design_registered_review_ready"
            elif design_errors and entry.get("state") in {
                STATE_REVIEW_READY,
                STATE_USER_APPROVED,
                STATE_PREOPEN_SCHEDULED,
                STATE_AUTO_CHAIN_ELIGIBLE,
            }:
                entry["state"] = STATE_DESIGN_REQUIRED
                entry["state_reason"] = "trusted_runtime_design_revalidation_failed"
            continue
        entry = {
            "queue_key": key,
            "candidate_id": candidate_id,
            "candidate_sha256": digest,
            "source_date": candidate.get("source_date"),
            "source_path": str(source_path) if source_path else None,
            "evidence_valid_through": candidate.get("evidence_valid_through"),
            "first_seen_at_kst": generated.isoformat(timespec="seconds"),
            "last_seen_at_kst": generated.isoformat(timespec="seconds"),
            "state": STATE_DESIGN_REQUIRED if design_errors else STATE_REVIEW_READY,
            "state_reason": (
                "runtime_design_required_before_operator_review"
                if design_errors
                else "evidence_and_runtime_design_ready_for_operator_review"
            ),
            "runtime_design_errors": design_errors,
            "runtime_registry_entry_sha256": registry_digest,
            "candidate": candidate,
            "reminders": {},
        }
        entries.append(entry)
        by_key[key] = entry

    for entry in entries:
        if entry.get("state") in EXPIRABLE_STATES and _entry_expired(
            entry, as_of_date=as_of_date
        ):
            entry["state"] = STATE_EXPIRED
            entry["state_reason"] = "evidence_validity_expired_revalidation_required"

    _apply_operator_decisions(
        entries,
        approval_artifacts,
        runtime_registry=runtime_registry,
    )
    family_enrollments = _validated_existing_enrollments(
        queue.get("family_enrollments") or {},
        entries,
        receipt_dir=apply_receipt_dir,
        runtime_registry=runtime_registry,
    )
    new_enrollments = _apply_family_receipts(
        entries,
        apply_receipt_dir,
        runtime_registry=runtime_registry,
    )
    family_enrollments.update(new_enrollments)
    for entry in entries:
        candidate = entry.get("candidate") or {}
        family = _candidate_runtime_family(candidate)
        if (
            entry.get("state") == STATE_REVIEW_READY
            and candidate.get("first_operator_approval_required") is False
            and family in family_enrollments
            and not runtime_design_errors(candidate, runtime_registry=runtime_registry)
        ):
            enrolled = family_enrollments[family]
            design = candidate.get("runtime_design") or {}
            if (
                enrolled.get("stage") == design.get("stage")
                and enrolled.get("axis") == design.get("axis")
                and enrolled.get("bounded_contract_sha256")
                == design.get("bounded_contract_sha256")
            ):
                entry["state"] = STATE_AUTO_CHAIN_ELIGIBLE
                entry["state_reason"] = "same_family_bounded_contract_enrolled"

    output = {
        **dict(queue),
        "schema": QUEUE_SCHEMA,
        "updated_at_kst": generated.isoformat(timespec="seconds"),
        "metric_contract": METRIC_CONTRACT,
        "authority": {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
        "last_sync": {
            "as_of_date": as_of_date.isoformat(),
            "source_path": str(source_path) if source_path else None,
            "source_status": source_status,
            "source_candidate_count": len(source_candidates),
            "intake_rejection_count": len(intake_rejections),
        },
        "candidates": sorted(entries, key=lambda row: str(row.get("queue_key") or "")),
        "family_enrollments": family_enrollments,
    }
    return output, intake_rejections


def _safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "candidate"


def approval_artifact_path(
    entry: Mapping[str, Any], approval_dir: Path = APPROVAL_DIR
) -> Path:
    return approval_dir / (
        f"{_safe_id(str(entry.get('candidate_id') or 'candidate'))}_"
        f"{str(entry.get('candidate_sha256') or '')[:16]}.json"
    )


def record_operator_decision(
    queue: Mapping[str, Any],
    *,
    candidate_id: str,
    expected_candidate_sha256: str,
    decision: str,
    operator_authorization_id: str,
    operator_instruction: str,
    approval_dir: Path = APPROVAL_DIR,
    now: datetime | None = None,
    runtime_registry: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[dict[str, Any], Path]:
    if decision not in VALID_DECISIONS:
        raise ValueError("operator_decision_invalid")
    if not operator_authorization_id.strip() or not operator_instruction.strip():
        raise ValueError("explicit_operator_authority_missing")
    matches = [
        row
        for row in queue.get("candidates", [])
        if isinstance(row, Mapping)
        and row.get("candidate_id") == candidate_id
        and row.get("candidate_sha256") == expected_candidate_sha256
    ]
    if len(matches) != 1:
        raise ValueError("candidate_id_and_hash_not_uniquely_found")
    entry = matches[0]
    state = str(entry.get("state") or "")
    if _entry_expired(entry, as_of_date=_now_kst(now).date()):
        raise ValueError("candidate_evidence_expired")
    if decision == "approve":
        if state not in {STATE_REVIEW_READY, STATE_HOLD}:
            raise ValueError(f"candidate_not_approval_ready:{state}")
        design_errors = runtime_design_errors(
            entry.get("candidate") or {}, runtime_registry=runtime_registry
        )
        if design_errors:
            raise ValueError("runtime_design_not_ready:" + ",".join(design_errors))
    elif decision == "hold" and state not in {
        STATE_DESIGN_REQUIRED,
        STATE_REVIEW_READY,
        STATE_USER_APPROVED,
    }:
        raise ValueError(f"candidate_not_holdable:{state}")
    elif decision == "reject" and state not in {
        STATE_DESIGN_REQUIRED,
        STATE_REVIEW_READY,
        STATE_USER_APPROVED,
        STATE_HOLD,
    }:
        raise ValueError(f"candidate_not_rejectable:{state}")
    decided_at = _now_kst(now).isoformat(timespec="seconds")
    runtime_family = _candidate_runtime_family(entry.get("candidate") or {})
    registry_digest = _registry_entry_sha256(
        _trusted_registry_entry(runtime_family, runtime_registry)
    )
    artifact = {
        "schema": APPROVAL_SCHEMA,
        "queue_key": entry.get("queue_key"),
        "candidate_id": candidate_id,
        "candidate_sha256": expected_candidate_sha256,
        "source_date": entry.get("source_date"),
        "decision": decision,
        "decided_at_kst": decided_at,
        "operator_authorization_id": operator_authorization_id.strip(),
        "operator_instruction": operator_instruction.strip(),
        "runtime_family": runtime_family,
        "runtime_registry_entry_sha256": registry_digest,
        "runtime_effect": False,
        "allowed_runtime_apply": decision == "approve",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": METRIC_CONTRACT["forbidden_uses"],
    }
    path = approval_artifact_path(entry, approval_dir)
    _atomic_write_json(path, artifact)
    updated, _ = sync_queue(
        queue,
        source_candidates=(),
        source_path=None,
        as_of_date=_now_kst(now).date(),
        now=now,
        approval_artifacts=[{**artifact, "_artifact_path": str(path)}],
        apply_receipt_dir=Path("/__machine_micro_no_receipts__"),
        runtime_registry=runtime_registry,
    )
    return updated, path


def schedule_preopen_handoffs(
    queue: Mapping[str, Any],
    *,
    target_date: date,
    handoff_dir: Path = HANDOFF_DIR,
    now: datetime | None = None,
    runtime_registry: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[dict[str, Any], list[Path]]:
    generated = _now_kst(now)
    entries = [
        dict(row) for row in queue.get("candidates", []) if isinstance(row, dict)
    ]
    written: list[Path] = []
    for entry in entries:
        if entry.get("state") not in {
            STATE_USER_APPROVED,
            STATE_AUTO_CHAIN_ELIGIBLE,
        }:
            continue
        candidate = entry.get("candidate") or {}
        design_errors = runtime_design_errors(
            candidate, runtime_registry=runtime_registry
        )
        if design_errors:
            entry["state"] = STATE_DESIGN_REQUIRED
            entry["state_reason"] = "preopen_blocked_runtime_design_not_ready"
            entry["runtime_design_errors"] = design_errors
            continue
        design = candidate["runtime_design"]
        family = str(design.get("runtime_family") or "")
        registry_digest = _registry_entry_sha256(
            _trusted_registry_entry(family, runtime_registry)
        )
        enrollment = (queue.get("family_enrollments") or {}).get(family)
        authorization_mode = (
            "enrolled_same_bounded_family_auto_chain"
            if entry.get("state") == STATE_AUTO_CHAIN_ELIGIBLE
            else "first_explicit_operator_approval"
        )
        if authorization_mode == "enrolled_same_bounded_family_auto_chain":
            if (
                not isinstance(enrollment, Mapping)
                or enrollment.get("enrolled_after_guarded_apply") is not True
                or enrollment.get("stage") != design.get("stage")
                or enrollment.get("axis") != design.get("axis")
                or enrollment.get("bounded_contract_sha256")
                != design.get("bounded_contract_sha256")
            ):
                entry["state"] = STATE_DESIGN_REQUIRED
                entry["state_reason"] = "preopen_blocked_family_enrollment_mismatch"
                continue
        elif str(entry.get("operator_registry_entry_sha256") or "") != str(
            registry_digest or ""
        ):
            entry["state"] = STATE_DESIGN_REQUIRED
            entry["state_reason"] = "preopen_blocked_operator_registry_hash_mismatch"
            continue
        payload = {
            "schema": HANDOFF_SCHEMA,
            "target_date": target_date.isoformat(),
            "created_at_kst": generated.isoformat(timespec="seconds"),
            "queue_key": entry.get("queue_key"),
            "candidate_id": entry.get("candidate_id"),
            "candidate_sha256": entry.get("candidate_sha256"),
            "operator_decision_artifact": entry.get("operator_decision_artifact"),
            "operator_authorization_id": entry.get("operator_authorization_id"),
            "authorization_mode": authorization_mode,
            "family_enrollment": enrollment,
            "runtime_family": design.get("runtime_family"),
            "stage": design.get("stage"),
            "axis": design.get("axis"),
            "bounded_values": design.get("bounded_values"),
            "bounded_contract_sha256": design.get("bounded_contract_sha256"),
            "runtime_registry_entry_sha256": registry_digest,
            "preopen_consumer": design.get("preopen_consumer"),
            "rollback": design.get("rollback"),
            "post_apply_attribution": design.get("post_apply_attribution"),
            "same_stage_owner_conflict_free": True,
            "status": "preopen_authorization_handoff_ready",
            "runtime_effect": False,
            "runtime_apply_performed": False,
            "allowed_runtime_apply": True,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "forbidden_uses": METRIC_CONTRACT["forbidden_uses"],
        }
        path = (
            handoff_dir
            / target_date.isoformat()
            / (
                f"{_safe_id(str(entry.get('candidate_id') or 'candidate'))}_"
                f"{str(entry.get('candidate_sha256') or '')[:16]}.json"
            )
        )
        _atomic_write_json(path, payload)
        written.append(path)
        entry["state"] = STATE_PREOPEN_SCHEDULED
        entry["state_reason"] = "exact_date_preopen_authorization_handoff_written"
        entry["preopen_handoff"] = str(path)
        entry["preopen_target_date"] = target_date.isoformat()
        entry["authorization_mode"] = authorization_mode
    output = {**dict(queue), "candidates": entries}
    output["updated_at_kst"] = generated.isoformat(timespec="seconds")
    return output, written


def _load_telegram_config() -> tuple[str, str]:
    config_path = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    payload = _load_json(config_path) or {}
    return (
        str(payload.get("TELEGRAM_TOKEN") or "").strip(),
        str(payload.get("ADMIN_ID") or "").strip(),
    )


def _send_telegram(token: str, admin_id: str, message: str) -> None:
    data = parse.urlencode({"chat_id": admin_id, "text": message}).encode("utf-8")
    req = request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data,
        method="POST",
    )
    with request.urlopen(req, timeout=10) as response:
        response.read()


def build_reminder_message(
    entries: Sequence[Mapping[str, Any]], *, phase: str, target_date: date
) -> str:
    lines = [
        "🔔 [Micro 정책 후속 확인]",
        f"기준: {target_date.isoformat()} {phase.upper()}",
        "정책은 자동 변경되지 않으며 승인·PREOPEN handoff만 추적합니다.",
    ]
    for index, entry in enumerate(entries[:5], start=1):
        candidate = entry.get("candidate") or {}
        design = candidate.get("runtime_design") or {}
        lines.append(f"{index}. {entry.get('candidate_id')} [{entry.get('state')}]")
        lines.append(
            "   family="
            f"{design.get('runtime_family') or '-'} "
            f"stage={design.get('stage') or '-'} axis={design.get('axis') or '-'}"
        )
        lines.append(
            f"   hash={str(entry.get('candidate_sha256') or '')[:16]} "
            f"valid_through={entry.get('evidence_valid_through')}"
        )
        if entry.get("runtime_design_errors"):
            lines.append(
                "   design_gap=" + ",".join(entry.get("runtime_design_errors") or [])
            )
    if len(entries) > 5:
        lines.append(f"외 {len(entries) - 5}건")
    lines.append("상태별로 설계·승인·exact-date 적용·사후 귀속을 닫아주세요.")
    return "\n".join(lines)


def notify_pending(
    queue: Mapping[str, Any],
    *,
    phase: str,
    target_date: date,
    config_loader: ConfigLoader = _load_telegram_config,
    sender: Sender = _send_telegram,
) -> tuple[dict[str, Any], str]:
    if phase not in VALID_PHASES:
        raise ValueError("phase_invalid")
    entries = [
        dict(row) for row in queue.get("candidates", []) if isinstance(row, dict)
    ]
    pending = [
        row
        for row in entries
        if row.get("state") in REMINDER_STATES
        and (row.get("reminders") or {}).get(phase) != target_date.isoformat()
    ]
    if not pending:
        return {**dict(queue), "candidates": entries}, "not_needed_or_duplicate"
    token, admin_id = config_loader()
    if not token or not admin_id:
        return {**dict(queue), "candidates": entries}, "missing_config"
    try:
        sender(
            token,
            admin_id,
            build_reminder_message(pending, phase=phase, target_date=target_date),
        )
    except Exception:
        return {**dict(queue), "candidates": entries}, "send_failed"
    pending_keys = {str(row.get("queue_key") or "") for row in pending}
    for entry in entries:
        if str(entry.get("queue_key") or "") in pending_keys:
            reminders = dict(entry.get("reminders") or {})
            reminders[phase] = target_date.isoformat()
            entry["reminders"] = reminders
    return {**dict(queue), "candidates": entries}, "sent"


def build_status_report(
    queue: Mapping[str, Any],
    *,
    phase: str,
    target_date: date,
    source_path: Path | None,
    intake_rejections: Sequence[Mapping[str, Any]],
    reminder_status: str,
    queue_path: Path = DEFAULT_QUEUE_PATH,
    source_status: str = "not_provided",
    handoff_paths: Sequence[Path] = (),
    now: datetime | None = None,
) -> dict[str, Any]:
    entries = [row for row in queue.get("candidates", []) if isinstance(row, Mapping)]
    counts = Counter(str(row.get("state") or "UNKNOWN") for row in entries)
    actionable = [row for row in entries if row.get("state") in REMINDER_STATES]
    decision = (
        "operator_attention_required"
        if actionable
        else "source_gap_queue_preserved"
        if source_status not in {"loaded", "not_applicable_preopen", "not_provided"}
        else "no_operator_attention_required"
    )
    return {
        "schema": REPORT_SCHEMA,
        "report_type": "machine_microstructure_policy_approval",
        "phase": phase,
        "target_date": target_date.isoformat(),
        "generated_at_kst": _now_kst(now).isoformat(timespec="seconds"),
        "decision": decision,
        "metric_contract": METRIC_CONTRACT,
        "source_path": str(source_path) if source_path else None,
        "source_status": source_status,
        "queue_path": str(queue_path),
        "summary": {
            "candidate_count": len(entries),
            "actionable_candidate_count": len(actionable),
            "state_counts": dict(sorted(counts.items())),
            "intake_rejection_count": len(intake_rejections),
            "preopen_handoff_count": len(handoff_paths),
            "reminder_status": reminder_status,
        },
        "actionable_candidates": [
            {
                "queue_key": row.get("queue_key"),
                "candidate_id": row.get("candidate_id"),
                "candidate_sha256": row.get("candidate_sha256"),
                "state": row.get("state"),
                "state_reason": row.get("state_reason"),
                "runtime_family": _candidate_runtime_family(row.get("candidate") or {}),
                "runtime_design_errors": row.get("runtime_design_errors") or [],
                "evidence_valid_through": row.get("evidence_valid_through"),
                "operator_decision_artifact": row.get("operator_decision_artifact"),
                "preopen_handoff": row.get("preopen_handoff"),
            }
            for row in actionable
        ],
        "intake_rejections": list(intake_rejections),
        "preopen_handoffs": [str(path) for path in handoff_paths],
        "authority": {
            "runtime_effect": False,
            "runtime_apply_performed": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
    }


def render_status_markdown(report: Mapping[str, Any]) -> str:
    summary = report.get("summary") or {}
    lines = [
        "# Machine Microstructure Policy Approval",
        "",
        f"- Target date: `{report.get('target_date')}`",
        f"- Phase: `{report.get('phase')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Source status: `{report.get('source_status')}`",
        f"- Actionable: `{summary.get('actionable_candidate_count', 0)}`",
        f"- Reminder: `{summary.get('reminder_status')}`",
        "- Runtime apply performed: `false`",
        "",
        "## Pending",
        "",
    ]
    rows = report.get("actionable_candidates") or []
    if not rows:
        lines.append("- None")
    else:
        lines.extend(
            [
                "| Candidate | State | Family | Hash | Valid through |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for row in rows:
            lines.append(
                f"| {row.get('candidate_id')} | {row.get('state')} | "
                f"{row.get('runtime_family') or '-'} | "
                f"{str(row.get('candidate_sha256') or '')[:16]} | "
                f"{row.get('evidence_valid_through')} |"
            )
    lines.extend(
        [
            "",
            "The queue and reminders do not mutate runtime policy. A registered family, "
            "explicit operator decision, exact-date PREOPEN handoff, family apply receipt, "
            "and post-apply attribution remain separate gates.",
            "",
        ]
    )
    return "\n".join(lines)


def status_report_paths(
    *, target_date: date, phase: str, report_dir: Path = REPORT_DIR
) -> tuple[Path, Path]:
    stem = f"machine_microstructure_policy_approval_{phase}_{target_date.isoformat()}"
    return report_dir / f"{stem}.json", report_dir / f"{stem}.md"


def _load_source_candidates(
    *, target_date: date, source_report: Path | None
) -> tuple[Path, list[Mapping[str, Any]], str]:
    path = source_report or SOURCE_REPORT_DIR / (
        f"machine_microstructure_attribution_{target_date.isoformat()}.json"
    )
    payload = _load_json(path)
    if payload is None:
        return path, [], "missing_or_unreadable"
    if (
        payload.get("schema") != "machine_microstructure_attribution_v1"
        or payload.get("target_date") != target_date.isoformat()
        or (payload.get("authority") or {}).get("runtime_effect") is not False
        or (payload.get("authority") or {}).get("allowed_runtime_apply") is not False
        or (payload.get("authority") or {}).get("actual_order_submitted") is not False
        or (payload.get("authority") or {}).get("broker_order_forbidden") is not True
    ):
        return path, [], "contract_invalid"
    intake_contract = payload.get("promotion_candidate_intake_contract")
    if (
        not isinstance(intake_contract, Mapping)
        or intake_contract.get("schema") != CANDIDATE_SCHEMA
        or intake_contract.get("consumer")
        != "src.engine.automation.machine_microstructure_policy_approval"
        or intake_contract.get("daily_report_runtime_effect") is not False
    ):
        return path, [], "intake_contract_invalid"
    rows = payload.get("policy_promotion_candidates")
    if not isinstance(rows, list):
        return path, [], "candidate_list_missing_or_invalid"
    if any(not isinstance(row, Mapping) for row in rows):
        return path, [], "candidate_rows_invalid"
    return path, list(rows), "loaded"


@contextmanager
def _queue_lock(queue_path: Path) -> Iterator[None]:
    lock_path = queue_path.with_suffix(queue_path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _run_phase(args: argparse.Namespace) -> dict[str, Any]:
    target_date = date.fromisoformat(args.target_date)
    source_path: Path | None = None
    source_candidates: list[Mapping[str, Any]] = []
    source_status = "not_applicable_preopen"
    if args.phase == "postclose":
        source_path, source_candidates, source_status = _load_source_candidates(
            target_date=target_date,
            source_report=args.source_report,
        )
    with _queue_lock(args.queue_path):
        queue = load_queue(args.queue_path)
        queue, rejections = sync_queue(
            queue,
            source_candidates=source_candidates,
            source_path=source_path,
            as_of_date=target_date,
            source_status=source_status,
            approval_artifacts=_approval_artifacts(args.approval_dir),
            apply_receipt_dir=args.apply_receipt_dir,
        )
        handoff_paths: list[Path] = []
        if args.phase == "preopen":
            queue, handoff_paths = schedule_preopen_handoffs(
                queue,
                target_date=target_date,
                handoff_dir=args.handoff_dir,
            )
        reminder_status = "not_requested"
        if args.notify:
            queue, reminder_status = notify_pending(
                queue,
                phase=args.phase,
                target_date=target_date,
            )
        report = build_status_report(
            queue,
            phase=args.phase,
            target_date=target_date,
            source_path=source_path,
            queue_path=args.queue_path,
            source_status=source_status,
            intake_rejections=rejections,
            reminder_status=reminder_status,
            handoff_paths=handoff_paths,
        )
        if args.write:
            _atomic_write_json(args.queue_path, queue)
            json_path, md_path = status_report_paths(
                target_date=target_date,
                phase=args.phase,
                report_dir=args.report_dir,
            )
            _atomic_write_json(json_path, report)
            _atomic_write_text(md_path, render_status_markdown(report))
        return report


def _record_decision(args: argparse.Namespace) -> dict[str, Any]:
    with _queue_lock(args.queue_path):
        queue = load_queue(args.queue_path)
        queue, artifact_path = record_operator_decision(
            queue,
            candidate_id=args.candidate_id,
            expected_candidate_sha256=args.candidate_sha256,
            decision=args.record_decision,
            operator_authorization_id=args.operator_authorization_id,
            operator_instruction=args.operator_instruction,
            approval_dir=args.approval_dir,
        )
        _atomic_write_json(args.queue_path, queue)
    return {
        "status": "operator_decision_recorded",
        "decision": args.record_decision,
        "candidate_id": args.candidate_id,
        "candidate_sha256": args.candidate_sha256,
        "artifact_path": str(artifact_path),
        "runtime_effect": False,
        "runtime_apply_performed": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=sorted(VALID_PHASES))
    parser.add_argument("--target-date", default=_now_kst().date().isoformat())
    parser.add_argument("--source-report", type=Path)
    parser.add_argument("--queue-path", type=Path, default=DEFAULT_QUEUE_PATH)
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--approval-dir", type=Path, default=APPROVAL_DIR)
    parser.add_argument("--handoff-dir", type=Path, default=HANDOFF_DIR)
    parser.add_argument("--apply-receipt-dir", type=Path, default=APPLY_RECEIPT_DIR)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--notify", action="store_true")
    parser.add_argument("--record-decision", choices=sorted(VALID_DECISIONS))
    parser.add_argument("--candidate-id", default="")
    parser.add_argument("--candidate-sha256", default="")
    parser.add_argument("--operator-authorization-id", default="")
    parser.add_argument("--operator-instruction", default="")
    args = parser.parse_args(argv)
    try:
        date.fromisoformat(args.target_date)
        if args.record_decision:
            if not args.candidate_id or not args.candidate_sha256:
                parser.error("--candidate-id and --candidate-sha256 are required")
            result = _record_decision(args)
        else:
            if not args.phase:
                parser.error("--phase is required unless --record-decision is used")
            result = _run_phase(args)
    except ValueError as exc:
        print(
            json.dumps(
                {
                    "status": "blocked_contract_error",
                    "reason": str(exc),
                    "runtime_effect": False,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
