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


def _postclose_not_yet_due(target_date: str) -> bool:
    try:
        parsed = date.fromisoformat(target_date)
    except ValueError:
        return False
    now = datetime.now()
    return parsed == now.date() and now.time() < dtime(16, 10)


def build_threshold_cycle_postclose_verification(target_date: str) -> dict[str, Any]:
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

    ev_report = _load_json(_artifact_paths(target_date)["threshold_cycle_ev"])
    workorder = _load_json(_artifact_paths(target_date)["code_improvement_workorder"])
    runtime_summary = _load_json(_artifact_paths(target_date)["runtime_approval_summary"])

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
    execution_profile_status = "full_profile"
    if disabled_stage_flags:
        execution_profile_status = "recovered_partial_profile"
    elif done_line is None and start_line:
        execution_profile_status = "done_marker_missing"

    status = "pass"
    if not start_line:
        if _postclose_not_yet_due(target_date):
            status = "not_yet_due"
        else:
            status = "fail"
            log_issues.append("postclose_start_marker_missing")
    elif predecessor_timeouts or log_issues:
        status = "fail"
    elif done_line is None:
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
            "flags": execution_flags,
            "disabled_stage_flags": disabled_stage_flags,
            "missing_required_flags": missing_execution_flags,
            "interpretation": (
                "latest DONE marker was produced by a recovery run with selected heavy stages disabled; "
                "same-date artifacts are still validated separately"
                if disabled_stage_flags
                else "latest DONE marker used full/default stage profile"
                if done_line
                else "latest START marker has no matching DONE marker"
            ),
        },
        "predecessor_integrity": {
            "status": (
                "not_yet_due"
                if status == "not_yet_due"
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
    }


def _render_markdown(report: dict[str, Any]) -> str:
    predecessor = report.get("predecessor_integrity") if isinstance(report.get("predecessor_integrity"), dict) else {}
    workorder = report.get("workorder_snapshot") if isinstance(report.get("workorder_snapshot"), dict) else {}
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
    args = parser.parse_args()

    report = build_threshold_cycle_postclose_verification(args.date)
    VERIFY_DIR.mkdir(parents=True, exist_ok=True)
    json_path, md_path = verification_report_paths(args.date)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    print(json.dumps({"status": report.get("status"), "json": str(json_path), "md": str(md_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
