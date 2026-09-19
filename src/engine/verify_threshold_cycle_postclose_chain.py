"""Verify the direct family postclose chain after common Daily/EV retirement."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR

REPORT_DIR = DATA_DIR / "report"
OUTPUT_DIR = REPORT_DIR / "threshold_cycle_postclose_verification"
EXPLICIT_DISABLED_STAGE_ALLOWLIST = frozenset({
    "swing_lifecycle", "swing_strategy_discovery", "swing_lifecycle_matrix",
    "swing_lifecycle_bucket_discovery", "deepseek_swing_lab",
})


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _sha(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _artifact_paths(target_date: str) -> dict[str, Path]:
    return {
        "runtime_summary": REPORT_DIR / "runtime_approval_summary" / f"runtime_approval_summary_{target_date}.json",
        "postclose_status": REPORT_DIR / "threshold_cycle_postclose_status" / f"threshold_cycle_postclose_{target_date}.status.json",
        "scanner_lookup_attention_selection": DATA_DIR / "threshold_cycle" / "scanner_lookup_attention_preopen" / f"scanner_lookup_attention_preopen_{target_date}.json",
        "scanner_lookup_attention_policy": DATA_DIR / "threshold_cycle" / "scanner_lookup_attention_policy" / f"scanner_lookup_attention_policy_{target_date}.json",
    }


def _direct_source_checks(summary: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    checks: list[dict[str, Any]] = []
    issues: list[str] = []
    sources = summary.get("sources") if isinstance(summary.get("sources"), dict) else {}
    for owner, source in sources.items():
        if not isinstance(source, dict):
            issues.append(f"direct_source_invalid:{owner}")
            continue
        check = {
            "owner": owner,
            "path": source.get("path"),
            "exists": source.get("exists") is True,
            "target_date_matches": source.get("target_date_matches") is True,
            "sha256": source.get("sha256"),
            "status": source.get("status"),
            "error": source.get("error"),
            "applicability": source.get("applicability"),
            "economic_evidence": source.get("economic_evidence"),
            "required": source.get("required") is True,
            "current_sha256": _sha(Path(str(source.get("path") or ""))),
        }
        checks.append(check)
        evidence = check["economic_evidence"] if isinstance(check["economic_evidence"], dict) else {}
        comparison_status = evidence.get("comparison_status")
        if comparison_status in {"source_gap", "unsupported_scope", "mixed"} and evidence.get("policy_apply_allowed") is True:
            issues.append(f"blocked_economic_source_marked_applyable:{owner}")
        if comparison_status == "validated_edge":
            policy_receipt = source.get("policy_receipt") if isinstance(source.get("policy_receipt"), dict) else {}
            if evidence.get("policy_handoff_state") != "candidate_published" or policy_receipt.get("valid") is not True:
                issues.append(f"validated_edge_policy_handoff_missing:{owner}")
        if check["required"] and check["error"]:
            issues.append(f"direct_source_contract_error:{owner}:{check['error']}")
        elif check["exists"] and check["current_sha256"] != check["sha256"]:
            issues.append(f"direct_source_hash_mismatch:{owner}")
        elif not check["exists"] and check["required"]:
            issues.append(f"direct_source_missing:{owner}")
        elif check["required"] and check["exists"] and not check["target_date_matches"]:
            issues.append(f"direct_source_date_mismatch:{owner}")
        elif check["required"] and check["exists"] and not check["sha256"]:
            issues.append(f"direct_source_hash_missing:{owner}")
    return checks, issues


def _direct_checklist_checks(
    target_date: str, summary: dict[str, Any], summary_path: Path
) -> tuple[dict[str, Any], list[str]]:
    from src.engine.automation.postclose_summary_handoff import verify_summary_handoff
    from src.engine.build_next_stage2_checklist import (
        _next_krx_trading_day,
        _project_direct_tasks,
        stage2_checklist_path,
    )

    preopen = (
        summary.get("preopen_consumption_receipt")
        if isinstance(summary.get("preopen_consumption_receipt"), dict)
        else {}
    )
    apply_date = str(preopen.get("apply_date") or _next_krx_trading_day(target_date))
    checklist_path = stage2_checklist_path(apply_date)
    handoff = verify_summary_handoff(
        target_date,
        report_dir=REPORT_DIR,
        checklist_path=checklist_path,
        require_tower=False,
        require_checklist=True,
    )
    issues = list(handoff.get("issues") or [])
    summary_sha256 = _sha(summary_path) or "missing"
    expected_tasks, _ = _project_direct_tasks(
        summary=summary,
        source_date=target_date,
        target_date=apply_date,
        summary_path=summary_path,
        summary_sha256=summary_sha256,
    )
    expected_ids = sorted(task.task_id for task in expected_tasks)
    try:
        checklist_text = checklist_path.read_text(encoding="utf-8")
    except OSError:
        checklist_text = ""
    actual_ids = sorted(
        match.group(1)
        for match in re.finditer(
            r"^- \[[ xX]\] `\[(DirectFamily[A-Za-z0-9_:-]+)\]",
            checklist_text,
            re.MULTILINE,
        )
    )
    if actual_ids != expected_ids:
        issues.append("direct_checklist_task_projection_mismatch")
    return {
        "status": "pass" if not issues else "fail",
        "path": str(checklist_path),
        "apply_date": apply_date,
        "expected_task_ids": expected_ids,
        "actual_task_ids": actual_ids,
        "handoff": handoff,
    }, issues


def build_threshold_cycle_postclose_verification(
    target_date: str,
    *,
    require_done_marker: bool = True,
    disabled_stages: set[str] | None = None,
    require_summary_handoff: bool = False,
    allow_pending_entry_replay: bool = False,
) -> dict[str, Any]:
    paths = _artifact_paths(target_date)
    summary = _load(paths["runtime_summary"])
    postclose = _load(paths["postclose_status"])
    checks, issues = _direct_source_checks(summary)
    if summary.get("date") != target_date:
        issues.append("runtime_summary_date_mismatch")
    if summary.get("status") != "direct_evidence_complete":
        issues.append("runtime_summary_incomplete")
    if summary.get("direct_evidence_state") != "complete":
        issues.append("runtime_summary_direct_evidence_state_incomplete")
    if summary.get("runtime_effect") is not False:
        issues.append("runtime_summary_authority_invalid")
    if summary.get("allowed_runtime_apply") is not False:
        issues.append("runtime_summary_apply_authority_invalid")
    if summary.get("daily_threshold_cycle_retired") is not True:
        issues.append("daily_retirement_contract_missing")
    if summary.get("threshold_cycle_ev_retired") is not True:
        issues.append("ev_retirement_contract_missing")
    if require_done_marker and postclose.get("status") != "succeeded":
        issues.append("postclose_terminal_status_missing")
    if require_summary_handoff and not paths["runtime_summary"].exists():
        issues.append("summary_handoff_missing")
    checklist_handoff: dict[str, Any] = {
        "status": "not_required",
        "path": None,
        "expected_task_ids": [],
        "actual_task_ids": [],
    }
    if require_summary_handoff and paths["runtime_summary"].exists():
        checklist_handoff, checklist_issues = _direct_checklist_checks(
            target_date, summary, paths["runtime_summary"]
        )
        issues.extend(checklist_issues)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 2,
        "report_type": "threshold_cycle_postclose_verification",
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": status,
        "issues": issues,
        "failure_summary": {"issue_count": len(issues), "issues": issues},
        "direct_source_checks": checks,
        "summary_handoff": {
            "status": "pass" if paths["runtime_summary"].exists() else "missing",
            "path": str(paths["runtime_summary"]),
            "sha256": _sha(paths["runtime_summary"]),
            "recommendation_intake": "family_owned_direct_only",
        },
        "checklist_handoff": checklist_handoff,
        "retired_common_layers": [
            "daily_threshold_cycle_report", "threshold_cycle_ev_report", "threshold_cycle_preopen_apply"
        ],
        "disabled_stages": sorted(disabled_stages or set()),
        "allow_pending_entry_replay": allow_pending_entry_replay,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def _render(report: dict[str, Any]) -> str:
    lines = [
        f"# Direct postclose verification - {report['date']}", "",
        f"- status: `{report['status']}`",
        "- common Daily/EV/PREOPEN selector: `retired`",
        f"- issue_count: `{len(report['issues'])}`", "", "## Direct sources",
    ]
    lines.extend(
        f"- `{row['owner']}`: exists=`{row['exists']}` date_match=`{row['target_date_matches']}`"
        for row in report["direct_source_checks"]
    )
    if report["issues"]:
        lines.extend(["", "## Issues", *[f"- `{issue}`" for issue in report["issues"]]])
    return "\n".join(lines) + "\n"


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _write_verification_receipts(
    target_date: str, report: dict[str, Any], *, invocation: dict[str, Any]
) -> tuple[dict[str, Any], Path, Path, Path]:
    json_path = OUTPUT_DIR / f"threshold_cycle_postclose_verification_{target_date}.json"
    md_path = OUTPUT_DIR / f"threshold_cycle_postclose_verification_{target_date}.md"
    attempt_path = OUTPUT_DIR / f"threshold_cycle_postclose_verification_attempt_{target_date}.json"
    report = dict(report)
    report["verification_attempt"] = {
        "immutable": True,
        "invocation": invocation,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    if report.get("status") == "fail":
        report["first_failure_receipt"] = {
            "issues": list(report.get("issues") or []),
            "created_at": report["verification_attempt"]["created_at"],
        }
    body = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    _atomic_write(json_path, body)
    _atomic_write(md_path, _render(report))
    _atomic_write(attempt_path, body)
    return report, json_path, md_path, attempt_path


def _scanner_scope(target_date: str) -> dict[str, Any]:
    paths = _artifact_paths(target_date)
    issues = [name for name in ("scanner_lookup_attention_selection", "scanner_lookup_attention_policy") if not paths[name].exists()]
    return {"status": "pass" if not issues else "fail", "scope": "scanner_lookup_attention_only", "issues": issues, "whole_native_chain_done_claimed": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--require-summary-handoff", action="store_true")
    parser.add_argument("--scanner-lookup-summary-only", action="store_true")
    parser.add_argument("--compact-summary-only", action="store_true")
    parser.add_argument("--entry-cancel-wait-summary-only", action="store_true")
    parser.add_argument("--allow-pending-done-marker", action="store_true")
    parser.add_argument("--allow-pending-entry-replay", action="store_true")
    parser.add_argument("--disabled-stage", action="append", default=[])
    args = parser.parse_args(argv)
    if args.scanner_lookup_summary_only:
        report = _scanner_scope(args.date)
        print(json.dumps(report, ensure_ascii=False))
        return 0 if report["status"] == "pass" else 2
    if args.entry_cancel_wait_summary_only:
        from src.engine.automation.entry_cancel_wait_tuning import verify_handoff
        report = verify_handoff(args.date)
        print(json.dumps(report, ensure_ascii=False))
        return 0 if report.get("status") == "PASS" else 2
    if args.compact_summary_only:
        from src.engine.scalping.main_ai_prompt_consumer import verify_compact_handoff
        report = verify_compact_handoff(DATA_DIR, args.date)
        print(json.dumps(report, ensure_ascii=False))
        return 0 if report.get("status") == "PASS" else 2
    report = build_threshold_cycle_postclose_verification(
        args.date,
        require_done_marker=not args.allow_pending_done_marker,
        disabled_stages=set(args.disabled_stage),
        require_summary_handoff=args.require_summary_handoff,
        allow_pending_entry_replay=args.allow_pending_entry_replay,
    )
    report, json_path, md_path, attempt_path = _write_verification_receipts(
        args.date, report,
        invocation={
            "require_done_marker": not args.allow_pending_done_marker,
            "require_summary_handoff": args.require_summary_handoff,
            "disabled_stages": sorted(set(args.disabled_stage)),
        },
    )
    print(json.dumps({"status": report["status"], "json": str(json_path), "md": str(md_path), "attempt_json": str(attempt_path), "failure_summary": report["failure_summary"]}, ensure_ascii=False))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
