"""Verify postclose artifact predecessor integrity and workorder lineage consistency."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime, time as dtime
from pathlib import Path
from typing import Any

from src.engine.daily_threshold_cycle_report import REPORT_DIR

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = PROJECT_ROOT / "logs" / "threshold_cycle_postclose_cron.log"
VERIFY_DIR = REPORT_DIR / "threshold_cycle_postclose_verification"

_START_MARKER = "[START] threshold-cycle postclose"
_DONE_MARKER = "[DONE] threshold-cycle postclose"
_FAIL_MARKER = "[FAIL] threshold-cycle postclose"
_PAUSED_MARKER = "[PAUSED] threshold-cycle postclose"
_READY_RE = re.compile(
    r"artifact ready label=(?P<label>\S+) path=(?P<path>\S+) waited=(?P<waited>\d+)s(?: json_valid=(?P<json_valid>\w+))?"
)
_TIMEOUT_RE = re.compile(r"artifact wait timeout label=(?P<label>\S+) path=(?P<path>\S+) waited=(?P<waited>\d+)s")
_AI_RUNTIME_STATES = {
    "adjust_up",
    "adjust_down",
    "hold",
    "hold_no_edge",
}
_OPTIONAL_ARTIFACT_LABELS = {
    "lifecycle_bucket_discovery",
}
_AI_EXEMPT_RUNTIME_FAMILIES = {
    "latency_classifier_runtime_profile",
}


def verification_report_paths(target_date: str) -> tuple[Path, Path]:
    base = VERIFY_DIR / f"threshold_cycle_postclose_verification_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []


def _latest_run_lines(log_lines: list[str], target_date: str) -> tuple[list[str], str | None]:
    needle = f"{_START_MARKER} target_date={target_date}"
    start_indexes = [idx for idx, line in enumerate(log_lines) if needle in line]
    if not start_indexes:
        return [], None
    start_idx = start_indexes[-1]
    start_line = log_lines[start_idx]
    return log_lines[start_idx + 1 :], start_line


def _parse_bool_flags(line: str) -> dict[str, bool]:
    flags: dict[str, bool] = {}
    for key, value in re.findall(r"([A-Za-z0-9_]+)=(true|false|1|0)", line):
        flags[key] = value in {"true", "1"}
    return flags


def _artifact_paths(target_date: str) -> dict[str, Path]:
    next_day = _next_krx_trading_day(target_date)
    return {
        "market_panic_breadth": REPORT_DIR
        / "market_panic_breadth"
        / f"market_panic_breadth_{target_date}.json",
        "panic_sell_defense": REPORT_DIR / "panic_sell_defense" / f"panic_sell_defense_{target_date}.json",
        "panic_buying": REPORT_DIR / "panic_buying" / f"panic_buying_{target_date}.json",
        "threshold_cycle_ev": REPORT_DIR / "threshold_cycle_ev" / f"threshold_cycle_ev_{target_date}.json",
        "scalp_entry_action_decision_matrix": REPORT_DIR
        / "scalp_entry_action_decision_matrix"
        / f"scalp_entry_action_decision_matrix_{target_date}.json",
        "lifecycle_decision_matrix": REPORT_DIR
        / "lifecycle_decision_matrix"
        / f"lifecycle_decision_matrix_{target_date}.json",
        "lifecycle_bucket_discovery": REPORT_DIR
        / "lifecycle_bucket_discovery"
        / f"lifecycle_bucket_discovery_{target_date}.json",
        "code_improvement_workorder": REPORT_DIR / "code_improvement_workorder" / f"code_improvement_workorder_{target_date}.json",
        "runtime_approval_summary": REPORT_DIR / "runtime_approval_summary" / f"runtime_approval_summary_{target_date}.json",
        "pattern_lab_currentness_audit": REPORT_DIR
        / "pattern_lab_currentness_audit"
        / f"pattern_lab_currentness_audit_{target_date}.json",
        "pattern_lab_propagation_audit": REPORT_DIR
        / "pattern_lab_propagation_audit"
        / f"pattern_lab_propagation_audit_{target_date}.json",
        "swing_daily_simulation": REPORT_DIR / "swing_daily_simulation" / f"swing_daily_simulation_{target_date}.json",
        "swing_lifecycle_audit": REPORT_DIR / "swing_lifecycle_audit" / f"swing_lifecycle_audit_{target_date}.json",
        "next_stage2_checklist": PROJECT_ROOT / "docs" / "checklists" / f"{next_day}-stage2-todo-checklist.md",
    }


def _next_krx_trading_day(target_date: str) -> str:
    from src.engine.build_next_stage2_checklist import _next_krx_trading_day as _next

    return _next(target_date)


def _json_valid(path: Path) -> bool:
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return True


def _ai_review_path(target_date: str) -> Path:
    return REPORT_DIR / "threshold_cycle_ai_review" / f"threshold_cycle_ai_review_{target_date}_postclose.json"


def _scalp_sim_overnight_path(target_date: str) -> Path:
    return REPORT_DIR / "scalp_sim_overnight" / f"scalp_sim_overnight_{target_date}.json"


def _calibration_path(target_date: str) -> Path:
    return (
        REPORT_DIR
        / "threshold_cycle_calibration"
        / f"threshold_cycle_calibration_{target_date}_postclose.json"
    )


def _runtime_candidates_requiring_ai(calibration_report: dict[str, Any]) -> list[str]:
    candidates = calibration_report.get("calibration_candidates")
    if not isinstance(candidates, list):
        return []

    blocking: list[str] = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        family = str(item.get("family") or item.get("source_family") or "").strip()
        state = str(item.get("calibration_state") or "").strip()
        if not family or family in _AI_EXEMPT_RUNTIME_FAMILIES:
            continue
        if state not in _AI_RUNTIME_STATES:
            continue
        if item.get("allowed_runtime_apply") is not True:
            continue
        if item.get("human_approval_required") is True:
            continue
        blocking.append(family)
    return sorted(set(blocking))



def _slug(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9가-힣]+", "_", str(value or "").strip().lower()).strip("_")
    return text[:80] or "unknown"


def _entry_bucket_order_id(item: dict[str, Any]) -> str:
    bucket_type = _slug(str(item.get("bucket_type") or "bucket"))
    bucket_key = _slug(str(item.get("bucket_key") or item.get("workorder_id") or "unknown"))
    return f"order_lifecycle_entry_bucket_{bucket_type}_{bucket_key}"


def _scale_in_bucket_order_id(item: dict[str, Any]) -> str:
    bucket_type = _slug(str(item.get("bucket_type") or "bucket"))
    bucket_key = _slug(str(item.get("bucket_key") or item.get("workorder_id") or "unknown"))
    return f"order_lifecycle_scale_in_bucket_{bucket_type}_{bucket_key}"


def _overnight_bucket_order_id(item: dict[str, Any]) -> str:
    bucket_type = _slug(str(item.get("bucket_type") or "bucket"))
    bucket_key = _slug(str(item.get("bucket_key") or item.get("workorder_id") or "unknown"))
    return f"order_lifecycle_overnight_bucket_{bucket_type}_{bucket_key}"


def _collect_entry_bucket_candidate_ids(payload: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(payload, dict):
        candidates = payload.get("entry_bucket_runtime_approval_candidates")
        if isinstance(candidates, list):
            for item in candidates:
                if isinstance(item, dict) and item.get("candidate_id"):
                    found.add(str(item.get("candidate_id")))
        for value in payload.values():
            found.update(_collect_entry_bucket_candidate_ids(value))
    elif isinstance(payload, list):
        for item in payload:
            found.update(_collect_entry_bucket_candidate_ids(item))
    return found


def _collect_scale_in_bucket_candidate_ids(payload: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(payload, dict):
        candidates = payload.get("scale_in_bucket_runtime_approval_candidates")
        if isinstance(candidates, list):
            for item in candidates:
                if isinstance(item, dict) and item.get("candidate_id"):
                    found.add(str(item.get("candidate_id")))
        for value in payload.values():
            found.update(_collect_scale_in_bucket_candidate_ids(value))
    elif isinstance(payload, list):
        for item in payload:
            found.update(_collect_scale_in_bucket_candidate_ids(item))
    return found


def _collect_overnight_bucket_candidate_ids(payload: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(payload, dict):
        candidates = payload.get("overnight_bucket_runtime_approval_candidates")
        if isinstance(candidates, list):
            for item in candidates:
                if isinstance(item, dict) and item.get("candidate_id"):
                    found.add(str(item.get("candidate_id")))
        for value in payload.values():
            found.update(_collect_overnight_bucket_candidate_ids(value))
    elif isinstance(payload, list):
        for item in payload:
            found.update(_collect_overnight_bucket_candidate_ids(item))
    return found


def _collect_lifecycle_bucket_discovery_ids(payload: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(payload, dict):
        for key in ("surfaced_candidate_ids", "approved_bucket_ids"):
            value = payload.get(key)
            if isinstance(value, list):
                found.update(str(item) for item in value if item)
        for key in ("surfaced_candidates", "live_auto_apply_candidates", "sim_auto_approved_candidates"):
            value = payload.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and item.get("bucket_id"):
                        found.add(str(item.get("bucket_id")))
        for value in payload.values():
            found.update(_collect_lifecycle_bucket_discovery_ids(value))
    elif isinstance(payload, list):
        for item in payload:
            found.update(_collect_lifecycle_bucket_discovery_ids(item))
    return found


def _lifecycle_bucket_discovery_handoff_status(
    discovery: dict[str, Any],
    bridge_report: dict[str, Any],
    runtime_summary: dict[str, Any],
    workorder: dict[str, Any],
) -> dict[str, Any]:
    discovery_summary = discovery.get("summary") if isinstance(discovery.get("summary"), dict) else {}
    discovery_warnings = [str(item) for item in (discovery.get("warnings") or []) if str(item)]
    source_contract_status = str(discovery_summary.get("source_contract_status") or "")
    ai_review_status = str(discovery_summary.get("ai_two_pass_review_status") or "")
    candidates = discovery.get("surfaced_candidates") if isinstance(discovery.get("surfaced_candidates"), list) else []
    expected_ids = sorted(
        str(item.get("bucket_id"))
        for item in candidates
        if isinstance(item, dict) and item.get("bucket_id")
    )
    live_families = sorted(
        {
            str(item.get("live_auto_apply_family"))
            for item in candidates
            if isinstance(item, dict) and item.get("classification_state") == "live_auto_apply_ready" and item.get("live_auto_apply_family")
        }
    )
    bridge_families = {
        str(item.get("family"))
        for item in (bridge_report.get("candidates") if isinstance(bridge_report.get("candidates"), list) else [])
        if isinstance(item, dict) and item.get("family")
    }
    runtime_ids = _collect_lifecycle_bucket_discovery_ids(runtime_summary)
    order_ids = {
        str(item.get("order_id"))
        for item in (workorder.get("orders") if isinstance(workorder.get("orders"), list) else [])
        if isinstance(item, dict) and item.get("order_id")
    }
    expected_workorder_prefix = "order_lifecycle_bucket_discovery_"
    workorder_needed = [
        str(item.get("bucket_id"))
        for item in candidates
        if isinstance(item, dict)
        and str(item.get("classification_state") or "") in {"new_bucket_candidate", "runtime_blocked_contract_gap", "code_patch_required", "code_review_failed"}
    ]
    ai_followup_ids = sorted(
        str(item.get("bucket_id"))
        for item in candidates
        if isinstance(item, dict) and item.get("bucket_id") and item.get("ai_review_followup_required")
    )
    missing_bridge_families = sorted(set(live_families) - bridge_families)
    missing_runtime_summary_ids = sorted(set(expected_ids) - runtime_ids) if runtime_ids else expected_ids
    has_discovery_workorder = any(order_id.startswith(expected_workorder_prefix) for order_id in order_ids)
    missing: list[str] = []
    warnings: list[str] = []
    if missing_bridge_families:
        missing.append("lifecycle_bucket_discovery_live_auto_bridge_missing")
    if expected_ids and missing_runtime_summary_ids:
        missing.append("runtime_approval_summary_lifecycle_bucket_discovery_missing")
    if workorder_needed and not has_discovery_workorder:
        missing.append("code_improvement_workorder_lifecycle_bucket_discovery_orders_missing")
    if source_contract_status == "fail":
        missing.append("lifecycle_bucket_discovery_source_contract_fail")
    elif source_contract_status and source_contract_status != "pass":
        warnings.append(f"lifecycle_bucket_discovery_source_contract_{source_contract_status}")
    if ai_followup_ids:
        warnings.append("lifecycle_bucket_discovery_ai_post_apply_followup_required")
    warnings.extend(
        item
        for item in discovery_warnings
        if item.startswith("ai_") or item.startswith("source_contract_")
    )
    warnings = list(dict.fromkeys(warnings))
    return {
        "status": "fail" if missing else ("missing" if not discovery else "pass"),
        "source_contract_status": source_contract_status or None,
        "ai_two_pass_review_status": ai_review_status or None,
        "expected_candidate_ids": expected_ids,
        "live_auto_apply_families": live_families,
        "runtime_apply_bridge_families": sorted(bridge_families),
        "runtime_approval_summary_candidate_ids": sorted(runtime_ids),
        "missing_bridge_families": missing_bridge_families,
        "missing_runtime_summary_candidate_ids": missing_runtime_summary_ids,
        "workorder_needed_bucket_ids": workorder_needed,
        "ai_post_apply_followup_bucket_ids": ai_followup_ids,
        "has_discovery_workorder": has_discovery_workorder,
        "missing": missing,
        "warnings": warnings,
        "interpretation": (
            "lifecycle bucket discovery candidates propagated to bridge/runtime summary/workorder"
            if discovery and not missing
            else "lifecycle bucket discovery produced surfaced candidates that downstream consumers dropped"
            if discovery
            else "lifecycle bucket discovery report missing"
        ),
    }


def _entry_bucket_handoff_status(
    ldm_report: dict[str, Any],
    ev_report: dict[str, Any],
    runtime_summary: dict[str, Any],
    workorder: dict[str, Any],
) -> dict[str, Any]:
    attribution = (
        ldm_report.get("entry_bucket_attribution")
        if isinstance(ldm_report.get("entry_bucket_attribution"), dict)
        else {}
    )
    candidates = (
        attribution.get("runtime_approval_candidates")
        if isinstance(attribution.get("runtime_approval_candidates"), list)
        else []
    )
    source_workorders = (
        attribution.get("code_improvement_workorders")
        if isinstance(attribution.get("code_improvement_workorders"), list)
        else []
    )
    expected_candidate_ids = sorted(
        str(item.get("candidate_id"))
        for item in candidates
        if isinstance(item, dict) and item.get("candidate_id")
    )
    expected_order_ids = sorted(
        _entry_bucket_order_id(item)
        for item in source_workorders
        if isinstance(item, dict) and item.get("bucket_type") and item.get("bucket_key")
    )
    ev_candidate_ids = _collect_entry_bucket_candidate_ids(ev_report)
    runtime_candidate_ids = _collect_entry_bucket_candidate_ids(runtime_summary)
    actual_order_ids = {
        str(item.get("order_id"))
        for item in (workorder.get("orders") if isinstance(workorder.get("orders"), list) else [])
        if isinstance(item, dict) and item.get("order_id")
    }
    missing_ev_candidates = sorted(set(expected_candidate_ids) - ev_candidate_ids)
    missing_runtime_summary_candidates = sorted(set(expected_candidate_ids) - runtime_candidate_ids)
    missing_workorder_order_ids = sorted(set(expected_order_ids) - actual_order_ids)
    missing: list[str] = []
    if missing_ev_candidates:
        missing.append("threshold_cycle_ev_entry_bucket_candidates_missing")
    if missing_runtime_summary_candidates:
        missing.append("runtime_approval_summary_entry_bucket_candidates_missing")
    if missing_workorder_order_ids:
        missing.append("code_improvement_workorder_entry_bucket_orders_missing")
    return {
        "status": "fail" if missing else "pass",
        "expected_candidate_ids": expected_candidate_ids,
        "threshold_cycle_ev_candidate_ids": sorted(ev_candidate_ids),
        "runtime_approval_summary_candidate_ids": sorted(runtime_candidate_ids),
        "missing_ev_candidate_ids": missing_ev_candidates,
        "missing_runtime_summary_candidate_ids": missing_runtime_summary_candidates,
        "expected_workorder_order_ids": expected_order_ids,
        "actual_workorder_order_ids": sorted(actual_order_ids),
        "missing_workorder_order_ids": missing_workorder_order_ids,
        "missing": missing,
        "interpretation": (
            "LDM entry bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder."
            if not missing
            else "LDM entry bucket output was generated but one or more downstream consumers dropped it."
        ),
    }


def _scale_in_bucket_handoff_status(
    ldm_report: dict[str, Any],
    ev_report: dict[str, Any],
    runtime_summary: dict[str, Any],
    workorder: dict[str, Any],
) -> dict[str, Any]:
    attribution = (
        ldm_report.get("scale_in_bucket_attribution")
        if isinstance(ldm_report.get("scale_in_bucket_attribution"), dict)
        else {}
    )
    candidates = (
        attribution.get("runtime_approval_candidates")
        if isinstance(attribution.get("runtime_approval_candidates"), list)
        else []
    )
    source_workorders = (
        attribution.get("code_improvement_workorders")
        if isinstance(attribution.get("code_improvement_workorders"), list)
        else []
    )
    expected_candidate_ids = sorted(
        str(item.get("candidate_id"))
        for item in candidates
        if isinstance(item, dict) and item.get("candidate_id")
    )
    expected_order_ids = sorted(
        _scale_in_bucket_order_id(item)
        for item in source_workorders
        if isinstance(item, dict) and item.get("bucket_type") and item.get("bucket_key")
    )
    ev_candidate_ids = _collect_scale_in_bucket_candidate_ids(ev_report)
    runtime_candidate_ids = _collect_scale_in_bucket_candidate_ids(runtime_summary)
    actual_order_ids = {
        str(item.get("order_id"))
        for item in (workorder.get("orders") if isinstance(workorder.get("orders"), list) else [])
        if isinstance(item, dict) and item.get("order_id")
    }
    missing_ev_candidates = sorted(set(expected_candidate_ids) - ev_candidate_ids)
    missing_runtime_summary_candidates = sorted(set(expected_candidate_ids) - runtime_candidate_ids)
    missing_workorder_order_ids = sorted(set(expected_order_ids) - actual_order_ids)
    missing: list[str] = []
    if missing_ev_candidates:
        missing.append("threshold_cycle_ev_scale_in_bucket_candidates_missing")
    if missing_runtime_summary_candidates:
        missing.append("runtime_approval_summary_scale_in_bucket_candidates_missing")
    if missing_workorder_order_ids:
        missing.append("code_improvement_workorder_scale_in_bucket_orders_missing")
    return {
        "status": "fail" if missing else "pass",
        "expected_candidate_ids": expected_candidate_ids,
        "threshold_cycle_ev_candidate_ids": sorted(ev_candidate_ids),
        "runtime_approval_summary_candidate_ids": sorted(runtime_candidate_ids),
        "missing_ev_candidate_ids": missing_ev_candidates,
        "missing_runtime_summary_candidate_ids": missing_runtime_summary_candidates,
        "expected_workorder_order_ids": expected_order_ids,
        "actual_workorder_order_ids": sorted(actual_order_ids),
        "missing_workorder_order_ids": missing_workorder_order_ids,
        "missing": missing,
        "interpretation": (
            "LDM scale-in bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder."
            if not missing
            else "LDM scale-in bucket output was generated but one or more downstream consumers dropped it."
        ),
    }


def _overnight_bucket_handoff_status(
    ldm_report: dict[str, Any],
    ev_report: dict[str, Any],
    runtime_summary: dict[str, Any],
    workorder: dict[str, Any],
) -> dict[str, Any]:
    attribution = (
        ldm_report.get("overnight_bucket_attribution")
        if isinstance(ldm_report.get("overnight_bucket_attribution"), dict)
        else {}
    )
    candidates = (
        attribution.get("runtime_approval_candidates")
        if isinstance(attribution.get("runtime_approval_candidates"), list)
        else []
    )
    source_workorders = (
        attribution.get("code_improvement_workorders")
        if isinstance(attribution.get("code_improvement_workorders"), list)
        else []
    )
    expected_candidate_ids = sorted(
        str(item.get("candidate_id"))
        for item in candidates
        if isinstance(item, dict) and item.get("candidate_id")
    )
    expected_order_ids = sorted(
        _overnight_bucket_order_id(item)
        for item in source_workorders
        if isinstance(item, dict) and item.get("bucket_type") and item.get("bucket_key")
    )
    ev_candidate_ids = _collect_overnight_bucket_candidate_ids(ev_report)
    runtime_candidate_ids = _collect_overnight_bucket_candidate_ids(runtime_summary)
    actual_order_ids = {
        str(item.get("order_id"))
        for item in (workorder.get("orders") if isinstance(workorder.get("orders"), list) else [])
        if isinstance(item, dict) and item.get("order_id")
    }
    missing_ev_candidates = sorted(set(expected_candidate_ids) - ev_candidate_ids)
    missing_runtime_summary_candidates = sorted(set(expected_candidate_ids) - runtime_candidate_ids)
    missing_workorder_order_ids = sorted(set(expected_order_ids) - actual_order_ids)
    missing: list[str] = []
    if missing_ev_candidates:
        missing.append("threshold_cycle_ev_overnight_bucket_candidates_missing")
    if missing_runtime_summary_candidates:
        missing.append("runtime_approval_summary_overnight_bucket_candidates_missing")
    if missing_workorder_order_ids:
        missing.append("code_improvement_workorder_overnight_bucket_orders_missing")
    return {
        "status": "fail" if missing else "pass",
        "expected_candidate_ids": expected_candidate_ids,
        "threshold_cycle_ev_candidate_ids": sorted(ev_candidate_ids),
        "runtime_approval_summary_candidate_ids": sorted(runtime_candidate_ids),
        "missing_ev_candidate_ids": missing_ev_candidates,
        "missing_runtime_summary_candidate_ids": missing_runtime_summary_candidates,
        "expected_workorder_order_ids": expected_order_ids,
        "actual_workorder_order_ids": sorted(actual_order_ids),
        "missing_workorder_order_ids": missing_workorder_order_ids,
        "missing": missing,
        "interpretation": (
            "LDM overnight bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder."
            if not missing
            else "LDM overnight bucket output was generated but one or more downstream consumers dropped it."
        ),
    }


def _has_scale_in_source(ldm_report: dict[str, Any]) -> bool:
    sources = ldm_report.get("sources") if isinstance(ldm_report.get("sources"), dict) else {}
    summary = sources.get("scale_in_attribution") if isinstance(sources.get("scale_in_attribution"), dict) else {}
    if int(summary.get("rows") or 0) > 0:
        return True
    report_summary = ldm_report.get("summary") if isinstance(ldm_report.get("summary"), dict) else {}
    stage_counts = report_summary.get("stage_counts") if isinstance(report_summary.get("stage_counts"), dict) else {}
    return int(stage_counts.get("scale_in") or 0) > 0


def _has_overnight_source(ldm_report: dict[str, Any]) -> bool:
    sources = ldm_report.get("sources") if isinstance(ldm_report.get("sources"), dict) else {}
    summary = sources.get("scalp_sim_overnight") if isinstance(sources.get("scalp_sim_overnight"), dict) else {}
    return int(summary.get("rows") or 0) > 0


def _scalp_sim_overnight_source_quality(report: dict[str, Any], *, report_exists: bool) -> dict[str, Any]:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    active_undecided_count = int(summary.get("active_undecided_count") or 0)
    decision_target = int(summary.get("decision_target") or 0)
    source_quality_status = str(summary.get("source_quality_status") or "missing").strip()
    warnings = summary.get("source_quality_warnings") if isinstance(summary.get("source_quality_warnings"), list) else []
    missing: list[str] = []
    if report_exists and not summary:
        missing.append("scalp_sim_overnight_report_missing_or_invalid")
    if active_undecided_count > 0 and decision_target == 0:
        missing.append("scalp_sim_overnight_active_undecided_without_decision")
    if source_quality_status == "source_quality_blocker":
        missing.append("scalp_sim_overnight_source_quality_blocker")
    return {
        "status": "fail" if missing else ("missing" if not report_exists else "pass"),
        "decision_target": decision_target,
        "active_undecided_count": active_undecided_count,
        "decision_coverage_rate": summary.get("decision_coverage_rate"),
        "source_quality_status": source_quality_status,
        "source_quality_warnings": warnings,
        "missing": missing,
        "interpretation": (
            "scalp sim overnight report was not present in this verification fixture/run"
            if not report_exists
            else "scalp sim overnight preclose decisions covered active sim positions"
            if not missing
            else "active scalp sim overnight positions were not covered by preclose decision events"
        ),
    }

def _ai_correction_status(target_date: str) -> dict[str, Any]:
    ai_path = _ai_review_path(target_date)
    calibration_path = _calibration_path(target_date)
    ai_review = _load_json(ai_path)
    calibration_report = _load_json(calibration_path)
    blocking_families = _runtime_candidates_requiring_ai(calibration_report)
    ai_status = str(ai_review.get("ai_status") or "missing").strip()
    provider_status = ai_review.get("provider_status")
    parse_warnings = ai_review.get("parse_warnings")
    if not isinstance(parse_warnings, list):
        parse_warnings = []

    if ai_status == "parsed":
        status = "pass"
    elif blocking_families:
        status = "fail"
    elif ai_path.exists() and ai_status not in {"", "missing"}:
        status = "warning"
    else:
        status = "missing"

    return {
        "status": status,
        "ai_status": ai_status,
        "ai_review_path": str(ai_path),
        "calibration_path": str(calibration_path),
        "provider_status": provider_status,
        "parse_warnings": parse_warnings,
        "blocking_runtime_candidate_families": blocking_families,
        "interpretation": (
            "AI correction parsed successfully"
            if status == "pass"
            else "AI correction unavailable blocks runtime-applicable threshold candidates"
            if status == "fail"
            else "AI correction unavailable but no runtime-applicable candidate was detected"
            if status == "warning"
            else "AI correction artifact missing or unreadable"
        ),
    }


def _postclose_not_yet_due(target_date: str) -> bool:
    try:
        parsed = date.fromisoformat(target_date)
    except ValueError:
        return False
    now = datetime.now()
    return parsed == now.date() and now.time() < dtime(16, 10)


def build_threshold_cycle_postclose_verification(
    target_date: str,
    *,
    require_done_marker: bool = True,
) -> dict[str, Any]:
    target_date = str(target_date).strip()
    log_lines = _read_lines(LOG_PATH)
    run_lines, start_line = _latest_run_lines(log_lines, target_date)

    predecessor_ready: list[dict[str, Any]] = []
    predecessor_waits: list[dict[str, Any]] = []
    predecessor_timeouts: list[dict[str, Any]] = []
    log_issues: list[str] = []
    done_line: str | None = None

    for line in run_lines:
        ready_match = _READY_RE.search(line)
        if ready_match:
            waited = int(ready_match.group("waited"))
            item = {
                "label": ready_match.group("label"),
                "path": ready_match.group("path"),
                "waited_sec": waited,
                "json_valid": ready_match.group("json_valid"),
            }
            predecessor_ready.append(item)
            if waited > 0:
                predecessor_waits.append(item)
        timeout_match = _TIMEOUT_RE.search(line)
        if timeout_match:
            predecessor_timeouts.append(
                {
                    "label": timeout_match.group("label"),
                    "path": timeout_match.group("path"),
                    "waited_sec": int(timeout_match.group("waited")),
                }
            )
        if _FAIL_MARKER in line and f"target_date={target_date}" in line:
            log_issues.append("postclose_fail_marker_present")
        if _PAUSED_MARKER in line and f"target_date={target_date}" in line:
            log_issues.append("postclose_paused_marker_present")
        if _DONE_MARKER in line and f"target_date={target_date}" in line:
            done_line = line

    artifact_status = []
    for label, path in _artifact_paths(target_date).items():
        item = {
            "label": label,
            "path": str(path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
        }
        if path.suffix == ".json":
            item["json_valid"] = _json_valid(path)
        artifact_status.append(item)

    paths = _artifact_paths(target_date)
    ev_report = _load_json(paths["threshold_cycle_ev"])
    workorder = _load_json(paths["code_improvement_workorder"])
    runtime_summary = _load_json(paths["runtime_approval_summary"])
    ldm_report = _load_json(paths["lifecycle_decision_matrix"])
    discovery_report = _load_json(paths["lifecycle_bucket_discovery"])
    bridge_report = _load_json(REPORT_DIR / "runtime_apply_bridge" / f"runtime_apply_bridge_{target_date}.json")
    scalp_sim_overnight_path = _scalp_sim_overnight_path(target_date)
    scalp_sim_overnight = _load_json(scalp_sim_overnight_path)
    scalp_sim_overnight_quality = _scalp_sim_overnight_source_quality(
        scalp_sim_overnight,
        report_exists=scalp_sim_overnight_path.exists(),
    )
    if scalp_sim_overnight_quality.get("status") == "fail":
        log_issues.extend(scalp_sim_overnight_quality.get("missing") or [])
    ai_correction = _ai_correction_status(target_date)
    if ai_correction.get("status") == "fail":
        log_issues.append("ai_correction_unavailable_blocks_runtime_candidates")
    entry_bucket_handoff = _entry_bucket_handoff_status(ldm_report, ev_report, runtime_summary, workorder)
    if entry_bucket_handoff.get("status") == "fail":
        log_issues.append("ldm_entry_bucket_handoff_missing")
    scale_in_attribution = ldm_report.get("scale_in_bucket_attribution")
    scale_in_source_present = _has_scale_in_source(ldm_report)
    if scale_in_source_present and not isinstance(scale_in_attribution, dict):
        log_issues.append("ldm_scale_in_bucket_attribution_missing")
    scale_in_bucket_handoff = _scale_in_bucket_handoff_status(ldm_report, ev_report, runtime_summary, workorder)
    if isinstance(scale_in_attribution, dict) and scale_in_bucket_handoff.get("status") == "fail":
        log_issues.append("ldm_scale_in_bucket_handoff_missing")
    overnight_attribution = ldm_report.get("overnight_bucket_attribution")
    overnight_source_present = _has_overnight_source(ldm_report)
    if overnight_source_present and not isinstance(overnight_attribution, dict):
        log_issues.append("ldm_overnight_bucket_attribution_missing")
    overnight_bucket_handoff = _overnight_bucket_handoff_status(ldm_report, ev_report, runtime_summary, workorder)
    if isinstance(overnight_attribution, dict) and overnight_bucket_handoff.get("status") == "fail":
        log_issues.append("ldm_overnight_bucket_handoff_missing")
    lifecycle_bucket_discovery_handoff = _lifecycle_bucket_discovery_handoff_status(
        discovery_report,
        bridge_report,
        runtime_summary,
        workorder,
    )
    if lifecycle_bucket_discovery_handoff.get("status") == "fail":
        log_issues.append("lifecycle_bucket_discovery_handoff_missing")

    lineage = workorder.get("lineage") if isinstance(workorder.get("lineage"), dict) else {}
    workorder_snapshot = {
        "generation_id": workorder.get("generation_id"),
        "source_hash": workorder.get("source_hash"),
        "previous_generation_id": lineage.get("previous_generation_id"),
        "previous_source_hash": lineage.get("previous_source_hash"),
        "previous_exists": bool(lineage.get("previous_exists")),
        "new_order_ids": list(lineage.get("new_order_ids") or []),
        "removed_order_ids": list(lineage.get("removed_order_ids") or []),
        "decision_changed_order_ids": list(lineage.get("decision_changed_order_ids") or []),
        "new_selected_order_count": ((workorder.get("summary") or {}).get("new_selected_order_count")),
        "removed_selected_order_count": ((workorder.get("summary") or {}).get("removed_selected_order_count")),
        "decision_changed_order_count": ((workorder.get("summary") or {}).get("decision_changed_order_count")),
    }

    if workorder_snapshot["generation_id"] and workorder_snapshot["source_hash"]:
        if workorder_snapshot["source_hash"] == workorder_snapshot["previous_source_hash"]:
            workorder_snapshot_status = "same_snapshot_replay"
        elif workorder_snapshot["previous_exists"]:
            workorder_snapshot_status = "source_changed_with_lineage"
        else:
            workorder_snapshot_status = "first_generation"
    else:
        workorder_snapshot_status = "missing_snapshot_identity"

    downstream_links = {
        "threshold_cycle_ev_sources_workorder": (
            ((ev_report.get("sources") or {}).get("code_improvement_workorder")) or None
        ),
        "runtime_approval_summary_sources_ev": (
            ((runtime_summary.get("sources") or {}).get("threshold_cycle_ev")) or None
        ),
        "threshold_cycle_ev_sources_pattern_lab_currentness_audit": (
            ((ev_report.get("sources") or {}).get("pattern_lab_currentness_audit")) or None
        ),
        "threshold_cycle_ev_sources_pattern_lab_propagation_audit": (
            ((ev_report.get("sources") or {}).get("pattern_lab_propagation_audit")) or None
        ),
        "threshold_cycle_ev_sources_scalp_entry_action_decision_matrix": (
            ((ev_report.get("sources") or {}).get("scalp_entry_action_decision_matrix")) or None
        ),
        "threshold_cycle_ev_sources_lifecycle_decision_matrix": (
            ((ev_report.get("sources") or {}).get("lifecycle_decision_matrix")) or None
        ),
        "runtime_approval_summary_sources_scalp_entry_action_decision_matrix": (
            ((runtime_summary.get("sources") or {}).get("scalp_entry_action_decision_matrix")) or None
        ),
        "runtime_approval_summary_sources_lifecycle_decision_matrix": (
            ((runtime_summary.get("sources") or {}).get("lifecycle_decision_matrix")) or None
        ),
        "runtime_approval_summary_sources_pattern_lab_propagation_audit": (
            ((runtime_summary.get("sources") or {}).get("pattern_lab_propagation_audit")) or None
        ),
    }

    execution_flags = _parse_bool_flags(done_line or "")
    required_execution_flags = (
        "swing_lifecycle",
        "pattern_labs",
        "deepseek_swing_lab",
        "pattern_lab_currentness_audit",
        "pattern_lab_propagation_audit",
        "scalp_entry_adm",
        "lifecycle_decision_matrix",
        "code_improvement_workorder",
        "daily_ev",
        "runtime_approval_summary",
        "next_stage2_checklist",
    )
    missing_execution_flags = [
        key for key in required_execution_flags if done_line and key not in execution_flags
    ]
    disabled_stage_flags = [
        key
        for key in (
            "swing_lifecycle",
            "pattern_labs",
            "deepseek_swing_lab",
            "pattern_lab_currentness_audit",
            "pattern_lab_propagation_audit",
            "scalp_entry_adm",
            "lifecycle_decision_matrix",
            "code_improvement_workorder",
            "daily_ev",
            "runtime_approval_summary",
            "next_stage2_checklist",
        )
        if key in execution_flags and not execution_flags[key]
    ]
    disabled_artifact_labels = {
        "pattern_lab_currentness_audit" if "pattern_lab_currentness_audit" in disabled_stage_flags else "",
        "pattern_lab_propagation_audit" if "pattern_lab_propagation_audit" in disabled_stage_flags else "",
        "scalp_entry_action_decision_matrix" if "scalp_entry_adm" in disabled_stage_flags else "",
        "lifecycle_decision_matrix" if "lifecycle_decision_matrix" in disabled_stage_flags else "",
        "code_improvement_workorder" if "code_improvement_workorder" in disabled_stage_flags else "",
        "threshold_cycle_ev" if "daily_ev" in disabled_stage_flags else "",
        "runtime_approval_summary" if "runtime_approval_summary" in disabled_stage_flags else "",
        "next_stage2_checklist" if "next_stage2_checklist" in disabled_stage_flags else "",
    }
    disabled_artifact_labels.discard("")
    missing_required_artifacts = [
        item["label"]
        for item in artifact_status
        if item["label"] not in disabled_artifact_labels
        and (
            item["label"] not in _OPTIONAL_ARTIFACT_LABELS
            or item.get("exists")
        )
        and (
            not item.get("exists")
            or (item.get("json_valid") is False)
        )
    ]
    missing_downstream_links = [
        key for key, value in downstream_links.items() if value in (None, "", "-")
    ]
    if "pattern_lab_currentness_audit" in disabled_stage_flags:
        missing_downstream_links = [
            key for key in missing_downstream_links if "pattern_lab_currentness_audit" not in key
        ]
    if "pattern_lab_propagation_audit" in disabled_stage_flags:
        missing_downstream_links = [
            key for key in missing_downstream_links if "pattern_lab_propagation_audit" not in key
        ]
    if "code_improvement_workorder" in disabled_stage_flags:
        missing_downstream_links = [
            key for key in missing_downstream_links if "code_improvement_workorder" not in key
        ]
    if "scalp_entry_adm" in disabled_stage_flags:
        missing_downstream_links = [
            key for key in missing_downstream_links if "scalp_entry_action_decision_matrix" not in key
        ]
    if "lifecycle_decision_matrix" in disabled_stage_flags:
        missing_downstream_links = [
            key for key in missing_downstream_links if "lifecycle_decision_matrix" not in key
        ]
    if "daily_ev" in disabled_stage_flags or "runtime_approval_summary" in disabled_stage_flags:
        missing_downstream_links = []
    pending_done_marker = bool(start_line and done_line is None and not require_done_marker)
    execution_profile_status = "full_profile"
    if disabled_stage_flags:
        execution_profile_status = "recovered_partial_profile"
    elif done_line is None and start_line:
        execution_profile_status = "done_marker_missing" if require_done_marker else "pending_done_marker"

    status = "pass"
    if not start_line:
        if _postclose_not_yet_due(target_date):
            status = "not_yet_due"
        else:
            status = "fail"
            log_issues.append("postclose_start_marker_missing")
    elif predecessor_timeouts or log_issues:
        status = "fail"
    elif done_line is None and require_done_marker:
        status = "fail"
        log_issues.append("postclose_done_marker_missing")
    elif missing_execution_flags:
        status = "fail"
        log_issues.append("postclose_done_marker_missing_required_flags")
    elif missing_required_artifacts:
        status = "fail"
    elif missing_downstream_links:
        status = "fail"
    elif predecessor_waits:
        status = "warning"
    elif disabled_stage_flags:
        status = "warning"
    elif workorder_snapshot_status == "missing_snapshot_identity":
        status = "fail"
    elif pending_done_marker:
        status = "pass_with_pending_done_marker"

    return {
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": "threshold_cycle_postclose_verification",
        "status": status,
        "log_path": str(LOG_PATH),
        "latest_start_marker": start_line,
        "latest_done_marker": done_line,
        "execution_profile": {
            "status": execution_profile_status,
            "require_done_marker": require_done_marker,
            "pending_done_marker": pending_done_marker,
            "flags": execution_flags,
            "disabled_stage_flags": disabled_stage_flags,
            "missing_required_flags": missing_execution_flags,
            "interpretation": (
                "latest DONE marker was produced by a recovery run with selected heavy stages disabled; "
                "same-date artifacts are still validated separately"
                if disabled_stage_flags
                else "latest DONE marker used full/default stage profile"
                if done_line
                else "wrapper-internal verification passed required artifacts; final DONE marker is checked by a later health check"
                if pending_done_marker
                else "latest START marker has no matching DONE marker"
            ),
        },
        "predecessor_integrity": {
            "status": (
                "not_yet_due"
                if status == "not_yet_due"
                else "pass_pending_done_marker"
                if status == "pass_with_pending_done_marker"
                else "fail"
                if predecessor_timeouts or log_issues
                else "warning"
                if predecessor_waits
                else "pass"
            ),
            "wait_count": len(predecessor_waits),
            "timeout_count": len(predecessor_timeouts),
            "waits": predecessor_waits,
            "timeouts": predecessor_timeouts,
            "log_issues": sorted(set(log_issues)),
        },
        "artifact_status": artifact_status,
        "missing_required_artifacts": missing_required_artifacts,
        "workorder_snapshot": {
            **workorder_snapshot,
            "status": workorder_snapshot_status,
            "priority_rule": "prefer_generation_id_source_hash_lineage_over_mtime",
        },
        "downstream_links": downstream_links,
        "missing_downstream_links": missing_downstream_links,
        "ai_correction": ai_correction,
        "scalp_sim_overnight_source_quality": scalp_sim_overnight_quality,
        "entry_bucket_handoff": entry_bucket_handoff,
        "scale_in_bucket_handoff": scale_in_bucket_handoff,
        "scale_in_bucket_attribution_present": isinstance(scale_in_attribution, dict),
        "scale_in_source_present": scale_in_source_present,
        "overnight_bucket_handoff": overnight_bucket_handoff,
        "overnight_bucket_attribution_present": isinstance(overnight_attribution, dict),
        "overnight_source_present": overnight_source_present,
        "lifecycle_bucket_discovery_handoff": lifecycle_bucket_discovery_handoff,
    }


def _render_markdown(report: dict[str, Any]) -> str:
    predecessor = report.get("predecessor_integrity") if isinstance(report.get("predecessor_integrity"), dict) else {}
    workorder = report.get("workorder_snapshot") if isinstance(report.get("workorder_snapshot"), dict) else {}
    ai_correction = report.get("ai_correction") if isinstance(report.get("ai_correction"), dict) else {}
    overnight_quality = (
        report.get("scalp_sim_overnight_source_quality")
        if isinstance(report.get("scalp_sim_overnight_source_quality"), dict)
        else {}
    )
    entry_bucket = report.get("entry_bucket_handoff") if isinstance(report.get("entry_bucket_handoff"), dict) else {}
    scale_in_bucket = report.get("scale_in_bucket_handoff") if isinstance(report.get("scale_in_bucket_handoff"), dict) else {}
    overnight_bucket = report.get("overnight_bucket_handoff") if isinstance(report.get("overnight_bucket_handoff"), dict) else {}
    lifecycle_bucket = (
        report.get("lifecycle_bucket_discovery_handoff")
        if isinstance(report.get("lifecycle_bucket_discovery_handoff"), dict)
        else {}
    )
    lines = [
        f"# Threshold Cycle Postclose Verification - {report.get('date')}",
        "",
        f"- status: `{report.get('status')}`",
        f"- latest_start_marker: `{report.get('latest_start_marker') or '-'}`",
        f"- latest_done_marker: `{report.get('latest_done_marker') or '-'}`",
        f"- predecessor_status: `{predecessor.get('status')}`",
        f"- predecessor_wait_count: `{predecessor.get('wait_count')}`",
        f"- predecessor_timeout_count: `{predecessor.get('timeout_count')}`",
        f"- log_issues: `{predecessor.get('log_issues') or []}`",
        "",
        "## Execution Profile",
        f"- profile_status: `{(report.get('execution_profile') or {}).get('status') or '-'}`",
        f"- disabled_stage_flags: `{(report.get('execution_profile') or {}).get('disabled_stage_flags') or []}`",
        f"- missing_required_flags: `{(report.get('execution_profile') or {}).get('missing_required_flags') or []}`",
        f"- interpretation: `{(report.get('execution_profile') or {}).get('interpretation') or '-'}`",
        f"- missing_required_artifacts: `{report.get('missing_required_artifacts') or []}`",
        f"- missing_downstream_links: `{report.get('missing_downstream_links') or []}`",
        "",
        "## AI Correction",
        f"- status: `{ai_correction.get('status') or '-'}`",
        f"- ai_status: `{ai_correction.get('ai_status') or '-'}`",
        f"- provider_status: `{ai_correction.get('provider_status') or '-'}`",
        f"- blocking_runtime_candidate_families: `{ai_correction.get('blocking_runtime_candidate_families') or []}`",
        f"- parse_warnings: `{ai_correction.get('parse_warnings') or []}`",
        f"- interpretation: `{ai_correction.get('interpretation') or '-'}`",
        "",
        "## Scalp Sim Overnight",
        f"- status: `{overnight_quality.get('status') or '-'}`",
        f"- decision_target: `{overnight_quality.get('decision_target') or 0}`",
        f"- active_undecided_count: `{overnight_quality.get('active_undecided_count') or 0}`",
        f"- decision_coverage_rate: `{overnight_quality.get('decision_coverage_rate')}`",
        f"- source_quality_status: `{overnight_quality.get('source_quality_status') or '-'}`",
        f"- source_quality_warnings: `{overnight_quality.get('source_quality_warnings') or []}`",
        f"- interpretation: `{overnight_quality.get('interpretation') or '-'}`",
        "",
        "## Entry Bucket Handoff",
        f"- status: `{entry_bucket.get('status') or '-'}`",
        f"- expected_candidate_ids: `{entry_bucket.get('expected_candidate_ids') or []}`",
        f"- missing_ev_candidate_ids: `{entry_bucket.get('missing_ev_candidate_ids') or []}`",
        f"- missing_runtime_summary_candidate_ids: `{entry_bucket.get('missing_runtime_summary_candidate_ids') or []}`",
        f"- missing_workorder_order_ids: `{entry_bucket.get('missing_workorder_order_ids') or []}`",
        f"- interpretation: `{entry_bucket.get('interpretation') or '-'}`",
        "",
        "## Scale-In Bucket Handoff",
        f"- attribution_present: `{report.get('scale_in_bucket_attribution_present')}`",
        f"- source_present: `{report.get('scale_in_source_present')}`",
        f"- status: `{scale_in_bucket.get('status') or '-'}`",
        f"- expected_candidate_ids: `{scale_in_bucket.get('expected_candidate_ids') or []}`",
        f"- missing_ev_candidate_ids: `{scale_in_bucket.get('missing_ev_candidate_ids') or []}`",
        f"- missing_runtime_summary_candidate_ids: `{scale_in_bucket.get('missing_runtime_summary_candidate_ids') or []}`",
        f"- missing_workorder_order_ids: `{scale_in_bucket.get('missing_workorder_order_ids') or []}`",
        f"- interpretation: `{scale_in_bucket.get('interpretation') or '-'}`",
        "",
        "## Overnight Bucket Handoff",
        f"- attribution_present: `{report.get('overnight_bucket_attribution_present')}`",
        f"- source_present: `{report.get('overnight_source_present')}`",
        f"- status: `{overnight_bucket.get('status') or '-'}`",
        f"- expected_candidate_ids: `{overnight_bucket.get('expected_candidate_ids') or []}`",
        f"- missing_ev_candidate_ids: `{overnight_bucket.get('missing_ev_candidate_ids') or []}`",
        f"- missing_runtime_summary_candidate_ids: `{overnight_bucket.get('missing_runtime_summary_candidate_ids') or []}`",
        f"- missing_workorder_order_ids: `{overnight_bucket.get('missing_workorder_order_ids') or []}`",
        f"- interpretation: `{overnight_bucket.get('interpretation') or '-'}`",
        "",
        "## Lifecycle Bucket Discovery Handoff",
        f"- status: `{lifecycle_bucket.get('status') or '-'}`",
        f"- source_contract_status: `{lifecycle_bucket.get('source_contract_status') or '-'}`",
        f"- ai_two_pass_review_status: `{lifecycle_bucket.get('ai_two_pass_review_status') or '-'}`",
        f"- expected_candidate_ids: `{lifecycle_bucket.get('expected_candidate_ids') or []}`",
        f"- live_auto_apply_families: `{lifecycle_bucket.get('live_auto_apply_families') or []}`",
        f"- missing_bridge_families: `{lifecycle_bucket.get('missing_bridge_families') or []}`",
        f"- missing_runtime_summary_candidate_ids: `{lifecycle_bucket.get('missing_runtime_summary_candidate_ids') or []}`",
        f"- workorder_needed_bucket_ids: `{lifecycle_bucket.get('workorder_needed_bucket_ids') or []}`",
        f"- ai_post_apply_followup_bucket_ids: `{lifecycle_bucket.get('ai_post_apply_followup_bucket_ids') or []}`",
        f"- warnings: `{lifecycle_bucket.get('warnings') or []}`",
        f"- interpretation: `{lifecycle_bucket.get('interpretation') or '-'}`",
        "",
        "## Workorder Snapshot",
        f"- generation_id: `{workorder.get('generation_id') or '-'}`",
        f"- source_hash: `{workorder.get('source_hash') or '-'}`",
        f"- snapshot_status: `{workorder.get('status') or '-'}`",
        f"- previous_generation_id: `{workorder.get('previous_generation_id') or '-'}`",
        f"- previous_source_hash: `{workorder.get('previous_source_hash') or '-'}`",
        f"- new_order_ids: `{workorder.get('new_order_ids') or []}`",
        f"- removed_order_ids: `{workorder.get('removed_order_ids') or []}`",
        f"- decision_changed_order_ids: `{workorder.get('decision_changed_order_ids') or []}`",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify threshold-cycle postclose chain integrity.")
    parser.add_argument("--date", required=True)
    parser.add_argument(
        "--allow-pending-done-marker",
        action="store_true",
        help=(
            "Allow wrapper-internal verification to pass when required artifacts are present "
            "but the wrapper has not emitted its final DONE marker yet."
        ),
    )
    args = parser.parse_args()

    report = build_threshold_cycle_postclose_verification(
        args.date,
        require_done_marker=not args.allow_pending_done_marker,
    )
    VERIFY_DIR.mkdir(parents=True, exist_ok=True)
    json_path, md_path = verification_report_paths(args.date)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    print(json.dumps({"status": report.get("status"), "json": str(json_path), "md": str(md_path)}, ensure_ascii=False))
    if report.get("status") == "fail":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
