"""Generate the next trading day's stage2 checklist from postclose artifacts."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterator
from zoneinfo import ZoneInfo

from src.engine.monitoring.machine_microstructure_attribution import (
    resolve_completed_machine_target_date,
)
from src.utils.constants import PROJECT_ROOT
from src.utils.market_day import get_krx_trading_day_status

DOCS_DIR = PROJECT_ROOT / "docs"
CHECKLIST_DIR = DOCS_DIR / "checklists"
CHECKLIST_LOCK_DIR = PROJECT_ROOT / "data" / "runtime" / "build_next_stage2_checklist"
EV_REPORT_DIR = PROJECT_ROOT / "data" / "report" / "threshold_cycle_ev"
SWING_RUNTIME_APPROVAL_DIR = PROJECT_ROOT / "data" / "report" / "swing_runtime_approval"
CODE_IMPROVEMENT_REPORT_DIR = (
    PROJECT_ROOT / "data" / "report" / "code_improvement_workorder"
)
RUNTIME_APPLY_GAP_REPORT_DIR = (
    PROJECT_ROOT / "data" / "report" / "runtime_apply_gap_audit"
)
TUNING_PERFORMANCE_REPORT_DIR = (
    PROJECT_ROOT / "data" / "report" / "tuning_performance_control_tower"
)
AUTOMATION_TRIGGER_DECISION_REPORT_DIR = (
    PROJECT_ROOT / "data" / "report" / "automation_chain_trigger_decision"
)
RISING_MISSED_SCOUT_WORKORDER_REPORT_DIR = (
    PROJECT_ROOT / "data" / "report" / "rising_missed_scout_workorder"
)
MAIN_AI_QUALITY_REPORT_DIR = PROJECT_ROOT / "data" / "report" / "main_ai_quality_r0_r3"
MAIN_AI_QUALITY_REPORT_SCHEMA = "main_ai_quality_postclose_r0_r3_cycle_v1"
MAIN_AI_QUALITY_WORKORDER_SCHEMA = "main_ai_quality_source_only_gap_workorder_v1"
MAIN_AI_QUALITY_CHECKLIST_CONTRACT_START_DATE = "2026-08-18"
MAIN_AI_QUALITY_SOURCE_GAP_OWNERS = frozenset(
    {
        "MicroReversionForwardCollectorContinuity",
        "MicroReversionIntegratedRouteProof",
        "RuntimeExecutionReceiptCustodyRepair",
        "MainAIQualityMaterializedCompanionBindingRepair",
    }
)
MAIN_AI_QUALITY_OPTIONAL_NO_AUTHORITY_FIELDS = (
    "runtime_authority",
    "order_authority",
    "provider_authority",
)
MACHINE_MICROSTRUCTURE_POLICY_APPROVAL_REPORT_DIR = (
    PROJECT_ROOT / "data" / "report" / "machine_microstructure_policy_approval"
)
MACHINE_MICROSTRUCTURE_POLICY_APPROVAL_REPORT_SCHEMA = (
    "machine_microstructure_policy_approval_status_v1"
)
MACHINE_MICROSTRUCTURE_ATTRIBUTION_REPORT_DIR = (
    PROJECT_ROOT / "data" / "report" / "machine_microstructure_attribution"
)
MACHINE_MICROSTRUCTURE_ATTRIBUTION_REPORT_SCHEMA = (
    "machine_microstructure_attribution_v1"
)
MACHINE_MICROSTRUCTURE_SOURCE_ARTIFACT_SCHEMA = (
    "machine_microstructure_policy_source_artifact_provenance_v1"
)
MACHINE_MICROSTRUCTURE_COMPLETED_REFRESH_MAX_AGE = timedelta(minutes=30)
MACHINE_MICROSTRUCTURE_BUILDER_OWNED_CONDITIONAL_TASK_PREFIXES = (
    "MachineMicroPolicyApprovalPreopen",
    "MachineLifecycleTurnoverObjectiveFollowup",
    "MachineMicroPolicyApprovalSourceGap",
    "MainAIQualitySourceGap",
)
MACHINE_MICROSTRUCTURE_OBJECTIVE_OPEN_STATES = {
    "IMPLEMENTATION_REQUIRED",
    "EVIDENCE_ACCUMULATING",
}
MACHINE_MICROSTRUCTURE_OBJECTIVE_SOURCE_GAP_STATUSES = {
    "missing_or_unreadable",
    "source_changed_during_snapshot",
    "contract_invalid",
    "objective_followup_list_missing_or_invalid",
}
MACHINE_MICROSTRUCTURE_NON_RUNTIME_AUTHORITY = {
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
}

AUTO_START = "<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->"
AUTO_END = "<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->"
SYNC_COMMAND = (
    "PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && "
    "PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar"
)


@dataclass(frozen=True)
class GeneratedTask:
    task_id: str
    title: str
    slot: str
    time_window: str
    track: str
    source: str
    lines: tuple[str, ...]


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _load_main_ai_quality_workorders(
    path: Path, *, source_date: str
) -> tuple[list[dict[str, Any]], str]:
    """Load hash-bound source-only workorders without granting runtime authority."""

    if not path.is_file():
        return (
            [],
            (
                "missing_artifact"
                if source_date >= MAIN_AI_QUALITY_CHECKLIST_CONTRACT_START_DATE
                else "not_available"
            ),
        )
    try:
        raw = path.read_bytes()
        payload = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return [], "invalid_artifact"
    if not isinstance(payload, dict):
        return [], "invalid_artifact"
    declared_hash = payload.get("artifact_content_sha256")
    actual_hash = _canonical_sha256(
        {
            key: value
            for key, value in payload.items()
            if key != "artifact_content_sha256"
        }
    )
    if (
        payload.get("schema") != MAIN_AI_QUALITY_REPORT_SCHEMA
        or payload.get("target_date") != source_date
        or declared_hash != actual_hash
        or payload.get("decision_authority")
        != "postclose_source_only_ai_quality_research"
    ):
        return [], "invalid_artifact"
    for key, expected in MACHINE_MICROSTRUCTURE_NON_RUNTIME_AUTHORITY.items():
        if payload.get(key) is not expected:
            return [], "invalid_authority"
    if any(
        key in payload and payload.get(key) is not False
        for key in MAIN_AI_QUALITY_OPTIONAL_NO_AUTHORITY_FIELDS
    ):
        return [], "invalid_authority"

    workorders = payload.get("source_only_gap_workorders")
    diagnostics = payload.get("source_gap_diagnostics")
    if not isinstance(workorders, list) or not isinstance(diagnostics, dict):
        return [], "invalid_workorders"
    if (
        diagnostics.get("schema") != "main_ai_quality_source_only_gap_diagnostics_v1"
        or diagnostics.get("target_date") != source_date
        or diagnostics.get("contract_findings") != []
    ):
        return [], "invalid_workorders"
    for key, expected in MACHINE_MICROSTRUCTURE_NON_RUNTIME_AUTHORITY.items():
        if diagnostics.get(key) is not expected:
            return [], "invalid_workorder_authority"
    if any(
        key in diagnostics and diagnostics.get(key) is not False
        for key in MAIN_AI_QUALITY_OPTIONAL_NO_AUTHORITY_FIELDS
    ):
        return [], "invalid_workorder_authority"
    if diagnostics.get("workorders") != workorders:
        return [], "invalid_workorders"

    validated: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for row in workorders:
        if not isinstance(row, dict):
            return [], "invalid_workorders"
        if (
            row.get("schema") != MAIN_AI_QUALITY_WORKORDER_SCHEMA
            or row.get("status") != "open_source_producer_repair"
            or row.get("target_date") != source_date
        ):
            return [], "invalid_workorders"
        for key, expected in MACHINE_MICROSTRUCTURE_NON_RUNTIME_AUTHORITY.items():
            if row.get(key) is not expected:
                return [], "invalid_workorder_authority"
        if any(
            key in row and row.get(key) is not False
            for key in MAIN_AI_QUALITY_OPTIONAL_NO_AUTHORITY_FIELDS
        ):
            return [], "invalid_workorder_authority"
        reasons = row.get("reason_codes")
        if (
            not isinstance(row.get("owner"), str)
            or not str(row.get("owner") or "").strip()
            or row.get("owner") not in MAIN_AI_QUALITY_SOURCE_GAP_OWNERS
            or not isinstance(reasons, list)
            or not reasons
            or any(
                not isinstance(reason, str) or not reason.strip() for reason in reasons
            )
            or not isinstance(row.get("acceptance_test"), str)
            or not str(row.get("acceptance_test") or "").strip()
        ):
            return [], "invalid_workorders"
        identity_body = {
            "target_date": row["target_date"],
            "owner": row["owner"],
            "reason_codes": reasons,
            "acceptance_test": row["acceptance_test"],
            **MACHINE_MICROSTRUCTURE_NON_RUNTIME_AUTHORITY,
        }
        expected_id = f"main-ai-gap-{_canonical_sha256(identity_body)[:24]}"
        workorder_id = str(row.get("workorder_id") or "")
        if workorder_id != expected_id or workorder_id in seen_ids:
            return [], "invalid_workorders"
        seen_ids.add(workorder_id)
        validated.append(dict(row))
    return validated, "loaded"


def _machine_microstructure_predecessor_errors(
    *,
    approval_path: Path,
    approval_payload: dict[str, Any],
    attribution_path: Path,
    source_date: str,
    approval_not_before: datetime | None = None,
    require_loaded_source: bool = True,
    allow_empty_source_identity: bool = False,
) -> list[str]:
    errors: list[str] = []
    generated_raw = str(approval_payload.get("generated_at_kst") or "")
    try:
        generated_at = datetime.fromisoformat(generated_raw)
    except ValueError:
        generated_at = None
    if generated_at is None or generated_at.tzinfo is None:
        errors.append("generated_at_kst")
    else:
        try:
            source_day = date.fromisoformat(source_date)
        except ValueError:
            errors.append("source_date")
        else:
            if generated_at.date() < source_day:
                errors.append("generated_before_source_date")
        if (
            approval_not_before is not None
            and approval_not_before.tzinfo is not None
            and generated_at < approval_not_before.astimezone(generated_at.tzinfo)
        ):
            errors.append("approval_generated_before_completed_refresh_window")

    try:
        approval_stat = approval_path.stat()
    except OSError:
        approval_stat = None
        errors.append("approval_artifact_missing_or_unreadable")
    if (
        generated_at is not None
        and generated_at.tzinfo is not None
        and approval_stat is not None
        and generated_at.timestamp() > approval_stat.st_mtime + 1.0
    ):
        errors.append("approval_generated_after_report_file")

    provenance = approval_payload.get("source_artifact")
    if not isinstance(provenance, dict):
        return [*errors, "source_artifact"]
    if provenance.get("schema") != MACHINE_MICROSTRUCTURE_SOURCE_ARTIFACT_SCHEMA:
        errors.append("source_artifact_schema")
    recorded_path = str(provenance.get("path") or "").strip()
    try:
        path_matches = bool(recorded_path) and Path(recorded_path).resolve() == (
            attribution_path.resolve()
        )
    except OSError:
        path_matches = False
    if not path_matches:
        errors.append("source_artifact_path")
    if str(approval_payload.get("source_path") or "").strip() != recorded_path:
        errors.append("source_path_provenance_mismatch")
    recorded_digest = provenance.get("sha256")
    recorded_mtime_ns = provenance.get("mtime_ns")
    recorded_size = provenance.get("size_bytes")
    identity_is_empty = all(
        value is None for value in (recorded_digest, recorded_mtime_ns, recorded_size)
    )
    identity_is_complete = (
        isinstance(recorded_digest, str)
        and bool(re.fullmatch(r"[0-9a-f]{64}", recorded_digest))
        and isinstance(recorded_mtime_ns, int)
        and not isinstance(recorded_mtime_ns, bool)
        and isinstance(recorded_size, int)
        and not isinstance(recorded_size, bool)
        and recorded_size >= 0
    )
    if allow_empty_source_identity and identity_is_empty:
        return errors
    if not identity_is_complete:
        return [*errors, "source_artifact_identity"]

    try:
        source_bytes = attribution_path.read_bytes()
        source_stat = attribution_path.stat()
    except OSError:
        return [*errors, "source_artifact_missing_or_unreadable"]
    source_digest = hashlib.sha256(source_bytes).hexdigest()
    if recorded_digest != source_digest:
        errors.append("source_artifact_sha256")
    if (
        not isinstance(recorded_mtime_ns, int)
        or isinstance(recorded_mtime_ns, bool)
        or recorded_mtime_ns != source_stat.st_mtime_ns
    ):
        errors.append("source_artifact_mtime_ns")
    if (
        not isinstance(recorded_size, int)
        or isinstance(recorded_size, bool)
        or recorded_size != source_stat.st_size
    ):
        errors.append("source_artifact_size_bytes")
    if (
        approval_stat is not None
        and approval_stat.st_mtime_ns < source_stat.st_mtime_ns
    ):
        errors.append("approval_file_older_than_source_artifact")
    if generated_at is not None and generated_at.tzinfo is not None:
        # Status timestamps are intentionally serialized to whole seconds.
        # One second of tolerance preserves that representation while still
        # rejecting a report generated before its exact predecessor.
        if generated_at.timestamp() + 1.0 < source_stat.st_mtime:
            errors.append("approval_generated_before_source_artifact")
    if not require_loaded_source:
        return errors
    try:
        source_payload = json.loads(source_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError):
        source_payload = None
    if not isinstance(source_payload, dict):
        errors.append("source_payload_not_object")
    else:
        if (
            source_payload.get("schema")
            != MACHINE_MICROSTRUCTURE_ATTRIBUTION_REPORT_SCHEMA
        ):
            errors.append("source_payload_schema")
        if source_payload.get("target_date") != source_date:
            errors.append("source_payload_target_date")
        if approval_not_before is not None and approval_not_before.tzinfo is not None:
            not_before = approval_not_before.astimezone(ZoneInfo("Asia/Seoul"))
            source_generated_raw = str(source_payload.get("generated_at_kst") or "")
            try:
                source_generated_at = datetime.fromisoformat(source_generated_raw)
            except ValueError:
                source_generated_at = None
            if source_generated_at is None or source_generated_at.tzinfo is None:
                errors.append("source_payload_generated_at_kst")
            elif source_generated_at < not_before.astimezone(
                source_generated_at.tzinfo
            ):
                errors.append(
                    "source_payload_generated_before_completed_refresh_window"
                )
            if source_stat.st_mtime < not_before.timestamp():
                errors.append("source_artifact_mtime_before_completed_refresh_window")
        source_authority = source_payload.get("authority")
        expected_source_authority = {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }
        if not isinstance(source_authority, dict) or any(
            source_authority.get(field) is not expected
            for field, expected in expected_source_authority.items()
        ):
            errors.append("source_payload_authority")
    return errors


def _load_machine_microstructure_approval_report(
    path: Path,
    *,
    source_date: str,
    attribution_path: Path,
    approval_not_before: datetime | None = None,
) -> tuple[dict[str, Any], str]:
    if not path.exists():
        return {}, "missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}, "unreadable"
    if not isinstance(payload, dict):
        return {}, "contract_invalid:payload_not_object"

    errors: list[str] = []
    if payload.get("schema") != MACHINE_MICROSTRUCTURE_POLICY_APPROVAL_REPORT_SCHEMA:
        errors.append("schema")
    if payload.get("phase") != "postclose":
        errors.append("phase")
    if payload.get("target_date") != source_date:
        errors.append("target_date")
    authority = payload.get("authority")
    expected_authority = {
        "runtime_effect": False,
        "runtime_apply_performed": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    if not isinstance(authority, dict) or any(
        authority.get(field) is not expected
        for field, expected in expected_authority.items()
    ):
        errors.append("authority")
    objective_followups = payload.get("objective_followups")
    objective_source_status = payload.get("objective_followup_source_status")
    source_status = payload.get("source_status")
    if objective_source_status not in {
        "loaded",
        *MACHINE_MICROSTRUCTURE_OBJECTIVE_SOURCE_GAP_STATUSES,
    }:
        errors.append("objective_followup_source_status")
    capture_gap_statuses = {
        "missing_or_unreadable",
        "source_changed_during_snapshot",
        "contract_invalid",
    }
    if (
        objective_source_status in capture_gap_statuses
        and source_status != objective_source_status
    ):
        errors.append("source_status_objective_source_status_mismatch")
    if not isinstance(objective_followups, list) or any(
        not isinstance(row, dict) for row in objective_followups
    ):
        errors.append("objective_followups")
    summary = payload.get("summary")
    actionable_count = (
        summary.get("actionable_objective_followup_count")
        if isinstance(summary, dict)
        else None
    )
    rejection_count = (
        summary.get("objective_followup_rejection_count")
        if isinstance(summary, dict)
        else None
    )
    objective_followup_rejections = payload.get("objective_followup_rejections")
    if (
        not isinstance(rejection_count, int)
        or isinstance(rejection_count, bool)
        or rejection_count < 0
        or not isinstance(objective_followup_rejections, list)
        or any(not isinstance(row, dict) for row in objective_followup_rejections)
        or (
            isinstance(objective_followup_rejections, list)
            and rejection_count != len(objective_followup_rejections)
        )
    ):
        errors.append("objective_followup_rejection_count")
        rejection_count = 0
    allow_prior_source_date = (
        objective_source_status in MACHINE_MICROSTRUCTURE_OBJECTIVE_SOURCE_GAP_STATUSES
        or rejection_count > 0
    )
    if (
        isinstance(objective_followups, list)
        and all(isinstance(row, dict) for row in objective_followups)
        and any(
            not _machine_microstructure_objective_row_is_valid(
                row,
                source_date=source_date,
                allow_prior_source_date=allow_prior_source_date,
            )
            for row in objective_followups
        )
    ):
        errors.append("objective_followup_rows")
    if (
        not isinstance(actionable_count, int)
        or isinstance(actionable_count, bool)
        or (
            isinstance(objective_followups, list)
            and actionable_count != len(objective_followups)
        )
    ):
        errors.append("objective_followup_count")
    if errors:
        return {}, "contract_invalid:" + ",".join(errors)
    predecessor_errors = _machine_microstructure_predecessor_errors(
        approval_path=path,
        approval_payload=payload,
        attribution_path=attribution_path,
        source_date=source_date,
        approval_not_before=approval_not_before,
        require_loaded_source=objective_source_status == "loaded",
        allow_empty_source_identity=objective_source_status
        in {"missing_or_unreadable", "source_changed_during_snapshot"},
    )
    if predecessor_errors:
        return {}, "predecessor_invalid:" + ",".join(predecessor_errors)
    if objective_source_status != "loaded":
        return payload, f"objective_source_gap:{objective_source_status}"
    if rejection_count > 0:
        return payload, f"objective_source_gap:rejected_rows:{rejection_count}"
    return payload, "loaded"


def _machine_microstructure_objective_row_is_valid(
    row: dict[str, Any], *, source_date: str, allow_prior_source_date: bool
) -> bool:
    authority = row.get("authority")
    metric_contract = row.get("metric_contract")
    row_source_date = str(row.get("source_date") or "")
    try:
        row_source_day = date.fromisoformat(row_source_date)
        report_source_day = date.fromisoformat(source_date)
    except ValueError:
        source_date_valid = False
    else:
        row_is_trading_day, _ = get_krx_trading_day_status(row_source_day)
        source_date_valid = row_is_trading_day and (
            row_source_day <= report_source_day
            if allow_prior_source_date
            else row_source_day == report_source_day
        )
    return (
        row.get("schema") == "machine_fast_lifecycle_objective_followup_v1"
        and str(row.get("followup_id") or "").strip() != ""
        and source_date_valid
        and row.get("followup_required") is True
        and row.get("state") in MACHINE_MICROSTRUCTURE_OBJECTIVE_OPEN_STATES
        and row.get("operator_decision_required") is False
        and isinstance(metric_contract, dict)
        and metric_contract.get("decision_authority")
        == "postclose_followup_tracking_only"
        and all(
            row.get(field) is expected
            for field, expected in MACHINE_MICROSTRUCTURE_NON_RUNTIME_AUTHORITY.items()
        )
        and isinstance(authority, dict)
        and all(
            authority.get(field) is expected
            for field, expected in MACHINE_MICROSTRUCTURE_NON_RUNTIME_AUTHORITY.items()
        )
    )


def _missing_required_postclose_artifacts(source_date: str) -> list[Path]:
    required = [
        EV_REPORT_DIR / f"threshold_cycle_ev_{source_date}.json",
    ]
    return [path for path in required if not path.exists()]


def _has_payload(payload: dict[str, Any]) -> bool:
    return bool(payload)


def _next_krx_trading_day(source_date: str) -> str:
    current = date.fromisoformat(source_date)
    for _ in range(14):
        current += timedelta(days=1)
        is_trading_day, _ = get_krx_trading_day_status(current)
        if is_trading_day:
            return current.isoformat()
    raise RuntimeError(f"could not resolve next KRX trading day after {source_date}")


def _compact_mmdd(target_date: str) -> str:
    return target_date[5:7] + target_date[8:10]


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def stage2_checklist_path(target_date: str) -> Path:
    return CHECKLIST_DIR / f"{target_date}-stage2-todo-checklist.md"


def _list_selected_families(ev_report: dict[str, Any]) -> list[str]:
    runtime_apply = (
        ev_report.get("runtime_apply")
        if isinstance(ev_report.get("runtime_apply"), dict)
        else {}
    )
    raw = runtime_apply.get("selected_families")
    if not isinstance(raw, list):
        return []
    return [str(item).strip() for item in raw if str(item).strip()]


def _has_runtime_change(ev_report: dict[str, Any]) -> bool:
    runtime_apply = (
        ev_report.get("runtime_apply")
        if isinstance(ev_report.get("runtime_apply"), dict)
        else {}
    )
    return bool(runtime_apply.get("runtime_change")) or bool(
        _list_selected_families(ev_report)
    )


def _has_approval_request(
    ev_report: dict[str, Any], swing_report: dict[str, Any]
) -> bool:
    if (
        isinstance(ev_report.get("approval_requests"), list)
        and ev_report["approval_requests"]
    ):
        return True
    swing_ev = (
        ev_report.get("swing_runtime_approval")
        if isinstance(ev_report.get("swing_runtime_approval"), dict)
        else {}
    )
    for payload in (swing_ev, swing_report):
        if (
            isinstance(payload.get("approval_requests"), list)
            and payload["approval_requests"]
        ):
            return True
        if isinstance(payload.get("requests"), list) and payload["requests"]:
            return True
        summary = (
            payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        )
        requested = payload.get("requested", summary.get("requested", 0))
        try:
            if int(requested or 0) > 0:
                return True
        except (TypeError, ValueError):
            continue
    return False


def _has_sim_probe_activity(ev_report: dict[str, Any]) -> bool:
    simulator = (
        ev_report.get("scalp_simulator")
        if isinstance(ev_report.get("scalp_simulator"), dict)
        else {}
    )
    try:
        if int(simulator.get("event_count") or 0) > 0:
            return True
    except (TypeError, ValueError):
        pass
    daily = (
        ev_report.get("daily_ev_summary")
        if isinstance(ev_report.get("daily_ev_summary"), dict)
        else {}
    )
    source_split = (
        daily.get("source_split") if isinstance(daily.get("source_split"), dict) else {}
    )
    for key in ("sim", "probe"):
        payload = (
            source_split.get(key) if isinstance(source_split.get(key), dict) else {}
        )
        try:
            if int(payload.get("sample") or 0) > 0:
                return True
        except (TypeError, ValueError):
            continue
    return False


def _code_workorder_count(
    ev_report: dict[str, Any], code_report: dict[str, Any]
) -> int:
    code_ev = (
        ev_report.get("code_improvement_workorder")
        if isinstance(ev_report.get("code_improvement_workorder"), dict)
        else {}
    )
    for payload in (
        (
            code_report.get("summary")
            if isinstance(code_report.get("summary"), dict)
            else {}
        ),
        code_ev,
    ):
        try:
            count = int(payload.get("selected_order_count") or 0)
        except (TypeError, ValueError):
            count = 0
        if count > 0:
            return count
    return 0


def _runtime_gap_preopen_pending_items(
    runtime_gap_report: dict[str, Any],
) -> list[dict[str, Any]]:
    if not runtime_gap_report:
        return []
    by_id: dict[str, dict[str, Any]] = {}
    ledger = runtime_gap_report.get("candidate_route_ledger")
    if isinstance(ledger, list):
        for item in ledger:
            if not isinstance(item, dict):
                continue
            candidate_id = str(
                item.get("candidate_id") or item.get("family") or ""
            ).strip()
            if not candidate_id:
                continue
            final_disposition = str(item.get("final_disposition") or "").strip()
            failure_state = str(item.get("failure_state") or "").strip()
            next_stage = str(
                item.get("next_retry_stage") or item.get("preopen_apply_state") or ""
            ).strip()
            if (
                final_disposition == "post_apply_attribution_pending"
                or failure_state == "retry_pending"
                or next_stage == "preopen_apply_candidate"
            ):
                by_id[candidate_id] = item
    retry_queue = runtime_gap_report.get("retry_queue")
    if isinstance(retry_queue, list):
        for item in retry_queue:
            if not isinstance(item, dict):
                continue
            candidate_id = str(item.get("candidate_id") or "").strip()
            if not candidate_id:
                continue
            current = dict(by_id.get(candidate_id) or {})
            current.update(item)
            by_id[candidate_id] = current
    return sorted(
        by_id.values(),
        key=lambda item: str(item.get("candidate_id") or item.get("family") or ""),
    )


def _runtime_gap_preopen_pending_summary(runtime_gap_report: dict[str, Any]) -> str:
    items = _runtime_gap_preopen_pending_items(runtime_gap_report)
    if not items:
        return ""
    rendered = []
    for item in items[:5]:
        candidate_id = str(item.get("candidate_id") or item.get("family") or "-")
        family = str(item.get("family") or "").strip()
        state = str(item.get("failure_state") or item.get("final_disposition") or "-")
        reason = str(
            item.get("failure_reason")
            or item.get("failure_code")
            or item.get("retry_reason")
            or "-"
        )
        if family and family not in candidate_id:
            candidate_id = f"{candidate_id} / family={family}"
        rendered.append(f"`{candidate_id}`({state}, reason={reason})")
    suffix = f" 외 {len(items) - 5}건" if len(items) > 5 else ""
    return ", ".join(rendered) + suffix


def _runtime_gap_codex_directive_summary(runtime_gap_report: dict[str, Any]) -> str:
    directives = runtime_gap_report.get("codex_workorder_directives")
    if not isinstance(directives, list):
        return ""
    rendered: list[str] = []
    for item in directives[:5]:
        if not isinstance(item, dict):
            continue
        directive_type = str(item.get("directive_type") or "-")
        candidate_id = str(item.get("candidate_id") or "-")
        blocking_contract = str(
            item.get("blocking_contract") or item.get("ai_reasoning_summary") or "-"
        )
        rendered.append(f"`{directive_type}`:{candidate_id}(block={blocking_contract})")
    if not rendered:
        return ""
    suffix = f" 외 {len(directives) - 5}건" if len(directives) > 5 else ""
    return ", ".join(rendered) + suffix


def _source_dimension_gap_summary(runtime_gap_report: dict[str, Any]) -> str:
    summary = (
        runtime_gap_report.get("source_dimension_gap_summary")
        if isinstance(runtime_gap_report.get("source_dimension_gap_summary"), dict)
        else {}
    )
    actionable = int(summary.get("actionable_unknown_gap_count") or 0)
    if actionable <= 0:
        return ""
    gap_count = int(summary.get("gap_count") or actionable)
    resolutions = (
        summary.get("recommended_resolution_counts")
        if isinstance(summary.get("recommended_resolution_counts"), dict)
        else {}
    )
    missing_keys = (
        summary.get("missing_dimension_key_counts")
        if isinstance(summary.get("missing_dimension_key_counts"), dict)
        else {}
    )
    return (
        f"actionable_unknown_gap_count=`{actionable}`, source_dimension_gap_count=`{gap_count}`, "
        f"recommended_resolution_counts=`{resolutions}`, missing_dimension_key_counts=`{missing_keys}`"
    )


def _quiet_gap_summary(runtime_gap_report: dict[str, Any]) -> str:
    summary = (
        runtime_gap_report.get("quiet_gap_summary")
        if isinstance(runtime_gap_report.get("quiet_gap_summary"), dict)
        else {}
    )
    quiet_count = int(summary.get("quiet_gap_count") or 0)
    if quiet_count <= 0:
        return ""
    type_counts = (
        summary.get("quiet_gap_type_counts")
        if isinstance(summary.get("quiet_gap_type_counts"), dict)
        else {}
    )
    return (
        f"quiet_gap_count=`{quiet_count}`, rollup_required_count=`{summary.get('rollup_required_count') or 0}`, "
        f"sim_live_connected_quiet_gap_count=`{summary.get('sim_live_connected_quiet_gap_count') or 0}`, "
        f"observation_source_quality_warning_count=`{summary.get('observation_source_quality_warning_count') or 0}`, "
        f"quiet_gap_type_counts=`{type_counts}`"
    )


def _rising_missed_scout_summary(rising_missed_report: dict[str, Any]) -> str:
    if not rising_missed_report:
        return "report_missing_or_unreadable"
    summary = (
        rising_missed_report.get("summary")
        if isinstance(rising_missed_report.get("summary"), dict)
        else {}
    )
    order_count = summary.get("code_improvement_order_count")
    if order_count is None:
        orders = rising_missed_report.get("code_improvement_orders")
        order_count = len(orders) if isinstance(orders, list) else 0
    return (
        f"code_improvement_order_count=`{order_count}`, "
        f"forced_scout_with_post_sell_count=`{summary.get('forced_scout_with_post_sell_count') or 0}`, "
        f"post_sell_join_coverage_pct=`{summary.get('forced_scout_post_sell_join_coverage_pct') or 0}`, "
        f"outcome_coverage_state=`{summary.get('forced_scout_outcome_coverage_state') or 'unknown'}`, "
        f"profitable_forced_scout_count=`{summary.get('profitable_forced_scout_count') or 0}`, "
        f"loss_or_flat_forced_scout_count=`{summary.get('loss_or_flat_forced_scout_count') or 0}`, "
        f"current_missed_count=`{summary.get('current_missed_count') or 0}`"
    )


def _machine_microstructure_approval_pending_summary(
    report: dict[str, Any],
) -> str:
    if not report:
        return ""
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    try:
        actionable_count = int(summary.get("actionable_candidate_count") or 0)
    except (TypeError, ValueError):
        actionable_count = 0
    if actionable_count <= 0:
        source_status = str(report.get("source_status") or "").strip()
        return (
            f"`source_gap`({source_status})"
            if source_status
            and source_status not in {"loaded", "not_applicable_preopen"}
            else ""
        )
    rows = report.get("actionable_candidates")
    rendered: list[str] = []
    if isinstance(rows, list):
        for row in rows[:5]:
            if not isinstance(row, dict):
                continue
            rendered.append(
                f"`{row.get('candidate_id') or '-'}`"
                f"({row.get('state') or '-'}, hash="
                f"{str(row.get('candidate_sha256') or '')[:16] or '-'})"
            )
    suffix = (
        f" 외 {actionable_count - len(rendered)}건"
        if actionable_count > len(rendered)
        else ""
    )
    source_status = str(report.get("source_status") or "").strip()
    source_gap = (
        f"; `source_gap`({source_status})"
        if source_status and source_status not in {"loaded", "not_applicable_preopen"}
        else ""
    )
    return ", ".join(rendered) + suffix + source_gap


def _compact_inline_value(
    value: Any,
    *,
    fallback: str = "-",
    max_length: int | None = 160,
) -> str:
    rendered = " ".join(str(value or "").replace("`", "'").split()).strip()
    if not rendered:
        return fallback
    if max_length is None or len(rendered) <= max_length:
        return rendered
    return rendered[:max_length]


def _machine_microstructure_objective_followup_summary(
    report: dict[str, Any],
) -> str:
    rows = report.get("objective_followups")
    if not isinstance(rows, list):
        return ""

    unresolved: list[str] = []
    fallback_actions = {
        "IMPLEMENTATION_REQUIRED": "implement_source_only_rolling_paired_policy_research",
        "EVIDENCE_ACCUMULATING": "continue_exact_date_collection_and_rolling_readiness_review",
    }
    for row in rows:
        if not isinstance(row, dict) or row.get("followup_required") is not True:
            continue
        status = _compact_inline_value(
            row.get("status") or row.get("state"), fallback="UNKNOWN"
        ).upper()
        if status in {"CANDIDATE_QUEUE_HANDOFF", "COMPLETE"}:
            continue
        objective_id = _compact_inline_value(
            row.get("objective_id")
            or row.get("followup_id")
            or row.get("id")
            or row.get("objective"),
            fallback="machine_lifecycle_turnover",
        )
        next_action = _compact_inline_value(
            row.get("next_action") or fallback_actions.get(status),
            fallback="inspect_unresolved_objective_and_assign_owner",
        )
        unresolved.append(
            f"`{objective_id}`(status=`{status}`, next_action=`{next_action}`)"
        )

    if not unresolved:
        return ""
    rendered = unresolved[:5]
    suffix = f" 외 {len(unresolved) - len(rendered)}건" if len(unresolved) > 5 else ""
    return ", ".join(rendered) + suffix


def _automation_trigger_decision_summary(trigger_report: dict[str, Any]) -> str:
    if not trigger_report:
        return "trigger_report_missing=`true`, required_action=`run_required_or_report_generation_check`"

    summary = (
        trigger_report.get("summary")
        if isinstance(trigger_report.get("summary"), dict)
        else {}
    )
    decisions = (
        trigger_report.get("decisions")
        if isinstance(trigger_report.get("decisions"), list)
        else []
    )
    reason_counts: dict[str, int] = {}
    run_steps: list[str] = []
    skip_steps: list[str] = []
    source_missing_steps: list[str] = []
    for raw_decision in decisions:
        if not isinstance(raw_decision, dict):
            continue
        step_id = str(raw_decision.get("step_id") or "").strip()
        decision = str(raw_decision.get("decision") or "").strip()
        if step_id and decision == "run":
            run_steps.append(step_id)
        elif step_id and decision == "skip":
            skip_steps.append(step_id)
        if step_id and raw_decision.get("source_missing") is True:
            source_missing_steps.append(step_id)
        reasons = raw_decision.get("trigger_reasons")
        if isinstance(reasons, list):
            for reason in reasons:
                key = str(reason).strip()
                if key:
                    reason_counts[key] = reason_counts.get(key, 0) + 1

    top_reasons = ", ".join(
        f"{reason}:{count}"
        for reason, count in sorted(
            reason_counts.items(), key=lambda item: (-item[1], item[0])
        )[:5]
    )
    return (
        f"total_steps=`{summary.get('total_steps') or len(decisions)}`, "
        f"run_count=`{summary.get('run_count') or len(run_steps)}`, "
        f"skip_count=`{summary.get('skip_count') or len(skip_steps)}`, "
        f"source_missing_count=`{summary.get('source_missing_count') or len(source_missing_steps)}`, "
        f"force_override_count=`{summary.get('force_override_count') or 0}`, "
        f"run_steps_sample=`{', '.join(run_steps[:5]) or '-'}`, "
        f"skip_steps_sample=`{', '.join(skip_steps[:5]) or '-'}`, "
        f"top_reasons=`{top_reasons or '-'}`"
    )


def _task_line(task: GeneratedTask, target_date: str) -> str:
    return (
        f"- [ ] `[{task.task_id}] {task.title}` "
        f"(`Due: {target_date}`, `Slot: {task.slot}`, `TimeWindow: {task.time_window}`, `Track: {task.track}`)"
    )


def _render_task(task: GeneratedTask, target_date: str) -> list[str]:
    out = [_task_line(task, target_date), f"  - Source: {task.source}"]
    out.extend(f"  - {line}" for line in task.lines)
    out.append("")
    return out


def _task_sort_key(task: GeneratedTask) -> tuple[int, str, str]:
    slot_order = {"PREOPEN": 0, "INTRADAY": 1, "POSTCLOSE": 2}
    return (slot_order.get(task.slot, 99), task.time_window, task.task_id)


def _build_tasks(
    *,
    source_date: str,
    target_date: str,
    ev_report: dict[str, Any],
    swing_report: dict[str, Any],
    code_report: dict[str, Any],
    runtime_gap_report: dict[str, Any],
    trigger_report: dict[str, Any],
    rising_missed_report: dict[str, Any],
    machine_micro_approval_report: dict[str, Any],
    machine_micro_approval_source_status: str,
    main_ai_quality_workorders: list[dict[str, Any]],
    main_ai_quality_source_status: str,
) -> list[GeneratedTask]:
    mmdd = _compact_mmdd(target_date)
    ev_path = EV_REPORT_DIR / f"threshold_cycle_ev_{source_date}.json"
    tuning_performance_path = (
        TUNING_PERFORMANCE_REPORT_DIR
        / f"tuning_performance_control_tower_{source_date}.json"
    )
    code_md_path = (
        DOCS_DIR
        / "code-improvement-workorders"
        / f"code_improvement_workorder_{source_date}.md"
    )
    runtime_gap_path = (
        RUNTIME_APPLY_GAP_REPORT_DIR / f"runtime_apply_gap_audit_{source_date}.json"
    )
    runtime_gap_pending = _runtime_gap_preopen_pending_summary(runtime_gap_report)
    runtime_gap_directives = _runtime_gap_codex_directive_summary(runtime_gap_report)
    source_dimension_gap_summary = _source_dimension_gap_summary(runtime_gap_report)
    quiet_gap_summary = _quiet_gap_summary(runtime_gap_report)
    trigger_decision_path = (
        AUTOMATION_TRIGGER_DECISION_REPORT_DIR
        / f"automation_chain_trigger_decision_{source_date}.json"
    )
    rising_missed_path = (
        RISING_MISSED_SCOUT_WORKORDER_REPORT_DIR
        / f"rising_missed_scout_workorder_{source_date}.json"
    )
    trigger_decision_summary = _automation_trigger_decision_summary(trigger_report)
    rising_missed_summary = _rising_missed_scout_summary(rising_missed_report)
    machine_micro_approval_pending = _machine_microstructure_approval_pending_summary(
        machine_micro_approval_report
    )
    machine_micro_objective_followups = (
        _machine_microstructure_objective_followup_summary(
            machine_micro_approval_report
        )
    )
    main_ai_quality_path = (
        MAIN_AI_QUALITY_REPORT_DIR / f"main_ai_quality_r0_r3_cycle_{source_date}.json"
    )
    tuning_sources = f"[threshold_cycle_ev_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(ev_path)})"
    tuning_decision_line = "판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다."
    if tuning_performance_path.exists():
        tuning_sources = (
            f"[tuning_performance_control_tower_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(tuning_performance_path)}), "
            f"{tuning_sources}"
        )
        tuning_decision_line = "판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다."
    threshold_source = (
        f"[threshold_cycle_ev_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(ev_path)}), "
        "[threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), "
        "[run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)"
    )
    threshold_lines = [
        "판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.",
        "금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.",
        "다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.",
    ]
    if runtime_gap_pending:
        threshold_source = (
            f"[threshold_cycle_ev_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(ev_path)}), "
            f"[runtime_apply_gap_audit_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(runtime_gap_path)}), "
            "[threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), "
            "[run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)"
        )
        threshold_lines = [
            threshold_lines[0],
            f"판정 기준: runtime apply gap audit의 `post_apply_attribution_pending`/`retry_pending` 후보가 다음 PREOPEN apply plan과 runtime env에서 소비되는지 사용자에게 표면화한다. 확인 대상: {runtime_gap_pending}.",
            threshold_lines[1],
            "다음 액션: `runtime_gap_pending_consumed`, `runtime_gap_pending_not_consumed`, `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.",
        ]
    tasks = [
        GeneratedTask(
            task_id=f"ThresholdEnvAutoApplyPreopen{mmdd}",
            title="threshold env 자동 apply 산출물 및 사용자 개입 여부 확인",
            slot="PREOPEN",
            time_window="08:50~08:55",
            track="RuntimeStability",
            source=threshold_source,
            lines=tuple(threshold_lines),
        ),
        GeneratedTask(
            task_id=f"RisingMissedScoutRuntimePreopen{mmdd}",
            title="rising_missed_scout_workorder 후속 구현 및 귀속 확인",
            slot="PREOPEN",
            time_window="08:55~09:00",
            track="ScalpingLogic",
            source=(
                f"[rising_missed_scout_workorder_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(rising_missed_path)}), "
                f"[code_improvement_workorder_{source_date}.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_{source_date}.json), "
                f"[threshold_apply_{target_date}.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_{target_date}.json), "
                f"[threshold_runtime_env_{target_date}.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_{target_date}.json), "
                f"[threshold_runtime_env_verify_{target_date}.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_{target_date}.json)"
            ),
            lines=(
                f"판정 기준: 전일 `rising_missed_scout_workorder` 요약({rising_missed_summary})의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.",
                "금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.",
                "다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.",
            ),
        ),
    ]
    if machine_micro_approval_pending:
        machine_micro_approval_path = (
            MACHINE_MICROSTRUCTURE_POLICY_APPROVAL_REPORT_DIR
            / f"machine_microstructure_policy_approval_postclose_{source_date}.json"
        )
        tasks.append(
            GeneratedTask(
                task_id=f"MachineMicroPolicyApprovalPreopen{mmdd}",
                title="micro 기반 기계 정책 승인 대기열 및 PREOPEN handoff 확인",
                slot="PREOPEN",
                time_window="08:45~08:50",
                track="ScalpingLogic",
                source=(
                    f"[machine_microstructure_policy_approval_postclose_{source_date}.json]"
                    f"(/home/ubuntu/KORStockScan/{_rel(machine_micro_approval_path)}), "
                    "[machine_microstructure_policy_approval.py]"
                    "(/home/ubuntu/KORStockScan/src/engine/automation/"
                    "machine_microstructure_policy_approval.py)"
                ),
                lines=(
                    f"판정 기준: 이월된 승인 대기 후보 {machine_micro_approval_pending}의 design/approval/expiry 상태와 동일 candidate hash의 명시 승인 artifact를 확인한다.",
                    "금지: `DESIGN_REQUIRED`, 변경된 candidate hash, 미등록 runtime family, same-stage 충돌, rollback/post-apply 계약 결손을 PREOPEN env 수정으로 우회하지 않는다.",
                    "다음 액션: `source_gap_repair`, `design_required`, `review_ready_request_operator_decision`, `user_approved_handoff_ready`, `preopen_scheduled`, `hold_followup`, `applied_attribution_pending`, `post_apply_attributed`, `expired_revalidate`, `rejected` 중 하나로 닫고 handoff는 family-owned apply receipt와 분리 확인한다.",
                ),
            )
        )
    if machine_micro_objective_followups:
        machine_micro_approval_path = (
            MACHINE_MICROSTRUCTURE_POLICY_APPROVAL_REPORT_DIR
            / f"machine_microstructure_policy_approval_postclose_{source_date}.json"
        )
        tasks.append(
            GeneratedTask(
                task_id=f"MachineLifecycleTurnoverObjectiveFollowup{mmdd}",
                title="위젯·episode 빠른 회전 목적의 미완료 후속 구현 확인",
                slot="POSTCLOSE",
                time_window="21:30~21:40",
                track="ScalpingLogic",
                source=(
                    f"[machine_microstructure_policy_approval_postclose_{source_date}.json]"
                    f"(/home/ubuntu/KORStockScan/{_rel(machine_micro_approval_path)}), "
                    "[machine_microstructure_attribution.py]"
                    "(/home/ubuntu/KORStockScan/src/engine/monitoring/"
                    "machine_microstructure_attribution.py)"
                ),
                lines=(
                    "판정 기준: 승인 후보 수와 무관하게 "
                    f"`followup_required=true`인 미완료 목적 항목 {machine_micro_objective_followups}의 "
                    "상태와 상태별 `next_action`을 확인하고 구현 또는 표본수집 경로로 닫는다.",
                    "상태별 다음 액션: `IMPLEMENTATION_REQUIRED`는 source-only rolling paired policy 연구를 구현하고, "
                    "`EVIDENCE_ACCUMULATING`은 exact-date floor 충족까지 수집·재검증한다. "
                    "`CANDIDATE_QUEUE_HANDOFF|COMPLETE`는 closed 상태이므로 report에서 제외되고 다음 refresh에서 builder-owned 항목이 제거된다.",
                    "권한 경계: 이 POSTCLOSE 후속 항목은 source-only 구현·검증 작업이며 runtime env, 실주문, target/timeout/cooldown/cap, threshold, provider/bot, hard safety 또는 broker guard 변경 권한이 없다.",
                ),
            )
        )
    if machine_micro_approval_source_status != "loaded":
        machine_micro_approval_path = (
            MACHINE_MICROSTRUCTURE_POLICY_APPROVAL_REPORT_DIR
            / f"machine_microstructure_policy_approval_postclose_{source_date}.json"
        )
        source_status = _compact_inline_value(
            machine_micro_approval_source_status,
            fallback="unknown_source_gap",
        )
        tasks.append(
            GeneratedTask(
                task_id=f"MachineMicroPolicyApprovalSourceGap{mmdd}",
                title="micro 정책 승인·목적 ledger source gap 복구",
                slot="POSTCLOSE",
                time_window="21:25~21:30",
                track="RuntimeStability",
                source=(
                    f"[machine_microstructure_policy_approval_postclose_{source_date}.json]"
                    f"(/home/ubuntu/KORStockScan/{_rel(machine_micro_approval_path)}), "
                    "[machine_microstructure_policy_approval.py]"
                    "(/home/ubuntu/KORStockScan/src/engine/automation/"
                    "machine_microstructure_policy_approval.py), "
                    "[widget expansion service]"
                    "(/home/ubuntu/KORStockScan/deploy/systemd/"
                    "korstockscan-widget-expansion-recommendation.service)"
                ),
                lines=(
                    "판정 기준: 21:15 final refresh의 exact-date POSTCLOSE approval report가 "
                    f"`source_status={source_status}`이므로 schema/phase/target-date/non-runtime authority와 generated-at/source hash·mtime predecessor 계약을 복구하고 checklist를 재생성한다.",
                    "완료 조건: 동일 source date의 approval report가 현재 attribution source hash·mtime 이후의 exact contract로 재생성되고, 미완료 objective는 별도 POSTCLOSE followup task로 이월되며 closed objective는 제거되어야 한다.",
                    "권한 경계: source gap 복구는 report/checklist 제어면 작업이며 runtime env, 실주문, threshold, provider/bot, hard safety 또는 broker guard 변경 권한이 없다.",
                ),
            )
        )
    for workorder in main_ai_quality_workorders:
        owner = str(workorder.get("owner") or "UnknownOwner").strip()
        owner_token = re.sub(r"[^A-Za-z0-9]", "", owner) or "UnknownOwner"
        reason_codes = ", ".join(
            _compact_inline_value(reason)
            for reason in workorder.get("reason_codes") or []
        )
        # Acceptance is an executable contract, not a display-only summary.
        # Preserve it in full so the next-day task never ends with a truncated
        # or semantically incomplete condition.
        acceptance = _compact_inline_value(
            workorder.get("acceptance_test"),
            max_length=None,
        )
        if owner == "MicroReversionForwardCollectorContinuity":
            slot = "PREOPEN"
            time_window = "08:40~08:45"
            title = "micro observer 저장공간·연속수집 source gap 복구 확인"
            owner_action = (
                "장전 free bytes가 writer low-disk watermark를 충분히 상회하는지 "
                "확인하고, 부족하면 실주문과 무관한 closed-date verified compression만 "
                "실행한 뒤 observer canary를 재검증한다."
            )
        elif owner == "MicroReversionIntegratedRouteProof":
            slot = "POSTCLOSE"
            time_window = "17:40~18:00"
            title = "micro integrated-route exact proof source gap 복구 확인"
            owner_action = (
                "동일 request의 explicit route item과 raw venue/session proof를 대사하고, "
                "ambiguous SOR row는 거래소를 추정하지 않은 채 exact window에서 제외한다."
            )
        elif owner == "MainAIQualityMaterializedCompanionBindingRepair":
            slot = "POSTCLOSE"
            time_window = "18:00~18:20"
            title = "main AI materialized companion exact-hash 결속 복구 확인"
            owner_action = (
                "reason_codes에 명시된 source date별 execution report와 materialized "
                "request/response companion의 exact hash를 재검증하고, 불변 원천에 "
                "결속할 수 없는 historical row는 합성 없이 제외한다."
            )
        else:
            slot = "POSTCLOSE"
            time_window = "18:00~18:20"
            title = f"{owner} main lifecycle source gap 복구 확인"
            owner_action = (
                "공식 raw execution envelope의 order/execution identity를 합성 없이 "
                "검증하고 결손 lifecycle만 제외한 뒤 paired producer를 재검증한다."
            )
        tasks.append(
            GeneratedTask(
                task_id=f"MainAIQualitySourceGap{owner_token}{mmdd}",
                title=title,
                slot=slot,
                time_window=time_window,
                track="RuntimeStability" if slot == "PREOPEN" else "ScalpingLogic",
                source=(
                    f"[main_ai_quality_r0_r3_cycle_{source_date}.json]"
                    f"(/home/ubuntu/KORStockScan/{_rel(main_ai_quality_path)})"
                ),
                lines=(
                    f"판정 기준: workorder `{workorder.get('workorder_id')}`의 owner=`{owner}`, reason_codes=`{reason_codes}`를 source-only producer 보완으로 닫는다. {owner_action}",
                    f"완료 조건: {acceptance}",
                    "권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.",
                ),
            )
        )
    if main_ai_quality_source_status not in {"loaded", "not_available"}:
        tasks.append(
            GeneratedTask(
                task_id=f"MainAIQualitySourceGapArtifactContract{mmdd}",
                title="main AI R0→R3 source-gap workorder artifact 계약 복구",
                slot="POSTCLOSE",
                time_window="21:40~21:50",
                track="RuntimeStability",
                source=(
                    f"[main_ai_quality_r0_r3_cycle_{source_date}.json]"
                    f"(/home/ubuntu/KORStockScan/{_rel(main_ai_quality_path)})"
                ),
                lines=(
                    f"판정 기준: source_status=`{main_ai_quality_source_status}`인 exact-date cycle report의 schema/content hash/non-runtime authority/workorder identity를 복구하고 checklist를 재생성한다.",
                    "금지: invalid report의 workorder 문구를 신뢰하거나 source gap을 runtime/order/provider 변경으로 우회하지 않는다.",
                    "완료 조건: report와 nested diagnostics의 hash-bound workorder 목록이 일치하고 각 open workorder가 owner별 checklist 항목으로 생성되어야 한다.",
                ),
            )
        )
    if _has_approval_request(ev_report, swing_report):
        tasks.append(
            GeneratedTask(
                task_id=f"SwingPreFinalAutoAndFinalApprovalPreopen{mmdd}",
                title="스윙 pre-final auto state 및 final approval artifact 확인",
                slot="PREOPEN",
                time_window="08:45~08:50",
                track="RuntimeStability",
                source=(
                    f"[swing_runtime_approval_{source_date}.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_{source_date}.json), "
                    f"[threshold_cycle_ev_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(ev_path)})"
                ),
                lines=(
                    "판정 기준: pre-final은 parsed AI Tier2 auto state가 있어야 하고, final-stage는 사용자 승인 artifact가 있어야 한다.",
                    "금지: 스윙 full-live 전환, cap release, provider/bot 변경, hard-safety 완화를 pre-final auto state로 처리하지 않는다.",
                    "다음 액션: `pre_final_auto_selected`, `final_approval_artifact_present`, `blocked_by_policy` 중 하나로 닫는다.",
                ),
            )
        )
    selected = _list_selected_families(ev_report)
    if _has_runtime_change(ev_report):
        tasks.append(
            GeneratedTask(
                task_id=f"RuntimeEnvIntradayObserve{mmdd}",
                title="전일 selected runtime family 장중 provenance 및 rollback guard 확인",
                slot="INTRADAY",
                time_window="09:05~09:20",
                track="RuntimeStability",
                source=f"[threshold_cycle_ev_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(ev_path)})",
                lines=(
                    f"전일 postclose candidate_selected_families={', '.join(selected) if selected else '-'}이며 실제 기동 기대 목록으로 직접 사용하지 않는다.",
                    "판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.",
                    "금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.",
                    "다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.",
                ),
            )
        )
    if _has_sim_probe_activity(ev_report):
        tasks.append(
            GeneratedTask(
                task_id=f"SimProbeIntradayCoverage{mmdd}",
                title="sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인",
                slot="INTRADAY",
                time_window="09:35~09:50",
                track="ScalpingLogic",
                source=f"[threshold_cycle_ev_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(ev_path)})",
                lines=(
                    "판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.",
                    "금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.",
                    "다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.",
                ),
            )
        )
    tasks.append(
        GeneratedTask(
            task_id=f"IntradaySourceQualityGateCheck{mmdd}",
            title="장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인",
            slot="INTRADAY",
            time_window="14:20~14:35",
            track="RuntimeStability",
            source=(
                f"[pipeline_events_{target_date}.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_{target_date}.jsonl), "
                f"[threshold_events_{target_date}.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_{target_date}.jsonl), "
                f"[observation_source_quality_audit_{target_date}.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_{target_date}.json), "
                "[observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)"
            ),
            lines=(
                f"판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date {target_date} --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.",
                "금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.",
                "다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.",
            ),
        )
    )
    tasks.extend(
        [
            GeneratedTask(
                task_id=f"ThresholdDailyEVReport{mmdd}",
                title="daily EV real/sim/combined split 및 자동 반영 결과 확인",
                slot="POSTCLOSE",
                time_window="16:30~16:45",
                track="RuntimeStability",
                source=tuning_sources,
                lines=(
                    tuning_decision_line,
                    "금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.",
                    "다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.",
                ),
            ),
            GeneratedTask(
                task_id=f"PostcloseSourceQualityGateReview{mmdd}",
                title="장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인",
                slot="POSTCLOSE",
                time_window="21:40~21:55",
                track="RuntimeStability",
                source=(
                    f"[observation_source_quality_audit_{target_date}.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_{target_date}.json), "
                    f"[threshold_cycle_ev_{target_date}.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_{target_date}.json), "
                    f"[code_improvement_workorder_{target_date}.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_{target_date}.json), "
                    f"[threshold_cycle_postclose_verification_{target_date}.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_{target_date}.json)"
                ),
                lines=(
                    "판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.",
                    "금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.",
                    "다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.",
                ),
            ),
            GeneratedTask(
                task_id=f"HumanInterventionSummary{mmdd}",
                title="자동화체인 사용자 개입 요구사항 분류 및 누락 확인",
                slot="POSTCLOSE",
                time_window="17:00~17:15",
                track="RuntimeStability",
                source=(
                    f"[threshold_cycle_ev_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(ev_path)}), "
                    "[time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)"
                ),
                lines=(
                    "판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.",
                    "금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.",
                    "다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.",
                ),
            ),
        ]
    )
    if _has_payload(code_report) and code_md_path.exists():
        tasks.append(
            GeneratedTask(
                task_id=f"CodeImprovementWorkorderReview{mmdd}",
                title="code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인",
                slot="POSTCLOSE",
                time_window="21:15~21:25",
                track="ScalpingLogic",
                source=(
                    f"[code_improvement_workorder_{source_date}.md](/home/ubuntu/KORStockScan/{_rel(code_md_path)}), "
                    f"[code_improvement_workorder_{source_date}.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_{source_date}.json)"
                ),
                lines=(
                    f"판정 기준: selected_order_count={_code_workorder_count(ev_report, code_report)}와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.",
                    "금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.",
                    "다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.",
                ),
            )
        )
    if _has_payload(trigger_report):
        tasks.append(
            GeneratedTask(
                task_id=f"AutomationTriggerDecisionSummary{mmdd}",
                title="자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인",
                slot="POSTCLOSE",
                time_window="21:40~21:55",
                track="RuntimeStability",
                source=(
                    f"[automation_chain_trigger_decision_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(trigger_decision_path)}), "
                    "[run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)"
                ),
                lines=(
                    f"판정 기준: trigger decision summary의 {trigger_decision_summary}를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.",
                    "금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.",
                    "다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.",
                ),
            ),
        )
    tasks.extend(
        [
            *(
                [
                    GeneratedTask(
                        task_id=f"RuntimeApplyGapDirectiveReview{mmdd}",
                        title="runtime apply gap Codex 작업지시 표면화 및 구현 여부 확인",
                        slot="POSTCLOSE",
                        time_window="21:25~21:40",
                        track="ScalpingLogic",
                        source=(
                            f"[runtime_apply_gap_audit_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(runtime_gap_path)}), "
                            f"[runtime_apply_gap_audit_{source_date}.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_{source_date}.md), "
                            "[runtime-apply-gap-audit-user-guide.md](/home/ubuntu/KORStockScan/docs/runtime-apply-gap-audit-user-guide.md)"
                        ),
                        lines=(
                            f"판정 기준: runtime apply gap audit의 Codex 작업지시 {runtime_gap_directives}를 구현 필요, 이미 해결, 설계 보류, reject로 분류한다.",
                            "금지: 작업지시만을 approval artifact나 즉시 runtime env 수정 권한으로 해석하지 않는다. 장중 반영은 별도의 사용자 명시 지시와 bounded 단일축 계약이 필요하며 broker/order/provider/cap guard는 우회하지 않는다.",
                            "다음 액션: `implement_now`, `already_implemented`, `defer_design`, `reject`, `needs_new_workorder` 중 하나로 닫고, 구현 시 테스트와 postclose verifier handoff를 같이 확인한다.",
                        ),
                    )
                ]
                if runtime_gap_directives
                else []
            ),
            *(
                [
                    GeneratedTask(
                        task_id=f"LifecycleSourceDimensionGapReview{mmdd}",
                        title="lifecycle source dimension gap 자동 표면화 및 처리 확인",
                        slot="POSTCLOSE",
                        time_window="21:25~21:40",
                        track="ScalpingLogic",
                        source=(
                            f"[runtime_apply_gap_audit_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(runtime_gap_path)}), "
                            f"[runtime_apply_gap_audit_{source_date}.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_{source_date}.md)"
                        ),
                        lines=(
                            f"판정 기준: source dimension gap summary의 {source_dimension_gap_summary}를 확인하고 workorder/checklist 표면화 누락 여부를 닫는다.",
                            "금지: source-dimension gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.",
                            "다음 액션: `implement_now`, `already_covered_by_fallback`, `rollup_only`, `defer_until_postclose_report`, `reject_not_applicable` 중 하나로 닫는다.",
                        ),
                    )
                ]
                if source_dimension_gap_summary and not runtime_gap_directives
                else []
            ),
            *(
                [
                    GeneratedTask(
                        task_id=f"LifecycleQuietGapReview{mmdd}",
                        title="lifecycle quiet gap rollup 자동 표면화 및 처리 확인",
                        slot="POSTCLOSE",
                        time_window="21:25~21:40",
                        track="ScalpingLogic",
                        source=(
                            f"[runtime_apply_gap_audit_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(runtime_gap_path)}), "
                            f"[runtime_apply_gap_audit_{source_date}.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_{source_date}.md)"
                        ),
                        lines=(
                            f"판정 기준: quiet gap summary의 {quiet_gap_summary}를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.",
                            "금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.",
                            "다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.",
                        ),
                    )
                ]
                if quiet_gap_summary and not runtime_gap_directives
                else []
            ),
        ]
    )
    return tasks


def _render_auto_block(
    *,
    source_date: str,
    target_date: str,
    ev_report: dict[str, Any],
    swing_report: dict[str, Any],
    code_report: dict[str, Any],
    runtime_gap_report: dict[str, Any],
    trigger_report: dict[str, Any],
    rising_missed_report: dict[str, Any],
    machine_micro_approval_report: dict[str, Any],
    machine_micro_approval_source_status: str,
    main_ai_quality_workorders: list[dict[str, Any]],
    main_ai_quality_source_status: str,
    exclude_task_ids: set[str] | None = None,
) -> str:
    tasks = _build_tasks(
        source_date=source_date,
        target_date=target_date,
        ev_report=ev_report,
        swing_report=swing_report,
        code_report=code_report,
        runtime_gap_report=runtime_gap_report,
        trigger_report=trigger_report,
        rising_missed_report=rising_missed_report,
        machine_micro_approval_report=machine_micro_approval_report,
        machine_micro_approval_source_status=machine_micro_approval_source_status,
        main_ai_quality_workorders=main_ai_quality_workorders,
        main_ai_quality_source_status=main_ai_quality_source_status,
    )
    exclude_task_ids = exclude_task_ids or set()
    tasks = [task for task in tasks if task.task_id not in exclude_task_ids]
    tasks.sort(key=_task_sort_key)
    by_slot = {"PREOPEN": [], "INTRADAY": [], "POSTCLOSE": []}
    for task in tasks:
        by_slot.setdefault(task.slot, []).append(task)

    lines = [
        AUTO_START,
        f"## 자동 생성 체크리스트 (`{source_date}` postclose -> `{target_date}`)",
        "",
        "- 이 블록은 postclose 자동화 산출물에서 생성된다.",
        "- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.",
        "- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.",
        "",
    ]
    sections = (
        ("PREOPEN", "장전 체크리스트 (07:45~09:00)"),
        ("INTRADAY", "장중 체크리스트 (09:05~15:20)"),
        ("POSTCLOSE", "장후 체크리스트 (16:25~21:55)"),
    )
    for slot, heading in sections:
        lines.append(f"## {heading}")
        lines.append("")
        if not by_slot.get(slot):
            lines.append("- 해당 슬롯 자동 생성 항목 없음.")
            lines.append("")
            continue
        for task in by_slot[slot]:
            lines.extend(_render_task(task, target_date))
    lines.append(AUTO_END)
    return "\n".join(lines).rstrip() + "\n"


def _render_new_document(target_date: str, auto_block: str) -> str:
    return "\n".join(
        [
            f"# {target_date} Stage2 To-Do Checklist",
            "",
            "## 오늘 목적",
            "",
            "- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.",
            "- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.",
            "- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.",
            "",
            "## 오늘 강제 규칙",
            "",
            "- 장중 runtime 변경은 사용자 명시 지시가 있을 때만 기존 `bounded_tunable` 단일 축에 한해 허용한다. fresh/conflict-free source, 유효 effective price, 단일 blocker 인과, same-stage owner 비충돌, before/after·PID/env provenance·rollback·즉시 attribution을 모두 남긴다. hard safety, stale/conflict, price freshness, broker/account/order/quantity/cooldown, provider, bot, cap, 요청수량은 변경하거나 우회하지 않는다.",
            "- 튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-05`, `clean_tuning_baseline_ts_kst=2026-06-05T00:00:00+09:00`이다. 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 보고 EV/rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다.",
            "- Baseline 이후 raw source-quality contract 결손은 날짜 전체 차단이 아니라 결손 row/window를 `raw_row_exclusion`으로 제외하는 것이 기본이다. 전체 block은 preflight missing/invalid, row/window exclusion 실패, 또는 결손을 안정적으로 특정할 수 없는 high-volume no-contract 상황에만 사용한다.",
            "- 장중과 장후에는 `observation_source_quality_audit --write` 또는 최신 artifact로 raw source-quality를 반복 확인한다. Hard contract gap은 결손 row/window 제외 또는 `source_quality_blocked` 없이는 튜닝 입력에 들어갈 수 없고, unknown-token warning은 hard block이 아니더라도 code-improvement workorder handoff 확인 대상이다.",
            "- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.",
            "- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.",
            "- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.",
            "",
            auto_block.rstrip(),
            "",
            _render_sync_section().rstrip(),
            "",
        ]
    )


def _render_sync_section() -> str:
    return "\n".join(
        [
            "## Project/Calendar 동기화",
            "",
            "문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.",
            "",
            "```bash",
            SYNC_COMMAND,
            "```",
        ]
    )


def _upsert_auto_block(existing: str, auto_block: str) -> str:
    if AUTO_START in existing and AUTO_END in existing:
        prefix, rest = existing.split(AUTO_START, 1)
        _, suffix = rest.split(AUTO_END, 1)
        return (
            prefix.rstrip()
            + "\n\n"
            + auto_block.rstrip()
            + "\n\n"
            + suffix.lstrip("\r\n")
        )

    sync_heading = "\n## Project/Calendar 동기화"
    if sync_heading in existing:
        prefix, suffix = existing.split(sync_heading, 1)
        return (
            prefix.rstrip()
            + "\n\n"
            + auto_block.rstrip()
            + "\n"
            + sync_heading
            + suffix
        )

    suffix = "" if existing.endswith("\n") else "\n"
    return existing + suffix + "\n" + auto_block


def _manual_text_without_auto_block(existing: str) -> str:
    if AUTO_START not in existing or AUTO_END not in existing:
        return existing
    prefix, rest = existing.split(AUTO_START, 1)
    _, suffix = rest.split(AUTO_END, 1)
    return prefix + suffix


def _auto_block_text(existing: str) -> str:
    if AUTO_START not in existing or AUTO_END not in existing:
        return ""
    _, rest = existing.split(AUTO_START, 1)
    body, _ = rest.split(AUTO_END, 1)
    return AUTO_START + body + AUTO_END


def _existing_manual_task_ids(existing: str) -> set[str]:
    text = _manual_text_without_auto_block(existing)
    return {match.group(1) for match in re.finditer(r"`\[([A-Za-z0-9_:-]+)\]", text)}


def _task_ids_from_text(text: str) -> set[str]:
    return {
        match.group(1)
        for match in re.finditer(
            r"^- \[[ xX]\] `\[([A-Za-z0-9_:-]+)\]", text, re.MULTILINE
        )
    }


def _task_slot_from_block(block: str, fallback_slot: str) -> str:
    match = re.search(r"`Slot:\s*([A-Z_]+)`", block)
    if match:
        return match.group(1)
    return fallback_slot


def _is_builder_owned_conditional_task(task_id: str) -> bool:
    return task_id.startswith(
        MACHINE_MICROSTRUCTURE_BUILDER_OWNED_CONDITIONAL_TASK_PREFIXES
    )


def _preserved_auto_task_blocks(
    existing: str, generated_task_ids: set[str]
) -> dict[str, list[str]]:
    text = _auto_block_text(existing)
    if not text:
        return {}
    preserved: dict[str, list[str]] = {"PREOPEN": [], "INTRADAY": [], "POSTCLOSE": []}
    current_slot = ""
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("## 장전"):
            current_slot = "PREOPEN"
        elif line.startswith("## 장중"):
            current_slot = "INTRADAY"
        elif line.startswith("## 장후"):
            current_slot = "POSTCLOSE"

        if re.match(r"^- \[[ xX]\] `\[[A-Za-z0-9_:-]+]", line):
            if current:
                block = "\n".join(current).rstrip()
                task_id_match = re.match(
                    r"^- \[[ xX]\] `\[([A-Za-z0-9_:-]+)]", current[0]
                )
                task_id = task_id_match.group(1) if task_id_match else ""
                if (
                    task_id
                    and task_id not in generated_task_ids
                    and not _is_builder_owned_conditional_task(task_id)
                ):
                    slot = _task_slot_from_block(block, current_slot or "POSTCLOSE")
                    preserved.setdefault(slot, []).append(block)
            current = [line]
            continue

        if current:
            if line.startswith("## ") or line == AUTO_END:
                block = "\n".join(current).rstrip()
                task_id_match = re.match(
                    r"^- \[[ xX]\] `\[([A-Za-z0-9_:-]+)]", current[0]
                )
                task_id = task_id_match.group(1) if task_id_match else ""
                if (
                    task_id
                    and task_id not in generated_task_ids
                    and not _is_builder_owned_conditional_task(task_id)
                ):
                    slot = _task_slot_from_block(block, current_slot or "POSTCLOSE")
                    preserved.setdefault(slot, []).append(block)
                current = []
            else:
                current.append(line)
    if current:
        block = "\n".join(current).rstrip()
        task_id_match = re.match(r"^- \[[ xX]\] `\[([A-Za-z0-9_:-]+)]", current[0])
        task_id = task_id_match.group(1) if task_id_match else ""
        if (
            task_id
            and task_id not in generated_task_ids
            and not _is_builder_owned_conditional_task(task_id)
        ):
            slot = _task_slot_from_block(block, current_slot or "POSTCLOSE")
            preserved.setdefault(slot, []).append(block)
    return {slot: blocks for slot, blocks in preserved.items() if blocks}


def _merge_preserved_auto_tasks(existing: str, auto_block: str) -> str:
    preserved = _preserved_auto_task_blocks(existing, _task_ids_from_text(auto_block))
    if not preserved:
        return auto_block
    lines: list[str] = []
    current_slot = ""

    def flush_slot(slot: str) -> None:
        if not slot:
            return
        for block in preserved.pop(slot, []):
            if lines and lines[-1] != "":
                lines.append("")
            lines.extend(block.splitlines())
            lines.append("")

    for line in auto_block.splitlines():
        if line.startswith("## 장전"):
            flush_slot(current_slot)
            current_slot = "PREOPEN"
        elif line.startswith("## 장중"):
            flush_slot(current_slot)
            current_slot = "INTRADAY"
        elif line.startswith("## 장후"):
            flush_slot(current_slot)
            current_slot = "POSTCLOSE"
        if line == AUTO_END:
            flush_slot(current_slot)
            current_slot = ""
        lines.append(line)
    if preserved:
        insert_at = len(lines) - 1 if lines and lines[-1] == AUTO_END else len(lines)
        extra: list[str] = []
        for blocks in preserved.values():
            for block in blocks:
                if extra and extra[-1] != "":
                    extra.append("")
                extra.extend(block.splitlines())
                extra.append("")
        lines[insert_at:insert_at] = extra
    return "\n".join(lines).rstrip() + "\n"


@contextmanager
def _checklist_write_lock(target_path: Path) -> Iterator[None]:
    lock_path = CHECKLIST_LOCK_DIR / f"{target_path.name}.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _atomic_write_checklist(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_mode = path.stat().st_mode & 0o777 if path.exists() else 0o664
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temporary_path.chmod(existing_mode)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def build_next_stage2_checklist(
    source_date: str, *, machine_micro_approval_not_before: datetime | None = None
) -> dict[str, Any]:
    source_date = str(source_date).strip()
    if not source_date:
        raise ValueError("source_date is required")
    date.fromisoformat(source_date)
    target_date = _next_krx_trading_day(source_date)
    target_path = stage2_checklist_path(target_date)
    with _checklist_write_lock(target_path):
        return _build_next_stage2_checklist_locked(
            source_date=source_date,
            target_date=target_date,
            target_path=target_path,
            machine_micro_approval_not_before=machine_micro_approval_not_before,
        )


def _build_next_stage2_checklist_locked(
    *,
    source_date: str,
    target_date: str,
    target_path: Path,
    machine_micro_approval_not_before: datetime | None = None,
) -> dict[str, Any]:
    missing_required = _missing_required_postclose_artifacts(source_date)
    if missing_required:
        missing = ", ".join(_rel(path) for path in missing_required)
        raise RuntimeError(
            f"required postclose artifacts are missing for {source_date}: {missing}"
        )
    ev_report = _load_json(EV_REPORT_DIR / f"threshold_cycle_ev_{source_date}.json")
    swing_report = _load_json(
        SWING_RUNTIME_APPROVAL_DIR / f"swing_runtime_approval_{source_date}.json"
    )
    code_report = _load_json(
        CODE_IMPROVEMENT_REPORT_DIR / f"code_improvement_workorder_{source_date}.json"
    )
    runtime_gap_report = _load_json(
        RUNTIME_APPLY_GAP_REPORT_DIR / f"runtime_apply_gap_audit_{source_date}.json"
    )
    trigger_report = _load_json(
        AUTOMATION_TRIGGER_DECISION_REPORT_DIR
        / f"automation_chain_trigger_decision_{source_date}.json"
    )
    rising_missed_report = _load_json(
        RISING_MISSED_SCOUT_WORKORDER_REPORT_DIR
        / f"rising_missed_scout_workorder_{source_date}.json"
    )
    machine_micro_approval_report, machine_micro_approval_source_status = (
        _load_machine_microstructure_approval_report(
            MACHINE_MICROSTRUCTURE_POLICY_APPROVAL_REPORT_DIR
            / f"machine_microstructure_policy_approval_postclose_{source_date}.json",
            source_date=source_date,
            attribution_path=(
                MACHINE_MICROSTRUCTURE_ATTRIBUTION_REPORT_DIR
                / f"machine_microstructure_attribution_{source_date}.json"
            ),
            approval_not_before=machine_micro_approval_not_before,
        )
    )
    main_ai_quality_workorders, main_ai_quality_source_status = (
        _load_main_ai_quality_workorders(
            MAIN_AI_QUALITY_REPORT_DIR
            / f"main_ai_quality_r0_r3_cycle_{source_date}.json",
            source_date=source_date,
        )
    )
    existing = target_path.read_text(encoding="utf-8") if target_path.exists() else ""
    exclude_task_ids = _existing_manual_task_ids(existing) if existing else set()
    auto_block = _render_auto_block(
        source_date=source_date,
        target_date=target_date,
        ev_report=ev_report,
        swing_report=swing_report,
        code_report=code_report,
        runtime_gap_report=runtime_gap_report,
        trigger_report=trigger_report,
        rising_missed_report=rising_missed_report,
        machine_micro_approval_report=machine_micro_approval_report,
        machine_micro_approval_source_status=machine_micro_approval_source_status,
        main_ai_quality_workorders=main_ai_quality_workorders,
        main_ai_quality_source_status=main_ai_quality_source_status,
        exclude_task_ids=exclude_task_ids,
    )
    if existing:
        auto_block = _merge_preserved_auto_tasks(existing, auto_block)

    if existing:
        content = _upsert_auto_block(existing, auto_block)
        created = False
    else:
        content = _render_new_document(target_date, auto_block)
        created = True

    _atomic_write_checklist(target_path, content)
    tasks = _build_tasks(
        source_date=source_date,
        target_date=target_date,
        ev_report=ev_report,
        swing_report=swing_report,
        code_report=code_report,
        runtime_gap_report=runtime_gap_report,
        trigger_report=trigger_report,
        rising_missed_report=rising_missed_report,
        machine_micro_approval_report=machine_micro_approval_report,
        machine_micro_approval_source_status=machine_micro_approval_source_status,
        main_ai_quality_workorders=main_ai_quality_workorders,
        main_ai_quality_source_status=main_ai_quality_source_status,
    )
    tasks = [task for task in tasks if task.task_id not in exclude_task_ids]
    tasks.sort(key=_task_sort_key)
    return {
        "source_date": source_date,
        "target_date": target_date,
        "path": str(target_path),
        "created": created,
        "task_count": len(tasks),
        "tasks": [task.task_id for task in tasks],
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build next trading day's stage2 checklist from postclose outputs."
    )
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "--source-date",
        default="",
        help="Postclose source date in YYYY-MM-DD. Defaults to KST today.",
    )
    source_group.add_argument(
        "--completed-machine-source-date",
        nargs="?",
        const="__resolve_completed_machine_source_date__",
        default=None,
        metavar="YYYY-MM-DD",
        help=(
            "Use the supplied completed KRX machine target date, or resolve it "
            "when the flag has no value. Intended for the persistent 21:15 "
            "machine final-refresh service."
        ),
    )
    args = parser.parse_args()
    invoked_at = datetime.now(ZoneInfo("Asia/Seoul"))
    source_date = args.source_date.strip()
    if args.completed_machine_source_date is not None:
        source_date = (
            resolve_completed_machine_target_date().isoformat()
            if args.completed_machine_source_date
            == "__resolve_completed_machine_source_date__"
            else str(args.completed_machine_source_date).strip()
        )
        date.fromisoformat(source_date)
    elif not source_date:
        source_date = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    summary = build_next_stage2_checklist(
        source_date,
        machine_micro_approval_not_before=(
            invoked_at - MACHINE_MICROSTRUCTURE_COMPLETED_REFRESH_MAX_AGE
            if args.completed_machine_source_date
            else None
        ),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[NEXT_STAGE2_CHECKLIST_ERROR] {exc}", file=sys.stderr)
        raise
