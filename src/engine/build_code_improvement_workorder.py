"""Build Codex-ready code improvement workorders from postclose automation."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = PROJECT_ROOT / "data" / "report"
PATTERN_LAB_AUTOMATION_DIR = REPORT_DIR / "scalping_pattern_lab_automation"
SWING_IMPROVEMENT_AUTOMATION_DIR = REPORT_DIR / "swing_improvement_automation"
SWING_PATTERN_LAB_AUTOMATION_DIR = REPORT_DIR / "swing_pattern_lab_automation"
SWING_STRATEGY_DISCOVERY_EV_DIR = REPORT_DIR / "swing_strategy_discovery_ev"
SWING_LIFECYCLE_DECISION_MATRIX_DIR = REPORT_DIR / "swing_lifecycle_decision_matrix"
SWING_LIFECYCLE_BUCKET_DISCOVERY_DIR = REPORT_DIR / "swing_lifecycle_bucket_discovery"
PATTERN_LAB_AI_REVIEW_DIR = REPORT_DIR / "pattern_lab_ai_review"
THRESHOLD_CYCLE_EV_DIR = REPORT_DIR / "threshold_cycle_ev"
HOLDING_EXIT_DECISION_MATRIX_DIR = REPORT_DIR / "holding_exit_decision_matrix"
LIFECYCLE_DECISION_MATRIX_DIR = REPORT_DIR / "lifecycle_decision_matrix"
PIPELINE_EVENT_VERBOSITY_DIR = REPORT_DIR / "pipeline_event_verbosity"
OBSERVATION_SOURCE_QUALITY_AUDIT_DIR = REPORT_DIR / "observation_source_quality_audit"
CODEBASE_PERFORMANCE_WORKORDER_DIR = REPORT_DIR / "codebase_performance_workorder"
PATTERN_LAB_CURRENTNESS_AUDIT_DIR = REPORT_DIR / "pattern_lab_currentness_audit"
BUY_FUNNEL_SENTINEL_DIR = REPORT_DIR / "buy_funnel_sentinel"
PRODUCER_GAP_DISCOVERY_DIR = REPORT_DIR / "producer_gap_discovery"
STAGE_HOOK_WORKORDER_DISCOVERY_DIR = REPORT_DIR / "stage_hook_workorder_discovery"
STAGE_HOOK_RUNTIME_SCAFFOLD_DIR = REPORT_DIR / "stage_hook_runtime_scaffold"
CONVERSION_LANE_DIR = REPORT_DIR / "conversion_lane"
CODE_IMPROVEMENT_WORKORDER_DIR = PROJECT_ROOT / "docs" / "code-improvement-workorders"
CODE_IMPROVEMENT_WORKORDER_REPORT_DIR = REPORT_DIR / "code_improvement_workorder"
WORKORDER_SCHEMA_VERSION = 1
IMPLEMENTED_STATUSES = {
    "implemented",
    "implemented_but_hold_sample",
    "implemented_but_waiting_sample",
    "implemented_submit_contract_verified",
    "implemented_source_quality_contract_available",
    "implemented_source_quality_contract_waiting_sample",
}
TERMINAL_NON_IMPLEMENT_STATUSES = {
    "terminal_design_family_candidate",
    "terminal_deferred_evidence",
    "terminal_existing_family_evidence",
    "terminal_not_applicable_evidence",
    "terminal_rejected",
}

KNOWN_FIXED_UNKNOWN_TOKEN_FIELDS = {
    "swing_micro_ws_quote_stale",
    "lifecycle_bucket_entry_bucket_key",
    "lifecycle_bucket_entry_bucket_id",
    "lifecycle_bucket_bucket_id",
    "pre_submit_liquidity_value",
    "overbought_guard_reason",
    "pre_submit_overbought_reason",
    "holding_exit_matrix_decision_alignment",
    "sim_pre_submit_overbought_reason",
    "broker_receipt_status",
    "fill_quality",
}


DECISION_RANK = {
    "implement_now": 0,
    "attach_existing_family": 1,
    "design_family_candidate": 2,
    "defer_evidence": 3,
    "reject": 4,
}


@dataclass(frozen=True)
class ClassifiedOrder:
    order: dict[str, Any]
    decision: str
    reason: str
    mapped_family: str | None
    route: str | None
    confidence: str | None
    automation_reentry: str
    decision_source: str | None = None


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _file_fingerprint(path: Path, label: str) -> dict[str, Any]:
    exists = path.exists()
    payload = b""
    if exists:
        try:
            payload = path.read_bytes()
        except OSError:
            payload = b""
    stat = path.stat() if exists else None
    return {
        "label": label,
        "path": str(path),
        "exists": bool(exists),
        "size_bytes": int(stat.st_size) if stat else 0,
        "mtime_ns": int(stat.st_mtime_ns) if stat else None,
        "sha256": hashlib.sha256(payload).hexdigest() if exists else None,
    }


def _source_fingerprint(source_paths: dict[str, Path]) -> dict[str, Any]:
    files = [_file_fingerprint(path, label) for label, path in sorted(source_paths.items())]
    hash_input = json.dumps(files, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    source_hash = hashlib.sha256(hash_input).hexdigest()
    return {
        "source_hash": source_hash,
        "generation_id": source_hash[:12],
        "files": files,
    }


def _previous_workorder_lineage(previous_report: dict[str, Any], current_orders: list[dict[str, Any]]) -> dict[str, Any]:
    previous_orders = previous_report.get("orders") if isinstance(previous_report.get("orders"), list) else []
    previous_by_id = {
        str(order.get("order_id")): order
        for order in previous_orders
        if isinstance(order, dict) and order.get("order_id") not in (None, "")
    }
    current_by_id = {
        str(order.get("order_id")): order
        for order in current_orders
        if isinstance(order, dict) and order.get("order_id") not in (None, "")
    }
    previous_ids = set(previous_by_id)
    current_ids = set(current_by_id)
    decision_changed = sorted(
        order_id
        for order_id in previous_ids & current_ids
        if previous_by_id[order_id].get("decision") != current_by_id[order_id].get("decision")
    )
    return {
        "previous_exists": bool(previous_report),
        "previous_generation_id": previous_report.get("generation_id"),
        "previous_source_hash": previous_report.get("source_hash"),
        "previous_generated_at": previous_report.get("generated_at"),
        "new_order_ids": sorted(current_ids - previous_ids),
        "removed_order_ids": sorted(previous_ids - current_ids),
        "unchanged_order_ids": sorted(current_ids & previous_ids),
        "decision_changed_order_ids": decision_changed,
    }


def conversion_lane_report_path(target_date: str) -> Path:
    return CONVERSION_LANE_DIR / f"conversion_lane_{target_date}.json"


def _conversion_rank_by_candidate(conversion_lane: dict[str, Any]) -> dict[str, dict[str, Any]]:
    ranked: dict[str, dict[str, Any]] = {}
    for item in conversion_lane.get("conversion_blocker_rank") or []:
        if not isinstance(item, dict):
            continue
        candidate_id = str(item.get("conversion_candidate_id") or "").strip()
        if not candidate_id:
            continue
        existing = ranked.get(candidate_id)
        if existing and _safe_int(existing.get("conversion_impact_rank"), 999) <= _safe_int(item.get("conversion_impact_rank"), 999):
            continue
        ranked[candidate_id] = item
    return ranked


def _annotate_order_conversion_fields(order: dict[str, Any], conversion_rank: dict[str, dict[str, Any]]) -> dict[str, Any]:
    candidate_keys = [
        str(order.get(key) or "").strip()
        for key in (
            "conversion_candidate_id",
            "candidate_id",
            "bucket_id",
            "threshold_family",
            "family",
            "source_bucket_id",
        )
    ]
    candidate_keys.extend(str(item) for item in (order.get("candidate_ids") or []) if str(item or "").strip())
    blocker: dict[str, Any] = {}
    for key in candidate_keys:
        if key in conversion_rank:
            blocker = conversion_rank[key]
            break
    if not blocker:
        return order
    annotated = dict(order)
    annotated.setdefault("conversion_candidate_id", blocker.get("conversion_candidate_id"))
    annotated.setdefault("conversion_impact_rank", blocker.get("conversion_impact_rank"))
    annotated.setdefault("remaining_gap_count_before", blocker.get("remaining_gap_count"))
    annotated.setdefault("remaining_gap_count_after_expected", max(0, _safe_int(blocker.get("remaining_gap_count"), 1) - 1))
    annotated.setdefault("blocks_bounded_real_canary", True)
    annotated.setdefault("acceptance_test", blocker.get("acceptance_test"))
    return annotated


def _conversion_lane_followup_orders(conversion_lane: dict[str, Any], *, limit: int = 20) -> list[dict[str, Any]]:
    blockers = conversion_lane.get("conversion_blocker_rank")
    if not isinstance(blockers, list):
        return []
    orders: list[dict[str, Any]] = []
    actionable_classes = {
        "key_lineage",
        "submit_drought",
        "runtime_hook",
        "env_mapping",
        "post_apply_attribution",
        "bridge_contract",
        "source_quality",
    }
    for blocker in blockers:
        if not isinstance(blocker, dict):
            continue
        blocker_class = str(blocker.get("blocker_class") or "").strip()
        if blocker_class not in actionable_classes:
            continue
        candidate_id = str(blocker.get("conversion_candidate_id") or "").strip()
        if not candidate_id:
            continue
        safe_slug = _slug(f"{blocker_class}_{candidate_id}")[:80]
        instrumentation_implemented = (
            blocker.get("blocker_runtime_effect") is False
            and blocker.get("blocker_allowed_runtime_apply") is False
            and str(blocker.get("blocker_resolution_status") or "") == "open"
            and bool(str(blocker.get("blocker_axis") or "").strip())
        )
        implementation_provenance = None
        if instrumentation_implemented:
            implementation_provenance = {
                "implementation_status": "implemented",
                "implemented_scope": "conversion_lane_blocker_axis_report_provenance",
                "blocker_axis": blocker.get("blocker_axis"),
                "blocker_resolution_status": blocker.get("blocker_resolution_status"),
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "remaining_blocker_is_observation_or_policy_closure": True,
            }
        orders.append(
            {
                "order_id": f"order_conversion_lane_{safe_slug}",
                "title": f"Conversion lane blocker follow-up: {blocker_class} {candidate_id}",
                "source_report_type": "conversion_lane",
                "target_subsystem": "sim_to_real_conversion_lineage",
                "lifecycle_stage": "conversion",
                "threshold_family": "sim_to_real_conversion_lane",
                "mapped_family": "sim_to_real_conversion_lane",
                "route": "instrumentation_order",
                "improvement_type": f"conversion_{blocker_class}_blocker",
                "priority": _safe_int(blocker.get("conversion_impact_rank"), 999),
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "conversion_candidate_id": candidate_id,
                "blocker_axis": blocker.get("blocker_axis"),
                "blocker_resolution_status": blocker.get("blocker_resolution_status"),
                "conversion_impact_rank": blocker.get("conversion_impact_rank"),
                "remaining_gap_count_before": blocker.get("remaining_gap_count"),
                "remaining_gap_count_after_expected": max(0, _safe_int(blocker.get("remaining_gap_count"), 1) - 1),
                "blocks_bounded_real_canary": True,
                "acceptance_test": blocker.get("acceptance_test"),
                "implementation_status": "implemented" if instrumentation_implemented else None,
                "original_implementation_status": "implemented" if instrumentation_implemented else None,
                "implementation_provenance": implementation_provenance,
                "intent": (
                    "Close the conversion critical-path blocker as source-only instrumentation/report/test work. "
                    "This does not create real order, provider, bot, cap, or threshold authority."
                ),
                "expected_ev_effect": "reduce remaining blocker count before bounded real canary can be requested",
                "evidence": [
                    f"conversion_candidate_id={candidate_id}",
                    f"blocker_class={blocker_class}",
                    f"conversion_impact_rank={blocker.get('conversion_impact_rank')}",
                    f"next_repair_action={blocker.get('next_repair_action')}",
                    f"acceptance_test={blocker.get('acceptance_test')}",
                    "runtime_effect=false",
                    "allowed_runtime_apply=false",
                ],
                "files_likely_touched": [
                    "src/engine/automation/key_lineage_ledger.py",
                    "src/engine/automation/conversion_lane.py",
                    "src/engine/verify_threshold_cycle_postclose_chain.py",
                    "src/engine/build_code_improvement_workorder.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py",
                ],
                "forbidden_uses": [
                    "real_order_authority",
                    "provider_route_change",
                    "bot_restart",
                    "cap_release",
                    "runtime_threshold_mutation",
                    "broker_order_guard_change",
                ],
            }
        )
        if len(orders) >= limit:
            break
    return orders


def _recent_workorder_reports(target_date: str, *, lookback_days: int = 10) -> list[dict[str, Any]]:
    try:
        end_date = date.fromisoformat(target_date)
    except ValueError:
        return []
    reports: list[dict[str, Any]] = []
    for offset in range(1, lookback_days + 1):
        candidate_date = (end_date - timedelta(days=offset)).isoformat()
        path, _ = code_improvement_workorder_paths(candidate_date)
        payload = _load_json(path)
        if payload:
            reports.append(payload)
    return reports


def _repeat_unresolved_signature(order: dict[str, Any]) -> str | None:
    source_report_type = str(order.get("source_report_type") or "").strip()
    target_subsystem = str(order.get("target_subsystem") or "").strip()
    lifecycle_stage = str(order.get("lifecycle_stage") or "").strip()
    improvement_type = str(order.get("improvement_type") or "").strip()
    threshold_family = str(order.get("threshold_family") or "").strip()
    title_slug = _slug(str(order.get("title") or ""))
    identity_fields = [
        source_report_type,
        target_subsystem,
        lifecycle_stage,
        improvement_type,
        threshold_family,
        title_slug,
    ]
    if sum(1 for value in identity_fields if value) < 3:
        return None
    parts = [
        source_report_type,
        target_subsystem,
        lifecycle_stage,
        improvement_type,
        threshold_family,
        title_slug,
    ]
    return "sig:" + "|".join(parts)


def _unresolved_repeat_counts(reports: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    counts: dict[str, dict[str, Any]] = {}
    unresolved_decisions = {"attach_existing_family", "design_family_candidate", "defer_evidence"}
    for report in reports:
        seen_in_report: set[str] = set()
        for section in ("orders", "non_selected_orders"):
            orders = report.get(section) if isinstance(report.get(section), list) else []
            for order in orders:
                if not isinstance(order, dict):
                    continue
                order_id = str(order.get("order_id") or "").strip()
                if not order_id or order_id in seen_in_report:
                    continue
                decision = str(order.get("decision") or "").strip()
                status = str(order.get("implementation_status") or "").strip()
                if decision not in unresolved_decisions:
                    continue
                if _is_implemented_status(status):
                    continue
                if _is_terminal_non_implement_status(status):
                    continue
                if order.get("runtime_effect") is True:
                    continue
                signature = _repeat_unresolved_signature(order)
                repeat_keys = {order_id}
                if signature:
                    repeat_keys.add(signature)
                for repeat_key in repeat_keys:
                    if repeat_key in seen_in_report:
                        continue
                    seen_in_report.add(repeat_key)
                    repeat_info = counts.setdefault(repeat_key, {"count": 0, "implementation_status_counts": {}})
                    repeat_info["count"] = int(repeat_info.get("count") or 0) + 1
                    if status:
                        status_counts = repeat_info.setdefault("implementation_status_counts", {})
                        status_counts[status] = int(status_counts.get(status) or 0) + 1
    return counts


def _repeat_info_count(repeat_info: Any) -> int:
    if isinstance(repeat_info, dict):
        return _safe_int(repeat_info.get("count"))
    return _safe_int(repeat_info)


def _repeat_info_primary_status(repeat_info: Any) -> str | None:
    if not isinstance(repeat_info, dict):
        return None
    status_counts = repeat_info.get("implementation_status_counts")
    if not isinstance(status_counts, dict) or not status_counts:
        return None
    status, _ = max(
        ((str(key), _safe_int(value)) for key, value in status_counts.items() if str(key).strip()),
        key=lambda pair: pair[1],
        default=("", 0),
    )
    return status or None


def _escalate_repeated_unresolved_orders(
    classified: list[ClassifiedOrder],
    *,
    repeat_counts: dict[str, dict[str, Any]],
    repeat_floor: int = 2,
) -> tuple[list[ClassifiedOrder], list[str]]:
    escalated: list[ClassifiedOrder] = []
    escalated_ids: list[str] = []
    unresolved_decisions = {"attach_existing_family", "design_family_candidate", "defer_evidence"}
    for item in classified:
        order_id = str(item.order.get("order_id") or "").strip()
        signature = _repeat_unresolved_signature(item.order)
        repeat_keys = [order_id]
        if signature:
            repeat_keys.append(signature)
        repeat_key_counts = {
            key: _repeat_info_count(repeat_counts.get(key))
            for key in repeat_keys
            if key
        }
        repeat_key, repeat_count = max(
            repeat_key_counts.items(),
            key=lambda pair: pair[1],
            default=("", 0),
        )
        status = str(item.order.get("implementation_status") or "").strip()
        primary_history_status = _repeat_info_primary_status(repeat_counts.get(repeat_key))
        implemented_status_present = _is_implemented_status(status)
        terminal_non_implement_status_present = _is_terminal_non_implement_status(status) or _is_terminal_non_implement_status(
            primary_history_status
        )
        existing_family_only = (
            item.decision == "attach_existing_family"
            and bool(item.mapped_family)
            and not status
            and str(item.order.get("improvement_type") or "") != "source_quality_gap"
        )
        pattern_lab_design_only = (
            item.decision == "design_family_candidate"
            and item.order.get("source_report_type")
            in {"scalping_pattern_lab_automation", "swing_pattern_lab_automation", "swing_improvement_automation"}
            and not item.mapped_family
            and not status
            and not primary_history_status
        )
        pattern_lab_existing_family_evidence_only = (
            item.decision == "defer_evidence"
            and item.order.get("source_report_type")
            in {"scalping_pattern_lab_automation", "swing_pattern_lab_automation"}
            and bool(item.mapped_family)
            and str(item.order.get("route") or "") in {"existing_family", "attach_existing_family"}
            and str(item.order.get("improvement_type") or "")
            in {"threshold_family_input", "pattern_lab_observation"}
            and not status
        )
        manual_review_only = (
            item.order.get("source_report_type") == "codebase_performance_workorder"
            and str(
                item.order.get("performance_candidate_state")
                or item.order.get("candidate_state")
                or ""
            ).strip()
            in {"deferred", "rejected"}
        )
        if (
            order_id
            and repeat_count >= repeat_floor
            and item.decision in unresolved_decisions
            and not implemented_status_present
            and not terminal_non_implement_status_present
            and item.order.get("runtime_effect") is not True
            and item.decision_source != "implement_now_rejudge"
            and not existing_family_only
            and not pattern_lab_design_only
            and not pattern_lab_existing_family_evidence_only
            and not manual_review_only
        ):
            escalated_order = dict(item.order)
            original_status = status or primary_history_status or None
            provenance = escalated_order.get("implementation_provenance")
            if not isinstance(provenance, dict):
                provenance = {}
            escalated_order["original_implementation_status"] = original_status
            escalated_order["implementation_status"] = "repeat_unresolved_escalated"
            escalated_order["repeat_unresolved_escalation"] = {
                "repeat_count": repeat_count,
                "repeat_floor": repeat_floor,
                "repeat_key": repeat_key,
                "repeat_signature": signature,
                "previous_decision": item.decision,
                "previous_route": item.route,
                "implementation_status": original_status,
                "implementation_status_counts": (
                    (repeat_counts.get(repeat_key) or {}).get("implementation_status_counts")
                    if isinstance(repeat_counts.get(repeat_key), dict)
                    else {}
                ),
                "runtime_effect": escalated_order.get("runtime_effect"),
                "allowed_runtime_apply": escalated_order.get("allowed_runtime_apply"),
            }
            escalated_order["implementation_provenance"] = {
                **provenance,
                "repeat_unresolved_escalation": escalated_order["repeat_unresolved_escalation"],
            }
            escalated.append(
                ClassifiedOrder(
                    order=escalated_order,
                    decision="implement_now",
                    reason=(
                        f"repeat unresolved automation finding appeared in {repeat_count} recent workorders; "
                        "promote to source-only implementation review instead of leaving it as passive evidence"
                    ),
                    mapped_family=item.mapped_family,
                    route="repeat_unresolved_escalation",
                    confidence=item.confidence or "repeat_unresolved",
                    automation_reentry=(
                        "After implementation, regenerate the source report, code improvement workorder, "
                        "threshold EV/runtime summary, and postclose verifier; runtime/order/provider/bot state "
                        "must remain unchanged."
                    ),
                )
            )
            escalated_ids.append(order_id)
        else:
            escalated.append(item)
    return escalated, sorted(escalated_ids)


def _repeat_unresolved_original_status(order: dict[str, Any]) -> str:
    repeat_escalation = order.get("repeat_unresolved_escalation")
    if not isinstance(repeat_escalation, dict):
        repeat_escalation = {}
    return str(
        order.get("original_implementation_status")
        or repeat_escalation.get("implementation_status")
        or order.get("implementation_status")
        or ""
    ).strip()


def _selected_implement_now_resolution_summary(selected: list[ClassifiedOrder]) -> dict[str, Any]:
    existing_ids: list[str] = []
    new_ids: list[str] = []
    existing_status_counts: dict[str, int] = {}
    new_route_counts: dict[str, int] = {}
    runtime_effect_true_ids: list[str] = []
    for item in selected:
        order = item.order
        order_id = str(order.get("order_id") or "").strip()
        if item.decision != "implement_now" or not order_id:
            continue
        if order.get("runtime_effect") is True:
            runtime_effect_true_ids.append(order_id)
            continue
        original_status = _repeat_unresolved_original_status(order)
        if _is_implemented_status(original_status):
            existing_ids.append(order_id)
            status_key = original_status or "implemented"
            existing_status_counts[status_key] = existing_status_counts.get(status_key, 0) + 1
            continue
        new_ids.append(order_id)
        route = str(item.route or order.get("route") or "implement_now")
        new_route_counts[route] = new_route_counts.get(route, 0) + 1
    return {
        "existing_implementation_order_ids": sorted(existing_ids),
        "existing_implementation_count": len(existing_ids),
        "existing_implementation_status_counts": existing_status_counts,
        "new_runtime_effect_false_order_ids": sorted(new_ids),
        "new_runtime_effect_false_count": len(new_ids),
        "new_runtime_effect_false_route_counts": new_route_counts,
        "runtime_effect_true_order_ids": sorted(runtime_effect_true_ids),
        "runtime_effect_true_count": len(runtime_effect_true_ids),
    }


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        numeric = float(value)
        return numeric if math.isfinite(numeric) else default
    except (TypeError, ValueError):
        return default


def _slug(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9가-힣]+", "_", str(value or "").strip().lower()).strip("_")
    return text[:80] or "unknown"


def _slug_with_hash(value: str, *, limit: int = 80) -> str:
    base = _slug(value)
    digest = hashlib.sha1(str(value or "").encode("utf-8")).hexdigest()[:8]
    keep = max(1, int(limit) - len(digest) - 1)
    return f"{base[:keep].rstrip('_')}_{digest}"


def _next_calendar_day(target_date: str) -> str:
    try:
        return (date.fromisoformat(target_date) + timedelta(days=1)).isoformat()
    except ValueError:
        return target_date


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except (OSError, ValueError):
        return False


def _workorder_isolated_source_mode() -> bool:
    source_roots = [
        PATTERN_LAB_AUTOMATION_DIR,
        SWING_IMPROVEMENT_AUTOMATION_DIR,
        SWING_PATTERN_LAB_AUTOMATION_DIR,
        SWING_STRATEGY_DISCOVERY_EV_DIR,
        SWING_LIFECYCLE_DECISION_MATRIX_DIR,
        SWING_LIFECYCLE_BUCKET_DISCOVERY_DIR,
        PATTERN_LAB_AI_REVIEW_DIR,
        THRESHOLD_CYCLE_EV_DIR,
        LIFECYCLE_DECISION_MATRIX_DIR,
        PIPELINE_EVENT_VERBOSITY_DIR,
        OBSERVATION_SOURCE_QUALITY_AUDIT_DIR,
        CODEBASE_PERFORMANCE_WORKORDER_DIR,
        PATTERN_LAB_CURRENTNESS_AUDIT_DIR,
        BUY_FUNNEL_SENTINEL_DIR,
        PRODUCER_GAP_DISCOVERY_DIR,
        STAGE_HOOK_WORKORDER_DISCOVERY_DIR,
        STAGE_HOOK_RUNTIME_SCAFFOLD_DIR,
    ]
    return any(not _is_relative_to(Path(root), REPORT_DIR) for root in source_roots)


def _source_path_enabled(path: Path, *, isolated_source_mode: bool) -> bool:
    if not isolated_source_mode:
        return True
    return not _is_relative_to(path, REPORT_DIR)


def _load_source_json(path: Path, *, isolated_source_mode: bool) -> dict[str, Any]:
    if not _source_path_enabled(path, isolated_source_mode=isolated_source_mode):
        return {}
    return _load_json(path)


def automation_report_path(target_date: str) -> Path:
    return PATTERN_LAB_AUTOMATION_DIR / f"scalping_pattern_lab_automation_{target_date}.json"


def swing_automation_report_path(target_date: str) -> Path:
    return SWING_IMPROVEMENT_AUTOMATION_DIR / f"swing_improvement_automation_{target_date}.json"


def swing_pattern_lab_automation_report_path(target_date: str) -> Path:
    return SWING_PATTERN_LAB_AUTOMATION_DIR / f"swing_pattern_lab_automation_{target_date}.json"


def threshold_ev_report_path(target_date: str) -> Path:
    return THRESHOLD_CYCLE_EV_DIR / f"threshold_cycle_ev_{target_date}.json"


def lifecycle_decision_matrix_report_path(target_date: str) -> Path:
    return LIFECYCLE_DECISION_MATRIX_DIR / f"lifecycle_decision_matrix_{target_date}.json"


def swing_strategy_discovery_ev_report_path(target_date: str) -> Path:
    return SWING_STRATEGY_DISCOVERY_EV_DIR / f"swing_strategy_discovery_ev_{target_date}.json"


def swing_lifecycle_decision_matrix_report_path(target_date: str) -> Path:
    return SWING_LIFECYCLE_DECISION_MATRIX_DIR / f"swing_lifecycle_decision_matrix_{target_date}.json"


def swing_lifecycle_bucket_discovery_report_path(target_date: str) -> Path:
    return SWING_LIFECYCLE_BUCKET_DISCOVERY_DIR / f"swing_lifecycle_bucket_discovery_{target_date}.json"


def code_improvement_workorder_paths(target_date: str) -> tuple[Path, Path]:
    base = f"code_improvement_workorder_{target_date}"
    return (
        CODE_IMPROVEMENT_WORKORDER_REPORT_DIR / f"{base}.json",
        CODE_IMPROVEMENT_WORKORDER_DIR / f"{base}.md",
    )


def pattern_lab_currentness_audit_report_path(target_date: str) -> Path:
    return PATTERN_LAB_CURRENTNESS_AUDIT_DIR / f"pattern_lab_currentness_audit_{target_date}.json"


def pattern_lab_ai_review_report_path(target_date: str) -> Path:
    return PATTERN_LAB_AI_REVIEW_DIR / f"pattern_lab_ai_review_{target_date}.json"


def buy_funnel_sentinel_report_path(target_date: str) -> Path:
    return BUY_FUNNEL_SENTINEL_DIR / f"buy_funnel_sentinel_{target_date}.json"


def producer_gap_discovery_report_path(target_date: str) -> Path:
    return PRODUCER_GAP_DISCOVERY_DIR / f"producer_gap_discovery_{target_date}.json"


def stage_hook_workorder_discovery_report_path(target_date: str) -> Path:
    return STAGE_HOOK_WORKORDER_DISCOVERY_DIR / f"stage_hook_workorder_discovery_{target_date}.json"


def stage_hook_runtime_scaffold_report_path(target_date: str) -> Path:
    return STAGE_HOOK_RUNTIME_SCAFFOLD_DIR / f"stage_hook_runtime_scaffold_{target_date}.json"


def _implementation_marker_from_attribution(attribution: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    implementation_status = "implemented" if attribution.get("implementation_status") == "implemented" else None
    implementation_provenance = (
        attribution.get("implementation_provenance")
        if isinstance(attribution.get("implementation_provenance"), dict)
        else {}
    )
    if implementation_status == "implemented" and not implementation_provenance:
        implementation_provenance = {
            "runtime_effect": False,
            "decision_authority": attribution.get("decision_authority"),
            "primary_decision_metric": attribution.get("primary_decision_metric"),
            "source_quality_gate": attribution.get("source_quality_gate"),
            "forbidden_uses": attribution.get("forbidden_uses") or [],
        }
    return implementation_status, implementation_provenance


def _implementation_status_for_bucket(
    item: dict[str, Any],
    attribution_status: str | None,
) -> str | None:
    return item.get("implementation_status") or attribution_status


def _implementation_provenance_for_bucket(
    item: dict[str, Any],
    attribution_provenance: dict[str, Any],
) -> dict[str, Any] | None:
    if isinstance(item.get("implementation_provenance"), dict):
        return item.get("implementation_provenance")
    return attribution_provenance or None


def _sanitize_producer_gap_order(order: dict[str, Any]) -> dict[str, Any]:
    sanitized = {**order, "source_report_type": "producer_gap_discovery"}
    sanitized.pop("runtime_hook_candidate_contract", None)
    return sanitized


def _is_implemented_status(value: Any) -> bool:
    return str(value or "").strip() in IMPLEMENTED_STATUSES


def _is_terminal_non_implement_status(value: Any) -> bool:
    return str(value or "").strip() in TERMINAL_NON_IMPLEMENT_STATUSES


def _terminal_non_implement_status(item: ClassifiedOrder) -> str | None:
    status = str(item.order.get("implementation_status") or "").strip()
    if _is_implemented_status(status) or _is_terminal_non_implement_status(status):
        return status
    source_type = str(item.order.get("source_report_type") or "").strip()
    if item.decision == "attach_existing_family":
        provenance = (
            item.order.get("implementation_provenance")
            if isinstance(item.order.get("implementation_provenance"), dict)
            else {}
        )
        if str(provenance.get("recommended_resolution") or "") == "mark_not_applicable_explicitly":
            return "terminal_not_applicable_evidence"
        if not status:
            return "terminal_existing_family_evidence"
        return None
    if item.decision == "design_family_candidate":
        if source_type in {"scalping_pattern_lab_automation", "swing_pattern_lab_automation", "swing_improvement_automation"}:
            return "terminal_design_family_candidate"
        return None
    if item.decision == "defer_evidence":
        if item.decision_source == "implement_now_rejudge":
            return "terminal_deferred_evidence"
        if source_type in {
            "scalping_pattern_lab_automation",
            "swing_pattern_lab_automation",
        } and str(item.order.get("improvement_type") or "").strip() in {
            "threshold_family_input",
            "pattern_lab_observation",
        }:
            return "terminal_deferred_evidence"
        if source_type in {"pattern_lab_ai_review", "codebase_performance_workorder"}:
            return "terminal_deferred_evidence"
        return None
    if item.decision == "reject":
        return "terminal_rejected"
    return None


def _entry_submit_drought_implementation_marker(contract: dict[str, Any]) -> dict[str, Any]:
    required = contract.get("required_downstream") if isinstance(contract.get("required_downstream"), list) else []
    if not {
        "code_improvement_workorder",
        "lifecycle_decision_matrix.submit_bucket_attribution",
        "threshold_cycle_ev_report",
        "runtime_approval_summary",
        "postclose_verifier",
    }.issubset({str(item) for item in required}):
        return {}
    return {
        "implementation_status": "implemented",
        "implementation_checks": [
            "buy_funnel_sentinel emits entry_submit_drought_contract",
            "code_improvement_workorder selects drought and weak-contract follow-ups",
            "required_downstream includes LDM, EV, runtime summary, and verifier consumers",
            "runtime_effect=false",
            "allowed_runtime_apply=false",
        ],
        "implementation_provenance": {
            "implementation_type": "source_only_report_provenance_handoff",
            "source_report_type": "buy_funnel_sentinel",
            "required_downstream": required,
            "weak_contract_matches": contract.get("weak_contract_matches") or [],
            "runtime_effect": contract.get("runtime_effect"),
            "allowed_runtime_apply": contract.get("allowed_runtime_apply"),
            "broker_order_submit_allowed": contract.get("broker_order_submit_allowed"),
            "forbidden_uses": contract.get("forbidden_uses") or [],
        },
    }


def _entry_submit_weak_contract_implementation_marker(
    *,
    gap_type: str,
    contract: dict[str, Any],
    taxonomy_leakage_labels: list[str] | None = None,
    lifecycle_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    required = contract.get("required_downstream") if isinstance(contract.get("required_downstream"), list) else []
    if "lifecycle_decision_matrix.submit_bucket_attribution" not in {str(item) for item in required}:
        return {}
    submit_attribution = (
        lifecycle_report.get("submit_bucket_attribution")
        if isinstance(lifecycle_report, dict) and isinstance(lifecycle_report.get("submit_bucket_attribution"), dict)
        else {}
    )
    submit_summary = (
        submit_attribution.get("summary")
        if isinstance(submit_attribution.get("summary"), dict)
        else {}
    )
    post_submit_gaps = (
        submit_attribution.get("post_submit_contract_gaps")
        if isinstance(submit_attribution.get("post_submit_contract_gaps"), list)
        else []
    )
    unresolved_gap_types = {
        str(item.get("gap_type") or "")
        for item in post_submit_gaps
        if isinstance(item, dict)
    }
    unresolved_taxonomy_leakage = [
        str(item)
        for item in (taxonomy_leakage_labels or [])
        if str(item).strip()
    ]
    if (
        submit_attribution
        and _safe_int(submit_summary.get("submit_rows"), 0) > 0
        and _safe_int(submit_summary.get("contract_gap_count"), 0) == 0
        and not bool(submit_summary.get("post_submit_provenance_join_gap"))
        and gap_type not in unresolved_gap_types
        and (gap_type != "source_taxonomy_contract_gap" or not unresolved_taxonomy_leakage)
    ):
        return {
            "implementation_status": "implemented_submit_contract_verified",
            "implementation_checks": [
                "buy_funnel_sentinel weak contract workorder is source-only",
                "lifecycle_decision_matrix submit_bucket_attribution is present",
                "submit_bucket_attribution contract_gap_count=0",
                "post_submit_provenance_join_gap=false",
                f"weak contract gap={gap_type}",
                "runtime_effect=false",
                "allowed_runtime_apply=false",
            ],
            "implementation_provenance": {
                "implementation_type": "submit_contract_report_provenance_verified",
                "source_report_type": "buy_funnel_sentinel",
                "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution",
                "gap_type": gap_type,
                "weak_contract_matches": contract.get("weak_contract_matches") or [],
                "sample_status": "ldm_submit_contract_verified",
                "submit_rows": _safe_int(submit_summary.get("submit_rows"), 0),
                "real_submitted_row_count": _safe_int(submit_summary.get("real_submitted_row_count"), 0),
                "missing_broker_order_key_count": _safe_int(
                    submit_summary.get("missing_broker_order_key_count"),
                    0,
                ),
                "taxonomy_leakage_labels": unresolved_taxonomy_leakage,
                "post_submit_provenance_join_resolution": submit_summary.get(
                    "post_submit_provenance_join_resolution"
                ),
                "runtime_effect": contract.get("runtime_effect"),
                "allowed_runtime_apply": contract.get("allowed_runtime_apply"),
            },
        }
    stage_unique = contract.get("stage_unique") if isinstance(contract.get("stage_unique"), dict) else {}
    submitted_unique = _safe_int(stage_unique.get("order_bundle_submitted"), 0)
    if submitted_unique > 0 and gap_type == "source_taxonomy_contract_gap":
        return {
            "implementation_status": "open_source_taxonomy_provenance_gap",
            "implementation_checks": [
                "buy_funnel_sentinel weak contract workorder is source-only",
                "real order_bundle_submitted samples exist",
                "strategy/source/blocker taxonomy must be emitted or explicitly marked not applicable",
                "weak contract gap=source_taxonomy_contract_gap",
                "runtime_effect=false",
                "allowed_runtime_apply=false",
            ],
            "implementation_provenance": {
                "implementation_type": "source_taxonomy_provenance_gap",
                "source_report_type": "buy_funnel_sentinel",
                "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution",
                "gap_type": gap_type,
                "weak_contract_matches": contract.get("weak_contract_matches") or [],
                "sample_status": "submitted_sample_exists_source_taxonomy_missing",
                "submitted_unique": submitted_unique,
                "runtime_effect": contract.get("runtime_effect"),
                "allowed_runtime_apply": contract.get("allowed_runtime_apply"),
            },
        }
    if submitted_unique > 0 and gap_type in {
        "broker_receipt_contract_gap",
        "fill_quality_contract_gap",
        "post_submit_contract_gap",
        "telegram_post_submit_contract_gap",
    }:
        return {
            "implementation_status": "open_post_submit_provenance_join_gap",
            "implementation_checks": [
                "buy_funnel_sentinel weak contract workorder is source-only",
                "real order_bundle_submitted samples exist",
                "broker/fill/post-submit provenance must join from broker order key instead of waiting for sample",
                f"weak contract gap={gap_type}",
                "runtime_effect=false",
                "allowed_runtime_apply=false",
            ],
            "implementation_provenance": {
                "implementation_type": "post_submit_provenance_join_gap",
                "source_report_type": "buy_funnel_sentinel",
                "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution",
                "gap_type": gap_type,
                "weak_contract_matches": contract.get("weak_contract_matches") or [],
                "sample_status": "submitted_sample_exists_broker_or_fill_join_missing",
                "submitted_unique": submitted_unique,
                "runtime_effect": contract.get("runtime_effect"),
                "allowed_runtime_apply": contract.get("allowed_runtime_apply"),
            },
        }
    return {
        "implementation_status": "implemented_but_waiting_sample",
        "implementation_checks": [
            "buy_funnel_sentinel weak contract workorder is source-only",
            "lifecycle_decision_matrix submit_bucket_attribution is the downstream consumer",
            f"weak contract gap={gap_type}",
            "runtime_effect=false",
            "allowed_runtime_apply=false",
        ],
        "implementation_provenance": {
            "implementation_type": "entry_submit_source_contract_waiting_real_sample",
            "source_report_type": "buy_funnel_sentinel",
            "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution",
            "gap_type": gap_type,
            "weak_contract_matches": contract.get("weak_contract_matches") or [],
            "sample_status": "waiting_real_broker_or_fill_sample",
            "runtime_effect": contract.get("runtime_effect"),
            "allowed_runtime_apply": contract.get("allowed_runtime_apply"),
        },
    }


def _sanitize_pattern_lab_ai_review_order(
    order: dict[str, Any],
    *,
    swing_lab_automation: dict[str, Any],
) -> dict[str, Any]:
    sanitized = {**order, "source_report_type": "pattern_lab_ai_review"}
    if sanitized.get("implementation_status") == "implemented":
        return sanitized
    if str(sanitized.get("improvement_type") or "") != "source_quality_gap":
        return sanitized
    ev_summary = (
        swing_lab_automation.get("ev_report_summary")
        if isinstance(swing_lab_automation.get("ev_report_summary"), dict)
        else {}
    )
    data_quality = (
        swing_lab_automation.get("data_quality")
        if isinstance(swing_lab_automation.get("data_quality"), dict)
        else {}
    )
    ofi_qi_quality = (
        data_quality.get("ofi_qi_quality")
        if isinstance(data_quality.get("ofi_qi_quality"), dict)
        else {}
    )
    blocked = (
        ev_summary.get("source_quality_blocked_families")
        if isinstance(ev_summary.get("source_quality_blocked_families"), list)
        else []
    )
    reason_counts = (
        ofi_qi_quality.get("reason_counts")
        if isinstance(ofi_qi_quality.get("reason_counts"), dict)
        else {}
    )
    if not blocked or not reason_counts:
        return sanitized
    sanitized["implementation_status"] = "implemented"
    sanitized["implementation_checks"] = [
        "swing_pattern_lab_automation exposes source_quality_blocked_families",
        "swing_pattern_lab_automation exposes ofi_qi_quality.reason_counts",
        "pattern_lab_ai_review routes invalid micro context as source_quality_gap",
        "runtime_effect=false",
        "allowed_runtime_apply=false",
    ]
    sanitized["implementation_provenance"] = {
        "implementation_type": "source_quality_report_provenance",
        "source_report_type": "swing_pattern_lab_automation",
        "blocked_family_count": len(blocked),
        "blocked_families": [
            {
                "family": item.get("family"),
                "stage": item.get("stage"),
                "source_quality_blockers": item.get("source_quality_blockers") or [],
                "invalid_micro_context_unique_record_count": item.get(
                    "invalid_micro_context_unique_record_count"
                ),
                "runtime_effect": item.get("runtime_effect"),
            }
            for item in blocked[:8]
            if isinstance(item, dict)
        ],
        "ofi_qi_reason_counts": reason_counts,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": ev_summary.get("decision_authority"),
    }
    return sanitized


def _stage_hook_scaffold_by_name(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("hook_name")): item
        for item in (report.get("implemented_hooks") if isinstance(report.get("implemented_hooks"), list) else [])
        if isinstance(item, dict)
        and item.get("hook_name")
        and item.get("implementation_status") == "implemented"
        and item.get("runtime_effect") is False
        and item.get("allowed_runtime_apply") is False
    }


def _sanitize_stage_hook_order(order: dict[str, Any], scaffold_by_name: dict[str, dict[str, Any]]) -> dict[str, Any]:
    sanitized = {**order, "source_report_type": "stage_hook_workorder_discovery"}
    contract = sanitized.get("stage_hook_candidate_contract") if isinstance(sanitized.get("stage_hook_candidate_contract"), dict) else {}
    hook_name = str(contract.get("hook_name") or "")
    scaffold = scaffold_by_name.get(hook_name)
    if scaffold:
        sanitized["implementation_status"] = "implemented"
        sanitized["implementation_provenance"] = {
            "source_report_type": "stage_hook_runtime_scaffold",
            "hook_name": hook_name,
            "initial_runtime_state": scaffold.get("initial_runtime_state"),
            "runtime_effect": scaffold.get("runtime_effect"),
            "allowed_runtime_apply": scaffold.get("allowed_runtime_apply"),
            "requires_separate_runtime_apply_candidate": scaffold.get("requires_separate_runtime_apply_candidate"),
            "implementation_files": scaffold.get("implementation_files") or [],
        }
    return sanitized


def _serialize_classified_order(item: ClassifiedOrder) -> dict[str, Any]:
    ldm_existing_source_handoff = (
        item.decision == "attach_existing_family"
        and str(item.order.get("target_subsystem") or "") == "lifecycle_decision_matrix"
    )
    implementation_status = _terminal_non_implement_status(item) or item.order.get("implementation_status")
    return {
        "order_id": item.order.get("order_id"),
        "title": item.order.get("title"),
        "target_subsystem": item.order.get("target_subsystem"),
        "source_report_type": item.order.get("source_report_type"),
        "lifecycle_stage": item.order.get("lifecycle_stage"),
        "threshold_family": item.order.get("threshold_family"),
        "improvement_type": item.order.get("improvement_type"),
        "priority": item.order.get("priority"),
        "decision": item.decision,
        "decision_reason": item.reason,
        "derived_review_category": (
            "already_implemented_source_handoff" if ldm_existing_source_handoff else item.order.get("derived_review_category")
        ),
        "implementation_candidate": False if ldm_existing_source_handoff else item.decision == "implement_now",
        "route": item.route,
        "mapped_family": item.mapped_family,
        "confidence": item.confidence,
        "intent": item.order.get("intent"),
        "expected_ev_effect": item.order.get("expected_ev_effect"),
        "evidence": item.order.get("evidence") or [],
        "required_downstream": item.order.get("required_downstream") or [],
        "weak_contract_matches": item.order.get("weak_contract_matches") or [],
        "next_postclose_metric": item.order.get("next_postclose_metric"),
        "files_likely_touched": item.order.get("files_likely_touched") or [],
        "acceptance_tests": item.order.get("acceptance_tests") or [],
        "forbidden_uses": item.order.get("forbidden_uses") or [],
        "adm_issue_types": item.order.get("adm_issue_types") or [],
        "automation_reentry": item.automation_reentry,
        "runtime_effect": bool(item.order.get("runtime_effect")),
        "allowed_runtime_apply": bool(item.order.get("allowed_runtime_apply")),
        "actual_order_submitted": item.order.get("actual_order_submitted"),
        "broker_order_forbidden": item.order.get("broker_order_forbidden"),
        "strategy_effect": bool(item.order.get("strategy_effect")),
        "data_quality_effect": bool(item.order.get("data_quality_effect")),
        "tuning_axis_effect": bool(item.order.get("tuning_axis_effect")),
        "implementation_status": implementation_status,
        "original_implementation_status": item.order.get("original_implementation_status"),
        "implementation_checks": item.order.get("implementation_checks") or [],
        "implementation_id": item.order.get("implementation_id"),
        "explicit_redecision_required": item.order.get("explicit_redecision_required"),
        "conflict_resolution_acceptance_test": item.order.get("conflict_resolution_acceptance_test"),
        "implementation_provenance": item.order.get("implementation_provenance"),
        "repeat_unresolved_escalation": item.order.get("repeat_unresolved_escalation"),
        "parity_contract": item.order.get("parity_contract"),
        "source_bucket_id": item.order.get("source_bucket_id"),
        "conversion_candidate_id": item.order.get("conversion_candidate_id"),
        "conversion_impact_rank": item.order.get("conversion_impact_rank"),
        "remaining_gap_count_before": item.order.get("remaining_gap_count_before"),
        "remaining_gap_count_after_expected": item.order.get("remaining_gap_count_after_expected"),
        "blocks_bounded_real_canary": item.order.get("blocks_bounded_real_canary"),
        "acceptance_test": item.order.get("acceptance_test"),
        "runtime_hook_candidate_contract": item.order.get("runtime_hook_candidate_contract"),
        "stage_hook_candidate_contract": item.order.get("stage_hook_candidate_contract"),
        "initial_runtime_state": item.order.get("initial_runtime_state"),
        "requires_separate_runtime_apply_candidate": item.order.get("requires_separate_runtime_apply_candidate"),
        "raw_row_exclusion_context_classification": item.order.get("raw_row_exclusion_context_classification"),
        "raw_row_exclusion_context": item.order.get("raw_row_exclusion_context"),
        "terminal_disposition": item.order.get("terminal_disposition"),
    }


def _finding_maps(report: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_order_id: dict[str, dict[str, Any]] = {}
    by_title_slug: dict[str, dict[str, Any]] = {}
    for section in ("consensus_findings", "solo_findings"):
        for finding in report.get(section) or []:
            if not isinstance(finding, dict):
                continue
            finding_id = str(finding.get("finding_id") or "").strip()
            title = str(finding.get("title") or "").strip()
            if finding_id:
                by_order_id[f"order_{finding_id}"] = finding
            if title:
                by_title_slug[_slug(title)] = finding
    return by_order_id, by_title_slug


def _auto_family_order_ids(report: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for item in report.get("auto_family_candidates") or []:
        if not isinstance(item, dict):
            continue
        implementation_id = str(item.get("implementation_order_id") or "").strip()
        if implementation_id:
            result.add(implementation_id)
        family_id = str(item.get("family_id") or "").strip()
        if family_id:
            result.add(f"order_{family_id}")
    return result


def _contains_any(text: str, tokens: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(token in lower for token in tokens)


_IMPLEMENT_ACCEPTANCE_PREFIXES = (
    "python -m pytest ",
    "pytest ",
    "python -m src.engine.sync_docs_backlog_to_project ",
    "python -m py_compile ",
)


def _normalized_acceptance_text(text: str) -> str:
    normalized = str(text or "").strip()
    if normalized.startswith("PYTHONPATH=. "):
        normalized = normalized[len("PYTHONPATH=. "):]
    if normalized.startswith(".venv/bin/python "):
        normalized = "python " + normalized[len(".venv/bin/python "):]
    if normalized.startswith("./.venv/bin/python "):
        normalized = "python " + normalized[len("./.venv/bin/python "):]
    if normalized.startswith(".venv/bin/pytest "):
        normalized = "pytest " + normalized[len(".venv/bin/pytest "):]
    if normalized.startswith("./.venv/bin/pytest "):
        normalized = "pytest " + normalized[len("./.venv/bin/pytest "):]
    if normalized.startswith("venv/Scripts/python.exe "):
        normalized = "python " + normalized[len("venv/Scripts/python.exe "):]
    return normalized


def _has_runnable_acceptance(order: dict[str, Any]) -> bool:
    for raw in order.get("acceptance_tests") or []:
        normalized = _normalized_acceptance_text(str(raw))
        if not any(normalized.startswith(prefix) for prefix in _IMPLEMENT_ACCEPTANCE_PREFIXES):
            continue
        if normalized.startswith("pytest ") or normalized.startswith("python -m pytest "):
            parts = normalized.split()
            meaningful = [part for part in parts if part not in {"python", "-m", "pytest"} and not part.startswith("-")]
            if not any(
                part.startswith(("src/tests/", "tests/")) or part.endswith("_test.py") or part.startswith("src/tests/test_")
                for part in meaningful
            ):
                continue
            return True
    return False


def _implement_now_rejudge(order: dict[str, Any]) -> tuple[str, str] | None:
    if _is_implemented_status(order.get("implementation_status")):
        return None
    if (
        order.get("source_report_type") == "pattern_lab_ai_review"
        and str(order.get("improvement_type") or "") == "automation_handoff_gap"
    ):
        return None
    issues = {str(item).strip() for item in (order.get("adm_issue_types") or []) if str(item).strip()}
    if issues and issues.issubset({"joined_sample_below_sample_floor", "prompt_context_not_loaded"}):
        return (
            "defer_evidence",
            "Entry ADM warning is waiting on clean sample/runtime observation, not a code implementation gap",
        )
    provenance = order.get("implementation_provenance") if isinstance(order.get("implementation_provenance"), dict) else {}
    if str(provenance.get("recommended_resolution") or "") == "mark_not_applicable_explicitly":
        return (
            "attach_existing_family",
            "source coverage is present and the remaining bucket is an explicit not_applicable evidence classification",
        )
    files = order.get("files_likely_touched")
    file_count = len([item for item in files if str(item).strip()]) if isinstance(files, list) else 0
    source_type = str(order.get("source_report_type") or "")
    if (
        source_type in {"lifecycle_decision_matrix_holding_bucket_attribution", "lifecycle_decision_matrix_exit_bucket_attribution"}
        and file_count <= 0
        and not _has_runnable_acceptance(order)
    ):
        return (
            "defer_evidence",
            "not code-actionable in this cycle: no files_likely_touched and no runnable acceptance tests",
        )
    tests = [str(item).strip() for item in (order.get("acceptance_tests") or []) if str(item).strip()]
    if (
        tests
        and not _has_runnable_acceptance(order)
        and order.get("order_id") == "order_swing_lifecycle_observation_coverage"
    ):
        return (
            "defer_evidence",
            "not code-actionable in this cycle: acceptance contract is review text only, not an executable validation",
        )
    if source_type == "pattern_lab_ai_review" and file_count <= 0 and not _has_runnable_acceptance(order):
        return (
            "defer_evidence",
            "not code-actionable in this cycle: no files_likely_touched and no runnable acceptance tests",
        )
    return None


def _classify_order(
    order: dict[str, Any],
    *,
    finding_by_order_id: dict[str, dict[str, Any]],
    finding_by_title_slug: dict[str, dict[str, Any]],
    auto_family_order_ids: set[str],
    closed_instrumentation_order_families: dict[str, str],
) -> ClassifiedOrder:
    order_id = str(order.get("order_id") or "").strip()
    title = str(order.get("title") or "").strip()
    subsystem = str(order.get("target_subsystem") or "").strip()
    text = f"{order_id} {title} {subsystem}"
    finding = finding_by_order_id.get(order_id) or finding_by_title_slug.get(_slug(title)) or {}
    route = str(finding.get("route") or order.get("route") or "").strip() or None
    mapped_family = str(finding.get("mapped_family") or order.get("mapped_family") or "").strip() or None
    confidence = str(finding.get("confidence") or order.get("confidence") or "").strip() or None
    closed_family = closed_instrumentation_order_families.get(order_id)
    if closed_family:
        return ClassifiedOrder(
            order=order,
            decision="attach_existing_family",
            reason="instrumentation/provenance contract is already implemented; keep as report source for the existing family",
            mapped_family=closed_family,
            route="existing_family",
            confidence=confidence,
            automation_reentry="Next postclose calibration consumes the implemented report/provenance fields; no runtime mutation.",
        )

    if bool(order.get("runtime_effect")):
        return ClassifiedOrder(
            order=order,
            decision="reject",
            reason="automation order must remain runtime_effect=false; runtime_effect=true is treated as artifact error",
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry="Reject artifact and regenerate the source automation report before implementation.",
        )

    rejudged = _implement_now_rejudge(order)
    if rejudged:
        decision, reason = rejudged
        return ClassifiedOrder(
            order=order,
            decision=decision,
            reason=reason,
            mapped_family=mapped_family or str(order.get("threshold_family") or "").strip() or None,
            route="existing_family" if decision == "attach_existing_family" else route or "evidence_wait",
            confidence=confidence,
            decision_source="implement_now_rejudge",
            automation_reentry=(
                "Keep the item out of the canonical implement_now queue; regenerated postclose reports and "
                "runner terminal dispositions must preserve the non-implement decision."
            ),
        )

    if (
        order.get("source_report_type") == "swing_improvement_automation"
        and order_id == "order_swing_entry_bottleneck_auto_resolution"
    ):
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason=(
                "SWING_ENTRY_DROUGHT_CRITICAL is a source-only swing entry bottleneck handoff and must not be "
                "dropped by workorder selection limits"
            ),
            mapped_family=mapped_family or "swing_gatekeeper_accept_reject",
            route=route or "instrumentation_order",
            confidence=confidence or "consensus",
            automation_reentry=(
                "After implementation, regenerate swing audit, Swing LDM, bucket discovery, code workorder, "
                "EV/runtime summary, and postclose verifier; runtime/live order guards remain unchanged."
            ),
        )

    if _is_implemented_status(order.get("implementation_status")) and order.get("source_report_type") != "codebase_performance_workorder":
        status = str(order.get("implementation_status") or "").strip()
        return ClassifiedOrder(
            order=order,
            decision="attach_existing_family",
            reason=(
                f"instrumentation/report/provenance implementation status is {status}; keep the order as "
                "existing-family source evidence instead of re-implementing"
            ),
            mapped_family=mapped_family or str(order.get("threshold_family") or "").strip() or None,
            route="existing_family",
            confidence=confidence,
            automation_reentry=(
                f"Next postclose workorder should preserve implementation_status={status} and use the "
                "source metrics as provenance only."
            ),
        )

    if order.get("source_report_type") == "pipeline_event_verbosity":
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason="pipeline event compaction V2 is report-only instrumentation; shadow means producer-summary observe mode, not trading shadow",
            mapped_family=mapped_family,
            route=route or "instrumentation_order",
            confidence=confidence,
            automation_reentry="Next postclose pipeline_event_verbosity report must show producer summary freshness and parity status.",
        )

    if order.get("source_report_type") == "codebase_performance_workorder":
        if _is_implemented_status(order.get("implementation_status")):
            return ClassifiedOrder(
                order=order,
                decision="attach_existing_family",
                reason=(
                    "report-only performance implementation is already present in code; keep the order as provenance "
                    "and validate through regenerated reports/tests instead of re-implementing"
                ),
                mapped_family=mapped_family or "ops_performance_report_only_implemented",
                route=route or "existing_report_only_implementation",
                confidence=confidence,
                automation_reentry="Next postclose codebase performance source report must keep implementation_status=implemented and parity tests green.",
            )
        state = str(order.get("performance_candidate_state") or order.get("candidate_state") or "").strip()
        if state == "accepted":
            return ClassifiedOrder(
                order=order,
                decision="implement_now",
                reason="accepted codebase performance order is logic-preserving and report/workorder-only; implementation still requires parity tests",
                mapped_family=mapped_family,
                route=route or "performance_optimization_order",
                confidence=confidence,
                automation_reentry="After implementation, rerun the same artifact/report parity tests before postclose workorder refresh.",
            )
        if state == "deferred":
            return ClassifiedOrder(
                order=order,
                decision="defer_evidence",
                reason=str(order.get("defer_reason") or "performance order requires manual review before implementation"),
                mapped_family=mapped_family,
                route=route or "performance_optimization_order",
                confidence=confidence,
                automation_reentry="Keep as deferred performance backlog until scope/risk is reviewed separately.",
            )
        return ClassifiedOrder(
            order=order,
            decision="reject",
            reason=str(order.get("defer_reason") or "performance order is outside current no-logic-change scope"),
            mapped_family=mapped_family,
            route=route or "performance_optimization_order",
            confidence=confidence,
            automation_reentry="Do not implement from this workorder source.",
        )

    if order.get("source_report_type") in {"pattern_lab_currentness_audit", "pattern_lab_ai_review", "tuning_observability_summary"}:
        if (
            order.get("source_report_type") == "pattern_lab_ai_review"
            and str(order.get("improvement_type") or "") == "ai_review_followup"
        ):
            return ClassifiedOrder(
                order=order,
                decision="defer_evidence",
                reason=(
                    "Pattern Lab generic ai_review_followup is reviewer evidence for concrete source-quality "
                    "or handoff orders; do not duplicate it as a Codex implement_now item"
                ),
                mapped_family=mapped_family or "pattern_lab_feedback_handoff",
                route="pattern_lab_ai_review_followup_evidence",
                confidence=confidence or "parsed_ai_review_followup",
                automation_reentry=(
                    "Keep as terminal review evidence until the concrete source-quality/handoff orders and "
                    "regenerated Pattern Lab AI review close the audit."
                ),
            )
        if (
            order.get("source_report_type") == "pattern_lab_ai_review"
            and str(order.get("improvement_type") or "") == "automation_handoff_gap"
        ):
            return ClassifiedOrder(
                order=order,
                decision="attach_existing_family",
                reason=(
                    "Pattern Lab AI review automation_handoff_gap is coverage evidence for the currentness "
                    "handoff workorders; do not create duplicate implement_now items from the reviewer layer"
                ),
                mapped_family=mapped_family or "pattern_lab_feedback_handoff",
                route="pattern_lab_ai_review_handoff_evidence",
                confidence=confidence or "ai_two_pass_review",
                automation_reentry=(
                    "Keep as source-quality blocker evidence until pattern_lab_currentness_audit handoff "
                    "orders close and the regenerated AI review parses sufficient context."
                ),
            )
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason="pattern lab audit/review/observability order is report/source-quality instrumentation only and must remain runtime_effect=false",
            mapped_family=mapped_family,
            route=route or "instrumentation_order",
            confidence=confidence or "consensus",
            automation_reentry="After implementation, rerun pattern labs, currentness audit, workorder, EV, and propagation audit.",
        )

    if order.get("source_report_type") == "producer_gap_discovery":
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason=(
                "producer gap discovery high-priority order is source-only missing producer work; "
                "implementation still requires Codex implement_now and cannot mutate runtime/order/provider/bot state"
            ),
            mapped_family=mapped_family,
            route=route or "implement_now",
            confidence=confidence or "ai_two_pass_review",
            automation_reentry=(
                "After implementation, rerun producer_gap_discovery, code improvement workorder, "
                "threshold EV, runtime summary, and postclose verifier."
            ),
        )

    if order.get("source_report_type") == "stage_hook_workorder_discovery":
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason=(
                "stage hook workorder discovery surfaced an implementation-ready hook scaffold; "
                "implementation starts disabled/source-only and requires a separate runtime apply candidate"
            ),
            mapped_family=mapped_family,
            route=route or "implement_now",
            confidence=confidence or "ai_tier2_review",
            automation_reentry=(
                "After implementation, rerun stage_hook_workorder_discovery, code improvement workorder, "
                "threshold EV, and postclose verifier; runtime/live order guards remain unchanged."
            ),
        )

    if order.get("source_report_type") == "conversion_lane":
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason=(
                "conversion lane blocker is source-only lineage/report/instrumentation work needed before any "
                "bounded real canary request can be considered"
            ),
            mapped_family=mapped_family or "sim_to_real_conversion_lane",
            route=route or "instrumentation_order",
            confidence=confidence or "conversion_kpi",
            automation_reentry=(
                "After implementation, rerun key_lineage_ledger, conversion_lane, code_improvement_workorder, "
                "tuning performance control tower, and postclose verifier; runtime/live order guards remain unchanged."
            ),
        )

    if (
        order.get("source_report_type") in ("scalping_pattern_lab_automation", "swing_pattern_lab_automation")
        and (route in ("auto_family_candidate", "design_family_candidate") or order_id in auto_family_order_ids)
    ):
        return ClassifiedOrder(
            order=order,
            decision="design_family_candidate",
            reason=(
                "pattern lab can only propose source-only family design input; LDM/discovery/runtime bridge "
                "contracts must close before any auto_bounded_live consideration"
            ),
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry=(
                "Keep as report-only family metadata and validate through lifecycle artifacts before any runtime "
                "approval artifact is considered."
            ),
        )

    if order.get("source_report_type") == "lifecycle_decision_matrix_scale_in_bucket_attribution":
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason=(
                "LDM scale-in bucket workorder is source-only attribution/handoff instrumentation; "
                "runtime scale-in changes still require a separate approval artifact"
            ),
            mapped_family=mapped_family or "lifecycle_decision_matrix_runtime",
            route=route or "instrumentation_order",
            confidence=confidence,
            automation_reentry=(
                "Next postclose LDM, threshold EV, runtime approval summary, and verifier must preserve "
                "scale-in bucket candidates/workorders without runtime mutation."
            ),
        )

    if order.get("source_report_type") == "lifecycle_decision_matrix_lifecycle_flow_bucket_attribution":
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason=(
                "LDM lifecycle-flow parent bucket workorder is source-only bundle attribution/handoff "
                "instrumentation; Greenfield real-env stays blocked until complete entry-submit-holding-exit "
                "flows pass the regenerated chain."
            ),
            mapped_family=mapped_family or "lifecycle_decision_matrix_runtime",
            route=route or "instrumentation_order",
            confidence=confidence,
            automation_reentry=(
                "Next postclose LDM, lifecycle bucket discovery, threshold EV, runtime approval summary, "
                "runtime apply bridge, and verifier must preserve lifecycle-flow parent bucket state."
            ),
        )

    if order.get("source_report_type") == "lifecycle_bucket_discovery_source_dimension_rollup":
        return ClassifiedOrder(
            order=order,
            decision="attach_existing_family",
            reason=(
                "source-dimension gap rollup is visibility evidence; actionable emit/backfill gaps are tracked "
                "by dedicated lifecycle_bucket_discovery implement_now orders"
            ),
            mapped_family=mapped_family or "lifecycle_bucket_discovery",
            route=route or "source_dimension_rollup",
            confidence=confidence,
            automation_reentry=(
                "Next postclose checklist/workorder should keep source_dimension_gap_summary visible until "
                "actionable gaps are resolved or explicitly marked not applicable."
            ),
        )

    if order.get("source_report_type") == "lifecycle_bucket_discovery_quiet_gap_rollup":
        is_conflict_order = order.get("route") == "parent_conflict_exclusion_review"
        conflict_ready = is_conflict_order and bool(order.get("implementation_candidate"))
        if conflict_ready:
            return ClassifiedOrder(
                order=order,
                decision="implement_now",
                reason=(
                    "parent conflict resolution evidence is closed with resolution states and child "
                    "reclassification items; implementation is source-only output generation and does "
                    "not authorize runtime mutation"
                ),
                mapped_family=mapped_family or "lifecycle_bucket_discovery",
                route=route or "parent_conflict_resolution_implement_now",
                confidence=confidence or "postclose_discovery_source",
                automation_reentry=(
                    "After implementation, rerun lifecycle_bucket_discovery, code_improvement_workorder, "
                    "threshold EV, and postclose verifier. runtime_effect=false, allowed_runtime_apply=false."
                ),
            )
        return ClassifiedOrder(
            order=order,
            decision="attach_existing_family",
            reason=(
                "quiet gap rollup is visibility evidence for parent conflict/source-only/AI coverage review; "
                "it does not authorize a runtime patch by itself"
            ),
            mapped_family=mapped_family or "lifecycle_bucket_discovery",
            route=route or "quiet_gap_rollup",
            confidence=confidence,
            automation_reentry=(
                "Next postclose checklist/workorder should keep quiet_gap_summary visible until the gap is "
                "implemented, covered by parent policy, deferred for more sample, or explicitly rejected."
            ),
        )

    if order.get("improvement_type") == "observation_source_quality_warning_rollup":
        return ClassifiedOrder(
            order=order,
            decision="attach_existing_family",
            reason=(
                "observation source-quality warning rollup is evidence-only visibility for warnings outside "
                "the immediate implementation allowlist"
            ),
            mapped_family=mapped_family or "observation_source_quality_audit",
            route=route or "source_quality_warning_rollup",
            confidence=confidence,
            automation_reentry=(
                "Next postclose observation source-quality audit and workorder should preserve this warning "
                "until it is covered by a dedicated source-quality order or explicitly deferred."
            ),
        )

    if order.get("improvement_type") == "source_quality_hard_block_contract_gap":
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason=(
                "observation source-quality hard block prevents tuning/live-auto/runtime approval inputs until "
                "the producer contract gap is fixed and a new clean cutoff is recorded"
            ),
            mapped_family=mapped_family or "observation_source_quality_audit",
            route=route or "source_quality_gap",
            confidence=confidence or "audit",
            automation_reentry=(
                "After implementation, rerun observation_source_quality_audit, code improvement workorder, "
                "threshold EV, runtime approval summary, and postclose verifier; only post-cutoff raw may feed tuning."
            ),
        )

    if order.get("improvement_type") == "source_quality_raw_row_exclusion_producer_gap":
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason=(
                "raw row exclusion protected tuning inputs, but the producer/source-quality cause must be fixed "
                "or explicitly classified so future rows are not repeatedly excluded"
            ),
            mapped_family=mapped_family or "observation_source_quality_audit",
            route=route or "source_quality_raw_row_exclusion_producer_fix",
            confidence=confidence or "audit",
            automation_reentry=(
                "After implementation, rerun observation_source_quality_audit and code improvement workorder; "
                "raw_row_exclusion.excluded_row_count should fall or remaining exclusions must carry reviewed "
                "not_available/waiting_sample-only provenance."
            ),
        )

    if order.get("improvement_type") == "source_quality_raw_row_exclusion_limit_up_locked_context":
        return ClassifiedOrder(
            order=order,
            decision="attach_existing_family",
            reason=(
                "raw row exclusion is concentrated in a limit-up locked context; keep it as reviewed "
                "source-quality evidence and do not create an automatic producer-fix implementation"
            ),
            mapped_family=mapped_family or "observation_source_quality_audit",
            route=route or "review_required_limit_up_locked_context",
            confidence=confidence or "audit",
            automation_reentry=(
                "Next postclose source-quality audit should reclassify only if the same intraday_range_pct=0 "
                "gap repeats in non-limit-up rows or independent high/low/candle source loss is proven."
            ),
        )

    if order.get("improvement_type") == "source_quality_raw_row_exclusion_market_halt_context":
        return ClassifiedOrder(
            order=order,
            decision="attach_existing_family",
            reason=(
                "raw row exclusion is concentrated inside a confirmed market halt/circuit-breaker recovery "
                "window; keep it as reviewed source-quality evidence and do not create an automatic producer-fix "
                "implementation unless the gap repeats after normal flow resumes"
            ),
            mapped_family=mapped_family or "observation_source_quality_audit",
            route=route or "review_required_market_halt_context",
            confidence=confidence or "audit",
            automation_reentry=(
                "Next postclose source-quality audit should reclassify only if the same intraday_range_pct=0 "
                "gap repeats outside the market halt/circuit-breaker recovery window."
            ),
        )

    if order.get("improvement_type") == "source_quality_unknown_token_provenance_gap":
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason=(
                "unknown-token source-quality warnings are not tuning hard blocks, but they must be traced to "
                "producer provenance or replaced with explicit not_available/insufficient_sample labels"
            ),
            mapped_family=mapped_family or "observation_source_quality_audit",
            route=route or "source_quality_warning_producer_fix",
            confidence=confidence or "audit",
            automation_reentry=(
                "After implementation, rerun observation_source_quality_audit and code improvement workorder; "
                "unknown_token_stage_count should fall or remaining unknowns must carry explicit reviewed provenance."
            ),
        )


    if order.get("source_report_type") == "lifecycle_bucket_discovery":
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason=(
                "lifecycle bucket discovery follow-up is report/provenance handoff work; runtime apply remains "
                "blocked until the regenerated reports and verifier pass"
            ),
            mapped_family=mapped_family,
            route=route or "instrumentation_order",
            confidence=confidence,
            automation_reentry=(
                "After implementation, rerun lifecycle bucket discovery, code improvement workorder, runtime "
                "approval summary, threshold EV, and postclose verifier."
            ),
        )

    if _contains_any(text, ("fallback", "shadow")):
        return ClassifiedOrder(
            order=order,
            decision="reject",
            reason="fallback revival or shadow reintroduction conflicts with current Plan Rebase policy",
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry="Keep as rejected finding unless translated into report_only_calibration or bounded canary design.",
        )

    if confidence == "solo":
        return ClassifiedOrder(
            order=order,
            decision="defer_evidence",
            reason="single-lab finding; keep as low-confidence backlog until repeated by fresh lab or EV report",
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry="Re-evaluate in the next postclose pattern lab automation and daily EV report.",
        )

    if subsystem == "runtime_instrumentation" or route == "instrumentation_order":
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason="instrumentation/provenance work can improve attribution without direct runtime mutation",
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry="After implementation, next postclose report must show source freshness or warning reduction.",
        )

    if route == "existing_family" or mapped_family:
        return ClassifiedOrder(
            order=order,
            decision="attach_existing_family",
            reason="finding maps to an existing threshold family and should strengthen source metrics/provenance",
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry="After implementation, intraday/postclose calibration should include the updated family input.",
        )

    if route == "auto_family_candidate" or order_id in auto_family_order_ids:
        return ClassifiedOrder(
            order=order,
            decision="design_family_candidate",
            reason="finding needs family design; allowed_runtime_apply remains false until metadata/tests/guards are closed",
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry="Create report-only family metadata first; only later can auto_bounded_live consider it.",
        )

    return ClassifiedOrder(
        order=order,
        decision="defer_evidence",
        reason="route is not strong enough for immediate implementation",
        mapped_family=mapped_family,
        route=route,
        confidence=confidence,
        automation_reentry="Keep in generated workorder as deferred context and re-check after next daily EV report.",
    )


def _sort_classified(items: list[ClassifiedOrder]) -> list[ClassifiedOrder]:
    return sorted(
        items,
        key=lambda item: (
            DECISION_RANK.get(item.decision, 99),
            _safe_int(item.order.get("priority"), 999),
            str(item.order.get("order_id") or ""),
        ),
    )


def _holding_exit_counterfactual_contract_status(target_date: str) -> dict[str, Any]:
    report = _load_json(
        HOLDING_EXIT_DECISION_MATRIX_DIR / f"holding_exit_decision_matrix_{target_date}.json"
    )
    if not report:
        return {"implemented": False, "reason": "missing_holding_exit_decision_matrix_report"}
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    proxy = (
        report.get("counterfactual_proxy_summary")
        if isinstance(report.get("counterfactual_proxy_summary"), dict)
        else {}
    )
    required_actions = {
        "hold_defer",
        "exit_only",
        "avg_down_wait",
        "pyramid_wait",
    }
    per_action_samples = (
        proxy.get("per_action_samples") if isinstance(proxy.get("per_action_samples"), dict) else {}
    )
    actions_present = {str(value) for value in proxy.get("actions_present") or []}
    has_required_actions = required_actions.issubset(actions_present) and all(
        _safe_int(per_action_samples.get(action), 0) > 0 for action in required_actions
    )
    implemented = (
        str(report.get("instrumentation_status") or "") == "implemented"
        and report.get("runtime_change") is False
        and "non_no_clear_edge_count" in summary
        and bool(summary.get("per_action_edge_buckets"))
        and bool(proxy.get("ready"))
        and has_required_actions
    )
    return {
        "implemented": implemented,
        "reason": "implemented_contract_available" if implemented else "contract_incomplete",
        "report_path": str(HOLDING_EXIT_DECISION_MATRIX_DIR / f"holding_exit_decision_matrix_{target_date}.json"),
    }


def _threshold_ev_followup_orders(ev_report: dict[str, Any], *, target_date: str) -> list[dict[str, Any]]:
    outcome = ev_report.get("calibration_outcome") if isinstance(ev_report.get("calibration_outcome"), dict) else {}
    decisions = outcome.get("decisions") if isinstance(outcome.get("decisions"), list) else []
    orders: list[dict[str, Any]] = []
    for item in decisions:
        if not isinstance(item, dict):
            continue
        family = str(item.get("family") or "").strip()
        state = str(item.get("calibration_state") or "").strip()
        if family != "holding_exit_decision_matrix_advisory" or state != "hold_no_edge":
            continue
        source_metrics = item.get("source_metrics") if isinstance(item.get("source_metrics"), dict) else {}
        if source_metrics.get("instrumentation_status") == "implemented":
            continue
        contract_status = _holding_exit_counterfactual_contract_status(target_date)
        if contract_status.get("implemented") is True:
            continue
        counterfactual_gap_count = _safe_int(source_metrics.get("counterfactual_gap_count"), 0)
        proxy_sample_snapshots = _safe_int(source_metrics.get("eligible_but_not_chosen_sample_snapshots"), 0)
        proxy_joined_candidates = _safe_int(
            source_metrics.get("eligible_but_not_chosen_post_sell_joined_candidates"),
            0,
        )
        proxy_missing_actions = (
            list(source_metrics.get("counterfactual_proxy_missing_actions") or [])
            if isinstance(source_metrics.get("counterfactual_proxy_missing_actions"), list)
            else []
        )
        instrumentation_gap = not source_metrics or (
            counterfactual_gap_count > 0 or proxy_sample_snapshots <= 0 or proxy_joined_candidates <= 0
        )
        if not instrumentation_gap:
            continue
        evidence = [
            "calibration_state=hold_no_edge",
            f"sample_count={item.get('sample_count')}",
            f"sample_floor={item.get('sample_floor')}",
        ]
        if source_metrics:
            evidence.extend(
                [
                    f"counterfactual_gap_count={counterfactual_gap_count}",
                    f"eligible_snapshot_count={proxy_sample_snapshots}",
                    f"eligible_joined_candidates={proxy_joined_candidates}",
                ]
            )
            if proxy_missing_actions:
                evidence.append(f"proxy_missing_actions={','.join(str(value) for value in proxy_missing_actions)}")
        orders.append(
            {
                "order_id": "order_holding_exit_decision_matrix_edge_counterfactual",
                "title": "holding exit decision matrix edge counterfactual coverage",
                "source_report_type": "threshold_cycle_ev",
                "lifecycle_stage": "holding_exit",
                "target_subsystem": "runtime_instrumentation",
                "route": "instrumentation_order",
                "mapped_family": family,
                "threshold_family": family,
                "improvement_type": "instrumentation",
                "confidence": "consensus",
                "priority": 4,
                "runtime_effect": False,
                "expected_ev_effect": "Break hold_no_edge by separating exit_only/hold_defer/avg_down/pyramid counterfactual outcomes.",
                "evidence": evidence,
                "next_postclose_metric": "holding_exit_decision_matrix_advisory should report per-action edge buckets, non_no_clear_edge_count, and counterfactual coverage.",
                "files_likely_touched": [
                    "src/engine/daily_threshold_cycle_report.py",
                    "src/engine/holding_exit_decision_matrix.py",
                    "src/engine/statistical_action_weight.py",
                ],
                "acceptance_tests": [
                    "pytest holding exit decision matrix/report tests",
                    "threshold EV report includes per-action counterfactual coverage",
                ],
            }
        )
    return orders


def _entry_adm_followup_orders(ev_report: dict[str, Any]) -> list[dict[str, Any]]:
    adm = (
        ev_report.get("scalp_entry_action_decision_matrix")
        if isinstance(ev_report.get("scalp_entry_action_decision_matrix"), dict)
        else {}
    )
    if not adm:
        return []
    joined = _safe_int(adm.get("joined_sample"), 0)
    floor = _safe_int(adm.get("sample_floor"), 20)
    missing_actions = adm.get("missing_actions") if isinstance(adm.get("missing_actions"), list) else []
    prompt_applied_count = _safe_int(adm.get("prompt_applied_count"), 0)
    issues: list[str] = []
    if joined < floor:
        issues.append("joined_sample_below_sample_floor")
    if missing_actions:
        issues.append("missing_action_bucket")
    if prompt_applied_count <= 0:
        issues.append("prompt_context_not_loaded")
    if str(adm.get("status") or "").lower() == "missing":
        issues.append("source_quality_gap")
    if not issues:
        return []
    sources = ev_report.get("sources") if isinstance(ev_report.get("sources"), dict) else {}
    evidence = [
        f"status={adm.get('status')}",
        f"joined_sample={joined}",
        f"sample_floor={floor}",
        f"prompt_applied_count={prompt_applied_count}",
    ]
    if missing_actions:
        evidence.append("missing_actions=" + ",".join(str(value) for value in missing_actions))
    source_path = sources.get("scalp_entry_action_decision_matrix") or adm.get("artifact")
    return [
        {
            "order_id": "order_scalp_entry_adm_daily_tuning_coverage",
            "title": "scalp entry ADM daily tuning coverage",
            "source_report_type": "threshold_cycle_ev",
            "lifecycle_stage": "entry",
            "target_subsystem": "entry_funnel",
            "route": "instrumentation_order",
            "mapped_family": "scalp_entry_action_decision_matrix_advisory",
            "threshold_family": "scalp_entry_action_decision_matrix_advisory",
            "improvement_type": "instrumentation_report_provenance",
            "confidence": "consensus",
            "priority": 3,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "expected_ev_effect": "Keep BUY_NOW/WAIT_REQUOTE/SKIP_STALE/BUY_DEFENSIVE/NO_BUY_AI/SKIP_SOURCE_QUALITY/SKIP_PRE_SUBMIT_SAFETY action buckets joined to post-sell outcomes and runtime forced_action provenance for daily entry policy tuning.",
            "evidence": evidence,
            "source_paths": [str(source_path)] if source_path else [],
            "next_postclose_metric": "scalp_entry_action_decision_matrix should meet sample_floor, include all action buckets, show prompt_applied_count, and expose entry_adm_runtime_effect/forced_action evidence when runtime bias env is enabled.",
            "files_likely_touched": [
                "src/engine/scalp_entry_action_decision_matrix.py",
                "src/engine/sniper_state_handlers.py",
                "src/engine/scalp_entry_adm_runtime.py",
                "src/engine/threshold_cycle_ev_report.py",
            ],
            "acceptance_tests": [
                "PYTHONPATH=. .venv/bin/pytest src/tests/test_scalp_entry_action_decision_matrix.py src/tests/test_build_code_improvement_workorder.py",
                "runtime_effect remains false and broker submit safety guards remain owner",
            ],
            "adm_issue_types": issues,
        }
    ]


def _lifecycle_ai_context_followup_orders(ev_report: dict[str, Any]) -> list[dict[str, Any]]:
    attribution = (
        ev_report.get("lifecycle_ai_context_attribution")
        if isinstance(ev_report.get("lifecycle_ai_context_attribution"), dict)
        else {}
    )
    context = ev_report.get("lifecycle_ai_context") if isinstance(ev_report.get("lifecycle_ai_context"), dict) else {}
    if not attribution and not context:
        return []
    applied = _safe_int(attribution.get("context_applied_count"), 0)
    prompt_stage_count = _safe_int(context.get("prompt_stage_count"), 0)
    issues: list[str] = []
    if not context.get("available"):
        issues.append("context_artifact_missing")
    if prompt_stage_count <= 0:
        issues.append("prompt_stage_context_missing")
    if applied <= 0:
        issues.append("runtime_context_provenance_missing")
    if not issues:
        return []
    sources = ev_report.get("sources") if isinstance(ev_report.get("sources"), dict) else {}
    implementation_status = (
        "implemented"
        if attribution.get("implementation_status") == "implemented"
        and context.get("available")
        and prompt_stage_count > 0
        else None
    )
    return [
        {
            "order_id": "order_lifecycle_ai_context_attribution_feedback",
            "title": "lifecycle AI context attribution feedback coverage",
            "source_report_type": "threshold_cycle_ev",
            "lifecycle_stage": "lifecycle",
            "target_subsystem": "lifecycle_decision_matrix",
            "route": "instrumentation_order",
            "mapped_family": "lifecycle_ai_context",
            "threshold_family": None,
            "improvement_type": "instrumentation_report_provenance",
            "confidence": "consensus",
            "priority": 4,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "implementation_status": implementation_status,
            "implementation_checks": attribution.get("implementation_checks") or [],
            "implementation_provenance": attribution.get("implementation_provenance") or {},
            "expected_ev_effect": (
                "Keep lifecycle AI context contribution visible as bounded auxiliary ADM/LDM feedback "
                "without creating real order gates or standalone threshold families."
            ),
            "evidence": [
                f"context_available={context.get('available')}",
                f"prompt_stage_count={prompt_stage_count}",
                f"context_applied_count={applied}",
                f"replay_budget={attribution.get('replay_budget')}",
            ],
            "source_paths": [
                str(path)
                for path in (
                    sources.get("lifecycle_ai_context"),
                    sources.get("lifecycle_ai_context_attribution"),
                )
                if path
            ],
            "next_postclose_metric": (
                "lifecycle_ai_context_attribution should show context_applied_count, stage attribution, "
                "and bounded auxiliary weights that LDM policy entries can consume."
            ),
            "files_likely_touched": [
                "src/engine/lifecycle_ai_context.py",
                "src/engine/lifecycle_decision_matrix.py",
                "src/engine/ai_engine_openai.py",
                "src/engine/threshold_cycle_ev_report.py",
            ],
            "acceptance_tests": [
                "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_lifecycle_ai_context.py src/tests/test_threshold_cycle_ev_report.py",
                "runtime_effect remains false and context is not used as real order gate",
            ],
            "adm_issue_types": issues,
        }
    ]



def _lifecycle_entry_bucket_order_id(item: dict[str, Any]) -> str:
    bucket_type = _slug(str(item.get("bucket_type") or "bucket"))
    bucket_key = _slug(str(item.get("bucket_key") or item.get("workorder_id") or "unknown"))
    return f"order_lifecycle_entry_bucket_{bucket_type}_{bucket_key}"


def _lifecycle_entry_bucket_followup_orders(report: dict[str, Any]) -> list[dict[str, Any]]:
    attribution = (
        report.get("entry_bucket_attribution")
        if isinstance(report.get("entry_bucket_attribution"), dict)
        else {}
    )
    workorders = attribution.get("code_improvement_workorders")
    if not isinstance(workorders, list) or not workorders:
        return []
    contract = {
        "metric_role": attribution.get("metric_role"),
        "decision_authority": attribution.get("decision_authority"),
        "window_policy": attribution.get("window_policy"),
        "sample_floor": attribution.get("sample_floor"),
        "primary_decision_metric": attribution.get("primary_decision_metric"),
        "source_quality_gate": attribution.get("source_quality_gate"),
        "forbidden_uses": attribution.get("forbidden_uses") or [],
    }
    implementation_status, implementation_provenance = _implementation_marker_from_attribution(attribution)
    orders: list[dict[str, Any]] = []
    for item in workorders:
        if not isinstance(item, dict):
            continue
        bucket_type = str(item.get("bucket_type") or "").strip()
        bucket_key = str(item.get("bucket_key") or "").strip()
        if not bucket_type or not bucket_key:
            continue
        reason = str(item.get("reason") or "").strip()
        route = "instrumentation_order"
        if "unknown" not in bucket_key and "missing" not in bucket_key:
            route = "existing_family"
        orders.append(
            {
                "order_id": _lifecycle_entry_bucket_order_id(item),
                "title": f"LDM entry bucket attribution follow-up: {bucket_type}={bucket_key}",
                "source_report_type": "lifecycle_decision_matrix_entry_bucket_attribution",
                "lifecycle_stage": "entry",
                "target_subsystem": (
                    "runtime_instrumentation"
                    if route == "instrumentation_order"
                    else "lifecycle_decision_matrix"
                ),
                "route": route,
                "mapped_family": "lifecycle_decision_matrix_runtime",
                "threshold_family": "lifecycle_decision_matrix_runtime",
                "improvement_type": "entry_bucket_source_quality_attribution",
                "confidence": "daily_ldm_source",
                "priority": 2 if route == "instrumentation_order" else 5,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "implementation_status": _implementation_status_for_bucket(item, implementation_status),
                "implementation_provenance": _implementation_provenance_for_bucket(
                    item,
                    implementation_provenance,
                ),
                "expected_ev_effect": (
                    "Keep entry bucket EV attribution, source-quality gaps, and threshold-cycle approval "
                    "candidates connected without mutating intraday thresholds or broker submission."
                ),
                "evidence": [
                    f"workorder_id={item.get('workorder_id')}",
                    f"bucket_type={bucket_type}",
                    f"bucket_key={bucket_key}",
                    f"reason={reason}",
                    f"recommended_route={item.get('recommended_route')}",
                    f"metric_role={item.get('metric_role') or contract.get('metric_role')}",
                    f"decision_authority={contract.get('decision_authority')}",
                    f"primary_decision_metric={contract.get('primary_decision_metric')}",
                    "runtime_effect=false",
                    "allowed_runtime_apply=false",
                ],
                "intent": (
                    "If the bucket is unknown/missing, add observation tags or provenance. If it has edge, "
                    "preserve it as source evidence for LDM/threshold-cycle rolling confirmation."
                ),
                "next_postclose_metric": (
                    "lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep "
                    "runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this "
                    "workorder when source-quality confirmation is still needed."
                ),
                "files_likely_touched": [
                    "src/engine/lifecycle_decision_matrix.py",
                    "src/engine/scalp_entry_action_decision_matrix.py",
                    "src/engine/daily_threshold_cycle_report.py",
                    "src/engine/runtime_approval_summary.py",
                    "docs/report-based-automation-traceability.md",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py",
                    "postclose verifier fails if LDM entry bucket candidates/workorders are not propagated",
                ],
                "metric_contract": contract,
            }
        )
    return orders


def _lifecycle_submit_bucket_order_id(item: dict[str, Any]) -> str:
    workorder_id = str(item.get("workorder_id") or "").strip()
    if workorder_id.startswith("order_entry_"):
        return workorder_id
    bucket_type = _slug(str(item.get("bucket_type") or "bucket"))
    bucket_key = _slug(str(item.get("bucket_key") or item.get("workorder_id") or "unknown"))
    return f"order_lifecycle_submit_bucket_{bucket_type}_{bucket_key}"


def _lifecycle_submit_bucket_followup_orders(report: dict[str, Any]) -> list[dict[str, Any]]:
    attribution = (
        report.get("submit_bucket_attribution")
        if isinstance(report.get("submit_bucket_attribution"), dict)
        else {}
    )
    workorders = attribution.get("code_improvement_workorders")
    if not isinstance(workorders, list) or not workorders:
        return []
    contract = {
        "metric_role": attribution.get("metric_role"),
        "decision_authority": attribution.get("decision_authority"),
        "window_policy": attribution.get("window_policy"),
        "sample_floor": attribution.get("sample_floor"),
        "primary_decision_metric": attribution.get("primary_decision_metric"),
        "source_quality_gate": attribution.get("source_quality_gate"),
        "forbidden_uses": attribution.get("forbidden_uses") or [],
    }
    implementation_status, implementation_provenance = _implementation_marker_from_attribution(attribution)
    orders: list[dict[str, Any]] = []
    for item in workorders:
        if not isinstance(item, dict):
            continue
        bucket_type = str(item.get("bucket_type") or "").strip()
        bucket_key = str(item.get("bucket_key") or "").strip()
        if not bucket_type or not bucket_key:
            continue
        orders.append(
            {
                "order_id": _lifecycle_submit_bucket_order_id(item),
                "title": f"LDM submit bucket contract follow-up: {bucket_type}={bucket_key}",
                "source_report_type": "lifecycle_decision_matrix_submit_bucket_attribution",
                "lifecycle_stage": "submit",
                "target_subsystem": "runtime_instrumentation",
                "route": "instrumentation_order",
                "mapped_family": "lifecycle_decision_matrix_runtime",
                "threshold_family": "lifecycle_decision_matrix_runtime",
                "improvement_type": "submit_bucket_contract_gap",
                "confidence": "daily_ldm_source",
                "priority": 1,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "implementation_status": _implementation_status_for_bucket(item, implementation_status),
                "implementation_provenance": _implementation_provenance_for_bucket(
                    item,
                    implementation_provenance,
                ),
                "expected_ev_effect": (
                    "Make submit revalidation, broker receipt, fill quality, and post-submit messaging "
                    "contracts observable before any threshold or broker behavior tuning."
                ),
                "evidence": [
                    f"workorder_id={item.get('workorder_id')}",
                    f"bucket_type={bucket_type}",
                    f"bucket_key={bucket_key}",
                    f"reason={item.get('reason')}",
                    f"metric_role={item.get('metric_role') or contract.get('metric_role')}",
                    f"decision_authority={contract.get('decision_authority')}",
                    f"primary_decision_metric={contract.get('primary_decision_metric')}",
                    "runtime_effect=false",
                    "allowed_runtime_apply=false",
                ],
                "intent": (
                    "Close post-entry submit observability gaps as source-only instrumentation/workorder handoff. "
                    "Do not change broker submit guards, provider routing, Telegram semantics, or thresholds here."
                ),
                "next_postclose_metric": (
                    "lifecycle_decision_matrix.submit_bucket_attribution must remain visible in EV/runtime "
                    "summary, and postclose verifier must fail if dropped."
                ),
                "files_likely_touched": [
                    "src/engine/lifecycle_decision_matrix.py",
                    "src/engine/threshold_cycle_ev_report.py",
                    "src/engine/runtime_approval_summary.py",
                    "src/engine/verify_threshold_cycle_postclose_chain.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py",
                ],
                "metric_contract": contract,
            }
        )
    return orders


ENTRY_POST_SUBMIT_WEAK_CONTRACT_ORDERS = (
    (
        "order_entry_post_submit_contract_gap_review",
        "Entry post-submit contract gap review",
        "post_submit_contract_gap",
        "Ensure pre-submit revalidation, cancel, and post-submit state transitions are observable.",
    ),
    (
        "order_entry_broker_receipt_contract_gap_review",
        "Entry broker receipt contract gap review",
        "broker_receipt_contract_gap",
        "Ensure real submitted orders bind broker receipt/order number/fill/cancel provenance.",
    ),
    (
        "order_entry_fill_quality_contract_gap_review",
        "Entry fill quality contract gap review",
        "fill_quality_contract_gap",
        "Ensure full fill, partial fill, slippage, limit fill, and no-fill outcomes are separated.",
    ),
    (
        "order_entry_telegram_post_submit_contract_gap_review",
        "Entry Telegram post-submit contract gap review",
        "telegram_post_submit_contract_gap",
        "Ensure BUY Telegram messages are emitted only for orders submitted to the broker path.",
    ),
    (
        "order_entry_source_taxonomy_contract_gap_review",
        "Entry source taxonomy contract gap review",
        "source_taxonomy_contract_gap",
        "Ensure scalping and swing blocker namespaces are separated in BUY funnel attribution.",
    ),
)


def _entry_post_submit_weak_contract_orders(
    *,
    evidence: list[str],
    contract: dict[str, Any],
    weak_contract_matches: list[Any],
    taxonomy_leakage_labels: list[str],
    lifecycle_report: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    required_downstream = contract.get("required_downstream") if contract else []
    orders: list[dict[str, Any]] = []
    for order_id, title, gap_type, intent in ENTRY_POST_SUBMIT_WEAK_CONTRACT_ORDERS:
        order_evidence = [
            *evidence,
            f"weak_contract_gap={gap_type}",
            "runtime_effect=false",
            "allowed_runtime_apply=false",
        ]
        if order_id == "order_entry_source_taxonomy_contract_gap_review":
            order_evidence.append(f"taxonomy_leakage_labels={taxonomy_leakage_labels}")
        orders.append(
            {
                "order_id": order_id,
                "title": title,
                "source_report_type": "buy_funnel_sentinel",
                "target_subsystem": "runtime_instrumentation",
                "lifecycle_stage": "entry_submit",
                "route": "instrumentation_order",
                "mapped_family": "lifecycle_decision_matrix_runtime",
                "threshold_family": "lifecycle_decision_matrix_runtime",
                "priority": 1,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                **_entry_submit_weak_contract_implementation_marker(
                    gap_type=gap_type,
                    contract=contract,
                    taxonomy_leakage_labels=taxonomy_leakage_labels,
                    lifecycle_report=lifecycle_report,
                ),
                "strategy_effect": gap_type,
                "data_quality_effect": "post_entry_contract_gap",
                "tuning_axis_effect": "source_quality_only",
                "expected_ev_effect": "none_direct_source_quality_only",
                "intent": intent,
                "evidence": order_evidence,
                "required_downstream": required_downstream,
                "weak_contract_matches": weak_contract_matches,
                "files_likely_touched": [
                    "src/engine/buy_funnel_sentinel.py",
                    "src/engine/lifecycle_decision_matrix.py",
                    "src/engine/build_code_improvement_workorder.py",
                    "src/engine/verify_threshold_cycle_postclose_chain.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py",
                ],
                "next_postclose_metric": (
                    "Entry post-submit weak contracts remain source-only workorders with runtime_effect=false "
                    "and allowed_runtime_apply=false until explicit implementation and verification."
                ),
            }
        )
    return orders


def _lifecycle_scale_in_bucket_order_id(item: dict[str, Any]) -> str:
    bucket_type = _slug(str(item.get("bucket_type") or "bucket"))
    bucket_key = _slug(str(item.get("bucket_key") or item.get("workorder_id") or "unknown"))
    return f"order_lifecycle_scale_in_bucket_{bucket_type}_{bucket_key}"


def _lifecycle_scale_in_bucket_followup_orders(report: dict[str, Any]) -> list[dict[str, Any]]:
    attribution = (
        report.get("scale_in_bucket_attribution")
        if isinstance(report.get("scale_in_bucket_attribution"), dict)
        else {}
    )
    workorders = attribution.get("code_improvement_workorders")
    if not isinstance(workorders, list) or not workorders:
        return []
    contract = {
        "metric_role": attribution.get("metric_role"),
        "decision_authority": attribution.get("decision_authority"),
        "window_policy": attribution.get("window_policy"),
        "sample_floor": attribution.get("sample_floor"),
        "primary_decision_metric": attribution.get("primary_decision_metric"),
        "source_quality_gate": attribution.get("source_quality_gate"),
        "forbidden_uses": attribution.get("forbidden_uses") or [],
    }
    orders: list[dict[str, Any]] = []
    for item in workorders:
        if not isinstance(item, dict):
            continue
        bucket_type = str(item.get("bucket_type") or "").strip()
        bucket_key = str(item.get("bucket_key") or "").strip()
        if not bucket_type or not bucket_key:
            continue
        orders.append(
            {
                "order_id": _lifecycle_scale_in_bucket_order_id(item),
                "title": f"LDM scale-in bucket attribution follow-up: {bucket_type}={bucket_key}",
                "source_report_type": "lifecycle_decision_matrix_scale_in_bucket_attribution",
                "lifecycle_stage": "scale_in",
                "target_subsystem": "lifecycle_decision_matrix",
                "route": "source_quality_or_bounded_tunable_candidate",
                "mapped_family": "lifecycle_decision_matrix_runtime",
                "threshold_family": "lifecycle_decision_matrix_runtime",
                "improvement_type": "scale_in_bucket_source_quality_attribution",
                "confidence": "daily_ldm_source",
                "priority": 4,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "implementation_status": item.get("implementation_status"),
                "implementation_provenance": item.get("implementation_provenance"),
                "expected_ev_effect": (
                    "Separate AVG_DOWN/PYRAMID attribution and keep scale-in threshold/cap candidates "
                    "as source-only evidence until rolling confirmation and approval artifact."
                ),
                "evidence": [
                    f"workorder_id={item.get('workorder_id')}",
                    f"bucket_type={bucket_type}",
                    f"bucket_key={bucket_key}",
                    f"reason={item.get('reason')}",
                    f"recommended_route={item.get('recommended_route')}",
                    f"metric_role={item.get('metric_role') or contract.get('metric_role')}",
                    f"decision_authority={contract.get('decision_authority')}",
                    f"primary_decision_metric={contract.get('primary_decision_metric')}",
                    "runtime_effect=false",
                    "allowed_runtime_apply=false",
                ],
                "intent": (
                    "Preserve scale-in arm/blocker attribution and route any PYRAMID/AVG_DOWN threshold "
                    "changes through source-only LDM/threshold-cycle handoff."
                ),
                "next_postclose_metric": (
                    "lifecycle_decision_matrix.scale_in_bucket_attribution candidates/workorders must remain "
                    "visible in threshold EV/runtime summary, and postclose verifier must fail if dropped."
                ),
                "files_likely_touched": [
                    "src/engine/sniper_state_handlers.py",
                    "src/engine/lifecycle_decision_matrix.py",
                    "src/engine/daily_threshold_cycle_report.py",
                    "src/engine/runtime_approval_summary.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py",
                    "postclose verifier fails if LDM scale-in bucket candidates/workorders are not propagated",
                ],
                "metric_contract": contract,
            }
        )
    return orders


def _lifecycle_overnight_bucket_order_id(item: dict[str, Any]) -> str:
    bucket_type = _slug(str(item.get("bucket_type") or "bucket"))
    bucket_key = _slug(str(item.get("bucket_key") or item.get("workorder_id") or "unknown"))
    return f"order_lifecycle_overnight_bucket_{bucket_type}_{bucket_key}"


def _lifecycle_flow_bucket_order_id(item: dict[str, Any]) -> str:
    workorder_id = _slug(str(item.get("workorder_id") or "unknown"))
    bucket_id = _slug_with_hash(str(item.get("lifecycle_flow_bucket_id") or item.get("bucket_key") or "unknown"))
    return f"order_lifecycle_flow_bucket_{workorder_id}_{bucket_id}"


def _lifecycle_stage_bucket_order_id(stage: str, item: dict[str, Any]) -> str:
    bucket_type = _slug(str(item.get("bucket_type") or "bucket"))
    bucket_key = _slug_with_hash(str(item.get("bucket_key") or item.get("workorder_id") or "unknown"))
    return f"order_lifecycle_{stage}_bucket_{bucket_type}_{bucket_key}"


def _lifecycle_flow_bucket_followup_orders(report: dict[str, Any]) -> list[dict[str, Any]]:
    attribution = (
        report.get("lifecycle_flow_bucket_attribution")
        if isinstance(report.get("lifecycle_flow_bucket_attribution"), dict)
        else {}
    )
    workorders = attribution.get("code_improvement_workorders")
    if not isinstance(workorders, list) or not workorders:
        return []
    contract = {
        "metric_role": attribution.get("metric_role"),
        "decision_authority": attribution.get("decision_authority"),
        "window_policy": attribution.get("window_policy"),
        "sample_floor": attribution.get("sample_floor"),
        "primary_decision_metric": attribution.get("primary_decision_metric"),
        "source_quality_gate": attribution.get("source_quality_gate"),
        "forbidden_uses": attribution.get("forbidden_uses") or [],
    }
    implementation_status, implementation_provenance = _implementation_marker_from_attribution(attribution)
    orders: list[dict[str, Any]] = []
    for item in workorders:
        if not isinstance(item, dict):
            continue
        flow_bucket_id = str(item.get("lifecycle_flow_bucket_id") or "").strip()
        if not flow_bucket_id:
            continue
        orders.append(
            {
                "order_id": _lifecycle_flow_bucket_order_id(item),
                "title": f"LDM lifecycle flow bucket follow-up: {flow_bucket_id}",
                "source_report_type": "lifecycle_decision_matrix_lifecycle_flow_bucket_attribution",
                "lifecycle_stage": "lifecycle_flow",
                "target_subsystem": "lifecycle_decision_matrix",
                "route": "instrumentation_order",
                "mapped_family": "lifecycle_decision_matrix_runtime",
                "threshold_family": "lifecycle_decision_matrix_runtime",
                "improvement_type": item.get("improvement_type") or "join_gap_resolution",
                "confidence": "daily_ldm_source",
                "priority": 1,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "implementation_status": _implementation_status_for_bucket(item, implementation_status),
                "implementation_provenance": _implementation_provenance_for_bucket(item, implementation_provenance),
                "expected_ev_effect": (
                    "Prevent entry-only EV from being interpreted as full lifecycle EV by keeping incomplete "
                    "parent flow bundles visible as source-quality evidence."
                ),
                "evidence": [
                    f"workorder_id={item.get('workorder_id')}",
                    f"lifecycle_flow_bucket_id={flow_bucket_id}",
                    f"reason={item.get('reason')}",
                    f"join_gap_reasons={item.get('join_gap_reasons') or []}",
                    f"required_producer_consumer_candidates={item.get('required_producer_consumer_candidates') or []}",
                    f"metric_role={item.get('metric_role') or contract.get('metric_role')}",
                    f"decision_authority={contract.get('decision_authority')}",
                    f"primary_decision_metric={contract.get('primary_decision_metric')}",
                    "runtime_effect=false",
                    "allowed_runtime_apply=false",
                ],
                "intent": (
                    "Close parent lifecycle-flow attribution gaps without changing runtime thresholds, broker "
                    "submit behavior, provider routing, or Greenfield real-env authority."
                ),
                "next_postclose_metric": (
                    "lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders "
                    "must be visible in threshold EV, runtime summary, control tower, and verifier."
                ),
                "files_likely_touched": [
                    "src/engine/lifecycle_decision_matrix.py",
                    "src/engine/lifecycle_bucket_discovery.py",
                    "src/engine/runtime_approval_summary.py",
                    "src/engine/runtime_apply_bridge.py",
                    "src/engine/verify_threshold_cycle_postclose_chain.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py",
                    "postclose verifier fails if lifecycle-flow parent bucket output is dropped",
                ],
                "metric_contract": contract,
            }
        )
    return orders


def _lifecycle_holding_exit_bucket_followup_orders(report: dict[str, Any]) -> list[dict[str, Any]]:
    orders: list[dict[str, Any]] = []
    for stage, attribution_key in (
        ("holding", "holding_bucket_attribution"),
        ("exit", "exit_bucket_attribution"),
    ):
        attribution = (
            report.get(attribution_key)
            if isinstance(report.get(attribution_key), dict)
            else {}
        )
        workorders = attribution.get("code_improvement_workorders")
        if not isinstance(workorders, list) or not workorders:
            continue
        implementation_status, implementation_provenance = _implementation_marker_from_attribution(attribution)
        for item in workorders:
            if not isinstance(item, dict) or not item.get("bucket_type") or not item.get("bucket_key"):
                continue
            orders.append(
                {
                    "order_id": _lifecycle_stage_bucket_order_id(stage, item),
                    "title": f"LDM {stage} bucket source-quality follow-up: {item.get('bucket_type')}={item.get('bucket_key')}",
                    "source_report_type": f"lifecycle_decision_matrix_{stage}_bucket_attribution",
                    "lifecycle_stage": stage,
                    "target_subsystem": "lifecycle_decision_matrix",
                    "route": "instrumentation_order",
                    "mapped_family": "lifecycle_decision_matrix_runtime",
                    "threshold_family": "lifecycle_decision_matrix_runtime",
                    "improvement_type": f"{stage}_bucket_source_quality_child_evidence",
                    "confidence": "daily_ldm_source",
                    "priority": 2,
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "implementation_status": _implementation_status_for_bucket(item, implementation_status),
                    "implementation_provenance": _implementation_provenance_for_bucket(item, implementation_provenance),
                    "expected_ev_effect": (
                        f"Keep {stage} stage buckets visible as child evidence while parent lifecycle flow owns "
                        "promotion EV."
                    ),
                    "evidence": [
                        f"workorder_id={item.get('workorder_id')}",
                        f"bucket_type={item.get('bucket_type')}",
                        f"bucket_key={item.get('bucket_key')}",
                        f"reason={item.get('reason')}",
                        f"recommended_route={item.get('recommended_route')}",
                        "runtime_effect=false",
                        "allowed_runtime_apply=false",
                        "stage_only_live_promotion_forbidden=true",
                    ],
                    "intent": (
                        f"Close {stage} bucket source-quality or lifecycle-flow child-evidence gaps without "
                        "changing runtime thresholds, broker behavior, provider routing, or bot state."
                    ),
                    "next_postclose_metric": (
                        f"{stage}_bucket_attribution bucket/workorder counts, identity join rate, and complete "
                        "lifecycle flow count remain visible in downstream reports."
                    ),
                }
            )
    return orders


def _lifecycle_bucket_discovery_report_path(target_date: str) -> Path:
    return REPORT_DIR / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target_date}.json"


def _lifecycle_bucket_discovery_order_id(item: dict[str, Any]) -> str:
    stage = _slug(str(item.get("stage") or "stage"))
    bucket_id = _slug_with_hash(str(item.get("source_bucket_id") or item.get("bucket_id") or item.get("bucket_key") or "unknown"))
    return f"order_lifecycle_bucket_discovery_{stage}_{bucket_id}"


def _lifecycle_source_dimension_gap_order_id(item: dict[str, Any]) -> str:
    stage = _slug(str(item.get("stage") or "stage"))
    bucket_type = _slug(str(item.get("bucket_type") or "bucket"))
    source_bucket = _slug_with_hash(str(item.get("source_bucket_id") or item.get("bucket_id") or "unknown"))
    return f"order_lifecycle_source_dimension_gap_{stage}_{bucket_type}_{source_bucket}"


def _source_dimension_summary_items(report: dict[str, Any]) -> list[dict[str, Any]]:
    summary = (
        report.get("source_dimension_gap_summary")
        if isinstance(report.get("source_dimension_gap_summary"), dict)
        else {}
    )
    items = summary.get("actionable_candidates") if isinstance(summary.get("actionable_candidates"), list) else []
    return [item for item in items if isinstance(item, dict)]


def _quiet_gap_summary(report: dict[str, Any]) -> dict[str, Any]:
    return report.get("quiet_gap_summary") if isinstance(report.get("quiet_gap_summary"), dict) else {}


def _is_explicit_source_only_lifecycle_flow_exclusion(report: dict[str, Any], item: dict[str, Any]) -> bool:
    if item.get("explicit_runtime_exclusion") is True or item.get("source_only_explicit_exclusion") is True:
        return True
    stage = str(item.get("stage") or "").strip()
    state = str(item.get("classification_state") or "").strip()
    family = str(item.get("live_auto_apply_family") or item.get("mapped_family") or "").strip()
    if stage != "lifecycle_flow" or state not in {"new_bucket_candidate", "runtime_blocked_contract_gap"}:
        return False
    source_kind = str(item.get("source_bucket_kind") or "").strip()
    if source_kind in {"taxonomy_provenance_gap", "source_only_observation"}:
        return True
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    greenfield_state = str(summary.get("greenfield_policy_emit_state") or "").strip()
    if family == "greenfield_real_environment_authority" and (
        greenfield_state
        in {
            "not_emitted_no_complete_lifecycle_flow",
            "not_emitted_no_live_auto_ready_lifecycle_flow",
        }
        or item.get("allowed_runtime_apply") is False
        or item.get("broker_order_forbidden") is True
    ):
        return True
    return False


def _lifecycle_bucket_discovery_followup_orders(report: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = report.get("surfaced_candidates") if isinstance(report.get("surfaced_candidates"), list) else []
    orders: list[dict[str, Any]] = []
    seen_bucket_keys: set[tuple[str, str]] = set()
    actionable_resolutions = {"emit_or_backfill_source_field", "resolve_unknown_source_dimensions"}
    for item in [*candidates, *_source_dimension_summary_items(report)]:
        if not isinstance(item, dict):
            continue
        state = str(item.get("classification_state") or "")
        source_dimension_gap = str(item.get("source_dimension_gap") or "")
        recommended_resolution = str(item.get("recommended_resolution") or "")
        source_dimension_gap_required = (
            source_dimension_gap == "unknown_source_dimensions"
            and recommended_resolution in actionable_resolutions
        )
        if (
            state not in {"new_bucket_candidate", "runtime_blocked_contract_gap", "code_patch_required", "code_review_failed"}
            and not source_dimension_gap_required
        ):
            continue
        if _is_explicit_source_only_lifecycle_flow_exclusion(report, item):
            continue
        stage = str(item.get("stage") or "unknown")
        bucket_id = str(item.get("bucket_id") or "")
        source_bucket_id = str(item.get("source_bucket_id") or bucket_id)
        if source_dimension_gap_required:
            missing_dimension_keys = tuple(str(key) for key in (item.get("missing_dimension_keys") or []))
            bucket_key = (stage, bucket_id, recommended_resolution, ",".join(missing_dimension_keys))
        else:
            bucket_key = (stage, source_bucket_id)
        if bucket_key in seen_bucket_keys:
            continue
        seen_bucket_keys.add(bucket_key)
        order_id = (
            _lifecycle_source_dimension_gap_order_id(item)
            if source_dimension_gap_required
            else _lifecycle_bucket_discovery_order_id(item)
        )
        improvement_type = (
            "source_dimension_gap_resolution"
            if source_dimension_gap_required
            else "bucket_classifier_hook_or_taxonomy_gap"
        )
        orders.append(
            {
                "order_id": order_id,
                "source_bucket_id": source_bucket_id,
                "canonical_bucket": item.get("canonical_bucket"),
                "legacy_raw_bucket_key": item.get("legacy_raw_bucket_key"),
                "bucket_alias_version": item.get("bucket_alias_version"),
                "dimension_set_version": item.get("dimension_set_version"),
                "ai_tier2_comparative_review": item.get("ai_tier2_comparative_review")
                if isinstance(item.get("ai_tier2_comparative_review"), dict)
                else {},
                "title": f"Lifecycle bucket discovery follow-up: {bucket_id}",
                "source_report_type": "lifecycle_bucket_discovery",
                "lifecycle_stage": stage,
                "target_subsystem": "lifecycle_bucket_discovery_taxonomy_provenance",
                "route": "auto_patch_required",
                "mapped_family": item.get("live_auto_apply_family") or "lifecycle_bucket_discovery",
                "threshold_family": item.get("live_auto_apply_family") or "lifecycle_bucket_discovery",
                "improvement_type": improvement_type,
                "confidence": "postclose_discovery_source",
                "priority": 1 if state in {"code_patch_required", "runtime_blocked_contract_gap"} or source_dimension_gap_required else 3,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "expected_ev_effect": (
                    "Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can "
                    "auto-classify and auto-apply without operator memory."
                ),
                "evidence": [
                    f"bucket_id={bucket_id}",
                    f"source_bucket_id={source_bucket_id}",
                    f"canonical_bucket={item.get('canonical_bucket')}",
                    f"legacy_raw_bucket_key={item.get('legacy_raw_bucket_key')}",
                    f"bucket_alias_version={item.get('bucket_alias_version')}",
                    f"dimension_set_version={item.get('dimension_set_version')}",
                    f"bucket_absorption_reason={item.get('bucket_absorption_reason')}",
                    f"ai_tier2_taxonomy_decision={item.get('ai_tier2_taxonomy_decision') or ((item.get('ai_tier2_comparative_review') or {}).get('selected_decision') if isinstance(item.get('ai_tier2_comparative_review'), dict) else None)}",
                    f"ai_tier2_selected_source={item.get('ai_tier2_selected_source') or ((item.get('ai_tier2_comparative_review') or {}).get('selected_source') if isinstance(item.get('ai_tier2_comparative_review'), dict) else None)}",
                    f"source_bucket_kind={item.get('source_bucket_kind')}",
                    f"stage={stage}",
                    f"classification_state={state}",
                    f"bucket_relation={item.get('bucket_relation')}",
                    f"recommended_action={item.get('recommended_action')}",
                    f"recommended_resolution={item.get('recommended_resolution')}",
                    f"source_dimension_gap={item.get('source_dimension_gap') or ''}",
                    f"missing_dimension_keys={item.get('missing_dimension_keys') or []}",
                    f"missing_lifecycle_flow_stage_keys={item.get('missing_lifecycle_flow_stage_keys') or []}",
                    f"unknown_reason_counts={item.get('unknown_reason_counts') or {}}",
                    f"source_quality_adjusted_ev_pct={item.get('source_quality_adjusted_ev_pct')}",
                    "runtime_effect=false_until_patch_review_passes",
                    "allowed_runtime_apply=false_until_contract_hook_tests_pass",
                ],
                "intent": (
                    "Add missing bucket taxonomy/provenance/post-apply attribution, then rerun discovery, "
                    "self review, and targeted tests before any runtime env selection."
                ),
                "next_postclose_metric": (
                    "lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or "
                    "live_auto_apply_ready, or keep it source-only with an explicit blocker."
                ),
                "files_likely_touched": [
                    "src/engine/lifecycle_bucket_discovery.py",
                    "src/engine/threshold_cycle_preopen_apply.py",
                    "src/engine/verify_threshold_cycle_postclose_chain.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py",
                    "postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped",
                ],
                "metric_contract": {
                    "metric_role": report.get("metric_role"),
                    "decision_authority": report.get("decision_authority"),
                    "window_policy": report.get("window_policy"),
                    "sample_floor": report.get("sample_floor"),
                    "primary_decision_metric": report.get("primary_decision_metric"),
                    "source_quality_gate": report.get("source_quality_gate"),
                    "forbidden_uses": report.get("forbidden_uses") or [],
                },
            }
        )
    source_dimension_summary = (
        report.get("source_dimension_gap_summary")
        if isinstance(report.get("source_dimension_gap_summary"), dict)
        else {}
    )
    rollup_count = _safe_int(source_dimension_summary.get("rollup_only_gap_count"))
    unknown_gap_count = _safe_int(
        (source_dimension_summary.get("source_dimension_gap_counts") or {}).get("unknown_source_dimensions")
        if isinstance(source_dimension_summary.get("source_dimension_gap_counts"), dict)
        else 0
    )
    if rollup_count > 0 and unknown_gap_count > 1:
        orders.append(
            {
                "order_id": "order_lifecycle_source_dimension_gap_rollup",
                "source_report_type": "lifecycle_bucket_discovery_source_dimension_rollup",
                "lifecycle_stage": "multi_stage",
                "target_subsystem": "lifecycle_bucket_discovery_taxonomy_provenance",
                "route": "source_dimension_rollup",
                "mapped_family": "lifecycle_bucket_discovery",
                "threshold_family": "lifecycle_bucket_discovery",
                "improvement_type": "source_dimension_gap_rollup_evidence",
                "confidence": "postclose_discovery_source",
                "priority": 3,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "expected_ev_effect": (
                    "Keep repeated source-dimension gaps visible without treating not-applicable or absorbed "
                    "dimensions as immediate code defects."
                ),
                "evidence": [
                    f"rollup_only_gap_count={rollup_count}",
                    f"unknown_source_dimensions={unknown_gap_count}",
                    f"recommended_resolution_counts={source_dimension_summary.get('recommended_resolution_counts') or {}}",
                    f"missing_dimension_key_counts={source_dimension_summary.get('missing_dimension_key_counts') or {}}",
                    "runtime_effect=false",
                    "allowed_runtime_apply=false",
                ],
                "intent": (
                    "Surface repeated source-dimension gaps in the postclose workorder chain so the operator "
                    "does not have to manually inspect raw bucket candidates."
                ),
                "next_postclose_metric": "source_dimension_gap_summary rollup/actionable counts remain visible.",
            }
        )
    quiet_summary = _quiet_gap_summary(report)
    quiet_type_counts = (
        quiet_summary.get("quiet_gap_type_counts")
        if isinstance(quiet_summary.get("quiet_gap_type_counts"), dict)
        else {}
    )
    quiet_orders: list[tuple[str, str, str, int]] = [
        (
            "order_lifecycle_quiet_gap_parent_conflict_rollup",
            "Lifecycle quiet gap parent conflict/exclusion review",
            "parent_conflict_exclusion_review",
            _safe_int(quiet_type_counts.get("parent_conflict_child"))
            + _safe_int(quiet_type_counts.get("exclusion_dimension_candidate")),
        ),
        (
            "order_lifecycle_quiet_gap_positive_source_only_rollup",
            "Lifecycle quiet gap positive source-only review",
            "positive_source_only_review",
            _safe_int(quiet_type_counts.get("positive_source_only_keep_collecting"))
            + _safe_int(quiet_type_counts.get("absorbed_into_parent_policy")),
        ),
        (
            "order_lifecycle_quiet_gap_ai_review_coverage_rollup",
            "Lifecycle quiet gap AI review coverage review",
            "ai_review_coverage_review",
            _safe_int(quiet_type_counts.get("ai_review_parsed_low_coverage")),
        ),
    ]
    parent_conflict_resolution = (
        report.get("parent_conflict_resolution")
        if isinstance(report.get("parent_conflict_resolution"), list)
        else []
    )
    for order_id, title, route, count in quiet_orders:
        if count <= 0:
            continue
        is_conflict_order = route == "parent_conflict_exclusion_review"
        order = {
            "order_id": order_id,
            "title": title,
            "source_report_type": "lifecycle_bucket_discovery_quiet_gap_rollup",
            "lifecycle_stage": "multi_stage",
            "target_subsystem": "lifecycle_bucket_discovery_taxonomy_provenance",
            "route": route,
            "mapped_family": "lifecycle_bucket_discovery",
            "threshold_family": "lifecycle_bucket_discovery",
            "improvement_type": "quiet_gap_rollup_evidence",
            "confidence": "postclose_discovery_source",
            "priority": 3,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "expected_ev_effect": (
                "Keep quiet source-quality gaps visible without treating every rollup as an immediate "
                "code patch requirement."
            ),
            "evidence": [
                f"quiet_gap_count={quiet_summary.get('quiet_gap_count')}",
                f"rollup_required_count={quiet_summary.get('rollup_required_count')}",
                f"sim_live_connected_quiet_gap_count={quiet_summary.get('sim_live_connected_quiet_gap_count')}",
                f"quiet_gap_type_counts={quiet_type_counts}",
                f"ai_review_coverage={quiet_summary.get('ai_review_coverage') or {}}",
                "runtime_effect=false",
                "allowed_runtime_apply=false",
            ],
            "intent": (
                "Surface parent conflict/exclusion children, positive source-only keep-collecting rows, "
                "absorbed parent-policy evidence, and low AI coverage in the postclose workorder chain."
            ),
            "next_postclose_metric": "quiet_gap_summary rollup counts remain visible until explicitly resolved.",
        }
        if is_conflict_order:
            conflict_resolved = len(parent_conflict_resolution) > 0
            order["implementation_candidate"] = conflict_resolved
            order["explicit_redecision_required"] = not conflict_resolved
            if conflict_resolved:
                resolution_states = Counter(
                    str(p.get("conflict_resolution_state") or "")
                    for p in parent_conflict_resolution
                )
                sim_eligible = sum(
                    1 for p in parent_conflict_resolution
                    if p.get("sim_policy_eligible_after_resolution")
                )
                order["evidence"].extend([
                    f"parent_conflict_resolution_count={len(parent_conflict_resolution)}",
                    f"resolution_states={dict(resolution_states)}",
                    f"sim_eligible_after_resolution={sim_eligible}",
                ])
                order["conflict_resolution_acceptance_test"] = "pass"
                order["implementation_id"] = "parent_conflict_resolution_produced"
                order["implementation_status"] = "implemented"
                order["implementation_checks"] = [
                    {
                        "name": "parent_conflict_resolution_present",
                        "status": "pass",
                        "resolution_count": len(parent_conflict_resolution),
                        "sim_eligible_after_resolution": sim_eligible,
                    }
                ]
            else:
                order["evidence"].append(
                    "parent_conflict_resolution_missing: child_conflict_warning > 0 but no resolution items produced"
                )
                order["conflict_resolution_acceptance_test"] = "fail"
                order["warnings"] = [
                    "parent_conflict_resolution_missing",
                ]
        orders.append(order)
    return orders


def _lifecycle_overnight_bucket_followup_orders(report: dict[str, Any]) -> list[dict[str, Any]]:
    attribution = (
        report.get("overnight_bucket_attribution")
        if isinstance(report.get("overnight_bucket_attribution"), dict)
        else {}
    )
    workorders = attribution.get("code_improvement_workorders")
    if not isinstance(workorders, list) or not workorders:
        return []
    contract = {
        "metric_role": attribution.get("metric_role"),
        "decision_authority": attribution.get("decision_authority"),
        "window_policy": attribution.get("window_policy"),
        "sample_floor": attribution.get("sample_floor"),
        "primary_decision_metric": attribution.get("primary_decision_metric"),
        "source_quality_gate": attribution.get("source_quality_gate"),
        "forbidden_uses": attribution.get("forbidden_uses") or [],
    }
    implementation_status, implementation_provenance = _implementation_marker_from_attribution(attribution)
    orders: list[dict[str, Any]] = []
    for item in workorders:
        if not isinstance(item, dict):
            continue
        bucket_type = str(item.get("bucket_type") or "").strip()
        bucket_key = str(item.get("bucket_key") or "").strip()
        if not bucket_type or not bucket_key:
            continue
        orders.append(
            {
                "order_id": _lifecycle_overnight_bucket_order_id(item),
                "title": f"LDM overnight bucket attribution follow-up: {bucket_type}={bucket_key}",
                "source_report_type": "lifecycle_decision_matrix_overnight_bucket_attribution",
                "lifecycle_stage": "overnight",
                "target_subsystem": "lifecycle_decision_matrix",
                "route": "source_quality_or_bounded_tunable_candidate",
                "mapped_family": "scalp_sim_overnight_ai_carry",
                "threshold_family": "scalp_sim_overnight_ai_carry",
                "improvement_type": "overnight_bucket_source_quality_attribution",
                "confidence": "daily_ldm_source",
                "priority": 4,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "implementation_status": _implementation_status_for_bucket(item, implementation_status),
                "implementation_provenance": _implementation_provenance_for_bucket(
                    item,
                    implementation_provenance,
                ),
                "expected_ev_effect": (
                    "Keep SELL_TODAY/HOLD_OVERNIGHT bucket attribution and next-day carry labels connected "
                    "as source-only evidence for threshold-cycle rolling confirmation."
                ),
                "evidence": [
                    f"workorder_id={item.get('workorder_id')}",
                    f"bucket_type={bucket_type}",
                    f"bucket_key={bucket_key}",
                    f"reason={item.get('reason')}",
                    f"recommended_route={item.get('recommended_route')}",
                    f"metric_role={item.get('metric_role') or contract.get('metric_role')}",
                    f"decision_authority={contract.get('decision_authority')}",
                    f"primary_decision_metric={contract.get('primary_decision_metric')}",
                    "runtime_effect=false",
                    "allowed_runtime_apply=false",
                ],
                "intent": (
                    "Preserve overnight action/status/confidence/source-quality attribution without turning "
                    "the sim-only decision into a hard gate or real sell/order route."
                ),
                "next_postclose_metric": (
                    "lifecycle_decision_matrix.overnight_bucket_attribution candidates/workorders must remain "
                    "visible in threshold EV/runtime summary, and postclose verifier must fail if dropped."
                ),
                "files_likely_touched": [
                    "src/engine/scalp_sim_overnight.py",
                    "src/engine/lifecycle_decision_matrix.py",
                    "src/engine/daily_threshold_cycle_report.py",
                    "src/engine/runtime_approval_summary.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py",
                    "postclose verifier fails if LDM overnight bucket candidates/workorders are not propagated",
                ],
                "metric_contract": contract,
            }
        )
    return orders


def _pipeline_event_verbosity_report_path(target_date: str) -> Path:
    return PIPELINE_EVENT_VERBOSITY_DIR / f"pipeline_event_verbosity_{target_date}.json"


def _observation_source_quality_audit_path(target_date: str) -> Path:
    return OBSERVATION_SOURCE_QUALITY_AUDIT_DIR / f"observation_source_quality_audit_{target_date}.json"


def _codebase_performance_report_path(target_date: str) -> Path:
    return CODEBASE_PERFORMANCE_WORKORDER_DIR / f"codebase_performance_workorder_{target_date}.json"


def _pipeline_event_verbosity_followup_orders(report: dict[str, Any]) -> list[dict[str, Any]]:
    if not report:
        return []
    state = str(report.get("state") or "").strip()
    recommended = str(report.get("recommended_workorder_state") or "").strip()
    raw_stream = report.get("raw_stream") if isinstance(report.get("raw_stream"), dict) else {}
    parity = report.get("parity") if isinstance(report.get("parity"), dict) else {}
    producer = report.get("producer_summary") if isinstance(report.get("producer_summary"), dict) else {}
    evidence = [
        f"state={state}",
        f"recommended_workorder_state={recommended}",
        f"raw_size_bytes={raw_stream.get('raw_size_bytes')}",
        f"high_volume_line_count={raw_stream.get('high_volume_line_count')}",
        f"high_volume_byte_share_pct={raw_stream.get('high_volume_byte_share_pct')}",
        f"producer_summary_exists={producer.get('exists')}",
        f"parity_ok={parity.get('ok')}",
        f"raw_derived_event_count={parity.get('raw_derived_event_count')}",
        f"producer_event_count={parity.get('producer_event_count')}",
    ]
    base = {
        "source_report_type": "pipeline_event_verbosity",
        "lifecycle_stage": "ops_volume_diagnostic",
        "target_subsystem": "runtime_instrumentation",
        "runtime_effect": False,
        "route": "instrumentation_order",
        "confidence": "consensus",
        "expected_ev_effect": "none_direct_ops_cpu_io_reduction_only",
        "next_postclose_metric": "pipeline_event_verbosity.parity.ok",
    }
    if recommended in {"open_shadow_order", "block_suppress_and_fix_shadow"}:
        return [
            {
                **base,
                "order_id": "order_pipeline_event_compaction_v2_shadow",
                "title": "Pipeline event compaction V2 shadow producer summary",
                "priority": 1,
                "intent": "Keep or repair producer-side high-volume diagnostic summary in shadow mode without raw suppression.",
                "evidence": evidence,
                "files_likely_touched": [
                    "src/utils/pipeline_event_logger.py",
                    "src/engine/pipeline_event_summary.py",
                    "src/engine/pipeline_event_verbosity_report.py",
                ],
                "acceptance_tests": [
                    "pytest src/tests/test_pipeline_event_logger.py src/tests/test_pipeline_event_verbosity_report.py",
                ],
            }
        ]
    if recommended == "open_suppress_guard_order":
        return [
            {
                **base,
                "order_id": "order_pipeline_event_compaction_v2_suppress_guard",
                "title": "Pipeline event compaction V2 suppress guard",
                "priority": 2,
                "intent": "Design default-off suppress guard after repeated shadow parity pass; do not enable suppression automatically.",
                "evidence": evidence,
                "files_likely_touched": [
                    "src/utils/pipeline_event_logger.py",
                    "src/engine/pipeline_event_verbosity_report.py",
                    "docs/time-based-operations-runbook.md",
                ],
                "acceptance_tests": [
                    "pytest src/tests/test_pipeline_event_logger.py src/tests/test_pipeline_event_verbosity_report.py",
                ],
            }
        ]
    return []


_SIM_FILL_CONTRACT_GAP_ORDER_METRIC_THRESHOLD = 3
_LDM_MATCH_MISSING_ORDER_THRESHOLD = 5
_ACTIVE_SEED_NONE_ORDER_THRESHOLD = 3


def _sim_fill_and_match_report_contract_orders(ev_report: dict[str, Any], source_quality_report: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    orders: list[dict[str, Any]] = []
    calibration = ev_report.get("calibration") if isinstance(ev_report.get("calibration"), dict) else {}
    scalp_simulator = calibration.get("scalp_simulator") if isinstance(calibration.get("scalp_simulator"), dict) else {}
    lifecycle_match = (
        scalp_simulator.get("lifecycle_bucket_match_aggregation")
        if isinstance(scalp_simulator.get("lifecycle_bucket_match_aggregation"), dict)
        else {}
    )
    swing_micro = (
        scalp_simulator.get("swing_micro_source_quality")
        if isinstance(scalp_simulator.get("swing_micro_source_quality"), dict)
        else {}
    )

    sim_quality = {}
    family_reports = ev_report.get("family_reports") if isinstance(ev_report.get("family_reports"), list) else []
    for family in family_reports:
        if not isinstance(family, dict):
            continue
        if str(family.get("family") or "") == "dynamic_entry_price_resolver":
            sim_quality = family.get("sim_submit_path_quality") if isinstance(family.get("sim_submit_path_quality"), dict) else {}
            break

    has_canonical_fill_price_gap = False
    unpriced_no_canonical_total = 0
    if sim_quality:
        for stage, data in sim_quality.items():
            if not isinstance(data, dict):
                continue
            defect = data.get("canonical_sim_fill_price_defect_breakdown") if isinstance(data.get("canonical_sim_fill_price_defect_breakdown"), dict) else {}
            unpriced_no_canonical_total += _safe_int(defect.get("unpriced_no_canonical"), 0)
    has_canonical_fill_price_gap = unpriced_no_canonical_total > 0

    active_seed_none = _safe_int(lifecycle_match.get("active_seed_matched_none_count"), 0)
    contract_missing = _safe_int(lifecycle_match.get("contract_missing_count"), 0)
    not_instrumented = _safe_int(lifecycle_match.get("not_instrumented_count"), 0)
    prefix_parent_missing = _safe_int(lifecycle_match.get("active_seed_prefix_matched_parent_missing_count"), 0)
    natural_no_match = _safe_int(lifecycle_match.get("natural_no_match_count"), 0)
    hypothesis_no_match = _safe_int(lifecycle_match.get("hypothesis_matched_but_parent_bucket_no_match_count"), 0)
    panic_excluded = _safe_int(lifecycle_match.get("panic_scale_in_stage_excluded_count"), 0)
    provenance_gap = _safe_int(swing_micro.get("provenance_gap_count"), 0)
    missing_ws_quote = _safe_int(swing_micro.get("missing_ws_quote_source_count"), 0)

    source_quality_status = str((source_quality_report or {}).get("status") or "").strip()
    source_quality_contract_gap = source_quality_status in {"fail", "missing", "incomplete"}

    base = {
        "source_report_type": "threshold_cycle_ev_report",
        "lifecycle_stage": "entry",
        "target_subsystem": "daily_threshold_cycle_report",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "expected_ev_effect": "Keep fill/EV denominator clean and ADM/LDM/sim matching contracts accurate without affecting real order authority.",
        "forbidden_uses": [
            "runtime_threshold_apply",
            "order_submit",
            "provider_route_change",
            "bot_restart",
            "cap_release",
        ],
    }

    if has_canonical_fill_price_gap:
        orders.append({
            **base,
            "order_id": "order_sim_fill_canonical_price_contract_gap",
            "title": "Sim fill canonical price contract gap",
            "priority": 1,
            "route": "source_quality_gap",
            "mapped_family": "dynamic_entry_price_resolver",
            "threshold_family": "dynamic_entry_price_resolver",
            "improvement_type": "sim_fill_canonical_price_contract_gap",
            "confidence": "postclose_threshold_ev_source",
            "intent": "Priced sim fill rows must produce a canonical_sim_fill_price. Fix the producer or report contract so no priced row has unpriced_no_canonical classification.",
            "evidence": [
                f"unpriced_no_canonical_total={unpriced_no_canonical_total}",
                f"has_canonical_fill_price_gap={has_canonical_fill_price_gap}",
            ],
            "next_postclose_metric": "canonical_sim_fill_price_defect_breakdown.unpriced_no_canonical=0 for all priced stages",
            "files_likely_touched": [
                "src/engine/daily_threshold_cycle_report.py",
                "src/engine/sniper_state_handlers.py",
                "docs/report-based-automation-traceability.md",
            ],
            "acceptance_tests": [
                "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_daily_threshold_cycle_report.py",
            ],
        })

    if contract_missing >= _LDM_MATCH_MISSING_ORDER_THRESHOLD or prefix_parent_missing >= _LDM_MATCH_MISSING_ORDER_THRESHOLD:
        orders.append({
            **base,
            "order_id": "order_active_seed_or_ldm_match_missing_contract_gap",
            "title": "Contract missing or active seed parent bridge missing above threshold",
            "priority": 1,
            "route": "source_quality_gap",
            "mapped_family": "lifecycle_decision_matrix_runtime",
            "threshold_family": "lifecycle_decision_matrix_runtime",
            "improvement_type": "active_seed_ldm_match_contract_gap",
            "confidence": "postclose_threshold_ev_source",
            "intent": "contract_missing indicates required instrumentation gap; prefix_matched_parent_missing indicates active seed prefix found but parent lifecycle-flow approved row not closed. Both must be diagnosed.",
            "evidence": [
                f"contract_missing_count={contract_missing} (lifecycle-eligible stages only)",
                f"not_instrumented_count={not_instrumented} (excluded: diagnostic/observation stages without lifecycle contract requirement)",
                f"active_seed_prefix_matched_parent_missing_count={prefix_parent_missing}",
                f"active_seed_matched_none_count={active_seed_none}",
                f"natural_no_match_count={natural_no_match} (excluded from workorder trigger)",
                f"panic_scale_in_stage_excluded_count={panic_excluded} (excluded from workorder trigger)",
                f"hypothesis_matched_but_parent_bucket_no_match_count={hypothesis_no_match} (includes natural_no_match + prefix_matched_parent_missing)",
                f"ldm_match_missing_order_threshold={_LDM_MATCH_MISSING_ORDER_THRESHOLD}",
            ],
            "next_postclose_metric": "contract_missing_count < threshold AND prefix_parent_missing_count < threshold",
            "files_likely_touched": [
                "src/engine/daily_threshold_cycle_report.py",
                "src/engine/observation_source_quality_audit.py",
                "docs/report-based-automation-traceability.md",
            ],
            "acceptance_tests": [
                "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_daily_threshold_cycle_report.py src/tests/test_observation_source_quality_audit.py",
            ],
        })

    if provenance_gap > 0 and missing_ws_quote > 0 and swing_micro.get("ready_count", 0) > 0:
        orders.append({
            **base,
            "order_id": "order_swing_micro_provenance_gap_missing_from_report",
            "title": "Swing micro ws_quote_source=missing provenance gap not surfaced in postclose report",
            "priority": 2,
            "route": "source_quality_gap",
            "mapped_family": "swing_micro_source_quality",
            "threshold_family": "swing_micro_source_quality",
            "improvement_type": "swing_micro_provenance_gap",
            "confidence": "postclose_threshold_ev_source",
            "intent": "Swing micro ws_quote_source=missing with orderbook_micro ready state is a provenance gap, not a readiness gap. Ensure it is tracked separately in postclose reports.",
            "evidence": [
                f"provenance_gap_count={provenance_gap}",
                f"missing_ws_quote_source_count={missing_ws_quote}",
                f"ready_count={swing_micro.get('ready_count', 0)}",
                f"wide_spread_count={swing_micro.get('wide_spread_count', 0)}",
                f"ofi_outlier_count={swing_micro.get('ofi_outlier_count', 0)}",
            ],
            "next_postclose_metric": "swing_micro_source_quality.provenance_gap_count visible and ws_quote_source=missing not mixed with readiness",
            "files_likely_touched": [
                "src/engine/daily_threshold_cycle_report.py",
                "src/engine/observation_source_quality_audit.py",
                "src/engine/sniper_state_handlers.py",
                "docs/report-based-automation-traceability.md",
            ],
            "acceptance_tests": [
                "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_daily_threshold_cycle_report.py src/tests/test_observation_source_quality_audit.py",
            ],
        })

    if source_quality_contract_gap:
        orders.append({
            **base,
            "order_id": "order_source_quality_report_contract_status_gap",
            "title": "Source quality report contract status failed/missing/incomplete",
            "priority": 0,
            "route": "source_quality_hard_gap",
            "mapped_family": "observation_source_quality_audit",
            "threshold_family": "observation_source_quality_audit",
            "improvement_type": "report_contract_gap",
            "confidence": "postclose_source_quality_fail",
            "intent": "Report contract status is failed/missing/incomplete. Tuning inputs using this report must be blocked until the contract is restored.",
            "evidence": [
                f"source_quality_status={source_quality_status}",
            ],
            "next_postclose_metric": "observation_source_quality_audit status=pass or warning",
            "files_likely_touched": [
                "src/engine/observation_source_quality_audit.py",
                "src/engine/daily_threshold_cycle_report.py",
                "docs/report-based-automation-traceability.md",
            ],
            "acceptance_tests": [
                "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_observation_source_quality_audit.py src/tests/test_build_code_improvement_workorder.py",
            ],
        })

    return orders


def _observation_source_quality_followup_orders(report: dict[str, Any]) -> list[dict[str, Any]]:
    if not report:
        return []
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    raw_row_exclusion = (
        report.get("raw_row_exclusion")
        if isinstance(report.get("raw_row_exclusion"), dict)
        else {}
    )
    raw_row_exclusion = _raw_row_exclusion_with_manifest_details(raw_row_exclusion)
    if (
        str(report.get("status") or "").strip() not in {"warning", "fail"}
        and int(raw_row_exclusion.get("excluded_row_count") or 0) <= 0
    ):
        return []
    hard_gaps = (
        report.get("hard_blocking_contract_gaps")
        if isinstance(report.get("hard_blocking_contract_gaps"), list)
        else []
    )
    stage_contracts = report.get("stage_contracts") if isinstance(report.get("stage_contracts"), dict) else {}
    high_volume_gaps = (
        report.get("high_volume_no_source_fields")
        if isinstance(report.get("high_volume_no_source_fields"), list)
        else []
    )
    unknown_token_findings = (
        report.get("unknown_token_findings")
        if isinstance(report.get("unknown_token_findings"), list)
        else []
    )

    def unknown_findings_covered_by_known_fix() -> bool:
        fields: set[str] = set()
        for finding in unknown_token_findings:
            if not isinstance(finding, dict):
                continue
            for field in finding.get("fields") or []:
                if isinstance(field, dict) and field.get("field"):
                    fields.add(str(field.get("field")))
        return bool(fields) and fields.issubset(KNOWN_FIXED_UNKNOWN_TOKEN_FIELDS)

    warning_stages = [
        stage
        for stage, result in stage_contracts.items()
        if isinstance(result, dict) and result.get("status") == "warning"
    ]
    evidence = [
        f"status={report.get('status')}",
        f"event_count={summary.get('event_count')}",
        f"warning_stage_count={summary.get('warning_stage_count')}",
        f"warning_stages={','.join(warning_stages[:12])}",
        f"high_volume_no_source_field_stage_count={summary.get('high_volume_no_source_field_stage_count')}",
        f"unknown_token_stage_count={summary.get('unknown_token_stage_count')}",
        f"review_warning_count={summary.get('review_warning_count')}",
        "decision_authority=source_quality_only",
        "runtime_effect=false",
    ]
    base = {
        "source_report_type": "observation_source_quality_audit",
        "lifecycle_stage": "source_quality_gate",
        "target_subsystem": "runtime_instrumentation",
        "runtime_effect": False,
        "route": "instrumentation_order",
        "confidence": "audit",
        "expected_ev_effect": "none_direct_source_quality_attribution_only",
        "next_postclose_metric": "observation_source_quality_audit.warning_stage_count and high_volume_no_source_field_stage_count",
        "forbidden_uses": [
            "runtime_threshold_apply",
            "order_submit",
            "provider_route_change",
            "bot_restart",
            "cap_release",
            "hard_safety_relaxation",
        ],
    }
    orders: list[dict[str, Any]] = []
    if summary.get("tuning_input_allowed") is False or hard_gaps:
        hard_evidence = [
            *evidence,
            f"tuning_input_allowed={summary.get('tuning_input_allowed')}",
            f"blocked_reason={summary.get('blocked_reason')}",
            f"hard_blocking_contract_gap_count={summary.get('hard_blocking_contract_gap_count')}",
            f"hard_blocking_stages={','.join(str(stage) for stage in (summary.get('hard_blocking_stages') or [])[:20])}",
            "forbidden_uses=EV/rolling/MTD/cumulative tuning/live-auto promotion/runtime approval until fixed",
            "required_acceptance_tests=source-quality audit pass, EV/runtime summary source_quality_gate pass_or_not_evaluated, postclose verifier pass",
        ]
        for gap in hard_gaps[:12]:
            if not isinstance(gap, dict):
                continue
            hard_evidence.append(
                "gap:"
                f"stage={gap.get('stage')} "
                f"reason={gap.get('reason')} "
                f"missing_fields={','.join(str(field) for field in (gap.get('missing_fields') or [])[:12]) or '-'} "
                f"sample_count={gap.get('sample_count')} "
                f"first_timestamp={gap.get('first_timestamp') or '-'} "
                f"last_timestamp={gap.get('last_timestamp') or '-'}"
            )
        orders.append(
            {
                **base,
                "order_id": "order_observation_source_quality_hard_block_contract_gap",
                "title": "Observation source-quality hard block contract gap",
                "priority": 0,
                "route": "source_quality_gap",
                "mapped_family": "observation_source_quality_audit",
                "threshold_family": "observation_source_quality_audit",
                "improvement_type": "source_quality_hard_block_contract_gap",
                "intent": (
                    "Fix producer-side contract/provenance gaps before any affected raw row/window can feed EV, "
                    "rolling/MTD/cumulative tuning, live-auto promotion, or runtime approval."
                ),
                "evidence": hard_evidence,
                "files_likely_touched": [
                    "src/engine/sniper_state_handlers.py",
                    "src/engine/observation_source_quality_audit.py",
                    "src/engine/build_code_improvement_workorder.py",
                    "docs/report-based-automation-traceability.md",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_observation_source_quality_audit.py src/tests/test_build_code_improvement_workorder.py src/tests/test_threshold_cycle_ev_report.py src/tests/test_runtime_approval_summary.py src/tests/test_verify_threshold_cycle_postclose_chain.py",
                ],
            }
        )
    excluded_row_count = int(raw_row_exclusion.get("excluded_row_count") or 0)
    if excluded_row_count > 0:
        context_review = _raw_row_exclusion_limit_up_locked_context(raw_row_exclusion)
        market_halt_context_review = None if context_review else _raw_row_exclusion_market_halt_context(raw_row_exclusion)
        context_classification = None
        if context_review:
            context_classification = "limit_up_locked_context"
        elif market_halt_context_review:
            context_classification = "market_halt_or_circuit_window_overlap"
        stage_counts = (
            raw_row_exclusion.get("stage_counts")
            if isinstance(raw_row_exclusion.get("stage_counts"), dict)
            else {}
        )
        field_gap_counts = (
            raw_row_exclusion.get("field_gap_counts")
            if isinstance(raw_row_exclusion.get("field_gap_counts"), dict)
            else {}
        )
        exclusion_reasons = (
            raw_row_exclusion.get("exclusion_reasons")
            if isinstance(raw_row_exclusion.get("exclusion_reasons"), dict)
            else {}
        )
        producer_hint = (
            raw_row_exclusion.get("producer_hint")
            if isinstance(raw_row_exclusion.get("producer_hint"), list)
            else []
        )
        sample_rows = (
            raw_row_exclusion.get("sample_rows")
            if isinstance(raw_row_exclusion.get("sample_rows"), list)
            else []
        )
        raw_exclusion_evidence = [
            *evidence,
            f"raw_row_exclusion_manifest={raw_row_exclusion.get('manifest_path') or '-'}",
            f"excluded_row_count={excluded_row_count}",
            f"stage_counts={json.dumps(stage_counts, ensure_ascii=False, sort_keys=True)}",
            f"field_gap_counts={json.dumps(field_gap_counts, ensure_ascii=False, sort_keys=True)}",
            f"exclusion_reasons={json.dumps(exclusion_reasons, ensure_ascii=False, sort_keys=True)}",
            f"first_timestamp={raw_row_exclusion.get('first_timestamp') or '-'}",
            f"last_timestamp={raw_row_exclusion.get('last_timestamp') or '-'}",
            "forbidden_uses=EV/rolling/MTD/cumulative tuning/live-auto promotion/runtime approval for excluded rows",
            "required_action=fix producer provenance/source-quality cause or mark reviewed_not_available/waiting_sample_only explicitly",
        ]
        for hint in producer_hint[:12]:
            if isinstance(hint, dict):
                raw_exclusion_evidence.append(
                    "producer_hint:"
                    f"stage={hint.get('stage')} "
                    f"count={hint.get('count')} "
                    f"pipeline={hint.get('pipeline') or '-'} "
                    f"subsystem={hint.get('subsystem') or '-'} "
                    f"top_reasons={','.join(str(item) for item in (hint.get('top_reasons') or [])[:8]) or '-'}"
                )
        for row in sample_rows[:8]:
            if isinstance(row, dict):
                raw_exclusion_evidence.append(
                    "sample_row:"
                    f"line_no={row.get('line_no')} "
                    f"stage={row.get('stage')} "
                    f"record_id={row.get('record_id')} "
                    f"reasons={','.join(str(item) for item in (row.get('reasons') or [])[:8]) or '-'} "
                    f"gap_fields={json.dumps(row.get('gap_fields') or {}, ensure_ascii=False, sort_keys=True)}"
                )
        if context_review:
            raw_exclusion_evidence.extend(
                [
                    "context_classification=limit_up_locked_context",
                    f"context_evidence={json.dumps(context_review, ensure_ascii=False, sort_keys=True)}",
                    (
                        "required_action=review postclose only; do not auto-implement unless non-limit-up rows "
                        "repeat the same zero intraday range gap or independent high/low/candle source loss is proven"
                    ),
                ]
            )
        if market_halt_context_review:
            raw_exclusion_evidence.extend(
                [
                    "context_classification=market_halt_or_circuit_window_overlap",
                    f"context_evidence={json.dumps(market_halt_context_review, ensure_ascii=False, sort_keys=True)}",
                    (
                        "required_action=review postclose only; do not auto-implement unless the same zero "
                        "intraday range gap repeats after normal market flow resumes"
                    ),
                ]
            )
        orders.append(
            {
                **base,
                "order_id": "order_observation_source_quality_raw_row_exclusion_producer_gap",
                "title": (
                    "Observation source-quality raw row exclusion limit-up locked context"
                    if context_review
                    else "Observation source-quality raw row exclusion market halt context"
                    if market_halt_context_review
                    else "Observation source-quality raw row exclusion producer gap"
                ),
                "priority": 0,
                "route": (
                    "review_required_limit_up_locked_context"
                    if context_review
                    else "review_required_market_halt_context"
                    if market_halt_context_review
                    else "source_quality_raw_row_exclusion_producer_fix"
                ),
                "mapped_family": "observation_source_quality_audit",
                "threshold_family": "observation_source_quality_audit",
                "improvement_type": (
                    "source_quality_raw_row_exclusion_limit_up_locked_context"
                    if context_review
                    else "source_quality_raw_row_exclusion_market_halt_context"
                    if market_halt_context_review
                    else "source_quality_raw_row_exclusion_producer_gap"
                ),
                "intent": (
                    "Keep the excluded rows out of tuning inputs, but treat the current cluster as a reviewed "
                    "limit-up locked market context until non-limit-up evidence proves a producer gap."
                    if context_review
                    else (
                        "Keep the excluded rows out of tuning inputs, but treat the current cluster as a reviewed "
                        "market halt/circuit-breaker recovery context until post-resume evidence proves a producer gap."
                    )
                    if market_halt_context_review
                    else (
                        "Analyze all excluded raw rows by stage/field/reason and fix producer-side source-quality "
                        "or provenance causes so the postclose chain does not repeatedly need to exclude the same "
                        "class of rows from tuning inputs."
                    )
                ),
                "evidence": raw_exclusion_evidence,
                "files_likely_touched": [
                    "src/engine/observation_source_quality_audit.py",
                    "src/engine/build_code_improvement_workorder.py",
                    "src/engine/sniper_state_handlers.py",
                    "src/engine/lifecycle_decision_matrix.py",
                    "docs/report-based-automation-traceability.md",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_observation_source_quality_audit.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py",
                ],
                "raw_row_exclusion_context_classification": context_classification,
                "raw_row_exclusion_context": context_review or market_halt_context_review,
                "terminal_disposition": "no_code_required_pending_policy_classification" if context_classification else None,
            }
        )
    if unknown_token_findings:
        producer_fix_implemented = unknown_findings_covered_by_known_fix()
        unknown_evidence = [
            *evidence,
            "unknown_token_policy=warning_only_not_tuning_hard_block",
            "required_action=producer_provenance_fix_or_explicit_reviewed_not_available_label",
            "forbidden_uses=ignore_unknown_token_warning/silent_tuning_promotion_without_review",
        ]
        top_fields: list[str] = []
        for finding in unknown_token_findings:
            if not isinstance(finding, dict):
                continue
            fields = finding.get("fields") if isinstance(finding.get("fields"), list) else []
            field_bits = []
            for field in fields:
                if not isinstance(field, dict):
                    continue
                field_bits.append(
                    f"{field.get('field')}:{field.get('count')}:{field.get('rate')}"
                )
                top_fields.append(str(field.get("field") or ""))
            unknown_evidence.append(
                "unknown:"
                f"stage={finding.get('stage')} "
                f"event_count={finding.get('event_count')} "
                f"fields={','.join(field_bits) or '-'}"
            )
        orders.append(
            {
                **base,
                "order_id": "order_observation_source_quality_unknown_token_provenance_gap",
                "title": "Observation source-quality unknown-token provenance gap",
                "priority": 1,
                "route": "source_quality_warning_producer_fix",
                "mapped_family": "observation_source_quality_audit",
                "threshold_family": "observation_source_quality_audit",
                "improvement_type": "source_quality_unknown_token_provenance_gap",
                "intent": (
                    "Trace high-rate unknown-token warning fields back to their producers and replace silent "
                    "unknown placeholders with real provenance or explicit reviewed not_available/insufficient_sample "
                    "labels, without changing runtime thresholds, orders, provider route, bot state, or safety guards."
                ),
                "evidence": [
                    *unknown_evidence,
                    f"top_unknown_fields={','.join(item for item in top_fields if item)}",
                ],
                "files_likely_touched": [
                    "src/engine/observation_source_quality_audit.py",
                    "src/engine/build_code_improvement_workorder.py",
                    "src/engine/sniper_state_handlers.py",
                    "src/engine/lifecycle_decision_matrix.py",
                    "src/engine/scalp_sim_overnight.py",
                    "docs/report-based-automation-traceability.md",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_observation_source_quality_audit.py src/tests/test_build_code_improvement_workorder.py",
                ],
                "implementation_status": "implemented_but_waiting_sample" if producer_fix_implemented else None,
                "implementation_provenance": {
                    "producer_fix_status": "implemented_waiting_new_postfix_raw"
                    if producer_fix_implemented
                    else "open_unknown_field_producer_fix_required",
                    "fixed_unknown_fields": sorted(KNOWN_FIXED_UNKNOWN_TOKEN_FIELDS),
                    "current_raw_contains_pre_fix_rows": producer_fix_implemented,
                },
            }
        )
    if any(stage in warning_stages for stage in ("ai_confirmed", "blocked_ai_score", "wait65_79_ev_candidate")):
        orders.append(
            {
                **base,
                "order_id": "order_ai_source_quality_not_evaluated_provenance",
                "title": "AI source-quality not-evaluated provenance for cooldown and score50 paths",
                "priority": 1,
                "intent": (
                    "Mark cooldown/score50 AI events as not_evaluated with reason and inherit available "
                    "source-quality snapshots where appropriate, without changing score thresholds or provider route."
                ),
                "evidence": evidence,
                "files_likely_touched": [
                    "src/engine/sniper_state_handlers.py",
                    "src/engine/observation_source_quality_audit.py",
                ],
                "acceptance_tests": [
                    "pytest src/tests/test_observation_source_quality_audit.py src/tests/test_state_handler_fast_signatures.py",
                ],
            }
        )
    if high_volume_gaps:
        gap_stages = [
            str(item.get("stage"))
            for item in high_volume_gaps
            if isinstance(item, dict) and item.get("stage")
        ][:12]
        orders.append(
            {
                **base,
                "order_id": "order_high_volume_diagnostic_stage_contract_labels",
                "title": "High-volume diagnostic stage metric contract labels",
                "priority": 2,
                "intent": (
                    "Label high-volume funnel diagnostics as ops_volume_diagnostic or funnel_count with explicit "
                    "decision_authority, so they cannot be mistaken for threshold/order inputs."
                ),
                "evidence": [*evidence, f"gap_stages={','.join(gap_stages)}"],
                "files_likely_touched": [
                    "src/engine/sniper_state_handlers.py",
                    "src/engine/observation_source_quality_audit.py",
                    "docs/report-based-automation-traceability.md",
                ],
                "acceptance_tests": [
                    "pytest src/tests/test_observation_source_quality_audit.py src/tests/test_build_code_improvement_workorder.py",
                ],
            }
        )
    swing_warning_stages = [
        stage
        for stage in warning_stages
        if stage
        in {
            "swing_probe_state_persisted",
            "scale_in_price_p2_observe",
            "swing_scale_in_micro_context_observed",
            "scale_in_price_resolved",
            "swing_probe_scale_in_order_assumed_filled",
            "swing_sim_scale_in_order_assumed_filled",
        }
    ]
    if swing_warning_stages:
        stage_evidence: list[str] = []
        for stage in swing_warning_stages[:8]:
            contract = stage_contracts.get(stage) if isinstance(stage_contracts.get(stage), dict) else {}
            missing = contract.get("missing_violations") if isinstance(contract.get("missing_violations"), dict) else {}
            missing_fields = ",".join(str(key) for key in list(missing)[:8])
            stage_evidence.append(
                f"{stage}:sample_count={contract.get('sample_count')} missing_fields={missing_fields or '-'}"
            )
        orders.append(
            {
                **base,
                "order_id": "order_swing_source_quality_micro_context_provenance",
                "title": "Swing source-quality micro context provenance",
                "priority": 2,
                "intent": (
                    "Route swing probe-state contract warnings and OFI/QI micro-context observer gaps as "
                    "source-quality workorders, including fresh WS quote provenance where available, without "
                    "changing swing thresholds, order submission, approval gates, or provider route."
                ),
                "evidence": [
                    *evidence,
                    f"swing_warning_stages={','.join(swing_warning_stages)}",
                    *stage_evidence,
                ],
                "files_likely_touched": [
                    "src/engine/sniper_state_handlers.py",
                    "src/engine/observation_source_quality_audit.py",
                    "src/engine/build_code_improvement_workorder.py",
                    "docs/report-based-automation-traceability.md",
                ],
                "acceptance_tests": [
                    "pytest src/tests/test_observation_source_quality_audit.py "
                    "src/tests/test_swing_model_selection_funnel_repair.py "
                    "src/tests/test_build_code_improvement_workorder.py",
                ],
            }
        )
    if (warning_stages or unknown_token_findings) and not orders:
        orders.append(
            {
                **base,
                "order_id": "order_observation_source_quality_warning_rollup",
                "title": "Observation source-quality warning rollup",
                "priority": 3,
                "route": "source_quality_warning_rollup",
                "mapped_family": "observation_source_quality_audit",
                "threshold_family": "observation_source_quality_audit",
                "improvement_type": "observation_source_quality_warning_rollup",
                "intent": (
                    "Keep source-quality warning stages visible even when they are outside the immediate "
                    "implementation allowlist; follow-up Codex review decides whether a patch is needed."
                ),
                "evidence": evidence,
                "files_likely_touched": [
                    "src/engine/observation_source_quality_audit.py",
                    "src/engine/build_code_improvement_workorder.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_observation_source_quality_audit.py src/tests/test_build_code_improvement_workorder.py",
                ],
            }
        )
    return orders


def _raw_row_exclusion_with_manifest_details(raw_row_exclusion: dict[str, Any]) -> dict[str, Any]:
    if not raw_row_exclusion:
        return {}
    enriched = dict(raw_row_exclusion)
    if enriched.get("stage_counts") and enriched.get("exclusion_reasons"):
        return enriched
    manifest_path = Path(str(enriched.get("manifest_path") or ""))
    if not manifest_path.exists():
        return enriched
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return enriched
    if isinstance(manifest, dict):
        for key in (
            "stage_counts",
            "field_gap_counts",
            "exclusion_reasons",
            "first_timestamp",
            "last_timestamp",
            "sample_rows",
            "producer_hint",
        ):
            if not enriched.get(key) and manifest.get(key):
                enriched[key] = manifest.get(key)
        if not enriched.get("stage_counts") or not enriched.get("exclusion_reasons"):
            fallback = _summarize_legacy_raw_row_exclusion_manifest(manifest)
            for key, value in fallback.items():
                if not enriched.get(key) and value:
                    enriched[key] = value
    return enriched


def _float_or_none(value: Any) -> float | None:
    try:
        text = str(value).strip()
        if not text:
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def _manifest_excluded_rows(raw_row_exclusion: dict[str, Any]) -> list[dict[str, Any]]:
    manifest_path = Path(str(raw_row_exclusion.get("manifest_path") or ""))
    if not manifest_path.exists():
        return []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    rows = manifest.get("excluded_rows") if isinstance(manifest, dict) else []
    return [row for row in rows if isinstance(row, dict)]


def _raw_row_exclusion_limit_up_locked_context(raw_row_exclusion: dict[str, Any]) -> dict[str, Any] | None:
    excluded_row_count = int(raw_row_exclusion.get("excluded_row_count") or 0)
    if excluded_row_count <= 0:
        return None
    stage_counts = (
        raw_row_exclusion.get("stage_counts")
        if isinstance(raw_row_exclusion.get("stage_counts"), dict)
        else {}
    )
    relevant_stage_count = sum(
        int(stage_counts.get(stage) or 0)
        for stage in ("blocked_overbought", "blocked_strength_momentum")
    )
    if relevant_stage_count <= 0 or relevant_stage_count < max(1, int(excluded_row_count * 0.8)):
        return None
    field_gap_counts = (
        raw_row_exclusion.get("field_gap_counts")
        if isinstance(raw_row_exclusion.get("field_gap_counts"), dict)
        else {}
    )
    zero_range_count = int(field_gap_counts.get("zero_fields:intraday_range_pct") or 0)
    if zero_range_count < max(1, int(excluded_row_count * 0.8)):
        return None
    exclusion_reasons = (
        raw_row_exclusion.get("exclusion_reasons")
        if isinstance(raw_row_exclusion.get("exclusion_reasons"), dict)
        else {}
    )
    if not exclusion_reasons.get("source_quality_blocker"):
        return None
    if not (exclusion_reasons.get("not_evaluated_context") or exclusion_reasons.get("insufficient_history")):
        return None

    rows = _manifest_excluded_rows(raw_row_exclusion)
    if not rows:
        return None
    identity_counts: dict[str, int] = {}
    limit_up_rows = 0
    zero_range_rows = 0
    stages_seen: set[str] = set()
    stock_codes_seen: set[str] = set()
    for item in rows:
        payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
        fields = payload.get("fields") if isinstance(payload.get("fields"), dict) else {}
        stage = str(payload.get("stage") or "")
        stages_seen.add(stage)
        stock_code = str(payload.get("stock_code") or "")
        if stock_code:
            stock_codes_seen.add(stock_code)
        identity = f"{stock_code}:{payload.get('record_id') or ''}"
        identity_counts[identity] = identity_counts.get(identity, 0) + 1
        fluctuation = _float_or_none(fields.get("fluctuation"))
        if fluctuation is not None and fluctuation >= 29.0:
            limit_up_rows += 1
        intraday_range = _float_or_none(fields.get("intraday_range_pct"))
        if intraday_range is not None and abs(intraday_range) < 1e-9:
            zero_range_rows += 1

    top_identity, top_identity_count = ("", 0)
    if identity_counts:
        top_identity, top_identity_count = max(identity_counts.items(), key=lambda item: item[1])
    if limit_up_rows <= 0:
        return None
    if top_identity_count < max(1, int(len(rows) * 0.5)):
        return None
    if zero_range_rows < max(1, int(len(rows) * 0.5)):
        return None
    return {
        "classification": "limit_up_locked_context",
        "excluded_row_count": excluded_row_count,
        "relevant_stage_count": relevant_stage_count,
        "zero_intraday_range_count": zero_range_count,
        "manifest_row_count": len(rows),
        "manifest_limit_up_row_count": limit_up_rows,
        "manifest_zero_range_row_count": zero_range_rows,
        "top_identity": top_identity,
        "top_identity_count": top_identity_count,
        "stock_codes_sample": sorted(stock_codes_seen)[:8],
        "stages_seen": sorted(stages_seen),
        "required_followup": (
            "review_only_until_non_limit_up_zero_range_repeats_or_high_low_candle_source_loss_is_proven"
        ),
    }


def _raw_row_exclusion_market_halt_context(raw_row_exclusion: dict[str, Any]) -> dict[str, Any] | None:
    if raw_row_exclusion.get("market_halt_or_circuit_window_overlap") is not True:
        return None
    excluded_row_count = int(raw_row_exclusion.get("excluded_row_count") or 0)
    if excluded_row_count <= 0:
        return None
    field_gap_counts = (
        raw_row_exclusion.get("field_gap_counts")
        if isinstance(raw_row_exclusion.get("field_gap_counts"), dict)
        else {}
    )
    zero_range_count = int(field_gap_counts.get("zero_fields:intraday_range_pct") or 0)
    if zero_range_count < max(1, int(excluded_row_count * 0.8)):
        return None
    context = (
        raw_row_exclusion.get("market_halt_or_circuit_context")
        if isinstance(raw_row_exclusion.get("market_halt_or_circuit_context"), dict)
        else {}
    )
    overlap_count = int(context.get("overlap_excluded_row_count") or 0)
    if overlap_count < max(1, int(excluded_row_count * 0.8)):
        return None
    return {
        **context,
        "classification": "market_halt_or_circuit_window_overlap",
        "excluded_row_count": excluded_row_count,
        "zero_intraday_range_count": zero_range_count,
        "required_followup": (
            "review_only_until_zero_range_repeats_after_normal_market_flow_resumes"
        ),
    }


def _summarize_legacy_raw_row_exclusion_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    rows = manifest.get("excluded_rows") if isinstance(manifest.get("excluded_rows"), list) else []
    stage_counts: dict[str, int] = {}
    reason_counts: dict[str, int] = {}
    producer_hint: dict[str, dict[str, Any]] = {}
    timestamps: list[str] = []
    sample_rows: list[dict[str, Any]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
        fields = payload.get("fields") if isinstance(payload.get("fields"), dict) else {}
        stage = str(payload.get("stage") or "-")
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
        if payload.get("emitted_at"):
            timestamps.append(str(payload.get("emitted_at")))
        reasons: set[str] = set()
        for key, value in fields.items():
            text = json.dumps(value, ensure_ascii=False, sort_keys=True).lower() if isinstance(value, (dict, list)) else str(value).lower()
            if "source_quality_block" in text or str(key).lower() == "source_quality_blocker":
                reasons.add("source_quality_blocker")
            if "not_evaluated" in text:
                reasons.add("not_evaluated_context")
            if "insufficient_history" in text or "insufficient_sample" in text:
                reasons.add("insufficient_history")
            if "unknown" in text:
                reasons.add("unknown_token")
        if not reasons:
            reasons.add("row_contract_gap")
        for reason in reasons:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        hint = producer_hint.setdefault(
            stage,
            {
                "stage": stage,
                "pipeline": payload.get("pipeline"),
                "subsystem": "runtime_instrumentation_producer",
                "count": 0,
                "top_reasons": [],
            },
        )
        hint["count"] += 1
        if len(sample_rows) < 10:
            sample_rows.append(
                {
                    "line_no": item.get("line_no"),
                    "stage": stage,
                    "emitted_at": payload.get("emitted_at"),
                    "record_id": payload.get("record_id"),
                    "stock_code": payload.get("stock_code"),
                    "reasons": sorted(reasons),
                    "gap_fields": {},
                    "source_quality_route": fields.get("source_quality_route"),
                    "source_quality_blocker": fields.get("source_quality_blocker"),
                    "threshold_family": fields.get("threshold_family"),
                }
            )
    for hint in producer_hint.values():
        hint["top_reasons"] = sorted(reason_counts, key=lambda key: (-reason_counts[key], key))[:5]
    return {
        "stage_counts": dict(sorted(stage_counts.items())),
        "field_gap_counts": {},
        "exclusion_reasons": dict(sorted(reason_counts.items())),
        "first_timestamp": min(timestamps) if timestamps else None,
        "last_timestamp": max(timestamps) if timestamps else None,
        "sample_rows": sample_rows,
        "producer_hint": sorted(producer_hint.values(), key=lambda item: (-int(item.get("count") or 0), str(item.get("stage") or ""))),
    }


def _codebase_performance_followup_orders(report: dict[str, Any]) -> list[dict[str, Any]]:
    if not report:
        return []
    result: list[dict[str, Any]] = []
    for state, section in (
        ("accepted", "accepted_candidates"),
        ("deferred", "deferred_candidates"),
        ("rejected", "rejected_candidates"),
    ):
        candidates = report.get(section) if isinstance(report.get(section), list) else []
        for item in candidates:
            if not isinstance(item, dict):
                continue
            order_id = str(item.get("order_id") or item.get("item_id") or "").strip()
            if not order_id:
                continue
            result.append(
                {
                    "order_id": order_id,
                    "title": item.get("title"),
                    "source_report_type": "codebase_performance_workorder",
                    "lifecycle_stage": item.get("lifecycle_stage") or "ops_performance",
                    "target_subsystem": item.get("target_subsystem"),
                    "route": item.get("route") or "performance_optimization_order",
                    "confidence": item.get("confidence") or "consensus",
                    "priority": item.get("priority"),
                    "runtime_effect": False,
                    "strategy_effect": False,
                    "data_quality_effect": False,
                    "tuning_axis_effect": False,
                    "performance_candidate_state": state,
                    "risk_tier": item.get("risk_tier"),
                    "forbidden_uses": item.get("forbidden_uses") or [],
                    "implementation_status": item.get("implementation_status"),
                    "implementation_checks": item.get("implementation_checks") or [],
                    "implementation_provenance": item.get("implementation_provenance"),
                    "evidence": [
                        f"source_doc_hash={report.get('source_doc_hash')}",
                        f"candidate_state={state}",
                        f"implementation_status={item.get('implementation_status') or 'unknown'}",
                        f"risk_tier={item.get('risk_tier')}",
                        "runtime_effect=false",
                        "strategy_effect=false",
                        "data_quality_effect=false",
                        "tuning_axis_effect=false",
                        f"parity_contract={item.get('parity_contract')}",
                    ],
                    "intent": "Create a user-instructed, parity-tested code performance improvement without changing trading logic.",
                    "expected_ev_effect": "none_direct_ops_cpu_io_reduction_only",
                    "next_postclose_metric": "same report/output parity with lower runtime or CPU/IO overhead",
                    "files_likely_touched": item.get("files_likely_touched") or [],
                    "acceptance_tests": item.get("acceptance_tests") or [],
                    "parity_contract": item.get("parity_contract"),
                    "defer_reason": item.get("defer_reason"),
                }
            )
    return result


def _buy_funnel_sentinel_followup_orders(
    report: dict[str, Any],
    *,
    lifecycle_report: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if not report:
        return []
    classification = report.get("classification") if isinstance(report.get("classification"), dict) else {}
    matches = classification.get("matches") if isinstance(classification.get("matches"), list) else []
    if classification.get("primary") != "SUBMIT_DROUGHT_CRITICAL" and "SUBMIT_DROUGHT_CRITICAL" not in matches:
        return []
    session = (
        ((report.get("current") or {}).get("session") or {})
        if isinstance(report.get("current"), dict)
        else {}
    )
    ratios = session.get("ratios") if isinstance(session.get("ratios"), dict) else {}
    unique = session.get("stage_unique") if isinstance(session.get("stage_unique"), dict) else {}
    blockers = session.get("blocker_top") if isinstance(session.get("blocker_top"), list) else []
    upstream = session.get("upstream_blocker_top") if isinstance(session.get("upstream_blocker_top"), list) else []
    latency = session.get("latency_blocker_top") if isinstance(session.get("latency_blocker_top"), list) else []
    contract = (
        report.get("entry_submit_drought_contract")
        if isinstance(report.get("entry_submit_drought_contract"), dict)
        else {}
    )
    implementation_marker = _entry_submit_drought_implementation_marker(contract)
    weak_contract_matches = (
        contract.get("weak_contract_matches") if isinstance(contract.get("weak_contract_matches"), list) else []
    )
    evidence = [
        f"ai_confirmed_unique={_safe_int(unique.get('ai_confirmed'), 0)}",
        f"budget_pass_unique={_safe_int(unique.get('budget_pass'), 0)}",
        f"latency_pass_unique={_safe_int(unique.get('latency_pass'), 0)}",
        f"submitted_unique={_safe_int(unique.get('order_bundle_submitted'), 0)}",
        f"submitted_to_ai_pct={ratios.get('submitted_to_ai_unique_pct')}",
        f"submitted_to_budget_pct={ratios.get('submitted_to_budget_unique_pct')}",
    ]
    for label, items in (("blocker", blockers), ("upstream", upstream), ("latency", latency)):
        for item in items[:3]:
            if isinstance(item, dict):
                evidence.append(f"{label}:{item.get('label')}={item.get('count')}")
    orders = [
        {
            "order_id": "order_entry_submit_drought_auto_resolution",
            "title": "Entry submit drought automatic resolution handoff",
            "source_report_type": "buy_funnel_sentinel",
            "target_subsystem": "runtime_instrumentation",
            "lifecycle_stage": "entry_submit",
            "route": "instrumentation_order",
            "mapped_family": "lifecycle_decision_matrix_runtime",
            "threshold_family": "lifecycle_decision_matrix_runtime",
            "priority": 0,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            **implementation_marker,
            "strategy_effect": "entry_submit_drought_handoff",
            "data_quality_effect": "funnel_root_cause_split_required",
            "tuning_axis_effect": "auto_surface_to_ldm_and_workorder",
            "expected_ev_effect": "restore submitted coverage before evaluating EV edge",
            "intent": (
                "When submitted/ai is below the critical threshold, automatically create a Codex workorder/LDM "
                "handoff so upstream gate, budget pass, latency/pre-submit, and broker receipt blockers are fixed "
                "or routed without operator approval."
            ),
            "evidence": evidence,
            "required_downstream": (
                contract.get("required_downstream")
                if contract
                else [
                    "code_improvement_workorder",
                    "lifecycle_decision_matrix.submit_bucket_attribution",
                    "threshold_cycle_ev_report",
                    "runtime_approval_summary",
                    "postclose_verifier",
                ]
            ),
            "weak_contract_matches": weak_contract_matches,
            "files_likely_touched": [
                "src/engine/buy_funnel_sentinel.py",
                "src/engine/build_code_improvement_workorder.py",
                "src/engine/lifecycle_decision_matrix.py",
                "src/engine/runtime_apply_bridge.py",
                "src/engine/threshold_cycle_ev_report.py",
            ],
            "acceptance_tests": [
                "PYTHONPATH=. .venv/bin/python -m pytest -q "
                "src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py "
                "src/tests/test_runtime_approval_summary.py",
            ],
            "next_postclose_metric": (
                "SUBMIT_DROUGHT_CRITICAL must produce a selected implement_now workorder and the next "
                "postclose LDM/runtime summary must show submit blocker attribution."
            ),
        }
    ]
    taxonomy_leakage_labels = [
        str(item.get("label") or "")
        for item in blockers
        if isinstance(item, dict) and str(item.get("label") or "").startswith("blocked_swing_")
    ]
    orders.extend(
        _entry_post_submit_weak_contract_orders(
            evidence=evidence,
            contract=contract,
            weak_contract_matches=weak_contract_matches,
            taxonomy_leakage_labels=taxonomy_leakage_labels,
            lifecycle_report=lifecycle_report,
        )
    )
    return orders


def _closed_instrumentation_order_families(ev_report: dict[str, Any], *, target_date: str) -> dict[str, str]:
    outcome = ev_report.get("calibration_outcome") if isinstance(ev_report.get("calibration_outcome"), dict) else {}
    decisions = outcome.get("decisions") if isinstance(outcome.get("decisions"), list) else []
    closed: dict[str, str] = {}
    for item in decisions:
        if not isinstance(item, dict):
            continue
        family = str(item.get("family") or "").strip()
        source_metrics = item.get("source_metrics") if isinstance(item.get("source_metrics"), dict) else {}
        if source_metrics.get("instrumentation_status") != "implemented":
            continue
        if family == "dynamic_entry_price_resolver":
            closed["order_latency_guard_miss_ev_recovery"] = family
        elif family == "pre_submit_price_guard":
            closed["order_pre_submit_price_guard_safety_audit"] = family
        elif family == "holding_exit_decision_matrix_advisory":
            closed["order_holding_exit_decision_matrix_edge_counterfactual"] = family
    if _holding_exit_counterfactual_contract_status(target_date).get("implemented") is True:
        closed["order_holding_exit_decision_matrix_edge_counterfactual"] = (
            "holding_exit_decision_matrix_advisory"
        )
    return closed


def _dynamic_entry_price_report_contract_orders(ev_report: dict[str, Any]) -> list[dict[str, Any]]:
    outcome = ev_report.get("calibration_outcome") if isinstance(ev_report.get("calibration_outcome"), dict) else {}
    decisions = outcome.get("decisions") if isinstance(outcome.get("decisions"), list) else []
    dynamic = next(
        (
            item
            for item in decisions
            if isinstance(item, dict) and str(item.get("family") or "") == "dynamic_entry_price_resolver"
        ),
        {},
    )
    source_metrics = dynamic.get("source_metrics") if isinstance(dynamic.get("source_metrics"), dict) else {}
    if not source_metrics:
        return []
    orders: list[dict[str, Any]] = []
    contract_status = str(
        source_metrics.get("report_contract_status")
        or source_metrics.get("dynamic_entry_price_report_contract_status")
        or ""
    ).strip().lower()

    def _truthy_contract_gap(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes", "y", "gap", "contract_gap", "report_contract_gap"}
        return False

    explicit_contract_gap = any(
        _truthy_contract_gap(source_metrics.get(key))
        for key in (
            "report_contract_gap",
            "contract_gap",
            "candidate_quality_contract_gap",
            "sim_submit_path_contract_gap",
        )
    ) or contract_status in {
        "missing",
        "incomplete",
        "failed",
        "fail",
        "contract_gap",
        "report_contract_gap",
    }
    if not explicit_contract_gap:
        return []
    candidate_quality = (
        source_metrics.get("candidate_quality") if isinstance(source_metrics.get("candidate_quality"), dict) else {}
    )
    ai_quality = (
        candidate_quality.get("AI_candidate") if isinstance(candidate_quality.get("AI_candidate"), dict) else {}
    )
    failure_count = _safe_int(ai_quality.get("candidate_failure_count"), 0)
    if failure_count > 0:
        orders.append(
            {
                "order_id": "order_dynamic_entry_price_ai_candidate_failure_contract",
                "title": "dynamic entry price AI_candidate failure contract",
                "source_report_type": "threshold_cycle_ev",
                "lifecycle_stage": "entry",
                "target_subsystem": "daily_threshold_cycle_report",
                "route": "source_quality_gap",
                "mapped_family": "dynamic_entry_price_resolver",
                "threshold_family": "dynamic_entry_price_resolver",
                "improvement_type": "report_contract_gap",
                "confidence": "postclose_threshold_ev_source",
                "priority": 2,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "expected_ev_effect": "Keep AI_candidate missing_snapshot/invalid_price out of priced candidate EV while preserving failure provenance.",
                "evidence": [
                    f"candidate_failure_count={failure_count}",
                    f"candidate_failure_rate={ai_quality.get('candidate_failure_rate')}",
                    f"failure_reasons={json.dumps(ai_quality.get('failure_reasons') or {}, ensure_ascii=False, sort_keys=True)}",
                    "forbidden_uses=runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
                ],
                "next_postclose_metric": "AI_candidate candidate_failure_count should be explicit and priced EV should use priced candidate samples only.",
                "files_likely_touched": [
                    "src/engine/daily_threshold_cycle_report.py",
                    "src/tests/test_daily_threshold_cycle_report.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_daily_threshold_cycle_report.py src/tests/test_build_code_improvement_workorder.py",
                ],
            }
        )
    unpriced_count = _safe_int(source_metrics.get("unpriced_or_stale_warning_count"), 0)
    if unpriced_count > 0:
        orders.append(
            {
                "order_id": "order_dynamic_entry_price_sim_unpriced_stale_contract",
                "title": "dynamic entry price sim unpriced stale contract",
                "source_report_type": "threshold_cycle_ev",
                "lifecycle_stage": "submit",
                "target_subsystem": "daily_threshold_cycle_report",
                "route": "source_quality_gap",
                "mapped_family": "dynamic_entry_price_resolver",
                "threshold_family": "dynamic_entry_price_resolver",
                "improvement_type": "report_contract_gap",
                "confidence": "postclose_threshold_ev_source",
                "priority": 2,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "expected_ev_effect": "Prevent sim stale/unpriced warning rows from becoming fill/EV denominator evidence.",
                "evidence": [
                    f"unpriced_or_stale_warning_count={unpriced_count}",
                    f"sim_submit_path_quality={json.dumps(source_metrics.get('sim_submit_path_quality') or {}, ensure_ascii=False, sort_keys=True)[:1200]}",
                    "actual_order_submitted=false",
                    "broker_order_forbidden=true",
                ],
                "next_postclose_metric": "sim unpriced/stale rows should remain preserved as provenance and excluded_from_fill_ev_count.",
                "files_likely_touched": [
                    "src/engine/daily_threshold_cycle_report.py",
                    "src/tests/test_daily_threshold_cycle_report.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_daily_threshold_cycle_report.py src/tests/test_build_code_improvement_workorder.py",
                ],
            }
        )
    return orders


def _calibration_report_from_ev(ev_report: dict[str, Any]) -> dict[str, Any]:
    sources = ev_report.get("sources") if isinstance(ev_report.get("sources"), dict) else {}
    path_text = sources.get("calibration")
    if not path_text:
        return {}
    return _load_json(Path(str(path_text)))


def _calibration_report_path_from_ev(ev_report: dict[str, Any]) -> Path | None:
    sources = ev_report.get("sources") if isinstance(ev_report.get("sources"), dict) else {}
    path_text = sources.get("calibration")
    return Path(str(path_text)) if path_text else None


def _window_policy_audit_followup_orders(calibration_report: dict[str, Any]) -> list[dict[str, Any]]:
    audit = (
        calibration_report.get("window_policy_audit")
        if isinstance(calibration_report.get("window_policy_audit"), dict)
        else {}
    )
    issue_counts = audit.get("issue_counts") if isinstance(audit.get("issue_counts"), dict) else {}
    if not issue_counts:
        return []
    items = [item for item in audit.get("items") or [] if isinstance(item, dict) and item.get("issues")]
    if not items:
        return []
    affected = [str(item.get("family") or "") for item in items if item.get("family")]
    evidence = [
        f"issue_counts={json.dumps(issue_counts, ensure_ascii=False, sort_keys=True)}",
        "affected_families=" + ",".join(affected),
    ]
    for item in items[:8]:
        evidence.append(
            "family={family} primary={primary} state={state} primary_sample={sample} "
            "snapshot_sample={snapshot} source_sample={source} issues={issues}".format(
                family=item.get("family"),
                primary=item.get("primary"),
                state=item.get("candidate_state"),
                sample=item.get("primary_sample_count"),
                snapshot=item.get("primary_snapshot_sample_count"),
                source=item.get("primary_source_sample_count"),
                issues=",".join(str(value) for value in item.get("issues") or []),
            )
        )
    return [
        {
            "order_id": "order_threshold_window_policy_source_snapshot_alignment",
            "title": "threshold window policy source snapshot alignment",
            "source_report_type": "threshold_cycle_calibration",
            "lifecycle_stage": "threshold_cycle",
            "target_subsystem": "threshold_cycle_report",
            "route": "instrumentation_order",
            "mapped_family": None,
            "threshold_family": "window_policy_registry",
            "improvement_type": "source_quality_alignment",
            "confidence": "consensus",
            "priority": 3,
            "runtime_effect": False,
            "expected_ev_effect": (
                "Prevent daily-only or snapshot-only calibration blind spots by aligning rolling/cumulative "
                "source metrics, snapshot denominators, AI correction context, and EV/workorder rendering."
            ),
            "evidence": evidence,
            "next_postclose_metric": (
                "window_policy_audit should have no daily_only_leak or rolling_consumer_gap; "
                "rolling_source_snapshot_mismatch must be explained as rendering-only or eliminated."
            ),
            "files_likely_touched": [
                "src/engine/daily_threshold_cycle_report.py",
                "src/engine/threshold_cycle_ev_report.py",
                "src/engine/build_code_improvement_workorder.py",
                "data/threshold_cycle/README.md",
            ],
            "acceptance_tests": [
                "PYTHONPATH=. .venv/bin/pytest src/tests/test_daily_threshold_cycle_report.py src/tests/test_build_code_improvement_workorder.py",
                "threshold_cycle_YYYY-MM-DD.json includes window_policy_audit and calibration_source_bundle_by_window lineage",
            ],
        }
    ]


def _panic_lifecycle_followup_orders(calibration_report: dict[str, Any]) -> list[dict[str, Any]]:
    bundle = (
        calibration_report.get("calibration_source_bundle")
        if isinstance(calibration_report.get("calibration_source_bundle"), dict)
        else {}
    )
    source_metrics = bundle.get("source_metrics") if isinstance(bundle.get("source_metrics"), dict) else {}
    orders: list[dict[str, Any]] = []

    panic_sell = source_metrics.get("panic_sell_defense") if isinstance(source_metrics.get("panic_sell_defense"), dict) else {}
    panic_sell_candidates = panic_sell.get("candidate_status") if isinstance(panic_sell.get("candidate_status"), dict) else {}
    panic_sell_source_quality_blockers = (
        panic_sell.get("source_quality_blockers")
        if isinstance(panic_sell.get("source_quality_blockers"), list)
        else []
    )
    panic_sell_triggered = bool(panic_sell_candidates) or str(panic_sell.get("panic_state") or "") in {
        "PANIC_SELL",
        "RECOVERY_WATCH",
    }
    panic_sell_triggered = panic_sell_triggered or (_safe_int(panic_sell.get("active_sim_probe_positions"), 0) > 0)
    panic_sell_triggered = panic_sell_triggered or bool(panic_sell.get("market_breadth_followup_candidate"))
    panic_sell_triggered = panic_sell_triggered or bool(panic_sell_source_quality_blockers)
    if panic_sell_triggered:
        panic_sell_implementation_status = (
            "implemented_but_waiting_sample"
            if not panic_sell_source_quality_blockers
            else "implemented_source_quality_contract_waiting_sample"
        )
        orders.append(
            {
                "order_id": "order_panic_sell_defense_lifecycle_transition_pack",
                "title": "panic sell defense lifecycle transition pack",
                "source_report_type": "threshold_cycle_calibration_source_bundle",
                "lifecycle_stage": "holding_exit",
                "target_subsystem": "panic_sell_defense",
                "route": "auto_family_candidate",
                "mapped_family": None,
                "threshold_family": "panic_sell_defense",
                "improvement_type": "runtime_transition_design",
                "confidence": "consensus",
                "priority": 6,
                "runtime_effect": False,
                "implementation_status": panic_sell_implementation_status,
                "implementation_checks": [
                    "panic_sell_defense source metrics are present in calibration_source_bundle",
                    "panic_regime_mode and candidate_status are exposed as report-only provenance",
                    "runtime_effect=false",
                    "allowed_runtime_apply=false",
                ],
                "implementation_provenance": {
                    "implementation_type": "panic_lifecycle_report_only_source_bundle",
                    "source_report_type": "threshold_cycle_calibration_source_bundle",
                    "source_metric_key": "panic_sell_defense",
                    "panic_state": panic_sell.get("panic_state"),
                    "panic_regime_mode": panic_sell.get("panic_regime_mode"),
                    "source_quality_blockers": panic_sell_source_quality_blockers,
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "decision_authority": "report_only_source_bundle",
                },
                "expected_ev_effect": (
                    "Use panic-sell simulation and post-sell rebound evidence to propose threshold/guard changes, "
                    "then request explicit live-runtime approval without mutating exits automatically."
                ),
                "evidence": [
                    f"panic_state={panic_sell.get('panic_state')}",
                    f"panic_regime_mode={panic_sell.get('panic_regime_mode')}",
                    f"stop_loss_exit_count={panic_sell.get('stop_loss_exit_count')}",
                    f"confirmation_eligible_exit_count={panic_sell.get('confirmation_eligible_exit_count')}",
                    f"active_sim_probe_positions={panic_sell.get('active_sim_probe_positions')}",
                    f"post_sell_rebound_above_sell_10_20m_pct={panic_sell.get('post_sell_rebound_above_sell_10_20m_pct')}",
                    f"microstructure_market_risk_state={panic_sell.get('microstructure_market_risk_state')}",
                    f"microstructure_confirmed_risk_off_advisory={panic_sell.get('microstructure_confirmed_risk_off_advisory')}",
                    f"microstructure_portfolio_local_risk_off_only={panic_sell.get('microstructure_portfolio_local_risk_off_only')}",
                    f"market_breadth_followup_candidate={panic_sell.get('market_breadth_followup_candidate')}",
                    f"source_quality_blockers={panic_sell_source_quality_blockers}",
                    f"candidate_status={panic_sell_candidates}",
                    "allowed_runtime_apply=false",
                ],
                "next_postclose_metric": (
                    "panic_sell_defense should expose simulation EV, rollback guard, approval artifact status, "
                    "market/breadth confirmation, and candidate-specific threshold recommendations before any runtime transition."
                ),
                "files_likely_touched": [
                    "src/engine/panic_sell_defense_report.py",
                    "src/engine/daily_threshold_cycle_report.py",
                    "src/engine/runtime_approval_summary.py",
                    "docs/plan-korStockScanPerformanceOptimization.rebase.md",
                ],
                "acceptance_tests": [
                    "pytest panic sell defense/report lifecycle tests",
                    "pytest src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py",
                ],
            }
        )

    panic_buy = source_metrics.get("panic_buying") if isinstance(source_metrics.get("panic_buying"), dict) else {}
    panic_buy_candidates = panic_buy.get("candidate_status") if isinstance(panic_buy.get("candidate_status"), dict) else {}
    panic_buy_source_quality_blockers = (
        panic_buy.get("source_quality_blockers")
        if isinstance(panic_buy.get("source_quality_blockers"), list)
        else []
    )
    panic_buy_gate_state = str(panic_buy.get("risk_regime_gate_state") or "normal")
    panic_buy_confirmed_evidence_count = _safe_int(panic_buy.get("confirmed_evidence_count"), 0)
    panic_buy_report_candidate = any(
        str(status) == "report_only_candidate" for status in panic_buy_candidates.values()
    )
    panic_buy_triggered = panic_buy_report_candidate
    panic_buy_triggered = panic_buy_triggered or panic_buy_gate_state not in {"", "normal", "None"}
    panic_buy_triggered = panic_buy_triggered or panic_buy_confirmed_evidence_count > 0
    panic_buy_triggered = panic_buy_triggered or (_safe_int(panic_buy.get("tp_like_exit_count"), 0) > 0)
    panic_buy_triggered = panic_buy_triggered or (_safe_int(panic_buy.get("trailing_winner_count"), 0) > 0)
    panic_buy_triggered = panic_buy_triggered or bool(panic_buy_source_quality_blockers)
    if panic_buy_triggered:
        source_quality_only = bool(panic_buy_source_quality_blockers) or panic_buy_gate_state == "source_quality_blocked"
        panic_buy_implementation_status = (
            "implemented_source_quality_contract_waiting_sample"
            if source_quality_only
            else "implemented_but_waiting_sample"
        )
        orders.append(
            {
                "order_id": (
                    "order_panic_buying_source_quality_market_breadth_micro_coverage"
                    if source_quality_only
                    else "order_panic_buy_runner_tp_canary_lifecycle_pack"
                ),
                "title": (
                    "panic buying source-quality market breadth and micro coverage"
                    if source_quality_only
                    else "panic buy runner TP canary lifecycle pack"
                ),
                "source_report_type": "threshold_cycle_calibration_source_bundle",
                "lifecycle_stage": "source_quality" if source_quality_only else "holding_exit",
                "target_subsystem": "panic_buying",
                "route": "source_quality_blocker" if source_quality_only else "auto_family_candidate",
                "mapped_family": None,
                "threshold_family": None if source_quality_only else "panic_buy_runner_tp_canary",
                "improvement_type": "source_quality_instrumentation" if source_quality_only else "runtime_transition_design",
                "confidence": "consensus",
                "priority": 7,
                "runtime_effect": False,
                "implementation_status": panic_buy_implementation_status,
                "implementation_checks": [
                    "panic_buying source metrics are present in calibration_source_bundle",
                    "panic_buy_regime_mode and source_quality_blockers are exposed as report-only provenance",
                    "runtime_effect=false",
                    "allowed_runtime_apply=false",
                ],
                "implementation_provenance": {
                    "implementation_type": "panic_lifecycle_report_only_source_bundle",
                    "source_report_type": "threshold_cycle_calibration_source_bundle",
                    "source_metric_key": "panic_buying",
                    "panic_buy_state": panic_buy.get("panic_buy_state"),
                    "panic_buy_regime_mode": panic_buy.get("panic_buy_regime_mode"),
                    "source_quality_blockers": panic_buy_source_quality_blockers,
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "decision_authority": "report_only_source_bundle",
                },
                "expected_ev_effect": (
                    "Route market breadth and micro coverage gaps as source-quality blockers before any panic-buying runtime candidate."
                    if source_quality_only
                    else (
                        "Use panic-buying TP counterfactuals to reduce missed upside versus full fixed-TP exits, "
                        "while keeping hard/protect/emergency stops and order provenance guards dominant."
                    )
                ),
                "evidence": [
                    f"panic_buy_state={panic_buy.get('panic_buy_state')}",
                    f"panic_buy_regime_mode={panic_buy.get('panic_buy_regime_mode')}",
                    f"risk_regime_gate_state={panic_buy.get('risk_regime_gate_state')}",
                    f"risk_regime_threshold_mode={panic_buy.get('risk_regime_threshold_mode')}",
                    f"confirmed_evidence_count={panic_buy.get('confirmed_evidence_count')}",
                    f"panic_buy_active_count={panic_buy.get('panic_buy_active_count')}",
                    f"exhaustion_confirmed_count={panic_buy.get('exhaustion_confirmed_count')}",
                    f"tp_counterfactual_count={panic_buy.get('tp_counterfactual_count')}",
                    f"tp_like_exit_count={panic_buy.get('tp_like_exit_count')}",
                    f"trailing_winner_count={panic_buy.get('trailing_winner_count')}",
                    f"market_wide_panic_buy_confirmed={panic_buy.get('market_wide_panic_buy_confirmed')}",
                    f"market_breadth_risk_on_advisory={panic_buy.get('market_breadth_risk_on_advisory')}",
                    f"missing_orderbook_count={panic_buy.get('missing_orderbook_count')}",
                    f"missing_trade_aggressor_count={panic_buy.get('missing_trade_aggressor_count')}",
                    f"source_quality_blockers={panic_buy_source_quality_blockers}",
                    f"candidate_status={panic_buy_candidates}",
                    "allowed_runtime_apply=false",
                ],
                "next_postclose_metric": (
                    "panic_buying source-quality blockers must be resolved or explicitly carried before runner TP approval is reviewed."
                    if source_quality_only
                    else (
                        "panic_buying should expose runner-vs-full-TP EV, MAE/giveback/sell-failure rollback guards, "
                        "approval artifact status, panic_buy_regime_mode owner split, and no live TP mutation before approval."
                    )
                ),
                "files_likely_touched": [
                    "src/engine/panic_buying_report.py",
                    "src/engine/daily_threshold_cycle_report.py",
                    "src/engine/runtime_approval_summary.py",
                    "docs/plan-korStockScanPerformanceOptimization.rebase.md",
                    "docs/code-improvement-workorders/panic_buying_regime_mode_v2_2026-05-14.md",
                ],
                "acceptance_tests": [
                    "pytest src/tests/test_panic_buying_report.py",
                    "pytest src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py",
                ],
            }
        )

    return orders


def _swing_strategy_discovery_followup_orders(report: dict[str, Any]) -> list[dict[str, Any]]:
    if not report:
        return []
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    source_quality = (
        report.get("source_quality_summary") if isinstance(report.get("source_quality_summary"), dict) else {}
    )
    warnings = [str(item) for item in (report.get("warnings") or []) if str(item).strip()]
    avoid_count = _safe_int(summary.get("avoid_bucket_count"), 0)
    avoid_buckets = report.get("avoid_buckets") if isinstance(report.get("avoid_buckets"), list) else []
    avoid_contract_implemented = bool(avoid_buckets) and all(
        isinstance(item, dict)
        and "axis" in item
        and "sample_count" in item
        and "source_quality_adjusted_ev_pct" in item
        and "downside_p10_pct" in item
        for item in avoid_buckets
    )
    pending = _safe_int(summary.get("pending_future_quote_count"), 0)
    labeled = _safe_int(summary.get("labeled_sample_count"), 0)
    implementation_status = (
        "implemented" if source_quality.get("implementation_status") == "implemented" else None
    )
    orders: list[dict[str, Any]] = []
    if warnings or pending:
        orders.append(
            {
                "order_id": "order_swing_strategy_discovery_source_quality_followup",
                "title": "swing strategy discovery label/source quality follow-up",
                "source_report_type": "swing_strategy_discovery_ev",
                "lifecycle_stage": "source_quality",
                "target_subsystem": "swing_strategy_discovery_sim",
                "route": "instrumentation_order",
                "mapped_family": None,
                "threshold_family": None,
                "improvement_type": "source_quality_instrumentation",
                "confidence": "consensus",
                "priority": 6,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "implementation_status": implementation_status,
                "implementation_checks": source_quality.get("implementation_checks") or [],
                "implementation_provenance": source_quality.get("implementation_provenance") or {},
                "expected_ev_effect": "Improve discovery label coverage and source attribution before any swing strategy policy promotion is discussed.",
                "evidence": [
                    f"labeled_sample_count={labeled}",
                    f"pending_future_quote_count={pending}",
                    f"warnings={warnings}",
                    f"maturity_status_counts={source_quality.get('maturity_status_counts') or {}}",
                    "decision_authority=swing_sim_exploration_only",
                    "allowed_runtime_apply=false",
                ],
                "next_postclose_metric": "swing_strategy_discovery_ev should reduce pending_future_quotes where matured and keep source-only authority.",
                "files_likely_touched": [
                    "src/engine/swing_strategy_discovery_label_builder.py",
                    "src/engine/swing_strategy_discovery_ev_report.py",
                    "src/engine/swing_sector_theme_source.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_strategy_discovery_label_builder.py src/tests/test_swing_strategy_discovery_ev_report.py src/tests/test_swing_sector_theme_source.py",
                ],
            }
        )
    if avoid_count > 0:
        orders.append(
            {
                "order_id": "order_swing_strategy_discovery_avoid_bucket_review",
                "title": "swing strategy discovery avoid bucket report enrichment",
                "source_report_type": "swing_strategy_discovery_ev",
                "lifecycle_stage": "selection",
                "target_subsystem": "swing_strategy_discovery_sim",
                "route": "instrumentation_order",
                "mapped_family": None,
                "threshold_family": None,
                "improvement_type": "analysis_report_provenance",
                "confidence": "consensus",
                "priority": 7,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "implementation_status": "implemented" if avoid_contract_implemented else None,
                "implementation_provenance": {
                    "avoid_bucket_contract_fields": [
                        "axis",
                        "sample_count",
                        "source_quality_adjusted_ev_pct",
                        "downside_p10_pct",
                    ],
                    "avoid_bucket_count": avoid_count,
                }
                if avoid_contract_implemented
                else None,
                "expected_ev_effect": "Expose avoid buckets as analysis guidance only; do not mutate swing runtime or recommendation_history.",
                "evidence": [
                    f"avoid_bucket_count={avoid_count}",
                    f"top_surviving_arm={summary.get('top_surviving_arm')}",
                    "runtime_effect=false",
                ],
                "next_postclose_metric": "avoid_buckets should include axis/key/sample/EV/downside with enough sample floor to guide later design.",
                "files_likely_touched": [
                    "src/engine/swing_strategy_discovery_ev_report.py",
                    "docs/swing-strategy-discovery-sim-v1.md",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_strategy_discovery_ev_report.py src/tests/test_build_code_improvement_workorder.py",
                ],
            }
        )
    return orders


def _swing_ldm_order_id(item: dict[str, Any]) -> str:
    stage = _slug(str(item.get("lifecycle_stage") or "swing"))
    bucket_type = _slug(str(item.get("bucket_type") or "bucket"))
    bucket_key = _slug(str(item.get("bucket_key") or item.get("workorder_id") or "unknown"))
    return f"order_swing_ldm_{stage}_{bucket_type}_{bucket_key}"


def _swing_lifecycle_matrix_followup_orders(report: dict[str, Any]) -> list[dict[str, Any]]:
    if not report:
        return []
    orders: list[dict[str, Any]] = []
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    raw_event_count = _safe_int(summary.get("raw_swing_event_count"), 0)
    consumed_event_count = _safe_int(summary.get("ldm_consumed_event_count"), 0)
    coverage_rate = _safe_float(summary.get("ldm_event_coverage_rate"), 0.0)
    if raw_event_count >= 1000 and coverage_rate < 0.01:
        orders.append(
            {
                "order_id": "order_swing_ldm_event_coverage_rollup",
                "title": "Swing LDM raw event coverage roll-up review",
                "source_report_type": "swing_lifecycle_decision_matrix",
                "lifecycle_stage": "entry",
                "target_subsystem": "swing_lifecycle_decision_matrix",
                "route": "instrumentation_order",
                "mapped_family": None,
                "threshold_family": None,
                "improvement_type": "swing_ldm_event_coverage_gap",
                "confidence": "postclose_ldm_source",
                "priority": 1,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "expected_ev_effect": "Prevent observed Swing SIM events from being silently excluded before bucket discovery.",
                "evidence": [
                    f"raw_swing_event_count={raw_event_count}",
                    f"ldm_consumed_event_count={consumed_event_count}",
                    f"ldm_event_coverage_rate={coverage_rate}",
                    f"unmapped_swing_stage_counts={summary.get('unmapped_swing_stage_counts') or {}}",
                    "decision_authority=swing_ldm_source_only",
                    "actual_order_submitted=false",
                ],
                "next_postclose_metric": "Swing LDM coverage should stay >=0.01 when raw_swing_event_count>=1000, or unmapped stages should have explicit roll-up evidence.",
                "files_likely_touched": [
                    "src/engine/swing_lifecycle_decision_matrix.py",
                    "src/engine/verify_threshold_cycle_postclose_chain.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py",
                ],
            }
        )
    for section_name in (
        "entry_bucket_attribution",
        "holding_exit_bucket_attribution",
        "scale_in_bucket_attribution",
        "discovery_arm_attribution",
    ):
        section = report.get(section_name) if isinstance(report.get(section_name), dict) else {}
        for item in section.get("code_improvement_workorders") or []:
            if not isinstance(item, dict):
                continue
            orders.append(
                {
                    "order_id": _swing_ldm_order_id(item),
                    "title": f"Swing LDM source field follow-up: {item.get('bucket_key')}",
                    "source_report_type": "swing_lifecycle_decision_matrix",
                    "lifecycle_stage": item.get("lifecycle_stage") or "source_quality",
                    "target_subsystem": item.get("target_subsystem") or "swing_lifecycle_decision_matrix",
                    "route": "instrumentation_order",
                    "mapped_family": None,
                    "threshold_family": None,
                    "improvement_type": "swing_ldm_bucket_instrumentation_gap",
                    "confidence": "postclose_ldm_source",
                    "priority": 2,
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "implementation_status": item.get("implementation_status"),
                    "implementation_provenance": item.get("implementation_provenance") or {},
                    "expected_ev_effect": "Close Swing LDM bucket source-quality gaps while preserving sim-only authority.",
                    "evidence": [
                        f"section={section_name}",
                        f"bucket_type={item.get('bucket_type')}",
                        f"bucket_key={item.get('bucket_key')}",
                        f"reason={item.get('reason')}",
                        f"implementation_status={item.get('implementation_status') or '-'}",
                        "decision_authority=swing_ldm_source_only",
                        "actual_order_submitted=false",
                    ],
                    "next_postclose_metric": "Swing LDM bucket should move from code_patch_required to source_only_keep_collecting or sim_auto_approved.",
                    "files_likely_touched": [
                        "src/engine/swing_lifecycle_decision_matrix.py",
                        "src/engine/swing_lifecycle_bucket_discovery.py",
                    ],
                    "acceptance_tests": [
                        "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py",
                    ],
                }
            )
    return orders


def _swing_lifecycle_bucket_discovery_followup_orders(report: dict[str, Any]) -> list[dict[str, Any]]:
    if not report:
        return []
    orders: list[dict[str, Any]] = []
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    surfaced_candidates = report.get("surfaced_candidates") if isinstance(report.get("surfaced_candidates"), list) else []
    contract_gap_ids: list[str] = []
    for candidate in surfaced_candidates:
        if not isinstance(candidate, dict):
            continue
        candidate_id = str(candidate.get("candidate_id") or "").strip()
        bucket_id = str(candidate.get("bucket_id") or "").strip()
        stage = str(candidate.get("stage") or candidate.get("lifecycle_stage") or "").strip()
        if not candidate_id or not bucket_id or not stage or stage.lower() == "unknown":
            contract_gap_ids.append(candidate_id or bucket_id or "unknown")
    if contract_gap_ids:
        orders.append(
            {
                "order_id": "order_swing_lifecycle_bucket_discovery_contract_rollup",
                "title": "Swing lifecycle bucket discovery candidate contract roll-up review",
                "source_report_type": "swing_lifecycle_bucket_discovery",
                "lifecycle_stage": "source_quality",
                "target_subsystem": "swing_lifecycle_bucket_discovery",
                "route": "instrumentation_order",
                "mapped_family": None,
                "threshold_family": None,
                "improvement_type": "swing_bucket_candidate_contract_gap",
                "confidence": "postclose_bucket_discovery_source",
                "priority": 1,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "expected_ev_effect": "Ensure Swing discovery candidates preserve candidate_id, bucket_id, stage, and lifecycle_stage through downstream consumers.",
                "evidence": [
                    f"contract_gap_candidate_ids={sorted(set(contract_gap_ids))[:20]}",
                    "decision_authority=swing_ldm_bucket_discovery_sim_auto",
                    "allowed_runtime_apply=false",
                ],
                "next_postclose_metric": "All surfaced Swing discovery candidates should expose candidate_id, bucket_id, stage, and lifecycle_stage.",
                "files_likely_touched": [
                    "src/engine/swing_lifecycle_bucket_discovery.py",
                    "src/engine/runtime_apply_gap_audit.py",
                    "src/engine/verify_threshold_cycle_postclose_chain.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_gap_audit.py src/tests/test_verify_threshold_cycle_postclose_chain.py",
                ],
            }
        )
    unreviewed_count = _safe_int(summary.get("sim_auto_unreviewed_candidate_count"), 0)
    downgraded_count = _safe_int(summary.get("sim_auto_downgraded_by_review_count"), 0)
    if unreviewed_count > 0 or downgraded_count > 0:
        ai_review_followup_reasons = summary.get("ai_review_followup_reasons") or []
        provider_unavailable_hold = (
            str(summary.get("ai_review_blocker_state") or "") == "provider_unavailable"
            and not bool(summary.get("ai_review_followup_required"))
            and not ai_review_followup_reasons
        )
        orders.append(
            {
                "order_id": "order_swing_lifecycle_bucket_discovery_ai_review_rollup",
                "title": "Swing lifecycle sim-auto AI review shard roll-up review",
                "source_report_type": "swing_lifecycle_bucket_discovery",
                "lifecycle_stage": "source_quality",
                "target_subsystem": "swing_lifecycle_bucket_discovery",
                "route": "ai_review_provider_unavailable_hold" if provider_unavailable_hold else "instrumentation_order",
                "mapped_family": "swing_lifecycle_bucket_discovery" if provider_unavailable_hold else None,
                "threshold_family": None,
                "improvement_type": "swing_bucket_ai_review_shard_gap",
                "confidence": "postclose_bucket_discovery_source",
                "priority": 1,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "expected_ev_effect": "Keep parsed sim-auto shard candidates usable while fail-closing only unreviewed or failed shard candidates.",
                "evidence": [
                    f"sim_auto_review_shard_count={_safe_int(summary.get('sim_auto_review_shard_count'), 0)}",
                    f"sim_auto_reviewed_candidate_count={_safe_int(summary.get('sim_auto_reviewed_candidate_count'), 0)}",
                    f"sim_auto_unreviewed_candidate_count={unreviewed_count}",
                    f"sim_auto_downgraded_by_review_count={downgraded_count}",
                    f"ai_review_blocker_state={summary.get('ai_review_blocker_state') or ''}",
                    f"ai_review_followup_required={bool(summary.get('ai_review_followup_required'))}",
                    f"ai_review_followup_reasons={ai_review_followup_reasons}",
                    "decision_authority=swing_ldm_bucket_discovery_sim_auto",
                    "allowed_runtime_apply=false",
                ],
                "implementation_status": "implemented_but_waiting_sample" if provider_unavailable_hold else None,
                "next_postclose_metric": "Partial AI review failures should create source-only downgrade evidence without hiding parsed shard candidates.",
                "files_likely_touched": [
                    "src/engine/swing_lifecycle_bucket_discovery.py",
                    "src/engine/build_code_improvement_workorder.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_build_code_improvement_workorder.py",
                ],
            }
        )
    for item in report.get("code_improvement_workorders") or []:
        if not isinstance(item, dict):
            continue
        bucket_id = str(item.get("bucket_id") or item.get("workorder_id") or "")
        orders.append(
            {
                "order_id": f"order_swing_lifecycle_bucket_discovery_{_slug(bucket_id)}",
                "title": f"Swing lifecycle bucket discovery handoff follow-up: {bucket_id}",
                "source_report_type": "swing_lifecycle_bucket_discovery",
                "lifecycle_stage": item.get("lifecycle_stage") or "source_quality",
                "target_subsystem": item.get("target_subsystem") or "swing_lifecycle_bucket_discovery",
                "route": "instrumentation_order",
                "mapped_family": None,
                "threshold_family": None,
                "improvement_type": "swing_bucket_handoff_or_contract_gap",
                "confidence": "postclose_bucket_discovery_source",
                "priority": 2,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "implementation_status": item.get("implementation_status"),
                "implementation_provenance": item.get("implementation_provenance"),
                "expected_ev_effect": "Keep Swing bucket discovery handoff explicit without allowing sim-only output to mutate real runtime.",
                "evidence": [
                    f"bucket_id={bucket_id}",
                    f"canonical_bucket={item.get('canonical_bucket') or '-'}",
                    f"legacy_raw_bucket_key={item.get('legacy_raw_bucket_key') or '-'}",
                    f"ai_tier2_taxonomy_decision={(item.get('comparative_review') or {}).get('selected_decision') if isinstance(item.get('comparative_review'), dict) else '-'}",
                    f"ai_tier2_selected_source={(item.get('comparative_review') or {}).get('selected_source') if isinstance(item.get('comparative_review'), dict) else '-'}",
                    f"classification_state={item.get('classification_state')}",
                    f"reason={item.get('reason')}",
                    f"source_workorder_id={item.get('source_workorder_id') or '-'}",
                    f"parent_bucket_id={item.get('parent_bucket_id') or '-'}",
                    "decision_authority=swing_ldm_bucket_discovery_sim_auto",
                    "allowed_runtime_apply=false",
                ],
                "next_postclose_metric": "Swing bucket discovery candidates and workorders should be visible in EV, runtime summary, workorder, and verifier.",
                "files_likely_touched": [
                    "src/engine/swing_lifecycle_bucket_discovery.py",
                    "src/engine/threshold_cycle_ev_report.py",
                    "src/engine/runtime_approval_summary.py",
                    "src/engine/verify_threshold_cycle_postclose_chain.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_verify_threshold_cycle_postclose_chain.py",
                ],
                "canonical_bucket": item.get("canonical_bucket"),
                "legacy_raw_bucket_key": item.get("legacy_raw_bucket_key"),
                "deterministic_proposal": item.get("deterministic_proposal"),
                "ai_tier2_proposal": item.get("ai_tier2_proposal"),
                "comparative_review": item.get("comparative_review"),
            }
        )
    return orders


def build_code_improvement_workorder(target_date: str, *, max_orders: int = 12) -> dict[str, Any]:
    target_date = str(target_date).strip()
    isolated_source_mode = _workorder_isolated_source_mode()
    json_path, md_path = code_improvement_workorder_paths(target_date)
    previous_report = _load_json(json_path)
    source_path = automation_report_path(target_date)
    automation = _load_source_json(source_path, isolated_source_mode=isolated_source_mode)
    swing_source_path = swing_automation_report_path(target_date)
    swing_automation = _load_source_json(swing_source_path, isolated_source_mode=isolated_source_mode)
    swing_lab_source_path = swing_pattern_lab_automation_report_path(target_date)
    swing_lab_automation = _load_source_json(swing_lab_source_path, isolated_source_mode=isolated_source_mode)
    swing_discovery_source_path = swing_strategy_discovery_ev_report_path(target_date)
    swing_discovery_ev = _load_source_json(swing_discovery_source_path, isolated_source_mode=isolated_source_mode)
    swing_lifecycle_matrix_path = swing_lifecycle_decision_matrix_report_path(target_date)
    swing_lifecycle_matrix = _load_source_json(swing_lifecycle_matrix_path, isolated_source_mode=isolated_source_mode)
    swing_lifecycle_bucket_discovery_path = swing_lifecycle_bucket_discovery_report_path(target_date)
    swing_lifecycle_bucket_discovery = _load_source_json(
        swing_lifecycle_bucket_discovery_path,
        isolated_source_mode=isolated_source_mode,
    )
    ev_path = threshold_ev_report_path(target_date)
    ev_report = _load_source_json(ev_path, isolated_source_mode=isolated_source_mode)
    lifecycle_source_path = lifecycle_decision_matrix_report_path(target_date)
    lifecycle_report = _load_source_json(lifecycle_source_path, isolated_source_mode=isolated_source_mode)
    lifecycle_bucket_discovery_path = _lifecycle_bucket_discovery_report_path(target_date)
    lifecycle_bucket_discovery = _load_source_json(
        lifecycle_bucket_discovery_path,
        isolated_source_mode=isolated_source_mode,
    )
    pipeline_event_verbosity_path = _pipeline_event_verbosity_report_path(target_date)
    pipeline_event_verbosity = _load_source_json(pipeline_event_verbosity_path, isolated_source_mode=isolated_source_mode)
    observation_source_quality_path = _observation_source_quality_audit_path(target_date)
    observation_source_quality = _load_source_json(
        observation_source_quality_path,
        isolated_source_mode=isolated_source_mode,
    )
    codebase_performance_path = _codebase_performance_report_path(target_date)
    codebase_performance = _load_source_json(codebase_performance_path, isolated_source_mode=isolated_source_mode)
    pattern_lab_currentness_path = pattern_lab_currentness_audit_report_path(target_date)
    pattern_lab_currentness = _load_source_json(
        pattern_lab_currentness_path,
        isolated_source_mode=isolated_source_mode,
    )
    pattern_lab_ai_review_path = pattern_lab_ai_review_report_path(target_date)
    pattern_lab_ai_review = _load_source_json(pattern_lab_ai_review_path, isolated_source_mode=isolated_source_mode)
    producer_gap_discovery_path = producer_gap_discovery_report_path(target_date)
    producer_gap_discovery = _load_source_json(producer_gap_discovery_path, isolated_source_mode=isolated_source_mode)
    stage_hook_workorder_discovery_path = stage_hook_workorder_discovery_report_path(target_date)
    stage_hook_workorder_discovery = _load_source_json(
        stage_hook_workorder_discovery_path,
        isolated_source_mode=isolated_source_mode,
    )
    stage_hook_runtime_scaffold_path = stage_hook_runtime_scaffold_report_path(target_date)
    stage_hook_runtime_scaffold = _load_source_json(
        stage_hook_runtime_scaffold_path,
        isolated_source_mode=isolated_source_mode,
    )
    stage_hook_scaffold_by_name = _stage_hook_scaffold_by_name(stage_hook_runtime_scaffold)
    buy_funnel_sentinel_path = buy_funnel_sentinel_report_path(target_date)
    buy_funnel_sentinel = _load_source_json(buy_funnel_sentinel_path, isolated_source_mode=isolated_source_mode)
    conversion_lane_path = conversion_lane_report_path(target_date)
    conversion_lane = _load_source_json(conversion_lane_path, isolated_source_mode=isolated_source_mode)
    conversion_rank = _conversion_rank_by_candidate(conversion_lane)
    calibration_source_path = _calibration_report_path_from_ev(ev_report)
    calibration_report = _calibration_report_from_ev(ev_report)
    candidate_source_paths = {
        "pattern_lab_automation": source_path,
        "swing_improvement_automation": swing_source_path,
        "swing_pattern_lab_automation": swing_lab_source_path,
        "swing_strategy_discovery_ev": swing_discovery_source_path,
        "swing_lifecycle_decision_matrix": swing_lifecycle_matrix_path,
        "swing_lifecycle_bucket_discovery": swing_lifecycle_bucket_discovery_path,
        "threshold_cycle_ev": ev_path,
        "lifecycle_decision_matrix": lifecycle_source_path,
        "lifecycle_bucket_discovery": lifecycle_bucket_discovery_path,
        "pipeline_event_verbosity": pipeline_event_verbosity_path,
        "observation_source_quality_audit": observation_source_quality_path,
        "codebase_performance_workorder": codebase_performance_path,
        "pattern_lab_currentness_audit": pattern_lab_currentness_path,
        "pattern_lab_ai_review": pattern_lab_ai_review_path,
        "producer_gap_discovery": producer_gap_discovery_path,
        "stage_hook_workorder_discovery": stage_hook_workorder_discovery_path,
        "stage_hook_runtime_scaffold": stage_hook_runtime_scaffold_path,
        "buy_funnel_sentinel": buy_funnel_sentinel_path,
        "conversion_lane": conversion_lane_path,
    }
    source_paths = {
        label: path
        for label, path in candidate_source_paths.items()
        if _source_path_enabled(path, isolated_source_mode=isolated_source_mode)
    }
    ev_sources = ev_report.get("sources") if isinstance(ev_report.get("sources"), dict) else {}
    if ev_sources.get("scalp_entry_action_decision_matrix"):
        scalp_entry_source_path = Path(str(ev_sources.get("scalp_entry_action_decision_matrix")))
        if _source_path_enabled(scalp_entry_source_path, isolated_source_mode=isolated_source_mode):
            source_paths["scalp_entry_action_decision_matrix"] = scalp_entry_source_path
    if ev_sources.get("lifecycle_decision_matrix"):
        lifecycle_source_path = Path(str(ev_sources.get("lifecycle_decision_matrix")))
        if not _source_path_enabled(lifecycle_source_path, isolated_source_mode=isolated_source_mode):
            lifecycle_source_path = lifecycle_decision_matrix_report_path(target_date)
        else:
            lifecycle_report = _load_json(lifecycle_source_path)
    if _source_path_enabled(lifecycle_source_path, isolated_source_mode=isolated_source_mode):
        source_paths["lifecycle_decision_matrix"] = lifecycle_source_path
    if ev_sources.get("swing_lifecycle_decision_matrix"):
        swing_lifecycle_matrix_path = Path(str(ev_sources.get("swing_lifecycle_decision_matrix")))
        if not _source_path_enabled(swing_lifecycle_matrix_path, isolated_source_mode=isolated_source_mode):
            swing_lifecycle_matrix_path = swing_lifecycle_decision_matrix_report_path(target_date)
        else:
            swing_lifecycle_matrix = _load_json(swing_lifecycle_matrix_path)
    if _source_path_enabled(swing_lifecycle_matrix_path, isolated_source_mode=isolated_source_mode):
        source_paths["swing_lifecycle_decision_matrix"] = swing_lifecycle_matrix_path
    if ev_sources.get("swing_lifecycle_bucket_discovery"):
        swing_lifecycle_bucket_discovery_path = Path(str(ev_sources.get("swing_lifecycle_bucket_discovery")))
        if not _source_path_enabled(swing_lifecycle_bucket_discovery_path, isolated_source_mode=isolated_source_mode):
            swing_lifecycle_bucket_discovery_path = swing_lifecycle_bucket_discovery_report_path(target_date)
        else:
            swing_lifecycle_bucket_discovery = _load_json(swing_lifecycle_bucket_discovery_path)
    if _source_path_enabled(swing_lifecycle_bucket_discovery_path, isolated_source_mode=isolated_source_mode):
        source_paths["swing_lifecycle_bucket_discovery"] = swing_lifecycle_bucket_discovery_path
    if calibration_source_path is not None and _source_path_enabled(
        calibration_source_path,
        isolated_source_mode=isolated_source_mode,
    ):
        source_paths["threshold_cycle_calibration"] = calibration_source_path
    source_fingerprint = _source_fingerprint(source_paths)
    finding_by_order_id, finding_by_title_slug = _finding_maps(automation)
    swing_finding_by_order_id, swing_finding_by_title_slug = _finding_maps(swing_automation)
    swing_lab_finding_by_order_id, swing_lab_finding_by_title_slug = _finding_maps(swing_lab_automation)
    finding_by_order_id.update(swing_finding_by_order_id)
    finding_by_order_id.update(swing_lab_finding_by_order_id)
    finding_by_title_slug.update(swing_finding_by_title_slug)
    finding_by_title_slug.update(swing_lab_finding_by_title_slug)
    auto_family_ids = _auto_family_order_ids(automation) | _auto_family_order_ids(swing_automation) | _auto_family_order_ids(swing_lab_automation)
    scalping_orders = [
        {**item, "source_report_type": "scalping_pattern_lab_automation"}
        for item in (automation.get("code_improvement_orders") or [])
        if isinstance(item, dict)
    ]
    swing_orders = [
        {**item, "source_report_type": "swing_improvement_automation"}
        for item in (swing_automation.get("code_improvement_orders") or [])
        if isinstance(item, dict)
    ]
    swing_entry_bottleneck = (
        swing_automation.get("swing_entry_bottleneck")
        if isinstance(swing_automation.get("swing_entry_bottleneck"), dict)
        else {}
    )
    swing_entry_bottleneck_primary = str(swing_entry_bottleneck.get("primary") or "")
    swing_entry_bottleneck_matches = (
        swing_entry_bottleneck.get("matches") if isinstance(swing_entry_bottleneck.get("matches"), list) else []
    )
    swing_entry_bottleneck_order_ids = {
        str(item.get("order_id"))
        for item in swing_orders
        if item.get("order_id") == "order_swing_entry_bottleneck_auto_resolution"
    }
    swing_lab_orders = [
        {**item, "source_report_type": "swing_pattern_lab_automation"}
        for item in (swing_lab_automation.get("code_improvement_orders") or [])
        if isinstance(item, dict)
    ]
    swing_discovery_orders = _swing_strategy_discovery_followup_orders(swing_discovery_ev)
    swing_lifecycle_matrix_orders = _swing_lifecycle_matrix_followup_orders(swing_lifecycle_matrix)
    swing_lifecycle_bucket_discovery_orders = _swing_lifecycle_bucket_discovery_followup_orders(
        swing_lifecycle_bucket_discovery
    )
    pattern_lab_currentness_orders = [
        {**item, "source_report_type": item.get("source_report_type") or "pattern_lab_currentness_audit"}
        for item in (pattern_lab_currentness.get("code_improvement_orders") or [])
        if isinstance(item, dict)
    ]
    pattern_lab_ai_review_orders = [
        _sanitize_pattern_lab_ai_review_order(item, swing_lab_automation=swing_lab_automation)
        for item in (pattern_lab_ai_review.get("code_improvement_orders") or [])
        if isinstance(item, dict)
    ]
    producer_gap_discovery_orders = [
        _sanitize_producer_gap_order(item)
        for item in (producer_gap_discovery.get("code_improvement_orders") or [])
        if isinstance(item, dict)
    ]
    stage_hook_workorder_discovery_orders = [
        _sanitize_stage_hook_order(item, stage_hook_scaffold_by_name)
        for item in (stage_hook_workorder_discovery.get("code_improvement_orders") or [])
        if isinstance(item, dict)
    ]
    conversion_lane_orders = _conversion_lane_followup_orders(conversion_lane)
    buy_funnel_sentinel_orders = _buy_funnel_sentinel_followup_orders(
        buy_funnel_sentinel,
        lifecycle_report=lifecycle_report,
    )
    buy_funnel_sentinel_order_ids = {
        str(order.get("order_id"))
        for order in buy_funnel_sentinel_orders
        if order.get("order_id")
    }
    lifecycle_entry_bucket_orders = _lifecycle_entry_bucket_followup_orders(lifecycle_report)
    lifecycle_submit_bucket_orders = [
        order
        for order in _lifecycle_submit_bucket_followup_orders(lifecycle_report)
        if str(order.get("order_id") or "") not in buy_funnel_sentinel_order_ids
    ]
    lifecycle_flow_bucket_orders = _lifecycle_flow_bucket_followup_orders(lifecycle_report)
    lifecycle_holding_exit_bucket_orders = _lifecycle_holding_exit_bucket_followup_orders(lifecycle_report)
    lifecycle_scale_in_bucket_orders = _lifecycle_scale_in_bucket_followup_orders(lifecycle_report)
    lifecycle_overnight_bucket_orders = _lifecycle_overnight_bucket_followup_orders(lifecycle_report)
    lifecycle_bucket_discovery_orders = _lifecycle_bucket_discovery_followup_orders(lifecycle_bucket_discovery)
    observation_source_quality_orders = _observation_source_quality_followup_orders(observation_source_quality)
    sim_fill_match_orders = _sim_fill_and_match_report_contract_orders(ev_report, observation_source_quality)
    threshold_ev_orders = [
        *_threshold_ev_followup_orders(ev_report, target_date=target_date),
        *_entry_adm_followup_orders(ev_report),
        *_lifecycle_ai_context_followup_orders(ev_report),
        *_window_policy_audit_followup_orders(calibration_report),
        *_dynamic_entry_price_report_contract_orders(ev_report),
        *sim_fill_match_orders,
        *_panic_lifecycle_followup_orders(calibration_report),
        *_pipeline_event_verbosity_followup_orders(pipeline_event_verbosity),
        *observation_source_quality_orders,
        *_codebase_performance_followup_orders(codebase_performance),
        *buy_funnel_sentinel_orders,
    ]
    closed_instrumentation_order_families = _closed_instrumentation_order_families(
        ev_report,
        target_date=target_date,
    )
    orders = [
        *scalping_orders,
        *swing_orders,
        *swing_lab_orders,
        *swing_discovery_orders,
        *swing_lifecycle_matrix_orders,
        *swing_lifecycle_bucket_discovery_orders,
        *pattern_lab_currentness_orders,
        *pattern_lab_ai_review_orders,
        *producer_gap_discovery_orders,
        *stage_hook_workorder_discovery_orders,
        *conversion_lane_orders,
        *lifecycle_entry_bucket_orders,
        *lifecycle_submit_bucket_orders,
        *lifecycle_flow_bucket_orders,
        *lifecycle_holding_exit_bucket_orders,
        *lifecycle_scale_in_bucket_orders,
        *lifecycle_overnight_bucket_orders,
        *lifecycle_bucket_discovery_orders,
        *threshold_ev_orders,
    ]
    if conversion_rank:
        orders = [_annotate_order_conversion_fields(order, conversion_rank) for order in orders]
    seen_keys: set[tuple[str, str, str]] = set()
    deduped_orders: list[dict[str, Any]] = []
    collision_warnings: list[str] = []
    for order in orders:
        key = (str(order.get("source_report_type") or ""), str(order.get("lifecycle_stage") or ""), str(order.get("order_id") or ""))
        if key in seen_keys:
            collision_warnings.append(f"duplicate_order_id={order.get('order_id')} source={order.get('source_report_type')} stage={order.get('lifecycle_stage')}")
            continue
        seen_keys.add(key)
        deduped_orders.append(order)
    orders = deduped_orders
    recent_reports = _recent_workorder_reports(target_date)
    repeat_counts = _unresolved_repeat_counts(recent_reports)
    classified = _sort_classified(
        [
            _classify_order(
                order,
                finding_by_order_id=finding_by_order_id,
                finding_by_title_slug=finding_by_title_slug,
                auto_family_order_ids=auto_family_ids,
                closed_instrumentation_order_families=closed_instrumentation_order_families,
            )
            for order in orders
        ]
    )
    classified, repeat_escalated_order_ids = _escalate_repeated_unresolved_orders(
        classified,
        repeat_counts=repeat_counts,
    )
    classified = _sort_classified(classified)
    selected = classified[: max(1, int(max_orders))]
    required_handoff_order_ids = {
        str(order.get("order_id"))
        for order in [
            *lifecycle_entry_bucket_orders,
            *lifecycle_submit_bucket_orders,
            *lifecycle_holding_exit_bucket_orders,
            *lifecycle_scale_in_bucket_orders,
        ]
        if order.get("order_id")
    }
    required_handoff_order_ids.update(
        str(order.get("order_id"))
        for order in lifecycle_flow_bucket_orders
        if order.get("order_id")
    )
    required_handoff_order_ids.update(
        str(order.get("order_id"))
        for order in pattern_lab_currentness_orders
        if order.get("order_id")
    )
    required_handoff_order_ids.update(
        str(order.get("order_id"))
        for order in pattern_lab_ai_review_orders
        if order.get("order_id")
    )
    required_handoff_order_ids.update(
        str(order.get("order_id"))
        for order in producer_gap_discovery_orders
        if order.get("order_id")
        and str(order.get("producer_gap_priority") or "high") in {"critical", "high"}
    )
    required_handoff_order_ids.update(
        str(order.get("order_id"))
        for order in stage_hook_workorder_discovery_orders
        if order.get("order_id")
        and (
            str(order.get("stage_hook_priority") or "high") in {"critical", "high"}
            or (order.get("stage_hook_candidate_contract") or {}).get("readiness_tier")
            == "implementation_workorder_ready"
        )
    )
    required_handoff_order_ids.update(
        str(order.get("order_id"))
        for order in lifecycle_overnight_bucket_orders
        if order.get("order_id")
    )
    required_handoff_order_ids.update(
        str(order.get("order_id"))
        for order in [*swing_lifecycle_matrix_orders, *swing_lifecycle_bucket_discovery_orders]
        if order.get("order_id")
    )
    required_handoff_order_ids.update(swing_entry_bottleneck_order_ids)
    required_handoff_order_ids.update(
        str(order.get("order_id"))
        for order in lifecycle_bucket_discovery_orders
        if order.get("order_id")
    )
    required_handoff_order_ids.update(
        str(order.get("order_id"))
        for order in buy_funnel_sentinel_orders
        if order.get("order_id")
    )
    required_handoff_order_ids.update(
        str(order.get("order_id"))
        for order in conversion_lane_orders
        if order.get("order_id")
    )
    required_handoff_order_ids.update(
        str(order.get("order_id"))
        for order in observation_source_quality_orders
        if order.get("order_id")
        and order.get("improvement_type") == "source_quality_raw_row_exclusion_producer_gap"
    )
    selected_order_ids = {str(item.order.get("order_id")) for item in selected if item.order.get("order_id")}
    for item in classified:
        order_id = str(item.order.get("order_id") or "")
        if order_id in required_handoff_order_ids and order_id not in selected_order_ids:
            selected.append(item)
            selected_order_ids.add(order_id)
    selected_identity = {id(item) for item in selected}
    non_selected = [item for item in classified if id(item) not in selected_identity]
    counts: dict[str, int] = {}
    for item in classified:
        counts[item.decision] = counts.get(item.decision, 0) + 1
    selected_decision_counts: dict[str, int] = {}
    selected_route_counts: dict[str, int] = {}
    selected_unimplemented_route_counts: dict[str, int] = {}
    selected_terminal_non_implement_route_counts: dict[str, int] = {}
    selected_runtime_effect_false_count = 0
    selected_unimplemented_runtime_effect_false_count = 0
    selected_terminal_non_implement_runtime_effect_false_count = 0
    for item in selected:
        selected_decision_counts[item.decision] = selected_decision_counts.get(item.decision, 0) + 1
        route = str(item.route or item.order.get("route") or item.decision or "unknown")
        selected_route_counts[route] = selected_route_counts.get(route, 0) + 1
        if item.order.get("runtime_effect") is False:
            selected_runtime_effect_false_count += 1
            terminal_status = _terminal_non_implement_status(item)
            if terminal_status and _is_terminal_non_implement_status(terminal_status):
                selected_terminal_non_implement_runtime_effect_false_count += 1
                selected_terminal_non_implement_route_counts[route] = (
                    selected_terminal_non_implement_route_counts.get(route, 0) + 1
                )
                continue
            if item.decision != "attach_existing_family" and not _is_implemented_status(
                _repeat_unresolved_original_status(item.order)
            ):
                selected_unimplemented_runtime_effect_false_count += 1
                selected_unimplemented_route_counts[route] = selected_unimplemented_route_counts.get(route, 0) + 1
    non_selected_counts: dict[str, int] = {}
    for item in non_selected:
        non_selected_counts[item.decision] = non_selected_counts.get(item.decision, 0) + 1
    already_implemented_source_handoff_count = sum(
        1
        for item in selected
        if item.decision == "attach_existing_family"
        and str(item.order.get("target_subsystem") or "") == "lifecycle_decision_matrix"
    )
    implement_now_resolution_summary = _selected_implement_now_resolution_summary(selected)
    deferred_or_rejected_count = sum(
        non_selected_counts.get(decision, 0)
        for decision in ("design_family_candidate", "defer_evidence", "reject")
    )

    def source_ref(label: str) -> str | None:
        path = source_paths.get(label)
        if path is None:
            return None
        return str(path) if Path(path).exists() else None

    report = {
        "schema_version": WORKORDER_SCHEMA_VERSION,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "generation_id": f"{target_date}-{source_fingerprint['generation_id']}",
        "source_hash": source_fingerprint["source_hash"],
        "purpose": "codex_code_improvement_workorder_from_postclose_automation",
        "source": {
            "pattern_lab_automation": source_ref("pattern_lab_automation"),
            "swing_improvement_automation": source_ref("swing_improvement_automation"),
            "swing_pattern_lab_automation": source_ref("swing_pattern_lab_automation"),
            "swing_strategy_discovery_ev": source_ref("swing_strategy_discovery_ev"),
            "swing_lifecycle_decision_matrix": source_ref("swing_lifecycle_decision_matrix"),
            "swing_lifecycle_bucket_discovery": source_ref("swing_lifecycle_bucket_discovery"),
            "threshold_cycle_ev": source_ref("threshold_cycle_ev"),
            "lifecycle_decision_matrix": source_ref("lifecycle_decision_matrix"),
            "lifecycle_bucket_discovery": source_ref("lifecycle_bucket_discovery"),
            "scalp_entry_action_decision_matrix": source_ref("scalp_entry_action_decision_matrix"),
            "pipeline_event_verbosity": source_ref("pipeline_event_verbosity"),
            "observation_source_quality_audit": source_ref("observation_source_quality_audit"),
            "codebase_performance_workorder": source_ref("codebase_performance_workorder"),
            "pattern_lab_currentness_audit": source_ref("pattern_lab_currentness_audit"),
            "pattern_lab_ai_review": source_ref("pattern_lab_ai_review"),
            "producer_gap_discovery": source_ref("producer_gap_discovery"),
            "stage_hook_workorder_discovery": source_ref("stage_hook_workorder_discovery"),
            "stage_hook_runtime_scaffold": source_ref("stage_hook_runtime_scaffold"),
            "buy_funnel_sentinel": source_ref("buy_funnel_sentinel"),
            "conversion_lane": source_ref("conversion_lane"),
            "threshold_cycle_calibration": source_ref("threshold_cycle_calibration"),
        },
        "source_fingerprint": source_fingerprint["files"],
        "policy": {
            "runtime_patch_automation": "lifecycle_bucket_discovery_patch_candidate_only",
            "user_intervention_point": "none_for_bucket_discovery_classification",
            "post_implementation_reentry": "postclose reports and daily EV consume the updated source metrics automatically",
            "recommended_operator_instruction": (
                "lifecycle bucket discovery hook gap은 자동 patch 후보를 만들고, self code review + fix "
                "2-pass + targeted tests 통과 전에는 runtime env로 소비하지 않는다."
            ),
        },
        "summary": {
            "source_order_count": len(orders),
            "scalping_source_order_count": len(scalping_orders),
            "swing_source_order_count": len(swing_orders),
            "swing_entry_bottleneck_primary": swing_entry_bottleneck_primary or None,
            "swing_entry_bottleneck_source_order_count": len(swing_entry_bottleneck_order_ids),
            "swing_entry_bottleneck_selected": bool(
                swing_entry_bottleneck_order_ids
                and swing_entry_bottleneck_order_ids.issubset(selected_order_ids)
            ),
            "swing_entry_bottleneck_matches": swing_entry_bottleneck_matches,
            "swing_lab_source_order_count": len(swing_lab_orders),
            "swing_strategy_discovery_source_order_count": len(swing_discovery_orders),
            "swing_lifecycle_matrix_source_order_count": len(swing_lifecycle_matrix_orders),
            "swing_lifecycle_bucket_discovery_source_order_count": len(swing_lifecycle_bucket_discovery_orders),
            "pattern_lab_currentness_source_order_count": len(pattern_lab_currentness_orders),
            "pattern_lab_ai_review_source_order_count": len(pattern_lab_ai_review_orders),
            "producer_gap_discovery_source_order_count": len(producer_gap_discovery_orders),
            "producer_gap_discovery_status": producer_gap_discovery.get("status"),
            "stage_hook_workorder_discovery_source_order_count": len(stage_hook_workorder_discovery_orders),
            "stage_hook_workorder_discovery_status": stage_hook_workorder_discovery.get("status"),
            "stage_hook_runtime_scaffold_status": stage_hook_runtime_scaffold.get("status"),
            "stage_hook_runtime_scaffold_implemented_hook_count": len(stage_hook_scaffold_by_name),
            "conversion_lane_source_order_count": len(conversion_lane_orders),
            "producer_gap_discovery_high_priority_selected": bool(
                {
                    str(order.get("order_id"))
                    for order in producer_gap_discovery_orders
                    if order.get("order_id")
                    and str(order.get("producer_gap_priority") or "high") in {"critical", "high"}
                }.issubset(selected_order_ids)
            ),
            "threshold_ev_source_order_count": len(threshold_ev_orders),
            "lifecycle_entry_bucket_source_order_count": len(lifecycle_entry_bucket_orders),
            "lifecycle_submit_bucket_source_order_count": len(lifecycle_submit_bucket_orders),
            "lifecycle_flow_bucket_source_order_count": len(lifecycle_flow_bucket_orders),
            "lifecycle_holding_exit_bucket_source_order_count": len(lifecycle_holding_exit_bucket_orders),
            "lifecycle_scale_in_bucket_source_order_count": len(lifecycle_scale_in_bucket_orders),
            "lifecycle_overnight_bucket_source_order_count": len(lifecycle_overnight_bucket_orders),
            "lifecycle_bucket_discovery_source_order_count": len(lifecycle_bucket_discovery_orders),
            "pipeline_event_verbosity_source_order_count": len(
                _pipeline_event_verbosity_followup_orders(pipeline_event_verbosity)
            ),
            "observation_source_quality_source_order_count": len(
                _observation_source_quality_followup_orders(observation_source_quality)
            ),
            "codebase_performance_source_order_count": len(
                _codebase_performance_followup_orders(codebase_performance)
            ),
            "panic_lifecycle_source_order_count": len(_panic_lifecycle_followup_orders(calibration_report)),
            "selected_order_count": len(selected),
            "non_selected_order_count": len(non_selected),
            "source_decision_counts": counts,
            "decision_counts": counts,
            "selected_decision_counts": selected_decision_counts,
            "selected_route_counts": selected_route_counts,
            "selected_implement_now_route_count": selected_decision_counts.get("implement_now", 0),
            "already_implemented_source_handoff_count": already_implemented_source_handoff_count,
            "selected_runtime_effect_false_count": selected_runtime_effect_false_count,
            "selected_unimplemented_runtime_effect_false_count": selected_unimplemented_runtime_effect_false_count,
            "selected_unimplemented_route_counts": selected_unimplemented_route_counts,
            "selected_terminal_non_implement_runtime_effect_false_count": (
                selected_terminal_non_implement_runtime_effect_false_count
            ),
            "selected_terminal_non_implement_route_counts": selected_terminal_non_implement_route_counts,
            "selected_implement_now_resolution_summary": implement_now_resolution_summary,
            "selected_implement_now_existing_implementation_count": implement_now_resolution_summary[
                "existing_implementation_count"
            ],
            "selected_implement_now_existing_implementation_order_ids": implement_now_resolution_summary[
                "existing_implementation_order_ids"
            ],
            "selected_implement_now_new_runtime_effect_false_count": implement_now_resolution_summary[
                "new_runtime_effect_false_count"
            ],
            "selected_implement_now_new_runtime_effect_false_order_ids": implement_now_resolution_summary[
                "new_runtime_effect_false_order_ids"
            ],
            "repeat_unresolved_escalation_count": len(repeat_escalated_order_ids),
            "repeat_unresolved_escalated_order_ids": repeat_escalated_order_ids,
            "repeat_unresolved_history_window_days": 10,
            "non_selected_decision_counts": non_selected_counts,
            "gemini_fresh": ((automation.get("ev_report_summary") or {}).get("gemini_fresh")),
            "claude_fresh": ((automation.get("ev_report_summary") or {}).get("claude_fresh")),
            "swing_lifecycle_audit_available": bool(swing_automation),
            "swing_pattern_lab_automation_available": bool(swing_lab_automation),
            "swing_strategy_discovery_ev_available": bool(swing_discovery_ev),
            "swing_lifecycle_matrix_available": bool(swing_lifecycle_matrix),
            "swing_lifecycle_bucket_discovery_available": bool(swing_lifecycle_bucket_discovery),
            "swing_pattern_lab_fresh": ((swing_lab_automation.get("ev_report_summary") or {}).get("deepseek_lab_available")),
            "pattern_lab_currentness_status": pattern_lab_currentness.get("status"),
            "pattern_lab_currentness_fail_count": ((pattern_lab_currentness.get("summary") or {}).get("fail_count")),
            "pattern_lab_ai_review_status": pattern_lab_ai_review.get("status"),
            "pattern_lab_ai_review_workorder_count": ((pattern_lab_ai_review.get("summary") or {}).get("workorder_count")),
            "buy_funnel_sentinel_source_order_count": len(buy_funnel_sentinel_orders),
            "conversion_blocker_rank_count": len(conversion_rank),
            "buy_funnel_sentinel_primary": ((buy_funnel_sentinel.get("classification") or {}).get("primary")),
            "entry_submit_drought_primary": ((buy_funnel_sentinel.get("classification") or {}).get("primary")),
            "entry_submit_drought_selected": bool(
                buy_funnel_sentinel_orders
                and {
                    str(order.get("order_id"))
                    for order in buy_funnel_sentinel_orders
                    if order.get("order_id")
                }.issubset(selected_order_ids)
            ),
            "entry_submit_drought_required_downstream": (
                (buy_funnel_sentinel.get("entry_submit_drought_contract") or {}).get("required_downstream")
                if isinstance(buy_funnel_sentinel.get("entry_submit_drought_contract"), dict)
                else []
            ),
            "entry_submit_drought_handoff_missing": bool(
                buy_funnel_sentinel_orders
                and not {
                    str(order.get("order_id"))
                    for order in buy_funnel_sentinel_orders
                    if order.get("order_id")
                }.issubset(selected_order_ids)
            ),
            "swing_threshold_ai_status": ((swing_automation.get("ev_report_summary") or {}).get("threshold_ai_status")),
            "daily_ev_available": bool(ev_report),
            "duplicate_order_warnings": collision_warnings,
        },
        "orders": [_serialize_classified_order(item) for item in selected],
        "non_selected_orders": [_serialize_classified_order(item) for item in non_selected],
        "deferred_or_rejected_count": deferred_or_rejected_count,
        "next_codex_session": {
            "instruction": "Paste the generated markdown into Codex and ask: '이 code improvement workorder를 순서대로 구현하고 검증해줘.'",
            "workorder_markdown": str(code_improvement_workorder_paths(target_date)[1]),
        },
    }
    report["lineage"] = _previous_workorder_lineage(previous_report, report["orders"])
    report["summary"]["new_selected_order_count"] = len(report["lineage"]["new_order_ids"])
    report["summary"]["removed_selected_order_count"] = len(report["lineage"]["removed_order_ids"])
    report["summary"]["decision_changed_order_count"] = len(report["lineage"]["decision_changed_order_ids"])
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_code_improvement_workorder_markdown(report), encoding="utf-8")
    return report


def _format_list(values: Any) -> str:
    items = [str(item) for item in (values or []) if str(item).strip()]
    return ", ".join(f"`{item}`" for item in items) if items else "-"


def render_code_improvement_workorder_markdown(report: dict[str, Any]) -> str:
    date_value = report.get("date") or ""
    next_date = _next_calendar_day(str(date_value))
    source = report.get("source") if isinstance(report.get("source"), dict) else {}
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    policy = report.get("policy") if isinstance(report.get("policy"), dict) else {}
    lineage = report.get("lineage") if isinstance(report.get("lineage"), dict) else {}
    lines = [
        f"# Code Improvement Workorder - {date_value}",
        "",
        "## 목적",
        "",
        "- Postclose 자동화가 생성한 `code_improvement_order`를 Codex 실행용 작업지시서로 변환한다.",
        "- 입력은 scalping pattern lab automation, swing lifecycle improvement automation, swing pattern lab automation을 함께 포함할 수 있다.",
        "- 이 문서는 repo/runtime을 직접 변경하지 않는다. 사용자가 이 문서를 Codex 세션에 넣고 구현을 요청하는 지점만 사람 개입으로 남긴다.",
        "- 구현 후 자동화체인 재투입은 다음 postclose report, threshold calibration, daily EV report가 담당한다.",
        "",
        "## Source",
        "",
        f"- pattern_lab_automation: `{source.get('pattern_lab_automation')}`",
        f"- swing_improvement_automation: `{source.get('swing_improvement_automation') or '-'}`",
        f"- swing_pattern_lab_automation: `{source.get('swing_pattern_lab_automation') or '-'}`",
        f"- swing_strategy_discovery_ev: `{source.get('swing_strategy_discovery_ev') or '-'}`",
        f"- swing_lifecycle_decision_matrix: `{source.get('swing_lifecycle_decision_matrix') or '-'}`",
        f"- swing_lifecycle_bucket_discovery: `{source.get('swing_lifecycle_bucket_discovery') or '-'}`",
        f"- threshold_cycle_ev: `{source.get('threshold_cycle_ev') or '-'}`",
        f"- lifecycle_decision_matrix: `{source.get('lifecycle_decision_matrix') or '-'}`",
        f"- threshold_cycle_calibration: `{source.get('threshold_cycle_calibration') or '-'}`",
        f"- pipeline_event_verbosity: `{source.get('pipeline_event_verbosity') or '-'}`",
        f"- observation_source_quality_audit: `{source.get('observation_source_quality_audit') or '-'}`",
        f"- codebase_performance_workorder: `{source.get('codebase_performance_workorder') or '-'}`",
        f"- pattern_lab_currentness_audit: `{source.get('pattern_lab_currentness_audit') or '-'}`",
        f"- pattern_lab_ai_review: `{source.get('pattern_lab_ai_review') or '-'}`",
        f"- producer_gap_discovery: `{source.get('producer_gap_discovery') or '-'}`",
        f"- stage_hook_workorder_discovery: `{source.get('stage_hook_workorder_discovery') or '-'}`",
        f"- stage_hook_runtime_scaffold: `{source.get('stage_hook_runtime_scaffold') or '-'}`",
        f"- buy_funnel_sentinel: `{source.get('buy_funnel_sentinel') or '-'}`",
        f"- generated_at: `{report.get('generated_at')}`",
        f"- generation_id: `{report.get('generation_id')}`",
        f"- source_hash: `{report.get('source_hash')}`",
        "",
        "## 운영 원칙",
        "",
        "- `runtime_effect=false` order만 구현 대상으로 본다.",
        "- fallback 재개, shadow 재개, safety guard 우회는 구현하지 않는다.",
        "- runtime 영향이 생길 수 있는 변경은 feature flag, threshold family metadata, provenance, safety guard를 같이 닫는다.",
        "- 새 family는 `allowed_runtime_apply=false`에서 시작하고, 구현/테스트/guard 완료 후에만 auto_bounded_live 후보가 될 수 있다.",
        "- 구현 후에는 관련 테스트와 parser 검증을 실행하고, 다음 postclose daily EV에서 metric을 확인한다.",
        "- 같은 날짜 workorder를 재생성하면 `generation_id`와 `lineage` diff로 신규/삭제/판정변경 order를 먼저 확인한다.",
        "",
        "## 2-Pass 실행 기준",
        "",
        "- Pass 1: `implement_now` 중 instrumentation/report/provenance 구현만 먼저 수행한다.",
        "- Regeneration: 관련 postclose report와 이 workorder를 재생성하고 `lineage` diff를 확인한다.",
        "- Pass 2: 재생성 후 새로 생긴 `runtime_effect=false` order만 추가 구현한다.",
        "- Final freeze: `generation_id`, `source_hash`, 신규/삭제/판정변경 order를 최종 보고에 남긴다.",
        f"- 권장 지시문: `{policy.get('recommended_operator_instruction')}`",
        "",
        "## Snapshot Lineage",
        "",
        f"- previous_exists: `{lineage.get('previous_exists')}`",
        f"- previous_generation_id: `{lineage.get('previous_generation_id') or '-'}`",
        f"- previous_source_hash: `{lineage.get('previous_source_hash') or '-'}`",
        f"- new_order_ids: `{lineage.get('new_order_ids') or []}`",
        f"- removed_order_ids: `{lineage.get('removed_order_ids') or []}`",
        f"- decision_changed_order_ids: `{lineage.get('decision_changed_order_ids') or []}`",
        "",
        "## Summary",
        "",
        f"- source_order_count: `{summary.get('source_order_count')}`",
        f"- scalping_source_order_count: `{summary.get('scalping_source_order_count')}`",
        f"- swing_source_order_count: `{summary.get('swing_source_order_count')}`",
        f"- swing_entry_bottleneck_primary: `{summary.get('swing_entry_bottleneck_primary')}`",
        f"- swing_entry_bottleneck_selected: `{summary.get('swing_entry_bottleneck_selected')}`",
        f"- swing_lab_source_order_count: `{summary.get('swing_lab_source_order_count')}`",
        f"- swing_strategy_discovery_source_order_count: `{summary.get('swing_strategy_discovery_source_order_count')}`",
        f"- swing_lifecycle_matrix_source_order_count: `{summary.get('swing_lifecycle_matrix_source_order_count')}`",
        f"- swing_lifecycle_bucket_discovery_source_order_count: `{summary.get('swing_lifecycle_bucket_discovery_source_order_count')}`",
        f"- pattern_lab_currentness_source_order_count: `{summary.get('pattern_lab_currentness_source_order_count')}`",
        f"- pattern_lab_ai_review_source_order_count: `{summary.get('pattern_lab_ai_review_source_order_count')}`",
        f"- threshold_ev_source_order_count: `{summary.get('threshold_ev_source_order_count')}`",
        f"- lifecycle_submit_bucket_source_order_count: `{summary.get('lifecycle_submit_bucket_source_order_count')}`",
        f"- lifecycle_holding_exit_bucket_source_order_count: `{summary.get('lifecycle_holding_exit_bucket_source_order_count')}`",
        f"- pipeline_event_verbosity_source_order_count: `{summary.get('pipeline_event_verbosity_source_order_count')}`",
        f"- observation_source_quality_source_order_count: `{summary.get('observation_source_quality_source_order_count')}`",
        f"- codebase_performance_source_order_count: `{summary.get('codebase_performance_source_order_count')}`",
        f"- buy_funnel_sentinel_source_order_count: `{summary.get('buy_funnel_sentinel_source_order_count')}`",
        f"- entry_submit_drought_selected: `{summary.get('entry_submit_drought_selected')}`",
        f"- entry_submit_drought_handoff_missing: `{summary.get('entry_submit_drought_handoff_missing')}`",
        f"- panic_lifecycle_source_order_count: `{summary.get('panic_lifecycle_source_order_count')}`",
        f"- selected_order_count: `{summary.get('selected_order_count')}`",
        f"- non_selected_order_count: `{summary.get('non_selected_order_count')}`",
        f"- source_decision_counts: `{summary.get('source_decision_counts')}`",
        f"- selected_decision_counts: `{summary.get('selected_decision_counts')}`",
        f"- selected_route_counts: `{summary.get('selected_route_counts')}`",
        f"- selected_implement_now_route_count: `{summary.get('selected_implement_now_route_count')}`",
        f"- selected_runtime_effect_false_count: `{summary.get('selected_runtime_effect_false_count')}`",
        f"- selected_unimplemented_runtime_effect_false_count: `{summary.get('selected_unimplemented_runtime_effect_false_count')}`",
        f"- selected_unimplemented_route_counts: `{summary.get('selected_unimplemented_route_counts')}`",
        f"- selected_terminal_non_implement_runtime_effect_false_count: `{summary.get('selected_terminal_non_implement_runtime_effect_false_count')}`",
        f"- selected_terminal_non_implement_route_counts: `{summary.get('selected_terminal_non_implement_route_counts')}`",
        f"- selected_implement_now_existing_implementation_count: `{summary.get('selected_implement_now_existing_implementation_count')}`",
        f"- selected_implement_now_existing_implementation_order_ids: `{summary.get('selected_implement_now_existing_implementation_order_ids')}`",
        f"- selected_implement_now_new_runtime_effect_false_count: `{summary.get('selected_implement_now_new_runtime_effect_false_count')}`",
        f"- selected_implement_now_new_runtime_effect_false_order_ids: `{summary.get('selected_implement_now_new_runtime_effect_false_order_ids')}`",
        f"- repeat_unresolved_escalation_count: `{summary.get('repeat_unresolved_escalation_count')}`",
        f"- repeat_unresolved_escalated_order_ids: `{summary.get('repeat_unresolved_escalated_order_ids')}`",
        f"- non_selected_decision_counts: `{summary.get('non_selected_decision_counts')}`",
        f"- gemini_fresh: `{summary.get('gemini_fresh')}`",
        f"- claude_fresh: `{summary.get('claude_fresh')}`",
        f"- swing_lifecycle_audit_available: `{summary.get('swing_lifecycle_audit_available')}`",
        f"- swing_pattern_lab_automation_available: `{summary.get('swing_pattern_lab_automation_available')}`",
        f"- swing_pattern_lab_fresh: `{summary.get('swing_pattern_lab_fresh')}`",
        f"- pattern_lab_currentness_status: `{summary.get('pattern_lab_currentness_status')}`",
        f"- pattern_lab_currentness_fail_count: `{summary.get('pattern_lab_currentness_fail_count')}`",
        f"- pattern_lab_ai_review_status: `{summary.get('pattern_lab_ai_review_status')}`",
        f"- pattern_lab_ai_review_workorder_count: `{summary.get('pattern_lab_ai_review_workorder_count')}`",
        f"- swing_threshold_ai_status: `{summary.get('swing_threshold_ai_status')}`",
        f"- daily_ev_available: `{summary.get('daily_ev_available')}`",
        "",
    ]
    dup_warnings = summary.get("duplicate_order_warnings") if isinstance(summary.get("duplicate_order_warnings"), list) else []
    if dup_warnings:
        lines.extend(["### Duplicate Order Collisions"])
        for w in dup_warnings:
            lines.append(f"- `{w}`")
        lines.append("")
    lines.extend([
        "## Codex 실행 지시",
        "",
        "아래 order를 위에서부터 순서대로 처리한다. 각 order는 `판정 -> 근거 -> 다음 액션`으로 닫고, 코드 변경 시 관련 문서와 테스트를 함께 갱신한다.",
        "",
        "필수 검증:",
        "",
        "```bash",
        "PYTHONPATH=. .venv/bin/pytest -q <관련 테스트 파일>",
        "PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500",
        "git diff --check",
        "```",
        "",
        "threshold/postclose 체인 영향 시 추가 검증:",
        "",
        "```bash",
        "bash -n deploy/run_threshold_cycle_preopen.sh deploy/run_threshold_cycle_calibration.sh deploy/run_threshold_cycle_postclose.sh",
        "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_daily_threshold_cycle_report.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_threshold_cycle_ev_report.py",
        "```",
        "",
        "## Implementation Orders",
        "",
    ])
    for index, item in enumerate(report.get("orders") or [], start=1):
        if not isinstance(item, dict):
            continue
        lines.extend(
            [
                f"### {index}. `{item.get('order_id')}`",
                "",
                f"- title: {item.get('title')}",
                f"- decision: `{item.get('decision')}`",
                f"- decision_reason: {item.get('decision_reason')}",
                f"- source_report_type: `{item.get('source_report_type') or '-'}`",
                f"- lifecycle_stage: `{item.get('lifecycle_stage') or '-'}`",
                f"- target_subsystem: `{item.get('target_subsystem')}`",
                f"- route: `{item.get('route') or '-'}`",
                f"- mapped_family: `{item.get('mapped_family') or '-'}`",
                f"- threshold_family: `{item.get('threshold_family') or item.get('mapped_family') or '-'}`",
                f"- improvement_type: `{item.get('improvement_type') or '-'}`",
                f"- confidence: `{item.get('confidence') or '-'}`",
                f"- priority: `{item.get('priority')}`",
                f"- runtime_effect: `{item.get('runtime_effect')}`",
                f"- strategy_effect: `{item.get('strategy_effect')}`",
                f"- data_quality_effect: `{item.get('data_quality_effect')}`",
                f"- tuning_axis_effect: `{item.get('tuning_axis_effect')}`",
                f"- expected_ev_effect: {item.get('expected_ev_effect')}",
                f"- evidence: {_format_list(item.get('evidence'))}",
                f"- parity_contract: {item.get('parity_contract') or '-'}",
                f"- next_postclose_metric: {item.get('next_postclose_metric') or '-'}",
                f"- files_likely_touched: {_format_list(item.get('files_likely_touched'))}",
                f"- acceptance_tests: {_format_list(item.get('acceptance_tests'))}",
                f"- implementation_status: `{item.get('implementation_status') or '-'}`",
                f"- implementation_provenance: `{json.dumps(item.get('implementation_provenance'), ensure_ascii=False, sort_keys=True) if item.get('implementation_provenance') else '-'}`",
                f"- automation_reentry: {item.get('automation_reentry')}",
                "",
            ]
        )
        hook_contract = item.get("runtime_hook_candidate_contract")
        if isinstance(hook_contract, dict) and hook_contract:
            lines.extend(
                [
                    "Runtime hook candidate:",
                    "",
                    f"- hook_name: `{hook_contract.get('hook_name') or '-'}`",
                    f"- stage: `{hook_contract.get('stage') or '-'}`",
                    f"- initial_authority: `{hook_contract.get('initial_authority') or '-'}`",
                    f"- apply_boundary: `{hook_contract.get('apply_boundary') or '-'}`",
                    f"- action_namespace: {_format_list(hook_contract.get('action_namespace'))}",
                    f"- eligible_after: {_format_list(hook_contract.get('eligible_after'))}",
                    f"- safety_vetoes: {_format_list(hook_contract.get('safety_vetoes'))}",
                    f"- rollback_guards: {_format_list(hook_contract.get('rollback_guards'))}",
                    f"- required_source_artifacts: {_format_list(hook_contract.get('required_source_artifacts'))}",
                    f"- required_ev_evidence: {_format_list(hook_contract.get('required_ev_evidence'))}",
                    f"- forbidden_uses: {_format_list(hook_contract.get('forbidden_uses'))}",
                    "",
                ]
            )
        stage_hook_contract = item.get("stage_hook_candidate_contract")
        if isinstance(stage_hook_contract, dict) and stage_hook_contract:
            lines.extend(
                [
                    "Stage hook candidate:",
                    "",
                    f"- hook_name: `{stage_hook_contract.get('hook_name') or '-'}`",
                    f"- hook_class: `{stage_hook_contract.get('hook_class') or '-'}`",
                    f"- stage: `{stage_hook_contract.get('stage') or '-'}`",
                    f"- initial_authority: `{stage_hook_contract.get('initial_authority') or '-'}`",
                    f"- readiness_tier: `{stage_hook_contract.get('readiness_tier') or '-'}`",
                    f"- evidence_score: `{stage_hook_contract.get('evidence_score')}`",
                    f"- action_namespace: {_format_list(stage_hook_contract.get('action_namespace'))}",
                    f"- action_namespace_scope: `{stage_hook_contract.get('action_namespace_scope') or '-'}`",
                    f"- required_source_artifacts: {_format_list(stage_hook_contract.get('required_source_artifacts'))}",
                    f"- required_mapping_tests: {_format_list(stage_hook_contract.get('required_mapping_tests'))}",
                    f"- rollback_guard_requirements: {_format_list(stage_hook_contract.get('rollback_guard_requirements'))}",
                    f"- forbidden_uses: {_format_list(stage_hook_contract.get('forbidden_uses'))}",
                    "",
                ]
            )
        lines.extend(["실행 기준:", ""])
        decision = item.get("decision")
        if decision == "implement_now":
            lines.extend(
                [
                    "- instrumentation/provenance/report source 보강을 우선 구현한다.",
                    "- runtime 판단값을 직접 바꾸지 않는다.",
                    "- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.",
                    "",
                ]
            )
        elif decision == "attach_existing_family":
            lines.extend(
                [
                    "- 기존 threshold family의 source metric/provenance를 보강한다.",
                    "- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.",
                    "- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.",
                    "",
                ]
            )
        elif decision == "design_family_candidate":
            lines.extend(
                [
                    "- 새 family 후보 metadata와 report-only source를 설계한다.",
                    "- `allowed_runtime_apply=false`를 유지한다.",
                    "- sample floor, safety guard, target env key, tests가 닫히기 전 runtime 적용 금지.",
                    "",
                ]
            )
        elif decision == "defer_evidence":
            lines.extend(
                [
                    "- 구현하지 말고 부족한 evidence와 다음 확인 artifact를 명시한다.",
                    "- 필요한 경우 report warning 또는 다음 pattern lab 재평가 항목으로만 남긴다.",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "- 구현하지 않는다.",
                    "- reject 사유를 유지하고, 필요하면 report_only_calibration 또는 bounded canary 설계로 번역 가능한지 별도 판단한다.",
                    "",
                ]
            )
    if not report.get("orders"):
        lines.append("- none")
        lines.append("")
    non_selected_orders = [item for item in (report.get("non_selected_orders") or []) if isinstance(item, dict)]
    if non_selected_orders:
        lines.extend(
            [
                "## Non-Selected Source Orders",
                "",
                "아래 항목은 source order로 분류됐지만 selected implementation order에는 포함되지 않았다. 재작업 지시 시 `decision`, `decision_reason`, `runtime_effect`를 먼저 재판정한다.",
                "",
            ]
        )
        for index, item in enumerate(non_selected_orders, start=1):
            lines.extend(
                [
                    f"### N{index}. `{item.get('order_id')}`",
                    "",
                    f"- title: {item.get('title')}",
                    f"- decision: `{item.get('decision')}`",
                    f"- decision_reason: {item.get('decision_reason')}",
                    f"- source_report_type: `{item.get('source_report_type') or '-'}`",
                    f"- lifecycle_stage: `{item.get('lifecycle_stage') or '-'}`",
                    f"- target_subsystem: `{item.get('target_subsystem')}`",
                    f"- runtime_effect: `{item.get('runtime_effect')}`",
                    f"- allowed_runtime_apply: `{item.get('allowed_runtime_apply')}`",
                    f"- implementation_status: `{item.get('implementation_status') or '-'}`",
                    f"- files_likely_touched: {_format_list(item.get('files_likely_touched'))}",
                    f"- acceptance_tests: {_format_list(item.get('acceptance_tests'))}",
                    "",
                ]
            )
    lines.extend(
        [
            "## 자동화체인 재투입",
            "",
            f"- 구현 결과는 `{next_date}` 이후 postclose `threshold_cycle`, `scalping_pattern_lab_automation`, `threshold_cycle_ev`가 자동으로 다시 읽는다.",
            "- 구현자가 수동으로 threshold 값을 바꾸는 것이 아니라, source/report/provenance를 닫아 다음 calibration이 판단하게 한다.",
            f"- 다음 Codex 세션 입력 문구: `{policy.get('user_intervention_point')}`",
            "",
            "## Project/Calendar 동기화",
            "",
            "문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.",
            "",
            "```bash",
            "PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Codex code improvement workorder from pattern lab automation.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--max-orders", type=int, default=12)
    args = parser.parse_args(argv)
    report = build_code_improvement_workorder(args.target_date, max_orders=args.max_orders)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
