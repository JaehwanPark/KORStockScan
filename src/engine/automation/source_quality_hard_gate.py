from __future__ import annotations

import copy
import json
import gzip
import hashlib
from functools import lru_cache
from pathlib import Path
from collections.abc import Callable
from typing import Any

from src.engine.automation.source_quality_clean_baseline import (
    clean_baseline_policy,
    is_date_allowed,
)
from src.engine.daily_threshold_cycle_report import REPORT_DIR
from src.utils.jsonl_io import read_json_object_strict

BLOCKED_STATUS = "source_quality_blocked"
BLOCKED_GATE = "blocked_contract_gap"
RUNTIME_CANDIDATE_LIST_FIELDS = {
    "runtime_approval_candidates",
    "approval_requests",
    "surfaced_live_auto_candidates",
    "live_auto_apply_ready_candidates",
    "selected",
    "approved_requests",
    "auto_apply_selected",
}
RUNTIME_CANDIDATE_COUNT_FIELDS = {
    "allowed_runtime_apply_candidate_count",
    "live_auto_apply_ready_count",
    "runtime_candidate_count",
    "runtime_approval_candidate_count",
    "scalping_selected_auto_bounded_live",
    "selected_count",
    "approved",
}
RUNTIME_APPLY_BOOL_FIELDS = {
    "allowed_runtime_apply",
    "runtime_effect",
    "runtime_change",
    "selected_auto_bounded_live",
    "runtime_mutation_allowed",
    "threshold_env_mutation_allowed",
    "env_apply_allowed",
    "preopen_apply_allowed",
}


def observation_source_quality_audit_path(target_date: str) -> Path:
    return (
        REPORT_DIR
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json"
    )


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


def _compact_raw_row_exclusion(raw_row_exclusion: Any) -> dict[str, Any]:
    if not isinstance(raw_row_exclusion, dict) or not raw_row_exclusion:
        return {}
    compact: dict[str, Any] = {}
    for key in (
        "manifest_path",
        "backup_path",
        "excluded_row_count",
        "stage_counts",
        "field_gap_counts",
        "exclusion_reasons",
        "first_timestamp",
        "last_timestamp",
        "producer_hint",
        "policy",
        "market_halt_or_circuit_window_overlap",
        "market_halt_or_circuit_context",
    ):
        value = raw_row_exclusion.get(key)
        if value in (None, "", [], {}):
            continue
        compact[key] = value
    return compact


@lru_cache(maxsize=64)
def _archived_raw_digest(
    path: str, device: int, inode: int, size: int, mtime: int
) -> str:
    """Only compressed-generation migration needs a logical-byte recheck."""
    digest = hashlib.sha256()
    with gzip.open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _archive_matches_source(archived: Path, source: dict, current: dict) -> bool:
    """Use the verified archiver receipt; legacy migrations have a bounded-memory fallback."""
    try:
        receipt = json.loads(
            Path(f"{archived}.archive_receipt.json").read_text(encoding="utf-8")
        )
        if (
            isinstance(receipt, dict)
            and receipt.get("schema") == "pipeline_raw_archive_identity_v1"
            and receipt.get("archive_generation") == current
            and receipt.get("logical_path") == source.get("pipeline_events")
            and receipt.get("runtime_effect") is False
            and receipt.get("allowed_runtime_apply") is False
            and receipt.get("logical_content_sha256")
            == source.get("logical_content_sha256")
        ):
            return True
    except (ValueError, OSError):
        pass
    return _archived_raw_digest(
        str(archived),
        current["device"],
        current["inode"],
        current["size_bytes"],
        current["mtime_ns"],
    ) == source.get("logical_content_sha256")


def load_source_quality_preflight(
    target_date: str, *, artifact_path: Path | None = None
) -> dict[str, Any]:
    path = (
        artifact_path
        if artifact_path is not None
        else observation_source_quality_audit_path(target_date)
    )
    exists = path.exists() or Path(f"{path}.gz").exists()
    clean_baseline_enforced = is_date_allowed(target_date, clean_baseline_policy())
    load_error: str | None = None
    try:
        payload = read_json_object_strict(path)
    except Exception as exc:
        load_error = type(exc).__name__
        payload = {}
    if not isinstance(payload, dict):
        load_error = load_error or f"non_dict_json:{type(payload).__name__}"
        payload = {}
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    raw_row_exclusion = _compact_raw_row_exclusion(payload.get("raw_row_exclusion"))
    raw_row_exclusion_manifest = summary.get(
        "raw_row_exclusion_manifest"
    ) or raw_row_exclusion.get("manifest_path")
    raw_row_exclusion_applied = bool(
        summary.get("raw_row_exclusion_applied")
        or raw_row_exclusion
        or raw_row_exclusion_manifest
    )
    hard_blocking_excluded_row_count = _safe_int(
        summary.get("hard_blocking_excluded_row_count")
        or raw_row_exclusion.get("excluded_row_count")
    )
    raw_status = payload.get("status")
    status = (
        raw_status
        if isinstance(raw_status, str) and raw_status
        else ("missing" if not exists else "invalid")
    )
    has_machine_summary = bool(summary)
    explicit_allowed = summary.get("tuning_input_allowed")
    validation_errors: list[str] = []
    if clean_baseline_enforced and has_machine_summary:
        if payload.get("target_date") != target_date:
            validation_errors.append("source_quality_preflight_target_date_mismatch")
        if type(explicit_allowed) is not bool:
            validation_errors.append("source_quality_preflight_allow_type_invalid")
        source = payload.get("source")
        if not isinstance(source, dict) or source.get("exists") is not True:
            validation_errors.append("source_quality_preflight_source_missing")
        if status not in {"pass", "warning", "fail"}:
            validation_errors.append("source_quality_preflight_status_invalid")
        raw_gap_count = summary.get("hard_blocking_contract_gap_count")
        if type(raw_gap_count) is not int or raw_gap_count < 0:
            validation_errors.append("source_quality_preflight_gap_count_invalid")
        if payload.get("schema_version") not in (
            None,
            "observation_source_quality_audit_v2",
        ):
            validation_errors.append("source_quality_preflight_schema_invalid")
        # Legacy exact-date reports stay readable; only v2 claims a bound raw generation.
        if payload.get("schema_version") == "observation_source_quality_audit_v2":
            source = source if isinstance(source, dict) else {}
            try:
                raw_path = Path(source["pipeline_events"])
                archived = raw_path.with_name(raw_path.name + ".gz")
                migrated = not raw_path.exists() and archived.exists()
                stat = (archived if migrated else raw_path).stat()
                current = {
                    "device": stat.st_dev,
                    "inode": stat.st_ino,
                    "size_bytes": stat.st_size,
                    "mtime_ns": stat.st_mtime_ns,
                }
                same_content = migrated and _archive_matches_source(
                    archived, source, current
                )
                if source.get("generation_stable") is not True or not (
                    source.get("generation") == current or same_content
                ):
                    validation_errors.append(
                        "source_quality_preflight_source_generation_changed"
                    )
                digest = source.get("logical_content_sha256")
                if (
                    not isinstance(digest, str)
                    or len(digest) != 64
                    or any(c not in "0123456789abcdef" for c in digest)
                ):
                    validation_errors.append(
                        "source_quality_preflight_source_digest_invalid"
                    )
                after = (archived if migrated else raw_path).stat()
                if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != (
                    stat.st_dev,
                    stat.st_ino,
                    stat.st_size,
                    stat.st_mtime_ns,
                ):
                    validation_errors.append(
                        "source_quality_preflight_source_changed_during_validation"
                    )
            except (KeyError, TypeError, ValueError, EOFError, OSError):
                validation_errors.append(
                    "source_quality_preflight_source_generation_missing"
                )
    hard_gap_count = _safe_int(summary.get("hard_blocking_contract_gap_count"))
    explicit_hard_block = (
        status == "fail"
        or explicit_allowed is False
        or hard_gap_count > 0
        or bool(summary.get("blocked_reason"))
    )
    preflight_unusable = (
        not exists or status in {"missing", "invalid"} or not has_machine_summary
    )
    fail_closed = explicit_hard_block or (
        clean_baseline_enforced and (preflight_unusable or bool(validation_errors))
    )
    blocked_reason = summary.get("blocked_reason") or None
    if fail_closed and blocked_reason is None:
        if not exists:
            blocked_reason = "source_quality_preflight_missing"
        elif load_error:
            blocked_reason = "source_quality_preflight_invalid"
        elif not has_machine_summary:
            blocked_reason = "source_quality_preflight_summary_missing"
        elif status == "fail":
            blocked_reason = "source_quality_preflight_status_fail"
        elif validation_errors:
            blocked_reason = validation_errors[0]
        else:
            blocked_reason = "blocked_contract_gap"
    return {
        "artifact": str(path) if exists else None,
        "target_date": target_date,
        "validation_errors": validation_errors,
        "status": status,
        "tuning_input_allowed": not fail_closed,
        "source_quality_gate": (
            BLOCKED_GATE
            if fail_closed
            else "pass" if has_machine_summary else "pass_or_not_evaluated"
        ),
        "blocked_reason": blocked_reason,
        "hard_blocking_contract_gap_count": hard_gap_count,
        "hard_blocking_excluded_row_count": hard_blocking_excluded_row_count,
        "raw_row_exclusion_applied": raw_row_exclusion_applied,
        "raw_row_exclusion_manifest": raw_row_exclusion_manifest,
        "raw_row_exclusion": raw_row_exclusion,
        "hard_blocking_stages": (
            summary.get("hard_blocking_stages")
            if isinstance(summary.get("hard_blocking_stages"), list)
            else []
        ),
        "review_warning_count": _safe_int(summary.get("review_warning_count")),
        "runtime_effect": False,
        "allowed_runtime_apply": not fail_closed,
        "load_error": load_error,
        "clean_baseline_enforced": clean_baseline_enforced,
    }


def source_quality_preflight_blocked(preflight: dict[str, Any]) -> bool:
    if preflight.get("validation_errors"):
        return True
    if preflight.get("tuning_input_allowed") is False:
        return True
    if preflight.get("allowed_runtime_apply") is False:
        return True
    if preflight.get("status") == "fail":
        return True
    if (
        preflight.get("status") in {"missing", "invalid"}
        and preflight.get("clean_baseline_enforced") is not False
    ):
        return True
    if preflight.get("hard_blocking_contract_gap_count"):
        return True
    if preflight.get("blocked_reason"):
        return True
    summary = (
        preflight.get("summary") if isinstance(preflight.get("summary"), dict) else {}
    )
    if (
        "tuning_input_allowed" in summary
        and type(summary["tuning_input_allowed"]) is not bool
    ):
        return True
    return summary.get("tuning_input_allowed") is False or bool(
        summary.get("blocked_reason")
    )


def filter_source_dates_by_preflight(
    source_dates: list[str],
    *,
    preflight_loader: Callable[[str], dict[str, Any]] | None = None,
) -> tuple[list[str], list[dict[str, Any]]]:
    """Exclude cumulative tuning dates whose own source-quality gate is blocked.

    A target-date preflight cannot vouch for historical rows from another date.
    Keep the per-date decision and compact provenance together so cumulative
    report producers cannot silently admit a missing, invalid, or failed audit.
    """

    loader = preflight_loader or load_source_quality_preflight
    allowed: list[str] = []
    excluded: list[dict[str, Any]] = []
    for source_date in dict.fromkeys(str(item).strip() for item in source_dates):
        if not source_date:
            continue
        preflight = loader(source_date)
        if not source_quality_preflight_blocked(preflight):
            allowed.append(source_date)
            continue
        excluded.append(
            {
                "source_date": source_date,
                "status": preflight.get("status"),
                "source_quality_gate": preflight.get("source_quality_gate"),
                "blocked_reason": preflight.get("blocked_reason"),
                "artifact": preflight.get("artifact"),
                "load_error": preflight.get("load_error"),
                "hard_blocking_contract_gap_count": int(
                    preflight.get("hard_blocking_contract_gap_count") or 0
                ),
            }
        )
    return allowed, excluded


def source_quality_blocked_stub(
    target_date: str, preflight: dict[str, Any] | None = None
) -> dict[str, Any]:
    gate = preflight or load_source_quality_preflight(target_date)
    return {
        "status": BLOCKED_STATUS,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "source_quality_gate": BLOCKED_GATE,
        "source_quality_preflight_gate": gate,
    }


def apply_source_quality_preflight_block(
    report: dict[str, Any], preflight: dict[str, Any]
) -> dict[str, Any]:
    if not source_quality_preflight_blocked(preflight):
        report["source_quality_preflight_gate"] = preflight
        return report
    blocked = _scrub_runtime_applicable_candidates(copy.deepcopy(report))
    blocked["status"] = BLOCKED_STATUS
    blocked["runtime_effect"] = False
    blocked["allowed_runtime_apply"] = False
    blocked["calibration_state"] = BLOCKED_STATUS
    blocked["source_quality_gate"] = BLOCKED_GATE
    blocked["source_quality_preflight_gate"] = preflight
    warnings = (
        blocked.get("warnings") if isinstance(blocked.get("warnings"), list) else []
    )
    if "source_quality_blocked_contract_gap" not in warnings:
        warnings.append("source_quality_blocked_contract_gap")
    blocked["warnings"] = warnings
    summary = blocked.get("summary")
    if isinstance(summary, dict):
        summary["status"] = BLOCKED_STATUS
        summary["runtime_effect"] = False
        summary["allowed_runtime_apply"] = False
        summary["calibration_state"] = BLOCKED_STATUS
        summary["source_quality_gate"] = BLOCKED_GATE
    return blocked


def _scrub_runtime_applicable_candidates(value: Any) -> Any:
    if isinstance(value, list):
        return [_scrub_runtime_applicable_candidates(item) for item in value]
    if not isinstance(value, dict):
        return value
    scrubbed: dict[str, Any] = {}
    for key, item in value.items():
        if key in RUNTIME_CANDIDATE_LIST_FIELDS:
            scrubbed[key] = []
            continue
        if key in RUNTIME_CANDIDATE_COUNT_FIELDS:
            scrubbed[key] = 0
            continue
        if key in RUNTIME_APPLY_BOOL_FIELDS:
            scrubbed[key] = False
            continue
        scrubbed[key] = _scrub_runtime_applicable_candidates(item)
    return scrubbed
