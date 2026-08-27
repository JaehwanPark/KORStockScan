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
import hashlib
import json
import os
import re
import tempfile
from collections import Counter
from contextlib import contextmanager
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping, Sequence
from urllib import parse, request
from zoneinfo import ZoneInfo

from src.engine.monitoring.machine_microstructure_attribution import (
    FAST_LIFECYCLE_OBJECTIVE_FOLLOWUP_ID,
    OBJECTIVE_CANDIDATE_BINDING_SCHEMA,
    OBJECTIVE_FOLLOWUP_SCHEMA,
    OBJECTIVE_HANDOFF_BINDING_SCHEMA,
    OBJECTIVE_HANDOFF_RESOLVABLE_GAP_CODES,
    resolve_completed_machine_target_date,
)
from src.engine.monitoring.machine_lifecycle_turnover_policy_research import (
    ROLLING_PAIRED_LIFECYCLE_FLOORS,
)
from src.engine.scalping.micro_reversion.contracts import CLEAN_BASELINE_DATE
from src.utils.constants import CONFIG_PATH, DATA_DIR, DEV_PATH
from src.utils.jsonl_io import (
    ArtifactGenerationLease,
    json_artifact_generation_lock,
    read_json_object_strict_receipt,
    write_json_object_generation_safe,
)
from src.utils.market_day import is_krx_trading_day

KST = ZoneInfo("Asia/Seoul")
QUEUE_SCHEMA = "machine_microstructure_policy_approval_queue_v1"
REPORT_SCHEMA = "machine_microstructure_policy_approval_status_v1"
CANDIDATE_SCHEMA = "machine_microstructure_policy_promotion_candidate_v1"
APPROVAL_SCHEMA = "machine_microstructure_policy_operator_decision_v1"
HANDOFF_SCHEMA = "machine_microstructure_policy_preopen_handoff_v1"
APPLY_RECEIPT_SCHEMA = "machine_microstructure_policy_family_apply_receipt_v1"
SOURCE_ARTIFACT_PROVENANCE_SCHEMA = (
    "machine_microstructure_policy_source_artifact_provenance_v1"
)

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
STATE_PREOPEN_MISSED_REVIEW_REQUIRED = "PREOPEN_MISSED_REVIEW_REQUIRED"
STATE_REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"
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
    STATE_PREOPEN_MISSED_REVIEW_REQUIRED,
    STATE_REVALIDATION_REQUIRED,
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
    STATE_PREOPEN_MISSED_REVIEW_REQUIRED,
    STATE_REVALIDATION_REQUIRED,
    STATE_AUTO_CHAIN_ELIGIBLE,
    STATE_HOLD,
}
VALID_DECISIONS = {"approve", "hold", "reject"}
VALID_PHASES = {"postclose", "preopen"}
VALID_STAGES = {"entry", "submit", "holding", "scale_in", "exit"}
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
OBJECTIVE_FOLLOWUP_STATES = {
    "IMPLEMENTATION_REQUIRED",
    "EVIDENCE_ACCUMULATING",
    "CANDIDATE_QUEUE_HANDOFF",
    "COMPLETE",
}
OBJECTIVE_FOLLOWUP_CLOSED_STATES = {"CANDIDATE_QUEUE_HANDOFF", "COMPLETE"}
OBJECTIVE_FOLLOWUP_ALLOWED_TRANSITIONS = {
    "IMPLEMENTATION_REQUIRED": {
        "IMPLEMENTATION_REQUIRED",
        "EVIDENCE_ACCUMULATING",
        "CANDIDATE_QUEUE_HANDOFF",
        "COMPLETE",
    },
    "EVIDENCE_ACCUMULATING": {
        "EVIDENCE_ACCUMULATING",
        "CANDIDATE_QUEUE_HANDOFF",
        "COMPLETE",
    },
    "CANDIDATE_QUEUE_HANDOFF": {"CANDIDATE_QUEUE_HANDOFF", "COMPLETE"},
    "COMPLETE": {"COMPLETE"},
}
OBJECTIVE_METRIC_CONTRACT_FIELDS = {
    "metric_role",
    "decision_authority",
    "window_policy",
    "sample_floor",
    "primary_decision_metric",
    "source_quality_gate",
    "forbidden_uses",
}
OBJECTIVE_FOLLOWUP_FORBIDDEN_FIELDS = {
    "candidate_id",
    "candidate_sha256",
    "runtime_design",
    "runtime_family",
    "preopen_consumer",
    "bounded_values",
    "operator_authorization_id",
    "operator_decision_artifact",
    "preopen_handoff",
}
# This ledger has no trusted per-candidate venue scope.  Use the earliest
# supported market open (NXT 08:00 KST) as the common fail-closed cutoff.
PREOPEN_HANDOFF_CUTOFF_KST = time(hour=8)
OBJECTIVE_FOLLOWUP_REMINDER_CUTOFF_KST = time(hour=21, minute=15)

DECISION_ALLOWED_STATES = {
    "approve": {
        STATE_REVIEW_READY,
        STATE_HOLD,
        STATE_PREOPEN_MISSED_REVIEW_REQUIRED,
    },
    "hold": {
        STATE_DESIGN_REQUIRED,
        STATE_REVIEW_READY,
        STATE_USER_APPROVED,
        STATE_PREOPEN_MISSED_REVIEW_REQUIRED,
    },
    "reject": {
        STATE_DESIGN_REQUIRED,
        STATE_REVIEW_READY,
        STATE_USER_APPROVED,
        STATE_HOLD,
        STATE_PREOPEN_MISSED_REVIEW_REQUIRED,
        STATE_REVALIDATION_REQUIRED,
    },
}

# Candidate producers cannot grant runtime authority to their own output.
# This first entry is source-owned and names a concrete PREOPEN consumer,
# rollback, apply-receipt, and post-apply-attribution implementation.  Its
# bounded contract changes only the entry prompt from the exact hot-v1 hash to
# the reviewed V2.6 hash for KRX regular; all broker/safety/provider/quantity
# authority remains outside the family.
MAIN_AI_QUALITY_RUNTIME_FAMILY = "main_ai_quality_entry_prompt_contract_v1"
MAIN_AI_QUALITY_BOUNDED_CONTRACT = {
    "schema": "main_ai_quality_entry_prompt_bounded_contract_v1",
    "stage": "entry",
    "axis": "prompt_contract_effect",
    "effective_venue": "KRX",
    "session_bucket": "KRX_REGULAR",
    "instrument_scope": "effective_date_official_kospi_kosdaq_common_stock_only",
    "current_prompt_version": "hot_v1",
    "recommended_prompt_version": "decision_quality_v2_6",
    "apply_timing": "next_krx_trading_date_preopen_before_0800_kst",
    "rollback": "automatic_configured_prompt_fallback_on_any_contract_gap",
    "forbidden_changes": [
        "provider_or_model",
        "order_price_or_quantity",
        "threshold_or_cap",
        "bot_process_state",
        "broker_account_order_cooldown_guard",
        "hard_protect_or_emergency_safety",
    ],
}
MAIN_AI_QUALITY_BOUNDED_CONTRACT_SHA256 = hashlib.sha256(
    json.dumps(
        MAIN_AI_QUALITY_BOUNDED_CONTRACT,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
).hexdigest()
TRUSTED_RUNTIME_FAMILY_REGISTRY: Mapping[str, Mapping[str, Any]] = {
    MAIN_AI_QUALITY_RUNTIME_FAMILY: {
        "enabled": True,
        "stage": "entry",
        "axis": "prompt_contract_effect",
        "bounded_contract_sha256": MAIN_AI_QUALITY_BOUNDED_CONTRACT_SHA256,
        "preopen_consumer": (
            "src.engine.automation.main_ai_quality_runtime_family.preopen_apply"
        ),
        "apply_receipt_owner": "main_ai_quality_runtime_family_preopen_apply",
        "post_apply_attribution_owner": (
            "main_ai_quality_runtime_family_post_apply_attribution"
        ),
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "bounded_values": {
            "current": (
                "922c6ccebe50be668c195acbe8f3a795aec9dacf3e4be09adc4174547d1be10e"
            ),
            "recommended": (
                "ca3b73e0ce857929d8fb0d0e667223163f8cb358c2054bedac7f62a0f1f3b0d0"
            ),
        },
        "direct_order_authority": False,
        "provider_route_authority": False,
        "quantity_authority": False,
        "hard_safety_authority": False,
        "receipt_content_sha256_required": True,
        "requires_post_apply_attribution_before_auto_chain": True,
    }
}

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


def _aware_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(KST)


def _artifact_is_newer_than_invalidation(
    artifact: Mapping[str, Any], entry: Mapping[str, Any]
) -> bool:
    decided_at = _aware_datetime(artifact.get("decided_at_kst"))
    if decided_at is None:
        return False
    invalidated_at = _aware_datetime(entry.get("operator_decision_invalidated_at_kst"))
    if invalidated_at is None:
        return True
    return decided_at > invalidated_at


def _invalidate_operator_decision(
    entry: dict[str, Any], *, invalidated_at: datetime, reason: str
) -> None:
    previous = str(entry.get("operator_decision_artifact") or "").strip()
    if previous:
        previous_payload = _load_json(Path(previous))
        if previous_payload is None:
            # Do not clear the only canonical approval pointer when neither an
            # immutable archive nor an inline artifact snapshot can be made.
            raise ValueError(
                "operator_decision_artifact_unreadable_during_invalidation"
            )
        if (
            previous_payload.get("schema") != APPROVAL_SCHEMA
            or previous_payload.get("queue_key") != entry.get("queue_key")
            or previous_payload.get("candidate_id") != entry.get("candidate_id")
            or previous_payload.get("candidate_sha256") != entry.get("candidate_sha256")
            or previous_payload.get("operator_authorization_id")
            != entry.get("operator_authorization_id")
            or previous_payload.get("decided_at_kst")
            != entry.get("operator_decision_at_kst")
        ):
            raise ValueError(
                "operator_decision_artifact_contract_invalid_during_invalidation"
            )
        archived = _archive_operator_decision_artifact(
            Path(previous),
            payload=previous_payload,
            invalidated_at=invalidated_at,
            reason=reason,
        )
        history = list(entry.get("invalidated_operator_decision_artifacts") or ())
        if archived is not None and str(archived) not in history:
            history.append(str(archived))
        entry["invalidated_operator_decision_artifacts"] = history
        history_rows = list(entry.get("invalidated_operator_decision_history") or ())
        history_rows.append(
            {
                "canonical_artifact_path": previous,
                "archived_artifact_path": str(archived) if archived else None,
                "invalidated_at_kst": invalidated_at.isoformat(timespec="microseconds"),
                "reason": reason,
                "archive_status": (
                    "immutable_file_and_inline_snapshot"
                    if archived
                    else "inline_snapshot_only"
                ),
                "operator_decision_artifact_sha256": hashlib.sha256(
                    _canonical_json(previous_payload)
                ).hexdigest(),
                "operator_decision_artifact_snapshot": previous_payload,
            }
        )
        entry["invalidated_operator_decision_history"] = history_rows
    for field in (
        "operator_decision_artifact",
        "operator_decision_at_kst",
        "operator_authorization_id",
        "operator_registry_entry_sha256",
    ):
        entry.pop(field, None)
    entry["operator_decision_invalidated_at_kst"] = invalidated_at.isoformat(
        timespec="microseconds"
    )
    entry["operator_decision_invalidation_reason"] = reason


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _empty_source_artifact_provenance(path: Path | None) -> dict[str, Any]:
    return {
        "schema": SOURCE_ARTIFACT_PROVENANCE_SCHEMA,
        "path": str(path) if path else None,
        "sha256": None,
        "mtime_ns": None,
        "size_bytes": None,
    }


def _source_path_stat(path: Path) -> os.stat_result:
    """Return the pathname stat used to verify an opened source snapshot."""

    return path.stat()


def _source_stat_identity(stat: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        stat.st_dev,
        stat.st_ino,
        stat.st_size,
        stat.st_mtime_ns,
        stat.st_ctime_ns,
    )


def _capture_source_artifact(
    path: Path,
) -> tuple[dict[str, Any] | None, dict[str, Any], str]:
    """Read and identify one stable source snapshot without pathname re-reads.

    The parsed payload and provenance digest are derived from the same bytes. The
    descriptor and pathname identities are compared so an in-place write or atomic
    replacement during capture fails closed instead of mixing queue input with a
    different status-report artifact.
    """

    provenance = _empty_source_artifact_provenance(path)
    try:
        with path.open("rb") as handle:
            stat_before = os.fstat(handle.fileno())
            raw = handle.read()
            stat_after = os.fstat(handle.fileno())
        pathname_stat = _source_path_stat(path)
    except OSError:
        return None, provenance, "missing_or_unreadable"
    if (
        _source_stat_identity(stat_before) != _source_stat_identity(stat_after)
        or _source_stat_identity(stat_after) != _source_stat_identity(pathname_stat)
        or len(raw) != stat_after.st_size
    ):
        return None, provenance, "source_changed_during_snapshot"
    provenance.update(
        {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "mtime_ns": stat_after.st_mtime_ns,
            "size_bytes": stat_after.st_size,
        }
    )
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, provenance, "missing_or_unreadable"
    if not isinstance(payload, dict):
        return None, provenance, "missing_or_unreadable"
    return payload, provenance, "loaded"


def _source_artifact_snapshot_is_current(
    path: Path, expected_provenance: Mapping[str, Any]
) -> bool:
    """Confirm that the canonical path still names the captured source snapshot."""

    _payload, current_provenance, _status = _capture_source_artifact(path)
    return current_provenance == dict(expected_provenance)


def candidate_sha256(candidate: Mapping[str, Any]) -> str:
    payload = dict(candidate)
    payload.pop("candidate_sha256", None)
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def _atomic_write_json(
    path: Path,
    payload: Mapping[str, Any],
    *,
    generation: ArtifactGenerationLease | None = None,
) -> None:
    write_json_object_generation_safe(
        path,
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
        trailing_newline=True,
        generation=generation,
    )


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
        payload = read_json_object_strict_receipt(path).payload
    except FileNotFoundError:
        return None
    return payload


def _archive_operator_decision_artifact(
    path: Path,
    *,
    payload: Mapping[str, Any],
    invalidated_at: datetime,
    reason: str,
) -> Path | None:
    invalidated_at_text = invalidated_at.isoformat(timespec="microseconds")
    artifact_digest = hashlib.sha256(_canonical_json(payload)).hexdigest()
    archive_identity = hashlib.sha256(
        _canonical_json(
            {
                "artifact_sha256": artifact_digest,
                "invalidated_at_kst": invalidated_at_text,
                "reason": reason,
            }
        )
    ).hexdigest()
    archive_path = (
        path.parent
        / "invalidated"
        / (f"{path.stem}__invalidated_{archive_identity[:16]}.json")
    )
    archive_payload = {
        "schema": "machine_microstructure_policy_invalidated_decision_archive_v1",
        "canonical_artifact_path": str(path),
        "operator_decision_artifact_sha256": artifact_digest,
        "invalidated_at_kst": invalidated_at_text,
        "invalidation_reason": reason,
        "operator_decision_artifact": payload,
    }
    try:
        _atomic_write_json(archive_path, archive_payload)
    except OSError:
        return None
    return archive_path


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
    rolling_paired_counts = evidence.get("rolling_paired_complete_lifecycle_count")
    rolling_paired_floors = evidence.get("rolling_paired_complete_lifecycle_floor")
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
    if rolling_paired_floors != ROLLING_PAIRED_LIFECYCLE_FLOORS:
        errors.append("rolling_paired_lifecycle_floor_contract_invalid")
    if not isinstance(rolling_paired_counts, Mapping):
        errors.append("rolling_paired_lifecycle_counts_missing")
    else:
        for window, floor in ROLLING_PAIRED_LIFECYCLE_FLOORS.items():
            count = _nonnegative_int(rolling_paired_counts.get(window))
            if count is None or count < floor:
                errors.append(f"rolling_{window}_paired_lifecycle_count_below_{floor}")
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


def _required_receipt_hash_valid(
    receipt: Mapping[str, Any], registry_entry: Mapping[str, Any] | None
) -> bool:
    if not (registry_entry or {}).get("receipt_content_sha256_required"):
        return True
    body = {
        key: value for key, value in receipt.items() if key != "receipt_content_sha256"
    }
    expected = hashlib.sha256(
        json.dumps(
            body,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return receipt.get("receipt_content_sha256") == expected


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
    post_apply_attribution = design.get("post_apply_attribution")
    if not _nonempty_mapping(post_apply_attribution):
        errors.append("post_apply_attribution_missing")
    elif not str(post_apply_attribution.get("owner") or "").strip():
        errors.append("post_apply_attribution_owner_missing")
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
        or (
            "effective_venue" in registry_entry
            and registry_entry.get("effective_venue") != design.get("effective_venue")
        )
        or (
            "session_bucket" in registry_entry
            and registry_entry.get("session_bucket") != design.get("session_bucket")
        )
        or (
            "bounded_values" in registry_entry
            and registry_entry.get("bounded_values") != bounded_values
        )
        or not str(registry_entry.get("apply_receipt_owner") or "").strip()
        or registry_entry.get("post_apply_attribution_owner")
        != (post_apply_attribution or {}).get("owner")
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
        "objective_followups": [],
        "family_enrollments": {},
    }


_PERSISTED_CANDIDATE_STATES = {
    STATE_DESIGN_REQUIRED,
    STATE_REVIEW_READY,
    STATE_USER_APPROVED,
    STATE_PREOPEN_SCHEDULED,
    STATE_PREOPEN_MISSED_REVIEW_REQUIRED,
    STATE_REVALIDATION_REQUIRED,
    STATE_APPLIED,
    STATE_POST_APPLY_ATTRIBUTED,
    STATE_AUTO_CHAIN_ELIGIBLE,
    STATE_HOLD,
    STATE_REJECTED,
    STATE_EXPIRED,
}


def _persisted_candidate_errors(entry: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    candidate = entry.get("candidate")
    if not isinstance(candidate, Mapping):
        return ["candidate_not_object"]
    recomputed = candidate_sha256(candidate)
    candidate_id = str(candidate.get("candidate_id") or "")
    declared = str(candidate.get("candidate_sha256") or "")
    if not candidate_id:
        errors.append("candidate_id_missing")
    if declared != recomputed:
        errors.append("nested_candidate_sha256_mismatch")
    if str(entry.get("candidate_sha256") or "") != recomputed:
        errors.append("entry_candidate_sha256_mismatch")
    if str(entry.get("candidate_id") or "") != candidate_id:
        errors.append("entry_candidate_id_mismatch")
    if entry.get("source_date") != candidate.get("source_date"):
        errors.append("entry_source_date_mismatch")
    if entry.get("evidence_valid_through") != candidate.get("evidence_valid_through"):
        errors.append("entry_evidence_valid_through_mismatch")
    if entry.get("queue_key") != _queue_key(candidate_id, recomputed):
        errors.append("queue_key_derivation_mismatch")
    if entry.get("state") not in _PERSISTED_CANDIDATE_STATES:
        errors.append("candidate_state_invalid")
    for field, expected in (
        ("runtime_effect", False),
        ("allowed_runtime_apply", False),
        ("actual_order_submitted", False),
        ("broker_order_forbidden", True),
    ):
        if candidate.get(field) is not expected:
            errors.append(f"candidate_authority_mismatch:{field}")
    state = str(entry.get("state") or "")
    authorization_mode = str(entry.get("authorization_mode") or "")
    if (
        state
        in {
            STATE_USER_APPROVED,
            STATE_PREOPEN_SCHEDULED,
            STATE_APPLIED,
            STATE_POST_APPLY_ATTRIBUTED,
        }
        and authorization_mode != "enrolled_same_bounded_family_auto_chain"
    ):
        for field in (
            "operator_decision_artifact",
            "operator_authorization_id",
            "operator_decision_at_kst",
            "operator_registry_entry_sha256",
        ):
            if not str(entry.get(field) or "").strip():
                errors.append(f"candidate_operator_binding_missing:{field}")
    if state in {
        STATE_PREOPEN_SCHEDULED,
        STATE_APPLIED,
        STATE_POST_APPLY_ATTRIBUTED,
    }:
        if not str(entry.get("preopen_handoff") or "").strip():
            errors.append("candidate_preopen_handoff_missing")
        try:
            date.fromisoformat(str(entry.get("preopen_target_date") or ""))
        except ValueError:
            errors.append("candidate_preopen_target_date_invalid")
        if authorization_mode not in {
            "first_explicit_operator_approval",
            "enrolled_same_bounded_family_auto_chain",
        }:
            errors.append("candidate_authorization_mode_invalid")
    if (
        state in {STATE_APPLIED, STATE_POST_APPLY_ATTRIBUTED}
        and not str(entry.get("family_apply_receipt") or "").strip()
    ):
        errors.append("candidate_apply_receipt_missing")
    if (
        state == STATE_POST_APPLY_ATTRIBUTED
        and not str(entry.get("post_apply_attribution_receipt") or "").strip()
    ):
        errors.append("candidate_attribution_receipt_missing")
    return errors


def _persisted_candidate_collection_errors(
    candidates: Any,
    family_enrollments: Mapping[str, Any],
) -> list[str]:
    if not isinstance(candidates, list):
        return ["candidates_not_list"]
    errors: list[str] = []
    queue_keys: list[str] = []
    identities: list[tuple[str, str]] = []
    for index, raw in enumerate(candidates):
        if not isinstance(raw, Mapping):
            errors.append(f"candidate_row_not_object:{index}")
            continue
        row_errors = _persisted_candidate_errors(raw)
        errors.extend(f"candidate:{index}:{error}" for error in row_errors)
        queue_keys.append(str(raw.get("queue_key") or ""))
        identities.append(
            (
                str(raw.get("candidate_id") or ""),
                str(raw.get("candidate_sha256") or ""),
            )
        )
        if raw.get("state") in {
            STATE_AUTO_CHAIN_ELIGIBLE,
            STATE_PREOPEN_SCHEDULED,
        } and raw.get("authorization_mode") in {
            None,
            "enrolled_same_bounded_family_auto_chain",
        }:
            candidate = raw.get("candidate") or {}
            design = candidate.get("runtime_design") or {}
            family = str(design.get("runtime_family") or "")
            enrollment = family_enrollments.get(family)
            if (
                not isinstance(enrollment, Mapping)
                or enrollment.get("runtime_family") != family
                or enrollment.get("stage") != design.get("stage")
                or enrollment.get("axis") != design.get("axis")
                or enrollment.get("bounded_contract_sha256")
                != design.get("bounded_contract_sha256")
                or enrollment.get("runtime_registry_entry_sha256")
                != raw.get("runtime_registry_entry_sha256")
                or enrollment.get("enrolled_after_guarded_apply") is not True
            ):
                errors.append(f"candidate:{index}:family_enrollment_mismatch")
    if len(queue_keys) != len(set(queue_keys)):
        errors.append("duplicate_queue_key")
    if len(identities) != len(set(identities)):
        errors.append("duplicate_candidate_identity")
    return errors


def load_queue(
    path: Path = DEFAULT_QUEUE_PATH,
    *,
    now: datetime | None = None,
    generation: ArtifactGenerationLease | None = None,
) -> dict[str, Any]:
    try:
        receipt = read_json_object_strict_receipt(path, generation=generation)
    except FileNotFoundError:
        return _empty_queue(now=_now_kst(now))
    if (
        receipt.logical_path != path.absolute()
        or receipt.physical_path != receipt.logical_path
        or receipt.generation_census
        != ((receipt.logical_path.name, receipt.physical_identity),)
    ):
        raise ValueError("approval_queue_generation_invalid")
    payload = receipt.payload
    if (
        payload.get("schema") != QUEUE_SCHEMA
        or payload.get("metric_contract") != METRIC_CONTRACT
        or not isinstance(payload.get("candidates"), list)
        or not isinstance(payload.get("family_enrollments"), dict)
        or not isinstance(payload.get("objective_followups", []), list)
    ):
        raise ValueError("approval_queue_contract_invalid")
    candidate_errors = _persisted_candidate_collection_errors(
        payload.get("candidates"),
        payload.get("family_enrollments") or {},
    )
    if candidate_errors:
        raise ValueError(
            "approval_queue_candidate_contract_invalid:" + ",".join(candidate_errors)
        )
    # Keep the v1 queue and metric contract compatible with ledgers written
    # before objective follow-ups existed.  The new collection is deliberately
    # separate from candidates and therefore cannot enter approval/apply code.
    objective_followups = payload.get("objective_followups", [])
    objective_followup_ids = [
        str(row.get("followup_id") or "")
        for row in objective_followups
        if isinstance(row, Mapping)
    ]
    persisted_candidates = [
        row for row in payload.get("candidates", []) if isinstance(row, Mapping)
    ]
    if any(
        not isinstance(row, Mapping)
        or _persisted_objective_followup_errors(row)
        or _objective_handoff_queue_evidence_errors(
            row, queue_candidates=persisted_candidates
        )
        or _objective_completion_evidence_errors(
            row, queue_candidates=persisted_candidates
        )
        for row in objective_followups
    ) or any(count != 1 for count in Counter(objective_followup_ids).values()):
        raise ValueError("approval_queue_objective_followup_contract_invalid")
    return {**payload, "objective_followups": list(objective_followups)}


def _objective_authority_value(row: Mapping[str, Any], field: str) -> Any:
    nested = row.get("authority")
    nested_value = nested.get(field) if isinstance(nested, Mapping) else None
    top_present = field in row
    nested_present = isinstance(nested, Mapping) and field in nested
    if top_present and nested_present and row.get(field) != nested_value:
        return "__conflicting_authority__"
    if top_present:
        return row.get(field)
    if nested_present:
        return nested_value
    return None


def _objective_gap_codes(value: Any, *, allow_empty: bool = False) -> list[str] | None:
    if (
        not isinstance(value, list)
        or (not value and not allow_empty)
        or any(not isinstance(item, str) or not item.strip() for item in value)
        or len(set(value)) != len(value)
    ):
        return None
    return list(value)


def _objective_candidate_binding_errors(
    candidate: Mapping[str, Any],
    *,
    followup_id: str,
    expected_resolved_gap_codes: Sequence[str],
) -> list[str]:
    binding = candidate.get("objective_followup_binding")
    if not isinstance(binding, Mapping):
        return ["objective_candidate_binding_missing"]
    errors: list[str] = []
    if binding.get("schema") != OBJECTIVE_CANDIDATE_BINDING_SCHEMA:
        errors.append("objective_candidate_binding_schema_invalid")
    if binding.get("followup_id") != followup_id:
        errors.append("objective_candidate_binding_followup_id_mismatch")
    resolved_gap_codes = _objective_gap_codes(
        binding.get("resolved_gap_codes"), allow_empty=True
    )
    if resolved_gap_codes is None:
        errors.append("objective_candidate_binding_gap_codes_invalid")
    elif sorted(resolved_gap_codes) != sorted(expected_resolved_gap_codes):
        errors.append("objective_candidate_binding_gap_codes_mismatch")
    return errors


def _objective_handoff_binding_errors(row: Mapping[str, Any]) -> list[str]:
    if row.get("state") != "CANDIDATE_QUEUE_HANDOFF":
        return []
    binding = row.get("candidate_handoff_binding")
    if not isinstance(binding, Mapping):
        return ["objective_followup_candidate_handoff_binding_missing"]
    errors: list[str] = []
    if binding.get("schema") != OBJECTIVE_HANDOFF_BINDING_SCHEMA:
        errors.append("objective_followup_candidate_handoff_binding_schema_invalid")
    if binding.get("followup_id") != row.get("followup_id"):
        errors.append("objective_followup_candidate_handoff_binding_id_mismatch")
    if not str(binding.get("candidate_id") or "").strip():
        errors.append("objective_followup_bound_candidate_id_missing")
    if not SHA256_PATTERN.fullmatch(str(binding.get("candidate_sha256") or "")):
        errors.append("objective_followup_bound_candidate_sha256_invalid")
    required_gap_codes = _objective_gap_codes(
        binding.get("required_gap_codes"), allow_empty=True
    )
    resolved_gap_codes = _objective_gap_codes(
        binding.get("resolved_gap_codes"), allow_empty=True
    )
    if required_gap_codes is None:
        errors.append("objective_followup_required_gap_codes_invalid")
    if resolved_gap_codes is None:
        errors.append("objective_followup_resolved_gap_codes_invalid")
    if (
        required_gap_codes is not None
        and resolved_gap_codes is not None
        and sorted(required_gap_codes) != sorted(resolved_gap_codes)
    ):
        errors.append("objective_followup_required_gaps_not_fully_resolved")
    if required_gap_codes is not None and any(
        gap_code not in OBJECTIVE_HANDOFF_RESOLVABLE_GAP_CODES
        for gap_code in required_gap_codes
    ):
        errors.append("objective_followup_non_handoff_gap_transfer_forbidden")
    return errors


def objective_followup_errors(
    row: Mapping[str, Any],
    *,
    target_date: date,
    require_consumer_completion_evidence: bool = False,
) -> list[str]:
    errors: list[str] = []
    if row.get("schema") != OBJECTIVE_FOLLOWUP_SCHEMA:
        errors.append("objective_followup_schema_invalid")
    if not str(row.get("followup_id") or "").strip():
        errors.append("objective_followup_id_missing")
    elif row.get("followup_id") != FAST_LIFECYCLE_OBJECTIVE_FOLLOWUP_ID:
        errors.append("objective_followup_id_invalid")
    if str(row.get("source_date") or "") != target_date.isoformat():
        errors.append("objective_followup_source_date_not_target_date")
    if not is_krx_trading_day(target_date):
        errors.append("objective_followup_source_date_not_krx_trading_day")
    state = str(row.get("state") or "").strip()
    if state not in OBJECTIVE_FOLLOWUP_STATES:
        errors.append("objective_followup_state_invalid")
    followup_required = row.get("followup_required")
    if followup_required is not True and followup_required is not False:
        errors.append("objective_followup_required_not_boolean")
    if state in OBJECTIVE_FOLLOWUP_CLOSED_STATES:
        if followup_required is not False:
            errors.append("closed_objective_followup_still_required")
    elif followup_required is not True:
        errors.append("open_objective_followup_not_required")
    if not str(row.get("attention_class") or "").strip():
        errors.append("objective_followup_attention_class_missing")
    if row.get("operator_decision_required") is not False:
        errors.append("objective_followup_operator_decision_authority_forbidden")
    if not str(row.get("next_action") or "").strip():
        errors.append("objective_followup_next_action_missing")
    metric_contract = row.get("metric_contract")
    if not isinstance(metric_contract, Mapping):
        errors.append("objective_followup_metric_contract_missing")
    else:
        missing_metric_fields = sorted(
            OBJECTIVE_METRIC_CONTRACT_FIELDS.difference(metric_contract)
        )
        if missing_metric_fields:
            errors.append(
                "objective_followup_metric_contract_fields_missing:"
                + ",".join(missing_metric_fields)
            )
        if (
            metric_contract.get("decision_authority")
            != "postclose_followup_tracking_only"
        ):
            errors.append("objective_followup_metric_decision_authority_invalid")
        for field in (
            "metric_role",
            "window_policy",
            "primary_decision_metric",
        ):
            if not str(metric_contract.get(field) or "").strip():
                errors.append(f"objective_followup_metric_{field}_invalid")
        for field in ("source_quality_gate", "forbidden_uses"):
            value = metric_contract.get(field)
            if (
                not isinstance(value, list)
                or not value
                or any(not isinstance(item, str) or not item.strip() for item in value)
            ):
                errors.append(f"objective_followup_metric_{field}_invalid")
        if metric_contract.get("sample_floor") is None:
            errors.append("objective_followup_metric_sample_floor_invalid")
    gap_codes = row.get("remaining_gap_codes")
    if not isinstance(gap_codes, list) or any(
        not isinstance(value, str) or not value.strip() for value in gap_codes
    ):
        errors.append("objective_followup_gap_codes_invalid")
    elif followup_required is True and not gap_codes:
        errors.append("open_objective_followup_gap_codes_empty")
    if state == "CANDIDATE_QUEUE_HANDOFF":
        if gap_codes:
            errors.append("handoff_objective_followup_gap_codes_not_empty")
        errors.extend(_objective_handoff_binding_errors(row))
    elif row.get("candidate_handoff_binding") is not None and (
        state != "COMPLETE" or not require_consumer_completion_evidence
    ):
        errors.append("objective_followup_source_handoff_binding_forbidden")
    if state == "COMPLETE":
        if gap_codes:
            errors.append("complete_objective_followup_gap_codes_not_empty")
        completion_evidence = row.get("completion_evidence")
        if not require_consumer_completion_evidence:
            if "completion_evidence" in row:
                errors.append(
                    "complete_objective_followup_source_completion_evidence_forbidden"
                )
        elif not isinstance(completion_evidence, Mapping):
            errors.append("complete_objective_followup_evidence_missing")
        else:
            if not str(completion_evidence.get("candidate_queue_key") or "").strip():
                errors.append("complete_objective_followup_candidate_queue_key_missing")
            if not str(completion_evidence.get("candidate_id") or "").strip():
                errors.append("complete_objective_followup_candidate_id_missing")
            if not SHA256_PATTERN.fullmatch(
                str(completion_evidence.get("candidate_sha256") or "")
            ):
                errors.append("complete_objective_followup_candidate_sha256_invalid")
            if (
                completion_evidence.get("candidate_state")
                != STATE_POST_APPLY_ATTRIBUTED
            ):
                errors.append("complete_objective_followup_candidate_state_invalid")
            if not str(
                completion_evidence.get("post_apply_attribution_receipt") or ""
            ).strip():
                errors.append("complete_objective_followup_attribution_receipt_missing")
            if completion_evidence.get("causal_completion_verified") is not True:
                errors.append(
                    "complete_objective_followup_causal_completion_not_verified"
                )
            if completion_evidence.get("objective_followup_id") != row.get(
                "followup_id"
            ):
                errors.append("complete_objective_followup_objective_binding_mismatch")
            if (
                completion_evidence.get("verification")
                != "consumer_queue_handoff_and_attribution_receipt_match"
            ):
                errors.append("complete_objective_followup_verification_invalid")
    expected_authority = {
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    for field, expected in expected_authority.items():
        if _objective_authority_value(row, field) is not expected:
            errors.append(f"objective_followup_{field}_invalid")
    forbidden_present = sorted(
        field for field in OBJECTIVE_FOLLOWUP_FORBIDDEN_FIELDS if field in row
    )
    if forbidden_present:
        errors.append(
            "objective_followup_candidate_authority_fields_forbidden:"
            + ",".join(forbidden_present)
        )
    return errors


def _persisted_objective_followup_errors(row: Mapping[str, Any]) -> list[str]:
    try:
        source_date = date.fromisoformat(str(row.get("source_date") or ""))
    except ValueError:
        return ["objective_followup_source_date_invalid"]
    errors = objective_followup_errors(
        row,
        target_date=source_date,
        require_consumer_completion_evidence=True,
    )
    source_path = row.get("source_path")
    if not isinstance(source_path, str) or not source_path.strip():
        errors.append("objective_followup_source_path_invalid")
    if not SHA256_PATTERN.fullmatch(str(row.get("source_payload_sha256") or "")):
        errors.append("objective_followup_source_payload_sha256_invalid")
    first_seen = _aware_datetime(row.get("first_seen_at_kst"))
    last_seen = _aware_datetime(row.get("last_seen_at_kst"))
    if first_seen is None:
        errors.append("objective_followup_first_seen_at_kst_invalid")
    if last_seen is None:
        errors.append("objective_followup_last_seen_at_kst_invalid")
    if first_seen is not None and last_seen is not None and first_seen > last_seen:
        errors.append("objective_followup_seen_at_order_invalid")
    reminders = row.get("reminders")
    if not isinstance(reminders, Mapping):
        errors.append("objective_followup_reminders_invalid")
    else:
        for phase, reminder_date_raw in reminders.items():
            if phase != "postclose":
                errors.append("objective_followup_reminder_phase_invalid")
                continue
            try:
                reminder_date = date.fromisoformat(str(reminder_date_raw or ""))
            except ValueError:
                errors.append("objective_followup_reminder_date_invalid")
                continue
            if not is_krx_trading_day(reminder_date):
                errors.append("objective_followup_reminder_date_not_krx_trading_day")
    handoff_evidence = row.get("handoff_evidence")
    if row.get("state") == "CANDIDATE_QUEUE_HANDOFF" or handoff_evidence is not None:
        if not isinstance(handoff_evidence, Mapping):
            errors.append("objective_followup_handoff_evidence_missing")
        else:
            if not str(
                handoff_evidence.get("accepted_candidate_queue_key") or ""
            ).strip():
                errors.append("objective_followup_handoff_queue_key_missing")
            if not SHA256_PATTERN.fullmatch(
                str(handoff_evidence.get("accepted_candidate_sha256") or "")
            ):
                errors.append("objective_followup_handoff_candidate_sha256_invalid")
            if not str(handoff_evidence.get("accepted_candidate_id") or "").strip():
                errors.append("objective_followup_handoff_candidate_id_missing")
            if not str(handoff_evidence.get("source_path") or "").strip():
                errors.append("objective_followup_handoff_source_path_missing")
            try:
                handoff_source_date = date.fromisoformat(
                    str(handoff_evidence.get("source_date") or "")
                )
            except ValueError:
                errors.append("objective_followup_handoff_source_date_invalid")
            else:
                if handoff_source_date > source_date:
                    errors.append("objective_followup_handoff_source_date_after_state")
                if not is_krx_trading_day(handoff_source_date):
                    errors.append(
                        "objective_followup_handoff_source_date_not_krx_trading_day"
                    )
            if (
                handoff_evidence.get("verification")
                != "same_run_objective_bound_candidate_intake_accepted"
            ):
                errors.append("objective_followup_handoff_verification_invalid")
            if handoff_evidence.get("objective_followup_id") != row.get("followup_id"):
                errors.append("objective_followup_handoff_objective_id_mismatch")
            handoff_gap_codes = _objective_gap_codes(
                handoff_evidence.get("resolved_gap_codes"), allow_empty=True
            )
            if handoff_gap_codes is None:
                errors.append("objective_followup_handoff_gap_codes_invalid")
            source_binding = row.get("candidate_handoff_binding")
            if not isinstance(source_binding, Mapping):
                errors.append("objective_followup_persisted_binding_missing")
            else:
                if handoff_evidence.get("accepted_candidate_id") != source_binding.get(
                    "candidate_id"
                ):
                    errors.append("objective_followup_handoff_bound_candidate_mismatch")
                if handoff_evidence.get(
                    "accepted_candidate_sha256"
                ) != source_binding.get("candidate_sha256"):
                    errors.append("objective_followup_handoff_bound_sha256_mismatch")
                if handoff_gap_codes is not None and sorted(
                    handoff_gap_codes
                ) != sorted(source_binding.get("resolved_gap_codes") or []):
                    errors.append("objective_followup_handoff_bound_gaps_mismatch")
    return errors


def _objective_handoff_queue_evidence_errors(
    row: Mapping[str, Any], *, queue_candidates: Sequence[Mapping[str, Any]]
) -> list[str]:
    handoff_evidence = row.get("handoff_evidence")
    if not isinstance(handoff_evidence, Mapping):
        return []
    matching = [
        candidate
        for candidate in queue_candidates
        if candidate.get("queue_key")
        == handoff_evidence.get("accepted_candidate_queue_key")
        and candidate.get("candidate_sha256")
        == handoff_evidence.get("accepted_candidate_sha256")
    ]
    if len(matching) != 1:
        return ["objective_followup_handoff_candidate_not_uniquely_found"]
    candidate = matching[0]
    errors: list[str] = []
    if candidate.get("candidate_id") != handoff_evidence.get("accepted_candidate_id"):
        errors.append("objective_followup_handoff_candidate_id_mismatch")
    if candidate.get("source_date") != handoff_evidence.get("source_date"):
        errors.append("objective_followup_handoff_candidate_source_date_mismatch")
    source_binding = row.get("candidate_handoff_binding")
    source_candidate = candidate.get("candidate")
    if not isinstance(source_binding, Mapping):
        errors.append("objective_followup_persisted_binding_missing")
    elif not isinstance(source_candidate, Mapping):
        errors.append("objective_followup_queued_source_candidate_missing")
    else:
        if candidate.get("candidate_id") != source_binding.get("candidate_id"):
            errors.append("objective_followup_queued_candidate_binding_id_mismatch")
        if candidate.get("candidate_sha256") != source_binding.get("candidate_sha256"):
            errors.append("objective_followup_queued_candidate_binding_sha_mismatch")
        errors.extend(
            _objective_candidate_binding_errors(
                source_candidate,
                followup_id=str(row.get("followup_id") or ""),
                expected_resolved_gap_codes=list(
                    source_binding.get("resolved_gap_codes") or []
                ),
            )
        )
    return errors


def _objective_completion_evidence_errors(
    row: Mapping[str, Any], *, queue_candidates: Sequence[Mapping[str, Any]]
) -> list[str]:
    if row.get("state") != "COMPLETE":
        return []
    completion_evidence = row.get("completion_evidence")
    if not isinstance(completion_evidence, Mapping):
        return []
    queue_key = str(completion_evidence.get("candidate_queue_key") or "")
    candidate_sha256_value = str(completion_evidence.get("candidate_sha256") or "")
    matching = [
        candidate
        for candidate in queue_candidates
        if str(candidate.get("queue_key") or "") == queue_key
        and str(candidate.get("candidate_sha256") or "") == candidate_sha256_value
    ]
    if len(matching) != 1:
        return ["complete_objective_followup_candidate_not_uniquely_found"]
    candidate = matching[0]
    errors: list[str] = []
    if candidate.get("state") != STATE_POST_APPLY_ATTRIBUTED:
        errors.append("complete_objective_followup_candidate_not_post_apply_attributed")
    if str(candidate.get("post_apply_attribution_receipt") or "") != str(
        completion_evidence.get("post_apply_attribution_receipt") or ""
    ):
        errors.append("complete_objective_followup_attribution_receipt_mismatch")
    if completion_evidence.get("objective_followup_id") != row.get("followup_id"):
        errors.append("complete_objective_followup_objective_binding_mismatch")
    handoff_evidence = row.get("handoff_evidence")
    if not isinstance(handoff_evidence, Mapping):
        errors.append("complete_objective_followup_handoff_evidence_missing")
    elif (
        handoff_evidence.get("accepted_candidate_queue_key") != queue_key
        or handoff_evidence.get("accepted_candidate_sha256") != candidate_sha256_value
        or handoff_evidence.get("accepted_candidate_id")
        != completion_evidence.get("candidate_id")
        or handoff_evidence.get("source_date")
        != completion_evidence.get("handoff_source_date")
    ):
        errors.append("complete_objective_followup_handoff_candidate_mismatch")
    source_binding = row.get("candidate_handoff_binding")
    source_candidate = candidate.get("candidate")
    if not isinstance(source_binding, Mapping):
        errors.append("complete_objective_followup_candidate_binding_missing")
    elif not isinstance(source_candidate, Mapping):
        errors.append("complete_objective_followup_source_candidate_missing")
    else:
        errors.extend(
            _objective_candidate_binding_errors(
                source_candidate,
                followup_id=str(row.get("followup_id") or ""),
                expected_resolved_gap_codes=list(
                    source_binding.get("resolved_gap_codes") or []
                ),
            )
        )
    return errors


def _derive_objective_completion_evidence(
    row: Mapping[str, Any],
    *,
    existing: Mapping[str, Any] | None,
    queue_candidates: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any] | None, list[str]]:
    if row.get("state") != "COMPLETE":
        return None, []
    handoff_evidence = (
        existing.get("handoff_evidence")
        if isinstance(existing, Mapping)
        and isinstance(existing.get("handoff_evidence"), Mapping)
        else None
    )
    if not isinstance(handoff_evidence, Mapping):
        return None, ["complete_objective_followup_handoff_evidence_missing"]
    if handoff_evidence.get("objective_followup_id") != row.get("followup_id"):
        return None, ["complete_objective_followup_handoff_objective_id_mismatch"]
    candidate_handoff_binding = (
        existing.get("candidate_handoff_binding")
        if isinstance(existing, Mapping)
        and isinstance(existing.get("candidate_handoff_binding"), Mapping)
        else None
    )
    if not isinstance(candidate_handoff_binding, Mapping):
        return None, ["complete_objective_followup_candidate_binding_missing"]
    queue_key = str(handoff_evidence.get("accepted_candidate_queue_key") or "").strip()
    candidate_sha256_value = str(
        handoff_evidence.get("accepted_candidate_sha256") or ""
    ).strip()
    candidate_id = str(handoff_evidence.get("accepted_candidate_id") or "").strip()
    matching = [
        candidate
        for candidate in queue_candidates
        if str(candidate.get("queue_key") or "") == queue_key
        and str(candidate.get("candidate_sha256") or "") == candidate_sha256_value
        and str(candidate.get("candidate_id") or "") == candidate_id
    ]
    if len(matching) != 1:
        return None, ["complete_objective_followup_causal_candidate_not_unique"]
    candidate = matching[0]
    if (
        candidate_handoff_binding.get("candidate_id") != candidate_id
        or candidate_handoff_binding.get("candidate_sha256") != candidate_sha256_value
    ):
        return None, ["complete_objective_followup_handoff_binding_mismatch"]
    source_candidate = candidate.get("candidate")
    if not isinstance(source_candidate, Mapping):
        return None, ["complete_objective_followup_source_candidate_missing"]
    candidate_binding_errors = _objective_candidate_binding_errors(
        source_candidate,
        followup_id=str(row.get("followup_id") or ""),
        expected_resolved_gap_codes=list(
            candidate_handoff_binding.get("resolved_gap_codes") or []
        ),
    )
    if candidate_binding_errors:
        return None, candidate_binding_errors
    if candidate.get("state") != STATE_POST_APPLY_ATTRIBUTED:
        return None, ["complete_objective_followup_candidate_not_post_apply_attributed"]
    receipt = str(candidate.get("post_apply_attribution_receipt") or "").strip()
    if not receipt:
        return None, ["complete_objective_followup_attribution_receipt_missing"]
    return (
        {
            "objective_followup_id": str(row.get("followup_id") or ""),
            "candidate_queue_key": queue_key,
            "candidate_id": candidate_id,
            "candidate_sha256": candidate_sha256_value,
            "candidate_state": STATE_POST_APPLY_ATTRIBUTED,
            "post_apply_attribution_receipt": receipt,
            "handoff_source_date": handoff_evidence.get("source_date"),
            "causal_completion_verified": True,
            "verification": "consumer_queue_handoff_and_attribution_receipt_match",
        },
        [],
    )


def _normalized_objective_followup(
    row: Mapping[str, Any],
    *,
    source_path: Path | None,
    generated: datetime,
    existing: Mapping[str, Any] | None,
    handoff_evidence: Mapping[str, Any] | None = None,
    completion_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    first_seen = (
        existing.get("first_seen_at_kst")
        if isinstance(existing, Mapping)
        else generated.isoformat(timespec="seconds")
    )
    reminders = (
        dict(existing.get("reminders") or {}) if isinstance(existing, Mapping) else {}
    )
    authority = {
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    existing_handoff_evidence = (
        existing.get("handoff_evidence")
        if isinstance(existing, Mapping)
        and isinstance(existing.get("handoff_evidence"), Mapping)
        else None
    )
    existing_candidate_handoff_binding = (
        existing.get("candidate_handoff_binding")
        if isinstance(existing, Mapping)
        and isinstance(existing.get("candidate_handoff_binding"), Mapping)
        else None
    )
    source_candidate_handoff_binding = (
        row.get("candidate_handoff_binding")
        if isinstance(row.get("candidate_handoff_binding"), Mapping)
        else None
    )
    return {
        "schema": OBJECTIVE_FOLLOWUP_SCHEMA,
        "followup_id": str(row.get("followup_id") or "").strip(),
        "source_date": str(row.get("source_date") or ""),
        "source_path": str(source_path) if source_path else None,
        "source_payload_sha256": hashlib.sha256(_canonical_json(row)).hexdigest(),
        "first_seen_at_kst": first_seen,
        "last_seen_at_kst": generated.isoformat(timespec="seconds"),
        "state": str(row.get("state") or "").strip(),
        "state_reason": str(row.get("state_reason") or "").strip() or None,
        "followup_required": row.get("followup_required"),
        "attention_class": str(row.get("attention_class") or "").strip(),
        "operator_decision_required": False,
        "objective": str(row.get("objective") or "").strip() or None,
        "current_capability": str(row.get("current_capability") or "").strip() or None,
        "remaining_gap_codes": list(row.get("remaining_gap_codes") or []),
        "next_action": str(row.get("next_action") or "").strip(),
        "metric_contract": dict(row.get("metric_contract") or {}),
        "completion_conditions": list(row.get("completion_conditions") or []),
        "completion_evidence": (
            dict(completion_evidence) if completion_evidence is not None else None
        ),
        "candidate_handoff_binding": (
            dict(source_candidate_handoff_binding)
            if row.get("state") == "CANDIDATE_QUEUE_HANDOFF"
            and source_candidate_handoff_binding is not None
            else (
                dict(existing_candidate_handoff_binding)
                if existing_candidate_handoff_binding is not None
                else None
            )
        ),
        "handoff_evidence": (
            dict(existing_handoff_evidence)
            if existing_handoff_evidence is not None
            else dict(handoff_evidence) if handoff_evidence is not None else None
        ),
        **authority,
        "authority": authority,
        "reminders": reminders,
    }


def sync_objective_followups(
    queue: Mapping[str, Any],
    *,
    source_followups: Sequence[Mapping[str, Any]],
    source_path: Path | None,
    as_of_date: date,
    source_status: str = "not_provided",
    accepted_candidate_queue_keys: Sequence[str] = (),
    now: datetime | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    generated = _now_kst(now)
    raw_entries = queue.get("objective_followups", [])
    queue_candidates = [
        row for row in queue.get("candidates", []) if isinstance(row, Mapping)
    ]
    if not isinstance(raw_entries, list) or any(
        not isinstance(row, Mapping)
        or _persisted_objective_followup_errors(row)
        or _objective_handoff_queue_evidence_errors(
            row, queue_candidates=queue_candidates
        )
        or _objective_completion_evidence_errors(row, queue_candidates=queue_candidates)
        for row in raw_entries
    ):
        raise ValueError("approval_queue_objective_followup_contract_invalid")
    entries = [dict(row) for row in raw_entries if isinstance(row, Mapping)]
    existing_id_counts = Counter(str(row.get("followup_id") or "") for row in entries)
    if any(count != 1 for count in existing_id_counts.values()):
        raise ValueError("approval_queue_objective_followup_contract_invalid")
    by_id = {
        str(row.get("followup_id") or ""): row
        for row in entries
        if str(row.get("followup_id") or "")
    }
    rejections: list[dict[str, Any]] = []
    accepted_candidate_keys = {
        str(value).strip()
        for value in accepted_candidate_queue_keys
        if str(value).strip()
    }
    accepted_candidates = sorted(
        (
            row
            for row in queue_candidates
            if str(row.get("queue_key") or "") in accepted_candidate_keys
            and row.get("source_date") == as_of_date.isoformat()
            and row.get("source_path") == (str(source_path) if source_path else None)
            and row.get("last_seen_at_kst") == generated.isoformat(timespec="seconds")
        ),
        key=lambda row: str(row.get("queue_key") or ""),
    )
    # Missing, stale, or invalid sources never erase a durable work item.  A
    # follow-up closes only through a valid exact-date handoff/complete row.
    if source_status == "loaded":
        source_id_counts = Counter(
            str(raw.get("followup_id") or "").strip()
            for raw in source_followups
            if isinstance(raw, Mapping)
        )
        for raw in source_followups:
            errors = objective_followup_errors(raw, target_date=as_of_date)
            handoff_evidence: dict[str, Any] | None = None
            completion_evidence: dict[str, Any] | None = None
            followup_id = str(raw.get("followup_id") or "").strip()
            if followup_id and source_id_counts[followup_id] != 1:
                errors.append("objective_followup_id_duplicate")
            existing = by_id.get(followup_id)
            if existing is not None:
                try:
                    existing_source_date = date.fromisoformat(
                        str(existing.get("source_date") or "")
                    )
                except ValueError:
                    errors.append("persisted_objective_followup_source_date_invalid")
                else:
                    if as_of_date < existing_source_date:
                        errors.append("objective_followup_source_date_regression")
                previous_state = str(existing.get("state") or "")
                next_state = str(raw.get("state") or "")
                if next_state not in OBJECTIVE_FOLLOWUP_ALLOWED_TRANSITIONS.get(
                    previous_state, set()
                ):
                    errors.append(
                        "objective_followup_state_transition_forbidden:"
                        f"{previous_state}->{next_state}"
                    )
            if (
                raw.get("state") == "CANDIDATE_QUEUE_HANDOFF"
                and not accepted_candidate_keys
            ):
                errors.append(
                    "objective_followup_candidate_handoff_not_accepted_this_run"
                )
            elif raw.get("state") == "CANDIDATE_QUEUE_HANDOFF":
                source_binding = raw.get("candidate_handoff_binding")
                source_required_gap_codes = (
                    _objective_gap_codes(source_binding.get("required_gap_codes"))
                    if isinstance(source_binding, Mapping)
                    else None
                )
                if (
                    source_required_gap_codes is not None
                    and isinstance(existing, Mapping)
                    and existing.get("state") not in OBJECTIVE_FOLLOWUP_CLOSED_STATES
                    and sorted(source_required_gap_codes)
                    != sorted(existing.get("remaining_gap_codes") or [])
                ):
                    errors.append(
                        "objective_followup_handoff_prior_gap_binding_mismatch"
                    )
                bound_candidates = (
                    [
                        candidate
                        for candidate in accepted_candidates
                        if isinstance(source_binding, Mapping)
                        and candidate.get("candidate_id")
                        == source_binding.get("candidate_id")
                        and candidate.get("candidate_sha256")
                        == source_binding.get("candidate_sha256")
                    ]
                    if isinstance(source_binding, Mapping)
                    else []
                )
                if len(bound_candidates) != 1:
                    errors.append(
                        "objective_followup_bound_candidate_not_accepted_this_run"
                    )
                else:
                    accepted_candidate = bound_candidates[0]
                    queued_source_candidate = accepted_candidate.get("candidate")
                    if not isinstance(queued_source_candidate, Mapping):
                        errors.append(
                            "objective_followup_bound_source_candidate_missing"
                        )
                    else:
                        candidate_binding_errors = _objective_candidate_binding_errors(
                            queued_source_candidate,
                            followup_id=followup_id,
                            expected_resolved_gap_codes=list(
                                source_binding.get("resolved_gap_codes") or []
                            ),
                        )
                        errors.extend(candidate_binding_errors)
                    if not errors:
                        handoff_evidence = {
                            "objective_followup_id": followup_id,
                            "accepted_candidate_queue_key": accepted_candidate.get(
                                "queue_key"
                            ),
                            "accepted_candidate_id": accepted_candidate.get(
                                "candidate_id"
                            ),
                            "accepted_candidate_sha256": accepted_candidate.get(
                                "candidate_sha256"
                            ),
                            "resolved_gap_codes": list(
                                source_binding.get("resolved_gap_codes") or []
                            ),
                            "source_date": as_of_date.isoformat(),
                            "source_path": str(source_path) if source_path else None,
                            "verification": (
                                "same_run_objective_bound_candidate_intake_accepted"
                            ),
                        }
            completion_evidence, completion_errors = (
                _derive_objective_completion_evidence(
                    raw,
                    existing=existing,
                    queue_candidates=queue_candidates,
                )
            )
            errors.extend(completion_errors)
            if errors:
                rejections.append(
                    {"followup_id": followup_id or None, "errors": errors}
                )
                continue
            normalized = _normalized_objective_followup(
                raw,
                source_path=source_path,
                generated=generated,
                existing=existing,
                handoff_evidence=handoff_evidence,
                completion_evidence=completion_evidence,
            )
            if followup_id in by_id:
                entries[entries.index(by_id[followup_id])] = normalized
            else:
                entries.append(normalized)
            by_id[followup_id] = normalized
    output = {
        **dict(queue),
        "objective_followups": sorted(
            entries, key=lambda row: str(row.get("followup_id") or "")
        ),
        "objective_followup_last_sync": {
            "as_of_date": as_of_date.isoformat(),
            "source_path": str(source_path) if source_path else None,
            "source_status": source_status,
            "source_followup_count": len(source_followups),
            "accepted_candidate_count": len(accepted_candidate_keys),
            "rejection_count": len(rejections),
        },
    }
    return output, rejections


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
    as_of: datetime,
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
        if not _artifact_is_newer_than_invalidation(artifact, entry):
            continue
        if str(artifact.get("candidate_sha256") or "") != str(
            entry.get("candidate_sha256") or ""
        ):
            continue
        decision = str(artifact.get("decision") or "")
        if decision not in VALID_DECISIONS:
            continue
        decided_at = _aware_datetime(artifact.get("decided_at_kst"))
        if decided_at is None or decided_at > as_of:
            continue
        if entry.get("state") not in DECISION_ALLOWED_STATES[decision]:
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
        if decision == "approve" and runtime_design_errors(
            candidate, runtime_registry=runtime_registry
        ):
            _invalidate_operator_decision(
                entry,
                invalidated_at=as_of,
                reason="approval_ignored_runtime_design_not_ready",
            )
            entry["state"] = STATE_DESIGN_REQUIRED
            entry["state_reason"] = "approval_ignored_runtime_design_not_ready"
            continue
        entry["operator_decision_artifact"] = str(artifact.get("_artifact_path") or "")
        entry["operator_decision_at_kst"] = artifact.get("decided_at_kst")
        entry["operator_authorization_id"] = artifact.get("operator_authorization_id")
        entry["operator_registry_entry_sha256"] = registry_digest
        entry.pop("operator_decision_invalidated_at_kst", None)
        entry.pop("operator_decision_invalidation_reason", None)
        if decision == "approve":
            entry["state"] = STATE_USER_APPROVED
            entry["state_reason"] = "explicit_operator_approval_recorded"
        elif decision == "hold":
            entry["state"] = STATE_HOLD
            entry["state_reason"] = "explicit_operator_hold_recorded"
        else:
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
        and handoff.get("effective_venue") == design.get("effective_venue")
        and handoff.get("session_bucket") == design.get("session_bucket")
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


def _applied_receipt_time_is_valid(
    receipt: Mapping[str, Any],
    entry: Mapping[str, Any],
    *,
    as_of: datetime,
) -> bool:
    applied_at = _aware_datetime(receipt.get("applied_at_kst"))
    handoff = _load_json(Path(str(entry.get("preopen_handoff") or "")))
    handoff_created_at = _aware_datetime((handoff or {}).get("created_at_kst"))
    try:
        target_date = date.fromisoformat(str(entry.get("preopen_target_date") or ""))
    except ValueError:
        return False
    return bool(
        applied_at is not None
        and handoff_created_at is not None
        and applied_at.date() == target_date
        and applied_at.time() < PREOPEN_HANDOFF_CUTOFF_KST
        and handoff_created_at <= applied_at <= as_of
    )


def _attribution_receipt_time_is_valid(
    receipt: Mapping[str, Any],
    entry: Mapping[str, Any],
    *,
    as_of: datetime,
) -> bool:
    attributed_at = _aware_datetime(receipt.get("attributed_at_kst"))
    source_receipt = _load_json(Path(str(entry.get("family_apply_receipt") or "")))
    applied_at = _aware_datetime((source_receipt or {}).get("applied_at_kst"))
    return bool(
        attributed_at is not None
        and applied_at is not None
        and applied_at <= attributed_at <= as_of
    )


def _apply_family_receipts(
    entries: list[dict[str, Any]],
    receipt_dir: Path,
    *,
    as_of: datetime,
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
        registry_entry = _trusted_registry_entry(
            str(design.get("runtime_family") or ""), runtime_registry
        )
        registry_digest = _registry_entry_sha256(registry_entry)
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
            or not _required_receipt_hash_valid(receipt, registry_entry)
        ):
            continue
        status = str(receipt.get("status") or "")
        if status not in {"applied_guard_passed", "post_apply_attribution_complete"}:
            continue
        family = str(design.get("runtime_family") or "")
        if family == MAIN_AI_QUALITY_RUNTIME_FAMILY:
            suffix = "applied" if status == "applied_guard_passed" else "post_apply"
            canonical = receipt_dir / (
                f"{str(receipt.get('target_date') or '')}_"
                f"{str(entry.get('candidate_sha256') or '')}_{suffix}.json"
            )
            if path.absolute() != canonical.absolute():
                continue
            try:
                from src.engine.automation import (
                    main_ai_quality_runtime_family as main_ai_runtime,
                )
                from src.engine.scalping import main_ai_quality_live_policy

                if status == "applied_guard_passed":
                    activation_path = Path(
                        str(receipt.get("activation_artifact_path") or "")
                    )
                    activation = _load_json(activation_path) or {}
                    if main_ai_runtime.apply_receipt_errors(
                        receipt,
                        activation=activation,
                    ) or main_ai_quality_live_policy.activation_errors(
                        activation,
                        target_date=str(receipt.get("target_date") or ""),
                        selected_path=activation_path,
                        receipt=receipt,
                    ):
                        continue
                else:
                    rolling = _load_json(
                        Path(str(receipt.get("source_rolling_artifact_path") or ""))
                    )
                    if rolling is None:
                        continue
                    main_ai_runtime.validate_post_apply_attribution_receipt(
                        entry=entry,
                        attribution=receipt,
                        attribution_path=path,
                        rolling=rolling,
                        target_date=str(receipt.get("target_date") or ""),
                    )
            except (OSError, TypeError, ValueError):
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
                or (
                    (registry_entry or {}).get("direct_order_authority") is False
                    and receipt.get("broker_order_forbidden") is not True
                )
                or receipt.get("receipt_owner")
                != (registry_entry or {}).get("apply_receipt_owner")
                or not _applied_receipt_time_is_valid(
                    receipt,
                    entry,
                    as_of=as_of,
                )
            ):
                continue
            entry["family_apply_receipt"] = str(path)
            entry["state"] = STATE_APPLIED
        else:
            if (
                receipt.get("runtime_effect") is not False
                or receipt.get("runtime_apply_performed") is not False
                or receipt.get("actual_order_submitted") is not False
                or (
                    (registry_entry or {}).get("direct_order_authority") is False
                    and receipt.get("broker_order_forbidden") is not True
                )
                or receipt.get("post_apply_attribution_complete") is not True
                or receipt.get("receipt_owner")
                != (registry_entry or {}).get("post_apply_attribution_owner")
                or str(receipt.get("source_apply_receipt") or "")
                != str(entry.get("family_apply_receipt") or "")
                or not _attribution_receipt_time_is_valid(
                    receipt,
                    entry,
                    as_of=as_of,
                )
            ):
                continue
            entry["post_apply_attribution_receipt"] = str(path)
            entry["state"] = STATE_POST_APPLY_ATTRIBUTED
        entry["state_reason"] = status
        requires_post_apply = bool(
            (registry_entry or {}).get(
                "requires_post_apply_attribution_before_auto_chain"
            )
        )
        if family and (
            (requires_post_apply and status == "post_apply_attribution_complete")
            or (not requires_post_apply and status == "applied_guard_passed")
        ):
            enrollments[family] = {
                "runtime_family": family,
                "stage": design.get("stage"),
                "axis": design.get("axis"),
                "bounded_contract_sha256": design.get("bounded_contract_sha256"),
                "runtime_registry_entry_sha256": registry_digest,
                "first_approved_queue_key": entry.get("queue_key"),
                "first_apply_receipt": (
                    str(entry.get("family_apply_receipt") or "")
                    if requires_post_apply
                    else str(path)
                ),
                "post_apply_attribution_receipt": (
                    str(path) if requires_post_apply else None
                ),
                "enrolled_after_guarded_apply": True,
                "enrolled_after_post_apply_attribution": requires_post_apply,
            }
    return enrollments


def _validated_existing_enrollments(
    raw_enrollments: Mapping[str, Any],
    entries: Sequence[Mapping[str, Any]],
    *,
    receipt_dir: Path,
    as_of: datetime,
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
        registry_entry = _trusted_registry_entry(str(family), runtime_registry)
        requires_post_apply = bool(
            (registry_entry or {}).get(
                "requires_post_apply_attribution_before_auto_chain"
            )
        )
        if entry is None or entry.get("state") not in (
            {STATE_POST_APPLY_ATTRIBUTED}
            if requires_post_apply
            else {STATE_APPLIED, STATE_POST_APPLY_ATTRIBUTED}
        ):
            continue
        candidate = entry.get("candidate") or {}
        design = candidate.get("runtime_design") or {}
        registry_digest = _registry_entry_sha256(registry_entry)
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
            or (
                (registry_entry or {}).get("direct_order_authority") is False
                and receipt.get("broker_order_forbidden") is not True
            )
            or receipt.get("receipt_owner")
            != (registry_entry or {}).get("apply_receipt_owner")
            or receipt.get("same_stage_owner_conflict_free") is not True
            or receipt.get("hard_safety_and_broker_guards_preserved") is not True
            or not _required_receipt_hash_valid(receipt, registry_entry)
            or not _applied_receipt_time_is_valid(
                receipt,
                entry,
                as_of=as_of,
            )
        ):
            continue
        if str(family) == MAIN_AI_QUALITY_RUNTIME_FAMILY:
            expected_apply_path = receipt_dir / (
                f"{str(receipt.get('target_date') or '')}_"
                f"{str(entry.get('candidate_sha256') or '')}_applied.json"
            )
            if receipt_path.absolute() != expected_apply_path.absolute():
                continue
            try:
                from src.engine.automation import (
                    main_ai_quality_runtime_family as main_ai_runtime,
                )
                from src.engine.scalping import main_ai_quality_live_policy

                activation_path = Path(
                    str(receipt.get("activation_artifact_path") or "")
                )
                activation = _load_json(activation_path) or {}
                if main_ai_runtime.apply_receipt_errors(
                    receipt,
                    activation=activation,
                ) or main_ai_quality_live_policy.activation_errors(
                    activation,
                    target_date=str(receipt.get("target_date") or ""),
                    selected_path=activation_path,
                    receipt=receipt,
                ):
                    continue
            except (OSError, TypeError, ValueError):
                continue
        if requires_post_apply:
            if raw.get("enrolled_after_post_apply_attribution") is not True:
                continue
            attribution_path = Path(
                str(raw.get("post_apply_attribution_receipt") or "")
            )
            try:
                attribution_path.resolve().relative_to(receipt_root)
            except (OSError, ValueError):
                continue
            attribution = _load_json(attribution_path)
            if (
                not attribution
                or attribution.get("schema") != APPLY_RECEIPT_SCHEMA
                or attribution.get("status") != "post_apply_attribution_complete"
                or attribution.get("queue_key") != entry.get("queue_key")
                or attribution.get("candidate_sha256") != entry.get("candidate_sha256")
                or attribution.get("source_apply_receipt") != str(receipt_path)
                or attribution.get("post_apply_attribution_complete") is not True
                or attribution.get("runtime_effect") is not False
                or attribution.get("runtime_apply_performed") is not False
                or attribution.get("actual_order_submitted") is not False
                or (
                    (registry_entry or {}).get("direct_order_authority") is False
                    and attribution.get("broker_order_forbidden") is not True
                )
                or attribution.get("receipt_owner")
                != (registry_entry or {}).get("post_apply_attribution_owner")
                or not _required_receipt_hash_valid(attribution, registry_entry)
                or not _attribution_receipt_time_is_valid(
                    attribution,
                    entry,
                    as_of=as_of,
                )
            ):
                continue
            if str(family) == MAIN_AI_QUALITY_RUNTIME_FAMILY:
                expected_attribution_path = receipt_dir / (
                    f"{str(attribution.get('target_date') or '')}_"
                    f"{str(entry.get('candidate_sha256') or '')}_post_apply.json"
                )
                if attribution_path.absolute() != expected_attribution_path.absolute():
                    continue
                try:
                    rolling = _load_json(
                        Path(str(attribution.get("source_rolling_artifact_path") or ""))
                    )
                    if rolling is None:
                        continue
                    main_ai_runtime.validate_post_apply_attribution_receipt(
                        entry=entry,
                        attribution=attribution,
                        attribution_path=attribution_path,
                        rolling=rolling,
                        target_date=str(attribution.get("target_date") or ""),
                    )
                except (OSError, TypeError, ValueError):
                    continue
        validated[str(family)] = dict(raw)
    return validated


_FRESH_SOURCE_REVALIDATION_STATES = {
    STATE_DESIGN_REQUIRED,
    STATE_REVIEW_READY,
    STATE_USER_APPROVED,
    STATE_PREOPEN_MISSED_REVIEW_REQUIRED,
    STATE_REVALIDATION_REQUIRED,
    STATE_AUTO_CHAIN_ELIGIBLE,
    STATE_HOLD,
}


def _mark_missed_preopen_handoffs(
    entries: Sequence[dict[str, Any]],
    *,
    as_of_date: date,
    now: datetime,
) -> None:
    for entry in entries:
        if entry.get("state") != STATE_PREOPEN_SCHEDULED:
            continue
        try:
            target_date = date.fromisoformat(
                str(entry.get("preopen_target_date") or "")
            )
        except ValueError:
            target_date = date.min
        if target_date >= as_of_date:
            continue
        history = list(entry.get("missed_preopen_handoffs") or ())
        history.append(
            {
                "target_date": entry.get("preopen_target_date"),
                "handoff": entry.get("preopen_handoff"),
                "authorization_mode": entry.get("authorization_mode"),
                "marked_missed_at_kst": now.isoformat(timespec="seconds"),
            }
        )
        entry["missed_preopen_handoffs"] = history
        _invalidate_operator_decision(
            entry,
            invalidated_at=now,
            reason="exact_date_preopen_handoff_missed",
        )
        for field in (
            "preopen_handoff",
            "preopen_target_date",
            "authorization_mode",
        ):
            entry.pop(field, None)
        entry["state"] = STATE_PREOPEN_MISSED_REVIEW_REQUIRED
        entry["state_reason"] = (
            "exact_date_preopen_handoff_missed_explicit_redecision_required"
        )


def _revalidate_entries_against_fresh_source(
    entries: Sequence[dict[str, Any]],
    *,
    source_status: str,
    accepted_queue_keys: set[str],
    raw_candidate_ids: set[str],
    rejected_candidate_ids: set[str],
    now: datetime,
) -> None:
    if source_status != "loaded":
        return
    for entry in entries:
        if entry.get("state") not in _FRESH_SOURCE_REVALIDATION_STATES:
            continue
        queue_key = str(entry.get("queue_key") or "")
        if queue_key in accepted_queue_keys:
            continue
        candidate_id = str(entry.get("candidate_id") or "")
        reason = (
            "fresh_source_candidate_rejected_revalidation_required"
            if candidate_id in rejected_candidate_ids
            else (
                "fresh_source_candidate_withdrawn_revalidation_required"
                if candidate_id not in raw_candidate_ids
                else "fresh_source_candidate_version_not_accepted_revalidation_required"
            )
        )
        if entry.get("state") != STATE_REVALIDATION_REQUIRED:
            _invalidate_operator_decision(
                entry,
                invalidated_at=now,
                reason=reason,
            )
        entry["state"] = STATE_REVALIDATION_REQUIRED
        entry["state_reason"] = reason


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
    # Reconcile a family-owned apply receipt before a fresh daily candidate can
    # supersede the scheduled version that was actually applied that morning.
    # Otherwise the normal source-date/hash refresh can make the receipt
    # unreachable and silently lose both APPLIED state and family enrollment.
    family_enrollments = _validated_existing_enrollments(
        queue.get("family_enrollments") or {},
        entries,
        receipt_dir=apply_receipt_dir,
        as_of=generated,
        runtime_registry=runtime_registry,
    )
    new_enrollments = _apply_family_receipts(
        entries,
        apply_receipt_dir,
        as_of=generated,
        runtime_registry=runtime_registry,
    )
    family_enrollments.update(new_enrollments)
    by_key = {str(entry.get("queue_key") or ""): entry for entry in entries}
    intake_rejections: list[dict[str, Any]] = []
    accepted_queue_keys: set[str] = set()
    raw_candidate_ids: set[str] = set()
    rejected_candidate_ids: set[str] = set()
    for raw_candidate in source_candidates:
        candidate = dict(raw_candidate)
        raw_candidate_id = str(candidate.get("candidate_id") or "").strip()
        if raw_candidate_id:
            raw_candidate_ids.add(raw_candidate_id)
        errors = evidence_readiness_errors(candidate)
        if str(candidate.get("source_date") or "") != as_of_date.isoformat():
            errors.append("candidate_source_date_not_as_of_date")
        if errors:
            if raw_candidate_id:
                rejected_candidate_ids.add(raw_candidate_id)
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
            if raw_candidate_id:
                rejected_candidate_ids.add(raw_candidate_id)
            intake_rejections.append(
                {
                    "candidate_id": candidate.get("candidate_id"),
                    "errors": ["candidate_sha256_mismatch"],
                }
            )
            continue
        candidate["candidate_sha256"] = digest
        candidate_id = str(candidate["candidate_id"])
        key = _queue_key(candidate_id, digest)
        collided = by_key.get(key)
        if collided is not None and collided.get("candidate_sha256") != digest:
            rejected_candidate_ids.add(candidate_id)
            intake_rejections.append(
                {
                    "candidate_id": candidate_id,
                    "errors": ["candidate_sha256_prefix_collision"],
                }
            )
            continue
        accepted_queue_keys.add(key)
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
            if entry.get("state") == STATE_REVALIDATION_REQUIRED:
                _invalidate_operator_decision(
                    entry,
                    invalidated_at=generated,
                    reason=("fresh_source_candidate_revalidated_new_decision_required"),
                )
                entry["state"] = (
                    STATE_DESIGN_REQUIRED if design_errors else STATE_REVIEW_READY
                )
                entry["state_reason"] = (
                    "fresh_source_candidate_revalidated_runtime_design_required"
                    if design_errors
                    else "fresh_source_candidate_revalidated_review_ready"
                )
            elif entry.get("state") == STATE_DESIGN_REQUIRED and not design_errors:
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

    _mark_missed_preopen_handoffs(
        entries,
        as_of_date=as_of_date,
        now=generated,
    )
    for entry in entries:
        if entry.get("state") in EXPIRABLE_STATES and _entry_expired(
            entry, as_of_date=as_of_date
        ):
            entry["state"] = STATE_EXPIRED
            entry["state_reason"] = "evidence_validity_expired_revalidation_required"
    _apply_operator_decisions(
        entries,
        approval_artifacts,
        as_of=generated,
        runtime_registry=runtime_registry,
    )
    _revalidate_entries_against_fresh_source(
        entries,
        source_status=source_status,
        accepted_queue_keys=accepted_queue_keys,
        raw_candidate_ids=raw_candidate_ids,
        rejected_candidate_ids=rejected_candidate_ids,
        now=generated,
    )
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
            "accepted_candidate_count": len(accepted_queue_keys),
            "accepted_candidate_queue_keys": sorted(accepted_queue_keys),
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
    apply_receipt_dir: Path = APPLY_RECEIPT_DIR,
    now: datetime | None = None,
    runtime_registry: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[dict[str, Any], Path]:
    if decision not in VALID_DECISIONS:
        raise ValueError("operator_decision_invalid")
    if not operator_authorization_id.strip() or not operator_instruction.strip():
        raise ValueError("explicit_operator_authority_missing")
    requested_at = _now_kst(now)
    queue, _ = sync_queue(
        queue,
        source_candidates=(),
        source_path=None,
        as_of_date=requested_at.date(),
        now=requested_at,
        apply_receipt_dir=apply_receipt_dir,
        runtime_registry=runtime_registry,
    )
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
    if _entry_expired(entry, as_of_date=requested_at.date()):
        raise ValueError("candidate_evidence_expired")
    if state not in DECISION_ALLOWED_STATES[decision]:
        reason = {
            "approve": "candidate_not_approval_ready",
            "hold": "candidate_not_holdable",
            "reject": "candidate_not_rejectable",
        }[decision]
        raise ValueError(f"{reason}:{state}")
    if decision == "approve":
        design_errors = runtime_design_errors(
            entry.get("candidate") or {}, runtime_registry=runtime_registry
        )
        if design_errors:
            raise ValueError("runtime_design_not_ready:" + ",".join(design_errors))
    decision_time = requested_at
    invalidated_at = _aware_datetime(entry.get("operator_decision_invalidated_at_kst"))
    if invalidated_at is not None and decision_time <= invalidated_at:
        # The persisted timestamps used to have second precision.  Preserve a
        # strict causal ordering even when an operator re-decides in the same
        # wall-clock second as the invalidation instead of silently ignoring
        # the newly written artifact.
        decision_time = invalidated_at + timedelta(microseconds=1)
    decided_at = decision_time.isoformat(timespec="microseconds")
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
    updated, _ = sync_queue(
        queue,
        source_candidates=(),
        source_path=None,
        as_of_date=decision_time.date(),
        now=decision_time,
        approval_artifacts=[{**artifact, "_artifact_path": str(path)}],
        apply_receipt_dir=apply_receipt_dir,
        runtime_registry=runtime_registry,
    )
    expected_state = {
        "approve": STATE_USER_APPROVED,
        "hold": STATE_HOLD,
        "reject": STATE_REJECTED,
    }[decision]
    updated_matches = [
        row
        for row in updated.get("candidates", [])
        if isinstance(row, Mapping)
        and row.get("candidate_id") == candidate_id
        and row.get("candidate_sha256") == expected_candidate_sha256
    ]
    if (
        len(updated_matches) != 1
        or updated_matches[0].get("state") != expected_state
        or updated_matches[0].get("operator_authorization_id")
        != operator_authorization_id.strip()
        or updated_matches[0].get("operator_decision_at_kst") != decided_at
    ):
        raise ValueError("operator_decision_not_applied_after_receipt_reconciliation")
    _atomic_write_json(path, artifact)
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
    if generated.date() != target_date:
        raise ValueError("preopen_handoff_target_date_not_generated_kst_date")
    if not is_krx_trading_day(target_date):
        raise ValueError("preopen_handoff_target_date_not_krx_trading_day")
    # The scheduled automation runs at 07:35 KST.  Preserve that valid path,
    # but never mint an apply-authorizing handoff after any supported venue
    # could already be trading; venue/cohort is not a trusted registry field.
    if generated.time() >= PREOPEN_HANDOFF_CUTOFF_KST:
        raise ValueError("preopen_handoff_generated_at_or_after_market_open_cutoff")
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
        if family == MAIN_AI_QUALITY_RUNTIME_FAMILY:
            # This registry entry is retained for archive/receipt compatibility,
            # but its legacy prompt runtime authority is explicitly retired.
            # The generic scheduler must not publish a positive apply handoff
            # that a downstream consumer later has to reject.
            from src.engine.scalping import main_ai_quality_live_policy

            if not main_ai_quality_live_policy.LEGACY_RUNTIME_AUTHORITY_ENABLED:
                entry["state"] = STATE_DESIGN_REQUIRED
                entry["state_reason"] = (
                    "preopen_blocked_runtime_family_authority_disabled"
                )
                entry["runtime_design_errors"] = [
                    "legacy_main_ai_quality_runtime_authority_disabled"
                ]
                continue
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
                or (
                    (_trusted_registry_entry(family, runtime_registry) or {}).get(
                        "requires_post_apply_attribution_before_auto_chain"
                    )
                    is True
                    and enrollment.get("enrolled_after_post_apply_attribution")
                    is not True
                )
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
            "effective_venue": design.get("effective_venue"),
            "session_bucket": design.get("session_bucket"),
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
    entries: Sequence[Mapping[str, Any]],
    *,
    phase: str,
    target_date: date,
    objective_followups: Sequence[Mapping[str, Any]] = (),
) -> str:
    lines = [
        "🔔 [Micro 정책 후속 확인]",
        f"기준: {target_date.isoformat()} {phase.upper()}",
        "이 알림은 정책·주문을 변경하지 않고 연구 후속과 승인 상태만 추적합니다.",
    ]
    if objective_followups:
        lines.extend(["", "[빠른 회전 목표 후속]"])
        for index, followup in enumerate(objective_followups[:5], start=1):
            lines.append(
                f"R{index}. {followup.get('followup_id')} [{followup.get('state')}]"
            )
            lines.append(
                f"   current={followup.get('current_capability') or 'diagnostic_only'}"
            )
            gap_codes = followup.get("remaining_gap_codes") or []
            if gap_codes:
                lines.append("   gaps=" + ",".join(str(value) for value in gap_codes))
            lines.append(f"   next={followup.get('next_action') or '-'}")
        if len(objective_followups) > 5:
            lines.append(f"연구 후속 외 {len(objective_followups) - 5}건")
    if entries:
        lines.extend(["", "[정책 후보 승인 대기]"])
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
        lines.append(f"정책 후보 외 {len(entries) - 5}건")
    lines.append(
        "후속은 source-only 연구로 닫고, 실제 정책은 별도 설계·명시 승인·"
        "exact-date PREOPEN·사후 귀속 전까지 그대로 유지합니다."
    )
    return "\n".join(lines)


def notify_pending(
    queue: Mapping[str, Any],
    *,
    phase: str,
    target_date: date,
    include_objective_followups: bool = False,
    now: datetime | None = None,
    config_loader: ConfigLoader | None = None,
    sender: Sender | None = None,
) -> tuple[dict[str, Any], str]:
    if phase not in VALID_PHASES:
        raise ValueError("phase_invalid")
    generated = _now_kst(now)
    entries = [
        dict(row) for row in queue.get("candidates", []) if isinstance(row, dict)
    ]
    objective_followups = [
        dict(row)
        for row in queue.get("objective_followups", [])
        if isinstance(row, Mapping)
    ]
    pending_candidates = [
        row
        for row in entries
        if row.get("state") in REMINDER_STATES
        and (row.get("reminders") or {}).get(phase) != target_date.isoformat()
    ]
    pending_followups = (
        [
            row
            for row in objective_followups
            if row.get("followup_required") is True
            and row.get("state") not in OBJECTIVE_FOLLOWUP_CLOSED_STATES
            and (row.get("reminders") or {}).get("postclose") != target_date.isoformat()
        ]
        if (
            include_objective_followups
            and phase == "postclose"
            and target_date == generated.date()
            and is_krx_trading_day(target_date)
            and generated.timetz().replace(tzinfo=None)
            >= OBJECTIVE_FOLLOWUP_REMINDER_CUTOFF_KST
        )
        else []
    )
    if not pending_candidates and not pending_followups:
        return {
            **dict(queue),
            "candidates": entries,
            "objective_followups": objective_followups,
        }, "not_needed_or_duplicate"
    config_loader = config_loader or _load_telegram_config
    sender = sender or _send_telegram
    token, admin_id = config_loader()
    if not token or not admin_id:
        return {
            **dict(queue),
            "candidates": entries,
            "objective_followups": objective_followups,
        }, "missing_config"
    try:
        sender(
            token,
            admin_id,
            build_reminder_message(
                pending_candidates,
                phase=phase,
                target_date=target_date,
                objective_followups=pending_followups,
            ),
        )
    except Exception:
        return {
            **dict(queue),
            "candidates": entries,
            "objective_followups": objective_followups,
        }, "send_failed"
    pending_keys = {str(row.get("queue_key") or "") for row in pending_candidates}
    for entry in entries:
        if str(entry.get("queue_key") or "") in pending_keys:
            reminders = dict(entry.get("reminders") or {})
            reminders[phase] = target_date.isoformat()
            entry["reminders"] = reminders
    pending_followup_ids = {
        str(row.get("followup_id") or "") for row in pending_followups
    }
    for followup in objective_followups:
        if str(followup.get("followup_id") or "") in pending_followup_ids:
            reminders = dict(followup.get("reminders") or {})
            reminders["postclose"] = target_date.isoformat()
            followup["reminders"] = reminders
    return {
        **dict(queue),
        "candidates": entries,
        "objective_followups": objective_followups,
    }, "sent"


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
    objective_followup_source_status: str = "not_provided",
    handoff_paths: Sequence[Path] = (),
    objective_followup_rejections: Sequence[Mapping[str, Any]] = (),
    source_artifact: Mapping[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    entries = [row for row in queue.get("candidates", []) if isinstance(row, Mapping)]
    counts = Counter(str(row.get("state") or "UNKNOWN") for row in entries)
    actionable = [row for row in entries if row.get("state") in REMINDER_STATES]
    objective_followups = [
        row for row in queue.get("objective_followups", []) if isinstance(row, Mapping)
    ]
    actionable_objective_followups = (
        [
            row
            for row in objective_followups
            if row.get("followup_required") is True
            and row.get("state") not in OBJECTIVE_FOLLOWUP_CLOSED_STATES
        ]
        if phase == "postclose"
        else []
    )
    decision = (
        "operator_attention_required"
        if actionable
        else (
            "objective_followup_required"
            if actionable_objective_followups
            else (
                "objective_followup_contract_rejected"
                if objective_followup_rejections
                else (
                    "source_gap_queue_preserved"
                    if source_status
                    not in {"loaded", "not_applicable_preopen", "not_provided"}
                    else "no_operator_attention_required"
                )
            )
        )
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
        "source_artifact": (
            dict(source_artifact)
            if isinstance(source_artifact, Mapping)
            else _empty_source_artifact_provenance(source_path)
        ),
        "source_status": source_status,
        "objective_followup_source_status": objective_followup_source_status,
        "queue_path": str(queue_path),
        "summary": {
            "candidate_count": len(entries),
            "actionable_candidate_count": len(actionable),
            "objective_followup_count": len(objective_followups),
            "actionable_objective_followup_count": len(actionable_objective_followups),
            "state_counts": dict(sorted(counts.items())),
            "intake_rejection_count": len(intake_rejections),
            "objective_followup_rejection_count": len(objective_followup_rejections),
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
        "objective_followups": [
            {
                "schema": row.get("schema"),
                "followup_id": row.get("followup_id"),
                "source_date": row.get("source_date"),
                "state": row.get("state"),
                "state_reason": row.get("state_reason"),
                "followup_required": row.get("followup_required"),
                "attention_class": row.get("attention_class"),
                "operator_decision_required": False,
                "current_capability": row.get("current_capability"),
                "remaining_gap_codes": list(row.get("remaining_gap_codes") or []),
                "next_action": row.get("next_action"),
                "metric_contract": dict(row.get("metric_contract") or {}),
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "authority": {
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
            }
            for row in actionable_objective_followups
        ],
        "intake_rejections": list(intake_rejections),
        "objective_followup_rejections": list(objective_followup_rejections),
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
        (
            "- Objective follow-up source status: "
            f"`{report.get('objective_followup_source_status')}`"
        ),
        f"- Actionable: `{summary.get('actionable_candidate_count', 0)}`",
        (
            "- Objective follow-ups: "
            f"`{summary.get('actionable_objective_followup_count', 0)}`"
        ),
        (
            "- Objective follow-up rejections: "
            f"`{summary.get('objective_followup_rejection_count', 0)}`"
        ),
        f"- Reminder: `{summary.get('reminder_status')}`",
        "- Runtime apply performed: `false`",
        "",
        "## Fast Lifecycle Objective Follow-up",
        "",
    ]
    objective_rows = report.get("objective_followups") or []
    if not objective_rows:
        lines.append("- None")
    else:
        lines.extend(
            [
                "| Follow-up | State | Current capability | Gaps | Next action |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for row in objective_rows:
            lines.append(
                f"| {row.get('followup_id')} | {row.get('state')} | "
                f"{row.get('current_capability') or '-'} | "
                f"{','.join(row.get('remaining_gap_codes') or []) or '-'} | "
                f"{row.get('next_action') or '-'} |"
            )
    lines.extend(
        [
            "",
            "Objective follow-ups are research/workorder reminders only. They cannot be "
            "approved, scheduled, enrolled, or applied as runtime policy.",
            "",
            "## Pending",
            "",
        ]
    )
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


def _load_source_payload_snapshot(
    *, target_date: date, source_report: Path | None
) -> tuple[Path, dict[str, Any] | None, str, dict[str, Any]]:
    path = source_report or SOURCE_REPORT_DIR / (
        f"machine_microstructure_attribution_{target_date.isoformat()}.json"
    )
    payload, source_artifact, capture_status = _capture_source_artifact(path)
    if payload is None:
        return path, None, capture_status, source_artifact
    if (
        payload.get("schema") != "machine_microstructure_attribution_v1"
        or payload.get("target_date") != target_date.isoformat()
        or (payload.get("authority") or {}).get("runtime_effect") is not False
        or (payload.get("authority") or {}).get("allowed_runtime_apply") is not False
        or (payload.get("authority") or {}).get("actual_order_submitted") is not False
        or (payload.get("authority") or {}).get("broker_order_forbidden") is not True
    ):
        return path, None, "contract_invalid", source_artifact
    return path, payload, "loaded", source_artifact


def _load_source_payload(
    *, target_date: date, source_report: Path | None
) -> tuple[Path, dict[str, Any] | None, str]:
    """Compatibility wrapper for payload-only callers and tests."""

    path, payload, status, _source_artifact = _load_source_payload_snapshot(
        target_date=target_date,
        source_report=source_report,
    )
    return path, payload, status


def _candidate_rows_from_source_payload(
    payload: Mapping[str, Any],
) -> tuple[list[Mapping[str, Any]], str]:
    intake_contract = payload.get("promotion_candidate_intake_contract")
    if (
        not isinstance(intake_contract, Mapping)
        or intake_contract.get("schema") != CANDIDATE_SCHEMA
        or intake_contract.get("consumer")
        != "src.engine.automation.machine_microstructure_policy_approval"
        or intake_contract.get("daily_report_runtime_effect") is not False
    ):
        return [], "intake_contract_invalid"
    rows = payload.get("policy_promotion_candidates")
    if not isinstance(rows, list):
        return [], "candidate_list_missing_or_invalid"
    if any(not isinstance(row, Mapping) for row in rows):
        return [], "candidate_rows_invalid"
    return list(rows), "loaded"


def _load_source_candidates(
    *, target_date: date, source_report: Path | None
) -> tuple[Path, list[Mapping[str, Any]], str]:
    """Compatibility loader for candidate-only callers and tests."""

    path, payload, status = _load_source_payload(
        target_date=target_date,
        source_report=source_report,
    )
    if payload is None:
        return path, [], status
    rows, candidate_status = _candidate_rows_from_source_payload(payload)
    return path, rows, candidate_status


def _objective_rows_from_source_payload(
    payload: Mapping[str, Any], *, target_date: date
) -> tuple[list[Mapping[str, Any]], str, list[dict[str, Any]]]:
    raw_rows = payload.get("objective_followups")
    if not isinstance(raw_rows, list):
        return (
            [],
            "objective_followup_list_missing_or_invalid",
            [
                {
                    "followup_id": None,
                    "errors": ["objective_followup_list_missing_or_invalid"],
                }
            ],
        )
    rows: list[Mapping[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    followup_id_counts = Counter(
        str(raw.get("followup_id") or "").strip()
        for raw in raw_rows
        if isinstance(raw, Mapping)
    )
    for raw in raw_rows:
        if not isinstance(raw, Mapping):
            rejections.append(
                {
                    "followup_id": None,
                    "errors": ["objective_followup_row_not_object"],
                }
            )
            continue
        errors = objective_followup_errors(raw, target_date=target_date)
        followup_id = str(raw.get("followup_id") or "").strip()
        if followup_id and followup_id_counts[followup_id] != 1:
            errors.append("objective_followup_id_duplicate")
        if errors:
            rejections.append(
                {
                    "followup_id": followup_id or None,
                    "errors": errors,
                }
            )
            continue
        rows.append(raw)
    return rows, "loaded", rejections


def _load_source_context_snapshot(
    *, target_date: date, source_report: Path | None
) -> tuple[
    Path,
    list[Mapping[str, Any]],
    list[Mapping[str, Any]],
    str,
    str,
    list[dict[str, Any]],
    dict[str, Any],
]:
    path, payload, status, source_artifact = _load_source_payload_snapshot(
        target_date=target_date,
        source_report=source_report,
    )
    if payload is None:
        return path, [], [], status, status, [], source_artifact
    candidates, candidate_status = _candidate_rows_from_source_payload(payload)
    objective_followups, objective_status, rejections = (
        _objective_rows_from_source_payload(
            payload,
            target_date=target_date,
        )
    )
    return (
        path,
        candidates,
        objective_followups,
        candidate_status,
        objective_status,
        rejections,
        source_artifact,
    )


def _load_source_context(*, target_date: date, source_report: Path | None) -> tuple[
    Path,
    list[Mapping[str, Any]],
    list[Mapping[str, Any]],
    str,
    str,
    list[dict[str, Any]],
]:
    """Compatibility wrapper for source-context callers and tests."""

    (
        path,
        candidates,
        objective_followups,
        candidate_status,
        objective_status,
        rejections,
        _source_artifact,
    ) = _load_source_context_snapshot(
        target_date=target_date,
        source_report=source_report,
    )
    return (
        path,
        candidates,
        objective_followups,
        candidate_status,
        objective_status,
        rejections,
    )


@contextmanager
def _queue_lock(queue_path: Path) -> Iterator[ArtifactGenerationLease]:
    with json_artifact_generation_lock(
        queue_path,
        exclusive=True,
        blocking=True,
    ) as generation:
        yield generation


def _run_phase(args: argparse.Namespace) -> dict[str, Any]:
    target_date = date.fromisoformat(args.target_date)
    generated = _now_kst()
    if args.phase == "postclose" and target_date > generated.date():
        raise ValueError("postclose_target_date_in_future")
    source_path: Path | None = None
    source_candidates: list[Mapping[str, Any]] = []
    source_objective_followups: list[Mapping[str, Any]] = []
    objective_followup_rejections: list[dict[str, Any]] = []
    source_status = "not_applicable_preopen"
    objective_followup_source_status = "not_applicable_preopen"
    source_artifact = _empty_source_artifact_provenance(None)
    if args.phase == "postclose":
        (
            source_path,
            source_candidates,
            source_objective_followups,
            source_status,
            objective_followup_source_status,
            objective_followup_rejections,
            source_artifact,
        ) = _load_source_context_snapshot(
            target_date=target_date, source_report=args.source_report
        )
    with _queue_lock(args.queue_path) as queue_generation:
        if (
            not args.queue_path.exists()
            and source_status != "loaded"
            and objective_followup_source_status != "loaded"
        ):
            raise ValueError("approval_queue_and_source_unavailable")
        queue = load_queue(args.queue_path, generation=queue_generation)
        queue, rejections = sync_queue(
            queue,
            source_candidates=source_candidates,
            source_path=source_path,
            as_of_date=target_date,
            source_status=source_status,
            approval_artifacts=_approval_artifacts(args.approval_dir),
            apply_receipt_dir=args.apply_receipt_dir,
            now=generated,
        )
        accepted_candidate_queue_keys = (queue.get("last_sync") or {}).get(
            "accepted_candidate_queue_keys"
        ) or []
        queue, sync_followup_rejections = sync_objective_followups(
            queue,
            source_followups=source_objective_followups,
            source_path=source_path,
            as_of_date=target_date,
            source_status=objective_followup_source_status,
            accepted_candidate_queue_keys=accepted_candidate_queue_keys,
            now=generated,
        )
        objective_followup_rejections.extend(sync_followup_rejections)
        if (
            args.phase == "postclose"
            and args.write
            and source_path is not None
            and not _source_artifact_snapshot_is_current(source_path, source_artifact)
        ):
            raise ValueError("source_artifact_changed_before_commit")
        handoff_paths: list[Path] = []
        if args.phase == "preopen":
            queue, handoff_paths = schedule_preopen_handoffs(
                queue,
                target_date=target_date,
                handoff_dir=args.handoff_dir,
                now=generated,
            )
        reminder_status = "not_requested"
        if args.notify:
            queue, reminder_status = notify_pending(
                queue,
                phase=args.phase,
                target_date=target_date,
                include_objective_followups=getattr(
                    args, "notify_objective_followups", False
                ),
                now=generated,
            )
        report = build_status_report(
            queue,
            phase=args.phase,
            target_date=target_date,
            source_path=source_path,
            queue_path=args.queue_path,
            source_status=source_status,
            objective_followup_source_status=objective_followup_source_status,
            intake_rejections=rejections,
            reminder_status=reminder_status,
            handoff_paths=handoff_paths,
            objective_followup_rejections=objective_followup_rejections,
            source_artifact=source_artifact,
            now=generated,
        )
        if args.write:
            if (
                args.phase == "postclose"
                and source_path is not None
                and not _source_artifact_snapshot_is_current(
                    source_path, source_artifact
                )
            ):
                raise ValueError("source_artifact_changed_before_commit")
            _atomic_write_json(
                args.queue_path,
                queue,
                generation=queue_generation,
            )
            json_path, md_path = status_report_paths(
                target_date=target_date,
                phase=args.phase,
                report_dir=args.report_dir,
            )
            _atomic_write_json(json_path, report)
            _atomic_write_text(md_path, render_status_markdown(report))
        return report


def _record_decision(args: argparse.Namespace) -> dict[str, Any]:
    with _queue_lock(args.queue_path) as queue_generation:
        queue = load_queue(args.queue_path, generation=queue_generation)
        queue, artifact_path = record_operator_decision(
            queue,
            candidate_id=args.candidate_id,
            expected_candidate_sha256=args.candidate_sha256,
            decision=args.record_decision,
            operator_authorization_id=args.operator_authorization_id,
            operator_instruction=args.operator_instruction,
            approval_dir=args.approval_dir,
            apply_receipt_dir=args.apply_receipt_dir,
        )
        _atomic_write_json(
            args.queue_path,
            queue,
            generation=queue_generation,
        )
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
    parser.add_argument("--target-date")
    parser.add_argument("--source-report", type=Path)
    parser.add_argument("--queue-path", type=Path, default=DEFAULT_QUEUE_PATH)
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--approval-dir", type=Path, default=APPROVAL_DIR)
    parser.add_argument("--handoff-dir", type=Path, default=HANDOFF_DIR)
    parser.add_argument("--apply-receipt-dir", type=Path, default=APPLY_RECEIPT_DIR)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--notify", action="store_true")
    parser.add_argument("--notify-objective-followups", action="store_true")
    parser.add_argument("--record-decision", choices=sorted(VALID_DECISIONS))
    parser.add_argument("--candidate-id", default="")
    parser.add_argument("--candidate-sha256", default="")
    parser.add_argument("--operator-authorization-id", default="")
    parser.add_argument("--operator-instruction", default="")
    args = parser.parse_args(argv)
    if not args.target_date:
        args.target_date = (
            resolve_completed_machine_target_date().isoformat()
            if args.phase == "postclose"
            else _now_kst().date().isoformat()
        )
    try:
        date.fromisoformat(args.target_date)
        if args.notify and not args.write:
            raise ValueError("notify_requires_write")
        if args.notify_objective_followups and not args.notify:
            raise ValueError("notify_objective_followups_requires_notify")
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
    if args.notify_objective_followups and (result.get("summary") or {}).get(
        "reminder_status"
    ) in {"missing_config", "send_failed"}:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
