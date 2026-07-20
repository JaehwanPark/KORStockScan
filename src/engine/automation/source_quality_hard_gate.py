from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from src.engine.automation.source_quality_clean_baseline import (
    clean_baseline_policy,
    is_date_allowed,
)
from src.engine.daily_threshold_cycle_report import REPORT_DIR

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
    except (TypeError, ValueError):
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


def load_source_quality_preflight(target_date: str) -> dict[str, Any]:
    path = observation_source_quality_audit_path(target_date)
    exists = path.exists()
    clean_baseline_enforced = is_date_allowed(target_date, clean_baseline_policy())
    load_error: str | None = None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
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
    status = payload.get("status") or ("missing" if not exists else "invalid")
    has_machine_summary = bool(summary)
    explicit_allowed = summary.get("tuning_input_allowed")
    hard_gap_count = int(summary.get("hard_blocking_contract_gap_count") or 0)
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
        clean_baseline_enforced and preflight_unusable
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
        else:
            blocked_reason = "blocked_contract_gap"
    return {
        "artifact": str(path) if exists else None,
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
        "review_warning_count": int(summary.get("review_warning_count") or 0),
        "runtime_effect": False,
        "allowed_runtime_apply": not fail_closed,
        "load_error": load_error,
        "clean_baseline_enforced": clean_baseline_enforced,
    }


def source_quality_preflight_blocked(preflight: dict[str, Any]) -> bool:
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
    return summary.get("tuning_input_allowed") is False


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
